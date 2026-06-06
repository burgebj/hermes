---
title: "Dspy — DSPy: декларативні програми LM, автоматичне оптимізування підказок, RAG"
sidebar_label: "Dspy"
description: "DSPy: декларативні програми LM, автоматично оптимізувати підказки, RAG"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Dspy

DSPy: декларативні LM‑програми, автоматичне оптимізування підказок, RAG.

## Метадані навички

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/mlops/research/dspy` |
| Version | `1.0.0` |
| Author | Orchestra Research |
| License | MIT |
| Dependencies | `dspy`, `openai`, `anthropic` |
| Platforms | linux, macos, windows |
| Tags | `Prompt Engineering`, `DSPy`, `Declarative Programming`, `RAG`, `Agents`, `Prompt Optimization`, `LM Programming`, `Stanford NLP`, `Automatic Optimization`, `Modular AI` |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# DSPy: Декларативне програмування мовних моделей

## Коли використовувати цю навичку

Використовуй DSPy, коли потрібно:
- **Створювати складні AI‑системи** з кількома компонентами та робочими процесами
- **Програмувати LMs декларативно** замість ручного інженерингу підказок
- **Оптимізувати підказки автоматично** за допомогою методів, орієнтованих на дані
- **Створювати модульні AI‑конвеєри**, які легко підтримувати та переносити
- **Систематично покращувати вихід моделі** за допомогою оптимізаторів
- **Будувати RAG‑системи, агентів або класифікатори** з вищою надійністю

**GitHub Stars**: 22,000+ | **Created By**: Stanford NLP

## Встановлення

```bash
# Stable release
pip install dspy

# Latest development version
pip install git+https://github.com/stanfordnlp/dspy.git

# With specific LM providers
pip install dspy[openai]        # OpenAI
pip install dspy[anthropic]     # Anthropic Claude
pip install dspy[all]           # All providers
```

## Швидкий старт

### Основний приклад: Відповіді на питання

```python
import dspy

# Configure your language model
lm = dspy.Claude(model="claude-sonnet-4-5-20250929")
dspy.settings.configure(lm=lm)

# Define a signature (input → output)
class QA(dspy.Signature):
    """Answer questions with short factual answers."""
    question = dspy.InputField()
    answer = dspy.OutputField(desc="often between 1 and 5 words")

# Create a module
qa = dspy.Predict(QA)

# Use it
response = qa(question="What is the capital of France?")
print(response.answer)  # "Paris"
```

### Ланцюжок мислення (Chain of Thought)

```python
import dspy

lm = dspy.Claude(model="claude-sonnet-4-5-20250929")
dspy.settings.configure(lm=lm)

# Use ChainOfThought for better reasoning
class MathProblem(dspy.Signature):
    """Solve math word problems."""
    problem = dspy.InputField()
    answer = dspy.OutputField(desc="numerical answer")

# ChainOfThought generates reasoning steps automatically
cot = dspy.ChainOfThought(MathProblem)

response = cot(problem="If John has 5 apples and gives 2 to Mary, how many does he have?")
print(response.rationale)  # Shows reasoning steps
print(response.answer)     # "3"
```

## Основні концепції

### 1. Підписи (Signatures)

Підписи визначають структуру твоєї AI‑задачі (inputs → outputs):

```python
# Inline signature (simple)
qa = dspy.Predict("question -> answer")

# Class signature (detailed)
class Summarize(dspy.Signature):
    """Summarize text into key points."""
    text = dspy.InputField()
    summary = dspy.OutputField(desc="bullet points, 3-5 items")

summarizer = dspy.ChainOfThought(Summarize)
```

**Коли використовувати кожен:**
- **Inline**: Швидке прототипування, прості завдання
- **Class**: Складні завдання, підказки типів, краща документація

### 2. Модулі

Модулі — це багаторазові компоненти, які перетворюють вхідні дані в вихідні:

#### dspy.Predict
Базовий модуль передбачення:

```python
predictor = dspy.Predict("context, question -> answer")
result = predictor(context="Paris is the capital of France",
                   question="What is the capital?")
