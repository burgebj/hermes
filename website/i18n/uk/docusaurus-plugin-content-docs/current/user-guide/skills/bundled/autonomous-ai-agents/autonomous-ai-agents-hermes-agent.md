---
title: "Налаштуй, розширюй або внеси свій внесок у Hermes Agent"
sidebar_label: "Hermes Agent"
description: "Налаштуй, розширюй або внеси свій внесок у Hermes Agent"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Hermes Agent

Налаштовуй, розширюй або роби внесок у Hermes Agent.
## Метадані навички

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/autonomous-ai-agents/hermes-agent` |
| Version | `2.1.0` |
| Author | Hermes Agent + Teknium |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `hermes`, `setup`, `configuration`, `multi-agent`, `spawning`, `cli`, `gateway`, `development` |
| Related skills | [`claude-code`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-claude-code), [`codex`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-codex), [`opencode`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-opencode) |
:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Hermes Agent

Hermes Agent — це open‑source фреймворк AI‑агентів від Nous Research, який працює у твоєму терміналі, платформах обміну повідомленнями та IDE. Він належить до тієї ж категорії, що й Claude Code (Anthropic), Codex (OpenAI) та OpenClaw — автономні агенти кодування та виконання завдань, які використовують виклик інструментів для взаємодії з твоєю системою. Hermes працює з будь‑яким провайдером LLM (OpenRouter, Anthropic, OpenAI, DeepSeek, локальні моделі та 15+ інших) і працює на Linux, macOS та WSL.

Що робить Hermes унікальним:

- **Самонавчальний агент** — Hermes навчається на досвіді, зберігаючи повторно використовувані процедури як навички. Коли він вирішує складну проблему, відкриває робочий процес або отримує виправлення, він може зберегти ці знання у вигляді документа навички, який завантажується у майбутніх сесіях. Навички накопичуються з часом, роблячи агента кращим у твоїх конкретних завданнях та середовищі.
- **Постійна пам'ять між сесіями** — пам'ятає, хто ти, твої уподобання, деталі середовища та отримані уроки. Плагін‑бекенди пам'яті (вбудовані, Honcho, Mem0 та інші) дозволяють обрати, як працює пам'ять.
- **Багатоплатформений шлюз інструментів** — той самий агент працює в Telegram, Discord, Slack, WhatsApp, Signal, Matrix, Email та 10+ інших платформах з повним доступом до інструментів, а не лише в чаті.
- **Провайдер‑агностичний** — міняй моделі та провайдерів під час робочого процесу без зміни іншого коду. Пули облікових даних автоматично чергуються між кількома API‑ключами.
- **Профілі** — запускай кілька незалежних екземплярів Hermes з ізольованими конфігураціями, сесіями, навичками та пам'яттю.
- **Розширюваний** — плагіни, MCP‑сервери, кастомні інструменти, веб‑хуки, планування cron та вся екосистема Python.

Люди використовують Hermes для розробки ПЗ, досліджень, системного адміністрування, аналізу даних, створення контенту, домашньої автоматизації та будь‑яких інших задач, які виграють від AI‑агента з постійним контекстом та повним доступом до системи.

**Ця навичка допоможе тобі ефективно працювати з Hermes Agent** — налаштування, конфігурація функцій, створення додаткових екземплярів агента, усунення проблем, пошук потрібних команд і налаштувань, а також розуміння роботи системи, коли потрібно розширювати або вносити свій внесок.

**Docs:** https://hermes-agent.nousresearch.com/docs/
## Швидкий старт

```bash
# Install
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

# Interactive chat (default)
hermes

# Single query
hermes chat -q "What is the capital of France?"

# Setup wizard
hermes setup

# Change model/provider
hermes model

# Check health
hermes doctor
```

---
## Довідник CLI

### Глобальні прапорці

```
hermes [flags] [command]

  --version, -V             Show version
  --resume, -r SESSION      Resume session by ID or title
  --continue, -c [NAME]     Resume by name, or most recent session
  --worktree, -w            Isolated git worktree mode (parallel agents)
  --skills, -s SKILL        Preload skills (comma-separate or repeat)
  --profile, -p NAME        Use a named profile
  --yolo                    Skip dangerous command approval
  --pass-session-id         Include session ID in system prompt
```

Відсутність підкоманди за замовчуванням — `chat`.

### Чат

```
hermes chat [flags]
  -q, --query TEXT          Single query, non-interactive
  -m, --model MODEL         Model (e.g. anthropic/claude-sonnet-4)
  -t, --toolsets LIST       Comma-separated toolsets
  --provider PROVIDER       Force provider (openrouter, anthropic, nous, etc.)
  -v, --verbose             Verbose output
  -Q, --quiet               Suppress banner, spinner, tool previews
  --checkpoints             Enable filesystem checkpoints (/rollback)
  --source TAG              Session source tag (default: cli)
```

### Конфігурація

```
hermes setup [section]      Interactive wizard (model|terminal|gateway|tools|agent)
hermes model                Interactive model/provider picker
hermes config               View current config
hermes config edit          Open config.yaml in $EDITOR
hermes config set KEY VAL   Set a config value
hermes config path          Print config.yaml path
hermes config env-path      Print .env path
hermes config check         Check for missing/outdated config
hermes config migrate       Update config with new options
hermes auth                 Interactive credential manager
hermes auth add PROVIDER    Add OAuth or API-key credential (e.g. nous, openai-codex, qwen-oauth)
hermes auth list            List stored credentials
hermes auth remove PROVIDER Remove a stored credential
hermes doctor [--fix]       Check dependencies and config
hermes status [--all]       Show component status
```

### Інструменти та Skills

```
hermes tools                Interactive tool enable/disable (curses UI)
hermes tools list           Show all tools and status
hermes tools enable NAME    Enable a toolset
hermes tools disable NAME   Disable a toolset

