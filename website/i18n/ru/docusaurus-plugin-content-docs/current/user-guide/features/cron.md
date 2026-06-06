---
sidebar_position: 5
title: "Запланированные задачи (Cron)"
description: "Планируй автоматические задачи с помощью естественного языка, управляй ими одним инструментом cron и привязывай один или несколько skills"
---

# Запланированные задачи (Cron)

Запланируй задачи для автоматического выполнения с помощью естественного языка или cron‑выражений. Hermes предоставляет управление cron через единый инструмент `cronjob` с операциями в стиле action, вместо отдельных инструментов schedule/list/remove.
## Что теперь умеет cron

Cron‑задачи могут:

- планировать одноразовые или повторяющиеся задачи
- приостанавливать, возобновлять, редактировать, запускать и удалять задачи
- привязывать ноль, одну или несколько **skill** к задаче
- возвращать результаты в исходный чат, локальные файлы или настроенные целевые платформы
- запускаться в новых сессиях агента со стандартным статическим списком инструментов
- запускаться в **режиме без агента** — скрипт по расписанию, его `stdout` передаётся дословно, без участия LLM (см. раздел [no-agent mode](#no-agent-mode-script-only-jobs) ниже)

Всё это доступно самому Hermes через инструмент `cronjob`, так что ты можешь создавать, приостанавливать, редактировать и удалять задачи, просто задавая вопросы на естественном языке — без необходимости использовать CLI.

:::tip
Cron‑задачи используют тот провайдер, который выбран командой `hermes model`. `hermes setup --portal` — вариант с наименьшим трением для автоматических запусков, так как обновление OAuth происходит автоматически. См. [Nous Portal](/integrations/nous-portal).
:::

:::warning
Сессии, запущенные через cron, не могут рекурсивно создавать новые cron‑задачи. Hermes отключает инструменты управления cron внутри cron‑исполнений, чтобы предотвратить бесконтрольные циклы планирования.
:::
## Создание запланированных задач

### В чате с `/cron`

```bash
/cron add 30m "Remind me to check the build"
/cron add "every 2h" "Check server status"
/cron add "every 1h" "Summarize new feed items" --skill blogwatcher
/cron add "every 1h" "Use both skills and combine the result" --skill blogwatcher --skill maps
```

### Из отдельного CLI

```bash
hermes cron create "every 2h" "Check server status"
hermes cron create "every 1h" "Summarize new feed items" --skill blogwatcher
hermes cron create "every 1h" "Use both skills and combine the result" \
  --skill blogwatcher \
  --skill maps \
  --name "Skill combo"
```

### Через естественный разговор

Спроси Hermes как обычно:

```text
Every morning at 9am, check Hacker News for AI news and send me a summary on Telegram.
```

Hermes будет использовать внутренний унифицированный инструмент `cronjob`.
## Cron‑задачи с поддержкой навыков

Cron‑задача может загрузить один или несколько навыков перед выполнением **prompt**.

### Один навык

```python
cronjob(
    action="create",
    skill="blogwatcher",
    prompt="Check the configured feeds and summarize anything new.",
    schedule="0 9 * * *",
    name="Morning feeds",
)
```

### Несколько навыков

Навыки загружаются последовательно. **Prompt** становится инструкцией задачи, наложенной поверх этих навыков.

```python
cronjob(
    action="create",
    skills=["blogwatcher", "maps"],
    prompt="Look for new local events and interesting nearby places, then combine them into one short brief.",
    schedule="every 6h",
    name="Local brief",
)
```

Это полезно, когда ты хочешь, чтобы запланированный агент унаследовал повторно используемые рабочие процессы, не встраивая полный текст навыка в сам **prompt** cron.
## Запуск задания внутри каталога проекта

Cron‑задачи по умолчанию запускаются независимо от любого репозитория — `AGENTS.md`, `CLAUDE.md` и `.cursorrules` не загружаются, а инструменты `terminal` / `file` / `code‑exec` работают из того рабочего каталога, в котором был запущен gateway. Чтобы изменить это, передай `--workdir` (CLI) или `workdir=` (вызов инструмента):

```bash
# Standalone CLI (schedule and prompt are positional)
hermes cron create "every 1d at 09:00" \
  "Audit open PRs, summarize CI health, and post to #eng" \
  --workdir /home/me/projects/acme
```

```python
# From a chat, via the cronjob tool
cronjob(
    action="create",
    schedule="every 1d at 09:00",
    workdir="/home/me/projects/acme",
    prompt="Audit open PRs, summarize CI health, and post to #eng",
)
```

Когда установлен `workdir`:

- `AGENTS.md`, `CLAUDE.md` и `.cursorrules` из этого каталога внедряются в system prompt (тот же порядок обнаружения, что и в интерактивном CLI);
- `terminal`, `read_file`, `write_file`, `patch`, `search_files` и `execute_code` используют этот каталог как свой рабочий каталог (через `TERMINAL_CWD`);
- Путь должен быть абсолютным каталогом, который существует — относительные пути и отсутствующие каталоги отклоняются во время создания/обновления;
- Передай `--workdir ""` (или `workdir=""` через инструмент) при редактировании, чтобы очистить его и вернуть прежнее поведение.

:::note Serialization
Задания с `workdir` выполняются последовательно на тик планировщика, а не в параллельном пуле. Это сделано намеренно — `TERMINAL_CWD` глобален для процесса, поэтому два задания с рабочим каталогом, запущенные одновременно, могли бы испортить cwd друг друга. Задания без рабочего каталога по‑прежнему выполняются параллельно.
:::
## Запуск cron‑задач в конкретном профиле

По умолчанию cron‑задача наследует профиль Hermes, которому принадлежит gateway / CLI, создавший её. Передай `--profile <name>` (CLI) или `profile=` (инструмент cronjob), чтобы перенаправить задачу на другой профиль — планировщик определит `HERMES_HOME` этого профиля, временно переключится в него на время выполнения, загрузит его `.env` + `config.yaml` и выполнит задачу там:

```bash
# Pin a job to the `night-ops` profile regardless of where it was scheduled
hermes cron create "every 1d at 03:00" \
  "Tail the security log and flag anomalies" \
  --profile night-ops
```

```python
# From a chat, via the cronjob tool
cronjob(
    action="create",
    schedule="every 1d at 03:00",
    prompt="Tail the security log and flag anomalies",
    profile="night-ops",
)
```

Используй `--profile default`, чтобы явно привязать задачу к корневому профилю Hermes. Указанный профиль должен уже существовать; планировщик отказывается создавать профили «на лету». Чтобы снять привязку к профилю во время `cron edit`, передай пустую строку (`--profile ""` или `profile=""`) — задача вернётся к выполнению в том профиле, в котором находится сам планировщик.

Если привязанный профиль позже будет удалён, планировщик запишет предупреждение и вернётся к выполнению задачи в текущем профиле, вместо того чтобы завершиться с ошибкой — так что устаревшая ссылка `profile` никогда не «зажимает» задачу.

:::note Serialization
Задачи с установленным `profile` также выполняются последовательно, по той же причине, что и задачи с привязанным `workdir`: переключение `HERMES_HOME` является глобальной мутацией процесса, поэтому две задачи, привязанные к профилям и запущенные параллельно, будут конкурировать друг с другом. Непривязанные задачи по‑прежнему выполняются в обычном параллельном пуле.
:::
## Редактирование задач

Тебе не нужно удалять и заново создавать задачи только для того, чтобы изменить их.

:::tip Ссылка на задачу
Заполнитель `<job_id>` ниже (и в [Lifecycle actions](#lifecycle-actions)) также принимает имя задачи (без учёта регистра) — удобно, когда ты помнишь `morning-digest`, но не знаешь шестнадцатеричный ID. Точный ID задачи имеет приоритет над совпадениями по имени; если ссылка не является ID и имя совпадает более чем с одной задачей, команда откажется и выведет возможные ID, чтобы ты мог уточнить выбор.
:::

### Чат

```bash
/cron edit <job_id> --schedule "every 4h"
/cron edit <job_id> --prompt "Use the revised task"
/cron edit <job_id> --skill blogwatcher --skill maps
/cron edit <job_id> --remove-skill blogwatcher
/cron edit <job_id> --clear-skills
```

### Standalone CLI

```bash
hermes cron edit <job_id> --schedule "every 4h"
hermes cron edit <job_id> --prompt "Use the revised task"
hermes cron edit <job_id> --skill blogwatcher --skill maps
hermes cron edit <job_id> --add-skill maps
hermes cron edit <job_id> --remove-skill blogwatcher
hermes cron edit <job_id> --clear-skills
```

Примечания:

- повторяющийся `--skill` заменяет список прикреплённых к задаче навыков
- `--add-skill` добавляет к существующему списку без его замены
- `--remove-skill` удаляет конкретные прикреплённые навыки
- `--clear-skills` удаляет все прикреплённые навыки
## Действия жизненного цикла

Cron‑задачи теперь имеют более полный жизненный цикл, а не только создание/удаление.

### Chat

```bash
/cron list
/cron pause <job_id>
/cron resume <job_id>
/cron run <job_id>
/cron remove <job_id>
```

### Standalone CLI

```bash
hermes cron list
hermes cron pause <job_id_or_name>
hermes cron resume <job_id_or_name>
hermes cron run <job_id_or_name>
hermes cron remove <job_id_or_name>
hermes cron edit <job_id_or_name> [...flags]
hermes cron status
hermes cron tick
```

Что они делают:

- `pause` — приостанавливает задачу, но сохраняет её
- `resume` — повторно включает задачу и вычисляет следующий запуск
- `run` — запускает задачу на следующем тике планировщика
- `remove` — полностью удаляет её
- `edit` — изменяет расписание, запрос, профиль, доставку и т.д.

**Поиск по имени.** Все изменяющие глаголы (`pause`, `resume`, `run`, `remove`, `edit`) и инструмент агента `cronjob` теперь принимают **имя** задачи (без учёта регистра) вместо шестнадцатеричного ID. Агент и CLI предпочитают точное совпадение по ID, если оно существует; неоднозначные совпадения имён (несколько задач с одинаковым именем) отклоняются с полным списком кандидатных ID, чтобы ты мог явно выбрать нужное. Имена не уникальны, поэтому эта проверка критична — она предотвращает тихое изменение неверной задачи, когда две задачи имеют одинаковое имя.
## Как это работает

**Выполнение Cron обрабатывается демоном шлюза.** Шлюз отсчитывает тик планировщика каждые 60 секунд, запуская все запланированные задачи в изолированных сессиях агента.

```bash
hermes gateway install     # Install as a user service
sudo hermes gateway install --system   # Linux: boot-time system service for servers
hermes gateway             # Or run in foreground

hermes cron list
hermes cron status
```

### Поведение планировщика шлюза

При каждом тике Hermes:

1. загружает задачи из `~/.hermes/cron/jobs.json`
2. проверяет `next_run_at` относительно текущего времени
3. запускает новую сессию `AIAgent` для каждой запланированной задачи
4. при необходимости внедряет один или несколько прикреплённых навыков в эту новую сессию
5. выполняет промпт до завершения
6. передаёт окончательный ответ
7. обновляет метаданные выполнения и время следующего запуска

Блокировка файла `~/.hermes/cron/.tick.lock` предотвращает наложение тиков планировщика и двойное выполнение одной и той же партии задач.
## Варианты доставки

При планировании задач ты указываешь, куда будет отправлен вывод:

| Option | Description | Example |
|--------|-------------|---------|
| `"origin"` | Обратно туда, где была создана задача | По умолчанию на платформах обмена сообщениями |
| `"local"` | Сохранить только в локальные файлы (`~/.hermes/cron/output/`) | По умолчанию в CLI |
| `"telegram"` | Главный канал Telegram | Использует `TELEGRAM_HOME_CHANNEL` |
| `"telegram:123456"` | Конкретный чат Telegram по ID | Прямая доставка |
| `"telegram:-100123:17585"` | Конкретная тема Telegram | Формат `chat_id:thread_id` |
| `"discord"` | Главный канал Discord | Использует `DISCORD_HOME_CHANNEL` |
| `"discord:#engineering"` | Конкретный канал Discord | По имени канала |
| `"slack"` | Главный канал Slack | |
| `"whatsapp"` | Главный канал WhatsApp | |
| `"signal"` | Signal | |
| `"matrix"` | Главная комната Matrix | |
| `"mattermost"` | Главный канал Mattermost | |
| `"email"` | Email | |
| `"sms"` | SMS через Twilio | |
| `"homeassistant"` | Home Assistant | |
| `"dingtalk"` | DingTalk | |
| `"feishu"` | Feishu/Lark | |
| `"wecom"` | WeCom | |
| `"weixin"` | Weixin (WeChat) | |
| `"bluebubbles"` | BlueBubbles (iMessage) | |
| `"qqbot"` | QQ Bot (Tencent QQ) | |
| `"all"` | Рассылает во все подключённые домашние каналы | Разрешается в момент срабатывания |
| `"telegram,discord"` | Рассылает в конкретный набор каналов | Список, разделённый запятыми |
| `"origin,all"` | Доставляет в исходный чат **плюс** каждый другой подключённый канал | Комбинация любых токенов |

Ответ агента автоматически доставляется. Вызывать `send_message` в запросе cron не требуется.

### Маршрутизация намерения (`all`)

`all` позволяет отправить одну задачу cron во все каналы обмена сообщениями, которые ты настроил, без необходимости перечислять их по именам. Она **разрешается в момент срабатывания**, поэтому задача, созданная до настройки Telegram, подхватит Telegram на следующем тике после установки `TELEGRAM_HOME_CHANNEL`.

Семантика: `all` разворачивается во все платформы с настроенным домашним каналом. Ноль — тоже допустимо; задача просто не имеет целей доставки и фиксируется как ошибка доставки выше по цепочке.

`all` комбинируется с явными целями. `origin,all` доставляет в исходный чат *плюс* каждый другой подключённый канал, удаляя дубликаты по `(platform, chat_id, thread_id)`.

### Тема cron в Telegram (`TELEGRAM_CRON_THREAD_ID`)

Когда включён режим тем в Telegram, корневой DM зарезервирован как системный лобби — ответы, отправленные туда, отклоняются с напоминанием о лобби, а `reply_to_message_id` отбрасывается, поэтому нельзя ответить на сообщение cron, попавшее в основной чат.

Перенаправь cron в отдельную тему форума:

1. В Telegram открой DM бота и создай тему, например `Cron`. Долгим нажатием на заголовок темы выбери **Copy link**; конечное число — это `message_thread_id` темы.
2. Установи `TELEGRAM_CRON_THREAD_ID=<that id>` в своём `.env`.

Это применяется только к доставкам cron. `TELEGRAM_HOME_CHANNEL_THREAD_ID` (используется в других местах, например для уведомлений о перезапуске) остаётся без изменений. Явные цели `deliver="telegram:chat_id:thread_id"` по‑прежнему имеют приоритет над переменной окружения. Ответы на сообщения cron теперь приходят в существующую сессию темы, так что можно реагировать на них напрямую.

### Обёртка ответа

По умолчанию вывод cron, доставляемый получателю, оборачивается заголовком и подвалом, чтобы получатель понял, что это результат запланированной задачи:

```
Cronjob Response: Morning feeds
-------------

<agent output here>

Note: The agent cannot see this message, and therefore cannot respond to it.
```

Чтобы доставлять «сырой» вывод агента без обёртки, установи `cron.wrap_response` в `false`:

```yaml
# ~/.hermes/config.yaml
cron:
  wrap_response: false
```

### Тихое подавление

Если финальный ответ агента начинается с `[SILENT]`, доставка полностью подавляется. Вывод всё равно сохраняется локально для аудита (в `~/.hermes/cron/output/`), но сообщение не отправляется в цель доставки.

Это удобно для мониторинговых задач, которые должны сообщать только при возникновении проблемы:

```text
Check if nginx is running. If everything is healthy, respond with only [SILENT].
Otherwise, report the issue.
```

Неудачные задачи всегда доставляются независимо от маркера `[SILENT]` — только успешные запуски могут быть заглушены.
## Тайм‑аут скрипта

Скрипты, выполняемые перед запуском (привязанные через параметр `script`), имеют тайм‑аут — 120 секунд. Если твоим скриптам требуется больше времени — например, чтобы добавить случайные задержки и избежать шаблонов тайминга, характерных для ботов — можешь увеличить его:

```yaml
# ~/.hermes/config.yaml
cron:
  script_timeout_seconds: 300   # 5 minutes
```

Или установить переменную окружения `HERMES_CRON_SCRIPT_TIMEOUT`. Порядок разрешения: переменная окружения → `config.yaml` → значение по умолчанию — 120 сек.
## Режим без агента (только скрипты)

Для периодических задач, которым не требуется рассуждение LLM — классические watchdog‑ы, оповещения о диске/памяти, heartbeat‑ы, CI‑ping‑и — передай `no_agent=True` при создании. Планировщик будет запускать твой скрипт по расписанию и передавать его `stdout` напрямую, полностью обходя агента:

```bash
hermes cron create "every 5m" \
  --no-agent \
  --script memory-watchdog.sh \
  --deliver telegram \
  --name "memory-watchdog"
```

**Семантика**

- `stdout` скрипта (обрезанный) → доставляется дословно как сообщение.
- **Пустой `stdout` → тихий тик**, без доставки. Это шаблон watchdog: «сообщать только когда что‑то пошло не так».
- Ненулевой код выхода или тайм‑аут → отправляется оповещение об ошибке, чтобы сломанный watchdog не молчал.
- `{"wakeAgent": false}` в последней строке → тихий тик (тот же шлюз, что используют задачи LLM).
- Нет токенов, модели, запасного провайдера — задача никогда не касается уровня вывода инференса.

Файлы `.sh` / `.bash` выполняются под `/bin/bash`; всё остальное — под текущим интерпретатором Python (`sys.executable`). Скрипты должны находиться в `~/.hermes/scripts/` (то же правило изоляции, что и для предзапуска скрипта).

### Агент настраивает это за тебя

Схема инструмента `cronjob` раскрывает `no_agent` напрямую Hermes, так что ты можешь описать watchdog в чате и позволить агенту настроить его:

```text
Ping me on Telegram if RAM is over 85%, every 5 minutes.
```

Hermes запишет проверочный скрипт в `~/.hermes/scripts/` через `write_file`, затем вызовет:

```python
cronjob(action="create", schedule="every 5m",
        script="memory-watchdog.sh", no_agent=True,
        deliver="telegram", name="memory-watchdog")
```

Он автоматически выбирает `no_agent=True`, когда содержание сообщения полностью определяется скриптом (watchdog‑ы, пороговые оповещения, heartbeat‑ы). Тот же инструмент позволяет агенту ставить задачу на паузу, возобновлять, редактировать и удалять — так что весь жизненный цикл управляется через чат без обращения к CLI.

См. руководство [Script-Only Cron Jobs guide](/guides/cron-script-only) для готовых примеров.
## Связывание задач с помощью `context_from`

Cron‑задачи выполняются в изолированных сессиях без памяти о предыдущих запусках. Но иногда вывод одной задачи — именно то, что нужно следующей. Параметр `context_from` автоматически устанавливает эту связь — prompt задачи B получает самый свежий вывод задачи A, добавленный в качестве контекста во время выполнения.

```python
# Job 1: Collect raw data
cronjob(
    action="create",
    prompt="Fetch the top 10 AI/ML stories from Hacker News. Save them to ~/.hermes/data/briefs/raw.md in markdown format with title, URL, and score.",
    schedule="0 7 * * *",
    name="AI News Collector",
)

# Job 2: Triage — receives Job 1's output as context
# Get Job 1's ID from: cronjob(action="list")
cronjob(
    action="create",
    prompt="Read ~/.hermes/data/briefs/raw.md. Score each story 1–10 for engagement potential and novelty. Output the top 5 to ~/.hermes/data/briefs/ranked.md.",
    schedule="30 7 * * *",
    context_from="<job1_id>",
    name="AI News Triage",
)

# Job 3: Ship — receives Job 2's output as context
cronjob(
    action="create",
    prompt="Read ~/.hermes/data/briefs/ranked.md. Write 3 tweet drafts (hook + body + hashtags). Deliver to telegram:7976161601.",
    schedule="0 8 * * *",
    context_from="<job2_id>",
    name="AI News Brief",
)
```

**Как это работает:**

- Когда запускается задача 2, Hermes читает самый последний вывод задачи 1 из `~/.hermes/cron/output/{job1_id}/*.md`
- Этот вывод автоматически добавляется в начало prompt задачи 2
- Задаче 2 не нужно жёстко прописывать «прочитать этот файл» — она получает содержимое как контекст
- Цепочка может быть любой длины: задача 1 → задача 2 → задача 3 → …

**Что принимает `context_from`:**

| Формат | Пример |
|--------|--------|
| Идентификатор одной задачи (строка) | `context_from="a1b2c3d4"` |
| Несколько идентификаторов задач (список) | `context_from=["job_a", "job_b"]` |

Выводы конкатенируются в указанном порядке.

**Когда использовать:**

- Многоэтапные конвейеры (сбор → фильтрация → форматирование → доставка)
- Зависимые задачи, где работа шага N зависит от вывода шага N−1
- Шаблоны fan‑out/fan‑in, когда одна задача агрегирует результаты нескольких других
## Восстановление провайдера

Cron‑задачи наследуют настроенные тобой запасные (фоллбэк) провайдеры и ротацию пула учётных данных. Если основной API‑ключ ограничен по скорости или провайдер возвращает ошибку, cron‑агент может:

- **Перейти к альтернативному провайдеру**, если в `config.yaml` указаны `fallback_providers` (или устаревший `fallback_model`);
- **Перейти к следующему набору учётных данных** в твоём [пуле учётных данных](/user-guide/configuration#credential-pool-strategies) для того же провайдера.

Это значит, что cron‑задачи, запускаемые с высокой частотой или в пиковые часы, становятся более надёжными — один ограниченный по скорости ключ не приведёт к провалу всего запуска.
## Форматы расписания

Ответ агента в финальном виде доставляется автоматически — тебе **не нужно** включать `send_message` в запросе cron для того же самого получателя. Если запуск cron вызывает `send_message` к точному получателю, которому планировщик уже доставит сообщение, Hermes пропустит дублирующую отправку и сообщит модели разместить пользовательский контент в финальном ответе. Используй `send_message` только для дополнительных или иных получателей.

### Относительные задержки (однократные)

```text
30m     → Run once in 30 minutes
2h      → Run once in 2 hours
1d      → Run once in 1 day
```

### Интервалы (повторяющиеся)

```text
every 30m    → Every 30 minutes
every 2h     → Every 2 hours
every 1d     → Every day
```

### Cron‑выражения

```text
0 9 * * *       → Daily at 9:00 AM
0 9 * * 1-5     → Weekdays at 9:00 AM
0 */6 * * *     → Every 6 hours
30 8 1 * *      → First of every month at 8:30 AM
0 0 * * 0       → Every Sunday at midnight
```

### ISO‑метки времени

```text
2026-03-15T09:00:00    → One-time at March 15, 2026 9:00 AM
```
## Поведение повторения

| Тип расписания | Повтор по умолчанию | Поведение |
|----------------|---------------------|-----------|
| One-shot (`30m`, timestamp) | 1 | Выполняется один раз |
| Interval (`every 2h`) | forever | Выполняется, пока не будет удалён |
| Cron expression | forever | Выполняется, пока не будет удалён |

Ты можешь переопределить это:

```python
cronjob(
    action="create",
    prompt="...",
    schedule="every 2h",
    repeat=5,
)
```
## Управление заданиями программно

API, ориентированное на агента, — один из инструментов:

```python
cronjob(action="create", ...)
cronjob(action="list")
cronjob(action="update", job_id="...")
cronjob(action="pause", job_id="...")
cronjob(action="resume", job_id="...")
cronjob(action="run", job_id="...")
cronjob(action="remove", job_id="...")
```

Для `update` передай `skills=[]`, чтобы удалить все прикреплённые навыки.
## Наборы инструментов, доступные для cron‑задач

Cron запускает каждую задачу в новой сессии агента без привязки к чат‑платформе. По умолчанию cron‑агент получает **набор инструментов, который ты настроил для платформы `cron` в `hermes tools`** — не значение по умолчанию CLI и не всё, что существует.

```bash
hermes tools
# → pick the "cron" platform in the curses UI
# → toggle toolsets on/off just like you would for Telegram/Discord/etc.
```

Более тонкое управление задачами доступно через поле `enabled_toolsets` в `cronjob.create` (или в уже существующей задаче через `cronjob.update`):

```text
cronjob(action="create", name="weekly-news-summary",
        schedule="every sunday 9am",
        enabled_toolsets=["web", "file"],      # just web + file, no terminal/browser/etc.
        prompt="Summarize this week's AI news: ...")
```

Если `enabled_toolsets` задано для задачи, оно имеет приоритет; иначе приоритет имеет конфигурация `hermes tools` для платформы `cron`; иначе Hermes переходит к встроенным значениям по умолчанию. Это важно для контроля расходов: включение `moa`, `browser`, `delegation` в каждую крошечную задачу «получить новости» раздувает подсказку схемы инструментов при каждом вызове LLM.

### Пропуск агента полностью: `wakeAgent`

Если твоя cron‑задача подключает скрипт предварительной проверки (через `script=`), скрипт может решить во время выполнения, должен ли Hermes вообще вызывать агента. Выведи в stdout последнюю строку вида:

```text
{"wakeAgent": false}
```

…и cron полностью пропустит запуск агента для этого тика. Это полезно для частых опросов (каждые 1–5 мин), которым нужно разбудить LLM только когда состояние действительно изменилось — иначе ты платишь за пустые обращения агента снова и снова.

```python
# pre-check script
import json, sys
latest = fetch_latest_issue_count()
prev = read_state("issue_count")
if latest == prev:
    print(json.dumps({"wakeAgent": False}))   # skip this tick
    sys.exit(0)
write_state("issue_count", latest)
print(json.dumps({"wakeAgent": True, "context": {"new_issues": latest - prev}}))
```

Если `wakeAgent` опущено, значение по умолчанию — `true` (пробуждать агент как обычно).

#### Рецепты: дешёвые ворота перед запуском

Ворота `wakeAgent` дают возможность бесплатно решить, должна ли запланированная задача тратить токены LLM. Три шаблона покрывают большинство сценариев.

**Ворота изменения файла** — запуск только когда наблюдаемый файл получил новое содержимое с последнего успешного тика. Планировщик сохраняет для каждой задачи значение `last_run_at`; сравни его с временем изменения файла.

```bash
#!/bin/bash
# ~/.hermes/scripts/feed-changed.sh
FEED="$HOME/data/feed.json"
STATE="$HOME/.hermes/scripts/.feed-changed.last"
test -f "$FEED" || { echo '{"wakeAgent": false}'; exit 0; }
mtime=$(stat -c %Y "$FEED")
last=$(cat "$STATE" 2>/dev/null || echo 0)
if [ "$mtime" -le "$last" ]; then
  echo '{"wakeAgent": false}'
else
  echo "$mtime" > "$STATE"
  echo '{"wakeAgent": true}'
fi
```

```text
cronjob(action="create", name="process-feed",
        schedule="every 30m",
        script="feed-changed.sh",
        prompt="A new ~/data/feed.json has landed. Summarize what changed.")
```

**Ворота внешнего флага** — запуск только когда какой‑то другой процесс сигнализировал о готовности (например, хук деплоя создал файл, CI‑задача записала значение в твоё хранилище состояния).

```bash
#!/bin/bash
# ~/.hermes/scripts/flag-ready.sh
if test -f /tmp/new-data-ready; then
  rm -f /tmp/new-data-ready
  echo '{"wakeAgent": true}'
else
  echo '{"wakeAgent": false}'
fi
```

```text
cronjob(action="create", name="nightly-analysis",
        schedule="0 9 * * *",
        script="flag-ready.sh",
        prompt="Run the nightly analysis over today's batch.")
```

**Ворота подсчёта SQL** — запуск только когда в твоей базе появились новые строки для обработки. Скрипт может также передать количество через `context`, чтобы агент знал, сколько данных обрабатывать, без повторного запроса.

```python
#!/usr/bin/env python
# ~/.hermes/scripts/new-rows.py
import json, sqlite3
conn = sqlite3.connect("/home/me/data/app.db")
n = conn.execute(
    "SELECT COUNT(*) FROM messages WHERE ts > strftime('%s','now','-2 hours')"
).fetchone()[0]
if n < 1:
    print(json.dumps({"wakeAgent": False}))
else:
    print(json.dumps({"wakeAgent": True, "context": {"new_rows": n}}))
```

```text
cronjob(action="create", name="summarize-new-msgs",
        schedule="every 2h",
        script="new-rows.py",
        prompt="Summarize the new messages from the last 2 hours.")
```

Тот же шаблон работает с любым источником данных, к которому можно обратиться из скрипта — Postgres, HTTP‑API, собственное хранилище состояния — без необходимости встраивать SQL‑движок в подсистему cron.

:::tip
Внутренняя схема `~/.hermes/state.db` Hermes меняется между релизами. Не запрашивай её из ворота перед запуском — указывай свою базу данных или поток данных.
:::

Credit: этот набор рецептов появился благодаря исследованию @iankar8 в [#2654](https://github.com/NousResearch/hermes-agent/pull/2654), где предлагалось добавить триггеры sql/file/command как параллельный механизм. Комбинация `script` + ворота `wakeAgent` уже покрывает все три случая бесплатно, поэтому работа была оформлена как документация.

### Последовательный запуск задач: `context_from`

Cron‑задача может использовать самый последний успешный вывод одной или нескольких других задач, указав их имена (или ID) в `context_from`:

```text
cronjob(action="create", name="daily-digest",
        schedule="every day 7am",
        context_from=["ai-news-fetch", "github-prs-fetch"],
        prompt="Write the daily digest using the outputs above.")
```

Выводы указанных задач вставляются над подсказкой как контекст для текущего запуска. Каждая запись upstream должна быть действительным ID или именем задачи (см. `cronjob action="list"`). Замечание: последовательность читает *самый последний завершённый* вывод — она не ждёт задачи, запущенной в том же тике.
## Хранилище задач

Задачи сохраняются в `~/.hermes/cron/jobs.json`. Вывод выполнения задач записывается в `~/.hermes/cron/output/{job_id}/{timestamp}.md`.

В записях задач поля `model` и `provider` могут иметь значение `null`. Если эти поля опущены, Hermes определяет их во время выполнения из глобальной конфигурации. Они появляются в записи задачи только при наличии переопределения для конкретной задачи.

Хранилище использует атомарные записи файлов, поэтому прерванные записи не оставляют частично записанный файл задачи.
## Самодостаточные подсказки всё ещё важны

:::warning Important
Cron‑задачи запускаются в полностью новой сессии агента. Подсказка должна содержать всё, что агенту нужно и что не предоставлено уже подключёнными навыками.
:::

**BAD:** `"Check on that server issue"`

**GOOD:** `"SSH into server 192.168.1.100 as user 'deploy', check if nginx is running with 'systemctl status nginx', and verify https://example.com returns HTTP 200."`
## Безопасность

Запланированные задачи‑подсказки сканируются на наличие шаблонов инъекции подсказок и утечки учётных данных при их создании и обновлении. Подсказки, содержащие невидимые приёмы Unicode, попытки установить SSH‑бекдор или явные полезные нагрузки для утечки секретов, блокируются.