---
sidebar_position: 1
title: "Архітектура"
description: "Внутрішня архітектура Hermes Agent — основні підсистеми, шляхи виконання, потік даних та куди читати далі"
---

# Архітектура

Ця сторінка — карта верхнього рівня внутрішньої структури Hermes Agent. Використовуй її, щоб орієнтуватися у кодовій базі, а потім занурюватися у документи підсистем для деталей реалізації.

## Огляд системи

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

## Структура каталогів

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

## Потік даних

### CLI‑сесія

```text
User input → HermesCLI.process_input()
  → AIAgent.run_conversation()
    → prompt_builder.build_system_prompt()
    → runtime_provider.resolve_runtime_provider()
    → API call (chat_completions / codex_responses / anthropic_messages)
    → tool_calls? → model_tools.handle_function_call() → loop
    → final response → display → save to SessionDB
```

### Повідомлення шлюзу

```text
Platform event → Adapter.on_message() → MessageEvent
  → GatewayRunner._handle_message()
    → authorize user
    → resolve session key
    → create AIAgent with session history
    → AIAgent.run_conversation()
    → deliver response back through adapter
```

### Cron‑завдання

```text
Scheduler tick → load due jobs from jobs.json
  → create fresh AIAgent (no history)
  → inject attached skills as context
  → run job prompt
  → deliver response to target platform
  → update job state and next_run
```

## Рекомендований порядок читання

Якщо ти новий у кодовій базі:

1. **Ця сторінка** — орієнтуйся
2. **[Agent Loop Internals](./agent-loop.md)** — як працює AIAgent
3. **[Prompt Assembly](./prompt-assembly.md)** — побудова системного промпту
4. **[Provider Runtime Resolution](./provider-runtime.md)** — як вибираються провайдери
5. **[Adding Providers](./adding-providers.md)** — практичний посібник з додавання нового провайдера
6. **[Tools Runtime](./tools-runtime.md)** — реєстр інструментів, диспетчеризація, середовища
7. **[Session Storage](./session-storage.md)** — схема SQLite, FTS5, родовід сесій
8. **[Gateway Internals](./gateway-internals.md)** — шлюз платформи обміну повідомленнями
9. **[Context Compression & Prompt Caching](./context-compression-and-caching.md)** — компресія та кешування
10. **[ACP Internals](./acp-internals.md)** — інтеграція IDE

## Основні підсистеми

### Agent Loop

Синхронний оркестраційний движок (`AIAgent` у `run_agent.py`). Обробляє вибір провайдера, побудову промпту, виконання інструментів, повтори, запасний (варіант), зворотні виклики, компресію та збереження. Підтримує три режими API для різних бекендів провайдерів.

→ [Agent Loop Internals](./agent-loop.md)

### Prompt System

Побудова та підтримка промпту протягом життєвого циклу розмови:

- **`prompt_builder.py`** — збирає системний промпт з: персональності (SOUL.md), пам’яті (MEMORY.md, USER.md), навичок, контекстних файлів (AGENTS.md, .hermes.md), рекомендацій щодо використання інструментів та інструкцій, специфічних для моделі
- **`prompt_caching.py`** — застосовує точки розриву кешу Anthropic для кешування префікса
- **`context_compressor.py`** — підсумовує проміжні ходи розмови, коли контекст перевищує пороги

→ [Prompt Assembly](./prompt-assembly.md), [Context Compression & Prompt Caching](./context-compression-and-caching.md)

### Provider Resolution

Спільний рантайм‑резолвер, що використовується CLI, шлюзом, cron, ACP та допоміжними викликами. Відображає кортежі `(provider, model)` у `(api_mode, api_key, base_url)`. Підтримує 18+ провайдерів, OAuth‑потоки, пул облікових даних та розв’язання псевдонімів.

→ [Provider Runtime Resolution](./provider-runtime.md)

### Tool System

