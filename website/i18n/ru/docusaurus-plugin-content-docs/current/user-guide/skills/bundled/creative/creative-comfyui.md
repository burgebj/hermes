---
title: "Comfyui"
sidebar_label: "Comfyui"
description: "Генерируй изображения, видео и аудио с помощью ComfyUI — устанавливай, запускай, управляй узлами/моделями, запускай рабочие процессы с внедрением параметров"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Comfyui

Генерируй изображения, видео и аудио с помощью ComfyUI — устанавливай, запускай, управляй узлами и моделями, запускай рабочие процессы с внедрением параметров. Использует официальную `comfy-cli` для управления жизненным циклом и прямой REST/WebSocket API для выполнения.
## Метаданные навыка

| | |
|---|---|
| Источник | Built‑in (устанавливается по умолчанию) |
| Путь | `skills/creative/comfyui` |
| Версия | `5.1.0` |
| Автор | ['kshitijk4poor', 'alt-glitch', 'purzbeats'] |
| Лицензия | MIT |
| Платформы | macos, linux, windows |
| Теги | `comfyui`, `image-generation`, `stable-diffusion`, `flux`, `sd3`, `wan-video`, `hunyuan-video`, `creative`, `generative-ai`, `video-generation` |
| Связанные навыки | [`stable-diffusion-image-generation`](/docs/user-guide/skills/optional/mlops/mlops-stable-diffusion), `image_gen` |
:::info
Следующее — полное определение **skill**, которое Hermes загружает при срабатывании этого **skill**. Это то, что агент видит как инструкции, когда **skill** активен.
:::

# ComfyUI

Генерируй изображения, видео, аудио и 3D‑контент через ComfyUI, используя официальный `comfy-cli` для настройки / жизненного цикла и прямой REST/WebSocket API для выполнения рабочих процессов.
## Что находится в этом навыке

**Документация (`references/`):**

