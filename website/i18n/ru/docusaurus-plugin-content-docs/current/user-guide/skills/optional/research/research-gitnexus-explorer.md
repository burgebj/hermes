---
title: "Gitnexus Проводник"
sidebar_label: "Gitnexus Explorer"
description: "Индексировать кодовую базу с GitNexus и предоставить интерактивный граф знаний через веб‑интерфейс + туннель Cloudflare"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# GitNexus Explorer

Индексируй кодовую базу с помощью GitNexus и предоставляй интерактивный граф знаний через веб‑интерфейс + туннель Cloudflare.

## Метаданные навыка

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/research/gitnexus-explorer` |
| Path | `optional-skills/research/gitnexus-explorer` |
| Version | `1.0.0` |
| Author | Hermes Agent + Teknium |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `gitnexus`, `code-intelligence`, `knowledge-graph`, `visualization` |
| Related skills | [`native-mcp`](/docs/user-guide/skills/bundled/mcp/mcp-native-mcp), [`codebase-inspection`](/docs/user-guide/skills/bundled/github/github-codebase-inspection) |

## Ссылка: полный SKILL.md

:::info
Ниже представлено полное определение навыка, которое Hermes загружает при его активации. Это то, что агент видит как инструкции, когда навык активен.
:::

# GitNexus Explorer

Индексируй любую кодовую базу в граф знаний и предоставляй интерактивный веб‑интерфейс для исследования символов, цепочек вызовов, кластеров и потоков выполнения. Туннелируется через Cloudflare для удалённого доступа.

## Когда использовать

- Пользователь хочет визуально исследовать архитектуру кодовой базы
- Пользователь запрашивает граф знаний / граф зависимостей репозитория
- Пользователь хочет поделиться интерактивным исследователем кодовой базы с кем‑то

## Предварительные требования

- **Node.js** (v18+) — требуется для GitNexus и прокси
- **git** — репозиторий должен содержать каталог `.git`
- **cloudflared** — для туннелирования (автоустанавливается в `~/.local/bin`, если отсутствует)

## Предупреждение о размере

Веб‑интерфейс рендерит все узлы в браузере. Репозитории до ~5 000 файлов работают стабильно. Большие репозитории (30 k+ узлов) будут медленными или могут привести к сбою вкладки браузера. Инструменты CLI/MCP работают на любом масштабе — ограничение относится только к веб‑визуализации.

## Шаги

### 1. Клонировать и собрать GitNexus (однократная настройка)

```bash
GITNEXUS_DIR="${GITNEXUS_DIR:-$HOME/.local/share/gitnexus}"

if [ ! -d "$GITNEXUS_DIR/gitnexus-web/dist" ]; then
  git clone https://github.com/abhigyanpatwari/GitNexus.git "$GITNEXUS_DIR"
  cd "$GITNEXUS_DIR/gitnexus-shared" && npm install && npm run build
  cd "$GITNEXUS_DIR/gitnexus-web" && npm install
