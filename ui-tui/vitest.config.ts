import { defineConfig } from 'vitest/config'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  resolve: {
    alias: {
      '@hermes/ink': resolve(root, 'packages/hermes-ink/src/entry-exports.ts')
    }
  },
  test: {
    exclude: ['dist/**', 'node_modules/**']
  }
})
