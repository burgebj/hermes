const assert = require('node:assert/strict')
const fs = require('node:fs')
const os = require('node:os')
const path = require('node:path')
const { EventEmitter } = require('node:events')
const test = require('node:test')

const { isRunnableUpdaterBinary, waitForUpdaterSpawn } = require('./updater-handoff.cjs')

function withTempDir(fn) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'hermes-updater-handoff-'))
  try {
    return fn(dir)
  } finally {
    fs.rmSync(dir, { recursive: true, force: true })
  }
}

test('isRunnableUpdaterBinary rejects missing paths and directories', () => {
  withTempDir(dir => {
    assert.equal(isRunnableUpdaterBinary(path.join(dir, 'missing'), { isWindows: false }), false)
    assert.equal(isRunnableUpdaterBinary(dir, { isWindows: false }), false)
  })
})

test('isRunnableUpdaterBinary requires executable bit on POSIX', () => {
  withTempDir(dir => {
    const file = path.join(dir, 'hermes-setup')
    fs.writeFileSync(file, '#!/bin/sh\nexit 0\n', { mode: 0o644 })

    assert.equal(isRunnableUpdaterBinary(file, { isWindows: false }), false)

    fs.chmodSync(file, 0o755)
    assert.equal(isRunnableUpdaterBinary(file, { isWindows: false }), true)
  })
})

test('isRunnableUpdaterBinary accepts existing files on Windows', () => {
  withTempDir(dir => {
    const file = path.join(dir, 'hermes-setup.exe')
    fs.writeFileSync(file, 'not actually used by this test', { mode: 0o644 })

    assert.equal(isRunnableUpdaterBinary(file, { isWindows: true }), true)
  })
})

test('waitForUpdaterSpawn rejects asynchronous spawn errors', async () => {
  const child = new EventEmitter()
  child.off = child.removeListener.bind(child)
  const promise = waitForUpdaterSpawn(child, { timeoutMs: 100 })
  const error = new Error('ENOENT')

  child.emit('error', error)

  await assert.rejects(promise, /ENOENT/)
})

test('waitForUpdaterSpawn resolves after spawn event', async () => {
  const child = new EventEmitter()
  child.off = child.removeListener.bind(child)
  const promise = waitForUpdaterSpawn(child, { timeoutMs: 100 })

  child.emit('spawn')

  await promise
})
