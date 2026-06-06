---
sidebar_position: 4
title: "Посібник: Team Telegram Assistant"
description: "Покроковий посібник зі створення Telegram‑бота, яким може користуватися вся твоя команда для допомоги з кодом, досліджень, адміністрування систем та іншого."
---

# Налаштування командного Telegram‑асистента

Цей посібник крок за кроком проведе тебе через процес налаштування Telegram‑бота, який працює на базі Hermes Agent і яким можуть користуватися кілька учасників команди. Після завершення у вашій команді буде спільний AI‑асистент, якому можна надсилати повідомлення для отримання допомоги з кодом, дослідженнями, адмініструванням системи та будь‑якими іншими питаннями — захищений індивідуальною авторизацією для кожного користувача.
## Що ми будуємо

Telegram‑бот, який:

- **Будь‑який уповноважений учасник команди** може написати в DM для отримання допомоги — рев’ю коду, дослідження, команди оболонки, налагодження
- **Працює на твоєму сервері** з повним доступом до інструментів — термінал, редагування файлів, веб‑пошук, виконання коду
- **Сесії для кожного користувача** — кожна особа отримує власний контекст розмови
- **Безпечний за замовчуванням** — лише схвалені користувачі можуть взаємодіяти, з двома методами авторизації
- **Заплановані завдання** — щоденні стендапи, перевірки стану та нагадування, що надсилаються в канал команди

---
## Передумови

Перш ніж почати, переконайся, що у тебе є:

- **Hermes Agent встановлений** на сервері або VPS (не на ноутбуці — бот має працювати постійно). Дотримуйся [посібника з встановлення](/getting-started/installation), якщо ще не зробив цього.
- **Обліковий запис Telegram** для себе (власник бота)
- **Налаштований провайдер LLM** — принаймні API‑ключ для OpenAI, Anthropic або іншого підтримуваного провайдера у `~/.hermes/.env`

:::tip
VPS за $5/місяць цілком достатньо для запуску шлюзу. Сам Hermes легкий — витрати йдуть на виклики API LLM, які виконуються віддалено.
:::

---
## Крок 1: Створи Telegram‑бота

Кожен Telegram‑бот починається з **@BotFather** — офіційного бота Telegram для створення ботів.

