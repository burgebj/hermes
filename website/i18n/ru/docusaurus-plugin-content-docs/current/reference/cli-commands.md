---
sidebar_position: 1
title: "Справочник команд CLI"
description: "Авторитетный справочник команд терминала Hermes и семейств команд"
---

# Справочник команд CLI

Эта страница охватывает **команды терминала**, которые ты запускаешь из своей оболочки.

Для команд со слешем в чате смотри [Справочник команд со слешем](./slash-commands.md).
## Глобальная точка входа

```bash
hermes [global-options] <command> [subcommand/options]
```

### Глобальные параметры

| Option | Description |
|--------|-------------|
| `--version`, `-V` | Показать версию и выйти. |
| `--profile <name>`, `-p <name>` | Выбрать профиль Hermes, который будет использоваться для этого вызова. Переопределяет «липкий» профиль, установленный командой `hermes profile use`. |
| `--resume <session>`, `-r <session>` | Возобновить предыдущую сессию по ID или названию. |
| `--continue [name]`, `-c [name]` | Возобновить последнюю сессию или последнюю сессию, соответствующую указанному названию. |
| `--worktree`, `-w` | Запустить в изолированном git‑worktree для параллельных рабочих процессов агента. |
| `--yolo` | Обойти запросы подтверждения опасных команд. |
| `--pass-session-id` | Включить ID сессии в системный запрос агента. |
| `--ignore-user-config` | Игнорировать `~/.hermes/config.yaml` и использовать встроенные настройки по умолчанию. Учётные данные в `.env` всё равно загружаются. |
| `--ignore-rules` | Пропустить автоматическое внедрение `AGENTS.md`, `SOUL.md`, `.cursorrules`, памяти и предзагруженных инструментов. |
| `--tui` | Запустить [TUI](../user-guide/tui.md) вместо классического CLI. Эквивалентно `HERMES_TUI=1`. |
| `--dev` | При `--tui`: запускать TypeScript‑исходники напрямую через `tsx` вместо предсобранного пакета (для участников разработки TUI). |
## Команды верхнего уровня

