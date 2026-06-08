import { describe, expect, it } from 'vitest'

import { LONG_RUN_CHARMS } from '../content/charms.js'

describe('LONG_RUN_CHARMS', () => {
  it('exposes a non-empty array of charm strings', () => {
    expect(Array.isArray(LONG_RUN_CHARMS)).toBe(true)
    expect(LONG_RUN_CHARMS.length).toBeGreaterThan(0)
  })

  it('every entry is a non-empty string', () => {
    for (const charm of LONG_RUN_CHARMS) {
      expect(typeof charm).toBe('string')
      expect(charm.length).toBeGreaterThan(0)
    }
  })

  it('all charms are unique (no duplicates)', () => {
    expect(new Set(LONG_RUN_CHARMS).size).toBe(LONG_RUN_CHARMS.length)
  })

  it('every entry ends with the ellipsis "…" character', () => {
    for (const charm of LONG_RUN_CHARMS) {
      expect(charm.endsWith('…')).toBe(true)
    }
  })

  it('no entry contains literal newlines (single-line surface only)', () => {
    for (const charm of LONG_RUN_CHARMS) {
      expect(charm.includes('\n')).toBe(false)
    }
  })

  it('every entry stays under 60 chars (suffix appended at runtime fits status row)', () => {
    for (const charm of LONG_RUN_CHARMS) {
      expect(charm.length).toBeLessThan(60)
    }
  })
})
