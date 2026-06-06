import { EventEmitter } from 'node:events'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const spawnSpy = vi.fn()

vi.mock('node:child_process', () => ({
  spawn: (...args: unknown[]) => spawnSpy(...args)
}))

const { launchHermesCommand } = await import('../lib/externalCli.js')

class FakeChild extends EventEmitter {}

describe('launchHermesCommand', () => {
  let originalBin: string | undefined

  beforeEach(() => {
    originalBin = process.env.HERMES_BIN
    delete process.env.HERMES_BIN
    spawnSpy.mockReset()
  })

  afterEach(() => {
    if (originalBin === undefined) {
      delete process.env.HERMES_BIN
    } else {
      process.env.HERMES_BIN = originalBin
    }
  })

  it('spawns the default hermes binary with stdio inherit', async () => {
    const child = new FakeChild()

    spawnSpy.mockReturnValue(child)

    const promise = launchHermesCommand(['setup'])

    child.emit('exit', 0)

    await promise

    expect(spawnSpy).toHaveBeenCalledWith('hermes', ['setup'], { stdio: 'inherit' })
  })

  it('honors HERMES_BIN env override', async () => {
    process.env.HERMES_BIN = '/opt/hermes/bin/hermes'

    const child = new FakeChild()

    spawnSpy.mockReturnValue(child)

    const promise = launchHermesCommand([])

    child.emit('exit', 0)

    await promise

    expect(spawnSpy.mock.calls[0]?.[0]).toBe('/opt/hermes/bin/hermes')
  })

  it('trims whitespace from HERMES_BIN', async () => {
    process.env.HERMES_BIN = '  /usr/local/bin/hermes  '

    const child = new FakeChild()

    spawnSpy.mockReturnValue(child)

    const promise = launchHermesCommand([])

    child.emit('exit', 0)

    await promise

    expect(spawnSpy.mock.calls[0]?.[0]).toBe('/usr/local/bin/hermes')
  })

  it('falls back to default when HERMES_BIN is empty/whitespace', async () => {
    process.env.HERMES_BIN = '   '

    const child = new FakeChild()

    spawnSpy.mockReturnValue(child)

    const promise = launchHermesCommand([])

    child.emit('exit', 0)

    await promise

    expect(spawnSpy.mock.calls[0]?.[0]).toBe('hermes')
  })

  it('resolves with exit code 0 on clean exit', async () => {
    const child = new FakeChild()

    spawnSpy.mockReturnValue(child)

    const promise = launchHermesCommand([])

    child.emit('exit', 0)

    await expect(promise).resolves.toEqual({ code: 0 })
  })

  it('resolves with non-zero exit code', async () => {
    const child = new FakeChild()

    spawnSpy.mockReturnValue(child)

    const promise = launchHermesCommand([])

    child.emit('exit', 2)

    await expect(promise).resolves.toEqual({ code: 2 })
  })

  it('resolves with {code: null, error} on spawn error event', async () => {
    const child = new FakeChild()

    spawnSpy.mockReturnValue(child)

    const promise = launchHermesCommand([])

    child.emit('error', new Error('ENOENT'))

    await expect(promise).resolves.toEqual({ code: null, error: 'ENOENT' })
  })

  it('passes args through unchanged', async () => {
    const child = new FakeChild()

    spawnSpy.mockReturnValue(child)

    const promise = launchHermesCommand(['setup', '--force', '--verbose'])

    child.emit('exit', 0)

    await promise

    expect(spawnSpy.mock.calls[0]?.[1]).toEqual(['setup', '--force', '--verbose'])
  })
})
