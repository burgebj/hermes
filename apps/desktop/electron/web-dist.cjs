const fs = require('node:fs')
const path = require('node:path')

function directoryExists(candidate) {
  try {
    return fs.statSync(candidate).isDirectory()
  } catch {
    return false
  }
}

function unpackedPathFor(filePath) {
  return filePath.replace(/app\.asar(?=$|[\\/])/, 'app.asar.unpacked')
}

function resolveDashboardWebDist(appRoot, options = {}) {
  const env = options.env || process.env
  const exists = options.directoryExists || directoryExists

  const override = env.HERMES_DESKTOP_WEB_DIST
  if (override) {
    const resolved = path.resolve(override)
    if (exists(resolved)) return resolved
  }

  const unpackedDist = path.join(unpackedPathFor(appRoot), 'dist')
  if (exists(unpackedDist)) return unpackedDist

  return null
}

function applyDashboardWebDist(env, webDist) {
  const next = { ...env }
  if (webDist) {
    next.HERMES_WEB_DIST = webDist
  } else {
    delete next.HERMES_WEB_DIST
  }
  return next
}

module.exports = {
  applyDashboardWebDist,
  resolveDashboardWebDist
}
