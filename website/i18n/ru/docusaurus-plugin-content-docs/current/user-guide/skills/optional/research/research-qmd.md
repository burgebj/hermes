---
title: "Qmd"
sidebar_label: "Qmd"
description: "Ищи персональные базы знаний, заметки, документы и стенограммы встреч локально с помощью qmd — гибридного поискового движка с BM25, векторным поиском и переранжированием LLM"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Qmd

Ищи в личных базах знаний, заметках, документах и расшифровках встреч локально с помощью **qmd** — гибридного поискового движка с BM25, векторным поиском и переранжированием LLM. Поддерживает CLI и интеграцию с MCP.
## Метаданные навыка

| | |
|---|---|
| Источник | Опционально — установить с помощью `hermes skills install official/research/qmd` |
| Путь | `optional-skills/research/qmd` |
| Версия | `1.0.0` |
| Автор | Hermes Agent + Teknium |
| Лицензия | MIT |
| Платформы | macos, linux |
| Теги | `Search`, `Knowledge-Base`, `RAG`, `Notes`, `MCP`, `Local-AI` |
| Связанные навыки | [`obsidian`](/docs/user-guide/skills/bundled/note-taking/note-taking-obsidian), [`native-mcp`](/docs/user-guide/skills/bundled/mcp/mcp-native-mcp), [`arxiv`](/docs/user-guide/skills/bundled/research/research-arxiv) |
:::info
Следующий текст — полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции во время работы навыка.
:::

# QMD — Query Markup Documents

Локальная поисковая система на устройстве для персональных баз знаний. Индексирует markdown‑заметки, стенограммы встреч, документацию и любые текстовые файлы, затем предоставляет гибридный поиск, объединяющий совпадения по ключевым словам, семантическое понимание и пере‑ранжирование с помощью LLM — всё работает локально без облачных зависимостей.

