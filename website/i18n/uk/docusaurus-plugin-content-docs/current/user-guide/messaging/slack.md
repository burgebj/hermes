---
sidebar_position: 4
title: "Slack"
description: "Налаштуй Hermes Agent як Slack‑бот у режимі Socket Mode"
---

# Налаштування Slack

Підключи Hermes Agent до Slack як бота, використовуючи Socket Mode. Socket Mode працює через WebSockets замість публічних HTTP‑endpoint‑ів, тому твій екземпляр Hermes не потребує публічного доступу — він працює за брандмауерами, на ноутбуці чи на приватному сервері.

:::warning Classic Slack Apps Deprecated
Класичні Slack‑додатки (які використовують RTM API) **повністю виведені з експлуатації у березні 2025 р.** Hermes використовує сучасний Bolt SDK з Socket Mode. Якщо у тебе є старий класичний додаток, потрібно створити новий, слідуючи наведеним нижче крокам.
:::
## Огляд

| Компонент | Значення |
|-----------|----------|
| **Бібліотека** | `slack-bolt` / `slack_sdk` for Python (Socket Mode) |
| **З’єднання** | WebSocket — не потрібна публічна URL‑адреса |
| **Потрібні токени автентифікації** | Bot Token (`xoxb-`) + App-Level Token (`xapp-`) |
| **Ідентифікація користувачів** | Slack Member IDs (наприклад, `U01ABC2DEF3`) |

---
## Крок 1: Створити Slack‑додаток

Найшвидший шлях – вставити маніфест, який генерує Hermes. Він
оголошує всі вбудовані slash‑команди (`/btw`, `/stop`, `/model`, …),
всі необхідні OAuth‑області, всі підписки на події та вмикає Socket
Mode — все одразу.

### Варіант A: З маніфесту, згенерованого Hermes (рекомендовано)

1. Згенеруй маніфест:
      ```bash
   hermes slack manifest --write
   ```
   Це створює `~/.hermes/slack-manifest.json` і виводить інструкції
   щодо вставки.
