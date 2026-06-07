---
sidebar_position: 99
title: HermesSuite
description: The official web command centre for Hermes Agent
---

# HermesSuite

HermesSuite is the official web-based command centre for Hermes Agent — providing a visual dashboard, agent orchestration, chat sessions, skills management, memory browser, cron manager, and integrated terminal.

![HermesSuite Dashboard](https://via.placeholder.com/800x400?text=HermesSuite+Dashboard)

## Features

- **Dashboard** — Customisable widget grid with system status, active agents, Linear issues, and cron summaries
- **Agent Hub** — Spawn, pause, resume, and abort sub-agents with real-time status
- **Chat** — Persistent session history with real-time token streaming
- **Skills Browser** — Browse, search, and manage skills installed in `~/.hermes/skills/`
- **Memory Browser** — Browse, search, and edit files in `~/.hermes/memory/`
- **Cron Manager** — Visual scheduling and management of recurring tasks
- **Terminal** — Integrated terminal (xterm.js) for shell access
- **File Explorer** — Browse and preview files in your project directories
- **3 Themes** — Paper Light, Ops Dark, and Premium Dark
- **PWA** — Install as a native app on macOS, Windows, iOS, and Android

## Installation

HermesSuite is bundled with Hermes Agent from v0.8.0+.

```bash
# Start HermesSuite dev server
hermes suite dev

# Build for production
hermes suite build
```

Or run standalone:

```bash
cd hermes_suite
npm install
cp .env.example .env
npm run dev
```

## Configuration

| Environment Variable | Description | Default |
|----------------------|-------------|---------|
| `VITE_HERMES_GATEWAY_URL` | Hermes gateway URL | `http://localhost:8642` |
| `VITE_HERMES_GATEWAY_TOKEN` | Gateway authentication token | — |
| `VITE_STUDIO_PASSWORD` | Password for HermesSuite web UI | — |
| `VITE_LINEAR_API_KEY` | Linear API key (optional, for dashboard widget) | — |

## Screenshots

*(Screenshots to be added)*

## Architecture

HermesSuite is a React SPA that communicates with the Hermes gateway via the same MCP API used by all platform integrations (Telegram, Discord, etc.). No separate backend is required — the gateway handles all logic.

```
Browser (HermesSuite SPA)
    │
    ├── Vite proxy: /api/gateway/* → Hermes gateway
    ├── Vite proxy: /api/chat/*    → Upstream LLM API
    └── Vite proxy: /api/mcp/*     → Hermes MCP tools
            │
            └── Hermes gateway (Python)
                    ├── Session management
                    ├── Tool execution
                    └── Platform integrations
```

## Contributing

HermesSuite is part of the Hermes Agent monorepo. See [CONTRIBUTING.md](../CONTRIBUTING.md) for development setup and PR guidelines.

When submitting a PR for HermesSuite:
- New features should include screenshots or a screen recording
- All TypeScript must pass `npm run typecheck`
- Follow the existing component patterns (shadcn/ui + Tailwind)
- Write in British English
