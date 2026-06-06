---
title: "Hermes Agent — Настраивай, расширяй или вноси вклад в Hermes Agent"
sidebar_label: "Hermes Agent"
description: "Настрой, расширяй или вноси вклад в Hermes Agent"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Hermes Agent

Настраивай, расширяй или вноси вклад в Hermes Agent.
## Метаданные навыка

| | |
|---|---|
| Источник | Встроенный (устанавливается по умолчанию) |
| Путь | `skills/autonomous-ai-agents/hermes-agent` |
| Версия | `2.1.0` |
| Автор | Hermes Agent + Teknium |
| Лицензия | MIT |
| Платформы | linux, macos, windows |
| Теги | `hermes`, `setup`, `configuration`, `multi-agent`, `spawning`, `cli`, `gateway`, `development` |
| Связанные навыки | [`claude-code`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-claude-code), [`codex`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-codex), [`opencode`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-opencode) |
:::info
Следующий текст — полное определение навыка, которое Hermes загружает при срабатывании этого навыка. Это то, что агент видит как инструкции, когда навык активен.
:::

# Hermes Agent

Hermes Agent — это открытый фреймворк AI‑агентов от Nous Research, работающий в твоём терминале, мессенджерах и IDE. Он относится к той же категории, что и Claude Code (Anthropic), Codex (OpenAI) и OpenClaw — автономные агенты кодинга и выполнения задач, использующие вызов инструментов для взаимодействия с системой. Hermes совместим с любым провайдером LLM (OpenRouter, Anthropic, OpenAI, DeepSeek, локальными моделями и более чем 15 другими) и работает на Linux, macOS и WSL.

Что отличает Hermes:

- **Самообучающийся агент через навыки** — Hermes учится на опыте, сохраняя переиспользуемые процедуры в виде навыков. Когда он решает сложную задачу, обнаруживает рабочий процесс или получает исправление, он может сохранить эти знания в документе навыка, который будет загружаться в будущих сессиях. Навыки накапливаются со временем, делая агента лучше в твоих конкретных задачах и окружении.
- **Постоянная память между сессиями** — помнит, кто ты, твои предпочтения, детали окружения и полученные уроки. Подключаемые бекэнды памяти (встроенные, Honcho, Mem0 и другие) позволяют выбрать, как будет работать память.
- **Мультиплатформенный шлюз** — один и тот же агент работает в Telegram, Discord, Slack, WhatsApp, Signal, Matrix, Email и более чем 10 других платформах с полным доступом к инструментам, а не только в чате.
- **Провайдер‑агностичный** — меняй модели и провайдеров в середине рабочего процесса без изменения чего‑либо ещё. Пулы учётных данных автоматически переключаются между несколькими API‑ключами.
- **Профили** — запускай несколько независимых экземпляров Hermes с изолированными конфигурациями, сессиями, навыками и памятью.
- **Расширяемый** — плагины, MCP‑серверы, пользовательские инструменты, веб‑хуки, планирование cron и весь экосистемный Python.

Люди используют Hermes для разработки программного обеспечения, исследований, администрирования систем, анализа данных, создания контента, домашней автоматизации и всего, что выигрывает от AI‑агента с постоянным контекстом и полным доступом к системе.

**Этот навык помогает эффективно работать с Hermes Agent** — настройка, конфигурация функций, запуск дополнительных экземпляров агента, устранение проблем, поиск нужных команд и параметров, а также понимание работы системы, когда нужно расширять или вносить вклад.

**Docs:** https://hermes-agent.nousresearch.com/docs/
## Быстрый старт

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
## Справочник CLI

### Глобальные флаги

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

Если не указана подкоманда, по умолчанию используется `chat`.

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

### Конфигурация

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

### Инструменты и навыки

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

### MCP‑серверы

```
hermes mcp serve            Run Hermes as an MCP server
hermes mcp add NAME         Add an MCP server (--url or --command)
hermes mcp remove NAME      Remove an MCP server
hermes mcp list             List configured servers
hermes mcp test NAME        Test connection
hermes mcp configure NAME   Toggle tool selection
```

### Шлюз (платформы обмена сообщениями)

```
hermes gateway run          Start gateway foreground
hermes gateway install      Install as background service
hermes gateway start/stop   Control the service
hermes gateway restart      Restart the service
hermes gateway status       Check status
hermes gateway setup        Configure platforms
```

Поддерживаемые платформы: Telegram, Discord, Slack, WhatsApp, Signal, Email, SMS, Matrix, Mattermost, Home Assistant, DingTalk, Feishu, WeCom, BlueBubbles (iMessage), Weixin (WeChat), API Server, Webhooks. Open WebUI подключается через адаптер API Server.

Документация по платформам: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/

### Сессии

```
hermes sessions list        List recent sessions
hermes sessions browse      Interactive picker
hermes sessions export OUT  Export to JSONL
hermes sessions rename ID T Rename a session
hermes sessions delete ID   Delete a session
hermes sessions prune       Clean up old sessions (--older-than N days)
hermes sessions stats       Session store statistics
```

