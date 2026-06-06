const assert = require('node:assert/strict')
const fs = require('node:fs')
const os = require('node:os')
const path = require('node:path')
const test = require('node:test')

const {
  candidateWslHermesHomes,
  copyHermesHomeState,
  importWslHermesHomeIfNeeded,
  isHermesHomeCandidate,
  shouldCopyHermesHomeEntry,
  windowsUsernameFromHome
} = require('./wsl-hermes-home.cjs')

function makeTempRoot() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'hermes-wsl-home-'))
}

function writeFile(filePath, content = '') {
  fs.mkdirSync(path.dirname(filePath), { recursive: true })
  fs.writeFileSync(filePath, content, 'utf8')
}

test('windowsUsernameFromHome falls back to basename of Windows home', () => {
  assert.equal(windowsUsernameFromHome(path.join('C:', 'Users', 'Ada')), 'Ada')
  assert.equal(windowsUsernameFromHome(''), '')
})

test('candidateWslHermesHomes checks common and discovered WSL distros', () => {
  const root = makeTempRoot()
  try {
    fs.mkdirSync(path.join(root, 'Fedora', 'home', 'ada'), { recursive: true })

    const candidates = candidateWslHermesHomes({
      env: { USERNAME: 'ada' },
      wslRoots: [root]
    })

    assert.ok(candidates.includes(path.join(root, 'Ubuntu', 'home', 'ada', '.hermes')))
    assert.ok(candidates.includes(path.join(root, 'Fedora', 'home', 'ada', '.hermes')))
  } finally {
    fs.rmSync(root, { force: true, recursive: true })
  }
})

test('isHermesHomeCandidate requires a real Hermes marker', () => {
  const root = makeTempRoot()
  try {
    const empty = path.join(root, 'empty')
    const hermes = path.join(root, 'hermes')
    fs.mkdirSync(empty)
    fs.mkdirSync(hermes)
    writeFile(path.join(hermes, 'config.yaml'), 'model: test\n')

    assert.equal(isHermesHomeCandidate(empty), false)
    assert.equal(isHermesHomeCandidate(hermes), true)
  } finally {
    fs.rmSync(root, { force: true, recursive: true })
  }
})

test('copyHermesHomeState copies user state but skips runtime directories', () => {
  const root = makeTempRoot()
  try {
    const source = path.join(root, 'wsl', 'Ubuntu', 'home', 'ada', '.hermes')
    const destination = path.join(root, 'LocalAppData', 'hermes')
    writeFile(path.join(source, 'config.yaml'), 'model: test\n')
    writeFile(path.join(source, '.env'), 'HERMES_API_KEY=test\n')
    writeFile(path.join(source, 'skills', 'demo', 'SKILL.md'), '# demo\n')
    writeFile(path.join(source, 'hermes-agent', 'venv', 'pyvenv.cfg'), 'runtime\n')
    writeFile(path.join(source, 'logs', 'desktop.log'), 'noise\n')

    const result = copyHermesHomeState(source, destination)

    assert.equal(result.copied, true)
    assert.deepEqual(new Set(result.copiedEntries), new Set(['.env', 'config.yaml', 'skills']))
    assert.equal(fs.existsSync(path.join(destination, 'config.yaml')), true)
    assert.equal(fs.existsSync(path.join(destination, 'skills', 'demo', 'SKILL.md')), true)
    assert.equal(fs.existsSync(path.join(destination, 'hermes-agent')), false)
    assert.equal(fs.existsSync(path.join(destination, 'logs')), false)
  } finally {
    fs.rmSync(root, { force: true, recursive: true })
  }
})

test('importWslHermesHomeIfNeeded does not overwrite an existing native Hermes home', () => {
  const root = makeTempRoot()
  try {
    const destination = path.join(root, 'LocalAppData', 'hermes')
    fs.mkdirSync(destination, { recursive: true })

    const result = importWslHermesHomeIfNeeded({
      destination,
      env: { USERNAME: 'ada' },
      wslRoots: [root]
    })

    assert.equal(result.imported, false)
    assert.equal(result.reason, 'destination-exists')
  } finally {
    fs.rmSync(root, { force: true, recursive: true })
  }
})

test('importWslHermesHomeIfNeeded imports first valid WSL Hermes home', () => {
  const root = makeTempRoot()
  try {
    const source = path.join(root, 'Ubuntu', 'home', 'ada', '.hermes')
    const destination = path.join(root, 'LocalAppData', 'hermes')
    writeFile(path.join(source, 'auth.json'), '{"ok": true}\n')

    const result = importWslHermesHomeIfNeeded({
      destination,
      env: { USERNAME: 'ada' },
      wslRoots: [root]
    })

    assert.equal(result.imported, true)
    assert.equal(result.source, source)
    assert.equal(fs.existsSync(path.join(destination, 'auth.json')), true)
  } finally {
    fs.rmSync(root, { force: true, recursive: true })
  }
})

test('shouldCopyHermesHomeEntry excludes OS-specific runtime state', () => {
  assert.equal(shouldCopyHermesHomeEntry('hermes-agent'), false)
  assert.equal(shouldCopyHermesHomeEntry('venv'), false)
  assert.equal(shouldCopyHermesHomeEntry('logs'), false)
  assert.equal(shouldCopyHermesHomeEntry('config.yaml'), true)
})
