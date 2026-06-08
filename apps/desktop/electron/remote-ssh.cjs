// Remote workspace access over SSH for the desktop's File Explorer and Terminal.
//
// When the chat session targets a remote gateway, these surfaces should operate
// on the machine the agent actually runs on — not the local Electron host
// (#38671). Rather than add a new HTTP/WebSocket API to the gateway, we mirror
// how Hermes' own SSH execution backend works (tools/environments/ssh.py): shell
// out to the OpenSSH client with the same ControlMaster connection-reuse
// conventions and the same socket naming. That means when the agent's backend is
// itself `ssh`, the desktop rides the very same multiplexed connection the agent
// already opened, instead of standing up a parallel mechanism.
//
// Scope/assumptions for this first cut:
//   * The remote host runs Linux with GNU find (uses `find -printf`). dev08 and
//     the typical self-hosted gateway qualify.
//   * Auth reuses the user's existing SSH key / agent (BatchMode=yes, no prompts).
//   * ControlMaster is POSIX-only; the Windows OpenSSH client does not support it,
//     so those options are omitted there (each call is its own connection).

const crypto = require('node:crypto')
const fs = require('node:fs')
const os = require('node:os')
const path = require('node:path')
const { execFile } = require('node:child_process')

const IS_WINDOWS = process.platform === 'win32'

// Mirror the hidden-entry filtering the local hermes:fs:readDir handler applies
// so the remote tree looks the same as the local one.
const FS_READDIR_HIDDEN = new Set(['.git', '.DS_Store'])

// Same socket path scheme as ssh.py so we share its ControlMaster master when
// the agent's SSH backend is live: <tmp>/hermes-ssh/<sha256(user@host:port)[:16]>.sock
function controlSocketPath(user, host, port) {
  const dir = path.join(os.tmpdir(), 'hermes-ssh')

  try {
    fs.mkdirSync(dir, { recursive: true })
  } catch {
    // Best-effort; ssh will surface a clear error if the socket can't be made.
  }

  const id = crypto.createHash('sha256').update(`${user}@${host}:${port}`).digest('hex').slice(0, 16)

  return path.join(dir, `${id}.sock`)
}

function sshBaseArgs(cfg) {
  const args = []

  if (!IS_WINDOWS) {
    args.push(
      '-o',
      `ControlPath=${controlSocketPath(cfg.user, cfg.host, cfg.port)}`,
      '-o',
      'ControlMaster=auto',
      '-o',
      'ControlPersist=300'
    )
  }

  args.push(
    '-o',
    'BatchMode=yes',
    '-o',
    'StrictHostKeyChecking=accept-new',
    '-o',
    'ConnectTimeout=10'
  )

  if (cfg.port && Number(cfg.port) !== 22) {
    args.push('-p', String(cfg.port))
  }

  if (cfg.keyPath) {
    args.push('-i', cfg.keyPath)
  }

  return args
}

function sshTarget(cfg) {
  return `${cfg.user}@${cfg.host}`
}

