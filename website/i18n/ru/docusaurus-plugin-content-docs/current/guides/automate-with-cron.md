---
sidebar_position: 11
title: "Автоматизируй всё с помощью Cron"
description: "Реальные шаблоны автоматизации с использованием Hermes cron — мониторинг, отчёты, конвейеры и многозадачные рабочие процессы"
---

# Автоматизируй всё с помощью Cron

[Учебник по боту ежедневных брифингов](/guides/daily-briefing-bot) охватывает основы. Это руководство идёт дальше — пять реальных шаблонов автоматизации, которые ты можешь адаптировать под свои рабочие процессы.

Для полного справочника по возможностям смотри [Запланированные задачи (Cron)](/user-guide/features/cron).

:::info Ключевая идея
Cron‑задачи запускаются в новых сессиях агента без памяти о текущем чате. Промпты должны быть **полностью автономными** — включать всё, что агенту нужно знать.
:::

:::tip Не нужен LLM? У тебя есть два варианта без токенов.
- **Регулярный наблюдатель**, когда скрипт уже генерирует точное сообщение (оповещения о памяти, оповещения о диске, сигналы жизни): используй [cron‑задачи только со скриптом](/guides/cron-script-only). Тот же планировщик, без LLM. Ты можешь попросить Hermes настроить её в чате — инструмент `cronjob` знает, когда выбрать `no_agent=True`, и пишет скрипт за тебя.
- **Одноразовый запуск из уже работающего скрипта** (шаг CI, post‑commit hook, скрипт деплоя, внешне запланированный монитор): используй [`hermes send`](/guides/pipe-script-output), чтобы передать stdout или файл напрямую в Telegram / Discord / Slack / и т.д. без создания записи в cron.
:::

---

## Шаблон 1: Мониторинг изменений сайта

Отслеживай URL на предмет изменений и получай уведомление только когда что‑то изменилось.

Параметр `script` здесь — секретное оружие. Python‑скрипт запускается перед каждым выполнением, а его stdout становится контекстом для агента. Скрипт занимается механической работой (запросы, сравнение); агент — рассуждениями (интересно ли это изменение?).

Создай скрипт мониторинга:

```bash
mkdir -p ~/.hermes/scripts
```

```python title="~/.hermes/scripts/watch-site.py"
import hashlib, json, os, urllib.request

URL = "https://example.com/pricing"
STATE_FILE = os.path.expanduser("~/.hermes/scripts/.watch-site-state.json")

# Fetch current content
req = urllib.request.Request(URL, headers={"User-Agent": "Hermes-Monitor/1.0"})
content = urllib.request.urlopen(req, timeout=30).read().decode()
current_hash = hashlib.sha256(content.encode()).hexdigest()

# Load previous state
prev_hash = None
if os.path.exists(STATE_FILE):
    with open(STATE_FILE) as f:
        prev_hash = json.load(f).get("hash")

# Save current state
with open(STATE_FILE, "w") as f:
    json.dump({"hash": current_hash, "url": URL}, f)

# Output for the agent
if prev_hash and prev_hash != current_hash:
    print(f"CHANGE DETECTED on {URL}")
    print(f"Previous hash: {prev_hash}")
    print(f"Current hash: {current_hash}")
    print(f"\nCurrent content (first 2000 chars):\n{content[:2000]}")
else:
    print("NO_CHANGE")
```

Настрой cron‑задачу:

```bash
/cron add "every 1h" "If the script output says CHANGE DETECTED, summarize what changed on the page and why it might matter. If it says NO_CHANGE, respond with just [SILENT]." --script ~/.hermes/scripts/watch-site.py --name "Pricing monitor" --deliver telegram
```

:::tip Трюк [SILENT]
Когда окончательный ответ агента содержит `[SILENT]`, доставка подавляется. Это значит, что ты получаешь уведомление только при реальном событии — без спама в тихие часы.
:::

---

## Шаблон 2: Еженедельный отчёт

Собери информацию из разных источников в отформатированное резюме. Выполняется раз в неделю и отправляется в твой основной канал.

```bash
/cron add "0 9 * * 1" "Generate a weekly report covering:

1. Search the web for the top 5 AI news stories from the past week
2. Search GitHub for trending repositories in the 'machine-learning' topic
3. Check Hacker News for the most discussed AI/ML posts

Format as a clean summary with sections for each source. Include links.
Keep it under 500 words — highlight only what matters." --name "Weekly AI digest" --deliver telegram
```

Из CLI:

```bash
hermes cron create "0 9 * * 1" \
  "Generate a weekly report covering the top AI news, trending ML GitHub repos, and most-discussed HN posts. Format with sections, include links, keep under 500 words." \
  --name "Weekly AI digest" \
  --deliver telegram
```

`0 9 * * 1` — стандартное cron‑выражение: 9:00 утра каждый понедельник.

---

## Шаблон 3: Наблюдатель репозитория GitHub

Отслеживай репозиторий на предмет новых issue, PR или релизов.

```bash
/cron add "every 6h" "Check the GitHub repository NousResearch/hermes-agent for:
- New issues opened in the last 6 hours
- New PRs opened or merged in the last 6 hours
- Any new releases

Use the terminal to run gh commands:
  gh issue list --repo NousResearch/hermes-agent --state open --json number,title,author,createdAt --limit 10
  gh pr list --repo NousResearch/hermes-agent --state all --json number,title,author,createdAt,mergedAt --limit 10

Filter to only items from the last 6 hours. If nothing new, respond with [SILENT].
Otherwise, provide a concise summary of the activity." --name "Repo watcher" --deliver discord
```

:::warning Автономные промпты
Обрати внимание, что в промпте указаны точные команды `gh`. У cron‑агента нет памяти о предыдущих запусках или твоих предпочтениях — всё нужно явно прописать.
:::

