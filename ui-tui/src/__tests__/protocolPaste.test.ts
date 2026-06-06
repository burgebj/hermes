import { describe, expect, it } from 'vitest'

import { PASTE_SNIPPET_RE } from '../protocol/paste.js'

const matchAll = (s: string) => s.match(new RegExp(PASTE_SNIPPET_RE.source, PASTE_SNIPPET_RE.flags)) ?? []

describe('PASTE_SNIPPET_RE', () => {
  it('matches a basic [[label]] token', () => {
    expect(matchAll('hello [[file.txt]] world')).toEqual(['[[file.txt]]'])
  })

  it('matches multiple tokens on the same line', () => {
    expect(matchAll('[[a]] mid [[b]] tail [[c]]')).toEqual(['[[a]]', '[[b]]', '[[c]]'])
  })

  it('is non-greedy across adjacent tokens', () => {
    expect(matchAll('[[a]][[b]]')).toEqual(['[[a]]', '[[b]]'])
  })

  it('matches empty token [[]]', () => {
    expect(matchAll('x [[]] y')).toEqual(['[[]]'])
  })

  it('does not span newlines', () => {
    expect(matchAll('[[broken\nlabel]]')).toEqual([])
  })

  it('returns empty array when no token present', () => {
    expect(matchAll('plain text without snippets')).toEqual([])
  })

  it('matches across multiple lines independently', () => {
    expect(matchAll('line1 [[a]]\nline2 [[b]]')).toEqual(['[[a]]', '[[b]]'])
  })

  it('exposes the global flag', () => {
    expect(PASTE_SNIPPET_RE.global).toBe(true)
  })

  it('allows internal characters except newline', () => {
    expect(matchAll('[[file with spaces & symbols! @1]]')).toEqual(['[[file with spaces & symbols! @1]]'])
  })

  it('replace() round-trip strips all tokens', () => {
    const out = '[[a]] keep [[b]]'.replace(new RegExp(PASTE_SNIPPET_RE.source, PASTE_SNIPPET_RE.flags), '')

    expect(out).toBe(' keep ')
  })
})
