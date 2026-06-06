---
sidebar_position: 8
title: "Використовуй голосовий режим з Hermes"
description: "Практичний посібник зі встановлення та використання режиму голосу Hermes у CLI, Telegram, Discord та голосових каналах Discord"
---

# Використовуй голосовий режим з Hermes

Цей посібник — практичний супутник до [документації функції голосового режиму](/user-guide/features/voice-mode).

Якщо сторінка функції пояснює, що може робити голосовий режим, цей посібник показує, як його ефективно використовувати.

:::tip
[Nous Portal](/integrations/nous-portal) об’єднує LLM і TTS через один OAuth — голосовий режим працює від початку до кінця без додаткових облікових даних.
:::
## Для чого корисний режим голосу

Режим голосу особливо корисний, коли:
- ти хочеш працювати в CLI без використання рук
- ти хочеш отримувати голосові відповіді в Telegram або Discord
- ти хочеш, щоб Hermes був у голосовому каналі Discord для живої розмови
- ти хочеш швидко фіксувати ідеї, відлагоджувати або вести діалог під час ходьби замість набору тексту
## Вибери налаштування режиму голосу

У Hermes є три різні голосові варіанти.

| Mode | Best for | Platform |
|---|---|---|
| Interactive microphone loop | Personal hands‑free use while coding or researching | CLI |
| Voice replies in chat | Spoken responses alongside normal messaging | Telegram, Discord |
| Live voice channel bot | Group or personal live conversation in a VC | Discord voice channels |

**Рекомендований порядок:**
1. Спочатку налаштуй текстовий ввід.
2. Потім увімкни голосові відповіді.
3. На кінець, якщо бажаєш повний досвід, перейди до голосових каналів Discord.
## Крок 1: переконайся, що звичайний Hermes працює спочатку

Перш ніж переходити до голосового режиму, перевір:
- Hermes запускається
- твій provider налаштований
- агент може відповідати на текстові підказки у звичайному режимі

```bash
hermes
```

Запитай щось просте:

```text
What tools do you have available?
```

Якщо це ще не стабільно, спочатку виправ текстовий режим.
## Крок 2: встановити потрібні extras

### CLI мікрофон + відтворення

```bash
pip install "hermes-agent[voice]"
```

### Платформи обміну повідомленнями

```bash
pip install "hermes-agent[messaging]"
```

### Преміум ElevenLabs TTS

```bash
pip install "hermes-agent[tts-premium]"
```

### Локальний NeuTTS (опційно)

```bash
python -m pip install -U neutts[all]
```

### Усе

```bash
pip install "hermes-agent[all]"
```
## Крок 3: встановити системні залежності

### macOS

```bash
brew install portaudio ffmpeg opus
brew install espeak-ng
```

### Ubuntu / Debian

```bash
sudo apt install portaudio19-dev ffmpeg libopus0
sudo apt install espeak-ng
```

Чому це важливо:
- `portaudio` → мікрофонний ввід/відтворення для CLI голосового режиму
- `ffmpeg` → конвертація аудіо для TTS та доставки повідомлень
- `opus` → підтримка голосового кодеку Discord
- `espeak-ng` → бекенд фонемізатора для NeuTTS
## Крок 4: вибір провайдерів STT і TTS

Hermes підтримує як локальні, так і хмарні стеки розпізнавання мови.

### Найпростіше / найдешевше налаштування

Використовуй локальний STT і безкоштовний Edge TTS:
- провайдер STT: `local`
- провайдер TTS: `edge`

Зазвичай це найкращий стартовий варіант.

### Приклад файлу середовища

Додай до `~/.hermes/.env`:

```bash
# Cloud STT options (local needs no key)
GROQ_API_KEY=***
VOICE_TOOLS_OPENAI_KEY=***

# Premium TTS (optional)
ELEVENLABS_API_KEY=***
```

### Рекомендації щодо провайдерів

#### Speech-to-text

- `local` → найкращий за замовчуванням для приватності та безкоштовного використання
- `groq` → дуже швидка хмарна транскрипція
- `openai` → хороший платний запасний (варіант)

