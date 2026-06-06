# Стиснення контексту та кешування

Hermes Agent використовує подвійну систему стиснення та кешування підказок Anthropic для
ефективного управління використанням вікна контексту під час тривалих розмов.

Source files: `agent/context_engine.py` (ABC), `agent/context_compressor.py` (default engine),
`agent/prompt_caching.py`, `gateway/run.py` (session hygiene), `run_agent.py` (search for `_compress_context`)
## Плагіновий контекстний движок

Управління контекстом побудовано на абстрактному класі `ContextEngine` (`agent/context_engine.py`). Вбудований `ContextCompressor` є реалізацією за замовчуванням, проте плагіни можуть замінити його альтернативними движками (наприклад, Lossless Context Management).

```yaml
context:
  engine: "compressor"    # default — built-in lossy summarization
  engine: "lcm"           # example — plugin providing lossless context
```

Движок відповідає за:
- Визначення, коли слід виконати стискання (`should_compress()`);
- Виконання стискання (`compress()`);
- За потреби – надає інструменти, які агент може викликати (наприклад, `lcm_grep`);
- Відстеження використання токенів у відповідях API.

Вибір здійснюється на основі конфігурації через `context.engine` у `config.yaml`. Порядок розв’язання:
1. Перевірити каталог `plugins/context_engine/<name>/`;
2. Перевірити загальну систему плагінів (`register_context_engine()`);
3. Повернутись до вбудованого `ContextCompressor`.

Плагінові движки **ніколи не активуються автоматично** — користувач повинен явно встановити `context.engine` на назву плагіна. За замовчуванням `"compressor"` завжди використовує вбудований.

Налаштуй через `hermes plugins` → Provider Plugins → Context Engine, або відредагуй `config.yaml` безпосередньо.

Для створення плагіна контекстного движка дивись [Context Engine Plugins](/developer-guide/context-engine-plugin).
## Dual Compression System

Hermes має два окремих рівня стискання, які працюють незалежно:

```
                     ┌──────────────────────────┐
  Incoming message   │   Gateway Session Hygiene │  Fires at 85% of context
  ─────────────────► │   (pre-agent, rough est.) │  Safety net for large sessions
                     └─────────────┬────────────┘
                                   │
                                   ▼
                     ┌──────────────────────────┐
                     │   Agent ContextCompressor │  Fires at 50% of context (default)
                     │   (in-loop, real tokens)  │  Normal context management
                     └──────────────────────────┘
```

### 1. Gateway Session Hygiene (поріг 85 %)

Розташовано у `gateway/run.py` (шукайте `Session hygiene: auto-compress`). Це **запобіжна мережа**, яка
виконується перед тим, як агент обробляє повідомлення. Вона запобігає збоям API, коли сесії
стають надто великими між ходами (наприклад, накопичення за ніч у Telegram/Discord).

- **Поріг**: Фіксовано на 85 % довжини контексту моделі
- **Джерело токенів**: Віддає перевагу фактичним токенам, повідомленим API у попередньому ході; у випадку їх відсутності
  використовує грубу оцінку за кількістю символів (`estimate_messages_tokens_rough`)
- **Запуск**: Тільки коли `len(history) >= 4` і стискання ввімкнено
- **Призначення**: Виявляти сесії, які обійшли стискання агента

Поріг гігієни шлюзу навмисно вищий, ніж у стискальника агента. Встановлення його на 50 % (те саме, що у агента) призводило до передчасного стискання на кожному ході у довгих сесіях шлюзу.

### 2. Agent ContextCompressor (поріг 50 %, налаштовується)

Розташовано у `agent/context_compressor.py`. Це **основна система стискання**, яка працює всередині інструментального циклу агента з доступом до точних підрахунків токенів, повідомлених API.
## Конфігурація

Усі налаштування стиснення читаються з `config.yaml` під ключем `compression`:

```yaml
compression:
  enabled: true              # Enable/disable compression (default: true)
  threshold: 0.50            # Fraction of context window (default: 0.50 = 50%)
  target_ratio: 0.20         # How much of threshold to keep as tail (default: 0.20)
  protect_last_n: 20         # Minimum protected tail messages (default: 20)

# Summarization model/provider configured under auxiliary:
auxiliary:
  compression:
    model: null              # Override model for summaries (default: auto-detect)
    provider: auto           # Provider: "auto", "openrouter", "nous", "main", etc.
    base_url: null           # Custom OpenAI-compatible endpoint
```

### Деталі параметрів

| Параметр | За замовчуванням | Діапазон | Опис |
|-----------|-------------------|----------|------|
| `threshold` | `0.50` | 0.0‑1.0 | Стиснення спрацьовує, коли кількість токенів запиту ≥ `threshold × context_length` |
| `target_ratio` | `0.20` | 0.10‑0.80 | Керує бюджетом токенів захисту хвоста: `threshold_tokens × target_ratio` |
| `protect_last_n` | `20` | ≥ 1 | Мінімальна кількість останніх повідомлень, які завжди зберігаються |
| `protect_first_n` | `3` | (hardcoded) | System prompt + перший обмін завжди зберігаються |

