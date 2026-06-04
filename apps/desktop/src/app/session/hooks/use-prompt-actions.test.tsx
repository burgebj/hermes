import { act, cleanup, render, waitFor } from '@testing-library/react'
import { useEffect, useRef } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { $composerAttachments, clearComposerAttachments, type ComposerAttachment } from '@/store/composer'

import type { ClientSessionState } from '../../types'

import { usePromptActions } from './use-prompt-actions'

const INITIAL_SESSION_STATE: ClientSessionState = {
  storedSessionId: null,
  messages: [],
  branch: '',
  cwd: '',
  busy: false,
  awaitingResponse: false,
  streamId: null,
  sawAssistantPayload: false,
  pendingBranchGroup: null,
  interrupted: false
}

function fileAttachment(): ComposerAttachment {
  return {
    id: 'file:report.txt',
    kind: 'file',
    label: 'report.txt',
    path: '/Users/alice/Downloads/report.txt',
    refText: '@file:`/Users/alice/Downloads/report.txt`'
  }
}

function PromptActionsHarness({
  onReady,
  requestGateway,
  updateSessionState
}: {
  onReady: (submitText: (text: string) => Promise<boolean>) => void
  requestGateway: <T>(method: string, params?: Record<string, unknown>) => Promise<T>
  updateSessionState: (
    sessionId: string,
    updater: (state: ClientSessionState) => ClientSessionState,
    storedSessionId?: string | null
  ) => ClientSessionState
}) {
  const activeSessionIdRef = useRef<string | null>('sid')
  const busyRef = useRef(false)
  const selectedStoredSessionIdRef = useRef<string | null>(null)

  const actions = usePromptActions({
    activeSessionId: 'sid',
    activeSessionIdRef,
    busyRef,
    branchCurrentSession: vi.fn(async () => false),
    createBackendSessionForSend: vi.fn(async () => 'sid'),
    handleSkinCommand: vi.fn(() => ''),
    requestGateway,
    selectedStoredSessionIdRef,
    startFreshSessionDraft: vi.fn(),
    sttEnabled: false,
    updateSessionState
  })

  useEffect(() => {
    onReady(actions.submitText)
  }, [actions.submitText, onReady])

  return null
}

describe('usePromptActions file attachment sync', () => {
  beforeEach(() => {
    clearComposerAttachments()
    Object.defineProperty(window, 'hermesDesktop', {
      configurable: true,
      value: {
        readFileDataUrl: vi.fn(async () => 'data:text/plain;base64,aGVsbG8gd29ybGQ=')
      }
    })
  })

  afterEach(() => {
    cleanup()
    clearComposerAttachments()
    vi.restoreAllMocks()
  })

  it('submits synced file refs instead of the local desktop path', async () => {
    const calls: Array<{ method: string; params?: Record<string, unknown> }> = []
    const states = new Map<string, ClientSessionState>()
    let submitText: ((text: string) => Promise<boolean>) | null = null

    $composerAttachments.set([fileAttachment()])

    const requestGateway = vi.fn(async (method: string, params?: Record<string, unknown>) => {
      calls.push({ method, params })

      if (method === 'file.attach') {
        return {
          attached: true,
          path: '/remote/work/.hermes/desktop-attachments/report.txt',
          ref_text: '@file:.hermes/desktop-attachments/report.txt',
          uploaded: true
        }
      }

      if (method === 'prompt.submit') {
        return { status: 'streaming' }
      }

      throw new Error(`Unexpected gateway method: ${method}`)
    })

    const updateSessionState = vi.fn(
      (sessionId: string, updater: (state: ClientSessionState) => ClientSessionState) => {
        const next = updater(states.get(sessionId) ?? INITIAL_SESSION_STATE)
        states.set(sessionId, next)

        return next
      }
    )

    render(
      <PromptActionsHarness
        onReady={fn => {
          submitText = fn
        }}
        requestGateway={requestGateway}
        updateSessionState={updateSessionState}
      />
    )

    await waitFor(() => {
      expect(submitText).not.toBeNull()
    })

    await act(async () => {
      const ok = await submitText?.('convert this to epub')
      expect(ok).toBe(true)
    })

    expect(calls.map(call => call.method)).toEqual(['file.attach', 'prompt.submit'])
    expect(calls[0]?.params).toMatchObject({
      session_id: 'sid',
      path: '/Users/alice/Downloads/report.txt',
      name: 'report.txt'
    })
    expect(calls[1]?.params).toEqual({
      session_id: 'sid',
      text: '@file:.hermes/desktop-attachments/report.txt\n\nconvert this to epub'
    })
    expect(states.get('sid')?.messages.at(-1)?.attachmentRefs).toEqual([
      '@file:.hermes/desktop-attachments/report.txt'
    ])
    expect($composerAttachments.get()).toEqual([])
  })
})
