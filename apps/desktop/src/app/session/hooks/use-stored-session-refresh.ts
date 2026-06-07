import { type MutableRefObject, useCallback, useEffect, useRef } from 'react'

import { getSessionMessages as fetchSessionMessages } from '@/hermes'
import {
  type ChatMessage,
  chatMessageText,
  preserveLocalAssistantErrors,
  toChatMessages
} from '@/lib/chat-messages'
import type { SessionMessage, SessionMessagesResponse } from '@/types/hermes'

import type { ClientSessionState } from '../../types'

const STORED_SESSION_REFRESH_INTERVAL_MS = 5000

interface StoredSessionRefreshOptions {
  activeSessionIdRef: MutableRefObject<null | string>
  busyRef: MutableRefObject<boolean>
  gatewayState: string
  getSessionMessages?: (storedSessionId: string, profile?: null | string) => Promise<SessionMessagesResponse>
  getStoredSessionProfile?: (storedSessionId: string) => null | string | undefined
  refreshSessions: () => Promise<unknown>
  selectedStoredSessionId: null | string
  sessionStateByRuntimeIdRef: MutableRefObject<Map<string, ClientSessionState>>
  updateSessionState: (
    sessionId: string,
    updater: (state: ClientSessionState) => ClientSessionState,
    storedSessionId?: null | string
  ) => ClientSessionState | unknown
}

function safeContent(value: unknown): string {
  if (typeof value === 'string') {
    return value
  }

  if (value === null || value === undefined) {
    return ''
  }

  try {
    return JSON.stringify(value)
  } catch {
    return String(value)
  }
}

export function sessionMessageRevision(messages: readonly SessionMessage[]): string {
  const last = messages.at(-1)

  if (!last) {
    return '0'
  }

  return [messages.length, last.role, last.timestamp ?? '', safeContent(last.content ?? last.text)].join(':')
}

export function chatMessageRevision(messages: readonly ChatMessage[]): string {
  const last = messages.at(-1)

  if (!last) {
    return '0'
  }

  return [messages.length, last.role, last.timestamp ?? '', chatMessageText(last)].join(':')
}

function runtimeIsBusy(state: ClientSessionState | undefined, busyRef: MutableRefObject<boolean>): boolean {
  return Boolean(busyRef.current || state?.busy || state?.awaitingResponse)
}

export function useStoredSessionRefresh({
  activeSessionIdRef,
  busyRef,
  gatewayState,
  getSessionMessages = fetchSessionMessages,
  getStoredSessionProfile,
  refreshSessions,
  selectedStoredSessionId,
  sessionStateByRuntimeIdRef,
  updateSessionState
}: StoredSessionRefreshOptions) {
  const checkingRef = useRef(false)
  const lastRemoteRevisionRef = useRef(new Map<string, string>())

  useEffect(() => {
    if (selectedStoredSessionId) {
      lastRemoteRevisionRef.current.delete(selectedStoredSessionId)
    }
  }, [selectedStoredSessionId])

  const checkForExternalUpdates = useCallback(async () => {
    const runtimeSessionId = activeSessionIdRef.current

    if (gatewayState !== 'open' || !runtimeSessionId || !selectedStoredSessionId || checkingRef.current) {
      return
    }

    const stateBeforeRead = sessionStateByRuntimeIdRef.current.get(runtimeSessionId)

    if (runtimeIsBusy(stateBeforeRead, busyRef)) {
      return
    }

    checkingRef.current = true

    try {
      const profile = getStoredSessionProfile?.(selectedStoredSessionId) ?? undefined
      const latest = await getSessionMessages(selectedStoredSessionId, profile)
      const stateAfterRead = sessionStateByRuntimeIdRef.current.get(runtimeSessionId)

      // A poll may start while idle and resolve after the user submits a prompt.
      // Re-check after the async read so we never replace optimistic/in-flight
      // Desktop messages with a stale persisted snapshot.
      if (runtimeIsBusy(stateAfterRead, busyRef)) {
        return
      }

      const remoteRevision = sessionMessageRevision(latest.messages)
      const localRevision = stateAfterRead ? chatMessageRevision(stateAfterRead.messages) : null
      const previousRemoteRevision = lastRemoteRevisionRef.current.get(selectedStoredSessionId)
      const firstSeen = previousRemoteRevision === undefined

      lastRemoteRevisionRef.current.set(selectedStoredSessionId, remoteRevision)

      if (firstSeen ? localRevision === remoteRevision : previousRemoteRevision === remoteRevision) {
        return
      }

      updateSessionState(
        runtimeSessionId,
        current => {
          if (current.busy || current.awaitingResponse) {
            return current
          }

          return {
            ...current,
            messages: preserveLocalAssistantErrors(toChatMessages(latest.messages), current.messages)
          }
        },
        selectedStoredSessionId
      )
      await refreshSessions().catch(() => undefined)
    } catch {
      // Best-effort cross-surface refresh. Stale session UI is better than
      // interrupting the local Desktop workflow when the backend is transiently
      // unavailable.
    } finally {
      checkingRef.current = false
    }
  }, [
    activeSessionIdRef,
    busyRef,
    gatewayState,
    getSessionMessages,
    getStoredSessionProfile,
    refreshSessions,
    selectedStoredSessionId,
    sessionStateByRuntimeIdRef,
    updateSessionState
  ])

  useEffect(() => {
    if (gatewayState !== 'open' || !selectedStoredSessionId) {
      return undefined
    }

    const intervalId = window.setInterval(() => {
      void checkForExternalUpdates()
    }, STORED_SESSION_REFRESH_INTERVAL_MS)

    const onFocus = () => {
      void checkForExternalUpdates()
    }

    const onVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        void checkForExternalUpdates()
      }
    }

    window.addEventListener('focus', onFocus)
    document.addEventListener('visibilitychange', onVisibilityChange)

    return () => {
      window.clearInterval(intervalId)
      window.removeEventListener('focus', onFocus)
      document.removeEventListener('visibilitychange', onVisibilityChange)
    }
  }, [checkForExternalUpdates, gatewayState, selectedStoredSessionId])
}
