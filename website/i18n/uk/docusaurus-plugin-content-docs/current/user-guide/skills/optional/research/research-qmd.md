---
title: "Qmd"
sidebar_label: "Qmd"
description: "Шукай особисті бази знань, нотатки, документи та стенограми зустрічей локально за допомогою qmd — гібридного механізму пошуку з BM25, векторним пошуком та переранжируванням LLM."
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Qmd

Шукай у особистих базах знань, нотатках, документах та транскрипціях зустрічей локально за допомогою **qmd** — гібридного механізму пошуку з BM25, векторним пошуком та переренжируванням LLM. Підтримує CLI та інтеграцію з MCP.
## Метадані навички

| | |
|---|---|
| Джерело | Optional — install with `hermes skills install official/research/qmd` |
| Шлях | `optional-skills/research/qmd` |
| Версія | `1.0.0` |
| Автор | Hermes Agent + Teknium |
| Ліцензія | MIT |
| Платформи | macos, linux |
| Теги | `Search`, `Knowledge-Base`, `RAG`, `Notes`, `MCP`, `Local-AI` |
| Пов’язані навички | [`obsidian`](/docs/user-guide/skills/bundled/note-taking/note-taking-obsidian), [`native-mcp`](/docs/user-guide/skills/bundled/mcp/mcp-native-mcp), [`arxiv`](/docs/user-guide/skills/bundled/research/research-arxiv) |
:::info
Нижче наведено повне визначення **skill**, яке Hermes завантажує, коли цей **skill** активовано. Це те, що агент бачить як інструкції, коли **skill** активний.
:::

# QMD — Query Markup Documents

Локальний пошуковий движок на пристрої для особистих баз знань. Індексує markdown‑нотатки, стенограми зустрічей, документацію та будь‑які текстові файли, а потім забезпечує гібридний пошук, що поєднує збіг ключових слів, семантичне розуміння та переранжування за допомогою LLM — все працює локально без залежностей від хмари.