1. **Відкрий Telegram** і знайди `@BotFather`, або перейди за посиланням [t.me/BotFather](https://t.me/BotFather)

2. **Надішли `/newbot`** — BotFather запитає у тебе два параметри:
   - **Display name** — ім’я, що бачать користувачі (наприклад, `Team Hermes Assistant`)
   - **Username** — має закінчуватись на `bot` (наприклад, `myteam_hermes_bot`)

3. **Скопіюй токен бота** — BotFather відповість чимось на кшталт:
   ```
   Use this token to access the HTTP API:
   7123456789:AAH1bGciOiJSUzI1NiIsInR5cCI6Ikp...
   ```
   Збережи цей токен — він знадобиться в наступному кроці.

4. **Встанови опис** (необов’язково, але рекомендовано):
   ```
   /setdescription
   ```
   Вибери свого бота, потім введи щось на кшталт:
   ```
   Team AI assistant powered by Hermes Agent. DM me for help with code, research, debugging, and more.
   ```

5. **Встанови команди бота** (необов’язково — додає меню команд для користувачів):
   ```
   /setcommands
   ```
   Вибери свого бота, потім встав:
   ```
   new - Start a fresh conversation
   model - Show or change the AI model
   status - Show session info
   help - Show available commands
   stop - Stop the current task
   ```

:::warning
Тримай токен бота в таємниці. Будь‑хто, хто має токен, може керувати ботом. Якщо він витече, використай `/revoke` у BotFather, щоб згенерувати новий.
:::

---
## Крок 2: Налаштуй шлюз

У тебе є два варіанти: інтерактивний майстер налаштування (рекомендовано) або ручна конфігурація.

### Варіант A: Інтерактивний майстер (рекомендовано)

```bash
hermes gateway setup
```

Це проведе тебе через усе за допомогою вибору клавішами‑стрілками. Вибери **Telegram**, встав свій токен бота та введи свій ідентифікатор користувача, коли буде запитано.

### Варіант B: Ручна конфігурація

Додай ці рядки до `~/.hermes/.env`:

```bash
# Telegram bot token from BotFather
TELEGRAM_BOT_TOKEN=7123456789:AAH1bGciOiJSUzI1NiIsInR5cCI6Ikp...

# Your Telegram user ID (numeric)
TELEGRAM_ALLOWED_USERS=123456789
```

### Пошук твого ідентифікатора користувача

Твій ідентифікатор користувача Telegram — це числове значення (не твоє ім’я користувача). Щоб його знайти:

1. Напиши повідомлення [@userinfobot](https://t.me/userinfobot) у Telegram
2. Він миттєво відповість твоїм числовим ідентифікатором користувача
3. Скопіюй це число у `TELEGRAM_ALLOWED_USERS`

:::info
Ідентифікатори користувачів Telegram — це постійні числа, наприклад `123456789`. Вони відрізняються від твого `@username`, який може змінюватись. Завжди використовуй числовий ідентифікатор у списку дозволу.
:::

---
## Крок 3: Запуск шлюзу

### Швидкий тест

Запусти шлюз на передньому плані, щоб переконатися, що все працює:

```bash
hermes gateway
```

Ти маєш побачити вивід, схожий на:

```
[Gateway] Starting Hermes Gateway...
[Gateway] Telegram adapter connected
[Gateway] Cron scheduler started (tick every 60s)
```

Відкрий Telegram, знайди свого бота і надішли йому повідомлення. Якщо він відповідає, все готово. Натисни `Ctrl+C`, щоб зупинити.

### Продакшн: Встановити як сервіс

Для постійного розгортання, яке переживатиме перезавантаження:

```bash
hermes gateway install
sudo hermes gateway install --system   # Linux only: boot-time system service
```

Це створює фоновий сервіс: сервіс **systemd** рівня користувача у Linux за замовчуванням, сервіс **launchd** у macOS або системний сервіс Linux під час завантаження, якщо передати `--system`.

```bash
# Linux — manage the default user service
hermes gateway start
hermes gateway stop
hermes gateway status

# View live logs
journalctl --user -u hermes-gateway -f

# Keep running after SSH logout
sudo loginctl enable-linger $USER

# Linux servers — explicit system-service commands
sudo hermes gateway start --system
sudo hermes gateway status --system
journalctl -u hermes-gateway -f
```

```bash
# macOS — manage the service
hermes gateway start
hermes gateway stop
tail -f ~/.hermes/logs/gateway.log
```

:::tip macOS PATH
Файл launchd plist захоплює PATH твоєї оболонки під час встановлення, щоб підпроцеси шлюзу могли знаходити інструменти, такі як Node.js та ffmpeg. Якщо ти встановиш нові інструменти пізніше, повторно запусти `hermes gateway install`, щоб оновити plist.
:::

### Перевірка роботи

```bash
hermes gateway status
```

Потім надішли тестове повідомлення своєму боту у Telegram. Ти маєш отримати відповідь протягом кількох секунд.

---
## Крок 4: Налаштування доступу команди

Тепер надаємо доступ твоїм колегам. Є два підходи.

### Підхід A: Статичний білий список

Збери Telegram‑ідентифікатори користувачів кожного члена команди (нехай вони надішлють повідомлення [@userinfobot](https://t.me/userinfobot)) і додай їх у список, розділений комами:

```bash
# In ~/.hermes/.env
TELEGRAM_ALLOWED_USERS=123456789,987654321,555555555
```

Перезапусти шлюз після змін:

```bash
hermes gateway stop && hermes gateway start
```

### Підхід B: DM‑парування (рекомендовано для команд)

DM‑парування більш гнучке — не потрібно збирати ідентифікатори користувачів заздалегідь. Ось як це працює:

1. **Колега надсилає боту DM** — оскільки його немає у білому списку, бот відповідає одноразовим кодом парування:
   ```
   🔐 Pairing code: XKGH5N7P
   Send this code to the bot owner for approval.
   ```

2. **Колега надсилає тобі код** (будь‑яким каналом — Slack, електронна пошта, особисто)

3. **Ти підтверджуєш його** на сервері:
   ```bash
   hermes pairing approve telegram XKGH5N7P
   ```

4. **Він у системі** — бот одразу починає відповідати на його повідомлення

**Керування парованими користувачами:**

```bash
# See all pending and approved users
hermes pairing list

# Revoke someone's access
hermes pairing revoke telegram 987654321

# Clear expired pending codes
hermes pairing clear-pending
```

:::tip
DM‑парування ідеальне для команд, оскільки не потрібно перезапускати шлюз при додаванні нових користувачів. Підтвердження набирає чинності миттєво.
:::

### Зауваження щодо безпеки

- **Ніколи не встановлюй `GATEWAY_ALLOW_ALL_USERS=true`** у бота з доступом до терміналу — будь‑хто, хто знайде твого бота, зможе виконувати команди на твоєму сервері
- Коди парування діють **1 годину** і генеруються криптографічно випадковим чином
- Обмеження швидкості запобігає атакам перебору: 1 запит на користувача кожні 10 хвилин, максимум 3 очікуючі коди на платформу
- Після 5 невдалих спроб підтвердження платформа переходить у блокування на 1 годину
- Усі дані парування зберігаються з правами `chmod 0600`
## Крок 5: Налаштування бота

### Встановити домашній канал

**Домашній канал** — це місце, куди бот надсилає результати cron‑завдань та проактивні повідомлення. Без нього заплановані завдання не матимуть куди відправляти вивід.

**Опція 1:** Використай команду `/sethome` у будь‑якій групі або чаті Telegram, де бот є учасником.

**Опція 2:** Встанови його вручну у `~/.hermes/.env`:

```bash
TELEGRAM_HOME_CHANNEL=-1001234567890
TELEGRAM_HOME_CHANNEL_NAME="Team Updates"
```

Щоб знайти ідентифікатор каналу, додай [@userinfobot](https://t.me/userinfobot) до групи — він повідомить ID чату групи.

### Налаштування відображення прогресу інструментів

Керуй тим, скільки деталей бот показує під час використання інструментів. У `~/.hermes/config.yaml`:

```yaml
display:
  tool_progress: new    # off | new | all | verbose
```

| Режим   | Що ти бачиш |
|---------|--------------|
| `off`   | Тільки чисті відповіді — без активності інструментів |
| `new`   | Короткий статус кожного нового виклику інструмента (рекомендовано для обміну повідомленнями) |
| `all`   | Кожен виклик інструмента з деталями |
| `verbose` | Повний вивід інструмента, включаючи результати команд |

Користувачі також можуть змінити це під час сесії за допомогою команди `/verbose` у чаті.

### Налаштування персональності за допомогою SOUL.md

Налаштуй, як бот спілкується, редагуючи `~/.hermes/SOUL.md`:

Для повного посібника дивись [Use SOUL.md with Hermes](/guides/use-soul-with-hermes).

```markdown
# Soul
You are a helpful team assistant. Be concise and technical.
Use code blocks for any code. Skip pleasantries — the team
values directness. When debugging, always ask for error logs
before guessing at solutions.
```

### Додати контекст проєкту

Якщо ваша команда працює над конкретними проєктами, створіть файли контексту, щоб бот знав ваш стек:

```markdown
<!-- ~/.hermes/AGENTS.md -->
# Team Context
- We use Python 3.12 with FastAPI and SQLAlchemy
- Frontend is React with TypeScript
- CI/CD runs on GitHub Actions
- Production deploys to AWS ECS
- Always suggest writing tests for new code
```

:::info
Файли контексту вставляються у системний підказник кожної сесії. Тримайте їх стислими — кожен символ враховується у ваш бюджет токенів.
:::

---
## Крок 6: Налаштування запланованих завдань

Коли шлюз працює, ти можеш планувати повторювані завдання, які доставляють результати у канал твоєї команди.

### Щоденний підсумок стендапу

Надішли повідомлення боту в Telegram:

```
Every weekday at 9am, check the GitHub repository at
github.com/myorg/myproject for:
1. Pull requests opened/merged in the last 24 hours
2. Issues created or closed
3. Any CI/CD failures on the main branch
Format as a brief standup-style summary.
```

Агент автоматично створює cron‑завдання і доставляє результати в чат, де ти запитав (або в домашньому каналі).

### Перевірка стану сервера

```
Every 6 hours, check disk usage with 'df -h', memory with 'free -h',
and Docker container status with 'docker ps'. Report anything unusual —
partitions above 80%, containers that have restarted, or high memory usage.
```

### Керування запланованими завданнями

```bash
# From the CLI
hermes cron list          # View all scheduled jobs
hermes cron status        # Check if scheduler is running

# From Telegram chat
/cron list                # View jobs
/cron remove <job_id>     # Remove a job
```

:::warning
Запити cron‑завдань виконуються в абсолютно нових сесіях без пам’яті про попередні розмови. Переконайся, що кожен запит містить **весь** контекст, необхідний агенту — шляхи до файлів, URL‑адреси, адреси серверів та чіткі інструкції.
:::

---
## Поради щодо продакшн

### Використовуй Docker для безпеки

На спільному боті команди використай Docker як бекенд терміналу, щоб команди агента виконувалися в контейнері, а не на твоїй хост‑системі:

```bash
# In ~/.hermes/.env
TERMINAL_BACKEND=docker
TERMINAL_DOCKER_IMAGE=nikolaik/python-nodejs:python3.11-nodejs20
```

Або в `~/.hermes/config.yaml`:

```yaml
terminal:
  backend: docker
  container_cpu: 1
  container_memory: 5120
  container_persistent: true
```

Таким чином, навіть якщо хтось попросить бота виконати щось руйнівне, твоя система буде захищена.

### Моніторинг шлюзу

```bash
# Check if the gateway is running
hermes gateway status

# Watch live logs (Linux)
journalctl --user -u hermes-gateway -f

# Watch live logs (macOS)
tail -f ~/.hermes/logs/gateway.log
```

### Тримай Hermes оновленим

У Telegram надішли `/update` боту — він завантажить останню версію та перезапуститься. Або з сервера:

```bash
hermes update
hermes gateway stop && hermes gateway start
```

### Розташування журналів

| Що | Розташування |
|------|----------|
| Gateway logs | `journalctl --user -u hermes-gateway` (Linux) або `~/.hermes/logs/gateway.log` (macOS) |
| Cron job output | `~/.hermes/cron/output/{job_id}/{timestamp}.md` |
| Cron job definitions | `~/.hermes/cron/jobs.json` |
| Pairing data | `~/.hermes/pairing/` |
| Session history | `~/.hermes/sessions/` |

---
## Що далі

У тебе вже працює Telegram‑асистент для команди. Ось кілька наступних кроків:

- **[Посібник з безпеки](/user-guide/security)** — глибоке занурення в авторизацію, ізоляцію контейнерів та схвалення команд
- **[Шлюз обміну повідомленнями](/user-guide/messaging)** — повна довідка щодо архітектури шлюзу, управління сесіями та чат‑команд
- **[Налаштування Telegram](/user-guide/messaging/telegram)** — специфічні для платформи деталі, включаючи голосові повідомлення та TTS
- **[Заплановані завдання](/user-guide/features/cron)** — розширене планування cron з параметрами доставки та виразами cron
- **[Файли контексту](/user-guide/features/context-files)** — AGENTS.md, SOUL.md та .cursorrules для знань про проєкт
- **[Персональність](/user-guide/features/personality)** — вбудовані пресети персональності та визначення кастомних персонажів
- **Додати інші платформи** — той самий шлюз може одночасно працювати з [Discord](/user-guide/messaging/discord), [Slack](/user-guide/messaging/slack) та [WhatsApp](/user-guide/messaging/whatsapp)

---

*Питання чи проблеми? Відкрий issue на GitHub — внески вітаються.*