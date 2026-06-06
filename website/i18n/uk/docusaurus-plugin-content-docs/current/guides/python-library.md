---
sidebar_position: 5
title: "Використання Hermes як бібліотеки Python"
description: "Вбудуй AIAgent у свої власні скрипти Python, веб‑додатки або автоматизовані конвеєри — не потрібен CLI"
---

# Використання Hermes як Python‑бібліотеки

Hermes — це не лише інструмент CLI. Ти можеш імпортувати `AIAgent` безпосередньо і використовувати його програмно у своїх Python‑скриптах, веб‑додатках або автоматизаційних конвеєрах. У цьому посібнику показано, як це зробити.

---

## Встановлення

Встанови Hermes безпосередньо з репозиторію:

```bash
pip install git+https://github.com/NousResearch/hermes-agent.git
```

Або за допомогою [uv](https://docs.astral.sh/uv/):

```bash
uv pip install git+https://github.com/NousResearch/hermes-agent.git
```

Також можеш зафіксувати його у своєму `requirements.txt`:

```text
hermes-agent @ git+https://github.com/NousResearch/hermes-agent.git
```

:::tip
Ті ж змінні середовища, що використовуються CLI, потрібні й при використанні Hermes як бібліотеки. Принаймні встанови `OPENROUTER_API_KEY` (або `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`, якщо використовуєш прямий доступ до провайдера).
:::

---

## Базове використання

Найпростіший спосіб використати Hermes — це метод `chat()` — передай повідомлення, отримай рядок у відповідь:

```python
from run_agent import AIAgent

agent = AIAgent(
    model="anthropic/claude-sonnet-4.6",
    quiet_mode=True,
)
response = agent.chat("What is the capital of France?")
print(response)
```

`chat()` обробляє повний цикл розмови всередині — виклики інструментів, повтори, усе — і повертає лише остаточну текстову відповідь.

:::warning
Завжди встановлюй `quiet_mode=True`, коли вбудовуєш Hermes у свій код. Без цього агент виводитиме спінери CLI, індикатори прогресу та інший термінальний вивід, який засмічуватиме вихід твого застосунку.
:::

---

## Повний контроль розмови

Для більшого контролю над розмовою використай `run_conversation()` безпосередньо. Він повертає словник з повною відповіддю, історією повідомлень та метаданими:

```python
agent = AIAgent(
    model="anthropic/claude-sonnet-4.6",
    quiet_mode=True,
)

result = agent.run_conversation(
    user_message="Search for recent Python 3.13 features",
    task_id="my-task-1",
)

print(result["final_response"])
print(f"Messages exchanged: {len(result['messages'])}")
```

Повернутий словник містить:
- **`final_response`** — остаточна текстова відповідь агента
- **`messages`** — повна історія повідомлень (system, user, assistant, tool calls)

(`task_id`, який ти передаєш, зберігається у екземплярі агента для ізоляції VM, але не повертається у словнику.)

Ти також можеш передати власне системне повідомлення, яке перевизначає тимчасовий системний підказник для цього виклику:

```python
result = agent.run_conversation(
    user_message="Explain quicksort",
    system_message="You are a computer science tutor. Use simple analogies.",
)
```

---

## Налаштування інструментів

Керуй наборами інструментів, до яких має доступ агент, за допомогою `enabled_toolsets` або `disabled_toolsets`:

```python
# Only enable web tools (browsing, search)
agent = AIAgent(
    model="anthropic/claude-sonnet-4.6",
    enabled_toolsets=["web"],
    quiet_mode=True,
)

# Enable everything except terminal access
agent = AIAgent(
    model="anthropic/claude-sonnet-4.6",
    disabled_toolsets=["terminal"],
    quiet_mode=True,
)
```

:::tip
Використовуй `enabled_toolsets`, коли потрібен мінімальний, закритий агент (наприклад, лише веб‑пошук для дослідницького бота). Використовуй `disabled_toolsets`, коли потрібен більший функціонал, але треба обмежити конкретні інструменти (наприклад, без доступу до терміналу в спільному середовищі).
:::

---

## Багатокрокові розмови

Зберігай стан розмови між кількома кроками, передаючи історію повідомлень назад:

```python
agent = AIAgent(
    model="anthropic/claude-sonnet-4.6",
    quiet_mode=True,
)

# First turn
result1 = agent.run_conversation("My name is Alice")
history = result1["messages"]

# Second turn — agent remembers the context
result2 = agent.run_conversation(
    "What's my name?",
    conversation_history=history,
)
print(result2["final_response"])  # "Your name is Alice."
```

Параметр `conversation_history` приймає список `messages` з попереднього результату. Агент копіює його всередині, тому твій оригінальний список ніколи не змінюється.

---

## Збереження траєкторій

Увімкни збереження траєкторій, щоб фіксувати розмови у форматі ShareGPT — це корисно для створення навчальних даних або налагодження:

```python
agent = AIAgent(
    model="anthropic/claude-sonnet-4.6",
    save_trajectories=True,
    quiet_mode=True,
)

agent.chat("Write a Python function to sort a list")
# Saves to trajectory_samples.jsonl in ShareGPT format
```

Кожна розмова додається як один рядок JSONL, що спрощує збір наборів даних з автоматизованих запусків.

---

## Кастомні системні підказки

Використовуй `ephemeral_system_prompt`, щоб задати власну системну підказку, яка керує поведінкою агента, але **не** зберігається у файлах траєкторій (зберігаючи чистоту твоїх навчальних даних):

```python
agent = AIAgent(
    model="anthropic/claude-sonnet-4",
    ephemeral_system_prompt="You are a SQL expert. Only answer database questions.",
    quiet_mode=True,
)

response = agent.chat("How do I write a JOIN query?")
print(response)
```

Це ідеально підходить для створення спеціалізованих агентів — рев’юера коду, автора документації, помічника SQL — всі вони працюють на одній базовій інструментальній платформі.

---

## Пакетна обробка

Для паралельного запуску багатьох запитів Hermes включає `batch_runner.py`. Він керує одночасними екземплярами `AIAgent` з належною ізоляцією ресурсів:

```bash
python batch_runner.py --input prompts.jsonl --output results.jsonl
```

Кожен запит отримує свій `task_id` та ізольоване середовище. Якщо потрібна власна логіка пакетної обробки, можеш створити її, використовуючи `AIAgent` безпосередньо:

```python
import concurrent.futures
from run_agent import AIAgent

prompts = [
    "Explain recursion",
    "What is a hash table?",
    "How does garbage collection work?",
]

def process_prompt(prompt):
    # Create a fresh agent per task for thread safety
    agent = AIAgent(
        model="anthropic/claude-sonnet-4",
        quiet_mode=True,
        skip_memory=True,
    )
    return agent.chat(prompt)

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(process_prompt, prompts))

for prompt, result in zip(prompts, results):
    print(f"Q: {prompt}\nA: {result}\n")
```

:::warning
Завжди створюй **новий екземпляр `AIAgent` для кожного потоку або завдання**. Агент зберігає внутрішній стан (історію розмов, сесії інструментів, лічильники ітерацій), який не є потокобезпечним для спільного використання.
:::

---

## Приклади інтеграції

### FastAPI Endpoint

```python
from fastapi import FastAPI
from pydantic import BaseModel
from run_agent import AIAgent

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    model: str = "anthropic/claude-sonnet-4"

@app.post("/chat")
async def chat(request: ChatRequest):
    agent = AIAgent(
        model=request.model,
        quiet_mode=True,
        skip_context_files=True,
        skip_memory=True,
    )
    response = agent.chat(request.message)
    return {"response": response}
```

### Discord Bot

```python
import discord
from run_agent import AIAgent

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith("!hermes "):
        query = message.content[8:]
        agent = AIAgent(
            model="anthropic/claude-sonnet-4",
            quiet_mode=True,
            skip_context_files=True,
            skip_memory=True,
            platform="discord",
        )
        response = agent.chat(query)
        await message.channel.send(response[:2000])

client.run("YOUR_DISCORD_TOKEN")
```

### CI/CD Pipeline Step

```python
#!/usr/bin/env python3
"""CI step: auto-review a PR diff."""
import subprocess
from run_agent import AIAgent

diff = subprocess.check_output(["git", "diff", "main...HEAD"]).decode()

agent = AIAgent(
    model="anthropic/claude-sonnet-4",
    quiet_mode=True,
    skip_context_files=True,
    skip_memory=True,
    disabled_toolsets=["terminal", "browser"],
)

review = agent.chat(
    f"Review this PR diff for bugs, security issues, and style problems:\n\n{diff}"
)
print(review)
```

---

## Ключові параметри конструктора

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `str` | `""` | Модель у форматі OpenRouter (за замовчуванням порожня; визначається з конфігурації hermes під час виконання) |
| `quiet_mode` | `bool` | `False` | Прибирає вивід CLI |
| `enabled_toolsets` | `List[str]` | `None` | Білий список конкретних наборів інструментів |
| `disabled_toolsets` | `List[str]` | `None` | Чорний список конкретних наборів інструментів |
| `save_trajectories` | `bool` | `False` | Зберігати розмови у JSONL |
| `ephemeral_system_prompt` | `str` | `None` | Кастомна системна підказка (не зберігається у траєкторіях) |
| `max_iterations` | `int` | `90` | Максимальна кількість ітерацій виклику інструментів у розмові |
| `skip_context_files` | `bool` | `False` | Пропускати завантаження файлів AGENTS.md |
| `skip_memory` | `bool` | `False` | Вимкнути читання/запис постійної пам’яті |
| `api_key` | `str` | `None` | API‑ключ (перевага змінним середовища) |
| `base_url` | `str` | `None` | Кастомний URL кінцевої точки API |
| `platform` | `str` | `None` | Підказка платформи (`"discord"`, `"telegram"` тощо) |

---

## Важливі нотатки

:::tip
- Встанови **`skip_context_files=True`**, якщо не хочеш, щоб файли `AGENTS.md` з робочого каталогу завантажувалися у системний підказник.
- Встанови **`skip_memory=True`**, щоб запобігти читанню або запису постійної пам’яті агентом — рекомендовано для безстанових API‑ендпоінтів.
- Параметр `platform` (наприклад, `"discord"`, `"telegram"`) додає специфічні підказки форматування, щоб агент адаптував стиль виводу під конкретну платформу.
:::

:::warning
- **Потокова безпека**: Створюй один `AIAgent` на кожен потік або завдання. Ніколи не ділись екземпляром між одночасними викликами.
- **Очищення ресурсів**: Агент автоматично очищає ресурси (термінальні сесії, браузерні інстанси) після завершення розмови. Якщо ти працюєш у довгоживучому процесі, переконайся, що кожна розмова завершується коректно.
- **Обмеження ітерацій**: Значення за замовчуванням `max_iterations=90` досить щедре. Для простих Q&A випадків розглянь можливість зменшити його (наприклад, `max_iterations=10`), щоб уникнути нескінченних циклів виклику інструментів і контролювати витрати.
:::