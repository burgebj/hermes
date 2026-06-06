---
title: "Openhands — Делегуй кодування до OpenHands CLI (model-agnostic, LiteLLM)"
sidebar_label: "Openhands"
description: "Делегуй кодування OpenHands CLI (model-agnostic, LiteLLM)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Openhands

Делегуй кодування OpenHands CLI (модель‑агностичний, LiteLLM).

## Метадані навички

| | |
|---|---|
| Джерело | Optional — install with `hermes skills install official/autonomous-ai-agents/openhands` |
| Шлях | `optional-skills/autonomous-ai-agents/openhands` |
| Версія | `0.1.0` |
| Автор | Tim Koepsel (xzessmedia), Hermes Agent |
| Ліцензія | MIT |
| Платформи | linux, macos |
| Теги | `Coding-Agent`, `OpenHands`, `Model-Agnostic`, `LiteLLM` |
| Пов’язані навички | [`claude-code`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-claude-code), [`codex`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-codex), [`opencode`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-opencode), [`hermes-agent`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-hermes-agent) |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції, коли навичка активна.
:::

# OpenHands CLI

Делегуй завдання кодування [OpenHands CLI](https://github.com/All-Hands-AI/OpenHands) через інструмент `terminal`. OpenHands — модель‑агностичний: будь‑який провайдер, підтримуваний LiteLLM (OpenAI, Anthropic, OpenRouter, DeepSeek, Ollama, vLLM тощо).

Ця навичка — обгортка у headless‑режимі для пакетної / одноразової делегації. Інтерактивний текстовий UI не використовується з Hermes.

## Коли використовувати

- Користувач хоче делегувати завдання кодування саме OpenHands.
- Користувач хоче агента кодування, який може працювати на провайдері, відмінному від Anthropic / OpenAI (DeepSeek, Qwen, Ollama, vLLM, Nous тощо) — суміжні навички `claude-code` і `codex` прив’язані до одного вендора.
- Багатокрокові правки файлів + команди оболонки всередині робочого простору.

Для Claude‑нативного використовуйте `claude-code`. Для OpenAI‑нативного — `codex`. Для Hermes‑нативних підагентів — `delegate_task`.

## Передумови

1. Встанови upstream (потрібен Python 3.12+ і `uv`):

   ```
   terminal(command="uv tool install openhands --python 3.12")
   ```

   Перевірка: `openhands --version` (на момент написання `OpenHands CLI 1.16.0` / `SDK v1.21.0`).

2. Вибери модель і встанови змінні середовища для `--override-with-envs`:

   ```
   export LLM_MODEL=openrouter/openai/gpt-4o-mini       # or any LiteLLM slug
   export LLM_API_KEY=$OPENROUTER_API_KEY
   export LLM_BASE_URL=https://openrouter.ai/api/v1     # omit for native OpenAI
   ```

   `LLM_MODEL` використовує повний slug LiteLLM. Коли провайдер — OpenRouter, slug має подвійний префікс: `openrouter/<vendor>/<model>` (наприклад `openrouter/anthropic/claude-sonnet-4.5`). Для нативного Anthropic: `anthropic/claude-sonnet-4-5`. Для нативного OpenAI: `openai/gpt-4o-mini`.

3. Приховай стартовий банер, щоб JSON‑вивід не був попереджений ASCII‑артом:

   ```
   export OPENHANDS_SUPPRESS_BANNER=1
   ```

## Як запускати

Завжди викликай через інструмент `terminal`. Завжди передавай `--headless --json --override-with-envs --exit-without-confirmation` для автоматизації.

### Одноразове завдання

```
terminal(
  command="OPENHANDS_SUPPRESS_BANNER=1 LLM_MODEL=openrouter/openai/gpt-4o-mini LLM_API_KEY=$OPENROUTER_API_KEY LLM_BASE_URL=https://openrouter.ai/api/v1 openhands --headless --json --override-with-envs --exit-without-confirmation -t 'Add error handling to all API calls in src/'",
  workdir="/path/to/project",
  timeout=600
)
```

### Фонова обробка довгих завдань

```
terminal(command="<same as above>", workdir="/path/to/project", background=true, notify_on_complete=true)
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")
```

### Відновлення попередньої розмови

OpenHands виводить `Conversation ID: <32-hex>` і рядок `Hint: openhands --resume <dashed-uuid>` в кінці кожного запуску. Використай форму з дефісами, щоб відновити:

```
terminal(
  command="OPENHANDS_SUPPRESS_BANNER=1 LLM_MODEL=... openhands --headless --json --override-with-envs --exit-without-confirmation --resume <dashed-uuid> -t 'Now fix the bug you found'",
  workdir="/path/to/project"
)
```

## Список реальних прапорців

Перевірено за `openhands --help` (CLI 1.16.0). Все, що не в цій таблиці, не є прапорцем — передавай його через змінну середовища або файл налаштувань.

| Прапорець | Ефект |
|------|--------|
| `--headless` | Без UI, потребує `-t` або `-f`. Авто‑підтверджує всі дії (без `--llm-approve` у цьому режимі). |
| `--json` | Потік подій JSONL (потребує `--headless`). |
| `-t TEXT` | Промпт завдання. |
| `-f PATH` | Читати завдання з файлу. |
| `--resume [ID]` | Відновити розмову. Без ID → список останніх. |
| `--last` | Відновити найостаннішу (з `--resume`). |
| `--override-with-envs` | Застосувати змінні `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL`. Без цього OpenHands використовує `~/.openhands/settings.json` і ігнорує env. |
| `--exit-without-confirmation` | Не показувати діалог підтвердження виходу. |
| `--always-approve` / `--yolo` | Авто‑підтвердження кожної дії (за замовчуванням у `--headless`). |
| `--llm-approve` | Безпековий шлюз на базі LLM (лише інтерактивно — НЕ працює у headless). |
| `--version` / `-v` | Вивести версію і вийти. |

**Прапорців `--model`, `--max-iterations`, `--workspace`, `--sandbox`, `--sandbox-type` немає.** Модель задається через `LLM_MODEL`. Робочий простір — це `workdir`, який передається інструменту `terminal`. Пісочниця / середовище виконання задаються змінними `RUNTIME` і `SANDBOX_VOLUMES`.

## Схема JSON‑подій

З `--json --headless` OpenHands генерує JSONL — один JSON‑об’єкт на рядок, плюс кілька рядків статусу, які не є JSON (`Initializing agent...`, `Agent is working`, `Agent finished`, підсумковий блок, `Goodbye!`, `Conversation ID:`, `Hint:`). Фільтруй рядки, що починаються з `{`.

Поле верхнього рівня `kind` розрізняє типи подій:

- `MessageEvent` — текстовий хід користувача/агента. `source` — `user` або `agent`.
- `ActionEvent` — агент вибрав інструмент. Читай `tool_name` (`file_editor`, `terminal`, `finish`) і `action.kind` (`FileEditorAction`, `TerminalAction`, `FinishAction`).
- `ObservationEvent` — результат інструмента. `observation.is_error` — прапорець успішності. `source` — `environment`.
- `FinishAction` всередині `ActionEvent` несе фінальне повідомлення агента у `action.message`.

CLI спочатку виводить весь stderr від LiteLLM/Authlib — дивись розділ «Проблеми». Парсь лише stdout, рядок за рядком, ігноруючи рядки, що не починаються з `{`.

## Проблеми

- **Попередження LiteLLM при кожному виклику.** CLI виводить попередження `bedrock-runtime` і `sagemaker-runtime` у stderr, бо `botocore` не встановлений. Плюс deprecation Authlib. Це шум, а не помилки. Перенаправляй stderr у `/dev/null` або фільтруй його перед показом користувачу.
- **Спам банера.** Без `OPENHANDS_SUPPRESS_BANNER=1` кожен запуск починається з багаторядкового ASCII‑боксу `+--+`, що рекламує SDK. Завжди експортуй цю змінну.
- **`--override-with-envs` обов’язковий для автоматизації.** Без нього OpenHands ігнорує `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` і повертається до `~/.openhands/settings.json`. При чистій інсталяції цей файл відсутній, і CLI зависає, чекаючи налаштування першого запуску.
- **Slug моделі — це slug LiteLLM, а не провайдера.** `openrouter/openai/gpt-4o-mini` працює; `openai/gpt-4o-mini` при вказанні OpenRouter — ні. `anthropic/claude-sonnet-4-5` (дефіс) — нативний Anthropic; `openrouter/anthropic/claude-sonnet-4.5` (крапка) — через OpenRouter. Помилка → незрозуміла помилка LiteLLM 400.
- **`pip install openhands-ai` — неправильний пакет.** Це застарілий V0 SDK. Новий CLI встановлюється командою `uv tool install openhands --python 3.12`. Пакет conda не підтримується.
- **Формат ID для відновлення складний.** CLI завершує рядком `Conversation ID: f46573d9cfdb45e492ca189bde40019b` (без дефісів), а потім `Hint: openhands --resume f46573d9-cfdb-45e4-92ca-189bde40019b` (з дефісами). Використовуй форму з дефісами.
- **Headless ігнорує `--llm-approve`.** Якщо передати його, отримаєш помилку argparse. У headless режимі завжди включено auto‑approve.
- **Немає підтримки Windows у upstream.** Документація OpenHands вимагає WSL на Windows. Ця навичка обмежена `[linux, macos]`.
- **`~/.openhands/conversations/<id>/` накопичується.** Кожен запуск зберігає траєкторію. Очисти її при пакетних запусках.
- **Важка інсталяція (~200 пакетів).** Використовуй `uv tool install` (ізольоване venv), щоб уникнути конфліктів залежностей з активним проєктом.

## Перевірка

```
terminal(
  command="OPENHANDS_SUPPRESS_BANNER=1 LLM_MODEL=openrouter/openai/gpt-4o-mini LLM_API_KEY=$OPENROUTER_API_KEY LLM_BASE_URL=https://openrouter.ai/api/v1 openhands --headless --json --override-with-envs --exit-without-confirmation -t 'Print the string OPENHANDS_OK to stdout via the terminal tool.'",
  workdir="/tmp",
  timeout=120
)
```

Якщо потік JSONL закінчується `FinishAction`, у якому `action.message` містить `OPENHANDS_OK`, інсталяція працює.

## Пов’язане

- [OpenHands GitHub](https://github.com/All-Hands-AI/OpenHands)
- [OpenHands CLI command reference](https://docs.openhands.dev/openhands/usage/cli/command-reference)
- Суміжні навички: `claude-code` (лише Anthropic), `codex` (лише OpenAI), `opencode` (мульти‑провайдер через OpenCode), `hermes-agent` (підагенти Hermes через `delegate_task`).