import { describe, expect, it, vi } from 'vitest'

import { composerPlainText, renderComposerContents, RICH_INPUT_SLOT, syncComposerDraft } from './rich-editor'

describe('renderComposerContents', () => {
  it('renders refs and raw text without interpreting user text as HTML', () => {
    const editor = document.createElement('div')
    editor.dataset.slot = RICH_INPUT_SLOT

    renderComposerContents(editor, '@file:`<img src=x onerror=alert(1)>` <b>raw</b>')

    expect(editor.querySelector('img')).toBeNull()
    expect(editor.querySelector('b')).toBeNull()
    expect(editor.textContent).toContain('<img src=x onerror=alert(1)>')
    expect(editor.textContent).toContain('<b>raw</b>')
    expect(composerPlainText(editor)).toBe('@file:`<img src=x onerror=alert(1)>` <b>raw</b>')
  })
})

describe('composerPlainText', () => {
  it('does not add a trailing newline for browser-created block wrappers', () => {
    const editor = document.createElement('div')
    const line = document.createElement('div')

    editor.dataset.slot = RICH_INPUT_SLOT
    line.textContent = '帮我查一下这个bug'
    editor.append(line)

    expect(composerPlainText(editor)).toBe('帮我查一下这个bug')
  })

  it('keeps newlines between browser-created block wrappers', () => {
    const editor = document.createElement('div')
    const first = document.createElement('div')
    const second = document.createElement('div')

    editor.dataset.slot = RICH_INPUT_SLOT
    first.textContent = 'first line'
    second.textContent = 'second line'
    editor.append(first, second)

    expect(composerPlainText(editor)).toBe('first line\nsecond line')
  })
})

describe('syncComposerDraft', () => {
  it('commits live editor text when tracked draft is stale', () => {
    const editor = document.createElement('div')
    const setText = vi.fn()

    editor.dataset.slot = RICH_INPUT_SLOT
    editor.textContent = '帮我查一下这个bug'

    const next = syncComposerDraft(editor, '帮我查一下这个bu', setText)

    expect(next).toBe('帮我查一下这个bug')
    expect(setText).toHaveBeenCalledTimes(1)
    expect(setText).toHaveBeenCalledWith('帮我查一下这个bug')
  })

  it('does not write when tracked draft already matches live editor text', () => {
    const editor = document.createElement('div')
    const setText = vi.fn()

    editor.dataset.slot = RICH_INPUT_SLOT
    editor.textContent = 'hello'

    expect(syncComposerDraft(editor, 'hello', setText)).toBe('hello')
    expect(setText).not.toHaveBeenCalled()
  })
})
