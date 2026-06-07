import { describe, expect, it } from 'vitest'

import { buildSetupRequiredSections, SETUP_REQUIRED_TITLE } from '../content/setup.js'

describe('SETUP_REQUIRED_TITLE', () => {
  it('exposes the panel title constant', () => {
    expect(SETUP_REQUIRED_TITLE).toBe('Setup Required')
  })
})

describe('buildSetupRequiredSections', () => {
  it('returns two sections: intro text + actions table', () => {
    const sections = buildSetupRequiredSections()
    expect(sections).toHaveLength(2)
  })

  it('first section is the intro mentioning model provider', () => {
    const [intro] = buildSetupRequiredSections()
    expect(intro.text).toMatch(/model provider/i)
    expect(intro.rows).toBeUndefined()
  })

  it('second section is the actions table with title "Actions"', () => {
    const [, actions] = buildSetupRequiredSections()
    expect(actions.title).toBe('Actions')
    expect(actions.rows).toBeDefined()
  })

  it('actions table includes /model, /setup and Ctrl+C entries', () => {
    const [, actions] = buildSetupRequiredSections()
    const keys = (actions.rows ?? []).map(row => row[0])
    expect(keys).toEqual(['/model', '/setup', 'Ctrl+C'])
  })

  it('every action row has a label and a description', () => {
    const [, actions] = buildSetupRequiredSections()
    for (const row of actions.rows ?? []) {
      expect(row).toHaveLength(2)
      expect(row[0]).toBeTruthy()
      expect(row[1]).toBeTruthy()
    }
  })

  it('returns a fresh array on each call (no shared mutable state)', () => {
    const a = buildSetupRequiredSections()
    const b = buildSetupRequiredSections()
    expect(a).not.toBe(b)
    expect(a).toEqual(b)
  })
})
