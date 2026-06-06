---
sidebar_position: 10
title: "Мігрувати з OpenClaw"
description: "Повний посібник з перенесення налаштувань OpenClaw / Clawdbot на Hermes Agent — що переноситься, як налаштовуються мапи конфігурації та що перевіряти після цього."
---

# Міграція з OpenClaw

`hermes claw migrate` імпортує твою установку OpenClaw (або застарілого Clawdbot/Moldbot) у Hermes. У цьому посібнику розглядаються саме те, що переноситься, відповідність ключів конфігурації та що треба перевірити після міграції.

:::tip
Якщо твоя установка OpenClaw була багатопровайдерною, `hermes setup --portal` зводить її до одного OAuth — 300+ моделей плюс шлюз інструментів в одному логіні. Дивись [Nous Portal](/integrations/nous-portal).
:::
## Швидкий старт

```bash
# Preview then migrate (always shows a preview first, then asks to confirm)
hermes claw migrate

# Preview only, no changes
hermes claw migrate --dry-run

# Full migration including API keys, skip confirmation
hermes claw migrate --preset full --migrate-secrets --yes
```

Міграція завжди показує повний попередній перегляд того, що буде імпортовано, перед внесенням будь‑яких змін. Переглянь список, а потім підтвердь, щоб продовжити.

За замовчуванням читає з `~/.openclaw/`. Директорії старих версій `~/.clawdbot/` або `~/.moltbot/` виявляються автоматично. Те ж саме стосується старих імен файлів конфігурації (`clawdbot.json`, `moltbot.json`).
## Опції

| Опція | Опис |
|--------|-------------|
| `--dry-run` | Тільки попередній перегляд — зупинитися після показу того, що буде перенесено. |
| `--preset <name>` | `full` (всі сумісні налаштування) або `user-data` (виключає конфігурацію інфраструктури). Жоден preset не імпортує секрети за замовчуванням — передай `--migrate-secrets` явно. |
| `--overwrite` | Перезаписати існуючі файли Hermes при конфліктах (за замовчуванням: відмовитися застосовувати, коли план має конфлікти). |
| `--migrate-secrets` | Включити API‑ключі. Потрібно навіть при `--preset full` — жоден preset не імпортує секрети без явного зазначення. |
| `--no-backup` | Пропустити створення zip‑знімка `~/.hermes/` перед міграцією (за замовчуванням перед застосуванням створюється архів відновлення у `~/.hermes/backups/pre-migration-*.zip`; його можна відновити за допомогою `hermes import`). |
| `--source <path>` | Користувацька директорія OpenClaw. |
| `--workspace-target <path>` | Куди розмістити `AGENTS.md`. |
| `--skill-conflict <mode>` | `skip` (за замовчуванням), `overwrite` або `rename`. |
| `--yes` | Пропустити запит підтвердження після попереднього перегляду. |
## Що переноситься
### Персона, пам'ять і інструкції

| Що | Джерело OpenClaw | Призначення Hermes | Примітки |
|------|----------------|-------------------|-------|
| Персона | `workspace/SOUL.md` | `~/.hermes/SOUL.md` | Пряме копіювання |
| Інструкції робочого простору | `workspace/AGENTS.md` | `AGENTS.md` у `--workspace-target` | Потрібен прапорець `--workspace-target` |
| Довгострокова пам'ять | `workspace/MEMORY.md` | `~/.hermes/memories/MEMORY.md` | Розбирається на записи, об’єднується з існуючими, видаляються дублікати. Використовується розділювач `§`. |
| Профіль користувача | `workspace/USER.md` | `~/.hermes/memories/USER.md` | Така ж логіка об’єднання записів, як і для пам'яті. |
| Щоденні файли пам'яті | `workspace/memory/*.md` | `~/.hermes/memories/MEMORY.md` | Усі щоденні файли об’єднуються в основну пам'ять. |

