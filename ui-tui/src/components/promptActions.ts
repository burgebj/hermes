export const OPTS = ['once', 'session', 'always', 'deny'] as const

export type ApprovalKey = {
  downArrow?: boolean
  escape?: boolean
  return?: boolean
  upArrow?: boolean
}

export type ApprovalAction =
  | { kind: 'choose'; choice: (typeof OPTS)[number] }
  | { kind: 'move'; delta: -1 | 1 }
  | { kind: 'noop' }

export type ClarifyKey = {
  downArrow?: boolean
  escape?: boolean
  return?: boolean
  upArrow?: boolean
}

export type ClarifyAction =
  | { kind: 'back' }
  | { kind: 'cancel' }
  | { kind: 'choose'; answer: string }
  | { kind: 'move'; delta: -1 | 1 }
  | { kind: 'startTyping' }
  | { kind: 'noop' }

/**
 * Pure key-dispatch for the approval prompt.
 */
export function approvalAction(ch: string, key: ApprovalKey, sel: number): ApprovalAction {
  if (key.escape) {
    return { kind: 'choose', choice: 'deny' }
  }

  const n = parseInt(ch, 10)

  if (n >= 1 && n <= OPTS.length) {
    return { kind: 'choose', choice: OPTS[n - 1]! }
  }

  if (key.return) {
    return { kind: 'choose', choice: OPTS[sel]! }
  }

  if (key.upArrow && sel > 0) {
    return { kind: 'move', delta: -1 }
  }

  if (key.downArrow && sel < OPTS.length - 1) {
    return { kind: 'move', delta: 1 }
  }

  return { kind: 'noop' }
}

/**
 * Pure key-dispatch for the clarify prompt.
 *
 * Free-text clarify must not depend solely on ``TextInput.onSubmit`` because
 * prompt overlays can intercept Enter before the input widget turns it into a
 * submit callback. Handling Enter/Esc here keeps the clarify flow responsive
 * even when the surrounding overlay stack changes its input ordering.
 */
export function clarifyAction(
  ch: string,
  key: ClarifyKey,
  state: {
    choices: string[]
    custom: string
    sel: number
    typing: boolean
  }
): ClarifyAction {
  const { choices, custom, sel, typing } = state

  if (key.escape) {
    return typing && choices.length ? { kind: 'back' } : { kind: 'cancel' }
  }

  if (typing || !choices.length) {
    if (key.return) {
      return { kind: 'choose', answer: custom }
    }

    return { kind: 'noop' }
  }

  if (key.upArrow && sel > 0) {
    return { kind: 'move', delta: -1 }
  }

  if (key.downArrow && sel < choices.length) {
    return { kind: 'move', delta: 1 }
  }

  if (key.return) {
    return sel === choices.length ? { kind: 'startTyping' } : { kind: 'choose', answer: choices[sel] ?? '' }
  }

  const n = parseInt(ch, 10)

  if (n >= 1 && n <= choices.length) {
    return { kind: 'choose', answer: choices[n - 1] ?? '' }
  }

  return { kind: 'noop' }
}
