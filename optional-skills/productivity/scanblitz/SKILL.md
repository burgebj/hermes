---
name: scanblitz
description: Create trackable QR codes and pull scan analytics via the ScanBlitz API. Agents can generate dynamic QR codes, update destinations without regenerating, and get real-time analytics on every scan (device, location, referrer).
version: 1.0.0
author: community
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  env_vars: [SCANBLITZ_API_KEY]
metadata:
  hermes:
    tags: [QR Code, Analytics, Marketing, Tracking, API]
---

# ScanBlitz — QR Codes & Analytics for Agents

Create trackable QR codes, update destinations on the fly, and pull real-time scan analytics — all from your agent.

## What it does

- **Create QR codes** — one call, fully tracked with device/location/referrer data
- **Dynamic destinations** — update where a QR code points without regenerating it
- **Scan analytics** — device breakdown, country distribution, daily trends
- **Self-registration** — agents can create their own API key via email verification

## Tools

| Tool | Description |
|------|-------------|
| `scanblitz_create_qr` | Create a trackable QR code |
| `scanblitz_get_qr` | Get QR code details by short_id |
| `scanblitz_get_analytics` | Scan analytics (devices, countries, daily) |
| `scanblitz_update_qr` | Update destination URL, name, or status |
| `scanblitz_delete_qr` | Deactivate a QR code |
| `scanblitz_register` | Register for an API key (no key needed) |
| `scanblitz_verify` | Complete registration with email code |

## Setup

### 1. Get an API key

**Option A — Via your agent:**

Ask your agent: "Register for a ScanBlitz account using my-email@example.com"

The agent will call `scanblitz_register`, you'll get a 6-digit code via email, then the agent calls `scanblitz_verify` to get the API key.

**Option B — Via curl:**

```bash
# Step 1: Request code
curl -X POST https://kylpeyhiqtdonlqqguty.supabase.co/functions/v1/agent-register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "agent_name": "My Agent"}'

# Step 2: Verify (check email for 6-digit code)
curl -X POST https://kylpeyhiqtdonlqqguty.supabase.co/functions/v1/agent-register/verify \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "code": "123456"}'
```

**Option C — Web signup:** https://scanblitz.com/auth

### 2. Add to your environment

```bash
echo 'SCANBLITZ_API_KEY=sb_api_your_key_here' >> ~/.hermes/.env
```

### 3. Enable the toolset

Add `scanblitz` to your platform toolsets in `~/.hermes/config.yaml`:

```yaml
platform_toolsets:
  telegram:
    - ...existing tools...
    - scanblitz
```

Restart: `hermes restart` or `docker compose restart clawdbot-gateway`

## Usage examples

- "Create a QR code for https://example.com/promo"
- "How many scans did the QR code xK7mQ3 get?"
- "Update the QR code nDIsVY to point to https://example.com/new-page"
- "Deactivate the QR code V6WgJO"

## Free tier

- 50 QR codes
- 1,000 tracked scans/month
- 5,000 API calls/month
- 7-day analytics retention

Paid plans at https://scanblitz.com/pricing

## Links

- API Reference: https://scanblitz.com/llms-full.txt
- MCP Server: `npx -y @scanblitz/mcp-server` (for Claude Code / Cursor)
- Website: https://scanblitz.com
