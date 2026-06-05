import { describe, expect, it } from 'vitest'

import { blobDedupeKey, detectTrigger, extractClipboardImageBlobs } from './text-utils'

describe('detectTrigger', () => {
  it('detects a bare slash trigger with an empty query', () => {
    expect(detectTrigger('/')).toEqual({ kind: '/', query: '', tokenLength: 1 })
  })

  it('detects a slash command query', () => {
    expect(detectTrigger('/skill')).toEqual({ kind: '/', query: 'skill', tokenLength: 6 })
  })

  it('detects a bare at-mention trigger with an empty query', () => {
    expect(detectTrigger('@')).toEqual({ kind: '@', query: '', tokenLength: 1 })
  })

  it('detects an at-mention query', () => {
    expect(detectTrigger('@file')).toEqual({ kind: '@', query: 'file', tokenLength: 5 })
  })

  it('returns null for plain text', () => {
    expect(detectTrigger('hello there')).toBeNull()
  })
})

describe('extractClipboardImageBlobs', () => {
  it('dedupes the same image exposed on both items and files', () => {
    const image = new File([new Uint8Array([1, 2, 3])], 'paste.png', {
      type: 'image/png',
      lastModified: 1_700_000_000_000
    })

    const clipboard = {
      files: {
        length: 1,
        item: (index: number) => (index === 0 ? image : null)
      },
      getData: () => '',
      items: [
        {
          kind: 'file',
          type: 'image/png',
          getAsFile: () => image
        }
      ]
    } as unknown as DataTransfer

    expect(extractClipboardImageBlobs(clipboard)).toEqual([image])
  })

  it('falls back to files when items has no image', () => {
    const image = new File([new Uint8Array([4, 5])], 'shot.jpg', {
      type: 'image/jpeg',
      lastModified: 1_700_000_000_001
    })

    const clipboard = {
      files: {
        length: 1,
        item: (index: number) => (index === 0 ? image : null)
      },
      getData: () => '',
      items: []
    } as unknown as DataTransfer

    expect(extractClipboardImageBlobs(clipboard)).toEqual([image])
  })
})

describe('blobDedupeKey', () => {
  it('uses file metadata for File blobs', () => {
    const file = new File([], 'a.png', { type: 'image/png', lastModified: 42 })

    expect(blobDedupeKey(file)).toBe('file:a.png:0:image/png:42')
  })
})


describe('detectTrigger', () => {
  it('detects slash commands at the start of the input', () => {
    const result = detectTrigger('/steer')
    expect(result).toEqual({ kind: '/', query: 'steer', tokenLength: 6 })
  })

  it('detects partial slash commands at the start', () => {
    const result = detectTrigger('/st')
    expect(result).toEqual({ kind: '/', query: 'st', tokenLength: 3 })
  })

  it('detects bare slash at the start', () => {
    const result = detectTrigger('/')
    expect(result).toEqual({ kind: '/', query: '', tokenLength: 1 })
  })

  it('does NOT trigger slash autocomplete mid-message', () => {
    const result = detectTrigger('hello /steer')
    expect(result).toBeNull()
  })

  it('does NOT trigger slash autocomplete after a space mid-message', () => {
    const result = detectTrigger('some text /new')
    expect(result).toBeNull()
  })

  it('detects @ mentions at the start of the input', () => {
    const result = detectTrigger('@user')
    expect(result).toEqual({ kind: '@', query: 'user', tokenLength: 5 })
  })

  it('detects @ mentions mid-sentence after whitespace', () => {
    const result = detectTrigger('hello @user')
    expect(result).toEqual({ kind: '@', query: 'user', tokenLength: 5 })
  })

  it('detects @ mentions at the start of a new line', () => {
    const result = detectTrigger('hello\n@user')
    expect(result).toEqual({ kind: '@', query: 'user', tokenLength: 5 })
  })

  it('returns null for plain text without triggers', () => {
    expect(detectTrigger('hello world')).toBeNull()
  })

  it('returns null for empty input', () => {
    expect(detectTrigger('')).toBeNull()
  })

  it('returns null when / is embedded in a word mid-message', () => {
    expect(detectTrigger('use path/to/file')).toBeNull()
  })
})
