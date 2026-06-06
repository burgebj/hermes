---
title: "Antigravity Cli — Керуй Antigravity CLI (agy): плагіни, auth, sandbox"
sidebar_label: "Antigravity Cli"
description: "Керуй Antigravity CLI (agy): plugins, auth, sandbox"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Antigravity CLI

Керування Antigravity CLI (`agy`): плагіни, автентифікація, пісочниця.

## Метадані навички

| | |
|---|---|
| Джерело | Optional — install with `hermes skills install official/autonomous-ai-agents/antigravity-cli` |
| Шлях | `optional-skills/autonomous-ai-agents/antigravity-cli` |
| Версія | `0.1.0` |
| Автор | Tony Simons (asimons81), Hermes Agent |
| Ліцензія | MIT |
| Платформи | linux, macos, windows |
| Теги | `Coding-Agent`, `Antigravity`, `CLI`, `Auth`, `Plugins`, `Sandbox` |
| Пов’язані навички | [`grok`](/docs/user-guide/skills/optional/autonomous-ai-agents/autonomous-ai-agents-grok), [`codex`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-codex), [`claude-code`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-claude-code), [`hermes-agent`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-hermes-agent) |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує під час її активації. Це інструкції, які бачить агент, коли навичка активна.
:::

# Antigravity CLI (`agy`)

Посібник оператора для Antigravity CLI, викликається як `agy`. Виконуй усі команди `agy` через інструмент Hermes `terminal`; переглядай його конфігурацію та логи за допомогою `read_file`. Ця навичка — довідка + процедура, вона не обгортає мережевий API, тому немає потреби в автентифікації з боку Hermes.

## Коли використовувати

- Встановлення, оновлення або швидке тестування бінарника `agy`
- Запуск неінтерактивних однорядкових команд `agy --print` / `agy -p`
- Налагодження автентифікації, пісочниці, дозволів або стану плагінів Antigravity
- Читання налаштувань, прив’язок клавіш, розмов або логів Antigravity

## Ментальна модель

Antigravity має два рівні — тримай їх розділеними, інакше рекомендації будуть неправильними:

1. **Shell‑обгортки** — `agy help`, `agy install`, `agy plugin`, `agy update`, `agy changelog`. Запускай їх через інструмент `terminal`.
2. **Інтерактивні slash‑команди під час сесії** — `/config`, `/permissions`, `/skills`, `/agents` тощо. Вони існують лише всередині запущеної TUI‑сесії `agy`, а не в оболонці.

`agy help` показує лише оболонкові команди, а не slash‑команди сесії.

## Передумови

- Бінарник `agy` має бути в `PATH`. Перевір це через інструмент `terminal`: `command -v agy && agy --version`.
- Жодних змінних середовища чи API‑ключів не потрібно — Antigravity керує власною автентифікацією через OS‑keyring / вхід у браузері (див. розділ **Authentication** нижче).

## Як запускати

Виконуй кожну команду `agy` через інструмент `terminal`. Приклади:

```
terminal(command="agy --version")
terminal(command="agy help")
terminal(command="agy plugin list")
terminal(command="agy --print 'Summarize the repo in 3 bullets'", workdir="/path/to/project")
```

Для інтерактивної багатокрокової TUI‑сесії запусти `agy` з параметром `pty=true` (і `tmux` для захоплення/моніторингу) — такий же шаблон, як у навичок `codex` / `claude-code`. Для однорядкових тестів і скриптових запитів краще використовувати `agy --print` (неінтерактивно).

Щоб переглянути власні файли Antigravity, використай `read_file` за шляхами, зазначеними у розділі **Core paths** нижче — не використовуйте `cat` через термінал.

## Core paths

- Бінарник / точка входу: `agy`
- Каталог даних програми: `~/.gemini/antigravity-cli/`
- Файл налаштувань: `~/.gemini/antigravity-cli/settings.json`
- Файл прив’язок клавіш: `~/.gemini/antigravity-cli/keybindings.json`
- Логи: `~/.gemini/antigravity-cli/log/cli-*.log`
- Розмови: `~/.gemini/antigravity-cli/conversations/`
- Артефакти «мозку»: `~/.gemini/antigravity-cli/brain/`
- Історія: `~/.gemini/antigravity-cli/history.jsonl`
- Сцена плагінів: `~/.gemini/antigravity-cli/plugins/<plugin_name>/`

