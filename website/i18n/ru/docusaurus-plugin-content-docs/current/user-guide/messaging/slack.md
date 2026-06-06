---
sidebar_position: 4
title: "Slack"
description: "Настрой Hermes Agent как Slack‑бота с использованием Socket Mode"
---

# Настройка Slack

Подключи Hermes Agent к Slack в качестве бота, используя Socket Mode. Socket Mode использует WebSocket‑соединения вместо публичных HTTP‑конечных точек, поэтому твой экземпляр Hermes не требуется делать общедоступным — он работает за брандмауэрами, на ноутбуке или на частном сервере.

:::warning Классические приложения Slack устарели
Классические приложения Slack (использующие RTM API) **полностью устарели в марте 2025 г.** Hermes использует современный Bolt SDK с Socket Mode. Если у тебя есть старое классическое приложение, необходимо создать новое, следуя инструкциям ниже.
:::
## Обзор

| Компонент | Значение |
|-----------|----------|
| **Библиотека** | `slack-bolt` / `slack_sdk` for Python (Socket Mode) |
| **Подключение** | WebSocket — не требуется публичный URL |
| **Токены аутентификации** | Bot Token (`xoxb-`) + App-Level Token (`xapp-`) |
| **Идентификация пользователя** | Slack Member IDs (например, `U01ABC2DEF3`) |

---
## Шаг 1: Создай приложение Slack

Самый быстрый путь — вставить манифест, который генерирует Hermes. Он объявляет каждую встроенную слеш‑команду (`/btw`, `/stop`, `/model`, …), каждый требуемый OAuth‑scope, каждую подписку на события и включает Socket Mode — всё сразу.

### Вариант A: Из манифеста, сгенерированного Hermes (рекомендовано)

1. Сгенерируй манифест:
      ```bash
   hermes slack manifest --write
   ```
   Это создаёт файл `~/.hermes/slack-manifest.json` и выводит инструкции для вставки.
