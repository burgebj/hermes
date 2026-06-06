import { describe, expect, it } from 'vitest'

import { INTERPOLATION_RE, hasInterpolation } from '../protocol/interpolation.js'

const matchAll = (s: string) => s.match(new RegExp(INTERPOLATION_RE.source, INTERPOLATION_RE.flags)) ?? []

describe('INTERPOLATION_RE', () => {
  it('matches {!name}', () => {
    expect(matchAll('hello {!name}')).toEqual(['{!name}'])
  })

  it('matches multiple tokens', () => {
    expect(matchAll('{!a} mid {!b}')).toEqual(['{!a}', '{!b}'])
  })

  it('is non-greedy across adjacent tokens', () => {
    expect(matchAll('{!a}{!b}')).toEqual(['{!a}', '{!b}'])
  })

  it('captures inner identifier', () => {
    const re = new RegExp(INTERPOLATION_RE.source, INTERPOLATION_RE.flags)
    const m = re.exec('value: {!user_name}')

    expect(m?.[1]).toBe('user_name')
  })

  it('does not match without bang', () => {
    expect(matchAll('{name}')).toEqual([])
  })

  it('does not match empty body', () => {
    expect(matchAll('{!}')).toEqual([])
  })

  it('exposes the global flag', () => {
    expect(INTERPOLATION_RE.global).toBe(true)
  })
})

describe('hasInterpolation', () => {
  it('returns true when at least one token is present', () => {
    expect(hasInterpolation('hi {!name}')).toBe(true)
  })

  it('returns false for plain text', () => {
    expect(hasInterpolation('plain text')).toBe(false)
  })

  it('returns false for {!} alone', () => {
    expect(hasInterpolation('value {!}')).toBe(false)
  })

  it('returns false for {name} without bang', () => {
    expect(hasInterpolation('hi {name}')).toBe(false)
  })

  it('returns true when token is wedged between text', () => {
    expect(hasInterpolation('a{!x}b')).toBe(true)
  })
})
