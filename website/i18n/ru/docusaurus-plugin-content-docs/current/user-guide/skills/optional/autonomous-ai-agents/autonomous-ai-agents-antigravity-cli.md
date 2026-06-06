---
title: "Antigravity Cli — Управляй Antigravity CLI (agy): плагины, аутентификация, песочница"
sidebar_label: "Antigravity Cli"
description: "Управляй Antigravity CLI (agy): plugins, auth, sandbox"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Antigravity CLI

Работа с Antigravity CLI (`agy`): плагины, аутентификация, песочница.

## Метаданные навыка

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/autonomous-ai-agents/antigravity-cli` |
| Path | `optional-skills/autonomous-ai-agents/antigravity-cli` |
| Version | `0.1.0` |
| Author | Tony Simons (asimons81), Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Coding-Agent`, `Antigravity`, `CLI`, `Auth`, `Plugins`, `Sandbox` |
| Related skills | [`grok`](/docs/user-guide/skills/optional/autonomous-ai-agents/autonomous-ai-agents-grok), [`codex`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-codex), [`claude-code`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-claude-code), [`hermes-agent`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-hermes-agent) |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает при его активации. Это то, что агент видит как инструкции, когда навык включён.
:::

# Antigravity CLI (`agy`)

Руководство оператора для Antigravity CLI, вызываемого как `agy`. Выполняй все команды `agy` через инструмент Hermes `terminal`; просматривай конфигурацию и логи с помощью `read_file`. Этот навык — справка + процедура, он не обёртка над сетевым API, поэтому аутентификация в Hermes не требуется.

## Когда использовать

- Установка, обновление или smoke‑тестирование бинарника `agy`
- Запуск неинтерактивных однократных команд `agy --print` / `agy -p`
- Отладка аутентификации, песочницы, прав доступа или состояния плагинов Antigravity
- Чтение настроек, привязок клавиш, диалогов или логов Antigravity

## Ментальная модель

У Antigravity два уровня — держи их раздельно, иначе рекомендации будут неверными:

1. **Оболочечные команды** — `agy help`, `agy install`, `agy plugin`, `agy update`, `agy changelog`. Выполняй их через инструмент `terminal`.
2. **Интерактивные slash‑команды внутри сессии** — `/config`, `/permissions`, `/skills`, `/agents` и др. Они существуют только в запущенной TUI‑сессии `agy`, а не в оболочке.

`agy help` показывает только оболочечные команды, а не slash‑команды внутри сессии.

## Предварительные требования

- Бинарник `agy` должен быть в `PATH`. Проверь через `terminal`: `command -v agy && agy --version`.
- Переменные окружения или API‑ключи не требуются — Antigravity управляет своей аутентификацией через системный keyring / вход в браузер (см. раздел «Аутентификация» ниже).

## Как запускать

Вызывай каждую команду `agy` через инструмент `terminal`. Примеры:

```
terminal(command="agy --version")
terminal(command="agy help")
terminal(command="agy plugin list")
terminal(command="agy --print 'Summarize the repo in 3 bullets'", workdir="/path/to/project")
```

Для интерактивной многоходовой TUI‑сессии запускай `agy` с `pty=true` (и `tmux` для захвата/мониторинга) — тот же шаблон, что используют навыки `codex` / `claude-code`. Для однократных smoke‑тестов и скриптовых запросов предпочтительнее `agy --print` (неинтерактивно).

Чтобы просмотреть файлы Antigravity, используй `read_file` по путям из раздела **Core paths** ниже — не `cat` их через терминал.

## Core paths

- Бинарник / точка входа: `agy`
- Каталог данных приложения: `~/.gemini/antigravity-cli/`
- Файл настроек: `~/.gemini/antigravity-cli/settings.json`
- Файл привязок клавиш: `~/.gemini/antigravity-cli/keybindings.json`
- Логи: `~/.gemini/antigravity-cli/log/cli-*.log`
- Диалоги: `~/.gemini/antigravity-cli/conversations/`
- Артефакты «мозга»: `~/.gemini/antigravity-cli/brain/`
- История: `~/.gemini/antigravity-cli/history.jsonl`
- Папка для плагинов: `~/.gemini/antigravity-cli/plugins/<plugin_name>/`

