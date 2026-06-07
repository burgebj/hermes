import { cleanup, render } from '@testing-library/react'
import type { MutableRefObject } from 'react'
import { useEffect } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { ClientSessionState } from '@/app/types'
import { createClientSessionState } from '@/lib/chat-runtime'
import { $selectedStoredSessionId, setSessions } from '@/store/session'
import type { SessionInfo } from '@/types/hermes'

import { useSessionActions } from './use-session-actions'

const ensureGatewayProfile = vi.fn(async (_profile?: string | null) => undefined)
const getSessionMessages = vi.fn(async (_id: string, _profile?: string | null) => ({ messages: [] }))
const deleteSession = vi.fn(async (_id: string) => undefined)
const setSessionArchived = vi.fn(async (_id: string, _archived: boolean, _profile?: string | null) => undefined)

vi.mock('@/store/profile', async importOriginal => {
  const actual = await importOriginal()

  return {
    ...(actual as object),
    ensureGatewayProfile: (profile: string | null | undefined) => ensureGatewayProfile(profile)
  }
})

vi.mock('@/hermes', async importOriginal => {
  const actual = await importOriginal()

  return {
    ...(actual as object),
    deleteSession: (id: string) => deleteSession(id),
    getSessionMessages: (id: string, profile?: string | null) => getSessionMessages(id, profile),
    setSessionArchived: (id: string, archived: boolean, profile?: string | null) =>
      setSessionArchived(id, archived, profile)
  }
})

function sessionInfo(overrides: Partial<SessionInfo> = {}): SessionInfo {
  return {
    ended_at: null,
    id: 'session-a',
    input_tokens: 0,
    is_active: false,
    last_active: 0,
    message_count: 1,
    model: null,
    output_tokens: 0,
    preview: null,
    profile: 'default',
    source: 'tui',
    started_at: 0,
    title: null,
    tool_call_count: 0,
    ...overrides
  }
}

interface HarnessHandle {
  resumeSession: (storedSessionId: string, replaceRoute?: boolean) => Promise<void>
}

function Harness({
  onReady,
  requestGateway
}: {
  onReady: (handle: HarnessHandle) => void
  requestGateway: <T>(method: string, params?: Record<string, unknown>) => Promise<T>
}) {
  const activeSessionIdRef: MutableRefObject<string | null> = { current: null }
  const busyRef: MutableRefObject<boolean> = { current: false }
  const creatingSessionRef: MutableRefObject<boolean> = { current: false }
  const selectedStoredSessionIdRef: MutableRefObject<string | null> = { current: null }
  const sessionStateByRuntimeIdRef: MutableRefObject<Map<string, ClientSessionState>> = { current: new Map() }
  const runtimeIdByStoredSessionIdRef: MutableRefObject<Map<string, string>> = { current: new Map() }

  const actions = useSessionActions({
    activeSessionId: null,
    activeSessionIdRef,
    busyRef,
    creatingSessionRef,
    ensureSessionState: (_sessionId, storedSessionId) => createClientSessionState(storedSessionId ?? null),
    getRouteToken: () => 'route',
    navigate: vi.fn(),
    requestGateway,
    runtimeIdByStoredSessionIdRef,
    selectedStoredSessionId: null,
    selectedStoredSessionIdRef,
    sessionStateByRuntimeIdRef,
    syncSessionStateToView: vi.fn(),
    updateSessionState: (_sessionId, updater, storedSessionId) =>
      updater(createClientSessionState(storedSessionId ?? null))
  })

  const { resumeSession } = actions

  useEffect(() => {
    onReady({ resumeSession: async (id, replace) => void (await resumeSession(id, replace)) })
  }, [onReady, resumeSession])

  return null
}

describe('useSessionActions resumeSession', () => {
  beforeEach(() => {
    setSessions(() => [
      sessionInfo({ id: 'session-a', profile: 'profile-a' }),
      sessionInfo({ id: 'session-b', profile: 'profile-b' })
    ])
    ensureGatewayProfile.mockReset()
    getSessionMessages.mockReset()
    getSessionMessages.mockResolvedValue({ messages: [] })
    deleteSession.mockReset()
    setSessionArchived.mockReset()
    $selectedStoredSessionId.set(null)
  })

  afterEach(() => {
    cleanup()
    vi.restoreAllMocks()
  })

  it('ignores an older delayed resume so it cannot reselect the wrong sidebar session', async () => {
    let releaseFirstProfile: (() => void) | null = null
    ensureGatewayProfile.mockImplementation(async (profile?: string | null) => {
      if (profile === 'profile-a') {
        await new Promise<void>(resolve => {
          releaseFirstProfile = resolve
        })
      }
    })

    const requestGateway = vi.fn(async (method: string, params?: Record<string, unknown>) => {
      if (method === 'session.resume') {
        return {
          info: {},
          messages: [],
          session_id: `runtime-${params?.session_id}`
        }
      }

      return {}
    })

    let handle: HarnessHandle | null = null
    render(<Harness onReady={h => (handle = h)} requestGateway={requestGateway as never} />)

    const staleResume = handle!.resumeSession('session-a')
    await vi.waitFor(() => expect(releaseFirstProfile).toBeTruthy())

    await handle!.resumeSession('session-b')
    expect($selectedStoredSessionId.get()).toBe('session-b')

    releaseFirstProfile!()
    await staleResume

    expect($selectedStoredSessionId.get()).toBe('session-b')
    expect(requestGateway).toHaveBeenCalledWith('session.resume', expect.objectContaining({ session_id: 'session-b' }))
    expect(requestGateway).not.toHaveBeenCalledWith('session.resume', expect.objectContaining({ session_id: 'session-a' }))
  })
})
