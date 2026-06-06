---
title: "Outlines — Outlines: структурована генерація JSON/regex/Pydantic LLM"
sidebar_label: "Outlines"
description: "Контури: structured JSON/regex/Pydantic LLM generation"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Outlines

Outlines: структурована генерація JSON/regex/Pydantic LLM.

## Метадані навички

| | |
|---|---|
| Джерело | Optional — install with `hermes skills install official/mlops/outlines` |
| Шлях | `optional-skills/mlops/inference/outlines` |
| Версія | `1.0.0` |
| Автор | Orchestra Research |
| Ліцензія | MIT |
| Залежності | `outlines`, `transformers`, `vllm`, `pydantic` |
| Платформи | linux, macos, windows |
| Теги | `Prompt Engineering`, `Outlines`, `Structured Generation`, `JSON Schema`, `Pydantic`, `Local Models`, `Grammar-Based Generation`, `vLLM`, `Transformers`, `Type Safety` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Outlines: Structured Text Generation

## Коли використовувати цю навичку

Використовуй Outlines, коли потрібно:
- **Гарантувати коректну структуру JSON/XML/коду** під час генерації
- **Використовувати моделі Pydantic** для типобезпечних результатів
- **Підтримувати локальні моделі** (Transformers, llama.cpp, vLLM)
- **Максимізувати швидкість інференсу** без накладних витрат
- **Автоматично генерувати за JSON‑схемами**
- **Керувати семплінгом токенів** на рівні граматики

**GitHub Stars**: 8,000+ | **From**: dottxt.ai (formerly .txt)

## Встановлення

```bash
# Base installation
pip install outlines

# With specific backends
pip install outlines transformers  # Hugging Face models
pip install outlines llama-cpp-python  # llama.cpp
pip install outlines vllm  # vLLM for high-throughput
```

## Швидкий старт

### Основний приклад: Класифікація

```python
import outlines
from typing import Literal

# Load model
model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")

# Generate with type constraint
prompt = "Sentiment of 'This product is amazing!': "
generator = outlines.generate.choice(model, ["positive", "negative", "neutral"])
sentiment = generator(prompt)

print(sentiment)  # "positive" (guaranteed one of these)
```

### З моделями Pydantic

```python
from pydantic import BaseModel
import outlines

class User(BaseModel):
    name: str
    age: int
    email: str

model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")

# Generate structured output
prompt = "Extract user: John Doe, 30 years old, john@example.com"
generator = outlines.generate.json(model, User)
user = generator(prompt)

print(user.name)   # "John Doe"
print(user.age)    # 30
print(user.email)  # "john@example.com"
```

## Основні концепції

### 1. Обмежене семплювання токенів

Outlines використовує скінченні автомати (FSM) для обмеження генерації токенів на рівні логітів.

**Як це працює:**
1. Перетворює схему (JSON/Pydantic/regex) у контекстно‑вільну граматику (CFG)
2. Перетворює CFG у скінченний автомат (FSM)
3. Фільтрує недійсні токени на кожному кроці генерації
4. Швидко переходить вперед, коли залишився лише один дійсний токен

**Переваги:**
- **Нульова накладна**: Фільтрація відбувається на рівні токенів
- **Покращення швидкості**: Швидке просування через детерміновані шляхи
- **Гарантована валідність**: Неможливі недійсні результати

```python
import outlines

# Pydantic model -> JSON schema -> CFG -> FSM
class Person(BaseModel):
    name: str
    age: int

model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")

# Behind the scenes:
# 1. Person -> JSON schema
# 2. JSON schema -> CFG
# 3. CFG -> FSM
# 4. FSM filters tokens during generation

generator = outlines.generate.json(model, Person)
result = generator("Generate person: Alice, 25")
```

### 2. Структуровані генератори

Outlines надає спеціалізовані генератори для різних типів вихідних даних.

#### Генератор вибору

```python
# Multiple choice selection
generator = outlines.generate.choice(
    model,
    ["positive", "negative", "neutral"]
)

sentiment = generator("Review: This is great!")
# Result: One of the three choices
```

#### Генератор JSON

