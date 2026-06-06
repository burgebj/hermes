---
title: "Mcporter"
sidebar_label: "Mcporter"
description: "Используй CLI mcporter для перечисления, настройки, аутентификации и вызова серверов/инструментов MCP напрямую (по HTTP или stdio), включая ad‑hoc серверы, правки конфигурации и команды/типы gene…"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Mcporter

Используй CLI `mcporter` для перечисления, настройки, аутентификации и вызова серверов/инструментов MCP напрямую (по HTTP или stdio), включая ad‑hoc серверы, правки конфигурации и генерацию CLI/типов.

## Метаданные навыка

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/mcp/mcporter` |
| Path | `optional-skills/mcp/mcporter` |
| Version | `1.0.0` |
| Author | community |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `MCP`, `Tools`, `API`, `Integrations`, `Interop` |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает при срабатывании этого навыка. Это то, что агент видит как инструкции, когда навык активен.
:::

# mcporter

Используй `mcporter` для обнаружения, вызова и управления серверами и инструментами [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) напрямую из терминала.

## Требования

Требуется Node.js:
```bash
# No install needed (runs via npx)
npx mcporter list

# Or install globally
npm install -g mcporter
```

## Быстрый старт

```bash
# List MCP servers already configured on this machine
mcporter list

# List tools for a specific server with schema details
mcporter list <server> --schema

# Call a tool
mcporter call <server.tool> key=value
```

## Обнаружение серверов MCP

`mcporter` автоматически обнаруживает серверы, настроенные другими клиентами MCP (Claude Desktop, Cursor и др.) на машине. Чтобы найти новые серверы для использования, просматривай реестры, такие как [mcpfinder.dev](https://mcpfinder.dev) или [mcp.so](https://mcp.so), затем подключай ad‑hoc:

```bash
# Connect to any MCP server by URL (no config needed)
mcporter list --http-url https://some-mcp-server.com --name my_server

# Or run a stdio server on the fly
mcporter list --stdio "npx -y @modelcontextprotocol/server-filesystem" --name fs
```

## Вызов инструментов

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

## Аутентификация и конфигурация

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

Расположение файла конфигурации: `./config/mcporter.json` (можно переопределить с помощью `--config`).

## Демон

Для постоянных соединений с сервером:
```bash
mcporter daemon start
mcporter daemon status
mcporter daemon stop
mcporter daemon restart
```

## Генерация кода

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

## Примечания

- Используй `--output json` для структурированного вывода, который легче парсить
- Ad‑hoc серверы (HTTP‑URL или команда `--stdio`) работают без какой‑либо конфигурации — удобно для одноразовых вызовов
- OAuth‑аутентификация может требовать интерактивного браузерного потока — при необходимости используй `terminal(command="mcporter auth <server>", pty=true)`