---
name: dataverse
description: Search X/Twitter and Reddit via the Macrocosmos Dataverse CLI (Bittensor Subnet 13). Supports real-time search and long-running Gravity data collection with Parquet export.
version: 1.0.0
author: Volodymyr Truba + Hermes Agent
license: MIT
platforms: [linux, macos]
prerequisites:
  commands: [dv]
  env_vars: [MC_API]
metadata:
  hermes:
    tags: [x, twitter, reddit, social-media, bittensor, subnet13, dataverse, macrocosmos]
    homepage: https://github.com/macrocosm-os/dataverse-cli
---

# Dataverse — X/Twitter & Reddit Search via Bittensor SN13

Query real-time social media data from X/Twitter and Reddit through the decentralized Bittensor Subnet 13 network. No X API keys needed — just a free Macrocosmos API key.

## When to use this skill

- User wants to search X/Twitter or Reddit posts by keyword, username, hashtag
- User wants to collect social data over time (Gravity tasks — up to 7 days)
- User wants to export social datasets as Parquet files
- User wants decentralized social data without per-platform API credentials

## Setup

### 1. Install the CLI

```bash
# Via Cargo (recommended)
cargo install dataverse-cli

# Or from source
git clone https://github.com/macrocosm-os/dataverse-cli
cd dataverse-cli
cargo install --path .
```

### 2. Get a free API key

Sign up at https://app.macrocosmos.ai/account?tab=api-keys

### 3. Authenticate

```bash
dv auth
```

This stores the key in `~/.config/dataverse/config.toml` (Linux) or `~/Library/Application Support/dataverse/config.toml` (macOS).

Alternatively, set the `MC_API` environment variable.

### 4. Verify

```bash
dv status
```

## Quick reference

### Search X/Twitter

```bash
# Basic keyword search
dv search x -k "bittensor AI" --limit 20

# Multiple keywords (AND mode)
dv search x -k "machine learning" -k "open source" --mode all

# By username
dv search x -k "AI agents" -u NousResearch --limit 10

# JSON output (best for agent processing)
dv search x -k "hermes agent" -o json

# CSV output
dv search x -k "LLM benchmarks" -o csv --limit 100

# With date range
dv search x -k "bittensor" --start 2026-03-01 --end 2026-03-15
```

### Search Reddit

```bash
# Search by subreddit
dv search reddit -k "bittensor" --subreddit MachineLearning --limit 20

# Multiple keywords
dv search reddit -k "AI" -k "open source" --mode all -o json

# Broad Reddit search
dv search reddit -k "decentralized AI" --limit 50
```

### Gravity — Long-running data collection

Gravity tasks run on Bittensor miners and collect data continuously for up to 7 days.

```bash
# Create a collection task for X
dv gravity create -p x -k "bittensor" -k "subnet"

# Create a collection task for Reddit
dv gravity create -p reddit -k "artificial intelligence" --subreddit MachineLearning

# Check task status
dv gravity status
dv gravity status <task_id> --crawlers

# Build a Parquet dataset from collected data (stops the crawler)
dv gravity build <crawler_id>

# Check dataset build progress and get download URL
dv gravity dataset <dataset_id>

# Cancel a task
dv gravity cancel <task_id>
```

## Output format

Use `-o json` for structured output the agent can parse. Each search result contains:

**X/Twitter results:**
- `datetime` — post timestamp
- `text` — post content
- `uri` — link to the post
- `user.username`, `user.display_name`, `user.followers_count`
- `tweet.like_count`, `tweet.retweet_count`, `tweet.reply_count`, `tweet.view_count`
- `tweet.hashtags`, `tweet.language`

**Reddit results:**
- `datetime` — post timestamp
- `text` — post content
- `uri` — link to the post

Reddit results return fewer fields than X. Run `dv search reddit -o json` to see the full current schema.

## Global flags

These work with any command:

| Flag | Description |
|------|-------------|
| `-o, --output <table\|json\|csv>` | Output format (default: table) |
| `--api-key <key>` | Override API key for this call |
| `--dry-run` | Preview the HTTP request without executing |
| `--timeout <seconds>` | Request timeout (default: 120) |

## Agent workflow

1. Confirm `dv` is installed: `dv status`
2. Always use `-o json` when you need to process results programmatically
3. For search: use `dv search x` or `dv search reddit` with keywords
4. For large-scale collection: create a Gravity task, monitor it, then build the dataset
5. Stdout is always clean data; diagnostics go to stderr

## Constraints

- Up to 5 keywords per search
- Up to 5 usernames per X search (Reddit does not support username filtering)
- Result limit: 1–1000 per search
- Keyword mode: `any` (OR, default) or `all` (AND)
- Gravity tasks run up to 7 days

## Comparison with xitter skill

| | dataverse | xitter |
|---|-----------|--------|
| **Reads X** | Yes (search) | Yes (search, timeline, mentions) |
| **Writes to X** | No | Yes (post, reply, like, retweet) |
| **Reddit** | Yes | No |
| **Auth** | 1 free API key | 5 paid X API secrets |
| **Data source** | Bittensor SN13 miners | Official X API |
| **Bulk collection** | Yes (Gravity) | No |
| **Export** | Parquet, JSON, CSV | JSON |

Use **dataverse** for search and data collection. Use **xitter** for posting and account actions.
