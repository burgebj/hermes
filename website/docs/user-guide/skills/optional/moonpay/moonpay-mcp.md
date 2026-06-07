---
title: "Mcp — Set up MoonPay as an MCP server for Claude Desktop or Claude Code"
sidebar_label: "Mcp"
description: "Set up MoonPay as an MCP server for Claude Desktop or Claude Code"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Mcp

Set up MoonPay as an MCP server for Claude Desktop or Claude Code. Provides all MoonPay CLI tools via the Model Context Protocol.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/moonpay/mcp` |
| Path | `optional-skills/moonpay/mcp` |
| Version | `0.1.0` |
| Author | MoonPay (tonyagents), Hermes Agent |
| License | MIT |
| Platforms | linux, macos |
| Tags | `MoonPay`, `Setup` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# MoonPay MCP Setup

## Goal

Configure the MoonPay CLI as an MCP server so Claude Desktop, Claude Code, or any MCP-compatible client can use all MoonPay tools directly.

## Prerequisites

```bash
npm i -g @moonpay/cli
mp login --email user@example.com
mp verify --email user@example.com --code <code>
```

## Claude Code setup

```bash
claude mcp add moonpay -- mp mcp
```

## Claude Desktop setup

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "moonpay": {
      "command": "mp",
      "args": ["mcp"]
    }
  }
}
```

Then restart Claude Desktop.

## What it provides

All MoonPay CLI tools are available as MCP tools:

- **Wallet management** — create, import, list, retrieve, delete, export wallets
- **Token operations** — search, retrieve, trending, swap, bridge, transfer
- **Fiat** — buy crypto with card/bank, virtual accounts with on-ramp
- **x402 payments** — paid API requests with automatic payment handling
- **Transactions** — sign locally, send, list, retrieve

## Verification

After setup, ask Claude: "What MoonPay tools do you have?" — it should list all available tools.

## Auth

The MCP server uses the same credentials as the CLI (`~/.config/moonpay/credentials.json`). Run `mp login --email <email>` then `mp verify --email <email> --code <code>` to authenticate.

## Related skills

- **moonpay-auth** — Login and wallet setup.
- **moonpay-discover-tokens** — Search and analyze tokens.
- **moonpay-swap-tokens** — Swap tokens.
