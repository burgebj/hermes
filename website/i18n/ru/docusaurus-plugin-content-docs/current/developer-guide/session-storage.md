# Хранилище сессий

Hermes Agent использует базу данных SQLite (`~/.hermes/state.db`) для
сохранения метаданных сессии, полной истории сообщений и конфигурации
модели между CLI‑ и gateway‑сессиями. Это заменяет прежний подход с
JSONL‑файлом для каждой сессии.

Source file: `hermes_state.py`

## Обзор архитектуры

```
~/.hermes/state.db (SQLite, WAL mode)
├── sessions              — Session metadata, token counts, billing
├── messages              — Full message history per session
├── messages_fts          — FTS5 virtual table (content + tool_name + tool_calls)
├── messages_fts_trigram  — FTS5 virtual table with trigram tokenizer (CJK / substring search)
├── state_meta            — Key/value metadata table
└── schema_version        — Single-row table tracking migration state
```

Ключевые решения дизайна:
- **WAL mode** для одновременных читателей + одного писателя (gateway‑мультиплатформенный)
- **FTS5 virtual table** для быстрого текстового поиска по всем сообщениям сессии
- **Наследование сессий** через цепочки `parent_session_id` (разделения, вызываемые компрессией)
- **Тегирование источника** (`cli`, `telegram`, `discord` и т.д.) для фильтрации по платформе
- Batch runner и RL‑траектории НЕ хранятся здесь (отдельные системы)

## Схема SQLite

### Таблица Sessions

```sql
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    user_id TEXT,
    model TEXT,
    model_config TEXT,
    system_prompt TEXT,
    parent_session_id TEXT,
    started_at REAL NOT NULL,
    ended_at REAL,
    end_reason TEXT,
    message_count INTEGER DEFAULT 0,
    tool_call_count INTEGER DEFAULT 0,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cache_read_tokens INTEGER DEFAULT 0,
    cache_write_tokens INTEGER DEFAULT 0,
    reasoning_tokens INTEGER DEFAULT 0,
    billing_provider TEXT,
    billing_base_url TEXT,
    billing_mode TEXT,
    estimated_cost_usd REAL,
    actual_cost_usd REAL,
    cost_status TEXT,
    cost_source TEXT,
    pricing_version TEXT,
    title TEXT,
    api_call_count INTEGER DEFAULT 0,
    FOREIGN KEY (parent_session_id) REFERENCES sessions(id)
);

CREATE INDEX IF NOT EXISTS idx_sessions_source ON sessions(source);
CREATE INDEX IF NOT EXISTS idx_sessions_parent ON sessions(parent_session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_started ON sessions(started_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_sessions_title_unique
    ON sessions(title) WHERE title IS NOT NULL;
```

### Таблица Messages

```sql
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    role TEXT NOT NULL,
    content TEXT,
    tool_call_id TEXT,
    tool_calls TEXT,
    tool_name TEXT,
    timestamp REAL NOT NULL,
    token_count INTEGER,
    finish_reason TEXT,
    reasoning TEXT,
    reasoning_content TEXT,
    reasoning_details TEXT,
    codex_reasoning_items TEXT,
    codex_message_items TEXT
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, timestamp);
```

Примечания:
- `tool_calls` хранится как строка JSON (сериализованный список объектов вызовов инструмента)
- `reasoning_details`, `codex_reasoning_items` и `codex_message_items` хранятся как строки JSON
- `reasoning` содержит необработанный текст рассуждений для провайдеров, которые его предоставляют
- Метки времени — числа с плавающей точкой Unix epoch (`time.time()`)

### FTS5 полнотекстовый поиск

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
    content,
    content=messages,
    content_rowid=id
);
```

Таблица FTS5 синхронизируется тремя триггерами, которые срабатывают при
INSERT, UPDATE и DELETE в таблице `messages`:

```sql
CREATE TRIGGER IF NOT EXISTS messages_fts_insert AFTER INSERT ON messages BEGIN
    INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
END;

CREATE TRIGGER IF NOT EXISTS messages_fts_delete AFTER DELETE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content)
        VALUES('delete', old.id, old.content);
END;

CREATE TRIGGER IF NOT EXISTS messages_fts_update AFTER UPDATE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content)
        VALUES('delete', old.id, old.content);
    INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
