---
title: "Heartmula — HeartMuLa: генерація пісень у стилі Suno з текстів + тегів"
sidebar_label: "Heartmula"
description: "HeartMuLa: генерація пісень у стилі Suno за текстами та тегами"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Heartmula

HeartMuLa: Suno‑подібна генерація пісень за текстами + тегами.

## Метадані навички

| | |
|---|---|
| Джерело | Bundled (installed by default) |
| Шлях | `skills/media/heartmula` |
| Версія | `1.0.0` |
| Платформи | linux, macos, windows |
| Теги | `music`, `audio`, `generation`, `ai`, `heartmula`, `heartcodec`, `lyrics`, `songs` |
| Пов’язані навички | `audiocraft` |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# HeartMuLa - Open‑Source генерація музики

## Огляд
HeartMuLa — це сімейство відкритих моделей музичної основи (Apache‑2.0), які генерують музику за текстами та тегами, підтримуючи багатомовність. Генерує повні пісні за текстами + тегами. Порівнянна з Suno у відкритому коді. Включає:
- **HeartMuLa** - мовна модель музики (3B/7B) для генерації за текстами + тегами
- **HeartCodec** - 12.5 Hz музичний кодек для високоякісної аудіо‑реконструкції
- **HeartTranscriptor** - транскрипція текстів на базі Whisper
- **HeartCLAP** - модель вирівнювання аудіо‑тексту

## Коли використовувати
- Користувач хоче генерувати музику/пісні за текстовим описом
- Користувач шукає відкриту альтернативу Suno
- Користувач потребує локальної/офлайн‑генерації музики
- Користувач запитує про HeartMuLa, heartlib або AI‑генерацію музики

## Вимоги до обладнання
- **Мінімум**: 8 GB VRAM з `--lazy_load true` (послідовне завантаження/вивантаження моделей)
- **Рекомендовано**: 16 GB+ VRAM для комфортного використання однієї GPU
- **Multi‑GPU**: використай `--mula_device cuda:0 --codec_device cuda:1` для розподілу навантаження між GPU
- 3B модель з lazy_load досягає піку ~6.2 GB VRAM

## Кроки встановлення

### 1. Клонування репозиторію
```bash
cd ~/  # or desired directory
git clone https://github.com/HeartMuLa/heartlib.git
cd heartlib
```

### 2. Створення віртуального середовища (потрібен Python 3.10)
```bash
uv venv --python 3.10 .venv
. .venv/bin/activate
uv pip install -e .
```

### 3. Виправлення проблем сумісності залежностей

**IMPORTANT**: станом на лютий 2026 закріплені залежності конфліктують із новішими пакетами. Застосуй ці виправлення:

```bash
# Upgrade datasets (old version incompatible with current pyarrow)
uv pip install --upgrade datasets

# Upgrade transformers (needed for huggingface-hub 1.x compatibility)
uv pip install --upgrade transformers
```

### 4. Патч вихідного коду (потрібно для transformers 5.x)

**Patch 1 - виправлення кешу RoPE** у `src/heartlib/heartmula/modeling_heartmula.py`:

У методі `setup_caches` класу `HeartMuLa` додай повторну ініціалізацію RoPE після блоку `try/except` з `reset_caches` і перед блоком `with device:`:

```python
# Re-initialize RoPE caches that were skipped during meta-device loading
from torchtune.models.llama3_1._position_embeddings import Llama3ScaledRoPE
for module in self.modules():
    if isinstance(module, Llama3ScaledRoPE) and not module.is_cache_built:
        module.rope_init()
        module.to(device)
```

**Чому**: `from_pretrained` спочатку створює модель на meta‑пристрої; `Llama3ScaledRoPE.rope_init()` пропускає побудову кешу на meta‑тензорах, і після завантаження ваг на реальний пристрій кеш не відбудується.

**Patch 2 - виправлення завантаження HeartCodec** у `src/heartlib/pipelines/music_generation.py`:

Додай `ignore_mismatched_sizes=True` до ВСІХ викликів `HeartCodec.from_pretrained()` (є 2: eager‑load у `__init__` та lazy‑load у властивості `codec`).

**Чому**: буфери `initted` VQ‑кодової книги мають форму `[1]` у контрольній точці проти `[]` у моделі. Дані однакові, лише скаляр проти 0‑д тензора. Безпечно ігнорувати.