### Обчислені значення (для моделі з контекстом 200 K за замовчуванням)

```
context_length       = 200,000
threshold_tokens     = 200,000 × 0.50 = 100,000
tail_token_budget    = 100,000 × 0.20 = 20,000
max_summary_tokens   = min(200,000 × 0.05, 12,000) = 10,000
```
## Алгоритм стиснення

Метод `ContextCompressor.compress()` виконує 4‑фазний алгоритм:

### Фаза 1: Обрізання старих результатів інструментів (дешево, без виклику LLM)

Старі результати інструментів (>200 символів) поза захищеним хвостом замінюються на:
```
[Old tool output cleared to save context space]
```

Це дешево виконаний попередній прохід, який економить значну кількість токенів від довгих виводів інструментів (вміст файлів, вивід терміналу, результати пошуку).

### Фаза 2: Визначення меж

```
┌─────────────────────────────────────────────────────────────┐
│  Message list                                               │
│                                                             │
│  [0..2]  ← protect_first_n (system + first exchange)        │
│  [3..N]  ← middle turns → SUMMARIZED                        │
│  [N..end] ← tail (by token budget OR protect_last_n)        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Захист хвоста **базується на бюджеті токенів**: проходить назад від кінця, накопичуючи токени, доки бюджет не буде вичерпано. Якщо бюджет захистив би менше повідомлень, використовується фіксована кількість `protect_last_n`.

Межі вирівнюються, щоб уникнути розриву груп `tool_call`/`tool_result`. Метод `_align_boundary_backward()` проходить повз послідовні результати інструментів, щоб знайти батьківське повідомлення асистента, зберігаючи групи недоторканими.

### Фаза 3: Генерація структурованого резюме

:::warning Довжина контексту моделі резюме
Модель резюме повинна мати вікно контексту **не менше**, ніж у основної моделі агента. Уся середня частина передається моделі резюме одним викликом `call_llm(task="compression")`. Якщо контекст моделі резюме менший, API повертає помилку довжини контексту — `_generate_summary()` ловить її, логуватиме попередження та поверне `None`. Компресор тоді відкидає середні ходи **без резюме**, тихо втрачаючи контекст розмови. Це найпоширеніша причина погіршення якості стиснення.
:::

Середні ходи резюмуються за допомогою допоміжного LLM за структурованим шаблоном:

```
## Goal
[What the user is trying to accomplish]

## Constraints & Preferences
[User preferences, coding style, constraints, important decisions]

## Progress
### Done
[Completed work — specific file paths, commands run, results]
### In Progress
[Work currently underway]
### Blocked
[Any blockers or issues encountered]

## Key Decisions
[Important technical decisions and why]

## Relevant Files
[Files read, modified, or created — with brief note on each]

## Next Steps
[What needs to happen next]

## Critical Context
[Specific values, error messages, configuration details]
```

Бюджет резюме масштабується відповідно до обсягу стискаємого вмісту:
- Формула: `content_tokens × 0.20` (константа `_SUMMARY_RATIO`)
- Мінімум: 2 000 токенів
- Максимум: `min(context_length × 0.05, 12 000)` токенів

### Фаза 4: Формування стиснених повідомлень

Список стиснених повідомлень виглядає так:
1. Повідомлення заголовка (з приміткою, доданою до system prompt при першому стисканні)
2. Повідомлення резюме (роль обрана, щоб уникнути порушень послідовних однакових ролей)
3. Повідомлення хвоста (не змінені)

Одинокі пари `tool_call`/`tool_result` очищуються функцією `_sanitize_tool_pairs()`:
- Результати інструментів, що посилаються на видалені виклики → видаляються
- Виклики інструментів, чиї результати були видалені → вставляється заглушка‑результат

### Ітеративне повторне стискання

При наступних стисканнях попереднє резюме передається LLM з інструкцією **оновити** його, а не створювати нове з нуля. Це зберігає інформацію протягом кількох стискань — елементи переходять з «В процесі» до «Готово», додається новий прогрес, а застаріла інформація видаляється.

Поле `_previous_summary` у екземплярі компресора зберігає останній текст резюме для цієї мети.
## Приклад до/після

### До стиснення (45 повідомлень, ~95 K токенів)

```
[0] system:    "You are a helpful assistant..." (system prompt)
[1] user:      "Help me set up a FastAPI project"
[2] assistant: <tool_call> terminal: mkdir project </tool_call>
[3] tool:      "directory created"
[4] assistant: <tool_call> write_file: main.py </tool_call>
[5] tool:      "file written (2.3KB)"
    ... 30 more turns of file editing, testing, debugging ...
