---
sidebar_position: 11
sidebar_label: "Plugins"
title: "Плагины"
description: "Расширь Hermes пользовательскими инструментами, хуками и интеграциями через систему плагинов"
---

# Плагины

Hermes имеет систему плагинов для добавления пользовательских инструментов, хуков и интеграций без изменения основного кода.

Если ты хочешь создать собственный инструмент для себя, своей команды или проекта, обычно это правильный путь. Страница руководства разработчика
[Adding Tools](/developer-guide/adding-tools) предназначена для встроенных инструментов ядра Hermes, которые находятся в `tools/` и `toolsets.py`.

**→ [Build a Hermes Plugin](/guides/build-a-hermes-plugin)** — пошаговое руководство с полностью рабочим примером.
## Краткий обзор

Перетащи каталог в `~/.hermes/plugins/` вместе с `plugin.yaml` и Python‑кодом:

```
~/.hermes/plugins/my-plugin/
├── plugin.yaml      # manifest
├── __init__.py      # register() — wires schemas to handlers
├── schemas.py       # tool schemas (what the LLM sees)
└── tools.py         # tool handlers (what runs when called)
```

Запусти Hermes — твои инструменты появятся рядом со встроенными. Модель сможет вызвать их сразу.

### Минимальный рабочий пример

Вот полностью готовый плагин, который добавляет инструмент `hello_world` и записывает каждый вызов инструмента через хук.

**`~/.hermes/plugins/hello‑world/plugin.yaml`**

```yaml
name: hello-world
version: "1.0"
description: A minimal example plugin
```

**`~/.hermes/plugins/hello‑world/__init__.py`**

```python
"""Minimal Hermes plugin — registers a tool and a hook."""

import json


def register(ctx):
    # --- Tool: hello_world ---
    schema = {
        "name": "hello_world",
        "description": "Returns a friendly greeting for the given name.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name to greet",
                }
            },
            "required": ["name"],
        },
    }

    def handle_hello(params, **kwargs):
        del kwargs
        name = params.get("name", "World")
        return json.dumps({"success": True, "greeting": f"Hello, {name}!"})

    ctx.register_tool(
        name="hello_world",
        toolset="hello_world",
        schema=schema,
        handler=handle_hello,
        description="Return a friendly greeting for the given name.",
    )

    # --- Hook: log every tool call ---
    def on_tool_call(tool_name, params, result):
        print(f"[hello-world] tool called: {tool_name}")

    ctx.register_hook("post_tool_call", on_tool_call)
```

Помести оба файла в `~/.hermes/plugins/hello‑world/`, перезапусти Hermes, и модель сразу сможет вызвать `hello_world`. Хук выводит строку журнала после каждого вызова инструмента.

Плагины, расположенные в каталоге проекта `./.hermes/plugins/`, по умолчанию отключены. Включай их только для доверенных репозиториев, задав `HERMES_ENABLE_PROJECT_PLUGINS=true` перед запуском Hermes.
## Что могут делать плагины

Каждый API `ctx.*`, перечисленный ниже, доступен внутри функции плагина `register(ctx)`.

