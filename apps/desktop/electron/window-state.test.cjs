/**
 * Tests for electron/window-state.cjs.
 *
 * Run with: node --test electron/window-state.test.cjs
 * (Wired into npm test:desktop:platforms in package.json.)
 *
 * Covers the pure validation logic behind window size/position restore:
 * sanitizing persisted state, off-screen detection across displays, and the
 * resulting BrowserWindow options (including the off-screen fallback).
 */

const test = require('node:test')
const assert = require('node:assert/strict')

const {
  DEFAULT_WIDTH,
  DEFAULT_HEIGHT,
  MIN_WIDTH,
  MIN_HEIGHT,
  sanitizeWindowState,
  boundsVisibleOnDisplays,
  largestWorkArea,
  computeWindowOptions,
  createTrailingDebounce
} = require('./window-state.cjs')

// A typical single 1920x1080 monitor (work area trimmed for the taskbar).
const PRIMARY = [{ workArea: { x: 0, y: 0, width: 1920, height: 1040 } }]

// A smaller laptop panel, e.g. after a larger external monitor was unplugged.
const LAPTOP = [{ workArea: { x: 0, y: 0, width: 1366, height: 728 } }]

// --- sanitizeWindowState ---

test('sanitizeWindowState returns null for missing/garbage input', () => {
  assert.equal(sanitizeWindowState(null), null)
  assert.equal(sanitizeWindowState(undefined), null)
  assert.equal(sanitizeWindowState('nope'), null)
  assert.equal(sanitizeWindowState(42), null)
  assert.equal(sanitizeWindowState({}), null)
  assert.equal(sanitizeWindowState({ width: 'wide', height: 800 }), null)
  assert.equal(sanitizeWindowState({ width: NaN, height: 800 }), null)
  assert.equal(sanitizeWindowState({ width: 1000 }), null) // height missing
})

test('sanitizeWindowState keeps a valid full state', () => {
  assert.deepEqual(sanitizeWindowState({ x: 100, y: 50, width: 1400, height: 900, isMaximized: true }), {
    x: 100,
    y: 50,
    width: 1400,
    height: 900,
    isMaximized: true
  })
})

test('sanitizeWindowState clamps width/height to the minimums', () => {
  const state = sanitizeWindowState({ width: 10, height: 10 })
  assert.equal(state.width, MIN_WIDTH)
  assert.equal(state.height, MIN_HEIGHT)
})

test('sanitizeWindowState rounds fractional bounds (HiDPI scaling)', () => {
  assert.deepEqual(sanitizeWindowState({ x: 100.6, y: 50.2, width: 1400.4, height: 900.7 }), {
    x: 101,
    y: 50,
    width: 1400,
    height: 901,
    isMaximized: false
  })
})

test('sanitizeWindowState drops a partial position but keeps the size', () => {
  const state = sanitizeWindowState({ x: 100, width: 1400, height: 900 })
  assert.equal(state.x, undefined)
  assert.equal(state.y, undefined)
  assert.equal(state.width, 1400)
})

test('sanitizeWindowState defaults isMaximized to false', () => {
  assert.equal(sanitizeWindowState({ width: 1400, height: 900 }).isMaximized, false)
  assert.equal(sanitizeWindowState({ width: 1400, height: 900, isMaximized: 'yes' }).isMaximized, false)
})

// --- boundsVisibleOnDisplays ---

test('boundsVisibleOnDisplays accepts a window fully on the primary display', () => {
  assert.equal(boundsVisibleOnDisplays({ x: 100, y: 100, width: 1220, height: 800 }, PRIMARY), true)
})

test('boundsVisibleOnDisplays rejects a window past the right edge (unplugged monitor)', () => {
  assert.equal(boundsVisibleOnDisplays({ x: 3000, y: 100, width: 1220, height: 800 }, PRIMARY), false)
})

test('boundsVisibleOnDisplays rejects a window above the top edge', () => {
  assert.equal(boundsVisibleOnDisplays({ x: 100, y: -900, width: 1220, height: 800 }, PRIMARY), false)
})

test('boundsVisibleOnDisplays accepts a window on a secondary display', () => {
  const displays = [
    { workArea: { x: 0, y: 0, width: 1920, height: 1040 } },
    { workArea: { x: 1920, y: 0, width: 2560, height: 1400 } }
  ]
  assert.equal(boundsVisibleOnDisplays({ x: 2200, y: 200, width: 1220, height: 800 }, displays), true)
})

test('boundsVisibleOnDisplays rejects a sliver of overlap below the threshold', () => {
  // Only ~10px peeking onto the primary display from the right.
  assert.equal(boundsVisibleOnDisplays({ x: 1910, y: 100, width: 1220, height: 800 }, PRIMARY), false)
})

test('boundsVisibleOnDisplays returns false with no displays or bad bounds', () => {
  assert.equal(boundsVisibleOnDisplays({ x: 0, y: 0, width: 1220, height: 800 }, []), false)
  assert.equal(boundsVisibleOnDisplays(null, PRIMARY), false)
  assert.equal(boundsVisibleOnDisplays({ x: 'a', y: 0, width: 1220, height: 800 }, PRIMARY), false)
})

