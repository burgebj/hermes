const fs = require('node:fs')

function isRunnableUpdaterBinary(candidate, { isWindows = process.platform === 'win32', fsModule = fs } = {}) {
  if (!candidate) return false

  try {
    const stat = fsModule.statSync(candidate)
    if (!stat.isFile()) return false

    if (isWindows) return true

    fsModule.accessSync(candidate, fsModule.constants.X_OK)
    return true
  } catch {
    return false
  }
}

function waitForUpdaterSpawn(child, { timeoutMs = 1500 } = {}) {
  return new Promise((resolve, reject) => {
    let settled = false
    const cleanup = () => {
      child.off?.('spawn', onSpawn)
      child.off?.('error', onError)
      if (timer) clearTimeout(timer)
    }
    const settle = callback => value => {
      if (settled) return
      settled = true
      cleanup()
      callback(value)
    }
    const onSpawn = settle(resolve)
    const onError = settle(reject)
    const timer = setTimeout(() => {
      // Older Electron/Node versions do not always expose a spawn event for
      // detached children. If no async error arrived quickly, treat handoff as
      // accepted; later updater failures belong to the updater log/UI.
      onSpawn()
    }, timeoutMs)

    child.once('spawn', onSpawn)
    child.once('error', onError)
  })
}

module.exports = { isRunnableUpdaterBinary, waitForUpdaterSpawn }
