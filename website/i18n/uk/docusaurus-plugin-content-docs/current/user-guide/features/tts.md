---
sidebar_position: 9
title: "Голос та TTS"
description: "Текст‑у‑мову та транскрипція голосових повідомлень на всіх платформах"
---

# Голос та TTS

Hermes Agent підтримує як перетворення тексту в мову, так і транскрипцію голосових повідомлень на всіх платформах обміну повідомленнями.

:::tip Nous Subscribers
Якщо у тебе є платна підписка на [Nous Portal](https://portal.nousresearch.com), OpenAI TTS доступний через **[Tool Gateway](tool-gateway.md)** без окремого ключа API OpenAI. Нові інсталяції можуть виконати `hermes setup --portal`, щоб увійти та увімкнути всі інструменти шлюзу одразу; існуючі інсталяції можуть обрати **Nous Subscription** лише для TTS за допомогою `hermes model` або `hermes tools`.
:::
## Text-to-Speech

Перетворюй текст у мову за допомогою десяти провайдерів:

| Провайдер | Якість | Вартість | API Key |
|----------|--------|----------|---------|
| **Edge TTS** (default) | Добра | Безкоштовно | Не потрібен |
| **ElevenLabs** | Відмінна | Платно | `ELEVENLABS_API_KEY` |
| **OpenAI TTS** | Добра | Платно | `VOICE_TOOLS_OPENAI_KEY` |
| **MiniMax TTS** | Відмінна | Платно | `MINIMAX_API_KEY` |
| **Mistral (Voxtral TTS)** | Відмінна | Платно | `MISTRAL_API_KEY` |
| **Google Gemini TTS** | Відмінна | Безкоштовний рівень | `GEMINI_API_KEY` |
| **xAI TTS** | Відмінна | Платно | `XAI_API_KEY` |
| **NeuTTS** | Добра | Безкоштовно (локально) | Не потрібен |
| **KittenTTS** | Добра | Безкоштовно (локально) | Не потрібен |
| **Piper** | Добра | Безкоштовно (локально) | Не потрібен |
### Доставка платформи

| Платформа | Доставка | Формат |
|----------|----------|--------|
| Telegram | Голосова бульбашка (відтворюється вбудовано) | Opus `.ogg` |
| Discord | Голосова бульбашка (Opus/OGG), запасний (варіант) — прикріплення файлу | Opus/MP3 |
| WhatsApp | Прикріплення аудіофайлу | MP3 |
| CLI | Збережено у `~/.hermes/audio_cache/` | MP3 |
### Конфігурація

```yaml
# In ~/.hermes/config.yaml
tts:
  provider: "edge"              # "edge" | "elevenlabs" | "openai" | "minimax" | "mistral" | "gemini" | "xai" | "neutts" | "kittentts" | "piper"
  speed: 1.0                    # Global speed multiplier (provider-specific settings override this)
  edge:
    voice: "en-US-AriaNeural"   # 322 voices, 74 languages
    speed: 1.0                  # Converted to rate percentage (+/-%)
  elevenlabs:
    voice_id: "pNInz6obpgDQGcFmaJgB"  # Adam
    model_id: "eleven_multilingual_v2"
  openai:
    model: "gpt-4o-mini-tts"
    voice: "alloy"              # alloy, echo, fable, onyx, nova, shimmer
    base_url: "https://api.openai.com/v1"  # Override for OpenAI-compatible TTS endpoints
    speed: 1.0                  # 0.25 - 4.0
  minimax:
    model: "speech-2.8-hd"     # speech-2.8-hd (default), speech-2.8-turbo
    voice_id: "English_Graceful_Lady"  # See https://platform.minimax.io/faq/system-voice-id
    speed: 1                    # 0.5 - 2.0
    vol: 1                      # 0 - 10
    pitch: 0                    # -12 - 12
  mistral:
    model: "voxtral-mini-tts-2603"
    voice_id: "c69964a6-ab8b-4f8a-9465-ec0925096ec8"  # Paul - Neutral (default)
  gemini:
    model: "gemini-2.5-flash-preview-tts"  # or gemini-2.5-pro-preview-tts
    voice: "Kore"               # 30 prebuilt voices: Zephyr, Puck, Kore, Enceladus, Gacrux, etc.
  xai:
    voice_id: "eve"             # or a custom voice ID — see docs below
    language: "en"              # ISO 639-1 code
    sample_rate: 24000          # 22050 / 24000 (default) / 44100 / 48000
    bit_rate: 128000            # MP3 bitrate; only applies when codec=mp3
    # base_url: "https://api.x.ai/v1"   # Override via XAI_BASE_URL env var
  neutts:
    ref_audio: ''
    ref_text: ''
    model: neuphonic/neutts-air-q4-gguf
    device: cpu
  kittentts:
    model: KittenML/kitten-tts-nano-0.8-int8   # 25MB int8; also: kitten-tts-micro-0.8 (41MB), kitten-tts-mini-0.8 (80MB)
    voice: Jasper                               # Jasper, Bella, Luna, Bruno, Rosie, Hugo, Kiki, Leo
    speed: 1.0                                  # 0.5 - 2.0
    clean_text: true                            # Expand numbers, currencies, units
  piper:
    voice: en_US-lessac-medium                  # voice name (auto-downloaded) OR absolute path to .onnx
    # voices_dir: ''                            # default: ~/.hermes/cache/piper-voices/
    # use_cuda: false                           # requires onnxruntime-gpu
    # length_scale: 1.0                         # 2.0 = twice as slow
    # noise_scale: 0.667
    # noise_w_scale: 0.8
    # volume: 1.0                               # 0.5 = half as loud
    # normalize_audio: true
```

**Керування швидкістю**: Глобальне значення `tts.speed` застосовується до всіх провайдерів за замовчуванням. Кожен провайдер може перевизначити його власним параметром `speed` (наприклад, `tts.openai.speed: 1.5`). Швидкість, специфічна для провайдера, має пріоритет над глобальним значенням. За замовчуванням — `1.0` (нормальна швидкість).
### Обмеження довжини вводу

Кожен провайдер має задокументоване обмеження кількості символів у запиті. Hermes обрізає текст перед викликом провайдера, тому запити ніколи не завершуються помилкою через перевищення довжини:

| Provider | Типове обмеження (символи) |
|----------|---------------------------|
| Edge TTS | 5000 |
| OpenAI | 4096 |
| xAI | 15000 |
| MiniMax | 10000 |
| Mistral | 4000 |
| Google Gemini | 5000 |
| ElevenLabs | Залежить від моделі (див. нижче) |
| NeuTTS | 2000 |
| KittenTTS | 2000 |
| Piper | 5000 |

**ElevenLabs** вибирає обмеження згідно налаштованого `model_id`:

| `model_id` | Обмеження (символи) |
|------------|--------------------|
| `eleven_flash_v2_5` | 40000 |
| `eleven_flash_v2` | 30000 |
| `eleven_multilingual_v2` (за замовчуванням), `eleven_multilingual_v1`, `eleven_english_sts_v2`, `eleven_english_sts_v1` | 10000 |
| `eleven_v3`, `eleven_ttv_v3` | 5000 |
| Невідома модель | Повертається до типового обмеження провайдера (10000) |

**Перевизначення для провайдера** за допомогою `max_text_length:` у розділі провайдера вашого конфігураційного файлу TTS:

```yaml
tts:
  openai:
    max_text_length: 8192   # raise or lower the provider cap
```

Лише додатні цілі числа враховуються. Нуль, від’ємні, нечислові або булеві значення переходять до типового обмеження провайдера, тому пошкоджений конфігураційний файл не може випадково вимкнути обрізання.
### Telegram Voice Bubbles & ffmpeg

Telegram voice bubbles потребують аудіоформат Opus/OGG:

- **OpenAI, ElevenLabs та Mistral** генерують Opus «з коробки» — додаткових налаштувань не потрібно
- **Edge TTS** (за замовчуванням) виводить MP3 і потребує **ffmpeg** для конвертації
- **MiniMax TTS** виводить MP3 і потребує **ffmpeg** для конвертації у формат Telegram voice bubbles
- **Google Gemini TTS** виводить raw PCM і використовує **ffmpeg** для кодування Opus безпосередньо для Telegram voice bubbles
- **xAI TTS** виводить MP3 і потребує **ffmpeg** для конвертації у формат Telegram voice bubbles
- **NeuTTS** виводить WAV і також потребує **ffmpeg** для конвертації у формат Telegram voice bubbles
- **KittenTTS** виводить WAV і також потребує **ffmpeg** для конвертації у формат Telegram voice bubbles
- **Piper** виводить WAV і також потребує **ffmpeg** для конвертації у формат Telegram voice bubbles

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Fedora
sudo dnf install ffmpeg
```

Без **ffmpeg** аудіо Edge TTS, MiniMax TTS, NeuTTS, KittenTTS та Piper надсилаються як звичайні аудіофайли (можна відтворити, але вони відображаються у вигляді прямокутного плеєра, а не голосового бульбашки).

:::tip
Якщо потрібні голосові бульбашки без встановлення **ffmpeg**, обери провайдера OpenAI, ElevenLabs або Mistral.
:::
### xAI Custom Voices (voice cloning)

xAI підтримує клонування твого голосу та використання його з TTS. Створи власний голос у [xAI Console](https://console.x.ai/team/default/voice/voice-library), потім встанови отриманий `voice_id` у своїй конфігурації:

```yaml
tts:
  provider: xai
  xai:
    voice_id: "nlbqfwie"   # your custom voice ID
```

Дивись [документацію xAI Custom Voices](https://docs.x.ai/developers/model-capabilities/audio/custom-voices) для деталей щодо запису, підтримуваних форматів та обмежень.
### Piper (локальний, 44 мови)

Piper — це швидкий локальний нейронний TTS‑двигун від Open Home Foundation (розробники Home Assistant). Він працює повністю на CPU, підтримує **44 мови** з попередньо навченими голосами і не потребує API‑ключа.

**Встановити через `hermes tools`** → Voice & TTS → Piper — Hermes виконує `pip install piper-tts` за тебе. Або встанови вручну: `pip install piper-tts`.

**Переключитися на Piper:**

```yaml
tts:
  provider: piper
  piper:
    voice: en_US-lessac-medium
```

При першому виклику TTS для голосу, який не кешовано локально, Hermes виконує `python -m piper.download_voices <name>` і завантажує модель (~20‑90 МБ залежно від рівня якості) у `~/.hermes/cache/piper-voices/`. Подальші виклики повторно використовують кешовану модель.

**Вибір голосу.** [Повний каталог голосів](https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/VOICES.md) охоплює англійську, іспанську, французьку, німецьку, італійську, нідерландську, португальську, російську, польську, турецьку, китайську, арабську, хінді та інші — кожна з рівнями якості `x_low` / `low` / `medium` / `high`. Приклади голосів доступні за адресою [rhasspy.github.io/piper-samples](https://rhasspy.github.io/piper-samples/).

**Використання попередньо завантаженого голосу.** Встанови `tts.piper.voice` у абсолютний шлях, що закінчується на `.onnx`:

```yaml
tts:
  piper:
    voice: /path/to/my-custom-voice.onnx
```

**Розширені налаштування** (`tts.piper.length_scale` / `noise_scale` / `noise_w_scale` / `volume` / `normalize_audio`, `use_cuda`) відповідають 1:1 параметрам Piper `SynthesisConfig`. Вони ігноруються в старіших версіях `piper-tts`.
### Провайдери команд користувача

Якщо потрібний тобі TTS‑движок не підтримується «з коробки» (VoxCPM, MLX‑Kokoro, XTTS CLI, скрипт клонування голосу чи будь‑який інший, що надає CLI), його можна підключити як **провайдер типу command** без написання Python‑коду. Hermes записує вхідний текст у тимчасовий UTF‑8 файл, запускає твою shell‑команду і читає аудіофайл, який створила команда.

Оголоси один або кілька провайдерів у `tts.providers.<name>` і перемикайся між ними за допомогою `tts.provider: <name>` — так само, як перемикаєшся між вбудованими, наприклад `edge` і `openai`.

```yaml
tts:
  provider: voxcpm                 # pick any name under tts.providers
  providers:
    voxcpm:
      type: command
      command: "voxcpm --ref ~/voice.wav --text-file {input_path} --out {output_path}"
      output_format: mp3
      timeout: 180
      voice_compatible: true       # try to deliver as a Telegram voice bubble

    mlx-kokoro:
      type: command
      command: "python -m mlx_kokoro --in {input_path} --out {output_path} --voice {voice}"
      voice: af_sky
      output_format: wav

    piper-custom:                  # native Piper also supports custom .onnx via tts.piper.voice
      type: command
      command: "piper -m /path/to/custom.onnx -f {output_path} < {input_path}"
      output_format: wav
```

#### Приклад: Doubao (китайський seed‑tts‑2.0)

Для високоякісного китайського TTS через двосторонній потоковий API ByteDance [seed‑tts‑2.0](https://www.volcengine.com/docs/6561/1257544) встанови пакет PyPI [`doubao-speech`](https://pypi.org/project/doubao-speech/) і підключи його як провайдер команд:

```bash
pip install doubao-speech
export VOLCENGINE_APP_ID="your-app-id"
export VOLCENGINE_ACCESS_TOKEN="your-access-token"
```

```yaml
tts:
  provider: doubao
  providers:
    doubao:
      type: command
      command: "doubao-speech say --text-file {input_path} --out {output_path}"
      output_format: mp3
      max_text_length: 1024
      timeout: 30
```

Облікові дані беруться з твого shell‑середовища (`VOLCENGINE_APP_ID` / `VOLCENGINE_ACCESS_TOKEN`) або `~/.doubao-speech/config.yaml`. Вибери голос, додавши `--voice zh-female-warm` (або будь‑який інший псевдонім з `doubao-speech list-voices`) до команди. `doubao-speech` також постачається зі стрімінговим ASR — дивись розділ [STT нижче](#example-doubao--volcengine-asr) для інтеграції з Hermes. Джерело та повна документація: [github.com/Hypnus-Yuan/doubao-speech](https://github.com/Hypnus-Yuan/doubao-speech).

#### Плейсхолдери

Твій шаблон команди може посилатися на ці плейсхолдери. Hermes підставляє їх під час рендерингу і екранує кожне значення для оточуючого контексту (без лапок / одинарних / подвійних), тому шляхи з пробілами та іншими чутливими до shell символами безпечні.

| Плейсхолдер      | Значення                                                |
|------------------|--------------------------------------------------------|
| `{input_path}`   | Шлях до тимчасового UTF‑8 текстового файлу, який записав Hermes |
| `{text_path}`    | Псевдонім для `{input_path}`                            |
| `{output_path}`  | Шлях, куди команда повинна записати аудіо               |
| `{format}`       | `mp3` / `wav` / `ogg` / `flac`                         |
| `{voice}`        | `tts.providers.<name>.voice`, порожньо, якщо не задано |
| `{model}`        | `tts.providers.<name>.model`                           |
| `{speed}`        | Обчислений множник швидкості (провайдер або глобальний) |

Для буквальних дужок використовуйте `{{` і `}}`.

#### Додаткові ключі

| Ключ               | За замовчуванням | Значення                                                                                                    |
|--------------------|------------------|------------------------------------------------------------------------------------------------------------|
| `timeout`          | `120`            | Секунди; дерево процесів завершується після закінчення часу (Unix `killpg`, Windows `taskkill /T`).        |
| `output_format`    | `mp3`            | Один з `mp3` / `wav` / `ogg` / `flac`. Автоматично визначається за розширенням вихідного файлу, якщо Hermes задає шлях. |
| `voice_compatible` | `false`          | Якщо `true`, Hermes конвертує MP3/WAV у Opus/OGG за допомогою ffmpeg, щоб Telegram відтворював голосове повідомлення. |
| `max_text_length`  | `5000`           | Вхідний текст обрізається до цієї довжини перед рендерингом команди.                                      |
| `voice` / `model`  | порожньо         | Передається в команду лише як значення плейсхолдерів.                                                       |

#### Примітки щодо поведінки

- **Вбудовані імена завжди мають пріоритет.** Запис `tts.providers.openai` ніколи не перекриває вбудований провайдер OpenAI, тому жодна користувацька конфігурація не може непомітно замінити вбудований.
- **Типова доставка — документ.** Провайдери команд надсилають звичайні аудіо‑вкладення на всіх платформах. Щоб отримати доставку у вигляді голосової бульбашки, увімкни `voice_compatible: true` для конкретного провайдера.
- **Помилки команд передаються агенту.** Ненульовий код виходу, порожній вихід або тайм‑аут повертають помилку зі `stderr`/`stdout` команди, щоб ти міг відлагодити провайдер у розмові.
- **`type: command` — це тип за замовчуванням, коли вказано `command:`.** Явно прописувати `type: command` — хороша практика, але не обов’язково; запис з непорожнім рядком `command` розглядається як провайдер команд.
- **`{input_path}` / `{text_path}` взаємозамінні.** Використовуй той, який краще читається у твоїй команді.

#### Безпека

Провайдери типу command виконують будь‑яку shell‑команду, яку ти налаштуєш, з правами твого користувача. Hermes екранує значення плейсхолдерів і дотримується заданого тайм‑ауту, проте сам шаблон команди — це довірений локальний ввід; стався до нього так само, як до скрипту у твоєму PATH.
### Провайдери Python‑плагінів

Для TTS‑рушіїв, які не можна виразити однією shell‑командою — Python SDK без CLI, потокові рушії, API зі списком голосів, OAuth‑оновлення — зареєструй Python‑плагін за допомогою `ctx.register_tts_provider()`. Плагін **співіснує** (не замінює) реєстр [провайдерів кастомних команд](#custom-command-providers); обери інтерфейс, який підходить твоєму рушію.

#### Коли обирати який

| Твій бекенд має… | Використовуй |
|---|---|
| Одна CLI, що читає текст з файлу/stdin і записує аудіо у файл/stdout | **Провайдер команд** (Python не потрібен) |
| Дві або три CLI, пов’язані pipe‑ами shell | **Провайдер команд** |
| Тільки Python SDK — без CLI | **Плагін** |
| Потокові байти, які треба доставляти частинами (голосові «бульбашки» під час генерації) | **Плагін** (перевизначити `stream()`) |
| API зі списком голосів, що використовується `hermes setup` | **Плагін** (перевизначити `list_voices()`) |
| OAuth‑потік оновлення (не статичний bearer‑токен) | **Плагін** |

Вбудовані провайдери завжди мають перевагу, а провайдери команд переважають плагін з таким же ім’ям — тому плагіни безпечно реєструвати під будь‑яким не‑вбудованим ім’ям, не боячись перекривати існуючу конфігурацію.

#### Мінімальний плагін

Помісти це у `~/.hermes/plugins/my-tts/`:

`plugin.yaml`:
```yaml
name: my-tts
version: 0.1.0
description: "My custom Python TTS backend"
```

`__init__.py`:
```python
from agent.tts_provider import TTSProvider


class MyTTSProvider(TTSProvider):
    @property
    def name(self) -> str:
        return "my-tts"  # what tts.provider matches against

    @property
    def display_name(self) -> str:
        return "My Custom TTS"

    def is_available(self) -> bool:
        # Return False when credentials/deps are missing — picker skips
        # this row but the dispatcher still routes here on explicit config.
        import os
        return bool(os.environ.get("MY_TTS_API_KEY"))

    def synthesize(self, text, output_path, *, voice=None, model=None,
                   speed=None, format="mp3", **extra) -> str:
        # Write audio bytes to output_path, return the path.
        # Raise on failure — the dispatcher converts exceptions to a
        # standard error envelope.
        import my_tts_sdk
        client = my_tts_sdk.Client()
        audio_bytes = client.synthesize(text=text, voice=voice or "default")
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
        return output_path


def register(ctx):
    ctx.register_tts_provider(MyTTSProvider())
```

Увімкни його (`hermes plugins enable my-tts`), вкажи `tts.provider` на нього (`tts.provider: my-tts` у `config.yaml`), і інструмент `text_to_speech` буде маршрутизуватися через твій плагін.

#### Додаткові хуки

Перевизначай їх у класі провайдера для більш глибокої інтеграції:

- `list_voices()` → список словників `{id, display, language, gender, preview_url}`, що показуються у `hermes tools`.
- `list_models()` → список словників `{id, display, languages, max_text_length}`.
- `get_setup_schema()` → повертає `{name, badge, tag, env_vars: [{key, prompt, url}]}` для заповнення рядка вибору у `hermes tools` / `hermes setup`. Без цього плагін працює, але його рядок у вибірці мінімальний.
- `stream(text, *, voice, model, format, **extra)` → ітератор, що повертає аудіо‑байти для потокової доставки (за замовчуванням піднімає `NotImplementedError`).
- Властивість `voice_compatible` → встанови `True`, якщо твій вихід сумісний з Opus і шлюз має доставляти його як голосову «бульбашку» (за замовчуванням `False` = звичайне аудіо‑вкладення).

Дивись `agent/tts_provider.py` для повного ABC, включаючи docstring‑и.
## Транскрипція голосових повідомлень (STT)

Голосові повідомлення, надіслані в Telegram, Discord, WhatsApp, Slack або Signal, автоматично транскрибуються та вставляються як текст у розмову. Агент бачить транскрипт як звичайний текст.

| Provider | Quality | Cost | API Key |
|----------|---------|------|---------|
| **Local Whisper** (default) | Good | Free | None needed |
| **Groq Whisper API** | Good–Best | Free tier | `GROQ_API_KEY` |
| **OpenAI Whisper API** | Good–Best | Paid | `VOICE_TOOLS_OPENAI_KEY` or `OPENAI_API_KEY` |

:::info Zero Config
Local transcription works out of the box when `faster-whisper` is installed. If that's unavailable, Hermes can also use a local `whisper` CLI from common install locations (like `/opt/homebrew/bin`) or a custom command via `HERMES_LOCAL_STT_COMMAND`.
:::
### Налаштування

⟦HOLD_11⟆
### Деталі провайдера

**Local (faster-whisper)** — Запускає Whisper локально через [faster-whisper](https://github.com/SYSTRAN/faster-whisper). За замовчуванням використовує CPU, GPU — якщо доступний. Розміри моделей:

| Model | Size | Speed | Quality |
|-------|------|-------|---------|
| `tiny` | ~75 MB | Найшвидший | Basic |
| `base` | ~150 MB | Fast | Good (default) |
| `small` | ~500 MB | Medium | Better |
| `medium` | ~1.5 GB | Slower | Great |
| `large-v3` | ~3 GB | Slowest | Best |

**Groq API** — Потрібен `GROQ_API_KEY`. Хороший хмарний запасний (варіант), коли потрібен безкоштовний хостинг STT.

**OpenAI API** — Спочатку використовує `VOICE_TOOLS_OPENAI_KEY`, а при його відсутності — `OPENAI_API_KEY`. Підтримує `whisper-1`, `gpt-4o-mini-transcribe` та `gpt-4o-transcribe`.

**Mistral API (Voxtral Transcribe)** — Потрібен `MISTRAL_API_KEY`. Використовує моделі Mistral's [Voxtral Transcribe](https://docs.mistral.ai/capabilities/audio/speech_to_text/). Підтримує 13 мов, діарізацію спікерів та мітки часу на рівні слів. Встановлюється через `pip install hermes-agent[mistral]`.

**xAI Grok STT** — Потрібен `XAI_API_KEY`. Надсилає запит до `https://api.x.ai/v1/stt` у форматі multipart/form-data. Хороший вибір, якщо ти вже користуєшся xAI для чату або TTS і хочеш один API‑ключ для всього. Порядок авто‑детекції розташовує його після Groq — явно встанови `stt.provider: xai`, щоб примусово використати його.

**Custom local CLI fallback** — Встанови `HERMES_LOCAL_STT_COMMAND`, якщо хочеш, щоб Hermes викликав локальну команду транскрипції безпосередньо. Шаблон команди підтримує плейсхолдери `{input_path}`, `{output_dir}`, `{language}` та `{model}`. Твоя команда повинна записати файл `.txt` транскрипту в будь‑яке місце під `{output_dir}`.

#### Приклад: Doubao / Volcengine ASR

Якщо ти використовуєш [`doubao-speech`](https://pypi.org/project/doubao-speech/) для Doubao TTS (дивись [вище](#example-doubao-chinese-seed-tts-20)), той самий пакет обробляє speech‑to‑text через поверхню local‑command STT:

```bash
pip install doubao-speech
export VOLCENGINE_APP_ID="your-app-id"
export VOLCENGINE_ACCESS_TOKEN="your-access-token"
export HERMES_LOCAL_STT_COMMAND='doubao-speech transcribe {input_path} --out {output_dir}/transcript.txt'
```

```yaml
stt:
  provider: local_command
```

Hermes записує вхідне голосове повідомлення у `{input_path}`, запускає команду та читає створений файл `.txt` під `{output_dir}`. Мова автоматично визначається за кінцевою точкою Volcengine bigmodel.
### Поведінка запасного (fallback)

Якщо налаштований провайдер недоступний, Hermes автоматично переходить до запасного варіанту:
- **Local faster-whisper unavailable** → Спочатку пробує локальний `whisper` CLI або `HERMES_LOCAL_STT_COMMAND` перед хмарними провайдерами
- **Groq key not set** → Переходить до локальної транскрипції, потім до OpenAI
- **OpenAI key not set** → Переходить до локальної транскрипції, потім до Groq
- **Mistral key/SDK not set** → Пропускається в авто‑детекції; переходить до наступного доступного провайдера
- **Nothing available** → Голосові повідомлення проходять далі з точним повідомленням користувачеві
### Постачальники власних команд STT

Якщо потрібний тобі STT‑двигун не підтримується «з коробки» (Doubao ASR, NVIDIA Parakeet, збірка whisper.cpp, відкритий CLI SenseVoice, будь‑що інше, що виконує shell‑команду), підключи його як **постачальник типу command** без написання Python‑коду. Hermes запускає твою shell‑команду над аудіофайлом і читає назад транскрипт.

Оголоси один або кілька постачальників у `stt.providers.<name>` і перемикайся між ними за допомогою `stt.provider: <name>` — та сама структура, що й у реєстрі [command‑provider](/custom-command-providers) для TTS, лише адаптована до напрямку `input=audio → output=transcript`.

```yaml
stt:
  provider: parakeet                # pick any name under stt.providers
  providers:
    parakeet:
      type: command
      command: "parakeet-asr --model nvidia/parakeet-tdt-0.6b-v2 --in {input_path} --out {output_path}"
      format: txt
      language: en
      timeout: 300

    whispercpp:
      type: command
      command: "whisper-cli -m ~/models/ggml-large-v3.bin -f {input_path} -otxt -of {output_dir}/transcript"
      format: txt

    sensevoice:
      type: command
      command: "sensevoice-cli {input_path} --json | tee {output_path}"
      format: json
```

Це доповнює застарілий «escape hatch» `HERMES_LOCAL_STT_COMMAND` — змінна середовища і надалі працює без змін через вбудований шлях `local_command`. Використовуй `stt.providers.<name>`, коли потрібні **кілька** STT‑двигунів, керованих shell‑командами, ім’я яких можна задати через `stt.provider`, або коли треба вказати індивідуальні `language` / `model` / `timeout` для кожного постачальника.

#### Заповнювачі STT

Твій шаблон команди може посилатися на ці заповнювачі. Hermes підставляє їх під час рендерингу і автоматично екранує значення для оболонки (без лапок / одинарних / подвійних), тому шляхи з пробілами безпечні.

| Заповнювач      | Значення                                                               |
|-----------------|------------------------------------------------------------------------|
| `{input_path}`  | Абсолютний шлях до вхідного аудіофайлу (оригінальне розташування, лише читання) |
| `{output_path}` | Абсолютний шлях, куди команда повинна записати транскрипт               |
| `{output_dir}`  | Батьківська директорія `{output_path}` (зручно для інструментів типу whisper) |
| `{format}`      | Налаштований формат виводу: `txt` / `json` / `srt` / `vtt`               |
| `{language}`    | Код мови, налаштований у конфігурації (за замовчуванням `en`)            |
| `{model}`       | `stt.providers.<name>.model`, порожньо, якщо не задано                  |

Для буквальних фігурних дужок використай `{{` і `}}` (зручно, коли потрібно вставити JSON‑фрагмент у команду).

#### Як читається транскрипт

Після успішного завершення команди:

1. Якщо існує `{output_path}` і він не порожній → Hermes читає його як UTF‑8‑текст.
2. Інакше, якщо команда вивела дані у stdout → Hermes використовує їх.
3. Інакше → помилка: «Command STT provider wrote no output file and produced no stdout».

Так можна використовувати реєстр і для CLI, які записують файл (`whisper-cli`, `parakeet-asr`), і для однорядкових curl‑команд, що виводять транскрипт у stdout (`curl … | jq -r .text`).

Для `format: json` / `srt` / `vtt` Hermes повертає вміст файлу як поле `transcript`. Витяг `.text` з JSON‑виводу не входить у обов’язки раннера — або налаштуй `format: txt`, або оброби JSON далі.

#### Додаткові ключі постачальника команд STT

| Ключ       | За замовчуванням | Значення                                                                                              |
|------------|------------------|-------------------------------------------------------------------------------------------------------|
| `timeout`  | `300`            | Кількість секунд; дерево процесів буде завершено після закінчення часу (Unix `start_new_session`, Windows `taskkill /T`). |
| `format`   | `txt`            | Один із `txt` / `json` / `srt` / `vtt`. Визначає розширення `{output_path}`.                           |
| `language` | `en`             | Передається у `{language}`. За замовчуванням береться `stt.language`, потім `en`.                      |
| `model`    | (порожньо)       | Передається у `{model}`. Аргумент `model=` у `transcribe_audio()` переважає це значення.               |

#### Примітки щодо поведінки постачальника команд STT

- **Вбудовані завжди мають перевагу.** Оголошення `stt.providers.openai: type: command` НЕ замінює справжній обробник OpenAI Whisper. Вбудоване ім’я коротко‑перериває процес перед тим, як запускається резолвер command‑provider.
- **Очищення дерева процесів.** Команда, що працює довше `timeout`, завершується разом зі всім своїм деревом процесів, а не лише оболонкою. Довгі ASR‑конвеєри, які створюють підпроцеси для завантаження моделей, коректно прибираються.
- **Автоматичне екранування для оболонки.** Заповнювачі всередині `'…'` отримують безпечне екранування одинарними лапками; у `"…"` — екранування `$`/`` ` ``/`"`; поза лапками — `shlex.quote`. Не потрібно попередньо екранувати значення заповнювачів.

#### Безпека постачальника команд STT

Shell‑команда виконується під тим самим користувачем, що й Hermes, з повним доступом до файлової системи — та сама модель довіри, що й у `tts.providers.<name>: type: command` та `HERMES_LOCAL_STT_COMMAND`. Оголошуй лише ті постачальники, джерела яких ти довіряєш.
### Python plugin providers (STT)

Для STT‑рушійок, які не вбудовані **і** не можуть бути виражені як shell‑команда (потрібен Python SDK, OAuth‑оновлювана автентифікація, потокові чанки тощо), зареєструй Python‑плагін через `ctx.register_transcription_provider()`. Плагін **співіснує** з 6‑мя вбудованими провайдерами (`local`, `local_command`, `groq`, `openai`, `mistral`, `xai`) та реєстром `stt.providers.<name>: type: command` — вбудовані зберігають свої нативні реалізації і завжди виграють при конфлікті імен; провайдери‑команди виграють над плагінами з однаковим ім’ям (конфігурація локальніша, ніж встановлення плагіна).

#### Коли обирати який (STT)

| Backend має…                                                | Використовуй                                                       |
|-------------------------------------------------------------|--------------------------------------------------------------------|
| Одна shell‑команда, що приймає аудіофайл і виводить текст   | `stt.providers.<name>: type: command` (Python не потрібен)         |
| Потрібен лише застарілий однокомандний “escape hatch”      | змінна середовища `HERMES_LOCAL_STT_COMMAND` (збережена для сумісності) |
| Python SDK без CLI                                          | плагін `register_transcription_provider()`                         |
| OAuth‑оновлювана автентифікація, потокові чанки, метадані voice‑list | плагін `register_transcription_provider()`                         |
| Вбудований вже покриває це (`local`, `groq`, `openai`, …)   | встанови `stt.provider: <name>` — вбудовані працюють inline        |

#### Порядок розв’язання

1. **`stt.provider` — це ім’я вбудованого провайдера** → вбудований диспетчер. **Завжди виграє.**
2. **`stt.provider` збігається з `stt.providers.<name>` і в ньому задано `command:`** → виконувач провайдера‑команди (див. [STT custom command providers](#stt-custom-command-providers)). Перемагає плагін з тим же ім’ям.
3. **`stt.provider` збігається з плагін‑зареєстрованим `TranscriptionProvider`** → диспетчер плагіна:
   - якщо `is_available()` плагіна повертає `False` (відсутні креденшіали або SDK), виклик повертає помилку недоступності, вказуючи конкретний плагін — **не** загальне повідомлення «No STT provider available».
   - інакше викликається `transcribe()` плагіна з `model` (з публічного аргументу `model=` або, за замовчуванням, `stt.<provider>.model`) та `language` (з `stt.<provider>.language`).
4. **Немає збігів** → помилка «No STT provider available».

#### Простір імен конфігурації провайдера

Плагіни читають свою конфігурацію провайдера з `stt.<provider>` у `config.yaml`, так само, як вбудовані читають `stt.openai.model` / `stt.mistral.model`:

```yaml
stt:
  provider: my-stt
  my-stt:
    model: whisper-large-v3
    language: ja          # forwarded as language= to transcribe()
    # any other plugin-specific keys go here; read them via your
    # own config.yaml access in __init__/is_available/transcribe
```

Диспетчер передає `model` і `language` з цього розділу; все інше плагін може зчитати сам.

#### Мінімальний плагін

Помісти це у `~/.hermes/plugins/my-stt/`:

`plugin.yaml`:
```yaml
name: my-stt
version: 0.1.0
description: "My custom Python STT backend"
```

`__init__.py`:
```python
from agent.transcription_provider import TranscriptionProvider


class MySTTProvider(TranscriptionProvider):
    @property
    def name(self) -> str:
        return "my-stt"  # what stt.provider matches against

    @property
    def display_name(self) -> str:
        return "My Custom STT"

    def is_available(self) -> bool:
        # Return False when credentials/deps are missing — picker skips
        # this row but the dispatcher still routes here on explicit config.
        import os
        return bool(os.environ.get("MY_STT_API_KEY"))

    def transcribe(self, file_path, *, model=None, language=None, **extra):
        # Return the standard transcribe envelope:
        #   {"success": bool, "transcript": str, "provider": str, "error": str}
        # Do NOT raise — convert exceptions to the error envelope so the
        # gateway/CLI caller sees a consistent shape on failure.
        try:
            import my_stt_sdk
            client = my_stt_sdk.Client()
            text = client.transcribe(open(file_path, "rb"))
            return {
                "success": True,
                "transcript": text,
                "provider": "my-stt",
            }
        except Exception as exc:
            return {
                "success": False,
                "transcript": "",
                "error": f"my-stt failed: {exc}",
                "provider": "my-stt",
            }


def register(ctx):
    ctx.register_transcription_provider(MySTTProvider())
```

Увімкни його (`hermes plugins enable my-stt`), встанови `stt.provider: my-stt` у `config.yaml`, і транскрипція голосових повідомлень буде проходити через твій плагін.

#### Додаткові хуки

Перевизначай їх у класі провайдера для більш глибокої інтеграції:

- `list_models()` → список словників `{id, display, languages, max_audio_seconds}`.
- `default_model()` → рядок, що повертається, коли користувач не вказав модель.
- `get_setup_schema()` → повертає `{name, badge, tag, env_vars: [{key, prompt, url}]}` для заповнення рядків у `hermes tools` / `hermes setup` (категорія picker для STT ще не випущена — ці метадані доступні плагінам для майбутньої сумісності).

Дивись `agent/transcription_provider.py` для повного ABC включно з docstring‑ами.