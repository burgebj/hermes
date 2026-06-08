import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('../config/env.js', () => ({ SHOW_FPS: true }))

describe('fpsStore trackFrame', () => {
  let nowSpy: ReturnType<typeof vi.spyOn>
  let now = 0

  beforeEach(async () => {
    vi.resetModules()
    now = 1_000
    nowSpy = vi.spyOn(performance, 'now').mockImplementation(() => now)
  })

  afterEach(() => {
    nowSpy.mockRestore()
  })

  it('is defined when SHOW_FPS env is enabled', async () => {
    const mod = await import('../lib/fpsStore.js')

    expect(mod.trackFrame).toBeTypeOf('function')
  })

  it('does not update fps state on a single frame (needs >=2 samples)', async () => {
    const { $fpsState, trackFrame } = await import('../lib/fpsStore.js')
    const before = $fpsState.get()

    trackFrame!(5)

    expect($fpsState.get()).toEqual(before)
  })

  it('computes fps after two frames', async () => {
    const { $fpsState, trackFrame } = await import('../lib/fpsStore.js')

    trackFrame!(10)
    now += 1000
    trackFrame!(10)

    const state = $fpsState.get()

    expect(state.fps).toBe(1)
    expect(state.totalFrames).toBe(2)
  })

  it('rounds lastDurationMs to two decimal places', async () => {
    const { $fpsState, trackFrame } = await import('../lib/fpsStore.js')

    trackFrame!(0)
    now += 1000
    trackFrame!(7.12345)

    expect($fpsState.get().lastDurationMs).toBe(7.12)
  })

  it('rounds fps to one decimal place', async () => {
    const { $fpsState, trackFrame } = await import('../lib/fpsStore.js')

    trackFrame!(0)
    now += 333
    trackFrame!(0)

    expect($fpsState.get().fps).toBe(3)
  })

  it('caps the sliding window at 30 timestamps', async () => {
    const { $fpsState, trackFrame } = await import('../lib/fpsStore.js')

    for (let i = 0; i < 60; i++) {
      trackFrame!(0)
      now += 100
    }

    const state = $fpsState.get()

    expect(state.totalFrames).toBe(60)
    expect(state.fps).toBe(10)
  })

  it('totalFrames keeps incrementing past the window cap', async () => {
    const { $fpsState, trackFrame } = await import('../lib/fpsStore.js')

    for (let i = 0; i < 100; i++) {
      trackFrame!(0)
      now += 10
    }

    expect($fpsState.get().totalFrames).toBe(100)
  })
})

describe('fpsStore trackFrame disabled', () => {
  it('is undefined when SHOW_FPS is false', async () => {
    vi.resetModules()
    vi.doMock('../config/env.js', () => ({ SHOW_FPS: false }))

    const mod = await import('../lib/fpsStore.js')

    expect(mod.trackFrame).toBeUndefined()

    vi.doUnmock('../config/env.js')
  })
})
