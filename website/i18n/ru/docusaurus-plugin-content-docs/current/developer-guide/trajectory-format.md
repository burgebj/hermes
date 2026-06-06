# Формат траекторий

Hermes Agent сохраняет траектории разговоров в совместимом с ShareGPT формате JSONL
для использования в качестве обучающих данных, артефактов отладки и наборов данных
для обучения с подкреплением.

Исходные файлы: `agent/trajectory.py`, `run_agent.py` (поиск `_save_trajectory`), `batch_runner.py`


## Конвенция именования файлов

Траектории записываются в файлы в текущем рабочем каталоге:

| Файл | Когда |
|------|------|
| `trajectory_samples.jsonl` | Разговоры, завершившиеся успешно (`completed=True`) |
| `failed_trajectories.jsonl` | Разговоры, завершившиеся с ошибкой или прерванные (`completed=False`) |

Пакетный запуск (`batch_runner.py`) записывает в пользовательский файл вывода для каждой партии
(например, `batch_001_output.jsonl`) с дополнительными полями метаданных.

Имя файла можно переопределить через параметр `filename` в `save_trajectory()`.


## Формат записи JSONL

Каждая строка в файле — самостоятельный JSON‑объект. Существует два варианта:

### Формат CLI/интерактивный (из `_save_trajectory`)

```json
{
  "conversations": [ ... ],
  "timestamp": "2026-03-30T14:22:31.456789",
  "model": "anthropic/claude-sonnet-4.6",
  "completed": true
}
```

### Формат пакетного запуска (из `batch_runner.py`)

```json
{
  "prompt_index": 42,
  "conversations": [ ... ],
  "metadata": { "prompt_source": "gsm8k", "difficulty": "hard" },
  "completed": true,
  "partial": false,
  "api_calls": 7,
  "toolsets_used": ["code_tools", "file_tools"],
  "tool_stats": {
    "terminal": {"count": 3, "success": 3, "failure": 0},
    "read_file": {"count": 2, "success": 2, "failure": 0},
    "write_file": {"count": 0, "success": 0, "failure": 0}
  },
  "tool_error_counts": {
    "terminal": 0,
    "read_file": 0,
    "write_file": 0
  }
}
```

Словари `tool_stats` и `tool_error_counts` нормализованы так, чтобы включать
ВСЕ возможные инструменты (из `model_tools.TOOL_TO_TOOLSET_MAP`) со значениями по умолчанию 0,
что обеспечивает согласованную схему записей при загрузке набора данных HuggingFace.


## Массив `conversations` (формат ShareGPT)

Массив `conversations` использует соглашения ролей ShareGPT:

| Роль API | ShareGPT `from` |
|----------|-----------------|
| system | `"system"` |
| user | `"human"` |
| assistant | `"gpt"` |
| tool | `"tool"` |

### Полный пример

```json
{
  "conversations": [
    {
      "from": "system",
      "value": "You are a function calling AI model. You are provided with function signatures within <tools> </tools> XML tags. You may call one or more functions to assist with the user query. If available tools are not relevant in assisting with user query, just respond in natural conversational language. Don't make assumptions about what values to plug into functions. After calling & executing the functions, you will be provided with function results within <tool_response> </tool_response> XML tags. Here are the available tools:\n<tools>\n[{\"name\": \"terminal\", \"description\": \"Execute shell commands\", \"parameters\": {\"type\": \"object\", \"properties\": {\"command\": {\"type\": \"string\"}}}, \"required\": null}]\n</tools>\nFor each function call return a JSON object, with the following pydantic model json schema for each:\n{'title': 'FunctionCall', 'type': 'object', 'properties': {'name': {'title': 'Name', 'type': 'string'}, 'arguments': {'title': 'Arguments', 'type': 'object'}}, 'required': ['name', 'arguments']}\nEach function call should be enclosed within <tool_call> </tool_call> XML tags.\nExample:\n<tool_call>\n{'name': <function-name>,'arguments': <args-dict>}\n</tool_call>"
    },
    {
      "from": "human",
      "value": "What Python version is installed?"
    },
    {
      "from": "gpt",
      "value": "<think>\nThe user wants to know the Python version. I should run python3 --version.\n</think>\n<tool_call>\n{\"name\": \"terminal\", \"arguments\": {\"command\": \"python3 --version\"}}\n</tool_call>"
    },
    {
      "from": "tool",
      "value": "<tool_response>\n{\"tool_call_id\": \"call_abc123\", \"name\": \"terminal\", \"content\": \"Python 3.11.6\"}\n</tool_response>"
    },
    {
      "from": "gpt",
      "value": "<think>\nGot the version. I can now answer the user.\n</think>\nPython 3.11.6 is installed on this system."
    }
  ],
  "timestamp": "2026-03-30T14:22:31.456789",
  "model": "anthropic/claude-sonnet-4.6",
  "completed": true
}
```


