import { mkdtempSync, readFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

let tmp: string
let originalHome: string | undefined

async function loadFreshModule() {
  vi.resetModules()
  return import('../lib/history.js')
}

beforeEach(() => {
  originalHome = process.env.HERMES_HOME
  tmp = mkdtempSync(join(tmpdir(), 'hermes-history-'))
  process.env.HERMES_HOME = tmp
})

afterEach(() => {
  if (originalHome === undefined) {
    delete process.env.HERMES_HOME
  } else {
    process.env.HERMES_HOME = originalHome
  }
})

describe('history.load', () => {
  it('returns an empty list when no history file exists yet', async () => {
    const { load } = await loadFreshModule()
    expect(load()).toEqual([])
  })

  it('caches subsequent calls (returns the same array reference)', async () => {
    const { load } = await loadFreshModule()
    expect(load()).toBe(load())
  })

  it('round-trips single-line entries through append+load', async () => {
    const { append, load } = await loadFreshModule()
    append('first')
    append('second')
    expect(load()).toEqual(['first', 'second'])
  })

  it('preserves multi-line entries with embedded newlines', async () => {
    const { append, load } = await loadFreshModule()
    append('line a\nline b\nline c')
    expect(load()).toEqual(['line a\nline b\nline c'])
  })
})

describe('history.append', () => {
  it('skips empty / whitespace-only input', async () => {
    const { append, load } = await loadFreshModule()
    append('')
    append('   ')
    append('\t\n')
    expect(load()).toEqual([])
  })

  it('deduplicates consecutive duplicates', async () => {
    const { append, load } = await loadFreshModule()
    append('foo')
    append('foo')
    append('foo')
    append('bar')
    append('foo')
    expect(load()).toEqual(['foo', 'bar', 'foo'])
  })

  it('trims surrounding whitespace before storing', async () => {
    const { append, load } = await loadFreshModule()
    append('  trimmed  ')
    expect(load()).toEqual(['trimmed'])
  })

  it('encodes each line with a leading + so multi-line entries survive on disk', async () => {
    const { append } = await loadFreshModule()
    append('a\nb')
    const file = readFileSync(join(tmp, '.hermes_history'), 'utf8')
    expect(file).toContain('+a')
    expect(file).toContain('+b')
  })
})

describe('history.MAX cap', () => {
  it('stays within the 1000-entry cap when appending many distinct lines', async () => {
    const { append, load } = await loadFreshModule()
    for (let i = 0; i < 1100; i++) {
      append(`entry-${i}`)
    }
    const items = load()
    expect(items.length).toBe(1000)
    expect(items[0]).toBe('entry-100')
    expect(items.at(-1)).toBe('entry-1099')
  })
})
