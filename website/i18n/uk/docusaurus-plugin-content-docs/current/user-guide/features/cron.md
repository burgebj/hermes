---
sidebar_position: 5
title: "Заплановані завдання (Cron)"
description: "Заплануй автоматизовані завдання за допомогою природної мови, керуй ними за допомогою одного cron інструмента та прикріпи один або кілька skills"
---

# Заплановані завдання (Cron)

Плануй виконання завдань автоматично за допомогою природної мови або cron‑виразів. Hermes надає керування cron через єдиний інструмент `cronjob` з операціями у стилі дій, замість окремих інструментів `schedule`/`list`/`remove`.
## Що тепер може cron

Cron‑завдання можуть:

- планувати одноразові або повторювані завдання
- призупиняти, відновлювати, редагувати, запускати та видаляти завдання
- прикріплювати нуль, один або кілька **skill** до завдання
- доставляти результати назад у вихідний чат, локальні файли або налаштовані цільові платформи
- запускатися у нових сесіях агента зі стандартним статичним списком інструментів
- працювати в **режимі без агента** — скрипт за розкладом, його `stdout` доставляється дослівно, без залучення LLM (див. розділ [no-agent mode](#no-agent-mode-script-only-jobs) нижче)

Все це доступно самому Hermes через інструмент `cronjob`, тому ти можеш створювати, призупиняти, редагувати та видаляти завдання, просто запитуючи природною мовою — без необхідності використовувати CLI.

:::tip
Cron‑завдання використовують будь‑якого **provider**, обраного `hermes model`. `hermes setup --portal` — найменш обтяжливий варіант для безнаглядових запусків, оскільки оновлення OAuth виконується автоматично. Дивись [Nous Portal](/integrations/nous-portal).
:::

:::warning
Сесії, запущені cron‑ом, не можуть рекурсивно створювати нові cron‑завдання. Hermes вимикає інструменти керування cron всередині виконань cron, щоб запобігти неконтрольованим циклам планування.
:::
## Створення запланованих завдань

### У чаті з `/cron`

```bash
/cron add 30m "Remind me to check the build"
/cron add "every 2h" "Check server status"
/cron add "every 1h" "Summarize new feed items" --skill blogwatcher
/cron add "every 1h" "Use both skills and combine the result" --skill blogwatcher --skill maps
```

### З автономного CLI

```bash
hermes cron create "every 2h" "Check server status"
hermes cron create "every 1h" "Summarize new feed items" --skill blogwatcher
hermes cron create "every 1h" "Use both skills and combine the result" \
  --skill blogwatcher \
  --skill maps \
  --name "Skill combo"
```

### Через природну розмову

Запитай Hermes як зазвичай:

```text
Every morning at 9am, check Hacker News for AI news and send me a summary on Telegram.
```

Hermes буде використовувати уніфікований інструмент `cronjob` внутрішньо.
## Skill‑backed cron jobs

Cron‑job може завантажити одну або кілька skills перед тим, як виконати prompt.

### Single skill

```python
cronjob(
    action="create",
    skill="blogwatcher",
    prompt="Check the configured feeds and summarize anything new.",
    schedule="0 9 * * *",
    name="Morning feeds",
)
```

### Multiple skills

Skills завантажуються у зазначеному порядку. Prompt стає інструкцією завдання, накладеною поверх цих skills.

```python
cronjob(
    action="create",
    skills=["blogwatcher", "maps"],
    prompt="Look for new local events and interesting nearby places, then combine them into one short brief.",
    schedule="every 6h",
    name="Local brief",
)
```

Це корисно, коли потрібно, щоб запланований агент успадковував повторно використовувані робочі процеси, не вбудовуючи повний текст skill безпосередньо в prompt cron‑job.
## Running a job inside a project directory

Cron‑jobs за замовчуванням виконуються відокремлено від будь‑якого репозиторію — не завантажується `AGENTS.md`, `CLAUDE.md` чи `.cursorrules`, а інструменти `terminal`, `read_file`, `execute_code` працюють у тому робочому каталозі, у якому був запущений **gateway**. Передай `--workdir` (CLI) або `workdir=` (виклик інструменту), щоб змінити це:

```bash
# Standalone CLI (schedule and prompt are positional)
hermes cron create "every 1d at 09:00" \
  "Audit open PRs, summarize CI health, and post to #eng" \
  --workdir /home/me/projects/acme
```

⟦HOLD_6⟩

Коли встановлено `workdir`:

- `AGENTS.md`, `CLAUDE.md` і `.cursorrules` з цього каталогу ін’єкціюються у системний підказник (та ж послідовність виявлення, що й у інтерактивному CLI)
- `terminal`, `read_file`, `write_file`, `patch`, `search_files` і `execute_code` всі використовують цей каталог як робочий (через `TERMINAL_CWD`)
- Шлях має бути абсолютним каталогом, який існує — відносні шляхи та відсутні каталоги відхиляються під час створення/оновлення
- Передай `--workdir ""` (або `workdir=""` через інструмент) під час редагування, щоб очистити його і відновити стару поведінку

:::note Serialization
Завдання з `workdir` виконуються послідовно під час тикання планувальника, а не у паралельному пулі. Це навмисно — `TERMINAL_CWD` є глобальним для процесу, тому два завдання з різними `workdir`, що працюють одночасно, могли б пошкодити cwd одне одного. Завдання без `workdir` і надалі виконуються паралельно, як раніше.
:::
## Запуск cron‑завдань у певному профілі

За замовчуванням cron‑завдання успадковує той профіль Hermes, якому належить шлюз / CLI, який його створив. Передай `--profile <name>` (CLI) або `profile=` (cronjob tool), щоб перенаправити завдання на інший профіль — планувальник визначає `HERMES_HOME` цього профілю, тимчасово переходить у нього на час виконання, завантажує його `.env` + `config.yaml` і виконує завдання там:

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

Використовуй `--profile default`, щоб явно прив’язати до кореневого профілю Hermes. Іменований профіль має вже існувати; планувальник відмовляється створювати профілі «на льоту». Щоб очистити прив’язку профілю під час `cron edit`, передай порожній рядок (`--profile ""` або `profile=""`) — завдання повернеться до виконання у тому профілі, у якому знаходиться сам планувальник.

Якщо прив’язаний профіль пізніше буде видалено, планувальник залогуватиме попередження та перейде до виконання завдання у поточному профілі, а не завершиться аварійно — тому застаріле посилання `profile` ніколи не блокує завдання.

:::note Серіалізація
Завдання з встановленим `profile` також виконуються послідовно, з тієї ж причини, що й завдання з прив’язаним `workdir`: зміна `HERMES_HOME` є глобальною мутацією процесу, тому два завдання, прив’язані до різних профілів, що виконуються паралельно, конкурували б між собою. Завдання без прив’язки все ще виконуються у звичайному паралельному пулі.
:::
## Редагування завдань

Ти не повинен видаляти та створювати завдання заново лише для їх зміни.

:::tip Job reference
Заповнювач `<job_id>` нижче (і в [Lifecycle actions](#lifecycle-actions)) також приймає назву завдання (без урахування регістру) — зручно, коли ти пам’ятаєш `morning-digest`, а не hex‑ідентифікатор. Точний ідентифікатор завдання має пріоритет над збігами за назвою; якщо посилання не є ідентифікатором і назва збігається з кількома завданнями, команда відмовляється і виводить кандидатські ідентифікатори, щоб ти міг їх розрізнити.
:::

### Chat

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

Нотатки:

- повторюване `--skill` замінює список приєднаних **skill**
- `--add-skill` додає до існуючого списку без його заміни
- `--remove-skill` видаляє конкретні приєднані **skill**
- `--clear-skills` видаляє всі приєднані **skill**
## Дії життєвого циклу

Cron‑завдання тепер мають повніший цикл, а не лише створення/видалення.

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

Що вони роблять:

- `pause` — зберегти завдання, але зупинити його планування
- `resume` — повторно ввімкнути завдання та обчислити наступний запуск
- `run` — запустити завдання на наступному тикі планувальника
- `remove` — повністю видалити його
- `edit` — змінити розклад, підказку, профіль, доставку тощо

**Пошук за назвою.** Усі дієслова, що змінюють стан (`pause`, `resume`, `run`, `remove`, `edit`), а також інструмент агента `cronjob` тепер приймають **назву** завдання (без урахування регістру) замість шістнадцяткового ID. Агент і CLI віддають перевагу точному збігу ID, якщо він існує; неоднозначні збіги за назвою (кілька завдань з однаковою назвою) відхиляються з повним списком кандидатних ID, щоб ти міг вибрати потрібне явно. Назви не є унікальними, тому ця перевірка є критичною — вона запобігає випадковому зміненню неправильного завдання, коли два мають одну й ту ж назву.
## Як це працює

**Виконання Cron обробляється демоном шлюзу.** Шлюз запускає планувальник кожні 60 секунд, виконуючи всі заплановані завдання в ізольованих сесіях агентів.

```bash
hermes gateway install     # Install as a user service
sudo hermes gateway install --system   # Linux: boot-time system service for servers
hermes gateway             # Or run in foreground

hermes cron list
hermes cron status
```

### Поведінка планувальника шлюзу

На кожному тіку шлюзу:

1. завантажує завдання з `~/.hermes/cron/jobs.json`
2. перевіряє `next_run_at` щодо поточного часу
3. запускає нову сесію `AIAgent` для кожного запланованого завдання
4. за потреби ін’єкціонує одну або кілька приєднаних навичок у цю нову сесію
5. виконує запит до завершення
6. повертає остаточну відповідь
7. оновлює метадані виконання та наступний запланований час

Блокування файлу `~/.hermes/cron/.tick.lock` запобігає накладанню тіків планувальника, що могло б призвести до подвійного запуску тієї ж партії завдань.
## Варіанти доставки

При плануванні завдань ти вказуєш, куди має потрапити output:

| Опція | Опис | Приклад |
|--------|-------------|---------|
| `"origin"` | Повернутись туди, звідки створено завдання | За замовчуванням у платформах обміну повідомленнями |
| `"local"` | Зберегти лише у локальних файлах (`~/.hermes/cron/output/`) | За замовчуванням у CLI |
| `"telegram"` | Домашній канал Telegram | Використовує `TELEGRAM_HOME_CHANNEL` |
| `"telegram:123456"` | Конкретний чат Telegram за ID | Пряма доставка |
| `"telegram:-100123:17585"` | Конкретна тема Telegram | Формат `chat_id:thread_id` |
| `"discord"` | Домашній канал Discord | Використовує `DISCORD_HOME_CHANNEL` |
| `"discord:#engineering"` | Конкретний канал Discord | За назвою каналу |
| `"slack"` | Домашній канал Slack | |
| `"whatsapp"` | Домашній канал WhatsApp | |
| `"signal"` | Signal | |
| `"matrix"` | Домашня кімната Matrix | |
| `"mattermost"` | Домашній канал Mattermost | |
| `"email"` | Email | |
| `"sms"` | SMS через Twilio | |
| `"homeassistant"` | Home Assistant | |
| `"dingtalk"` | DingTalk | |
| `"feishu"` | Feishu/Lark | |
| `"wecom"` | WeCom | |
| `"weixin"` | Weixin (WeChat) | |
| `"bluebubbles"` | BlueBubbles (iMessage) | |
| `"qqbot"` | QQ Bot (Tencent QQ) | |
| `"all"` | Розсилати на всі підключені домашні канали | Визначається під час запуску |
| `"telegram,discord"` | Розсилати на конкретний набір каналів | Список, розділений комами |
| `"origin,all"` | Доставити до вихідного чату **плюс** до всіх інших підключених каналів | Комбінується з будь‑якими токенами |

Остаточна відповідь агента автоматично доставляється. Не потрібно викликати `send_message` у запиті cron.

### Маршрутизація інтенції (`all`)

`all` дозволяє відправити одне cron‑завдання на кожен канал обміну повідомленнями, який ти налаштував, без необхідності перераховувати їх за іменами. Воно **визначається під час запуску**, тому завдання, створене до підключення Telegram, підхопить Telegram на наступному тіку після встановлення `TELEGRAM_HOME_CHANNEL`.

Семантика: `all` розширюється до кожної платформи з налаштованим домашнім каналом. Нульовий варіант допустимий; завдання просто не має цілей доставки і реєструється як помилка доставки вище.

`all` комбінується з явними цілями. `origin,all` доставляє до вихідного чату *плюс* до всіх інших підключених домашніх каналів, уникаючи дублювання за `(platform, chat_id, thread_id)`.

### Тема cron у Telegram (`TELEGRAM_CRON_THREAD_ID`)

Коли режим теми Telegram увімкнено, кореневий DM зарезервовано як системна лобі — відповіді, надіслані туди, відхиляються з нагадуванням про лобі, а `reply_to_message_id` відкидається, тому ти не можеш відповісти на cron‑повідомлення, що потрапило у головний чат.

Перенаправ cron у спеціальну тему форуму:

1. У Telegram відкрий DM бота і створи тему, наприклад `Cron`. Довго натисни заголовок теми → **Copy link**; останнє число — це `message_thread_id` теми.
2. Встанови `TELEGRAM_CRON_THREAD_ID=<той id>` у своєму `.env`.

Це стосується лише доставок cron. `TELEGRAM_HOME_CHANNEL_THREAD_ID` (використовується в інших місцях, напр. сповіщення про перезапуск) залишається без змін. Явні цілі `deliver="telegram:chat_id:thread_id"` продовжують мати пріоритет над змінною середовища. Відповіді на cron‑повідомлення тепер надходять у існуючу сесію теми, тож ти можеш діяти безпосередньо.

### Обгортка відповіді

За замовчуванням вихід cron‑завдання обгортається заголовком і підвалом, щоб отримувач знав, що це результат запланованого завдання:

```
Cronjob Response: Morning feeds
-------------

<agent output here>

Note: The agent cannot see this message, and therefore cannot respond to it.
```

Щоб доставити «чистий» output агента без обгортки, встанови `cron.wrap_response` у `false`:

```yaml
# ~/.hermes/config.yaml
cron:
  wrap_response: false
```

### Тиха підмова

Якщо остаточна відповідь агента починається з `[SILENT]`, доставка повністю придушується. Output все одно зберігається локально для аудиту (у `~/.hermes/cron/output/`), але повідомлення не надсилається до цілі доставки.

Це корисно для моніторингових завдань, які мають повідомляти лише про проблеми:

```text
Check if nginx is running. If everything is healthy, respond with only [SILENT].
Otherwise, report the issue.
```

Невдалі завдання завжди доставляються, незалежно від маркера `[SILENT]` — лише успішні запуски можуть бути заглушені.
## Тайм‑аут скрипту

Скрипти, що виконуються перед запуском (підключені через параметр `script`), мають типовий тайм‑аут 120 секунд. Якщо твоїм скриптам потрібен довший час — наприклад, щоб включити випадкові затримки, які уникають шаблонних бот‑подібних інтервалів — ти можеш збільшити його:

```yaml
# ~/.hermes/config.yaml
cron:
  script_timeout_seconds: 300   # 5 minutes
```

Або встановити змінну середовища `HERMES_CRON_SCRIPT_TIMEOUT`. Порядок розв’язання такий: змінна середовища → `config.yaml` → типове значення 120 секунд.
## Режим без агента (тільки скрипти)

Для повторюваних завдань, які не потребують LLM‑роздумів — класичні watchdog'и, сповіщення про диск/пам’ять, heartbeat'и, CI‑ping'и — передай `no_agent=True` під час створення. Планувальник запускає твій скрипт за розкладом і передає його stdout безпосередньо, повністю минаючи агента:

```bash
hermes cron create "every 5m" \
  --no-agent \
  --script memory-watchdog.sh \
  --deliver telegram \
  --name "memory-watchdog"
```

**Семантика**:

- Stdout скрипту (обрізаний) → доставляється дослівно як повідомлення.
- **Порожній stdout → тихий тик**, без доставки. Це шаблон watchdog: «говори лише коли щось не так».
- Ненульовий код виходу або тайм‑аут → доставляється сповіщення про помилку, тому поламаний watchdog не може «тихо» завершитися.
- `{"wakeAgent": false}` у останньому рядку → тихий тик (те саме, що використовується у LLM‑завданнях).
- Жодних токенів, моделей, запасного провайдера — завдання ніколи не торкається шару інференції.

Файли `.sh` / `.bash` виконуються під `/bin/bash`; все інше — під поточним інтерпретатором Python (`sys.executable`). Скрипти мають знаходитися в `~/.hermes/scripts/` (те саме правило пісочниці, що й у попередньо‑запусковому скрипті).

### Агент налаштовує це за тебе

Схема інструмента `cronjob` експонує `no_agent` безпосередньо в Hermes, тому ти можеш описати watchdog у чаті і дозволити агенту підключити його:

```text
Ping me on Telegram if RAM is over 85%, every 5 minutes.
```

Hermes запише скрипт перевірки у `~/.hermes/scripts/` за допомогою `write_file`, а потім виконає:

```python
cronjob(action="create", schedule="every 5m",
        script="memory-watchdog.sh", no_agent=True,
        deliver="telegram", name="memory-watchdog")
```

Він автоматично встановлює `no_agent=True`, коли вміст повідомлення повністю визначається скриптом (watchdog'и, порогові сповіщення, heartbeat'и). Той самий інструмент також дозволяє агенту призупиняти, відновлювати, редагувати та видаляти завдання — таким чином весь життєвий цикл керується через чат без необхідності взаємодії з CLI.

Дивись [Посібник щодо скриптових cron‑завдань](/guides/cron-script-only) для готових прикладів.
## Зв’язування завдань за допомогою `context_from`

Cron‑завдання виконуються в ізольованих сесіях без пам’яті про попередні запуски. Але іноді вихідні дані одного завдання саме те, що потрібно наступному. Параметр `context_from` автоматично встановлює цей зв’язок — підказка Job B отримує найновіший вихід Job A, доданий як контекст під час виконання.

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

**Як це працює:**

- Коли запускається Job 2, Hermes читає найновіший вихід Job 1 з `~/.hermes/cron/output/{job1_id}/*.md`
- Цей вихід автоматично додається перед підказкою Job 2
- Job 2 не потрібно жорстко кодувати «читай цей файл» — він отримує вміст як контекст
- Ланцюг може мати будь‑яку довжину: Job 1 → Job 2 → Job 3 → …

**Що приймає `context_from`:**

| Формат | Приклад |
|--------|---------|
| Ідентифікатор одного завдання (рядок) | `context_from="a1b2c3d4"` |
| Ідентифікатори кількох завдань (список) | `context_from=["job_a", "job_b"]` |

Виходи конкатенуються у вказаному порядку.

**Коли варто використовувати:**

- Багатоступеневі конвеєри (збір → фільтрація → форматування → доставка)
- Залежні завдання, коли робота кроку N залежить від виходу кроку N−1
- Шаблони fan‑out/fan‑in, коли одне завдання агрегує результати кількох інших
## Відновлення провайдера

Cron‑завдання успадковують ваші налаштовані запасні (варіант) провайдери та ротацію пулу облікових даних. Якщо основний API‑ключ підлягає обмеженню за швидкістю або провайдер повертає помилку, cron‑агент може:

- **Перейти до альтернативного провайдера**, якщо у вас налаштовано `fallback_providers` (або застарілий `fallback_model`) у `config.yaml`
- **Перейти до наступного облікового запису** у вашому [credential pool](/user-guide/configuration#credential-pool-strategies) для того самого провайдера

Це означає, що cron‑завдання, які виконуються з високою частотою або під час пікових навантажень, стають більш стійкими — один обмежений за швидкістю ключ не призведе до збою всього запуску.
## Формати розкладу

Фінальна відповідь агента автоматично доставляється — тобі **не** потрібно включати `send_message` у запит cron для того самого призначення. Якщо запуск cron викликає `send_message` до точної цілі, куди вже планувальник доставляє, Hermes пропускає це дублювання і каже моделі розмістити користувацький контент у фінальній відповіді. Використовуй `send_message` лише для додаткових або інших цілей.

### Відносні затримки (одноразові)

```text
30m     → Run once in 30 minutes
2h      → Run once in 2 hours
1d      → Run once in 1 day
```

### Інтервали (повторювані)

```text
every 30m    → Every 30 minutes
every 2h     → Every 2 hours
every 1d     → Every day
```

### Вирази cron

```text
0 9 * * *       → Daily at 9:00 AM
0 9 * * 1-5     → Weekdays at 9:00 AM
0 */6 * * *     → Every 6 hours
30 8 1 * *      → First of every month at 8:30 AM
0 0 * * 0       → Every Sunday at midnight
```

### ISO‑мітки часу

```text
2026-03-15T09:00:00    → One-time at March 15, 2026 9:00 AM
```
## Повторення поведінки

| Тип розкладу | Повторення за замовчуванням | Поведінка |
|--------------|----------------------------|----------|
| One-shot (`30m`, timestamp) | 1 | Виконується один раз |
| Interval (`every 2h`) | безкінечно | Виконується, доки не буде видалено |
| Cron expression | безкінечно | Виконується, доки не буде видалено |

Ти можеш перевизначити це:

```python
cronjob(
    action="create",
    prompt="...",
    schedule="every 2h",
    repeat=5,
)
```
## Керування завданнями програмно

API, орієнтоване на агента, — один інструмент:

```python
cronjob(action="create", ...)
cronjob(action="list")
cronjob(action="update", job_id="...")
cronjob(action="pause", job_id="...")
cronjob(action="resume", job_id="...")
cronjob(action="run", job_id="...")
cronjob(action="remove", job_id="...")
```

Для `update` передай `skills=[]`, щоб видалити всі приєднані навички.
## Набори інструментів, доступні для cron‑завдань

Cron запускає кожне завдання в новій сесії агента без підключеної чат‑платформи. За замовчуванням cron‑агент отримує **набір інструментів, який ти налаштував для платформи `cron` у `hermes tools`** — не стандартний CLI, не все, що існує.

```bash
hermes tools
# → pick the "cron" platform in the curses UI
# → toggle toolsets on/off just like you would for Telegram/Discord/etc.
```

Точніше керування per‑job доступне через поле `enabled_toolsets` у `cronjob.create` (або в існуючому завданні за допомогою `cronjob.update`):

```text
cronjob(action="create", name="weekly-news-summary",
        schedule="every sunday 9am",
        enabled_toolsets=["web", "file"],      # just web + file, no terminal/browser/etc.
        prompt="Summarize this week's AI news: ...")
```

Коли `enabled_toolsets` встановлено для завдання, воно має пріоритет; інакше пріоритет має конфігурація `hermes tools` для cron‑платформи; якщо і це відсутнє, Hermes повертається до вбудованих значень за замовчуванням. Це важливо для контролю витрат: перенесення `moa`, `browser`, `delegation` у кожне крихітне завдання «отримати новини» роздуває підказку схеми інструментів при кожному виклику LLM.

### Пропуск агента повністю: `wakeAgent`

Якщо твоє cron‑завдання підключає скрипт попередньої перевірки (через `script=`), скрипт може під час виконання вирішити, чи слід Hermes навіть викликати агента. Виведи фінальний рядок stdout у такій формі:

```text
{"wakeAgent": false}
```

…і cron пропустить запуск агента повністю для цього тіку. Корисно для частих опитувань (кожні 1–5 хв), які потребують пробудити LLM лише коли стан справді змінився — інакше ти платиш за порожні оберти агента знову і знову.

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

Якщо `wakeAgent` опущено, за замовчуванням використовується `true` (пробудити агента, як звичайно).

#### Рецепти: дешеві ворота перед запуском

Ворота `wakeAgent` дають безкоштовний спосіб вирішити, чи має заплановане завдання витрачати LLM‑токени. Три шаблони охоплюють більшість випадків.

**Ворота зміни файлу** — запуск лише коли спостережуваний файл має новий вміст з останнього успішного тіку. Планувальник записує `last_run_at` кожного завдання; порівняй його з `mtime` файлу.

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

**Ворота зовнішнього прапорця** — запуск лише коли інший процес подав сигнал готовності (наприклад, хук розгортання залишив файл, CI‑завдання встановило значення у твоєму сховищі стану).

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

**Ворота підрахунку SQL** — запуск лише коли в твоїй базі даних з’явилися нові рядки для обробки. Скрипт може також передати підрахунок агенту через `context`, щоб агент знав, скільки даних розглядати, без повторного запиту.

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

Той самий шаблон працює з будь‑яким джерелом даних, яке можна запитати зі скрипту — Postgres, HTTP‑API, власне сховище стану — без вбудовування SQL‑виконавця в підсистему cron.

:::tip
Внутрішня схема `~/.hermes/state.db` Hermes змінюється між релізами. Не запитуй її з воріт перед запуском — вказуй свою базу даних або потік даних.
:::

Credit: цей набір рецептів був запропонований @iankar8 у [#2654](https://github.com/NousResearch/hermes-agent/pull/2654), де пропонувалося додати тригери sql/file/command як паралельний механізм. Поєднання `script` + воріт `wakeAgent` вже охоплює всі три випадки безкоштовно, тому роботу оформлено як документацію.

### Ланцюжок завдань: `context_from`

Cron‑завдання може використати найновіший успішний результат одного чи кількох інших завдань, вказавши їхні імена (або ID) у `context_from`:

```text
cronjob(action="create", name="daily-digest",
        schedule="every day 7am",
        context_from=["ai-news-fetch", "github-prs-fetch"],
        prompt="Write the daily digest using the outputs above.")
```

Посилання на найновіші завершені результати інжектуються у підказку перед виконанням. Кожен запис у верхньому потоці має бути дійсним ID або назвою завдання (див. `cronjob action="list"`). Зауваж: ланцюжок читає *найновіший завершений* результат — він не чекає на завдання, що виконуються в тому ж тіку.
## Сховище завдань

Завдання зберігаються у `~/.hermes/cron/jobs.json`. Вивід виконання завдань зберігається у `~/.hermes/cron/output/{job_id}/{timestamp}.md`.

У завданні можуть бути `model` та `provider` зі значенням `null`. Коли ці поля опущені, Hermes визначає їх під час виконання з глобальної конфігурації. Вони з’являються в записі завдання лише тоді, коли встановлено перевизначення для конкретного завдання.

Сховище використовує атомарні записи у файл, тому перервані записи не залишають частково записаний файл завдання.
## Самостійні підказки все ще важливі

:::warning Important
Cron‑завдання виконуються в абсолютно новій сесії агента. Підказка повинна містити все, що агенту потрібно, а не надається вже підключеними навичками.
:::

**BAD:** `"Check on that server issue"`

**GOOD:** `"SSH into server 192.168.1.100 as user 'deploy', check if nginx is running with 'systemctl status nginx', and verify https://example.com returns HTTP 200."`
## Безпека

Заплановані завдання‑промпти скануються на наявність шаблонів ін’єкції промптів та витоку облікових даних під час їх створення та оновлення. Промпти, що містять невидимі Unicode‑трюки, спроби SSH‑бекдору або очевидні корисні навантаження для витоку секретів, блокуються.