hermes skills list          List installed skills
hermes skills search QUERY  Search the skills hub
hermes skills install ID    Install a skill (ID can be a hub identifier OR a direct https://…/SKILL.md URL; pass --name to override when frontmatter has no name)
hermes skills inspect ID    Preview without installing
hermes skills config        Enable/disable skills per platform
hermes skills check         Check for updates
hermes skills update        Update outdated skills
hermes skills uninstall N   Remove a hub skill
hermes skills publish PATH  Publish to registry
hermes skills browse        Browse all available skills
hermes skills tap add REPO  Add a GitHub repo as skill source
```

### MCP Servers

```
hermes mcp serve            Run Hermes as an MCP server
hermes mcp add NAME         Add an MCP server (--url or --command)
hermes mcp remove NAME      Remove an MCP server
hermes mcp list             List configured servers
hermes mcp test NAME        Test connection
hermes mcp configure NAME   Toggle tool selection
```

### Шлюз (платформи обміну повідомленнями)

```
hermes gateway run          Start gateway foreground
hermes gateway install      Install as background service
hermes gateway start/stop   Control the service
hermes gateway restart      Restart the service
hermes gateway status       Check status
hermes gateway setup        Configure platforms
```

Підтримувані платформи: Telegram, Discord, Slack, WhatsApp, Signal, Email, SMS, Matrix, Mattermost, Home Assistant, DingTalk, Feishu, WeCom, BlueBubbles (iMessage), Weixin (WeChat), API Server, Webhooks. Open WebUI підключається через адаптер API Server.

Документація платформи: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/

### Сесії

```
hermes sessions list        List recent sessions
hermes sessions browse      Interactive picker
hermes sessions export OUT  Export to JSONL
hermes sessions rename ID T Rename a session
hermes sessions delete ID   Delete a session
hermes sessions prune       Clean up old sessions (--older-than N days)
hermes sessions stats       Session store statistics
```

### Cron Jobs

```
hermes cron list            List jobs (--all for disabled)
hermes cron create SCHED    Create: '30m', 'every 2h', '0 9 * * *'
hermes cron edit ID         Edit schedule, prompt, delivery
hermes cron pause/resume ID Control job state
hermes cron run ID          Trigger on next tick
hermes cron remove ID       Delete a job
hermes cron status          Scheduler status
```

### Webhooks

```
hermes webhook subscribe N  Create route at /webhooks/<name>
hermes webhook list         List subscriptions
hermes webhook remove NAME  Remove a subscription
hermes webhook test NAME    Send a test POST
```

### Профілі

```
hermes profile list         List all profiles
hermes profile create NAME  Create (--clone, --clone-all, --clone-from)
hermes profile use NAME     Set sticky default
hermes profile delete NAME  Delete a profile
hermes profile show NAME    Show details
hermes profile alias NAME   Manage wrapper scripts
hermes profile rename A B   Rename a profile
hermes profile export NAME  Export to tar.gz
hermes profile import FILE  Import from archive
```

### Пул облікових даних

```
hermes auth add             Interactive credential wizard
hermes auth list [PROVIDER] List pooled credentials
hermes auth remove P INDEX  Remove by provider + index
hermes auth reset PROVIDER  Clear exhaustion status
```

### Інше

```
hermes insights [--days N]  Usage analytics
hermes update               Update to latest version
hermes pairing list/approve/revoke  DM authorization
hermes plugins list/install/remove  Plugin management
hermes honcho setup/status  Honcho memory integration (requires honcho plugin)
hermes memory setup/status/off  Memory provider config
hermes completion bash|zsh  Shell completions
hermes acp                  ACP server (IDE integration)
hermes claw migrate         Migrate from OpenClaw
hermes uninstall            Uninstall Hermes
```

---
## Команди зі слешем (In-Session)

Набирай їх під час інтерактивної чат‑сесії. Нові команди з’являються досить часто; якщо щось нижче здається застарілим, запусти `/help` у сесії, щоб отримати офіційний список, або переглянь [довідник живих slash‑команд](https://hermes-agent.nousresearch.com/docs/reference/slash-commands). Офіційний реєстр знаходиться у `hermes_cli/commands.py` — усі споживачі (autocomplete, Telegram menu, Slack mapping, `/help`) успадковують його.

### Керування сесією
```
/new (/reset)        Fresh session
/clear               Clear screen + new session (CLI)
/retry               Resend last message
/undo                Remove last exchange
/title [name]        Name the session
/compress            Manually compress context
/stop                Kill background processes
/rollback [N]        Restore filesystem checkpoint
/snapshot [sub]      Create or restore state snapshots of Hermes config/state (CLI)
/background <prompt> Run prompt in background
/queue <prompt>      Queue for next turn
/steer <prompt>      Inject a message after the next tool call without interrupting
/agents (/tasks)     Show active agents and running tasks
/resume [name]       Resume a named session
/goal [text|sub]     Set a standing goal Hermes works on across turns until achieved
                     (subcommands: status, pause, resume, clear)
/redraw              Force a full UI repaint (CLI)
```

### Конфігурація
```
/config              Show config (CLI)
/model [name]        Show or change model
/personality [name]  Set personality
/reasoning [level]   Set reasoning (none|minimal|low|medium|high|xhigh|show|hide)
/verbose             Cycle: off → new → all → verbose
/voice [on|off|tts]  Voice mode
/yolo                Toggle approval bypass
/busy [sub]          Control what Enter does while Hermes is working (CLI)
                     (subcommands: queue, steer, interrupt, status)
/indicator [style]   Pick the TUI busy-indicator style (CLI)
                     (styles: kaomoji, emoji, unicode, ascii)
/footer [on|off]     Toggle gateway runtime-metadata footer on final replies
/skin [name]         Change theme (CLI)
/statusbar           Toggle status bar (CLI)
```

### Інструменти та skills
```
/tools               Manage tools (CLI)
/toolsets            List toolsets (CLI)
/skills              Search/install skills (CLI)
/skill <name>        Load a skill into session
/reload-skills       Re-scan ~/.hermes/skills/ for added/removed skills
/reload              Reload .env variables into the running session (CLI)
/reload-mcp          Reload MCP servers
/cron                Manage cron jobs (CLI)
/curator [sub]       Background skill maintenance (status, run, pin, archive, …)
/kanban [sub]        Multi-profile collaboration board (tasks, links, comments)
/plugins             List plugins (CLI)
```

### Шлюз
```
/approve             Approve a pending command (gateway)
/deny                Deny a pending command (gateway)
/restart             Restart gateway (gateway)
/sethome             Set current chat as home channel (gateway)
/update              Update Hermes to latest (gateway)
/topic [sub]         Enable or inspect Telegram DM topic sessions (gateway)
/platforms (/gateway) Show platform connection status (gateway)
```

### Утиліти
```
/branch (/fork)      Branch the current session
/fast                Toggle priority/fast processing
/browser             Open CDP browser connection
/history             Show conversation history (CLI)
/save                Save conversation to file (CLI)
/copy [N]            Copy the last assistant response to clipboard (CLI)
/paste               Attach clipboard image (CLI)
/image               Attach local image file (CLI)
```

### Інформація
```
/help                Show commands
/commands [page]     Browse all commands (gateway)
/usage               Token usage
/insights [days]     Usage analytics
/gquota              Show Google Gemini Code Assist quota usage (CLI)
/status              Session info (gateway)
/profile             Active profile info
/debug               Upload debug report (system info + logs) and get shareable links
```

### Вихід
```
/quit (/exit, /q)    Exit CLI
```

---
## Ключові шляхи та конфігурація

```
~/.hermes/config.yaml       Main configuration
~/.hermes/.env              API keys and secrets
$HERMES_HOME/skills/        Installed skills
~/.hermes/sessions/         Gateway routing index, request dumps, *.jsonl transcripts (and optional per-session JSON snapshots when sessions.write_json_snapshots: true)
~/.hermes/state.db          Canonical session store (SQLite + FTS5)
~/.hermes/logs/             Gateway and error logs
~/.hermes/auth.json         OAuth tokens and credential pools
~/.hermes/hermes-agent/     Source code (if git-installed)
```

Профілі використовують `~/.hermes/profiles/<name>/` з тією ж структурою.

### Розділи конфігурації

Редагуй за допомогою `hermes config edit` або `hermes config set section.key value`.

| Розділ | Параметри |
|---------|-------------|
| `model` | `default`, `provider`, `base_url`, `api_key`, `context_length` |
| `agent` | `max_turns` (90), `tool_use_enforcement` |
| `terminal` | `backend` (local/docker/ssh/modal), `cwd`, `timeout` (180) |
| `compression` | `enabled`, `threshold` (0.50), `target_ratio` (0.20) |
| `display` | `skin`, `tool_progress`, `show_reasoning`, `show_cost` |
| `stt` | `enabled`, `provider` (local/groq/openai/mistral) |
| `tts` | `provider` (edge/elevenlabs/openai/minimax/mistral/neutts) |
| `memory` | `memory_enabled`, `user_profile_enabled`, `provider` |
| `security` | `tirith_enabled`, `website_blocklist` |
| `delegation` | `model`, `provider`, `base_url`, `api_key`, `max_iterations` (50), `reasoning_effort` |
| `checkpoints` | `enabled`, `max_snapshots` (50) |

Повна довідка з конфігурації: https://hermes-agent.nousresearch.com/docs/user-guide/configuration

### Провайдери

Підтримується 20+ провайдерів. Встановлюються через `hermes model` або `hermes setup`.

| Провайдер | Авторизація | Змінна середовища |
|----------|------|-------------|
| OpenRouter | API key | `OPENROUTER_API_KEY` |
| Anthropic | API key | `ANTHROPIC_API_KEY` |
| Nous Portal | OAuth | `hermes auth` |
| OpenAI Codex | OAuth | `hermes auth` |
| GitHub Copilot | Token | `COPILOT_GITHUB_TOKEN` |
| Google Gemini | API key | `GOOGLE_API_KEY` or `GEMINI_API_KEY` |
| DeepSeek | API key | `DEEPSEEK_API_KEY` |
| xAI / Grok | API key | `XAI_API_KEY` |
| Hugging Face | Token | `HF_TOKEN` |
| Z.AI / GLM | API key | `GLM_API_KEY` |
| MiniMax | API key | `MINIMAX_API_KEY` |
| MiniMax CN | API key | `MINIMAX_CN_API_KEY` |
| Kimi / Moonshot | API key | `KIMI_API_KEY` |
| Alibaba / DashScope | API key | `DASHSCOPE_API_KEY` |
| Xiaomi MiMo | API key | `XIAOMI_API_KEY` |
| Kilo Code | API key | `KILOCODE_API_KEY` |
| OpenCode Zen | API key | `OPENCODE_ZEN_API_KEY` |
| OpenCode Go | API key | `OPENCODE_GO_API_KEY` |
| Qwen OAuth | OAuth | `hermes auth add qwen-oauth` |
| Custom endpoint | Config | `model.base_url` + `model.api_key` in config.yaml |
| GitHub Copilot ACP | External | `COPILOT_CLI_PATH` or Copilot CLI |

Повна документація провайдерів: https://hermes-agent.nousresearch.com/docs/integrations/providers

### Набори інструментів

Увімкнути/вимкнути за допомогою `hermes tools` (інтерактивно) або `hermes tools enable/disable NAME`.

| Набір інструментів | Що він надає |
|---------|-----------------|
| `web` | Веб‑пошук та витяг вмісту |
| `search` | Тільки веб‑пошук (підмножина `web`) |
| `browser` | Автоматизація браузера (Browserbase, Camofox або локальний Chromium) |
| `terminal` | Команди оболонки та керування процесами |
| `file` | Читання/запис/пошук/патч файлів |
| `code_execution` | Пісочниця для виконання Python |
| `vision` | Аналіз зображень |
| `image_gen` | Генерація зображень ШІ |
| `video` | Аналіз та генерація відео |
| `tts` | Текст‑у‑мову |
| `skills` | Перегляд та керування навичками |
| `memory` | Постійна пам’ять між сесіями |
| `session_search` | Пошук у минулих розмовах |
| `delegation` | Делегування завдань підагенту |
| `cronjob` | Планування завдань |
| `clarify` | Запит уточнень у користувача |
| `messaging` | Надсилання повідомлень між платформами |
| `todo` | Планування та відстеження завдань у сесії |
| `kanban` | Інструменти черги роботи багатьох агентів (доступно лише для воркерів) |
| `debugging` | Додаткові інструменти інспекції/налагодження (вимкнено за замовчуванням) |
| `safe` | Мінімальний, низькоризиковий набір інструментів для обмежених сесій |
| `spotify` | Керування відтворенням та плейлистами Spotify |
| `homeassistant` | Керування розумним будинком (вимкнено за замовчуванням) |
| `discord` | Інтеграція з Discord |
| `discord_admin` | Інструменти адміністрування/модерації Discord |
| `feishu_doc` | Інструменти документів Feishu (Lark) |
| `feishu_drive` | Інструменти диску Feishu (Lark) |
| `yuanbao` | Інтеграція з Yuanbao |
| `rl` | Інструменти підкріплювального навчання (вимкнено за замовчуванням) |
| `moa` | Mixture of Agents (вимкнено за замовчуванням) |

Повний перелік знаходиться у `toolsets.py` у словнику `TOOLSETS`; `_HERMES_CORE_TOOLS` — це стандартний пакет, який успадковують більшість платформ.

Зміни інструментів набувають чинності після `/reset` (нова сесія). Вони НЕ застосовуються під час розмови, щоб зберегти кеш промптів.
## Перемикачі безпеки та конфіденційності

Загальні «чому Hermes робить X з моїм виводом / викликами інструментів / командами?» перемикачі — і точні команди для їх зміни. Більшість з них потребують нової сесії (`/reset` у чаті або запуск нового виклику `hermes`), оскільки читаються один раз під час запуску.

### Приховування секретів у виводі інструменту

Приховування секретів **вимкнено за замовчуванням** — вивід інструменту (термінал stdout, `read_file`, веб‑вміст, підсумки підагентів тощо) проходить без змін. Якщо користувач хоче, щоб Hermes автоматично маскував рядки, що виглядають як API‑ключі, токени та інші секрети, перед їх попаданням у контекст розмови та логи:

```bash
hermes config set security.redact_secrets true       # enable globally
```

**Потрібне перезапускання.** `security.redact_secrets` зберігається у момент імпорту — зміна цього параметра під час сесії (наприклад, через `export HERMES_REDACT_SECRETS=true` під час виклику інструменту) НЕ набуде чинності для запущеного процесу. Порадьте користувачеві виконати `hermes config set security.redact_secrets true` у терміналі, а потім розпочати нову сесію. Це навмисно — запобігає LLM самостійно вмикати перемикач під час виконання завдання.

Вимкнути знову можна так:
```bash
hermes config set security.redact_secrets false
```

### Приховування персональних даних у повідомленнях шлюзу

Окремо від приховування секретів. Коли ввімкнено, шлюз хешує ідентифікатори користувачів та видаляє телефонні номери з контексту сесії перед передачею їх моделі:

```bash
hermes config set privacy.redact_pii true    # enable
hermes config set privacy.redact_pii false   # disable (default)
```

### Підтвердження команд

За замовчуванням (`approvals.mode: manual`) Hermes запитує підтвердження у користувача перед виконанням команд оболонки, позначених як руйнівні (`rm -rf`, `git reset --hard` тощо). Доступні режими:

- `manual` — завжди запитувати (за замовчуванням)
- `smart` — використовувати допоміжний LLM для автоматичного схвалення низькоризикових команд, запитувати при високому ризику
- `off` — пропускати всі запити підтвердження (еквівалент `--yolo`)

```bash
hermes config set approvals.mode smart       # recommended middle ground
hermes config set approvals.mode off         # bypass everything (not recommended)
```

Обхід під час виклику без зміни конфігурації:
- `hermes --yolo …`
- `export HERMES_YOLO_MODE=1`

Примітка: YOLO / `approvals.mode: off` НЕ вимикає приховування секретів. Це незалежні налаштування.

### Білий список хуків оболонки

Деякі інтеграції хуків оболонки потребують явного додавання до білого списку перед їх виконанням. Керується файлом `~/.hermes/shell-hooks-allowlist.json` — запит на підтвердження з’являється інтерактивно під час першого запуску хуку.

### Вимкнення інструментів веб/браузера/генерації зображень

Щоб повністю виключити модель з використанням мережевих або медіа‑інструментів, відкрий `hermes tools` і вимкни їх за платформою. Зміни набувають чинності у наступній сесії (`/reset`). Дивись розділ «Інструменти та навички» вище.
## Voice & Transcription

### STT (Voice → Text)

Голосові повідомлення з платформ обміну повідомленнями автоматично транскрибуються.

Пріоритет провайдерів (автоматично визначено):
1. **Local faster-whisper** — безкоштовно, без API‑ключа: `pip install faster-whisper`
2. **Groq Whisper** — безкоштовний тариф: вкажи `GROQ_API_KEY`
3. **OpenAI Whisper** — платний: вкажи `VOICE_TOOLS_OPENAI_KEY`
4. **Mistral Voxtral** — вкажи `MISTRAL_API_KEY`

Config:
```yaml
stt:
  enabled: true
  provider: local        # local, groq, openai, mistral
  local:
    model: base          # tiny, base, small, medium, large-v3
```

### TTS (Text → Voice)

| Provider | Env var | Безкоштовно? |
|----------|---------|--------------|
| Edge TTS | None | Yes (default) |
| ElevenLabs | `ELEVENLABS_API_KEY` | Free tier |
| OpenAI | `VOICE_TOOLS_OPENAI_KEY` | Paid |
| MiniMax | `MINIMAX_API_KEY` | Paid |
| Mistral (Voxtral) | `MISTRAL_API_KEY` | Paid |
| NeuTTS (local) | None (`pip install neutts[all]` + `espeak-ng`) | Free |

Voice commands: `/voice on` (voice‑to‑voice), `/voice tts` (завжди голос), `/voice off`.
## Запуск додаткових Hermes‑екземплярів

Запускай додаткові процеси Hermes як повністю незалежні підпроцеси — окремі сесії, інструменти та середовища.

### Коли використовувати це замість `delegate_task`

| | `delegate_task` | Запуск процесу `hermes` |
|---|-----------------|--------------------------|
| Ізоляція | Окрема розмова, спільний процес | Повністю незалежний процес |
| Тривалість | Хвилини (обмежені батьківським циклом) | Години/дні |
| Доступ до інструментів | Підмножина інструментів батька | Повний доступ до інструментів |
| Інтерактивність | Ні | Так (режим PTY) |
| Випадок використання | Швидкі паралельні підзадачі | Довгі автономні місії |

### Одноразовий режим

```
terminal(command="hermes chat -q 'Research GRPO papers and write summary to ~/research/grpo.md'", timeout=300)

# Background for long tasks:
terminal(command="hermes chat -q 'Set up CI/CD for ~/myapp'", background=true)
```

### Інтерактивний PTY‑режим (через tmux)

Hermes використовує `prompt_toolkit`, який потребує реального терміналу. Використовуй `tmux` для інтерактивного запуску:

```
# Start
terminal(command="tmux new-session -d -s agent1 -x 120 -y 40 'hermes'", timeout=10)

# Wait for startup, then send a message
terminal(command="sleep 8 && tmux send-keys -t agent1 'Build a FastAPI auth service' Enter", timeout=15)

# Read output
terminal(command="sleep 20 && tmux capture-pane -t agent1 -p", timeout=5)

# Send follow-up
terminal(command="tmux send-keys -t agent1 'Add rate limiting middleware' Enter", timeout=5)

# Exit
terminal(command="tmux send-keys -t agent1 '/exit' Enter && sleep 2 && tmux kill-session -t agent1", timeout=10)
```

### Координація багатьох агентів

```
# Agent A: backend
terminal(command="tmux new-session -d -s backend -x 120 -y 40 'hermes -w'", timeout=10)
terminal(command="sleep 8 && tmux send-keys -t backend 'Build REST API for user management' Enter", timeout=15)

# Agent B: frontend
terminal(command="tmux new-session -d -s frontend -x 120 -y 40 'hermes -w'", timeout=10)
terminal(command="sleep 8 && tmux send-keys -t frontend 'Build React dashboard for user management' Enter", timeout=15)

# Check progress, relay context between them
terminal(command="tmux capture-pane -t backend -p | tail -30", timeout=5)
terminal(command="tmux send-keys -t frontend 'Here is the API schema from the backend agent: ...' Enter", timeout=5)
```

### Відновлення сесії

```
# Resume most recent session
terminal(command="tmux new-session -d -s resumed 'hermes --continue'", timeout=10)

# Resume specific session
terminal(command="tmux new-session -d -s resumed 'hermes --resume 20260225_143052_a1b2c3'", timeout=10)
```

### Поради

- **Віддавай перевагу `delegate_task` для швидких підзадач** — менше накладних витрат, ніж запуск повного процесу
- **Використовуй `-w` (режим worktree)** при запуску агентів, які редагують код — запобігає конфліктам у `git`
- **Встановлюй тайм‑аути** для одноразового режиму — складні завдання можуть займати 5‑10 хвилин
- **Використовуй `hermes chat -q` для fire‑and‑forget** — PTY не потрібен
- **Використовуй `tmux` для інтерактивних сесій** — у чистому PTY‑режимі є проблеми з `\r` проти `\n` у `prompt_toolkit`
- **Для запланованих завдань** використай інструмент `cronjob` замість запуску — він обробляє доставку та повторення
## Durable & Background Systems

Чотири системи працюють паралельно з основним циклом розмови. Швидке ознайомлення
тут; повні нотатки для розробників знаходяться у `AGENTS.md`, документація для користувачів — у
`website/docs/user-guide/features/`.

### Делегування (`delegate_task`)

Синхронний запуск підагента — батько чекає підсумок дитини,
перш ніж продовжити власний цикл. Ізольований контекст + термінальна сесія.

- **Один:** `delegate_task(goal, context, toolsets)`.
- **Пакет:** `delegate_task(tasks=[{goal, ...}, ...])` запускає дочірні процеси
  паралельно, обмежено `delegation.max_concurrent_children` (за замовчуванням 3).
- **Ролі:** `leaf` (за замовчуванням; не може делегувати далі) проти `orchestrator`
  (може створювати власних працівників, обмежено `delegation.max_spawn_depth`).
- **Не стійке.** Якщо батьківський процес переривається, дочірній
  скасовується. Для роботи, яка має пережити поточний хід, використай `cronjob` або
  `terminal(background=True, notify_on_complete=True)`.

Налаштування: `delegation.*` у `config.yaml`.

### Cron (заплановані завдання)

Стійкий планувальник — `cron/jobs.py` + `cron/scheduler.py`. Керуй ним за допомогою
інструменту `cronjob`, CLI `hermes cron` (`list`, `add`, `edit`,
`pause`, `resume`, `run`, `remove`) або слеш‑команди `/cron`.

- **Розклади:** тривалість (`"30m"`, `"2h"`), вираз “every”
  (`"every monday 9am"`), 5‑поле cron (`"0 9 * * *"`), або ISO‑таймстамп.
- **Параметри завдання:** `skills`, перевизначення `model`/`provider`, `script`
  (збір даних перед запуском; `no_agent=True` робить скрипт цілим завданням), `context_from`
  (передає вихідні дані завдання A у завдання B), `workdir`
  (виконання у вказаній теці з завантаженими `AGENTS.md` / `CLAUDE.md`),
  мультиплатформна доставка.
- **Інваріанти:** жорстке переривання через 3 хвилини на запуск, файл `.tick.lock`
  запобігає дублюванню тіків між процесами, cron‑сесії за замовчуванням передають
  `skip_memory=True`, а доставки cron‑завдань оформлені заголовком/футером замість
  віддзеркалення у цільову сесію шлюзу (зберігає чергування ролей).

Документація для користувачів: https://hermes-agent.nousresearch.com/docs/user-guide/features/cron

### Curator (життєвий цикл skill)

Фонове обслуговування skill, створених агентом. Відстежує використання, позначає
неактивні skill як застарілі, архівує їх, зберігає tar.gz‑резервну копію,
щоб нічого не втратити.

- **CLI:** `hermes curator <verb>` — `status`, `run`, `pause`, `resume`,
  `pin`, `unpin`, `archive`, `restore`, `prune`, `backup`, `rollback`.
- **Slash:** `/curator <subcommand>` повторює CLI.
- **Область:** працює лише зі skill, у яких `created_by: "agent"` у provenance.
  Вбудовані та встановлені через hub skill недоступні. **Ніколи не видаляє** —
  максимальна руйнівна дія — архівування. Прикріплені (pinned) skill виключені
  з будь‑якого автоматичного переходу та перевірки LLM.
- **Телеметрія:** допоміжний файл `~/.hermes/skills/.usage.json` містить
  для кожного skill `use_count`, `view_count`, `patch_count`,
  `last_activity_at`, `state`, `pinned`.

Налаштування: `curator.*` (`enabled`, `interval_hours`, `min_idle_hours`,
`stale_after_days`, `archive_after_days`, `backup.*`).
Документація для користувачів: https://hermes-agent.nousresearch.com/docs/user-guide/features/curator

### Kanban (черга роботи багатьох агентів)

Стійка SQLite‑дошка для співпраці між кількома профілями / працівниками.
Користувачі керують нею через `hermes kanban <verb>`; працівники,
запущені диспетчером, бачать спеціальний `kanban_*` інструментальний набір,
заблокований змінною `HERMES_KANBAN_TASK`, а профілі‑оркестратори можуть
включити ширший набір `kanban`. У звичайних сесіях схеми `kanban_*` не
присутні, якщо їх не налаштовано.

- **CLI‑дієслова (поширені):** `init`, `create`, `list` (alias `ls`),
  `show`, `assign`, `link`, `unlink`, `comment`, `complete`, `block`,
  `unblock`, `archive`, `tail`. Менш поширені: `watch`, `stats`, `runs`,
  `log`, `dispatch`, `daemon`, `gc`.
- **Набір інструментів працівника/оркестратора:** `kanban_show`, `kanban_complete`,
  `kanban_block`, `kanban_heartbeat`, `kanban_comment`, `kanban_create`,
  `kanban_link`; профілі, які явно ввімкнули набір `kanban` поза
  задачами, створеними диспетчером, також отримують `kanban_list` і
  `kanban_unblock` для маршрутизації на дошці.
- **Диспетчер** за замовчуванням працює всередині шлюзу
  (`kanban.dispatch_in_gateway: true`) — відновлює застарілі заявки,
  просуває готові задачі, атомарно їх захоплює, запускає призначені профілі.
  Автоматично блокує задачу після `failure_limit` послідовних невдач запуску
  (за замовчуванням 2; налаштовується через `kanban.failure_limit` або
  індивідуальне `max_retries` у завданні).
- **Ізоляція:** дошка — жорстка межа (працівники отримують
  `HERMES_KANBAN_BOARD` у середовищі); tenant — м’яке простір імен
  всередині дошки для ізоляції шляхів робочих просторів та ключів пам'яті.

Документація для користувачів: https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban
## Windows‑Specific Quirks

Hermes працює нативно на Windows (PowerShell, cmd, Windows Terminal, git‑bash
mintty, інтегрований термінал VS Code). Більшість функцій просто працює, але
деякі відмінності між Win32 і POSIX нас підвели — документуй нові тут, коли
зустрічаєш їх, щоб наступна людина (або наступна сесія) не відкривала їх
знову з нуля.

### Input / Keybindings

**Alt+Enter не вставляє новий рядок.** Windows Terminal перехоплює Alt+Enter
на рівні терміналу, щоб перемкнутись у повноекранний режим — клавіша ніколи
не доходить до `prompt_toolkit`. Використовуй **Ctrl+Enter** замість цього.
Windows Terminal передає Ctrl+Enter як LF (`c-j`), відмінно від простого
Enter (`c-m` / CR), і CLI прив’язує `c-j` до вставки нового рядка лише на
`win32` (див. `_bind_prompt_submit_keys` + прив’язку Windows‑only `c-j` у
`cli.py`). Побічний ефект: «сирий» Ctrl+J також вставляє новий рядок у
Windows — це неминуче, бо Windows Terminal зводить Ctrl+Enter і Ctrl+J до
одного коду клавіші на рівні Win32 console API. Конфліктної прив’язки для
Ctrl+J у Windows не було, тому це безпечний побічний ефект.

mintty / git‑bash поводяться так само (повноекранний режим на Alt+Enter),
якщо не вимкнути скорочення Alt+Fn у Options → Keys. Проще просто
використовувати Ctrl+Enter.

**Діагностика прив’язок клавіш.** Запусти `python scripts/keystroke_diagnostic.py`
(корінь репозиторію), щоб точно побачити, як `prompt_toolkit` ідентифікує
кожну клавішу в поточному терміналі. Відповідає на питання типу «чи
Shift+Enter передається як окрема клавіша?» (майже ніколи — більшість
терміналів зводять її до простого Enter) або «яка послідовність байтів
надсилає мій термінал для Ctrl+Enter?» Це те, як було встановлено факт
Ctrl+Enter = c‑j.

### Config / Files

**HTTP 400 «No models provided» під час першого запуску.** `config.yaml` був
збережений з UTF‑8 BOM (часто, коли Windows‑додатки його записують). Перезапиши
як UTF‑8 без BOM. `hermes config edit` записує без BOM; ручне редагування в
Notepad зазвичай є причиною.

### `execute_code` / Sandbox

**WinError 10106** («The requested service provider could not be loaded or
initialized») від процесу‑дитини у пісочниці — він не може створити
`AF_INET`‑socket, тому запасний варіант loopback‑TCP RPC падає ще до
`connect()`. Основна причина зазвичай **не** поломка Winsock LSP; це
скраббер середовища Hermes, який видаляє `SYSTEMROOT` / `WINDIR` / `COMSPEC`
з середовища дитини. Модуль `socket` у Python потребує `SYSTEMROOT` для
знаходження `mswsock.dll`. Виправлено у білому списку `_WINDOWS_ESSENTIAL_ENV_VARS`
у `tools/code_execution_tool.py`. Якщо проблема ще виникає, виведи
`os.environ` всередині блоку `execute_code`, щоб переконатися, що `SYSTEMROOT`
встановлено. Повний рецепт діагностики у
`references/execute-code-sandbox-env-windows.md`.

### Testing / Contributing

**`scripts/run_tests.sh` не працює «як є» у Windows** — він шукає
POSIX‑розташування venv (`.venv/bin/activate`). Venv, встановлений Hermes,
у `venv/Scripts/` не містить ні `pip`, ні `pytest` (видалено для зменшення
розміру інсталяції). Обхідний шлях: встанови `pytest + pytest-xdist + pyyaml`
у системний Python 3.11 user‑site, потім виклич `pytest` безпосередньо,
встановивши `PYTHONPATH`:

```bash
"/c/Program Files/Python311/python" -m pip install --user pytest pytest-xdist pyyaml
export PYTHONPATH="$(pwd)"
"/c/Program Files/Python311/python" -m pytest tests/foo/test_bar.py -v --tb=short -n 0
```

Використовуй `-n 0`, а не `-n 4` — `addopts` у `pyproject.toml` вже містить
`-n`, і гарантії CI‑паритету обгортки не застосовуються поза POSIX.

**Тести, що працюють лише у POSIX, потребують guard‑ів.** Спільні маркери вже
є в кодовій базі:
- Символьні посилання — підвищені привілеї у Windows
- `0o600` режим файлів — бітові режимі POSIX не застосовуються за замовчуванням у NTFS
- `signal.SIGALRM` — лише Unix (див. `tests/conftest.py::_enforce_test_timeout`)
- Winsock / Windows‑специфічні регресії — `@pytest.mark.skipif(sys.platform != "win32", ...)`

Використовуй існуючий стиль skip‑патернів (`sys.platform == "win32"` або
`sys.platform.startswith("win")`), щоб залишатися узгодженим з рештою
набору.

### Path / Filesystem

**Кінці рядків.** Git може попереджати `LF will be replaced by CRLF the next time
Git touches it`. Це лише косметика — `.gitattributes` у репозиторії
нормалізує. Не дозволяй редакторам автоматично конвертувати файли з
POSIX‑новими рядками у CRLF.

**Прямі слеші працюють майже всюди.** `C:/Users/...` приймається всіма
інструментами Hermes і більшістю Windows‑API. Віддавай перевагу прямим
слешам у коді та логах — це уникає екранування зворотних слешів у bash.

---
## Усунення проблем

### Голос не працює
1. Перевір `stt.enabled: true` у `config.yaml`.
2. Переконайся у провайдері: `pip install faster-whisper` або встанови API‑ключ.
3. У gateway: `/restart`. У CLI: вийди та запусти знову.

### Інструмент недоступний
1. `hermes tools` — перевір, чи інструментальний набір увімкнено для твоєї платформи.
2. Деякі інструменти потребують змінних середовища (перевір `.env`).
3. `/reset` після увімкнення інструментів.

### Проблеми з моделлю/провайдером
1. `hermes doctor` — перевір конфігурацію та залежності.
2. `hermes auth` — повторно автентифікуй OAuth‑провайдерів (або `hermes auth add <provider>`).
3. Переконайся, що у `.env` правильний API‑ключ.
4. **Copilot 403**: токени `gh auth login` НЕ працюють з API Copilot. Потрібно використати специфічний для Copilot OAuth‑device‑code flow через `hermes model` → GitHub Copilot.

### Зміни не набирають сили
- **Інструменти/навички**: `/reset` запускає нову сесію з оновленим інструментальним набором.
- **Зміни конфігурації**: у gateway: `/restart`. У CLI: вийди та запусти знову.
- **Зміни коду**: перезапусти процес CLI або gateway.

### Навички не відображаються
1. `hermes skills list` — перевір, чи встановлені.
2. `hermes skills config` — перевір увімкнення на платформі.
3. Завантаж явно: `/skill name` або `hermes -s name`.

### Проблеми з gateway
Перевір журнали спочатку:
```bash
grep -i "failed to send\|error" ~/.hermes/logs/gateway.log | tail -20
```

Типові проблеми gateway:
- **Gateway падає при виході з SSH**: увімкни linger: `sudo loginctl enable-linger $USER`.
- **Gateway падає при закритті WSL2**: WSL2 потребує `systemd=true` у `/etc/wsl.conf` для роботи systemd‑служб. Без цього gateway переходить у `nohup` (падає при закритті сесії).
- **Gateway у циклі падінь**: скинь стан помилки: `systemctl --user reset-failed hermes-gateway`.

### Платформо‑специфічні проблеми
- **Discord‑бот мовчить**: потрібно увімкнути **Message Content Intent** у Bot → Privileged Gateway Intents.
- **Slack‑бот працює лише в DM**: потрібно підписатися на подію `message.channels`. Без цього бот ігнорує публічні канали.
- **Проблеми Windows** (`Alt+Enter` новий рядок, WinError 10106, конфігурація UTF‑8 BOM, тестовий набір, кінці рядків): дивись розділ **Windows‑Specific Quirks** вище.

### Додаткові моделі не працюють
Якщо завдання `auxiliary` (vision, compression, session_search) тихо падають, провайдер `auto` не може знайти бекенд. Встанови `OPENROUTER_API_KEY` або `GOOGLE_API_KEY`, або явно налаштуй провайдера для кожного додаткового завдання:
```bash
hermes config set auxiliary.vision.provider <your_provider>
hermes config set auxiliary.vision.model <model_name>
```
## Де знайти речі

| Шукаєте… | Розташування |
|----------------|----------|
| Параметри конфігурації | `hermes config edit` або [Документація конфігурації](https://hermes-agent.nousresearch.com/docs/user-guide/configuration) |
| Доступні інструменти | `hermes tools list` або [Посилання на інструменти](https://hermes-agent.nousresearch.com/docs/reference/tools-reference) |
| Слеш‑команди | `/help` у сесії або [Посилання на слеш‑команди](https://hermes-agent.nousresearch.com/docs/reference/slash-commands) |
| Каталог навичок | `hermes skills browse` або [Каталог навичок](https://hermes-agent.nousresearch.com/docs/reference/skills-catalog) |
| Налаштування провайдера | `hermes model` або [Посібник провайдерів](https://hermes-agent.nousresearch.com/docs/integrations/providers) |
| Налаштування платформи | `hermes gateway setup` або [Документація обміну повідомленнями](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/) |
| Сервери MCP | `hermes mcp list` або [Посібник MCP](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp) |
| Профілі | `hermes profile list` або [Документація профілів](https://hermes-agent.nousresearch.com/docs/user-guide/profiles) |
| Cron‑завдання | `hermes cron list` або [Документація Cron](https://hermes-agent.nousresearch.com/docs/user-guide/features/cron) |
| Пам’ять | `hermes memory status` або [Документація пам’яті](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory) |
| Змінні середовища | `hermes config env-path` або [Посилання на змінні середовища](https://hermes-agent.nousresearch.com/docs/reference/environment-variables) |
| Команди CLI | `hermes --help` або [Посилання CLI](https://hermes-agent.nousresearch.com/docs/reference/cli-commands) |
| Логи шлюзу | `~/.hermes/logs/gateway.log` |
| Файли сесії | `hermes sessions browse` (читає `state.db`) |
| Вихідний код | `~/.hermes/hermes-agent/` |

---
## Швидке посилання для контрибуторів

Для випадкових контрибуторів та авторів PR. Повна документація для розробників: https://hermes-agent.nousresearch.com/docs/developer-guide/

### Структура проєкту

<!-- ascii-guard-ignore -->
```
hermes-agent/
├── run_agent.py          # AIAgent — core conversation loop
├── model_tools.py        # Tool discovery and dispatch
├── toolsets.py           # Toolset definitions
├── cli.py                # Interactive CLI (HermesCLI)
├── hermes_state.py       # SQLite session store
├── agent/                # Prompt builder, context compression, memory, model routing, credential pooling, skill dispatch
├── hermes_cli/           # CLI subcommands, config, setup, commands
│   ├── commands.py       # Slash command registry (CommandDef)
│   ├── config.py         # DEFAULT_CONFIG, env var definitions
│   └── main.py           # CLI entry point and argparse
├── tools/                # One file per tool
│   └── registry.py       # Central tool registry
├── gateway/              # Messaging gateway
│   └── platforms/        # Platform adapters (telegram, discord, etc.)
├── cron/                 # Job scheduler
├── tests/                # ~3000 pytest tests
└── website/              # Docusaurus docs site
```
<!-- ascii-guard-ignore-end -->

Конфіг: `~/.hermes/config.yaml` (налаштування), `~/.hermes/.env` (API‑ключі).

### Додавання інструменту (3 файли)

**1. Створи `tools/your_tool.py`:**
```python
import json, os
from tools.registry import registry

def check_requirements() -> bool:
    return bool(os.getenv("EXAMPLE_API_KEY"))

def example_tool(param: str, task_id: str = None) -> str:
    return json.dumps({"success": True, "data": "..."})

registry.register(
    name="example_tool",
    toolset="example",
    schema={"name": "example_tool", "description": "...", "parameters": {...}},
    handler=lambda args, **kw: example_tool(
        param=args.get("param", ""), task_id=kw.get("task_id")),
    check_fn=check_requirements,
    requires_env=["EXAMPLE_API_KEY"],
)
```

**2. Додай у `toolsets.py`** → список `_HERMES_CORE_TOOLS`.

Автовиявлення: будь‑який файл `tools/*.py` з викликом `registry.register()` на верхньому рівні імпортується автоматично — ручний список не потрібен.

Усі обробники мають повертати рядки JSON. Використовуй `get_hermes_home()` для шляхів, ніколи не хардкодь `~/.hermes`.

### Додавання slash‑команди

1. Додай `CommandDef` до `COMMAND_REGISTRY` у `hermes_cli/commands.py`
2. Додай обробник у `cli.py` → `process_command()`
3. (Необов’язково) Додай обробник шлюзу у `gateway/run.py`

Усі споживачі (текст довідки, автодоповнення, меню Telegram, маппінг Slack) отримують дані з центрального реєстру автоматично.

### Цикл агента (високий рівень)

```
run_conversation():
  1. Build system prompt
  2. Loop while iterations < max:
     a. Call LLM (OpenAI-format messages + tool schemas)
     b. If tool_calls → dispatch each via handle_function_call() → append results → continue
     c. If text response → return
  3. Context compression triggers automatically near token limit
```

### Тестування

```bash
python -m pytest tests/ -o 'addopts=' -q   # Full suite
python -m pytest tests/tools/ -q            # Specific area
```

- Тести автоматично перенаправляють `HERMES_HOME` у тимчасові каталоги — ніколи не торкайся реального `~/.hermes/`.
- Запусти повний набір тестів перед пушем будь‑якої зміни.
- Використовуй `-o 'addopts='` щоб очистити будь‑які вбудовані прапорці pytest.

**Контрибутори Windows:** `scripts/run_tests.sh` наразі шукає POSIX‑віртуальні середовища (`.venv/bin/activate` / `venv/bin/activate`) і помилиться на Windows, де структура `venv/Scripts/activate` + `python.exe`. Віртуальне середовище, встановлене Hermes у `venv/Scripts/`, також не містить `pip` чи `pytest` — його спрощено для зменшення розміру інсталяції. Обхід: встанови `pytest` + `pytest-xdist` + `pyyaml` у системний Python 3.11 користувача (`/c/Program Files/Python311/python -m pip install --user pytest pytest-xdist pyyaml`), потім запусти тести безпосередньо:

```bash
export PYTHONPATH="$(pwd)"
"/c/Program Files/Python311/python" -m pytest tests/tools/test_foo.py -v --tb=short -n 0
```

Використовуй `-n 0` (не `-n 4`), бо в `pyproject.toml` вже є `addopts` з `-n`, і історія CI‑паритету обгортки не застосовується поза POSIX.

**Крос‑платформенні захисти тестів:** тести, що використовують лише POSIX‑системні виклики, потребують маркера пропуску. Загальні вже є в кодовій базі:
- Створення символьного посилання → `@pytest.mark.skipif(sys.platform == "win32", reason="Symlinks require elevated privileges on Windows")` (див. `tests/cron/test_cron_script.py`)
- POSIX‑режими файлів (0o600 тощо) → `@pytest.mark.skipif(sys.platform.startswith("win"), reason="POSIX mode bits not enforced on Windows")` (див. `tests/hermes_cli/test_auth_toctou_file_modes.py`)
- `signal.SIGALRM` → лише Unix (див. `tests/conftest.py::_enforce_test_timeout`)
- Live Winsock / Windows‑специфічні регресійні тести → `@pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific regression")`

**Monkeypatching `sys.platform` недостатньо**, коли код під тестом також викликає `platform.system()` / `platform.release()` / `platform.mac_ver()`. Ці функції читають реальну ОС окремо, тому тест, який встановлює `sys.platform = "linux"` на Windows‑ранері, все одно побачить `platform.system() == "Windows"` і перейде у Windows‑гілку. Патчуй усі три разом:

```python
monkeypatch.setattr(sys, "platform", "linux")
monkeypatch.setattr(platform, "system", lambda: "Linux")
monkeypatch.setattr(platform, "release", lambda: "6.8.0-generic")
```

Дивись `tests/agent/test_prompt_builder.py::TestEnvironmentHints` для прикладу.

### Розширення блоку execution‑environment у системній підказці

Фактичні дані про ОС хоста, домашню директорію користувача, cwd, бекенд терміналу та оболонку (bash vs. PowerShell на Windows) генерує `agent/prompt_builder.py::build_environment_hints()`. Тут же живе логіка підказки WSL та проби бекенду. Конвенція:

- **Локальний бекенд терміналу** → виводить інформацію про хост (OS, `$HOME`, cwd) + нотатки для Windows (hostname ≠ username, `terminal` використовує bash, а не PowerShell).
- **Віддалений бекенд терміналу** (будь‑який у `_REMOTE_TERMINAL_BACKENDS`: `docker, singularity, modal, daytona, ssh, managed_modal`) → **придушує** всю інформацію про хост і описує лише бекенд. Живий проб `uname`/`whoami`/`pwd` виконується всередині бекенду через `tools.environments.get_environment(...).execute(...)`, кешується процесом у `_BACKEND_PROBE_CACHE`, з статичним запасним варіантом при тайм‑ауті.
- **Ключовий факт для авторів підказок:** коли `TERMINAL_ENV != "local"`, *кожен* файловий інструмент (`read_file`, `write_file`, `patch`, `search_files`) працює всередині контейнера бекенду, а не на хості. Системна підказка ніколи не повинна описувати хост у цьому випадку — агент не може до нього дістатися.

Повні нотатки дизайну, точні рядки, що генеруються, та підводні камені тестування:
`references/prompt-builder-environment-hints.md`.

**Шаблон безпеки рефакторингу (захист POSIX‑еквівалентності):** коли винесеш інлайн‑логіку у допоміжну функцію, що додає Windows/платформо‑специфічну поведінку, залиш у тестовому файлі функцію‑оракул `_legacy_<name>`, що є точним копією старого коду, і порівнюй її параметризовано. Приклад: `tests/tools/test_code_execution_windows_env.py::TestPosixEquivalence`. Це фіксує інваріант, що поведінка POSIX має бути біт‑в‑біт, і будь‑яке відхилення буде помічено чітким різницевим виводом.

### Конвенції комітів

```
type: concise subject line

Optional body.
```

Типи: `fix:`, `feat:`, `refactor:`, `docs:`, `chore:`

### Ключові правила

- **Ніколи не порушуй кешування підказки** — не змінюй контекст, інструменти або системну підказку під час розмови.
- **Чередування ролей повідомлень** — ніколи не два повідомлення асистента або два повідомлення користувача підряд.
- Використовуй `get_hermes_home()` з `hermes_constants` для всіх шляхів (безпечно для профілів).
- Значення конфігурації розміщуй у `config.yaml`, секрети — у `.env`.
- Нові інструменти потребують `check_fn`, щоб вони з’являлися лише за виконання вимог.