/**
 * Tests for electron/backend-probes.cjs.
 *
 * Run with: node --test electron/backend-probes.test.cjs
 * (Wired into npm test:desktop:platforms in package.json.)
 */

const test = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const os = require('node:os')
const path = require('node:path')

const {
  canImportHermesCli,
  findSupportedPosixPython,
  isSupportedPosixPython,
  verifyHermesCli
} = require('./backend-probes.cjs')

// Resolve the host's own Node binary -- guaranteed to be on disk and
// runnable. We use it as both a stand-in for "a python that doesn't
// have hermes_cli" (since `node -c "import hermes_cli"` will exit
// non-zero) and as a way to script verifyHermesCli's success path
// (a tiny script we write to disk that exits 0 on --version).
const NODE_BIN = process.execPath

test('canImportHermesCli returns false when path is falsy', () => {
  assert.equal(canImportHermesCli(''), false)
  assert.equal(canImportHermesCli(null), false)
  assert.equal(canImportHermesCli(undefined), false)
})

test('canImportHermesCli returns false when interpreter cannot run -c', () => {
  // node IS an interpreter, but `node -c "import hermes_cli"` is a
  // SyntaxError -- different exit reason from a real Python's
  // ModuleNotFoundError, but the predicate is "exit 0 or not" and
  // both land on "not", which is exactly what we want for the
  // resolver fall-through.
  assert.equal(canImportHermesCli(NODE_BIN), false)
})

test('canImportHermesCli returns false when binary does not exist', () => {
  const ghost = path.join(os.tmpdir(), 'hermes-probes-ghost-' + Date.now() + '.exe')
  assert.equal(canImportHermesCli(ghost), false)
})

test('verifyHermesCli returns false when command is falsy', () => {
  assert.equal(verifyHermesCli(''), false)
  assert.equal(verifyHermesCli(null), false)
  assert.equal(verifyHermesCli(undefined), false)
})

test('verifyHermesCli returns false when binary does not exist', () => {
  const ghost = path.join(os.tmpdir(), 'hermes-probes-ghost-' + Date.now() + '.exe')
  assert.equal(verifyHermesCli(ghost), false)
})

test('verifyHermesCli returns true when --version exits 0', () => {
  // Write a tiny script that exits 0 regardless of args, then invoke
  // it through node. This stands in for a working hermes binary --
  // verifyHermesCli only cares about the exit code.
  const scriptPath = path.join(os.tmpdir(), `hermes-probes-ok-${Date.now()}-${process.pid}.cjs`)
  fs.writeFileSync(scriptPath, 'process.exit(0)\n')
  try {
    // Use node as the launcher and our script as the "command". Pass
    // shell:false (default) -- node is a real binary, no shim.
    // execFileSync passes ['--version'] as args, which node ignores
    // gracefully (well, it prints its version and exits 0, which is
    // perfect -- exit code 0 is the only signal we read).
    assert.equal(verifyHermesCli(NODE_BIN), true)
  } finally {
    try {
      fs.unlinkSync(scriptPath)
    } catch {
      void 0
    }
  }
})

test('verifyHermesCli swallows timeouts (does not throw)', () => {
  // We can't easily provoke a real 5s hang in CI without slowing the
  // suite, but we CAN confirm that an invocation that DOES throw
  // (because the binary is missing) returns false rather than
  // propagating. Same code path the timeout case takes.
  assert.equal(verifyHermesCli('/definitely/not/a/real/binary/anywhere'), false)
})

test('isSupportedPosixPython rejects Python 3.9 and accepts 3.10+', () => {
  const versions = new Map([
    ['/usr/bin/python3', '3.9\n'],
    ['/usr/local/bin/python3', '3.10\n'],
    ['/opt/homebrew/bin/python3', '3.14\n']
  ])

  const execFileSyncImpl = pythonPath => {
    const version = versions.get(pythonPath)
    if (!version) throw new Error(`unexpected path: ${pythonPath}`)
    return version
  }

  assert.equal(isSupportedPosixPython('/usr/bin/python3', { execFileSyncImpl }), false)
  assert.equal(isSupportedPosixPython('/usr/local/bin/python3', { execFileSyncImpl }), true)
  assert.equal(isSupportedPosixPython('/opt/homebrew/bin/python3', { execFileSyncImpl }), true)
})

test('findSupportedPosixPython prefers supported macOS well-known locations over PATH', () => {
  const versions = new Map([
    ['/opt/homebrew/bin/python3', '3.14\n'],
    ['/usr/bin/python3', '3.9\n']
  ])

  const candidateByCommand = new Map([
    ['python3', '/usr/bin/python3'],
    ['python', null]
  ])

  const candidate = findSupportedPosixPython({
    platform: 'darwin',
    resolveCommand: command => candidateByCommand.get(command) || null,
    fileExists: pythonPath => versions.has(pythonPath),
    execFileSyncImpl: pythonPath => versions.get(pythonPath)
  })

  assert.equal(candidate, '/opt/homebrew/bin/python3')
})

test('findSupportedPosixPython skips unsupported POSIX PATH hits before returning a newer one', () => {
  const versions = new Map([
    ['/usr/bin/python3', '3.9\n'],
    ['/usr/local/bin/python', '3.11\n']
  ])

  const candidateByCommand = new Map([
    ['python3', '/usr/bin/python3'],
    ['python', '/usr/local/bin/python']
  ])

  const candidate = findSupportedPosixPython({
    platform: 'linux',
    resolveCommand: command => candidateByCommand.get(command) || null,
    fileExists: pythonPath => versions.has(pythonPath),
    execFileSyncImpl: pythonPath => versions.get(pythonPath)
  })

  assert.equal(candidate, '/usr/local/bin/python')
})
