---
sidebar_position: 4
title: "Учебник: Помощник команды Telegram"
description: "Пошаговое руководство по настройке Telegram‑бота, которым вся команда сможет пользоваться для помощи с кодом, исследованиями, администрированием системы и прочим."
---

# Настройка командного Telegram‑ассистента

Этот учебник проведёт тебя через процесс настройки Telegram‑бота на базе Hermes Agent, которым смогут пользоваться несколько участников команды. В итоге у вашей команды будет общий AI‑ассистент, которому можно писать сообщения для получения помощи с кодом, исследованиями, администрированием систем и прочим — защищённый пользовательской авторизацией.
## Что мы строим

Telegram‑бот, который:

- **Любой уполномоченный член команды** может написать в личные сообщения за помощью — ревью кода, исследования, команды оболочки, отладка
- **Работает на твоём сервере** с полным доступом к инструментам — терминал, редактирование файлов, веб‑поиск, выполнение кода
- **Персональные сессии** — у каждого пользователя свой контекст разговора
- **Безопасен по умолчанию** — только одобренные пользователи могут взаимодействовать, используя два метода авторизации
- **Запланированные задачи** — ежедневные стендапы, проверки состояния и напоминания, отправляемые в канал команды

---
## Предварительные требования

Прежде чем начать, убедись, что у тебя есть:

- **Hermes Agent установлен** на сервере или VPS (не на ноутбуке — боту нужно постоянно работать). Следуй [руководству по установке](/getting-started/installation), если ещё не сделал этого.
- **Учётная запись Telegram** для себя (владелец бота)
- **Настроенный провайдер LLM** — минимум, API‑ключ для OpenAI, Anthropic или другого поддерживаемого провайдера в `~/.hermes/.env`

:::tip
VPS за $5/мес более чем достаточно для работы шлюза. Сам Hermes лёгкий — платишь только за вызовы API LLM, которые происходят удалённо.
:::

---
## Шаг 1: Создай Telegram‑бота

Каждый Telegram‑бот начинается с **@BotFather** — официального бота Telegram для создания ботов.

