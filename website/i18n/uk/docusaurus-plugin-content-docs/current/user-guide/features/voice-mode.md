---
sidebar_position: 10
title: "Режим голосу"
description: "Реальні голосові розмови в режимі реального часу з Hermes Agent — CLI, Telegram, Discord (DMs, текстові канали та голосові канали)"
---

# Режим голосу

Hermes Agent підтримує повну голосову взаємодію у CLI та на платформах обміну повідомленнями. Спілкуйся з агентом, використовуючи мікрофон, слухай озвучені відповіді та веди живі голосові розмови у голосових каналах Discord.

Якщо потрібен практичний посібник із налаштуванням, рекомендаціями щодо конфігурації та реальними сценаріями використання, дивись [Використання голосового режиму з Hermes](/guides/use-voice-mode-with-hermes).
## Передумови

Перш ніж користуватись голосовими функціями, переконайся, що у тебе є:

1. **Hermes Agent встановлений** — `pip install hermes-agent` (див. [Installation](/getting-started/installation))
2. **Налаштований провайдер LLM** — запусти `hermes model` або вкажи облікові дані обраного провайдера у `~/.hermes/.env`
3. **Працююче базове налаштування** — запусти `hermes`, щоб перевірити, що агент відповідає на текст, перш ніж вмикати голос

:::tip
Каталог `~/.hermes/` та файл `config.yaml` за замовчуванням створюються автоматично під час першого запуску `hermes`. Тобі лише потрібно вручну створити `~/.hermes/.env` для API‑ключів.
:::

:::tip Nous Portal covers both
Платна підписка [Nous Portal](/user-guide/features/tool-gateway) постачає LLM (крок 2) **і** OpenAI TTS через шлюз інструментів (Tool Gateway) — окремий ключ OpenAI не потрібен. При новій інсталяції `hermes setup --portal` підключає обидва одразу.
:::
## Огляд

| Feature | Platform | Description |
|---------|----------|-------------|
| **Інтерактивний голос** | CLI | Натисни `Ctrl+B`, щоб записати; агент автоматично виявляє тишу і відповідає |
| **Автоматична голосова відповідь** | Telegram, Discord | Агент надсилає аудіо разом із текстовими відповідями |
| **Голосовий канал** | Discord | Бот приєднується до голосового каналу, слухає, коли користувачі говорять, і відповідає голосом |
## Вимоги

### Пакети Python

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
| `voice` | `sounddevice`, `numpy` | CLI voice mode |
| `messaging` | `discord.py[voice]`, `python-telegram-bot`, `aiohttp` | Discord & Telegram bots |
| `tts-premium` | `elevenlabs` | ElevenLabs TTS provider |

Опційний локальний провайдер TTS: встанови `neutts` окремо за допомогою `python -m pip install -U neutts[all]`. При першому використанні він автоматично завантажує модель.

:::info
`discord.py[voice]` встановлює **PyNaCl** (для шифрування голосу) та **opus bindings** автоматично. Це необхідно для підтримки голосових каналів Discord.
:::

### Системні залежності

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
| **PortAudio** | Microphone input and audio playback | CLI voice mode |
| **ffmpeg** | Audio format conversion (MP3 → Opus, PCM → WAV) | All platforms |
| **Opus** | Discord voice codec | Discord voice channels |
| **espeak-ng** | Phonemizer backend | Local NeuTTS provider |

### API Keys

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
If `faster-whisper` is installed, voice mode works with **zero API keys** for STT. The model (~150 MB for `base`) downloads automatically on first use.
:::

---
## CLI Voice Mode

Voice mode доступний і в **класичному CLI** (`hermes chat`), і в **TUI** (`hermes --tui`). Поведінка ідентична в обох випадках — однакові slash‑команди, однакове виявлення тиші VAD, однаковий потоковий TTS, один і той же фільтр галюцинацій. TUI додатково пересилає логи краш‑форензіки до `~/.hermes/logs/`, щоб помилки push‑to‑talk на екзотичних аудіо‑бекендах можна було повідомити разом із повним стек‑трейсом, а не просто зникли без сліду.

### Quick Start

Запусти CLI і увімкни голосовий режим:

```bash
hermes                # Start the interactive CLI
```

Потім використай ці команди всередині CLI:

```
/voice          Toggle voice mode on/off
/voice on       Enable voice mode
/voice off      Disable voice mode
/voice tts      Toggle TTS output
/voice status   Show current state
```

### How It Works

