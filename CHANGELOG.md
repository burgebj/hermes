# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changes

- **fix(config): propagate `max_tokens` from config.yaml to AI transport (#20741)**
  `model.max_tokens` documented in `cli-config.yaml.example` was silently ignored:
  it was never read from config and never forwarded to `AIAgent.__init__()` or
  `ChatCompletionsTransport.build_kwargs()`. On providers without a hardcoded output
  cap (Ollama Cloud, zai, custom OpenAI-compatible endpoints) the parameter was
  omitted from the API call entirely, causing responses to be truncated at the
  server's own short default.

  Three gaps fixed: (1) `HermesCLI.__init__` now reads `model.max_tokens` from
  config and stores it as `self.max_tokens`, passing it to both the interactive
  and background `AIAgent` construction sites. (2) Gateway `_resolve_runtime_agent_kwargs`
  now includes `max_tokens` via the new `_resolve_config_max_tokens()` helper,
  which is copied through `_resolve_turn_agent_config` so all six gateway
  `AIAgent(...)` sites receive it. (3) `HERMES_MAX_TOKENS` env var supported as an
  override on both paths. The transport layer already honours `max_tokens` when
  non-None — no changes needed there.
