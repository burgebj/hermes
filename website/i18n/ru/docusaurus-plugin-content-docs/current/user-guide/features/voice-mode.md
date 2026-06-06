---
sidebar_position: 10
title: "Голосовой режим"
description: "Голосовые разговоры в реальном времени с Hermes Agent — CLI, Telegram, Discord (личные сообщения, текстовые каналы и голосовые каналы)"
---

# Голосовой режим

Hermes Agent поддерживает полноценное голосовое взаимодействие в CLI и на платформах обмена сообщениями. Говори с агентом через микрофон, слушай произнесённые ответы и веди живые голосовые беседы в голосовых каналах Discord.

Если нужен практический пошаговый гайд с рекомендациями по конфигурации и реальными сценариями использования, смотри [Использовать голосовой режим с Hermes](/guides/use-voice-mode-with-hermes).
## Предварительные требования

Перед использованием голосовых функций убедись, что у тебя есть:

1. **Hermes Agent установлен** — `pip install hermes-agent` (см. [Installation](/getting-started/installation))
2. **Настроен LLM‑provider** — запусти `hermes model` или укажи учётные данные выбранного провайдера в `~/.hermes/.env`
3. **Рабочая базовая конфигурация** — запусти `hermes`, чтобы проверить, что агент отвечает на текст, прежде чем включать голос

:::tip
Каталог `~/.hermes/` и файл `config.yaml` по умолчанию создаются автоматически при первом запуске `hermes`. Тебе нужно создать только `~/.hermes/.env` вручную для API‑ключей.
:::

:::tip Nous Portal covers both
Платная подписка [Nous Portal](/user-guide/features/tool-gateway) предоставляет LLM (шаг 2) **и** OpenAI TTS через шлюз инструментов — отдельный ключ OpenAI не требуется. При свежей установке `hermes setup --portal` подключает оба сразу.
:::
## Обзор

| Функция | Платформа | Описание |
|--------|-----------|----------|
| **Интерактивный голос** | CLI | Нажми Ctrl+B, чтобы записать; агент автоматически определяет тишину и отвечает |
| **Автоматический голосовой ответ** | Telegram, Discord | Агент отправляет озвученный аудиофайл вместе с текстовыми ответами |
| **Голосовой канал** | Discord | Бот присоединяется к VC, слушает речь пользователей и отвечает голосом |
## Требования

### Пакеты Python

```bash
# CLI voice mode (microphone + audio playback)
pip install "hermes-agent[voice]"

# Discord + Telegram messaging (includes discord.py[voice] for VC support)
pip install "hermes-agent[messaging]"

# Premium TTS (ElevenLabs)
pip install "hermes-agent[tts-premium]"

# Local TTS (NeuTTS, optional)
python -m pip install -U neutts[all]

# Everything at once
pip install "hermes-agent[all]"
```

| Extra | Packages | Required For |
|-------|----------|-------------|
| `voice` | `sounddevice`, `numpy` | режим голоса CLI |
| `messaging` | `discord.py[voice]`, `python-telegram-bot`, `aiohttp` | боты Discord и Telegram |
| `tts-premium` | `elevenlabs` | провайдер TTS ElevenLabs |

Опциональный локальный TTS‑провайдер: установи `neutts` отдельно с помощью `python -m pip install -U neutts[all]`. При первом использовании он автоматически скачивает модель.

:::info
`discord.py[voice]` устанавливает **PyNaCl** (для шифрования голоса) и **opus bindings** автоматически. Это необходимо для поддержки голосовых каналов Discord.
:::

### Системные зависимости

```bash
# macOS
brew install portaudio ffmpeg opus
brew install espeak-ng   # for NeuTTS

# Ubuntu/Debian
sudo apt install portaudio19-dev ffmpeg libopus0
sudo apt install espeak-ng   # for NeuTTS
```

