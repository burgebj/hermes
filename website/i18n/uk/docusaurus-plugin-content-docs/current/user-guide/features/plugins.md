---
sidebar_position: 11
sidebar_label: "Plugins"
title: "Плагіни"
description: "Розширити Hermes за допомогою власних інструментів, хуків та інтеграцій через систему плагінів"
---

# Плагіни

Hermes має систему плагінів для додавання власних інструментів, хуків та інтеграцій без зміни коду ядра.

Якщо ти хочеш створити власний інструмент для себе, своєї команди або одного проєкту,
це зазвичай правильний шлях. Сторінка посібника розробника
[Adding Tools](/developer-guide/adding-tools) призначена для вбудованих інструментів ядра Hermes, які розташовані в `tools/` та `toolsets.py`.

**→ [Build a Hermes Plugin](/guides/build-a-hermes-plugin)** — покроковий посібник з повним робочим прикладом.
## Швидкий огляд

Скинь каталог у `~/.hermes/plugins/` з `plugin.yaml` та Python‑кодом:

```
~/.hermes/plugins/my-plugin/
├── plugin.yaml      # manifest
├── __init__.py      # register() — wires schemas to handlers
├── schemas.py       # tool schemas (what the LLM sees)
└── tools.py         # tool handlers (what runs when called)
```

Запусти Hermes — твої інструменти з’являться поруч із вбудованими. Модель може викликати їх одразу.

### Мінімальний робочий приклад

Ось повний плагін, який додає інструмент `hello_world` і записує кожен виклик інструмента через хук.

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

Скинь обидва файли у `~/.hermes/plugins/hello‑world/`, перезапусти Hermes, і модель одразу зможе викликати `hello_world`. Хук виводить запис у журнал після кожного виклику інструмента.

Плагіни, розташовані у `./.hermes/plugins/`, вимкнені за замовчуванням. Увімкни їх лише для довірених репозиторіїв, встановивши `HERMES_ENABLE_PROJECT_PLUGINS=true` перед запуском Hermes.
## Які можливості мають плагіни

Кожен API `ctx.*`, наведений нижче, доступний всередині функції `register(ctx)` плагіна.