| Команда | Назначение |
|---------|------------|
| `hermes chat` | Интерактивный или одноразовый чат с агентом. |
| `hermes model` | Интерактивный выбор провайдера и модели по умолчанию. |
| `hermes fallback` | Управление запасными (вариант) провайдерами, которые пробуются при ошибке основной модели. |
| `hermes gateway` | Запуск или управление сервисом шлюза обмена сообщениями. |
| `hermes proxy` | Локальный совместимый с OpenAI прокси, который подключает учётные данные OAuth‑провайдера. См. [Subscription Proxy](../user-guide/features/subscription-proxy.md). |
| `hermes lsp` | Управление интеграцией Language Server Protocol (семантическая диагностика для `write_file`/`patch`). |
| `hermes setup` | Интерактивный мастер настройки всей конфигурации или её части. |
| `hermes whatsapp` | Настройка и сопряжение моста WhatsApp. |
| `hermes slack` | Помощники Slack (сейчас: генерация манифеста приложения с каждой командой как нативным slash). |
| `hermes auth` | Управление учётными данными — добавление, список, удаление, сброс, установка стратегии. Обрабатывает OAuth‑потоки для Codex/Nous/Anthropic. |
| `hermes login` / `logout` | **Устарело** — используйте `hermes auth` вместо этого. |
| `hermes send` | Отправка одноразового сообщения на настроенную платформу обмена (Telegram, Discord, Slack, Signal, SMS, …). Полезно в shell‑скриптах, cron‑задачах, CI‑хуках и демонах мониторинга — без цикла агента, без LLM. |
| `hermes secrets` | Управление внешними источниками секретов (сейчас Bitwarden Secrets Manager) для получения API‑ключей при запуске процесса вместо `~/.hermes/.env`. |
| `hermes migrate` | Диагностика и (по желанию) переписывание `config.yaml` для замены ссылок на устаревшие модели или устаревшие настройки (например, `migrate xai`). |
| `hermes status` | Показ состояния агента, аутентификации и платформ. |
| `hermes cron` | Просмотр и запуск планировщика cron. |
| `hermes kanban` | Доска совместной работы с несколькими профилями (задачи, ссылки, диспетчер). |
| `hermes webhook` | Управление динамическими подписками webhook для активации по событиям. |
| `hermes hooks` | Просмотр, одобрение или удаление shell‑скриптов‑хуков, объявленных в `config.yaml`. |
| `hermes doctor` | Диагностика проблем конфигурации и зависимостей. |
| `hermes security audit` | По запросу аудит цепочки поставок (OSV.dev) для виртуального окружения, требований плагинов и закреплённых серверов MCP. |
| `hermes dump` | Сводка настройки, готовая к копированию/вставке, для поддержки/отладки. |
| `hermes debug` | Инструменты отладки — загрузка логов и системной информации для поддержки. |
| `hermes backup` | Резервное копирование домашнего каталога Hermes в zip‑файл. |
| `hermes checkpoints` | Просмотр / очистка / удаление `~/.hermes/checkpoints/` (теневого хранилища, используемого `/rollback`). Запуск без аргументов выводит обзор статуса. |
| `hermes import` | Восстановление резервной копии Hermes из zip‑файла. |
| `hermes logs` | Просмотр, «tail», фильтрация логов агента/шлюза/ошибок. |
| `hermes config` | Показ, редактирование, миграция и запрос конфигурационных файлов. |
| `hermes pairing` | Одобрение или отзыв кодов сопряжения обмена сообщениями. |
| `hermes skills` | Обзор, установка, публикация, аудит и настройка навыков. |
| `hermes bundles` | Группировка нескольких навыков под одной slash‑командой `/<name>`. См. [Skill Bundles](../user-guide/features/skills.md#skill-bundles). |
| `hermes curator` | Фоновое обслуживание навыков — статус, запуск, пауза, закрепление. См. [Curator](../user-guide/features/curator.md). |
| `hermes memory` | Настройка внешнего провайдера памяти. Подкоманды, специфичные для плагина (например, `hermes honcho`), регистрируются автоматически, когда их провайдер активен. |
| `hermes acp` | Запуск Hermes как сервера ACP для интеграции с редактором. |
| `hermes mcp` | Управление конфигурациями сервера MCP и запуск Hermes как сервера MCP. |
| `hermes plugins` | Управление плагинами Hermes Agent (установка, включение, отключение, удаление). |
| `hermes portal` | Статус Nous Portal, ссылка на подписку и маршрутизация шлюза инструментов. См. [Tool Gateway](../user-guide/features/tool-gateway.md). |
| `hermes tools` | Настройка включённых инструментов для каждой платформы. |
| `hermes computer-use` | Установка или проверка бэкенда `cua-driver` (Computer Use для macOS). |
| `hermes sessions` | Обзор, экспорт, очистка, переименование и удаление сессий. |
| `hermes insights` | Показ аналитики токенов/стоимости/активности. |
| `hermes claw` | Помощники миграции OpenClaw. |
| `hermes dashboard` | Запуск веб‑дашборда для управления конфигурацией, API‑ключами и сессиями. |
| `hermes profile` | Управление профилями — несколькими изолированными экземплярами Hermes. |
| `hermes completion` | Вывод скриптов автодополнения для оболочек (bash/zsh/fish). |
| `hermes version` | Показ информации о версии. |
| `hermes update` | Получение последнего кода и переустановка зависимостей (git‑установки) или проверка PyPI и `pip install --upgrade` (pip‑установки). `--check` показывает предварительный результат без установки; `--backup` делает снимок `HERMES_HOME` перед получением. |
| `hermes uninstall` | Удаление Hermes из системы. |
## `hermes chat`

```bash
hermes chat [options]
```

Общие параметры:

| Параметр | Описание |
|--------|----------|
| `-q`, `--query "..."` | Одноразовый, неинтерактивный запрос. |
| `-m`, `--model <model>` | Переопределить модель для этого запуска. |
| `-t`, `--toolsets <csv>` | Включить набор **toolsets**, разделённых запятыми. |
| `--provider <provider>` | Принудительно задать провайдера: `auto`, `openrouter`, `nous`, `openai-codex`, `copilot-acp`, `copilot`, `anthropic`, `gemini`, `google-gemini-cli`, `huggingface`, `novita`, `zai`, `kimi-coding`, `kimi-coding-cn`, `minimax`, `minimax-cn`, `minimax-oauth`, `kilocode`, `xiaomi`, `arcee`, `gmi`, `alibaba`, `alibaba-coding-plan` (alias `alibaba_coding`), `deepseek`, `nvidia`, `ollama-cloud`, `xai` (alias `grok`), `xai-oauth` (alias `grok-oauth`), `qwen-oauth`, `bedrock`, `opencode-zen`, `opencode-go`, `azure-foundry`, `lmstudio`, `stepfun`, `tencent-tokenhub` (alias `tencent`, `tokenhub`). |
| `-s`, `--skills <name>` | Предзагрузить один или несколько **skills** для сессии (можно указывать несколько раз или через запятую). |
| `-v`, `--verbose` | Подробный вывод. |
| `-Q`, `--quiet` | Программный режим: подавить баннер, индикатор и предпросмотр инструментов. |
| `--image <path>` | Прикрепить локальное изображение к одиночному запросу. |
| `--resume <session>` / `--continue [name]` | Возобновить сессию напрямую из `chat`. |
| `--worktree` | Создать изолированный git‑worktree для этого запуска. |
| `--checkpoints` | Включить контрольные точки файловой системы перед разрушительными изменениями файлов. |
| `--yolo` | Пропустить запросы подтверждения. |
| `--pass-session-id` | Передать идентификатор сессии в системный запрос. |
| `--ignore-user-config` | Игнорировать `~/.hermes/config.yaml` и использовать встроенные значения по умолчанию. Учётные данные из `.env` всё равно загружаются. Полезно для изолированных CI‑запусков, воспроизводимых отчётов об ошибках и сторонних интеграций. |
| `--ignore-rules` | Пропустить авто‑вставку `AGENTS.md`, `SOUL.md`, `.cursorrules`, постоянную **memory** и предзагруженные **skills**. Сочетайте с `--ignore-user-config` для полностью изолированного запуска. |
| `--source <tag>` | Тег источника сессии для фильтрации (по умолчанию: `cli`). Используйте `tool` для сторонних интеграций, которые не должны появляться в списках пользовательских сессий. |
| `--max-turns <N>` | Максимальное количество итераций вызова инструментов за один ход разговора (по умолчанию: 90, или `agent.max_turns` в конфигурации). |

Примеры:

```bash
hermes
hermes chat -q "Summarize the latest PRs"
hermes chat --provider openrouter --model anthropic/claude-sonnet-4.6
hermes chat --toolsets web,terminal,skills
hermes chat --quiet -q "Return only JSON"
hermes chat --worktree -q "Review this repo and open a PR"
hermes chat --ignore-user-config --ignore-rules -q "Repro without my personal setup"
```

### `hermes -z <prompt>` — скриптовый одноразовый запуск

Для программных вызовов (shell‑скрипты, CI, cron, родительские процессы, передающие запрос) `hermes -z` — самый «чистый» одноразовый вход: **один запрос на вход, окончательный текст ответа на выход, ничего более в stdout или stderr.** Нет баннера, индикатора, предпросмотра инструментов, строки `Session:` — только окончательный ответ агента в виде простого текста.

```bash
hermes -z "What's the capital of France?"
# → Paris.

# Parent scripts can cleanly capture the response:
answer=$(hermes -z "summarize this" < /path/to/file.txt)
```

Переопределения для отдельного запуска (без изменения `~/.hermes/config.yaml`):

| Флаг | Эквивалентная переменная окружения | Назначение |
|---|---|---|
| `-m` / `--model <model>` | `HERMES_INFERENCE_MODEL` | Переопределить модель для этого запуска |
| `--provider <provider>` | _(none)_ | Переопределить провайдера для этого запуска |

```bash
hermes -z "…" --provider openrouter --model openai/gpt-5.5
# or:
HERMES_INFERENCE_MODEL=anthropic/claude-sonnet-4.6 hermes -z "…"
```

Тот же агент, те же инструменты, те же **skills** — просто убирает все интерактивные/косметические слои. Если нужен вывод инструментов в транскрипте, используй `hermes chat -q`; `-z` предназначен явно для «я хочу только окончательный ответ».
## `hermes model`

Интерактивный провайдер и селектор модели. **Это команда для добавления новых провайдеров, настройки API‑ключей и выполнения OAuth‑потоков.** Запусти её из терминала — а не из активной сессии чата Hermes.

```bash
hermes model
```

Используй её, когда нужно:
- **добавить нового провайдера** (OpenRouter, Anthropic, Copilot, DeepSeek, custom и т.д.)
- войти в провайдеры, поддерживающие OAuth (Anthropic, Copilot, Codex, Nous Portal)
- ввести или обновить API‑ключи
- выбрать из списка моделей конкретного провайдера
- настроить пользовательскую/само‑хостинговую конечную точку
- сохранить новый провайдер по умолчанию в конфигурацию

:::warning hermes model vs /model — know the difference
**`hermes model`** (запускается из терминала, вне любой сессии Hermes) — это **полный мастер настройки провайдера**. Он может добавлять новых провайдеров, выполнять OAuth‑потоки, запрашивать API‑ключи и настраивать конечные точки.

**`/model`** (вводится внутри активной сессии чата Hermes) может только **переключать между уже настроенными провайдерами и моделями**. Он не может добавлять новых провайдеров, выполнять OAuth или запрашивать API‑ключи.

**Если нужно добавить нового провайдера:** сначала выйди из сессии Hermes (`Ctrl+C` или `/quit`), затем запусти `hermes model` из терминала.
:::

### `/model` slash command (mid-session)

Переключайся между уже сконфигурированными моделями, не покидая сессию:

```
/model                              # Show current model and available options
/model claude-sonnet-4              # Switch model (auto-detects provider)
/model zai:glm-5                    # Switch provider and model
/model custom:qwen-2.5              # Use model on your custom endpoint
/model custom                       # Auto-detect model from custom endpoint
/model custom:local:qwen-2.5        # Use a named custom provider
/model openrouter:anthropic/claude-sonnet-4  # Switch back to cloud
```

По умолчанию изменения, внесённые через `/model`, применяются **только к текущей сессии**. Добавь `--global`, чтобы сохранить изменение в `config.yaml`:

```
/model claude-sonnet-4 --global     # Switch and save as new default
```

:::info What if I only see OpenRouter models?
Если у тебя настроен только OpenRouter, `/model` будет показывать только модели OpenRouter. Чтобы добавить другой провайдер (Anthropic, DeepSeek, Copilot и т.д.), выйди из сессии и запусти `hermes model` из терминала.
:::

Изменения провайдера и базового URL автоматически сохраняются в `config.yaml`. При переключении с пользовательской конечной точки устаревший базовый URL очищается, чтобы он не «просочился» в другие провайдеры.
## `hermes gateway`

```bash
hermes gateway <subcommand>
```

Подкоманды:

| Подкоманда | Описание |
|------------|----------|
| `run` | Запустить шлюз в foreground. Рекомендуется для WSL, Docker и Termux. |
| `start` | Запустить установленный фоновый сервис systemd/launchd. |
| `stop` | Остановить сервис (или процесс в foreground). |
| `restart` | Перезапустить сервис. |
| `status` | Показать статус сервиса. |
| `list` | Вывести **все профили** и информацию о том, запущен ли шлюз каждого профиля (с PID, если доступно). Удобно, когда ты запускаешь несколько профилей одновременно и нужен единый обзор. |
| `install` | Установить как фоновый сервис systemd (Linux) или launchd (macOS). |
| `uninstall` | Удалить установленный сервис. |
| `setup` | Интерактивная настройка платформы обмена сообщениями. |

Опции:

| Опция | Описание |
|--------|----------|
| `--all` | При `start` / `restart` / `stop`: действовать на **каждый** шлюз профиля, а не только на активный `HERMES_HOME`. Полезно, если ты запускаешь несколько профилей одновременно и хочешь перезапустить их все после `hermes update`. |
| `--no-supervise` | При `run`: в Docker‑образе s6-overlay отключить автоконтроль и использовать семантику foreground без s6 — шлюз работает как основной процесс контейнера без автоперезапуска. Вне s6‑образа — без действия. Эквивалентно установке `HERMES_GATEWAY_NO_SUPERVISE=1`. |

:::tip WSL users
Используй `hermes gateway run` вместо `hermes gateway start` — поддержка systemd в WSL ненадёжна. Оберни его в tmux для постоянства: `tmux new -s hermes 'hermes gateway run'`. См. [WSL FAQ](/reference/faq#wsl-gateway-keeps-disconnecting-or-hermes-gateway-start-fails) для деталей.
:::
## `hermes lsp`

```bash
hermes lsp <subcommand>
```

Управляет интеграцией Language Server Protocol. LSP запускает реальные
языковые серверы (pyright, gopls, rust-analyzer, …) в фоне и передаёт их
диагностические сообщения в проверку после записи,
используемую `write_file` и `patch`. Работает только при обнаружении git‑рабочего
пространства — LSP запускается лишь тогда, когда cwd или редактируемый файл находятся
внутри git‑рабочего дерева.

Подкоманды:

| Подкоманда | Описание |
|------------|----------|
| `status` | Показать состояние сервиса, настроенные серверы и статус установки. |
| `list` | Вывести реестр поддерживаемых серверов. Укажите `--installed-only`, чтобы пропустить отсутствующие. |
| `install <id>` | Установить бинарный файл сервера немедленно. |
| `install-all` | Установить все серверы, для которых известен рецепт автоустановки. |
| `restart` | Остановить работающие клиенты, чтобы при следующем редактировании они были заново запущены. |
| `which <id>` | Вывести разрешённый путь к бинарному файлу сервера. |

См. [LSP — Семантическая диагностика](/user-guide/features/lsp) для
полного руководства, поддерживаемых языков и параметров конфигурации.
## `hermes setup`

```bash
hermes setup [model|tts|terminal|gateway|tools|agent] [--non-interactive] [--reset] [--quick] [--reconfigure] [--portal]
```

**Самый простой путь:** `hermes setup --portal` — выполнить OAuth в Nous Portal и сразу включить [Tool Gateway](../user-guide/features/tool-gateway.md).

**Первый запуск:** открывает мастер первого запуска.

**Возвратившийся пользователь (уже сконфигурирован):** сразу переходит к полному мастеру переустановки — каждый запрос показывает текущее значение как значение по умолчанию, нажми **Enter**, чтобы оставить его, или введи новое значение. Меню нет.

Перейти к отдельному разделу вместо полного мастера:

| Раздел | Описание |
|--------|----------|
| `model` | Настройка провайдера и модели. |
| `terminal` | Настройка бэкенда терминала и песочницы. |
| `gateway` | Настройка платформы обмена сообщениями. |
| `tools` | Включение/отключение инструментов для каждой платформы. |
| `agent` | Параметры поведения агента. |

Опции:

| Опция | Описание |
|-------|----------|
| `--quick` | Для возвращающегося пользователя: запрашивает только недостающие или неустановленные параметры. Пропускает уже сконфигурированные элементы. |
| `--non-interactive` | Использовать значения по умолчанию / из окружения без запросов. |
| `--reset` | Сбросить конфигурацию к значениям по умолчанию перед настройкой. |
| `--reconfigure` | Псевдоним для обратной совместимости — теперь обычный `hermes setup` в существующей установке делает это по умолчанию. |
| `--portal` | Одноразовая настройка Nous Portal: вход через OAuth, установка Nous в качестве провайдера вывода и включение [Tool Gateway](../user-guide/features/tool-gateway.md). Пропускает остальную часть мастера. |
## `hermes portal`

```bash
hermes portal [status|open|tools]
```

Проверь аутентификацию Nous Portal, маршрутизацию шлюза инструментов и открой страницу подписки. Вызов без подкоманды выполняет `status`.

| Subcommand | Description |
|------------|-------------|
| `status` (default) | Состояние аутентификации портала + сводка маршрутизации шлюза инструментов по каждому инструменту. Отображается, когда подкоманда не указана. |
| `open` | Открой `portal.nousresearch.com/manage-subscription` в браузере по умолчанию. |
| `tools` | Выведи список всех партнёров шлюза инструментов (Firecrawl, FAL, OpenAI TTS, Browser Use, Modal) и укажи, какие из них маршрутизируются через Nous. |

Для настройки самого шлюза смотри [Шлюз инструментов](../user-guide/features/tool-gateway.md). Для одноразового пути настройки смотри `hermes setup --portal` выше.
## `hermes whatsapp`

```bash
hermes whatsapp
```

Запускает процесс сопряжения/настройки WhatsApp, включая выбор режима и сопряжение через QR‑код.
## `hermes slack`

```bash
hermes slack manifest              # print manifest to stdout
hermes slack manifest --write      # write to ~/.hermes/slack-manifest.json
hermes slack manifest --slashes-only  # just the features.slash_commands array
```

Создаёт манифест Slack‑приложения, который регистрирует каждую команду шлюза из
`COMMAND_REGISTRY` (`/btw`, `/stop`, `/model`, …) как полноценную
slash‑команду Slack — что обеспечивает соответствие с Discord и Telegram. Вставь
вывод в конфигурацию своего Slack‑приложения по адресу
[https://api.slack.com/apps](https://api.slack.com/apps) → твое приложение →
**Features → App Manifest → Edit**, затем **Save**. Slack предложит переустановить
приложение, если изменились области доступа или slash‑команды.

| Flag | Default | Purpose |
|------|---------|---------|
| `--write [PATH]` | stdout | Записать в файл вместо stdout. Параметр `--write` без пути записывает в `$HERMES_HOME/slack-manifest.json`. |
| `--name NAME` | `Hermes` | Отображаемое имя бота в Slack. |
| `--description DESC` | default blurb | Описание бота, отображаемое в каталоге приложений Slack. |
| `--slashes-only` | off | Выводить только `features.slash_commands` для объединения с вручную поддерживаемым манифестом. |

Запусти `hermes slack manifest --write` снова после `hermes update`, чтобы
подхватить новые команды.
## `hermes send`

```bash
hermes send --to <target> "message text"
hermes send --to <target> --file <path>
echo "message" | hermes send --to <target>
hermes send --list [platform]
```

Отправляет одноразовое сообщение в настроенную платформу обмена сообщениями без запуска агента или цикла шлюза. Повторно использует уже сконфигурированные учётные данные шлюза (`~/.hermes/.env` + `~/.hermes/config.yaml`), поэтому операционные скрипты, cron‑задачи, хуки CI и демоны мониторинга могут публиковать обновления статуса без повторной реализации REST‑клиента каждой платформы.

Для платформ с токеном бота (Telegram, Discord, Slack, Signal, SMS, WhatsApp-CloudAPI) работающий шлюз не требуется — `hermes send` обращается напрямую к REST‑endpoint платформы. Платформы‑плагины, которым нужен постоянный адаптер, всё равно требуют живой шлюз.

| Option | Description |
|--------|-------------|
| `-t`, `--to <TARGET>` | Цель доставки. Форматы: `platform` (использует домашний канал), `platform:chat_id`, `platform:chat_id:thread_id` или `platform:#channel-name`. Примеры: `telegram`, `telegram:-1001234567890`, `discord:#ops`, `slack:C0123ABCD`, `signal:+15551234567`. |
| `-f`, `--file <PATH>` | Прочитать тело сообщения из `PATH`. Укажи `-`, чтобы принудительно читать из stdin. |
| `-s`, `--subject <LINE>` | Добавить строку темы/заголовка перед телом сообщения. |
| `-l`, `--list [platform]` | Вывести список настроенных целей по всем платформам (или только для указанной платформы). |
| `-q`, `--quiet` | Подавить вывод в stdout при успехе — удобно в скриптах (полагаться только на код выхода). |
| `--json` | Вывести сырые JSON‑результаты вместо человекочитаемого вывода. |

Если не указан позиционный аргумент `message` и не использован `--file`, `hermes send` читает из stdin, когда он не является TTY. Коды выхода: `0` при успехе, `1` при ошибке доставки/бэкенда, `2` при ошибках использования.

Examples:

```bash
hermes send --to telegram "deploy finished"
echo "RAM 92%" | hermes send --to telegram:-1001234567890
hermes send --to discord:#ops --file /tmp/report.md
hermes send --to slack:#eng --subject "[CI]" --file build.log
hermes send --list                  # all platforms
hermes send --list telegram         # filter by platform
```
## `hermes secrets`

```bash
hermes secrets bitwarden <subcommand>
hermes secrets bw <subcommand>          # short alias
```

Получать API‑ключи из внешнего менеджера секретов при запуске процесса вместо их хранения в `~/.hermes/.env`. В настоящее время поддерживается **Bitwarden Secrets Manager**. Полное руководство: [Bitwarden integration](../user-guide/secrets/bitwarden.md).

Подкоманды `bitwarden` (alias `bw`):

| Subcommand | Description |
|------------|-------------|
| `setup` | Интерактивный мастер: установить закреплённый бинарный файл `bws`, сохранить токен доступа и выбрать проект. Принимает `--project-id`, `--access-token` и `--server-url` для неинтерактивного использования. |
| `status` | Показать текущую конфигурацию, путь/версию бинарного файла и информацию о последнем получении. |
| `sync` | Получить секреты сейчас и сообщить, что изменилось. Добавьте `--apply`, чтобы действительно экспортировать секреты в окружение текущего shell (по умолчанию — пробный запуск). |
| `install` | Скачать и проверить закреплённый бинарный файл `bws`. `--force` пере‑скачивает даже если управляемая копия уже существует. |
| `disable` | Отключить интеграцию с Bitwarden. |
## `hermes migrate`

```bash
hermes migrate <type>
```

Диагностировать и (при необходимости) переписать активный `config.yaml`, заменив ссылки на устаревшие модели или устаревшие настройки. Перед любой переписью создаётся резервная копия оригинального `config.yaml` с отметкой времени (можно пропустить с помощью `--no-backup`).

| Subcommand | Description |
|------------|-------------|
| `xai` | Просканировать `config.yaml` на наличие ссылок на модели xAI, запланированные к снятию с поддержки 15 мая 2026 г., и (с `--apply`) переписать их на месте на официальные замены согласно руководству по миграции xAI. По умолчанию — пробный запуск. |

Общие флаги для подкоманд миграции:

| Flag | Description |
|------|-------------|
| `--apply` | Переписать `config.yaml` на месте (по умолчанию: пробный запуск, без записей). |
| `--no-backup` | Пропустить создание резервной копии `config.yaml` с отметкой времени при применении. |

> Не путать с `hermes claw migrate` (одноразовый импорт конфигурации OpenClaw в Hermes) — `hermes migrate` это команда верхнего уровня для переписывания конфигурации.
## `hermes proxy`

```bash
hermes proxy <subcommand>
```

Запусти локальный HTTP‑сервер, совместимый с OpenAI, который перенаправляет запросы к upstream‑провайдеру, аутентифицированному через OAuth (например, Nous Portal, xAI). Внешние приложения могут указывать прокси с любым токеном‑носителем; прокси добавит твои реальные OAuth‑учётные данные при отправке запроса. См. [Subscription Proxy](../user-guide/features/subscription-proxy.md) для полного руководства.

| Subcommand | Description |
|------------|-------------|
| `start` | Запустить прокси в интерактивном режиме. Флаги: `--provider <nous\|xai>` (по умолчанию `nous`), `--host <addr>` (по умолчанию `127.0.0.1`; используй `0.0.0.0`, чтобы открыть доступ в LAN), `--port <int>` (по умолчанию `8645`). |
| `status` | Показать, какие upstream‑провайдеры прокси готовы (учётные данные присутствуют, OAuth действителен). |
| `providers` | Вывести список доступных upstream‑провайдеров прокси. |
## `hermes security`

```bash
hermes security <subcommand>
```

Сканирование уязвимостей по запросу с использованием [OSV.dev](https://osv.dev). Охватывает виртуальное окружение Hermes (установленные дистрибутивы PyPI), зависимости Python, объявленные плагинами в `~/.hermes/plugins/`, и зафиксированные серверы `npx`/`uvx` MCP в `config.yaml`. Не сканирует глобально установленные пакеты и расширения редакторов/браузеров.

| Subcommand | Description |
|------------|-------------|
| `audit` | Выполнить одноразовый аудит цепочки поставок. |

`audit` flags:

| Flag | Default | Description |
|------|---------|-------------|
| `--json` | off | Выводить машиночитаемый JSON вместо человекочитаемого текста. |
| `--fail-on <level>` | `critical` | Завершать с ненулевым кодом, если любое обнаружение имеет указанную тяжесть (`low`, `moderate`, `high`, `critical`). |
| `--skip-venv` | off | Пропустить сканирование Python‑venv Hermes. |
| `--skip-plugins` | off | Пропустить сканирование файлов требований плагинов. |
| `--skip-mcp` | off | Пропустить сканирование зафиксированных серверов MCP в `config.yaml`. |
## `hermes login` / `hermes logout` *(Устарело)*

:::caution
`hermes login` удалён. Используй `hermes auth` для управления OAuth‑учётными данными, `hermes model` для выбора провайдера или `hermes setup` для полной интерактивной настройки.
:::
## `hermes auth`

Управляй пулами учётных данных для ротации ключей одного провайдера. См. [Пулы учётных данных](/user-guide/features/credential-pools) для полной документации.

```bash
hermes auth                                              # Interactive wizard
hermes auth list                                         # Show all pools
hermes auth list openrouter                              # Show specific provider
hermes auth add openrouter --api-key sk-or-v1-xxx        # Add API key
hermes auth add anthropic --type oauth                   # Add OAuth credential
hermes auth remove openrouter 2                          # Remove by index
hermes auth reset openrouter                             # Clear cooldowns
hermes auth status anthropic                             # Show auth status for a provider
hermes auth logout anthropic                             # Log out and clear stored auth state
hermes auth spotify                                      # Authenticate Hermes with Spotify via PKCE
```

Подкоманды: `add`, `list`, `remove`, `reset`, `status`, `logout`, `spotify`. При вызове без подкоманды запускает интерактивный мастер управления.
## `hermes status`

```bash
hermes status [--all] [--deep]
```

| Option | Описание |
|--------|----------|
| `--all` | Показать все детали в формате, пригодном для совместного использования, с удалёнными конфиденциальными данными. |
| `--deep` | Выполнить более глубокие проверки, которые могут занять больше времени. |
## `hermes cron`

```bash
hermes cron <list|create|edit|pause|resume|run|remove|status|tick>
```

| Subcommand | Description |
|------------|-------------|
| `list` | Показать запланированные задачи. |
| `create` / `add` | Создать запланированную задачу из подсказки, при желании прикрепив один или несколько **skill** через повторяющийся `--skill`. |
| `edit` | Обновить расписание задачи, подсказку, имя, способ доставки, количество повторов или прикреплённые **skill**. Поддерживает `--clear-skills`, `--add-skill` и `--remove-skill`. |
| `pause` | Приостановить задачу без её удаления. |
| `resume` | Возобновить приостановленную задачу и вычислить её следующий запуск. |
| `run` | Запустить задачу на следующем тике планировщика. |
| `remove` | Удалить запланированную задачу. |
| `status` | Проверить, работает ли планировщик **cron**. |
| `tick` | Выполнить ожидающие задачи один раз и завершить работу. |
## `hermes kanban`

```bash
hermes kanban [--board <slug>] <action> [options]
```

Доска совместной работы с несколькими профилями и проектами. Каждый экземпляр может хостить множество досок (по одной на проект, репозиторий или домен); каждая доска — отдельная очередь со своей SQLite‑БД и областью действия диспетчера. Новые установки начинают работу с одной доской под названием `default`, чья БД находится в `~/.hermes/kanban.db` для обратной совместимости; дополнительные доски размещаются в `~/.hermes/kanban/boards/<slug>/kanban.db`. Встроенный в шлюз диспетчер обходит каждую доску каждый тик.

**Глобальные флаги (применяются ко всем действиям ниже):**

| Флаг | Назначение |
|------|------------|
| `--board <slug>` | Работать с конкретной доской. По умолчанию — текущая доска (устанавливается через `hermes kanban boards switch`, переменную окружения `HERMES_KANBAN_BOARD` или `default`). |

**Это пользовательский / скриптовый интерфейс.** Рабочие агенты, порождённые диспетчером, управляют доской через специальный набор `kanban_*` [toolset](/user-guide/features/kanban#how-workers-interact-with-the-board) (`kanban_show`, `kanban_complete`, `kanban_block`, `kanban_create`, `kanban_link`, `kanban_comment`, `kanban_heartbeat`; у профилей‑оркестраторов также есть `kanban_list` и `kanban_unblock`) вместо вызова `hermes kanban`. У рабочих процессов в переменной окружения закреплён `HERMES_KANBAN_BOARD`, поэтому они физически не могут видеть другие доски.

| Действие | Назначение |
|----------|------------|
| `init` | Создать `kanban.db`, если её нет. Идемпотентно. |
| `boards list` / `boards ls` | Вывести список всех досок с количеством задач. `--json`, `--all` (включая архивированные). |
| `boards create <slug>` | Создать новую доску. Флаги: `--name`, `--description`, `--icon`, `--color`, `--switch` (сделать активной). `slug` записывается в kebab‑case, автоматически в нижний регистр. |
| `boards switch <slug>` / `boards use` | Сохранить `<slug>` как активную доску (записывается в `~/.hermes/kanban/current`). |
| `boards show` / `boards current` | Показать имя текущей доски, путь к БД и количество задач. |
| `boards rename <slug> "<name>"` | Изменить отображаемое имя доски. `slug` неизменяем. |
| `boards rm <slug>` | Архивировать (по умолчанию) или полностью удалить доску. `--delete` пропускает шаг архивации. Архивированные доски перемещаются в `boards/_archived/<slug>-<ts>/`. Для `default` запрещено. |
| `create "<title>"` | Создать новую задачу на активной доске. Флаги: `--body`, `--assignee`, `--parent` (повторяемый), `--workspace scratch\|worktree\|dir:<path>`, `--tenant`, `--priority`, `--triage`, `--idempotency-key`, `--max-runtime`, `--max-retries`, `--skill` (повторяемый). |
| `list` / `ls` | Вывести список задач на активной доске. Фильтры: `--mine`, `--assignee`, `--status`, `--tenant`, `--archived`, `--json`. |
| `show <id>` | Показать задачу с комментариями и событиями. `--json` — машинный вывод. |
| `assign <id> <profile>` | Назначить или переназначить. Используй `none` для снятия назначения. Запрещено, пока задача выполняется. |
| `link <parent> <child>` | Добавить зависимость. Обнаруживает циклы. Обе задачи должны находиться на одной доске. |
| `unlink <parent> <child>` | Удалить зависимость. |
| `claim <id>` | Атомарно захватить готовую задачу. Выводит разрешённый путь рабочего пространства. |
| `comment <id> "<text>"` | Добавить комментарий. Следующий рабочий процесс, захвативший задачу, прочитает его как часть ответа `kanban_show()`. |
| `complete <id>` | Отметить задачу выполненной. Флаги: `--result`, `--summary`, `--metadata`. |
| `block <id> "<reason>"` | Пометить задачу как заблокированную для человеческого ввода. Также добавляет причину как комментарий. |
| `schedule <id> "<reason>"` | Переместить задачу в `scheduled` как отложенную работу, чтобы она не отображалась как человеческий блокировщик. |
| `unblock <id>` | Вернуть заблокированную или запланированную задачу в состояние готовности (или `todo`, если зависимости всё ещё открыты). |
| `archive <id>` | Скрыть из списка по умолчанию. `gc` удалит временные рабочие пространства. |
| `tail <id>` | Следить за потоком событий задачи. |
| `dispatch` | Один проход диспетчера по активной доске. Флаги: `--dry-run`, `--max N`, `--failure-limit N`, `--json`. |
| `context <id>` | Вывести полный контекст, который увидит рабочий процесс (заголовок + тело + результаты родителей + комментарии). |
| `specify <id>` / `specify --all` | Превратить задачу из колонки триажа в конкретную спецификацию (заголовок + тело с целью, подходом, критериями приёмки) с помощью вспомогательного LLM, затем продвинуть её в `todo`. Флаги: `--tenant` (ограничивает `--all` одним арендатором), `--author`, `--json`. Модель настраивается в `auxiliary.triage_specifier` в `config.yaml`. |
| `decompose <id>` / `decompose --all` | Разбить задачу из колонки триажа на граф дочерних задач, распределённых по специализированным профилям по описанию (путь, управляемый оркестратором). При отсутствии выгоды от раскрутки LLM откатывается к одношаговому продвижению в стиле `specify`. Те же флаги, что и у `specify`. Модель настраивается в `auxiliary.kanban_decomposer` в `config.yaml`. Также автоматически запускается каждый тик диспетчера, когда `kanban.auto_decompose: true` (по умолчанию). См. [Auto vs Manual orchestration](/user-guide/features/kanban#auto-vs-manual-orchestration). |
| `gc` | Удалить временные рабочие пространства для архивированных задач. |

Примеры:

```bash
# Create a second board and put a task on it without switching away.
hermes kanban boards create atm10-server --name "ATM10 Server" --icon 🎮
hermes kanban --board atm10-server create "Restart server" --assignee ops

# Switch the active board for subsequent calls.
hermes kanban boards switch atm10-server
hermes kanban list                  # shows atm10-server tasks

# Archive a board (recoverable) or hard-delete it.
hermes kanban boards rm atm10-server
hermes kanban boards rm atm10-server --delete
```

Порядок разрешения доски (высший приоритет первым): флаг `--board <slug>` → переменная окружения `HERMES_KANBAN_BOARD` → файл `~/.hermes/kanban/current` → `default`.

Все действия также доступны как слеш‑команда в шлюзе (`/kanban …`), с тем же набором аргументов — включая подкоманды `boards` и флаг `--board`.

Для полного описания — сравнение с Cline Kanban / Paperclip / NanoClaw / Gemini Enterprise, восемь паттернов совместной работы, четыре пользовательские истории, доказательство корректности конкурентности — см. `docs/hermes-kanban-v1-spec.pdf` в репозитории или [Kanban user guide](/user-guide/features/kanban).
## `hermes webhook`

```bash
hermes webhook <subscribe|list|remove|test>
```

Управляй динамическими подписками webhook для активации агента по событиям. Требует, чтобы платформа webhook была включена в конфигурации — если не настроена, выводит инструкции по установке.

| Subcommand | Description |
|------------|-------------|
| `subscribe` / `add` | Создать маршрут webhook. Возвращает URL и HMAC‑секрет для настройки в твоём сервисе. |
| `list` / `ls` | Показать все подписки, созданные агентом. |
| `remove` / `rm` | Удалить динамическую подписку. Статические маршруты из `config.yaml` не затрагиваются. |
| `test` | Отправить тестовый POST, чтобы проверить работу подписки. |

### `hermes webhook subscribe`

```bash
hermes webhook subscribe <name> [options]
```

| Option | Description |
|--------|-------------|
| `--prompt` | Шаблон подсказки с ссылками на данные `{dot.notation}`. |
| `--events` | Список типов событий через запятую, которые принимать (например `issues,pull_request`). Пусто = все. |
| `--description` | Человекочитаемое описание. |
| `--skills` | Список названий skill через запятую, которые загрузить для выполнения агента. |
| `--deliver` | Цель доставки: `log` (по умолчанию), `telegram`, `discord`, `slack`, `github_comment`. |
| `--deliver-chat-id` | ID чата/канала‑получателя для кроссплатформенной доставки. |
| `--secret` | Пользовательский HMAC‑секрет. Генерируется автоматически, если не указан. |
| `--deliver-only` | Пропустить агента — доставить отрендеренный `--prompt` как буквальное сообщение. Нулевые затраты LLM, доставка за доли секунды. Требует, чтобы `--deliver` был реальной целью (не `log`). |

Подписки сохраняются в `~/.hermes/webhook_subscriptions.json` и автоматически подгружаются адаптером webhook без перезапуска gateway.
## `hermes doctor`

```bash
hermes doctor [--fix]
```

| Option | Description |
|--------|-------------|
| `--fix` | Попытаться выполнить автоматический ремонт, если это возможно. |
## `hermes dump`

```bash
hermes dump [--show-keys]
```

Выводит компактный plain‑text‑отчёт о всей конфигурации Hermes. Предназначен для копирования в Discord, GitHub‑issues или Telegram при запросе поддержки — без ANSI‑цветов, без специального форматирования, только данные.

| Опция | Описание |
|-------|----------|
| `--show-keys` | Показывать замаскированные префиксы API‑ключей (первые и последние 4 символа) вместо простого `set`/`not set`. |

### Что включено

| Раздел | Подробности |
|--------|-------------|
| **Header** | Версия Hermes, дата релиза, хеш коммита git |
| **Environment** | ОС, версия Python, версия SDK OpenAI |
| **Identity** | Имя активного профиля, путь HERMES_HOME |
| **Model** | Настроенная модель по умолчанию и провайдер |
| **Terminal** | Тип бэкенда (local, docker, ssh и др.) |
| **API keys** | Проверка наличия всех 22 ключей API провайдеров/инструментов |
| **Features** | Включённые наборы инструментов, количество серверов MCP, провайдер памяти |
| **Services** | Состояние шлюза, настроенные платформы обмена сообщениями |
| **Workload** | Количество cron‑задач, количество установленных навыков |
| **Config overrides** | Любые значения конфигурации, отличающиеся от значений по умолчанию |

### Пример вывода

```
--- hermes dump ---
version:          0.8.0 (2026.4.8) [af4abd2f]
os:               Linux 6.14.0-37-generic x86_64
python:           3.11.14
openai_sdk:       2.24.0
profile:          default
hermes_home:      ~/.hermes
model:            anthropic/claude-opus-4.6
provider:         openrouter
terminal:         local

api_keys:
  openrouter           set
  openai               not set
  anthropic            set
  nous                 not set
  firecrawl            set
  ...

features:
  toolsets:           all
  mcp_servers:        0
  memory_provider:    built-in
  gateway:            running (systemd)
  platforms:          telegram, discord
  cron_jobs:          3 active / 5 total
  skills:             42

config_overrides:
  agent.max_turns: 250
  compression.threshold: 0.85
  display.streaming: True
--- end dump ---
```

### Когда использовать

- При сообщении об ошибке на GitHub — вставь дамп в свой issue
- При запросе помощи в Discord — размести его в блоке кода
- Для сравнения своей конфигурации с чужой
- Быстрая проверка работоспособности, когда что‑то не работает

:::tip
`hermes dump` специально создан для обмена информацией. Для интерактивной диагностики используй `hermes doctor`. Для визуального обзора — `hermes status`.
:::
## `hermes debug`

```bash
hermes debug share [options]
```

Загрузи отчёт отладки (системная информация + последние журналы) в сервис вставок и получи URL для совместного доступа. Полезно для быстрых запросов поддержки — включает всё, что понадобится помощнику для диагностики проблемы.

| Option | Description |
|--------|-------------|
| `--lines <N>` | Количество строк журнала, включаемых из каждого файла (по умолчанию: 200). |
| `--expire <days>` | Срок действия вставки в днях (по умолчанию: 7). |
| `--local` | Вывести отчёт локально вместо загрузки. |

Отчёт включает системную информацию (OS, версия Python, версия Hermes), последние журналы агента и gateway (лимит 512 KB на файл), а также статус скрытых API‑ключей. Ключи всегда скрыты — секреты не загружаются.

Сервисы вставок проверяются в следующем порядке: paste.rs, dpaste.com.

### Примеры

```bash
hermes debug share              # Upload debug report, print URL
hermes debug share --lines 500  # Include more log lines
hermes debug share --expire 30  # Keep paste for 30 days
hermes debug share --local      # Print report to terminal (no upload)
```
## `hermes backup`

```bash
hermes backup [options]
```

Создай zip‑архив с конфигурацией Hermes, навыками, сессиями и данными. Резервная копия не включает сам код `hermes-agent`.

| Option | Description |
|--------|-------------|
| `-o`, `--output <path>` | Путь для сохранения zip‑файла (по умолчанию: `~/hermes-backup-<timestamp>.zip`). |
| `-q`, `--quick` | Быстрый снимок: только критически важные файлы состояния (`config.yaml`, `state.db`, `.env`, `auth`, cron‑задачи). Работает гораздо быстрее, чем полная резервная копия. |
| `-l`, `--label <name>` | Метка для снимка (используется только с `--quick`). |

Резервное копирование использует API `backup()` SQLite для безопасного копирования, поэтому работает корректно даже когда Hermes запущен (безопасно в режиме WAL).

**Что исключено из zip‑файла:**

- `*.db-wal`, `*.db-shm`, `*.db-journal` — вспомогательные файлы WAL / shared‑memory / journal SQLite. Файл `*.db` уже получен согласованным снимком через `sqlite3.backup()`; включение живых вспомогательных файлов привело бы к восстановлению в полузакоммиченном состоянии.
- `checkpoints/` — кэши траекторий по сессиям. Хэш‑ключированы и регенерируются для каждой сессии; перенос их в другую установку невозможен.
- Сам код `hermes-agent` (это резервная копия пользовательских данных, а не снимок репозитория).

### Примеры

```bash
hermes backup                           # Full backup to ~/hermes-backup-*.zip
hermes backup -o /tmp/hermes.zip        # Full backup to specific path
hermes backup --quick                   # Quick state-only snapshot
hermes backup --quick --label "pre-upgrade"  # Quick snapshot with label
```
## `hermes checkpoints`

```bash
hermes checkpoints [COMMAND]
```

Просматривай и управляй теневым git‑хранилищем в `~/.hermes/checkpoints/` — слоем хранения, лежащим в основе команды сессии `/rollback`. Можно запускать в любое время; не требует запущенного агента.

| Subcommand | Description |
|------------|-------------|
| `status` (default) | Показать общий размер, количество проектов и разбивку по проектам. Эквивалентно просто `hermes checkpoints`. |
| `list` | Псевдоним для `status`. |
| `prune` | Принудительно выполнить очистку — удалить осиротевшие и устаревшие проекты, собрать мусор в хранилище, применить ограничение по размеру. Игнорирует 24‑часовой маркер идемпотентности. |
| `clear` | Удалить всё хранилище контрольных точек. Необратимо; запрашивает подтверждение, если не указан `-f`. |
| `clear-legacy` | Удалить только архивы `legacy-<timestamp>/`, созданные при миграции v1→v2. |

### Options

| Option | Subcommand | Description |
|--------|------------|-------------|
| `--limit N` | `status`, `list` | Максимальное количество проектов для вывода (по умолчанию 20). |
| `--retention-days N` | `prune` | Удалить проекты, у которых `last_touch` старше N дней (по умолчанию 7). |
| `--max-size-mb N` | `prune` | После обработки осиротевших и устаревших проектов удалить самые старые коммиты в каждом проекте, пока общий размер хранилища не станет ≤ N МБ (по умолчанию 500). |
| `--keep-orphans` | `prune` | Не удалять проекты, у которых рабочий каталог больше не существует. |
| `-f`, `--force` | `clear`, `clear-legacy` | Пропустить запрос подтверждения. |

### Examples

```bash
hermes checkpoints                                  # status overview
hermes checkpoints prune --retention-days 3         # aggressive cleanup
hermes checkpoints prune --max-size-mb 200          # tighten size cap once
hermes checkpoints clear-legacy -f                  # drop v1 archive dirs
hermes checkpoints clear -f                         # wipe everything
```

См. [Checkpoints and `/rollback`](../user-guide/checkpoints-and-rollback.md) для полного описания архитектуры и команд сессии.
## `hermes import`

```bash
hermes import <zipfile> [options]
```

Восстанавливает ранее созданную резервную копию Hermes в каталог Hermes home. Все файлы из архива перезаписывают существующие файлы в каталоге Hermes home; `--force` лишь пропускает запрос подтверждения, который появляется, когда в целевом каталоге уже установлена Hermes.

| Option | Description |
|--------|-------------|
| `-f`, `--force` | Пропустить запрос подтверждения при существующей установке. |

:::warning
Останови gateway перед импортом, чтобы избежать конфликтов с работающими процессами.
:::

### Примеры
```bash
hermes import ~/hermes-backup-20260423.zip           # Prompts before overwriting existing config
hermes import ~/hermes-backup-20260423.zip --force   # Overwrite without prompting
```
## `hermes logs`

```bash
hermes logs [log_name] [options]
```

Просмотр, хвост и фильтрация файлов журналов Hermes. Все журналы хранятся в `~/.hermes/logs/` (или `<profile>/logs/` для профилей, отличных от стандартного).

### Файлы журналов

| Name | File | What it captures |
|------|------|-----------------|
| `agent` (default) | `agent.log` | Вся активность агента — вызовы API, отправка инструментов, жизненный цикл сессии (INFO и выше) |
| `errors` | `errors.log` | Только предупреждения и ошибки — отфильтрованная часть `agent.log` |
| `gateway` | `gateway.log` | Активность шлюза сообщений — соединения платформ, отправка сообщений, события веб‑хуков |

### Параметры

| Option | Description |
|--------|-------------|
| `log_name` | Какой журнал просматривать: `agent` (по умолчанию), `errors`, `gateway` или `list` — показать доступные файлы с их размерами. |
| `-n`, `--lines <N>` | Количество строк для вывода (по умолчанию: 50). |
| `-f`, `--follow` | Следить за журналом в реальном времени, как `tail -f`. Нажми Ctrl+C — остановить. |
| `--level <LEVEL>` | Минимальный уровень журнала для отображения: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. |
| `--session <ID>` | Фильтровать строки, содержащие подстроку идентификатора сессии. |
| `--since <TIME>` | Показать строки, начиная с относительного времени назад: `30m`, `1h`, `2d` и т.д. Поддерживаются `s` (секунды), `m` (минуты), `h` (часы), `d` (дни). |
| `--component <NAME>` | Фильтровать по компоненту: `gateway`, `agent`, `tools`, `cli`, `cron`. |

### Примеры

```bash
# View the last 50 lines of agent.log (default)
hermes logs

# Follow agent.log in real time
hermes logs -f

# View the last 100 lines of gateway.log
hermes logs gateway -n 100

# Show only warnings and errors from the last hour
hermes logs --level WARNING --since 1h

# Filter by a specific session
hermes logs --session abc123

# Follow errors.log, starting from 30 minutes ago
hermes logs errors --since 30m -f

# List all log files with their sizes
hermes logs list
```

### Фильтрация

Фильтры можно комбинировать. Когда активно несколько фильтров, строка журнала должна удовлетворять **всем** из них, чтобы быть показанной:

```bash
# WARNING+ lines from the last 2 hours containing session "tg-12345"
hermes logs --level WARNING --since 2h --session tg-12345
```

Строки без разбираемого временного штампа включаются, когда активен `--since` (это могут быть продолжения многострочных записей). Строки без определяемого уровня включаются, когда активен `--level`.

### Ротация журналов

Hermes использует `RotatingFileHandler` из Python. Старые журналы автоматически ротируются — ищи `agent.log.1`, `agent.log.2` и т.д. Подкоманда `hermes logs list` выводит все файлы журналов, включая ротированные.
## `hermes config`

```bash
hermes config <subcommand>
```

Подкоманды:

| Подкоманда | Описание |
|------------|----------|
| `show` | Показать текущие значения конфигурации. |
| `edit` | Открыть `config.yaml` в твоём редакторе. |
| `set <key> <value>` | Установить значение конфигурации. |
| `path` | Вывести путь к файлу конфигурации. |
| `env-path` | Вывести путь к файлу `.env`. |
| `check` | Проверить наличие отсутствующих или устаревших параметров конфигурации. |
| `migrate` | Добавить недавно введённые параметры интерактивно. |
## `hermes pairing`

```bash
hermes pairing <list|approve|revoke|clear-pending>
```

| Подкоманда | Описание |
|------------|----------|
| `list` | Показать ожидающих и одобренных пользователей. |
| `approve <platform> <code>` | Одобрить код сопряжения. |
| `revoke <platform> <user-id>` | Отозвать доступ пользователя. |
| `clear-pending` | Очистить ожидающие коды сопряжения. |
## `hermes skills`

```bash
hermes skills <subcommand>
```

Подкоманды:

| Подкоманда | Описание |
|------------|----------|
| `browse` | Постраничный браузер реестров навыков. |
| `search` | Поиск в реестрах навыков. |
| `install` | Установить навык. |
| `inspect` | Предпросмотр навыка без установки. |
| `list` | Вывести список установленных навыков. |
| `check` | Проверить установленные hub‑навыки на наличие обновлений upstream. |
| `update` | Переустановить hub‑навыки с изменениями upstream, если они доступны. |
| `audit` | Повторно просканировать установленные hub‑навыки. |
| `uninstall` | Удалить навык, установленный через hub. |
| `reset` | Снять привязку у объединённого навыка, помеченного как `user_modified`, очистив его запись в манифесте. С `--restore` также заменяет пользовательскую копию на объединённую версию. |
| `publish` | Опубликовать навык в реестре. |
| `snapshot` | Экспортировать/импортировать конфигурацию навыков. |
| `tap` | Управлять пользовательскими источниками навыков. |
| `config` | Интерактивно включать/выключать конфигурацию навыков по платформе. |

Общие примеры:

```bash
hermes skills browse
hermes skills browse --source official
hermes skills search react --source skills-sh
hermes skills search https://mintlify.com/docs --source well-known
hermes skills inspect official/security/1password
hermes skills inspect skills-sh/vercel-labs/json-render/json-render-react
hermes skills install official/migration/openclaw-migration
hermes skills install skills-sh/anthropics/skills/pdf --force
hermes skills install https://sharethis.chat/SKILL.md                     # Direct URL (single-file SKILL.md)
hermes skills install https://example.com/SKILL.md --name my-skill        # Override name when frontmatter has none
hermes skills check
hermes skills update
hermes skills config
hermes skills reset google-workspace
hermes skills reset google-workspace --restore --yes
```

Примечания:
- `--force` может переопределять неопасные блокировки политики для сторонних/сообщества навыков.
- `--force` не переопределяет вердикт сканирования `dangerous`.
- `--source skills-sh` ищет в публичном каталоге `skills.sh`.
- `--source well-known` позволяет указать Hermes сайт, раскрывающий `/.well-known/skills/index.json`.
- `--source browse-sh` ищет в каталоге [browse.sh](https://browse.sh) более 200 специфичных для сайтов навыков автоматизации браузера. Идентификаторы выглядят как `browse-sh/airbnb.com/search-listings-ddgioa`.
- Передача URL `http(s)://…/*.md` устанавливает одиночный файл `SKILL.md` напрямую. Если во frontmatter нет `name:` и slug URL не является допустимым идентификатором, интерактивный терминал запрашивает имя; в неинтерактивных средах (`/skills install` внутри TUI, платформы gateway) требуется `--name <x>`.
## `hermes bundles`

```bash
hermes bundles <subcommand>
```

Skill bundles группируют несколько навыков под одной slash‑командой `/<bundle-name>`. При вызове пакета загружаются все указанные навыки в одно объединённое сообщение пользователя. Хранилище: `~/.hermes/skill-bundles/<slug>.yaml`. См. [Skill Bundles](../user-guide/features/skills.md#skill-bundles) для схемы YAML и поведения.

Подкоманды:

| Subcommand | Description |
|------------|-------------|
| `list` | Вывести список установленных пакетов (по умолчанию, если подкоманда не указана) |
| `show <name>` | Показать имя пакета, описание, навыки и путь к файлу |
| `create <name>` | Создать новый пакет. Передай `--skill <id>` (можно несколько раз) или пропусти для интерактивного ввода. Доступны `--description`, `--instruction`, `--force`. |
| `delete <name>` | Удалить файл пакета |
| `reload` | Пересканировать `~/.hermes/skill-bundles/` и сообщить о добавленных/удалённых пакетах |

Примеры:

```bash
hermes bundles create backend-dev \
  --skill github-code-review \
  --skill test-driven-development \
  --skill github-pr-workflow \
  -d "Backend feature work"

hermes bundles list
hermes bundles show backend-dev
hermes bundles delete backend-dev
```

В сессии чата команда `/bundles` выводит список установленных пакетов, а `/<bundle-name>` загружает один из них.
## `hermes curator`

```bash
hermes curator <subcommand>
```

Куратор — это вспомогательная модель‑задача, которая периодически просматривает созданные агентом **skills**, удаляет устаревшие, консолидирует дубли и архивирует устаревшие **skills**. **Skills**, поставляемые в комплекте и установленные через hub, никогда не трогаются. Архивы восстанавливаемы; автоматическое удаление не происходит.

| Subcommand | Description |
|------------|-------------|
| `status` | Показать статус куратора и статистику **skills** |
| `run` | Запустить проверку куратора сейчас (блокирует процесс до завершения прохода LLM) |
| `run --background` | Запустить проход LLM в фоновом потоке и сразу вернуть управление |
| `run --dry-run` | Только предварительный просмотр — создать отчёт проверки без изменений |
| `backup` | Сделать ручной снимок `~/.hermes/skills/` в виде tar.gz (куратор также автоматически делает снимок перед каждым реальным запуском) |
| `rollback` | Восстановить `~/.hermes/skills/` из снимка (по умолчанию — самый новый) |
| `rollback --list` | Показать доступные снимки |
| `rollback --id <ts>` | Восстановить конкретный снимок по идентификатору |
| `rollback -y` | Пропустить запрос подтверждения |
| `pause` | Приостановить куратора до возобновления |
| `resume` | Возобновить работу приостановленного куратора |
| `pin <skill>` | Закрепить **skill**, чтобы куратор никогда не переводил его автоматически |
| `unpin <skill>` | Снять закрепление с **skill** |
| `restore <skill>` | Восстановить архивированный **skill** |
| `archive <skill>` | Архивировать **skill** вручную |
| `prune` | Вручную удалить **skills**, которые куратор обычно удалял бы сам |
| `list-archived` | Показать архивированные **skills** (восстанавливаемые через `restore`) |

При свежей установке первый запланированный проход откладывается на полный `interval_hours` (по умолчанию — 7 дней) — шлюз не будет выполнять работу куратора сразу после первого тика после `hermes update`. Используй `hermes curator run --dry-run`, чтобы увидеть предварительный результат перед этим.

См. [Curator](../user-guide/features/curator.md) для описания поведения и настроек.
## `hermes fallback`

```bash
hermes fallback <subcommand>
```

Управляй цепочкой запасных провайдеров. Запасные провайдеры проверяются последовательно, когда основная модель завершается ошибкой ограничения скорости, перегрузки или ошибок соединения.

| Subcommand | Description |
|------------|-------------|
| `list` (alias: `ls`) | Показать текущую цепочку запасных вариантов (по умолчанию, если не указана подкоманда) |
| `add` | Выбрать провайдера + модель (тот же селектор, что и в `hermes model`) и добавить в конец цепочки |
| `remove` (alias: `rm`) | Выбрать запись для удаления из цепочки |
| `clear` | Удалить все записи запасных вариантов |

See [Fallback Providers](../user-guide/features/fallback-providers.md).
## `hermes hooks`

```bash
hermes hooks <subcommand>
```

Просматривай скриптовые хуки оболочки, объявленные в `~/.hermes/config.yaml`, тестируй их на синтетических payload и управляй белым списком согласий при первом использовании в `~/.hermes/shell-hooks-allowlist.json`.

| Подкоманда | Описание |
|------------|----------|
| `list` (alias: `ls`) | Вывести список настроенных хуков с matcher, тайм‑аутом и статусом согласия |
| `test <event>` | Запустить каждый хук, соответствующий `<event>`, на синтетическом payload |
| `revoke` (aliases: `remove`, `rm`) | Удалить записи из белого списка согласий для команды (вступает в силу после перезапуска) |
| `doctor` | Проверить каждый настроенный хук: бит исполняемости, белый список согласий, отклонение времени изменения, валидность JSON и время выполнения синтетического запуска |

См. [Хуки](../user-guide/features/hooks.md) для сигнатур событий и форматов payload.
## `hermes memory`

```bash
hermes memory <subcommand>
```

Настройка и управление плагинами внешних провайдеров памяти. Доступные провайдеры: honcho, openviking, mem0, hindsight, holographic, retaindb, byterover, supermemory. Одновременно может быть активен только один внешний провайдер. Встроенная память (MEMORY.md/USER.md) всегда активна.

Подкоманды:

| Подкоманда | Описание |
|------------|----------|
| `setup` | Интерактивный выбор провайдера и его конфигурация. |
| `status` | Показать текущую конфигурацию провайдера памяти. |
| `off` | Отключить внешний провайдер (только встроенная). |

:::info Подкоманды, специфичные для провайдера
Когда активен внешний провайдер памяти, он может зарегистрировать свою собственную команду верхнего уровня `hermes <provider>` для управления, специфичного для провайдера (например, `hermes honcho`, когда активен Honcho). Неактивные провайдеры не раскрывают свои подкоманды. Выполни `hermes --help`, чтобы увидеть, что сейчас подключено.
:::
## `hermes acp`

```bash
hermes acp
```

Запускает Hermes в качестве stdio‑сервера ACP (Agent Client Protocol) для интеграции с редактором.

Связанные точки входа:

```bash
hermes-acp
python -m acp_adapter
```

Сначала установи поддержку:

```bash
pip install -e '.[acp]'
```

См. [Интеграция редактора ACP](../user-guide/features/acp.md) и [Внутреннее устройство ACP](../developer-guide/acp-internals.md).
## `hermes mcp`

```bash
hermes mcp <subcommand>
```

Управляй конфигурациями сервера MCP (Model Context Protocol) и запускай Hermes в режиме сервера MCP.

| Subcommand | Description |
|------------|-------------|
| *(none)* or `picker` | Интерактивный выбор каталога — просматривай одобренные Nous MCP и устанавливай/включай/выключай их. |
| `catalog` | Вывести список одобренных Nous MCP (обычный текст, пригодный для скриптов). |
| `install <name>` | Установить запись из каталога (например `hermes mcp install n8n`). |
| `serve [-v\|--verbose]` | Запустить Hermes как сервер MCP — открыть доступ к разговорам для других агентов. |
| `add <name> [--url URL] [--command CMD] [--args ...] [--auth oauth\|header]` | Добавить пользовательский сервер MCP с автоматическим обнаружением инструментов. |
| `remove <name>` (alias: `rm`) | Удалить сервер MCP из конфигурации. |
| `list` (alias: `ls`) | Показать список настроенных серверов MCP. |
| `test <name>` | Проверить соединение с сервером MCP. |
| `configure <name>` (alias: `config`) | Переключить выбор инструментов для сервера. |
| `login <name>` | Принудительно выполнить повторную аутентификацию для сервера MCP на основе OAuth. |

См. [MCP Config Reference](./mcp-config-reference.md), [Use MCP with Hermes](../guides/use-mcp-with-hermes.md) и [MCP Server Mode](../user-guide/features/mcp.md#running-hermes-as-an-mcp-server).
## `hermes plugins`

```bash
hermes plugins [subcommand]
```

Единое управление плагинами — общие плагины, провайдеры памяти и движки контекста в одном месте. Запуск `hermes plugins` без подкоманды открывает составной интерактивный UI с двумя секциями:

- **General Plugins** — флажки множественного выбора для включения/отключения установленных плагинов
- **Provider Plugins** — одиночный выбор конфигурации для Memory Provider и Context Engine. Нажми **ENTER** на категории, чтобы открыть радиовыбор.

| Subcommand | Description |
|------------|-------------|
| *(none)* | Составной интерактивный UI — переключатели общих плагинов + конфигурация плагина‑провайдера. |
| `install <identifier> [--force]` | Установить плагин из Git‑URL или `owner/repo`. |
| `update <name>` | Получить последние изменения установленного плагина. |
| `remove <name>` (aliases: `rm`, `uninstall`) | Удалить установленный плагин. |
| `enable <name>` | Включить отключённый плагин. |
| `disable <name>` | Отключить плагин без его удаления. |
| `list` (alias: `ls`) | Вывести список установленных плагинов со статусом включён/отключён. |

Выбор провайдера плагина сохраняется в `config.yaml`:
- `memory.provider` — активный провайдер памяти (пусто = только встроенный)
- `context.engine` — активный движок контекста (`"compressor"` = встроенный по умолчанию)

Список отключённых общих плагинов хранится в `config.yaml` под `plugins.disabled`.

См. [Plugins](../user-guide/features/plugins.md) и [Build a Hermes Plugin](../guides/build-a-hermes-plugin.md).
## `hermes tools`

```bash
hermes tools [--summary]
```

| Опция | Описание |
|--------|-------------|
| `--summary` | Вывести текущий сводный список включённых инструментов и завершить работу. |

Без `--summary` запускается интерактивный пользовательский интерфейс настройки инструментов по платформам.
## `hermes computer-use`

```bash
hermes computer-use <subcommand>
```

Подкоманды:

| Подкоманда | Описание |
|------------|----------|
| `install` | Запускает установщик upstream‑cua‑driver (только macOS). |
| `install --upgrade` | Повторно запускает установщик, даже если `cua-driver` уже находится в `$PATH`. Скрипт upstream всегда загружает последнюю версию, поэтому это выполняет обновление «на месте». |
| `status` | Выводит, находится ли `cua-driver` в `$PATH` и какая версия установлена. |

`hermes computer-use install` — стабильная точка входа для установки бинарного файла [cua-driver](https://github.com/trycua/cua), используемого набором инструментов `computer_use`. Он запускает тот же установщик upstream, который вызывается командой `hermes tools` при первом включении Computer Use, поэтому его безопасно использовать для повторного запуска установки, если переключатель набора инструментов не сработал (например, в настройках возвращающихся пользователей).

`hermes update` автоматически повторно запускает установщик upstream в конце обновления, если `cua-driver` находится в `$PATH`, поэтому большинству пользователей не требуется вручную вызывать `--upgrade`. Используй его, когда upstream выпускает исправление, которое тебе нужно прямо сейчас, не дожидаясь следующего обновления Hermes.
## `hermes sessions`

```bash
hermes sessions <subcommand>
```

Подкоманды:

| Подкоманда | Описание |
|------------|----------|
| `list` | Вывести список недавних сессий. |
| `browse` | Интерактивный выбор сессии с возможностью поиска и возобновления. |
| `export <output> [--session-id ID]` | Экспортировать сессии в JSONL. |
| `delete <session-id>` | Удалить одну сессию. |
| `prune` | Очистить старые сессии. |
| `stats` | Показать статистику хранилища сессий. |
| `rename <session-id> <title>` | Установить или изменить заголовок сессии. |
## `hermes insights`

```bash
hermes insights [--days N] [--source platform]
```

| Опция | Описание |
|--------|-------------|
| `--days <n>` | Анализировать последние `n` дней (по умолчанию — 30). |
| `--source <platform>` | Отфильтровать по источнику, например `cli`, `telegram` или `discord`. |
## `hermes claw`

```bash
hermes claw migrate [options]
```

Перенеси свою конфигурацию OpenClaw в Hermes. Читает из `~/.openclaw` (или указанного пути) и пишет в `~/.hermes`. Автоматически обнаруживает устаревшие имена каталогов (`~/.clawdbot`, `~/.moltbot`) и файлы конфигураций (`clawdbot.json`, `moltbot.json`).

| Option | Description |
|--------|-------------|
| `--dry-run` | Предпросмотр того, что будет перенесено, без записи. |
| `--preset <name>` | Пресет миграции: `full` (все совместимые настройки) или `user-data` (исключает конфигурацию инфраструктуры). Ни один пресет не импортирует секреты — передай `--migrate-secrets` явно. |
| `--overwrite` | Перезаписать существующие файлы Hermes при конфликтах (по умолчанию — отказ от применения, если план содержит конфликты). |
| `--migrate-secrets` | Включить API‑ключи в миграцию. Требуется даже при `--preset full`. |
| `--no-backup` | Пропустить создание zip‑снимка `~/.hermes/` перед миграцией (по умолчанию перед применением создаётся архив restore‑point в `~/.hermes/backups/pre-migration-*.zip`, который можно восстановить с помощью `hermes import`). |
| `--source <path>` | Пользовательский каталог OpenClaw (по умолчанию — `~/.openclaw`). |
| `--workspace-target <path>` | Целевой каталог для инструкций рабочего пространства (AGENTS.md). |
| `--skill-conflict <mode>` | Обработка конфликтов имён skill: `skip` (по умолчанию), `overwrite` или `rename`. |
| `--yes` | Пропустить запрос подтверждения. |

### Что переносится

Миграция охватывает более 30 категорий, включая персонажи, память, skill, провайдеров моделей, платформы обмена сообщениями, поведение агента, политики сессий, серверы MCP, TTS и многое другое. Элементы либо **импортируются напрямую** в эквиваленты Hermes, либо **архивируются** для ручного обзора.

**Импортируются напрямую:** `SOUL.md`, `MEMORY.md`, `USER.md`, `AGENTS.md`, skill (4 исходных каталога), модель по умолчанию, пользовательские провайдеры, серверы MCP, токены и allowlist‑ы платформ обмена сообщениями (Telegram, Discord, Slack, WhatsApp, Signal, Matrix, Mattermost), настройки по умолчанию агента (уровень рассуждений, сжатие, задержка человека, часовой пояс, sandbox), политики сброса сессий, правила одобрения, конфигурация TTS, настройки браузера, настройки инструментов, таймаут выполнения, allowlist команд, конфигурация gateway и API‑ключи из трёх источников.

**Архивируются для ручного обзора:** задания Cron, плагины, хуки/webhooks, бекенд памяти (QMD), конфигурация реестра skill, UI/identity, логирование, настройка мульти‑агента, привязки каналов, `IDENTITY.md`, `TOOLS.md`, `HEARTBEAT.md`, `BOOTSTRAP.md`.

**Разрешение API‑ключей** проверяет три источника в порядке приоритета: значения конфигурации → `~/.openclaw/.env` → `auth-profiles.json`. Все поля токенов поддерживают простые строки, шаблоны окружения (`${VAR}`) и объекты `SecretRef`.

Полную таблицу соответствий ключей конфигурации, детали обработки `SecretRef` и чек‑лист после миграции смотри в **[полном руководстве по миграции](../guides/migrate-from-openclaw.md)**.

### Примеры

```bash
# Preview what would be migrated
hermes claw migrate --dry-run

# Full migration (all compatible settings, no secrets)
hermes claw migrate --preset full

# Full migration including API keys
hermes claw migrate --preset full --migrate-secrets

# Migrate user data only (no secrets), overwrite conflicts
hermes claw migrate --preset user-data --overwrite

# Migrate from a custom OpenClaw path
hermes claw migrate --source /home/user/old-openclaw
```
## `hermes dashboard`

```bash
hermes dashboard [options]
```

Запусти веб‑дашборд — UI в браузере для управления конфигурацией, API‑ключами и мониторинга сессий. Требуется `pip install hermes-agent[web]` (FastAPI + Uvicorn). Встроенная вкладка чата в браузере требует `--tui` и дополнительный пакет `pty`. См. [Web Dashboard](/user-guide/features/web-dashboard) для полной документации.

| Опция | По умолчанию | Описание |
|--------|--------------|----------|
| `--port` | `9119` | Порт, на котором будет работать веб‑сервер |
| `--host` | `127.0.0.1` | Адрес привязки |
| `--no-open` | — | Не открывать браузер автоматически |
| `--tui` | off | Включить вкладку чата в браузере, запустив `hermes --tui` через PTY/WebSocket‑мост. Требуется `pip install 'hermes-agent[web,pty]'` и POSIX‑окружение PTY, например Linux, macOS или WSL2. |
| `--insecure` | off | Разрешить привязку к хостам, отличным от localhost. Открывает учётные данные дашборда в сети; используй только за надёжными сетевыми контролями. |
| `--stop` | — | Остановить запущенные процессы `hermes dashboard` и выйти. |
| `--status` | — | Вывести список запущенных процессов `hermes dashboard` и выйти. |

```bash
# Default — opens browser to http://127.0.0.1:9119
hermes dashboard

# Custom port, no browser
hermes dashboard --port 8080 --no-open

# Enable the browser Chat tab
hermes dashboard --tui
```
## `hermes profile`

```bash
hermes profile <subcommand>
```

Управление профилями — несколько изолированных экземпляров Hermes, каждый со своей конфигурацией, сессиями, skill‑ами и домашним каталогом.

| Subcommand | Description |
|------------|-------------|
| `list` | Вывести список всех профилей. |
| `use <name>` | Установить запоминаемый профиль по умолчанию. |
| `create <name> [--clone] [--clone-all] [--clone-from <source>] [--no-alias]` | Создать новый профиль. `--clone` копирует конфигурацию, `.env` и `SOUL.md` из активного профиля. `--clone-all` копирует всё состояние. `--clone-from` указывает исходный профиль. |
| `delete <name> [-y]` | Удалить профиль. |
| `show <name>` | Показать детали профиля (домашний каталог, конфигурацию и т.п.). |
| `alias <name> [--remove] [--name NAME]` | Управлять обёртками‑скриптами для быстрого доступа к профилю. |
| `rename <old> <new>` | Переименовать профиль. |
| `export <name> [-o FILE]` | Экспортировать профиль в архив `.tar.gz` (локальная резервная копия). |
| `import <archive> [--name NAME]` | Импортировать профиль из архива `.tar.gz` (локальное восстановление). |
| `install <source> [--name N] [--alias] [--force] [-y]` | Установить дистрибутив профиля из git‑URL или локального каталога. |
| `update <name> [--force-config] [-y]` | Переполучить дистрибутив; сохраняет пользовательские данные (память, сессии, учётные данные). |
| `info <name>` | Показать манифест дистрибутива профиля (версия, требования, источник). |

Examples:

```bash
hermes profile list
hermes profile create work --clone
hermes profile use work
hermes profile alias work --name h-work
hermes profile export work -o work-backup.tar.gz
hermes profile import work-backup.tar.gz --name restored
hermes profile install github.com/user/my-distro --alias
hermes profile update work
hermes -p work chat -q "Hello from work profile"
```
## `hermes completion`

```bash
hermes completion [bash|zsh|fish]
```

Вывести скрипт автодополнения для оболочки в stdout. Подключи вывод к своему профилю оболочки, чтобы включить автодополнение команд Hermes, их подкоманд и имён профилей.

Примеры:

```bash
# Bash
hermes completion bash >> ~/.bashrc

# Zsh
hermes completion zsh >> ~/.zshrc

# Fish
hermes completion fish > ~/.config/fish/completions/hermes.fish
```
## `hermes update`

```bash
hermes update [--check] [--backup] [--restart-gateway]
```

Загружает последнюю версию кода `hermes-agent` и переустанавливает зависимости в твоём виртуальном окружении, затем повторно запускает post‑install‑хуки (MCP‑серверы, синхронизация skills, установка автодополнения). Безопасно запускать на работающей установке.

**pip‑установки:** `hermes update` автоматически определяет pip‑базированные установки — он запрашивает PyPI о последнем релизе и выполняет `pip install --upgrade hermes-agent` вместо `git pull`. Релизы в PyPI соответствуют помеченным версиям (мажорным/минорным), а не каждому коммиту в `main`. Используй `--check`, чтобы увидеть, доступен ли более новый релиз в PyPI, без установки.

| Option | Description |
|--------|-------------|
| `--check` | Выводит текущий коммит и последний коммит `origin/main` рядом и завершает работу с кодом 0, если они синхронны, или 1, если отстаёшь. Не делает pull, install и не перезапускает ничего. |
| `--backup` | Создаёт помеченный снимок `HERMES_HOME` (конфиги, авторизация, сессии, skills, данные паринга) перед загрузкой. По умолчанию **off** — поведение «всегда делать бэкап» добавляло несколько минут к каждому обновлению больших homes. Включи его постоянно через `update.backup: true` в `config.yaml`. |
| `--restart-gateway` | После успешного обновления перезапускает работающий сервис gateway. Означает семантику `--all`, если установлено несколько профилей. |

Дополнительное поведение:

- **Снимок данных паринга.** Даже когда `--backup` выключен, `hermes update` делает лёгкий снимок `~/.hermes/pairing/` и правил комментариев Feishu перед `git pull`. Ты можешь откатить его с помощью `hermes backup restore --state pre-update`, если pull переписал файл, который ты редактировал.
- **Предупреждение о legacy `hermes.service`.** Если Hermes обнаруживает старый unit `hermes.service` systemd (вместо текущего `hermes-gateway.service`), он выводит одноразовый совет по миграции, чтобы избежать проблем с flap‑loop.
- **Коды завершения.** `0` — успех, `1` — ошибки pull/install/post‑install, `2` — неожиданные изменения в рабочем дереве, блокирующие `git pull`.
## Команды обслуживания

| Command | Description |
|---------|-------------|
| `hermes version` | Вывести информацию о версии. |
| `hermes update` | Получить последние изменения и переустановить зависимости. |
| `hermes postinstall` | Внутренняя инициализация (bootstrap). Выполняется один раз после `pip install hermes-agent` (или `hermes update` при установке через pip) для установки зависимостей, которые pip не может предоставить — среда выполнения Node.js, браузер без графического интерфейса, ripgrep, ffmpeg — и затем запускает `hermes setup`, если профиль ещё не настроен. Безопасно повторно запускать идемпотентно. |
| `hermes uninstall [--full] [--yes]` | Удалить Hermes, по желанию удаляя все конфигурации и данные. |
## См. также

- [Справочник по слеш‑командам](./slash-commands.md)
- [CLI‑интерфейс](../user-guide/cli.md)
- [Сессии](../user-guide/sessions.md)
- [Система навыков](../user-guide/features/skills.md)
- [Скины и темы](../user-guide/features/skins.md)