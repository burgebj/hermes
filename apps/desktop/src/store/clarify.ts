import { atom, computed } from 'nanostores'

import { $activeSessionId } from './session'

export interface ClarifyRequest {
  requestId: string
  question: string
  choices: string[] | null
  sessionId: string | null
}

export interface ClarifyInputState {
  draft: string
  focusLocked: boolean
  scrollTop: number
  selectionEnd: number | null
  selectionStart: number | null
  typing: boolean
}

export interface ClarifyTextareaPosition {
  scrollTop: number
  selectionEnd: number
  selectionStart: number
}

// Pending clarify requests keyed by the runtime session id that raised them.
// Storing per-session (instead of one shared slot) lets a *background* session
// park its clarify request while the user is looking at a different chat, then
// resolve it once they switch over — without a second concurrent clarify
// clobbering the first. A request with no session id lands under the empty key.
const keyFor = (sessionId: string | null | undefined): string => sessionId ?? ''

export const $clarifyRequests = atom<Record<string, ClarifyRequest>>({})

// The clarify request for the currently-viewed session. The inline ClarifyTool
// only ever mounts inside the active session's transcript, so it reads this
// focus-scoped view rather than reaching into the whole map.
export const $clarifyRequest = computed(
  [$clarifyRequests, $activeSessionId],
  (requests, activeId) => requests[keyFor(activeId)] ?? null
)

// Persisted inline clarify UI state keyed by (requestId ?? question).
// Survives component remounts / assistant stream updates so the user's draft,
// scroll position, and caret selection are not lost while Hermes is streaming.
export const $clarifyInputs = atom<Record<string, ClarifyInputState>>({})

function normalizeClarifyInput(input?: Partial<ClarifyInputState>): ClarifyInputState {
  return {
    draft: input?.draft ?? '',
    focusLocked: input?.focusLocked ?? false,
    scrollTop: input?.scrollTop ?? 0,
    selectionEnd: input?.selectionEnd ?? null,
    selectionStart: input?.selectionStart ?? null,
    typing: input?.typing ?? false
  }
}

function updateClarifyInput(key: string, patch: Partial<ClarifyInputState>): void {
  const current = $clarifyInputs.get()
  const previous = normalizeClarifyInput(current[key])
  const next = { ...previous, ...patch }

  if (
    previous.draft === next.draft &&
    previous.focusLocked === next.focusLocked &&
    previous.scrollTop === next.scrollTop &&
    previous.selectionEnd === next.selectionEnd &&
    previous.selectionStart === next.selectionStart &&
    previous.typing === next.typing
  ) {
    return
  }

  $clarifyInputs.set({ ...current, [key]: next })
}

export function clarifyInputKey(requestId?: null | string, question?: string): string {
  const id = requestId?.trim()

  if (id) {
    return `request:${id}`
  }

  const normalizedQuestion = question?.trim()

  return normalizedQuestion ? `question:${normalizedQuestion}` : 'pending'
}

export function setClarifyRequest(request: ClarifyRequest): void {
  // Migrate any pending UI state keyed by question-only over to the full
  // request-id key once the id is known (the request component re-renders
  // with the id a tick after the initial tool.start from args).
  const idKey = clarifyInputKey(request.requestId, request.question)
  const questionKey = clarifyInputKey(null, request.question)
  const currentInputs = $clarifyInputs.get()
  const pendingInput = currentInputs[questionKey]

  if (idKey !== questionKey && pendingInput) {
    const { [questionKey]: _removed, ...rest } = currentInputs

    $clarifyInputs.set({ ...rest, [idKey]: currentInputs[idKey] ?? pendingInput })
  }

  $clarifyRequests.set({ ...$clarifyRequests.get(), [keyFor(request.sessionId)]: request })
}

export function clearClarifyRequest(requestId?: string, sessionId?: string | null): void {
  const requests = $clarifyRequests.get()

  // Targeted clear when the caller knows the session (the common path from the
  // inline ClarifyTool answering its own request).
  if (sessionId !== undefined) {
    const key = keyFor(sessionId)
    const current = requests[key]

    if (!current || (requestId && current.requestId !== requestId)) {
      return
    }

    // Clear persisted UI state for this request so drafts don't leak.
    clearClarifyInput(clarifyInputKey(current.requestId, current.question))
    clearClarifyInput(clarifyInputKey(null, current.question))

    const next = { ...requests }
    delete next[key]
    $clarifyRequests.set(next)

    return
  }

  // Fallback with no session hint: drop every entry matching the request id
  // (or clear all when none is given).
  const next: Record<string, ClarifyRequest> = {}
  let changed = false

  for (const [key, value] of Object.entries(requests)) {
    if (requestId && value.requestId !== requestId) {
      next[key] = value
    } else {
      changed = true
      clearClarifyInput(clarifyInputKey(value.requestId, value.question))
      clearClarifyInput(clarifyInputKey(null, value.question))
    }
  }

  if (changed) {
    $clarifyRequests.set(next)
  }
}

export function clearClarifyInput(key: string): void {
  const current = $clarifyInputs.get()

  if (!current[key]) {
    return
  }

  const { [key]: _cleared, ...rest } = current

  $clarifyInputs.set(rest)
}

export function setClarifyDraft(key: string, draft: string, position?: ClarifyTextareaPosition): void {
  updateClarifyInput(key, { draft, ...position })
}

export function setClarifyTyping(key: string, typing: boolean): void {
  updateClarifyInput(key, { typing })
}

export function setClarifyFocusLocked(key: string, focusLocked: boolean): void {
  updateClarifyInput(key, { focusLocked })
}

export function setClarifyTextareaPosition(key: string, position: ClarifyTextareaPosition): void {
  updateClarifyInput(key, position)
}
