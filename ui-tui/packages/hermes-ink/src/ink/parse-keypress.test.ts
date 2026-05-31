import { describe, expect, it } from 'vitest'

import { INITIAL_STATE, parseMultipleKeypresses } from './parse-keypress.js'
import { PASTE_END, PASTE_START } from './termio/csi.js'

describe('parseMultipleKeypresses bracketed paste recovery', () => {
  it('emits empty bracketed pastes when the terminal sends both markers', () => {
    const [keys, state] = parseMultipleKeypresses(INITIAL_STATE, PASTE_START + PASTE_END)

    expect(keys).toHaveLength(1)
    expect(keys[0]).toMatchObject({ isPasted: true, raw: '' })
    expect(state.mode).toBe('NORMAL')
  })

  it('flushes unterminated paste content back to normal input mode', () => {
    const [pendingKeys, pendingState] = parseMultipleKeypresses(INITIAL_STATE, PASTE_START + 'hello')

    expect(pendingKeys).toEqual([])
    expect(pendingState.mode).toBe('IN_PASTE')

    const [keys, state] = parseMultipleKeypresses(pendingState, null)

    expect(keys).toHaveLength(1)
    expect(keys[0]).toMatchObject({ isPasted: true, raw: 'hello' })
    expect(state.mode).toBe('NORMAL')
    expect(state.pasteBuffer).toBe('')
  })

  it('resets an empty unterminated paste start instead of staying stuck', () => {
    const [pendingKeys, pendingState] = parseMultipleKeypresses(INITIAL_STATE, PASTE_START)

    expect(pendingKeys).toEqual([])
    expect(pendingState.mode).toBe('IN_PASTE')

    const [keys, state] = parseMultipleKeypresses(pendingState, null)

    expect(keys).toEqual([])
    expect(state.mode).toBe('NORMAL')
    expect(state.pasteBuffer).toBe('')
  })
})

describe('mouse wheel modifier decoding', () => {
  // SGR mouse format: ESC [ < button ; col ; row M
  // Wheel up = 64 (0x40), wheel down = 65 (0x41).
  // Modifier bits: shift = 0x04, meta = 0x08, ctrl = 0x10.
  const sgrWheel = (button: number) => `\x1b[<${button};10;10M`

  it('plain wheel up has no modifiers', () => {
    const [[key]] = parseMultipleKeypresses(INITIAL_STATE, sgrWheel(0x40))

    expect(key).toMatchObject({ name: 'wheelup', ctrl: false, meta: false, shift: false })
  })

  it('plain wheel down has no modifiers', () => {
    const [[key]] = parseMultipleKeypresses(INITIAL_STATE, sgrWheel(0x41))

    expect(key).toMatchObject({ name: 'wheeldown', ctrl: false, meta: false, shift: false })
  })

  it('decodes meta (Alt/Option) on wheel up', () => {
    const [[key]] = parseMultipleKeypresses(INITIAL_STATE, sgrWheel(0x40 | 0x08))

    expect(key).toMatchObject({ name: 'wheelup', ctrl: false, meta: true, shift: false })
  })

  it('decodes meta (Alt/Option) on wheel down', () => {
    const [[key]] = parseMultipleKeypresses(INITIAL_STATE, sgrWheel(0x41 | 0x08))

    expect(key).toMatchObject({ name: 'wheeldown', ctrl: false, meta: true, shift: false })
  })

  it('decodes ctrl on wheel events', () => {
    const [[key]] = parseMultipleKeypresses(INITIAL_STATE, sgrWheel(0x40 | 0x10))

    expect(key).toMatchObject({ name: 'wheelup', ctrl: true, meta: false, shift: false })
  })

  it('decodes shift on wheel events', () => {
    const [[key]] = parseMultipleKeypresses(INITIAL_STATE, sgrWheel(0x41 | 0x04))

    expect(key).toMatchObject({ name: 'wheeldown', ctrl: false, meta: false, shift: true })
  })

  it('decodes combined modifiers', () => {
    const [[key]] = parseMultipleKeypresses(INITIAL_STATE, sgrWheel(0x40 | 0x08 | 0x10))

    expect(key).toMatchObject({ name: 'wheelup', ctrl: true, meta: true, shift: false })
  })

  it('decodes meta on legacy X10 wheel encoding', () => {
    // X10: ESC [ M Cb Cx Cy where each byte is value+32.
    const x10 = `\x1b[M${String.fromCharCode(0x40 + 0x08 + 32)}${String.fromCharCode(10 + 32)}${String.fromCharCode(10 + 32)}`
    const [[key]] = parseMultipleKeypresses(INITIAL_STATE, x10)

    expect(key).toMatchObject({ name: 'wheelup', meta: true })
  })
})

