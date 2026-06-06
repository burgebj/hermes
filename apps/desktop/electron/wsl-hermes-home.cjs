const fs = require('node:fs')
const path = require('node:path')

const DEFAULT_WSL_ROOTS = ['\\\\wsl.localhost', '\\\\wsl$']
const COMMON_WSL_DISTROS = ['Ubuntu', 'Ubuntu-24.04', 'Ubuntu-22.04', 'Debian']
const HERMES_HOME_MARKERS = [
  '.env',
  'auth.json',
  'config.yaml',
  'config.yml',
  'cron',
  'memories',
  'plugins',
  'profiles',
  'sessions',
  'skills'
]
const MIGRATION_EXCLUDE_NAMES = new Set([
  '.venv',
  '__pycache__',
  'bootstrap-cache',
  'git',
  'hermes-agent',
  'logs',
  'node',
  'tmp',
  'venv'
])

function directoryExists(dirPath, fsImpl = fs) {
  try {
    return fsImpl.statSync(dirPath).isDirectory()
  } catch {
    return false
  }
}

function readDirectoryNames(dirPath, fsImpl = fs) {
  try {
    return fsImpl
      .readdirSync(dirPath, { withFileTypes: true })
      .filter(entry => entry.isDirectory())
      .map(entry => entry.name)
  } catch {
    return []
  }
}

function unique(items) {
  return Array.from(new Set(items.filter(Boolean)))
}

function windowsUsernameFromHome(windowsHome, pathImpl = path) {
  return pathImpl.basename(String(windowsHome || '').replace(/[\\/]+$/, ''))
}

function candidateWslHermesHomes(options = {}) {
  const {
    env = process.env,
    fsImpl = fs,
    pathImpl = path,
    windowsHome = '',
    wslRoots = DEFAULT_WSL_ROOTS
  } = options
  const username = String(env.USERNAME || env.USER || windowsUsernameFromHome(windowsHome, pathImpl) || '').trim()
  const candidates = []

  for (const root of wslRoots) {
    const distros = unique([...COMMON_WSL_DISTROS, ...readDirectoryNames(root, fsImpl)])

    for (const distro of distros) {
      const homeRoot = pathImpl.join(root, distro, 'home')
      const users = username ? unique([username, ...readDirectoryNames(homeRoot, fsImpl)]) : readDirectoryNames(homeRoot, fsImpl)

      for (const user of users) {
        candidates.push(pathImpl.join(homeRoot, user, '.hermes'))
      }
    }
  }

  return unique(candidates)
}

function isHermesHomeCandidate(candidate, fsImpl = fs, pathImpl = path) {
  if (!directoryExists(candidate, fsImpl)) return false
  return HERMES_HOME_MARKERS.some(marker => {
    try {
      fsImpl.statSync(pathImpl.join(candidate, marker))
      return true
    } catch {
      return false
    }
  })
}

function shouldCopyHermesHomeEntry(entryName) {
  return !MIGRATION_EXCLUDE_NAMES.has(String(entryName || '').toLowerCase())
}

function copyHermesHomeState(source, destination, options = {}) {
  const { fsImpl = fs, pathImpl = path } = options

  if (!isHermesHomeCandidate(source, fsImpl, pathImpl)) {
    return { copied: false, reason: 'source-not-hermes-home', source, destination }
  }
  if (directoryExists(destination, fsImpl)) {
    return { copied: false, reason: 'destination-exists', source, destination }
  }

  const entries = fsImpl.readdirSync(source, { withFileTypes: true }).filter(entry => shouldCopyHermesHomeEntry(entry.name))

  if (entries.length === 0) {
    return { copied: false, reason: 'no-migratable-entries', source, destination }
  }

  fsImpl.mkdirSync(destination, { recursive: true })
  try {
    for (const entry of entries) {
      fsImpl.cpSync(pathImpl.join(source, entry.name), pathImpl.join(destination, entry.name), {
        errorOnExist: false,
        force: false,
        recursive: true
      })
    }
  } catch (error) {
    try {
      fsImpl.rmSync(destination, { force: true, recursive: true })
    } catch {
      // Best effort: leave the original copy error as the actionable failure.
    }
    throw error
  }

  return {
    copied: true,
    copiedEntries: entries.map(entry => entry.name),
    destination,
    source
  }
}

function importWslHermesHomeIfNeeded(options = {}) {
  const { destination, fsImpl = fs, logger = null, pathImpl = path } = options

  if (!destination) {
    return { imported: false, reason: 'missing-destination' }
  }
  if (directoryExists(destination, fsImpl)) {
    return { imported: false, reason: 'destination-exists', destination }
  }

  let lastError = null
  for (const source of candidateWslHermesHomes(options)) {
    if (!isHermesHomeCandidate(source, fsImpl, pathImpl)) continue

    try {
      const result = copyHermesHomeState(source, destination, options)
      if (result.copied) {
        logger?.(`Imported WSL Hermes state from ${source} into ${destination}`)
        return { ...result, imported: true }
      }
    } catch (error) {
      lastError = error
      logger?.(`Failed to import WSL Hermes state from ${source}: ${error.message}`)
    }
  }

  return {
    destination,
    error: lastError ? String(lastError.message || lastError) : null,
    imported: false,
    reason: lastError ? 'copy-failed' : 'no-source'
  }
}

module.exports = {
  COMMON_WSL_DISTROS,
  DEFAULT_WSL_ROOTS,
  MIGRATION_EXCLUDE_NAMES,
  candidateWslHermesHomes,
  copyHermesHomeState,
  importWslHermesHomeIfNeeded,
  isHermesHomeCandidate,
  shouldCopyHermesHomeEntry,
  windowsUsernameFromHome
}
