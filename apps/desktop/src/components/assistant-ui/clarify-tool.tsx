'use client'

import { type ToolCallMessagePartProps } from '@assistant-ui/react'
import { useStore } from '@nanostores/react'
import {
  type FormEvent,
  type KeyboardEvent as ReactKeyboardEvent,
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState
} from 'react'

import { ToolFallback } from '@/components/assistant-ui/tool-fallback'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { useI18n } from '@/i18n'
import { triggerHaptic } from '@/lib/haptics'
import { HelpCircle, Loader2, PencilLine } from '@/lib/icons'
import { cn } from '@/lib/utils'
import {
  $clarifyInputs,
  $clarifyRequest,
  clarifyInputKey,
  type ClarifyTextareaPosition,
  clearClarifyRequest,
  setClarifyDraft,
  setClarifyFocusLocked,
  setClarifyTextareaPosition,
  setClarifyTyping
} from '@/store/clarify'
import { $gateway } from '@/store/gateway'
import { notifyError } from '@/store/notifications'

interface ClarifyArgs {
  question?: string
  choices?: string[] | null
}

function readClarifyArgs(args: unknown): ClarifyArgs {
  if (!args || typeof args !== 'object') {
    return {}
  }

  const row = args as Record<string, unknown>
  const choices = Array.isArray(row.choices) ? row.choices.filter((c): c is string => typeof c === 'string') : null

  return {
    question: typeof row.question === 'string' ? row.question : undefined,
    choices: choices && choices.length > 0 ? choices : null
  }
}

export const ClarifyTool = (props: ToolCallMessagePartProps) => {
  const isPending = props.result === undefined

  // Once Hermes records an answer, fall back to the standard tool block so
  // the past Q/A renders consistently with every other tool in the thread.
  if (!isPending) {
    return <ToolFallback {...props} />
  }

  return <ClarifyToolPending {...props} />
}

