import { type ToolCallMessagePartProps } from '@assistant-ui/react'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import {
  $clarifyInputs,
  $clarifyRequest,
  clarifyInputKey,
  clearClarifyRequest,
  setClarifyRequest
} from '@/store/clarify'

import { ClarifyTool } from './clarify-tool'

const QUESTION = 'Which files should Hermes update?'
const CHOICES = ['Only changed files', 'All related files']

function clarifyProps(): ToolCallMessagePartProps {
  return {
    args: { choices: CHOICES, question: QUESTION },
    result: undefined,
    toolCallId: 'clarify-tool-1',
    toolName: 'clarify'
  } as ToolCallMessagePartProps
}

function setRequest(requestId = 'clarify-req-1') {
  setClarifyRequest({
    requestId,
    question: QUESTION,
    choices: CHOICES,
    sessionId: 'session-1'
  })
}

afterEach(() => {
  cleanup()
  $clarifyRequest.set(null)
  $clarifyInputs.set({})
})

describe('ClarifyTool', () => {
  it('preserves the freeform draft when the inline tool remounts', () => {
    setRequest()

    const first = render(<ClarifyTool {...clarifyProps()} />)

    fireEvent.click(screen.getByRole('button', { name: /other/i }))

    const draft = screen.getByPlaceholderText(/type your answer/i) as HTMLTextAreaElement

    fireEvent.change(draft, { target: { value: 'Use the desktop renderer files.' } })

    expect(draft.value).toBe('Use the desktop renderer files.')

    first.unmount()
    render(<ClarifyTool {...clarifyProps()} />)

    expect((screen.getByPlaceholderText(/type your answer/i) as HTMLTextAreaElement).value).toBe(
      'Use the desktop renderer files.'
    )
  })

  it('restores focus to the freeform input when the inline tool remounts while typing', async () => {
    setRequest()

    const first = render(<ClarifyTool {...clarifyProps()} />)

    fireEvent.click(screen.getByRole('button', { name: /other/i }))

    const draft = screen.getByPlaceholderText(/type your answer/i) as HTMLTextAreaElement

    fireEvent.change(draft, { target: { value: 'Keep focus here.' } })

    await waitFor(() => expect(document.activeElement).toBe(draft))

    first.unmount()
    render(<ClarifyTool {...clarifyProps()} />)

    await waitFor(() => expect(document.activeElement).toBe(screen.getByPlaceholderText(/type your answer/i)))
  })

  it('restores focus after another control is focused programmatically', async () => {
    setRequest()

    render(<ClarifyTool {...clarifyProps()} />)

    fireEvent.click(screen.getByRole('button', { name: /other/i }))
    const draft = screen.getByPlaceholderText(/type your answer/i)

    await waitFor(() => expect(document.activeElement).toBe(draft))

    const outside = document.createElement('input')
    document.body.appendChild(outside)

    outside.focus()

    await waitFor(() => expect(document.activeElement).toBe(draft))

    outside.remove()
  })

  it('does not steal focus back after the user intentionally leaves the input', async () => {
    setRequest()

    const first = render(<ClarifyTool {...clarifyProps()} />)

    fireEvent.click(screen.getByRole('button', { name: /other/i }))
    const draft = screen.getByPlaceholderText(/type your answer/i)

    await waitFor(() => expect(document.activeElement).toBe(draft))

    fireEvent.change(screen.getByPlaceholderText(/type your answer/i), {
      target: { value: 'Keep the draft, but do not force focus.' }
    })

    const outside = document.createElement('input')
    document.body.appendChild(outside)
    fireEvent.pointerDown(outside)
    outside.focus()

    first.unmount()
    render(<ClarifyTool {...clarifyProps()} />)

    expect(document.activeElement).toBe(outside)

    outside.remove()
  })

  it('restores the freeform selection and scroll position after focus returns', async () => {
    setRequest()

    const first = render(<ClarifyTool {...clarifyProps()} />)

    fireEvent.click(screen.getByRole('button', { name: /other/i }))

    const draft = screen.getByPlaceholderText(/type your answer/i) as HTMLTextAreaElement

    const longDraft = Array.from(
      { length: 18 },
      (_, index) => `Line ${index + 1}: keep the caret where the user stopped typing.`
    ).join('\n')

    fireEvent.change(draft, { target: { value: longDraft } })

    draft.setSelectionRange(longDraft.length, longDraft.length)
    draft.scrollTop = 72
    fireEvent.select(draft)
    fireEvent.scroll(draft)

    const outside = document.createElement('input')
    document.body.appendChild(outside)
    fireEvent.pointerDown(outside)
    fireEvent.blur(draft)
    outside.focus()

    first.unmount()
    render(<ClarifyTool {...clarifyProps()} />)

    const restored = screen.getByPlaceholderText(/type your answer/i) as HTMLTextAreaElement

    restored.setSelectionRange(0, 0)
    restored.scrollTop = 0
    restored.focus()

    await waitFor(() => {
      expect(restored.selectionStart).toBe(longDraft.length)
      expect(restored.selectionEnd).toBe(longDraft.length)
      expect(restored.scrollTop).toBe(72)
    })

    outside.remove()
  })

  it('clears the stored draft when the clarify request is cleared', () => {
    setRequest()

    render(<ClarifyTool {...clarifyProps()} />)

    fireEvent.click(screen.getByRole('button', { name: /other/i }))
    fireEvent.change(screen.getByPlaceholderText(/type your answer/i), {
      target: { value: 'This should not leak to the next request.' }
    })

    const key = clarifyInputKey('clarify-req-1', QUESTION)

    expect($clarifyInputs.get()[key]?.draft).toBe('This should not leak to the next request.')

    clearClarifyRequest('clarify-req-1')

    expect($clarifyInputs.get()[key]).toBeUndefined()
  })
})
