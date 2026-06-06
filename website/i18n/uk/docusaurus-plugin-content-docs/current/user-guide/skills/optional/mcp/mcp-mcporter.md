---
title: "Mcporter"
sidebar_label: "Mcporter"
description: "Використовуй CLI mcporter, щоб перелічувати, налаштовувати, автентифікувати та викликати сервери/інструменти MCP безпосередньо (HTTP або stdio), включаючи ad-hoc сервери, редагування конфігурації та CLI/тип gene..."
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Mcporter

Використовуй CLI `mcporter` для **переліку**, налаштування, автентифікації та виклику серверів/інструментів MCP безпосередньо (HTTP або stdio), включаючи ad‑hoc сервери, редагування конфігурації та генерацію CLI/типів.

## Метадані навички

| | |
|---|---|
| Джерело | Optional — install with `hermes skills install official/mcp/mcporter` |
| Шлях | `optional-skills/mcp/mcporter` |
| Версія | `1.0.0` |
| Автор | community |
| Ліцензія | MIT |
| Платформи | linux, macos, windows |
| Теги | `MCP`, `Tools`, `API`, `Integrations`, `Interop` |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# mcporter

Використовуй `mcporter` для виявлення, виклику та керування серверами та інструментами [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) безпосередньо з терміналу.

## Передумови

Потрібен Node.js:
```bash
# No install needed (runs via npx)
npx mcporter list

# Or install globally
npm install -g mcporter
```

## Швидкий старт

```bash
# List MCP servers already configured on this machine
mcporter list

# List tools for a specific server with schema details
mcporter list <server> --schema

# Call a tool
mcporter call <server.tool> key=value
```

## Виявлення серверів MCP

`mcporter` автоматично виявляє сервери, налаштовані іншими клієнтами MCP (Claude Desktop, Cursor тощо) на машині. Щоб знайти нові сервери, переглянь реєстри, такі як [mcpfinder.dev](https://mcpfinder.dev) або [mcp.so](https://mcp.so), а потім підключись ad‑hoc:

```bash
# Connect to any MCP server by URL (no config needed)
mcporter list --http-url https://some-mcp-server.com --name my_server

# Or run a stdio server on the fly
mcporter list --stdio "npx -y @modelcontextprotocol/server-filesystem" --name fs
```

## Виклик інструментів

```bash
# Key=value syntax
mcporter call linear.list_issues team=ENG limit:5

# Function syntax
mcporter call "linear.create_issue(title: \"Bug fix needed\")"

# Ad-hoc HTTP server (no config needed)
mcporter call https://api.example.com/mcp.fetch url=https://example.com

# Ad-hoc stdio server
mcporter call --stdio "bun run ./server.ts" scrape url=https://example.com

# JSON payload
mcporter call <server.tool> --args '{"limit": 5}'

# Machine-readable output (recommended for Hermes)
mcporter call <server.tool> key=value --output json
```

## Автентифікація та конфігурація

```bash
# OAuth login for a server
mcporter auth <server | url> [--reset]

# Manage config
mcporter config list
mcporter config get <key>
mcporter config add <server>
mcporter config remove <server>
mcporter config import <path>
```

Розташування файлу конфігурації: `./config/mcporter.json` (можна перевизначити за допомогою `--config`).

## Демон

Для постійних підключень до серверів:
```bash
mcporter daemon start
mcporter daemon status
mcporter daemon stop
mcporter daemon restart
```

## Генерація коду

```bash
# Generate a CLI wrapper for an MCP server
mcporter generate-cli --server <name>
mcporter generate-cli --command <url>

# Inspect a generated CLI
mcporter inspect-cli <path> [--json]

# Generate TypeScript types/client
mcporter emit-ts <server> --mode client
mcporter emit-ts <server> --mode types
```

## Примітки

- Використовуй `--output json` для структурованого виводу, який легше парсити
- Ad‑hoc сервери (HTTP URL або команда `--stdio`) працюють без будь‑якої конфігурації — корисно для одноразових викликів
- OAuth‑автентифікація може вимагати інтерактивного браузерного потоку — за потреби використай `terminal(command="mcporter auth <server>", pty=true)`