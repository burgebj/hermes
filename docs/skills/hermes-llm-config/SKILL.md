# Hermes LLM Configuration

Guide for configuring Hermes Agent's LLM provider stack — model selection, provider routing, custom endpoints, and fallback chains.

---

## Key Architectural Facts

1. **OpenAI is NOT a first-class Hermes provider.** There is no dedicated `OPENAI_API_KEY` env var in Hermes. OpenAI models are accessed via OpenRouter, OpenAI Codex OAuth, custom endpoint, or GitHub Copilot.
2. **`OPENAI_BASE_URL` and `LLM_MODEL` env vars have been removed.** `config.yaml` is the single source of truth for model configuration.
3. **Secrets go in `.env`, settings go in `config.yaml`.** Never put API keys in config.yaml. `hermes config set` auto-routes correctly.
4. **Config precedence (highest to lowest):** CLI arguments > `~/.hermes/config.yaml` > `~/.hermes/.env` > built-in defaults.

## Provider Access Paths

| Path | How It Works |
|---|---|
| **OpenRouter** (recommended) | `OPENROUTER_API_KEY` in `.env` — access 200+ models via unified naming |
| **OpenAI Codex** | `hermes model` — OAuth device code flow, Codex models specifically |
| **Custom Endpoint** | Point at `https://api.openai.com/v1` as OpenAI-compatible endpoint |
| **GitHub Copilot** | OAuth — accesses GPT-5.x through Copilot API |
| **DeepSeek Direct** | Point custom endpoint at `https://api.deepseek.com` (OpenAI format) or `https://api.deepseek.com/anthropic` (Anthropic format). Key env: `DEEPSEEK_API_KEY` |

## Recommended Setup: OpenRouter Primary + Direct OpenAI Custom Provider

This gives maximum flexibility — OpenRouter as daily driver with mid-session switching, plus direct OpenAI for business org billing and audit trail.

### config.yaml (target state)

```yaml
model:
  provider: openrouter
  default: anthropic/claude-sonnet-4-6    # Community #1 for coding agents

custom_providers:
  - name: openai-direct
    base_url: https://api.openai.com/v1
    key_env: OPENAI_API_KEY
  - name: deepseek
    base_url: https://api.deepseek.com
    key_env: DEEPSEEK_API_KEY

fallback_providers:
  - provider: openrouter
    model: openai/gpt-5.3-codex
  - provider: custom:deepseek
    model: deepseek-v4-flash
```

### .env (target state)

```bash
# ~/.hermes/.env (chmod 0600)
OPENROUTER_API_KEY=sk-or-...
OPENAI_API_KEY=sk-proj-...
DEEPSEEK_API_KEY=sk-...
```

### Setup Commands

```bash
# Interactive wizard (run from terminal, outside session)
hermes model

# Or configure directly
hermes config set OPENROUTER_API_KEY sk-or-...
hermes config set model anthropic/claude-sonnet-4-6

# Verify
hermes config check
```

### Mid-Session Switching

Inside an active Hermes session, use `/model` to switch between pre-configured providers:

```
/model custom:openai-direct:gpt-5.3-codex        # Direct OpenAI billing
/model openrouter:anthropic/claude-sonnet-4-6     # Back to OpenRouter default
/model openrouter:anthropic/claude-opus-4-7       # Upgrade for complex reasoning
/model custom:deepseek:deepseek-v4-pro            # DeepSeek V4 Pro (cheapest frontier reasoning)
/model custom:deepseek:deepseek-v4-flash          # DeepSeek V4 Flash (ultra-budget, still 1M context)
```

## Model Recommendations (May 2026, updated 2026-05-23)

### Daily Coding (repo edits, CI triage, test repair)

| Model | Cost (in/out per 1M) | Why |
|---|---|---|
| **Claude Sonnet 4.6** | $3 / $15 | Community #1 for Hermes — best tool-call reliability, 90% prompt caching discount |
| **Qwen 3.6 Plus** (OpenRouter) | ~$0.56/hr | 95% Claude Code quality at half cost |
| **GPT-5.3-Codex** | varies | Leads SWE-bench Pro and Terminal-Bench 2.0 |
| **DeepSeek V4 Pro** (promo) | $0.435 / $0.87 | OpenAI+Anthropic format compatible; thinking mode; 384K max output; massive cost savings for output-heavy coding tasks |

### Complex Reasoning (multi-file refactors, architecture)

| Model | Cost | Why |
|---|---|---|
| **Claude Opus 4.7** | $5 / $25 | Best for complex multi-file analysis |
| **GPT-5.5** | varies | 1M context, 82.7% Terminal-Bench 2.0 |
| **Gemini 3.1 Pro** | $2 / $12 | #1 Chatbot Arena, 2M context |

### Budget/Volume (long-running agents, batch work)

| Model | Cost | Why |
|---|---|---|
| **DeepSeek V4 Flash** | $0.14 / $0.28 | Best value frontier-class; 1M context, thinking mode, cache hits $0.003/M |
| **DeepSeek V4 Pro** (promo thru May 31) | $0.435 / $0.87 | 75% promo; reasoning-class at Flash-tier pricing |
| **GPT-5 Nano** | $0.05/M input | Best value for persistent agents |
| **GPT-4.1 Nano** | $0.10 / $0.40 | Ultra-cheap with 1.05M context |
| **Haiku 4.5** | $1.00 / $5.00 | Fast triage, lightweight |

