---
title: "Инструктор"
sidebar_label: "Instructor"
description: "Извлекай структурированные данные из ответов LLM с валидацией Pydantic, автоматически повторяй неудачные извлечения, разбирай сложный JSON с типобезопасностью и потоковой передачей."
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Instructor

Извлекай структурированные данные из ответов LLM с проверкой Pydantic, автоматически повторяй неудачные извлечения, разбирай сложный JSON с типобезопасностью и передавай частичные результаты с помощью Instructor — проверенная временем библиотека для структурированного вывода

## Метаданные навыка

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/mlops/instructor` |
| Path | `optional-skills/mlops/instructor` |
| Version | `1.0.0` |
| Author | Orchestra Research |
| License | MIT |
| Dependencies | `instructor`, `pydantic`, `openai`, `anthropic` |
| Platforms | linux, macos, windows |
| Tags | `Prompt Engineering`, `Instructor`, `Structured Output`, `Pydantic`, `Data Extraction`, `JSON Parsing`, `Type Safety`, `Validation`, `Streaming`, `OpenAI`, `Anthropic` |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает при его активации. Это то, что агент видит как инструкции, когда навык активен.
:::

# Instructor: Структурированные выводы LLM

## Когда использовать этот навык

Используй Instructor, когда нужно:
- **Извлекать структурированные данные** из ответов LLM надёжно
- **Валидировать выводы** автоматически по схемам Pydantic
- **Повторять неудачные извлечения** с автоматической обработкой ошибок
- **Разбирать сложный JSON** с типобезопасностью и валидацией
- **Стримить частичные результаты** для обработки в реальном времени
- **Поддерживать несколько провайдеров LLM** с единым API

**GitHub Stars**: 15 000+ | **Проверено в бою**: 100 000+ разработчиков

## Установка

```bash
# Base installation
pip install instructor

# With specific providers
pip install "instructor[anthropic]"  # Anthropic Claude
pip install "instructor[openai]"     # OpenAI
pip install "instructor[all]"        # All providers
```

## Быстрый старт

### Простой пример: извлечение данных пользователя

```python
import instructor
from pydantic import BaseModel
from anthropic import Anthropic

# Define output structure
class User(BaseModel):
    name: str
    age: int
    email: str

# Create instructor client
client = instructor.from_anthropic(Anthropic())

# Extract structured data
user = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "John Doe is 30 years old. His email is john@example.com"
    }],
    response_model=User
)

print(user.name)   # "John Doe"
print(user.age)    # 30
print(user.email)  # "john@example.com"
```

### С OpenAI

```python
from openai import OpenAI

client = instructor.from_openai(OpenAI())

user = client.chat.completions.create(
    model="gpt-4o-mini",
    response_model=User,
    messages=[{"role": "user", "content": "Extract: Alice, 25, alice@email.com"}]
)
```

## Основные концепции

### 1. Модели ответа (Pydantic)

Модели ответа определяют структуру и правила валидации выводов LLM.

#### Базовая модель

```python
from pydantic import BaseModel, Field

class Article(BaseModel):
    title: str = Field(description="Article title")
    author: str = Field(description="Author name")
    word_count: int = Field(description="Number of words", gt=0)
    tags: list[str] = Field(description="List of relevant tags")

article = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "Analyze this article: [article text]"
    }],
    response_model=Article
)
```

**Преимущества:**
- Типобезопасность с подсказками типов Python
- Автоматическая валидация (`word_count > 0`)
- Самодокументируемость с описаниями полей
- Поддержка автодополнения в IDE

#### Вложенные модели

```python
class Address(BaseModel):
    street: str
    city: str
    country: str

class Person(BaseModel):
    name: str
    age: int
    address: Address  # Nested model

person = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "John lives at 123 Main St, Boston, USA"
    }],
    response_model=Person
)

print(person.address.city)  # "Boston"
```

#### Необязательные поля

```python
from typing import Optional

class Product(BaseModel):
    name: str
    price: float
    discount: Optional[float] = None  # Optional
    description: str = Field(default="No description")  # Default value

# LLM doesn't need to provide discount or description
```

#### Перечисления для ограничений

```python
from enum import Enum

class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class Review(BaseModel):
    text: str
    sentiment: Sentiment  # Only these 3 values allowed

review = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "This product is amazing!"
    }],
    response_model=Review
)

print(review.sentiment)  # Sentiment.POSITIVE
```

### 2. Валидация

Pydantic автоматически валидирует выводы LLM. При ошибке валидации Instructor повторяет запрос.

#### Встроенные валидаторы

```python
from pydantic import Field, EmailStr, HttpUrl

