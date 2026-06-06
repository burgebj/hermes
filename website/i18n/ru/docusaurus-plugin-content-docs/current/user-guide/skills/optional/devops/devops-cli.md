---
title: "Inference Sh CLI — Запусти более 150 AI‑приложений через inference"
sidebar_label: "Inference Sh Cli"
description: "Запусти более 150 AI‑приложений через инференс"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Inference Sh Cli

Запусти более 150 AI‑приложений через CLI inference.sh (infsh) — генерация изображений, создание видео, LLM, поиск, 3D, автоматизация в соцсетях. Использует терминальный инструмент. Триггеры: inference.sh, infsh, ai apps, flux, veo, image generation, video generation, seedream, seedance, tavily

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
Ниже полное определение навыка, которое Hermes загружает, когда этот навык вызывается. Это то, что агент видит как инструкции, когда навык активен.
:::

# inference.sh CLI

Запусти более 150 AI‑приложений в облаке с помощью простого CLI. GPU не требуется.

Все команды используют **terminal tool** для выполнения команд `infsh`.

## When to Use

- Пользователь просит сгенерировать изображения (FLUX, Reve, Seedream, Grok, Gemini image)
- Пользователь просит сгенерировать видео (Veo, Wan, Seedance, OmniHuman)
- Пользователь интересуется inference.sh или infsh
- Пользователь хочет запускать AI‑приложения без управления отдельными API провайдеров
- Пользователь просит AI‑поиск (Tavily, Exa)
- Пользователю нужна генерация аватара/синхронизация губ

## Prerequisites

CLI `infsh` должен быть установлен и аутентифицирован. Проверь командой:

```bash
infsh me
```

Если не установлен:

```bash
curl -fsSL https://cli.inference.sh | sh
infsh login
```

См. `references/authentication.md` для полного описания настройки.

## Workflow

### 1. Always Search First

Никогда не угадывай названия приложений — всегда ищи, чтобы найти правильный ID приложения:

```bash
infsh app list --search flux
infsh app list --search video
infsh app list --search image
```

### 2. Run an App

Используй точный ID приложения из результатов поиска. Всегда указывай `--json` для машинно‑читаемого вывода:

```bash
infsh app run <app-id> --input '{"prompt": "your prompt here"}' --json
```

### 3. Parse the Output

JSON‑вывод содержит URL‑адреса сгенерированных медиа. Представь их пользователю в виде `MEDIA:<url>` для встроенного отображения.

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

CLI автоматически загружает локальные файлы, когда ты указываешь путь:

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

1. **Never guess app IDs** — всегда сначала выполняй `infsh app list --search <term>`. ID приложений меняются, новые приложения добавляются часто.
2. **Always use `--json`** — необработанный вывод трудно парсить. Флаг `--json` даёт структурированный вывод с URL‑ами.
3. **Check authentication** — если команды завершаются ошибками аутентификации, запусти `infsh login` или проверь, что установлен `INFSH_API_KEY`.
4. **Long-running apps** — генерация видео может занимать 30‑120 секунд. Таймаут terminal tool обычно достаточен, но предупреди пользователя, что процесс может занять время.
5. **Input format** — флаг `--input` принимает строку JSON. Убедись, что кавычки правильно экранированы.

## Reference Docs

- `references/authentication.md` — Настройка, вход, API‑ключи
- `references/app-discovery.md` — Поиск и просмотр каталога приложений
- `references/running-apps.md` — Запуск приложений, форматы ввода, обработка вывода
- `references/cli-reference.md` — Полный справочник команд CLI