// Single-quote for the remote POSIX shell: close, escaped quote, reopen.
function shQuote(value) {
  return `'${String(value).replace(/'/g, `'\\''`)}'`
}

// node-pty (used for the remote terminal) does NOT search PATH on Windows, so a
// bare "ssh" fails there with "File not found". Resolve an absolute path on
// Windows; on POSIX node-pty execvp's through PATH so the bare name is fine.
let _sshBinary
function sshBinary() {
  if (process.env.HERMES_DESKTOP_SSH_BIN) {
    return process.env.HERMES_DESKTOP_SSH_BIN
  }

  if (_sshBinary) {
    return _sshBinary
  }

  if (IS_WINDOWS) {
    const candidates = [
      path.join(process.env.WINDIR || 'C:\\Windows', 'System32', 'OpenSSH', 'ssh.exe'),
      path.join(process.env.LOCALAPPDATA || '', 'Microsoft', 'WinGet', 'Links', 'ssh.exe')
    ]
    for (const candidate of candidates) {
      try {
        if (candidate && fs.existsSync(candidate)) {
          _sshBinary = candidate
          return _sshBinary
        }
      } catch {
        // ignore and fall through
      }
    }
  }

  _sshBinary = 'ssh'
  return _sshBinary
}

function runRemote(cfg, remoteCommand, { timeout = 15_000, maxBuffer = 8 * 1024 * 1024 } = {}) {
  return new Promise(resolve => {
    const args = [...sshBaseArgs(cfg), sshTarget(cfg), remoteCommand]

    execFile(
      sshBinary(),
      args,
      { timeout, maxBuffer, windowsHide: true },
      (error, stdout, stderr) => {
        resolve({
          code: error ? (typeof error.code === 'number' ? error.code : 1) : 0,
          stdout: stdout || '',
          stderr: stderr || '',
          timedOut: Boolean(error && error.killed),
          error: error || null
        })
      }
    )
  })
}

// List a remote directory. Returns the same shape as the local fs:readDir handler:
// { entries: [{ name, path, isDirectory }], error? }.
async function readDir(cfg, dirPath) {
  const resolved = String(dirPath || '').trim()

  if (!resolved) {
    return { entries: [], error: 'invalid-path' }
  }

  // Portable across Linux and macOS/BSD: `ls -1Ap` prints one entry per line and
  // appends `/` to directories (GNU `find -printf` would be Linux-only). The
  // QUOTING_STYLE=literal prefix disables GNU coreutils' shell-quoting of names
  // with special characters (harmless on BSD ls, which doesn't quote).
  const cmd = `QUOTING_STYLE=literal ls -1Ap ${shQuote(resolved)} 2>/dev/null`
  const { code, stdout, timedOut } = await runRemote(cfg, cmd)

  if (timedOut) {
    return { entries: [], error: 'timeout' }
  }

  if (code !== 0 && !stdout) {
    return { entries: [], error: 'read-error' }
  }

  const base = resolved.replace(/\/+$/, '')
  const entries = stdout
    .split('\n')
    .filter(Boolean)
    .map(line => {
      const isDirectory = line.endsWith('/')
      const name = isDirectory ? line.slice(0, -1) : line

      return { name, path: `${base}/${name}`, isDirectory }
    })
    .filter(entry => entry.name && !FS_READDIR_HIDDEN.has(entry.name))
    .sort((a, b) => Number(b.isDirectory) - Number(a.isDirectory) || a.name.localeCompare(b.name))

  return { entries }
}

// Remote equivalent of the local gitRoot probe.
async function gitRoot(cfg, startPath) {
  const resolved = String(startPath || '').trim()

  if (!resolved) {
    return null
  }

  const cmd = `git -C ${shQuote(resolved)} rev-parse --show-toplevel 2>/dev/null`
  const { code, stdout } = await runRemote(cfg, cmd)
  const root = stdout.trim()

  return code === 0 && root ? root : null
}

// Stat a remote path. Returns { size, isFile, isDirectory } or null if missing.
async function statFile(cfg, filePath) {
  const resolved = String(filePath || '').trim()

  if (!resolved) {
    return null
  }

  // Portable test instead of GNU `stat -c` (BSD/macOS stat uses a different
  // syntax). `wc -c < file` gives the byte size on every POSIX system.
  const q = shQuote(resolved)
  const cmd = `if [ -d ${q} ]; then echo 'd 0'; elif [ -f ${q} ]; then echo "f $(wc -c < ${q})"; else echo 'x 0'; fi`
  const { code, stdout } = await runRemote(cfg, cmd)

  if (code !== 0 || !stdout.trim()) {
    return null
  }

  const parts = stdout.trim().split(/\s+/)
  const type = parts[0]

  if (type === 'x') {
    return null
  }

  return {
    size: Number.parseInt(parts[parts.length - 1], 10) || 0,
    isDirectory: type === 'd',
    isFile: type === 'f'
  }
}

// Read up to maxBytes of a remote file, returned as a Buffer. Transferred as
// base64 so binary content survives the text stdout channel intact.
async function readFileBytes(cfg, filePath, maxBytes) {
  const resolved = String(filePath || '').trim()

  if (!resolved) {
    return Buffer.alloc(0)
  }

  const cmd = `head -c ${Math.max(0, Number(maxBytes) || 0)} ${shQuote(resolved)} | base64`
  // base64 inflates ~4/3 and adds newlines; give the buffer generous headroom.
  const maxBuffer = Math.ceil((Number(maxBytes) || 0) * 1.4) + 64 * 1024
  const { code, stdout, error } = await runRemote(cfg, cmd, { timeout: 30_000, maxBuffer })

  if (code !== 0 || error) {
    throw new Error(`remote read failed: ${resolved}`)
  }

  return Buffer.from(stdout.replace(/\s+/g, ''), 'base64')
}

// ---------------------------------------------------------------------------
// Mutations (create / rename / delete / upload) — local fs equivalents live in
// main.cjs; these run the same operation on the remote host over SSH/SCP.
// ---------------------------------------------------------------------------

async function mkdir(cfg, dirPath) {
  const q = shQuote(String(dirPath || ''))
  const { code } = await runRemote(cfg, `mkdir -p -- ${q}`)

  return { ok: code === 0 }
}

async function newFile(cfg, filePath) {
  const q = shQuote(String(filePath || ''))
  // Create only when absent so we never clobber an existing file.
  const { code } = await runRemote(cfg, `[ -e ${q} ] || : > ${q}`)

  return { ok: code === 0 }
}

async function rename(cfg, fromPath, toPath) {
  const { code, stderr } = await runRemote(cfg, `mv -- ${shQuote(fromPath)} ${shQuote(toPath)}`)

  return { ok: code === 0, error: code === 0 ? undefined : stderr.trim() || 'rename-failed' }
}

async function remove(cfg, targetPath) {
  const { code, stderr } = await runRemote(cfg, `rm -rf -- ${shQuote(targetPath)}`)

  return { ok: code === 0, error: code === 0 ? undefined : stderr.trim() || 'delete-failed' }
}

function scpBinary() {
  if (process.env.HERMES_DESKTOP_SCP_BIN) {
    return process.env.HERMES_DESKTOP_SCP_BIN
  }

  // Derive scp from the configured ssh path so both come from the same install.
  const sshBin = sshBinary()

  return sshBin === 'ssh' ? 'scp' : sshBin.replace(/ssh(\.exe)?$/i, (_m, ext) => `scp${ext || ''}`)
}

function scpBaseArgs(cfg) {
  const args = []

  if (!IS_WINDOWS) {
    args.push('-o', `ControlPath=${controlSocketPath(cfg.user, cfg.host, cfg.port)}`, '-o', 'ControlMaster=auto')
  }

  args.push('-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=accept-new', '-o', 'ConnectTimeout=10')

  if (cfg.port && Number(cfg.port) !== 22) {
    args.push('-P', String(cfg.port))
  }

  if (cfg.keyPath) {
    args.push('-i', cfg.keyPath)
  }

  return args
}

// Upload a local file into a remote directory via scp. Returns { ok, error }.
function upload(cfg, localPath, remoteDir) {
  return new Promise(resolve => {
    const dest = `${sshTarget(cfg)}:${String(remoteDir || '').replace(/\/+$/, '')}/`
    const args = [...scpBaseArgs(cfg), String(localPath), dest]

    execFile(scpBinary(), args, { timeout: 120_000, windowsHide: true }, (error, _stdout, stderr) => {
      resolve({ ok: !error, error: error ? stderr.trim() || String(error.message || error) : undefined })
    })
  })
}

// Overwrite a remote file's contents. Writes the text to a local temp file and
// scp's it to the exact remote path (file -> file), then removes the temp.
function writeFile(cfg, remotePath, content) {
  return new Promise(resolve => {
    let tmp
    try {
      tmp = path.join(os.tmpdir(), `hermes-write-${crypto.randomBytes(8).toString('hex')}`)
      fs.writeFileSync(tmp, typeof content === 'string' ? content : String(content ?? ''), 'utf8')
    } catch (error) {
      resolve({ ok: false, error: 'temp-write-failed' })
      return
    }

    const dest = `${sshTarget(cfg)}:${String(remotePath || '')}`
    const args = [...scpBaseArgs(cfg), tmp, dest]

    execFile(scpBinary(), args, { timeout: 120_000, windowsHide: true }, (error, _stdout, stderr) => {
      try {
        fs.unlinkSync(tmp)
      } catch {
        // best-effort temp cleanup
      }
      resolve({ ok: !error, error: error ? stderr.trim() || String(error.message || error) : undefined })
    })
  })
}

// Argv for an interactive remote shell, spawned through node-pty. node-pty owns
// the *local* PTY; `ssh -tt` allocates the *remote* PTY and forwards window-size
// changes, so node-pty's resize() reaches the remote shell as a normal SIGWINCH.
function terminalSpawn(cfg, cwd) {
  const remoteCommand =
    `cd ${cwd ? shQuote(cwd) : '~'} 2>/dev/null; exec "\${SHELL:-/bin/bash}" -l`
  const args = [...sshBaseArgs(cfg), '-tt', sshTarget(cfg), remoteCommand]

  return { command: sshBinary(), args }
}

module.exports = {
  controlSocketPath,
  gitRoot,
  mkdir,
  newFile,
  readDir,
  readFileBytes,
  remove,
  rename,
  sshBaseArgs,
  statFile,
  writeFile,
  terminalSpawn,
  upload
}
