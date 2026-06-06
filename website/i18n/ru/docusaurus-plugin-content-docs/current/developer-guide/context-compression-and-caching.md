# Сжатие контекста и кэширование

Hermes Agent использует двойную систему компрессии и кеширование подсказок Anthropic для эффективного управления использованием окна контекста в длительных беседах.

Исходные файлы: `agent/context_engine.py` (ABC), `agent/context_compressor.py` (движок по умолчанию), `agent/prompt_caching.py`, `gateway/run.py` (гигиена сессии), `run_agent.py` (поиск `_compress_context`)
## Подключаемый движок контекста

Управление контекстом построено на абстрактном базовом классе `ContextEngine` (`agent/context_engine.py`). Встроенный `ContextCompressor` является реализацией по умолчанию, но плагины могут заменять его альтернативными движками (например, Lossless Context Management).

```yaml
context:
  engine: "compressor"    # default — built-in lossy summarization
  engine: "lcm"           # example — plugin providing lossless context
```

Движок отвечает за:
- Определение, когда следует выполнять сжатие (`should_compress()`);
- Выполнение сжатия (`compress()`);
- При необходимости предоставление инструментов, которые агент может вызвать (например, `lcm_grep`);
- Отслеживание использования токенов из ответов API.

Выбор управляется конфигурацией через `context.engine` в `config.yaml`. Порядок разрешения:
1. Проверить каталог `plugins/context_engine/<name>/`;
2. Проверить общую систему плагинов (`register_context_engine()`);
3. Запасной вариант — встроенный `ContextCompressor`.

Движки плагинов **никогда не активируются автоматически** — пользователь должен явно задать `context.engine` в имя плагина. Значение по умолчанию `"compressor"` всегда использует встроенный вариант.

Настройка через `hermes plugins` → Provider Plugins → Context Engine, либо прямое редактирование `config.yaml`.

Для создания плагина движка контекста смотри [Context Engine Plugins](/developer-guide/context-engine-plugin).
## Dual Compression System

Hermes имеет два отдельных уровня сжатия, работающих независимо:

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

### 1. Gateway Session Hygiene (порог 85 %)

Расположен в `gateway/run.py` (поиск `Session hygiene: auto-compress`). Это **механизм защиты**, который
запускается до того, как агент обрабатывает сообщение. Он предотвращает сбои API, когда сессии
становятся слишком большими между ходами (например, накопление за ночь в Telegram/Discord).

- **Порог**: фиксирован на уровне 85 % длины контекста модели
- **Источник токенов**: предпочитает фактические токены, полученные от API в последнем ходе; в качестве запасного (фоллбэк) варианта использует грубую оценку по количеству символов (`estimate_messages_tokens_rough`)
- **Срабатывает**: только когда `len(history) >= 4` и сжатие включено
- **Назначение**: перехватывать сессии, которые обошли компрессор агента

Порог гигиены сессии шлюза намеренно выше, чем у компрессора агента. Установка его на 50 % (как у агента) приводила к преждевременному сжатию на каждом ходе в длинных сессиях шлюза.

### 2. Agent ContextCompressor (порог 50 %, настраиваемый)

Расположен в `agent/context_compressor.py`. Это **основная система сжатия**, которая работает внутри цикла инструментов агента и имеет доступ к точным, сообщённым API подсчётам токенов.
## Конфигурация

Все настройки сжатия читаются из `config.yaml` под ключом `compression`:

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

### Подробности параметров

| Параметр | По умолчанию | Диапазон | Описание |
|-----------|--------------|----------|----------|
| `threshold` | `0.50` | 0.0‑1.0 | Сжатие срабатывает, когда количество токенов подсказки ≥ `threshold × context_length` |
| `target_ratio` | `0.20` | 0.10‑0.80 | Определяет бюджет токенов защиты хвоста: `threshold_tokens × target_ratio` |
| `protect_last_n` | `20` | ≥ 1 | Минимальное количество последних сообщений, которые всегда сохраняются |
| `protect_first_n` | `3` | (hardcoded) | Системный запрос + первый обмен всегда сохраняются |

### Вычисленные значения (для модели с контекстом 200 K при настройках по умолчанию)

```
context_length       = 200,000
threshold_tokens     = 200,000 × 0.50 = 100,000
tail_token_budget    = 100,000 × 0.20 = 20,000
max_summary_tokens   = min(200,000 × 0.05, 12,000) = 10,000
```
## Алгоритм сжатия

Метод `ContextCompressor.compress()` использует 4‑фазный алгоритм:

### Фаза 1: Обрезка старых результатов инструментов (дешево, без вызова LLM)

Старые результаты инструментов (> 200 симв.) за пределами защищённого хвоста заменяются на:
```
[Old tool output cleared to save context space]
```

Это дешёвая предварительная проходка, которая экономит значительное количество токенов от объёмных выводов инструментов (содержимое файлов, вывод терминала, результаты веб‑поиска).

### Фаза 2: Определение границ

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

Защита хвоста **основана на бюджете токенов**: обход назад от конца, накопление токенов до исчерпания бюджета. При необходимости происходит откат к фиксированному счёту `protect_last_n`, если бюджет защищал бы меньше сообщений.

Границы выравниваются, чтобы не разрывать группы `tool_call`/`tool_result`. Метод `_align_boundary_backward()` проходит мимо последовательных результатов инструментов, чтобы найти родительское сообщение ассистента, сохраняя группы целыми.

