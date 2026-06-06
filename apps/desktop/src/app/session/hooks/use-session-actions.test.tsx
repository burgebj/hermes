import { cleanup, render } from '@testing-library/react'
import type { MutableRefObject } from 'react'
import { useEffect } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { ChatMessage } from '@/lib/chat-messages'
import { ensureGatewayProfile } from '@/store/profile'
import { setMessages, setSessions } from '@/store/session'
import type { SessionInfo } from '@/types/hermes'

import { useSessionActions } from './use-session-actions'

vi.mock('@/hermes', () => ({
  deleteSession: vi.fn(async () => undefined),
  getProfiles: vi.fn(async () => ({ profiles: [] })),
  getSessionMessages: vi.fn(async () => ({ messages: [] })),
  setApiRequestProfile: vi.fn(),
  setSessionArchived: vi.fn(async () => undefined)
}))

// Spy on the gateway swap while keeping the real profile atoms/helpers (the
// hook reads $activeGatewayProfile + normalizeProfileKey for optimistic rows).
vi.mock('@/store/profile', async importOriginal => {
  const actual = await importOriginal<Record<string, unknown>>()

  return { ...actual, ensureGatewayProfile: vi.fn(async () => undefined) }
})

const ensureGatewayProfileMock = vi.mocked(ensureGatewayProfile)

// The active id the desktop holds is the *runtime* session id from
// session.create; the stored DB id is distinct (see use-prompt-actions.test).
const RUNTIME_SESSION_ID = 'rt-source'
const STORED_SESSION_ID = 'stored-source'

function sessionInfo(overrides: Partial<SessionInfo> = {}): SessionInfo {
  return {
    ended_at: null,
    id: STORED_SESSION_ID,
    input_tokens: 0,
    is_active: true,
    last_active: 0,
    message_count: 2,
    model: null,
    output_tokens: 0,
    preview: null,
    source: null,
    started_at: 0,
    title: 'Source thread',
    tool_call_count: 0,
    ...overrides
  }
}

function userMessage(text: string): ChatMessage {
  return { id: 'm1', role: 'user', parts: [{ type: 'text', text }] }
}

interface HarnessHandle {
  branchCurrentSession: (messageId?: string) => Promise<boolean>
}

function noopState() {
  return {} as never
}

function Harness({
  onReady,
  requestGateway
}: {
  onReady: (handle: HarnessHandle) => void
  requestGateway: <T>(method: string, params?: Record<string, unknown>) => Promise<T>
}) {
  const activeSessionIdRef: MutableRefObject<string | null> = { current: RUNTIME_SESSION_ID }
  const selectedStoredSessionIdRef: MutableRefObject<string | null> = { current: STORED_SESSION_ID }
  const busyRef: MutableRefObject<boolean> = { current: false }
  const creatingSessionRef: MutableRefObject<boolean> = { current: false }

  const actions = useSessionActions({
    activeSessionId: RUNTIME_SESSION_ID,
    activeSessionIdRef,
    busyRef,
    creatingSessionRef,
    ensureSessionState: noopState,
    getRouteToken: () => 'token',
    navigate: vi.fn() as never,
    requestGateway,
    runtimeIdByStoredSessionIdRef: { current: new Map() },
    selectedStoredSessionId: STORED_SESSION_ID,
    selectedStoredSessionIdRef,
    sessionStateByRuntimeIdRef: { current: new Map() },
    syncSessionStateToView: vi.fn(),
    updateSessionState: noopState
  })

  useEffect(() => {
    onReady({ branchCurrentSession: actions.branchCurrentSession })
  }, [actions.branchCurrentSession, onReady])

  return null
}

function createGatewayMock() {
  return vi.fn(async (method: string, _params?: Record<string, unknown>) =>
    (method === 'session.create'
      ? { session_id: 'rt-branch', stored_session_id: 'stored-branch', message_count: 1, messages: [] }
      : {}) as never
  )
}

describe('useSessionActions branchCurrentSession profile parity', () => {
  beforeEach(() => {
    setMessages([userMessage('hello from the work thread')])
  })

  afterEach(() => {
    cleanup()
    vi.clearAllMocks()
    setMessages([])
    setSessions(() => [])
  })

  it('carries the SOURCE session profile (not the new-chat picker) into session.create', async () => {
    // Active thread lives in `work`; the new-chat picker may point elsewhere.
    setSessions(() => [sessionInfo({ profile: 'work' })])
    const requestGateway = createGatewayMock()

    let handle: HarnessHandle | null = null
    render(<Harness onReady={h => (handle = h)} requestGateway={requestGateway} />)

    const ok = await handle!.branchCurrentSession()

    expect(ok).toBe(true)
    // Swap the live gateway onto the source profile before creating...
    expect(ensureGatewayProfileMock).toHaveBeenCalledWith('work')
    // ...and carry it on session.create so the branch builds + persists against
    // work's home/state.db (mirrors resumeSession; the #39993 invariant).
    expect(requestGateway).toHaveBeenCalledWith('session.create', expect.objectContaining({ profile: 'work' }))
  })

  it('omits the profile for a source session with none (single-profile users unaffected)', async () => {
    setSessions(() => [sessionInfo()]) // no `profile` field
    const requestGateway = createGatewayMock()

    let handle: HarnessHandle | null = null
    render(<Harness onReady={h => (handle = h)} requestGateway={requestGateway} />)

    await handle!.branchCurrentSession()

    expect(ensureGatewayProfileMock).toHaveBeenCalledWith(undefined)
    const createCall = requestGateway.mock.calls.find(([method]) => method === 'session.create')
    expect(createCall?.[1]).not.toHaveProperty('profile')
  })
})