describe('fragmented SGR mouse recovery', () => {
  it('re-synthesizes bracket-only SGR mouse tails as mouse events', () => {
    const [[mouse]] = parseMultipleKeypresses(INITIAL_STATE, '[<35;159;11M')

    expect(mouse).toMatchObject({ kind: 'mouse', button: 35, col: 159, row: 11, action: 'press' })
  })

  it('re-synthesizes angle-only SGR mouse tails as mouse events', () => {
    const [[mouse]] = parseMultipleKeypresses(INITIAL_STATE, '<35;159;11M')

    expect(mouse).toMatchObject({ kind: 'mouse', button: 35, col: 159, row: 11, action: 'press' })
  })

  it('re-synthesizes degraded SGR mouse bursts without leaking prompt text', () => {
    const [events] = parseMultipleKeypresses(INITIAL_STATE, '5;142;11M<35;159;11M35;124;26M35;119;26Mtyped')

    expect(events.slice(0, 4)).toEqual([
      expect.objectContaining({ kind: 'mouse', button: 5, col: 142, row: 11 }),
      expect.objectContaining({ kind: 'mouse', button: 35, col: 159, row: 11 }),
      expect.objectContaining({ kind: 'mouse', button: 35, col: 124, row: 26 }),
      expect.objectContaining({ kind: 'mouse', button: 35, col: 119, row: 26 })
    ])
    expect(events[4]).toMatchObject({ kind: 'key', sequence: 'typed' })
  })

  it('keeps isolated semicolon text that only resembles a prefixless mouse report', () => {
    const [[key]] = parseMultipleKeypresses(INITIAL_STATE, 'see 1;2;3M for details')

    expect(key).toMatchObject({ kind: 'key', sequence: 'see 1;2;3M for details' })
  })

  it('does not match prefixless fragments inside longer digit runs', () => {
    const [[key]] = parseMultipleKeypresses(INITIAL_STATE, '1234;56;78M9;10;11M')

    expect(key).toMatchObject({ kind: 'key', sequence: '1234;56;78M9;10;11M' })
  })

  it('swallows a fully degraded mouse-burst noise blob without leaking prompt text', () => {
    // Captured from Windows Terminal during a heavy tool-call render: the event
    // loop blocked past App's 50ms flush timer, so a long burst of SGR mouse
    // reports (mode 1003 any-motion) arrived as text with prefixes AND
    // too degraded for SGR_MOUSE_FRAGMENT_RE (1- and 2-param remnants, a
    // stray focus-in `[I`), so without the whole-text noise fast path the entire
    // blob types into the composer and locks the user out.
    const blob =
      'M6M35;220;56M6M35;218;56M169;48M;157;47M;44M20;43M79;40M78;40M0M7M35;49;41M48;41M;47;40M9;15;32M[I;31M5;211;26M35;211;25M7M;220;1MM0M09;25M24M23M3;22MM18M99;26M32MM38M63;44M47MM1;51M M4M54M'
    const [events] = parseMultipleKeypresses(INITIAL_STATE, blob)

    expect(events).toEqual([])
  })

  it('keeps plain prose that only contains scattered M and m letters', () => {
    const [[key]] = parseMultipleKeypresses(INITIAL_STATE, 'Mmm MMM mmm yummy')

    expect(key).toMatchObject({ kind: 'key', sequence: 'Mmm MMM mmm yummy' })
  })

  it('swallows noise wholesale even when it contains intact recoverable fragments', () => {
    // A noise blob can carry a few intact `<b;c;r M` fragments amid the chewed
    // shards. The whole-text noise check must run BEFORE fragment recovery —
    // otherwise parseTextWithSgrMouseFragments returns non-null and emits a
    // pile of recovered mouse events instead of dropping the blob wholesale.
    const blob = '<35;159;11M;44M20;43M0M7M<35;124;26M;47;40M9;15;32M5M2M'
    const [events] = parseMultipleKeypresses(INITIAL_STATE, blob)

    expect(events).toEqual([])
  })
})

