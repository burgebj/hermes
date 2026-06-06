---
sidebar_position: 10
title: "Мигрировать из OpenClaw"
description: "Полное руководство по миграции вашей настройки OpenClaw / Clawdbot на Hermes Agent — что переносится, как работают config maps и что проверить после."
---

# Перенос из OpenClaw

`hermes claw migrate` импортирует твою настройку OpenClaw (или устаревшего Clawdbot/Moldbot) в Hermes. В этом руководстве подробно описано, что именно переносится, какие соответствия ключей конфигурации используются и что проверять после переноса.

:::tip
Если твоя настройка OpenClaw была мультипровайдерной, `hermes setup --portal` сводит её к одному OAuth — 300 + моделей плюс шлюз инструментов (Tool Gateway) в едином входе. См. [Nous Portal](/integrations/nous-portal).
:::
## Быстрый старт

```bash
# Preview then migrate (always shows a preview first, then asks to confirm)
hermes claw migrate

# Preview only, no changes
hermes claw migrate --dry-run

# Full migration including API keys, skip confirmation
hermes claw migrate --preset full --migrate-secrets --yes
```

Миграция всегда отображает полный предварительный просмотр того, что будет импортировано, — ещё до внесения каких‑либо изменений. Просмотри список, а затем подтверди, чтобы продолжить.

По умолчанию читаются данные из `~/.openclaw/`. Директории устаревших `~/.clawdbot/` или `~/.moltbot/` обнаруживаются автоматически. То же самое относится к устаревшим именам файлов конфигурации (`clawdbot.json`, `moltbot.json`).
## Параметры

| Параметр | Описание |
|--------|-------------|
| `--dry-run` | Только предварительный просмотр — остановиться после показа того, что будет перенесено. |
| `--preset <name>` | `full` (все совместимые настройки) или `user-data` (исключает конфигурацию инфраструктуры). Ни один набор настроек не импортирует секреты по умолчанию — явно укажи `--migrate-secrets`. |
| `--overwrite` | Перезаписать существующие файлы Hermes при конфликтах (по умолчанию: отклонять применение, когда план содержит конфликты). |
| `--migrate-secrets` | Включить API‑ключи. Требуется даже при `--preset full` — ни один набор настроек не импортирует секреты без явного указания. |
| `--no-backup` | Пропустить zip‑снимок `~/.hermes/` перед миграцией (по умолчанию перед применением создаётся один архив точки восстановления в `~/.hermes/backups/pre-migration-*.zip`; его можно восстановить с помощью `hermes import`). |
| `--source <path>` | Пользовательская директория OpenClaw. |
| `--workspace-target <path>` | Куда разместить `AGENTS.md`. |
| `--skill-conflict <mode>` | `skip` (по умолчанию), `overwrite` или `rename`. |
| `--yes` | Пропустить запрос подтверждения после предварительного просмотра. |
## Что мигрируется

### Персона, память и инструкции

| Что | Исходный OpenClaw | Назначение Hermes | Примечания |
|------|-------------------|-------------------|------------|
| Персона | `workspace/SOUL.md` | `~/.hermes/SOUL.md` | Прямое копирование |
| Инструкции рабочего пространства | `workspace/AGENTS.md` | `AGENTS.md` в `--workspace-target` | Требуется флаг `--workspace-target` |
| Долгосрочная память | `workspace/MEMORY.md` | `~/.hermes/memories/MEMORY.md` | Парсится в записи, объединяется с существующими, удаляются дубликаты. Использует разделитель `§`. |
| Профиль пользователя | `workspace/USER.md` | `~/.hermes/memories/USER.md` | Та же логика объединения записей, что и у памяти. |
| Ежедневные файлы памяти | `workspace/memory/*.md` | `~/.hermes/memories/MEMORY.md` | Все ежедневные файлы объединяются в основную память. |

Файлы рабочего пространства также проверяются в `workspace.default/` и `workspace-main/` как запасные пути (в последних версиях OpenClaw переименовал `workspace/` в `workspace-main/`, а для многопользовательских настроек использует `workspace-{agentId}`).

