import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { dailyFortune, randomFortune } from '../content/fortunes.js'

describe('dailyFortune', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-01-15T12:00:00Z'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('is deterministic for the same seed within the same day', () => {
    expect(dailyFortune('alice')).toBe(dailyFortune('alice'))
  })

  it('produces different values for different seeds', () => {
    const samples = new Set<string>()

    for (const seed of ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']) {
      samples.add(dailyFortune(seed))
    }

    expect(samples.size).toBeGreaterThan(1)
  })

  it('falls back to "anon" when seed is null', () => {
    expect(dailyFortune(null)).toBe(dailyFortune('anon'))
  })

  it('falls back to "anon" when seed is empty string', () => {
    expect(dailyFortune('')).toBe(dailyFortune('anon'))
  })

  it('changes when the day changes', () => {
    const day1 = dailyFortune('alice')

    vi.setSystemTime(new Date('2026-06-15T12:00:00Z'))
    const day2 = dailyFortune('alice')

    expect(day1).not.toBe(day2)
  })

  it('output begins with either common or legendary glyph', () => {
    const out = dailyFortune('alice')

    expect(out.startsWith('🔮 ') || out.startsWith('🌟 ')).toBe(true)
  })
})

describe('randomFortune', () => {
  it('returns a valid fortune string', () => {
    const out = randomFortune()

    expect(typeof out).toBe('string')
    expect(out.length).toBeGreaterThan(0)
    expect(out.startsWith('🔮 ') || out.startsWith('🌟 ')).toBe(true)
  })
})