Файли робочого простору також перевіряються в `workspace.default/` та `workspace-main/` як запасні шляхи (OpenClaw перейменував `workspace/` у `workspace-main/` у останніх версіях і використовує `workspace-{agentId}` для налаштувань з кількома агентами).
### Навички (4 джерела)

| Джерело | Розташування OpenClaw | Призначення Hermes |
|--------|----------------------|--------------------|
| Навички робочого простору | `workspace/skills/` | `~/.hermes/skills/openclaw-imports/` |
| Керовані/спільні навички | `~/.openclaw/skills/` | `~/.hermes/skills/openclaw-imports/` |
| Особисті міжпроєктні навички | `~/.agents/skills/` | `~/.hermes/skills/openclaw-imports/` |
| Спільні на рівні проєкту | `workspace/.agents/skills/` | `~/.hermes/skills/openclaw-imports/` |

Конфлікти навичок обробляються за допомогою `--skill-conflict`: `skip` залишає існуючу навичку Hermes, `overwrite` замінює її, `rename` створює копію з суфіксом `-imported`.
### Конфігурація моделі та провайдера

| Що | Шлях конфігурації OpenClaw | Призначення Hermes | Примітки |
|------|---------------------|-------------------|-------|
| Модель за замовчуванням | `agents.defaults.model` | `config.yaml` → `model` | Може бути рядком або об’єктом `{primary, fallbacks}` |
| Користувацькі провайдери | `models.providers.*` | `config.yaml` → `custom_providers` | Відображає `baseUrl`, `apiType`/`api` — підтримує як короткі ("openai", "anthropic"), так і дефісні ("openai-completions", "anthropic-messages", "google-generative-ai") значення |
| API‑ключі провайдера | `models.providers.*.apiKey` | `~/.hermes/.env` | Потрібно `--migrate-secrets`. Дивись [розв’язання API‑ключа](#api-key-resolution) нижче. |
### Поведінка агента

| Що | Шлях конфігурації OpenClaw | Шлях конфігурації Hermes | Відповідність |
|------|---------------------------|--------------------------|---------------|
| Max turns | `agents.defaults.timeoutSeconds` | `agent.max_turns` | `timeoutSeconds / 10`, обмежено 200 |
| Verbose mode | `agents.defaults.verboseDefault` | `agent.verbose` | "off" / "on" / "full" |
| Reasoning effort | `agents.defaults.thinkingDefault` | `agent.reasoning_effort` | "always"/"high"/"xhigh" → "high", "auto"/"medium"/"adaptive" → "medium", "off"/"low"/"none"/"minimal" → "low" |
| Compression | `agents.defaults.compaction.mode` | `compression.enabled` | "off" → false, будь‑що інше → true |
| Compression model | `agents.defaults.compaction.model` | `compression.summary_model` | Пряме копіювання рядка |
| Human delay | `agents.defaults.humanDelay.mode` | `human_delay.mode` | "natural" / "custom" / "off" |
| Human delay timing | `agents.defaults.humanDelay.minMs` / `.maxMs` | `human_delay.min_ms` / `.max_ms` | Пряме копіювання |
| Timezone | `agents.defaults.userTimezone` | `timezone` | Пряме копіювання рядка |
| Exec timeout | `tools.exec.timeoutSec` | `terminal.timeout` | Пряме копіювання (поле `timeoutSec`, а не `timeout`) |
| Docker sandbox | `agents.defaults.sandbox.backend` | `terminal.backend` | "docker" → "docker" |
| Docker image | `agents.defaults.sandbox.docker.image` | `terminal.docker_image` | Пряме копіювання |
### Політики скидання сесії

| Шлях конфігурації OpenClaw | Шлях конфігурації Hermes | Примітки |
|----------------------------|--------------------------|----------|
| `session.reset.mode` | `session_reset.mode` | "daily", "idle" або обидва |
| `session.reset.atHour` | `session_reset.at_hour` | Година (0–23) для щоденного скидання |
| `session.reset.idleMinutes` | `session_reset.idle_minutes` | Хвилини бездіяльності |

Примітка: у OpenClaw також є `session.resetTriggers` (простий масив рядків типу `["daily", "idle"]`). Якщо структурований `session.reset` відсутній, міграція переходить до визначення з `resetTriggers`.
### MCP сервери

| OpenClaw field | Hermes field | Примітки |
|----------------|--------------|----------|
| `mcp.servers.*.command` | `mcp_servers.*.command` | Stdio transport |
| `mcp.servers.*.args` | `mcp_servers.*.args` | |
| `mcp.servers.*.env` | `mcp_servers.*.env` | |
| `mcp.servers.*.cwd` | `mcp_servers.*.cwd` | |
| `mcp.servers.*.url` | `mcp_servers.*.url` | HTTP/SSE transport |
| `mcp.servers.*.tools.include` | `mcp_servers.*.tools.include` | Tool filtering |
| `mcp.servers.*.tools.exclude` | `mcp_servers.*.tools.exclude` | |
### TTS (text-to-speech)

Налаштування TTS читаються з **двох** місць конфігурації OpenClaw з таким пріоритетом:

1. `messages.tts.providers.{provider}.*` (канонічне розташування)
2. `talk.providers.{provider}.*` на верхньому рівні (запасний (варіант))
3. Застарілі плоскі ключі `messages.tts.{provider}.*` (найстаріший формат)

| Що | Призначення Hermes |
|------|-------------------|
| Назва провайдера | `config.yaml` → `tts.provider` |
| ElevenLabs voice ID | `config.yaml` → `tts.elevenlabs.voice_id` |
| ElevenLabs model ID | `config.yaml` → `tts.elevenlabs.model_id` |
| OpenAI model | `config.yaml` → `tts.openai.model` |
| OpenAI voice | `config.yaml` → `tts.openai.voice` |
| Edge TTS voice | `config.yaml` → `tts.edge.voice` (OpenClaw перейменував «edge» на «microsoft» — обидва розпізнаються) |
| TTS assets | `~/.hermes/tts/` (копіювання файлів) |
### Платформи обміну повідомленнями

| Платформа | Шлях конфігурації OpenClaw | Змінна Hermes `.env` | Примітки |
|----------|---------------------------|----------------------|----------|
| Telegram | `channels.telegram.botToken` або `.accounts.default.botToken` | `TELEGRAM_BOT_TOKEN` | Токен може бути рядком або [SecretRef](#secretref-handling). Підтримуються як плоска, так і структура `accounts`. |
| Telegram | `credentials/telegram-default-allowFrom.json` | `TELEGRAM_ALLOWED_USERS` | Кома‑розділений список з масиву `allowFrom[]` |
| Discord | `channels.discord.token` або `.accounts.default.token` | `DISCORD_BOT_TOKEN` | |
| Discord | `channels.discord.allowFrom` або `.accounts.default.allowFrom` | `DISCORD_ALLOWED_USERS` | |
| Slack | `channels.slack.botToken` або `.accounts.default.botToken` | `SLACK_BOT_TOKEN` | |
| Slack | `channels.slack.appToken` або `.accounts.default.appToken` | `SLACK_APP_TOKEN` | |
| Slack | `channels.slack.allowFrom` або `.accounts.default.allowFrom` | `SLACK_ALLOWED_USERS` | |
| WhatsApp | `channels.whatsapp.allowFrom` або `.accounts.default.allowFrom` | `WHATSAPP_ALLOWED_USERS` | Авторизація через Baileys QR‑пару — потребує повторного спарювання після міграції |
| Signal | `channels.signal.account` або `.accounts.default.account` | `SIGNAL_ACCOUNT` | |
| Signal | `channels.signal.httpUrl` або `.accounts.default.httpUrl` | `SIGNAL_HTTP_URL` | |
| Signal | `channels.signal.allowFrom` або `.accounts.default.allowFrom` | `SIGNAL_ALLOWED_USERS` | |
| Matrix | `channels.matrix.accessToken` або `.accounts.default.accessToken` | `MATRIX_ACCESS_TOKEN` | Використовує `accessToken` (не `botToken`) |
| Mattermost | `channels.mattermost.botToken` або `.accounts.default.botToken` | `MATTERMOST_BOT_TOKEN` | |
### Інша конфігурація

| Що | Шлях OpenClaw | Шлях Hermes | Примітки |
|------|-------------|-------------|-------|
| Режим схвалення | `approvals.exec.mode` | `config.yaml` → `approvals.mode` | "auto"→"off", "always"→"manual", "smart"→"smart" |
| Білий список команд | `exec-approvals.json` | `config.yaml` → `command_allowlist` | Шаблони об’єднані та видалено дублікати |
| URL CDP браузера | `browser.cdpUrl` | `config.yaml` → `browser.cdp_url` | |
| Безголовий режим браузера | `browser.headless` | `config.yaml` → `browser.headless` | |
| Ключ пошуку Brave | `tools.web.search.brave.apiKey` | `.env` → `BRAVE_API_KEY` | Потрібно `--migrate-secrets` |
| Токен автентифікації шлюзу | `gateway.auth.token` | `.env` → `HERMES_GATEWAY_TOKEN` | Потрібно `--migrate-secrets` |
| Робочий каталог | `agents.defaults.workspace` | `.env` → `MESSAGING_CWD` | |
### Архівовано (немає прямого еквіваленту Hermes)

Ці файли зберігаються у `~/.hermes/migration/openclaw/<timestamp>/archive/` для ручного перегляду:

| Що | Файл архіву | Як відтворити в Hermes |
|------|-------------|--------------------------|
| `IDENTITY.md` | `archive/workspace/IDENTITY.md` | Об’єднати в `SOUL.md` |
| `TOOLS.md` | `archive/workspace/TOOLS.md` | Hermes має вбудовані інструкції інструментів |
| `HEARTBEAT.md` | `archive/workspace/HEARTBEAT.md` | Використовувати cron‑завдання для періодичних задач |
| `BOOTSTRAP.md` | `archive/workspace/BOOTSTRAP.md` | Використовувати файли контексту або skills |
| Cron jobs | `archive/cron-config.json` | Відтворити за допомогою `hermes cron create` |
| Plugins | `archive/plugins-config.json` | Дивись [plugins guide](/user-guide/features/hooks) |
| Hooks/webhooks | `archive/hooks-config.json` | Використовувати `hermes webhook` або gateway hooks |
| Memory backend | `archive/memory-backend-config.json` | Налаштувати через `hermes honcho` |
| Skills registry | `archive/skills-registry-config.json` | Використовувати `hermes skills config` |
| UI/identity | `archive/ui-identity-config.json` | Використовувати команду `/skin` |
| Logging | `archive/logging-diagnostics-config.json` | Встановити у розділі `logging` файлу `config.yaml` |
| Multi-agent list | `archive/agents-list.json` | Використовувати профілі Hermes |
| Channel bindings | `archive/bindings.json` | Ручне налаштування для кожної платформи |
| Complex channels | `archive/channels-deep-config.json` | Ручна конфігурація платформи |
## Розв’язання API‑ключів

Коли ввімкнено `--migrate-secrets`, API‑ключі збираються з **чотирьох джерел** у порядку пріоритету:

1. **Значення конфігурації** — `models.providers.*.apiKey` та ключі TTS‑провайдерів у `openclaw.json`
2. **Файл середовища** — `~/.openclaw/.env` (ключі типу `OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY` тощо)
3. **Підоб’єкт `env` у конфігурації** — `openclaw.json` → `"env"` або `"env"."vars"` (деякі налаштування зберігають ключі тут замість окремого `.env`‑файлу)
4. **Профілі автентифікації** — `~/.openclaw/agents/main/agent/auth-profiles.json` (облікові дані для кожного агента)

Значення конфігурації мають найвищий пріоритет. Кожне наступне джерело заповнює залишкові прогалини.

### Підтримувані цілі ключів

`OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `DEEPSEEK_API_KEY`, `GEMINI_API_KEY`, `ZAI_API_KEY`, `MINIMAX_API_KEY`, `ELEVENLABS_API_KEY`, `TELEGRAM_BOT_TOKEN`, `VOICE_TOOLS_OPENAI_KEY`

Ключі, яких немає у цьому дозволеному списку, ніколи не копіюються.
## Обробка SecretRef

Значення конфігурації OpenClaw для токенів та API‑ключів можуть бути у трьох форматах:

```json
// Plain string
"channels": { "telegram": { "botToken": "123456:ABC-DEF..." } }

// Environment template
"channels": { "telegram": { "botToken": "${TELEGRAM_BOT_TOKEN}" } }

// SecretRef object
"channels": { "telegram": { "botToken": { "source": "env", "id": "TELEGRAM_BOT_TOKEN" } } }
```

Міграція розв’язує всі три формати. Для шаблонів середовища та об’єктів SecretRef з `source: "env"` вона шукає значення у `~/.openclaw/.env` та у підоб’єкті `env` у файлі `openclaw.json`. Об’єкти SecretRef з `source: "file"` або `source: "exec"` не можуть бути розв’язані автоматично — міграція попереджає про це, і ці значення потрібно додати до Hermes вручну за допомогою `hermes config set`.
## Після міграції

1. **Перевір звіт про міграцію** — виводиться після завершення з кількістю перенесених, пропущених та конфліктних елементів.

2. **Переглянь заархівовані файли** — все, що знаходиться в `~/.hermes/migration/openclaw/<timestamp>/archive/`, потребує ручного втручання.

3. **Запусти нову сесію** — імпортовані skills та записи пам'яті набувають чинності в нових сесіях, а не в поточній.

4. **Перевір API‑ключі** — виконай `hermes status`, щоб перевірити автентифікацію провайдера.

5. **Протести обмін повідомленнями** — якщо ти мігрував токени платформи, перезапусти шлюз: `systemctl --user restart hermes-gateway`.

6. **Перевір політики сесії** — переконайся, що `hermes config get session_reset` відповідає твоїм очікуванням.

7. **Повторно підключи WhatsApp** — WhatsApp використовує QR‑код для підключення (Baileys), а не міграцію токену. Запусти `hermes whatsapp` для підключення.

8. **Очищення архіву** — після підтвердження, що все працює, виконай `hermes claw cleanup`, щоб перейменувати залишкові каталоги OpenClaw у `.pre-migration/` (запобігає плутанині стану).
## Усунення проблем

### «Не знайдено каталог OpenClaw»

Міграція перевіряє `~/.openclaw/`, потім `~/.clawdbot/`, потім `~/.moltbot/`. Якщо твоє встановлення знаходиться в іншому місці, використай `--source /path/to/your/openclaw`.

### «Не знайдено API‑ключі провайдера»

Ключі можуть зберігатися в кількох місцях залежно від версії OpenClaw: безпосередньо в `openclaw.json` у `models.providers.*.apiKey`, у `~/.openclaw/.env`, у підоб’єкті `"env"` файлу `openclaw.json` або у `agents/main/agent/auth-profiles.json`. Міграція перевіряє всі чотири. Якщо ключі використовують SecretRefs `source: "file"` або `source: "exec"`, їх не вдається розв’язати автоматично — додай їх вручну за допомогою `hermes config set`.

### Навички не з’являються після міграції

Імпортовані навички потрапляють у `~/.hermes/skills/openclaw-imports/`. Запусти нову сесію, щоб вони набули чинності, або виконай `/skills`, щоб перевірити, чи завантажені.

### Голос TTS не перенесено

OpenClaw зберігає налаштування TTS у двох місцях: `messages.tts.providers.*` та у конфігурації верхнього рівня `talk`. Міграція перевіряє обидва. Якщо ідентифікатор голосу був встановлений через інтерфейс OpenClaw (збережений у іншому шляху), можливо, доведеться задати його вручну: `hermes config set tts.elevenlabs.voice_id YOUR_VOICE_ID`.