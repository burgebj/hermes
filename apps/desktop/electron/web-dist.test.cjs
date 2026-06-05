const assert = require('node:assert/strict')
const path = require('node:path')
const test = require('node:test')

const {
  applyDashboardWebDist,
  resolveDashboardWebDist
} = require('./web-dist.cjs')

function existingPaths(...paths) {
  const normalized = new Set(paths.map(item => path.resolve(item)))
  return item => normalized.has(path.resolve(item))
}

test('resolveDashboardWebDist prefers an existing desktop override', () => {
  const override = path.join('tmp', 'hermes-web-dist')
  const appRoot = path.join('Applications', 'Hermes.app', 'Contents', 'Resources', 'app.asar')

  assert.equal(
    resolveDashboardWebDist(appRoot, {
      env: { HERMES_DESKTOP_WEB_DIST: override },
      directoryExists: existingPaths(override)
    }),
    path.resolve(override)
  )
})

test('resolveDashboardWebDist uses unpacked dist when packaged asar has one', () => {
  const appRoot = path.join('Applications', 'Hermes.app', 'Contents', 'Resources', 'app.asar')
  const unpackedDist = path.join(
    appRoot.replace(/app\.asar(?=$|[\\/])/, 'app.asar.unpacked'),
    'dist'
  )

  assert.equal(
    resolveDashboardWebDist(appRoot, {
      env: {},
      directoryExists: existingPaths(unpackedDist)
    }),
    unpackedDist
  )
})

test('resolveDashboardWebDist does not fall back to asar-internal dist', () => {
  const appRoot = path.join('Applications', 'Hermes.app', 'Contents', 'Resources', 'app.asar')

  assert.equal(
    resolveDashboardWebDist(appRoot, {
      env: {},
      directoryExists: () => false
    }),
    null
  )
})

test('applyDashboardWebDist removes inherited HERMES_WEB_DIST when no usable dist exists', () => {
  assert.deepEqual(
    applyDashboardWebDist({
      HERMES_WEB_DIST: path.join('Applications', 'Hermes.app', 'Contents', 'Resources', 'app.asar', 'dist'),
      OTHER: 'kept'
    }, null),
    { OTHER: 'kept' }
  )
})

test('applyDashboardWebDist sets HERMES_WEB_DIST when a usable dist exists', () => {
  assert.deepEqual(
    applyDashboardWebDist({ OTHER: 'kept' }, path.resolve('dist')),
    {
      OTHER: 'kept',
      HERMES_WEB_DIST: path.resolve('dist')
    }
  )
})
