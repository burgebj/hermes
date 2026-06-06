---
sidebar_position: 8
title: "Программная интеграция"
description: "Три протокола для управления hermes-agent из внешних программ: ACP, шлюз TUI JSON‑RPC и совместимый с OpenAI HTTP API"
---

# Программная интеграция

Hermes поставляется с тремя протоколами для управления агентом из внешних программ — плагинов IDE, пользовательских UI, CI‑конвейеров, встроенных суб‑агентов. Выбери тот, который соответствует твоему транспорту и потребителю.

| Protocol | Transport | Best for | Defined by |
|----------|-----------|----------|------------|
| **ACP** | JSON-RPC over stdio | IDE clients (VS Code, Zed, JetBrains) that already speak the [Agent Client Protocol](https://github.com/zed-industries/agent-client-protocol) | `acp_adapter/` |
| **TUI gateway** | JSON-RPC over stdio (or WebSocket) | Custom hosts that want fine-grained control of sessions, slash commands, approvals, and streaming events | `tui_gateway/server.py` |
| **API server** | HTTP + Server-Sent Events | OpenAI‑compatible frontends (Open WebUI, LobeChat, LibreChat…) and language‑agnostic web clients | `gateway/platforms/api_server.py` |

Все три управляют одним и тем же ядром `AIAgent`. Они различаются только форматом передачи данных и набором функций, которые они раскрывают.

---

## ACP (Agent Client Protocol)

`hermes acp` запускает сервер JSON‑RPC через stdio, говорящий по ACP. Используется в продакшене в VS Code (расширение ACP от Zed Industries), Zed и любой IDE JetBrains с плагином ACP.

Экспонируемые возможности: создание сессии, отправка подсказки, потоковая передача фрагментов сообщений агента, события вызова инструмента, запросы разрешений, форк сессии, отмена и аутентификация. Вывод инструмента рендерится в блоки контента ACP `Diff`/`ToolCall`, которые понимает IDE.

Полный жизненный цикл, мост событий и процесс одобрения: [ACP Internals](./acp-internals).

```bash
hermes acp                  # serve ACP on stdio
hermes acp --bootstrap      # print install snippet for an ACP-capable IDE
```

---

## TUI Gateway JSON‑RPC

`tui_gateway/server.py` — протокол, к которому обращаются Ink TUI (`hermes --tui`) и встроенный PTY‑мост дашборда. Любой внешний хост может говорить тем же протоколом через stdio (или WebSocket через `tui_gateway/ws.py`).

### Каталог методов (выбранные)

```
prompt.submit           prompt.background       session.steer
session.create          session.list            session.active_list
session.activate        session.close           session.interrupt
session.history         session.compress        session.branch
session.title           session.usage           session.status
clarify.respond         sudo.respond            secret.respond
approval.respond        config.set / config.get commands.catalog
command.resolve         command.dispatch        cli.exec
reload.mcp              reload.env              process.stop
delegation.status       subagent.interrupt      spawn_tree.save / list / load
terminal.resize         clipboard.paste         image.attach
```

`session.active_list`, `session.activate` и `session.close` — локальные управляющие команды живой сессии, используемые переключателем сессий TUI. Используй `session.list` / `/resume` для поиска сохранённых транскриптов; активные методы сессии применяй только к сессиям, которые в данный момент открыты в процессе шлюза TUI.

### Потоковые события

`message.delta`, `message.complete`, `tool.start`, `tool.progress`, `tool.complete`, `approval.request`, `clarify.request`, `sudo.request`, `secret.request`, `gateway.ready`, плюс события жизненного цикла сессии и ошибки.

### Сопоставление Pi‑стиля RPC

Каждая команда из спецификации Pi‑mono RPC ([issue #360](https://github.com/NousResearch/hermes-agent/issues/360)) имеет эквивалент в шлюзе TUI:

| Pi command | Hermes equivalent |
|------------|-------------------|
| `prompt` | `prompt.submit` (or ACP `session/prompt`) |
| `steer` | `session.steer` |
| `follow_up` | `prompt.submit` queued after current turn |
| `abort` | `session.interrupt` |
| `set_model` | `command.dispatch` for `/model <provider:model>` (mid-session, persistent) |
| `compact` | `session.compress` |
| `get_state` | `session.status` |
| `get_messages` | `session.history` |
| `switch_session` | `session.resume` |
| `fork` | `session.branch` |
| `ui_request` / `ui_response` | `clarify.respond` / `sudo.respond` / `secret.respond` / `approval.respond` |

---

## OpenAI‑совместимый API‑сервер

`gateway/platforms/api_server.py` раскрывает Hermes через HTTP для любого клиента, уже говорящего форматом OpenAI. Полезно, когда нужен веб‑фронтенд, CI‑раннер на curl или клиент, не зависящий от Python.

Точки входа:

```
POST /v1/chat/completions        OpenAI Chat Completions (streaming via SSE)
POST /v1/responses               OpenAI Responses API (stateful)
POST /v1/runs                    Start a run, returns run_id (202)
GET  /v1/runs/{id}               Run status
GET  /v1/runs/{id}/events        SSE stream of lifecycle events
POST /v1/runs/{id}/approval      Resolve a pending approval
POST /v1/runs/{id}/stop          Interrupt the run
GET  /v1/capabilities            Machine-readable feature flags
GET  /v1/models                  Lists hermes-agent
GET  /health, /health/detailed
```

Настройка, заголовки (`X-Hermes-Session-Id`, `X-Hermes-Session-Key`) и подключение фронтенда: [API Server](../user-guide/features/api-server).

---

## Какой вариант выбрать?

- **Ты пишешь плагин IDE, и IDE уже поддерживает ACP** → ACP. Никакой работы с протоколом на стороне IDE не требуется.
- **Ты пишешь собственный десктопный / веб / TUI‑хост и хочешь все возможности Hermes** (слеш‑команды, одобрения, уточнения, мульти‑агент, форк сессий) → TUI gateway JSON‑RPC.
- **Тебе нужен любой OpenAI‑совместимый фронтенд, язык‑независимый HTTP‑клиент или автоматизация через curl** → API server.
- **Ты хочешь встроить Hermes в процесс Python без отдельного подпроцесса** → импортируй `run_agent.AIAgent` напрямую. См. [Agent Loop](./agent-loop).

---

## Горячая замена модели

Переключение модели в середине сессии работает во всех случаях — это фактически слеш‑команда `/model`.

- **CLI / TUI:** `/model claude-sonnet-4` или `/model openrouter:anthropic/claude-sonnet-4.6`
- **TUI gateway RPC:** `command.dispatch` с `{"command": "/model claude-sonnet-4"}`
- **ACP:** IDE отправляет слеш‑команду как подсказку; агент её обрабатывает
- **API server:** укажи поле `model` в теле запроса или задай заголовок `X-Hermes-Model`

Разрешение с учётом провайдера (одно и то же имя модели автоматически подбирает правильный формат для текущего провайдера) реализовано встроенно. См. `hermes_cli/model_switch.py`.

---

## Примечание о `--mode rpc`

У Hermes нет флага `--mode rpc`. Три перечисленных выше протокола уже покрывают все сценарии — ACP для клиентов IDE, шлюз TUI для хостов stdio JSON‑RPC и API‑сервер для HTTP. Если ты обнаружил реальный пробел, который никто из них не заполняет, открой issue с конкретным потребителем, который ты разрабатываешь.