| Dependency | Purpose | Required For |
|-----------|---------|-------------|
| **PortAudio** | Ввод с микрофона и воспроизведение аудио | режим голоса CLI |
| **ffmpeg** | Конвертация аудио форматов (MP3 → Opus, PCM → WAV) | все платформы |
| **Opus** | Голосовой кодек Discord | голосовые каналы Discord |
| **espeak-ng** | Бэкенд фонемизатора | локальный провайдер NeuTTS |

### API‑ключи

Add to `~/.hermes/.env`:

```bash
# Speech-to-Text — local provider needs NO key at all
# pip install faster-whisper          # Free, runs locally, recommended
GROQ_API_KEY=your-key                 # Groq Whisper — fast, free tier (cloud)
VOICE_TOOLS_OPENAI_KEY=your-key       # OpenAI Whisper — paid (cloud)

# Text-to-Speech (optional — Edge TTS and NeuTTS work without any key)
ELEVENLABS_API_KEY=***           # ElevenLabs — premium quality
# VOICE_TOOLS_OPENAI_KEY above also enables OpenAI TTS
```

:::tip
Если установлен `faster-whisper`, режим голоса работает без **API‑ключей** для STT. Модель (~150 МБ для `base`) автоматически скачивается при первом использовании.
:::

---
## CLI Voice Mode

Режим голоса доступен как в **классическом CLI** (`hermes chat`), так и в **TUI** (`hermes --tui`). Поведение идентично в обоих случаях — одинаковые слеш‑команды, одинаковое обнаружение тишины VAD, одинаковый потоковый TTS, одинаковый фильтр галлюцинаций. TUI дополнительно пересылает форензик‑логи падений в `~/.hermes/logs/`, чтобы сбои push‑to‑talk на экзотических аудио‑бэкендах можно было отчитаться с полным стек‑трейсом, а не исчезали без следа.

### Быстрый старт

Запусти CLI и включи режим голоса:

```bash
hermes                # Start the interactive CLI
```

Затем используй эти команды внутри CLI:

```
/voice          Toggle voice mode on/off
/voice on       Enable voice mode
/voice off      Disable voice mode
/voice tts      Toggle TTS output
/voice status   Show current state
```

### Как это работает

1. Запусти CLI командой `hermes` и включи режим голоса командой `/voice on`.
2. **Нажми Ctrl+B** — прозвучит сигнал (880 Гц), запись начнётся.
3. **Говори** — полоса уровня аудио в реальном времени показывает твой ввод: `● [▁▂▃▅▇▇▅▂] ❯`.
4. **Перестань говорить** — после 3 секунд тишины запись автоматически остановится.
5. **Два сигнала** (660 Гц) подтверждают окончание записи.
6. Аудио транскрибируется Whisper‑ом и отправляется агенту.
7. Если включён TTS, ответ агента озвучивается.
8. Запись **автоматически перезапускается** — говори снова без нажатия клавиш.

Этот цикл продолжается, пока ты не нажмёшь **Ctrl+B** во время записи (выход из непрерывного режима) или пока 3 последовательные записи не обнаружат отсутствие речи.

:::tip
Клавиша записи настраивается через `voice.record_key` в `~/.hermes/config.yaml` (по умолчанию: `ctrl+b`).
:::

### Обнаружение тишины

Двухэтапный алгоритм определяет, когда ты закончил говорить:

1. **Подтверждение речи** — ждёт аудио выше порога RMS (200) не менее 0,3 с, допускает короткие спады между слогами.
2. **Обнаружение конца** — после подтверждения речи срабатывает через 3,0 с непрерывной тишины.

Если речь не обнаружена вовсе в течение 15 секунд, запись останавливается автоматически.

Параметры `silence_threshold` и `silence_duration` настраиваются в `config.yaml`. Также можно отключить сигналы начала/окончания записи, установив `voice.beep_enabled: false`.

### Потоковый TTS

Когда TTS включён, агент произносит свой ответ **по предложениям** по мере генерации текста — не нужно ждать полного ответа:

