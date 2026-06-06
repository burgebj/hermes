---
sidebar_position: 1
title: "Архитектура"
description: "Внутреннее устройство Hermes Agent — основные подсистемы, пути выполнения, поток данных и где читать дальше"
---

# Архитектура

Эта страница — карта верхнего уровня внутренностей Hermes Agent. Используй её, чтобы сориентироваться в кодовой базе, а затем переходи к документам конкретных подсистем для деталей реализации.

## Обзор системы

```text
┌─────────────────────────────────────────────────────────────────────┐
│                        Entry Points                                  │
│                                                                      │
│  CLI (cli.py)    Gateway (gateway/run.py)    ACP (acp_adapter/)     │
│  Batch Runner    API Server                  Python Library          │
└──────────┬──────────────┬───────────────────────┬───────────────────┘
           │              │                       │
           ▼              ▼                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     AIAgent (run_agent.py)                          │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ Prompt       │  │ Provider     │  │ Tool         │               │
│  │ Builder      │  │ Resolution   │  │ Dispatch     │               │
│  │ (prompt_     │  │ (runtime_    │  │ (model_      │               │
│  │  builder.py) │  │  provider.py)│  │  tools.py)   │               │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘               │
│         │                 │                 │                       │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐               │
│  │ Compression  │  │ 3 API Modes  │  │ Tool Registry│               │
│  │ & Caching    │  │ chat_compl.  │  │ (registry.py)│               │
│  │              │  │ codex_resp.  │  │ 70+ tools    │               │
│  │              │  │ anthropic    │  │ 28 toolsets  │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
└─────────┴─────────────────┴─────────────────┴───────────────────────┘
           │                                    │
           ▼                                    ▼
┌───────────────────┐              ┌──────────────────────┐
│ Session Storage   │              │ Tool Backends         │
│ (SQLite + FTS5)   │              │ Terminal (6 backends) │
│ hermes_state.py   │              │ Browser (5 backends)  │
│ gateway/session.py│              │ Web (4 backends)      │
└───────────────────┘              │ MCP (dynamic)         │
                                   │ File, Vision, etc.    │
                                   └──────────────────────┘
```

## Структура каталогов

```text
hermes-agent/
├── run_agent.py              # AIAgent — core conversation loop (large file)
├── cli.py                    # HermesCLI — interactive terminal UI (large file)
├── model_tools.py            # Tool discovery, schema collection, dispatch
├── toolsets.py               # Tool groupings and platform presets
├── hermes_state.py           # SQLite session/state database with FTS5
├── hermes_constants.py       # HERMES_HOME, profile-aware paths
├── batch_runner.py           # Batch trajectory generation
│
├── agent/                    # Agent internals
│   ├── prompt_builder.py     # System prompt assembly
│   ├── context_engine.py     # ContextEngine ABC (pluggable)
│   ├── context_compressor.py # Default engine — lossy summarization
│   ├── prompt_caching.py     # Anthropic prompt caching
│   ├── auxiliary_client.py   # Auxiliary LLM for side tasks (vision, summarization)
│   ├── model_metadata.py     # Model context lengths, token estimation
│   ├── models_dev.py         # models.dev registry integration
│   ├── anthropic_adapter.py  # Anthropic Messages API format conversion
│   ├── display.py            # KawaiiSpinner, tool preview formatting
│   ├── skill_commands.py     # Skill slash commands
│   ├── memory_manager.py    # Memory manager orchestration
│   ├── memory_provider.py   # Memory provider ABC
│   └── trajectory.py         # Trajectory saving helpers
│
├── hermes_cli/               # CLI subcommands and setup
│   ├── main.py               # Entry point — all `hermes` subcommands (large file)
│   ├── config.py             # DEFAULT_CONFIG, OPTIONAL_ENV_VARS, migration
│   ├── commands.py           # COMMAND_REGISTRY — central slash command definitions
│   ├── auth.py               # PROVIDER_REGISTRY, credential resolution
│   ├── runtime_provider.py   # Provider → api_mode + credentials
│   ├── models.py             # Model catalog, provider model lists
│   ├── model_switch.py       # /model command logic (CLI + gateway shared)
│   ├── setup.py              # Interactive setup wizard (large file)
│   ├── skin_engine.py        # CLI theming engine
│   ├── skills_config.py      # hermes skills — enable/disable per platform
│   ├── skills_hub.py         # /skills slash command
│   ├── tools_config.py       # hermes tools — enable/disable per platform
│   ├── plugins.py            # PluginManager — discovery, loading, hooks
│   ├── callbacks.py          # Terminal callbacks (clarify, sudo, approval)
│   └── gateway.py            # hermes gateway start/stop
│
├── tools/                    # Tool implementations (one file per tool)
│   ├── registry.py           # Central tool registry
│   ├── approval.py           # Dangerous command detection
│   ├── terminal_tool.py      # Terminal orchestration
│   ├── process_registry.py   # Background process management
│   ├── file_tools.py         # read_file, write_file, patch, search_files
│   ├── web_tools.py          # web_search, web_extract
│   ├── browser_tool.py       # 10 browser automation tools
│   ├── code_execution_tool.py # execute_code sandbox
│   ├── delegate_tool.py      # Subagent delegation
│   ├── mcp_tool.py           # MCP client (large file)
│   ├── credential_files.py   # File-based credential passthrough
│   ├── env_passthrough.py    # Env var passthrough for sandboxes
│   ├── ansi_strip.py         # ANSI escape stripping
│   └── environments/         # Terminal backends (local, docker, ssh, modal, daytona, singularity)
│
├── gateway/                  # Messaging platform gateway
│   ├── run.py                # GatewayRunner — message dispatch (large file)
│   ├── session.py            # SessionStore — conversation persistence
│   ├── delivery.py           # Outbound message delivery
│   ├── pairing.py            # DM pairing authorization
│   ├── hooks.py              # Hook discovery and lifecycle events
│   ├── mirror.py             # Cross-session message mirroring
│   ├── status.py             # Token locks, profile-scoped process tracking
│   ├── builtin_hooks/        # Extension point for always-registered hooks (none shipped)
│   └── platforms/            # 20 adapters: telegram, discord, slack, whatsapp,
│                             #   signal, matrix, mattermost, email, sms,
│                             #   dingtalk, feishu, wecom, wecom_callback, weixin,
│                             #   bluebubbles, qqbot, homeassistant, webhook, api_server,
│                             #   yuanbao
│
├── acp_adapter/              # ACP server (VS Code / Zed / JetBrains)
├── cron/                     # Scheduler (jobs.py, scheduler.py)
├── plugins/memory/           # Memory provider plugins
├── plugins/context_engine/   # Context engine plugins
├── skills/                   # Bundled skills (always available)
├── optional-skills/          # Official optional skills (install explicitly)
├── website/                  # Docusaurus documentation site
└── tests/                    # Pytest suite (~25,000 tests across ~1,250 files)
```

