---
title: "Heartmula — HeartMuLa: генерация песен в стиле Suno из текста и тегов"
sidebar_label: "Heartmula"
description: "HeartMuLa: Suno‑подобная генерация песен из текстов + тегов"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Heartmula

HeartMuLa: генерация песен в стиле Suno по текстам и тегам.

## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/media/heartmula` |
| Version | `1.0.0` |
| Platforms | linux, macos, windows |
| Tags | `music`, `audio`, `generation`, `ai`, `heartmula`, `heartcodec`, `lyrics`, `songs` |
| Related skills | `audiocraft` |

## Ссылка: полный SKILL.md

:::info
Ниже представлено полное определение навыка, которое Hermes загружает при его активации. Это то, что агент видит как инструкции, когда навык активен.
:::

# HeartMuLa — открытая генерация музыки

## Обзор
HeartMuLa — это семейство открытых моделей музыкального фундамента (Apache-2.0), генерирующих музыку на основе текста и тегов, с поддержкой нескольких языков. Генерирует полные песни из текста + тегов. Сравнимо с Suno для открытого кода. Включает:
- **HeartMuLa** — языковая модель музыки (3B/7B) для генерации по тексту + тегам
- **HeartCodec** — 12.5 Гц музыкальный кодек для высококачественной реконструкции аудио
- **HeartTranscriptor** — транскрипция текста на основе Whisper
- **HeartCLAP** — модель выравнивания аудио‑текст

## Когда использовать
- Пользователь хочет генерировать музыку/песни по текстовым описаниям
- Пользователь ищет открытый аналог Suno
- Пользователь хочет локальную/офлайн‑генерацию музыки
- Пользователь задаёт вопросы о HeartMuLa, heartlib или генерации AI‑музыки

## Требования к оборудованию
- **Минимум**: 8 ГБ VRAM с `--lazy_load true` (поочерёдная загрузка/выгрузка моделей)
- **Рекомендовано**: 16 ГБ+ VRAM для комфортного использования одной GPU
- **Мног GPU**: используйте `--mula_device cuda:0 --codec_device cuda:1` для распределения по GPU
- 3 B модель с lazy_load достигает пика ~6.2 ГБ VRAM

## Шаги установки

### 1. Клонирование репозитория
```bash
cd ~/  # or desired directory
git clone https://github.com/HeartMuLa/heartlib.git
cd heartlib
```

### 2. Создание виртуального окружения (требуется Python 3.10)
```bash
uv venv --python 3.10 .venv
. .venv/bin/activate
uv pip install -e .
```

### 3. Исправление проблем совместимости зависимостей

**IMPORTANT**: По состоянию на февраль 2026 зафиксированные зависимости конфликтуют с более новыми пакетами. Примените следующие исправления:

```bash
# Upgrade datasets (old version incompatible with current pyarrow)
uv pip install --upgrade datasets

# Upgrade transformers (needed for huggingface-hub 1.x compatibility)
uv pip install --upgrade transformers
```

### 4. Патч исходного кода (требуется для transformers 5.x)

**Patch 1 – исправление кэша RoPE** в `src/heartlib/heartmula/modeling_heartmula.py`:

В методе `setup_caches` класса `HeartMuLa` добавьте переинициализацию RoPE после блока `try/except` с `reset_caches` и перед блоком `with device:`:

```python
# Re-initialize RoPE caches that were skipped during meta-device loading
from torchtune.models.llama3_1._position_embeddings import Llama3ScaledRoPE
for module in self.modules():
    if isinstance(module, Llama3ScaledRoPE) and not module.is_cache_built:
        module.rope_init()
        module.to(device)
```

**Почему**: `from_pretrained` сначала создаёт модель на meta‑устройстве; `Llama3ScaledRoPE.rope_init()` пропускает построение кэша на meta‑тензорах, после загрузки весов на реальное устройство кэш больше не создаётся.

**Patch 2 – исправление загрузки HeartCodec** в `src/heartlib/pipelines/music_generation.py`:

Добавьте `ignore_mismatched_sizes=True` ко всем вызовам `HeartCodec.from_pretrained()` (их 2: eager‑load в `__init__` и lazy‑load в свойстве `codec`).

**Почему**: Буферы `initted` VQ‑кодека имеют форму `[1]` в контрольной точке и `[]` в модели. Данные одинаковы, только скаляр vs 0‑d тензор. Игнорировать безопасно.

### 5. Скачивание контрольных точек моделей
```bash
cd heartlib  # project root
hf download --local-dir './ckpt' 'HeartMuLa/HeartMuLaGen'
hf download --local-dir './ckpt/HeartMuLa-oss-3B' 'HeartMuLa/HeartMuLa-oss-3B-happy-new-year'
hf download --local-dir './ckpt/HeartCodec-oss' 'HeartMuLa/HeartCodec-oss-20260123'
```

Все 3 можно скачивать параллельно. Общий размер — несколько гигабайт.

## GPU / CUDA

HeartMuLa использует CUDA по умолчанию (`--mula_device cuda --codec_device cuda`). Дополнительная настройка не требуется, если у пользователя есть GPU NVIDIA с поддержкой PyTorch CUDA.

- Установленный `torch==2.4.1` уже включает поддержку CUDA 12.1
- `torchtune` может показывать версию `0.4.0+cpu` — это лишь метаданные пакета, он всё равно использует CUDA через PyTorch
- Чтобы убедиться, что используется GPU, ищите строки «CUDA memory» в выводе (например, «CUDA memory before unloading: 6.20 GB»)
- **Нет GPU?** Можно запустить на CPU с `--mula_device cpu --codec_device cpu`, но генерация будет **чрезвычайно медленной** (30‑60+ минут для одной песни против ~4 минут на GPU). Режим CPU также требует значительного ОЗУ (~12 ГБ+ свободных). Если у пользователя нет GPU NVIDIA, порекомендуй облачный сервис GPU (Google Colab free tier с T4, Lambda Labs и т.п.) или онлайн‑демо по адресу https://heartmula.github.io/.

## Использование

### Базовая генерация
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

### Формат ввода

**Теги** (через запятую, без пробелов):
```
piano,happy,wedding,synthesizer,romantic
```
или
```
rock,energetic,guitar,drums,male-vocal
```

**Текст песни** (используй структурные теги в квадратных скобках):
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

### Ключевые параметры
| Parameter | Default | Description |
|-----------|---------|-------------|
| `--max_audio_length_ms` | 240000 | Максимальная длина в мс (240 s = 4 мин) |
| `--topk` | 50 | Сэмплинг top‑k |
| `--temperature` | 1.0 | Температура сэмплинга |
| `--cfg_scale` | 1.5 | Масштаб классификатора‑свободного руководства |
| `--lazy_load` | false | Загрузка/выгрузка моделей по требованию (экономит VRAM) |
| `--mula_dtype` | bfloat16 | Тип данных для HeartMuLa (рекомендовано bf16) |
| `--codec_dtype` | float32 | Тип данных для HeartCodec (рекомендовано fp32 для качества) |

### Производительность
- RTF (Real-Time Factor) ≈ 1.0 — 4‑минутная песня генерируется ~4 минуты
- Вывод: MP3, 48 kHz стерео, 128 kbps

## Подводные камни
1. **Не используйте bf16 для HeartCodec** — ухудшает качество аудио. Используйте fp32 (по умолчанию).
2. **Теги могут игнорироваться** — известная проблема (#90). Текст песни обычно доминирует; экспериментируй с порядком тегов.
3. **Triton недоступен на macOS** — ускорение GPU только на Linux/CUDA.
4. **Несовместимость с RTX 5080** зафиксирована в upstream‑issues.
5. Конфликты фиксированных зависимостей требуют ручных обновлений и патчей, описанных выше.

## Ссылки
- Репозиторий: https://github.com/HeartMuLa/heartlib
- Модели: https://huggingface.co/HeartMuLa
- Статья: https://arxiv.org/abs/2601.10547
- Лицензия: Apache-2.0