END;
```

## Версия схемы и миграции

Текущая версия схемы: **11**

Таблица `schema_version` хранит единственное целое число. Простые добавления
столбцов обрабатываются декларативно функцией `_reconcile_columns()` (которая
сравнивает текущие столбцы с `SCHEMA_SQL` и добавляет недостающие). Цепочка,
зависящая от версии, зарезервирована для миграций данных и изменений индексов/FTS,
которые нельзя выразить декларативно:

| Версия | Изменение |
|--------|-----------|
| 1 | Начальная схема (sessions, messages, FTS5) |
| 2 | Добавлен столбец `finish_reason` в messages |
| 3 | Добавлен столбец `title` в sessions |
| 4 | Добавлен уникальный индекс по `title` (NULL допускаются, не‑NULL должны быть уникальны) |
| 5 | Добавлены столбцы биллинга: `cache_read_tokens`, `cache_write_tokens`, `reasoning_tokens`, `billing_provider`, `billing_base_url`, `billing_mode`, `estimated_cost_usd`, `actual_cost_usd`, `cost_status`, `cost_source`, `pricing_version` |
| 6 | Добавлены столбцы рассуждений в messages: `reasoning`, `reasoning_details`, `codex_reasoning_items` |
| 7 | Добавлен столбец `reasoning_content` в messages |
| 8 | Добавлен столбец `api_call_count` в sessions |
| 9 | Добавлен столбец `codex_message_items` в messages для повторного воспроизведения сообщения/фазы Codex Responses |
| 10 | Добавлена виртуальная таблица `messages_fts_trigram` (токенизатор триграмм для CJK / поиска подстрок) и заполнение существующих строк |
| 11 | Перестроены индексы `messages_fts` и `messages_fts_trigram` для охвата `tool_name` + `tool_calls` и переход от external‑content к inline‑mode; удалены старые триггеры и выполнено заполнение всех строк сообщений |

Декларативные добавления столбцов используют `ALTER TABLE ADD COLUMN`, обёрнутые в `try/except` для обработки случая «столбец уже существует» (идемпотентно). Номер версии увеличивается после каждого успешно выполненного блока миграции.

## Обработка конкуренции записи

Несколько процессов hermes (gateway + CLI‑сессии + worktree‑агенты) используют один
`state.db`. Класс `SessionDB` решает проблему конкуренции записи с помощью:

- **Короткого таймаута SQLite** (1 секунда) вместо стандартных 30 сек.
- **Повтора на уровне приложения** с случайным джиттером (20‑150 мс, до 15 попыток)
- Транзакций **BEGIN IMMEDIATE** для выявления блокировок сразу при начале транзакции
- **Периодических контрольных точек WAL** каждые 50 успешных записей (режим PASSIVE)

Это предотвращает эффект «конвоя», когда детерминированный внутренний откат SQLite заставляет всех конкурирующих писателей повторять попытки одновременно.

```
_WRITE_MAX_RETRIES = 15
_WRITE_RETRY_MIN_S = 0.020   # 20ms
_WRITE_RETRY_MAX_S = 0.150   # 150ms
_CHECKPOINT_EVERY_N_WRITES = 50
```

## Общие операции

### Инициализация

```python
from hermes_state import SessionDB

db = SessionDB()                           # Default: ~/.hermes/state.db
db = SessionDB(db_path=Path("/tmp/test.db"))  # Custom path
```

### Создание и управление сессиями

```python
# Create a new session
db.create_session(
    session_id="sess_abc123",
    source="cli",
    model="anthropic/claude-sonnet-4.6",
    user_id="user_1",
    parent_session_id=None,  # or previous session ID for lineage
)

# End a session
db.end_session("sess_abc123", end_reason="user_exit")

# Reopen a session (clear ended_at/end_reason)
db.reopen_session("sess_abc123")
```

### Сохранение сообщений

```python
msg_id = db.append_message(
    session_id="sess_abc123",
    role="assistant",
    content="Here's the answer...",
    tool_calls=[{"id": "call_1", "function": {"name": "terminal", "arguments": "{}"}}],
    token_count=150,
    finish_reason="stop",
    reasoning="Let me think about this...",
)
```

### Получение сообщений

```python
# Raw messages with all metadata
messages = db.get_messages("sess_abc123")

# OpenAI conversation format (for API replay)
conversation = db.get_messages_as_conversation("sess_abc123")
# Returns: [{"role": "user", "content": "..."}, {"role": "assistant", ...}]
```

### Заголовки сессий

```python
# Set a title (must be unique among non-NULL titles)
db.set_session_title("sess_abc123", "Fix Docker Build")

# Resolve by title (returns most recent in lineage)
session_id = db.resolve_session_by_title("Fix Docker Build")