1. Сохраняет дельты текста в полные предложения (минимум 20 символов).
2. Убирает markdown‑форматирование и блоки `<think>`.
3. Генерирует и воспроизводит аудио для каждого предложения в реальном времени.

### Фильтр галлюцинаций

Whisper иногда генерирует «фантомный» текст из тишины или фонового шума («Thank you for watching», «Subscribe» и т.п.). Агент отфильтровывает их, используя набор из 26 известных фраз‑галлюцинаций на разных языках и регулярное выражение, улавливающее повторяющиеся варианты.
## Gateway Voice Reply (Telegram & Discord)

Если ты ещё не настроил свои боты для обмена сообщениями, смотри руководства для конкретных платформ:
- [Telegram Setup Guide](../messaging/telegram.md)
- [Discord Setup Guide](../messaging/discord.md)

Запусти gateway, чтобы подключиться к платформам обмена сообщениями:

```bash
hermes gateway        # Start the gateway (connects to configured platforms)
hermes gateway setup  # Interactive setup wizard for first-time configuration
```

### Discord: Каналы vs Личные сообщения

Бот поддерживает два режима взаимодействия в Discord:

| Mode | How to Talk | Mention Required | Setup |
|------|------------|-----------------|-------|
| **Direct Message (DM)** | Открой профиль бота → **Message** | No | Работает сразу |
| **Server Channel** | Пиши в текстовом канале, где присутствует бот | Yes (`@botname`) | Бот должен быть приглашён на сервер |

**DM (рекомендовано для личного использования):** Просто открой личный чат с ботом и пиши — упоминание `@` не требуется. Голосовые ответы и все команды работают так же, как в каналах.

**Server channels:** Бот отвечает только при упоминании `@` (например, `@hermesbyt4 hello`). Убедись, что в всплывающем меню выбрал **пользователя‑бота**, а не роль с тем же именем.

:::tip
Чтобы отключить требование упоминания в каналах сервера, добавь в `~/.hermes/.env`:
```bash
DISCORD_REQUIRE_MENTION=false
```
Или укажи конкретные каналы как свободные (упоминание не требуется):
```bash
DISCORD_FREE_RESPONSE_CHANNELS=123456789,987654321
```
:::

### Commands

Эти команды работают и в Telegram, и в Discord (личные сообщения и текстовые каналы):

```
/voice          Toggle voice mode on/off
/voice on       Voice replies only when you send a voice message
/voice tts      Voice replies for ALL messages
/voice off      Disable voice replies
/voice status   Show current setting
```

### Modes

| Mode | Command | Behavior |
|------|---------|----------|
| `off` | `/voice off` | Текст только (по умолчанию) |
| `voice_only` | `/voice on` | Произносит ответ только когда ты отправляешь голосовое сообщение |
| `all` | `/voice tts` | Произносит ответ на каждое сообщение |

Настройка режима голоса сохраняется между перезапусками gateway.

### Platform Delivery

| Platform | Format | Notes |
|----------|--------|-------|
| **Telegram** | Голосовой пузырь (Opus/OGG) | Воспроизводится прямо в чате. ffmpeg конвертирует MP3 → Opus при необходимости |
| **Discord** | Нативный голосовой пузырь (Opus/OGG) | Воспроизводится в чате как голосовое сообщение пользователя. При сбое API голосового пузыря используется вложенный файл |

---
## Каналы голоса Discord

Самая захватывающая голосовая функция: бот присоединяется к голосовому каналу Discord, слушает, что говорят пользователи, транскрибирует их речь, обрабатывает её через агент и озвучивает ответ обратно в голосовом канале.

### Настройка

#### 1. Разрешения бота Discord

Если у тебя уже настроен бот Discord для текста (см. [Discord Setup Guide](../messaging/discord.md)), нужно добавить голосовые разрешения.