---

## Шаблон 4: Конвейер сбора данных

Собирай данные через регулярные интервалы, сохраняй в файлы и выявляй тренды со временем. Этот шаблон сочетает скрипт (для сбора) с агентом (для анализа).

```python title="~/.hermes/scripts/collect-prices.py"
import json, os, urllib.request
from datetime import datetime

DATA_DIR = os.path.expanduser("~/.hermes/data/prices")
os.makedirs(DATA_DIR, exist_ok=True)

# Fetch current data (example: crypto prices)
url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd"
data = json.loads(urllib.request.urlopen(url, timeout=30).read())

# Append to history file
entry = {"timestamp": datetime.now().isoformat(), "prices": data}
history_file = os.path.join(DATA_DIR, "history.jsonl")
with open(history_file, "a") as f:
    f.write(json.dumps(entry) + "\n")

# Load recent history for analysis
lines = open(history_file).readlines()
recent = [json.loads(l) for l in lines[-24:]]  # Last 24 data points

# Output for the agent
print(f"Current: BTC=${data['bitcoin']['usd']}, ETH=${data['ethereum']['usd']}")
print(f"Data points collected: {len(lines)} total, showing last {len(recent)}")
print(f"\nRecent history:")
for r in recent[-6:]:
    print(f"  {r['timestamp']}: BTC=${r['prices']['bitcoin']['usd']}, ETH=${r['prices']['ethereum']['usd']}")
```

```bash
/cron add "every 1h" "Analyze the price data from the script output. Report:
1. Current prices
2. Trend direction over the last 6 data points (up/down/flat)
3. Any notable movements (>5% change)

If prices are flat and nothing notable, respond with [SILENT].
If there's a significant move, explain what happened." \
  --script ~/.hermes/scripts/collect-prices.py \
  --name "Price tracker" \
  --deliver telegram
```

Скрипт выполняет механический сбор; агент добавляет слой рассуждений.

---

## Шаблон 5: Многоуровневый рабочий процесс

Последовательно вызывай навыки для сложных запланированных задач. Навыки загружаются в порядке, указанном перед выполнением промпта.

```bash
# Use the arxiv skill to find papers, then the obsidian skill to save notes
/cron add "0 8 * * *" "Search arXiv for the 3 most interesting papers on 'language model reasoning' from the past day. For each paper, create an Obsidian note with the title, authors, abstract summary, and key contribution." \
  --skill arxiv \
  --skill obsidian \
  --name "Paper digest"
```

Непосредственно из инструмента:

```python
cronjob(
    action="create",
    skills=["arxiv", "obsidian"],
    prompt="Search arXiv for papers on 'language model reasoning' from the past day. Save the top 3 as Obsidian notes.",
    schedule="0 8 * * *",
    name="Paper digest",
    deliver="local"
)
```

Навыки загружаются по порядку — сначала `arxiv` (обучает агента искать статьи), затем `obsidian` (обучает писать заметки). Промпт связывает их вместе.

---

## Управление задачами

```bash
# List all active jobs
/cron list

# Trigger a job immediately (for testing)
/cron run <job_id>

# Pause a job without deleting it
/cron pause <job_id>

# Edit a running job's schedule or prompt
/cron edit <job_id> --schedule "every 4h"
/cron edit <job_id> --prompt "Updated task description"

# Add or remove skills from an existing job
/cron edit <job_id> --skill arxiv --skill obsidian
/cron edit <job_id> --clear-skills

# Remove a job permanently
/cron remove <job_id>
```

---

## Цели доставки

Флаг `--deliver` определяет, куда отправляются результаты:

| Target | Example | Use case |
|--------|---------|----------|
| `origin` | `--deliver origin` | Тот же чат, в котором создана задача (по умолчанию) |
| `local` | `--deliver local` | Сохранить только в локальный файл |
| `telegram` | `--deliver telegram` | Твой основной канал в Telegram |
| `discord` | `--deliver discord` | Твой основной канал в Discord |
| `slack` | `--deliver slack` | Твой основной канал в Slack |
| Specific chat | `--deliver telegram:-1001234567890` | Конкретная группа Telegram |
| Threaded | `--deliver telegram:-1001234567890:17585` | Конкретная ветка темы в Telegram |

---

## Советы

**Делай промпты автономными.** Агент в cron‑задаче не помнит твои разговоры. Включай URL, имена репозиториев, предпочтения формата и инструкции по доставке прямо в промпт.

**Активно используй `[SILENT]`.** Для мониторинговых задач всегда добавляй инструкцию вроде «если ничего не изменилось, ответь `[SILENT]`». Это избавит от лишних уведомлений.

**Применяй скрипты для сбора данных.** Параметр `script` позволяет Python‑скрипту выполнять скучные части (HTTP‑запросы, работа с файлами, отслеживание состояния). Агент видит только stdout скрипта и применяет к нему рассуждения. Это дешевле и надёжнее, чем заставлять агента делать запросы самостоятельно.

**Тестируй с `/cron run`.** Прежде чем ждать планового запуска, используй `/cron run <job_id>`, чтобы выполнить задачу сразу и убедиться, что вывод выглядит правильно.

**Выражения расписания.** Поддерживаемые форматы: относительные задержки (`30m`), интервалы (`every 2h`), стандартные cron‑выражения (`0 9 * * *`) и ISO‑таймстемпы (`2025-06-15T09:00:00`). Естественный язык вроде `daily at 9am` не поддерживается — используй `0 9 * * *` вместо него.

---

*Для полного справочника по cron — все параметры, граничные случаи и внутренности — смотри [Запланированные задачи (Cron)](/user-guide/features/cron).*