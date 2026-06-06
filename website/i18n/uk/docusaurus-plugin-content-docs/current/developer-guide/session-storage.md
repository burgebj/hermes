# Сховище сесій

Hermes Agent використовує базу даних SQLite (`~/.hermes/state.db`) для збереження метаданих сесії, повної історії повідомлень та конфігурації моделі між CLI‑ та шлюзовими сесіями. Це замінює попередній підхід із окремим JSONL‑файлом для кожної сесії.

Source file: `hermes_state.py`


## Огляд архітектури

```
~/.hermes/state.db (SQLite, WAL mode)
├── sessions              — Session metadata, token counts, billing
├── messages              — Full message history per session
├── messages_fts          — FTS5 virtual table (content + tool_name + tool_calls)
├── messages_fts_trigram  — FTS5 virtual table with trigram tokenizer (CJK / substring search)
├── state_meta            — Key/value metadata table
└── schema_version        — Single-row table tracking migration state
```

Ключові рішення дизайну:
- **WAL mode** для одночасних читачів + одного записувача (багатоплатформений шлюз)
- **FTS5 virtual table** для швидкого текстового пошуку по всіх повідомленнях сесії
- **Session lineage** через ланцюги `parent_session_id` (розділення, викликане компресією)
- **Source tagging** (`cli`, `telegram`, `discord` тощо) для фільтрації за платформою
- Batch runner та RL‑траєкторії НЕ зберігаються тут (окремі системи)


## Схема SQLite

### Таблиця Sessions

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

### Таблиця Messages

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

Примітки:
- `tool_calls` зберігається як JSON‑рядок (серіалізований список об’єктів викликів інструменту)
- `reasoning_details`, `codex_reasoning_items` та `codex_message_items` зберігаються як JSON‑рядки
- `reasoning` містить необроблений текст міркувань для провайдерів, які його надають
- Позначки часу — це числа типу `float` у форматі Unix epoch (`time.time()`)

### Повнотекстовий пошук FTS5

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
    content,
    content=messages,
    content_rowid=id
);
```

Таблиця FTS5 синхронізується за допомогою трьох тригерів, які спрацьовують під час **INSERT**, **UPDATE** та **DELETE** у таблиці `messages`:

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


## Версія схеми та міграції

Поточна версія схеми: **11**

Таблиця `schema_version` зберігає одне ціле число. Просте додавання колонок обробляється декларативно функцією `_reconcile_columns()` (яка порівнює поточні колонки з `SCHEMA_SQL` і додає відсутні). Ланцюг, керований версією, зарезервовано для міграцій даних та змін індексів/FTS, які не можна виразити декларативно:

| Версія | Зміна |
|--------|-------|
| 1 | Початкова схема (sessions, messages, FTS5) |
| 2 | Додано колонку `finish_reason` до messages |
| 3 | Додано колонку `title` до sessions |
| 4 | Додано унікальний індекс на `title` (NULL допускаються, не‑NULL мають бути унікальними) |
| 5 | Додано колонки білінгу: `cache_read_tokens`, `cache_write_tokens`, `reasoning_tokens`, `billing_provider`, `billing_base_url`, `billing_mode`, `estimated_cost_usd`, `actual_cost_usd`, `cost_status`, `cost_source`, `pricing_version` |
| 6 | Додано колонки міркувань до messages: `reasoning`, `reasoning_details`, `codex_reasoning_items` |
| 7 | Додано колонку `reasoning_content` до messages |
| 8 | Додано колонку `api_call_count` до sessions |
| 9 | Додано колонку `codex_message_items` до messages для відтворення ідентифікатора/фази повідомлення Codex Responses |
| 10 | Додано віртуальну таблицю `messages_fts_trigram` (токенізатор триграм для CJK / пошуку підрядків) та заповнено існуючі рядки |
| 11 | Перебудовано індекси `messages_fts` та `messages_fts_trigram` для охоплення `tool_name` + `tool_calls` і переключено з external‑content на inline mode; видалено старі тригери та заповнено всі рядки повідомлень |

Декларативне додавання колонок використовує `ALTER TABLE ADD COLUMN`, обгорнуте у `try/except` для обробки випадку, коли колонка вже існує (ідемпотентність). Номер версії збільшується після успішного виконання кожного блоку міграції.


## Обробка конфліктів запису

Кілька процесів hermes (шлюз + CLI‑сесії + агенти робочих дерев) спільно використовують один `state.db`. Клас `SessionDB` вирішує конфлікти запису за допомогою:

- **Короткого тайм‑ауту SQLite** (1 секунда) замість типових 30 секунд
- **Повторних спроб на рівні застосунку** з випадковим джиттером (20‑150 мс, до 15 спроб)
- Транзакцій **BEGIN IMMEDIATE** для виявлення блокувань на початку транзакції
- **Періодичних WAL‑контрольних точок** кожні 50 успішних записів (режим PASSIVE)

Це запобігає ефекту «конвеєра», коли детермінований внутрішній бек‑офф SQLite змушує всіх конкурентних записувачів повторювати спроби одночасно.

```
_WRITE_MAX_RETRIES = 15
_WRITE_RETRY_MIN_S = 0.020   # 20ms
_WRITE_RETRY_MAX_S = 0.150   # 150ms
_CHECKPOINT_EVERY_N_WRITES = 50
```


## Типові операції

### Ініціалізація

```python
from hermes_state import SessionDB

