# Mem0 Memory Provider

Long-term memory backed by [mem0](https://github.com/mem0ai/mem0). Two modes:

* **Cloud** (default): Mem0 Platform API — server-side LLM fact extraction,
  semantic search with reranking, automatic deduplication.
* **Local**: self-hosted via mem0ai's `Memory` class — bring your own vector
  store, LLM, and embedder. No data leaves the host.

## Requirements

- `pip install mem0ai`
- **Cloud mode:** Mem0 API key from [app.mem0.ai](https://app.mem0.ai)
- **Local mode:** a vector store, an LLM endpoint, and an embedder reachable
  from the Hermes process (see [Local Mode](#local-mode) below)

## Setup

```bash
hermes memory setup    # select "mem0"
```

Or manually for cloud mode:
```bash
hermes config set memory.provider mem0
echo "MEM0_API_KEY=your-key" >> ~/.hermes/.env
```

## Config

Config file: `$HERMES_HOME/mem0.json`

| Key | Default | Description |
|-----|---------|-------------|
| `mode` | `cloud` | Backend: `cloud` (Mem0 Platform) or `local` (self-host) |
| `api_key` | — | Mem0 Platform API key (required when `mode=cloud`) |
| `user_id` | `hermes-user` | User identifier |
| `agent_id` | `hermes` | Agent identifier |
| `rerank` | `true` | Enable reranking for recall (cloud mode only) |
| `config` | — | mem0 `MemoryConfig` dict (required when `mode=local`) |

Environment variable equivalents: `MEM0_MODE`, `MEM0_API_KEY`, `MEM0_USER_ID`,
`MEM0_AGENT_ID`. JSON values override env vars.

## Tools

| Tool | Description |
|------|-------------|
| `mem0_profile` | All stored memories about the user |
| `mem0_search` | Semantic search with optional reranking (cloud only) |
| `mem0_conclude` | Store a fact verbatim (no LLM extraction) |

## Local Mode

Set `mode: local` and provide a `config` block in `mem0.json` matching mem0's
[`MemoryConfig`](https://docs.mem0.ai/components/overview) schema. Worked
example below uses a Qdrant vector store, an OpenAI-compatible LLM endpoint
(any provider — Z.AI / OpenRouter / your own vLLM / Ollama works), and Ollama
for embeddings.

```json
{
  "mode": "local",
  "user_id": "hermes-user",
  "agent_id": "hermes",
  "config": {
    "vector_store": {
      "provider": "qdrant",
      "config": {
        "host": "localhost",
        "port": 6333,
        "collection_name": "hermes",
        "embedding_model_dims": 768
      }
    },
    "llm": {
      "provider": "openai",
      "config": {
        "openai_base_url": "https://api.example.com/v1",
        "api_key": "sk-...",
        "model": "gpt-4o-mini"
      }
    },
    "embedder": {
      "provider": "ollama",
      "config": {
        "ollama_base_url": "http://localhost:11434",
        "model": "nomic-embed-text"
      }
    }
  }
}
```

### Notes

- `embedding_model_dims` must match the embedder's output dimension
  (`nomic-embed-text` is 768; `text-embedding-3-small` is 1536). Mismatches
  surface as Qdrant write errors.
- The cloud-only `rerank` flag is silently ignored in local mode; mem0 still
  ranks results by vector similarity.
- mem0 supports many vector stores (Chroma, Pinecone, Weaviate, pgvector, …),
  LLM providers, and embedders. See the
  [mem0 docs](https://docs.mem0.ai/components/overview) for the full matrix —
  any combination that mem0 itself supports works here.

### Quick Qdrant + Ollama bring-up

```bash
# Vector store
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant:latest

# Embedder (skip if you already run Ollama on the host)
docker run -d --name ollama -p 11434:11434 ollama/ollama:latest
docker exec ollama ollama pull nomic-embed-text
```

Then drop the JSON above into `~/.hermes/mem0.json`, set
`memory.provider: mem0` in `~/.hermes/config.yaml`, and restart Hermes.
