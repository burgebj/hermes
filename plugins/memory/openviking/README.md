# OpenViking Memory Provider

Context database by Volcengine (ByteDance) with filesystem-style knowledge hierarchy, tiered retrieval, and automatic memory extraction.

## Requirements

- OpenViking installed and server running (`openviking-server`)
- Embedding model configured in the OpenViking config file
- Optional VLM/chat model configured in OpenViking if you want automatic long-term extraction beyond session/resource storage

For local-first labs, Ollama's `nomic-embed-text` model is a lightweight embedding-only starting point.

## Setup

```bash
hermes memory setup    # select "openviking"
```

Or manually:

```bash
hermes config set memory.provider openviking
```

Add the connection settings to the active profile's `.env` file. For the default profile that is `~/.hermes/.env`; for a named profile use `~/.hermes/profiles/<profile>/.env`.

```text
OPENVIKING_ENDPOINT=http://127.0.0.1:1933
OPENVIKING_API_KEY=<blank-for-local-dev-or-api-key>
OPENVIKING_ACCOUNT=default
OPENVIKING_USER=default
OPENVIKING_AGENT=hermes
```

`OPENVIKING_API_KEY` can be blank for local dev servers that do not require authentication. Authenticated or multi-tenant servers should set the key and tenant IDs explicitly.

## Config

All Hermes-side provider config is read from environment variables in the active profile's `.env`:

| Env Var | Default | Description |
|---------|---------|-------------|
| `OPENVIKING_ENDPOINT` | `http://127.0.0.1:1933` | OpenViking server URL. This is the only required Hermes availability flag. |
| `OPENVIKING_API_KEY` | (none) | API key. Optional for local dev mode. |
| `OPENVIKING_ACCOUNT` | `default` | Tenant account ID. Send explicitly when using ROOT/API-key authenticated servers. |
| `OPENVIKING_USER` | `default` | Tenant user ID. Used in memory URIs such as `viking://user/default/...`. |
| `OPENVIKING_AGENT` | `hermes` | Agent ID. Useful for profile or multi-agent isolation. |

OpenViking's own server config is separate from Hermes. If you use a custom config file, point OpenViking at it when validating or starting the server:

```bash
OPENVIKING_CONFIG_FILE=/path/to/ov.conf uvx --from openviking ov config validate
OPENVIKING_CONFIG_FILE=/path/to/ov.conf \
  uvx --from openviking openviking-server \
  --config /path/to/ov.conf \
  --host 127.0.0.1 \
  --port 1933
```

## Local Ollama embeddings

Ollama can provide local embeddings for OpenViking without changing Hermes' chat model provider.

```bash
ollama pull nomic-embed-text
curl -fsS http://localhost:11434/v1/embeddings \
  -H 'Content-Type: application/json' \
  -d '{"model":"nomic-embed-text","input":"OpenViking embedding probe"}' \
  -o /tmp/openviking-ollama-embed-probe.json
```

`nomic-embed-text` returns 768-dimensional vectors. OpenViking should use Ollama's OpenAI-compatible `/v1` base URL, not the native Ollama root URL:

```json
"embedding": {
  "dense": {
    "provider": "ollama",
    "model": "nomic-embed-text",
    "api_base": "http://localhost:11434/v1",
    "dimension": 768
  },
  "max_concurrent": 2,
  "max_retries": 2,
  "text_source": "content_only",
  "max_input_tokens": 2048
}
```

Keep concurrency conservative on laptops or WSL instances with limited RAM. Avoid pulling large local chat models unless the machine has enough memory and you explicitly need extraction/model-generation features.

## Validation

Check OpenViking first:

```bash
curl -fsS http://127.0.0.1:1933/health
OPENVIKING_CONFIG_FILE=/path/to/ov.conf uvx --from openviking ov health -o json
```

Then check Hermes against the intended profile:

```bash
hermes memory status
hermes --profile openviking-lab memory status
```

The default profile can remain built-in-only while a lab profile uses OpenViking:

```bash
hermes profile create openviking-lab --clone
hermes --profile openviking-lab config set memory.provider openviking
```

For an embedding-only local setup, immediate verification may find data in `viking://session` before it appears as extracted long-term memories under `viking://user/<user>/memories`. Long-term extraction may require a configured OpenViking extraction/chat model.

## Tools

| Tool | Description |
|------|-------------|
| `viking_search` | Semantic search with fast/deep/auto modes |
| `viking_read` | Read content at a viking:// URI (abstract/overview/full) |
| `viking_browse` | Filesystem-style navigation (list/tree/stat) |
| `viking_remember` | Store a fact for extraction on session commit |
| `viking_add_resource` | Ingest URLs/docs into the knowledge base |
