# Mem0 Memory Provider

Server-side LLM fact extraction with semantic search, reranking, and automatic deduplication.

The provider supports two backends:

- `platform` (default): Mem0 Platform through the `mem0ai` SDK.
- `local_rest`: a self-hosted Mem0 server through its REST API.

## Requirements

Platform mode:
- `pip install mem0ai`
- Mem0 API key from [app.mem0.ai](https://app.mem0.ai)

Local REST mode:
- A self-hosted Mem0 API reachable at `MEM0_BASE_URL` (for example `http://localhost:8888`)
- `MEM0_API_KEY` set to the local `X-API-Key` value

## Setup

```bash
hermes memory setup    # select "mem0"
```

Or manually:

```bash
hermes config set memory.provider mem0
```

Platform mode:

```bash
echo "MEM0_API_KEY=your-platform-key" >> ~/.hermes/.env
```

Local REST mode:

```bash
echo "MEM0_BACKEND=local_rest" >> ~/.hermes/.env
echo "MEM0_BASE_URL=http://localhost:8888" >> ~/.hermes/.env
echo "MEM0_API_KEY=your-local-x-api-key" >> ~/.hermes/.env
```

## Config

Config file: `$HERMES_HOME/mem0.json`

| Key | Default | Description |
|-----|---------|-------------|
| `backend` | `platform` | `platform` or `local_rest` |
| `base_url` | `http://localhost:8888` | Local REST URL when `backend=local_rest` |
| `user_id` | `hermes-user` | User identifier on Mem0 |
| `agent_id` | `hermes` | Agent identifier |
| `rerank` | `true` | Enable reranking for platform recall. Ignored by `local_rest` because the self-hosted REST API does not consistently expose a rerank parameter. |

## Local REST endpoint mapping

When `backend=local_rest`, Hermes calls:

| Hermes action | REST call |
|---------------|-----------|
| `mem0_profile` | `GET /memories?user_id=...` |
| `mem0_search` and prefetch | `POST /search` with `query`, `filters`, and `top_k` |
| `mem0_conclude` | `POST /memories` with `messages`, `user_id`, `agent_id`, and `infer=false` |
| turn sync | `POST /memories` with the user and assistant messages |

Local REST requests authenticate with the `X-API-Key` header.

## Tools

| Tool | Description |
|------|-------------|
| `mem0_profile` | All stored memories about the user |
| `mem0_search` | Semantic search with optional reranking in platform mode |
| `mem0_conclude` | Store a fact verbatim (no LLM extraction) |
