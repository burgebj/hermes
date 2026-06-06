---
sidebar_position: 8
title: "Програмна інтеграція"
description: "Три протоколи для керування Hermes Agent з зовнішніх програм: ACP, шлюз TUI JSON‑RPC та сумісний з OpenAI HTTP API"
---

# Програмна інтеграція

Hermes постачається з трьома протоколами для керування агентом з зовнішніх програм — плагіни IDE, кастомні UI, CI‑конвеєри, вбудовані під‑агенти. Обери той, що відповідає твоєму транспорту та споживачу.

| Протокол | Транспорт | Найкраще підходить для | Визначено |
|----------|-----------|------------------------|-----------|
| **ACP** | JSON‑RPC over stdio | IDE‑клієнти (VS Code, Zed, JetBrains), які вже підтримують [Agent Client Protocol](https://github.com/zed-industries/agent-client-protocol) | `acp_adapter/` |
| **TUI gateway** | JSON‑RPC over stdio (або WebSocket) | Кастомні хости, які потребують тонкого керування сесіями, слеш‑командами, затвердженнями та потоковими подіями | `tui_gateway/server.py` |
| **API server** | HTTP + Server‑Sent Events | OpenAI‑сумісні фронтенди (Open WebUI, LobeChat, LibreChat…) та мова‑незалежні веб‑клієнти | `gateway/platforms/api_server.py` |

Усі три керують одним ядром `AIAgent`. Вони різняться лише форматом передачі даних та набором функцій, які вони відкривають.

---

## ACP (Agent Client Protocol)

`hermes acp` запускає сервер JSON‑RPC через stdio, який спілкується за протоколом ACP. Використовується у продакшені VS Code (розширення ACP від Zed Industries), Zed та будь‑якій IDE JetBrains з плагіном ACP.

Функції, що експонуються: створення сесії, надсилання підказки, потокове передавання фрагментів повідомлень агента, події виклику інструменту, запити дозволу, розгалуження сесії, скасування та автентифікація. Вихід інструменту рендериться у блоки вмісту ACP `Diff`/`ToolCall`, які розуміє IDE.

Повний життєвий цикл, міст подій та процес затвердження: [ACP Internals](./acp-internals).

```bash
hermes acp                  # serve ACP on stdio
hermes acp --bootstrap      # print install snippet for an ACP-capable IDE
```

---

## TUI Gateway JSON‑RPC

`tui_gateway/server.py` — це протокол, яким користується Ink TUI (`hermes --tui`) та вбудований PTY‑мост дашборда. Будь‑який зовнішній хост може спілкуватися за тим же протоколом через stdio (або WebSocket через `tui_gateway/ws.py`).

### Каталог методів (вибрано)

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

`session.active_list`, `session.activate` та `session.close` — це локальні керування живими сесіями, які використовує перемикач сесій TUI. Використовуй `session.list` / `/resume` для пошуку збережених транскриптів; активні методи застосовуй лише до сесій, які наразі відкриті в процесі TUI‑gateway.

### Події, що передаються у потоці

`message.delta`, `message.complete`, `tool.start`, `tool.progress`, `tool.complete`, `approval.request`, `clarify.request`, `sudo.request`, `secret.request`, `gateway.ready`, а також події життєвого циклу сесії та помилок.

### Відображення RPC у стилі Pi

Кожна команда у специфікації Pi‑mono RPC ([issue #360](https://github.com/NousResearch/hermes-agent/issues/360)) має еквівалент у TUI‑gateway:

| Команда Pi | Еквівалент у Hermes |
|------------|---------------------|
| `prompt` | `prompt.submit` (або ACP `session/prompt`) |
| `steer` | `session.steer` |
| `follow_up` | `prompt.submit` у черзі після поточного ходу |
| `abort` | `session.interrupt` |
| `set_model` | `command.dispatch` для `/model <provider:model>` (під час сесії, постійно) |
| `compact` | `session.compress` |
| `get_state` | `session.status` |
| `get_messages` | `session.history` |
| `switch_session` | `session.resume` |
| `fork` | `session.branch` |
| `ui_request` / `ui_response` | `clarify.respond` / `sudo.respond` / `secret.respond` / `approval.respond` |

---

## OpenAI‑сумісний API Server

`gateway/platforms/api_server.py` надає Hermes через HTTP для будь‑якого клієнта, який вже розуміє формат OpenAI. Корисно, коли потрібен веб‑фронтенд, CI‑раннер на базі curl або споживач, що не написаний на Python.

Точки входу:

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

Налаштування, заголовки (`X-Hermes-Session-Id`, `X-Hermes-Session-Key`) та підключення фронтенду: [API Server](../user-guide/features/api-server).

---

## Який варіант обрати?

- **Ти пишеш плагін IDE, і IDE вже підтримує ACP** → ACP. Нуль роботи з протоколом на боці IDE.
- **Ти створюєш кастомний десктоп/веб/TUI‑хост і хочеш усі можливості Hermes** (слеш‑команди, затвердження, уточнення, мульти‑агент, розгалуження сесій) → TUI gateway JSON‑RPC.
- **Тобі потрібен будь‑який OpenAI‑сумісний фронтенд, мова‑незалежний HTTP‑клієнт або автоматизація через curl** → API server.
- **Ти хочеш вбудувати Hermes у процес Python без створення підпроцесу** → імпортуй `run_agent.AIAgent` безпосередньо. Дивись [Agent Loop](./agent-loop).

---

## Гаряча заміна моделі

Перемикання моделі під час сесії працює на всіх рівнях — це слеш‑команда `/model` «під капотом».

- **CLI / TUI:** `/model claude-sonnet-4` або `/model openrouter:anthropic/claude-sonnet-4.6`
- **TUI gateway RPC:** `command.dispatch` з `{"command": "/model claude-sonnet-4"}`
- **ACP:** IDE надсилає слеш‑команду як підказку; агент її обробляє
- **API server:** додай поле `model` у тіло запиту або встанови заголовок `X-Hermes-Model`

Розв’язання, залежне від провайдера (те саме ім’я моделі підбирає правильний формат для конкретного провайдера), вбудовано. Дивись `hermes_cli/model_switch.py`.

---

## Примітка щодо `--mode rpc`

Hermes не має прапорця `--mode rpc`. Три протоколи вище вже охоплюють усі випадки використання — ACP для клієнтів IDE‑протоколу, TUI gateway для хостів stdio JSON‑RPC та API server для HTTP. Якщо ти виявив реальну прогалину, яку жоден з них не заповнює, відкрий issue з конкретним споживачем, який ти розробляєш.