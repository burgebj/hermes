import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { $composerAttachments, clearComposerAttachments } from '@/store/composer'

import { useComposerActions } from './use-composer-actions'

describe('useComposerActions', () => {
  beforeEach(() => {
    clearComposerAttachments()
  })

  afterEach(() => {
    clearComposerAttachments()
    vi.restoreAllMocks()
  })

  it('keeps pasted image bytes on blob attachments for remote gateway upload', async () => {
    const saveImageBuffer = vi.fn(async () => '/home/alice/.config/Hermes/composer-images/paste.png')

    Object.defineProperty(window, 'hermesDesktop', {
      configurable: true,
      value: {
        saveImageBuffer
      }
    })

    const { result } = renderHook(() =>
      useComposerActions({
        activeSessionId: 'sid',
        currentCwd: '/work',
        requestGateway: vi.fn()
      })
    )

    await act(async () => {
      await result.current.attachImageBlob(new Blob([new Uint8Array([1, 2, 3])], { type: 'image/png' }))
    })

    expect(saveImageBuffer).toHaveBeenCalledWith(expect.any(Uint8Array), '.png')
    const attachment = $composerAttachments.get()[0]

    expect(attachment).toMatchObject({
      contentBase64: 'AQID',
      filename: 'paste.png',
      kind: 'image',
      path: '/home/alice/.config/Hermes/composer-images/paste.png'
    })
    expect(attachment?.previewUrl).toBe('data:image/png;base64,AQID')
  })
})
