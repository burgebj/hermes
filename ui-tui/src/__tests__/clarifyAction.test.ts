import { describe, expect, it } from 'vitest'

import { clarifyAction } from '../components/promptActions.js'

describe('clarifyAction — pure key dispatch for ClarifyPrompt', () => {
  it('submits the current free-text answer on Enter', () => {
    expect(
      clarifyAction('', { return: true }, { choices: ['A', 'B'], custom: 'typed answer', sel: 2, typing: true })
    ).toEqual({ kind: 'choose', answer: 'typed answer' })
  })

  it('uses Esc to leave free-text mode when choices exist', () => {
    expect(
      clarifyAction('', { escape: true }, { choices: ['A'], custom: 'typed answer', sel: 1, typing: true })
    ).toEqual({ kind: 'back' })
  })

  it('uses Esc to cancel open-ended clarify prompts', () => {
    expect(
      clarifyAction('', { escape: true }, { choices: [], custom: 'typed answer', sel: 0, typing: true })
    ).toEqual({ kind: 'cancel' })
  })

  it('enters free-text mode when Enter targets the Other row', () => {
    expect(
      clarifyAction('', { return: true }, { choices: ['A', 'B'], custom: '', sel: 2, typing: false })
    ).toEqual({ kind: 'startTyping' })
  })

  it('submits the highlighted canned choice on Enter', () => {
    expect(
      clarifyAction('', { return: true }, { choices: ['A', 'B'], custom: '', sel: 1, typing: false })
    ).toEqual({ kind: 'choose', answer: 'B' })
  })

  it('accepts numeric quick-picks in choice mode', () => {
    expect(
      clarifyAction('2', {}, { choices: ['A', 'B'], custom: '', sel: 0, typing: false })
    ).toEqual({ kind: 'choose', answer: 'B' })
  })
})
