# Формат траєкторії

Hermes Agent зберігає траєкторії розмов у форматі JSONL, сумісному з ShareGPT,
для використання як навчальних даних, артефактів налагодження та наборів даних підкріплювального навчання.

Вихідні файли: `agent/trajectory.py`, `run_agent.py` (шукайте `_save_trajectory`), `batch_runner.py`


## Конвенція іменування файлів

Траєкторії записуються у файли в поточному робочому каталозі:

| Файл | Коли |
|------|------|
| `trajectory_samples.jsonl` | Розмови, які успішно завершились (`completed=True`) |
| `failed_trajectories.jsonl` | Розмови, які завершились помилкою або були перервані (`completed=False`) |

Пакетний запуск (`batch_runner.py`) записує у власний файл виводу для кожного батчу
(наприклад, `batch_001_output.jsonl`) з додатковими полями метаданих.

Назву файлу можна перевизначити за допомогою параметра `filename` у `save_trajectory()`.


## Формат запису JSONL

Кожен рядок у файлі — це самодостатній JSON‑об’єкт. Існує два варіанти:

### Формат CLI/Інтерактивний (з `_save_trajectory`)

```json
{
  "conversations": [ ... ],
  "timestamp": "2026-03-30T14:22:31.456789",
  "model": "anthropic/claude-sonnet-4.6",
  "completed": true
}
```

### Формат пакетного запуску (з `batch_runner.py`)

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

Словники `tool_stats` та `tool_error_counts` нормалізуються, щоб включати
ВСІ можливі інструменти (з `model_tools.TOOL_TO_TOOLSET_MAP`) зі значенням 0 за замовчуванням,
забезпечуючи єдину схему для всіх записів під час завантаження набору даних HuggingFace.


## Масив `conversations` (формат ShareGPT)

Масив `conversations` використовує ролі ShareGPT:

| API‑роль | ShareGPT `from` |
|----------|-----------------|
| system | `"system"` |
| user | `"human"` |
| assistant | `"gpt"` |
| tool | `"tool"` |

### Повний приклад

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


## Правила нормалізації

### Маркування змісту роздумів

Конвертер траєкторій нормалізує ВСІ роздуми у теги `<think>`, незалежно від того,
як їх спочатку згенерувала модель:

1. **Нативні токени роздумів** (`msg["reasoning"]` від провайдерів типу Anthropic, OpenAI o‑series): обгортаються як `<think>\n{reasoning}\n</think>\n` і додаються перед вмістом.

2. **XML‑блок REASONING_SCRATCHPAD** (коли нативні роздуми вимкнено і модель розмірковує через XML‑інструкції): теги `<REASONING_SCRATCHPAD>` перетворюються у `<think>` за допомогою `convert_scratchpad_to_think()`.

3. **Порожні блоки think**: Кожен хід `gpt` гарантовано містить блок `<think>`. Якщо роздумів не було, вставляється порожній блок: `<think>\n</think>\n` — це забезпечує однорідний формат для навчальних даних.

### Нормалізація викликів інструментів

Виклики інструментів у форматі API (з `tool_call_id`, назвою функції, аргументами у вигляді JSON‑рядка) конвертуються у JSON, обгорнутий XML:

```
<tool_call>
{"name": "terminal", "arguments": {"command": "ls -la"}}
</tool_call>
```

- Аргументи парсяться з JSON‑рядків назад у об’єкти (не подвійно кодуються)
- Якщо парсинг JSON не вдається (не повинно траплятись — перевіряється під час розмови), використовується порожній `{}` з попередженням у логах
- Кілька викликів інструментів в одному ході асистента створюють кілька блоків `<tool_call>` в одному повідомленні `gpt`

### Нормалізація відповідей інструментів

Всі результати інструментів, що йдуть після повідомлення асистента, групуються в один хід `tool` з JSON, обгорнутим у XML:

```
<tool_response>
{"tool_call_id": "call_abc123", "name": "terminal", "content": "output here"}
</tool_response>
```

- Якщо вміст інструменту виглядає як JSON (починається з `{` або `[`), він парситься, і поле `content` містить об’єкт/масив JSON, а не рядок
- Кілька результатів інструментів об’єднуються новими рядками в одному повідомленні
- Назва інструменту підбирається за позицією у масиві `tool_calls` батьківського повідомлення `gpt`

### Системне повідомлення

Системне повідомлення генерується під час збереження (не береться з розмови).
Воно слідує шаблону підказки Hermes для функціонального виклику і містить:

- Преамбулу, що пояснює протокол функціонального виклику
- XML‑блок `<tools>` з JSON‑визначеннями інструментів
- Посилання на схему об’єктів `FunctionCall`
- Приклад `<tool_call>`

Визначення інструментів включають `name`, `description`, `parameters` та `required` (встановлено `null` для відповідності канонічному формату).


## Завантаження траєкторій

Траєкторії — це звичайний JSONL, їх можна завантажити будь‑яким читачем JSON‑рядків:

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

### Завантаження для наборів даних HuggingFace

```python
from datasets import load_dataset

ds = load_dataset("json", data_files="trajectory_samples.jsonl")
```

Нормалізована схема `tool_stats` гарантує, що у всіх записів однакові стовпці,
уникаючи помилок невідповідності схеми Arrow під час завантаження набору даних.


## Керування збереженням траєкторій

У CLI збереження траєкторій контролюється за допомогою:

```yaml
# config.yaml
agent:
  save_trajectories: true  # default: false
```

Або прапорцем `--save-trajectories`. Коли агент ініціалізується з `save_trajectories=True`, метод `_save_trajectory()` викликається в кінці кожного ходу розмови.

Пакетний запуск завжди зберігає траєкторії (це його основна мета).

Зразки без роздумів у всіх ходах автоматично відкидаються пакетним запуском, щоб не забруднювати навчальні дані прикладами без роздумів.