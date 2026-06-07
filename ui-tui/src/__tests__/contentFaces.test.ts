import { describe, expect, it } from 'vitest'

import { FACES } from '../content/faces.js'

describe('FACES', () => {
  it('has at least 10 entries', () => {
    expect(FACES.length).toBeGreaterThanOrEqual(10)
  })

  it('all entries are unique', () => {
    expect(new Set(FACES).size).toBe(FACES.length)
  })

  it('all entries are non-empty strings', () => {
    for (const face of FACES) {
      expect(typeof face).toBe('string')
      expect(face.length).toBeGreaterThan(0)
    }
  })

  it('no entry contains a newline', () => {
    for (const face of FACES) {
      expect(face).not.toContain('\n')
    }
  })

  it('no entry contains an ASCII control character', () => {
    for (const face of FACES) {
      // eslint-disable-next-line no-control-regex
      expect(face).not.toMatch(/[\x00-\x1f]/)
    }
  })

  it('every entry has bounded display width', () => {
    for (const face of FACES) {
      expect([...face].length).toBeLessThanOrEqual(20)
    }
  })
})
