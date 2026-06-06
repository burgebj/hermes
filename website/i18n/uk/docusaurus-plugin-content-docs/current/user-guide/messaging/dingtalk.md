---
sidebar_position: 10
title: "DingTalk"
description: "Налаштуй Hermes Agent як чат-бот DingTalk"
---

# Налаштування DingTalk

Hermes Agent інтегрується з DingTalk (钉钉) як чат‑бот, дозволяючи спілкуватися з твоїм AI‑асистентом через прямі повідомлення або групові чати. Бот підключається через **Stream Mode** — довготривале WebSocket‑з’єднання, яке не потребує публічної URL‑адреси чи сервера веб‑хуків — і відповідає, використовуючи повідомлення у форматі markdown через **API веб‑хука сесії** DingTalk.

Перед налаштуванням ось те, що більшість людей хоче знати: як Hermes поводиться, коли він вже знаходиться у твоєму робочому просторі DingTalk.
## Як поводиться Hermes

| Context | Behavior |
|---------|----------|
| **DMs (1:1 chat)** | Hermes відповідає на кожне повідомлення. `@mention` не потрібен. Кожен DM має свою сесію. |
| **Group chats** | Hermes відповідає, коли ти `@mention` його. Без згадки Hermes ігнорує повідомлення. |
| **Shared groups with multiple users** | За замовчуванням Hermes ізолює історію сесії для кожного користувача в групі. Двоє людей, які спілкуються в одній групі, не ділять один транскрипт, якщо ти явно не вимкнув це. |

### Модель сесії в DingTalk

За замовчуванням:

- кожен DM отримує свою сесію
- кожен користувач у спільному груповому чаті отримує свою сесію всередині цієї групи

Це контролюється файлом `config.yaml`:

```yaml
group_sessions_per_user: true
```

Встанови `false` лише якщо ти явно хочеш одну спільну розмову для всієї групи:

```yaml
group_sessions_per_user: false
```

Цей посібник проведе тебе через повний процес налаштування — від створення твого бота DingTalk до надсилання першого повідомлення.
## Передумови

Встанови необхідні пакети Python:

```bash
pip install "hermes-agent[dingtalk]"
```

Або окремо:

```bash
pip install dingtalk-stream httpx alibabacloud-dingtalk
```

- `dingtalk-stream` — офіційний SDK DingTalk для режиму Stream (реальний‑часовий обмін повідомленнями на базі WebSocket)
- `httpx` — асинхронний HTTP‑клієнт, що використовується для надсилання відповідей через веб‑хук сесії
- `alibabacloud-dingtalk` — SDK DingTalk OpenAPI для AI‑карток, реакцій emoji та завантаження медіа
## Крок 1: Створити DingTalk‑додаток