```

#### dspy.ChainOfThought
Генерує кроки міркування перед відповіддю:

```python
cot = dspy.ChainOfThought("question -> answer")
result = cot(question="Why is the sky blue?")
print(result.rationale)  # Reasoning steps
print(result.answer)     # Final answer
```

#### dspy.ReAct
Міркування в стилі агента з інструментами:

```python
from dspy.predict import ReAct

class SearchQA(dspy.Signature):
    """Answer questions using search."""
    question = dspy.InputField()
    answer = dspy.OutputField()

def search_tool(query: str) -> str:
    """Search Wikipedia."""
    # Your search implementation
    return results

react = ReAct(SearchQA, tools=[search_tool])
result = react(question="When was Python created?")
```

#### dspy.ProgramOfThought
Генерує та виконує код для міркування:

```python
pot = dspy.ProgramOfThought("question -> answer")
result = pot(question="What is 15% of 240?")
# Generates: answer = 240 * 0.15
```

### 3. Оптимізатори

Оптимізатори автоматично покращують твої модулі, використовуючи навчальні дані:

#### BootstrapFewShot
Навчається на прикладах:

```python
from dspy.teleprompt import BootstrapFewShot

# Training data
trainset = [
    dspy.Example(question="What is 2+2?", answer="4").with_inputs("question"),
    dspy.Example(question="What is 3+5?", answer="8").with_inputs("question"),
]

# Define metric
def validate_answer(example, pred, trace=None):
    return example.answer == pred.answer

# Optimize
optimizer = BootstrapFewShot(metric=validate_answer, max_bootstrapped_demos=3)
optimized_qa = optimizer.compile(qa, trainset=trainset)

# Now optimized_qa performs better!
```

#### MIPRO (Most Important Prompt Optimization)
Ітеративно покращує підказки:

```python
from dspy.teleprompt import MIPRO

optimizer = MIPRO(
    metric=validate_answer,
    num_candidates=10,
    init_temperature=1.0
)

optimized_cot = optimizer.compile(
    cot,
    trainset=trainset,
    num_trials=100
)
```

#### BootstrapFinetune
Створює набори даних для донастройки моделі:

```python
from dspy.teleprompt import BootstrapFinetune

optimizer = BootstrapFinetune(metric=validate_answer)
optimized_module = optimizer.compile(qa, trainset=trainset)

# Exports training data for fine-tuning
```

### 4. Побудова складних систем

#### Багатоступеневий конвеєр

```python
import dspy

class MultiHopQA(dspy.Module):
    def __init__(self):
        super().__init__()
        self.retrieve = dspy.Retrieve(k=3)
        self.generate_query = dspy.ChainOfThought("question -> search_query")
        self.generate_answer = dspy.ChainOfThought("context, question -> answer")

    def forward(self, question):
        # Stage 1: Generate search query
        search_query = self.generate_query(question=question).search_query

        # Stage 2: Retrieve context
        passages = self.retrieve(search_query).passages
        context = "\n".join(passages)

        # Stage 3: Generate answer
        answer = self.generate_answer(context=context, question=question).answer
        return dspy.Prediction(answer=answer, context=context)

# Use the pipeline
qa_system = MultiHopQA()
result = qa_system(question="Who wrote the book that inspired the movie Blade Runner?")
```

#### RAG‑система з оптимізацією

```python
import dspy
from dspy.retrieve.chromadb_rm import ChromadbRM

# Configure retriever
retriever = ChromadbRM(
    collection_name="documents",
    persist_directory="./chroma_db"
)

class RAG(dspy.Module):
    def __init__(self, num_passages=3):
        super().__init__()
        self.retrieve = dspy.Retrieve(k=num_passages)
        self.generate = dspy.ChainOfThought("context, question -> answer")

    def forward(self, question):
        context = self.retrieve(question).passages
        return self.generate(context=context, question=question)

# Create and optimize
rag = RAG()

# Optimize with training data
from dspy.teleprompt import BootstrapFewShot

optimizer = BootstrapFewShot(metric=validate_answer)
optimized_rag = optimizer.compile(rag, trainset=trainset)
```

## Конфігурація провайдера LM

### Anthropic Claude

```python
import dspy

