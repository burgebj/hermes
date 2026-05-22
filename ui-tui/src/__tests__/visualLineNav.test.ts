import { describe, expect, it } from 'vitest'

import {
  isOnFirstVisualLine,
  isOnLastVisualLine,
  visualLineBounds,
  visualLineNav
} from '../lib/inputMetrics.js'

describe('visualLineBounds — word-wrap-aware HOME/END (issue #22008)', () => {
  it('returns whole-string bounds for an unwrapped single line', () => {
    expect(visualLineBounds('hello world', 6, 40)).toEqual({ end: 11, start: 0 })
  })

  it('isolates the wrapped row when the cursor sits on row two', () => {
    // 'hello world' at cols=8 wraps after the space → row 0 = 'hello ' (0..6),
    // row 1 = 'world' (6..11). Cursor at offset 9 (the 'r') lives on row 1.
    expect(visualLineBounds('hello world', 9, 8)).toEqual({ end: 11, start: 6 })
  })

  it('respects logical newlines as hard row boundaries', () => {
    // 'one\ntwo' → row 0 = 'one' (0..3), row 1 = 'two' (4..7). Cursor in 'two'.
    expect(visualLineBounds('one\ntwo', 5, 40)).toEqual({ end: 7, start: 4 })
  })

  it('reports the first row when the cursor sits at offset 0', () => {
    expect(visualLineBounds('hello world', 0, 8)).toEqual({ end: 6, start: 0 })
  })

  it('clamps to last row when cursor is past the end', () => {
    expect(visualLineBounds('abcdefgh', 99, 4)).toEqual({ end: 8, start: 4 })
  })

  it('handles an empty string without throwing', () => {
    expect(visualLineBounds('', 0, 10)).toEqual({ end: 0, start: 0 })
  })
})

describe('visualLineNav — word-wrap-aware UP/DOWN (issue #22009)', () => {
  it('returns null on UP when already on the first visual row', () => {
    expect(visualLineNav('hello world', 2, 8, -1)).toBeNull()
  })

  it('returns null on DOWN when already on the last visual row', () => {
    expect(visualLineNav('hello world', 9, 8, 1)).toBeNull()
  })

  it('moves UP one visual row across a wrapped single logical line', () => {
    // 'hello world' at cols=8: row 0 = 'hello ' (col 0..5), row 1 starts at 'world'.
    // Cursor at offset 9 ('r' of world) sits at column 3 of row 1; UP → column 3 of row 0 = 'l'.
    expect(visualLineNav('hello world', 9, 8, -1)).toBe(3)
  })

  it('moves DOWN one visual row across a wrapped single logical line', () => {
    // Cursor at offset 3 ('l' of hello) on row 0; DOWN → row 1 starting at 'world'.
    // Column 3 lands on 'l' of 'world' (offset 9).
    expect(visualLineNav('hello world', 3, 8, 1)).toBe(9)
  })

  it('clamps cursor column when the destination visual row is shorter', () => {
    // 'hello world abc' at cols=8 wraps as 'hello ' / 'world ' / 'abc'.
    // Cursor at offset 8 (column 2 of row 1 'world'); DOWN → 'abc' clamped at column 2.
    expect(visualLineNav('hello world abc', 8, 8, 1)).toBe(14)
  })

  it('descends through a logical newline as a regular visual boundary', () => {
    // 'one\ntwo' at cols=40: row 0 = 'one', row 1 = 'two'. Cursor at offset 1 → DOWN to col 1 of 'two' (offset 5).
    expect(visualLineNav('one\ntwo', 1, 40, 1)).toBe(5)
  })

  it('preserves column on UP through a logical newline', () => {
    expect(visualLineNav('one\ntwo', 5, 40, -1)).toBe(1)
  })
})

describe('isOnFirstVisualLine / isOnLastVisualLine (issue #22009 — history boundary)', () => {
  it('treats a single unwrapped line as both first and last row', () => {
    expect(isOnFirstVisualLine('hello', 3, 40)).toBe(true)
    expect(isOnLastVisualLine('hello', 3, 40)).toBe(true)
  })

  it('returns false on a middle visual row of a wrapped one-liner', () => {
    // 'hello world abc def' at cols=8 wraps to 3 rows. Cursor on the middle row.
    const text = 'hello world abc def'
    const middleCursor = 8

    expect(isOnFirstVisualLine(text, middleCursor, 8)).toBe(false)
    expect(isOnLastVisualLine(text, middleCursor, 8)).toBe(false)
  })

  it('detects the first row of a multiline block', () => {
    expect(isOnFirstVisualLine('one\ntwo\nthree', 1, 40)).toBe(true)
    expect(isOnFirstVisualLine('one\ntwo\nthree', 5, 40)).toBe(false)
  })

  it('detects the last row of a multiline block', () => {
    expect(isOnLastVisualLine('one\ntwo\nthree', 11, 40)).toBe(true)
    expect(isOnLastVisualLine('one\ntwo\nthree', 1, 40)).toBe(false)
  })
})
