import { cleanup, render } from '@testing-library/react'
import type { MutableRefObject } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { ChatMessage } from '@/lib/chat-messages'

import type { ClientSessionState } from '../../types'

import { useStoredSessionRefresh } from './use-stored-session-refresh'

vi.mock('@/hermes', () => ({
  getSessionMessages: vi.fn()
}))

const { getSessionMessages } = await import('@/hermes')

interface HarnessProps {
  activeSessionIdRef: MutableRefObject<null | string>
  busyRef: MutableRefObject<boolean>
  gatewayState: string
  getStoredSessionProfile: (storedSessionId: string) => null | string | undefined
  refreshSessions: () => Promise<unknown>
  selectedStoredSessionId: null | string
  sessionStateByRuntimeIdRef: MutableRefObject<Map<string, ClientSessionState>>
  updateSessionState: (
    sessionId: string,
    updater: (state: ClientSessionState) => ClientSessionState,
    storedSessionId?: null | string
  ) => ClientSessionState | unknown
}

function Harness(props: HarnessProps) {
  useStoredSessionRefresh(props)

  return null
}

function message(id: string, role: ChatMessage['role'], text: string, extra: Partial<ChatMessage> = {}): ChatMessage {
  return {
    id,
    role,
    parts: [{ type: 'text', text }],
    ...extra
  }
}

function sessionState(overrides: Partial<ClientSessionState> = {}): ClientSessionState {
  return {
    storedSessionId: 'stored-1',
    messages: [message('1', 'user', 'old')],
    branch: '',
    cwd: '',
    busy: false,
    awaitingResponse: false,
    streamId: null,
    sawAssistantPayload: false,
    pendingBranchGroup: null,
    interrupted: false,
    needsInput: false,
    ...overrides
  }
}

function renderHarness(overrides: Partial<HarnessProps> = {}) {
  const defaultSessionMap = new Map<string, ClientSessionState>([['runtime-1', sessionState()]])
  const sessionStateByRuntimeIdRef = overrides.sessionStateByRuntimeIdRef ?? { current: defaultSessionMap }
  const sessionMap = sessionStateByRuntimeIdRef.current
  const updateSessionState: HarnessProps['updateSessionState'] = (sessionId, updater, storedSessionId) => {
    const previous = sessionMap.get(sessionId) ?? sessionState()
    const next = updater(previous)
    sessionMap.set(sessionId, next)

    return { ...next, storedSessionId: storedSessionId ?? next.storedSessionId }
  }
  const props: HarnessProps = {
    activeSessionIdRef: { current: 'runtime-1' },
    busyRef: { current: false },
    gatewayState: 'open',
    getStoredSessionProfile: vi.fn(() => 'remote-profile'),
    refreshSessions: vi.fn(async () => undefined),
    selectedStoredSessionId: 'stored-1',
    sessionStateByRuntimeIdRef,
    updateSessionState: vi.fn(updateSessionState),
    ...overrides
  }

  const view = render(<Harness {...props} />)

  return { ...view, props, sessionMap }
}

describe('useStoredSessionRefresh', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.clearAllMocks()
    vi.mocked(getSessionMessages).mockResolvedValue({
      session_id: 'stored-1',
      messages: [{ id: 1, role: 'user', content: 'old' }]
    } as never)
  })

  afterEach(() => {
    cleanup()
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('updates the open runtime session directly when polling sees a backend message change', async () => {
    vi.mocked(getSessionMessages).mockResolvedValue({
      session_id: 'stored-1',
      messages: [
        { id: 1, role: 'user', content: 'old' },
        { id: 2, role: 'assistant', content: 'new from telegram' }
      ]
    } as never)

    const { props, sessionMap } = renderHarness()

    await vi.advanceTimersByTimeAsync(5000)

    expect(getSessionMessages).toHaveBeenCalledWith('stored-1', 'remote-profile')
    expect(props.updateSessionState).toHaveBeenCalledTimes(1)
    expect(props.updateSessionState).toHaveBeenCalledWith('runtime-1', expect.any(Function), 'stored-1')
    expect(sessionMap.get('runtime-1')?.messages.at(-1)?.parts).toEqual([
      { type: 'text', text: 'new from telegram' }
    ])
    expect(props.refreshSessions).toHaveBeenCalledTimes(1)
  })

  it('does not fetch while the desktop session is busy', async () => {
    const { props } = renderHarness({ busyRef: { current: true } })

    await vi.advanceTimersByTimeAsync(5000)

    expect(getSessionMessages).not.toHaveBeenCalled()
    expect(props.updateSessionState).not.toHaveBeenCalled()
  })

  it('does not overwrite optimistic or in-flight messages if the session becomes busy after the read starts', async () => {
    let resolveLatest: (value: unknown) => void = () => undefined
    vi.mocked(getSessionMessages).mockImplementation(
      () =>
        new Promise(resolve => {
          resolveLatest = resolve
        }) as never
    )

    const { props } = renderHarness()

    await vi.advanceTimersByTimeAsync(5000)
    props.busyRef.current = true
    resolveLatest({
      session_id: 'stored-1',
      messages: [
        { id: 1, role: 'user', content: 'old' },
        { id: 2, role: 'assistant', content: 'new from telegram' }
      ]
    })
    await Promise.resolve()

    expect(props.updateSessionState).not.toHaveBeenCalled()
    expect(props.refreshSessions).not.toHaveBeenCalled()
  })

  it('preserves local assistant errors missing from the persisted snapshot', async () => {
    vi.mocked(getSessionMessages).mockResolvedValue({
      session_id: 'stored-1',
      messages: [
        { id: 1, role: 'user', content: 'old' },
        { id: 3, role: 'assistant', content: 'new from telegram' }
      ]
    } as never)

    const localError = message('local-error', 'assistant', 'Network failed', { error: 'Network failed', pending: true })
    const { sessionMap } = renderHarness({
      sessionStateByRuntimeIdRef: {
        current: new Map([['runtime-1', sessionState({ messages: [message('1', 'user', 'old'), localError] })]])
      }
    })

    await vi.advanceTimersByTimeAsync(5000)

    expect(sessionMap.get('runtime-1')?.messages.some(item => item.id === 'local-error' && item.error)).toBe(true)
  })

  it('checks for updates when the window regains focus', async () => {
    vi.mocked(getSessionMessages).mockResolvedValue({
      session_id: 'stored-1',
      messages: [
        { id: 1, role: 'user', content: 'old' },
        { id: 3, role: 'assistant', content: 'new from telegram' }
      ]
    } as never)

    const { props } = renderHarness()

    window.dispatchEvent(new Event('focus'))
    await Promise.resolve()

    expect(props.updateSessionState).toHaveBeenCalledTimes(1)
  })
})