#### Text-to-speech

- `edge` → безкоштовний і достатньо хороший для більшості користувачів
- `neutts` → безкоштовний локальний/на‑пристрої TTS
- `elevenlabs` → найвища якість
- `openai` → хороший середній варіант
- `mistral` → багатомовний, нативний Opus

### Якщо ти використовуєш `hermes setup`

Якщо ти обираєш NeuTTS у майстрі налаштування, Hermes перевіряє, чи `neutts` вже встановлений. Якщо його немає, майстер повідомляє, що NeuTTS потребує Python‑пакет `neutts` і системний пакет `espeak-ng`, пропонує їх встановити, встановлює `espeak-ng` за допомогою менеджера пакетів твоєї платформи, а потім виконує:

```bash
python -m pip install -U neutts[all]
```

Якщо ти пропустиш це встановлення або воно завершиться помилкою, майстер переходить до запасного (варіанту) Edge TTS.
## Крок 5: рекомендована конфігурація

```yaml
voice:
  record_key: "ctrl+b"
  max_recording_seconds: 120
  auto_tts: false
  beep_enabled: true
  silence_threshold: 200
  silence_duration: 3.0

stt:
  provider: "local"
  local:
    model: "base"

tts:
  provider: "edge"
  edge:
    voice: "en-US-AriaNeural"
```

Це хороший консервативний варіант за замовчуванням для більшості користувачів.

Якщо ти хочеш локальний TTS, заміни блок `tts` на:

```yaml
tts:
  provider: "neutts"
  neutts:
    ref_audio: ''
    ref_text: ''
    model: neuphonic/neutts-air-q4-gguf
    device: cpu
```
## Випадок використання 1: голосовий режим CLI
## Увімкнути його

Запусти Hermes:

```bash
hermes
```

У CLI:

```text
/voice on
```

### Потік запису

Клавіша за замовчуванням:
- `Ctrl+B`

Робочий процес:
1. натисни `Ctrl+B`
2. говори
3. зачекай, доки детектор тиші автоматично не зупинить запис
4. Hermes транскрибує та відповідає
5. якщо TTS увімкнено, він озвучує відповідь
6. цикл може автоматично перезапуститися для безперервного використання

### Корисні команди

```text
/voice
/voice on
/voice off
/voice tts
/voice status
```

### Хороші робочі процеси в CLI

#### Walk-up налагодження

Скажи:

```text
I keep getting a docker permission error. Help me debug it.
```

Потім продовжуй без рук:
- «Прочитай останню помилку ще раз»
- «Поясни причину в простіших термінах»
- «Тепер дай мені точне виправлення»

#### Дослідження / мозковий штурм

Чудово підходить для:
- ходіння навколо під час роздумів
- диктування недороблених ідей
- запиту у Hermes структурувати твої думки в реальному часі

#### Доступність / сесії з мінімальним набором тексту

Якщо набір тексту незручний, голосовий режим — один із найшвидших способів залишатися в повному циклі Hermes.
## Налаштування поведінки CLI

### Поріг тиші

Якщо Hermes запускається/зупиняється занадто агресивно, налаштуй:

```yaml
voice:
  silence_threshold: 250
```

Вищий поріг = менша чутливість.

### Тривалість тиші

Якщо ти часто робиш паузи між реченнями, збільш:

```yaml
voice:
  silence_duration: 4.0
```

### Клавіша запису

Якщо `Ctrl+B` конфліктує з твоїми налаштуваннями терміналу або tmux:

```yaml
voice:
  record_key: "ctrl+space"
```
## Use case 2: voice replies in Telegram or Discord

Цей режим простіший, ніж повноцінні голосові канали.

Hermes залишається звичайним чат‑ботом, але може озвучувати відповіді.

### Start the gateway

```bash
hermes gateway
```

### Turn on voice replies

У Telegram або Discord:

```text
/voice on
```

або

```text
/voice tts
```

### Modes