### High-Value Reasoning (cost-efficient frontier alternative)

| Model | Cost | Why |
|---|---|---|
| **DeepSeek V4 Pro** (post-promo, Jun 1) | $1.74 / $3.48 | 57-86% cheaper output than GPT-4.1/Claude; 1M context, 384K max output, thinking mode |
| **GPT-4.1** | $2.00 / $8.00 | 1.05M context, 50% batch discount, strong SWE-bench |
| **Gemini 2.5 Flash** | $0.30 / $2.50 | 1M context, good for input-heavy RAG |

## CCFT-Aware Model Routing

For governance-sensitive biotech pipelines, route by blast radius, not just cost:

| Code Surface | Minimum Model |
|---|---|
| CCFT enforcement, selector, scoring, catalyst pipeline | Sonnet 4.6 or Opus 4.7 |
| Walk-forward harness, SHA256 hash flows | Sonnet 4.6 |
| Tests, utility scripts, data ingestion | GPT-5.3-Codex or Sonnet 4.6 or DeepSeek V4 Pro |
| Documentation, non-scoring agent code | GPT-5.3-Codex or DeepSeek V4 Pro |
| Batch data processing, long-context ingestion | DeepSeek V4 Flash (1M context, $0.14/M input) |
| Log summarization, terminal output | Deterministic scripts (not LLMs) |

**Note:** DeepSeek V4 Pro/Flash support both OpenAI and Anthropic SDK formats, making them drop-in alternatives for non-governance-critical surfaces. However, China-based infrastructure means data sovereignty considerations apply — do NOT route portfolio-sensitive or PII-containing prompts through DeepSeek without operator review.

## Claude Code Inspection Task

Paste this into a fresh Hermes session to audit and configure providers:

```
Inspect the Hermes provider configuration and current setup.

Goal:
Configure Hermes to use Claude Sonnet 4.6 via OpenRouter as primary model,
with OpenAI GPT-5.3-Codex (direct API from my Platform business org) as named
custom provider for on-demand switching.

Rules:
- Primary: OpenRouter with OPENROUTER_API_KEY
- Alternate: OpenAI direct via custom_providers with key_env: OPENAI_API_KEY
- Do not overwrite existing config; merge changes
- Add fallback_providers for resilience
- Show exact files changed and commands to validate
- Do not print API keys

Check:
- ~/.hermes/config.yaml (current model, provider, custom_providers)
- ~/.hermes/.env (existing keys)
- hermes config check (missing options)

Then propose the smallest config change.
```

## Directory Structure

```
~/.hermes/
  config.yaml     # Settings (model, provider, terminal, compression)
  .env            # API keys and secrets (chmod 0600)
  auth.json       # OAuth credentials (Nous Portal, Copilot, etc.)
  SOUL.md         # Agent identity/persona
  memories/       # Persistent memory (MEMORY.md, USER.md)
  skills/         # Agent-created skills
  cron/           # Scheduled jobs
  sessions/       # Gateway sessions
  logs/           # Logs (secrets auto-redacted)
```

## Local LLM via Ollama (16GB RAM Constraint)

On 16GB RAM Surface hardware, local models are Tier 6 (deferred). The 32B models that win agent benchmarks won't fit at useful context lengths.

If experimenting locally:
- Stick to 7-14B models: Qwen3 9B, Phi-4 14B, Llama 3.3 8B
- Set `OLLAMA_MAX_LOADED_MODELS=1`, `OLLAMA_NUM_PARALLEL=1`, `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_CONTEXT_LENGTH=4096`
- Use Q4_K_M or Q5_K_M quantization
- Revisit at 32GB+ RAM or 24GB+ VRAM

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| "No provider configured" | Missing provider in config.yaml | Run `hermes model` wizard |
| "Invalid API key" on OpenRouter | Stale/missing `OPENROUTER_API_KEY` in `.env` | Regenerate at openrouter.ai/keys |
| Can't `/model` switch | Provider not in config.yaml `custom_providers` | Add named provider entry |
| "OPENAI_BASE_URL not found" | Using removed legacy env var | Migrate to config.yaml `model:` block |
| Slow/OOM on local model | Model too large for RAM | Drop to 8-9B model, reduce context to 4K |

## Reference Docs

- [Hermes OpenAI API Setup Guide](https://www.town.com/content/file/sh710nqw769cqegymmaqq4nh4586tg6b)
- [Surface/16GB RAM Constraints & Ollama Optimization](https://www.town.com/content/file/sh739pcama839tvszr24gsfyt5871eey)
- [CCFT-Aware Routing Policy](https://www.town.com/content/file/sh75yt8qsbdtep7ja2f8r6cpfs86vwzt)
- [Optimal Agent Setup](https://www.town.com/content/document/nx7bhdet5bfd6727qgyxejd6fh870zek)