### Навыки (4 источника)

| Источник | Расположение в OpenClaw | Назначение в Hermes |
|--------|--------------------------|---------------------|
| Навыки рабочего пространства | `workspace/skills/` | `~/.hermes/skills/openclaw-imports/` |
| Управляемые/общие навыки | `~/.openclaw/skills/` | `~/.hermes/skills/openclaw-imports/` |
| Персональные кросс‑проектные | `~/.agents/skills/` | `~/.hermes/skills/openclaw-imports/` |
| Общие на уровне проекта | `workspace/.agents/skills/` | `~/.hermes/skills/openclaw-imports/` |

Конфликты навыков обрабатываются параметром `--skill-conflict`: `skip` оставляет существующий навык Hermes, `overwrite` заменяет его, `rename` создаёт копию с суффиксом `-imported`.

### Конфигурация модели и провайдера

| Что | Путь конфигурации OpenClaw | Назначение в Hermes | Примечания |
|------|---------------------------|---------------------|------------|
| Модель по умолчанию | `agents.defaults.model` | `config.yaml` → `model` | Может быть строкой или объектом `{primary, fallbacks}` |
| Пользовательские провайдеры | `models.providers.*` | `config.yaml` → `custom_providers` | Сопоставляет `baseUrl`, `apiType`/`api` — поддерживает как короткие (`"openai"`, `"anthropic"`), так и дефисные (`"openai-completions"`, `"anthropic-messages"`, `"google-generative-ai"`) значения |
| API‑ключи провайдера | `models.providers.*.apiKey` | `~/.hermes/.env` | Требуется `--migrate-secrets`. См. [разрешение API‑ключей](#api-key-resolution) ниже. |

### Поведение агента

| Что | Путь конфигурации OpenClaw | Путь конфигурации Hermes | Преобразование |
|------|---------------------------|--------------------------|----------------|
| Максимальное количество ходов | `agents.defaults.timeoutSeconds` | `agent.max_turns` | `timeoutSeconds / 10`, максимум 200 |
| Подробный режим | `agents.defaults.verboseDefault` | `agent.verbose` | `"off"` / `"on"` / `"full"` |
| Усилие рассуждения | `agents.defaults.thinkingDefault` | `agent.reasoning_effort` | `"always"`/`"high"`/`"xhigh"` → `"high"`, `"auto"`/`"medium"`/`"adaptive"` → `"medium"`, `"off"`/`"low"`/`"none"`/`"minimal"` → `"low"` |
| Сжатие | `agents.defaults.compaction.mode` | `compression.enabled` | `"off"` → `false`, всё остальное → `true` |
| Модель сжатия | `agents.defaults.compaction.model` | `compression.summary_model` | Прямая копия строки |
| Задержка человека | `agents.defaults.humanDelay.mode` | `human_delay.mode` | `"natural"` / `"custom"` / `"off"` |
| Параметры задержки человека | `agents.defaults.humanDelay.minMs` / `.maxMs` | `human_delay.min_ms` / `.max_ms` | Прямая копия |
| Часовой пояс | `agents.defaults.userTimezone` | `timezone` | Прямая копия строки |
| Таймаут выполнения | `tools.exec.timeoutSec` | `terminal.timeout` | Прямая копия (поле называется `timeoutSec`, а не `timeout`) |
| Песочница Docker | `agents.defaults.sandbox.backend` | `terminal.backend` | `"docker"` → `"docker"` |
| Docker‑образ | `agents.defaults.sandbox.docker.image` | `terminal.docker_image` | Прямая копия |

### Политики сброса сессии

| Путь конфигурации OpenClaw | Путь конфигурации Hermes | Примечания |
|----------------------------|--------------------------|------------|
| `session.reset.mode` | `session_reset.mode` | `"daily"`, `"idle"` или оба |
| `session.reset.atHour` | `session_reset.at_hour` | Час (0–23) для ежедневного сброса |
| `session.reset.idleMinutes` | `session_reset.idle_minutes` | Минуты бездействия |

Примечание: в OpenClaw также есть `session.resetTriggers` (простой массив строк, например `["daily", "idle"]`). Если структурированный `session.reset` отсутствует, миграция переходит к выводу из `resetTriggers`.

### Серверы MCP

| Поле OpenClaw | Поле Hermes | Примечания |
|---------------|------------|------------|
| `mcp.servers.*.command` | `mcp_servers.*.command` | Транспорт Stdio |
| `mcp.servers.*.args` | `mcp_servers.*.args` | |
| `mcp.servers.*.env` | `mcp_servers.*.env` | |
| `mcp.servers.*.cwd` | `mcp_servers.*.cwd` | |
| `mcp.servers.*.url` | `mcp_servers.*.url` | Транспорт HTTP/SSE |
| `mcp.servers.*.tools.include` | `mcp_servers.*.tools.include` | Фильтрация инструментов |
| `mcp.servers.*.tools.exclude` | `mcp_servers.*.tools.exclude` | |

### TTS (text-to-speech)

Настройки TTS читаются из **трёх** мест конфигурации OpenClaw с приоритетом:

1. `messages.tts.providers.{provider}.*` (каноничное место)
2. Верхнеуровневый `talk.providers.{provider}.*` (запасной)
3. Устаревшие плоские ключи `messages.tts.{provider}.*` (самый старый формат)

| Что | Назначение в Hermes |
|------|---------------------|
| Имя провайдера | `config.yaml` → `tts.provider` |
| ID голоса ElevenLabs | `config.yaml` → `tts.elevenlabs.voice_id` |
| ID модели ElevenLabs | `config.yaml` → `tts.elevenlabs.model_id` |
| Модель OpenAI | `config.yaml` → `tts.openai.model` |
| Голос OpenAI | `config.yaml` → `tts.openai.voice` |
| Голос Edge TTS | `config.yaml` → `tts.edge.voice` (OpenClaw переименовал `"edge"` в `"microsoft"` — оба распознаются) |
| TTS‑ресурсы | `~/.hermes/tts/` (копирование файлов) |

### Платформы обмена сообщениями

| Платформа | Путь конфигурации OpenClaw | Переменная `.env` Hermes | Примечания |
|----------|----------------------------|--------------------------|------------|
| Telegram | `channels.telegram.botToken` или `.accounts.default.botToken` | `TELEGRAM_BOT_TOKEN` | Токен может быть строкой или [SecretRef](#secretref-handling). Поддерживаются как плоская, так и структура `accounts`. |
| Telegram | `credentials/telegram-default-allowFrom.json` | `TELEGRAM_ALLOWED_USERS` | Формируется как строка, разделённая запятыми, из массива `allowFrom[]` |
| Discord | `channels.discord.token` или `.accounts.default.token` | `DISCORD_BOT_TOKEN` | |
| Discord | `channels.discord.allowFrom` или `.accounts.default.allowFrom` | `DISCORD_ALLOWED_USERS` | |
| Slack | `channels.slack.botToken` или `.accounts.default.botToken` | `SLACK_BOT_TOKEN` | |
| Slack | `channels.slack.appToken` или `.accounts.default.appToken` | `SLACK_APP_TOKEN` | |
| Slack | `channels.slack.allowFrom` или `.accounts.default.allowFrom` | `SLACK_ALLOWED_USERS` | |
| WhatsApp | `channels.whatsapp.allowFrom` или `.accounts.default.allowFrom` | `WHATSAPP_ALLOWED_USERS` | Авторизация через QR‑пару Baileys — после миграции требуется повторное сопряжение |
| Signal | `channels.signal.account` или `.accounts.default.account` | `SIGNAL_ACCOUNT` | |
| Signal | `channels.signal.httpUrl` или `.accounts.default.httpUrl` | `SIGNAL_HTTP_URL` | |
| Signal | `channels.signal.allowFrom` или `.accounts.default.allowFrom` | `SIGNAL_ALLOWED_USERS` | |
| Matrix | `channels.matrix.accessToken` или `.accounts.default.accessToken` | `MATRIX_ACCESS_TOKEN` | Используется `accessToken` (а не `botToken`) |
| Mattermost | `channels.mattermost.botToken` или `.accounts.default.botToken` | `MATTERMOST_BOT_TOKEN` | |

### Прочая конфигурация

| Что | Путь OpenClaw | Путь Hermes | Примечания |
|------|---------------|------------|------------|
| Режим одобрения | `approvals.exec.mode` | `config.yaml` → `approvals.mode` | `"auto"`→`"off"`, `"always"`→`"manual"`, `"smart"`→`"smart"` |
| Белый список команд | `exec-approvals.json` | `config.yaml` → `command_allowlist` | Объединяются паттерны и удаляются дубликаты |
| URL CDP браузера | `browser.cdpUrl` | `config.yaml` → `browser.cdp_url` | |
| Безголовый режим браузера | `browser.headless` | `config.yaml` → `browser.headless` | |
| Ключ Brave search | `tools.web.search.brave.apiKey` | `.env` → `BRAVE_API_KEY` | Требуется `--migrate-secrets` |
| Токен аутентификации шлюза | `gateway.auth.token` | `.env` → `HERMES_GATEWAY_TOKEN` | Требуется `--migrate-secrets` |
| Рабочий каталог | `agents.defaults.workspace` | `.env` → `MESSAGING_CWD` | |

### Архивировано (нет прямого эквивалента в Hermes)

Эти файлы сохраняются в `~/.hermes/migration/openclaw/<timestamp>/archive/` для ручного анализа:

| Что | Файл архива | Как воссоздать в Hermes |
|------|-------------|--------------------------|
| `IDENTITY.md` | `archive/workspace/IDENTITY.md` | Объединить в `SOUL.md` |
| `TOOLS.md` | `archive/workspace/TOOLS.md` | В Hermes встроены инструкции по инструментам |
| `HEARTBEAT.md` | `archive/workspace/HEARTBEAT.md` | Использовать cron‑задачи для периодических действий |
| `BOOTSTRAP.md` | `archive/workspace/BOOTSTRAP.md` | Использовать файлы контекста или навыки |
| Cron‑задачи | `archive/cron-config.json` | Воссоздать через `hermes cron create` |
| Плагины | `archive/plugins-config.json` | См. [руководство по плагинам](/user-guide/features/hooks) |
| Хуки/webhooks | `archive/hooks-config.json` | Использовать `hermes webhook` или шлюзовые хуки |
| Бэкенд памяти | `archive/memory-backend-config.json` | Настроить через `hermes honcho` |
| Реестр навыков | `archive/skills-registry-config.json` | Использовать `hermes skills config` |
| UI/идентичность | `archive/ui-identity-config.json` | Команда `/skin` |
| Логирование | `archive/logging-diagnostics-config.json` | Указать в секции `logging` файла `config.yaml` |
| Список агентов | `archive/agents-list.json` | Использовать профили Hermes |
| Привязки каналов | `archive/bindings.json` | Настраивать вручную для каждой платформы |
| Сложные каналы | `archive/channels-deep-config.json` | Ручная настройка платформы |
## Разрешение API‑ключей

Когда включён параметр `--migrate-secrets`, API‑ключи собираются из **четырёх источников** в порядке приоритета:

1. **Значения конфигурации** — `models.providers.*.apiKey` и ключи TTS‑провайдера в `openclaw.json`
2. **Файл окружения** — `~/.openclaw/.env` (ключи типа `OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY` и т.д.)
3. **Подобъект `env` в конфигурации** — `openclaw.json` → `"env"` или `"env"."vars"` (в некоторых настройках ключи хранятся здесь вместо отдельного файла `.env`)
4. **Профили аутентификации** — `~/.openclaw/agents/main/agent/auth-profiles.json` (учётные данные для каждого агента)

Значения конфигурации имеют высший приоритет. Каждый последующий источник заполняет оставшиеся пропуски.

### Поддерживаемые цели ключей

`OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `DEEPSEEK_API_KEY`, `GEMINI_API_KEY`, `ZAI_API_KEY`, `MINIMAX_API_KEY`, `ELEVENLABS_API_KEY`, `TELEGRAM_BOT_TOKEN`, `VOICE_TOOLS_OPENAI_KEY`

Ключи, не входящие в этот список разрешённых, никогда не копируются.
## Обработка SecretRef

Значения конфигурации OpenClaw для токенов и API‑ключей могут быть в трёх форматах:

```json
// Plain string
"channels": { "telegram": { "botToken": "123456:ABC-DEF..." } }

// Environment template
"channels": { "telegram": { "botToken": "${TELEGRAM_BOT_TOKEN}" } }

// SecretRef object
"channels": { "telegram": { "botToken": { "source": "env", "id": "TELEGRAM_BOT_TOKEN" } } }
```

Миграция поддерживает все три формата. Для шаблонов `env` и объектов SecretRef с `source: "env"` она ищет значение в `~/.openclaw/.env` и в под‑объекте `env` файла `openclaw.json`. Объекты SecretRef с `source: "file"` или `source: "exec"` нельзя разрешить автоматически — миграция выдаёт предупреждение, и такие значения необходимо добавить в Hermes вручную с помощью `hermes config set`.
## После миграции

1. **Проверь отчёт о миграции** — выводится по завершении с подсчётом перенесённых, пропущенных и конфликтующих элементов.

2. **Просмотри архивированные файлы** — всё, что находится в `~/.hermes/migration/openclaw/<timestamp>/archive/`, требует ручного вмешательства.

3. **Запусти новую сессию** — импортированные skills и записи памяти вступают в силу только в новых сессиях, а не в текущей.

4. **Проверь API‑ключи** — выполни `hermes status`, чтобы проверить аутентификацию провайдера.

5. **Протестируй обмен сообщениями** — если ты мигрировал токены платформ, перезапусти шлюз: `systemctl --user restart hermes-gateway`.

6. **Проверь политики сессий** — убедись, что `hermes config get session_reset` соответствует твоим ожиданиям.

7. **Повтори сопряжение WhatsApp** — WhatsApp использует сопряжение через QR‑код (Baileys), а не миграцию токенов. Выполни `hermes whatsapp` для сопряжения.

8. **Очистка архива** — после подтверждения, что всё работает, выполни `hermes claw cleanup`, чтобы переименовать оставшиеся директории OpenClaw в `.pre-migration/` (это предотвращает путаницу состояния).
## Устранение неполадок

### «Каталог OpenClaw не найден»

Миграция проверяет `~/.openclaw/`, затем `~/.clawdbot/`, затем `~/.moltbot/`. Если твоя установка находится в другом месте, используй `--source /path/to/your/openclaw`.

### «Не найдены API‑ключи провайдера»

Ключи могут храниться в нескольких местах в зависимости от версии OpenClaw: встроенно в `openclaw.json` в `models.providers.*.apiKey`, в `~/.openclaw/.env`, в подпункте `"env"` файла `openclaw.json` или в `agents/main/agent/auth-profiles.json`. Миграция проверяет все четыре. Если ключи используют SecretRefs `source: "file"` или `source: "exec"`, их нельзя автоматически разрешить — добавь их через `hermes config set`.

### Skills не появляются после миграции

Импортированные skills попадают в `~/.hermes/skills/openclaw-imports/`. Запусти новую сессию, чтобы они вступили в силу, или выполни `/skills`, чтобы проверить, что они загружены.

### Голос TTS не мигрировал

OpenClaw хранит настройки TTS в двух местах: `messages.tts.providers.*` и в конфигурации верхнего уровня `talk`. Миграция проверяет оба места. Если идентификатор голоса был установлен через UI OpenClaw (хранится в другом пути), возможно, придётся задать его вручную: `hermes config set tts.elevenlabs.voice_id YOUR_VOICE_ID`.