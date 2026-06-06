# OpenRouter Free Models Reference

OpenRouter has a `/models?type=free` endpoint that lists all currently-free models.
These change over time — check https://openrouter.ai/models?type=free for the latest.

## Known Free Models (as of 2026)

These are models with `:free` suffix on OpenRouter:

| Model | Context | Best For |
|-------|---------|----------|
| `owl-alpha` | Large | General purpose, primary free pick |
| `qwen/qwen3-8b:free` | 131K | Coding, reasoning |
| `google/gemini-2.0-flash-001:free` | 1M | Fast, long context |
| `meta-llama/llama-4-maverick:free` | 1M | General, large context |
| `moonshotai/kimi-k2:free` | 131K | Coding, Chinese+English |
| `x-ai/grok-4-fast:free` | 32K | Fast general tasks |

## How to Use Free Models in Hermes

Set as primary or in fallback chain:

```yaml
model:
  default: owl-alpha
  provider: openrouter
fallback_providers:
- model: qwen/qwen3-8b:free
  provider: openrouter
- model: google/gemini-2.0-flash-001:free
  provider: openrouter
```

## Fetching Live List

```bash
curl -s https://openrouter.ai/api/v1/models | python3 -c "
import json,sys
data = json.load(sys.stdin)
for m in data.get('data',[]):
    pricing = m.get('pricing',{})
    if pricing.get('completion','0') == '0' and pricing.get('prompt','0') == '0':
        print(m['id'],' ctx=',m.get('context_length','?'))
" | sort
```