## Швидка довідка

### Команди‑обгортки
- `agy changelog`
- `agy help`
- `agy install`
- `agy plugin` / `agy plugins`
- `agy update`

### Корисні прапорці
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

### Підкоманди плагінів (`agy plugin --help`)
- `list`, `import [source]`, `install <target>`, `uninstall <name>`,
  `enable <name>`, `disable <name>`, `validate [path]`, `link <mp> <target>`,
  `help`

### Прапорці встановлення (`agy install --help`)
- `--dir`, `--skip-aliases`, `--skip-path`

### Slash‑команди під час сесії
- **Керування розмовою:** `/resume` (`/switch`), `/rewind` (`/undo`), `/rename <name>`, `/clear`, `/fork`, `/reset`, `/new`
- **Налаштування та інструменти:** `/config`, `/settings`, `/permissions`, `/model`, `/keybindings`, `/statusline`, `/tasks`, `/skills`, `/mcp`, `/open <path>`, `/usage`, `/logout`, `/agents`
- **Помічники підказок:** `@` автодоповнення шляху, `esc esc` очищає підказку (коли не транслюється), `!` виконує команду терміналу безпосередньо, `?` відкриває довідку

## Налаштування та дозволи

### Типові ключі налаштувань (`settings.json`)
- `allowNonWorkspaceAccess`
- `colorScheme`
- `permissions.allow`
- `trustedWorkspaces`

### Режими дозволів
`request-review`, `always-proceed`, `strict`, `proceed-in-sandbox`.

### Поведінка пісочниці
- `enableTerminalSandbox` — булевий параметр у `settings.json`; за замовчуванням `false`.
- Перевизначення під час запуску (`--sandbox`, `--dangerously-skip-permissions`) можуть замінити постійні налаштування для поточної сесії.

## Поведінка автентифікації

- CLI спочатку звертається до захищеного сховища ОС.
- Якщо збереженої сесії немає, виконується запасний (fallback) вхід через браузер Google.
- Локально відкриває браузер за замовчуванням; через SSH виводить URL для авторизації і очікує, що код буде вставлений назад.
- `/logout` видаляє збережені облікові дані.

## Плагіни

- Плагіни розташовуються у `~/.gemini/antigravity-cli/plugins/<plugin_name>/`.
- Вони можуть включати навички, агентів, правила, MCP‑сервери та хуки.
- `agy plugin list`, що не повертає імпортованих плагінів, — це коректний порожній стан.

## Підводні камені

- `agy help` показує лише обгорткові команди, а не інтерактивні slash‑команди.
- `agy --version` — безпечна неінтерактивна перевірка версії; `agy version` — інтерактивна і може не працювати без реального TTY.
- Перше місце для пошуку помилок — `~/.gemini/antigravity-cli/log/cli-*.log` (читай за допомогою `read_file`).
- Не плутай постійні JSON‑налаштування з перевизначеннями під час запуску.
- `~/.gemini/antigravity-cli/bin/agentapi` — тонка обгортка над `agy agentapi`.
- У WSL сховище токенів файлове, тому проблеми з автентифікацією зазвичай пов’язані з локальними файлами/станом сесії, а не лише з браузером.
- Ідентифікатор робочого простору може залежати від каталогу запуску та маркера проекту `.antigravitycli`.

## Перевірка

Переконайся, що встановлення справжнє і працездатне, використовуючи лише інструмент `terminal` (читай файли за допомогою `read_file`):

1. `terminal(command="command -v agy")`
2. `terminal(command="agy --version")`
3. `terminal(command="agy help")`
4. `terminal(command="agy plugin list")`
5. `read_file` на `~/.gemini/antigravity-cli/settings.json`
6. `read_file` на останній `~/.gemini/antigravity-cli/log/cli-*.log`
7. При потребі `read_file` на `~/.gemini/antigravity-cli/keybindings.json`

## Файли підтримки

- `references/cli-docs.md` — стислий нотатки з документації «getting‑started», використання та функцій.