| Можливість | Як |
|-----------|-----|
| Додавати інструменти | `ctx.register_tool(name=..., toolset=..., schema=..., handler=...)` |
| Додавати хуки | `ctx.register_hook("post_tool_call", callback)` |
| Додавати slash‑команди | `ctx.register_command(name, handler, description)` — додає `/name` у CLI та сесіях шлюзу |
| Викликати інструменти з команд | `ctx.dispatch_tool(name, args)` — викликає зареєстрований інструмент з автоматичним підключенням контексту батьківського агента |
| Додавати CLI‑команди | `ctx.register_cli_command(name, help, setup_fn, handler_fn)` — додає `hermes <plugin> <subcommand>` |
| Вставляти повідомлення | `ctx.inject_message(content, role="user")` — див. [Injecting Messages](#injecting-messages) |
| Поставляти файли даних | `Path(__file__).parent / "data" / "file.yaml"` |
| Об’єднувати навички | `ctx.register_skill(name, path)` — простір імен `plugin:skill`, завантажується через `skill_view("plugin:skill")` |
| Вимагати змінні оточення | `requires_env: [API_KEY]` у `plugin.yaml` — запитується під час `hermes plugins install` |
| Поширювати через pip | `[project.entry-points."hermes_agent.plugins"]` |
| Реєструвати платформу шлюзу (Discord, Telegram, IRC, …) | `ctx.register_platform(name, label, adapter_factory, check_fn, ...)` — див. [Adding Platform Adapters](/developer-guide/adding-platform-adapters) |
| Реєструвати бекенд генерації зображень | `ctx.register_image_gen_provider(provider)` — див. [Image Generation Provider Plugins](/developer-guide/image-gen-provider-plugin) |
| Реєструвати бекенд генерації відео | `ctx.register_video_gen_provider(provider)` — див. [Video Generation Provider Plugins](/developer-guide/video-gen-provider-plugin) |
| Реєструвати движок стиснення контексту | `ctx.register_context_engine(engine)` — див. [Context Engine Plugins](/developer-guide/context-engine-plugin) |
| Реєструвати бекенд пам’яті | Наслідуй `MemoryProvider` у `plugins/memory/<name>/__init__.py` — див. [Memory Provider Plugins](/developer-guide/memory-provider-plugin) (використовує окрему систему виявлення) |
| Виконувати виклик LLM, що належить хосту | `ctx.llm.complete(...)` / `ctx.llm.complete_structured(...)` — використай активну модель користувача + автентифікацію для одноразового завершення з необов’язковою валідацією JSON‑схеми. Див. [Plugin LLM Access](/developer-guide/plugin-llm-access) |
| Реєструвати бекенд інференсу (LLM‑провайдер) | `register_provider(ProviderProfile(...))` у `plugins/model-providers/<name>/__init__.py` — див. [Model Provider Plugins](/developer-guide/model-provider-plugin) (використовує окрему систему виявлення) |
## Виявлення плагінів

| Джерело | Шлях | Випадок використання |
|--------|------|-----------------------|
| Bundled | `<repo>/plugins/` | Поставляється з Hermes — дивись [Built-in Plugins](/user-guide/features/built-in-plugins) |
| User | `~/.hermes/plugins/` | Особисті плагіни |
| Project | `.hermes/plugins/` | Плагіни, специфічні для проєкту (вимагає `HERMES_ENABLE_PROJECT_PLUGINS=true`) |
| pip | `hermes_agent.plugins` entry_points | Пакети, що розповсюджуються |
| Nix | `services.hermes-agent.extraPlugins` / `extraPythonPackages` | Декларативні установки NixOS — дивись [Nix Setup](/getting-started/nix-setup#plugins) |

Пізніші джерела перекривають ранні при конфлікті імен, тому плагін користувача з тим же ім’ям, що й вбудований, замінює його.

### Підкатегорії плагінів

У кожному джерелі Hermes також розпізнає підкаталоги, які спрямовують плагіни до спеціалізованих систем виявлення:

| Підкаталог | Що містить | Система виявлення |
|---|---|---|
| `plugins/` (корінь) | Загальні плагіни — інструменти, хуки, slash‑команди, CLI‑команди, вбудовані skills | `PluginManager` (kind: `standalone` або `backend`) |
| `plugins/platforms/<name>/` | Адаптери каналів шлюзу (`ctx.register_platform()`) | `PluginManager` (kind: `platform`, на один рівень глибше) |
| `plugins/image_gen/<name>/` | Бекенди генерації зображень (`ctx.register_image_gen_provider()`) | `PluginManager` (kind: `backend`, на один рівень глибше) |
| `plugins/memory/<name>/` | Провайдери пам’яті (підклас `MemoryProvider`) | **Власний завантажувач** у `plugins/memory/__init__.py` (kind: `exclusive` — один активний одночасно) |
| `plugins/context_engine/<name>/` | Двигуни стиснення контексту (`ctx.register_context_engine()`) | **Власний завантажувач** у `plugins/context_engine/__init__.py` (один активний одночасно) |
| `plugins/model-providers/<name>/` | Профілі провайдерів LLM (`register_provider(ProviderProfile(...))`) | **Власний завантажувач** у `providers/__init__.py` (лениво сканується при першому виклику `get_provider_profile()`) |

Плагіни користувача у `~/.hermes/plugins/model-providers/<name>/` та `~/.hermes/plugins/memory/<name>/` перекривають вбудовані плагіни з тим же ім’ям — останній запис виграє у `register_provider()` / `register_memory_provider()`. Додай каталог, і він замінить вбудований без будь‑яких змін у репозиторії.

Підкатегорійні плагіни з’являються у `hermes plugins list` та інтерактивному UI `hermes plugins` під їх **ключем, отриманим з шляху** — напр., `observability/langfuse`, `image_gen/openai`, `platforms/teams`. Цей ключ (а не чистий `name:` у маніфесті) є значенням, яке передається у `hermes plugins enable …` / `disable …` і рядком, що додається до `plugins.enabled` у `config.yaml`.
## Плагіни підключаються за бажанням (з кількома винятками)

**Загальні плагіни та встановлені користувачем бекенди вимкнені за замовчуванням** — система виявлення їх знаходить (тому вони з’являються у `hermes plugins` та `/plugins`), але нічого з хуками чи інструментами не завантажується, доки ти не додаси назву плагіна до `plugins.enabled` у `~/.hermes/config.yaml`. Це запобігає виконанню стороннього коду без твоєї явної згоди.

```yaml
plugins:
  enabled:
    - my-tool-plugin
    - disk-cleanup
  disabled:       # optional deny-list — always wins if a name appears in both
    - noisy-plugin
```

Три способи змінити стан:

```bash
hermes plugins                    # interactive toggle (space to check/uncheck)
hermes plugins enable <name>      # add to allow-list
hermes plugins disable <name>     # remove from allow-list + add to disabled
```

Після `hermes plugins install owner/repo` тебе запитують `Enable 'name' now? [y/N]` — за замовчуванням «ні». Пропусти запит під час скриптових інсталяцій за допомогою `--enable` або `--no-enable`.

### Що не контролює білий список

Кілька категорій плагінів обходять `plugins.enabled` — вони є частиною вбудованого функціоналу Hermes і порушили б базову роботу, якби їх вимкнути за замовчуванням:

| Тип плагіна | Як він активується замість цього |
|---|---|
| **Вбудовані плагіни платформ** (IRC, Teams тощо у `plugins/platforms/`) | Автозавантажуються, тому кожен постачений канал шлюзу доступний. Сам канал вмикається через `gateway.platforms.<name>.enabled` у `config.yaml`. |
| **Вбудовані бекенди** (провайдери генерації зображень у `plugins/image_gen/` тощо) | Автозавантажуються, тому бекенд за замовчуванням «просто працює». Вибір здійснюється через `<category>.provider` у `config.yaml` (наприклад, `image_gen.provider: openai`). |
| **Провайдери пам'яті** (`plugins/memory/`) | Всі виявлені; активний лише один, обирається за `memory.provider` у `config.yaml`. |
| **Контекстні рушії** (`plugins/context_engine/`) | Всі виявлені; активний лише один, обирається за `context.engine` у `config.yaml`. |
| **Провайдери моделей** (`plugins/model-providers/`) | Всі вбудовані провайдери у `plugins/model-providers/` виявляються та реєструються під час першого виклику `get_provider_profile()`. Користувач обирає один за раз через `--provider` або `config.yaml`. |
| **Плагіни `backend`, встановлені через pip** | Підключаються за бажанням через `plugins.enabled` (те ж саме, що й загальні плагіни). |
| **Платформи, встановлені користувачем** (у `~/.hermes/plugins/platforms/`) | Підключаються за бажанням через `plugins.enabled` — сторонні адаптери шлюзу потребують явної згоди. |

Коротко: **вбудована «завжди‑працююча» інфраструктура завантажується автоматично; загальні сторонні плагіни підключаються за бажанням**. Білий список `plugins.enabled` саме контролює довільний код, який користувач розміщує у `~/.hermes/plugins/`.

### Міграція для існуючих користувачів

Коли ти оновлюєшся до версії Hermes з opt‑in плагінами (схема конфігурації v21+), будь‑які користувацькі плагіни, вже встановлені у `~/.hermes/plugins/`, які ще не були в `plugins.disabled`, **автоматично додаються** до `plugins.enabled`. Твоя існуюча настройка продовжує працювати. Вбудовані окремі плагіни НЕ додаються автоматично — навіть існуючі користувачі повинні явно їх підключити. (Вбудовані плагіни платформ/бекендів ніколи не потребували такої «додаткової» активації, бо вони не були піддані обмеженню.)
## Доступні хуки

Плагіни можуть реєструвати колбеки для цих подій життєвого циклу. Дивись **[Сторінка Event Hooks](/user-guide/features/hooks#plugin-hooks)** для повних деталей, сигнатур колбеків та прикладів.

| Hook | Спрацьовує коли |
|------|-----------------|
| [`pre_tool_call`](/user-guide/features/hooks#pre_tool_call) | Перед виконанням будь‑якого інструмента |
| [`post_tool_call`](/user-guide/features/hooks#post_tool_call) | Після повернення результату будь‑якого інструмента |
| [`pre_llm_call`](/user-guide/features/hooks#pre_llm_call) | Один раз за хід, перед циклом LLM — може повернути `{"context": "..."}` щоб [вставити контекст у повідомлення користувача](/user-guide/features/hooks#pre_llm_call) |
| [`post_llm_call`](/user-guide/features/hooks#post_llm_call) | Один раз за хід, після циклу LLM (лише успішні ходи) |
| [`on_session_start`](/user-guide/features/hooks#on_session_start) | Створено нову сесію (лише перший хід) |
| [`on_session_end`](/user-guide/features/hooks#on_session_end) | Кінець кожного виклику `run_conversation` + обробник виходу CLI |
| [`on_session_finalize`](/user-guide/features/hooks#on_session_finalize) | CLI/шлюз завершує активну сесію (`/new`, GC, вихід CLI) |
| [`on_session_reset`](/user-guide/features/hooks#on_session_reset) | Шлюз замінює ключ сесії на новий (`/new`, `/reset`, `/clear`, ротація під час простою) |
| [`subagent_stop`](/user-guide/features/hooks#subagent_stop) | Один раз за дочірній процес після завершення `delegate_task` |
| [`pre_gateway_dispatch`](/user-guide/features/hooks#pre_gateway_dispatch) | Шлюз отримав повідомлення користувача, перед автентифікацією та диспетчуванням. Поверни `{"action": "skip" \| "rewrite" \| "allow", ...}` щоб вплинути на потік. |
## Типи плагінів

Hermes має чотири види плагінів:

| Тип | Що робить | Вибір | Розташування |
|------|-------------|-----------|----------|
| **Загальні плагіни** | Додає інструменти, хуки, slash‑команди, CLI‑команди | Мультивибір (увімкнути/вимкнути) | `~/.hermes/plugins/` |
| **Постачальники пам’яті** | Замінює або доповнює вбудовану пам’ять | Одинарний вибір (один активний) | `plugins/memory/` |
| **Контекстні рушії** | Замінює вбудований компресор контексту | Одинарний вибір (один активний) | `plugins/context_engine/` |
| **Постачальники моделей** | Оголошує бекенд інференсу (OpenRouter, Anthropic, …) | Мульти‑реєстрація, обираються за допомогою `--provider` / `config.yaml` | `plugins/model-providers/` |

Постачальники пам’яті та контекстні рушії є **плагінами‑постачальниками** — одночасно може бути активний лише один плагін кожного типу. Постачальники моделей також є плагінами, але їх можна завантажувати одночасно; користувач обирає один за раз за допомогою `--provider` або `config.yaml`. Загальні плагіни можна вмикати у будь‑якій комбінації.
## Pluggable interfaces — where to go for each

The table above shows the four plugin categories, but within "General plugins" the `PluginContext` exposes several distinct extension points — and Hermes also accepts extensions outside the Python plugin system (config-driven backends, shell-hooked commands, external servers, etc.). Use this table to find the right doc for what you want to build:

| Want to add… | How | Authoring guide |
|---|---|---|
| **інструмент**, який LLM може викликати | Python plugin — `ctx.register_tool()` | [Build a Hermes Plugin](/guides/build-a-hermes-plugin) · [Adding Tools](/developer-guide/adding-tools) |
| **хук життєвого циклу** (pre/post LLM, session start/end, tool filter) | Python plugin — `ctx.register_hook()` | [Hooks reference](/user-guide/features/hooks) · [Build a Hermes Plugin](/guides/build-a-hermes-plugin) |
| **slash‑команда** для CLI / gateway | Python plugin — `ctx.register_command()` | [Build a Hermes Plugin](/guides/build-a-hermes-plugin) · [Extending the CLI](/developer-guide/extending-the-cli) |
| **підкоманда** для `hermes <thing>` | Python plugin — `ctx.register_cli_command()` | [Extending the CLI](/developer-guide/extending-the-cli) |
| **skill**, що постачається разом з плагіном | Python plugin — `ctx.register_skill()` | [Creating Skills](/developer-guide/creating-skills) |
| **inference backend** (LLM provider: OpenAI-compat, Codex, Anthropic-Messages, Bedrock) | Provider plugin — `register_provider(ProviderProfile(...))` in `plugins/model-providers/<name>/` | **[Model Provider Plugins](/developer-guide/model-provider-plugin)** · [Adding Providers](/developer-guide/adding-providers) |
| **gateway channel** (Discord / Telegram / IRC / Teams / тощо) | Platform plugin — `ctx.register_platform()` in `plugins/platforms/<name>/` | [Adding Platform Adapters](/developer-guide/adding-platform-adapters) |
| **memory backend** (Honcho, Mem0, Supermemory, …) | Memory plugin — subclass `MemoryProvider` in `plugins/memory/<name>/` | [Memory Provider Plugins](/developer-guide/memory-provider-plugin) |
| **стратегія стиснення контексту** | Context-engine plugin — `ctx.register_context_engine()` | [Context Engine Plugins](/developer-guide/context-engine-plugin) |
| **backend генерації зображень** (DALL·E, SDXL, …) | Backend plugin — `ctx.register_image_gen_provider()` | [Image Generation Provider Plugins](/developer-guide/image-gen-provider-plugin) |
| **backend генерації відео** (Veo, Kling, Pixverse, Grok-Imagine, Runway, …) | Backend plugin — `ctx.register_video_gen_provider()` | [Video Generation Provider Plugins](/developer-guide/video-gen-provider-plugin) |
| **TTS backend** (any CLI — Piper, VoxCPM, Kokoro, xtts, voice-cloning scripts, …) | Config‑driven (recommended) — declare under `tts.providers.<name>` with `type: command` in `config.yaml`. OR Python backend plugin — `ctx.register_tts_provider()` for Python‑SDK / streaming engines that need more than a shell template. | [TTS Setup](/user-guide/features/tts#custom-command-providers) · [Python plugin guide](/user-guide/features/tts#python-plugin-providers) |
| **STT backend** (any CLI — whisper.cpp, custom whisper binary, local ASR CLI) | Config‑driven (recommended) — declare under `stt.providers.<name>` with `type: command` in `config.yaml`, or set `HERMES_LOCAL_STT_COMMAND` for the legacy single‑command escape hatch. OR Python backend plugin — `ctx.register_transcription_provider()` for Python‑SDK engines (OpenRouter, SenseAudio, Gemini‑STT, etc.). | [STT Setup](/user-guide/features/tts#stt-custom-command-providers) · [Python plugin guide](/user-guide/features/tts#python-plugin-providers-stt) |
| **external tools via MCP** (filesystem, GitHub, Linear, Notion, any MCP server) | Config‑driven — declare `mcp_servers.<name>` with `command:` / `url:` in `config.yaml`. Hermes auto‑discovers the server's tools and registers them alongside built‑ins. | [MCP](/user-guide/features/mcp) |
| **additional skill sources** (custom GitHub repos, private skill indexes) | CLI — `hermes skills tap add <repo>` | [Skills Hub](/user-guide/features/skills#skills-hub) · [Publishing a custom tap](/user-guide/features/skills#publishing-a-custom-skill-tap) |
| **gateway event hooks** (fire on `gateway:startup`, `session:start`, `agent:end`, `command:*`) | Drop `HOOK.yaml` + `handler.py` into `~/.hermes/hooks/<name>/` | [Event Hooks](/user-guide/features/hooks#gateway-event-hooks) |
| **shell hooks** (run a shell command on events — notifications, audit logs, desktop alerts) | Config‑driven — declare under `hooks:` in `config.yaml` | [Shell Hooks](/user-guide/features/hooks#shell-hooks) |

:::note
Не все розширення — це Python‑плагіни. Деякі точки розширення навмисно використовують **config‑driven shell‑команди** (TTS, STT, shell hooks), тож будь‑яка CLI, яку ти вже маєш, стає плагіном без написання коду Python. Інші — це **зовнішні сервери** (MCP), до яких агент підключається і автоматично реєструє інструменти. А ще є **директорії‑вставки** (gateway hooks) зі своїм форматом маніфесту. Обери правильну точку інтеграції, що відповідає твоєму випадку; у посібниках у таблиці наведено плейсхолдери, процеси виявлення та приклади.
:::
## Декларативні плагіни NixOS

У NixOS плагіни можна встановлювати декларативно за допомогою параметрів модуля — без необхідності запускати `hermes plugins install`. Дивись **[Посібник з налаштування Nix](/getting-started/nix-setup#plugins)** для детальної інформації.

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

Декларативні плагіни створюються як символічні посилання з префіксом `nix-managed-` — вони співіснують із вручну встановленими плагінами та автоматично очищуються при видаленні з конфігурації Nix.
## Керування плагінами

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

Для плагінів, розташованих у підкаталозі (наприклад `plugins/observability/langfuse/`, `plugins/image_gen/openai/`), використовуйте повний ключ `<category>/<plugin>` — саме так `hermes plugins list` показує його у колонці **Name**.

### Інтерактивний інтерфейс

Запуск `hermes plugins` без аргументів відкриває складний інтерактивний екран:

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

- **Розділ General Plugins** — чекбокси, перемикаються клавішею **SPACE**. Позначені = у `plugins.enabled`, зняті = у `plugins.disabled` (явно вимкнено).
- **Розділ Provider Plugins** — показує поточний вибір. Натисни **ENTER**, щоб перейти до радіо‑вибору, де можна обрати один активний провайдер.
- Вбудовані плагіни відображаються в тому ж списку з міткою `[bundled]`.

Вибір провайдер‑плагінів зберігається у `config.yaml`:

```yaml
memory:
  provider: "honcho"      # empty string = built-in only

context:
  engine: "compressor"    # default built-in compressor
```

### Увімкнено vs. вимкнено vs. не увімкнено

Плагіни можуть перебувати в одному з трьох станів:

| Стан | Значення | У `plugins.enabled`? | У `plugins.disabled`? |
|---|---|---|---|
| `enabled` | Завантажується у наступній сесії | Так | Ні |
| `disabled` | Явно вимкнено — не завантажиться, навіть якщо також у `enabled` | (не має значення) | Так |
| `not enabled` | Виявлено, але не обрано | Ні | Ні |

Типовим для нововстановленого або вбудованого плагіна є стан `not enabled`. `hermes plugins list` показує всі три окремих стани, щоб ти міг бачити, що саме вимкнено явно, а що лише чекає на увімкнення.

У запущеній сесії команда `/plugins` показує, які плагіни наразі завантажені.
## Вставка повідомлень

Плагіни можуть вставляти повідомлення в активну розмову за допомогою `ctx.inject_message()`:

```python
ctx.inject_message("New data arrived from the webhook", role="user")
```

**Сигнатура:** `ctx.inject_message(content: str, role: str = "user") -> bool`

Як це працює:

- Якщо агент **неактивний** (чекає вводу користувача), повідомлення ставиться в чергу як наступний ввід і ініціює новий хід.
- Якщо агент **в середині ходу** (активно працює), повідомлення перериває поточну операцію — так само, як користувач вводить нове повідомлення і натискає Enter.
- Для ролей, відмінних від `"user"`, вміст отримує префікс `[role]` (наприклад, `[system] ...`).
- Повертає `True`, якщо повідомлення успішно поставлено в чергу, `False`, якщо немає посилання на CLI (наприклад, у режимі шлюзу).

Це дозволяє плагінам, таким як переглядачі віддаленого керування, мости обміну повідомленнями або отримувачі вебхук, надсилати повідомлення в розмову з зовнішніх джерел.

:::note
`inject_message` доступний лише в режимі CLI. У режимі шлюзу посилання на CLI немає, і метод повертає `False`.
:::

Дивись **[повний посібник](/guides/build-a-hermes-plugin)** для контрактів обробників, формату схеми, поведінки хуків, обробки помилок та типових помилок.