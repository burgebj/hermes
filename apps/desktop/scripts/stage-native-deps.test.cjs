const assert = require('node:assert/strict')
const test = require('node:test')

const { nativePrebuildArchs } = require('../scripts/stage-native-deps.cjs')

test('nativePrebuildArchs uses the requested target architecture', () => {
  assert.deepEqual(nativePrebuildArchs('x64', 'darwin'), ['x64'])
  assert.deepEqual(nativePrebuildArchs('arm64', 'darwin'), ['arm64'])
})

test('nativePrebuildArchs stages both macOS prebuilds for universal builds', () => {
  assert.deepEqual(nativePrebuildArchs('universal', 'darwin'), ['x64', 'arm64'])
})

test('nativePrebuildArchs keeps non-macOS universal requests literal', () => {
  assert.deepEqual(nativePrebuildArchs('universal', 'linux'), ['universal'])
})
