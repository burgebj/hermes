---
title: "Отладка команд Hermes Tui — Отладка slash‑команд Hermes TUI: Python, gateway, Ink UI"
sidebar_label: "Debugging Hermes Tui Commands"
description: "Отладка Hermes TUI слеш‑команды: Python, gateway, Ink UI"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Отладка слеш‑команд Hermes TUI

Отладка слеш‑команд Hermes TUI: Python, gateway, Ink UI.

## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/software-development/debugging-hermes-tui-commands` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `debugging`, `hermes-agent`, `tui`, `slash-commands`, `typescript`, `python` |
| Related skills | [`python-debugpy`](/docs/user-guide/skills/bundled/software-development/software-development-python-debugpy), [`node-inspect-debugger`](/docs/user-guide/skills/bundled/software-development/software-development-node-inspect-debugger), [`systematic-debugging`](/docs/user-guide/skills/bundled/software-development/software-development-systematic-debugging) |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает при его активации. Это то, что агент видит как инструкции, когда навык активен.
:::

# Отладка слеш‑команд Hermes TUI

## Обзор

Слеш‑команды Hermes охватывают три уровня — реестр команд Python, мост JSON‑RPC `tui_gateway` и фронтенд Ink/TypeScript. Когда команда ведёт себя некорректно (отсутствует в автодополнении, работает в CLI, но не в TUI, конфигурация сохраняется, но UI не обновляется), ошибка почти всегда связана с рассинхроной между уровнями.

Используй этот навык, когда сталкиваешься с проблемами слеш‑команд в Hermes TUI, особенно если команды не отображаются в автодополнении, не работают в TUI или требуют добавления/обновления.

## Когда использовать

- Слеш‑команда существует в одной части кода, но не работает полностью
- Команду нужно добавить и в бэкенд, и во фронтенд
- Автодополнение команды не работает для конкретных команд
- Поведение команды отличается между CLI и TUI
- Команда сохраняет конфигурацию, но не применяется в живом режиме TUI

## Обзор архитектуры

<!-- ascii-guard-ignore -->
```
Python backend (hermes_cli/commands.py)     <- canonical COMMAND_REGISTRY
       │
       ▼
TUI gateway (tui_gateway/server.py)         <- slash.exec / command.dispatch
       │
       ▼
TUI frontend (ui-tui/src/app/slash/)        <- local handlers + fallthrough
```
<!-- ascii-guard-ignore-end -->

Определения команд должны быть зарегистрированы согласованно в Python и TypeScript, чтобы работать корректно. Python `COMMAND_REGISTRY` — источник правды для: диспетчеризации CLI, справки gateway, меню Telegram BotCommand, карты подкоманд Slack и данных автодополнения, отправляемых в Ink.

## Шаги расследования

1. **Проверь, существует ли команда во фронтенде TUI:**
      ```bash
   search_files --pattern "/commandname" --file_glob "*.ts" --path ui-tui/
   search_files --pattern "/commandname" --file_glob "*.tsx" --path ui-tui/
   ```

2. **Изучи определение команды в TUI:**
      ```bash
   read_file ui-tui/src/app/slash/commands/core.ts
   # If not there:
   search_files --pattern "commandname" --path ui-tui/src/app/slash/commands --target files
   ```

3. **Проверь, существует ли команда в бэкенде Python:**
      ```bash
   search_files --pattern "CommandDef" --file_glob "*.py" --path hermes_cli/
   search_files --pattern "commandname" --path hermes_cli/commands.py --context 3
   ```

4. **Изучи реализацию gateway:**
      ```bash
   search_files --pattern "complete.slash|slash.exec" --path tui_gateway/
   ```

## Исправление: отсутствие автодополнения команды

Если команда присутствует в TUI, но не отображается в автодополнении:

1. Добавь запись `CommandDef` в `COMMAND_REGISTRY` в `hermes_cli/commands.py`:
      ```python
   CommandDef("commandname", "Description of the command", "Session",
              cli_only=True, aliases=("alias",),
              args_hint="[arg1|arg2|arg3]",
              subcommands=("arg1", "arg2", "arg3")),
   ```

2. Тщательно выбирай между `cli_only` и доступностью через gateway:
   - `cli_only=True` — только в интерактивном CLI/TUI
   - `gateway_only=True` — только в платформах обмена сообщениями
   - отсутствие флага — доступна везде
   - `gateway_config_gate="display.foo"` — доступность, управляемая конфигурацией в gateway

3. Убедись, что `subcommands` соответствует ожидаемым вариантам автодополнения, показываемым TUI.

4. Если команда исполняется на сервере, добавь обработчик в `HermesCLI.process_command()` в `cli.py`:
      ```python
   elif canonical == "commandname":
       self._handle_commandname(cmd_original)
   ```