2. Перейди до [https://api.slack.com/apps](https://api.slack.com/apps) →
   **Create New App** → **From an app manifest**
3. Вибери свою робочу область, встав JSON‑вміст, переглянь, натисни **Next**
   → **Create**
4. Перейди до **Step 6: Install App to Workspace**. Маніфест
   вже налаштував області, події та slash‑команди за тебе.

### Варіант B: З нуля (вручну)

1. Перейди до [https://api.slack.com/apps](https://api.slack.com/apps)
2. Натисни **Create New App**
3. Вибери **From scratch**
4. Введи назву додатку (наприклад, "Hermes Agent") і обери свою робочу область
5. Натисни **Create App**

Ти потрапиш на сторінку **Basic Information** додатку. Продовжуй
з кроками 2–6 нижче.
## Крок 2: Налаштуй області дій Bot Token

Перейди до **Features → OAuth & Permissions** у боковій панелі. Прокрути до **Scopes → Bot Token Scopes** і додай наступні:

| Scope | Призначення |
|-------|-------------|
| `chat:write` | Надсилати повідомлення від імені бота |
| `app_mentions:read` | Виявляти, коли @згадують у каналах |
| `channels:history` | Читати повідомлення у публічних каналах, в яких є бот |
| `channels:read` | Перелік і отримання інформації про публічні канали |
| `groups:history` | Читати повідомлення у приватних каналах, куди запрошено бота |
| `im:history` | Читати історію прямих повідомлень |
| `im:read` | Перегляд базової інформації про прямі повідомлення |
| `im:write` | Відкривати та керувати прямими повідомленнями |
| `users:read` | Дізнаватися інформацію про користувачів |
| `files:read` | Читати та завантажувати прикріплені файли, включно з голосовими нотатками/аудіо |
| `files:write` | Завантажувати файли (зображення, аудіо, документи) |

:::caution Missing scopes = missing features
Без `channels:history` і `groups:history` бот **не отримуватиме повідомлення в каналах** — він працюватиме лише в прямих повідомленнях. Без `files:read` Hermes може спілкуватися, але **не зможе надійно читати завантажені користувачами вкладення**. Це найчастіше пропущені області дій.
:::

**Опційні області дій:**

| Scope | Призначення |
|-------|-------------|
| `groups:read` | Перелік і отримання інформації про приватні канали |

---
## Крок 3: Увімкнути Socket Mode

Socket Mode дозволяє боту підключатися через WebSocket замість того, щоб вимагати публічну URL‑адресу.

1. У боковій панелі перейдіть до **Settings → Socket Mode**
2. Увімкніть **Enable Socket Mode** у стан **ON**
3. Вам буде запропоновано створити **App-Level Token**:
   - Назвіть його, наприклад, `hermes-socket` (назва не має значення)
   - Додайте область **`connections:write`**
   - Натисніть **Generate**
4. **Copy the token** — він починається з `xapp-`. Це ваш `SLACK_APP_TOKEN`

:::tip
Ти завжди можеш знайти або згенерувати токени рівня додатку у розділі **Settings → Basic Information → App-Level Tokens**.
:::
## Крок 4: Підписка на події

Цей крок критичний — він контролює, які повідомлення бот може бачити.

1. У бічній панелі перейдіть до **Features → Event Subscriptions**
2. Перемкніть **Enable Events** у стан **ON**
3. Розгорніть **Subscribe to bot events** і додайте:

| Event | Required? | Purpose |
|-------|-----------|---------|
| `message.im` | **Yes** | Bot receives direct messages |
| `message.channels` | **Yes** | Bot receives messages in **public** channels it's added to |
| `message.groups` | **Recommended** | Bot receives messages in **private** channels it's invited to |
| `app_mention` | **Yes** | Prevents Bolt SDK errors when bot is @mentioned |

4. Натисніть **Save Changes** внизу сторінки

:::danger Missing event subscriptions is the #1 setup issue
Якщо бот працює в ДМ, але **не в каналах**, ти, ймовірно, забув додати
`message.channels` (для публічних каналів) та/або `message.groups` (для приватних каналів).
Без цих подій Slack просто не надсилатиме повідомлення каналів боту.
:::
## Крок 5: Увімкнути вкладку **Messages Tab**

Цей крок дозволяє надсилати прямі повідомлення боту. Без нього користувачі бачать **"Sending messages to this app has been turned off"** під час спроби написати боту в DM.

1. У бічній панелі перейдіть до **Features → App Home**
2. Прокрутіть до **Show Tabs**
3. Перемкніть **Messages Tab** у стан **ON**
4. Позначте **"Allow users to send Slash commands and messages from the messages tab"**

:::danger Без цього кроку DМ‑повідомлення повністю блокуються
Навіть при правильних дозволах і підписках на події Slack не дозволить користувачам надсилати прямі повідомлення боту, якщо вкладка **Messages Tab** не увімкнена. Це вимога платформи Slack, а не проблема налаштувань Hermes.
:::
## Крок 6: Встановити додаток у робочий простір

1. У бічній панелі перейдіть до **Settings → Install App**
2. Натисни **Install to Workspace**
3. Переглянь дозволи та натисни **Allow**
4. Після авторизації ти побачиш **Bot User OAuth Token**, що починається з `xoxb-`
5. **Скопіюй цей токен** — це твій `SLACK_BOT_TOKEN`

:::tip
Якщо ти пізніше змінюєш scopes або підписки на події, ти **повинен переустановити додаток**, щоб зміни набули чинності. На сторінці Install App з’явиться банер із пропозицією це зробити.
:::
## Крок 7: Знайти ID користувачів для білого списку

Hermes використовує Slack **Member IDs** (не імена користувачів або відображувані імена) для білого списку.

Щоб знайти Member ID:

1. У Slack натисни на ім’я або аватар користувача
2. Натисни **View full profile**
3. Натисни кнопку **⋮** (more)
4. Вибери **Copy member ID**

Member IDs виглядають як `U01ABC2DEF3`. Тобі потрібен принаймні твій власний Member ID.

---
## Крок 8: Налаштуй Hermes

Додай наступне у файл `~/.hermes/.env`:

```bash
# Required
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_APP_TOKEN=xapp-your-app-token-here
SLACK_ALLOWED_USERS=U01ABC2DEF3              # Comma-separated Member IDs

# Optional
SLACK_HOME_CHANNEL=C01234567890              # Default channel for cron/scheduled messages
SLACK_HOME_CHANNEL_NAME=general              # Human-readable name for the home channel (optional)
```

Або запусти інтерактивну настройку:

```bash
hermes gateway setup    # Select Slack when prompted
```

Потім запусти шлюз:

```bash
hermes gateway              # Foreground
hermes gateway install      # Install as a user service
sudo hermes gateway install --system   # Linux only: boot-time system service
```

---
## Крок 9: Запроси бота в канали

Після запуску шлюзу потрібно **запросити бота** в будь‑який канал, у якому ти хочеш, щоб він відповідав:

```
/invite @Hermes Agent
```

Бот **не** приєднається до каналів автоматично. Тобі треба запросити його в кожен канал окремо.
## Slash Commands

Кожна команда Hermes (`/btw`, `/stop`, `/new`, `/model`, `/help`, …) є
рідною slash‑командою Slack — саме так вони працюють у Telegram і
Discord. Введи `/` у Slack, і автодоповнювач покаже всі команди Hermes
з їх описом.

Під капотом: Hermes постачається зі згенерованим маніфестом Slack‑додатку
(див. Крок 1, Варіант A), який оголошує кожну команду у
[`COMMAND_REGISTRY`](https://github.com/NousResearch/hermes-agent/blob/main/hermes_cli/commands.py)
як slash‑команду. У Socket Mode Slack передає подію команди через
WebSocket незалежно від поля `url` у маніфесті.

### Оновлення slash‑команд після змін

Коли Hermes додає нові команди (наприклад після `hermes update`), згенеруй
заново маніфест і онови свій Slack‑додаток:

```bash
hermes slack manifest --write
```

Потім у Slack:
1. Відкрий [https://api.slack.com/apps](https://api.slack.com/apps) →
   свій Hermes‑додаток
2. **Features → App Manifest → Edit**
3. Встав новий вміст `~/.hermes/slack-manifest.json`
4. **Save**. Slack запропонує переустановити додаток, якщо змінилися
   scopes або slash‑команди.

### Legacy `/hermes <subcommand>` все ще працює

Для зворотної сумісності зі старими маніфестами ти все ще можеш вводити
`/hermes btw run the tests` — Hermes обробляє це так само, як `/btw
run the tests`. Питання у вільній формі теж працюють:
`/hermes what's the weather?` розглядається як звичайне повідомлення.

### Використання команд у тредах (префікс `!cmd`)

Slack блокує рідні slash‑команди у відповідях у тредах — спробуй
`/queue` у треді, і Slack відповість *"/queue is not supported in
threads. Sorry!"*. Немає налаштування на боці додатку, яке їх
поверне; Slack ніколи не доставляє їх Hermes.

Як обхідний шлях, Hermes розпізнає початковий `!` як альтернативний
префікс команди, який працює у тредах (і в будь‑якому іншому місці).
Введи `!queue`, `!stop`, `!model gpt-5.4` тощо як звичайну відповідь у
треді — Hermes обробляє їх так само, як slash‑форму, і відповідає в
тому ж треді.

Перевіряється лише перший токен проти відомого списку команд, тому
повідомлення типу `!nice work` проходять до агента без змін.

### Розширено: вивести лише масив slash‑commands

Якщо ти підтримуєш маніфест Slack вручну і потрібен лише список
slash‑команд:

```bash
hermes slack manifest --slashes-only > /tmp/slashes.json
```

Встав цей масив у ключ `features.slash_commands` свого існуючого
маніфесту.

---
## Як бот відповідає

Розуміння того, як Hermes поводиться в різних контекстах:

| Context | Behavior |
|---------|----------|
| **DMs** | Bot відповідає на кожне повідомлення — без необхідності @згадки |
| **Channels** | Bot **відповідає лише коли його @згадують** (наприклад, `@Hermes Agent what time is it?`). У каналах Hermes відповідає в треді, прикріпленому до цього повідомлення. |
| **Threads** | Якщо ти @згадуєш Hermes всередині існуючого треду, він відповідає в цьому ж треді. Після того, як бот має активну сесію в треді, **подальші відповіді в цьому треді не потребують @згадки** — бот природно продовжує розмову. |

:::tip
У каналах завжди @згадуй бота, щоб розпочати розмову. Після того, як бот активний у треді, ти можеш відповідати в цьому треді без згадки. Позапоточні повідомлення без @згадки ігноруються, щоб запобігти шуму в зайнятих каналах.
:::
## Параметри конфігурації

Окрім обов’язкових змінних середовища з кроку 8, ти можеш налаштувати поведінку Slack‑бота у файлі `~/.hermes/config.yaml`.

### Поведінка потоків та відповідей

```yaml
platforms:
  slack:
    # Controls how multi-part responses are threaded
    # "off"   — never thread replies to the original message
    # "first" — first chunk threads to user's message (default)
    # "all"   — all chunks thread to user's message
    reply_to_mode: "first"

    extra:
      # Whether to reply in a thread (default: true).
      # When false, channel messages get direct channel replies instead
      # of threads. Messages inside existing threads still reply in-thread.
      reply_in_thread: true

      # Also post thread replies to the main channel
      # (Slack's "Also send to channel" feature).
      # Only the first chunk of the first reply is broadcast.
      reply_broadcast: false
```

| Ключ | За замовчуванням | Опис |
|-----|------------------|------|
| `platforms.slack.reply_to_mode` | `"first"` | Режим створення потоків для багаточастинних повідомлень: `"off"`, `"first"` або `"all"` |
| `platforms.slack.extra.reply_in_thread` | `true` | Якщо `false`, повідомлення в каналі отримують прямі відповіді замість потоків. Повідомлення в існуючих потоках все одно відповідаються у потоці. |
| `platforms.slack.extra.reply_broadcast` | `false` | Якщо `true`, відповіді у потоці також публікуються у головному каналі. Тільки перший фрагмент транслюється. |

### Ізоляція сесії

```yaml
# Global setting — applies to Slack and all other platforms
group_sessions_per_user: true
```

Коли `true` (за замовчуванням), кожен користувач у спільному каналі отримує свою ізольовану сесію розмови. Двоє людей, які спілкуються з Hermes у `#general`, матимуть окремі історії та контексти.

Встанови `false`, якщо потрібен колаборативний режим, коли весь канал ділиться однією сесією розмови. Зауваж, що це означає спільне зростання контексту та витрати токенів, а команда `/reset` одного користувача скидає сесію для всіх.

### Поведінка згадок та тригерів

```yaml
slack:
  # Require @mention in channels (this is the default behavior;
  # the Slack adapter enforces @mention gating in channels regardless,
  # but you can set this explicitly for consistency with other platforms)
  require_mention: true

  # Prevent thread auto-engagement: only reply to channel messages that
  # contain an explicit @mention. With this OFF (default), Slack can
  # "auto-engage" — remembering past mentions in a thread and following
  # up on bot-message replies, and resuming active sessions without a
  # fresh mention. With strict_mention ON, every new channel message
  # must @mention the bot before Hermes will respond.
  strict_mention: false

  # Custom mention patterns that trigger the bot
  # (in addition to the default @mention detection)
  mention_patterns:
    - "hey hermes"
    - "hermes,"

  # Text prepended to every outgoing message
  reply_prefix: ""
```

:::tip Коли використовувати `strict_mention`
Встанови це в `true` у зайнятих робочих просторах, де стандартна поведінка Slack «бот пам’ятає цей потік» може здивувати користувачів — наприклад, у довгому технічному потоці підтримки, де бот допоміг на початку, а ти хочеш, щоб він залишався мовчазним, доки його явно не згадати знову. Прямі повідомлення та активні інтерактивні сесії не змінюються.
:::

:::info
Slack підтримує обидва варіанти: за замовчуванням потрібна `@mention` для старту розмови, але можна виключити конкретні канали через `SLACK_FREE_RESPONSE_CHANNELS` (список ID каналів, розділених комами) або `slack.free_response_channels` у `config.yaml`. Після того, як бот має активну сесію у потоці, подальші відповіді у цьому потоці не вимагають згадки. У прямих повідомленнях бот завжди відповідає без згадки.
:::

### Білий список каналів (`allowed_channels`)

Обмеж бот фіксованим набором Slack‑каналів — корисно, коли бот запрошений у багато каналів, але має відповідати лише в декількох. Коли параметр встановлений, повідомлення з каналів, яких **немає** у цьому списку, **тихо ігноруються**, навіть якщо бот `@mentioned`.

**Прямі повідомлення** не підлягають цьому фільтру, тому уповноважені користувачі завжди можуть звертатися до бота в DM.

```yaml
slack:
  allowed_channels:
    - "C0123456789"   # #ops
    - "C0987654321"   # #incident-response
```

Або через змінну середовища (список, розділений комами):

```bash
SLACK_ALLOWED_CHANNELS="C0123456789,C0987654321"
```

Поведінка:

- Порожнє / не встановлене → без обмежень (повна зворотна сумісність).
- Не порожнє → ID каналу має бути у списку, інакше повідомлення відкидається ще до будь‑яких інших перевірок (вимоги згадки, `free_response_channels` тощо).
- ID каналів Slack починаються з `C` (публічний), `G` (приватний) або `D` (DM). Дізнайся їх у UI Slack у розділі «Open channel details» → «About», або через API.

Дивись також: [admin/user slash command split](../../reference/slash-commands.md#permissions-and-adminuser-split).

### Обробка неавторизованих користувачів

```yaml
slack:
  # What happens when an unauthorized user (not in SLACK_ALLOWED_USERS) DMs the bot
  # "pair"   — prompt them for a pairing code (default)
  # "ignore" — silently drop the message
  unauthorized_dm_behavior: "pair"
```

Ти можеш також встановити це глобально для всіх платформ:

```yaml
unauthorized_dm_behavior: "pair"
```

Налаштування, специфічне для платформи під `slack:`, має пріоритет над глобальним.

### Транскрипція голосу

```yaml
# Global setting — enable/disable automatic transcription of incoming voice messages
stt_enabled: true
```

Коли `true` (за замовчуванням), вхідні аудіо‑повідомлення автоматично транскрибуються за допомогою налаштованого STT‑провайдера перед обробкою агентом.

### Повний приклад

```yaml
# Global gateway settings
group_sessions_per_user: true
unauthorized_dm_behavior: "pair"
stt_enabled: true

# Slack-specific settings
slack:
  require_mention: true
  unauthorized_dm_behavior: "pair"

# Platform config
platforms:
  slack:
    reply_to_mode: "first"
    extra:
      reply_in_thread: true
      reply_broadcast: false
```

---
## Канал Home

Встанови `SLACK_HOME_CHANNEL` у ідентифікатор каналу, куди Hermes буде надсилати заплановані повідомлення, результати cron‑завдань та інші проактивні сповіщення. Щоб знайти ідентифікатор каналу:

1. Клацни правою кнопкою миші на назві каналу в Slack
2. Вибери **View channel details**
3. Прокрути донизу — там буде показано ідентифікатор каналу

```bash
SLACK_HOME_CHANNEL=C01234567890
```

Переконайся, що бот **запрошений у канал** (`/invite @Hermes Agent`).

---
## Підтримка кількох робочих просторів Slack

Hermes може підключатися до **кількох робочих просторів Slack** одночасно, використовуючи один екземпляр шлюзу. Кожен робочий простір автентифікується окремо зі своїм ідентифікатором користувача‑бота.

### Конфігурація

Надай кілька токенів бота у вигляді **списку, розділеного комами** у `SLACK_BOT_TOKEN`:

```bash
# Multiple bot tokens — one per workspace
SLACK_BOT_TOKEN=xoxb-workspace1-token,xoxb-workspace2-token,xoxb-workspace3-token

# A single app-level token is still used for Socket Mode
SLACK_APP_TOKEN=xapp-your-app-token
```

Або у `~/.hermes/config.yaml`:

```yaml
platforms:
  slack:
    token: "xoxb-workspace1-token,xoxb-workspace2-token"
```

### Файл OAuth‑токенів

Окрім токенів у середовищі або конфігурації, Hermes також завантажує токени з **файлу OAuth‑токенів** за адресою:

```
~/.hermes/slack_tokens.json
```

Цей файл — JSON‑об’єкт, що відображає ідентифікатори команд у токенних записах:

```json
{
  "T01ABC2DEF3": {
    "token": "xoxb-workspace-token-here",
    "team_name": "My Workspace"
  }
}
```

Токени з цього файлу об’єднуються з будь‑якими токенами, вказаними через `SLACK_BOT_TOKEN`. Дублікати токенів автоматично видаляються.

### Як це працює

- **Перший токен** у списку є основним, використовується для підключення в режимі Socket Mode (`AsyncApp`).
- Кожен токен автентифікується через `auth.test` під час запуску. Шлюз прив’язує кожен `team_id` до свого власного `WebClient` та `bot_user_id`.
- Коли надходить повідомлення, Hermes використовує відповідний клієнт, специфічний для робочого простору, щоб відповісти.
- Основний `bot_user_id` (з першого токену) використовується для зворотної сумісності з функціями, які очікують єдину ідентичність бота.

---
## Голосові повідомлення

Hermes підтримує голос у Slack:

- **Вхідні:** Голосові та аудіо повідомлення автоматично транскрибуються за допомогою налаштованого STT‑провайдера: локальний `faster-whisper`, Groq Whisper (`GROQ_API_KEY`) або OpenAI Whisper (`VOICE_TOOLS_OPENAI_KEY`)
- **Вихідні:** Відповіді TTS надсилаються у вигляді аудіофайлів‑вкладень

---
## Підказки для окремих каналів

Призначай тимчасові системні підказки конкретним каналам Slack. Підказка вставляється під час виконання на кожному ході — ніколи не зберігається в історії транскрипції — тому зміни набувають чинності одразу.

```yaml
slack:
  channel_prompts:
    "C01RESEARCH": |
      You are a research assistant. Focus on academic sources,
      citations, and concise synthesis.
    "C02ENGINEERING": |
      Code review mode. Be precise about edge cases and
      performance implications.
```

Ключами є ідентифікатори каналів Slack (знайди їх у деталях каналу → «Про» → прокрути донизу). Усі повідомлення в відповідному каналі отримують підказку у вигляді тимчасової системної інструкції.
## Прив’язки навичок до каналів

Автозавантаження навички щоразу, коли в певному каналі або DM починається нова сесія. На відміну від підказок для окремих каналів (які ін’єкціюються на кожному кроці), прив’язки навичок вставляють вміст навички як повідомлення користувача на **початку сесії** — воно стає частиною історії розмови і не потребує повторного завантаження на наступних кроках.

Це ідеально підходить для DM або каналів з визначеною метою (флеш‑картки, бот питань‑відповідей за певною доменною темою, канал триажу підтримки тощо), коли не хочеш, щоб власний селектор навичок моделі вирішував, чи завантажувати її на кожну коротку відповідь.

```yaml
slack:
  channel_skill_bindings:
    # DM channel — always runs in "german-flashcards" mode
    - id: "D0ATH9TQ0G6"
      skills:
        - german-flashcards
    # Research channel — preload multiple skills in order
    - id: "C01RESEARCH"
      skills:
        - arxiv
        - writing-plans
    # Short form: single skill as a string
    - id: "C02SUPPORT"
      skill: hubspot-on-demand
```

Примітки:
- Прив’язка збігається за ідентифікатором каналу. Для повідомлень у гілці в прив’язаному каналі гілка успадковує прив’язку батьківського каналу.
- Навичка завантажується лише на початку сесії (нова сесія або після автоматичного скидання). Якщо ти змінюєш прив’язку, запусти `/new` або зачекай, доки сесія автоматично не скинеся, щоб зміни набули чинності.
- Поєднуй з `channel_prompts` для налаштування тону/обмежень каналу поверх інструкцій навички.
## Устранення проблем

| Проблема | Рішення |
|----------|----------|
| Bot doesn't respond to DMs | Перевір, що `message.im` включено у підписки на події, і додаток переустановлено |
| Bot works in DMs but not in channels | **Найпоширеніша проблема.** Додай `message.channels` і `message.groups` до підписок на події, переустанови додаток і запроси бота в канал за допомогою `/invite @Hermes Agent` |
| Bot doesn't respond to @mentions in channels | 1) Перевір, що підписка на подію `message.channels` активна. 2) Бот має бути запрошений у канал. 3) Переконайся, що додано scope `channels:history`. 4) Переустанови додаток після змін scope/подій |
| Bot ignores messages in private channels | Додай підписку на подію `message.groups` і scope `groups:history`, потім переустанови додаток і запроси бота (`/invite @Hermes Agent`) |
| "Sending messages to this app has been turned off" in DMs | Увімкни **Messages Tab** у налаштуваннях App Home (дивись крок 5) |
| "not_authed" або "invalid_auth" помилки | Згенеруй заново Bot Token і App Token, онови `.env` |
| Bot responds but can't post in a channel | Запроси бота в канал за допомогою `/invite @Hermes Agent` |
| Bot can chat but can't read uploaded images/files | Додай `files:read`, потім **переустанови** додаток. Hermes тепер показує діагностику доступу до вкладень у чаті, коли Slack повертає помилки scope/auth/permission. |
| `missing_scope` помилка | Додай необхідний scope у OAuth & Permissions, потім **переустанови** додаток |
| Socket disconnects frequently | Перевір мережу; Bolt автоматично перепідключається, але нестабільні з’єднання викликають затримки |
| Changed scopes/events but nothing changed | Ти **повинен переустановити** додаток у своєму робочому просторі після будь‑якої зміни scope або підписки на події |

### Швидка контрольна листа

Якщо бот не працює в каналах, перевір **усі** наступні пункти:

1. ✅ Подія `message.channels` підписана (для публічних каналів)
2. ✅ Подія `message.groups` підписана (для приватних каналів)
3. ✅ Подія `app_mention` підписана
4. ✅ Додано scope `channels:history` (для публічних каналів)
5. ✅ Додано scope `groups:history` (для приватних каналів)
6. ✅ Додаток **переустановлено** після додавання scope/подій
7. ✅ Бот **запрошений** до каналу (`/invite @Hermes Agent`)
8. ✅ Ти **@згадуєш** бота у своєму повідомленні

---
## Безпека

:::warning
**Завжди встановлюй `SLACK_ALLOWED_USERS`** з Member ID авторизованих користувачів. Без цього налаштування,
шлюз **відхилятиме всі повідомлення** за замовчуванням як захисний захід. Ніколи не поширюй токени бота —
став їх на рівень паролів.
:::

- Токени слід зберігати у `~/.hermes/.env` (права доступу файлу `600`)
- Періодично оновлюй токени через налаштування Slack‑додатку
- Проводь аудит, хто має доступ до каталогу конфігурації Hermes
- Socket Mode означає, що публічний кінцевий пункт не відкритий — ще один меншій вектор атаки