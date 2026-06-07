---
title: Running Hermes on WSL2 with a Windows Host
sidebar_position: 12
description: Practical setup guide for running Hermes Agent on WSL2 — covering self-hosted backends, filesystem quirks, and known gotchas.
---

# Running Hermes on WSL2

Hermes runs well on WSL2 under Windows, but a few things behave differently than on native Linux. This guide covers the sharp edges.

## Prerequisites

- Windows 10 or 11 with WSL2 enabled
- Ubuntu 24.04+ (or any Debian-based distro) as the WSL guest
- Python 3.11+ in WSL

## Installation

Standard install works in WSL:

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

No Windows-specific steps needed.

## File Search: Know Your Tools

This is the most common WSL-specific gotcha. Hermes has two search paths, and which one you pick matters on WSL:

| Path | Best tool | Why |
|------|-----------|-----|
| `/home/`, `/tmp/`, WSL-native paths | `search_files` (Hermes built-in) | Works fine with ripgrep |
| `/mnt/c/`, `/mnt/d/` (Windows drives) | `mcp_everything_everything_search` (via voidtools Everything) | 100x faster |

If `search_files` is used on `/mnt/` paths without ripgrep installed, it falls back to GNU `find` which runs single-threaded through the WSL9P/Plan 9 translation layer. Large directories (like `C:\Users`) will time out after 60 seconds.

**Fix:** Install ripgrep in WSL for native paths:
```bash
sudo apt install ripgrep
```
For Windows filesystem searches, install [voidtools Everything](https://www.voidtools.com/) on the Windows host and configure the [Everything MCP server](https://github.com/nicepkg/everything-mcp) — it indexes NTFS at the kernel level and returns results in milliseconds.

## Finding Your Windows Files

WSL mounts Windows drives under `/mnt/`. Your Desktop is at:
```
/mnt/c/Users/<yourname>/OneDrive/Desktop/      (if OneDrive is used)
/mnt/c/Users/<yourname>/Desktop/               (without OneDrive)
```
To find your Windows username from WSL:
```bash
ls /mnt/c/Users/
# or
cmd.exe /c whoami
```

## Python: Which One to Use

WSL has its own Python (typically 3.11+). Windows also has Python (e.g. at `C:\Program Files\Python311\python.exe`). For Hermes services that need to interact with Windows-native features (Tailscale, Windows HTTPS, scheduled tasks, the Windows registry), run them via PowerShell:

```bash
powershell.exe -Command '& "C:\Program Files\Python311\python.exe" script.py'
```

For everything else (Hermes itself, scripts, tools), the WSL Python is fine.

## Web Backends: Self-Hosted Search and Extraction

If you don't want to depend on third-party API keys (Firecrawl, Tavily, Exa), you can self-host:

### Search: SearXNG

SearXNG ([github.com/searxng/searxng](https://github.com/searxng/searxng)) is a privacy-respecting metasearch engine that aggregates Google, DuckDuckGo, Brave, Bing, and Wikipedia.

```yaml
# ~/.hermes/config.yaml
web:
  search_backend: "searxng"
```

Set `SEARXNG_URL` in `~/.hermes/.env`:
```
SEARXNG_URL=http://10.42.42.10:8080
```

SearXNG is **search-only** — it cannot extract page content. If you call `web_extract`, it will fail with a message saying so. This is expected behaviour; see Extraction below for alternatives.

### Extraction: Crawl4AI ([github.com/unclecode/crawl4ai](https://github.com/unclecode/crawl4ai)) (via script)

For extracting page content without a commercial API, use a self-hosted Crawl4AI instance:

```bash
# ~/.hermes/scripts/crawl4ai.sh
# Usage: crawl4ai.sh <url> [url2 ...]
# Points at a Crawl4AI server (e.g. http://10.42.42.10:8090)
```

There is no native `web_extract` backend for Crawl4AI in Hermes — you call it via terminal. This works in subagents and interactive sessions alike.

To make it a proper native backend, a plugin would need to be written. See [Adding a Backend](https://hermes-agent.nousresearch.com/docs/developer-guide/adding-a-backend).

## Keeping Hermes Running After SSH Disconnect

WSL2 doesn't have native systemd support (unless you've enabled it in `/etc/wsl.conf`). If you SSH into WSL and start Hermes, it dies when the session closes.

Options:

1. **tmux** — most reliable for WSL:
   ```bash
   tmux new -s hermes
   hermes gateway run
   # Ctrl+B, D to detach
   # tmux attach -t hermes to reattach
   ```

2. **Windows Task Scheduler** — for truly persistent services (e.g. the cron job runner), launch a WSL command from a Windows scheduled task.

## Known Issues on WSL

| Issue | Symptom | Workaround |
|-------|---------|------------|
| `search_files` timeout on `/mnt/` | "Model returned empty after tool calls" | Use Everything MCP instead |
| `web_extract` fails with SearXNG only | "SearXNG is a search-only backend" | Use `crawl4ai.sh` via terminal |
| Update process stashes local changes | Changes reapplied after `hermes update` | Commit local customizations before updating |
| Gateway dies on WSL2 close | Hermes stops when terminal closes | Use tmux or a Windows scheduled task |

## Related

- [Hermes General Installation Guide](https://hermes-agent.nousresearch.com/docs/getting-started)
- [Self-Hosted Providers](https://hermes-agent.nousresearch.com/docs/guides/self-hosted)
- [MCP Servers](https://hermes-agent.nousresearch.com/docs/features/mcp)