class Contact(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    age: int = Field(ge=0, le=120)  # 0 <= age <= 120
    email: EmailStr  # Validates email format
    website: HttpUrl  # Validates URL format

# If LLM provides invalid data, Instructor retries automatically
```

#### Пользовательские валидаторы

```python
from pydantic import field_validator

class Event(BaseModel):
    name: str
    date: str
    attendees: int

    @field_validator('date')
    def validate_date(cls, v):
        """Ensure date is in YYYY-MM-DD format."""
        import re
        if not re.match(r'\d{4}-\d{2}-\d{2}', v):
            raise ValueError('Date must be YYYY-MM-DD format')
        return v

    @field_validator('attendees')
    def validate_attendees(cls, v):
        """Ensure positive attendees."""
        if v < 1:
            raise ValueError('Must have at least 1 attendee')
        return v
```

#### Валидация на уровне модели

```python
from pydantic import model_validator

class DateRange(BaseModel):
    start_date: str
    end_date: str

    @model_validator(mode='after')
    def check_dates(self):
        """Ensure end_date is after start_date."""
        from datetime import datetime
        start = datetime.strptime(self.start_date, '%Y-%m-%d')
        end = datetime.strptime(self.end_date, '%Y-%m-%d')

        if end < start:
            raise ValueError('end_date must be after start_date')
        return self
```

### 3. Автоматическое повторение

Instructor автоматически повторяет запрос, когда валидация не проходит, передавая сообщение об ошибке LLM.

```python
# Retries up to 3 times if validation fails
user = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "Extract user from: John, age unknown"
    }],
    response_model=User,
    max_retries=3  # Default is 3
)

# If age can't be extracted, Instructor tells the LLM:
# "Validation error: age - field required"
# LLM tries again with better extraction
```

**Как это работает:**
1. LLM генерирует вывод
2. Pydantic валидирует
3. Если неверно — сообщение об ошибке отправляется обратно LLM
4. LLM пытается снова, учитывая ошибку
5. Повторяется до `max_retries`

### 4. Стриминг

Стрими частичные результаты для обработки в реальном времени.

#### Стриминг частичных объектов

```python
from instructor import Partial

class Story(BaseModel):
    title: str
    content: str
    tags: list[str]

# Stream partial updates as LLM generates
for partial_story in client.messages.create_partial(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "Write a short sci-fi story"
    }],
    response_model=Story
):
    print(f"Title: {partial_story.title}")
    print(f"Content so far: {partial_story.content[:100]}...")
    # Update UI in real-time
```

#### Стриминг итерируемых объектов

```python
class Task(BaseModel):
    title: str
    priority: str

# Stream list items as they're generated
tasks = client.messages.create_iterable(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "Generate 10 project tasks"
    }],
    response_model=Task
)

for task in tasks:
    print(f"- {task.title} ({task.priority})")
    # Process each task as it arrives
```

## Конфигурация провайдера

### Anthropic Claude

```python
import instructor
from anthropic import Anthropic

client = instructor.from_anthropic(
    Anthropic(api_key="your-api-key")
)

# Use with Claude models
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[...],
    response_model=YourModel
)
```

### OpenAI

```python
from openai import OpenAI

client = instructor.from_openai(
    OpenAI(api_key="your-api-key")
)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    response_model=YourModel,
    messages=[...]
)
```

### Локальные модели (Ollama)

```python
from openai import OpenAI

# Point to local Ollama server
client = instructor.from_openai(
    OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama"  # Required but ignored
    ),
    mode=instructor.Mode.JSON
)

response = client.chat.completions.create(
    model="llama3.1",
    response_model=YourModel,
    messages=[...]
)
```

## Распространённые шаблоны

### Шаблон 1: извлечение данных из текста

```python
class CompanyInfo(BaseModel):
    name: str
    founded_year: int
    industry: str
    employees: int
    headquarters: str

text = """
Tesla, Inc. was founded in 2003. It operates in the automotive and energy
industry with approximately 140,000 employees. The company is headquartered
in Austin, Texas.
"""

company = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": f"Extract company information from: {text}"
    }],
    response_model=CompanyInfo
)
```

### Шаблон 2: классификация

```python
class Category(str, Enum):
    TECHNOLOGY = "technology"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    OTHER = "other"

class ArticleClassification(BaseModel):
    category: Category
    confidence: float = Field(ge=0.0, le=1.0)
    keywords: list[str]

classification = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "Classify this article: [article text]"
    }],
    response_model=ArticleClassification
)
```

### Шаблон 3: извлечение нескольких сущностей

```python
class Person(BaseModel):
    name: str
    role: str

class Organization(BaseModel):
    name: str
    industry: str

class Entities(BaseModel):
    people: list[Person]
    organizations: list[Organization]
    locations: list[str]

text = "Tim Cook, CEO of Apple, announced at the event in Cupertino..."

entities = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": f"Extract all entities from: {text}"
    }],
    response_model=Entities
)

for person in entities.people:
    print(f"{person.name} - {person.role}")
```

### Шаблон 4: структурированный анализ

```python
class SentimentAnalysis(BaseModel):
    overall_sentiment: Sentiment
    positive_aspects: list[str]
    negative_aspects: list[str]
    suggestions: list[str]
    score: float = Field(ge=-1.0, le=1.0)

review = "The product works well but setup was confusing..."

analysis = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": f"Analyze this review: {review}"
    }],
    response_model=SentimentAnalysis
)
```

### Шаблон 5: пакетная обработка

```python
def extract_person(text: str) -> Person:
    return client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"Extract person from: {text}"
        }],
        response_model=Person
    )

