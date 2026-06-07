# HermesSuite

Web-based command centre for Hermes Agent — a visual dashboard, agent orchestration, chat sessions, skills management, memory browser, cron manager, and integrated terminal.

## Relationship to Hermes Agent

HermesSuite is the **official web UI** for Hermes Agent. It communicates with the Hermes gateway via the MCP API (same as all other platform integrations) and provides a graphical alternative to the CLI and Telegram interface.

## Running

```bash
cd hermes_suite
npm install
cp .env.example .env   # fill in VITE_HERMES_GATEWAY_URL and VITE_STUDIO_PASSWORD
npm run dev            # http://localhost:5173
```

## Building

```bash
npm run build          # production build to dist/
npm run typecheck       # TypeScript check
```

## Architecture

- **SPA** (React 18 + Vite + TypeScript) — no SSR
- **State:** TanStack Query (server) + Zustand (client UI)
- **Routing:** TanStack Router
- **Styling:** Tailwind CSS with 3-theme CSS variable system
- **Proxy:** Vite dev server proxies `/api/gateway/*`, `/api/chat/*`, `/api/mcp/*` to the Hermes gateway
- **PWA:** Vite PWA plugin with Workbox service worker

## Screens

| Route | Description |
|-------|-------------|
| `/` | Dashboard — widget grid, gateway status, active agents |
| `/chat` | Streaming chat sessions |
| `/agent-hub` | Spawn / pause / resume / abort sub-agents |
| `/skills` | Skills browser — installed skills in `~/.hermes/skills/` |
| `/memory` | Memory browser — files in `~/.hermes/memory/` |
| `/cron` | Cron manager — visual `mcp_cronjob` management |
| `/terminal` | Integrated xterm.js terminal |
| `/files` | File explorer |

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) in the repo root.

## License

MIT — same as Hermes Agent.