### Фаза 3: Генерация структурированного резюме

:::warning Длина контекста модели‑резюме
Модель‑резюме должна иметь окно контекста **не меньше**, чем у основной модели агента. Весь средний участок отправляется модели‑резюме одним вызовом `call_llm(task="compression")`. Если контекст модели‑резюме меньше, API возвращает ошибку о превышении длины контекста — `_generate_summary()` перехватывает её, записывает предупреждение и возвращает `None`. Компрессор затем отбрасывает средние ходы **без резюме**, тихо теряя контекст разговора. Это самая частая причина ухудшения качества компрессии.
:::

Средние ходы суммируются вспомогательной LLM с помощью структурированного шаблона:
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

Бюджет резюме масштабируется в зависимости от объёма сжимаемого контента:
- Формула: `content_tokens × 0.20` (константа `_SUMMARY_RATIO`)
- Минимум: 2 000 токенов
- Максимум: `min(context_length × 0.05, 12 000)` токенов

### Фаза 4: Сборка сжатых сообщений

Список сжатых сообщений формируется так:
1. Сообщения‑заголовки (с примечанием, добавленным к системному запросу при первой компрессии)
2. Сообщение‑резюме (роль выбрана, чтобы избежать нарушений последовательных одинаковых ролей)
3. Сообщения‑хвост (без изменений)

Оставшиеся пары `tool_call`/`tool_result` очищаются функцией `_sanitize_tool_pairs()`:
- Результаты инструментов, ссылающиеся на удалённые вызовы → удаляются
- Вызовы инструментов, у которых удалены результаты → вставляется заглушка‑результат

### Итеративное повторное сжатие

При последующих компрессиях предыдущее резюме передаётся LLM с инструкцией **обновить** его, а не создавать новое с нуля. Это сохраняет информацию при множественных компрессиях — элементы переходят из «В процессе» в «Готово», добавляется новый прогресс, а устаревшая информация удаляется.

Поле `_previous_summary` в экземпляре компрессора хранит последний текст резюме для этой цели.
## Пример до/после

### До сжатия (45 сообщений, ~95 K токенов)

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

### После сжатия (25 сообщений, ~45 K токенов)

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
## Кеширование подсказок (Anthropic)

Source: `agent/prompt_caching.py`

Сокращает затраты токенов ввода примерно на 75 % в многосерийных диалогах за счёт кеширования префикса разговора. Использует контрольные точки Anthropic `cache_control`.

### Стратегия: system_and_3

Anthropic позволяет максимум 4 контрольных точки `cache_control` на запрос. Hermes использует стратегию «system_and_3»:

```
Breakpoint 1: System prompt           (stable across all turns)
Breakpoint 2: 3rd-to-last non-system message  ─┐
Breakpoint 3: 2nd-to-last non-system message   ├─ Rolling window
Breakpoint 4: Last non-system message          ─┘
```

### Как это работает

`apply_anthropic_cache_control()` делает глубокую копию сообщений и внедряет маркеры `cache_control`:

```python
# Cache marker format
marker = {"type": "ephemeral"}
# Or for 1-hour TTL:
marker = {"type": "ephemeral", "ttl": "1h"}
```

Маркеры применяются по‑разному в зависимости от типа содержимого:

| Тип содержимого | Куда помещается маркер |
|----------------|------------------------|
| Строковое содержимое | Преобразуется в `[{"type": "text", "text": ..., "cache_control": ...}]` |
| Список | Добавляется в словарь последнего элемента |
| None/пустой | Добавляется как `msg["cache_control"]` |
| Сообщения инструмента | Добавляется как `msg["cache_control"]` (только нативный Anthropic) |

### Паттерны проектирования, учитывающие кеш

1. **Стабильный системный запрос**: Системный запрос — это контрольная точка 1 и кешируется на всех ходах. Не изменяй его в середине разговора (компрессия добавляет заметку только при первой компрессии).

2. **Порядок сообщений важен**: Хиты кеша требуют совпадения префикса. Добавление или удаление сообщений в середине делает кеш недействительным для всех последующих сообщений.

3. **Взаимодействие с кешем компрессии**: После компрессии кеш инвалидируется для сжатого региона, но кеш системного запроса остаётся. Скользящее окно из 3‑х сообщений восстанавливает кеширование в течение 1‑2 ходов.

4. **Выбор TTL**: По умолчанию `5m` (5 минут). Используй `1h` для длительных сессий, когда пользователь делает паузы между ходами.

### Включение кеширования подсказок

Кеширование подсказок включается автоматически, когда:
- Модель — модель Anthropic Claude (определяется по названию модели)
- Провайдер поддерживает `cache_control` (нативный Anthropic API или OpenRouter)

```yaml
# config.yaml — TTL is configurable (must be "5m" or "1h")
prompt_caching:
  cache_ttl: "5m"
```

CLI отображает статус кеширования при запуске:
```
💾 Prompt caching: ENABLED (Claude via OpenRouter, 5m TTL)
```
## Предупреждения о давлении контекста

Промежуточные предупреждения о давлении контекста были удалены (см. блок `iteration-budget` в `run_agent.py`, где указано: «No intermediate pressure warnings — they caused models to 'give up' prematurely on complex tasks»). Сжатие активируется, когда количество токенов подсказки достигает настроенного `compression.threshold` (по умолчанию 50 %) без предварительного шага предупреждения; гигиена сессии шлюза срабатывает как вторичная система безопасности при 85 % окна контекста модели.