| Возможность | Как |
|-----------|-----|
| Добавлять инструменты | `ctx.register_tool(name=..., toolset=..., schema=..., handler=...)` |
| Добавлять хуки | `ctx.register_hook("post_tool_call", callback)` |
| Добавлять slash‑команды | `ctx.register_command(name, handler, description)` — добавляет `/name` в CLI и gateway‑сессиях |
| Вызывать инструменты из команд | `ctx.dispatch_tool(name, args)` — вызывает зарегистрированный инструмент с автоматически подключённым контекстом родительского агента |
| Добавлять CLI‑команды | `ctx.register_cli_command(name, help, setup_fn, handler_fn)` — добавляет `hermes <plugin> <subcommand>` |
| Вставлять сообщения | `ctx.inject_message(content, role="user")` — см. [Вставка сообщений](#injecting-messages) |
| Поставлять файлы данных | `Path(__file__).parent / "data" / "file.yaml"` |
| Группировать skills | `ctx.register_skill(name, path)` — с пространством имён `plugin:skill`, загружается через `skill_view("plugin:skill")` |
| Ограничивать по переменным окружения | `requires_env: [API_KEY]` в `plugin.yaml` — запрашивается во время `hermes plugins install` |
| Распространять через pip | `[project.entry-points."hermes_agent.plugins"]` |
| Регистрация платформы gateway (Discord, Telegram, IRC, …) | `ctx.register_platform(name, label, adapter_factory, check_fn, ...)` — см. [Добавление адаптеров платформ](/developer-guide/adding-platform-adapters) |
| Регистрация бэкенда генерации изображений | `ctx.register_image_gen_provider(provider)` — см. [Плагины провайдеров генерации изображений](/developer-guide/image-gen-provider-plugin) |
| Регистрация бэкенда генерации видео | `ctx.register_video_gen_provider(provider)` — см. [Плагины провайдеров генерации видео](/developer-guide/video-gen-provider-plugin) |
| Регистрация движка сжатия контекста | `ctx.register_context_engine(engine)` — см. [Плагины движков контекста](/developer-guide/context-engine-plugin) |
| Регистрация бэкенда памяти | Наследуй `MemoryProvider` в `plugins/memory/<name>/__init__.py` — см. [Плагины провайдеров памяти](/developer-guide/memory-provider-plugin) (использует отдельную систему обнаружения) |
| Выполнение вызова LLM, управляемого хостом | `ctx.llm.complete(...)` / `ctx.llm.complete_structured(...)` — использует активную модель пользователя + аутентификацию для одноразового завершения с опциональной проверкой JSON‑схемы. См. [Доступ плагина к LLM](/developer-guide/plugin-llm-access) |
| Регистрация inference‑бэкенда (провайдера LLM) | `register_provider(ProviderProfile(...))` в `plugins/model-providers/<name>/__init__.py` — см. [Плагины провайдеров моделей](/developer-guide/model-provider-plugin) (использует отдельную систему обнаружения) |
## Обнаружение плагинов

| Источник | Путь | Сценарий использования |
|----------|------|------------------------|
| Bundled | `<repo>/plugins/` | Поставляется с Hermes — см. [Built-in Plugins](/user-guide/features/built-in-plugins) |
| User | `~/.hermes/plugins/` | Персональные плагины |
| Project | `.hermes/plugins/` | Плагины, специфичные для проекта (требует `HERMES_ENABLE_PROJECT_PLUGINS=true`) |
| pip | `hermes_agent.plugins` entry_points | Распространяемые пакеты |
| Nix | `services.hermes-agent.extraPlugins` / `extraPythonPackages` | Декларативные установки NixOS — см. [Nix Setup](/getting-started/nix-setup#plugins) |

Поздние источники переопределяют более ранние при конфликте имён, поэтому пользовательский плагин с тем же именем, что и встроенный, заменяет его.

### Подкатегории плагинов

В каждом источнике Hermes также распознаёт подкаталоги, которые направляют плагины в специализированные системы обнаружения:

| Подкаталог | Что содержит | Система обнаружения |
|---|---|---|
| `plugins/` (корень) | Общие плагины — инструменты, хуки, slash‑команды, команды CLI, встроенные skills | `PluginManager` (kind: `standalone` or `backend`) |
| `plugins/platforms/<name>/` | Адаптеры каналов шлюза (`ctx.register_platform()`) | `PluginManager` (kind: `platform`, один уровень глубже) |
| `plugins/image_gen/<name>/` | Бэкенды генерации изображений (`ctx.register_image_gen_provider()`) | `PluginManager` (kind: `backend`, один уровень глубже) |
| `plugins/memory/<name>/` | Провайдеры памяти (подкласс `MemoryProvider`) | **Собственный загрузчик** в `plugins/memory/__init__.py` (kind: `exclusive` — один активный одновременно) |
| `plugins/context_engine/<name>/` | Движки сжатия контекста (`ctx.register_context_engine()`) | **Собственный загрузчик** в `plugins/context_engine/__init__.py` (один активный одновременно) |
| `plugins/model-providers/<name>/` | Профили провайдеров LLM (`register_provider(ProviderProfile(...))`) | **Собственный загрузчик** в `providers/__init__.py` (лениво сканируется при первом вызове `get_provider_profile()`) |

Пользовательские плагины в `~/.hermes/plugins/model-providers/<name>/` и `~/.hermes/plugins/memory/<name>/` переопределяют встроенные плагины с тем же именем — правило «последний записавший выигрывает» в `register_provider()` / `register_memory_provider()`. Добавь каталог, и он заменит встроенный без правок репозитория.

Плагины подкатегорий отображаются в `hermes plugins list` и в интерактивном UI `hermes plugins` под их **ключом, полученным из пути** — например `observability/langfuse`, `image_gen/openai`, `platforms/teams`. Этот ключ (а не чистый `name:` из манифеста) используется в командах `hermes plugins enable …` / `disable …` и в строке, которую нужно добавить в `plugins.enabled` в `config.yaml`.
## Плагины включаются по желанию (за некоторыми исключениями)

**Общие плагины и пользовательские бекенды отключены по умолчанию** — система обнаружения находит их (поэтому они отображаются в `hermes plugins` и `/plugins`), но ничего с хуками или инструментами не загружается, пока ты не добавишь имя плагина в `plugins.enabled` в `~/.hermes/config.yaml`. Это предотвращает запуск стороннего кода без твоего явного согласия.

```yaml
plugins:
  enabled:
    - my-tool-plugin
    - disk-cleanup
  disabled:       # optional deny-list — always wins if a name appears in both
    - noisy-plugin
```

Три способа изменить состояние:

```bash
hermes plugins                    # interactive toggle (space to check/uncheck)
hermes plugins enable <name>      # add to allow-list
hermes plugins disable <name>     # remove from allow-list + add to disabled
```

После `hermes plugins install owner/repo` тебя спрашивают `Enable 'name' now? [y/N]` — по умолчанию «нет». Пропусти запрос при скриптовой установке с помощью `--enable` или `--no-enable`.

### Что список разрешённых НЕ ограничивает

Несколько категорий плагинов обходят `plugins.enabled` — они являются частью встроенного набора Hermes и нарушили бы базовую функциональность, если бы их отключали по умолчанию:

| Тип плагина | Как он активируется вместо этого |
|---|---|
| **Встроенные платформенные плагины** (IRC, Teams и др. в `plugins/platforms/`) | Автозагружаются, поэтому каждый поставляемый канал шлюза доступен. Сам канал включается через `gateway.platforms.<name>.enabled` в `config.yaml`. |
| **Встроенные бекенды** (провайдеры генерации изображений в `plugins/image_gen/` и др.) | Автозагружаются, так что бекенд по умолчанию «просто работает». Выбор происходит через `<category>.provider` в `config.yaml` (например, `image_gen.provider: openai`). |
| **Провайдеры памяти** (`plugins/memory/`) | Все обнаружены; активен ровно один, выбранный через `memory.provider` в `config.yaml`. |
| **Движки контекста** (`plugins/context_engine/`) | Все обнаружены; один активен, выбранный через `context.engine` в `config.yaml`. |
| **Провайдеры моделей** (`plugins/model-providers/`) | Все встроенные провайдеры в `plugins/model-providers/` обнаруживаются и регистрируются при первом вызове `get_provider_profile()`. Пользователь выбирает один за раз через `--provider` или `config.yaml`. |
| **Установленные через pip плагины `backend`** | Включаются через `plugins.enabled` (как обычные плагины). |
| **Пользовательские платформы** (в `~/.hermes/plugins/platforms/`) | Включаются через `plugins.enabled` — адаптеры шлюза от третьих сторон требуют явного согласия. |

Короче: **встроенная «всегда работает» инфраструктура загружается автоматически; сторонние общие плагины включаются по желанию**. Список разрешённых `plugins.enabled` служит шлюзом именно для произвольного кода, который пользователь помещает в `~/.hermes/plugins/`.

### Миграция для существующих пользователей

Когда ты обновляешься до версии Hermes с включаемыми плагинами (схема конфигурации v21+), любые пользовательские плагины, уже установленные в `~/.hermes/plugins/` и не находившиеся в `plugins.disabled`, **автоматически попадают** в `plugins.enabled`. Твоя текущая настройка продолжит работать. Встроенные отдельные плагины НЕ попадают автоматически — даже существующим пользователям нужно явно включить их. (Встроенные платформенные и бекендовые плагины никогда не требовали такой миграции, потому что они никогда не были закрыты.)
## Доступные хуки

Плагины могут регистрировать обратные вызовы для этих событий жизненного цикла. См. **[страницу хуков событий](/user-guide/features/hooks#plugin-hooks)** для полного описания, сигнатур обратных вызовов и примеров.

| Хук | Срабатывает при |
|------|-------------------|
| [`pre_tool_call`](/user-guide/features/hooks#pre_tool_call) | Перед выполнением любого инструмента |
| [`post_tool_call`](/user-guide/features/hooks#post_tool_call) | После возврата любого инструмента |
| [`pre_llm_call`](/user-guide/features/hooks#pre_llm_call) | Один раз за ход, перед циклом LLM — может вернуть `{"context": "..."}` чтобы [вставить контекст в сообщение пользователя](/user-guide/features/hooks#pre_llm_call) |
| [`post_llm_call`](/user-guide/features/hooks#post_llm_call) | Один раз за ход, после цикла LLM (только успешные ходы) |
| [`on_session_start`](/user-guide/features/hooks#on_session_start) | Создана новая сессия (только первый ход) |
| [`on_session_end`](/user-guide/features/hooks#on_session_end) | Конец каждого вызова `run_conversation` + обработчик выхода CLI |
| [`on_session_finalize`](/user-guide/features/hooks#on_session_finalize) | CLI/шлюз завершает активную сессию (`/new`, GC, выход из CLI) |
| [`on_session_reset`](/user-guide/features/hooks#on_session_reset) | Шлюз меняет ключ сессии (`/new`, `/reset`, `/clear`, ротация в режиме простоя) |
| [`subagent_stop`](/user-guide/features/hooks#subagent_stop) | Один раз для дочернего агента после завершения `delegate_task` |
| [`pre_gateway_dispatch`](/user-guide/features/hooks#pre_gateway_dispatch) | Шлюз получил сообщение пользователя, до аутентификации и диспетчеризации. Верни `{"action": "skip" \| "rewrite" \| "allow", ...}` чтобы влиять на поток. |
## Типы плагинов

Hermes имеет четыре вида плагинов:

| Тип | Что делает | Выбор | Расположение |
|------|-------------|-----------|----------|
| **General plugins** | Добавляют инструменты, хуки, slash‑команды, CLI‑команды | Множественный выбор (включить/выключить) | `~/.hermes/plugins/` |
| **Memory providers** | Заменяют или дополняют встроенную память | Одиночный выбор (один активный) | `plugins/memory/` |
| **Context engines** | Заменяют встроенный компрессор контекста | Одиночный выбор (один активный) | `plugins/context_engine/` |
| **Model providers** | Объявляют backend вывода (inference backend) (OpenRouter, Anthropic, …) | Множественная регистрация, выбирается через `--provider` / `config.yaml` | `plugins/model-providers/` |

Memory providers и context engines являются **провайдерными плагинами** — одновременно может быть активен только один плагин каждого типа. Model providers также являются плагинами, но их может быть загружено много одновременно; пользователь выбирает один из них через `--provider` или `config.yaml`. General plugins можно включать в любой комбинации.
## Подключаемые интерфейсы — куда идти за каждым

Таблица выше показывает четыре категории плагинов, но в разделе «General plugins» `PluginContext` раскрывает несколько различных точек расширения — и Hermes также принимает расширения вне системы плагинов Python (конфигурационные бэкенды, команды, привязанные к оболочке, внешние серверы и т.д.). Используй эту таблицу, чтобы найти нужную документацию для того, что ты хочешь построить:

| Что добавить… | Как | Руководство по созданию |
|---|---|---|
| **Инструмент**, который LLM может вызвать | Плагин Python — `ctx.register_tool()` | [Build a Hermes Plugin](/guides/build-a-hermes-plugin) · [Adding Tools](/developer-guide/adding-tools) |
| **Хук жизненного цикла** (pre/post LLM, начало/окончание сессии, фильтр инструмента) | Плагин Python — `ctx.register_hook()` | [Hooks reference](/user-guide/features/hooks) · [Build a Hermes Plugin](/guides/build-a-hermes-plugin) |
| **Slash‑команда** для CLI / шлюза | Плагин Python — `ctx.register_command()` | [Build a Hermes Plugin](/guides/build-a-hermes-plugin) · [Extending the CLI](/developer-guide/extending-the-cli) |
| **Подкоманда** для `hermes <thing>` | Плагин Python — `ctx.register_cli_command()` | [Extending the CLI](/developer-guide/extending-the-cli) |
| Скомпонованный **skill**, который поставляется с твоим плагином | Плагин Python — `ctx.register_skill()` | [Creating Skills](/developer-guide/creating-skills) |
| **Inference backend** (провайдер LLM: OpenAI‑compat, Codex, Anthropic‑Messages, Bedrock) | Плагин провайдера — `register_provider(ProviderProfile(...))` в `plugins/model-providers/<name>/` | **[Model Provider Plugins](/developer-guide/model-provider-plugin)** · [Adding Providers](/developer-guide/adding-providers) |
| **Канал шлюза** (Discord / Telegram / IRC / Teams и т.д.) | Плагин платформы — `ctx.register_platform()` в `plugins/platforms/<name>/` | [Adding Platform Adapters](/developer-guide/adding-platform-adapters) |
| **Бэкенд памяти** (Honcho, Mem0, Supermemory, …) | Плагин памяти — наследуй `MemoryProvider` в `plugins/memory/<name>/` | [Memory Provider Plugins](/developer-guide/memory-provider-plugin) |
| **Стратегия сжатия контекста** | Плагин движка контекста — `ctx.register_context_engine()` | [Context Engine Plugins](/developer-guide/context-engine-plugin) |
| **Бэкенд генерации изображений** (DALL·E, SDXL, …) | Плагин бэкенда — `ctx.register_image_gen_provider()` | [Image Generation Provider Plugins](/developer-guide/image-gen-provider-plugin) |
| **Бэкенд генерации видео** (Veo, Kling, Pixverse, Grok‑Imagine, Runway, …) | Плагин бэкенда — `ctx.register_video_gen_provider()` | [Video Generation Provider Plugins](/developer-guide/video-gen-provider-plugin) |
| **Бэкенд TTS** (любой CLI — Piper, VoxCPM, Kokoro, xtts, скрипты клонирования голоса, …) | Управляемый конфигурацией (рекомендовано) — объявить в `tts.providers.<name>` с `type: command` в `config.yaml`. **Или** плагин Python — `ctx.register_tts_provider()` для Python‑SDK / потоковых движков, которым нужен более сложный шаблон. | [TTS Setup](/user-guide/features/tts#custom-command-providers) · [Python plugin guide](/user-guide/features/tts#python-plugin-providers) |
| **Бэкенд STT** (любой CLI — whisper.cpp, пользовательский бинарный whisper, локальный ASR CLI) | Управляемый конфигурацией (рекомендовано) — объявить в `stt.providers.<name>` с `type: command` в `config.yaml`, либо установить `HERMES_LOCAL_STT_COMMAND` для устаревшего однокомандного обхода. **Или** плагин Python — `ctx.register_transcription_provider()` для движков Python‑SDK (OpenRouter, SenseAudio, Gemini‑STT и т.д.). | [STT Setup](/user-guide/features/tts#stt-custom-command-providers) · [Python plugin guide](/user-guide/features/tts#python-plugin-providers-stt) |
| **Внешние инструменты через MCP** (файловая система, GitHub, Linear, Notion, любой сервер MCP) | Управляемый конфигурацией — объявить `mcp_servers.<name>` с `command:` / `url:` в `config.yaml`. Hermes автоматически обнаруживает инструменты сервера и регистрирует их вместе со встроенными. | [MCP](/user-guide/features/mcp) |
| **Дополнительные источники skill** (пользовательские репозитории GitHub, закрытые индексы skill) | CLI — `hermes skills tap add <repo>` | [Skills Hub](/user-guide/features/skills#skills-hub) · [Publishing a custom tap](/user-guide/features/skills#publishing-a-custom-skill-tap) |
| **Хуки событий шлюза** (срабатывают на `gateway:startup`, `session:start`, `agent:end`, `command:*`) | Помести `HOOK.yaml` + `handler.py` в `~/.hermes/hooks/<name>/` | [Event Hooks](/user-guide/features/hooks#gateway-event-hooks) |
| **Оболочечные хуки** (выполнять команду оболочки при событиях — уведомления, журналы аудита, настольные оповещения) | Управляемый конфигурацией — объявить в `hooks:` в `config.yaml` | [Shell Hooks](/user-guide/features/hooks#shell-hooks) |

:::note
Не всё является плагином Python. Некоторые точки расширения намеренно используют **управляемые конфигурацией команды оболочки** (TTS, STT, оболочечные хуки), так что любой уже существующий CLI становится плагином без написания кода на Python. Другие — **внешние серверы** (MCP), к которым агент подключается и автоматически регистрирует инструменты. А некоторые — **директории «подключи‑и‑используй»** (хуки шлюза) со своим форматом манифеста. Выбирай подходящую точку интеграции, соответствующую твоему случаю использования; руководства в таблице выше охватывают заполнители, обнаружение и примеры.
:::
## Декларативные плагины NixOS

В NixOS плагины можно установить декларативно через параметры модуля — без необходимости выполнять `hermes plugins install`. Смотри **[Руководство по настройке Nix](/getting-started/nix-setup#plugins)** для полного описания.

```nix
services.hermes-agent = {
  # Directory plugin (source tree with plugin.yaml)
  extraPlugins = [ (pkgs.fetchFromGitHub { ... }) ];
  # Entry-point plugin (pip package)
  extraPythonPackages = [ (pkgs.python312Packages.buildPythonPackage { ... }) ];
  # Enable in config
  settings.plugins.enabled = [ "my-plugin" ];
};
```

Декларативные плагины создаются как символические ссылки с префиксом `nix-managed-` — они сосуществуют с установленными вручную плагинами и автоматически удаляются при удалении из конфигурации Nix.
## Управление плагинами

```bash
hermes plugins                                       # unified interactive UI
hermes plugins list                                  # table: enabled / disabled / not enabled
hermes plugins install user/repo                     # install from Git, then prompt Enable? [y/N]
hermes plugins install user/repo --enable            # install AND enable (no prompt)
hermes plugins install user/repo --no-enable         # install but leave disabled (no prompt)
hermes plugins update my-plugin                      # pull latest
hermes plugins remove my-plugin                      # uninstall
hermes plugins enable my-plugin                      # add to allow-list (flat plugin)
hermes plugins enable observability/langfuse         # add to allow-list (sub-category plugin)
hermes plugins disable my-plugin                     # remove from allow-list + add to disabled
```

Для плагинов, находящихся в подкаталоге (например, `plugins/observability/langfuse/`, `plugins/image_gen/openai/`), используй полный ключ `<category>/<plugin>` — это именно то, что `hermes plugins list` отображает в колонке **Name**.

### Интерактивный UI

Запуск `hermes plugins` без аргументов открывает составной интерактивный экран:

```
Plugins
  ↑↓ navigate  SPACE toggle  ENTER configure/confirm  ESC done

  General Plugins
 → [✓] my-tool-plugin — Custom search tool
   [ ] webhook-notifier — Event hooks
   [ ] disk-cleanup — Auto-cleanup of ephemeral files [bundled]
   [ ] observability/langfuse — Trace turns / LLM calls / tools to Langfuse [bundled]

  Provider Plugins
     Memory Provider          ▸ honcho
     Context Engine           ▸ compressor
```

- **Раздел General Plugins** — флажки, переключаются клавишей **SPACE**. Отмечено = в `plugins.enabled`, не отмечено = в `plugins.disabled` (явно отключено).
- **Раздел Provider Plugins** — показывает текущий выбор. Нажми **ENTER**, чтобы перейти к радиопереключателю, где выбирается один активный provider.
- Встроенные плагины отображаются в том же списке с тегом `[bundled]`.

Выбор provider‑плагинов сохраняется в `config.yaml`:

```yaml
memory:
  provider: "honcho"      # empty string = built-in only

context:
  engine: "compressor"    # default built-in compressor
```

### Включённые, отключённые и не включённые

Плагины могут находиться в одном из трёх состояний:

| Состояние | Значение | В `plugins.enabled`? | В `plugins.disabled`? |
|---|---|---|---|
| `enabled` | Загружается в следующей сессии | Да | Нет |
| `disabled` | Явно отключён — не загрузится, даже если также присутствует в `enabled` | (не имеет значения) | Да |
| `not enabled` | Обнаружен, но не выбран | Нет | Нет |

По умолчанию для только что установленного или встроенного плагина состояние — `not enabled`. `hermes plugins list` показывает все три состояния, чтобы ты мог понять, что было явно отключено, а что просто ждёт включения.

В запущенной сессии команда `/plugins` показывает, какие плагины сейчас загружены.
## Внедрение сообщений

Плагины могут внедрять сообщения в активный диалог, используя `ctx.inject_message()`:

```python
ctx.inject_message("New data arrived from the webhook", role="user")
```

**Подпись:** `ctx.inject_message(content: str, role: str = "user") -> bool`

Как это работает:

- Если агент **в режиме ожидания** (ожидает ввода от пользователя), сообщение ставится в очередь как следующий ввод и начинается новый ход.
- Если агент **в середине хода** (активно работает), сообщение прерывает текущую операцию — то же самое, что пользователь вводит новое сообщение и нажимает Enter.
- Для ролей, отличных от `"user"`, к содержимому добавляется префикс `[role]` (например, `[system] …`).
- Возвращает `True`, если сообщение успешно поставлено в очередь, и `False`, если ссылка на CLI недоступна (например, в режиме шлюза).

Это позволяет плагинам, таким как просмотрщики удалённого управления, мосты обмена сообщениями или получатели веб‑хуков, подавать сообщения в диалог из внешних источников.

:::note
`inject_message` доступен только в режиме CLI. В режиме шлюза ссылка на CLI отсутствует, и метод возвращает `False`.
:::

См. **[полное руководство](/guides/build-a-hermes-plugin)** для контрактов обработчиков, формата схем, поведения хуков, обработки ошибок и типичных ошибок.