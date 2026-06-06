---
title: "Openhands — Делегировать кодирование OpenHands CLI (model-agnostic, LiteLLM)"
sidebar_label: "Openhands"
description: "Делегировать кодирование OpenHands CLI (model-agnostic, LiteLLM)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# OpenHands

Делегировать кодирование OpenHands CLI (модель‑агностичный, LiteLLM).

## Метаданные навыка

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/autonomous-ai-agents/openhands` |
| Path | `optional-skills/autonomous-ai-agents/openhands` |
| Version | `0.1.0` |
| Author | Tim Koepsel (xzessmedia), Hermes Agent |
| License | MIT |
| Platforms | linux, macos |
| Tags | `Coding-Agent`, `OpenHands`, `Model-Agnostic`, `LiteLLM` |
| Related skills | [`claude-code`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-claude-code), [`codex`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-codex), [`opencode`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-opencode), [`hermes-agent`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-hermes-agent) |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает при его активации. Это то, что агент видит как инструкции, когда навык активен.
:::

# OpenHands CLI

Делегировать задачи кодирования [OpenHands CLI](https://github.com/All-Hands-AI/OpenHands) через инструмент `terminal`. OpenHands является модель‑агностичным: любой провайдер, поддерживаемый LiteLLM (OpenAI, Anthropic, OpenRouter, DeepSeek, Ollama, vLLM и др.).

Этот навык — обёртка в headless‑mode для пакетного / одноразового делегирования. Интерактивный текстовый UI из Hermes не используется.

## Когда использовать

- Пользователь хочет делегировать задачу кодирования именно OpenHands.
- Пользователь хочет агента, который может работать с провайдером, отличным от Anthropic / OpenAI (DeepSeek, Qwen, Ollama, vLLM, Nous и др.) — соседние навыки `claude-code` и `codex` привязаны к одному вендору.
- Многошаговые правки файлов + команды оболочки внутри рабочего пространства.

Для Claude‑нативного используйте `claude-code`. Для OpenAI‑нативного — `codex`. Для субагентов Hermes — `delegate_task`.

## Предварительные требования

1. Установить upstream (требуется Python 3.12+ и `uv`):

   ```
   terminal(command="uv tool install openhands --python 3.12")
   ```

   Проверка: `openhands --version` (на момент написания `OpenHands CLI 1.16.0` / `SDK v1.21.0`).

2. Выбрать модель и задать переменные окружения для `--override-with-envs`:

   ```
   export LLM_MODEL=openrouter/openai/gpt-4o-mini       # or any LiteLLM slug
   export LLM_API_KEY=$OPENROUTER_API_KEY
   export LLM_BASE_URL=https://openrouter.ai/api/v1     # omit for native OpenAI
   ```

   `LLM_MODEL` использует полный slug LiteLLM. Когда провайдер — OpenRouter, slug имеет двойной префикс: `openrouter/<vendor>/<model>` (например, `openrouter/anthropic/claude-sonnet-4.5`). Для нативного Anthropic: `anthropic/claude-sonnet-4-5`. Для нативного OpenAI: `openai/gpt-4o-mini`.

3. Подавить стартовый баннер, чтобы вывод JSON не предшествовал ASCII‑арт:

   ```
   export OPENHANDS_SUPPRESS_BANNER=1
   ```

## Как запускать

Всегда вызывай через инструмент `terminal`. Всегда передавай `--headless --json --override-with-envs --exit-without-confirmation` для автоматизации.

### Одноразовая задача

```
terminal(
  command="OPENHANDS_SUPPRESS_BANNER=1 LLM_MODEL=openrouter/openai/gpt-4o-mini LLM_API_KEY=$OPENROUTER_API_KEY LLM_BASE_URL=https://openrouter.ai/api/v1 openhands --headless --json --override-with-envs --exit-without-confirmation -t 'Add error handling to all API calls in src/'",
  workdir="/path/to/project",
  timeout=600
)
```

### Фоновый режим для длительных задач

```
terminal(command="<same as above>", workdir="/path/to/project", background=true, notify_on_complete=true)
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")
```

### Возобновление предыдущего разговора

OpenHands выводит `Conversation ID: <32-hex>` и строку `Hint: openhands --resume <dashed-uuid>` в конце каждого запуска. Используй форму с дефисами для возобновления:

```
terminal(
  command="OPENHANDS_SUPPRESS_BANNER=1 LLM_MODEL=... openhands --headless --json --override-with-envs --exit-without-confirmation --resume <dashed-uuid> -t 'Now fix the bug you found'",
  workdir="/path/to/project"
)
```

## Полный список флагов

Проверено по `openhands --help` (CLI 1.16.0). Всё, чего нет в этой таблице, не является флагом — передавай через переменные окружения или файл настроек.

| Flag | Effect |
|------|--------|
| `--headless` | Без UI, требует `-t` или `-f`. Автоодобряет все действия (нет `--llm-approve` в этом режиме). |
| `--json` | Поток событий JSONL (требует `--headless`). |
| `-t TEXT` | Промпт задачи. |
| `-f PATH` | Читать задачу из файла. |
| `--resume [ID]` | Возобновить разговор. Без ID → список последних. |
| `--last` | Возобновить самый последний (с `--resume`). |
| `--override-with-envs` | Применить переменные `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL`. Без этого OpenHands использует `~/.openhands/settings.json` и игнорирует env. |
| `--exit-without-confirmation` | Не показывать диалог подтверждения выхода. |
| `--always-approve` / `--yolo` | Автоодобрять каждое действие (по умолчанию в `--headless`). |
| `--llm-approve` | LLM‑базированный шлюз безопасности (только интерактивно — НЕ работает в headless). |
| `--version` / `-v` | Вывести версию и выйти. |

**Флагов `--model`, `--max-iterations`, `--workspace`, `--sandbox`, `--sandbox-type` нет.** Модель задаётся через `LLM_MODEL`. Рабочее пространство — это `workdir`, который ты передаёшь инструменту `terminal`. Песочница / runtime задаются переменными `RUNTIME` и `SANDBOX_VOLUMES`.

## Схема JSON‑событий

С `--json --headless` OpenHands выводит JSONL — один JSON‑объект на строку, плюс несколько строк статуса без JSON (`Initializing agent...`, `Agent is working`, `Agent finished`, итоговый блок, `Goodbye!`, `Conversation ID:`, `Hint:`). Фильтруй строки, начинающиеся с `{`.

Поле верхнего уровня `kind` различает типы событий:

- `MessageEvent` — ход текста пользователя / агента. `source` — `user` или `agent`.
- `ActionEvent` — агент выбрал инструмент. Читай `tool_name` (`file_editor`, `terminal`, `finish`) и `action.kind` (`FileEditorAction`, `TerminalAction`, `FinishAction`).
- `ObservationEvent` — результат инструмента. `observation.is_error` — флаг успеха. `source` — `environment`.
- `FinishAction` внутри `ActionEvent` несёт финальное сообщение агента в `action.message`.

CLI сначала выводит весь `stderr` от LiteLLM/Authlib — см. раздел «Подводные камни». Парсить нужно только `stdout`, построчно, игнорируя строки, не начинающиеся с `{`.

## Подводные камни

- **Предупреждения LiteLLM при каждом вызове.** CLI выводит предупреждения `bedrock-runtime` и `sagemaker-runtime` в `stderr`, потому что `botocore` не установлен. Плюс устаревшее сообщение Authlib. Это шум, а не ошибки. Перенаправляй `stderr` в `/dev/null` или фильтруй перед показом пользователю.
- **Спам баннером.** Без `OPENHANDS_SUPPRESS_BANNER=1` каждый запуск начинается с многострочного ASCII‑бокса `+--+`, рекламирующего SDK. Всегда экспортируй эту переменную.
- **`--override-with-envs` обязателен для автоматизации.** Без него OpenHands игнорирует `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` и переходит к `~/.openhands/settings.json`. При свежей установке этого файла нет, и CLI зависает, ожидая настройку первого запуска.
- **Slug модели — slug LiteLLM, а не провайдера.** `openrouter/openai/gpt-4o-mini` работает; `openai/gpt-4o-mini` при указании OpenRouter — нет. `anthropic/claude-sonnet-4-5` (дефис) — нативный Anthropic; `openrouter/anthropic/claude-sonnet-4.5` (точка) — через OpenRouter. Ошибка в slug приводит к непонятной ошибке LiteLLM 400.
- **`pip install openhands-ai` — неверный пакет.** Это устаревший SDK V0. Новый CLI устанавливается командой `uv tool install openhands --python 3.12`. Конда‑пакет не поддерживается.
- **Формат ID для возобновления щекотлив.** CLI заканчивает выводом `Conversation ID: f46573d9cfdb45e492ca189bde40019b` (без дефисов), а затем `Hint: openhands --resume f46573d9-cfdb-45e4-92ca-189bde40019b` (с дефисами). Используй форму с дефисами.
- **Headless игнорирует `--llm-approve`.** При передаче этого флага получаешь ошибку `argparse`. Headless режим жёстко задаёт always‑approve.
- **Отсутствие поддержки Windows upstream.** Документация OpenHands требует WSL на Windows. Этот навык ограничен `[linux, macos]`.
- **`~/.openhands/conversations/<id>/` накапливается.** Каждый запуск сохраняет траекторию. Очищай её при пакетных запусках.
- **Тяжёлая установка (~200 пакетов).** Используй `uv tool install` (изолированное venv), чтобы избежать конфликтов зависимостей с текущим проектом.

## Проверка

```
terminal(
  command="OPENHANDS_SUPPRESS_BANNER=1 LLM_MODEL=openrouter/openai/gpt-4o-mini LLM_API_KEY=$OPENROUTER_API_KEY LLM_BASE_URL=https://openrouter.ai/api/v1 openhands --headless --json --override-with-envs --exit-without-confirmation -t 'Print the string OPENHANDS_OK to stdout via the terminal tool.'",
  workdir="/tmp",
  timeout=120
)
```

Если поток JSONL заканчивается `FinishAction`, у которого `action.message` содержит `OPENHANDS_OK`, установка работает.

## Связанные ссылки

- [OpenHands GitHub](https://github.com/All-Hands-AI/OpenHands)
- [OpenHands CLI command reference](https://docs.openhands.dev/openhands/usage/cli/command-reference)
- Соседние навыки: `claude-code` (только Anthropic), `codex` (только OpenAI), `opencode` (мульти‑провайдер через OpenCode), `hermes-agent` (субагенты Hermes через `delegate_task`).