## Поток данных

### CLI‑сессия

```text
User input → HermesCLI.process_input()
  → AIAgent.run_conversation()
    → prompt_builder.build_system_prompt()
    → runtime_provider.resolve_runtime_provider()
    → API call (chat_completions / codex_responses / anthropic_messages)
    → tool_calls? → model_tools.handle_function_call() → loop
    → final response → display → save to SessionDB
```

### Сообщение шлюза

```text
Platform event → Adapter.on_message() → MessageEvent
  → GatewayRunner._handle_message()
    → authorize user
    → resolve session key
    → create AIAgent with session history
    → AIAgent.run_conversation()
    → deliver response back through adapter
```

### Cron‑задача

```text
Scheduler tick → load due jobs from jobs.json
  → create fresh AIAgent (no history)
  → inject attached skills as context
  → run job prompt
  → deliver response to target platform
  → update job state and next_run
```

## Рекомендуемый порядок чтения

Если ты новичок в кодовой базе:

1. **Эта страница** — сориентируйся
2. **[Внутренности цикла агента](./agent-loop.md)** — как работает AIAgent
3. **[Сборка подсказки](./prompt-assembly.md)** — построение системной подсказки
4. **[Разрешение среды провайдера](./provider-runtime.md)** — как выбираются провайдеры
5. **[Добавление провайдеров](./adding-providers.md)** — практическое руководство по добавлению нового провайдера
6. **[Среда инструментов](./tools-runtime.md)** — реестр инструментов, диспетчеризация, окружения
7. **[Хранилище сессий](./session-storage.md)** — схема SQLite, FTS5, родословная сессий
8. **[Внутренности шлюза](./gateway-internals.md)** — шлюз платформ обмена сообщениями
9. **[Сжатие контекста и кэширование подсказок](./context-compression-and-caching.md)** — сжатие и кэширование
10. **[Внутренности ACP](./acp-internals.md)** — интеграция IDE

## Основные подсистемы

### Цикл агента

Синхронный движок оркестрации (`AIAgent` в `run_agent.py`). Обрабатывает выбор провайдера, построение подсказки, выполнение инструментов, повторные попытки, запасной вариант, обратные вызовы, сжатие и сохранение. Поддерживает три режима API для разных бекендов провайдеров.

→ [Agent Loop Internals](./agent-loop.md)

### Система подсказок

Построение и поддержка подсказки на протяжении всего жизненного цикла диалога:

- **`prompt_builder.py`** — собирает системную подсказку из: личности (SOUL.md), памяти (MEMORY.md, USER.md), навыков, файлов контекста (AGENTS.md, .hermes.md), рекомендаций по использованию инструментов и инструкций, специфичных для модели
- **`prompt_caching.py`** — применяет точки разрыва кэша Anthropic для кэширования префикса
- **`context_compressor.py`** — суммирует промежуточные реплики диалога, когда контекст превышает пороги