Створено [Tobi Lütke](https://github.com/tobi/qmd). MIT ліцензія.
## Коли використовувати

- Користувач просить шукати свої нотатки, документи, базу знань або транскрипти зустрічей
- Користувач хоче знайти щось у великій колекції markdown/текстових файлів
- Користувач потребує семантичного пошуку («знайти нотатки про X концепцію»), а не просто пошуку за ключовим словом
- Користувач вже налаштував колекції `qmd` і хоче їх запитувати
- Користувач просить налаштувати локальну базу знань або систему пошуку документів
- Ключові слова: «search my notes», «find in my docs», «knowledge base», «qmd»
## Передумови

### Node.js >= 22 (обов’язково)

```bash
# Check version
node --version  # must be >= 22

# macOS — install or upgrade via Homebrew
brew install node@22

# Linux — use NodeSource or nvm
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs
# or with nvm:
nvm install 22 && nvm use 22
```

### SQLite з підтримкою розширень (лише macOS)

У macOS системний SQLite не підтримує завантаження розширень. Встанови через Homebrew:

```bash
brew install sqlite
```

### Встановити qmd

```bash
npm install -g @tobilu/qmd
# or with Bun:
bun install -g @tobilu/qmd
```

Перший запуск автоматично завантажує 3 локальні моделі GGUF (~2 GB загалом):

| Model | Purpose | Size |
|-------|---------|------|
| embeddinggemma-300M-Q8_0 | Vector embeddings | ~300MB |
| qwen3-reranker-0.6b-q8_0 | Result reranking | ~640MB |
| qmd-query-expansion-1.7B | Query expansion | ~1.1GB |

### Перевірка встановлення

```bash
qmd --version
qmd status
```
## Швидка довідка

| Команда | Що робить | Швидкість |
|---------|-----------|-----------|
| `qmd search "query"` | Пошук BM25 за ключовими словами (без моделей) | ~0.2 s |
| `qmd vsearch "query"` | Семантичний векторний пошук (1 модель) | ~3 s |
| `qmd query "query"` | Гібридний + повторне ранжування (всі 3 моделі) | ~2‑3 s «теплий», ~19 s «холодний» |
| `qmd get <docid>` | Отримати повний вміст документа | миттєво |
| `qmd multi-get "glob"` | Отримати кілька файлів | миттєво |
| `qmd collection add <path> --name <n>` | Додати каталог як колекцію | миттєво |
| `qmd context add <path> "description"` | Додати метадані контексту для покращення пошуку | миттєво |
| `qmd embed` | Генерувати/оновлювати векторні ембеддинги | змінна |
| `qmd status` | Показати стан індексу та інформацію про колекції | миттєво |
| `qmd mcp` | Запустити сервер MCP (stdio) | постійно |
| `qmd mcp --http --daemon` | Запустити сервер MCP (HTTP, «теплі» моделі) | постійно |
## Налаштування робочого процесу

### 1. Додати колекції

Вкажи `qmd` на каталоги, що містять твої документи:

```bash
# Add a notes directory
qmd collection add ~/notes --name notes

# Add project docs
qmd collection add ~/projects/myproject/docs --name project-docs

# Add meeting transcripts
qmd collection add ~/meetings --name meetings

# List all collections
qmd collection list
```

### 2. Додати опис контексту

Метадані контексту допомагають пошуковому движку зрозуміти, що містить кожна колекція. Це значно підвищує якість пошуку:

```bash
qmd context add qmd://notes "Personal notes, ideas, and journal entries"
qmd context add qmd://project-docs "Technical documentation for the main project"
qmd context add qmd://meetings "Meeting transcripts and action items from team syncs"
```

### 3. Створити ембеддинги

```bash
qmd embed
```

Це обробляє всі документи у всіх колекціях і створює векторні ембеддинги. Перезапусти після додавання нових документів або колекцій.

### 4. Перевірити

```bash
qmd status   # shows index health, collection stats, model info
```
## Шаблони пошуку

### Швидкий пошук за ключовими словами (BM25)

Найкраще для: точних термінів, ідентифікаторів коду, імен, відомих фраз.
Не завантажує моделі — майже миттєві результати.

```bash
qmd search "authentication middleware"
qmd search "handleError async"
```

### Семантичний векторний пошук

Найкраще для: питань природною мовою, концептуальних запитів.
Завантажує модель вбудовування (~3 с першого запиту).

```bash
qmd vsearch "how does the rate limiter handle burst traffic"
qmd vsearch "ideas for improving onboarding flow"
```

### Гібридний пошук з повторним ранжируванням (найвища якість)

Найкраще для: важливих запитів, де якість має першорядне значення.
Використовує всі 3 моделі — розширення запиту, паралельний BM25 + вектор, повторне ранжирування.

```bash
qmd query "what decisions were made about the database migration"
```

### Структуровані багатомодальні запити

Комбінуйте різні типи пошуку в одному запиті для точності:

```bash
# BM25 for exact term + vector for concept
qmd query $'lex: rate limiter\nvec: how does throttling work under load'

# With query expansion
qmd query $'expand: database migration plan\nlex: "schema change"'
```

### Синтаксис запиту (режим lex/BM25)

| Синтаксис | Ефект | Приклад |
|-----------|-------|---------|
| `term` | Префіксний збіг | `perf` збігається з “performance” |
| `"phrase"` | Точна фраза | `"rate limiter"` |
| `-term` | Виключити термін | `performance -sports` |

### HyDE (Гіпотетичні вбудовування документів)

Для складних тем напиши те, як ти очікуєш, що виглядатиме відповідь:

```bash
qmd query $'hyde: The migration plan involves three phases. First, we add the new columns without dropping the old ones. Then we backfill data. Finally we cut over and remove legacy columns.'
```

### Обмеження за колекціями

```bash
qmd search "query" --collection notes
qmd query "query" --collection project-docs
```

### Формати виводу

```bash
qmd search "query" --json        # JSON output (best for parsing)
qmd search "query" --limit 5     # Limit results
qmd get "#abc123"                # Get by document ID
qmd get "path/to/file.md"       # Get by file path
qmd get "file.md:50" -l 100     # Get specific line range
qmd multi-get "journals/*.md" --json  # Batch retrieve by glob
```
## Інтеграція MCP (рекомендовано)

qmd надає сервер MCP, який забезпечує інструменти пошуку безпосередньо
Hermes Agent через рідний клієнт MCP. Це переважний
спосіб інтеграції — після налаштування агент отримує інструменти qmd автоматично,
не потребуючи завантажувати цей skill.

### Варіант A: режим Stdio (простий)

Додай до `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  qmd:
    command: "qmd"
    args: ["mcp"]
    timeout: 30
    connect_timeout: 45
```

Це реєструє інструменти: `mcp_qmd_search`, `mcp_qmd_vsearch`,
`mcp_qmd_deep_search`, `mcp_qmd_get`, `mcp_qmd_status`.

**Компроміс:** моделі завантажуються під час першого запиту пошуку (~19 сек холодний старт),
потім залишаються активними протягом сесії. Прийнятно для випадкового використання.

### Варіант B: режим HTTP‑демона (швидко, рекомендовано для інтенсивного використання)

Запусти демон qmd окремо — він тримає моделі в пам’яті:

```bash
# Start daemon (persists across agent restarts)
qmd mcp --http --daemon

# Runs on http://localhost:8181 by default
```

Потім налаштуй Hermes Agent підключатися через HTTP:

```yaml
mcp_servers:
  qmd:
    url: "http://localhost:8181/mcp"
    timeout: 30
```

**Компроміс:** споживає ~2 ГБ ОЗУ під час роботи, але кожен запит виконується швидко
(~2‑3 сек). Найкраще для користувачів, які часто шукають.

### Підтримка роботи демона

#### macOS (launchd)

```bash
cat > ~/Library/LaunchAgents/com.qmd.daemon.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.qmd.daemon</string>
  <key>ProgramArguments</key>
  <array>
    <string>qmd</string>
    <string>mcp</string>
    <string>--http</string>
    <string>--daemon</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>/tmp/qmd-daemon.log</string>
  <key>StandardErrorPath</key>
  <string>/tmp/qmd-daemon.log</string>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.qmd.daemon.plist
```

#### Linux (служба systemd користувача)

```bash
mkdir -p ~/.config/systemd/user

cat > ~/.config/systemd/user/qmd-daemon.service << 'EOF'
[Unit]
Description=QMD MCP Daemon
After=network.target

[Service]
ExecStart=qmd mcp --http --daemon
Restart=on-failure
RestartSec=10
Environment=PATH=/usr/local/bin:/usr/bin:/bin

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now qmd-daemon
systemctl --user status qmd-daemon
```

### Довідник інструментів MCP

Після підключення ці інструменти доступні як `mcp_qmd_*`:

| Інструмент MCP | Відповідає | Опис |
|----------------|-----------|------|
| `mcp_qmd_search` | `qmd search` | BM25 пошук за ключовими словами |
| `mcp_qmd_vsearch` | `qmd vsearch` | семантичний векторний пошук |
| `mcp_qmd_deep_search` | `qmd query` | гібридний пошук + повторне ранжування |
| `mcp_qmd_get` | `qmd get` | отримання документа за ID або шляхом |
| `mcp_qmd_status` | `qmd status` | стан індексу та статистика |

Інструменти MCP приймають структуровані запити JSON для багаторежимного пошуку:

```json
{
  "searches": [
    {"type": "lex", "query": "authentication middleware"},
    {"type": "vec", "query": "how user login is verified"}
  ],
  "collections": ["project-docs"],
  "limit": 10
}
```
## Використання CLI (без MCP)

Коли MCP не налаштовано, використай `qmd` безпосередньо в терміналі:

```
terminal(command="qmd query 'what was decided about the API redesign' --json", timeout=30)
```

Для завдань налаштування та управління завжди використай термінал:

```
terminal(command="qmd collection add ~/Documents/notes --name notes")
terminal(command="qmd context add qmd://notes 'Personal research notes and ideas'")
terminal(command="qmd embed")
terminal(command="qmd status")
```
## Як працює конвеєр пошуку

Розуміння внутрішньої роботи допомагає обрати правильний режим пошуку:

1. **Query Expansion** — Тонко налаштована модель 1.7 B генерує 2 альтернативних запити. Оригінальний запит отримує 2‑х кратну вагу у злитті.
2. **Parallel Retrieval** — BM25 (SQLite FTS5) та векторний пошук працюють одночасно для всіх варіантів запиту.
3. **RRF Fusion** — Reciprocal Rank Fusion (k=60) об’єднує результати. Бонус за верхню позицію: #1 → +0.05, #2‑3 → +0.02.
4. **LLM Reranking** — `qwen3-reranker` оцінює топ‑30 кандидатів (0.0‑1.0).
5. **Position‑Aware Blending** — Ранги 1‑3: 75 % пошук / 25 % повторне ранжування. Ранги 4‑10: 60 % / 40 %. Ранги 11+: 40 % / 60 % (довіряє повторному ранжуванню більше для довгого хвоста).

**Smart Chunking:** Документи розбиваються у природних точках розриву (заголовки, блоки коду, порожні рядки), орієнтуючись на ~900 токенів з 15 % перекриттям. Блоки коду ніколи не розрізаються всередині блоку.
## Кращі практики

1. **Завжди додавай опис контексту** — `qmd context add` значно підвищує точність отримання. Описуй, що містить кожна колекція.
2. **Повторно вбудовуй після додавання документів** — `qmd embed` треба запускати знову, коли до колекцій додаються нові файли.
3. **Використовуй `qmd search` для швидкості** — коли потрібен швидкий пошук за ключовими словами (ідентифікатори коду, точні назви), BM25 працює миттєво і не потребує моделей.
4. **Використовуй `qmd query` для якості** — коли питання концептуальне або користувачеві потрібні найкращі результати, застосовуй гібридний пошук.
5. **Надавай перевагу інтеграції MCP** — після налаштування агент отримує вбудовані інструменти без необхідності завантажувати цей навик щоразу.
6. **Режим демона для частих користувачів** — якщо користувач регулярно шукає у своїй базі знань, рекомендуй налаштування HTTP‑демона.
7. **Перший запит у структурованому пошуку має 2× вагу** — розмісти найважливіший/найбільш впевнений запит першим, коли комбінуєш lex і vec.
## Усунення проблем

### «Моделі завантажуються під час першого запуску»
Нормально — `qmd` автоматично завантажує ~2 ГБ моделей GGUF під час першого використання. Це одноразова операція.

### Затримка холодного запуску (~19 сек)
Така затримка виникає, коли моделі не завантажені в пам’ять. Рішення:
- Використовуй режим HTTP‑демона (`qmd mcp --http --daemon`), щоб тримати їх «теплими»
- Використовуй `qmd search` (лише BM25), коли моделі не потрібні
- MCP у режимі `stdio` завантажує моделі під час першого пошуку і тримає їх «теплими» протягом сесії

### macOS: «не вдається завантажити розширення»
Встанови SQLite через Homebrew: `brew install sqlite`
Потім переконайся, що вона є в `PATH` перед системним SQLite.

### «Колекції не знайдено»
Виконай `qmd collection add <path> --name <name>`, щоб додати каталоги,
потім `qmd embed` для їх індексації.

### Перевизначення моделі вбудовування (CJK/багатомовний)
Встанови змінну середовища `QMD_EMBED_MODEL` для контенту не англійською мовою:
```bash
export QMD_EMBED_MODEL="your-multilingual-model"
```
## Зберігання даних

- **Індекс і вектори:** `~/.cache/qmd/index.sqlite`
- **Моделі:** Автоматично завантажуються у локальний кеш під час першого запуску
- **Без хмарних залежностей** — все працює локально
## Посилання

- [GitHub: tobi/qmd](https://github.com/tobi/qmd)
- [QMD Changelog](https://github.com/tobi/qmd/blob/main/CHANGELOG.md)