---
sidebar_position: 11
title: "Внутрішні механізми Cron"
description: "Як Hermes зберігає, планує, редагує, призупиняє, завантажує навички та виконує cron‑завдання"
---

# Внутрішня робота Cron

Підсистема cron забезпечує планове виконання завдань — від простих одноразових затримок до повторюваних завдань за cron‑виразом із ін’єкцією skill та крос‑платформенною доставкою.

## Ключові файли

| Файл | Призначення |
|------|--------------|
| `cron/jobs.py` | Модель завдання, сховище, атомарне читання/запис у `jobs.json` |
| `cron/scheduler.py` | Цикл планувальника — виявлення готових завдань, виконання, відстеження повторень |
| `tools/cronjob_tools.py` | Реєстрація та обробка інструмента `cronjob` на рівні моделі |
| `gateway/run.py` | Інтеграція шлюзу — тикання cron у довготривалому циклі |
| `hermes_cli/cron.py` | Підкоманди CLI `hermes cron` |

## Модель планування

Підтримуються чотири формати розкладу:

| Формат | Приклад | Поведінка |
|--------|---------|----------|
| **Відносна затримка** | `30m`, `2h`, `1d` | Одноразово, спрацьовує після зазначеної тривалості |
| **Інтервал** | `every 2h`, `every 30m` | Повторювано, спрацьовує через регулярні інтервали |
| **Cron‑вираз** | `0 9 * * *` | Стандартний 5‑полеовий синтаксис cron (хвилина, година, день, місяць, день тижня) |
| **ISO‑таймстамп** | `2025-01-15T09:00:00` | Одноразово, спрацьовує у точний час |

Поверхня, що працює з моделлю, — це єдиний інструмент `cronjob` з діями: `create`, `list`, `update`, `pause`, `resume`, `run`, `remove`.

## Зберігання завдань

Завдання зберігаються у `~/.hermes/cron/jobs.json` з атомарною семантикою запису (запис у тимчасовий файл, потім перейменування). Кожен запис завдання містить:

```json
{
  "id": "a1b2c3d4e5f6",
  "name": "Daily briefing",
  "prompt": "Summarize today's AI news and funding rounds",
  "schedule": {
    "kind": "cron",
    "expr": "0 9 * * *",
    "display": "0 9 * * *"
  },
  "skills": ["ai-funding-daily-report"],
  "deliver": "telegram:-1001234567890",
  "repeat": {
    "times": null,
    "completed": 42
  },
  "state": "scheduled",
  "enabled": true,
  "next_run_at": "2025-01-16T09:00:00Z",
  "last_run_at": "2025-01-15T09:00:00Z",
  "last_status": "ok",
  "created_at": "2025-01-01T00:00:00Z",
  "model": null,
  "provider": null,
  "script": null
}
```

### Стани життєвого циклу завдання

| Стан | Значення |
|------|----------|
| `scheduled` | Активний, спрацює у наступний запланований час |
| `paused` | Призупинений — не спрацює, доки не буде відновлений |
| `completed` | Вичерпано кількість повторень або одноразове завдання вже спрацювало |
| `running` | Поточне виконання (транзиторний стан) |

### Зворотна сумісність

У старих завдань може бути одне поле `skill` замість масиву `skills`. Планувальник нормалізує це під час завантаження — одиничний `skill` підвищується до `skills: [skill]`.

## Робочий час планувальника

### Цикл тика

Планувальник працює за періодичним тиком (за замовчуванням: кожні 60 секунд):

```text
tick()
  1. Acquire scheduler lock (prevents overlapping ticks)
  2. Load all jobs from jobs.json
  3. Filter to due jobs (next_run <= now AND state == "scheduled")
  4. For each due job:
     a. Set state to "running"
     b. Create fresh AIAgent session (no conversation history)
     c. Load attached skills in order (injected as user messages)
     d. Run the job prompt through the agent
     e. Deliver the response to the configured target
     f. Update run_count, compute next_run
     g. If repeat count exhausted → state = "completed"
     h. Otherwise → state = "scheduled"
  5. Write updated jobs back to jobs.json
  6. Release scheduler lock
```

### Інтеграція шлюзу

У режимі шлюзу планувальник працює у виділеному фонового потоці (`_start_cron_ticker` у `gateway/run.py`), який викликає `scheduler.tick()` кожні 60 секунд разом із обробкою повідомлень.

У режимі CLI завдання cron спрацьовують лише коли виконуються команди `hermes cron` або під час активних CLI‑сесій.

### Ізоляція нової сесії

Кожне завдання cron запускається у повністю новій сесії агента:

- Немає історії розмов з попередніх запусків
- Немає пам’яті про попередні виконання cron (хіба що збережено у пам’яті/файлах)
- Промпт має бути самодостатнім — завдання cron не можуть ставити уточнюючі питання
- Набір інструментів `cronjob` вимкнено (захист від рекурсії)

## Завдання, підкріплені skill

Завдання cron може приєднувати один або кілька skill через поле `skills`. Під час виконання:

1. Skill завантажуються у зазначеному порядку
2. Вміст кожного `SKILL.md` ін’єкціюється як контекст
3. Промпт завдання додається як інструкція завдання
4. Агент обробляє комбінований контекст skill + промпт

Це дозволяє створювати повторно використовувані, протестовані робочі процеси без копіювання повних інструкцій у промпти cron. Наприклад:

```
Create a daily funding report → attach "ai-funding-daily-report" skill
```

### Завдання, підкріплені скриптом