| Mode | Meaning |
|---|---|
| `off` | лише текст |
| `voice_only` | озвучувати лише коли користувач надіслав голосове повідомлення |
| `all` | озвучувати кожну відповідь |

### When to use which mode

- `/voice on` – якщо потрібні лише голосові відповіді на голосові повідомлення
- `/voice tts` – якщо потрібен постійний голосовий помічник

### Good messaging workflows

#### Telegram‑assistant на твоєму телефоні

Використовуй, коли:
- ти не біля комп’ютера;
- хочеш надсилати голосові нотатки та отримувати швидкі голосові відповіді;
- потрібен Hermes як портативний помічник для досліджень або операцій.

#### Discord DMs з голосовим виводом

Корисно, коли потрібна приватна взаємодія без поведінки згадок у серверних каналах.
## Use case 3: Discord voice channels

This is the most advanced mode.

Hermes joins a Discord VC, listens to user speech, transcribes it, runs the normal agent pipeline, and speaks replies back into the channel.
## Необхідні дозволи Discord

Окрім звичайного налаштування текстового бота, переконайся, що у бота є:
- Connect
- Speak
- бажано Use Voice Activity

Також увімкни привілейовані інтенти в Developer Portal:
- Presence Intent
- Server Members Intent
- Message Content Intent
## Приєднання та вихід

У текстовому каналі Discord, де присутній бот:

```text
/voice join
/voice leave
/voice status
```

### Що відбувається після приєднання

- користувачі говорять у голосовому чаті
- Hermes виявляє межі мовлення
- транскрипти публікуються у пов’язаному текстовому каналі
- Hermes відповідає у тексті та аудіо
- текстовий канал — це той, у якому було виконано `/voice join`

### Кращі практики використання голосового чату Discord

- тримай `DISCORD_ALLOWED_USERS` обмеженим
- спочатку використай спеціальний канал для бота/тестування
- переконайся, що STT і TTS працюють у звичайному режимі текстового чату перед переходом у режим голосового чату
## Рекомендації щодо якості голосу

### Найкраща якість

- STT: local `large-v3` або Groq `whisper-large-v3`
- TTS: ElevenLabs

### Найкраща швидкість/зручність

- STT: local `base` або Groq
- TTS: Edge

### Найкраща безкоштовна конфігурація

- STT: local
- TTS: Edge
## Common failure modes

### "No audio device found"

Встанови `portaudio`.

### "Bot joins but hears nothing"

Перевір:
- чи є твій Discord‑ідентифікатор у `DISCORD_ALLOWED_USERS`
- чи не вимкнено звук
- чи ввімкнено привілейовані intents
- чи має бот дозволи Connect/Speak

### "It transcribes but does not speak"

Перевір:
- налаштування провайдера TTS
- API‑ключ / квоту для ElevenLabs або OpenAI
- встановлення `ffmpeg` для шляхів конвертації Edge

### "Whisper outputs garbage"

Спробуй:
- тихіше оточення
- збільшити `silence_threshold`
- інший провайдер/модель STT
- коротші, чіткіші репліки

### "It works in DMs but not in server channels"

Зазвичай це пов’язано з політикою згадок.

За замовчуванням бот потребує `@mention` у текстових каналах Discord‑серверу, якщо не налаштовано інше.
## Suggested first-week setup

Якщо ти хочеш найкоротший шлях до успіху:

1. запусти текстовий інтерфейс Hermes
2. встанови `hermes-agent[voice]`
3. використай режим voice в CLI з локальним STT + Edge TTS
4. потім увімкни `/voice on` у Telegram або Discord
5. лише після цього спробуй режим голосового каналу Discord

Такий підхід зберігає поверхню налагодження мінімальною.
## Де читати далі

- [Довідка про функцію Voice Mode](/user-guide/features/voice-mode)
- [Шлюз обміну повідомленнями](/user-guide/messaging)
- [Налаштування Discord](/user-guide/messaging/discord)
- [Налаштування Telegram](/user-guide/messaging/telegram)
- [Налаштування](/user-guide/configuration)