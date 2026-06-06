---
sidebar_position: 5
title: "Использование Hermes как библиотеки Python"
description: "Встраивай AIAgent в свои собственные скрипты Python, веб‑приложения или конвейеры автоматизации — без необходимости в CLI"
---

# Использование Hermes как библиотеки Python

Hermes — это не только инструмент CLI. Ты можешь импортировать `AIAgent` напрямую и использовать его программно в своих скриптах Python, веб‑приложениях или автоматизационных пайплайнах. В этом руководстве показано, как это сделать.

---

## Установка

Установи Hermes напрямую из репозитория:

```bash
pip install git+https://github.com/NousResearch/hermes-agent.git
```

Или с помощью [uv](https://docs.astral.sh/uv/):

```bash
uv pip install git+https://github.com/NousResearch/hermes-agent.git
```

Также можешь зафиксировать его в файле `requirements.txt`:

```text
hermes-agent @ git+https://github.com/NousResearch/hermes-agent.git
```

:::tip
Те же переменные окружения, что используются CLI, требуются и при работе с Hermes как библиотекой. Как минимум, установи `OPENROUTER_API_KEY` (или `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`, если используешь прямой доступ к провайдеру).
:::

---

## Базовое использование

Самый простой способ использовать Hermes — метод `chat()` — передаёшь сообщение, получаешь строку в ответ:

```python
from run_agent import AIAgent

agent = AIAgent(
    model="anthropic/claude-sonnet-4.6",
    quiet_mode=True,
)
response = agent.chat("What is the capital of France?")
print(response)
```

`chat()` обрабатывает весь цикл разговора внутри — вызовы инструментов, повторные попытки, всё — и возвращает только окончательный текстовый ответ.

:::warning
Всегда указывай `quiet_mode=True`, когда встраиваешь Hermes в свой код. Иначе агент выводит спиннеры CLI, индикаторы прогресса и прочий терминальный вывод, который будет захламлять вывод твоего приложения.
:::

---

## Полный контроль над разговором

Для более гибкого управления разговором используй `run_conversation()` напрямую. Он возвращает словарь с полным ответом, историей сообщений и метаданными:

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

Возвращаемый словарь содержит:
- **`final_response`** — окончательный текстовый ответ агента
- **`messages`** — полная история сообщений (system, user, assistant, tool calls)

(`task_id`, который ты передаёшь, сохраняется в экземпляре агента для изоляции VM, но не возвращается в словаре.)

Также можешь передать пользовательское системное сообщение, которое переопределит временное системное приглашение для этого вызова:

```python
result = agent.run_conversation(
    user_message="Explain quicksort",
    system_message="You are a computer science tutor. Use simple analogies.",
)
```

---

## Настройка инструментов

Контролируй, к каким наборам инструментов имеет доступ агент, используя `enabled_toolsets` или `disabled_toolsets`:

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
Используй `enabled_toolsets`, когда нужен минимальный, ограниченный агент (например, только веб‑поиск для исследовательского бота). Используй `disabled_toolsets`, когда нужны почти все возможности, но требуется ограничить конкретные (например, отключить доступ к терминалу в общей среде).
:::

---

## Многошаговые диалоги

Сохраняй состояние разговора между несколькими ходами, передавая историю сообщений обратно:

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

Параметр `conversation_history` принимает список `messages` из предыдущего результата. Агент копирует его внутренне, поэтому твой оригинальный список никогда не изменяется.

---

## Сохранение траекторий

Включи сохранение траекторий, чтобы фиксировать разговоры в формате ShareGPT — удобно для генерации обучающих данных или отладки:

```python
agent = AIAgent(
    model="anthropic/claude-sonnet-4.6",
    save_trajectories=True,
    quiet_mode=True,
)

agent.chat("Write a Python function to sort a list")
# Saves to trajectory_samples.jsonl in ShareGPT format
```

Каждый разговор добавляется как отдельная строка JSONL, что упрощает сбор наборов данных из автоматических запусков.

---

## Пользовательские системные подсказки

Используй `ephemeral_system_prompt`, чтобы задать собственную системную подсказку, влияющую на поведение агента, но **не** сохраняемую в файлы траекторий (чтобы обучающие данные оставались чистыми):

```python
agent = AIAgent(
    model="anthropic/claude-sonnet-4",
    ephemeral_system_prompt="You are a SQL expert. Only answer database questions.",
    quiet_mode=True,
)

response = agent.chat("How do I write a JOIN query?")
print(response)
```

Это идеально подходит для создания специализированных агентов — ревьюера кода, писателя документации, помощника по SQL — все они используют одну и ту же базовую инфраструктуру.

---

## Пакетная обработка

Для параллельного выполнения множества запросов Hermes предоставляет `batch_runner.py`. Он управляет конкурентными экземплярами `AIAgent` с правильной изоляцией ресурсов:

```bash
python batch_runner.py --input prompts.jsonl --output results.jsonl
```

Каждому запросу назначается свой `task_id` и изолированная среда. Если нужна собственная пакетная логика, можешь построить её, используя `AIAgent` напрямую:

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
Всегда создавай **новый экземпляр `AIAgent` для каждого потока или задачи**. Агент хранит внутреннее состояние (историю диалога, сессии инструментов, счётчики итераций), которое не является потокобезопасным для совместного использования.
:::

---

## Примеры интеграции

### FastAPI endpoint

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

### Discord‑бот

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

### Шаг CI/CD пайплайна

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

## Ключевые параметры конструктора

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `str` | `""` | Модель в формате OpenRouter (по умолчанию пусто; берётся из конфигурации hermes во время выполнения) |
| `quiet_mode` | `bool` | `False` | Подавлять вывод CLI |
| `enabled_toolsets` | `List[str]` | `None` | Белый список конкретных наборов инструментов |
| `disabled_toolsets` | `List[str]` | `None` | Чёрный список конкретных наборов инструментов |
| `save_trajectories` | `bool` | `False` | Сохранять разговоры в JSONL |
| `ephemeral_system_prompt` | `str` | `None` | Пользовательская системная подсказка (не сохраняется в траектории) |
| `max_iterations` | `int` | `90` | Максимальное число итераций вызова инструментов за разговор |
| `skip_context_files` | `bool` | `False` | Пропускать загрузку файлов AGENTS.md |
| `skip_memory` | `bool` | `False` | Отключить чтение/запись постоянной памяти |
| `api_key` | `str` | `None` | API‑ключ (по умолчанию берётся из переменных окружения) |
| `base_url` | `str` | `None` | Пользовательский URL конечной точки API |
| `platform` | `str` | `None` | Подсказка платформы (`"discord"`, `"telegram"` и т.п.) |

---

## Важные замечания

:::tip
- Установи **`skip_context_files=True`**, если не хочешь, чтобы файлы `AGENTS.md` из текущей директории загружались в системную подсказку.
- Установи **`skip_memory=True`**, чтобы агент не читал и не записывал постоянную память — рекомендуется для без‑состояния API‑эндпоинтов.
- Параметр `platform` (например, `"discord"`, `"telegram"`) добавляет специфические подсказки форматирования, позволяя агенту адаптировать стиль вывода.
:::

:::warning
- **Потокобезопасность**: создавай один `AIAgent` на каждый поток или задачу. Никогда не делись экземпляром между конкурентными вызовами.
- **Очистка ресурсов**: агент автоматически освобождает ресурсы (сессии терминала, браузерные инстансы) по завершении разговора. Если ты работаешь в длительно живом процессе, убедись, что каждый разговор завершается корректно.
- **Ограничения итераций**: значение `max_iterations=90` по умолчанию достаточно велико. Для простых вопросов‑ответов можешь уменьшить его (например, `max_iterations=10`), чтобы избежать бесконечных циклов вызова инструментов и контролировать расходы.
:::