texts = [
    "John Doe is a 30-year-old engineer",
    "Jane Smith, 25, works in marketing",
    "Bob Johnson, age 40, software developer"
]

people = [extract_person(text) for text in texts]
```

## Расширенные возможности

### Объединённые типы

```python
from typing import Union

class TextContent(BaseModel):
    type: str = "text"
    content: str

class ImageContent(BaseModel):
    type: str = "image"
    url: HttpUrl
    caption: str

class Post(BaseModel):
    title: str
    content: Union[TextContent, ImageContent]  # Either type

# LLM chooses appropriate type based on content
```

### Динамические модели

```python
from pydantic import create_model

# Create model at runtime
DynamicUser = create_model(
    'User',
    name=(str, ...),
    age=(int, Field(ge=0)),
    email=(EmailStr, ...)
)

user = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[...],
    response_model=DynamicUser
)
```

### Пользовательские режимы

```python
# For providers without native structured outputs
client = instructor.from_anthropic(
    Anthropic(),
    mode=instructor.Mode.JSON  # JSON mode
)

# Available modes:
# - Mode.ANTHROPIC_TOOLS (recommended for Claude)
# - Mode.JSON (fallback)
# - Mode.TOOLS (OpenAI tools)
```

### Управление контекстом

```python
# Single-use client
with instructor.from_anthropic(Anthropic()) as client:
    result = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[...],
        response_model=YourModel
    )
    # Client closed automatically
```

## Обработка ошибок

### Обработка ошибок валидации

```python
from pydantic import ValidationError

try:
    user = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[...],
        response_model=User,
        max_retries=3
    )
except ValidationError as e:
    print(f"Failed after retries: {e}")
    # Handle gracefully

except Exception as e:
    print(f"API error: {e}")
```

### Пользовательские сообщения об ошибках

```python
class ValidatedUser(BaseModel):
    name: str = Field(description="Full name, 2-100 characters")
    age: int = Field(description="Age between 0 and 120", ge=0, le=120)
    email: EmailStr = Field(description="Valid email address")

    class Config:
        # Custom error messages
        json_schema_extra = {
            "examples": [
                {
                    "name": "John Doe",
                    "age": 30,
                    "email": "john@example.com"
                }
            ]
        }
```

## Лучшие практики

### 1. Чёткие описания полей

```python
# ❌ Bad: Vague
class Product(BaseModel):
    name: str
    price: float

# ✅ Good: Descriptive
class Product(BaseModel):
    name: str = Field(description="Product name from the text")
    price: float = Field(description="Price in USD, without currency symbol")
```

### 2. Используй подходящую валидацию

```python
# ✅ Good: Constrain values
class Rating(BaseModel):
    score: int = Field(ge=1, le=5, description="Rating from 1 to 5 stars")
    review: str = Field(min_length=10, description="Review text, at least 10 chars")
```

### 3. Приводи примеры в подсказках

```python
messages = [{
    "role": "user",
    "content": """Extract person info from: "John, 30, engineer"

Example format:
{
  "name": "John Doe",
  "age": 30,
  "occupation": "engineer"
}"""
}]
```

### 4. Используй перечисления для фиксированных категорий

```python
# ✅ Good: Enum ensures valid values
class Status(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class Application(BaseModel):
    status: Status  # LLM must choose from enum
```

### 5. Обрабатывай отсутствие данных корректно

```python
class PartialData(BaseModel):
    required_field: str
    optional_field: Optional[str] = None
    default_field: str = "default_value"

# LLM only needs to provide required_field
```

## Сравнение с альтернативами

| Feature | Instructor | Manual JSON | LangChain | DSPy |
|---------|------------|-------------|-----------|------|
| Type Safety | ✅ Yes | ❌ No | ⚠️ Partial | ✅ Yes |
| Auto Validation | ✅ Yes | ❌ No | ❌ No | ⚠️ Limited |
| Auto Retry | ✅ Yes | ❌ No | ❌ No | ✅ Yes |
| Streaming | ✅ Yes | ❌ No | ✅ Yes | ❌ No |
| Multi-Provider | ✅ Yes | ⚠️ Manual | ✅ Yes | ✅ Yes |
| Learning Curve | Low | Low | Medium | High |

**Когда выбирать Instructor:**
- Нужно получать структурированные, проверенные выводы
- Требуется типобезопасность и поддержка IDE
- Нужны автоматические повторения
- Строишь системы извлечения данных

**Когда выбирать альтернативы:**
- DSPy: требуется оптимизация подсказок
- LangChain: построение сложных цепочек
- Manual: простые одноразовые извлечения

## Ресурсы

- **Документация**: https://python.useinstructor.com
- **GitHub**: https://github.com/jxnl/instructor (15k+ stars)
- **Кулинарная книга**: https://python.useinstructor.com/examples
- **Discord**: Community support available

## См. также

- `references/validation.md` — расширенные шаблоны валидации
- `references/providers.md` — конфигурация провайдеров
- `references/examples.md` — реальные примеры использования