```python
from pydantic import BaseModel

class Product(BaseModel):
    name: str
    price: float
    in_stock: bool

# Generate valid JSON matching schema
generator = outlines.generate.json(model, Product)
product = generator("Extract: iPhone 15, $999, available")

# Guaranteed valid Product instance
print(type(product))  # <class '__main__.Product'>
```

#### Генератор regex

```python
# Generate text matching regex
generator = outlines.generate.regex(
    model,
    r"[0-9]{3}-[0-9]{3}-[0-9]{4}"  # Phone number pattern
)

phone = generator("Generate phone number:")
# Result: "555-123-4567" (guaranteed to match pattern)
```

#### Генератори цілих/дробових чисел

```python
# Generate specific numeric types
int_generator = outlines.generate.integer(model)
age = int_generator("Person's age:")  # Guaranteed integer

float_generator = outlines.generate.float(model)
price = float_generator("Product price:")  # Guaranteed float
```

### 3. Бекенди моделей

Outlines підтримує кілька локальних та API‑базованих бекендів.

#### Transformers (Hugging Face)

```python
import outlines

# Load from Hugging Face
model = outlines.models.transformers(
    "microsoft/Phi-3-mini-4k-instruct",
    device="cuda"  # Or "cpu"
)

# Use with any generator
generator = outlines.generate.json(model, YourModel)
```

#### llama.cpp

```python
# Load GGUF model
model = outlines.models.llamacpp(
    "./models/llama-3.1-8b-instruct.Q4_K_M.gguf",
    n_gpu_layers=35
)

generator = outlines.generate.json(model, YourModel)
```

#### vLLM (High Throughput)

```python
# For production deployments
model = outlines.models.vllm(
    "meta-llama/Llama-3.1-8B-Instruct",
    tensor_parallel_size=2  # Multi-GPU
)

generator = outlines.generate.json(model, YourModel)
```

#### OpenAI (Обмежена підтримка)

```python
# Basic OpenAI support
model = outlines.models.openai(
    "gpt-4o-mini",
    api_key="your-api-key"
)

# Note: Some features limited with API models
generator = outlines.generate.json(model, YourModel)
```

### 4. Інтеграція Pydantic

Outlines має повноцінну підтримку Pydantic з автоматичним перекладом схеми.

#### Базові моделі

```python
from pydantic import BaseModel, Field

class Article(BaseModel):
    title: str = Field(description="Article title")
    author: str = Field(description="Author name")
    word_count: int = Field(description="Number of words", gt=0)
    tags: list[str] = Field(description="List of tags")

model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")
generator = outlines.generate.json(model, Article)

article = generator("Generate article about AI")
print(article.title)
print(article.word_count)  # Guaranteed > 0
```

#### Вкладені моделі

```python
class Address(BaseModel):
    street: str
    city: str
    country: str

class Person(BaseModel):
    name: str
    age: int
    address: Address  # Nested model

generator = outlines.generate.json(model, Person)
person = generator("Generate person in New York")

print(person.address.city)  # "New York"
```

#### Перелічення та літерали

```python
from enum import Enum
from typing import Literal

class Status(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class Application(BaseModel):
    applicant: str
    status: Status  # Must be one of enum values
    priority: Literal["low", "medium", "high"]  # Must be one of literals

generator = outlines.generate.json(model, Application)
app = generator("Generate application")

print(app.status)  # Status.PENDING (or APPROVED/REJECTED)
```

## Типові шаблони

### Шаблон 1: Видобуток даних

```python
from pydantic import BaseModel
import outlines

class CompanyInfo(BaseModel):
    name: str
    founded_year: int
    industry: str
    employees: int

model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")
generator = outlines.generate.json(model, CompanyInfo)

text = """
Apple Inc. was founded in 1976 in the technology industry.
The company employs approximately 164,000 people worldwide.
"""

prompt = f"Extract company information:\n{text}\n\nCompany:"
company = generator(prompt)

print(f"Name: {company.name}")
print(f"Founded: {company.founded_year}")
print(f"Industry: {company.industry}")
print(f"Employees: {company.employees}")
```

### Шаблон 2: Класифікація

