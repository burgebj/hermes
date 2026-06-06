---
title: "Inference Sh Cli — Запусти 150+ AI‑додатків через inference"
sidebar_label: "Inference Sh Cli"
description: "Запусти 150+ AI додатків через інференс"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Inference Sh Cli

Запусти 150+ AI‑додатків через CLI inference.sh (infsh) — генерація зображень, створення відео, LLM, пошук, 3D, соціальна автоматизація. Використовує інструмент **terminal tool**. Тригери: inference.sh, infsh, ai apps, flux, veo, image generation, video generation, seedream, seedance, tavily

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/devops/cli` |
| Path | `optional-skills/devops/cli` |
| Version | `1.0.0` |
| Author | okaris |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `AI`, `image-generation`, `video`, `LLM`, `search`, `inference`, `FLUX`, `Veo`, `Claude` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# inference.sh CLI

Запусти 150+ AI‑додатків у хмарі за допомогою простого CLI. GPU не потрібен.

Усі команди використовують **terminal tool** для запуску команд `infsh`.

## When to Use

- Користувач просить згенерувати зображення (FLUX, Reve, Seedream, Grok, Gemini image)
- Користувач просить згенерувати відео (Veo, Wan, Seedance, OmniHuman)
- Користувач запитує про inference.sh або infsh
- Користувач хоче запускати AI‑додатки без керування окремими API провайдерів
- Користувач просить AI‑пошук (Tavily, Exa)
- Користувач потребує генерацію аватара/синхронізації губ

## Prerequisites

CLI `infsh` має бути встановлений та автентифікований. Перевір за допомогою:

```bash
infsh me
```

Якщо не встановлено:

```bash
curl -fsSL https://cli.inference.sh | sh
infsh login
```

Дивись `references/authentication.md` для повних інструкцій налаштування.

## Workflow

### 1. Always Search First

Ніколи не вгадуй назви додатків — завжди шукай, щоб знайти правильний **app ID**:

```bash
infsh app list --search flux
infsh app list --search video
infsh app list --search image
```

### 2. Run an App

Використовуй точний **app ID** з результатів пошуку. Завжди додавай `--json` для машиночитабельного виводу:

```bash
infsh app run <app-id> --input '{"prompt": "your prompt here"}' --json
```

### 3. Parse the Output

JSON‑вивід містить URL‑адреси згенерованих медіа. Показуй їх користувачу у вигляді `MEDIA:<url>` для вбудованого відображення.

## Common Commands

### Image Generation

```bash
# Search for image apps
infsh app list --search image

# FLUX Dev with LoRA
infsh app run falai/flux-dev-lora --input '{"prompt": "sunset over mountains", "num_images": 1}' --json

# Gemini image generation
infsh app run google/gemini-2-5-flash-image --input '{"prompt": "futuristic city", "num_images": 1}' --json

# Seedream (ByteDance)
infsh app run bytedance/seedream-5-lite --input '{"prompt": "nature scene"}' --json

# Grok Imagine (xAI)
infsh app run xai/grok-imagine-image --input '{"prompt": "abstract art"}' --json
```

### Video Generation

```bash
# Search for video apps
infsh app list --search video

# Veo 3.1 (Google)
infsh app run google/veo-3-1-fast --input '{"prompt": "drone shot of coastline"}' --json

# Seedance (ByteDance)
infsh app run bytedance/seedance-1-5-pro --input '{"prompt": "dancing figure", "resolution": "1080p"}' --json

# Wan 2.5
infsh app run falai/wan-2-5 --input '{"prompt": "person walking through city"}' --json
```

### Local File Uploads

CLI автоматично завантажує локальні файли, коли вказуєш шлях:

```bash
# Upscale a local image
infsh app run falai/topaz-image-upscaler --input '{"image": "/path/to/photo.jpg", "upscale_factor": 2}' --json

# Image-to-video from local file
infsh app run falai/wan-2-5-i2v --input '{"image": "/path/to/image.png", "prompt": "make it move"}' --json

# Avatar with audio
infsh app run bytedance/omnihuman-1-5 --input '{"audio": "/path/to/audio.mp3", "image": "/path/to/face.jpg"}' --json
```

### Search & Research

```bash
infsh app list --search search
infsh app run tavily/tavily-search --input '{"query": "latest AI news"}' --json
infsh app run exa/exa-search --input '{"query": "machine learning papers"}' --json
```

### Other Categories

```bash
# 3D generation
infsh app list --search 3d

# Audio / TTS
infsh app list --search tts

# Twitter/X automation
infsh app list --search twitter
```

## Pitfalls

1. **Never guess app IDs** — завжди спочатку виконуй `infsh app list --search <term>`. App IDs змінюються, а нові додатки додаються часто.
2. **Always use `--json`** — сирий вивід важко парсити. Прапорець `--json` дає структурований вивід з URL‑адресами.
3. **Check authentication** — якщо команди повертають помилки автентифікації, запусти `infsh login` або перевір, чи встановлена змінна `INFSH_API_KEY`.
4. **Long‑running apps** — генерація відео може займати 30‑120 секунд. Таймаут **terminal tool** має бути достатнім, але попереджай користувача, що це може зайняти трохи часу.
5. **Input format** — прапорець `--input` приймає JSON‑рядок. Переконайся, що правильно екрануєш лапки.

## Reference Docs

- `references/authentication.md` — Setup, login, API keys
- `references/app-discovery.md` — Searching and browsing the app catalog
- `references/running-apps.md` — Running apps, input formats, output handling
- `references/cli-reference.md` — Complete CLI command reference