## Правила нормализации

### Разметка содержимого рассуждений

Конвертер траекторий нормализует ВСЕ рассуждения в теги `<think>`, независимо
от того, как модель изначально их сгенерировала:

1. **Нативные токены размышления** (`msg["reasoning"]` от провайдеров вроде Anthropic, OpenAI o-series): оборачиваются как `<think>\n{reasoning}\n</think>\n` и добавляются перед содержимым.
2. **XML `REASONING_SCRATCHPAD`** (когда нативное размышление отключено и модель рассуждает через XML, указанный в системном промпте): теги `<REASONING_SCRATCHPAD>` преобразуются в `<think>` функцией `convert_scratchpad_to_think()`.
3. **Пустые блоки `<think>`**: каждому ходу `gpt` гарантировано присутствует блок `<think>`. Если рассуждения не были сгенерированы, вставляется пустой блок: `<think>\n</think>\n` — это обеспечивает единый формат для обучающих данных.

### Нормализация вызовов инструментов

Вызовы инструментов из формата API (с `tool_call_id`, именем функции, аргументами в виде JSON‑строки) преобразуются в JSON, обёрнутый в XML:

```
<tool_call>
{"name": "terminal", "arguments": {"command": "ls -la"}}
</tool_call>
```

- Аргументы парсятся из JSON‑строк обратно в объекты (не двойное кодирование).
- Если парсинг JSON не удался (не должно происходить — проверяется во время разговора), используется пустой `{}` с записью предупреждения в лог.
- Несколько вызовов инструментов в одном ходу ассистента приводят к нескольким блокам `<tool_call>` в едином сообщении `gpt`.

### Нормализация ответов инструментов

Все результаты инструментов, следующие за сообщением ассистента, группируются в один ход `tool` с ответами JSON, обёрнутыми в XML:

```
<tool_response>
{"tool_call_id": "call_abc123", "name": "terminal", "content": "output here"}
</tool_response>
```

- Если содержимое инструмента выглядит как JSON (начинается с `{` или `[`), оно парсится, чтобы поле `content` содержало объект/массив JSON, а не строку.
- Несколько результатов инструментов объединяются переводами строки в одном сообщении.
- Имя инструмента сопоставляется по позиции с массивом `tool_calls` родительского сообщения ассистента.

### Системное сообщение

Системное сообщение генерируется во время сохранения (не берётся из разговора).
Оно следует шаблону подсказки Hermes для вызова функций и содержит:

- Преамбулу, объясняющую протокол вызова функций;
- XML‑блок `<tools>` с JSON‑определениями инструментов;
- Ссылку на схему объектов `FunctionCall`;
- Пример `<tool_call>`.

Определения инструментов включают `name`, `description`, `parameters` и `required` (установлено в `null` для соответствия каноничному формату).


## Загрузка траекторий

Траектории — обычный JSONL; их можно загрузить любой программой‑чтением JSON‑строк:

```python
import json

def load_trajectories(path: str):
    """Load trajectory entries from a JSONL file."""
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries

# Filter to successful completions only
successful = [e for e in load_trajectories("trajectory_samples.jsonl")
              if e.get("completed")]

# Extract just the conversations for training
training_data = [e["conversations"] for e in successful]
```

### Загрузка для наборов данных HuggingFace

```python
from datasets import load_dataset

ds = load_dataset("json", data_files="trajectory_samples.jsonl")
```

Нормализованная схема `tool_stats` гарантирует, что у всех записей одинаковые столбцы,
что предотвращает ошибки несовпадения схем Arrow при загрузке набора данных.

## Управление сохранением траекторий

В CLI сохранение траекторий контролируется параметром:

```yaml
# config.yaml
agent:
  save_trajectories: true  # default: false
```

Или флагом `--save-trajectories`. Когда агент инициализируется с `save_trajectories=True`, метод `_save_trajectory()` вызывается в конце каждого хода разговора.

Пакетный запуск всегда сохраняет траектории (это его основная цель).

Примеры с нулевыми рассуждениями во всех ходах автоматически отбрасываются пакетным запуском, чтобы не загрязнять обучающие данные примерами без рассуждений.