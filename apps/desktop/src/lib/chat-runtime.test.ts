import { describe, expect, it } from 'vitest'

import { coerceThinkingText, sessionTitle } from './chat-runtime'

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

describe('sessionTitle', () => {
  it('keeps stored titles for local sessions', () => {
    expect(sessionTitle({ source: 'tui', title: 'Old local title', preview: 'newer local preview' } as any)).toBe(
      'Old local title'
    )
  })

  it('prefers previews for gateway sessions so long-lived chats do not hide under stale titles', () => {
    expect(sessionTitle({ source: 'whatsapp', title: 'Hostname check', preview: 'Karpathy LLM wiki follow-up' } as any)).toBe(
      'Karpathy LLM wiki follow-up'
    )
  })
})