→ [Prompt Assembly](./prompt-assembly.md), [Context Compression & Prompt Caching](./context-compression-and-caching.md)

### Разрешение провайдера

Общий рантайм‑резольвер, используемый CLI, шлюзом, cron, ACP и вспомогательными вызовами. Сопоставляет кортежи `(provider, model)` с `(api_mode, api_key, base_url)`. Обрабатывает более 18 провайдеров, OAuth‑потоки, пул учётных данных и разрешение алиасов.

→ [Provider Runtime Resolution](./provider-runtime.md)

### Система инструментов

Центральный реестр инструментов (`tools/registry.py`) с более чем 70 зарегистрированными инструментами в ≈ 28 наборах. Каждый файл инструмента саморегистрируется при импорте. Реестр управляет сбором схем, диспетчеризацией, проверкой доступности и обёрткой ошибок. Инструменты терминала поддерживают 6 бекендов (local, Docker, SSH, Daytona, Modal, Singularity).

→ [Tools Runtime](./tools-runtime.md)

### Сохранение сессий

Хранилище сессий на базе SQLite с полнотекстовым поиском FTS5. Сессии имеют отслеживание родословной (родитель/потомок при сжатиях), изоляцию по платформам и атомарные записи с обработкой конфликтов.

→ [Session Storage](./session-storage.md)

### Шлюз обмена сообщениями

Долгоживущий процесс с 20 адаптерами платформ, унифицированной маршрутизацией сессий, авторизацией пользователей (белые списки + сопряжение DM), диспетчеризацией слеш‑команд, системой хуков, тик‑тактами cron и фоновым обслуживанием.

→ [Gateway Internals](./gateway-internals.md)

### Система плагинов

Три источника обнаружения: `~/.hermes/plugins/` (пользователь), `.hermes/plugins/` (проект) и точки входа pip. Плагины регистрируют инструменты, хуки и команды CLI через API контекста. Существуют два специализированных типа плагинов: провайдеры памяти (`plugins/memory/`) и движки контекста (`plugins/context_engine/`). Оба являются единственными выборами — только один из каждого типа может быть активен одновременно, настраивается через `hermes plugins` или `config.yaml`.

→ [Plugin Guide](/guides/build-a-hermes-plugin), [Memory Provider Plugin](./memory-provider-plugin.md)

### Cron

Задачи первого класса агента (не shell‑задачи). Задачи хранятся в JSON, поддерживают несколько форматов расписания, могут привязывать навыки и скрипты и доставляются на любую платформу.

→ [Cron Internals](./cron-internals.md)

### Интеграция ACP

Предоставляет Hermes как агент, встроенный в редактор, через stdio/JSON‑RPC для VS Code, Zed и JetBrains.

→ [ACP Internals](./acp-internals.md)

### Траектории

Генерирует траектории в формате ShareGPT из сессий агента для создания обучающих данных.

→ [Trajectories & Training Format](./trajectory-format.md)

## Принципы проектирования

| Принцип | Что это значит на практике |
|-----------|--------------------------|
| **Стабильность подсказки** | Системная подсказка не меняется в середине диалога. Нет разрушения кэша, кроме явных действий пользователя (`/model`). |
| **Наблюдаемое выполнение** | Каждый вызов инструмента виден пользователю через обратные вызовы. Обновления прогресса в CLI (спиннер) и в шлюзе (сообщения чата). |
| **Прерываемость** | API‑вызовы и выполнение инструментов можно отменить в полёте вводом пользователя или сигналами. |
| **Платформенно‑агностичное ядро** | Один класс `AIAgent` обслуживает CLI, шлюз, ACP, пакетный режим и API‑сервер. Платформенные различия находятся в точке входа, а не в агенте. |
| **Слабая связность** | Опциональные подсистемы (MCP, плагины, провайдеры памяти, среды RL) используют паттерн реестра и проверку `check_fn`, а не жёсткие зависимости. |
| **Изоляция профилей** | Каждый профиль (`hermes -p <name>`) получает собственный `HERMES_HOME`, конфигурацию, память, сессии и PID шлюза. Несколько профилей могут работать одновременно. |

## Цепочка зависимостей файлов

```text
tools/registry.py  (no deps — imported by all tool files)
       ↑
tools/*.py  (each calls registry.register() at import time)
       ↑
model_tools.py  (imports tools/registry + triggers tool discovery)
       ↑
run_agent.py, cli.py, batch_runner.py, environments/
```

Эта цепочка означает, что регистрация инструментов происходит во время импорта, до создания любого экземпляра агента. Любой файл `tools/*.py` с вызовом `registry.register()` на верхнем уровне автоматически обнаруживается — список ручных импортов не требуется.