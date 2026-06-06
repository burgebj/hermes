---
title: "Comfyui"
sidebar_label: "Comfyui"
description: "Створюй зображення, відео та аудіо за допомогою ComfyUI — встановлюй, запускай, керуй вузлами/моделями, виконуй робочі процеси з ін’єкцією параметрів"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Comfyui

Генеруй зображення, відео та аудіо за допомогою ComfyUI — встанови, запусти, керуй вузлами/моделями, запускай робочі процеси з ін’єкцією параметрів. Використовуй офіційний `comfy-cli` для управління життєвим циклом та прямий REST/WebSocket API для виконання.
## Метадані навички

| | |
|---|---|
| Джерело | Bundled (installed by default) |
| Шлях | `skills/creative/comfyui` |
| Версія | `5.1.0` |
| Автор | ['kshitijk4poor', 'alt-glitch', 'purzbeats'] |
| Ліцензія | MIT |
| Платформи | macos, linux, windows |
| Теги | `comfyui`, `image-generation`, `stable-diffusion`, `flux`, `sd3`, `wan-video`, `hunyuan-video`, `creative`, `generative-ai`, `video-generation` |
| Пов'язані навички | [`stable-diffusion-image-generation`](/docs/user-guide/skills/optional/mlops/mlops-stable-diffusion), `image_gen` |
:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# ComfyUI

Генеруй зображення, відео, аудіо та 3D‑контент за допомогою ComfyUI, використовуючи
офіційний `comfy-cli` для налаштування / життєвого циклу та прямий REST/WebSocket API
для виконання робочих процесів.
## Що в цьому skill

**Документація (`references/`):**