### 5. Завантаження контрольних точок моделей
```bash
cd heartlib  # project root
hf download --local-dir './ckpt' 'HeartMuLa/HeartMuLaGen'
hf download --local-dir './ckpt/HeartMuLa-oss-3B' 'HeartMuLa/HeartMuLa-oss-3B-happy-new-year'
hf download --local-dir './ckpt/HeartCodec-oss' 'HeartMuLa/HeartCodec-oss-20260123'
```

Усі 3 можна завантажити паралельно. Загальний розмір — кілька ГБ.

## GPU / CUDA

HeartMuLa за замовчуванням використовує CUDA (`--mula_device cuda --codec_device cuda`). Додаткових налаштувань не потрібно, якщо у користувача є NVIDIA GPU з підтримкою PyTorch CUDA.

- Встановлений `torch==2.4.1` вже включає підтримку CUDA 12.1
- `torchtune` може показувати версію `0.4.0+cpu` — це лише метадані пакету, він все одно використовує CUDA через PyTorch
- Щоб перевірити, чи використовується GPU, шукай рядки «CUDA memory» у виводі (наприклад, «CUDA memory before unloading: 6.20 GB»)
- **Немає GPU?** Можна запустити на CPU з `--mula_device cpu --codec_device cpu`, але очікуй **надзвичайно повільну** генерацію (може зайняти 30‑60 хвилин для однієї пісні проти ~4 хвилин на GPU). CPU‑режим також потребує значної оперативної пам’яті (~12 GB+ вільно). Якщо користувач не має NVIDIA GPU, порекомендуй хмарний GPU‑сервіс (Google Colab free tier з T4, Lambda Labs тощо) або онлайн‑демо за адресою https://heartmula.github.io/.

## Використання

### Базова генерація
```bash
cd heartlib
. .venv/bin/activate
python ./examples/run_music_generation.py \
  --model_path=./ckpt \
  --version="3B" \
  --lyrics="./assets/lyrics.txt" \
  --tags="./assets/tags.txt" \
  --save_path="./assets/output.mp3" \
  --lazy_load true
```

### Форматування вводу

**Теги** (через кому, без пробілів):
```
piano,happy,wedding,synthesizer,romantic
```
або
```
rock,energetic,guitar,drums,male-vocal
```

**Текст пісні** (використовуй структурні теги в квадратних дужках):
```
[Intro]

[Verse]
Your lyrics here...

[Chorus]
Chorus lyrics...

[Bridge]
Bridge lyrics...

[Outro]
```

### Ключові параметри
| Параметр | За замовчуванням | Опис |
|-----------|-------------------|------|
| `--max_audio_length_ms` | 240000 | Максимальна довжина в мс (240 s = 4 хв) |
| `--topk` | 50 | Top‑k семплінг |
| `--temperature` | 1.0 | Температура семплінгу |
| `--cfg_scale` | 1.5 | Масштаб Classifier‑free guidance |
| `--lazy_load` | false | Завантаження/вивантаження моделей за потребою (економія VRAM) |
| `--mula_dtype` | bfloat16 | Тип даних для HeartMuLa (рекомендовано bf16) |
| `--codec_dtype` | float32 | Тип даних для HeartCodec (рекомендовано fp32 для якості) |

### Продуктивність
- RTF (Real‑Time Factor) ≈ 1.0 — 4‑хвилинна пісня генерується ~4 хвилини
- Вихід: MP3, 48 kHz стерео, 128 kbps

## Підводні камені
1. **Не використовуйте bf16 для HeartCodec** — це погіршує якість аудіо. Використовуйте fp32 (за замовчуванням).
2. **Теги можуть ігноруватись** — відома проблема (#90). Тексти переважають; експериментуй з порядком тегів.
3. **Triton недоступний на macOS** — лише Linux/CUDA для GPU‑прискорення.
4. **Несумісність RTX 5080** зафіксовано в upstream‑issues.
5. Конфлікти закріплених залежностей вимагають ручних оновлень і патчів, описаних вище.

## Посилання
- Репо: https://github.com/HeartMuLa/heartlib
- Моделі: https://huggingface.co/HeartMuLa
- Стаття: https://arxiv.org/abs/2601.10547
- Ліцензія: Apache-2.0