db = SessionDB()                           # Default: ~/.hermes/state.db
db = SessionDB(db_path=Path("/tmp/test.db"))  # Custom path
```

### Створення та керування сесіями

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

### Збереження повідомлень

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

### Отримання повідомлень

```python
# Raw messages with all metadata
messages = db.get_messages("sess_abc123")

# OpenAI conversation format (for API replay)
conversation = db.get_messages_as_conversation("sess_abc123")
# Returns: [{"role": "user", "content": "..."}, {"role": "assistant", ...}]
```

### Заголовки сесій

```python
# Set a title (must be unique among non-NULL titles)
db.set_session_title("sess_abc123", "Fix Docker Build")

# Resolve by title (returns most recent in lineage)
session_id = db.resolve_session_by_title("Fix Docker Build")

# Auto-generate next title in lineage
next_title = db.get_next_title_in_lineage("Fix Docker Build")
# Returns: "Fix Docker Build #2"
```


## Повнотекстовий пошук

Метод `search_messages()` підтримує синтаксис запитів FTS5 з автоматичною санітизацією вводу користувача.

### Базовий пошук

```python
results = db.search_messages("docker deployment")
```

### Синтаксис запитів FTS5

| Синтаксис | Приклад | Значення |
|-----------|---------|----------|
| Ключові слова | `docker deployment` | Обидва терміни (неявний AND) |
| Фраза в лапках | `"exact phrase"` | Точний збіг фрази |
| Boolean OR | `docker OR kubernetes` | Будь‑який з термінів |
| Boolean NOT | `python NOT java` | Виключити термін |
| Префікс | `deploy*` | Пошук за префіксом |

### Фільтрований пошук

```python
# Search only CLI sessions
results = db.search_messages("error", source_filter=["cli"])

# Exclude gateway sessions
results = db.search_messages("bug", exclude_sources=["telegram", "discord"])

# Search only user messages
results = db.search_messages("help", role_filter=["user"])
```

### Формат результатів пошуку

Кожен результат містить:
- `id`, `session_id`, `role`, `timestamp`
- `snippet` — фрагмент, згенерований FTS5, з маркерами `>>>match<<<`
- `context` — 1 повідомлення до і після збігу (вміст скорочено до 200 символів)
- `source`, `model`, `session_started` — дані з батьківської сесії

Метод `_sanitize_fts5_query()` обробляє крайові випадки:
- Видаляє незакриті лапки та спеціальні символи
- Обгортає дефісні терміни в лапки (`chat-send` → `"chat-send"`)
- Прибирає «повисаючі» логічні оператори (`hello AND` → `hello`)


## Ланцюжок сесій

Сесії можуть утворювати ланцюги через `parent_session_id`. Це відбувається, коли компресія контексту викликає розділення сесії в шлюзі.

### Запит: знайти ланцюжок сесій

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

### Запит: останні сесії з попереднім переглядом

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

### Запит: статистика використання токенів

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


## Експорт та очистка

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


## Розташування бази даних

Типовий шлях: `~/.hermes/state.db`

Він формується функцією `hermes_constants.get_hermes_home()`, яка за замовчуванням повертає `~/.hermes/`, або значенням змінної середовища `HERMES_HOME`.

Файл бази даних, WAL‑файл (`state.db-wal`) та файл спільної пам’яті (`state.db-shm`) створюються в одному каталозі.