5. Для команд, доступных через gateway, добавь обработчик в `gateway/run.py`:
      ```python
   if canonical == "commandname":
       return await self._handle_commandname(event)
   ```

## Распространённые проблемы

1. **Команда видна в TUI, но нет в автодополнении.** Команда определена в коде TUI, но отсутствует в `COMMAND_REGISTRY` в `hermes_cli/commands.py`. Данные автодополнения формируются в Python.

2. **Команда отображается в автодополнении, но не работает.** Проверь обработчик команды в `tui_gateway/server.py` и фронтенд‑обработчик в `ui-tui/src/app/createSlashHandler.ts`. Если команда локальная только в Ink, её нужно обрабатывать в ветке `app.tsx`; иначе запрос попадает в `slash.exec` и требует Python‑обработчика.

3. **Поведение команды различается между CLI и TUI.** Возможно, реализованы разные версии. Проверь как `cli.py::process_command`, так и локальный обработчик TUI. Локальные обработчики TUI имеют приоритет над диспетчером gateway.

4. **Команда сохраняет конфигурацию, но не применяет её в живом режиме.** Для локальных команд TUI недостаточно вызвать `config.set`. Нужно также сразу обновить соответствующее состояние nanostore (обычно `patchUiState(...)`) и передать новое состояние через компоненты рендеринга. Пример: `/details collapsed` должен обновлять видимость деталей сразу, а не только сохранять `details_mode`; глобальная команда `/details <mode>` может потребовать отдельного флага‑переопределения, чтобы живые команды могли переопределять встроенные значения по умолчанию, пока синхронизация при старте/конфиге сохраняет поведение по умолчанию.

5. **Gateway тихо игнорирует команду.** Gateway отправляет только известные команды. Убедись, что `GATEWAY_KNOWN_COMMANDS` (формируется автоматически из `COMMAND_REGISTRY`) содержит каноническое имя. Если команда `cli_only` с `gateway_config_gate`, проверь, что значение конфигурации истинно.

## Тактики отладки

Когда поверхностный осмотр не выявил проблему:

- **Проблемы на стороне Python:** используй навык `python-debugpy` для установки точки останова в `_SlashWorker.exec` или в обработчике команды. `remote-pdb` у входа обработчика — самый быстрый путь.
- **Ink‑часть не реагирует:** используй навык `node-inspect-debugger` для установки брейкпоинта в `app.tsx` в месте диспетчеризации слеша или в ветке локальной команды. `sb('dist/app.js', <line>)` после `npm run build`.
- **Несоответствие реестров / неясно, где ошибка:** сравни каноничную запись `COMMAND_REGISTRY` с локальным списком команд TUI бок о бок.

## Подводные камни

- Не забудь задать правильную категорию для команды в `CommandDef` (например, «Session», «Configuration», «Tools & Skills», «Info», «Exit»).
- Убедись, что все алиасы корректно зарегистрированы в кортеже `aliases` — других изменений не требуется, всё ниже (меню Telegram, маппинг Slack, автодополнение, справка) выводится из него.
- Для команд с подкомандами убедись, что кортеж `subcommands` в `CommandDef` совпадает с тем, что реализовано в коде TUI.
- Команды с `cli_only=True` не работают в gateway/мессенджерах — если нужен доступ через gateway, добавь `gateway_config_gate` и убедись, что соответствующий флаг включён.
- После добавления живого состояния UI проверь каждый потребитель старого свойства/хелпера и протяни новое состояние через все пути рендеринга, а не только активный поток. Рендеринг деталей TUI имеет минимум два важных пути: живой `StreamingAssistant`/`ToolTrail` и строки транскрипта/ожидания `MessageLine`. Команда `/clean` должна явно проверять оба.
- Пересобери TUI (`npm --prefix ui-tui run build`) перед тестированием — режим наблюдения tsx может отставать при первом запуске.

## Проверка

После исправления:

1. Пересобери TUI:
      ```bash
   cd /home/bb/hermes-agent && npm --prefix ui-tui run build
   ```

2. Запусти TUI и протестируй команду:
      ```bash
   hermes --tui
   ```

3. Нажми `/` и убедись, что команда появляется в подсказках автодополнения с ожидаемым описанием и подсказкой аргументов.

4. Выполни команду и проверь:
   - Ожидаемое поведение срабатывает
   - Любые сохранённые конфигурации обновляются корректно (`read_file ~/.hermes/config.yaml`)
   - Живое состояние UI отражает изменение сразу (а не только после перезапуска)

5. Если команда также доступна через gateway, протестируй её хотя бы в одной платформе обмена сообщениями (или запусти тесты gateway: `scripts/run_tests.sh tests/gateway/`).