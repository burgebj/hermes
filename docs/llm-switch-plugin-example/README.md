# llm-switch — Local LLM Server Manager Plugin

Auto-manage a local LLM server (llama.cpp, vLLM, etc.) from within Hermes.
Define your models in a YAML file and the plugin handles the server lifecycle.

## Motivation

Many users run local models alongside cloud providers — using llama.cpp for
drafting, coding, or research while keeping cloud models for complex tasks.
Today this requires manually starting/stopping the server outside of Hermes.

This plugin bridges that gap: configure your local models in a YAML file,
and Hermes handles the server lifecycle transparently.

## How it works

The plugin uses two lifecycle hooks (activated in #3542):

- **`pre_llm_call`** — fires before each conversation turn. If the active
  model matches a locally configured model and the correct server isn't
  running, the plugin starts it automatically.
- **`on_session_end`** — kills the server when you exit Hermes.

It also registers a **`switch_local_llm` tool** so the agent can switch
models mid-session. This is the primary mid-session switching mechanism —
the user tells the agent "switch to the code model" and the tool swaps
the server behind the scenes.

## Setup

1. Copy the plugin to your Hermes plugins directory:

   ```bash
   cp -r docs/llm-switch-plugin-example ~/.hermes/plugins/llm-switch
   ```

2. Create your model config:

   ```bash
   cd ~/.hermes/plugins/llm-switch
   cp models.yaml.example models.yaml
   # Edit models.yaml with your GGUF paths, context sizes, sampling params
   ```

3. Add a custom provider for your local endpoint in `~/.hermes/config.yaml`:

   ```yaml
   custom_providers:
     - name: local
       base_url: http://localhost:8080/v1
       api_key: "sk-local"
   ```

4. Select the local provider before starting a session:

   ```bash
   hermes model
   # Select your custom provider → pick model name matching a models.yaml key
   ```

## Usage

### Startup — auto-start on first message

After selecting a local model via `hermes model`, the `pre_llm_call` hook
detects the model name on your first message and starts the server:

```
$ hermes
> Write me a blog post about...
  Starting local model: write (SEO articles and content briefs)
  Ready on http://localhost:8080/v1
[model responds...]
```

### Mid-session — switch via the agent

Tell the agent to switch models. It calls the `switch_local_llm` tool:

```
> This task needs the code model, switch to it
  Switching to: code (Agentic coding and tool calling)
[agent continues with new model]
```

### Switch to cloud and back

Use `hermes model` (in a separate terminal or before starting) to switch
between local and cloud providers. Within a session, the agent can handle
local model swaps via the tool.

### Exit — auto-cleanup

When you exit Hermes, the `on_session_end` hook kills the server automatically.

## Configuration

See `models.yaml.example` for the full schema. Key sections:

### `server` — shared server settings

| Field             | Default          | Description                    |
|-------------------|------------------|--------------------------------|
| `binary`          | `llama-server`   | Server binary name or path     |
| `models_dir`      | `~/llama-models` | Base directory for model files |
| `host`            | `0.0.0.0`        | Listen address                 |
| `port`            | `8080`           | Listen port                    |
| `gpu_layers`      | `99`             | GPU offload layers (-ngl)      |
| `flash_attention` | `true`           | Flash attention (-fa)          |
| `parallel`        | `1`              | Concurrent slots (-np)         |
| `jinja`           | `true`           | Chat templates (--jinja)       |

### `models.<name>` — per-model settings

| Field         | Required | Description                              |
|---------------|----------|------------------------------------------|
| `gguf`        | yes      | Path to GGUF file (relative to models_dir) |
| `description` | no       | Human-readable purpose                   |
| `context`     | no       | Context size in tokens (default: 8192)   |
| `kv_cache`    | no       | `{key: q8_0, value: q4_0}` quantization  |
| `sampling`    | no       | Default sampling: temp, top_p, top_k, etc. |
| `alias`       | no       | Name reported by /v1/models              |

## Environment variables

| Variable             | Description                                  |
|----------------------|----------------------------------------------|
| `LLM_SWITCH_MODELS`  | Custom path to models.yaml (default: plugin dir) |

## Complementary PRs

This plugin works best with in-session model switching. See:
- **#3360** — restores `/model` slash command for CLI and gateway
- **#3548** — CLI-only `/model` restoration

Once `/model` is restored, `/model custom:write` would trigger the
`pre_llm_call` hook to auto-start the right server on the next message.
