# AntSeed Setup Guide

## 1. Install CLI

```bash
npm install -g @antseed/cli
```

## 2. Start Buyer Proxy

```bash
antseed buyer start
```

OpenAI-compatible endpoint on `http://127.0.0.1:8377/v1/`. State persisted in `~/.antseed/`.

## 3. Wallet

```bash
antseed buyer wallet import <private-key>   # or: antseed buyer wallet create
antseed buyer deposit 1                      # $1 USDC on Base minimum
antseed buyer status                         # verify balance
```

**Never move `identity.key` between hosts.**

## 4. Pin a Peer

```bash
antseed network browse --top 15
antseed buyer connection set --peer <peer-id>
```

Or use smart selection: `bash ${HERMES_SKILL_DIR}/scripts/discover.sh best <task>`

## 5. Hermes Config

Add to `~/.hermes/config.yaml`:

```yaml
custom_providers:
  - name: antseed
    base_url: http://127.0.0.1:8377/v1
    api_key: antseed-p2p
    api_mode: chat_completions
    models:
      # Discover available models:
      # bash ${HERMES_SKILL_DIR}/scripts/discover.sh models --json | jq '.categories[].models[].model' -r

delegation:
  provider: antseed
  # Pick a model from discover.sh output:
  model: <model-id>
  reasoning_effort: minimal
```

**`api_mode: chat_completions`** is mandatory — `openai-responses` requires streaming and breaks auxiliaries.

## 6. Verify

```bash
curl -sf http://127.0.0.1:8377/v1/models -H "Authorization: Bearer antseed-p2p" | head
bash ${HERMES_SKILL_DIR}/scripts/discover.sh models
bash ${HERMES_SKILL_DIR}/scripts/discover.sh best any
```