1. Запусти CLI командою `hermes` і ввімкни голосовий режим за допомогою `/voice on`
2. **Натисни Ctrl+B** — прозвучить сигнал (880 Hz), запис починається
3. **Говори** — індикатор рівня аудіо в реальному часі показує твоє введення: `● [▁▂▃▅▇▇▅▂] ❯`
4. **Перестань говорити** — після 3 секунд тиші запис автоматично зупиняється
5. **Два сигнали** (660 Hz) підтверджують, що запис завершено
6. Аудіо транскрибується Whisper‑ом і надсилається агенту
7. Якщо ввімкнено TTS, відповідь агента озвучується
8. Запис **автоматично перезапускається** — говори знову, не натискаючи жодної клавіші

Цей цикл триває, доки ти не натиснеш **Ctrl+B** під час запису (вихід з безперервного режиму) або доки 3 послідовних запису не виявлять жодної мови.

:::tip
Клавішу запису можна налаштувати через `voice.record_key` у `~/.hermes/config.yaml` (за замовчуванням: `ctrl+b`).
:::

### Silence Detection

Двоетапний алгоритм визначає, коли ти закінчив говорити:

1. **Підтвердження мови** — чекає аудіо вище порогу RMS (200) принаймні 0,3 с, допускаючи короткі спади між складами
2. **Виявлення кінця** — після підтвердження мови спрацьовує через 3,0 с безперервної тиші

Якщо протягом 15 секунд мова не виявлена взагалі, запис зупиняється автоматично.

Як `silence_threshold`, так і `silence_duration` можна налаштувати у `config.yaml`. Також можна вимкнути сигнали старту/зупинки запису, встановивши `voice.beep_enabled: false`.

### Streaming TTS

Коли TTS увімкнено, агент озвучує свою відповідь **речення за реченням** під час генерації тексту — не треба чекати повної відповіді:

1. Буферизує дельти тексту в повні речення (мін. 20 символів)
2. Видаляє markdown‑форматування та блоки `<think>`
3. Генерує і відтворює аудіо для кожного речення в реальному часі

### Hallucination Filter

Whisper іноді генерує фантомний текст зі тиші або фонового шуму («Thank you for watching», «Subscribe» тощо). Агент фільтрує їх, використовуючи набір з 26 відомих фраз‑галюцинацій різними мовами, а також regex‑шаблон, що ловить повторювані варіації.

---
## Gateway Voice Reply (Telegram & Discord)

Якщо ти ще не налаштував своїх ботів для обміну повідомленнями, переглянь посібники для конкретних платформ:
- [Telegram Setup Guide](../messaging/telegram.md)
- [Discord Setup Guide](../messaging/discord.md)

Запусти gateway, щоб підключитися до своїх платформ обміну повідомленнями:

```bash
hermes gateway        # Start the gateway (connects to configured platforms)
hermes gateway setup  # Interactive setup wizard for first-time configuration
```

### Discord: Канали vs DM

Бот підтримує два режими взаємодії в Discord:

| Mode | How to Talk | Mention Required | Setup |
|------|------------|-------------------|-------|
| **Direct Message (DM)** | Відкрий профіль бота → «Message» | No | Працює одразу |
| **Server Channel** | Напиши в текстовому каналі, де присутній бот | Yes (`@botname`) | Бот має бути запрошений на сервер |

**DM (рекомендовано для особистого використання):** Просто відкрий DM з ботом і напиши — згадка не потрібна. Голосові відповіді та всі команди працюють так само, як у каналах.

**Server channels:** Бот відповідає лише коли його @згадати (наприклад, `@hermesbyt4 hello`). Переконайся, що вибрав **користувача бота** у спливаючому вікні згадки, а не роль з такою ж назвою.

:::tip
Щоб вимкнути вимогу згадування в каналах сервера, додай у `~/.hermes/.env`:
```bash
DISCORD_REQUIRE_MENTION=false
```
Або встанови окремі канали як вільні (без згадки):
```bash
DISCORD_FREE_RESPONSE_CHANNELS=123456789,987654321
```
:::

### Commands

Ці команди працюють і в Telegram, і в Discord (DM та текстові канали):

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
| `off` | `/voice off` | Тільки текст (за замовчуванням) |
| `voice_only` | `/voice on` | Відповідає голосом лише коли ти надсилаєш голосове повідомлення |
| `all` | `/voice tts` | Відповідає голосом на кожне повідомлення |

Налаштування режиму голосу зберігається між перезапусками gateway.

### Platform Delivery