Перейди в [Discord Developer Portal](https://discord.com/developers/applications) → твоё приложение → **Installation** → **Default Install Settings** → **Guild Install**:

**Добавь эти разрешения к уже существующим текстовым разрешениям:**

| Permission | Purpose | Required |
|-----------|---------|----------|
| **Connect** | Присоединяться к голосовым каналам | Yes |
| **Speak** | Воспроизводить TTS‑аудио в голосовых каналах | Yes |
| **Use Voice Activity** | Обнаруживать, когда пользователи говорят | Recommended |

**Обновлённое целочисленное значение разрешений:**

| Level | Integer | What's Included |
|-------|---------|----------------|
| Текст только | `274878286912` | View Channels, Send Messages, Read History, Embeds, Attachments, Threads, Reactions |
| Текст + голос | `274881432640` | All above + Connect, Speak |

**Повтори приглашение бота** с обновлённым URL разрешений:

```
https://discord.com/oauth2/authorize?client_id=YOUR_APP_ID&scope=bot+applications.commands&permissions=274881432640
```

Замени `YOUR_APP_ID` на свой Application ID из Developer Portal.

:::warning
Повторное приглашение бота на сервер, где он уже находится, обновит его разрешения без удаления. Ты не потеряешь данные или конфигурацию.
:::

#### 2. Привилегированные Intent’ы

В [Developer Portal](https://discord.com/developers/applications) → твоё приложение → **Bot** → **Privileged Gateway Intents** включи все три:

| Intent | Purpose |
|--------|---------|
| **Presence Intent** | Обнаруживать статус пользователя (онлайн/офлайн) |
| **Server Members Intent** | Преобразовывать имена пользователей в `DISCORD_ALLOWED_USERS` в числовые ID (при необходимости) |
| **Message Content Intent** | Читать текстовое содержание сообщений в каналах |

**Message Content Intent** обязателен. **Server Members Intent** нужен только если список `DISCORD_ALLOWED_USERS` содержит имена пользователей — если ты используешь числовые ID, его можно оставить OFF. Сопоставление SSRC голосового канала → `user_id` берётся из opcode SPEAKING в голосовом websocket и **не требует** Server Members Intent.

#### 3. Кодек Opus

Библиотека кодека Opus должна быть установлена на машине, где работает шлюз:

```bash
# macOS (Homebrew)
brew install opus

# Ubuntu/Debian
sudo apt install libopus0
```

Бот автоматически загружает кодек из:
- **macOS:** `/opt/homebrew/lib/libopus.dylib`
- **Linux:** `libopus.so.0`

#### 4. Переменные окружения

```bash
# ~/.hermes/.env

# Discord bot (already configured for text)
DISCORD_BOT_TOKEN=your-bot-token
DISCORD_ALLOWED_USERS=your-user-id

# STT — local provider needs no key (pip install faster-whisper)
# GROQ_API_KEY=your-key            # Alternative: cloud-based, fast, free tier

# TTS — optional. Edge TTS and NeuTTS need no key.
# ELEVENLABS_API_KEY=***      # Premium quality
# VOICE_TOOLS_OPENAI_KEY=***  # OpenAI TTS / Whisper
```

### Запуск шлюза

```bash
hermes gateway        # Start with existing configuration
```

Бот должен появиться в Discord в течение нескольких секунд.

### Команды

Используй их в текстовом канале Discord, где присутствует бот:

```
/voice join      Bot joins your current voice channel
/voice channel   Alias for /voice join
/voice leave     Bot disconnects from voice channel
/voice status    Show voice mode and connected channel
```

:::info
Ты должен находиться в голосовом канале перед выполнением `/voice join`. Бот присоединяется к тому же VC, в котором ты находишься.
:::

### Как это работает

Когда бот присоединяется к голосовому каналу, он:

1. **Слушает** аудиопоток каждого пользователя отдельно
2. **Обнаруживает тишину** — 1,5 с тишины после минимум 0,5 с речи запускает обработку
3. **Транскрибирует** аудио через Whisper STT (локально, Groq или OpenAI)
4. **Обрабатывает** через полный конвейер агента (сессия, инструменты, память)
5. **Озвучивает** ответ обратно в голосовом канале через TTS

### Интеграция с текстовым каналом

Когда бот находится в голосовом канале:

- Транскрипты появляются в текстовом канале: `[Voice] @user: what you said`
- Ответы агента отправляются как текст в канал **и** озвучиваются в VC
- Текстовым каналом считается тот, где была выполнена команда `/voice join`

### Предотвращение эхо

Бот автоматически приостанавливает слушатель аудио, пока воспроизводятся TTS‑ответы, чтобы не слышать и не переобрабатывать собственный вывод.

### Управление доступом

Только пользователи, указанные в `DISCORD_ALLOWED_USERS`, могут взаимодействовать через голос. Аудио остальных пользователей игнорируется без звука.

```bash
# ~/.hermes/.env
DISCORD_ALLOWED_USERS=284102345871466496
```

---
## Справочник конфигурации

### config.yaml

```yaml
# Voice recording (CLI)
voice:
  record_key: "ctrl+b"            # Key to start/stop recording
  max_recording_seconds: 120       # Maximum recording length
  auto_tts: false                  # Auto-enable TTS when voice mode starts
  beep_enabled: true               # Play record start/stop beeps
  silence_threshold: 200           # RMS level (0-32767) below which counts as silence
  silence_duration: 3.0            # Seconds of silence before auto-stop

# Speech-to-Text
stt:
  enabled: true                     # set to false to skip auto-transcription —
                                    # the gateway still caches the audio file and
                                    # passes its path to the agent as part of the
                                    # inbound message, useful for custom pipelines
                                    # (diarization, alignment, archival, etc.)
  provider: "local"                  # "local" (free) | "groq" | "openai"
  local:
    model: "base"                    # tiny, base, small, medium, large-v3
  # model: "whisper-1"              # Legacy: used when provider is not set

# Text-to-Speech
tts:
  provider: "edge"                 # "edge" (free) | "elevenlabs" | "openai" | "neutts" | "minimax"
  edge:
    voice: "en-US-AriaNeural"      # 322 voices, 74 languages
  elevenlabs:
    voice_id: "pNInz6obpgDQGcFmaJgB"    # Adam
    model_id: "eleven_multilingual_v2"
  openai:
    model: "gpt-4o-mini-tts"
    voice: "alloy"                 # alloy, echo, fable, onyx, nova, shimmer
    base_url: "https://api.openai.com/v1"  # optional: override for self-hosted or OpenAI-compatible endpoints
  neutts:
    ref_audio: ''
    ref_text: ''
    model: neuphonic/neutts-air-q4-gguf
    device: cpu
```

### Переменные окружения

```bash
# Speech-to-Text providers (local needs no key)
# pip install faster-whisper        # Free local STT — no API key needed
GROQ_API_KEY=...                    # Groq Whisper (fast, free tier)
VOICE_TOOLS_OPENAI_KEY=...         # OpenAI Whisper (paid)

# STT advanced overrides (optional)
STT_GROQ_MODEL=whisper-large-v3-turbo    # Override default Groq STT model
STT_OPENAI_MODEL=whisper-1               # Override default OpenAI STT model
GROQ_BASE_URL=https://api.groq.com/openai/v1     # Custom Groq endpoint
STT_OPENAI_BASE_URL=https://api.openai.com/v1    # Custom OpenAI STT endpoint

# Text-to-Speech providers (Edge TTS and NeuTTS need no key)
ELEVENLABS_API_KEY=***             # ElevenLabs (premium quality)
# VOICE_TOOLS_OPENAI_KEY above also enables OpenAI TTS

# Discord voice channel
DISCORD_BOT_TOKEN=...
DISCORD_ALLOWED_USERS=...
```

### Сравнение провайдеров STT

| provider | Model | Speed | Quality | Cost | API‑key |
|----------|-------|-------|---------|------|---------|
| **Local** | `base` | Быстрая (зависит от CPU/GPU) | Хорошее | Бесплатно | Нет |
| **Local** | `small` | Средняя | Лучше | Бесплатно | Нет |
| **Local** | `large‑v3` | Медленная | Лучшее | Бесплатно | Нет |
| **Groq** | `whisper-large-v3-turbo` | Очень быстрая (~0.5 s) | Хорошее | Бесплатный тариф | Да |
| **Groq** | `whisper-large-v3` | Быстрая (~1 s) | Лучше | Бесплатный тариф | Да |
| **OpenAI** | `whisper-1` | Быстрая (~1 s) | Хорошее | Платно | Да |
| **OpenAI** | `gpt-4o-transcribe` | Средняя (~2 s) | Лучшее | Платно | Да |

Приоритет провайдеров (автоматический фоллбэк): **local** > **groq** > **openai**

### Сравнение провайдеров TTS

| provider | Quality | Cost | Latency | Key Required |
|----------|---------|------|---------|--------------|
| **Edge TTS** | Хорошее | Бесплатно | ~1 s | Нет |
| **ElevenLabs** | Отличное | Платно | ~2 s | Да |
| **OpenAI TTS** | Хорошее | Платно | ~1.5 s | Да |
| **NeuTTS** | Хорошее | Бесплатно | Зависит от CPU/GPU | Нет |

NeuTTS использует конфигурационный блок `tts.neutts`, указанный выше.
## Устранение неполадок

### «No audio device found» (CLI)

PortAudio не установлен:

```bash
brew install portaudio    # macOS
sudo apt install portaudio19-dev  # Ubuntu
```

Если ты запускаешь Hermes внутри Docker на Linux‑рабочем столе, контейнеру также нужен доступ к аудиосокету хоста. См. заметки о [Docker audio bridge](/user-guide/docker#optional-linux-desktop-audio-bridge) для настройки, совместимой с PulseAudio/PipeWire.

### Бот не отвечает в каналах сервера Discord

Бот по умолчанию требует упоминания @ в каналах сервера. Убедись, что ты:

1. Вводишь `@` и выбираешь **пользователя‑бота** (с #дискриминатором), а не **роль** с тем же именем
2. Или используй личные сообщения — упоминание не требуется
3. Или задай `DISCORD_REQUIRE_MENTION=false` в `~/.hermes/.env`

### Бот присоединился к голосовому каналу, но не слышит меня

- Проверь, что твой Discord‑ID находится в `DISCORD_ALLOWED_USERS`
- Убедись, что ты не заглушён в Discord
- Боту нужно событие **SPEAKING** от Discord, прежде чем он сможет сопоставить твой звук — начни говорить в течение нескольких секунд после присоединения

### Бот слышит меня, но не отвечает

- Убедись, что STT доступен: установи `faster-whisper` (ключ не нужен) или задай `GROQ_API_KEY` / `VOICE_TOOLS_OPENAI_KEY`
- Проверь, что модель LLM настроена и доступна
- Просмотри логи шлюза: `tail -f ~/.hermes/logs/gateway.log`

### Бот отвечает текстом, но не в голосовом канале

- Провайдер TTS может давать сбой — проверь API‑ключ и квоту
- Edge TTS (бесплатный, без ключа) используется как запасной (вариант) по умолчанию
- Проверь логи на ошибки TTS

### Whisper возвращает мусорный текст

Фильтр галлюцинаций автоматически отлавливает большинство случаев. Если «призрачные» транскрипты всё ещё появляются:

- Используй более тихую обстановку
- Отрегулируй `silence_threshold` в конфигурации (чем выше — тем менее чувствительно)
- Попробуй другую модель STT