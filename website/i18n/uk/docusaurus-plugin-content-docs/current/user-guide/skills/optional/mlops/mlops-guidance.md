---
title: "Керівництво"
sidebar_label: "Guidance"
description: "Керуй виводом LLM за допомогою regex та граматик, гарантуй генерацію дійсного JSON/XML/коду, забезпечуй структуровані формати та створюй багатокрокові робочі процеси з Guidance"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Guidance

Керуй виводом LLM за допомогою regex та граматик, гарантуй коректну генерацію JSON/XML/коду, впроваджуй структуровані формати та створюй багатокрокові робочі процеси за допомогою Guidance — фреймворку обмеженої генерації від Microsoft Research

## Метадані навички

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/mlops/guidance` |
| Path | `optional-skills/mlops/guidance` |
| Version | `1.0.0` |
| Author | Orchestra Research |
| License | MIT |
| Dependencies | `guidance`, `transformers` |
| Platforms | linux, macos, windows |
| Tags | `Prompt Engineering`, `Guidance`, `Constrained Generation`, `Structured Output`, `JSON Validation`, `Grammar`, `Microsoft Research`, `Format Enforcement`, `Multi-Step Workflows` |

## Reference: full SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# Guidance: Constrained LLM Generation

## Коли використовувати цю навичку

Використовуй Guidance, коли потрібно:
- **Контролювати синтаксис виводу LLM** за допомогою regex або граматик
- **Гарантувати коректну генерацію JSON/XML/коду**
- **Зменшити затримку** у порівнянні з традиційними підходами до підказок
- **Впроваджувати структуровані формати** (дати, електронні листи, ідентифікатори тощо)
- **Створювати багатокрокові робочі процеси** з Python‑подібним керуванням потоком
- **Запобігати некоректним виводам** через граматичні обмеження

**GitHub Stars**: 18 000+ | **From**: Microsoft Research

## Встановлення

```bash
# Base installation
pip install guidance

# With specific backends
pip install guidance[transformers]  # Hugging Face models
pip install guidance[llama_cpp]     # llama.cpp models
```

## Швидкий старт

### Основний приклад: структурована генерація

```python
from guidance import models, gen

# Load model (supports OpenAI, Transformers, llama.cpp)
lm = models.OpenAI("gpt-4")

# Generate with constraints
result = lm + "The capital of France is " + gen("capital", max_tokens=5)

print(result["capital"])  # "Paris"
```

### З Anthropic Claude

```python
from guidance import models, gen, system, user, assistant

# Configure Claude
lm = models.Anthropic("claude-sonnet-4-5-20250929")

# Use context managers for chat format
with system():
    lm += "You are a helpful assistant."

with user():
    lm += "What is the capital of France?"

with assistant():
    lm += gen(max_tokens=20)
```

## Основні концепції

### 1. Менеджери контексту

Guidance використовує Python‑подібні менеджери контексту для взаємодії у стилі чату.

```python
from guidance import system, user, assistant, gen

lm = models.Anthropic("claude-sonnet-4-5-20250929")

# System message
with system():
    lm += "You are a JSON generation expert."

# User message
with user():
    lm += "Generate a person object with name and age."

# Assistant response
with assistant():
    lm += gen("response", max_tokens=100)

print(lm["response"])
```

**Переваги:**
- Натуральний чат‑потік
- Чітке розділення ролей
- Легко читати та підтримувати

### 2. Обмежена генерація

Guidance забезпечує відповідність виводу заданим шаблонам за допомогою regex або граматик.

#### Regex‑обмеження

```python
from guidance import models, gen

lm = models.Anthropic("claude-sonnet-4-5-20250929")