| Platform | Format | Notes |
|----------|--------|-------|
| **Telegram** | Voice bubble (Opus/OGG) | Відтворюється в чаті. ffmpeg конвертує MP3 → Opus за потреби |
| **Discord** | Native voice bubble (Opus/OGG) | Відтворюється в чаті як голосове повідомлення користувача. При збоях API голосової бульбашки переходить до вкладення файлу |
## Канали голосу Discord

Найзахопливіша голосова функція: бот приєднується до голосового каналу Discord, слухає, що говорять користувачі, транскрибує їхню мову, обробляє її через агента і озвучує відповідь у голосовому каналі.

### Налаштування

#### 1. Права бота Discord

Якщо у тебе вже налаштований бот Discord для тексту (див. [Discord Setup Guide](../messaging/discord.md)), потрібно додати голосові права.

Перейди до [Discord Developer Portal](https://discord.com/developers/applications) → твій застосунок → **Installation** → **Default Install Settings** → **Guild Install**:

**Додай ці права до існуючих текстових прав:**

| Permission | Purpose | Required |
|-----------|---------|----------|
| **Connect** | Приєднання до голосових каналів | Так |
| **Speak** | Відтворення TTS‑аудіо у голосових каналах | Так |
| **Use Voice Activity** | Виявлення, коли користувачі говорять | Рекомендовано |

**Оновлене ціле число прав:**

| Level | Integer | What's Included |
|-------|---------|----------------|
| Тільки текст | `274878286912` | View Channels, Send Messages, Read History, Embeds, Attachments, Threads, Reactions |
| Текст + голос | `274881432640` | All above + Connect, Speak |

**Повторно запроси бота** з оновленим URL прав:

```
https://discord.com/oauth2/authorize?client_id=YOUR_APP_ID&scope=bot+applications.commands&permissions=274881432640
```

Замінити `YOUR_APP_ID` на свій Application ID з Developer Portal.

:::warning
Повторне запрошення бота на сервер, на якому він вже є, оновить його права без видалення. Ти не втратиш жодних даних чи налаштувань.
:::

#### 2. Привілейовані Gateway Intents

У [Developer Portal](https://discord.com/developers/applications) → твій застосунок → **Bot** → **Privileged Gateway Intents** увімкни всі три:

| Intent | Purpose |
|--------|---------|
| **Presence Intent** | Виявлення статусу користувачів (онлайн/офлайн) |
| **Server Members Intent** | Перетворення імен користувачів у `DISCORD_ALLOWED_USERS` у числові ID (за умовою) |
| **Message Content Intent** | Читання вмісту текстових повідомлень у каналах |

**Message Content Intent** обов’язковий. **Server Members Intent** потрібен лише тоді, коли список `DISCORD_ALLOWED_USERS` містить імена користувачів — якщо використовуються числові ID, його можна залишити вимкненим. Відображення SSRC голосового каналу → user_id надходить з opcode **SPEAKING** у голосовому websocket і **не** потребує Server Members Intent.

#### 3. Кодек Opus

Бібліотеку кодека Opus треба встановити на машині, де працює шлюз:

```bash
# macOS (Homebrew)
brew install opus

# Ubuntu/Debian
sudo apt install libopus0
```

Бот автоматично завантажує кодек з:
- **macOS:** `/opt/homebrew/lib/libopus.dylib`
- **Linux:** `libopus.so.0`

#### 4. Змінні середовища

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

### Запуск шлюзу

```bash
hermes gateway        # Start with existing configuration
```

Бот має з’явитися в Discord протягом кількох секунд.

### Команди

Використовуй їх у текстовому каналі Discord, де присутній бот:

```
/voice join      Bot joins your current voice channel
/voice channel   Alias for /voice join
/voice leave     Bot disconnects from voice channel
/voice status    Show voice mode and connected channel
```

:::info
Ти маєш бути у голосовому каналі перед виконанням `/voice join`. Бот приєднується до того ж VC, у якому ти знаходишся.
:::

### Як це працює

Коли бот приєднується до голосового каналу, він:

1. **Слухає** аудіопотік кожного користувача окремо
2. **Виявляє тишу** — 1,5 с тиші після щонайменше 0,5 с мови запускає обробку
3. **Транскрибує** аудіо за допомогою Whisper STT (локально, Groq або OpenAI)
4. **Обробляє** через повний конвеєр агента (сесія, інструменти, пам’ять)
5. **Озвучує** відповідь у голосовому каналі за допомогою TTS

### Інтеграція з текстовим каналом

Коли бот знаходиться у голосовому каналі:

- Транскрипти з’являються у текстовому каналі: `[Voice] @user: what you said`
- Відповіді агента надсилаються як текст у канал **і** озвучуються у VC
- Текстовий канал — це той, у якому було виконано `/voice join`

### Запобігання ехо

Бот автоматично паузить свій аудіо‑слухач під час відтворення TTS‑відповідей, не дозволяючи собі чути та повторно обробляти власний вихід.

### Контроль доступу

Лише користувачі, зазначені у `DISCORD_ALLOWED_USERS`, можуть взаємодіяти через голос. Аудіо інших користувачів ігнорується без повідомлень.

```bash
# ~/.hermes/.env
DISCORD_ALLOWED_USERS=284102345871466496
```

---
## Посилання на конфігурацію

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

### Змінні середовища

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

### Порівняння провайдерів STT

| Провайдер | Модель | Швидкість | Якість | Вартість | API‑ключ |
|----------|-------|-----------|--------|----------|----------|
| **Local** | `base` | Швидко (залежить від CPU/GPU) | Добра | Безкоштовний | Ні |
| **Local** | `small` | Середня | Краща | Безкоштовний | Ні |
| **Local** | `large-v3` | Повільно | Найкраща | Безкоштовний | Ні |
| **Groq** | `whisper-large-v3-turbo` | Дуже швидко (~0.5 s) | Добра | Безкоштовний тариф | Так |
| **Groq** | `whisper-large-v3` | Швидко (~1 s) | Краща | Безкоштовний тариф | Так |
| **OpenAI** | `whisper-1` | Швидко (~1 s) | Добра | Платний | Так |
| **OpenAI** | `gpt-4o-transcribe` | Середня (~2 s) | Найкраща | Платний | Так |

Пріоритет провайдера (автоматичний запасний варіант): **local** > **groq** > **openai**

### Порівняння провайдерів TTS

| Провайдер | Якість | Вартість | Затримка | Потрібен ключ |
|----------|--------|----------|----------|----------------|
| **Edge TTS** | Добра | Безкоштовний | ~1 s | Ні |
| **ElevenLabs** | Відмінна | Платний | ~2 s | Так |
| **OpenAI TTS** | Добра | Платний | ~1.5 s | Так |
| **NeuTTS** | Добра | Безкоштовний | Залежить від CPU/GPU | Ні |

NeuTTS використовує блок конфігурації `tts.neutts`, зазначений вище.

---
## Усунення проблем

### «Не знайдено аудіо‑пристрій» (CLI)

PortAudio не встановлено:

```bash
brew install portaudio    # macOS
sudo apt install portaudio19-dev  # Ubuntu
```

Якщо ти запускаєш Hermes у Docker на Linux‑десктопі, контейнеру також потрібен доступ до аудіо‑сокету хоста. Дивись нотатки про [Docker audio bridge](/user-guide/docker#optional-linux-desktop-audio-bridge) для налаштування, сумісного з PulseAudio/PipeWire.

### Бот не відповідає в каналах Discord‑сервері

Бот за замовчуванням потребує @згадки у каналах серверу. Переконайся, що:

1. Введи `@` і вибери **користувача‑бота** (з #дискримінатором), а не **роль** з такою ж назвою
2. Або використай особисті повідомлення — згадка не потрібна
3. Або встанови `DISCORD_REQUIRE_MENTION=false` у `~/.hermes/.env`

### Бот приєднується до голосового каналу, але не чує мене

- Перевір, чи твій Discord‑ID внесений у `DISCORD_ALLOWED_USERS`
- Переконайся, що ти не вимкнув мікрофон у Discord
- Бот потребує події **SPEAKING** від Discord, перш ніж зможе обробити твоє аудіо — почни говорити протягом кількох секунд після приєднання

### Бот чує мене, але не відповідає

- Переконайся, що STT доступний: встанови `faster-whisper` (ключ не потрібен) або встанови `GROQ_API_KEY` / `VOICE_TOOLS_OPENAI_KEY`
- Перевір, чи налаштована і доступна модель LLM
- Переглянь логи шлюзу: `tail -f ~/.hermes/logs/gateway.log`

### Бот відповідає текстом, але не у голосовому каналі

- Провайдер TTS може не працювати — перевір API‑ключ і квоту
- Edge TTS (безкоштовний, без ключа) є запасним варіантом за замовчуванням
- Переглянь логи на предмет помилок TTS

### Whisper повертає беззмістовний текст

Фільтр галюцинацій автоматично ловить більшість випадків. Якщо ти все ще отримуєш «привидні» транскрипції:

- Використовуй тихіше оточення
- Налаштуй `silence_threshold` у конфігурації (вищий = менше чутливості)
- Спробуй іншу модель STT