import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

type Handler = (...args: unknown[]) => void

describe('setupGracefulExit', () => {
  let handlers: Map<string, Handler[]>
  let onSpy: ReturnType<typeof vi.spyOn>
  let exitSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    vi.resetModules()
    vi.useFakeTimers()
    handlers = new Map()
    onSpy = vi.spyOn(process, 'on').mockImplementation((event: string, h: Handler) => {
      const list = handlers.get(event) ?? []

      list.push(h)
      handlers.set(event, list)

      return process
    }) as never
    exitSpy = vi.spyOn(process, 'exit').mockImplementation(((_code?: number) => undefined) as never) as never
  })

  afterEach(() => {
    onSpy.mockRestore()
    exitSpy.mockRestore()
    vi.useRealTimers()
  })

  const fire = (event: string, ...args: unknown[]) => {
    for (const h of handlers.get(event) ?? []) {
      h(...args)
    }
  }

  it('registers handlers for SIGINT, SIGTERM, SIGHUP, uncaughtException, unhandledRejection', async () => {
    const { setupGracefulExit } = await import('../lib/gracefulExit.js')

    setupGracefulExit()

    expect(handlers.has('SIGINT')).toBe(true)
    expect(handlers.has('SIGTERM')).toBe(true)
    expect(handlers.has('SIGHUP')).toBe(true)
    expect(handlers.has('uncaughtException')).toBe(true)
    expect(handlers.has('unhandledRejection')).toBe(true)
  })

  it('SIGINT exits with code 130 and calls onSignal', async () => {
    const { setupGracefulExit } = await import('../lib/gracefulExit.js')
    const onSignal = vi.fn()

    setupGracefulExit({ onSignal })
    fire('SIGINT')

    expect(onSignal).toHaveBeenCalledWith('SIGINT')

    await vi.runAllTimersAsync()
    expect(exitSpy).toHaveBeenCalledWith(130)
  })

  it('SIGTERM exits with code 143', async () => {
    const { setupGracefulExit } = await import('../lib/gracefulExit.js')

    setupGracefulExit()
    fire('SIGTERM')
    await vi.runAllTimersAsync()

    expect(exitSpy).toHaveBeenCalledWith(143)
  })

  it('SIGHUP exits with code 129', async () => {
    const { setupGracefulExit } = await import('../lib/gracefulExit.js')

    setupGracefulExit()
    fire('SIGHUP')
    await vi.runAllTimersAsync()

    expect(exitSpy).toHaveBeenCalledWith(129)
  })

  it('runs all cleanup functions before exit', async () => {
    const { setupGracefulExit } = await import('../lib/gracefulExit.js')
    const a = vi.fn(async () => {})
    const b = vi.fn(() => {})

    setupGracefulExit({ cleanups: [a, b] })
    fire('SIGINT')
    await vi.runAllTimersAsync()

    expect(a).toHaveBeenCalledTimes(1)
    expect(b).toHaveBeenCalledTimes(1)
  })

  it('still exits when a cleanup rejects', async () => {
    const { setupGracefulExit } = await import('../lib/gracefulExit.js')
    const failing = vi.fn(async () => {
      throw new Error('boom')
    })

    setupGracefulExit({ cleanups: [failing] })
    fire('SIGINT')
    await vi.runAllTimersAsync()

    expect(failing).toHaveBeenCalled()
    expect(exitSpy).toHaveBeenCalledWith(130)
  })

  it('failsafe timer fires process.exit after failsafeMs', async () => {
    const { setupGracefulExit } = await import('../lib/gracefulExit.js')

    setupGracefulExit({ cleanups: [], failsafeMs: 1000 })
    fire('SIGTERM')

    vi.advanceTimersByTime(1000)
    expect(exitSpy).toHaveBeenCalledWith(143)
  })

  it('second signal during shutdown is a no-op', async () => {
    const { setupGracefulExit } = await import('../lib/gracefulExit.js')
    const onSignal = vi.fn()

    setupGracefulExit({ onSignal })
    fire('SIGINT')
    fire('SIGTERM')

    expect(onSignal).toHaveBeenCalledTimes(1)
    expect(onSignal).toHaveBeenCalledWith('SIGINT')
  })

  it('routes uncaughtException + unhandledRejection to onError', async () => {
    const { setupGracefulExit } = await import('../lib/gracefulExit.js')
    const onError = vi.fn()

    setupGracefulExit({ onError })
    fire('uncaughtException', new Error('uncaught'))
    fire('unhandledRejection', 'rejection-reason')

    expect(onError).toHaveBeenNthCalledWith(1, 'uncaughtException', expect.any(Error))
    expect(onError).toHaveBeenNthCalledWith(2, 'unhandledRejection', 'rejection-reason')
  })

  it('second setupGracefulExit call within the same module instance is a no-op', async () => {
    const { setupGracefulExit } = await import('../lib/gracefulExit.js')

    setupGracefulExit()
    onSpy.mockClear()

    setupGracefulExit()

    expect(onSpy).not.toHaveBeenCalled()
  })
})
