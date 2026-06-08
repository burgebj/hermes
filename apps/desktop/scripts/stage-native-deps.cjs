'use strict'

/**
 * Stage native node-modules dependencies for electron-builder packaging.
 *
 * Workspace dedup hoists `node-pty` into the root `node_modules/`, which
 * electron-builder's default file collector (when `files:` is explicitly set
 * in package.json) cannot reach.  The result: packaged builds ship with no
 * .node binaries and PTY initialization fails at runtime ("PTY support is
 * unavailable").
 *
 * Rather than restructure the workspace dedup (would require nohoist /
 * package.json shenanigans and risk breaking dev) or balloon the package
 * with the whole node_modules tree, we copy ONLY the runtime-essential
 * files of the native dep into apps/desktop/build/native-deps/ and ship
 * THAT subtree via extraResources.  main.cjs falls back to require()-ing
 * from process.resourcesPath when the hoisted-root require fails.
 *
 * Runs as part of `npm run build`. Idempotent -- always re-stages on each
 * build to pick up native binary updates.
 *
 * Layout note: upstream node-pty (microsoft/node-pty 1.x) is N-API based
 * and ships its prebuilts under `prebuilds/<platform>-<arch>/` instead of
 * `build/Release/`.  Its runtime resolver (lib/utils.js) checks
 * build/Release first and falls through to the per-arch prebuilds dir, so
 * shipping only the latter is sufficient for packaged runs.  Per-arch
 * staging keeps the resource bundle lean -- we only need the target
 * arch's prebuilt, not all of them.
 */

const fs = require('node:fs')
const path = require('node:path')

const APP_ROOT = path.resolve(__dirname, '..')
const REPO_ROOT = path.resolve(APP_ROOT, '..', '..')
const STAGE_ROOT = path.join(APP_ROOT, 'build', 'native-deps')

// The target arch may be overridden before `npm run build` via npm_config_arch
// (for example `cross-env npm_config_arch=x64 npm run build`).  This matters
// for cross-building macOS installers: electron-builder's `--x64` / `--arm64`
// flags are not visible until AFTER the build script has staged native deps.
const TARGET_ARCH = process.env.npm_config_arch || process.env.HERMES_DESKTOP_TARGET_ARCH || process.arch
const TARGET_PLATFORM = process.platform

function nativePrebuildArchs(targetArch = TARGET_ARCH, targetPlatform = TARGET_PLATFORM) {
  if (targetPlatform === 'darwin' && targetArch === 'universal') {
    return ['x64', 'arm64']
  }
  return [targetArch]
}

function prebuildIncludePatterns(targetPlatform = TARGET_PLATFORM, targetArch = TARGET_ARCH) {
  return nativePrebuildArchs(targetArch, targetPlatform).flatMap(arch => [
    `prebuilds/${targetPlatform}-${arch}/*.node`,
    `prebuilds/${targetPlatform}-${arch}/*.dll`,
    `prebuilds/${targetPlatform}-${arch}/*.exe`,
    `prebuilds/${targetPlatform}-${arch}/spawn-helper`,
    `prebuilds/${targetPlatform}-${arch}/conpty/*`
  ])
}

// Modules to stage. The "from" path is the hoisted location in the workspace
// root; "to" is the layout we want inside build/native-deps/.  The "include"
// globs (relative to "from") select the runtime-essential files.  Anything
// outside the include list is left behind (source, deps/, scripts, etc.).
const NATIVE_DEPS = [
  {
    from: path.join(REPO_ROOT, 'node_modules', 'node-pty'),
    to: path.join(STAGE_ROOT, 'node-pty'),
    include: [
      'package.json',
      'lib/*.js',
      'lib/**/*.js',
      'build/Release/*.node',
      // Per-arch runtime payload. Explicit file types so we don't ship the
      // ~25 MB of .pdb debug symbols that prebuild-install bundles for
      // Windows crash analysis -- not used at runtime, would just bloat
      // the installer. Universal macOS builds need BOTH darwin prebuild dirs,
      // because node-pty resolves `prebuilds/${platform}-${process.arch}` at
      // runtime after Electron starts on the user's machine.
      ...prebuildIncludePatterns()
    ]
  }
]

function rmrf(target) {
  fs.rmSync(target, { recursive: true, force: true })
}

function ensureDir(target) {
  fs.mkdirSync(target, { recursive: true })
}

function walk(root) {
  const results = []
  const stack = [root]
  while (stack.length) {
    const current = stack.pop()
    let entries
    try {
      entries = fs.readdirSync(current, { withFileTypes: true })
    } catch {
      continue
    }
    for (const entry of entries) {
      const full = path.join(current, entry.name)
      if (entry.isDirectory()) {
        stack.push(full)
      } else if (entry.isFile()) {
        results.push(full)
      }
    }
  }
  return results
}

// Match a relative path against simple ** and * glob patterns. Implementation
// is intentionally tiny -- the include lists are small and don't need full
// minimatch support.
function matchGlob(rel, pattern) {
  const r = rel.replace(/\\/g, '/')
  const re = new RegExp(
    '^' +
      pattern
        .replace(/\\/g, '/')
        .replace(/[.+^${}()|[\]\\]/g, '\\$&')
        .replace(/\*\*/g, '__DOUBLE_STAR__')
        .replace(/\*/g, '[^/]*')
        .replace(/__DOUBLE_STAR__/g, '.*') +
      '$'
  )
  return re.test(r)
}

function stageOne(spec) {
  if (!fs.existsSync(spec.from)) {
    throw new Error(
      `stage-native-deps: source missing at ${spec.from}.  Run \`npm install\` ` +
        `at the workspace root first.`
    )
  }
  rmrf(spec.to)
  ensureDir(spec.to)

  const files = walk(spec.from)
  let copied = 0
  for (const abs of files) {
    const rel = path.relative(spec.from, abs)
    const included = spec.include.some(g => matchGlob(rel, g))
    if (!included) continue
    const dest = path.join(spec.to, rel)
    ensureDir(path.dirname(dest))
    fs.copyFileSync(abs, dest)
    // node-pty's darwin spawn-helper and the Windows helper binaries
    // (OpenConsole.exe, winpty-agent.exe) are invoked via posix_spawn /
    // CreateProcess at runtime, so they must remain executable in the
    // staged tree.  fs.copyFileSync preserves source mode on POSIX, but we
    // re-assert +x defensively for the darwin spawn-helper (no extension
    // means a stripped mode would be silently broken at runtime).
    if (path.basename(rel) === 'spawn-helper' && process.platform !== 'win32') {
      try { fs.chmodSync(dest, 0o755) } catch { /* best-effort */ }
    }
    copied += 1
  }
  console.log(`[stage-native-deps] ${path.relative(APP_ROOT, spec.to)}: ${copied} files`)
}

function main() {
  rmrf(STAGE_ROOT)
  ensureDir(STAGE_ROOT)
  for (const spec of NATIVE_DEPS) {
    stageOne(spec)
  }
}

if (require.main === module) {
  main()
}

module.exports = {
  main,
  nativePrebuildArchs,
  prebuildIncludePatterns
}