[38] assistant: <tool_call> terminal: pytest </tool_call>
[39] tool:      "8 passed, 2 failed\n..."  (5KB output)
[40] user:      "Fix the failing tests"
[41] assistant: <tool_call> read_file: tests/test_api.py </tool_call>
[42] tool:      "import pytest\n..."  (3KB)
[43] assistant: "I see the issue with the test fixtures..."
[44] user:      "Great, also add error handling"
```

### Після стиснення (25 повідомлень, ~45 K токенів)

```
[0] system:    "You are a helpful assistant...
               [Note: Some earlier conversation turns have been compacted...]"
[1] user:      "Help me set up a FastAPI project"
[2] assistant: "[CONTEXT COMPACTION] Earlier turns were compacted...

               ## Goal
               Set up a FastAPI project with tests and error handling

               ## Progress
               ### Done
               - Created project structure: main.py, tests/, requirements.txt
               - Implemented 5 API endpoints in main.py
               - Wrote 10 test cases in tests/test_api.py
               - 8/10 tests passing

               ### In Progress
               - Fixing 2 failing tests (test_create_user, test_delete_user)

               ## Relevant Files
               - main.py — FastAPI app with 5 endpoints
               - tests/test_api.py — 10 test cases
               - requirements.txt — fastapi, pytest, httpx

               ## Next Steps
               - Fix failing test fixtures
               - Add error handling"
[3] user:      "Fix the failing tests"
[4] assistant: <tool_call> read_file: tests/test_api.py </tool_call>
[5] tool:      "import pytest\n..."
[6] assistant: "I see the issue with the test fixtures..."
[7] user:      "Great, also add error handling"
```
## Кешування підказок (Anthropic)

Джерело: `agent/prompt_caching.py`

Зменшує витрати токенів вводу приблизно на 75 % у багатокрокових розмовах, кешуючи префікс розмови. Використовує точки розриву `cache_control` від Anthropic.

### Стратегія: system_and_3

Anthropic дозволяє максимум 4 точки розриву `cache_control` на запит. Hermes використовує стратегію «system_and_3»:

```
Breakpoint 1: System prompt           (stable across all turns)
Breakpoint 2: 3rd-to-last non-system message  ─┐
Breakpoint 3: 2nd-to-last non-system message   ├─ Rolling window
Breakpoint 4: Last non-system message          ─┘
```

### Як це працює

`apply_anthropic_cache_control()` глибоко копіює повідомлення та вставляє маркер `cache_control`:

```python
# Cache marker format
marker = {"type": "ephemeral"}
# Or for 1-hour TTL:
marker = {"type": "ephemeral", "ttl": "1h"}
```

Маркер застосовується по‑різному залежно від типу вмісту:

| Тип вмісту | Куди додається маркер |
|------------|-----------------------|
| Текстовий рядок | Перетворюється на `[{"type": "text", "text": ..., "cache_control": ...}]` |
| Список | Додається до словника останнього елементу |
| None/порожньо | Додається як `msg["cache_control"]` |
| Повідомлення інструменту | Додається як `msg["cache_control"]` (лише у нативному Anthropic) |

### Патерни дизайну, орієнтовані на кеш

1. **Стабільна системна підказка**: Системна підказка — це точка розриву 1 і кешується протягом усіх ходів. Уникай її зміни під час розмови (компресія додає нотатку лише при першій компресії).

2. **Порядок повідомлень має значення**: Для попадання в кеш потрібне збігання префікса. Додавання або видалення повідомлень посередині робить кеш недійсним для всього, що йде після.

3. **Взаємодія з кешем компресії**: Після компресії кеш анулюється для стиснутого регіону, але кеш системної підказки зберігається. Ковзне вікно з 3‑х повідомлень відновлює кешування протягом 1‑2 ходів.

4. **Вибір TTL**: За замовчуванням `5m` (5 хвилин). Використовуй `1h` для довготривалих сесій, коли користувач робить перерви між ходами.

### Увімкнення кешування підказок

Кешування підказок автоматично вмикається, коли:
- Модель є моделлю Anthropic Claude (визначається за назвою моделі)
- Провайдер підтримує `cache_control` (нативний API Anthropic або OpenRouter)

```yaml
# config.yaml — TTL is configurable (must be "5m" or "1h")
prompt_caching:
  cache_ttl: "5m"
```

CLI показує статус кешування під час запуску:
```
💾 Prompt caching: ENABLED (Claude via OpenRouter, 5m TTL)
```
## Попередження про тиск контексту

Проміжні попередження про тиск контексту було видалено (дивись блок `iteration-budget` у `run_agent.py`, де зазначено: «No intermediate pressure warnings — they caused models to 'give up' prematurely on complex tasks»). Стиснення спрацьовує, коли кількість токенів запиту досягає налаштованого `compression.threshold` (за замовчуванням 50 %) без попереднього кроку попередження; гігієна сесії шлюзу діє як другий захисний механізм при 85 % вікна контексту моделі.