### Cron‑задачи

```
hermes cron list            List jobs (--all for disabled)
hermes cron create SCHED    Create: '30m', 'every 2h', '0 9 * * *'
hermes cron edit ID         Edit schedule, prompt, delivery
hermes cron pause/resume ID Control job state
hermes cron run ID          Trigger on next tick
hermes cron remove ID       Delete a job
hermes cron status          Scheduler status
```

### Webhook‑ы

```
hermes webhook subscribe N  Create route at /webhooks/<name>
hermes webhook list         List subscriptions
hermes webhook remove NAME  Remove a subscription
hermes webhook test NAME    Send a test POST
```

### Профили

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

### Пулы учётных данных

```
hermes auth add             Interactive credential wizard
hermes auth list [PROVIDER] List pooled credentials
hermes auth remove P INDEX  Remove by provider + index
hermes auth reset PROVIDER  Clear exhaustion status
```

### Прочее

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
## Команды со слешем (в сессии)

Вводи их во время интерактивной чат‑сессии. Новые команды появляются довольно часто; если что‑то ниже выглядит устаревшим, запусти `/help` в сессии для получения авторитетного списка или смотри [список живых команд со слешем](https://hermes-agent.nousresearch.com/docs/reference/slash-commands). Официальный реестр находится в `hermes_cli/commands.py` — каждый потребитель (autocomplete, Telegram menu, Slack mapping, `/help`) наследует его.

### Управление сессией
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

### Конфигурация
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

### Инструменты и skills
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

### Gateway
```
/approve             Approve a pending command (gateway)
/deny                Deny a pending command (gateway)
/restart             Restart gateway (gateway)
/sethome             Set current chat as home channel (gateway)
/update              Update Hermes to latest (gateway)
/topic [sub]         Enable or inspect Telegram DM topic sessions (gateway)
/platforms (/gateway) Show platform connection status (gateway)
```

### Утилиты
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

### Информация
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

### Выход
```
/quit (/exit, /q)    Exit CLI
```

---
## Ключевые пути и конфигурация

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

Профили используют `~/.hermes/profiles/<name>/` с той же структурой.

### Разделы конфигурации

Редактировать с помощью `hermes config edit` или `hermes config set section.key value`.

| Раздел | Параметры |
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

Полная справка по конфигурации: https://hermes-agent.nousresearch.com/docs/user-guide/configuration

### Провайдеры

Поддерживается более 20 провайдеров. Устанавливаются через `hermes model` или `hermes setup`.

| Провайдер | Авторизация | Переменная окружения |
|----------|--------------|----------------------|
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
| Пользовательский endpoint | Config | `model.base_url` + `model.api_key` in config.yaml |
| GitHub Copilot ACP | External | `COPILOT_CLI_PATH` or Copilot CLI |

Полная документация провайдеров: https://hermes-agent.nousresearch.com/docs/integrations/providers

### Наборы инструментов

Включать/выключать через `hermes tools` (интерактивно) или `hermes tools enable/disable NAME`.

| Набор инструментов | Что предоставляет |
|--------------------|--------------------|
| `web` | Веб‑поиск и извлечение контента |
| `search` | Только веб‑поиск (подмножество `web`) |
| `browser` | Автоматизация браузера (Browserbase, Camofox или локальный Chromium) |
| `terminal` | Команды оболочки и управление процессами |
| `file` | Чтение/запись/поиск/патч файлов |
| `code_execution` | Песочница для выполнения Python |
| `vision` | Анализ изображений |
| `image_gen` | Генерация изображений ИИ |
| `video` | Анализ и генерация видео |
| `tts` | Текст‑в‑речь |
| `skills` | Обзор и управление навыками |
| `memory` | Постоянная память между сессиями |
| `session_search` | Поиск по прошлым разговорам |
| `delegation` | Делегирование задач субагенту |
| `cronjob` | Планирование задач |
| `clarify` | Задавание уточняющих вопросов пользователю |
| `messaging` | Отправка сообщений на разных платформах |
| `todo` | Планирование и отслеживание задач в сессии |
| `kanban` | Инструменты очереди задач для нескольких агентов (доступно только рабочим) |
| `debugging` | Дополнительные инструменты отладки/интроспекции (по умолчанию выключено) |
| `safe` | Минимальный, низко‑рисковый набор инструментов для ограниченных сессий |
| `spotify` | Управление воспроизведением и плейлистами Spotify |
| `homeassistant` | Управление умным домом (по умолчанию выключено) |
| `discord` | Интеграция с Discord |
| `discord_admin` | Инструменты администрирования/модерации Discord |
| `feishu_doc` | Инструменты работы с документами Feishu (Lark) |
| `feishu_drive` | Инструменты работы с диском Feishu (Lark) |
| `yuanbao` | Интеграция с Yuanbao |
| `rl` | Инструменты обучения с подкреплением (по умолчанию выключено) |
| `moa` | Смешанные агенты (по умолчанию выключено) |

Полный перечень находится в `toolsets.py` в виде словаря `TOOLSETS`; `_HERMES_CORE_TOOLS` — набор инструментов по умолчанию, от которого наследуются большинство платформ.

Изменения наборов инструментов вступают в силу после `/reset` (новая сессия). Они НЕ применяются в середине разговора, чтобы сохранить кэш подсказок.
## Security & Privacy Toggles

Общие «почему Hermes делает X с моим выводом / вызовами инструментов / командами?» переключатели — и точные команды для их изменения. Большинство из них требуют новой сессии (`/reset` в чате или запуск нового вызова `hermes`), поскольку читаются один раз при старте.

### Secret redaction in tool output

Маскирование секретов **выключено по умолчанию** — вывод инструмента (stdout терминала, `read_file`, веб‑контент, резюме субагентов и т.д.) проходит без изменений. Если пользователь хочет, чтобы Hermes автоматически скрывал строки, похожие на API‑ключи, токены и секреты, до того как они попадут в контекст разговора и логи:

```bash
hermes config set security.redact_secrets true       # enable globally
```

**Требуется перезапуск.** `security.redact_secrets` фиксируется при импорте — переключение его в середине сессии (например, через `export HERMES_REDACT_SECRETS=true` из вызова инструмента) НЕ подействует на уже запущенный процесс. Попроси пользователя выполнить `hermes config set security.redact_secrets true` в терминале, затем запустить новую сессию. Это сделано намеренно — чтобы LLM не мог сам включить переключатель во время выполнения задачи.

Отключить снова можно так:
```bash
hermes config set security.redact_secrets false
```

### PII redaction in gateway messages

Отдельно от маскирования секретов. Когда включено, **gateway** хеширует идентификаторы пользователей и удаляет телефонные номера из контекста сессии до того, как они попадут к модели:

```bash
hermes config set privacy.redact_pii true    # enable
hermes config set privacy.redact_pii false   # disable (default)
```

### Command approval prompts

По умолчанию (`approvals.mode: manual`) Hermes запрашивает подтверждение у пользователя перед выполнением команд оболочки, помеченных как разрушительные (`rm -rf`, `git reset --hard` и т.п.). Доступные режимы:

- `manual` — всегда запрашивать (по умолчанию)
- `smart` — использовать вспомогательный LLM для автоодобрения команд низкого риска, запрашивать подтверждение для высокорисковых
- `off` — пропускать все запросы подтверждения (эквивалент `--yolo`)

```bash
hermes config set approvals.mode smart       # recommended middle ground
hermes config set approvals.mode off         # bypass everything (not recommended)
```

Обход для отдельного вызова без изменения конфигурации:
- `hermes --yolo …`
- `export HERMES_YOLO_MODE=1`

Важно: YOLO / `approvals.mode: off` НЕ отключает маскирование секретов. Они работают независимо.

### Shell hooks allowlist

Некоторые интеграции хуков оболочки требуют явного добавления в **allowlist** перед их выполнением. Управляется файлом `~/.hermes/shell-hooks-allowlist.json` — при первом запросе хука появляется интерактивный запрос.

### Disabling the web/browser/image-gen tools

Чтобы полностью исключить модель из использования сетевых или медиа‑инструментов, открой `hermes tools` и переключи соответствующие платформы. Изменения вступают в силу в следующей сессии (`/reset`). См. раздел «Tools & Skills» выше.
## Голос и транскрипция

### STT (Голос → Текст)

Голосовые сообщения с платформ обмена сообщениями автоматически транскрибируются.

Приоритет провайдера (автоматически определяется):
1. **Local faster-whisper** — бесплатно, без API‑ключа: `pip install faster-whisper`
2. **Groq Whisper** — бесплатный тариф: задайте `GROQ_API_KEY`
3. **OpenAI Whisper** — платный: задайте `VOICE_TOOLS_OPENAI_KEY`
4. **Mistral Voxtral** — задайте `MISTRAL_API_KEY`

Config:
```yaml
stt:
  enabled: true
  provider: local        # local, groq, openai, mistral
  local:
    model: base          # tiny, base, small, medium, large-v3
```

### TTS (Текст → Голос)

| Provider | Env var | Free? |
|----------|---------|-------|
| Edge TTS | None | Yes (default) |
| ElevenLabs | `ELEVENLABS_API_KEY` | Free tier |
| OpenAI | `VOICE_TOOLS_OPENAI_KEY` | Paid |
| MiniMax | `MINIMAX_API_KEY` | Paid |
| Mistral (Voxtral) | `MISTRAL_API_KEY` | Paid |
| NeuTTS (local) | None (`pip install neutts[all]` + `espeak-ng`) | Free |

Голосовые команды: `/voice on` (voice‑to‑voice), `/voice tts` (always voice), `/voice off`.
## Запуск дополнительных экземпляров Hermes

Запускай дополнительные процессы Hermes как полностью независимые подпроцессы — отдельные сессии, инструменты и окружения.

### Когда использовать это вместо `delegate_task`

|                     | `delegate_task` | Запуск процесса `hermes` |
|---------------------|-----------------|--------------------------|
| Изоляция            | Общий процесс, отдельный разговор | Полностью независимый процесс |
| Длительность        | Минуты (ограничено родительским циклом) | Часы/дни |
| Доступ к инструментам | Подмножество инструментов родителя | Полный доступ к инструментам |
| Интерактивность    | Нет | Да (режим PTY) |
| Сценарий использования | Быстрые параллельные подзадачи | Длительные автономные миссии |

### Одноразовый режим

```
terminal(command="hermes chat -q 'Research GRPO papers and write summary to ~/research/grpo.md'", timeout=300)

# Background for long tasks:
terminal(command="hermes chat -q 'Set up CI/CD for ~/myapp'", background=true)
```

### Интерактивный PTY‑режим (через tmux)

Hermes использует `prompt_toolkit`, которому нужен реальный терминал. Для интерактивного запуска используй `tmux`:

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

### Координация нескольких агентов

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

### Возобновление сессии

```
# Resume most recent session
terminal(command="tmux new-session -d -s resumed 'hermes --continue'", timeout=10)

# Resume specific session
terminal(command="tmux new-session -d -s resumed 'hermes --resume 20260225_143052_a1b2c3'", timeout=10)
```

### Советы

- **Отдавай предпочтение `delegate_task` для быстрых подзадач** — меньше накладных расходов, чем запуск полного процесса
- **Используй `-w` (режим worktree)** при запуске агентов, которые редактируют код — предотвращает конфликты Git
- **Устанавливай тайм‑ауты** для одноразового режима — сложные задачи могут занимать 5‑10 минут
- **Используй `hermes chat -q` для fire‑and‑forget** — PTY не требуется
- **Применяй `tmux` для интерактивных сессий** — в режиме raw PTY возникают проблемы `\r` vs `\n` с `prompt_toolkit`
- **Для запланированных задач** используй инструмент `cronjob` вместо запуска процесса — он обрабатывает доставку и повторные попытки
## Durable & Background Systems

Четыре системы работают параллельно с основным циклом диалога. Быстрый справочник
здесь; полные примечания для разработчиков находятся в `AGENTS.md`, пользовательская документация — в `website/docs/user‑guide/features/`.

### Делегирование (`delegate_task`)

Синхронный запуск под‑агента — родитель ждёт сводку от дочернего процесса,
прежде чем продолжить свой цикл. Изолированный контекст + терминальная сессия.

- **Один:** `delegate_task(goal, context, toolsets)`.
- **Пакет:** `delegate_task(tasks=[{goal, ...}, ...])` запускает дочерние задачи
  параллельно, ограничивая их числом `delegation.max_concurrent_children`
  (по умолчанию 3).
- **Роли:** `leaf` (по умолчанию; не может делегировать дальше) vs `orchestrator`
  (может порождать собственных работников, ограничено `delegation.max_spawn_depth`).
- **Не долговременно.** Если родитель прерывается, дочерняя задача отменяется.
  Для работы, которая должна пережить текущий ход, используй `cronjob` или
  `terminal(background=True, notify_on_complete=True)`.

Конфигурация: `delegation.*` в `config.yaml`.

### Cron (планировщик задач)

Долговременный планировщик — `cron/jobs.py` + `cron/scheduler.py`. Управляй им
через инструмент `cronjob`, CLI `hermes cron` (`list`, `add`, `edit`,
`pause`, `resume`, `run`, `remove`) или слеш‑команду `/cron`.

- **Расписания:** длительность (`"30m"`, `"2h"`), фраза «every»
  (`"every monday 9am"`), 5‑поле cron (`"0 9 * * *"`), либо ISO‑метка времени.
- **Параметры каждой задачи:** `skills`, переопределение `model`/`provider`,
  `script` (сбор данных перед запуском; `no_agent=True` делает скрипт всей задачей),
  `context_from` (передаёт вывод задачи A в задачу B), `workdir`
  (запуск в указанном каталоге с загруженными `AGENTS.md` / `CLAUDE.md`),
  доставка на несколько платформ.
- **Инварианты:** жёсткое прерывание через 3 минуты для каждой задачи,
  файл `.tick.lock` предотвращает дублирование тик‑сигналов между процессами,
  cron‑сессии по умолчанию используют `skip_memory=True`,
  а результаты cron‑задач обрамляются заголовком/подвалом вместо зеркалирования
  в целевую сессию шлюза (сохраняет чередование ролей).

Документация для пользователей: https://hermes-agent.nousresearch.com/docs/user-guide/features/cron

### Curator (жизненный цикл skill)

Фоновое обслуживание skill, созданных агентом. Отслеживает использование,
помечает неактивные skill как устаревшие, архивирует их и сохраняет
резервную tar.gz‑копию, чтобы ничего не потерять.

- **CLI:** `hermes curator <verb>` — `status`, `run`, `pause`, `resume`,
  `pin`, `unpin`, `archive`, `restore`, `prune`, `backup`, `rollback`.
- **Slash:** `/curator <subcommand>` дублирует CLI.
- **Объём:** затрагивает только skill с provenance `created_by: "agent"`.
  Встроенные и установленные из хаба skill недоступны. **Никогда не удаляет** —
  максимальное разрушительное действие — архивирование. Закреплённые skill
  исключены из всех автоматических переходов и проверок LLM.
- **Телеметрия:** вспомогательный файл `~/.hermes/skills/.usage.json` хранит
  для каждой skill `use_count`, `view_count`, `patch_count`,
  `last_activity_at`, `state`, `pinned`.

Конфигурация: `curator.*` (`enabled`, `interval_hours`, `min_idle_hours`,
`stale_after_days`, `archive_after_days`, `backup.*`).

Документация для пользователей: https://hermes-agent.nousresearch.com/docs/user-guide/features/curator

### Kanban (очередь задач для нескольких агентов)

Долговременная SQLite‑доска для совместной работы нескольких профилей/рабочих.
Пользователи управляют ею через `hermes kanban <verb>`; работники,
созданные диспетчером, видят специализированный набор инструментов `kanban_*`,
ограниченный переменной `HERMES_KANBAN_TASK`, а профили‑оркестраторы могут
подключить более широкий набор `kanban`. Обычные сессии не оставляют следов
схемы `kanban_*`, если не настроено иначе.

- **CLI‑глаголы (часто):** `init`, `create`, `list` (синоним `ls`),
  `show`, `assign`, `link`, `unlink`, `comment`, `complete`, `block`,
  `unblock`, `archive`, `tail`. Менее часто: `watch`, `stats`, `runs`,
  `log`, `dispatch`, `daemon`, `gc`.
- **Набор инструментов для worker/оркестратора:** `kanban_show`, `kanban_complete`,
  `kanban_block`, `kanban_heartbeat`, `kanban_comment`, `kanban_create`,
  `kanban_link`; профили, явно включившие набор `kanban` вне задачи,
  запущенной диспетчером, также получают `kanban_list` и `kanban_unblock`
  для маршрутизации по доске.
- **Диспетчер** по умолчанию работает внутри шлюза
  (`kanban.dispatch_in_gateway: true`) — восстанавливает устаревшие заявки,
  продвигает готовые задачи, атомарно захватывает их и запускает назначенные
  профили. Автоматически блокирует задачу после `failure_limit` последовательных
  неудач запуска (по умолчанию 2; настраивается через `kanban.failure_limit` или
  параметр задачи `max_retries`).
- **Изоляция:** доска — жёсткая граница (workers получают переменную
  `HERMES_KANBAN_BOARD` в окружении); tenant — мягкое пространство имён
  внутри доски для изоляции пути рабочего пространства и ключей памяти.

Документация для пользователей: https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban
## Специфические особенности Windows

Hermes работает нативно в Windows (PowerShell, cmd, Windows Terminal, git‑bash mintty, встроенный терминал VS Code). Большинство функций просто работают, но несколько различий между Win32 и POSIX уже доставили нам проблемы — фиксируй новые здесь, как только встретишь, чтобы следующий человек (или следующая сессия) не открывал их заново.

### Ввод / Клавиатурные привязки

**Alt+Enter не вставляет перевод строки.** Windows Terminal перехватывает Alt+Enter на уровне терминала, чтобы переключить полноэкранный режим — нажатие никогда не достигает `prompt_toolkit`. Вместо этого используй **Ctrl+Enter**. Windows Terminal передаёт `Ctrl+Enter` как LF (`c-j`), отличая его от обычного Enter (`c-m` / CR), и CLI привязывает `c-j` к вставке новой строки только на `win32` (см. `_bind_prompt_submit_keys` + привязку `c-j`, специфичную для Windows, в `cli.py`).
Побочный эффект: сырая клавиша `Ctrl+J` также вставляет новую строку в Windows — неизбежно, потому что Windows Terminal сводит `Ctrl+Enter` и `Ctrl+J` к одному коду клавиши на уровне Win32 console API. Конфликтующей привязки для `Ctrl+J` в Windows не было, поэтому это безвредный побочный эффект.

mintty / git‑bash ведут себя так же (полноэкранный режим по Alt+Enter), если только не отключить сочетания Alt+Fn в **Options → Keys**. Проще просто использовать `Ctrl+Enter`.

**Диагностика привязок.** Запусти `python scripts/keystroke_diagnostic.py` (корень репозитория), чтобы точно увидеть, как `prompt_toolkit` определяет каждое нажатие клавиши в текущем терминале. Это отвечает на вопросы вроде «передаётся ли `Shift+Enter` как отдельный ключ?» (почти никогда — большинство терминалов сводят его к обычному Enter) или «какая последовательность байтов посылает мой терминал для `Ctrl+Enter`?» — так был установлен факт `Ctrl+Enter = c-j`.

### Конфигурация / Файлы

**HTTP 400 «No models provided» при первом запуске.** `config.yaml` был сохранён с BOM UTF‑8 (часто происходит, когда Windows‑приложения пишут файл). Пересохрани его как UTF‑8 без BOM. `hermes config edit` сохраняет без BOM; ручные правки в Notepad обычно являются причиной.

### `execute_code` / Песочница

**WinError 10106** («Запрошенный поставщик услуг не может быть загружен или инициализирован») от дочернего процесса песочницы — он не может создать сокет `AF_INET`, поэтому запасный (вариант) RPC по loopback‑TCP падает до `connect()`. Корень проблемы обычно **не** в сломанном Winsock LSP; это очистка окружения Hermes, которая удаляет `SYSTEMROOT` / `WINDIR` / `COMSPEC` из окружения дочернего процесса. Модулю `socket` в Python нужен `SYSTEMROOT`, чтобы найти `mswsock.dll`. Исправлено через allowlist `_WINDOWS_ESSENTIAL_ENV_VARS` в `tools/code_execution_tool.py`. Если ошибка всё ещё возникает, выведи `os.environ` внутри блока `execute_code`, чтобы убедиться, что `SYSTEMROOT` установлен. Полный рецепт диагностики в `references/execute-code-sandbox-env-windows.md`.

### Тестирование / Вклад

**`scripts/run_tests.sh` не работает «как есть» в Windows** — он ищет POSIX‑структуру venv (`.venv/bin/activate`). Установленный Hermes‑venv в `venv/Scripts/` не содержит pip или pytest (удалено для уменьшения размера установки). Обходной путь: установи `pytest + pytest-xdist + pyyaml` в системный Python 3.11 пользовательский сайт, затем запусти pytest напрямую, задав `PYTHONPATH`:

```bash
"/c/Program Files/Python311/python" -m pip install --user pytest pytest-xdist pyyaml
export PYTHONPATH="$(pwd)"
"/c/Program Files/Python311/python" -m pytest tests/foo/test_bar.py -v --tb=short -n 0
```

Используй `-n 0`, а не `-n 4` — в `pyproject.toml` уже указаны `addopts`, включающие `-n`, и гарантии CI‑паритета обёртки не применимы вне POSIX.

**Тесты, предназначенные только для POSIX, нуждаются в пропусках.** Общие маркеры уже присутствуют в кодовой базе:
- Символические ссылки — требуют повышенных привилегий в Windows
- Режимы файлов `0o600` — биты режима POSIX по умолчанию не принудительно применяются в NTFS
- `signal.SIGALRM` — только Unix (см. `tests/conftest.py::_enforce_test_timeout`)
- Winsock / специфичные для Windows регрессии — `@pytest.mark.skipif(sys.platform != "win32", ...)`

Применяй существующий стиль пропусков (`sys.platform == "win32"` или `sys.platform.startswith("win")`), чтобы оставаться согласованным с остальной частью набора.

### Путь / Файловая система

**Концы строк.** Git может предупредить `LF will be replaced by CRLF the next time Git touches it`. Это косметика — `.gitattributes` репозитория нормализует их. Не позволяй редакторам автоматически конвертировать файлы с POSIX‑переводами строк в CRLF.

**Прямые слеши работают почти везде.** `C:/Users/...` принимается всеми инструментами Hermes и большинством Windows‑API. Предпочитай прямые слеши в коде и логах — так избегаются экранирования обратных слешей в bash.
## Устранение неполадок

### Voice not working
1. Проверь `stt.enabled: true` в `config.yaml`.
2. Убедись, что установлен провайдер: `pip install faster-whisper` или укажи API‑ключ.
3. В шлюзе: `/restart`. В CLI: выйди и запусти заново.

### Tool not available
1. `hermes tools` — проверь, включён ли **toolset** для твоей платформы.
2. Некоторые инструменты требуют переменных окружения (проверь `.env`).
3. Выполни `/reset` после включения инструментов.

### Model/provider issues
1. `hermes doctor` — проверь конфигурацию и зависимости.
2. `hermes auth` — повторно аутентифицируй OAuth‑провайдеров (или `hermes auth add <provider>`).
3. Убедись, что в `.env` указан правильный API‑ключ.
4. **Copilot 403**: токены `gh auth login` НЕ работают с API Copilot. Нужно использовать OAuth‑поток устройства, специфичный для Copilot, через `hermes model` → GitHub Copilot.

### Changes not taking effect
- **Tools/skills**: `/reset` запускает новую **session** с обновлённым **toolset**.
- **Config changes**: в шлюзе — `/restart`. В CLI — выйди и запусти заново.
- **Code changes**: перезапусти процесс CLI или шлюза.

### Skills not showing
1. `hermes skills list` — проверь, установлены ли они.
2. `hermes skills config` — проверь включённость платформы.
3. Явно загрузить: `/skill name` или `hermes -s name`.

### Gateway issues
Сначала проверь логи:
```bash
grep -i "failed to send\|error" ~/.hermes/logs/gateway.log | tail -20
```

Распространённые проблемы шлюза:
- **Gateway dies on SSH logout**: включи linger: `sudo loginctl enable-linger $USER`.
- **Gateway dies on WSL2 close**: WSL2 требует `systemd=true` в `/etc/wsl.conf` для работы systemd‑служб. Без этого шлюз переходит к `nohup` (падает при закрытии сессии).
- **Gateway crash loop**: сбрось ошибочное состояние: `systemctl --user reset-failed hermes-gateway`.

### Platform-specific issues
- **Discord bot silent**: необходимо включить **Message Content Intent** в Bot → Privileged Gateway Intents.
- **Slack bot only works in DMs**: необходимо подписаться на событие `message.channels`. Без этого бот игнорирует публичные каналы.
- **Windows-specific issues** (`Alt+Enter` newline, WinError 10106, UTF‑8 BOM config, test suite, line endings): смотри раздел **Windows‑Specific Quirks** выше.

### Auxiliary models not working
Если задачи `auxiliary` (vision, compression, session_search) завершаются молча, провайдер `auto` не может найти бекенд. Установи `OPENROUTER_API_KEY` или `GOOGLE_API_KEY`, либо явно укажи провайдера для каждой вспомогательной задачи:
```bash
hermes config set auxiliary.vision.provider <your_provider>
hermes config set auxiliary.vision.model <model_name>
```
## Где найти нужное

| Что ищем | Где находится |
|----------------|----------|
| Параметры конфигурации | `hermes config edit` или [Документация конфигурации](https://hermes-agent.nousresearch.com/docs/user-guide/configuration) |
| Доступные инструменты | `hermes tools list` или [Справочник по инструментам](https://hermes-agent.nousresearch.com/docs/reference/tools-reference) |
| Слеш‑команды | `/help` в сессии или [Справочник по слеш‑командам](https://hermes-agent.nousresearch.com/docs/reference/slash-commands) |
| Каталог навыков | `hermes skills browse` или [Каталог навыков](https://hermes-agent.nousresearch.com/docs/reference/skills-catalog) |
| Настройка провайдера | `hermes model` или [Руководство по провайдерам](https://hermes-agent.nousresearch.com/docs/integrations/providers) |
| Настройка платформы | `hermes gateway setup` или [Документация по обмену сообщениями](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/) |
| Серверы MCP | `hermes mcp list` или [Руководство по MCP](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp) |
| Профили | `hermes profile list` или [Документация по профилям](https://hermes-agent.nousresearch.com/docs/user-guide/profiles) |
| Cron‑задачи | `hermes cron list` или [Документация по Cron](https://hermes-agent.nousresearch.com/docs/user-guide/features/cron) |
| Память | `hermes memory status` или [Документация по памяти](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory) |
| Переменные окружения | `hermes config env-path` или [Справочник по переменным окружения](https://hermes-agent.nousresearch.com/docs/reference/environment-variables) |
| Команды CLI | `hermes --help` или [Справочник по CLI](https://hermes-agent.nousresearch.com/docs/reference/cli-commands) |
| Логи шлюза | `~/.hermes/logs/gateway.log` |
| Файлы сессий | `hermes sessions browse` (чтение `state.db`) |
| Исходный код | `~/.hermes/hermes-agent/` |

---
## Быстрый справочник для контрибьюторов

Для случайных контрибьюторов и авторов PR. Полная документация для разработчиков: https://hermes-agent.nousresearch.com/docs/developer-guide/

### Структура проекта

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

Конфиг: `~/.hermes/config.yaml` (настройки), `~/.hermes/.env` (API‑ключи).

### Добавление инструмента (3 файла)

**1. Создай `tools/your_tool.py`:**
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

**2. Добавь в `toolsets.py`** → список `_HERMES_CORE_TOOLS`.

Автообнаружение: любой файл `tools/*.py` с вызовом `registry.register()` на верхнем уровне импортируется автоматически — ручной список не нужен.

Все обработчики должны возвращать строки JSON. Используй `get_hermes_home()` для путей, никогда не хардкодь `~/.hermes`.

### Добавление slash‑команды

1. Добавь `CommandDef` в `COMMAND_REGISTRY` в `hermes_cli/commands.py`
2. Добавь обработчик в `cli.py` → `process_command()`
3. (Опционально) Добавь обработчик шлюза в `gateway/run.py`

Все потребители (текст помощи, автодополнение, меню Telegram, сопоставление Slack) автоматически берут данные из центрального реестра.

### Цикл агента (уровень выше)

```
run_conversation():
  1. Build system prompt
  2. Loop while iterations < max:
     a. Call LLM (OpenAI-format messages + tool schemas)
     b. If tool_calls → dispatch each via handle_function_call() → append results → continue
     c. If text response → return
  3. Context compression triggers automatically near token limit
```

### Тестирование

```bash
python -m pytest tests/ -o 'addopts=' -q   # Full suite
python -m pytest tests/tools/ -q            # Specific area
```

- Тесты автоматически перенаправляют `HERMES_HOME` во временные каталоги — никогда не трогай реальный `~/.hermes/`.
- Запусти полный набор тестов перед отправкой изменений.
- Используй `-o 'addopts='`, чтобы очистить любые встроенные флаги pytest.

**Контрибьюторы Windows:** `scripts/run_tests.sh` сейчас ищет POSIX‑окружения (`.venv/bin/activate` / `venv/bin/activate`) и выдаст ошибку на Windows, где структура — `venv/Scripts/activate` + `python.exe`. В установленном Hermes‑окружении в `venv/Scripts/` также нет `pip` или `pytest` — они удалены для уменьшения размера установки. Обходной путь: установи `pytest`, `pytest-xdist` и `pyyaml` в системный Python 3.11 пользовательский сайт (`/c/Program Files/Python311/python -m pip install --user pytest pytest-xdist pyyaml`), затем запусти тесты напрямую:

```bash
export PYTHONPATH="$(pwd)"
"/c/Program Files/Python311/python" -m pytest tests/tools/test_foo.py -v --tb=short -n 0
```

Используй `-n 0` (а не `-n 4`), потому что в `pyproject.toml` уже указано `addopts` с `-n`, и история CI‑паритета обёртки не применяется вне POSIX.

**Кроссплатформенные guard‑тесты:** тесты, использующие только POSIX‑системные вызовы, нуждаются в маркере пропуска. Общие примеры уже в кодовой базе:
- Создание симлинков → `@pytest.mark.skipif(sys.platform == "win32", reason="Symlinks require elevated privileges on Windows")` (см. `tests/cron/test_cron_script.py`)
- POSIX‑права файлов (0o600 и др.) → `@pytest.mark.skipif(sys.platform.startswith("win"), reason="POSIX mode bits not enforced on Windows")` (см. `tests/hermes_cli/test_auth_toctou_file_modes.py`)
- `signal.SIGALRM` → только Unix (см. `tests/conftest.py::_enforce_test_timeout`)
- Живые Winsock / Windows‑специфичные регрессионные тесты → `@pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific regression")`

**Monkeypatching `sys.platform` недостаточно**, когда тестируемый код также вызывает `platform.system()` / `platform.release()` / `platform.mac_ver()`. Эти функции читают реальную ОС независимо, поэтому тест, который устанавливает `sys.platform = "linux"` на Windows‑раннере, всё равно увидит `platform.system() == "Windows"` и пойдёт по ветке Windows. Патчьте все три вместе:

```python
monkeypatch.setattr(sys, "platform", "linux")
monkeypatch.setattr(platform, "system", lambda: "Linux")
monkeypatch.setattr(platform, "release", lambda: "6.8.0-generic")
```

См. `tests/agent/test_prompt_builder.py::TestEnvironmentHints` для примера.

### Расширение блока execution‑environment в системном промпте

Фактическая информация о хост‑ОС, домашней директории пользователя, текущем рабочем каталоге, бекэнде терминала и оболочке (bash vs. PowerShell на Windows) генерируется в `agent/prompt_builder.py::build_environment_hints()`. Здесь же находится логика подсказки WSL и проверки бекэнда. Конвенция:

- **Локальный бекэнд терминала** → выводит информацию о хосте (OS, `$HOME`, cwd) + Windows‑специфичные заметки (hostname ≠ username, `terminal` использует bash, а не PowerShell).
- **Удалённый бекэнд терминала** (любой из `_REMOTE_TERMINAL_BACKENDS`: `docker, singularity, modal, daytona, ssh, managed_modal`) → **полностью подавляет** информацию о хосте и описывает только бекэнд. Живой проб `uname`/`whoami`/`pwd` запускается внутри бекэнда через `tools.environments.get_environment(...).execute(...)`, кэшируется на процесс в `_BACKEND_PROBE_CACHE`, с статическим запасным вариантом на случай таймаута.
- **Ключевой факт для написания промптов:** когда `TERMINAL_ENV != "local"`, *каждый* файловый инструмент (`read_file`, `write_file`, `patch`, `search_files`) работает внутри контейнера бекэнда, а не на хосте. Системный промпт никогда не должен описывать хост в этом случае — агент не может к нему обращаться.

Полные заметки по дизайну, точные строки вывода и подводные камни тестирования: `references/prompt-builder-environment-hints.md`.

**Шаблон безопасного рефакторинга (POSIX‑эквивалентность):** когда вы выносите инлайн‑логику в вспомогательную функцию, добавляющую Windows/платформо‑специфическое поведение, оставьте в тестовом файле функцию‑оракул `_legacy_<name>`, содержащую дословную копию старого кода, и параметризуйте сравнение с ней. Пример: `tests/tools/test_code_execution_windows_env.py::TestPosixEquivalence`. Это фиксирует инвариант, что POSIX‑поведение идентично побитово, и любые отклонения будут явно видны.

### Конвенции коммитов

```
type: concise subject line

Optional body.
```

Типы: `fix:`, `feat:`, `refactor:`, `docs:`, `chore:`

### Ключевые правила

- **Никогда не ломай кэширование промпта** — не меняй контекст, инструменты или системный промпт в середине диалога.
- **Чередование ролей сообщений** — никогда не должно быть двух сообщений от ассистента или двух от пользователя подряд.
- Используй `get_hermes_home()` из `hermes_constants` для всех путей (безопасно для профилей).
- Значения конфигурации помещай в `config.yaml`, секреты — в `.env`.
- Новым инструментам нужен `check_fn`, чтобы они появлялись только при выполнении требований.