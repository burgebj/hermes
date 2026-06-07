import { describe, expect, it } from 'vitest'

import { coerceThinkingText, parseCommandDispatch } from './chat-runtime'

describe('parseCommandDispatch', () => {
  it('parses the prefill directive returned by /undo', () => {
    expect(parseCommandDispatch({ message: 'edit me', notice: '↶ Undid 1 turn', type: 'prefill' })).toEqual({
      message: 'edit me',
      notice: '↶ Undid 1 turn',
      type: 'prefill'
    })
  })

  it('parses a prefill directive with no message or notice', () => {
    expect(parseCommandDispatch({ type: 'prefill' })).toEqual({ type: 'prefill' })
  })

  it('returns null for unknown directive types', () => {
    expect(parseCommandDispatch({ type: 'mystery' })).toBeNull()
  })
})

describe('coerceThinkingText', () => {
  it('strips streaming status prefixes from thinking deltas', () => {
    expect(coerceThinkingText("◉_◉ processing... checking the user's request")).toBe("checking the user's request")
    expect(coerceThinkingText('(¬‿¬) analyzing... reading the file')).toBe('reading the file')
  })

  it('drops empty thinking rewrite placeholder text', () => {
    expect(
      coerceThinkingText(
        "◉_◉ processing... I don't see any current rewritten thinking or next thinking to process. Could you provide the thinking content you'd like me to rewrite?"
      )
    ).toBe('')
  })
})
