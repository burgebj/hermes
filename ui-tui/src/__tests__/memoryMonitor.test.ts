import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const performHeapDumpSpy = vi.fn(async () => ({ success: true }))
const evictInkCachesSpy = vi.fn()

vi.mock('../lib/memory.js', () => ({
  performHeapDump: (...args: unknown[]) => performHeapDumpSpy(...args)
}))

vi.mock('@hermes/ink', () => ({
  evictInkCaches: (...args: unknown[]) => evictInkCachesSpy(...args)
}))

const { startMemoryMonitor } = await import('../lib/memoryMonitor.js')

const GB = 1024 ** 3

const flush = async () => {
  for (let i = 0; i < 5; i++) {
    await Promise.resolve()
  }
}

describe('startMemoryMonitor level transitions', () => {
  let memUsage: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    vi.useFakeTimers()
    performHeapDumpSpy.mockClear()
    evictInkCachesSpy.mockClear()
    memUsage = vi.spyOn(process, 'memoryUsage') as never
  })

  afterEach(() => {
    vi.useRealTimers()
    memUsage.mockRestore()
  })

  const setHeap = (heapUsed: number) => {
    ;(memUsage as unknown as { mockReturnValue: (v: unknown) => void }).mockReturnValue({
      arrayBuffers: 0,
      external: 0,
      heapTotal: heapUsed,
      heapUsed,
      rss: heapUsed
    })
  }

  it('does not fire callbacks while heap stays in normal range', async () => {
    setHeap(0.5 * GB)
    const onHigh = vi.fn()
    const onCritical = vi.fn()

    const stop = startMemoryMonitor({ intervalMs: 100, onCritical, onHigh })

    await vi.advanceTimersByTimeAsync(100)
    await flush()

    expect(onHigh).not.toHaveBeenCalled()
    expect(onCritical).not.toHaveBeenCalled()
    expect(performHeapDumpSpy).not.toHaveBeenCalled()
    stop()
  })

  it('fires onHigh once when heap crosses high threshold', async () => {
    setHeap(1.6 * GB)
    const onHigh = vi.fn()

    const stop = startMemoryMonitor({ intervalMs: 100, onHigh })

    await vi.advanceTimersByTimeAsync(100)
    await flush()
    await vi.advanceTimersByTimeAsync(100)
    await flush()

    expect(onHigh).toHaveBeenCalledTimes(1)
    expect(performHeapDumpSpy).toHaveBeenCalledWith('auto-high')
    stop()
  })

  it('fires onCritical with auto-critical trigger when heap crosses critical threshold', async () => {
    setHeap(3 * GB)
    const onCritical = vi.fn()

    const stop = startMemoryMonitor({ intervalMs: 100, onCritical })

    await vi.advanceTimersByTimeAsync(100)
    await flush()

    expect(onCritical).toHaveBeenCalledTimes(1)
    expect(performHeapDumpSpy).toHaveBeenCalledWith('auto-critical')
    stop()
  })

  it('passes "all" to evictInkCaches on critical', async () => {
    setHeap(3 * GB)

    const stop = startMemoryMonitor({ intervalMs: 100, onCritical: vi.fn() })

    await vi.advanceTimersByTimeAsync(100)
    await flush()

    expect(evictInkCachesSpy).toHaveBeenCalledWith('all')
    stop()
  })

  it('snapshot passed to callback carries level + heapUsed + rss', async () => {
    setHeap(2 * GB)
    const onHigh = vi.fn()

    const stop = startMemoryMonitor({ intervalMs: 100, onHigh })

    await vi.advanceTimersByTimeAsync(100)
    await flush()

    const [snap] = onHigh.mock.calls[0] ?? []

    expect(snap).toMatchObject({ heapUsed: 2 * GB, level: 'high', rss: 2 * GB })
    stop()
  })

  it('clears dedup state when level returns to normal then refires on next high', async () => {
    setHeap(1.6 * GB)
    const onHigh = vi.fn()

    const stop = startMemoryMonitor({ intervalMs: 100, onHigh })

    await vi.advanceTimersByTimeAsync(100)
    await flush()
    expect(onHigh).toHaveBeenCalledTimes(1)

    setHeap(0.5 * GB)
    await vi.advanceTimersByTimeAsync(100)
    await flush()

    setHeap(1.6 * GB)
    await vi.advanceTimersByTimeAsync(100)
    await flush()

    expect(onHigh).toHaveBeenCalledTimes(2)
    stop()
  })

  it('respects custom thresholds', async () => {
    setHeap(50)
    const onHigh = vi.fn()

    const stop = startMemoryMonitor({ highBytes: 10, criticalBytes: 100, intervalMs: 100, onHigh })

    await vi.advanceTimersByTimeAsync(100)
    await flush()

    expect(onHigh).toHaveBeenCalledTimes(1)
    stop()
  })

  it('returns a stop function that cancels the interval', async () => {
    setHeap(3 * GB)
    const onCritical = vi.fn()

    const stop = startMemoryMonitor({ intervalMs: 100, onCritical })

    stop()

    await vi.advanceTimersByTimeAsync(500)
    await flush()

    expect(onCritical).not.toHaveBeenCalled()
  })
})