```python
from typing import Literal
import outlines

model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")

# Binary classification
generator = outlines.generate.choice(model, ["spam", "not_spam"])
result = generator("Email: Buy now! 50% off!")

# Multi-class classification
categories = ["technology", "business", "sports", "entertainment"]
category_gen = outlines.generate.choice(model, categories)
category = category_gen("Article: Apple announces new iPhone...")

# With confidence
class Classification(BaseModel):
    label: Literal["positive", "negative", "neutral"]
    confidence: float

classifier = outlines.generate.json(model, Classification)
result = classifier("Review: This product is okay, nothing special")
```

### Шаблон 3: Структуровані форми

```python
class UserProfile(BaseModel):
    full_name: str
    age: int
    email: str
    phone: str
    country: str
    interests: list[str]

model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")
generator = outlines.generate.json(model, UserProfile)

prompt = """
Extract user profile from:
Name: Alice Johnson
Age: 28
Email: alice@example.com
Phone: 555-0123
Country: USA
Interests: hiking, photography, cooking
"""

profile = generator(prompt)
print(profile.full_name)
print(profile.interests)  # ["hiking", "photography", "cooking"]
```

### Шаблон 4: Видобуток кількох сутностей

```python
class Entity(BaseModel):
    name: str
    type: Literal["PERSON", "ORGANIZATION", "LOCATION"]

class DocumentEntities(BaseModel):
    entities: list[Entity]

model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")
generator = outlines.generate.json(model, DocumentEntities)

text = "Tim Cook met with Satya Nadella at Microsoft headquarters in Redmond."
prompt = f"Extract entities from: {text}"

result = generator(prompt)
for entity in result.entities:
    print(f"{entity.name} ({entity.type})")
```

### Шаблон 5: Генерація коду

```python
class PythonFunction(BaseModel):
    function_name: str
    parameters: list[str]
    docstring: str
    body: str

model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")
generator = outlines.generate.json(model, PythonFunction)

prompt = "Generate a Python function to calculate factorial"
func = generator(prompt)

print(f"def {func.function_name}({', '.join(func.parameters)}):")
print(f'    """{func.docstring}"""')
print(f"    {func.body}")
```

### Шаблон 6: Пакетна обробка

```python
def batch_extract(texts: list[str], schema: type[BaseModel]):
    """Extract structured data from multiple texts."""
    model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")
    generator = outlines.generate.json(model, schema)

    results = []
    for text in texts:
        result = generator(f"Extract from: {text}")
        results.append(result)

    return results

class Person(BaseModel):
    name: str
    age: int

texts = [
    "John is 30 years old",
    "Alice is 25 years old",
    "Bob is 40 years old"
]

people = batch_extract(texts, Person)
for person in people:
    print(f"{person.name}: {person.age}")
```

## Налаштування бекенду

### Transformers

```python
import outlines

# Basic usage
model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")

# GPU configuration
model = outlines.models.transformers(
    "microsoft/Phi-3-mini-4k-instruct",
    device="cuda",
    model_kwargs={"torch_dtype": "float16"}
)

# Popular models
model = outlines.models.transformers("meta-llama/Llama-3.1-8B-Instruct")
model = outlines.models.transformers("mistralai/Mistral-7B-Instruct-v0.3")
model = outlines.models.transformers("Qwen/Qwen2.5-7B-Instruct")
```

### llama.cpp

```python
# Load GGUF model
model = outlines.models.llamacpp(
    "./models/llama-3.1-8b.Q4_K_M.gguf",
    n_ctx=4096,         # Context window
    n_gpu_layers=35,    # GPU layers
    n_threads=8         # CPU threads
)

# Full GPU offload
model = outlines.models.llamacpp(
    "./models/model.gguf",
    n_gpu_layers=-1  # All layers on GPU
)
```

### vLLM (Production)

```python
# Single GPU
model = outlines.models.vllm("meta-llama/Llama-3.1-8B-Instruct")

# Multi-GPU
model = outlines.models.vllm(
    "meta-llama/Llama-3.1-70B-Instruct",
    tensor_parallel_size=4  # 4 GPUs
)

# With quantization
model = outlines.models.vllm(
    "meta-llama/Llama-3.1-8B-Instruct",
    quantization="awq"  # Or "gptq"
)
```