# Auto-generate next title in lineage
next_title = db.get_next_title_in_lineage("Fix Docker Build")
# Returns: "Fix Docker Build #2"
```

## Полнотекстовый поиск

Метод `search_messages()` поддерживает синтаксис запросов FTS5 с автоматической
санитизацией пользовательского ввода.

### Базовый поиск

```python
results = db.search_messages("docker deployment")
```

### Синтаксис запросов FTS5

| Синтаксис | Пример | Значение |
|-----------|--------|----------|
| Ключевые слова | `docker deployment` | Оба термина (неявный AND) |
| Фраза в кавычках | `"exact phrase"` | Точное совпадение фразы |
| Boolean OR | `docker OR kubernetes` | Любой из терминов |
| Boolean NOT | `python NOT java` | Исключить термин |
| Префикс | `deploy*` | Поиск по префиксу |

### Фильтрованный поиск

```python
# Search only CLI sessions
results = db.search_messages("error", source_filter=["cli"])

# Exclude gateway sessions
results = db.search_messages("bug", exclude_sources=["telegram", "discord"])

# Search only user messages
results = db.search_messages("help", role_filter=["user"])
```

### Формат результатов поиска

Каждый результат включает:
- `id`, `session_id`, `role`, `timestamp`
- `snippet` — фрагмент, сгенерированный FTS5, с маркерами `>>>match<<<`
- `context` — 1 сообщение до и после совпадения (содержимое обрезано до 200 символов)
- `source`, `model`, `session_started` — из родительской сессии

Метод `_sanitize_fts5_query()` обрабатывает граничные случаи:
- Удаляет несоответствующие кавычки и специальные символы
- Оборачивает дефисные термины в кавычки (`chat-send` → `"chat-send"`)
- Убирает висящие булевые операторы (`hello AND` → `hello`)

## Наследование сессий

Сессии могут образовывать цепочки через `parent_session_id`. Это происходит,
когда компрессия контекста приводит к разделению сессии в gateway.

### Запрос: найти наследование сессий

```sql
-- Find all ancestors of a session
WITH RECURSIVE lineage AS (
    SELECT * FROM sessions WHERE id = ?
    UNION ALL
    SELECT s.* FROM sessions s
    JOIN lineage l ON s.id = l.parent_session_id
)
SELECT id, title, started_at, parent_session_id FROM lineage;

-- Find all descendants of a session
WITH RECURSIVE descendants AS (
    SELECT * FROM sessions WHERE id = ?
    UNION ALL
    SELECT s.* FROM sessions s
    JOIN descendants d ON s.parent_session_id = d.id
)
SELECT id, title, started_at FROM descendants;
```

### Запрос: последние сессии с превью

```sql
SELECT s.*,
    COALESCE(
        (SELECT SUBSTR(m.content, 1, 63)
         FROM messages m
         WHERE m.session_id = s.id AND m.role = 'user' AND m.content IS NOT NULL
         ORDER BY m.timestamp, m.id LIMIT 1),
        ''
    ) AS preview,
    COALESCE(
        (SELECT MAX(m2.timestamp) FROM messages m2 WHERE m2.session_id = s.id),
        s.started_at
    ) AS last_active
FROM sessions s
ORDER BY s.started_at DESC
LIMIT 20;
```

### Запрос: статистика использования токенов

```sql
-- Total tokens by model
SELECT model,
       COUNT(*) as session_count,
       SUM(input_tokens) as total_input,
       SUM(output_tokens) as total_output,
       SUM(estimated_cost_usd) as total_cost
FROM sessions
WHERE model IS NOT NULL
GROUP BY model
ORDER BY total_cost DESC;

-- Sessions with highest token usage
SELECT id, title, model, input_tokens + output_tokens AS total_tokens,
       estimated_cost_usd
FROM sessions
ORDER BY total_tokens DESC
LIMIT 10;
```

## Экспорт и очистка

```python
# Export a single session with messages
data = db.export_session("sess_abc123")

# Export all sessions (with messages) as list of dicts
all_data = db.export_all(source="cli")

# Delete old sessions (only ended sessions)
deleted_count = db.prune_sessions(older_than_days=90)
deleted_count = db.prune_sessions(older_than_days=30, source="telegram")

# Clear messages but keep the session record
db.clear_messages("sess_abc123")

# Delete session and all messages
db.delete_session("sess_abc123")
```

## Расположение базы данных

Путь по умолчанию: `~/.hermes/state.db`

Он формируется функцией `hermes_constants.get_hermes_home()`, которая по
умолчанию возвращает `~/.hermes/`, либо значение переменной окружения
`HERMES_HOME`.

Файл базы данных, WAL‑файл (`state.db-wal`) и файл совместно используемой
памяти (`state.db-shm`) создаются в одном и том же каталоге.