## Быстрая справка

### Оболочечные команды
- `agy changelog`
- `agy help`
- `agy install`
- `agy plugin` / `agy plugins`
- `agy update`

### Полезные флаги
- `--add-dir`
- `--continue` / `-c`
- `--conversation`
- `--dangerously-skip-permissions`
- `--print` / `-p`
- `--print-timeout`
- `--prompt`
- `--prompt-interactive` / `-i`
- `--sandbox`
- `--log-file`
- `--version`

### Подкоманды плагинов (`agy plugin --help`)
- `list`, `import [source]`, `install <target>`, `uninstall <name>`,
  `enable <name>`, `disable <name>`, `validate [path]`, `link <mp> <target>`,
  `help`

### Флаги установки (`agy install --help`)
- `--dir`, `--skip-aliases`, `--skip-path`

### Slash‑команды внутри сессии
- **Управление диалогом:** `/resume` (`/switch`), `/rewind` (`/undo`), `/rename <name>`, `/clear`, `/fork`, `/reset`, `/new`
- **Настройки и инструменты:** `/config`, `/settings`, `/permissions`, `/model`, `/keybindings`, `/statusline`, `/tasks`, `/skills`, `/mcp`, `/open <path>`, `/usage`, `/logout`, `/agents`
- **Помощники ввода:** автодополнение пути `@`, `esc esc` очищает запрос (когда не идёт поток), `!` сразу выполняет команду терминала, `?` открывает справку

## Настройки и права доступа

### Общие ключи настроек (`settings.json`)
- `allowNonWorkspaceAccess`
- `colorScheme`
- `permissions.allow`
- `trustedWorkspaces`

### Режимы прав
`request-review`, `always-proceed`, `strict`, `proceed-in-sandbox`.

### Поведение песочницы
- `enableTerminalSandbox` — булево значение в `settings.json`; по умолчанию `false`.
- Переопределения при запуске (`--sandbox`, `--dangerously-skip-permissions`) могут заменить постоянные настройки на текущую сессию.

## Поведение аутентификации

- CLI сначала обращается к системному secure keyring.
- Если сохранённой сессии нет, происходит fallback к входу через браузер Google.
- Локально открывается браузер по умолчанию; при работе через SSH выводится URL для авторизации, после чего требуется вставить код подтверждения.
- `/logout` удаляет сохранённые учётные данные.

## Плагины

- Плагины размещаются в `~/.gemini/antigravity-cli/plugins/<plugin_name>/`.
- Они могут включать навыки, агентов, правила, MCP‑серверы и хуки.
- `agy plugin list`, возвращающий пустой список, считается корректным пустым состоянием.

## Подводные камни

- `agy help` показывает только оболочечные команды, а не slash‑команды внутри сессии.
- `agy --version` — безопасная неинтерактивная проверка версии; `agy version` интерактивна и может не работать без реального TTY.
- Первое место для поиска ошибок — логи `~/.gemini/antigravity-cli/log/cli-*.log` (читай через `read_file`).
- Не путай постоянные JSON‑настройки с переопределениями при запуске.
- `~/.gemini/antigravity-cli/bin/agentapi` — тонкая обёртка над `agy agentapi`.
- В WSL хранение токенов реализовано в виде файлов, поэтому проблемы с аутентификацией обычно связаны с локальными файлами/состоянием сессии, а не только с браузером.
- Идентичность рабочего пространства может зависеть от каталога запуска и маркера проекта `.antigravitycli`.

## Проверка

Убедись, что установка реальна и работоспособна, используя только инструмент `terminal` (читай файлы через `read_file`):

1. `terminal(command="command -v agy")`
2. `terminal(command="agy --version")`
3. `terminal(command="agy help")`
4. `terminal(command="agy plugin list")`
5. `read_file` на `~/.gemini/antigravity-cli/settings.json`
6. `read_file` на последний `~/.gemini/antigravity-cli/log/cli-*.log`
7. При необходимости `read_file` на `~/.gemini/antigravity-cli/keybindings.json`

## Поддерживающие файлы

- `references/cli-docs.md` — сокращённые заметки из руководств по началу работы, использованию и функциям.