function ClarifyToolPending({ args }: ToolCallMessagePartProps) {
  const { t } = useI18n()
  const copy = t.assistant.clarify
  const request = useStore($clarifyRequest)
  const clarifyInputs = useStore($clarifyInputs)
  const gateway = useStore($gateway)
  const fromArgs = useMemo(() => readClarifyArgs(args), [args])

  const matchingRequest = useMemo(() => {
    if (!request) {
      return null
    }

    if (fromArgs.question && request.question && fromArgs.question !== request.question) {
      return null
    }

    return request
  }, [fromArgs.question, request])

  const question = fromArgs.question || matchingRequest?.question || ''

  const choices = useMemo(
    () => fromArgs.choices ?? matchingRequest?.choices ?? [],
    [fromArgs.choices, matchingRequest?.choices]
  )

  const hasChoices = choices.length > 0

  const [submitting, setSubmitting] = useState(false)
  const rootRef = useRef<HTMLDivElement | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)
  const userFocusAwayUntilRef = useRef(0)

  const inputKey = useMemo(
    () => clarifyInputKey(matchingRequest?.requestId ?? null, question),
    [matchingRequest?.requestId, question]
  )

  const clarifyInput = clarifyInputs[inputKey]
  const draft = clarifyInput?.draft ?? ''
  const focusLocked = clarifyInput?.focusLocked ?? false
  const scrollTop = clarifyInput?.scrollTop ?? 0
  const selectionEnd = clarifyInput?.selectionEnd ?? null
  const selectionStart = clarifyInput?.selectionStart ?? null
  const typing = clarifyInput?.typing ?? false
  const freeformOpen = typing || !hasChoices

  const readTextareaPosition = useCallback((textarea: HTMLTextAreaElement): ClarifyTextareaPosition => {
    return {
      scrollTop: textarea.scrollTop,
      selectionEnd: textarea.selectionEnd,
      selectionStart: textarea.selectionStart
    }
  }, [])

  const saveTextareaPosition = useCallback(() => {
    const textarea = textareaRef.current

    if (textarea) {
      setClarifyTextareaPosition(inputKey, readTextareaPosition(textarea))
    }
  }, [inputKey, readTextareaPosition])

  const focusTextareaAtSavedPosition = useCallback(() => {
    const textarea = textareaRef.current

    if (!textarea || textarea.disabled) {
      return
    }

    textarea.focus({ preventScroll: true })

    const fallbackSelection = textarea.value.length
    const nextSelectionStart = Math.min(selectionStart ?? fallbackSelection, textarea.value.length)
    const nextSelectionEnd = Math.min(selectionEnd ?? nextSelectionStart, textarea.value.length)

    textarea.setSelectionRange(nextSelectionStart, nextSelectionEnd)
    textarea.scrollTop = scrollTop
  }, [scrollTop, selectionEnd, selectionStart])

  const restoreTextareaFocus = useCallback(() => {
    if (!freeformOpen || !focusLocked || submitting) {
      return
    }

    const root = rootRef.current
    const textarea = textareaRef.current

    if (!textarea || textarea.disabled) {
      return
    }

    const active = document.activeElement

    if (active === textarea) {
      return
    }

    if (root && active instanceof Node && root.contains(active)) {
      return
    }

    if (userFocusAwayUntilRef.current > window.performance.now()) {
      return
    }

    focusTextareaAtSavedPosition()
  }, [focusLocked, focusTextareaAtSavedPosition, freeformOpen, submitting])

  useLayoutEffect(() => {
    restoreTextareaFocus()

    if (!freeformOpen || submitting) {
      return undefined
    }

    // The inline tool can be recreated while the assistant stream settles.
    // Repeat focus after browser focus restoration has finished.
    const frame = window.requestAnimationFrame(restoreTextareaFocus)
    const timeout = window.setTimeout(restoreTextareaFocus, 0)

    return () => {
      window.cancelAnimationFrame(frame)
      window.clearTimeout(timeout)
    }
  }, [freeformOpen, restoreTextareaFocus, submitting])

  useEffect(() => {
    if (!freeformOpen || submitting) {
      return undefined
    }

    const markUserFocusAway = () => {
      userFocusAwayUntilRef.current = window.performance.now() + 1000
      setClarifyFocusLocked(inputKey, false)
    }

    const handlePointerDown = (event: PointerEvent) => {
      const root = rootRef.current

      if (root && event.target instanceof Node && root.contains(event.target)) {
        return
      }

      markUserFocusAway()
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== 'Escape' && event.key !== 'Tab') {
        return
      }

      const root = rootRef.current
      const active = document.activeElement

      if (root && active instanceof Node && root.contains(active)) {
        markUserFocusAway()
      }
    }

    const handleFocusIn = () => {
      window.setTimeout(restoreTextareaFocus, 0)
    }

    window.addEventListener('pointerdown', handlePointerDown, true)
    window.addEventListener('keydown', handleKeyDown, true)
    window.addEventListener('focusin', handleFocusIn, true)

    return () => {
      window.removeEventListener('pointerdown', handlePointerDown, true)
      window.removeEventListener('keydown', handleKeyDown, true)
      window.removeEventListener('focusin', handleFocusIn, true)
    }
  }, [freeformOpen, inputKey, restoreTextareaFocus, submitting])

  // Race: tool.start fires a tick before clarify.request, so request_id
  // arrives slightly after the tool block mounts. Show the question (from
  // args) but disable submit until we have the request id from the gateway.
  const ready = Boolean(matchingRequest?.requestId)

  const respond = useCallback(
    async (answer: string) => {
      if (!ready || !matchingRequest) {
        notifyError(new Error(copy.notReady), copy.sendFailed)

        return
      }

      if (!gateway) {
        notifyError(new Error(copy.gatewayDisconnected), copy.sendFailed)

        return
      }

      setSubmitting(true)

      try {
        await gateway.request<{ ok?: boolean }>('clarify.respond', {
          request_id: matchingRequest.requestId,
          answer
        })
        triggerHaptic('submit')
        clearClarifyRequest(matchingRequest.requestId, matchingRequest.sessionId)
        // The matching tool.complete will land shortly after, swapping this
        // panel for the ToolFallback view above.
      } catch (error) {
        notifyError(error, copy.sendFailed)
        setSubmitting(false)
      }
    },
    [gateway, matchingRequest, ready]
  )

  const handleTextareaKey = useCallback(
    (event: ReactKeyboardEvent<HTMLTextAreaElement>) => {
      if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
        event.preventDefault()
        const trimmed = draft.trim()

        if (trimmed) {
          void respond(trimmed)
        }
      }
    },
    [draft, respond]
  )

  const handleSubmitFreeform = useCallback(
    (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault()
      const trimmed = draft.trim()

      if (trimmed) {
        void respond(trimmed)
      }
    },
    [draft, respond]
  )

  const handleChoiceKey = useCallback(
    (event: ReactKeyboardEvent<HTMLDivElement>) => {
      if (typing || submitting) {
        return
      }

      const numeric = Number.parseInt(event.key, 10)

      if (Number.isFinite(numeric) && numeric >= 1 && numeric <= choices.length) {
        event.preventDefault()
        void respond(choices[numeric - 1]!)
      }
    },
    [choices, respond, submitting, typing]
  )

  return (
    <div
      className={cn(
        'mb-3 mt-2 grid gap-3 rounded-xl border border-border/70 bg-card/40 px-4 py-3.5 text-sm',
        'shadow-[inset_0_1px_0_color-mix(in_srgb,var(--foreground)_3%,transparent)]'
      )}
      data-slot="clarify-inline"
      ref={rootRef}
    >
      <div className="flex items-start gap-2.5">
        <span
          aria-hidden
          className="mt-0.5 grid size-6 shrink-0 place-items-center rounded-md bg-[color-mix(in_srgb,var(--dt-primary)_14%,transparent)] text-primary ring-1 ring-inset ring-primary/15"
        >
          <HelpCircle className="size-3.5" />
        </span>
        <div className="grid flex-1 gap-0.5">
          <span className="text-[0.6875rem] font-medium uppercase tracking-wide text-muted-foreground/85">
            {copy.heading || 'Hermes is asking'}
          </span>
          <span className="whitespace-pre-wrap leading-snug text-foreground">
            {question || <em className="text-muted-foreground/70">{copy.loadingQuestion}</em>}
          </span>
        </div>
      </div>

      {!typing && hasChoices && (
        <div className="grid gap-1.5" onKeyDown={handleChoiceKey} role="group">
          {choices.map((choice, index) => (
            <button
              className={cn(
                'group/choice flex w-full items-center gap-3 rounded-lg border border-border/70 bg-background/60 px-3 py-2 text-left text-sm text-foreground/95',
                'transition-colors hover:border-border hover:bg-accent/60 disabled:cursor-not-allowed disabled:opacity-55'
              )}
              data-choice
              disabled={!ready || submitting}
              key={`${index}-${choice}`}
              onClick={() => void respond(choice)}
              type="button"
            >
              <span className="grid size-5 shrink-0 place-items-center rounded-md bg-muted text-[0.6875rem] font-mono tabular-nums text-muted-foreground group-hover/choice:bg-background">
                {index + 1}
              </span>
              <span className="flex-1 wrap-anywhere">{choice}</span>
            </button>
          ))}
          <button
            className={cn(
              'flex w-full items-center gap-3 rounded-lg border border-dashed border-border/60 bg-transparent px-3 py-2 text-left text-sm text-muted-foreground',
              'transition-colors hover:border-border hover:bg-accent/40 hover:text-foreground'
            )}
            disabled={submitting}
            onClick={() => {
              setClarifyTyping(inputKey, true)
              setClarifyFocusLocked(inputKey, true)
              window.setTimeout(focusTextareaAtSavedPosition, 0)
            }}
            type="button"
          >
            <span
              aria-hidden
              className="grid size-5 shrink-0 place-items-center rounded-md bg-muted text-muted-foreground"
            >
              <PencilLine className="size-3" />
            </span>
            <span className="flex-1">{copy.other}</span>
          </button>
        </div>
      )}

      {freeformOpen && (
        <form className="grid gap-2" onSubmit={handleSubmitFreeform}>
          <Textarea
            className="min-h-20 resize-y rounded-lg border-border/70 bg-background/60 text-sm"
            disabled={submitting}
            onBlur={event => {
              setClarifyTextareaPosition(inputKey, readTextareaPosition(event.currentTarget))
              window.setTimeout(restoreTextareaFocus, 0)
            }}
            onChange={event => setClarifyDraft(inputKey, event.target.value, readTextareaPosition(event.target))}
            onFocus={() => {
              setClarifyFocusLocked(inputKey, true)
              window.requestAnimationFrame(focusTextareaAtSavedPosition)
            }}
            onKeyDown={handleTextareaKey}
            onScroll={saveTextareaPosition}
            onSelect={saveTextareaPosition}
            placeholder={copy.placeholder}
            ref={textareaRef}
            value={draft}
          />
          <div className="flex items-center justify-between gap-2">
            <span className="text-[0.6875rem] text-muted-foreground/85">{copy.shortcut}</span>
            <div className="flex items-center gap-1.5">
              {hasChoices && (
                <Button
                  disabled={submitting}
                  onClick={() => {
                    setClarifyTyping(inputKey, false)
                    setClarifyFocusLocked(inputKey, false)
                    setClarifyDraft(inputKey, '')
                  }}
                  size="sm"
                  type="button"
                  variant="ghost"
                >
                  {copy.back}
                </Button>
              )}
              <Button
                disabled={!ready || submitting}
                onClick={() => void respond('')}
                size="sm"
                type="button"
                variant="ghost"
              >
                {copy.skip}
              </Button>
              <Button disabled={!ready || submitting || !draft.trim()} size="sm" type="submit">
                {submitting ? <Loader2 className="size-3.5 animate-spin" /> : copy.send}
              </Button>
            </div>
          </div>
        </form>
      )}

      {!typing && hasChoices && (
        <div className="flex items-center justify-between text-[0.6875rem] text-muted-foreground/85">
          <span>1–{choices.length} to pick</span>
          <button
            className="bg-transparent text-muted-foreground/85 underline-offset-4 decoration-current/20 hover:text-foreground hover:underline disabled:opacity-50"
            disabled={!ready || submitting}
            onClick={() => void respond('')}
            type="button"
          >
            {copy.skip}
          </button>
        </div>
      )}
    </div>
  )
}