1. Перейди до [DingTalk Developer Console](https://open-dev.dingtalk.com/).
2. Увійди за допомогою свого облікового запису адміністратора DingTalk.
3. Натисни **Application Development** → **Custom Apps** → **Create App via H5 Micro-App** (або **Robot**, залежно від версії консолі).
4. Заповни:
   - **App Name**: напр., `Hermes Agent`
   - **Description**: необов’язково
5. Після створення перейди до **Credentials & Basic Info**, щоб знайти свій **Client ID** (AppKey) та **Client Secret** (AppSecret). Скопіюй обидва.

:::warning[Credentials shown only once]
**Client Secret** відображається лише один раз під час створення додатку. Якщо ти його втратиш, доведеться згенерувати новий. Ніколи не публікуй ці облікові дані та не додавай їх у репозиторій Git.
:::
## Крок 2: Увімкнути можливість Robot

1. На сторінці налаштувань твого застосунку перейдіть до **Add Capability** → **Robot**.
2. Увімкніть можливість Robot.
3. У розділі **Message Reception Mode** виберіть **Stream Mode** (рекомендовано — не потрібен публічний URL).

:::tip
Stream Mode — це рекомендована конфігурація. Вона використовує довготривале підключення WebSocket, ініційоване з твого комп’ютера, тому тобі не потрібна публічна IP‑адреса, доменне ім’я чи кінцева точка webhook. Це працює за NAT, через брандмауери та на локальних машинах.
:::
## Крок 3: Знайди свій DingTalk User ID

Hermes Agent використовує твій DingTalk User ID, щоб контролювати, хто може взаємодіяти з ботом. DingTalk User ID — це алфавітно‑цифрові рядки, які задає адміністратор твоєї організації.

Щоб знайти його:

1. Запитай у адміністратора твоєї організації DingTalk — User ID налаштовуються в консолі адміністратора DingTalk у розділі **Contacts** → **Members**.
2. Або бот записує `sender_id` для кожного вхідного повідомлення. Запусти gateway, надішли боту повідомлення, а потім перевір журнали, щоб побачити свій ID.
## Крок 4: Налаштування Hermes Agent

### Варіант A: Інтерактивне налаштування (рекомендовано)

Запусти команду налаштування з підказками:

```bash
hermes gateway setup
```

Вибери **DingTalk**, коли буде запитано. Майстер налаштування може авторизуватись одним із двох шляхів:

- **QR‑code device flow (рекомендовано).** Скануй QR‑код, який виводиться у твоєму терміналі, за допомогою мобільного додатку DingTalk — твій **Client ID** і **Client Secret** будуть повернуті автоматично і записані у `~/.hermes/.env`. Не потрібно переходити в консоль розробника.
- **Manual paste.** Якщо у тебе вже є облікові дані (або сканування QR‑коду незручне), встав свої **Client ID**, **Client Secret** та дозволені ідентифікатори користувачів, коли буде запитано.

:::note openClaw branding disclosure
Оскільки `verification_uri_complete` DingTalk жорстко закодовано на ідентифікатор **openClaw** на рівні API, QR наразі авторизує під рядком джерела `openClaw`, доки Alibaba / DingTalk‑Real‑AI не зареєструє сервер‑сторонній шаблон, специфічний для Hermes. Це лише те, як DingTalk відображає екран згоди — бот, який ти створюєш, повністю твій і приватний для твого орендаря.
:::

### Варіант B: Ручна конфігурація

Додай наступне у файл `~/.hermes/.env`:

```bash
# Required
DINGTALK_CLIENT_ID=your-app-key
DINGTALK_CLIENT_SECRET=your-app-secret

# Security: restrict who can interact with the bot
DINGTALK_ALLOWED_USERS=user-id-1

# Multiple allowed users (comma-separated)
# DINGTALK_ALLOWED_USERS=user-id-1,user-id-2

# Optional: group-chat gating (mirrors Slack/Telegram/Discord/WhatsApp)
# DINGTALK_REQUIRE_MENTION=true
# DINGTALK_FREE_RESPONSE_CHATS=cidABC==,cidDEF==
# DINGTALK_MENTION_PATTERNS=^小马
# DINGTALK_HOME_CHANNEL=cidXXXX==
# DINGTALK_ALLOW_ALL_USERS=true
```

Опціональні налаштування поведінки у `~/.hermes/config.yaml`:

```yaml
group_sessions_per_user: true

gateway:
  platforms:
    dingtalk:
      extra:
        # Require @mention in groups before the bot replies (parity with Slack/Telegram/Discord).
        # DMs ignore this — the bot always replies in 1:1 chats.
        require_mention: true

        # Per-platform allowlist. When set, only these DingTalk user IDs can interact with the bot
        # (same semantics as DINGTALK_ALLOWED_USERS, but scoped here instead of in .env).
        allowed_users:
          - user-id-1
          - user-id-2
```

- `group_sessions_per_user: true` зберігає контекст кожного учасника окремо в спільних групових чатах
- `require_mention: true` запобігає відповіді бота на кожне групове повідомлення — він відповідає лише коли хтось згадує його за допомогою `@`
- `allowed_users` у `dingtalk.extra` є альтернативою `DINGTALK_ALLOWED_USERS`; якщо встановлені обидва, вони об’єднуються

### Запуск шлюзу

Після налаштування запусти шлюз **DingTalk**:

```bash
hermes gateway
```

Бот має підключитися до **Stream Mode** DingTalk за кілька секунд. Надішли йому повідомлення — будь то приватний чат або група, куди його додали — щоб перевірити.

:::tip
Ти можеш запускати `hermes gateway` у фоні або як службу `systemd` для постійної роботи. Дивись документацію з розгортання для деталей.
:::
## Функції

### AI‑карти

Hermes може відповідати, використовуючи AI‑карти DingTalk замість простих markdown‑повідомлень. Карти забезпечують більш насичений, структурований вигляд і підтримують потокові оновлення під час генерації відповіді агентом.

Щоб увімкнути AI‑карти, налаштуй ідентифікатор шаблону карти у `config.yaml`:

```yaml
platforms:
  dingtalk:
    enabled: true
    extra:
      card_template_id: "your-card-template-id"
```

Ти можеш знайти свій ідентифікатор шаблону карти в консолі розробника DingTalk у розділі налаштувань AI‑карт твого застосунку. Коли AI‑карти увімкнені, усі відповіді надсилаються у вигляді карт з потоковими оновленнями тексту.

### Реакції‑емодзі

Hermes автоматично додає реакції‑емодзі до твоїх повідомлень, щоб показати статус обробки:

- 🤔Thinking — додається, коли бот починає обробляти твоє повідомлення
- 🥳Done — додається, коли відповідь завершена (замінює реакцію Thinking)

Ці реакції працюють і в приватних повідомленнях, і в групових чатах.

### Налаштування відображення

Ти можеш налаштувати поведінку відображення DingTalk незалежно від інших платформ:

```yaml
display:
  platforms:
    dingtalk:
      show_reasoning: false   # Show model reasoning/thinking in replies
      streaming: true         # Enable streaming responses (works with AI Cards)
      tool_progress: all      # Show tool execution progress (all/new/off)
      interim_assistant_messages: true  # Show intermediate commentary messages
```

Щоб вимкнути прогрес інструментів та проміжні повідомлення для чистішого досвіду:

```yaml
display:
  platforms:
    dingtalk:
      tool_progress: off
      interim_assistant_messages: false
```
## Устранення неполадок

### Бот не відповідає на повідомлення

**Причина**: Можливість бота не ввімкнена, або `DINGTALK_ALLOWED_USERS` не містить вашого User ID.

**Виправлення**: Перевір, чи ввімкнено можливість бота у налаштуваннях твого застосунку та чи вибрано Stream Mode. Переконайся, що твій User ID присутній у `DINGTALK_ALLOWED_USERS`. Перезапусти шлюз.

### Помилка «dingtalk-stream not installed»

**Причина**: Пакет Python `dingtalk-stream` не встановлений.

**Виправлення**: Встанови його:

```bash
pip install dingtalk-stream httpx
```

### «DINGTALK_CLIENT_ID and DINGTALK_CLIENT_SECRET required»

**Причина**: Облікові дані не задані у твоєму середовищі або у файлі `.env`.

**Виправлення**: Переконайся, що `DINGTALK_CLIENT_ID` і `DINGTALK_CLIENT_SECRET` правильно встановлені у `~/.hermes/.env`. Client ID — це твій AppKey, а Client Secret — твій AppSecret з консолі розробника DingTalk.

### Розриви потоку / цикли перепідключення

**Причина**: Нестабільність мережі, технічне обслуговування платформи DingTalk або проблеми з обліковими даними.

**Виправлення**: Адаптер автоматично перепідключається з експоненціальним збільшенням інтервалу (2 s → 5 s → 10 s → 30 s → 60 s). Перевір, чи твої облікові дані дійсні і чи твій застосунок не був деактивований. Переконайся, що мережа дозволяє вихідні WebSocket‑з’єднання.

### Бот офлайн

**Причина**: Шлюз Hermes не запущений, або не вдалося підключитися.

**Виправлення**: Перевір, чи працює `hermes gateway`. Подивися вивід терміналу на предмет повідомлень про помилки. Типові проблеми: неправильні облікові дані, деактивований застосунок, `dingtalk-stream` або `httpx` не встановлені.

### «No session_webhook available»

**Причина**: Бот спробував відповісти, але не має URL‑адреси webhook‑сесії. Це зазвичай трапляється, коли webhook закінчився або бот був перезапущений між отриманням повідомлення та надсиланням відповіді.

**Виправлення**: Надішли нове повідомлення боту — кожне вхідне повідомлення створює новий webhook‑сесію для відповідей. Це нормальне обмеження DingTalk; бот може відповідати лише на повідомлення, отримані нещодавно.
## Безпека

:::warning
Завжди встановлюй `DINGTALK_ALLOWED_USERS`, щоб обмежити, хто може взаємодіяти з ботом. Без цього gateway за замовчуванням відхиляє всіх користувачів як запобіжний захід. Додавай лише ID користувачів людей, яким ти довіряєш — авторизовані користувачі мають повний доступ до можливостей агента, включно з використанням інструментів та доступом до системи.
:::

Для отримання додаткової інформації про захист розгортання Hermes Agent, переглянь [Посібник з безпеки](../security.md).
## Примітки

- **Stream Mode**: Не потрібен публічний URL, доменне ім’я чи сервер веб‑хук. З’єднання ініціюється з твого комп’ютера через WebSocket, тому працює за NAT та між брандмауерами.
- **AI Cards**: За бажанням можна відповідати за допомогою багатих AI Cards замість простого markdown. Налаштовується через `card_template_id`.
- **Emoji Reactions**: Автоматичні 🤔Thinking/🥳Done реакції для статусу обробки.
- **Markdown responses**: Відповіді форматуються у markdown‑форматі DingTalk для відображення багатого тексту.
- **Media support**: Зображення та файли у вхідних повідомленнях автоматично розпізнаються і можуть оброблятися інструментами зору.
- **Message deduplication**: Адаптер видаляє дублікати повідомлень протягом 5 хвилин, щоб запобігти повторній обробці того самого повідомлення.
- **Auto-reconnection**: Якщо стрім‑з’єднання розривається, адаптер автоматично підключається з експоненціальним збільшенням затримки.
- **Message length limit**: Відповіді обмежені 20 000 символами на повідомлення. Довші відповіді обрізаються.