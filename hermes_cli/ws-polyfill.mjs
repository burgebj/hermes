/**
 * WebSocket global polyfill for Node.js < 22.
 *
 * Node.js 22 introduced a stable global `WebSocket` (WHATWG-compatible).
 * Earlier runtimes expose nothing, so TUI code that calls `new WebSocket(url)`
 * exits immediately with "gateway websocket unavailable".  The `ws` package is
 * already a dependency of the monorepo root, so we simply promote its class
 * into `globalThis` when the built-in is absent.
 *
 * Loaded via `node --import hermes_cli/ws-polyfill.mjs` before entry.js runs.
 */
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

if (typeof globalThis.WebSocket === 'undefined') {
  const __dir = dirname(fileURLToPath(import.meta.url));
  const require = createRequire(resolve(__dir, '..', 'package.json'));
  const { WebSocket } = require('ws');
  globalThis.WebSocket = WebSocket;
}
