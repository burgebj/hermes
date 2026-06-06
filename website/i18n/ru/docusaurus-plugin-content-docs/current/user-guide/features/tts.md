---
sidebar_position: 9
title: "Голос & TTS"
description: "Текст‑в‑речь и транскрипция голосовых сообщений на всех платформах"
---

# Голос и TTS

Hermes Agent поддерживает как вывод текста в речь, так и транскрипцию голосовых сообщений на всех платформах обмена сообщениями.

:::tip Nous Subscribers
Если у тебя есть платная подписка на [Nous Portal](https://portal.nousresearch.com), OpenAI TTS доступен через **[шлюз инструментов](tool-gateway.md)** без отдельного ключа API OpenAI. При новой установке можно выполнить `hermes setup --portal`, чтобы войти в систему и включить все инструменты шлюза сразу; при существующей установке можно выбрать **Nous Subscription** только для TTS через `hermes model` или `hermes tools`.
:::
## Текст‑в‑речь

Преобразуй текст в речь с помощью десяти провайдеров:

| Провайдер | Качество | Стоимость | API‑ключ |
|----------|----------|-----------|----------|
| **Edge TTS** (по умолчанию) | Хорошее | Бесплатно | Не требуется |
| **ElevenLabs** | Отличное | Платно | `ELEVENLABS_API_KEY` |
| **OpenAI TTS** | Хорошее | Платно | `VOICE_TOOLS_OPENAI_KEY` |
| **MiniMax TTS** | Отличное | Платно | `MINIMAX_API_KEY` |
| **Mistral (Voxtral TTS)** | Отличное | Платно | `MISTRAL_API_KEY` |
| **Google Gemini TTS** | Отличное | Бесплатный тариф | `GEMINI_API_KEY` |
| **xAI TTS** | Отличное | Платно | `XAI_API_KEY` |
| **NeuTTS** | Хорошее | Бесплатно (локально) | Не требуется |
| **KittenTTS** | Хорошее | Бесплатно (локально) | Не требуется |
| **Piper** | Хорошее | Бесплатно (локально) | Не требуется |

### Доставка по платформам

| Платформа | Доставка | Формат |
|----------|----------|--------|
| Telegram | Голосовой пузырёк (встроенное воспроизведение) | Opus `.ogg` |
| Discord | Голосовой пузырёк (Opus/OGG), при необходимости — вложение файла | Opus/MP3 |
| WhatsApp | Вложение аудиофайла | MP3 |
| CLI | Сохраняется в `~/.hermes/audio_cache/` | MP3 |

### Конфигурация

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

**Регулировка скорости**: глобальное значение `tts.speed` применяется ко всем провайдерам по умолчанию. Каждый провайдер может переопределить его своим параметром `speed` (например, `tts.openai.speed: 1.5`). Скорость, указанная для конкретного провайдера, имеет приоритет над глобальной. По умолчанию — `1.0` (нормальная скорость).

### Ограничения длины ввода

У каждого провайдера есть документированный лимит количества символов в запросе. Hermes обрезает текст перед вызовом провайдера, чтобы запросы никогда не завершались ошибкой длины:

| Провайдер | Лимит по умолчанию (симв.) |
|----------|----------------------------|
| Edge TTS | 5000 |
| OpenAI | 4096 |
| xAI | 15000 |
| MiniMax | 10000 |
| Mistral | 4000 |
| Google Gemini | 5000 |
| ElevenLabs | Зависит от модели (см. ниже) |
| NeuTTS | 2000 |
| KittenTTS | 2000 |
| Piper | 5000 |

**ElevenLabs** выбирает лимит в зависимости от указанного `model_id`:

| `model_id` | Лимит (симв.) |
|------------|---------------|
| `eleven_flash_v2_5` | 40000 |
| `eleven_flash_v2` | 30000 |
| `eleven_multilingual_v2` (по умолчанию), `eleven_multilingual_v1`, `eleven_english_sts_v2`, `eleven_english_sts_v1` | 10000 |
| `eleven_v3`, `eleven_ttv_v3` | 5000 |
| Неизвестная модель | Возвращается к лимиту провайдера (10000) |

**Переопределить для провайдера** можно с помощью `max_text_length:` в секции провайдера вашего TTS‑конфига:

```yaml
tts:
  openai:
    max_text_length: 8192   # raise or lower the provider cap
```

Учитываются только положительные целые числа. Ноль, отрицательные, нечисловые или булевые значения игнорируются и используется значение по умолчанию провайдера, поэтому повреждённый конфиг не может случайно отключить обрезку.

### Голосовые пузырьки Telegram и ffmpeg

Для голосовых пузырьков Telegram требуется аудио‑формат Opus/OGG:

- **OpenAI, ElevenLabs и Mistral** нативно выводят Opus — дополнительная настройка не нужна
- **Edge TTS** (по умолчанию) выводит MP3 и требует **ffmpeg** для конвертации
- **MiniMax TTS** выводит MP3 и требует **ffmpeg** для конвертации в голосовой пузырёк
- **Google Gemini TTS** выводит сырые PCM и использует **ffmpeg** для прямого кодирования Opus в голосовой пузырёк
- **xAI TTS** выводит MP3 и требует **ffmpeg** для конвертации в голосовой пузырёк
- **NeuTTS** выводит WAV и также требует **ffmpeg** для конвертации в голосовой пузырёк
- **KittenTTS** выводит WAV и также требует **ffmpeg** для конвертации в голосовой пузырёк
- **Piper** выводит WAV и также требует **ffmpeg** для конвертации в голосовой пузырёк

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Fedora
sudo dnf install ffmpeg
```

Без ffmpeg аудио от Edge TTS, MiniMax TTS, NeuTTS, KittenTTS и Piper отправляется как обычный аудиофайл (воспроизводится, но отображается прямоугольным плеером вместо голосового пузырька).

:::tip
Если хочешь голосовые пузырьки без установки ffmpeg, переключись на провайдер OpenAI, ElevenLabs или Mistral.
:::

### Пользовательские голоса xAI (клонирование голоса)

xAI поддерживает клонирование твоего голоса и использование его в TTS. Создай пользовательский голос в [консоли xAI](https://console.x.ai/team/default/voice/voice-library), затем укажи полученный `voice_id` в конфиге:

```yaml
tts:
  provider: xai
  xai:
    voice_id: "nlbqfwie"   # your custom voice ID
```

Смотри [документацию по пользовательским голосам xAI](https://docs.x.ai/developers/model-capabilities/audio/custom-voices) для подробностей о записи, поддерживаемых форматах и ограничениях.

### Piper (локально, 44 языка)

Piper — быстрый локальный нейронный движок TTS от Open Home Foundation (поддержка Home Assistant). Работает полностью на CPU, поддерживает **44 языка** с предобученными голосами и не требует API‑ключа.

**Установить через `hermes tools`** → Voice & TTS → Piper — Hermes выполнит `pip install piper-tts` за тебя. Либо установить вручную: `pip install piper-tts`.

**Переключить на Piper:**

```yaml
tts:
  provider: piper
  piper:
    voice: en_US-lessac-medium
```

При первом вызове TTS для голоса, которого нет в локальном кэше, Hermes выполнит `python -m piper.download_voices <name>` и скачает модель (~20‑90 МБ в зависимости от качества) в `~/.hermes/cache/piper-voices/`. Последующие вызовы используют кэшированную модель.

**Выбор голоса.** Полный каталог голосов доступен [здесь](https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/VOICES.md) и охватывает английский, испанский, французский, немецкий, итальянский, нидерландский, португальский, русский, польский, турецкий, китайский, арабский, хинди и др. — каждый с уровнями качества `x_low` / `low` / `medium` / `high`. Примеры голосов — на [rhasspy.github.io/piper-samples](https://rhasspy.github.io/piper-samples/).

**Использовать заранее скачанный голос.** Укажи `tts.piper.voice` как абсолютный путь, заканчивающийся на `.onnx`:

```yaml
tts:
  piper:
    voice: /path/to/my-custom-voice.onnx
```

**Дополнительные параметры** (`tts.piper.length_scale` / `noise_scale` / `noise_w_scale` / `volume` / `normalize_audio`, `use_cuda`) соответствуют параметрам Piper `SynthesisConfig` один‑к‑одному. Они игнорируются в старых версиях `piper-tts`.

### Провайдеры‑команды

Если нужный тебе TTS‑движок не поддерживается из коробки (VoxCPM, MLX‑Kokoro, XTTS CLI, скрипт клонирования голоса и т.п.), его можно подключить как **провайдер‑команду** без написания Python‑кода. Hermes записывает входной текст во временный UTF‑8 файл, запускает указанную команду и читает полученный аудиофайл.

Объяви один или несколько провайдеров в `tts.providers.<name>` и переключай их через `tts.provider: <name>` — так же, как переключаешь встроенные `edge` и `openai`.

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

#### Пример: Doubao (китайский seed-tts-2.0)

Для качественного китайского TTS через двунаправленный API ByteDance — [seed-tts-2.0](https://www.volcengine.com/docs/6561/1257544) — установи пакет PyPI [`doubao-speech`](https://pypi.org/project/doubao-speech/) и подключи его как провайдер‑команду:

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

Учётные данные берутся из переменных окружения (`VOLCENGINE_APP_ID` / `VOLCENGINE_ACCESS_TOKEN`) или из `~/.doubao-speech/config.yaml`. Выбери голос, добавив `--voice zh-female-warm` (или любой другой алиас из `doubao-speech list-voices`) к команде. `doubao-speech` также включает потоковый ASR — см. раздел [STT ниже](#example-doubao--volcengine-asr) для интеграции с Hermes. Исходный код и полная документация: [github.com/Hypnus-Yuan/doubao-speech](https://github.com/Hypnus-Yuan/doubao-speech).

#### Плейсхолдеры

Шаблон команды может использовать следующие плейсхолдеры. Hermes подставит их во время рендеринга и экранирует каждое значение в зависимости от контекста (без кавычек / одинарные / двойные), поэтому пути с пробелами и другими чувствительными к оболочке символами безопасны.

| Плейсхолдер | Значение |
|--------------|----------|
| `{input_path}` | Путь к временному UTF‑8 файлу с текстом, который записал Hermes |
| `{text_path}` | Синоним `{input_path}` |
| `{output_path}` | Путь, в который команда должна записать аудио |
| `{format}` | `mp3` / `wav` / `ogg` / `flac` |
| `{voice}` | `tts.providers.<name>.voice`, пусто если не задано |
| `{model}` | `tts.providers.<name>.model` |
| `{speed}` | Вычисленный множитель скорости (провайдерный или глобальный) |

Для буквальных фигурных скобок используй `{{` и `}}`.

#### Опциональные ключи

| Ключ | По умолчанию | Описание |
|------|--------------|----------|
| `timeout` | `120` | Секунды; при истечении время процесс‑дерево завершается (Unix `killpg`, Windows `taskkill /T`). |
| `output_format` | `mp3` | Один из `mp3` / `wav` / `ogg` / `flac`. Автоматически выводится из расширения, если Hermes выбирает путь. |
| `voice_compatible` | `false` | При `true` Hermes конвертирует MP3/WAV в Opus/OGG через ffmpeg, чтобы Telegram отобразил голосовой пузырёк. |
| `max_text_length` | `5000` | Ввод обрезается до этой длины перед запуском команды. |
| `voice` / `model` | пусто | Передаётся в команду только как значения плейсхолдеров. |

#### Примечания к поведению

- **Имена встроенных провайдеров всегда имеют приоритет.** Запись `tts.providers.openai` никогда не заменит нативный провайдер OpenAI, поэтому пользовательский конфиг не может тихо переопределить встроенный.
- **Доставка по умолчанию — документ.** Провайдеры‑команды отдают обычные аудиовложения на всех платформах. Чтобы получать голосовые пузырьки, укажите `voice_compatible: true` в конфиге провайдера.
- **Ошибки команды передаются агенту.** Ненулевой код возврата, пустой вывод или тайм‑аут возвращают ошибку с включёнными `stderr`/`stdout`, чтобы ты мог отладить провайдер из диалога.
- **`type: command` задаётся автоматически, если указан `command:`.** Явно писать `type: command` рекомендуется, но не обязательно; запись с непустой строкой `command` считается провайдером‑командой.
- **`{input_path}` и `{text_path}` взаимозаменяемы.** Используй тот, который лучше читается в твоей команде.

#### Безопасность

Провайдеры‑команды выполняют любую оболочечную команду, которую ты укажешь, с правами твоего пользователя. Hermes экранирует значения плейсхолдеров и соблюдает заданный тайм‑аут, но сам шаблон команды считается доверенным локальным вводом — обращайся с ним так же, как с обычным скриптом в `PATH`.

### Провайдеры‑плагины на Python

Для TTS‑движков, которые нельзя выразить одной оболочечной командой — Python‑SDK без CLI, потоковые движки, API списка голосов, OAuth‑обновление токена — зарегистрируй Python‑плагин через `ctx.register_tts_provider()`. Плагин **существует вместе** с реестром [провайдеров‑команд](#custom-command-providers); выбирай тот интерфейс, который лучше подходит твоему движку.

#### Когда что выбирать

| У твоего бэкенда… | Выбирай |
|---|---|
| Один CLI, читающий текст из файла/stdin и записывающий аудио в файл/stdout | **Провайдер‑команда** (Python не нужен) |
| Два‑три CLI, соединённых конвейером | **Провайдер‑команда** |
| Только Python SDK — без CLI | **Плагин** |
| Потоковые байты, которые нужно доставлять кусками (голосовые пузырьки «на лету») | **Плагин** (переопределить `stream()`) |
| API списка голосов, используемое `hermes setup` | **Плагин** (переопределить `list_voices()`) |
| OAuth‑обновление (не статический токен) | **Плагин** |

Встроенные провайдеры всегда имеют приоритет, а провайдеры‑команды выигрывают у плагинов с тем же именем — поэтому плагины можно регистрировать под любыми не‑встроенными именами, не опасаясь перезаписать существующую конфигурацию.

#### Минимальный плагин

Помести это в `~/.hermes/plugins/my-tts/`:

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

Включи его (`hermes plugins enable my-tts`), укажи `tts.provider` на него (`tts.provider: my-tts` в `config.yaml`), и инструмент `text_to_speech` будет маршрутизироваться через твой плагин.

#### Опциональные хуки

Переопредели их в классе провайдера для более глубокой интеграции:

- `list_voices()` → список словарей `{id, display, language, gender, preview_url}`, показываемый в `hermes tools`.
- `list_models()` → список словарей `{id, display, languages, max_text_length}`.
- `get_setup_schema()` → возвращает `{name, badge, tag, env_vars: [{key, prompt, url}]}` для отображения строки выбора в `hermes tools` / `hermes setup`. Без этого плагин работает, но его строка в выборе будет минимальной.
- `stream(text, *, voice, model, format, **extra)` → итератор, выдающий байты аудио для потоковой доставки (по умолчанию бросает `NotImplementedError`).
- Свойство `voice_compatible` → установи `True`, если твой вывод совместим с Opus и шлюз должен доставлять его как голосовой пузырёк (по умолчанию `False` = обычное аудио‑вложение).

См. `agent/tts_provider.py` для полного ABC с докстрингами.
## Транскрипция голосовых сообщений (STT)

Голосовые сообщения, отправленные в Telegram, Discord, WhatsApp, Slack или Signal, автоматически транскрибируются и вставляются в виде текста в разговор. Агент видит транскрипт как обычный текст.

| Provider | Quality | Cost | API Key |
|----------|---------|------|---------|
| **Local Whisper** (default) | Good | Free | None needed |
| **Groq Whisper API** | Good–Best | Free tier | `GROQ_API_KEY` |
| **OpenAI Whisper API** | Good–Best | Paid | `VOICE_TOOLS_OPENAI_KEY` or `OPENAI_API_KEY` |

:::info Zero Config
Локальная транскрипция работает сразу после установки `faster-whisper`. Если её нет, Hermes может также использовать локальный CLI `whisper` из типовых путей установки (например, `/opt/homebrew/bin`) или пользовательскую команду через `HERMES_LOCAL_STT_COMMAND`.
:::

### Конфигурация

```yaml
# In ~/.hermes/config.yaml
stt:
  provider: "local"           # "local" | "groq" | "openai" | "mistral" | "xai"
  local:
    model: "base"             # tiny, base, small, medium, large-v3
  openai:
    model: "whisper-1"        # whisper-1, gpt-4o-mini-transcribe, gpt-4o-transcribe
  mistral:
    model: "voxtral-mini-latest"  # voxtral-mini-latest, voxtral-mini-2602
  xai:
    model: "grok-stt"         # xAI Grok STT
```

### Подробности провайдера

**Local (faster-whisper)** — запускает Whisper локально через [faster-whisper](https://github.com/SYSTRAN/faster-whisper). По умолчанию использует CPU, GPU — если доступен. Размеры моделей:

| Model | Size | Speed | Quality |
|-------|------|-------|---------|
| `tiny` | ~75 MB | Fastest | Basic |
| `base` | ~150 MB | Fast | Good (default) |
| `small` | ~500 MB | Medium | Better |
| `medium` | ~1.5 GB | Slower | Great |
| `large-v3` | ~3 GB | Slowest | Best |

**Groq API** — требует `GROQ_API_KEY`. Хороший облачный запасной вариант, когда нужен бесплатный хостинг STT.

**OpenAI API** — сначала использует `VOICE_TOOLS_OPENAI_KEY`, затем `OPENAI_API_KEY`. Поддерживает `whisper-1`, `gpt-4o-mini-transcribe` и `gpt-4o-transcribe`.

**Mistral API (Voxtral Transcribe)** — требует `MISTRAL_API_KEY`. Использует модели [Voxtral Transcribe](https://docs.mistral.ai/capabilities/audio/speech_to_text/) от Mistral. Поддерживает 13 языков, диаризацию говорящих и метки времени на уровне слов. Устанавливается через `pip install hermes-agent[mistral]`.

**xAI Grok STT** — требует `XAI_API_KEY`. Отправляет запросы на `https://api.x.ai/v1/stt` в формате multipart/form-data. Хороший выбор, если ты уже используешь xAI для чата или TTS и хочешь один API‑ключ для всего. Порядок автоопределения ставит его после Groq — явно укажи `stt.provider: xai`, чтобы принудительно использовать.

**Custom local CLI fallback** — установи `HERMES_LOCAL_STT_COMMAND`, если хочешь, чтобы Hermes вызывал локальную команду транскрипции напрямую. Шаблон команды поддерживает плейсхолдеры `{input_path}`, `{output_dir}`, `{language}` и `{model}`. Твоя команда должна записать файл `.txt` транскрипта где‑нибудь внутри `{output_dir}`.

#### Пример: Doubao / Volcengine ASR

Если ты используешь [`doubao-speech`](https://pypi.org/project/doubao-speech/) для Doubao TTS (см. [выше](#example-doubao-chinese-seed-tts-20)), тот же пакет обрабатывает speech‑to‑text через поверхность локального‑командного STT:

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

Hermes записывает входящее голосовое сообщение в `{input_path}`, запускает команду и читает файл `.txt`, созданный в `{output_dir}`. Язык определяется автоматически эндпоинтом Volcengine bigmodel.

### Поведение при отсутствии провайдера

Если настроенный провайдер недоступен, Hermes автоматически переходит к запасному варианту:
- **Local faster-whisper недоступен** → пытается локальный CLI `whisper` или `HERMES_LOCAL_STT_COMMAND` перед облачными провайдерами
- **Groq key не установлен** → переходит к локальной транскрипции, затем к OpenAI
- **OpenAI key не установлен** → переходит к локальной транскрипции, затем к Groq
- **Mistral key/SDK не установлен** → пропускается в автоопределении; переходит к следующему доступному провайдеру
- **Ничего не доступно** → голосовые сообщения проходят без транскрипции с точной заметкой пользователю

### Пользовательские провайдеры команд STT

Если нужный тебе STT‑движок не поддерживается из коробки (Doubao ASR, NVIDIA Parakeet, сборка whisper.cpp, открытый CLI SenseVoice и т.д.), подключи его как **провайдер типа command** без написания Python‑кода. Hermes запускает твою команду над аудиофайлом и читает полученный транскрипт.

Объяви один или несколько провайдеров в `stt.providers.<name>` и переключай их через `stt.provider: <name>` — та же схема, что и у реестра командных TTS‑провайдеров ([см. custom command providers](#custom-command-providers)), только для направления `input=audio → output=transcript`.

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

Это дополняет устаревший «escape hatch» `HERMES_LOCAL_STT_COMMAND` — переменная окружения по‑прежнему работает через встроенный путь `local_command`. Используй `stt.providers.<name>`, когда нужен **мульти‑провайдерный** набор командных STT‑движков, имя которого выбирается через `stt.provider`, или когда требуется отдельный `language` / `model` / `timeout` для каждого провайдера.

#### Плейсхолдеры STT

Твой шаблон команды может ссылаться на эти плейсхолдеры. Hermes подставляет их во время рендеринга и экранирует каждое значение в зависимости от контекста (bare / одинарные кавычки / двойные кавычки), так что пути с пробелами безопасны.

| Placeholder    | Meaning                                                                 |
|---------------|-------------------------------------------------------------------------|
| `{input_path}` | Абсолютный путь к входному аудиофайлу (исходное расположение, только чтение) |
| `{output_path}`| Абсолютный путь, куда команда должна записать транскрипт               |
| `{output_dir}`| Родительская директория `{output_path}` (удобно для инструментов типа whisper) |
| `{format}`    | Настроенный формат вывода: `txt` / `json` / `srt` / `vtt`                |
| `{language}` | Код языка (по умолчанию `en`)                                           |
| `{model}`     | `stt.providers.<name>.model`, пусто если не задано                     |

Для буквальных фигурных скобок используй `{{` и `}}` (удобно при встраивании JSON‑фрагментов в команду).

#### Как читается транскрипт

После успешного завершения команды:

1. Если существует непустой `{output_path}` → Hermes читает его как UTF‑8‑текст.
2. Иначе, если команда вывела результат в stdout → Hermes использует его.
3. Иначе → ошибка: «Command STT provider wrote no output file and produced no stdout».

Это позволяет использовать реестр как для CLI, пишущих файл (`whisper-cli`, `parakeet-asr`), так и для однострочников curl, которые выводят транскрипт в stdout (`curl … | jq -r .text`).

Для `format: json` / `srt` / `vtt` Hermes возвращает сырое содержимое файла в поле `transcript`. Извлечение `.text` из JSON выходит за рамки раннера — либо укажи `format: txt`, либо обрабатывай JSON дальше по цепочке.

#### Опциональные ключи провайдера команд STT

| Key       | Default | Meaning |
|-----------|---------|---------|
| `timeout` | `300`   | Секунды; дерево процессов будет завершено по истечении (Unix `start_new_session`, Windows `taskkill /T`). |
| `format`  | `txt`   | Один из `txt` / `json` / `srt` / `vtt`. Определяет расширение `{output_path}`. |
| `language`| `en`    | Передаётся в `{language}`. По умолчанию берётся из `stt.language`, затем `en`. |
| `model`    | (empty) | Передаётся в `{model}`. Аргумент `model=` функции `transcribe_audio()` переопределяет его. |

#### Примечания к поведению командных провайдеров STT

- **Встроенные всегда выигрывают.** Объявление `stt.providers.openai: type: command` **не** переопределяет реальный обработчик OpenAI Whisper. Встроенное имя отсекается до запуска резольвера командных провайдеров.
- **Очистка дерева процессов.** При превышении `timeout` завершается всё дерево процессов, а не только оболочка. Длинные пайплайны ASR, форкающие подпроцессы загрузки модели, надёжно убиваются.
- **Экранирование оболочки автоматическое.** Плейсхолдеры внутри `'…'` получают безопасное экранирование одинарными кавычками; внутри `"…"` — `$`/`` ` ``/`"`; вне кавычек — `shlex.quote`. Не предэкранируй значения.

#### Безопасность командных провайдеров STT

Команда выполняется от имени того же пользователя, что и Hermes, с полным доступом к файловой системе — та же модель доверия, что и у `tts.providers.<name>: type: command` и `HERMES_LOCAL_STT_COMMAND`. Объявляй только те провайдеры, которым доверяешь.

### Плагин‑провайдеры Python (STT)

Для STT‑движков, которые не встроены **и** не могут быть выражены как командная строка (нужен Python‑SDK, OAuth‑обновление токенов, потоковая передача, метаданные голоса и т.п.), зарегистрируй Python‑плагин через `ctx.register_transcription_provider()`. Плагин **существует вместе** с шестью встроенными провайдерами (`local`, `local_command`, `groq`, `openai`, `mistral`, `xai`) и реестром `stt.providers.<name>: type: command` — встроенные сохраняют свои реализации и всегда выигрывают при конфликте имён; командные провайдеры выигрывают над плагинами с тем же именем (конфиг более локален, чем установка плагина).

#### Когда что выбирать (STT)

| Backend has… | Use |
|--------------|-----|
| Одна командная строка, принимающая аудиофайл и выдающая текст | `stt.providers.<name>: type: command` (Python не нужен) |
| Нужно только устаревшее одиночное «escape hatch» | `HERMES_LOCAL_STT_COMMAND` env var (сохраняется для совместимости) |
| Python SDK без CLI | `register_transcription_provider()` plugin |
| OAuth‑обновление, потоковая передача, метаданные голоса | `register_transcription_provider()` plugin |
| Встроенный уже покрывает задачу (`local`, `groq`, `openai`, …) | Установи `stt.provider: <name>` — встроенные работают inline |

#### Порядок разрешения

1. **`stt.provider` — имя встроенного провайдера** → вызывается встроенный обработчик. **Всегда выигрывает.**
2. **`stt.provider` совпадает с `stt.providers.<name>` и имеет `type: command`** → запускается командный провайдер (см. [STT custom command providers](#stt-custom-command-providers)). Выигрывает над плагином с тем же именем.
3. **`stt.provider` совпадает с плагином, зарегистрированным как `TranscriptionProvider`** → вызывается плагин:
   - если `is_available()` возвращает `False` (нет учётных данных или SDK), возвращается ошибка недоступности конкретного плагина — **не** общая «No STT provider available».
   - иначе вызывается `transcribe()` с `model` (из публичного аргумента `model=` или `stt.<provider>.model`) и `language` (из `stt.<provider>.language`).
4. **Нет совпадения** → ошибка «No STT provider available».

#### Пространство имён конфигурации провайдера

Плагины читают свою конфигурацию из `stt.<provider>` в `config.yaml`, аналогично тому, как встроенные читают `stt.openai.model` / `stt.mistral.model`:

```yaml
stt:
  provider: my-stt
  my-stt:
    model: whisper-large-v3
    language: ja          # forwarded as language= to transcribe()
    # any other plugin-specific keys go here; read them via your
    # own config.yaml access in __init__/is_available/transcribe
```

Диспетчер передаёт `model` и `language` из этого раздела; всё остальное плагин может читать сам.

#### Минимальный плагин

Помести это в `~/.hermes/plugins/my-stt/`:

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

Включи его (`hermes plugins enable my-stt`), укажи `stt.provider: my-stt` в `config.yaml`, и транскрипция голосовых сообщений будет проходить через твой плагин.

#### Опциональные хуки

Переопредели их в классе провайдера для более глубокой интеграции:

- `list_models()` → список словарей `{id, display, languages, max_audio_seconds}`.
- `default_model()` → строка, возвращаемая, когда пользователь не задаёт модель.
- `get_setup_schema()` → возвращает `{name, badge, tag, env_vars: [{key, prompt, url}]}` для отображения строк выбора в `hermes tools` / `hermes setup` (категория picker для STT пока не выпущена — эти метаданные доступны плагинам для будущей совместимости).

Смотри `agent/transcription_provider.py` для полного ABC с докстрингами.