## Кращі практики

### 1. Використовуй конкретні типи

```python
# ✅ Good: Specific types
class Product(BaseModel):
    name: str
    price: float  # Not str
    quantity: int  # Not str
    in_stock: bool  # Not str

# ❌ Bad: Everything as string
class Product(BaseModel):
    name: str
    price: str  # Should be float
    quantity: str  # Should be int
```

### 2. Додавай обмеження

```python
from pydantic import Field

# ✅ Good: With constraints
class User(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=0, le=120)
    email: str = Field(pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")

# ❌ Bad: No constraints
class User(BaseModel):
    name: str
    age: int
    email: str
```

### 3. Використовуй перелічення для категорій

```python
# ✅ Good: Enum for fixed set
class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Task(BaseModel):
    title: str
    priority: Priority

# ❌ Bad: Free-form string
class Task(BaseModel):
    title: str
    priority: str  # Can be anything
```

### 4. Надавай контекст у підказках

```python
# ✅ Good: Clear context
prompt = """
Extract product information from the following text.
Text: iPhone 15 Pro costs $999 and is currently in stock.
Product:
"""

# ❌ Bad: Minimal context
prompt = "iPhone 15 Pro costs $999 and is currently in stock."
```

### 5. Обробляй необов’язкові поля

```python
from typing import Optional

# ✅ Good: Optional fields for incomplete data
class Article(BaseModel):
    title: str  # Required
    author: Optional[str] = None  # Optional
    date: Optional[str] = None  # Optional
    tags: list[str] = []  # Default empty list

# Can succeed even if author/date missing
```

## Порівняння з альтернативами

| Feature | Outlines | Instructor | Guidance | LMQL |
|---------|----------|------------|----------|------|
| Pydantic Support | ✅ Native | ✅ Native | ❌ No | ❌ No |
| JSON Schema | ✅ Yes | ✅ Yes | ⚠️ Limited | ✅ Yes |
| Regex Constraints | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes |
| Local Models | ✅ Full | ⚠️ Limited | ✅ Full | ✅ Full |
| API Models | ⚠️ Limited | ✅ Full | ✅ Full | ✅ Full |
| Zero Overhead | ✅ Yes | ❌ No | ⚠️ Partial | ✅ Yes |
| Automatic Retrying | ❌ No | ✅ Yes | ❌ No | ❌ No |
| Крива навчання | Low | Low | Low | High |

**Коли обирати Outlines:**
- Використання локальних моделей (Transformers, llama.cpp, vLLM)
- Потрібна максимальна швидкість інференсу
- Потрібна підтримка моделей Pydantic
- Необхідна генерація без накладних витрат
- Потрібен контроль процесу семплювання токенів

**Коли обирати альтернативи:**
- Instructor: Потрібні API‑моделі з автоматичним повторним запитом
- Guidance: Потрібне зцілення токенів та складні робочі процеси
- LMQL: Перевага декларативного синтаксису запитів

## Характеристики продуктивності

**Швидкість:**
- **Нульова накладна**: Структурована генерація така ж швидка, як і без обмежень
- **Оптимізація швидкого переходу**: Пропускає детерміновані токени
- **1.2‑2x швидше** ніж підходи з пост‑генераційною валідацією

**Пам'ять:**
- FSM компілюється один раз на схему (кешується)
- Мінімальні накладні під час виконання
- Ефективно працює з vLLM для високої пропускної здатності

**Точність:**
- **100% валідних результатів** (гарантує FSM)
- Не потрібні цикли повторних спроб
- Детерміноване фільтрування токенів

## Ресурси

- **Documentation**: https://outlines-dev.github.io/outlines
- **GitHub**: https://github.com/outlines-dev/outlines (8k+ stars)
- **Discord**: https://discord.gg/R9DSu34mGd
- **Blog**: https://blog.dottxt.co

## Дивись також

- `references/json_generation.md` - Comprehensive JSON and Pydantic patterns
- `references/backends.md` - Backend-specific configuration
- `references/examples.md` - Production-ready examples