Завдання можуть також приєднувати Python‑скрипт через поле `script`. Скрипт виконується *перед* кожним ходом агента, а його stdout ін’єкціюється у промпт як контекст. Це дозволяє збирати дані та виявляти зміни:

```python
# ~/.hermes/scripts/check_competitors.py
import requests, json
# Fetch competitor release notes, diff against last run
# Print summary to stdout — agent analyzes and reports
```

Тайм‑аут скрипту за замовчуванням — 120 секунд. `_get_script_timeout()` визначає ліміт через трирівневий ланцюжок:

1. **Перевизначення на рівні модуля** — `_SCRIPT_TIMEOUT` (для тестів/мок‑патчінгу). Використовується лише коли відрізняється від значення за замовчуванням.
2. **Змінна середовища** — `HERMES_CRON_SCRIPT_TIMEOUT`
3. **Конфіг** — `cron.script_timeout_seconds` у `config.yaml` (читається через `load_config()`)
4. **За замовчуванням** — 120 секунд

### Відновлення провайдера

`run_job()` передає користувачем налаштовані запасні провайдери та пул облікових даних у екземпляр `AIAgent`:

- **Запасні провайдери** — читає `fallback_providers` (list) або `fallback_model` (legacy dict) з `config.yaml`, згідно з шаблоном `_load_fallback_model()` шлюзу. Передається як `fallback_model=` у `AIAgent.__init__`, який нормалізує обидва формати у ланцюжок запасних провайдерів.
- **Пул облікових даних** — завантажується через `load_pool(provider)` з `agent.credential_pool` за розв’язаним ім’ям провайдера під час виконання. Передається лише коли пул містить облікові дані (`pool.has_credentials()`). Дозволяє ротацію ключа того ж провайдера при помилках 429/rate‑limit.

Це відтворює поведінку шлюзу — без цього агенти cron зазнавали б збою при обмеженнях без спроби відновлення.

## Модель доставки

Результати завдань cron можуть доставлятися на будь‑яку підтримувану платформу:

| Ціль | Синтаксис | Приклад |
|------|-----------|---------|
| Чат‑джерело | `origin` | Доставити у чат, де створено завдання |
| Локальний файл | `local` | Зберегти у `~/.hermes/cron/output/` |
| Telegram | `telegram` або `telegram:<chat_id>` | `telegram:-1001234567890` |
| Discord | `discord` або `discord:#channel` | `discord:#engineering` |
| Slack | `slack` | Доставити у домашній канал Slack |
| WhatsApp | `whatsapp` | Доставити у WhatsApp home |
| Signal | `signal` | Доставити у Signal |
| Matrix | `matrix` | Доставити у Matrix home room |
| Mattermost | `mattermost` | Доставити у Mattermost home |
| Email | `email` | Доставити електронною поштою |
| SMS | `sms` | Доставити через SMS |
| Home Assistant | `homeassistant` | Доставити у розмову HA |
| DingTalk | `dingtalk` | Доставити у DingTalk |
| Feishu | `feishu` | Доставити у Feishu |
| WeCom | `wecom` | Доставити у WeCom |
| Weixin | `weixin` | Доставити у Weixin (WeChat) |
| BlueBubbles | `bluebubbles` | Доставити у iMessage через BlueBubbles |
| QQ Bot | `qqbot` | Доставити у QQ (Tencent) через Official API v2 |

Для тем Telegram використовуйте формат `telegram:<chat_id>:<thread_id>` (наприклад, `telegram:-1001234567890:17585`).

### Обгортка відповіді

За замовчуванням (`cron.wrap_response: true`) доставки cron обгортаються:

- Заголовком, що ідентифікує назву та задачу cron‑завдання
- Нижнім колонтитулом, що зазначає, що агент не бачить доставлене повідомлення у розмові

Префікс `[SILENT]` у відповіді cron повністю придушує доставку — корисно для завдань, які лише записують у файли або виконують побічні ефекти.

### Ізоляція сесії

Доставки cron **не** дублюються у історії розмов шлюзу. Вони існують лише у власній сесії завдання cron. Це запобігає порушенням чергування повідомлень у цільовому чаті.

## Захист від рекурсії

У сесіях, запущених cron, набір інструментів `cronjob` вимкнено. Це запобігає:

- Плануваному завданню створювати нові cron‑завдання
- Рекурсивному плануванню, яке могло б вибухнути у використанні токенів
- Випадковій модифікації розкладу завдань зсередини завдання

## Блокування

Планувальник використовує міжпроцесне файлове блокування (`fcntl.flock` на Unix, `msvcrt.locking` на Windows), щоб запобігти одночасному виконанню одного й того ж пакету готових завдань двічі — навіть між тикером шлюзу в процесі та окремим викликом `hermes cron` / ручним викликом `tick()`. Якщо блокування не вдається отримати, `tick()` негайно повертає `0`.

## Інтерфейс CLI

CLI `hermes cron` надає пряме керування завданнями:

```bash
hermes cron list                    # Show all jobs
hermes cron create                  # Interactive job creation (alias: add)
hermes cron edit <job_id>           # Edit job configuration
hermes cron pause <job_id>          # Pause a running job
hermes cron resume <job_id>         # Resume a paused job
hermes cron run <job_id>            # Trigger immediate execution
hermes cron remove <job_id>         # Delete a job
```

## Пов’язані документи

- [Cron Feature Guide](/user-guide/features/cron)
- [Gateway Internals](./gateway-internals.md)
- [Agent Loop Internals](./agent-loop.md)