lm = dspy.Claude(
    model="claude-sonnet-4-5-20250929",
    api_key="your-api-key",  # Or set ANTHROPIC_API_KEY env var
    max_tokens=1000,
    temperature=0.7
)
dspy.settings.configure(lm=lm)
```

### OpenAI

```python
lm = dspy.OpenAI(
    model="gpt-4",
    api_key="your-api-key",
    max_tokens=1000
)
dspy.settings.configure(lm=lm)
```

### Локальні моделі (Ollama)

```python
lm = dspy.OllamaLocal(
    model="llama3.1",
    base_url="http://localhost:11434"
)
dspy.settings.configure(lm=lm)
```

### Кілька моделей

```python
# Different models for different tasks
cheap_lm = dspy.OpenAI(model="gpt-3.5-turbo")
strong_lm = dspy.Claude(model="claude-sonnet-4-5-20250929")

# Use cheap model for retrieval, strong model for reasoning
with dspy.settings.context(lm=cheap_lm):
    context = retriever(question)

with dspy.settings.context(lm=strong_lm):
    answer = generator(context=context, question=question)
```

## Поширені шаблони

### Шаблон 1: Структурований вихід

```python
from pydantic import BaseModel, Field

class PersonInfo(BaseModel):
    name: str = Field(description="Full name")
    age: int = Field(description="Age in years")
    occupation: str = Field(description="Current job")

class ExtractPerson(dspy.Signature):
    """Extract person information from text."""
    text = dspy.InputField()
    person: PersonInfo = dspy.OutputField()

extractor = dspy.TypedPredictor(ExtractPerson)
result = extractor(text="John Doe is a 35-year-old software engineer.")
print(result.person.name)  # "John Doe"
print(result.person.age)   # 35
```

### Шаблон 2: Оптимізація на основі тверджень

```python
import dspy
from dspy.primitives.assertions import assert_transform_module, backtrack_handler

class MathQA(dspy.Module):
    def __init__(self):
        super().__init__()
        self.solve = dspy.ChainOfThought("problem -> solution: float")

    def forward(self, problem):
        solution = self.solve(problem=problem).solution

        # Assert solution is numeric
        dspy.Assert(
            isinstance(float(solution), float),
            "Solution must be a number",
            backtrack=backtrack_handler
        )

        return dspy.Prediction(solution=solution)
```

### Шаблон 3: Самоузгодженість

```python
import dspy
from collections import Counter

class ConsistentQA(dspy.Module):
    def __init__(self, num_samples=5):
        super().__init__()
        self.qa = dspy.ChainOfThought("question -> answer")
        self.num_samples = num_samples

    def forward(self, question):
        # Generate multiple answers
        answers = []
        for _ in range(self.num_samples):
            result = self.qa(question=question)
            answers.append(result.answer)

        # Return most common answer
        most_common = Counter(answers).most_common(1)[0][0]
        return dspy.Prediction(answer=most_common)
```

### Шаблон 4: Пошук з переранжируванням

```python
class RerankedRAG(dspy.Module):
    def __init__(self):
        super().__init__()
        self.retrieve = dspy.Retrieve(k=10)
        self.rerank = dspy.Predict("question, passage -> relevance_score: float")
        self.answer = dspy.ChainOfThought("context, question -> answer")

    def forward(self, question):
        # Retrieve candidates
        passages = self.retrieve(question).passages

        # Rerank passages
        scored = []
        for passage in passages:
            score = float(self.rerank(question=question, passage=passage).relevance_score)
            scored.append((score, passage))

        # Take top 3
        top_passages = [p for _, p in sorted(scored, reverse=True)[:3]]
        context = "\n\n".join(top_passages)

        # Generate answer
        return self.answer(context=context, question=question)
```

## Оцінка та метрики

### Кастомні метрики

```python
def exact_match(example, pred, trace=None):
    """Exact match metric."""
    return example.answer.lower() == pred.answer.lower()

