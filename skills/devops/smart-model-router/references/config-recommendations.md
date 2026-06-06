# Config Recommendations for Optimal Model Routing

## Recommended config.yaml Setup

```yaml
# Primary model (free tier)
model:
  api_mode: chat_completions
  default: owl-alpha
  provider: openrouter

# Fallback chain: free first, then paid tiers
fallback_providers:
  # Free tier fallback
  - model: glm-4.7-free
    provider: opencode-zen
  # Mid-tier paid
  - model: claude-sonnet-4-20250514
    provider: anthropic
  # Heavy paid (last resort)
  - model: claude-opus-4-20250514
    provider: anthropic

# Credential pool rotation strategies (optional)
credential_pool_strategies:
  openrouter: least_used
  anthropic: round_robin
  opencode-zen: fill_first
```

## Cron Job Model Overrides

```bash
# Light cron (data collection, monitoring) — free tier
hermes cron create "every 1h" --model "openrouter/owl-alpha" --prompt "..."

# Medium cron (reports, summaries)
hermes cron create "every 6h" --model "anthropic/claude-sonnet-4-20250514" --prompt "..."

# Heavy cron (code review, complex analysis)
hermes cron create "daily" --model "anthropic/claude-opus-4-20250514" --prompt "..."
```

## Subagent Delegation Pattern

```
# Light subagent (use free tier)
delegate_task(goal="Check service statuses", model="openrouter/owl-alpha")

# Medium subagent
delegate_task(goal="Write API endpoint with tests", model="anthropic/claude-sonnet-4-20250514")

# Heavy subagent (best model)
delegate_task(goal="Design auth system", model="anthropic/claude-opus-4-20250514")
```