1. **Открой Telegram** и найди `@BotFather`, либо перейди по ссылке [t.me/BotFather](https://t.me/BotFather)

2. **Отправь `/newbot`** — BotFather спросит у тебя два параметра:
   - **Display name** — что видят пользователи (например, `Team Hermes Assistant`)
   - **Username** — должно заканчиваться на `bot` (например, `myteam_hermes_bot`)

3. **Скопируй токен бота** — BotFather ответит примерно так:
   ```
   Use this token to access the HTTP API:
   7123456789:AAH1bGciOiJSUzI1NiIsInR5cCI6Ikp...
   ```
   Сохрани этот токен — он понадобится в следующем шаге.

4. **Установи описание** (необязательно, но рекомендуется):
   ```
   /setdescription
   ```
   Выбери своего бота, затем введи что‑то вроде:
   ```
   Team AI assistant powered by Hermes Agent. DM me for help with code, research, debugging, and more.
   ```

5. **Установи команды бота** (необязательно — добавит меню команд для пользователей):
   ```
   /setcommands
   ```
   Выбери своего бота, затем вставь:
   ```
   new - Start a fresh conversation
   model - Show or change the AI model
   status - Show session info
   help - Show available commands
   stop - Stop the current task
   ```

:::warning
Храни токен бота в секрете. Любой, у кого есть токен, может управлять ботом. Если токен утечёт, используй `/revoke` в BotFather, чтобы сгенерировать новый.
:::

---
## Шаг 2: Настройка шлюза

У тебя есть два варианта: интерактивный мастер настройки (рекомендовано) или ручная конфигурация.

### Вариант A: Интерактивный мастер (рекомендовано)

```bash
hermes gateway setup
```

Он проведёт тебя через всё с помощью выбора стрелками. Выбери **Telegram**, вставь токен своего бота и введи свой ID пользователя, когда будет запрошено.

### Вариант B: Ручная конфигурация

Добавь эти строки в `~/.hermes/.env`:

```bash
# Telegram bot token from BotFather
TELEGRAM_BOT_TOKEN=7123456789:AAH1bGciOiJSUzI1NiIsInR5cCI6Ikp...

# Your Telegram user ID (numeric)
TELEGRAM_ALLOWED_USERS=123456789
```

### Как найти свой ID пользователя

Твой ID пользователя Telegram — это числовое значение (не твой ник). Чтобы найти его:

1. Напиши сообщение [@userinfobot](https://t.me/userinfobot) в Telegram
2. Он сразу ответит твоим числовым ID
3. Скопируй это число в `TELEGRAM_ALLOWED_USERS`

:::info
ID пользователей Telegram — это постоянные числа, например `123456789`. Они отличаются от твоего `@username`, который может измениться. Всегда используй числовой ID для списков разрешений.
:::

---
## Шаг 3: Запусти шлюз

### Быстрая проверка

Запусти шлюз в **foreground**, чтобы убедиться, что всё работает:

```bash
hermes gateway
```

Ты должен увидеть вывод, похожий на:

```
[Gateway] Starting Hermes Gateway...
[Gateway] Telegram adapter connected
[Gateway] Cron scheduler started (tick every 60s)
```

Открой Telegram, найди своего бота и отправь ему сообщение. Если он ответит — всё в порядке. Нажми `Ctrl+C`, чтобы остановить.

### Production: Установка как службы

Для постоянного развертывания, которое переживает перезагрузки:

```bash
hermes gateway install
sudo hermes gateway install --system   # Linux only: boot-time system service
```

Это создаёт фоновую службу: сервис уровня пользователя **systemd** на Linux по умолчанию, сервис **launchd** на macOS, либо системный сервис Linux при передаче `--system`.

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
Plist‑файл launchd фиксирует значение переменной **PATH** из твоего шелла во время установки, чтобы подпроцессы шлюза могли находить такие инструменты, как Node.js и ffmpeg. Если позже установишь новые инструменты, запусти `hermes gateway install` ещё раз, чтобы обновить plist.
:::

### Verify It’s Running

```bash
hermes gateway status
```

Затем отправь тестовое сообщение своему боту в Telegram. Ты должен получить ответ в течение нескольких секунд.

---
## Шаг 4: Настройка доступа команды

Теперь предоставим доступ твоим коллегам. Существует два подхода.

### Подход A: Статический allowlist

Собери Telegram‑идентификаторы пользователей каждого члена команды (попроси их написать боту [@userinfobot](https://t.me/userinfobot)) и добавь их в виде списка, разделённого запятыми:

```bash
# In ~/.hermes/.env
TELEGRAM_ALLOWED_USERS=123456789,987654321,555555555
```

Перезапусти шлюз после изменений:

```bash
hermes gateway stop && hermes gateway start
```

### Подход B: DM‑pairing (рекомендовано для команд)

DM‑pairing более гибок — не нужно заранее собирать идентификаторы пользователей. Как это работает:

1. **Коллега пишет боту в DM** — поскольку его нет в allowlist, бот отвечает одноразовым кодом сопряжения:
      ```
   🔐 Pairing code: XKGH5N7P
   Send this code to the bot owner for approval.
   ```

2. **Коллега отправляет тебе код** (через любой канал — Slack, email, лично)

3. **Ты одобряешь его** на сервере:
      ```bash
   hermes pairing approve telegram XKGH5N7P
   ```

4. **Он получает доступ** — бот сразу начинает отвечать на его сообщения

**Управление сопряжёнными пользователями:**

```bash
# See all pending and approved users
hermes pairing list

# Revoke someone's access
hermes pairing revoke telegram 987654321

# Clear expired pending codes
hermes pairing clear-pending
```

:::tip
DM‑pairing идеален для команд, потому что не требуется перезапуск шлюза при добавлении новых пользователей. Одобрения вступают в силу мгновенно.
:::

### Соображения безопасности

- **Никогда не устанавливай `GATEWAY_ALLOW_ALL_USERS=true`** для бота с терминальным доступом — любой, кто найдёт твоего бота, сможет выполнять команды на твоём сервере
- Коды сопряжения истекают через **1 час** и используют криптографически случайные значения
- Ограничение скорости предотвращает атаки перебором: 1 запрос на пользователя каждые 10 минут, максимум 3 ожидающих кода на платформу
- После 5 неудачных попыток одобрения платформа переходит в блокировку на 1 час
- Все данные сопряжения хранятся с правами `chmod 0600`
## Шаг 5: Настройка бота

### Установить домашний канал

**Домашний канал** — это место, куда бот отправляет результаты cron‑задач и проактивные сообщения. Без него запланированные задачи не имеют куда отправлять вывод.

**Вариант 1:** Используй команду `/sethome` в любой группе Telegram или чате, где бот является участником.

**Вариант 2:** Укажи его вручную в `~/.hermes/.env`:

```bash
TELEGRAM_HOME_CHANNEL=-1001234567890
TELEGRAM_HOME_CHANNEL_NAME="Team Updates"
```

Чтобы узнать ID канала, добавь [@userinfobot](https://t.me/userinfobot) в группу — бот сообщит ID чата группы.

### Настройка отображения прогресса инструментов

Контролируй, сколько деталей бот показывает при использовании инструментов. В `~/.hermes/config.yaml`:

```yaml
display:
  tool_progress: new    # off | new | all | verbose
```

| Режим   | Что ты видишь                                                                      |
|--------|------------------------------------------------------------------------------------|
| `off`      | Только чистые ответы — без активности инструментов                                 |
| `new`      | Краткий статус для каждого нового вызова инструмента (рекомендовано для обмена сообщениями) |
| `all`      | Каждый вызов инструмента с деталями                                               |
| `verbose` | Полный вывод инструмента, включая результаты команд                               |

Пользователи также могут менять это для отдельной сессии командой `/verbose` в чате.

### Настрой личность с помощью SOUL.md

Настрой, как бот общается, отредактировав `~/.hermes/SOUL.md`:

Для полного руководства смотри [Использовать SOUL.md с Hermes](/guides/use-soul-with-hermes).

```markdown
# Soul
You are a helpful team assistant. Be concise and technical.
Use code blocks for any code. Skip pleasantries — the team
values directness. When debugging, always ask for error logs
before guessing at solutions.
```

### Добавить контекст проекта

Если твоя команда работает над конкретными проектами, создай файлы контекста, чтобы бот знал ваш стек:

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
Файлы контекста внедряются в системный запрос каждой сессии. Делай их лаконичными — каждый символ учитывается в твоём токен‑бюджете.
:::

---
## Шаг 6: Настройка запланированных задач

При запущенном **gateway** ты можешь планировать повторяющиеся задачи, которые доставляют результаты в канал твоей команды.

### Ежедневное резюме стендапа

Отправь сообщение боту в Telegram:

```
Every weekday at 9am, check the GitHub repository at
github.com/myorg/myproject for:
1. Pull requests opened/merged in the last 24 hours
2. Issues created or closed
3. Any CI/CD failures on the main branch
Format as a brief standup-style summary.
```

Агент автоматически создаёт **cron‑задачу** и доставляет результаты в чат, где был сделан запрос (или в основной канал).

### Проверка состояния сервера

```
Every 6 hours, check disk usage with 'df -h', memory with 'free -h',
and Docker container status with 'docker ps'. Report anything unusual —
partitions above 80%, containers that have restarted, or high memory usage.
```

### Управление запланированными задачами

```bash
# From the CLI
hermes cron list          # View all scheduled jobs
hermes cron status        # Check if scheduler is running

# From Telegram chat
/cron list                # View jobs
/cron remove <job_id>     # Remove a job
```

:::warning
Запросы **cron‑задач** выполняются в полностью новых сессиях без памяти о предыдущих разговорах. Убедись, что каждый запрос содержит **весь** необходимый контекст — пути к файлам, URL, адреса серверов и чёткие инструкции.
:::
## Советы по эксплуатации

### Используй Docker для безопасности

На совместном командном боте используй Docker в качестве бэкенда терминала, чтобы команды агента выполнялись в контейнере, а не на твоём хосте:

```bash
# In ~/.hermes/.env
TERMINAL_BACKEND=docker
TERMINAL_DOCKER_IMAGE=nikolaik/python-nodejs:python3.11-nodejs20
```

Или в `~/.hermes/config.yaml`:

```yaml
terminal:
  backend: docker
  container_cpu: 1
  container_memory: 5120
  container_persistent: true
```

Таким образом, даже если кто‑то попросит бота выполнить что‑то разрушительное, твоя хост‑система будет защищена.

### Мониторинг шлюза

```bash
# Check if the gateway is running
hermes gateway status

# Watch live logs (Linux)
journalctl --user -u hermes-gateway -f

# Watch live logs (macOS)
tail -f ~/.hermes/logs/gateway.log
```

### Обновляй Hermes

Из Telegram отправь боту команду `/update` — он скачает последнюю версию и перезапустится. Или с сервера:

```bash
hermes update
hermes gateway stop && hermes gateway start
```

### Расположение журналов

| Что | Расположение |
|------|----------|
| Журналы шлюза | `journalctl --user -u hermes-gateway` (Linux) или `~/.hermes/logs/gateway.log` (macOS) |
| Вывод cron‑задач | `~/.hermes/cron/output/{job_id}/{timestamp}.md` |
| Определения cron‑задач | `~/.hermes/cron/jobs.json` |
| Данные сопряжения | `~/.hermes/pairing/` |
| История сессий | `~/.hermes/sessions/` |
## Дальнейшие шаги

У тебя уже работает помощник Telegram для команды. Вот несколько следующих шагов:

- **[Руководство по безопасности](/user-guide/security)** — глубокое погружение в авторизацию, изоляцию контейнеров и одобрение команд
- **[Шлюз сообщений](/user-guide/messaging)** — полная справка по архитектуре шлюза, управлению сессиями и чат‑командам
- **[Настройка Telegram](/user-guide/messaging/telegram)** — детали, специфичные для платформы, включая голосовые сообщения и TTS
- **[Запланированные задачи](/user-guide/features/cron)** — продвинутое планирование cron с опциями доставки и cron‑выражениями
- **[Контекстные файлы](/user-guide/features/context-files)** — AGENTS.md, SOUL.md и .cursorrules для знаний проекта
- **[Персонализация](/user-guide/features/personality)** — встроенные пресеты персональности и пользовательские определения персонажа
- **Добавить больше платформ** — тот же шлюз может одновременно работать с [Discord](/user-guide/messaging/discord), [Slack](/user-guide/messaging/slack) и [WhatsApp](/user-guide/messaging/whatsapp)

---

*Вопросы или проблемы? Открой issue на GitHub — вклад приветствуется.*