def f1_score(example, pred, trace=None):
    """F1 score for text overlap."""
    pred_tokens = set(pred.answer.lower().split())
    gold_tokens = set(example.answer.lower().split())

    if not pred_tokens:
        return 0.0

    precision = len(pred_tokens & gold_tokens) / len(pred_tokens)
    recall = len(pred_tokens & gold_tokens) / len(gold_tokens)

    if precision + recall == 0:
        return 0.0

    return 2 * (precision * recall) / (precision + recall)
```

### Оцінювання

```python
from dspy.evaluate import Evaluate

# Create evaluator
evaluator = Evaluate(
    devset=testset,
    metric=exact_match,
    num_threads=4,
    display_progress=True
)

# Evaluate model
score = evaluator(qa_system)
print(f"Accuracy: {score}")

# Compare optimized vs unoptimized
score_before = evaluator(qa)
score_after = evaluator(optimized_qa)
print(f"Improvement: {score_after - score_before:.2%}")
```

## Кращі практики

### 1. Починай просто, ітеративно розвивай

```python
# Start with Predict
qa = dspy.Predict("question -> answer")

# Add reasoning if needed
qa = dspy.ChainOfThought("question -> answer")

# Add optimization when you have data
optimized_qa = optimizer.compile(qa, trainset=data)
```

### 2. Використовуй описові підписи

```python
# ❌ Bad: Vague
class Task(dspy.Signature):
    input = dspy.InputField()
    output = dspy.OutputField()

# ✅ Good: Descriptive
class SummarizeArticle(dspy.Signature):
    """Summarize news articles into 3-5 key points."""
    article = dspy.InputField(desc="full article text")
    summary = dspy.OutputField(desc="bullet points, 3-5 items")
```

### 3. Оптимізуй за допомогою репрезентативних даних

```python
# Create diverse training examples
trainset = [
    dspy.Example(question="factual", answer="...).with_inputs("question"),
    dspy.Example(question="reasoning", answer="...").with_inputs("question"),
    dspy.Example(question="calculation", answer="...").with_inputs("question"),
]

# Use validation set for metric
def metric(example, pred, trace=None):
    return example.answer in pred.answer
```

### 4. Зберігай та завантажуй оптимізовані моделі

```python
# Save
optimized_qa.save("models/qa_v1.json")

# Load
loaded_qa = dspy.ChainOfThought("question -> answer")
loaded_qa.load("models/qa_v1.json")
```

### 5. Моніторинг та налагодження

```python
# Enable tracing
dspy.settings.configure(lm=lm, trace=[])

# Run prediction
result = qa(question="...")

# Inspect trace
for call in dspy.settings.trace:
    print(f"Prompt: {call['prompt']}")
    print(f"Response: {call['response']}")
```

## Порівняння з іншими підходами

| Feature | Manual Prompting | LangChain | DSPy |
|---------|-----------------|-----------|------|
| Prompt Engineering | Manual | Manual | Automatic |
| Optimization | Trial & error | None | Data-driven |
| Modularity | Low | Medium | High |
| Type Safety | No | Limited | Yes (Signatures) |
| Portability | Low | Medium | High |
| Learning Curve | Low | Medium | Medium-High |

**Коли обирати DSPy:**
- Є навчальні дані або їх можна згенерувати
- Потрібне систематичне покращення підказок
- Будуєш складні багатоступеневі системи
- Хочеш оптимізувати роботу різних LM

**Коли обирати альтернативи:**
- Швидкі прототипи (ручне підказування)
- Прості ланцюжки з існуючими інструментами (LangChain)
- Потрібна кастомна логіка оптимізації

## Ресурси

- **Documentation**: https://dspy.ai
- **GitHub**: https://github.com/stanfordnlp/dspy (22k+ stars)
- **Discord**: https://discord.gg/XCGy2WDCQB
- **Twitter**: @DSPyOSS
- **Paper**: "DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines"

## Дивись також

- `references/modules.md` - Детальний посібник з модулів (Predict, ChainOfThought, ReAct, ProgramOfThought)
- `references/optimizers.md` - Алгоритми оптимізації (BootstrapFewShot, MIPRO, BootstrapFinetune)
- `references/examples.md` - Приклади з реального світу (RAG, agents, classifiers)