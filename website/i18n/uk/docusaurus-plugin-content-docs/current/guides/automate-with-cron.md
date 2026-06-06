---
sidebar_position: 11
title: "Автоматизуй будь‑що за допомогою Cron"
description: "Реальні шаблони автоматизації з використанням Hermes cron — моніторинг, звіти, конвеєри та багатоскiльні робочі процеси"
---

# Автоматизуй будь‑що за допомогою Cron

[Посібник зі створення щоденного бота‑брифінгу](/guides/daily-briefing-bot) охоплює основи. Цей посібник йде далі — п’ять реальних шаблонів автоматизації, які ти можеш адаптувати під свої робочі процеси.

Для повного довідника з функціями дивись [Заплановані завдання (Cron)](/user-guide/features/cron).

:::info Ключова концепція
Cron‑завдання виконуються у нових сесіях агента без пам’яті про твою поточну розмову. Промпти мають бути **повністю самодостатніми** — включай усе, що агенту потрібно знати.
:::

:::tip Не потрібен LLM? У тебе є два варіанти без токенів.
- **Повторюваний watchdog**, коли скрипт вже генерує точне повідомлення (повідомлення про пам’ять, попередження про диск, heartbeat): використай [cron‑завдання лише зі скриптом](/guides/cron-script-only). Той самий планувальник, без LLM. Ти можеш попросити Hermes налаштувати його в чаті — інструмент `cronjob` знає, коли обрати `no_agent=True`, і пише скрипт за тебе.
- **Одноразовий запуск зі скриптом, який вже працює** (крок CI, post‑commit hook, скрипт розгортання, зовнішньо запланований монітор): використай [`hermes send`](/guides/pipe-script-output), щоб передати stdout або файл безпосередньо в Telegram / Discord / Slack тощо, без створення запису в cron.
:::

---

## Шаблон 1: Моніторинг змін на веб‑сайті

Слідкуй за URL‑адресою і отримуй сповіщення лише коли щось змінилося.

Параметр `script` — це секретна зброя. Python‑скрипт виконується перед кожним запуском, а його stdout стає контекстом для агента. Скрипт виконує механічну роботу (завантаження, порівняння); агент — розмірковує (чи цікава ця зміна?).

Створи скрипт моніторингу:

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

Налаштуй cron‑завдання:

```bash
/cron add "every 1h" "If the script output says CHANGE DETECTED, summarize what changed on the page and why it might matter. If it says NO_CHANGE, respond with just [SILENT]." --script ~/.hermes/scripts/watch-site.py --name "Pricing monitor" --deliver telegram
```

:::tip Трюк [SILENT]
Коли остаточна відповідь агента містить `[SILENT]`, доставка придушується. Це означає, що ти отримуєш сповіщення лише коли щось дійсно сталося — без спаму в тихі години.
:::

---

## Шаблон 2: Щотижневий звіт

Збирай інформацію з кількох джерел у відформатовану підсумкову нотатку. Це виконується раз на тиждень і надсилається у твій домашній канал.

```bash
/cron add "0 9 * * 1" "Generate a weekly report covering:

1. Search the web for the top 5 AI news stories from the past week
2. Search GitHub for trending repositories in the 'machine-learning' topic
3. Check Hacker News for the most discussed AI/ML posts

Format as a clean summary with sections for each source. Include links.
Keep it under 500 words — highlight only what matters." --name "Weekly AI digest" --deliver telegram
```

З CLI:

```bash
hermes cron create "0 9 * * 1" \
  "Generate a weekly report covering the top AI news, trending ML GitHub repos, and most-discussed HN posts. Format with sections, include links, keep under 500 words." \
  --name "Weekly AI digest" \
  --deliver telegram
```

`0 9 * * 1` — стандартний cron‑вираз: 9:00 ранку кожного понеділка.

---

## Шаблон 3: Спостерігач репозиторію GitHub

Слідкуй за новими issue, PR чи релізами у репозиторії.

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

:::warning Самодостатні промпти
Зверни увагу, що промпт містить точні команди `gh`. Cron‑агент не має пам’яті про попередні запуски чи твої уподобання — все треба прописати явно.
:::

---

## Шаблон 4: Конвеєр збору даних

Збирай дані регулярно, зберігай у файлах і виявляй тенденції з часом. Цей шаблон поєднує скрипт (для збору) з агентом (для аналізу).

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

Скрипт виконує механічний збір; агент додає шар розмірковування.

---

## Шаблон 5: Робочий процес з кількома навичками

Ланцюжок навичок для складних запланованих завдань. Навички завантажуються у порядку перед виконанням промпту.

```bash
# Use the arxiv skill to find papers, then the obsidian skill to save notes
/cron add "0 8 * * *" "Search arXiv for the 3 most interesting papers on 'language model reasoning' from the past day. For each paper, create an Obsidian note with the title, authors, abstract summary, and key contribution." \
  --skill arxiv \
  --skill obsidian \
  --name "Paper digest"
```

Безпосередньо інструментом:

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

Навички завантажуються послідовно — спочатку `arxiv` (вчить агента шукати статті), потім `obsidian` (вчить писати нотатки). Промпт об’єднує їх.

---

## Керування твоїми завданнями

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

## Цілі доставки

Параметр `--deliver` визначає, куди надходять результати:

| Ціль | Приклад | Випадок використання |
|--------|---------|----------------------|
| `origin` | `--deliver origin` | Той самий чат, у якому створено завдання (за замовчуванням) |
| `local` | `--deliver local` | Зберегти лише у локальний файл |
| `telegram` | `--deliver telegram` | Твій домашній канал у Telegram |
| `discord` | `--deliver discord` | Твій домашній канал у Discord |
| `slack` | `--deliver slack` | Твій домашній канал у Slack |
| Конкретний чат | `--deliver telegram:-1001234567890` | Окрема група Telegram |
| Тема в гілці | `--deliver telegram:-1001234567890:17585` | Конкретна тема в Telegram |

---

## Поради

**Роби промпти самодостатніми.** Агент у cron‑завданні не пам’ятає твої розмови. Включай URL‑адреси, назви репозиторіїв, уподобання форматування та інструкції щодо доставки безпосередньо у промпт.

**Використовуй `[SILENT]` щедро.** Для моніторингових завдань завжди додавай інструкції типу «якщо нічого не змінилося, відповісти `[SILENT]`». Це запобігає зайвому шуму.

**Використовуй скрипти для збору даних.** Параметр `script` дозволяє Python‑скрипту виконати нудні частини (HTTP‑запити, робота з файлами, відстеження стану). Агент бачить лише stdout скрипту і застосовує розмірковування. Це дешевше і надійніше, ніж змушувати агента робити запити самостійно.

**Тестуй за допомогою `/cron run`.** Перш ніж чекати, коли розклад запустить завдання, використай `/cron run <job_id>`, щоб виконати його одразу і переконатися, що результат правильний.

**Вирази розкладу.** Підтримувані формати: відносні затримки (`30m`), інтервали (`every 2h`), стандартні cron‑вирази (`0 9 * * *`), ISO‑таймстампи (`2025-06-15T09:00:00`). Натуральна мова типу `daily at 9am` не підтримується — використай `0 9 * * *`.

---

*Для повного довідника з cron — усі параметри, крайні випадки та внутрішні механізми — дивись [Заплановані завдання (Cron)](/user-guide/features/cron).*