Центральний реєстр інструментів (`tools/registry.py`) з 70+ зареєстрованих інструментів у ~28 наборах інструментів. Кожен файл інструменту самореєструється під час імпорту. Реєстр обробляє збір схеми, диспетчеризацію, перевірку доступності та обгортання помилок. Терминальні інструменти підтримують 6 бекендів (local, Docker, SSH, Daytona, Modal, Singularity).

→ [Tools Runtime](./tools-runtime.md)

### Session Persistence

Зберігання сесій на базі SQLite з повнотекстовим пошуком FTS5. Сесії мають відстеження родоводу (батько/дитина через компресії), ізоляцію per‑platform та атомарні записи з обробкою конфліктів.

→ [Session Storage](./session-storage.md)

### Messaging Gateway

Довготривалий процес з 20 адаптерами платформ, уніфікованою маршрутизацією сесій, авторизацією користувачів (білі списки + DM‑парування), диспетчеризацією slash‑команд, системою хуків, cron‑тиками та фоновим обслуговуванням.

→ [Gateway Internals](./gateway-internals.md)

### Plugin System

Три джерела виявлення: `~/.hermes/plugins/` (користувач), `.hermes/plugins/` (проект) та pip‑entry points. Плагіни реєструють інструменти, хуки та CLI‑команди через API контексту. Існує два спеціалізованих типи плагінів: провайдери пам’яті (`plugins/memory/`) та контекстні движери (`plugins/context_engine/`). Обидва — одиничний вибір: лише один з кожного типу може бути активним одночасно, налаштовується через `hermes plugins` або `config.yaml`.

→ [Plugin Guide](/guides/build-a-hermes-plugin), [Memory Provider Plugin](./memory-provider-plugin.md)

### Cron

Завдання першого класу для агента (не shell‑завдання). Завдання зберігаються у JSON, підтримують кілька форматів розкладу, можуть приєднувати навички та скрипти і доставляються на будь‑яку платформу.

→ [Cron Internals](./cron-internals.md)

### ACP Integration

Надає Hermes як агент, вбудований у редактор, через stdio/JSON‑RPC для VS Code, Zed та JetBrains.

→ [ACP Internals](./acp-internals.md)

### Trajectories

Генерує траєкторії у форматі ShareGPT з сесій агента для створення навчальних даних.

→ [Trajectories & Training Format](./trajectory-format.md)

## Принципи дизайну

| Принцип | Що це означає на практиці |
|-----------|--------------------------|
| **Prompt stability** | Системний промпт не змінюється під час розмови. Ніякі зміни, що руйнують кеш, окрім явних дій користувача (`/model`). |
| **Observable execution** | Кожен виклик інструменту видно користувачеві через зворотні виклики. Оновлення прогресу у CLI (спіннер) та шлюзі (повідомлення чату). |
| **Interruptible** | API‑виклики та виконання інструментів можна скасувати «на льоту» ввідмою користувача або сигналами. |
| **Platform-agnostic core** | Один клас AIAgent обслуговує CLI, шлюз, ACP, batch та API‑сервер. Платформенні відмінності живуть у точці входу, а не в агенті. |
| **Loose coupling** | Додаткові підсистеми (MCP, плагіни, провайдери пам’яті, RL‑оточення) використовують патерн реєстру та перевірки `check_fn`, а не жорсткі залежності. |
| **Profile isolation** | Кожен профіль (`hermes -p <name>`) має власний HERMES_HOME, конфіг, пам’ять, сесії та PID шлюзу. Кілька профілів можуть працювати одночасно. |

## Ланцюжок залежностей файлів

```text
tools/registry.py  (no deps — imported by all tool files)
       ↑
tools/*.py  (each calls registry.register() at import time)
       ↑
model_tools.py  (imports tools/registry + triggers tool discovery)
       ↑
run_agent.py, cli.py, batch_runner.py, environments/
```

Цей ланцюжок означає, що реєстрація інструментів відбувається під час імпорту, до створення будь‑якого екземпляра агента. Будь‑який файл `tools/*.py` з викликом `registry.register()` на верхньому рівні автоматично виявляється — список ручних імпортів не потрібен.