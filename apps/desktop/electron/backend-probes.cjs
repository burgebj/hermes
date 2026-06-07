/**
 * backend-probes.cjs
 *
 * Cheap "does this candidate backend actually work" checks used by
 * resolveHermesBackend (main.cjs). The resolver walks a ladder of
 * candidates -- bootstrap marker, `hermes` on PATH, system Python with
 * hermes_cli installed -- and historically returned the first candidate
 * whose binary existed on disk. That assumption breaks when a user has
 * a pre-installed Python 3.11-3.13 (so findSystemPython() returns a
 * path) but no hermes_cli in its site-packages: the resolver hands back
 * a backend the spawn step can't actually run, and the user gets a
 * dead-on-arrival "ModuleNotFoundError: No module named 'hermes_cli'"
 * instead of the first-launch installer.
 *
 * These probes give the resolver a way to verify a candidate before
 * trusting it. Failure (non-zero exit, exception, timeout) means "skip
 * this rung, try the next one"; success means "spawn this for real."
 * Falling off the bottom of the ladder lands on the bootstrap-needed
 * sentinel, which is exactly what we want when nothing pre-existing
 * actually works.
 *
 * Both probes are deliberately fast and forgiving:
 *   - 5s timeout (a hung interpreter beats forever, but we still give
 *     slow disks / cold caches room to breathe)
 *   - stdio ignored (we only care about exit code; stdout/stderr are
 *     not surfaced to the user, just to recentHermesLog for forensics
 *     via the caller's catch block if it chooses)
 *   - any throw -> false (never propagate -- resolver wants a boolean)
 *
 * Kept in a standalone cjs module so it can be unit-tested with
 * `node --test` without dragging in the electron runtime (same pattern
 * as bootstrap-platform.cjs and hardening.cjs).
 */

const { execFileSync } = require('node:child_process')
const path = require('node:path')

const PROBE_TIMEOUT_MS = 5000
const POSIX_MIN_PYTHON_MINOR = 10

/**
 * Return true iff `python -c "import hermes_cli"` exits 0.
 *
 * Used to gate the "fallback to system Python with hermes_cli installed"
 * rung of resolveHermesBackend. Without this, a system Python 3.11-3.13
 * registered in PEP 514 makes findSystemPython() succeed regardless of
 * whether hermes_cli has actually been pip-installed into its
 * site-packages -- and the resolver returns a backend that immediately
 * dies on spawn.
 *
 * @param {string} pythonPath - Absolute path to a python.exe / python.
 * @returns {boolean}
 */
function canImportHermesCli(pythonPath) {
  if (!pythonPath) return false
  try {
    execFileSync(pythonPath, ['-c', 'import hermes_cli'], {
      stdio: 'ignore',
      timeout: PROBE_TIMEOUT_MS,
      windowsHide: true
    })
    return true
  } catch {
    return false
  }
}

/**
 * Return true iff `<hermesCommand> --version` exits 0.
 *
 * Used to gate the "existing `hermes` on PATH" rung. Without this, a
 * stale hermes.cmd shim left behind by an uninstalled pip install (or
 * a half-built venv whose `hermes` entry-point points at a deleted
 * Python) survives findOnPath() and gets selected as the backend.
 *
 * We intentionally avoid invoking the command with the dashboard args
 * here -- `--version` is the cheapest "is this binary alive" smoke
 * test that every hermes_cli entry-point has supported since 0.1.
 *
 * @param {string} hermesCommand - Resolved absolute path to a hermes
 *   executable (or an interpreter+script wrapper).
 * @param {object} [opts]
 * @param {boolean} [opts.shell] - Whether to run through a shell. For
 *   .cmd/.bat shims on Windows execFileSync needs shell:true to find
 *   the cmd interpreter; mirrors the same flag isCommandScript() drives
 *   in resolveHermesBackend.
 * @returns {boolean}
 */
function verifyHermesCli(hermesCommand, opts = {}) {
  if (!hermesCommand) return false
  try {
    execFileSync(hermesCommand, ['--version'], {
      stdio: 'ignore',
      timeout: PROBE_TIMEOUT_MS,
      shell: Boolean(opts.shell),
      windowsHide: true
    })
    return true
  } catch {
    return false
  }
}

/**
 * Return true iff the given POSIX Python reports version >= 3.10.
 *
 * macOS Finder/Dock launches often inherit a minimal PATH where
 * `/usr/bin/python3` (3.9) wins even when a newer Homebrew or
 * `/usr/local/bin` install exists. Hermes itself only needs to know
 * whether the interpreter is modern enough to import hermes_cli; the
 * desktop bootstrap later verifies the module import separately.
 *
 * @param {string} pythonPath
 * @param {object} [opts]
 * @param {typeof execFileSync} [opts.execFileSyncImpl]
 * @returns {boolean}
 */
function isSupportedPosixPython(pythonPath, opts = {}) {
  if (!pythonPath) return false
  const execFileSyncImpl = opts.execFileSyncImpl || execFileSync
  try {
    const raw = execFileSyncImpl(
      pythonPath,
      ['-c', 'import sys; print(".".join(map(str, sys.version_info[:2])))'],
      {
        encoding: 'utf8',
        stdio: ['ignore', 'pipe', 'ignore'],
        timeout: PROBE_TIMEOUT_MS,
        windowsHide: true
      }
    )
    const [major, minor] = String(raw)
      .trim()
      .split('.')
      .map(value => Number.parseInt(value, 10))
    return major > 3 || (major === 3 && minor >= POSIX_MIN_PYTHON_MINOR)
  } catch {
    return false
  }
}

/**
 * Resolve the first supported POSIX Python candidate.
 *
 * On macOS we check the common Homebrew/install locations first because
 * GUI-launched apps frequently do not inherit `/opt/homebrew/bin` or
 * `/usr/local/bin` in PATH. We still fall back to PATH-based discovery,
 * but only after filtering out 3.9-era interpreters that would crash on
 * Hermes' Python 3.10+ syntax.
 *
 * @param {object} [opts]
 * @param {string} [opts.platform]
 * @param {(command: string) => string | null} [opts.resolveCommand]
 * @param {(candidate: string) => boolean} [opts.fileExists]
 * @param {typeof execFileSync} [opts.execFileSyncImpl]
 * @param {typeof path} [opts.pathModule]
 * @returns {string | null}
 */
function findSupportedPosixPython(opts = {}) {
  const platform = opts.platform || process.platform
  const resolveCommand = opts.resolveCommand || (() => null)
  const fileExists = opts.fileExists || (() => false)
  const execFileSyncImpl = opts.execFileSyncImpl || execFileSync
  const pathModule = opts.pathModule || path
  const commands = ['python3', 'python']
  const candidates = []

  if (platform === 'darwin') {
    for (const dir of ['/opt/homebrew/bin', '/usr/local/bin']) {
      for (const command of commands) {
        const candidate = pathModule.join(dir, command)
        if (fileExists(candidate)) candidates.push(candidate)
      }
    }
  }

  for (const command of commands) {
    const candidate = resolveCommand(command)
    if (candidate) candidates.push(candidate)
  }

  const seen = new Set()
  for (const candidate of candidates) {
    if (!candidate || seen.has(candidate)) continue
    seen.add(candidate)
    if (isSupportedPosixPython(candidate, { execFileSyncImpl })) {
      return candidate
    }
  }

  return null
}

module.exports = {
  canImportHermesCli,
  findSupportedPosixPython,
  isSupportedPosixPython,
  POSIX_MIN_PYTHON_MINOR,
  verifyHermesCli,
  PROBE_TIMEOUT_MS
}
