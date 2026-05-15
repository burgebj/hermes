import { describe, expect, it, vi } from 'vitest'

import { applyVoiceRecordResponse, popInputBufOnEmptyBackspace } from '../app/useInputHandlers.js'

describe('applyVoiceRecordResponse', () => {
  it('reverts optimistic REC state when the gateway reports voice busy', () => {
    const setProcessing = vi.fn()
    const setRecording = vi.fn()
    const sys = vi.fn()

    applyVoiceRecordResponse({ status: 'busy' }, true, { setProcessing, setRecording }, sys)

    expect(setRecording).toHaveBeenCalledWith(false)
    expect(setProcessing).toHaveBeenCalledWith(true)
    expect(sys).toHaveBeenCalledWith('voice: still transcribing; try again shortly')
  })

  it('keeps optimistic REC state for successful recording starts', () => {
    const setProcessing = vi.fn()
    const setRecording = vi.fn()

    applyVoiceRecordResponse({ status: 'recording' }, true, { setProcessing, setRecording }, vi.fn())

    expect(setRecording).not.toHaveBeenCalled()
    expect(setProcessing).not.toHaveBeenCalled()
  })

  it('reverts optimistic REC state when the gateway returns null', () => {
    const setProcessing = vi.fn()
    const setRecording = vi.fn()

    applyVoiceRecordResponse(null, true, { setProcessing, setRecording }, vi.fn())

    expect(setRecording).toHaveBeenCalledWith(false)
    expect(setProcessing).toHaveBeenCalledWith(false)
  })
})

describe('popInputBufOnEmptyBackspace', () => {
  it('returns null when the input is non-empty (textInput owns its own backspace)', () => {
    expect(popInputBufOnEmptyBackspace('hello', ['line1'])).toBeNull()
  })

  it('returns null when the input is empty but the buffer is empty too', () => {
    expect(popInputBufOnEmptyBackspace('', [])).toBeNull()
  })

  it('restores the last buffered line into the input and pops it from the buffer', () => {
    expect(popInputBufOnEmptyBackspace('', ['77', '88'])).toEqual({
      input: '88',
      inputBuf: ['77']
    })
  })

  it('handles a single-line buffer by emptying the buffer and restoring that line', () => {
    expect(popInputBufOnEmptyBackspace('', ['only line'])).toEqual({
      input: 'only line',
      inputBuf: []
    })
  })

  it('preserves earlier buffered lines when popping the most recent one', () => {
    expect(popInputBufOnEmptyBackspace('', ['a', 'b', 'c'])).toEqual({
      input: 'c',
      inputBuf: ['a', 'b']
    })
  })

  it('preserves an empty-string buffered line as the restored value', () => {
    expect(popInputBufOnEmptyBackspace('', ['first', ''])).toEqual({
      input: '',
      inputBuf: ['first']
    })
  })

  it('does not mutate the input buffer array', () => {
    const buf = ['a', 'b']

    popInputBufOnEmptyBackspace('', buf)

    expect(buf).toEqual(['a', 'b'])
  })
})
