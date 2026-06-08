import { describe, expect, it } from 'vitest'

import { usageCacheLabel } from './statusbar'

describe('usageCacheLabel', () => {
  it('hides cache usage when no cache tokens have been reported', () => {
    expect(usageCacheLabel({ calls: 0, input: 1_000, output: 0, total: 1_000 })).toBeNull()
  })

  it('summarizes cache reads and writes with a computed hit ratio', () => {
    expect(
      usageCacheLabel({
        calls: 1,
        cache_read: 2_000,
        cache_write: 500,
        input: 1_000,
        output: 300,
        total: 3_800
      })
    ).toEqual({
      detail: '2.0k read / 500 write',
      label: 'cache 57%',
      title: 'Cache hit 57%; read 2.0k tokens; write 500 tokens'
    })
  })

  it('accepts backend token field names and explicit ratios', () => {
    expect(
      usageCacheLabel({
        calls: 1,
        cache_hit_ratio: 0.25,
        cache_read_tokens: 750,
        cache_write_tokens: 250,
        input: 2_000,
        output: 100,
        total: 3_100
      })
    ).toMatchObject({
      detail: '750 read / 250 write',
      label: 'cache 25%'
    })
  })
})