describe('mouse report split across the App watchdog flush', () => {
  // A heavy render on a long session blocks Node's event loop past App's 50ms
  // flush timer, splitting a mouse report: the leading ESC is flushed alone and
  // the remainder arrives as a text token on the next readable event. Without
  // recovery, the tail leaks into the prompt as the cursor moves.

  // X10 (legacy 1000/1002/1003) payload byte = value + 32. No-button motion
  // under mode 1003 is Cb=35 -> byte 'C' (0x43). tmux and other terminals that
  // honor 1000/1002 but ignore SGR 1006 emit this on every cursor move.
  const x10 = (cb: number, col: number, row: number) =>
    `[M${String.fromCharCode(cb + 32, col + 32, row + 32)}`

  it('recovers a split X10 hover report instead of leaking [MC.. into the prompt', () => {
    // Lone ESC buffered (could begin a longer sequence), then the [M tail
    // arrives as text on the next readable event. Pre-fix this leaked the full
    // "[MCxy" payload into the prompt.
    const [escKeys, afterEsc] = parseMultipleKeypresses(INITIAL_STATE, '\x1b')
    expect(escKeys).toEqual([]) // ESC is held until the next chunk resolves it

    const [tailKeys] = parseMultipleKeypresses(afterEsc, x10(35, 80, 24))
    expect(tailKeys).toHaveLength(1)
    expect(tailKeys[0]).toMatchObject({ kind: 'key', name: 'mouse' })
  })

  it('still recovers a split X10 wheel report (scroll keeps working)', () => {
    const [, afterEsc] = parseMultipleKeypresses(INITIAL_STATE, '\x1b')
    const [tailKeys] = parseMultipleKeypresses(afterEsc, x10(64, 80, 24))

    expect(tailKeys).toHaveLength(1)
    expect(tailKeys[0]).toMatchObject({ kind: 'key', name: 'wheelup' })
  })

  it('suppresses a dangling SGR mouse prefix on flush instead of leaking "["', () => {
    // ESC[ flushed by the watchdog (incomplete CSI), then the <...M tail
    // arrives as text. Pre-fix the flushed "\x1b[" leaked a bare "[".
    const [feedKeys, pending] = parseMultipleKeypresses(INITIAL_STATE, '\x1b[')
    expect(feedKeys).toEqual([])

    const [flushKeys, flushed] = parseMultipleKeypresses(pending, null)
    expect(flushKeys).toEqual([]) // the dangling "\x1b[" is dropped, not leaked

    const [tailKeys] = parseMultipleKeypresses(flushed, '<35;80;24M')
    expect(tailKeys).toEqual([expect.objectContaining({ kind: 'mouse', button: 35, col: 80, row: 24 })])
  })

  it('drops a dangling "\\x1b[<" prefix flushed by the watchdog', () => {
    const [, pending] = parseMultipleKeypresses(INITIAL_STATE, '\x1b[<')
    const [flushKeys] = parseMultipleKeypresses(pending, null)

    expect(flushKeys).toEqual([])
  })

  it('still flushes a lone ESC as the Escape key (not suppressed)', () => {
    const [, pending] = parseMultipleKeypresses(INITIAL_STATE, '\x1b')
    const [flushKeys] = parseMultipleKeypresses(pending, null)

    expect(flushKeys).toEqual([expect.objectContaining({ kind: 'key', name: 'escape' })])
  })
})
