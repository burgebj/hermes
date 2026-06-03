import { describe, expect, it } from 'vitest'

import { coerceThinkingText, imageAttachRequestForAttachment } from './chat-runtime'

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

describe('imageAttachRequestForAttachment', () => {
  it('uses byte upload payloads instead of local paths when image bytes are available', () => {
    expect(
      imageAttachRequestForAttachment('sid', {
        contentBase64: 'iVBORw0KGgo=',
        filename: 'desktop-paste.png',
        id: 'image:/home/alice/.config/Hermes/composer-images/paste.png',
        kind: 'image',
        label: 'desktop-paste.png',
        path: '/home/alice/.config/Hermes/composer-images/paste.png'
      })
    ).toEqual({
      method: 'image.attach_bytes',
      params: {
        content_base64: 'iVBORw0KGgo=',
        filename: 'desktop-paste.png',
        session_id: 'sid'
      }
    })
  })

  it('keeps path attachments path-based when no upload payload exists', () => {
    expect(
      imageAttachRequestForAttachment('sid', {
        id: 'image:/tmp/local.png',
        kind: 'image',
        label: 'local.png',
        path: '/tmp/local.png'
      })
    ).toEqual({
      method: 'image.attach',
      params: {
        path: '/tmp/local.png',
        session_id: 'sid'
      }
    })
  })
})