# Constrain to valid email format
lm += "Email: " + gen("email", regex=r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# Constrain to date format (YYYY-MM-DD)
lm += "Date: " + gen("date", regex=r"\d{4}-\d{2}-\d{2}")

# Constrain to phone number
lm += "Phone: " + gen("phone", regex=r"\d{3}-\d{3}-\d{4}")

print(lm["email"])  # Guaranteed valid email
print(lm["date"])   # Guaranteed YYYY-MM-DD format
```

**Як це працює:**
- Regex перетворюється у граматику на рівні токенів
- Некоректні токени фільтруються під час генерації
- Модель може генерувати лише відповідні виводи

#### Вибіркові обмеження

```python
from guidance import models, gen, select

lm = models.Anthropic("claude-sonnet-4-5-20250929")

# Constrain to specific choices
lm += "Sentiment: " + select(["positive", "negative", "neutral"], name="sentiment")

# Multiple-choice selection
lm += "Best answer: " + select(
    ["A) Paris", "B) London", "C) Berlin", "D) Madrid"],
    name="answer"
)

print(lm["sentiment"])  # One of: positive, negative, neutral
print(lm["answer"])     # One of: A, B, C, or D
```

### 3. Зцілення токенів

Guidance автоматично «зцілює» межі токенів між підказкою та генерацією.

**Проблема:** Токенізація створює незручні межі.

```python
# Without token healing
prompt = "The capital of France is "
# Last token: " is "
# First generated token might be " Par" (with leading space)
# Result: "The capital of France is  Paris" (double space!)
```

**Рішення:** Guidance відкочує один токен назад і генерує заново.

```python
from guidance import models, gen

lm = models.Anthropic("claude-sonnet-4-5-20250929")

# Token healing enabled by default
lm += "The capital of France is " + gen("capital", max_tokens=5)
# Result: "The capital of France is Paris" (correct spacing)
```

**Переваги:**
- Натуральні межі тексту
- Відсутність незручних пробілів
- Краща продуктивність моделі (бачить природні послідовності токенів)

### 4. Генерація на основі граматики

Визначай складні структури за допомогою контекстно‑вільних граматик.

```python
from guidance import models, gen

lm = models.Anthropic("claude-sonnet-4-5-20250929")

# JSON grammar (simplified)
json_grammar = """
{
    "name": <gen name regex="[A-Za-z ]+" max_tokens=20>,
    "age": <gen age regex="[0-9]+" max_tokens=3>,
    "email": <gen email regex="[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}" max_tokens=50>
}
"""

# Generate valid JSON
lm += gen("person", grammar=json_grammar)

print(lm["person"])  # Guaranteed valid JSON structure
```

**Випадки використання:**
- Складні структуровані виводи
- Вкладені структури даних
- Синтаксис мов програмування
- Спеціалізовані доменні мови

### 5. Функції Guidance

Створюй багаторазові шаблони генерації за допомогою декоратора `@guidance`.

```python
from guidance import guidance, gen, models

@guidance
def generate_person(lm):
    """Generate a person with name and age."""
    lm += "Name: " + gen("name", max_tokens=20, stop="\n")
    lm += "\nAge: " + gen("age", regex=r"[0-9]+", max_tokens=3)
    return lm

# Use the function
lm = models.Anthropic("claude-sonnet-4-5-20250929")
lm = generate_person(lm)

print(lm["name"])
print(lm["age"])
```

**Станові функції:**

```python
@guidance(stateless=False)
def react_agent(lm, question, tools, max_rounds=5):
    """ReAct agent with tool use."""
    lm += f"Question: {question}\n\n"

    for i in range(max_rounds):
        # Thought
        lm += f"Thought {i+1}: " + gen("thought", stop="\n")

        # Action
        lm += "\nAction: " + select(list(tools.keys()), name="action")

        # Execute tool
        tool_result = tools[lm["action"]]()
        lm += f"\nObservation: {tool_result}\n\n"

        # Check if done
        lm += "Done? " + select(["Yes", "No"], name="done")
        if lm["done"] == "Yes":
            break

    # Final answer
    lm += "\nFinal Answer: " + gen("answer", max_tokens=100)
    return lm
```

## Налаштування бекенду

### Anthropic Claude

```python
from guidance import models

lm = models.Anthropic(
    model="claude-sonnet-4-5-20250929",
    api_key="your-api-key"  # Or set ANTHROPIC_API_KEY env var
)
```

### OpenAI

```python
lm = models.OpenAI(
    model="gpt-4o-mini",
    api_key="your-api-key"  # Or set OPENAI_API_KEY env var
)
```

### Локальні моделі (Transformers)

```python
from guidance.models import Transformers

lm = Transformers(
    "microsoft/Phi-4-mini-instruct",
    device="cuda"  # Or "cpu"
)
```

### Локальні моделі (llama.cpp)

```python
from guidance.models import LlamaCpp

lm = LlamaCpp(
    model_path="/path/to/model.gguf",
    n_ctx=4096,
    n_gpu_layers=35
)
```

## Типові шаблони

### Шаблон 1: Генерація JSON

```python
from guidance import models, gen, system, user, assistant

lm = models.Anthropic("claude-sonnet-4-5-20250929")

with system():
    lm += "You generate valid JSON."

with user():
    lm += "Generate a user profile with name, age, and email."

with assistant():
    lm += """{
    "name": """ + gen("name", regex=r'"[A-Za-z ]+"', max_tokens=30) + """,
    "age": """ + gen("age", regex=r"[0-9]+", max_tokens=3) + """,
    "email": """ + gen("email", regex=r'"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"', max_tokens=50) + """
}"""

print(lm)  # Valid JSON guaranteed
```

### Шаблон 2: Класифікація

```python
from guidance import models, gen, select

lm = models.Anthropic("claude-sonnet-4-5-20250929")

text = "This product is amazing! I love it."

lm += f"Text: {text}\n"
lm += "Sentiment: " + select(["positive", "negative", "neutral"], name="sentiment")
lm += "\nConfidence: " + gen("confidence", regex=r"[0-9]+", max_tokens=3) + "%"

print(f"Sentiment: {lm['sentiment']}")
print(f"Confidence: {lm['confidence']}%")
```

### Шаблон 3: Багатокрокове мислення

```python
from guidance import models, gen, guidance

@guidance
def chain_of_thought(lm, question):
    """Generate answer with step-by-step reasoning."""
    lm += f"Question: {question}\n\n"

    # Generate multiple reasoning steps
    for i in range(3):
        lm += f"Step {i+1}: " + gen(f"step_{i+1}", stop="\n", max_tokens=100) + "\n"

    # Final answer
    lm += "\nTherefore, the answer is: " + gen("answer", max_tokens=50)

    return lm

lm = models.Anthropic("claude-sonnet-4-5-20250929")
lm = chain_of_thought(lm, "What is 15% of 200?")

print(lm["answer"])
```

### Шаблон 4: ReAct агент

```python
from guidance import models, gen, select, guidance

@guidance(stateless=False)
def react_agent(lm, question):
    """ReAct agent with tool use."""
    tools = {
        "calculator": lambda expr: eval(expr),
        "search": lambda query: f"Search results for: {query}",
    }

    lm += f"Question: {question}\n\n"

    for round in range(5):
        # Thought
        lm += f"Thought: " + gen("thought", stop="\n") + "\n"

        # Action selection
        lm += "Action: " + select(["calculator", "search", "answer"], name="action")

        if lm["action"] == "answer":
            lm += "\nFinal Answer: " + gen("answer", max_tokens=100)
            break

        # Action input
        lm += "\nAction Input: " + gen("action_input", stop="\n") + "\n"

        # Execute tool
        if lm["action"] in tools:
            result = tools[lm["action"]](lm["action_input"])
            lm += f"Observation: {result}\n\n"

    return lm

lm = models.Anthropic("claude-sonnet-4-5-20250929")
lm = react_agent(lm, "What is 25 * 4 + 10?")
print(lm["answer"])
```

### Шаблон 5: Видобуток даних

```python
from guidance import models, gen, guidance

@guidance
def extract_entities(lm, text):
    """Extract structured entities from text."""
    lm += f"Text: {text}\n\n"

    # Extract person
    lm += "Person: " + gen("person", stop="\n", max_tokens=30) + "\n"

    # Extract organization
    lm += "Organization: " + gen("organization", stop="\n", max_tokens=30) + "\n"

    # Extract date
    lm += "Date: " + gen("date", regex=r"\d{4}-\d{2}-\d{2}", max_tokens=10) + "\n"

    # Extract location
    lm += "Location: " + gen("location", stop="\n", max_tokens=30) + "\n"

    return lm

text = "Tim Cook announced at Apple Park on 2024-09-15 in Cupertino."

lm = models.Anthropic("claude-sonnet-4-5-20250929")
lm = extract_entities(lm, text)

print(f"Person: {lm['person']}")
print(f"Organization: {lm['organization']}")
print(f"Date: {lm['date']}")
print(f"Location: {lm['location']}")
```

## Кращі практики

### 1. Використовуй Regex для валідації формату

```python
# ✅ Good: Regex ensures valid format
lm += "Email: " + gen("email", regex=r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# ❌ Bad: Free generation may produce invalid emails
lm += "Email: " + gen("email", max_tokens=50)
```

### 2. Використовуй select() для фіксованих категорій

```python
# ✅ Good: Guaranteed valid category
lm += "Status: " + select(["pending", "approved", "rejected"], name="status")

# ❌ Bad: May generate typos or invalid values
lm += "Status: " + gen("status", max_tokens=20)
```

### 3. Використовуй зцілення токенів

```python
# Token healing is enabled by default
# No special action needed - just concatenate naturally
lm += "The capital is " + gen("capital")  # Automatic healing
```

### 4. Використовуй стоп‑послідовності

```python
# ✅ Good: Stop at newline for single-line outputs
lm += "Name: " + gen("name", stop="\n")

# ❌ Bad: May generate multiple lines
lm += "Name: " + gen("name", max_tokens=50)
```

### 5. Створюй багаторазові функції

```python
# ✅ Good: Reusable pattern
@guidance
def generate_person(lm):
    lm += "Name: " + gen("name", stop="\n")
    lm += "\nAge: " + gen("age", regex=r"[0-9]+")
    return lm

# Use multiple times
lm = generate_person(lm)
lm += "\n\n"
lm = generate_person(lm)
```

### 6. Балансуй обмеження

```python
# ✅ Good: Reasonable constraints
lm += gen("name", regex=r"[A-Za-z ]+", max_tokens=30)

# ❌ Too strict: May fail or be very slow
lm += gen("name", regex=r"^(John|Jane)$", max_tokens=10)
```

## Порівняння з альтернативами

| Feature | Guidance | Instructor | Outlines | LMQL |
|---------|----------|------------|----------|------|
| Regex Constraints | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes |
| Grammar Support | ✅ CFG | ❌ No | ✅ CFG | ✅ CFG |
| Pydantic Validation | ❌ No | ✅ Yes | ✅ Yes | ❌ No |
| Token Healing | ✅ Yes | ❌ No | ✅ Yes | ❌ No |
| Local Models | ✅ Yes | ⚠️ Limited | ✅ Yes | ✅ Yes |
| API Models | ✅ Yes | ✅ Yes | ⚠️ Limited | ✅ Yes |
| Pythonic Syntax | ✅ Yes | ✅ Yes | ✅ Yes | ❌ SQL-like |
| Learning Curve | Low | Low | Medium | High |

**Коли обирати Guidance:**
- Потрібні regex/grammar обмеження
- Потрібне зцілення токенів
- Створення складних робочих процесів з керуванням потоком
- Використання локальних моделей (Transformers, llama.cpp)
- Перевага Python‑подібного синтаксису

**Коли обирати альтернативи:**
- Instructor: потрібна валідація Pydantic з автоматичним повторенням
- Outlines: потрібна валідація JSON‑схеми
- LMQL: перевага декларативного синтаксису запитів

## Характеристики продуктивності

**Зниження затримки:**
- 30‑50 % швидше, ніж традиційне підказування для обмежених виводів
- Зцілення токенів зменшує непотрібні повторні генерації
- Граматичні обмеження запобігають генерації некоректних токенів

**Використання пам'яті:**
- Мінімальне навантаження порівняно з неконтрольованою генерацією
- Компіляція граматик кешується після першого використання
- Ефективне фільтрування токенів під час інференсу

**Ефективність токенів:**
- Запобігає марнотраті токенів на некоректні виводи
- Не потребує циклів повтору
- Прямий шлях до валідних результатів

## Ресурси

- **Documentation**: https://guidance.readthedocs.io
- **GitHub**: https://github.com/guidance-ai/guidance (18k+ stars)
- **Notebooks**: https://github.com/guidance-ai/guidance/tree/main/notebooks
- **Discord**: Community support available

## Дивись також

- `references/constraints.md` — Comprehensive regex and grammar patterns
- `references/backends.md` — Backend-specific configuration
- `references/examples.md` — Production-ready examples