// --- computeWindowOptions ---

test('computeWindowOptions falls back to defaults when there is no saved state', () => {
  assert.deepEqual(computeWindowOptions(null, PRIMARY), {
    width: DEFAULT_WIDTH,
    height: DEFAULT_HEIGHT
  })
})

test('computeWindowOptions restores an on-screen saved position', () => {
  const saved = sanitizeWindowState({ x: 200, y: 150, width: 1400, height: 900 })
  assert.deepEqual(computeWindowOptions(saved, PRIMARY), {
    width: 1400,
    height: 900,
    x: 200,
    y: 150
  })
})

test('computeWindowOptions keeps the size but drops an off-screen position', () => {
  const saved = sanitizeWindowState({ x: 5000, y: 150, width: 1400, height: 900 })
  const opts = computeWindowOptions(saved, PRIMARY)
  assert.equal(opts.width, 1400)
  assert.equal(opts.height, 900)
  assert.equal(opts.x, undefined) // off-screen → Electron centers instead
  assert.equal(opts.y, undefined)
})

test('computeWindowOptions restores size when only a size was saved (no position)', () => {
  const saved = sanitizeWindowState({ width: 1400, height: 900 })
  assert.deepEqual(computeWindowOptions(saved, PRIMARY), { width: 1400, height: 900 })
})

// --- largestWorkArea ---

test('largestWorkArea picks the max width and height across displays', () => {
  const displays = [
    { workArea: { x: 0, y: 0, width: 1366, height: 728 } },
    { workArea: { x: 1366, y: 0, width: 2560, height: 1400 } }
  ]
  assert.deepEqual(largestWorkArea(displays), { width: 2560, height: 1400 })
})

test('largestWorkArea returns null for no displays or garbage work areas', () => {
  assert.equal(largestWorkArea([]), null)
  assert.equal(largestWorkArea(null), null)
  assert.equal(largestWorkArea([{ workArea: { width: NaN, height: 10 } }]), null)
})

// --- computeWindowOptions size clamping ---

test('computeWindowOptions clamps a size larger than the only display', () => {
  // Saved on a 2560x1440 monitor that is no longer connected; only a 1366x728
  // laptop panel remains. The window must not open wider/taller than it.
  const saved = sanitizeWindowState({ width: 2560, height: 1440 })
  const opts = computeWindowOptions(saved, LAPTOP)
  assert.equal(opts.width, 1366)
  assert.equal(opts.height, 728)
})

test('computeWindowOptions leaves a size that fits the display untouched', () => {
  const saved = sanitizeWindowState({ width: 1200, height: 800 })
  assert.deepEqual(computeWindowOptions(saved, PRIMARY), { width: 1200, height: 800 })
})

test('computeWindowOptions keeps the MIN floor even on a sub-minimum display', () => {
  const tiny = [{ workArea: { x: 0, y: 0, width: 800, height: 600 } }]
  const saved = sanitizeWindowState({ width: 2000, height: 1500 })
  const opts = computeWindowOptions(saved, tiny)
  // Floor wins over a display smaller than the usable minimum.
  assert.equal(opts.width, MIN_WIDTH)
  assert.equal(opts.height, MIN_HEIGHT)
})

test('computeWindowOptions does not clamp when displays are unknown', () => {
  const saved = sanitizeWindowState({ width: 2560, height: 1440 })
  // No display info → cannot cap; preserve the saved size rather than guess.
  assert.deepEqual(computeWindowOptions(saved, []), { width: 2560, height: 1440 })
})

// --- createTrailingDebounce ---

test('createTrailingDebounce coalesces rapid calls into a single trailing run', (t) => {
  t.mock.timers.enable({ apis: ['setTimeout'] })
  let calls = 0
  const debounced = createTrailingDebounce(() => { calls += 1 }, 250)

  debounced()
  debounced()
  debounced()
  assert.equal(calls, 0)

  t.mock.timers.tick(249)
  assert.equal(calls, 0)
  t.mock.timers.tick(1)
  assert.equal(calls, 1)
})

test('createTrailingDebounce.flush runs immediately and cancels the pending run', (t) => {
  t.mock.timers.enable({ apis: ['setTimeout'] })
  let calls = 0
  const debounced = createTrailingDebounce(() => { calls += 1 }, 250)

  debounced()
  debounced.flush()
  assert.equal(calls, 1)

  t.mock.timers.tick(1000)
  assert.equal(calls, 1) // pending timer was cancelled by flush
})

test('createTrailingDebounce.cancel drops a pending run', (t) => {
  t.mock.timers.enable({ apis: ['setTimeout'] })
  let calls = 0
  const debounced = createTrailingDebounce(() => { calls += 1 }, 250)

  debounced()
  debounced.cancel()
  t.mock.timers.tick(1000)
  assert.equal(calls, 0)
})
