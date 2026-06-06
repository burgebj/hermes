import { describe, expect, it } from 'vitest'

import { CircularBuffer } from '../lib/circularBuffer.js'

describe('CircularBuffer', () => {
  describe('constructor', () => {
    it('rejects zero capacity', () => {
      expect(() => new CircularBuffer<number>(0)).toThrow(RangeError)
    })

    it('rejects negative capacity', () => {
      expect(() => new CircularBuffer<number>(-1)).toThrow(RangeError)
    })

    it('rejects fractional capacity', () => {
      expect(() => new CircularBuffer<number>(1.5)).toThrow(RangeError)
    })

    it('rejects NaN capacity', () => {
      expect(() => new CircularBuffer<number>(Number.NaN)).toThrow(RangeError)
    })

    it('accepts capacity of one', () => {
      const buf = new CircularBuffer<number>(1)
      buf.push(7)
      expect(buf.tail()).toEqual([7])
    })
  })

  describe('push + tail', () => {
    it('returns nothing when empty', () => {
      const buf = new CircularBuffer<string>(4)
      expect(buf.tail()).toEqual([])
    })

    it('preserves insertion order while under capacity', () => {
      const buf = new CircularBuffer<number>(4)
      buf.push(1)
      buf.push(2)
      buf.push(3)
      expect(buf.tail()).toEqual([1, 2, 3])
    })

    it('drops the oldest items once capacity is exceeded', () => {
      const buf = new CircularBuffer<number>(3)
      buf.push(1)
      buf.push(2)
      buf.push(3)
      buf.push(4)
      buf.push(5)
      expect(buf.tail()).toEqual([3, 4, 5])
    })

    it('handles many wraps without losing order', () => {
      const buf = new CircularBuffer<number>(3)
      for (let i = 1; i <= 10; i++) {
        buf.push(i)
      }
      expect(buf.tail()).toEqual([8, 9, 10])
    })
  })

  describe('tail(n)', () => {
    it('returns the last n items when buffer is full', () => {
      const buf = new CircularBuffer<number>(5)
      for (let i = 1; i <= 5; i++) {
        buf.push(i)
      }
      expect(buf.tail(2)).toEqual([4, 5])
    })

    it('clamps n above the current length', () => {
      const buf = new CircularBuffer<number>(5)
      buf.push(1)
      buf.push(2)
      expect(buf.tail(10)).toEqual([1, 2])
    })

    it('returns an empty array for n = 0', () => {
      const buf = new CircularBuffer<number>(5)
      buf.push(1)
      expect(buf.tail(0)).toEqual([])
    })

    it('treats negative n as zero', () => {
      const buf = new CircularBuffer<number>(5)
      buf.push(1)
      buf.push(2)
      expect(buf.tail(-3)).toEqual([])
    })

    it('returns last n after wrap-around', () => {
      const buf = new CircularBuffer<number>(3)
      for (let i = 1; i <= 6; i++) {
        buf.push(i)
      }
      expect(buf.tail(2)).toEqual([5, 6])
    })
  })

  describe('drain', () => {
    it('returns all items and empties the buffer', () => {
      const buf = new CircularBuffer<number>(3)
      buf.push(1)
      buf.push(2)
      buf.push(3)
      expect(buf.drain()).toEqual([1, 2, 3])
      expect(buf.tail()).toEqual([])
    })

    it('returns empty array when draining empty buffer', () => {
      const buf = new CircularBuffer<number>(3)
      expect(buf.drain()).toEqual([])
    })

    it('returns post-wrap snapshot, not raw underlying array', () => {
      const buf = new CircularBuffer<number>(3)
      for (let i = 1; i <= 5; i++) {
        buf.push(i)
      }
      expect(buf.drain()).toEqual([3, 4, 5])
    })
  })

  describe('clear', () => {
    it('resets length and head so subsequent pushes start fresh', () => {
      const buf = new CircularBuffer<number>(3)
      buf.push(1)
      buf.push(2)
      buf.clear()
      expect(buf.tail()).toEqual([])
      buf.push(9)
      expect(buf.tail()).toEqual([9])
    })
  })

  describe('returned arrays', () => {
    it('does not share storage between callers — mutating result is safe', () => {
      const buf = new CircularBuffer<number>(3)
      buf.push(1)
      buf.push(2)
      const a = buf.tail()
      a[0] = 999
      expect(buf.tail()).toEqual([1, 2])
    })
  })
})