- `official-cli.md` — все команды `comfy …` с флагами
- `rest-api.md` — REST‑ и WebSocket‑конечные точки (локальные и облачные), схемы полезных нагрузок
- `workflow-format.md` — JSON‑формат API, общие типы узлов, сопоставление параметров
- `template-integrity.md` — преобразование `comfyui-workflow-templates` из формата редактора в формат API: обход переадресации, пунктирные ключи динамического ввода (`values.a`, `resize_type.width`), особенности облака (302‑перенаправление, 1 одновремённый бесплатный‑уровневый job, потолок VRAM 1080p), совместимая с Discord ffmpeg‑склейка. Автор — [@purzbeats](https://github.com/purzbeats). Загружай этот файл каждый раз, когда начинаешь работу с официальным шаблоном.

**Скрипты (`scripts/`):**

| Скрипт | Назначение |
|--------|------------|
| `_common.py` | Общий HTTP, маршрутизация в облако, каталоги узлов (не запускать напрямую) |
| `hardware_check.py` | Проверка GPU/VRAM/диска → рекомендация локального запуска vs Comfy Cloud |
| `comfyui_setup.sh` | Проверка оборудования + `comfy-cli` + установка ComfyUI + запуск + проверка |
| `extract_schema.py` | Чтение workflow → список управляемых параметров + зависимости моделей |
| `check_deps.py` | Проверка workflow против запущенного сервера → список недостающих узлов/моделей |
| `auto_fix_deps.py` | Запуск `check_deps`, затем `comfy node install` / `comfy model download` |
| `run_workflow.py` | Внедрение параметров, отправка, мониторинг, загрузка выводов (HTTP или WS) |
| `run_batch.py` | Отправка workflow N раз с переборами, параллельно до уровня твоего тарифа |
| `ws_monitor.py` | Просмотр WebSocket в реальном времени для выполняющихся задач (живая индикция прогресса) |
| `health_check.py` | Запуск чек‑листа проверки — `comfy-cli` + сервер + модели + smoke‑test |
| `fetch_logs.py` | Получение трассировки / сообщений статуса для заданного `prompt_id` |

**Примерные workflow (`workflows/`):** SD 1.5, SDXL, Flux Dev, SDXL img2img, SDXL inpaint, ESRGAN upscale, AnimateDiff video, Wan T2V. Смотри `workflows/README.md`.
## Когда использовать

- Пользователь просит сгенерировать изображения с помощью Stable Diffusion, SDXL, Flux, SD3 и т.п.
- Пользователь хочет запустить конкретный файл рабочего процесса ComfyUI
- Пользователь хочет связать генеративные шаги (txt2img → upscale → face restore)
- Пользователю нужен ControlNet, inpainting, img2img или другие продвинутые конвейеры
- Пользователь хочет управлять очередью ComfyUI, проверять модели или устанавливать пользовательские узлы
- Пользователь хочет генерировать видео/аудио/3D с помощью AnimateDiff, Hunyuan, Wan, AudioCraft и т.п.
## Архитектура: два уровня

<!-- ascii-guard-ignore -->
```
┌─────────────────────────────────────────────────────┐
│ Layer 1: comfy-cli (official lifecycle tool)        │
│   Setup, server lifecycle, custom nodes, models     │
│   → comfy install / launch / stop / node / model    │
└─────────────────────────┬───────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────┐
│ Layer 2: REST/WebSocket API + skill scripts         │
│   Workflow execution, param injection, monitoring   │
│   POST /api/prompt, GET /api/view, WS /ws           │
│   → run_workflow.py, run_batch.py, ws_monitor.py    │
└─────────────────────────────────────────────────────┘
```
<!-- ascii-guard-ignore-end -->

**Зачем два уровня?** Официальный CLI отлично подходит для установки и управления сервером, но предоставляет лишь минимальную поддержку выполнения рабочих процессов. REST/WS API закрывает этот пробел — скрипты обрабатывают инъекцию параметров, мониторинг выполнения и скачивание вывода, чего CLI не делает.
## Быстрый старт

### Определение окружения

```bash
# What's available?
command -v comfy >/dev/null 2>&1 && echo "comfy-cli: installed"
curl -s http://127.0.0.1:8188/system_stats 2>/dev/null && echo "server: running"

# Can this machine run ComfyUI locally? (GPU/VRAM/disk check)
python3 scripts/hardware_check.py
```

Если ничего не установлено, смотри раздел **Setup & Onboarding** ниже, но всегда сначала запускай проверку оборудования.

### Одностричная проверка состояния

```bash
python3 scripts/health_check.py
# → JSON: comfy_cli on PATH? server reachable? at least one checkpoint? smoke-test passes?
```
## Основной рабочий процесс

### Шаг 1: Получить JSON рабочего процесса в формате API

Рабочие процессы должны быть в формате API (каждый узел имеет `class_type`). Они получаются из:

- веб‑интерфейса ComfyUI → **Workflow → Export (API)** (новый UI) или
  кнопки «Save (API Format)» в старом UI
- каталога `workflows/` этого навыка (готовые к запуску примеры)
- загрузок из сообщества (civitai, Reddit, Discord) — обычно в формате редактора, их нужно загрузить в ComfyUI, а затем повторно экспортировать

Формат редактора (массивы верхнего уровня `nodes` и `links`) **не является непосредственно исполняемым**. Скрипты обнаруживают это и предлагают повторно экспортировать.

### Шаг 2: Посмотреть, что можно контролировать

```bash
python3 scripts/extract_schema.py workflow_api.json --summary-only
# → {"parameter_count": 12, "has_negative_prompt": true, "has_seed": true, ...}

python3 scripts/extract_schema.py workflow_api.json
# → full schema with parameters, model deps, embedding refs
```

### Шаг 3: Запустить с параметрами

```bash
# Local (defaults to http://127.0.0.1:8188)
python3 scripts/run_workflow.py \
  --workflow workflow_api.json \
  --args '{"prompt": "a beautiful sunset over mountains", "seed": -1, "steps": 30}' \
  --output-dir ./outputs

# Cloud (export API key once; uses correct /api routing automatically)
export COMFY_CLOUD_API_KEY="comfyui-..."
python3 scripts/run_workflow.py \
  --workflow workflow_api.json \
  --args '{"prompt": "..."}' \
  --host https://cloud.comfy.org \
  --output-dir ./outputs

# Real-time progress via WebSocket (requires `pip install websocket-client`)
python3 scripts/run_workflow.py \
  --workflow flux_dev.json \
  --args '{"prompt": "..."}' \
  --ws

# img2img / inpaint: pass --input-image to upload + reference automatically
python3 scripts/run_workflow.py \
  --workflow sdxl_img2img.json \
  --input-image image=./photo.png \
  --args '{"prompt": "make it watercolor", "denoise": 0.6}'

# Batch / sweep: 8 random seeds, parallel up to cloud tier limit
python3 scripts/run_batch.py \
  --workflow sdxl.json \
  --args '{"prompt": "abstract"}' \
  --count 8 --randomize-seed --parallel 3 \
  --output-dir ./outputs/batch
```

`-1` для `seed` (или опустить его с `--randomize-seed`) генерирует новый случайный seed при каждом запуске.

### Шаг 4: Представить результаты

Скрипты выводят JSON в `stdout`, описывающий каждый файл‑результат:

```json
{
  "status": "success",
  "prompt_id": "abc-123",
  "outputs": [
    {"file": "./outputs/sdxl_00001_.png", "node_id": "9",
     "type": "image", "filename": "sdxl_00001_.png"}
  ]
}
```
## Дерево решений

| Пользователь говорит | Инструмент | Команда |
|----------------------|-----------|---------|
| **Lifecycle (использовать comfy-cli)** | | |
| «install ComfyUI» | comfy-cli | `bash scripts/comfyui_setup.sh` |
| «start ComfyUI» | comfy-cli | `comfy launch --background` |
| «stop ComfyUI» | comfy-cli | `comfy stop` |
| «install X node» | comfy-cli | `comfy node install <name>` |
| «download X model» | comfy-cli | `comfy model download --url <url> --relative-path models/checkpoints` |
| «list installed models» | comfy-cli | `comfy model list` |
| «list installed nodes» | comfy-cli | `comfy node show installed` |
| **Execution (использовать скрипты)** | | |
| «is everything ready?» | script | `health_check.py` (опционально с `--workflow X --smoke-test`) |
| «what can I change in this workflow?» | script | `extract_schema.py W.json` |
| «check if W's deps are met» | script | `check_deps.py W.json` |
| «fix missing deps» | script | `auto_fix_deps.py W.json` |
| «generate an image» | script | `run_workflow.py --workflow W --args '{...}'` |
| «use this image» (img2img) | script | `run_workflow.py --input-image image=./x.png ...` |
| «8 variations with random seeds» | script | `run_batch.py --count 8 --randomize-seed ...` |
| «show me live progress» | script | `ws_monitor.py --prompt-id <id>` |
| «fetch the error from job X» | script | `fetch_logs.py <prompt_id>` |
| **Direct REST** | | |
| «what's in the queue?» | REST | `curl http://HOST:8188/queue` (локально) или `--host https://cloud.comfy.org` |
| «cancel that» | REST | `curl -X POST http://HOST:8188/interrupt` |
| «free GPU memory» | REST | `curl -X POST http://HOST:8188/free` |
## Настройка и ввод в эксплуатацию

Когда пользователь просит настроить ComfyUI, **первое, что нужно сделать — спросить, хочет ли он Comfy Cloud (хостинг, нулевая настройка, API‑ключ) или локальный вариант (установить ComfyUI на своей машине)**. Не начинай выполнять команды установки или проверять оборудование, пока они не ответят.

**Официальная документация:** https://docs.comfy.org/installation
**Документация CLI:** https://docs.comfy.org/comfy-cli/getting-started
**Документация Cloud:** https://docs.comfy.org/get_started/cloud
**Cloud API:** https://docs.comfy.org/development/cloud/overview

### Шаг 0: Спросить Local vs Cloud (ВСЕГДА СНАЧАЛА)

Предлагаемый скрипт:

> «Хочешь запустить ComfyUI локально на своей машине или использовать Comfy Cloud?
>
> - **Comfy Cloud** — хостинг на RTX 6000 Pro GPU, все популярные модели предустановлены, нулевая настройка. Требуется API‑ключ (для реального запуска рабочих процессов нужна платная подписка; бесплатный уровень только для чтения). Лучший вариант, если у тебя нет мощного GPU.
> - **Local** — бесплатно, но твоя машина ДОЛЖНА соответствовать требованиям к оборудованию:
>   - NVIDIA GPU с **≥6 GB VRAM** (≥8 GB для SDXL, ≥12 GB для Flux/video), ИЛИ
>   - AMD GPU с поддержкой ROCm (Linux), ИЛИ
>   - Apple Silicon Mac (M1+) с **≥16 GB объединённой памяти** (рекомендовано ≥32 GB).
>   - Intel Mac и машины без GPU НЕ будут работать — используйте Cloud.
>
> Что ты предпочитаешь?»

Маршрутизация:

- **Cloud** → переход к **Пути A**.
- **Local** → сначала выполнить проверку оборудования, затем выбрать путь B–E в зависимости от результата.
- **Не уверен** → выполнить проверку оборудования и решить по результату.

### Шаг 1: Проверка оборудования (ТОЛЬКО если выбран локальный вариант)

```bash
python3 scripts/hardware_check.py --json
# Optional: also probe `torch` for actual CUDA/MPS:
python3 scripts/hardware_check.py --json --check-pytorch
```

| Verdict    | Meaning                                                       | Action |
|------------|---------------------------------------------------------------|--------|
| `ok`       | ≥8 GB VRAM (дискретный) ИЛИ ≥32 GB объединённый (Apple Silicon) | Локальная установка — использовать `comfy_cli_flag` из отчёта |
| `marginal` | SD1.5 работает; SDXL впритирке; Flux/video маловероятно       | Локально OK для лёгких рабочих процессов, иначе **Путь A (Cloud)** |
| `cloud`    | Нет пригодного GPU, <6 GB VRAM, <16 GB Apple unified, Intel Mac, Rosetta Python | **Перейти на Cloud**, если пользователь явно не требует локальную установку |

Скрипт также выводит `wsl: true` (WSL2 с пробросом NVIDIA) и `rosetta: true` (x86_64 Python на Apple Silicon — требуется переустановка как ARM64).

Если verdict = `cloud`, но пользователь хочет локально, не продолжай молча. Выведи массив `notes` дословно и спроси, хочет ли он (a) переключиться на Cloud или (b) принудительно установить локально (что может привести к OOM или неприемлемой медлительности на современных моделях).

### Выбор пути установки

Сначала выполните проверку оборудования. Таблица ниже — запасной вариант, когда пользователь уже сообщил о своём оборудовании:

| Situation | Recommended Path |
|-----------|------------------|
| `verdict: cloud` из проверки оборудования | **Путь A: Comfy Cloud** |
| Нет GPU / хочется попробовать без обязательств | **Путь A: Comfy Cloud** |
| Windows + NVIDIA + нетехнический пользователь | **Путь B: ComfyUI Desktop** |
| Windows + NVIDIA + технический пользователь | **Путь C: Portable** или **Путь D: comfy-cli** |
| Linux + любой GPU | **Путь D: comfy-cli** (самый простой) |
| macOS + Apple Silicon | **Путь B: Desktop** или **Путь D: comfy-cli** |
| Безголовый / сервер / CI / агенты | **Путь D: comfy-cli** |

Для полностью автоматизированного пути (проверка оборудования → установка → запуск → проверка):

```bash
bash scripts/comfyui_setup.sh
# Or with overrides:
bash scripts/comfyui_setup.sh --m-series --port=8190 --workspace=/data/comfy
```

Он запускает `hardware_check.py` внутри, отказывается устанавливать локально, если verdict = `cloud` (если не указан `--force-cloud-override`), выбирает правильный флаг `comfy-cli` и предпочитает `pipx`/`uvx` вместо глобального `pip`, чтобы не загрязнять системный Python.

---

### Путь A: Comfy Cloud (без локальной установки)

Для пользователей без подходящего GPU или желающих нулевую настройку. Хостинг на RTX 6000 Pro.

**Документация:** https://docs.comfy.org/get_started/cloud

1. Зарегистрируйся на https://comfy.org/cloud
2. Сгенерируй API‑ключ на https://platform.comfy.org/login
3. Установи ключ:
      ```bash
   export COMFY_CLOUD_API_KEY="comfyui-xxxxxxxxxxxx"
   ```
4. Запусти рабочие процессы:
      ```bash
   python3 scripts/run_workflow.py \
     --workflow workflows/flux_dev_txt2img.json \
     --args '{"prompt": "..."}' \
     --host https://cloud.comfy.org \
     --output-dir ./outputs
   ```

**Цены:** https://www.comfy.org/cloud/pricing
**Одновременные задачи:** Free/Standard 1, Creator 3, Pro 5. Бесплатный уровень **не может выполнять рабочие процессы через API** — только просматривать модели. Платная подписка требуется для `/api/prompt`, `/api/upload/*`, `/api/view` и т.д.

---

### Путь B: ComfyUI Desktop (Windows / macOS)

Однокнопочный установщик для нетехнических пользователей. Сейчас в бета‑версии.

**Документация:** https://docs.comfy.org/installation/desktop
- **Windows (NVIDIA):** https://download.comfy.org/windows/nsis/x64
- **macOS (Apple Silicon):** https://comfy.org

Linux **не поддерживается** в Desktop‑версии — используйте Путь D.

---

### Путь C: ComfyUI Portable (только Windows)

**Документация:** https://docs.comfy.org/installation/comfyui_portable_windows

Скачайте с https://github.com/comfyanonymous/ComfyUI/releases, распакуйте, запустите `run_nvidia_gpu.bat`. Обновление через `update/update_comfyui_stable.bat`.

---

### Путь D: comfy-cli (все платформы — рекомендуется для агентов)

Официальный CLI — лучший путь для безголовых/автоматических установок.

**Документация:** https://docs.comfy.org/comfy-cli/getting-started

#### Установка comfy-cli

```bash
# Recommended:
pipx install comfy-cli
# Or use uvx without installing:
uvx --from comfy-cli comfy --help
# Or (if pipx/uvx unavailable):
pip install --user comfy-cli
```

Отключить аналитику без интерактивного ввода:
```bash
comfy --skip-prompt tracking disable
```

#### Установка ComfyUI

```bash
comfy --skip-prompt install --nvidia              # NVIDIA (CUDA)
comfy --skip-prompt install --amd                 # AMD (ROCm, Linux)
comfy --skip-prompt install --m-series            # Apple Silicon (MPS)
comfy --skip-prompt install --cpu                 # CPU only (slow)
comfy --skip-prompt install --nvidia --fast-deps  # uv-based dep resolution
```

Путь по умолчанию: `~/comfy/ComfyUI` (Linux), `~/Documents/comfy/ComfyUI` (macOS/Win). Переопределить можно через `comfy --workspace /custom/path install`.

#### Запуск / проверка

```bash
comfy launch --background                       # background daemon on :8188
comfy launch -- --listen 0.0.0.0 --port 8190    # LAN-accessible custom port
curl -s http://127.0.0.1:8188/system_stats      # health check
```

---

### Путь E: Ручная установка (продвинутый уровень / неподдерживаемое оборудование)

Для Ascend NPU, Cambricon MLU, Intel Arc и другого неподдерживаемого оборудования.

**Документация:** https://docs.comfy.org/installation/manual_install

```bash
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI
pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu130
pip install -r requirements.txt
python main.py
```

---

### После установки: загрузка моделей

```bash
# SDXL (general purpose, ~6.5 GB)
comfy model download \
  --url "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors" \
  --relative-path models/checkpoints

# SD 1.5 (lighter, ~4 GB, good for 6 GB cards)
comfy model download \
  --url "https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors" \
  --relative-path models/checkpoints

# Flux Dev fp8 (smaller variant, ~12 GB)
comfy model download \
  --url "https://huggingface.co/Comfy-Org/flux1-dev/resolve/main/flux1-dev-fp8.safetensors" \
  --relative-path models/checkpoints

# CivitAI (set token first):
comfy model download \
  --url "https://civitai.com/api/download/models/128713" \
  --relative-path models/checkpoints \
  --set-civitai-api-token "YOUR_TOKEN"
```

Список установленных: `comfy model list`.

### После установки: установка пользовательских узлов

```bash
comfy node install comfyui-impact-pack             # popular utility pack
comfy node install comfyui-animatediff-evolved     # video generation
comfy node install comfyui-controlnet-aux          # ControlNet preprocessors
comfy node install comfyui-essentials              # common helpers
comfy node update all
comfy node install-deps --workflow=workflow.json   # install everything a workflow needs
```

### После установки: проверка

```bash
python3 scripts/health_check.py
# → comfy_cli on PATH? server reachable? checkpoints? smoke test?

python3 scripts/check_deps.py my_workflow.json
# → are this workflow's nodes/models/embeddings installed?

python3 scripts/run_workflow.py \
  --workflow workflows/sd15_txt2img.json \
  --args '{"prompt": "test", "steps": 4}' \
  --output-dir ./test-outputs
```
## Загрузка изображения (img2img / Inpainting)

Самый простой способ — использовать `--input-image` с `run_workflow.py`:

```bash
python3 scripts/run_workflow.py \
  --workflow workflows/sdxl_img2img.json \
  --input-image image=./photo.png \
  --args '{"prompt": "make it cyberpunk", "denoise": 0.6}'
```

Флаг загружает `photo.png`, а затем вставляет его имя файла на сервере в
параметр схемы с именем `image`. Для inpainting передай оба:

```bash
python3 scripts/run_workflow.py \
  --workflow workflows/sdxl_inpaint.json \
  --input-image image=./photo.png \
  --input-image mask_image=./mask.png \
  --args '{"prompt": "fill with flowers"}'
```

Ручная загрузка через REST:
```bash
curl -X POST "http://127.0.0.1:8188/upload/image" \
  -F "image=@photo.png" -F "type=input" -F "overwrite=true"
# Returns: {"name": "photo.png", "subfolder": "", "type": "input"}

# Cloud equivalent:
curl -X POST "https://cloud.comfy.org/api/upload/image" \
  -H "X-API-Key: $COMFY_CLOUD_API_KEY" \
  -F "image=@photo.png" -F "type=input" -F "overwrite=true"
```
## Специфика облака

- **Базовый URL:** `https://cloud.comfy.org`
- **Авторизация:** заголовок `X-API-Key` (или `?token=KEY` для WebSocket)
- **API‑ключ:** задай переменную `$COMFY_CLOUD_API_KEY` один раз, и скрипты автоматически её используют
- **Скачивание вывода:** `/api/view` возвращает 302 на подписанный URL; скрипты
  следуют перенаправлению и удаляют `X-API-Key` перед запросом к хранилищу
  (чтобы не утекал API‑ключ в S3/CloudFront).
- **Отличия эндпоинтов от локального ComfyUI:**
  - `/api/object_info`, `/api/queue`, `/api/userdata` — **403 на бесплатном тарифе**; доступно только в платных.
  - `/history` переименован в `/history_v2` в облаке (скрипты автоматически перенаправляют).
  - `/models/<folder>` переименован в `/experiment/models/<folder>` в облаке (скрипты автоматически перенаправляют).
  - `clientId` в WebSocket в текущей версии игнорируется — все соединения одного пользователя получают одинаковый broadcast. Фильтруй по `prompt_id` на клиенте.
  - `subfolder` принимается при загрузке, но игнорируется — в облаке плоское пространство имён.
- **Одновременные задачи:** Free/Standard: 1, Creator: 3, Pro: 5. Очередь Extras формируется автоматически. Используй `run_batch.py --parallel N`, чтобы полностью использовать возможности твоего тарифа.
## Очереди и управление системой

```bash
# Local
curl -s http://127.0.0.1:8188/queue | python3 -m json.tool
curl -X POST http://127.0.0.1:8188/queue -d '{"clear": true}'    # cancel pending
curl -X POST http://127.0.0.1:8188/interrupt                      # cancel running
curl -X POST http://127.0.0.1:8188/free \
  -H "Content-Type: application/json" \
  -d '{"unload_models": true, "free_memory": true}'

# Cloud — same paths under /api/, plus:
python3 scripts/fetch_logs.py --tail-queue --host https://cloud.comfy.org
```
## Подводные камни

1. **Требуется формат API** — каждый скрипт и эндпоинт `/api/prompt` ожидают JSON рабочего процесса в формате API. Скрипты определяют формат редактора (масивы верхнего уровня `nodes` и `links`) и просят переэкспортировать через **Workflow → Export (API)** (новый UI) или **Save (API Format)** (старый UI).

2. **Сервер должен быть запущен** — вся работа требует живого сервера. `comfy launch --background` запускает его. Проверь с помощью `curl http://127.0.0.1:8188/system_stats`.

3. **Имена моделей должны быть точными** — учитывается регистр, включается расширение файла. `check_deps.py` выполняет нечёткое сопоставление (с/без расширения и префикса папки), но сам рабочий процесс должен использовать каноничное имя. Используй `comfy model list`, чтобы узнать, что установлено.

4. **Отсутствуют пользовательские узлы** — «class_type not found» означает, что требуемый узел не установлен. `check_deps.py` сообщает, какой пакет установить; `auto_fix_deps.py` выполнит установку за тебя.

5. **Рабочий каталог** — `comfy-cli` автоматически определяет рабочее пространство ComfyUI. Если команды завершаются ошибкой «no workspace found», используй `comfy --workspace /path/to/ComfyUI <command>` или `comfy set-default /path/to/ComfyUI`.

6. **Ограничения бесплатного уровня облака** — `/api/prompt`, `/api/view`, `/api/upload/*`, `/api/object_info` возвращают 403 для бесплатных аккаунтов. `health_check.py` и `check_deps.py` обрабатывают это корректно и выводят понятное сообщение.

7. **Таймаут для виде/аудио‑рабочих процессов** — автоматически определяется, когда выходной узел является `VHS_VideoCombine`, `SaveVideo` и т.п.; значение по умолчанию меняется с 300 с до 900 с. Переопредели явно с помощью `--timeout 1800`.

8. **Обход пути в именах файлов вывода** — имена файлов, предоставляемые сервером, проходят через `safe_path_join`, который отклоняет любые попытки выйти за пределы `--output-dir`. Оставляй эту защиту включённой — рабочие процессы с пользовательскими узлами сохранения могут генерировать произвольные пути.

9. **JSON рабочего процесса — произвольный код** — пользовательские узлы выполняют Python, поэтому отправка неизвестного рабочего процесса имеет такой же уровень доверия, как `eval`. Проверяй рабочие процессы из недоверенных источников перед запуском.

10. **Автослучайный сид** — передай `seed: -1` в `--args` (или используй `--randomize-seed` и опусти параметр `seed`), чтобы получать новый сид при каждом запуске. Фактический сид выводится в `stderr`.

11. **`tracking`‑подсказка** — при первом запуске `comfy` может запросить аналитические данные. Используй `comfy --skip-prompt tracking disable`, чтобы пропустить её в неинтерактивном режиме. `comfyui_setup.sh` делает это за тебя.
## Контрольный список проверки

Используй `python3 scripts/health_check.py`, чтобы выполнить весь список сразу. Вручную:

- [ ] `hardware_check.py` возвращает результат `ok` ИЛИ пользователь явно выбрал Comfy Cloud
- [ ] `comfy --version` работает (или `uvx --from comfy-cli comfy --help`)
- [ ] `curl http://HOST:PORT/system_stats` возвращает JSON
- [ ] `comfy model list` показывает хотя бы одну контрольную точку (локально) ИЛИ
      `/api/experiment/models/checkpoints` возвращает модели (облако)
- [ ] JSON рабочего процесса находится в формате API
- [ ] `check_deps.py` сообщает `is_ready: true` (или только `node_check_skipped`
      в облачном бесплатном тарифе)
- [ ] Тестовый запуск небольшого workflow завершается; выводы попадают в `--output-dir`