2. Перейди на [https://api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → **From an app manifest**
3. Выбери рабочее пространство, вставь содержимое JSON, проверь, нажми **Next** → **Create**
4. Перейди к **Step 6: Install App to Workspace**. Манифест обработал OAuth‑scopes, события и слеш‑команды за тебя.

### Вариант B: С нуля (вручную)

1. Перейди на [https://api.slack.com/apps](https://api.slack.com/apps)
2. Нажми **Create New App**
3. Выбери **From scratch**
4. Введи название приложения (например, «Hermes Agent») и выбери своё рабочее пространство
5. Нажми **Create App**

Ты окажешься на странице **Basic Information** приложения. Продолжай с Шагами 2–6 ниже.
## Шаг 2: Настройка Bot Token Scopes

Перейди в **Features → OAuth & Permissions** в боковой панели. Прокрути до **Scopes → Bot Token Scopes** и добавь следующее:

| Scope | Purpose |
|-------|---------|
| `chat:write` | Отправка сообщений от имени бота |
| `app_mentions:read` | Обнаружение упоминаний бота в каналах |
| `channels:history` | Чтение сообщений в публичных каналах, где находится бот |
| `channels:read` | Список и получение информации о публичных каналах |
| `groups:history` | Чтение сообщений в закрытых каналах, куда приглашён бот |
| `im:history` | Чтение истории прямых сообщений |
| `im:read` | Просмотр базовой информации о прямых сообщениях |
| `im:write` | Открытие и управление прямыми сообщениями |
| `users:read` | Получение информации о пользователях |
| `files:read` | Чтение и загрузка вложенных файлов, включая голосовые заметки/аудио |
| `files:write` | Загрузка файлов (изображения, аудио, документы) |

:::caution Missing scopes = missing features
Без `channels:history` и `groups:history` бот **не будет получать сообщения в каналах** — он будет работать только в прямых сообщениях. Без `files:read` Hermes может вести чат, но **не сможет надёжно читать загруженные пользователями вложения**. Это самые часто упускаемые scopes.
:::

**Optional scopes:**

| Scope | Purpose |
|-------|---------|
| `groups:read` | Список и получение информации о закрытых каналах |

---
## Шаг 3: Включить режим Socket Mode

Socket Mode позволяет боту подключаться через WebSocket вместо необходимости публичного URL.

1. В боковой панели перейди в **Settings → Socket Mode**
2. Включи **Enable Socket Mode**
3. Тебе будет предложено создать **App-Level Token**:
   - назови его, например, `hermes-socket` (имя не имеет значения)
   - добавь область доступа **`connections:write`**
   - нажми **Generate**
4. **Скопируй токен** — он начинается с `xapp-`. Это твой `SLACK_APP_TOKEN`

:::tip
Ты всегда можешь найти или сгенерировать токены уровня приложения в разделе **Settings → Basic Information → App-Level Tokens**.
:::
## Шаг 4: Подписка на события

Этот шаг критически важен — он определяет, какие сообщения бот может видеть.

1. В боковой панели перейди к **Features → Event Subscriptions**
2. Переключи **Enable Events** в положение **ON**
3. Разверни **Subscribe to bot events** и добавь:

| Event | Required? | Purpose |
|-------|-----------|---------|
| `message.im` | **Yes** | Бот получает личные сообщения |
| `message.channels` | **Yes** | Бот получает сообщения в **публичных** каналах, в которые он добавлен |
| `message.groups` | **Recommended** | Бот получает сообщения в **приватных** каналах, в которые его пригласили |
| `app_mention` | **Yes** | Предотвращает ошибки Bolt SDK, когда бот упомянут @ |

4. Нажми **Save Changes** внизу страницы

:::danger Отсутствие подписок на события — самая распространённая проблема настройки
Если бот работает в личных сообщениях, но **не в каналах**, ты почти наверняка забыл добавить `message.channels` (для публичных каналов) и/или `message.groups` (для приватных каналов). Без этих событий Slack просто не будет доставлять сообщения каналов боту.
:::
## Шаг 5: Включить вкладку «Messages»

Этот шаг позволяет отправлять прямые сообщения боту. Без него пользователи видят **"Sending messages to this app has been turned off"** при попытке написать боту в личных сообщениях.

1. В боковой панели перейди к **Features → App Home**
2. Прокрути до **Show Tabs**
3. Переключи **Messages Tab** в положение **ON**
4. Отметь **"Allow users to send Slash commands and messages from the messages tab"**

:::danger Без этого шага прямые сообщения полностью блокируются
Даже при наличии всех правильных прав доступа и подписок на события Slack не позволит пользователям отправлять прямые сообщения боту, если вкладка **Messages Tab** не включена. Это требование платформы Slack, а не проблема конфигурации Hermes.
:::
## Шаг 6: Установить приложение в рабочее пространство

1. В боковой панели перейди в **Settings → Install App**
2. Нажми **Install to Workspace**
3. Проверь разрешения и нажми **Allow**
4. После авторизации ты увидишь **Bot User OAuth Token**, начинающийся с `xoxb-`
5. **Скопируй этот токен** — это твой `SLACK_BOT_TOKEN`

:::tip
Если позже изменишь области доступа или подписки на события, ты **должен переустановить приложение**, чтобы изменения вступили в силу. На странице Install App появится баннер с предложением сделать это.
:::

---
## Шаг 7: Поиск идентификаторов пользователей для списка разрешённых

Hermes использует **Member ID** Slack (а не имена пользователей или отображаемые имена) для списка разрешённых.

Чтобы найти Member ID:

1. В Slack нажми на имя пользователя или аватарку
2. Выбери **View full profile**
3. Нажми кнопку **⋮** (more)
4. Выбери **Copy member ID**

Member ID выглядят как `U01ABC2DEF3`. Тебе нужен как минимум твой собственный Member ID.

---
## Шаг 8: Настройка Hermes

Добавь следующее в файл `~/.hermes/.env`:

```bash
# Required
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_APP_TOKEN=xapp-your-app-token-here
SLACK_ALLOWED_USERS=U01ABC2DEF3              # Comma-separated Member IDs

# Optional
SLACK_HOME_CHANNEL=C01234567890              # Default channel for cron/scheduled messages
SLACK_HOME_CHANNEL_NAME=general              # Human-readable name for the home channel (optional)
```

Или запусти интерактивную настройку:

```bash
hermes gateway setup    # Select Slack when prompted
```

Затем запусти gateway:

```bash
hermes gateway              # Foreground
hermes gateway install      # Install as a user service
sudo hermes gateway install --system   # Linux only: boot-time system service
```

---
## Шаг 9: Пригласи бота в каналы

После запуска шлюза тебе нужно **пригласить бота** в любой канал, где ты хочешь, чтобы он отвечал:

```
/invite @Hermes Agent
```

Бот **не** будет автоматически присоединяться к каналам. Его нужно приглашать в каждый канал отдельно.

---
## Slash Commands

Каждая команда Hermes (`/btw`, `/stop`, `/new`, `/model`, `/help`, …) — это нативная slash‑команда Slack, точно так же, как они работают в Telegram и Discord. Набери `/` в Slack, и в автодополнении появятся все команды Hermes с их описанием.

Под капотом: Hermes поставляется с сгенерированным манифестом приложения Slack (см. Шаг 1, Вариант A), в котором каждая команда из
[`COMMAND_REGISTRY`](https://github.com/NousResearch/hermes-agent/blob/main/hermes_cli/commands.py)
объявлена как slash‑команда. В режиме Socket Mode Slack направляет событие команды через WebSocket независимо от поля `url` в манифесте.

### Обновление slash‑команд после изменений

Когда Hermes добавляет новые команды (например, после `hermes update`), сгенерируй манифест заново и обнови приложение Slack:

```bash
hermes slack manifest --write
```

Затем в Slack:
1. Открой [https://api.slack.com/apps](https://api.slack.com/apps) → своё приложение Hermes
2. **Features → App Manifest → Edit**
3. Вставь новое содержимое `~/.hermes/slack-manifest.json`
4. **Save**. Slack предложит переустановить приложение, если изменились области доступа или slash‑команды.

### Устаревший вариант `/hermes <subcommand>` всё ещё работает

Для обратной совместимости со старыми манифестами ты всё ещё можешь вводить
`/hermes btw run the tests` — Hermes обрабатывает это так же, как `/btw run the tests`. Вопросы в свободной форме тоже работают: `/hermes what's the weather?` рассматривается как обычное сообщение.

### Использование команд в тредах (префикс `!cmd`)

Slack блокирует нативные slash‑команды в ответах внутри тредов — попробуй `/queue` в треде, и Slack ответит *"/queue is not supported in threads. Sorry!"*. Нет настройки на стороне приложения, которая могла бы их снова включить; Slack никогда не передаёт их Hermes.

В качестве обходного пути Hermes распознаёт начальный `!` как альтернативный префикс команды, который работает в тредах (и в любом другом месте). Введи `!queue`, `!stop`, `!model gpt-5.4` и т.д. как обычный ответ в треде — Hermes обрабатывает их так же, как slash‑форму и отвечает в той же ветке.

Проверяется только первый токен, поэтому обычные сообщения вроде `!nice work` проходят агенту без изменений.

### Продвинутое: вывести только массив slash‑команд

Если ты поддерживаешь манифест Slack вручную и нужен лишь список slash‑команд:

```bash
hermes slack manifest --slashes-only > /tmp/slashes.json
```

Вставь этот массив в ключ `features.slash_commands` своего текущего манифеста.
## Как бот отвечает

Понимание того, как Hermes Agent ведёт себя в разных контекстах:

| Context | Behavior |
|---------|----------|
| **DMs** | Бот отвечает на каждое сообщение — упоминание не требуется |
| **Channels** | Бот **отвечает только при упоминании** (например, `@Hermes Agent what time is it?`). В каналах Hermes Agent отвечает в треде, прикреплённом к этому сообщению. |
| **Threads** | Если упомянуть Hermes Agent внутри существующего треда, он отвечает в том же треде. Как только у бота появляется активная сессия в треде, **последующие ответы в этом треде не требуют упоминания** — бот продолжает разговор естественно. |

:::tip
В каналах всегда упоминай бота, чтобы начать разговор. Как только бот активен в треде, ты можешь отвечать в этом треде без упоминания. Сообщения без упоминания вне тредов игнорируются, чтобы избежать шума в загруженных каналах.
:::
## Параметры конфигурации

Помимо обязательных переменных окружения из Шага 8, ты можешь настроить поведение Slack‑бота через `~/.hermes/config.yaml`.

### Поведение потоков и ответов

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

| Ключ | По умолчанию | Описание |
|-----|--------------|----------|
| `platforms.slack.reply_to_mode` | `"first"` | Режим ветвления для многочастных сообщений: `"off"`, `"first"` или `"all"` |
| `platforms.slack.extra.reply_in_thread` | `true` | При `false` сообщения в канале получают прямые ответы вместо веток. Сообщения внутри существующих веток всё равно отвечают в ветке. |
| `platforms.slack.extra.reply_broadcast` | `false` | При `true` ответы в ветке также публикуются в основной канал. Только первый фрагмент транслируется. |

### Изоляция сессий

```yaml
# Global setting — applies to Slack and all other platforms
group_sessions_per_user: true
```

Когда `true` (по умолчанию), каждый пользователь в общем канале получает свою изолированную сессию разговора. Два человека, общающиеся с Hermes в `#general`, будут иметь отдельные истории и контексты.

Установи `false`, если нужен совместный режим, где весь канал делит одну сессию разговора. Учти, что в этом случае пользователи совместно используют рост контекста и затраты токенов, а `/reset` одного пользователя сбрасывает сессию для всех.

### Поведение упоминаний и триггеров

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

:::tip Когда использовать `strict_mention`
Установи `true` в загруженных рабочих пространствах, где поведение Slack по умолчанию «бот помнит эту ветку» может удивлять пользователей — например, в длинной техподдержке, где бот помог в начале, а ты хочешь, чтобы он молчал, пока его явно не упомянут снова. Личные сообщения и активные интерактивные сессии не затрагиваются.
:::

:::info
Slack поддерживает оба шаблона: по умолчанию требуется `@mention` для начала разговора, но ты можешь исключить конкретные каналы через `SLACK_FREE_RESPONSE_CHANNELS` (список ID каналов через запятую) или `slack.free_response_channels` в `config.yaml`. Как только бот открывает активную сессию в ветке, последующие ответы в ветке не требуют упоминания. В личных сообщениях бот всегда отвечает без необходимости упоминания.
:::

### Разрешённый список каналов (`allowed_channels`)

Ограничь бота фиксированным набором каналов Slack — полезно, когда бот приглашён во множество каналов, но должен отвечать только в некоторых. При включении сообщения из каналов, НЕ указанных в этом списке, **тихо игнорируются**, даже если бот `@mentioned`.

**Личные сообщения не подпадают под этот фильтр**, поэтому уполномоченные пользователи всегда могут связаться с ботом напрямую.

```yaml
slack:
  allowed_channels:
    - "C0123456789"   # #ops
    - "C0987654321"   # #incident-response
```

Или через переменную окружения (список через запятую):

```bash
SLACK_ALLOWED_CHANNELS="C0123456789,C0987654321"
```

Поведение:

- Пусто / не задано → без ограничений (полностью совместимо со старыми версиями).
- Не пусто → ID канала должен присутствовать в списке, иначе сообщение отбрасывается до применения любых других проверок (требование упоминания, `free_response_channels` и т.п.).
- ID каналов Slack начинаются с `C` (публичный), `G` (приватный) или `D` (личный). Найти их можно в UI Slack → «Open channel details» → панель «About», либо через API.

См. также: [разделение slash‑команд admin/user](../../reference/slash-commands.md#permissions-and-adminuser-split).

### Обработка неавторизованных пользователей

```yaml
slack:
  # What happens when an unauthorized user (not in SLACK_ALLOWED_USERS) DMs the bot
  # "pair"   — prompt them for a pairing code (default)
  # "ignore" — silently drop the message
  unauthorized_dm_behavior: "pair"
```

Ты также можешь задать это глобально для всех платформ:

```yaml
unauthorized_dm_behavior: "pair"
```

Настройка, специфичная для платформы `slack:`, имеет приоритет над глобальной.

### Транскрипция голоса

```yaml
# Global setting — enable/disable automatic transcription of incoming voice messages
stt_enabled: true
```

Когда `true` (по умолчанию), входящие аудиосообщения автоматически транскрибируются с помощью настроенного STT‑провайдера перед обработкой агентом.

### Полный пример

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
## Главный канал

Установи `SLACK_HOME_CHANNEL` в ID канала, куда Hermes будет доставлять запланированные сообщения, результаты cron‑задач и другие проактивные уведомления. Чтобы найти ID канала:

1. Щёлкни правой кнопкой мыши по названию канала в Slack
2. Выбери **View channel details**
3. Прокрути вниз — там будет отображён ID канала

```bash
SLACK_HOME_CHANNEL=C01234567890
```

Убедись, что бот **приглашён в канал** (`/invite @Hermes Agent`).
## Поддержка нескольких рабочих пространств

Hermes может подключаться к **нескольким рабочим пространствам Slack** одновременно, используя один экземпляр gateway. Каждое рабочее пространство аутентифицируется независимо со своим bot user ID.

### Конфигурация

Укажи несколько токенов бота в виде **списка, разделённого запятыми**, в переменной `SLACK_BOT_TOKEN`:

```bash
# Multiple bot tokens — one per workspace
SLACK_BOT_TOKEN=xoxb-workspace1-token,xoxb-workspace2-token,xoxb-workspace3-token

# A single app-level token is still used for Socket Mode
SLACK_APP_TOKEN=xapp-your-app-token
```

Или в файле `~/.hermes/config.yaml`:

```yaml
platforms:
  slack:
    token: "xoxb-workspace1-token,xoxb-workspace2-token"
```

### Файл токенов OAuth

Помимо токенов, заданных в окружении или конфигурации, Hermes также загружает токены из **файла токенов OAuth**, расположенного по адресу:

```
~/.hermes/slack_tokens.json
```

Этот файл представляет собой JSON‑объект, сопоставляющий идентификаторы команд (team IDs) с записями токенов:

```json
{
  "T01ABC2DEF3": {
    "token": "xoxb-workspace-token-here",
    "team_name": "My Workspace"
  }
}
```

Токены из этого файла объединяются с токенами, указанными через `SLACK_BOT_TOKEN`. Дублирующиеся токены автоматически удаляются.

### Как это работает

- **Первый токен** в списке считается основным и используется для подключения в режиме Socket Mode (AsyncApp).
- Каждый токен проходит аутентификацию через `auth.test` при запуске. gateway сопоставляет каждый `team_id` со своим собственным `WebClient` и `bot_user_id`.
- Когда приходит сообщение, Hermes использует соответствующий клиент конкретного рабочего пространства для ответа.
- Основной `bot_user_id` (из первого токена) используется для обратной совместимости с функциями, ожидающими единую идентичность бота.
## Голосовые сообщения

Hermes поддерживает голосовые сообщения в Slack:

- **Входящие:** Голосовые и аудио‑сообщения автоматически транскрибируются с помощью настроенного провайдера STT: локального `faster-whisper`, Groq Whisper (`GROQ_API_KEY`) или OpenAI Whisper (`VOICE_TOOLS_OPENAI_KEY`)
- **Исходящие:** TTS‑ответы отправляются в виде вложений аудиофайлов

---
## Подсказки для отдельных каналов

Назначай эфемерные системные подсказки конкретным каналам Slack. Подсказка вставляется во время выполнения на каждом ходе — никогда не сохраняется в истории транскрипта — поэтому изменения вступают в силу немедленно.

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

Ключами являются идентификаторы каналов Slack (найти их можно в деталях канала → «About» → прокрутить до конца). Все сообщения в соответствующем канале получают эту подсказку как эфемерную системную инструкцию.
## Привязка навыка к каналу

Автоматически загружать навык каждый раз, когда начинается новая сессия в конкретном канале или личных сообщениях. В отличие от привязок подсказок к каналам (которые внедряются на каждом ходу), привязка навыка вставляет содержимое навыка как сообщение пользователя **в начале сессии** — оно становится частью истории разговора и не требует повторной загрузки на последующих ходах.

Это идеально подходит для личных сообщений или каналов с определённой целью (карточки, бот вопросов‑ответов по конкретной области, канал триажа поддержки и т.п.), где не хочется, чтобы встроенный селектор навыков модели решал, загружать ли его при каждом коротком ответе.

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

Примечания:
- Привязка сопоставляется по ID канала. Для сообщений в ветках в привязанном канале ветка наследует привязку родительского канала.
- Навык загружается только в начале сессии (новая сессия или после авто‑сброса). Если ты изменил привязку, запусти `/new` или подожди, пока сессия автоматически сбросится, чтобы изменения вступили в силу.
- Сочетай с `channel_prompts` для задания тона/ограничений канала поверх инструкций навыка.
## Устранение неполадок

| Проблема | Решение |
|---------|----------|
| Бот не отвечает в личных сообщениях | Убедись, что `message.im` включён в подписки на события и приложение переустановлено |
| Бот работает в личных сообщениях, но не в каналах | **Самая распространённая проблема.** Добавь `message.channels` и `message.groups` в подписки на события, переустанови приложение и пригласи бота в канал с помощью `/invite @Hermes Agent` |
| Бот не реагирует на @упоминания в каналах | 1) Проверь, что событие `message.channels` подписано. 2) Бот должен быть приглашён в канал. 3) Убедись, что добавлен scope `channels:history`. 4) Переустанови приложение после изменения scope/событий |
| Бот игнорирует сообщения в приватных каналах | Добавь подписку на событие `message.groups` и scope `groups:history`, затем переустанови приложение и пригласи бота (`/invite @Hermes Agent`) |
| «Sending messages to this app has been turned off» в личных сообщениях | Включи **Messages Tab** в настройках App Home (см. Шаг 5) |
| Ошибки «not_authed» или «invalid_auth» | Сгенерируй заново Bot Token и App Token, обнови `.env` |
| Бот отвечает, но не может публиковать в канал | Пригласи бота в канал с помощью `/invite @Hermes Agent` |
| Бот может вести чат, но не читает загруженные изображения/файлы | Добавь `files:read`, затем **переустанови** приложение. Hermes теперь выводит диагностику доступа к вложениям в чате, когда Slack возвращает ошибки scope/auth/permission. |
| Ошибка `missing_scope` | Добавь требуемый scope в OAuth & Permissions, затем **переустанови** приложение |
| Частые отключения сокета | Проверь сеть; Bolt автоматически переподключается, но нестабильные соединения вызывают задержки |
| Изменены scopes/события, но ничего не изменилось | Ты **должен переустановить** приложение в рабочее пространство после любого изменения scopes или подписки на события |

### Быстрый чек‑лист

Если бот не работает в каналах, проверь **все** перечисленное:

1. ✅ Подписка на событие `message.channels` (для публичных каналов)
2. ✅ Подписка на событие `message.groups` (для приватных каналов)
3. ✅ Подписка на событие `app_mention`
4. ✅ Добавлен scope `channels:history` (для публичных каналов)
5. ✅ Добавлен scope `groups:history` (для приватных каналов)
6. ✅ Приложение было **переустановлено** после добавления scopes/событий
7. ✅ Бот был **приглашён** в канал (`/invite @Hermes Agent`)
8. ✅ Ты **упоминаешь** бота в своём сообщении (`@mention`)
## Безопасность

:::warning
**Всегда задавай `SLACK_ALLOWED_USERS`** с идентификаторами участников, которым разрешён доступ. Без этой настройки шлюз **по умолчанию отклонит все сообщения** как меру предосторожности. Никогда не делись токенами бота — относись к ним как к паролям.
:::

- Токены следует хранить в `~/.hermes/.env` (разрешения файла `600`)
- Периодически обновляй токены через настройки приложения Slack
- Проводите аудит доступа к каталогу конфигурации Hermes
- Режим Socket Mode означает, что публичный эндпоинт не раскрывается — это уменьшает поверхность атаки