- `official-cli.md` — кожна команда `comfy …` разом із прапорцями
- `rest-api.md` — REST‑ і WebSocket‑кінцеві точки (локальні + хмарні), схеми payload
- `workflow-format.md` — API‑формат JSON, типи загальних вузлів, відображення параметрів
- `template-integrity.md` — перетворення `comfyui-workflow-templates` з формату редактора у API‑формат: обходи Reroute, дотичні ключі dynamic‑input (`values.a`, `resize_type.width`), особливості хмари (302 redirect, 1 одночасна безкоштовна задача, обмеження VRAM 1080 p), сумісний з Discord ffmpeg‑stitch. Автор — [@purzbeats](https://github.com/purzbeats). Завантажуй це щоразу, коли починаєш з офіційного шаблону.

**Скрипти (`scripts/`):**

| Script | Призначення |
|--------|-------------|
| `_common.py` | Спільний HTTP, хмарна маршрутизація, каталоги вузлів (не запускати безпосередньо) |
| `hardware_check.py` | Перевірка GPU/VRAM/диска → рекомендація локально чи Comfy Cloud |
| `comfyui_setup.sh` | Перевірка обладнання + comfy‑cli + встановлення ComfyUI + запуск + верифікація |
| `extract_schema.py` | Читання workflow → список керованих параметрів + залежностей моделей |
| `check_deps.py` | Перевірка workflow проти запущеного сервера → список відсутніх вузлів/моделей |
| `auto_fix_deps.py` | Запуск `check_deps`, потім `comfy node install` / `comfy model download` |
| `run_workflow.py` | Вставка параметрів, відправка, моніторинг, завантаження результатів (HTTP або WS) |
| `run_batch.py` | Відправка workflow N разів зі sweep‑ами, паралельно до рівня твого тарифу |
| `ws_monitor.py` | Переглядач WebSocket у реальному часі для виконуваних задач (живий прогрес) |
| `health_check.py` | Запуск чек‑ліста верифікації — comfy‑cli + сервер + моделі + smoke‑test |
| `fetch_logs.py` | Отримання traceback / повідомлень статусу для заданого `prompt_id` |

**Прикладні workflow (`workflows/`):** SD 1.5, SDXL, Flux Dev, SDXL img2img, SDXL inpaint, ESRGAN upscale, AnimateDiff video, Wan T2V. Дивись `workflows/README.md`.
## Коли використовувати

- Користувач просить згенерувати зображення за допомогою Stable Diffusion, SDXL, Flux, SD3 тощо.
- Користувач хоче запустити конкретний файл робочого процесу ComfyUI.
- Користувач хоче ланцюжок генеративних кроків (txt2img → upscale → face restore).
- Користувач потребує ControlNet, inpainting, img2img або інші просунуті конвеєри.
- Користувач просить керувати чергою ComfyUI, перевіряти моделі або встановлювати власні ноди.
- Користувач хоче генерувати відео/аудіо/3D за допомогою AnimateDiff, Hunyuan, Wan, AudioCraft тощо.
## Архітектура: два рівні

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

**Чому два рівні?** Офіційний CLI чудово підходить для встановлення та керування сервером, але має мінімальну підтримку виконання робочих процесів. REST/WS API заповнює цю прогалину — скрипти виконують ін’єкцію параметрів, моніторинг виконання та завантаження результатів, чого CLI не робить.
## Швидкий старт

### Виявлення середовища

```bash
# What's available?
command -v comfy >/dev/null 2>&1 && echo "comfy-cli: installed"
curl -s http://127.0.0.1:8188/system_stats 2>/dev/null && echo "server: running"

# Can this machine run ComfyUI locally? (GPU/VRAM/disk check)
python3 scripts/hardware_check.py
```

Якщо нічого не встановлено, дивись розділ **Setup & Onboarding** нижче — але спочатку завжди виконуй перевірку апаратного забезпечення.

### Однорядкова перевірка стану

```bash
python3 scripts/health_check.py
# → JSON: comfy_cli on PATH? server reachable? at least one checkpoint? smoke-test passes?
```
## Основний робочий процес

### Крок 1: Отримати JSON робочого процесу у форматі API

Робочі процеси мають бути у форматі API (кожен вузол має `class_type`). Вони беруться з:

- ComfyUI web UI → **Workflow → Export (API)** (новіший інтерфейс) або
  кнопка «Save (API Format)» у застарілому інтерфейсі (старіший UI)
- Каталог `workflows/` цього інструменту (готові до запуску приклади)
- Завантаження спільноти (civitai, Reddit, Discord) — зазвичай у форматі редактора, їх треба завантажити в ComfyUI, а потім повторно експортувати

Формат редактора (масиви `nodes` і `links` верхнього рівня) **не є безпосередньо виконуваним**. Скрипти виявляють це і повідомляють про необхідність повторного експорту.

### Крок 2: Переглянути, що можна контролювати

```bash
python3 scripts/extract_schema.py workflow_api.json --summary-only
# → {"parameter_count": 12, "has_negative_prompt": true, "has_seed": true, ...}

python3 scripts/extract_schema.py workflow_api.json
# → full schema with parameters, model deps, embedding refs
```

### Крок 3: Запустити з параметрами

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

`-1` для `seed` (або пропуск його за допомогою `--randomize-seed`) генерує нове випадкове зерно при кожному запуску.

### Крок 4: Представити результати

Скрипти виводять JSON у `stdout`, описуючи кожен вихідний файл:

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
## Decision Tree

| User says | Tool | Command |
|-----------|------|---------|
| **Життєвий цикл (use comfy-cli)** | | |
| «install ComfyUI» | comfy-cli | `bash scripts/comfyui_setup.sh` |
| «start ComfyUI» | comfy-cli | `comfy launch --background` |
| «stop ComfyUI» | comfy-cli | `comfy stop` |
| «install X node» | comfy-cli | `comfy node install <name>` |
| «download X model» | comfy-cli | `comfy model download --url <url> --relative-path models/checkpoints` |
| «list installed models» | comfy-cli | `comfy model list` |
| «list installed nodes» | comfy-cli | `comfy node show installed` |
| **Виконання (use scripts)** | | |
| «is everything ready?» | script | `health_check.py` (optionally with `--workflow X --smoke-test`) |
| «what can I change in this workflow?» | script | `extract_schema.py W.json` |
| «check if W's deps are met» | script | `check_deps.py W.json` |
| «fix missing deps» | script | `auto_fix_deps.py W.json` |
| «generate an image» | script | `run_workflow.py --workflow W --args '{...}'` |
| «use this image» (img2img) | script | `run_workflow.py --input-image image=./x.png ...` |
| «8 variations with random seeds» | script | `run_batch.py --count 8 --randomize-seed ...` |
| «show me live progress» | script | `ws_monitor.py --prompt-id <id>` |
| «fetch the error from job X» | script | `fetch_logs.py <prompt_id>` |
| **Прямий REST** | | |
| «what's in the queue?» | REST | `curl http://HOST:8188/queue` (local) or `--host https://cloud.comfy.org` |
| «cancel that» | REST | `curl -X POST http://HOST:8188/interrupt` |
| «free GPU memory» | REST | `curl -X POST http://HOST:8188/free` |
## Налаштування та onboarding

Коли користувач просить налаштувати ComfyUI, **першою дією треба запитати, чи
він хоче Comfy Cloud (хостинг, без встановлення, API‑ключ) чи Local (встановити
ComfyUI на свою машину)**. Не запускай команди встановлення або перевірки
апаратури, доки він не відповів.

**Офіційна документація:** https://docs.comfy.org/installation
**Документація CLI:** https://docs.comfy.org/comfy-cli/getting-started
**Документація Cloud:** https://docs.comfy.org/get_started/cloud
**Cloud API:** https://docs.comfy.org/development/cloud/overview

### Крок 0: Запитати Local vs Cloud (ЗАВЖДИ ПЕРШИЙ)

Рекомендований скрипт:

> “Ти хочеш запускати ComfyUI локально на своїй машині, чи використовувати Comfy Cloud?
>
> - **Comfy Cloud** — хостинг на RTX 6000 Pro GPU, усі поширені моделі попередньо встановлені,
>   без налаштувань. Потрібен API‑ключ (платна підписка потрібна для фактичного запуску
>   робочих процесів; безкоштовний тариф лише для читання). Найкраще, якщо у тебе немає потужного GPU.
> - **Local** — безкоштовно, але твоя машина ПОВИННА відповідати вимогам апаратури:
>   - NVIDIA GPU з **≥6 GB VRAM** (≥8 GB для SDXL, ≥12 GB для Flux/video), АБО
>   - AMD GPU з підтримкою ROCm (Linux), АБО
>   - Apple Silicon Mac (M1+) з **≥16 GB уніфікованої пам’яті** (рекомендовано ≥32 GB).
>   - Intel Mac та машини без GPU НЕ працюватимуть — використай Cloud.
>
> Що ти обираєш?”

Маршрутизація:

- **Cloud** → перейти до **Шляху A**.
- **Local** → спочатку виконати перевірку апаратури, потім вибрати шлях B–E залежно від результату.
- **Не впевнений** → виконати перевірку апаратури і дозволити результату визначити шлях.

### Крок 1: Перевірка апаратури (ТІЛЬКИ якщо користувач обрав Local)

```bash
python3 scripts/hardware_check.py --json
# Optional: also probe `torch` for actual CUDA/MPS:
python3 scripts/hardware_check.py --json --check-pytorch
```

| Verdict    | Meaning                                                       | Action |
|------------|---------------------------------------------------------------|--------|
| `ok`       | ≥8 GB VRAM (дискретна) АБО ≥32 GB уніфікована (Apple Silicon) | Локальна інсталяція — використати `comfy_cli_flag` зі звіту |
| `marginal` | SD1.5 працює; SDXL щільно; Flux/video навряд чи                | Локально OK для легких процесів, інакше **Шлях A (Cloud)** |
| `cloud`    | Немає придатного GPU, <6 GB VRAM, <16 GB уніфіковано, Intel Mac, Rosetta Python | **Перейти на Cloud**, якщо користувач явно не вимагає локальну інсталяцію |

Скрипт також виводить `wsl: true` (WSL2 з NVIDIA passthrough) та `rosetta: true`
(x86_64 Python на Apple Silicon — треба переустановити як ARM64).

Якщо verdict `cloud`, а користувач хоче локально, не продовжуй мовчки.
Покажи масив `notes` дослівно і запитай, чи хоче він (a) перейти на Cloud
або (b) примусово встановити локально (може отримати OOM або дуже повільну
роботу на сучасних моделях).

### Вибір шляху інсталяції

Спочатку використай перевірку апаратури. Таблиця нижче — резервний варіант,
коли користувач вже повідомив про свою апаратуру:

| Situation | Recommended Path |
|-----------|------------------|
| `verdict: cloud` з перевірки апаратури | **Шлях A: Comfy Cloud** |
| Немає GPU / хочеш спробувати без зобов’язань | **Шлях A: Comfy Cloud** |
| Windows + NVIDIA + нетехнічний | **Шлях B: ComfyUI Desktop** |
| Windows + NVIDIA + технічний | **Шлях C: Portable** або **Шлях D: comfy-cli** |
| Linux + будь‑який GPU | **Шлях D: comfy-cli** (найпростіший) |
| macOS + Apple Silicon | **Шлях B: Desktop** або **Шлях D: comfy-cli** |
| Headless / сервер / CI / агенти | **Шлях D: comfy-cli** |

Для повністю автоматизованого шляху (перевірка апаратури → інсталяція → запуск → верифікація):

```bash
bash scripts/comfyui_setup.sh
# Or with overrides:
bash scripts/comfyui_setup.sh --m-series --port=8190 --workspace=/data/comfy
```

Він запускає `hardware_check.py` всередині, відмовляється встановлювати локально,
коли verdict `cloud` (крім випадку `--force-cloud-override`), підбирає правильний
флаг `comfy-cli` і віддає перевагу `pipx`/`uvx` над глобальним `pip`,
щоб не забруднювати системний Python.

---

### Шлях A: Comfy Cloud (без локальної інсталяції)

Для користувачів без потужного GPU або які хочуть нульове налаштування.
Хостинг на RTX 6000 Pro.

**Документація:** https://docs.comfy.org/get_started/cloud

1. Зареєструйся на https://comfy.org/cloud
2. Згенеруй API‑ключ на https://platform.comfy.org/login
3. Встанови ключ:
   ```bash
   export COMFY_CLOUD_API_KEY="comfyui-xxxxxxxxxxxx"
   ```
4. Запусти робочі процеси:
   ```bash
   python3 scripts/run_workflow.py \
     --workflow workflows/flux_dev_txt2img.json \
     --args '{"prompt": "..."}' \
     --host https://cloud.comfy.org \
     --output-dir ./outputs
   ```

**Тарифи:** https://www.comfy.org/cloud/pricing
**Одночасні завдання:** Free/Standard 1, Creator 3, Pro 5. Безкоштовний тариф
**не дозволяє запускати робочі процеси через API** — лише перегляд моделей.
Платна підписка потрібна для `/api/prompt`, `/api/upload/*`, `/api/view` тощо.

---

### Шлях B: ComfyUI Desktop (Windows / macOS)

Однокліковий інсталятор для нетехнічних користувачів. Поки що Beta.

**Документація:** https://docs.comfy.org/installation/desktop
- **Windows (NVIDIA):** https://download.comfy.org/windows/nsis/x64
- **macOS (Apple Silicon):** https://comfy.org

Linux **не підтримується** для Desktop — використай Шлях D.

---

### Шлях C: ComfyUI Portable (лише Windows)

**Документація:** https://docs.comfy.org/installation/comfyui_portable_windows

Завантажити з https://github.com/comfyanonymous/ComfyUI/releases, розпакувати,
запустити `run_nvidia_gpu.bat`. Оновлення через `update/update_comfyui_stable.bat`.

---

### Шлях D: comfy-cli (всі платформи — рекомендовано для агентів)

Офіційний CLI — найкращий шлях для безголових/автоматизованих налаштувань.

**Документація:** https://docs.comfy.org/comfy-cli/getting-started

#### Встановлення comfy-cli

```bash
# Recommended:
pipx install comfy-cli
# Or use uvx without installing:
uvx --from comfy-cli comfy --help
# Or (if pipx/uvx unavailable):
pip install --user comfy-cli
```

Вимкнути аналітику без інтерактивного запиту:
```bash
comfy --skip-prompt tracking disable
```

#### Встановлення ComfyUI

```bash
comfy --skip-prompt install --nvidia              # NVIDIA (CUDA)
comfy --skip-prompt install --amd                 # AMD (ROCm, Linux)
comfy --skip-prompt install --m-series            # Apple Silicon (MPS)
comfy --skip-prompt install --cpu                 # CPU only (slow)
comfy --skip-prompt install --nvidia --fast-deps  # uv-based dep resolution
```

Типове розташування: `~/comfy/ComfyUI` (Linux), `~/Documents/comfy/ComfyUI`
(macOS/Win). Перевизначити можна через `comfy --workspace /custom/path install`.

#### Запуск / верифікація

```bash
comfy launch --background                       # background daemon on :8188
comfy launch -- --listen 0.0.0.0 --port 8190    # LAN-accessible custom port
curl -s http://127.0.0.1:8188/system_stats      # health check
```

---

### Шлях E: Ручна інсталяція (просунутий / непідтримуване обладнання)

Для Ascend NPU, Cambricon MLU, Intel Arc або іншого непідтримуваного обладнання.

**Документація:** https://docs.comfy.org/installation/manual_install

```bash
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI
pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu130
pip install -r requirements.txt
python main.py
```

---

### Після інсталяції: Завантаження моделей

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

Список встановлених: `comfy model list`.

### Після інсталяції: Встановлення кастомних нод

```bash
comfy node install comfyui-impact-pack             # popular utility pack
comfy node install comfyui-animatediff-evolved     # video generation
comfy node install comfyui-controlnet-aux          # ControlNet preprocessors
comfy node install comfyui-essentials              # common helpers
comfy node update all
comfy node install-deps --workflow=workflow.json   # install everything a workflow needs
```

### Після інсталяції: Перевірка

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
## Завантаження зображення (img2img / Inpainting)

Найпростіший спосіб — використати `--input-image` з `run_workflow.py`:

```bash
python3 scripts/run_workflow.py \
  --workflow workflows/sdxl_img2img.json \
  --input-image image=./photo.png \
  --args '{"prompt": "make it cyberpunk", "denoise": 0.6}'
```

Прапорець завантажує `photo.png`, а потім вставляє його серверну назву файлу у
параметр схеми, який названий `image`. Для inpainting передай обидва:

```bash
python3 scripts/run_workflow.py \
  --workflow workflows/sdxl_inpaint.json \
  --input-image image=./photo.png \
  --input-image mask_image=./mask.png \
  --args '{"prompt": "fill with flowers"}'
```

Ручне завантаження через REST:
```bash
curl -X POST "http://127.0.0.1:8188/upload/image" \
  -F "image=@photo.png" -F "type=input" -F "overwrite=true"
# Returns: {"name": "photo.png", "subfolder": "", "type": "input"}

# Cloud equivalent:
curl -X POST "https://cloud.comfy.org/api/upload/image" \
  -H "X-API-Key: $COMFY_CLOUD_API_KEY" \
  -F "image=@photo.png" -F "type=input" -F "overwrite=true"
```
## Специфіка хмари

- **Базовий URL:** `https://cloud.comfy.org`
- **Аутентифікація:** заголовок `X-API-Key` (або `?token=KEY` для WebSocket)
- **API‑ключ:** встанови змінну `$COMFY_CLOUD_API_KEY` один раз, і скрипти підхоплять її автоматично
- **Завантаження результату:** `/api/view` повертає 302 до підписаного URL; скрипти
  слідують за ним і видаляють `X-API-Key` перед отриманням даних з бекенда сховища
  (не передавай API‑ключ до S3/CloudFront).
- **Відмінності кінцевих точок від локального ComfyUI:**
  - `/api/object_info`, `/api/queue`, `/api/userdata` — **403 у безкоштовному тарифі**; лише платний.
  - `/history` перейменовано на `/history_v2` у хмарі (скрипти маршрутизують автоматично).
  - `/models/<folder>` перейменовано на `/experiment/models/<folder>` у хмарі (скрипти маршрутизують автоматично).
  - `clientId` у WebSocket наразі ігнорується — усі з’єднання для одного користувача отримують однакове широкомовлення. Фільтруй за `prompt_id` на боці клієнта.
  - `subfolder` приймається при завантаженнях, але ігнорується — у хмарі — плоский простір імен.
- **Одночасні завдання:** Free/Standard — 1, Creator — 3, Pro — 5. Черга Extras додається автоматично. Використовуй `run_batch.py --parallel N`, щоб максимально використати свій тариф.
## Керування чергою та системою

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
## Підводні камені

1. **API format required** — кожен скрипт і кінцева точка `/api/prompt` очікують
   JSON у форматі API‑workflow. Скрипти визначають формат редактора (масиви
   `nodes` і `links` верхнього рівня) і підказують переекспортувати через
   «Workflow → Export (API)» (новіший UI) або «Save (API Format)» (старіший UI).

2. **Server must be running** — весь процес виконання потребує запущеного сервера.
   `comfy launch --background` запускає його. Перевірте за допомогою
   `curl http://127.0.0.1:8188/system_stats`.

3. **Model names are exact** — чутливі до регістру, включають розширення файлу.
   `check_deps.py` виконує нечітке зіставлення (з розширенням або без нього та
   префіксом папки), але сам workflow має використовувати канонічну назву.
   Використайте `comfy model list`, щоб дізнатися, що встановлено.

4. **Missing custom nodes** — «class_type not found» означає, що потрібний вузол
   не встановлений. `check_deps.py` повідомляє, який пакет треба встановити;
   `auto_fix_deps.py` виконує інсталяцію за вас.

5. **Working directory** — `comfy-cli` автоматично визначає робочий простір ComfyUI.
   Якщо команди падають з «no workspace found», використайте
   `comfy --workspace /path/to/ComfyUI <command>` або
   `comfy set-default /path/to/ComfyUI`.

6. **Cloud free-tier API limits** — `/api/prompt`, `/api/view`, `/api/upload/*`,
   `/api/object_info` повертають 403 для безкоштовних акаунтів. `health_check.py` і
   `check_deps.py` обробляють це коректно і виводять зрозуміле повідомлення.

7. **Timeout for video/audio workflows** — автоматично визначається, коли вихідний
   вузол є `VHS_VideoCombine`, `SaveVideo` тощо; за замовчуванням час збільшується
   з 300 s до 900 s. Перевизначте явно за допомогою `--timeout 1800`.

8. **Path traversal in output filenames** — імена файлів, що надходять від сервера,
   проходять через `safe_path_join`, щоб відхилити будь‑яке вихідне за межі
   `--output-dir`. Залишайте цей захист включеним — workflow‑и з кастомними вузлами
   збереження можуть генерувати довільні шляхи.

9. **Workflow JSON is arbitrary code** — кастомні вузли виконують Python, тому
   подання невідомого workflow має той самий рівень довіри, що й `eval`.
   Перевіряйте workflow‑и з ненадійних джерел перед запуском.

10. **Auto-randomized seed** — передайте `seed: -1` у `--args` (або використайте
    `--randomize-seed` і опустіть seed), щоб отримати нове зерно при кожному запуску.
    Фактичне зерно записується у `stderr`.

11. **`tracking` prompt** — при першому запуску `comfy` може запитати про аналітику.
    Використайте `comfy --skip-prompt tracking disable`, щоб пропустити її без
    інтерактивності. `comfyui_setup.sh` робить це за вас.
## Перелік перевірок

Використай `python3 scripts/health_check.py`, щоб запустити весь список одразу. Вручну:

- [ ] результат `hardware_check.py` — `ok` АБО користувач явно обрав Comfy Cloud
- [ ] `comfy --version` працює (або `uvx --from comfy-cli comfy --help`)
- [ ] `curl http://HOST:PORT/system_stats` повертає JSON
- [ ] `comfy model list` показує принаймні один checkpoint (локальний) АБО
      `/api/experiment/models/checkpoints` повертає моделі (хмара)
- [ ] JSON робочого процесу у форматі API
- [ ] `check_deps.py` повідомляє `is_ready: true` (або лише `node_check_skipped` у безкоштовному тарифі хмари)
- [ ] Тестовий запуск з малим workflow завершується; вихідні дані потрапляють у `--output-dir`