Создано [Tobi Lütke](https://github.com/tobi/qmd). MIT‑лицензия.
## Когда использовать

- Пользователь просит искать свои заметки, документы, базу знаний или стенограммы встреч
- Пользователь хочет найти что‑то в большой коллекции файлов **markdown**/текстовых файлов
- Пользователь нуждается в семантическом поиске («найти заметки о концепте X»), а не просто в поиске по ключевому слову
- Пользователь уже настроил коллекции **qmd** и хочет делать запросы к ним
- Пользователь просит настроить локальную базу знаний или систему поиска по документам
- Ключевые слова: «search my notes», «find in my docs», «knowledge base», «qmd»
## Предварительные требования

### Node.js >= 22 (обязательно)

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

### SQLite с поддержкой расширений (только macOS)

В системной SQLite macOS отсутствует возможность загружать расширения. Установи её через Homebrew:

```bash
brew install sqlite
```

### Установить qmd

```bash
npm install -g @tobilu/qmd
# or with Bun:
bun install -g @tobilu/qmd
```

При первом запуске автоматически загружаются 3 локальные модели GGUF (~2 GB всего):

| Модель | Назначение | Размер |
|-------|------------|--------|
| embeddinggemma-300M-Q8_0 | Векторные эмбеддинги | ~300 MB |
| qwen3-reranker-0.6b-q8_0 | Перерангирование результатов | ~640 MB |
| qmd-query-expansion-1.7B | Расширение запросов | ~1.1 GB |

### Проверка установки

```bash
qmd --version
qmd status
```
## Быстрая справка

| Команда | Что делает | Скорость |
|---------|------------|----------|
| `qmd search "query"` | Поиск BM25 по ключевым словам (без моделей) | ~0.2 s |
| `qmd vsearch "query"` | Семантический векторный поиск (1 модель) | ~3 s |
| `qmd query "query"` | Гибридный поиск + переранжирование (все 3 модели) | ~2‑3 s при прогреве, ~19 s без прогрева |
| `qmd get <docid>` | Получить полное содержимое документа | мгновенно |
| `qmd multi-get "glob"` | Получить несколько файлов | мгновенно |
| `qmd collection add <path> --name <n>` | Добавить каталог в качестве коллекции | мгновенно |
| `qmd context add <path> "description"` | Добавить метаданные контекста для улучшения извлечения | мгновенно |
| `qmd embed` | Сгенерировать/обновить векторные эмбеддинги | зависит |
| `qmd status` | Показать состояние индекса и информацию о коллекциях | мгновенно |
| `qmd mcp` | Запустить сервер MCP (stdio) | постоянно |
| `qmd mcp --http --daemon` | Запустить сервер MCP (HTTP, прогретые модели) | постоянно |
## Настройка рабочего процесса

### 1. Добавление коллекций

Укажи qmd на каталоги, содержащие твои документы:

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

### 2. Добавление описаний контекста

Метаданные контекста помогают поисковому движку понять, что содержит каждая коллекция. Это значительно повышает качество извлечения:

```bash
qmd context add qmd://notes "Personal notes, ideas, and journal entries"
qmd context add qmd://project-docs "Technical documentation for the main project"
qmd context add qmd://meetings "Meeting transcripts and action items from team syncs"
```

### 3. Генерация эмбеддингов

```bash
qmd embed
```

Этот процесс обрабатывает все документы во всех коллекциях и генерирует векторные эмбеддинги. Запусти процесс повторно после добавления новых документов или коллекций.

### 4. Проверка

```bash
qmd status   # shows index health, collection stats, model info
```
## Поисковые шаблоны

### Быстрый поиск по ключевым словам (BM25)

Лучше всего для: точных терминов, идентификаторов кода, имён, известных фраз.
Без загрузки моделей — почти мгновенные результаты.

```bash
qmd search "authentication middleware"
qmd search "handleError async"
```

### Семантический векторный поиск

Лучше всего для: вопросов на естественном языке, концептуальных запросов.
Загружает модель эмбеддингов (~3 с при первом запросе).

```bash
qmd vsearch "how does the rate limiter handle burst traffic"
qmd vsearch "ideas for improving onboarding flow"
```

### Гибридный поиск с переранжированием (наилучшее качество)

Лучше всего для: важных запросов, где качество имеет решающее значение.
Использует все 3 модели — расширение запроса, параллельный BM25 + вектор, переранжирование.

```bash
qmd query "what decisions were made about the database migration"
```

### Структурированные запросы в нескольких режимах

Комбинируй разные типы поиска в одном запросе для точности:

```bash
# BM25 for exact term + vector for concept
qmd query $'lex: rate limiter\nvec: how does throttling work under load'

# With query expansion
qmd query $'expand: database migration plan\nlex: "schema change"'
```

### Синтаксис запросов (режим lex/BM25)

| Синтаксис | Эффект | Пример |
|----------|--------|--------|
| `term` | Поиск по префиксу | `perf` находит «performance» |
| `"phrase"` | Точная фраза | `"rate limiter"` |
| `-term` | Исключить термин | `performance -sports` |

### HyDE (Hypothetical Document Embeddings)

Для сложных тем напиши, как ты ожидаешь увидеть ответ:

```bash
qmd query $'hyde: The migration plan involves three phases. First, we add the new columns without dropping the old ones. Then we backfill data. Finally we cut over and remove legacy columns.'
```

### Выбор коллекций

```bash
qmd search "query" --collection notes
qmd query "query" --collection project-docs
```

### Форматы вывода

```bash
qmd search "query" --json        # JSON output (best for parsing)
qmd search "query" --limit 5     # Limit results
qmd get "#abc123"                # Get by document ID
qmd get "path/to/file.md"       # Get by file path
qmd get "file.md:50" -l 100     # Get specific line range
qmd multi-get "journals/*.md" --json  # Batch retrieve by glob
```
## Интеграция MCP (рекомендовано)

qmd предоставляет сервер MCP, который напрямую предлагает инструменты поиска Hermes Agent через нативный клиент MCP. Это предпочтительная интеграция — после настройки агент получает инструменты qmd автоматически, без необходимости загружать этот навык.

### Вариант A: режим Stdio (простой)

Добавь в `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  qmd:
    command: "qmd"
    args: ["mcp"]
    timeout: 30
    connect_timeout: 45
```

Это регистрирует инструменты: `mcp_qmd_search`, `mcp_qmd_vsearch`, `mcp_qmd_deep_search`, `mcp_qmd_get`, `mcp_qmd_status`.

**Компромисс:** модели загружаются при первом вызове поиска (~19 с холодного старта), затем остаются «тёплыми» в течение сессии. Приемлемо для редкого использования.

### Вариант B: режим HTTP‑демона (быстро, рекомендуется для интенсивного использования)

Запусти демон qmd отдельно — он держит модели «тёплыми» в памяти:

```bash
# Start daemon (persists across agent restarts)
qmd mcp --http --daemon

# Runs on http://localhost:8181 by default
```

Затем настрой Hermes Agent для подключения по HTTP:

```yaml
mcp_servers:
  qmd:
    url: "http://localhost:8181/mcp"
    timeout: 30
```

**Компромисс:** использует ~2 ГБ ОЗУ во время работы, но каждый запрос быстрый (~2‑3 с). Лучший вариант для пользователей, часто выполняющих поиск.

### Поддержание работы демона

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

#### Linux (служба systemd для пользователя)

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

### Справочник инструментов MCP

После подключения эти инструменты доступны как `mcp_qmd_*`:

| Инструмент MCP | Соответствует | Описание |
|----------------|---------------|----------|
| `mcp_qmd_search` | `qmd search` | Поиск по ключевым словам BM25 |
| `mcp_qmd_vsearch` | `qmd vsearch` | Семантический векторный поиск |
| `mcp_qmd_deep_search` | `qmd query` | Гибридный поиск + переранжирование |
| `mcp_qmd_get` | `qmd get` | Получить документ по ID или пути |
| `mcp_qmd_status` | `qmd status` | Состояние индекса и статистика |

Инструменты MCP принимают структурированные запросы JSON для многорежимного поиска:

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
## Использование CLI (Без MCP)

Когда MCP не настроен, используй qmd напрямую в терминале:

```
terminal(command="qmd query 'what was decided about the API redesign' --json", timeout=30)
```

Для задач настройки и управления всегда используй терминал:

```
terminal(command="qmd collection add ~/Documents/notes --name notes")
terminal(command="qmd context add qmd://notes 'Personal research notes and ideas'")
terminal(command="qmd embed")
terminal(command="qmd status")
```
## Как работает конвейер поиска

Понимание внутренностей помогает выбрать правильный режим поиска:

1. **Query Expansion** — Тонко настроенная модель 1.7B генерирует 2 альтернативных запроса. Оригинальный запрос получает вес 2× при слиянии.
2. **Parallel Retrieval** — BM25 (SQLite FTS5) и векторный поиск работают одновременно для всех вариантов запросов.
3. **RRF Fusion** — Reciprocal Rank Fusion (k=60) объединяет результаты. Бонус за высокий ранг: #1 получает +0.05, #2‑3 получают +0.02.
4. **LLM Reranking** — `qwen3-reranker` переоценивает топ‑30 кандидатов (0.0‑1.0).
5. **Position‑Aware Blending** — Ранги 1‑3: 75 % поиск / 25 % переранжирование.
   Ранги 4‑10: 60 % / 40 %.
   Ранги 11+: 40 % / 60 % (больше доверия переранжированию для «длинного хвоста»).

**Smart Chunking:** Документы разбиваются в естественных точках разрыва (заголовки, блоки кода, пустые строки), ориентируясь на ≈ 900 токенов с 15 % перекрытием. Блоки кода никогда не разбиваются посередине.
## Лучшие практики

1. **Всегда добавляй описания контекста** — `qmd context add` значительно повышает точность извлечения. Описывай, что содержит каждая коллекция.
2. **Повторно встраивай после добавления документов** — `qmd embed` необходимо запустить заново, когда в коллекцию добавляются новые файлы.
3. **Используй `qmd search` для скорости** — когда нужен быстрый поиск по ключевым словам (идентификаторы кода, точные имена), BM25 мгновенен и не требует моделей.
4. **Используй `qmd query` для качества** — когда вопрос концептуальный или пользователю нужны наилучшие результаты, используй гибридный поиск.
5. **Отдавай предпочтение интеграции MCP** — после настройки агент получает нативные инструменты без необходимости загружать этот skill каждый раз.
6. **Режим демона для частых пользователей** — если пользователь регулярно ищет в своей базе знаний, рекомендовать настройку HTTP‑демона.
7. **Первый запрос в структурированном поиске получает вес 2×** — помещай самый важный/определённый запрос первым при комбинировании `lex` и `vec`.
## Устранение неполадок

### «Модели загружаются при первом запуске»
Нормально — `qmd` автоматически скачивает ~2 ГБ моделей GGUF при первом использовании.
Это однократная операция.

### Задержка холодного старта (~19 с)
Это происходит, когда модели не загружены в память. Решения:
- Запусти HTTP‑демон в режиме (`qmd mcp --http --daemon`), чтобы держать их «в тепле»;
- Используй `qmd search` (только BM25), когда модели не нужны;
- MCP в режиме stdio загружает модели при первом поиске и держит их «в тепле» в течение сессии.

### macOS: «не удалось загрузить расширение»
Установи SQLite через Homebrew: `brew install sqlite`
Затем убедись, что он находится в `PATH` до системного SQLite.

### «Коллекции не найдены»
Выполни `qmd collection add <path> --name <name>`, чтобы добавить каталоги,
затем `qmd embed` для их индексации.

### Переопределение модели встраивания (CJK/многоязычный)
Установи переменную окружения `QMD_EMBED_MODEL` для контента не на английском:
```bash
export QMD_EMBED_MODEL="your-multilingual-model"
```
## Хранение данных

- **Индекс и векторы:** `~/.cache/qmd/index.sqlite`
- **Модели:** автоматически загружаются в локальный кэш при первом запуске
- **Без облачных зависимостей** — всё работает локально
## Ссылки

- [GitHub: tobi/qmd](https://github.com/tobi/qmd)
- [Журнал изменений QMD](https://github.com/tobi/qmd/blob/main/CHANGELOG.md)