fi
```

### 2. Патчить веб‑интерфейс для удалённого доступа

Веб‑интерфейс по умолчанию использует `localhost:4747` для API‑вызовов. Патчите его на same‑origin, чтобы он работал через туннель/прокси:

**File: `$GITNEXUS_DIR/gitnexus-web/src/config/ui-constants.ts`**
Change:
```typescript
export const DEFAULT_BACKEND_URL = 'http://localhost:4747';
```
To:
```typescript
export const DEFAULT_BACKEND_URL = typeof window !== 'undefined' && window.location.hostname !== 'localhost' ? window.location.origin : 'http://localhost:4747';
```

**File: `$GITNEXUS_DIR/gitnexus-web/vite.config.ts`**
Add `allowedHosts: true` inside the `server: { }` block (only needed if running dev mode instead of production build):
```typescript
server: {
    allowedHosts: true,
    // ... existing config
},
```

Then build the production bundle:
```bash
cd "$GITNEXUS_DIR/gitnexus-web" && npx vite build
```

### 3. Индексировать целевой репозиторий

```bash
cd /path/to/target-repo
npx gitnexus analyze --skip-agents-md
rm -rf .claude/    # remove Claude Code-specific artifacts
```

Add `--embeddings` for semantic search (slower — minutes instead of seconds).

The index lives in `.gitnexus/` inside the repo (auto‑gitignored).

### 4. Создать скрипт прокси

Write this to a file (e.g., `$GITNEXUS_DIR/proxy.mjs`). It serves the production web UI and proxies `/api/*` to the GitNexus backend — same origin, no CORS issues, no sudo, no nginx.

```javascript
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const API_PORT = parseInt(process.env.API_PORT || '4747');
const DIST_DIR = process.argv[2] || './dist';
const PORT = parseInt(process.argv[3] || '8888');

const MIME = {
  '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css',
  '.json': 'application/json', '.png': 'image/png', '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon', '.woff2': 'font/woff2', '.woff': 'font/woff',
  '.wasm': 'application/wasm',
};

function proxyToApi(req, res) {
  const opts = {
    hostname: '127.0.0.1', port: API_PORT,
    path: req.url, method: req.method, headers: req.headers,
  };
  const proxy = http.request(opts, (upstream) => {
    res.writeHead(upstream.statusCode, upstream.headers);
    upstream.pipe(res, { end: true });
  });
  proxy.on('error', () => { res.writeHead(502); res.end('Backend unavailable'); });
  req.pipe(proxy, { end: true });
}

function serveStatic(req, res) {
  let filePath = path.join(DIST_DIR, req.url === '/' ? 'index.html' : req.url.split('?')[0]);
  if (!fs.existsSync(filePath)) filePath = path.join(DIST_DIR, 'index.html');
  const ext = path.extname(filePath);
  const mime = MIME[ext] || 'application/octet-stream';
  try {
    const data = fs.readFileSync(filePath);
    res.writeHead(200, { 'Content-Type': mime, 'Cache-Control': 'public, max-age=3600' });
    res.end(data);
  } catch { res.writeHead(404); res.end('Not found'); }
}

http.createServer((req, res) => {
  if (req.url.startsWith('/api')) proxyToApi(req, res);
  else serveStatic(req, res);
}).listen(PORT, () => console.log(`GitNexus proxy on http://localhost:${PORT}`));
```

### 5. Запустить сервисы

```bash
# Terminal 1: GitNexus backend API
npx gitnexus serve &

# Terminal 2: Proxy (web UI + API on one port)
node "$GITNEXUS_DIR/proxy.mjs" "$GITNEXUS_DIR/gitnexus-web/dist" 8888 &
```

Verify: `curl -s http://localhost:8888/api/repos` should return the indexed repo(s).

### 6. Туннелировать через Cloudflare (optional — for remote access)

```bash
# Install cloudflared if needed (no sudo)
if ! command -v cloudflared &>/dev/null; then
  mkdir -p ~/.local/bin
  curl -sL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
    -o ~/.local/bin/cloudflared
  chmod +x ~/.local/bin/cloudflared
  export PATH="$HOME/.local/bin:$PATH"
fi

# Start tunnel (--config /dev/null avoids conflicts with existing named tunnels)
cloudflared tunnel --config /dev/null --url http://localhost:8888 --no-autoupdate --protocol http2
```

The tunnel URL (e.g., `https://random-words.trycloudflare.com`) is printed to stderr. Share it — anyone with the link can explore the graph.

### 7. Очистка

```bash
# Stop services
pkill -f "gitnexus serve"
pkill -f "proxy.mjs"
pkill -f cloudflared

# Remove index from the target repo
cd /path/to/target-repo
npx gitnexus clean
rm -rf .claude/
```

## Подводные камни

- **`--config /dev/null` is required for cloudflared** if the user has an existing named tunnel config at `~/.cloudflared/config.yml`. Without it, the catch‑all ingress rule in the config returns 404 for all quick tunnel requests.

- **Production build is mandatory for tunneling.** The Vite dev server blocks non‑localhost hosts by default (`allowedHosts`). The production build + Node proxy avoids this entirely.

- **The web UI does NOT create `.claude/` or `CLAUDE.md`.** Those are created by `npx gitnexus analyze`. Use `--skip-agents-md` to suppress the markdown files, then `rm -rf .claude/` for the rest. These are Claude Code integrations that hermes-agent users don't need.

- **Browser memory limit.** The web UI loads the entire graph into browser memory. Repos with 5k+ files may be sluggish. 30k+ files will likely crash the tab.

- **Embeddings are optional.** `--embeddings` enables semantic search but takes minutes on large repos. Skip it for quick exploration; add it if you want natural language queries via the AI chat panel.

- **Multiple repos.** `gitnexus serve` serves ALL indexed repos. Index several repos, start serve once, and the web UI lets you switch between them.