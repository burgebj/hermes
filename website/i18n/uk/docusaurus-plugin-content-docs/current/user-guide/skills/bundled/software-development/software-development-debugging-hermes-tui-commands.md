---
title: "Налагодження Hermes Tui Commands — Налагодити Hermes TUI slash‑команди: Python, gateway, Ink UI"
sidebar_label: "Debugging Hermes Tui Commands"
description: "Налагодження slash‑команд Hermes TUI: Python, gateway, Ink UI"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Налагодження команд Hermes TUI

Налагоджуй slash‑команди Hermes TUI: Python, gateway, Ink UI.

## Метадані навички

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

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# Налагодження slash‑команд Hermes TUI

## Огляд

Slash‑команди Hermes охоплюють три рівні — реєстр Python‑команд, місток `tui_gateway` JSON‑RPC та фронтенд Ink/TypeScript. Коли команда поводиться неправильно (відсутня в автодоповненні, працює в CLI, але не в TUI, конфіг зберігається, а UI не оновлюється), помилка майже завжди полягає в тому, що один рівень не синхронізований з іншим.

Використовуй цю навичку, коли стикаєшся з проблемами slash‑команд у Hermes TUI, особливо коли команди не відображаються в автодоповненні, не працюють належним чином у TUI або їх потрібно додати/оновити.

## Коли використовувати

- Slash‑команда існує в одній частині коду, але не працює повністю
- Команду потрібно додати і в бекенд, і у фронтенд
- Автодоповнення команди не працює для певних команд
- Поведінка команди різна між CLI та TUI
- Команда зберігає конфіг, але не застосовується в живому режимі TUI

## Огляд архітектури

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

Визначення команд мають бути зареєстровані послідовно в Python та TypeScript, щоб працювати правильно. Python `COMMAND_REGISTRY` є джерелом правди для: диспетчеризації CLI, довідки gateway, меню Telegram BotCommand, мапи підкоманд Slack та даних автодоповнення, що надсилаються в Ink.

## Кроки розслідування

1. **Перевір, чи існує команда у фронтенді TUI:**
   ```bash
   search_files --pattern "/commandname" --file_glob "*.ts" --path ui-tui/
   search_files --pattern "/commandname" --file_glob "*.tsx" --path ui-tui/
   ```

2. **Оглянь визначення команди у TUI:**
   ```bash
   read_file ui-tui/src/app/slash/commands/core.ts
   # If not there:
   search_files --pattern "commandname" --path ui-tui/src/app/slash/commands --target files
   ```

3. **Перевір, чи існує команда у бекенді Python:**
   ```bash
   search_files --pattern "CommandDef" --file_glob "*.py" --path hermes_cli/
   search_files --pattern "commandname" --path hermes_cli/commands.py --context 3
   ```

4. **Оглянь реалізацію gateway:**
   ```bash
   search_files --pattern "complete.slash|slash.exec" --path tui_gateway/
   ```

## Виправлення: відсутнє автодоповнення команди

Якщо команда існує в TUI, але не показується в автодоповненні:

1. Додай запис `CommandDef` до `COMMAND_REGISTRY` у `hermes_cli/commands.py`:
   ```python
   CommandDef("commandname", "Description of the command", "Session",
              cli_only=True, aliases=("alias",),
              args_hint="[arg1|arg2|arg3]",
              subcommands=("arg1", "arg2", "arg3")),
   ```

2. Обережно вибирай між `cli_only` та доступністю в gateway:
   - `cli_only=True` — лише в інтерактивному CLI/TUI
   - `gateway_only=True` — лише в платформах обміну повідомленнями
   - ні те, ні інше — доступна скрізь
   - `gateway_config_gate="display.foo"` — доступність, керована конфігом у gateway

3. Переконайся, що `subcommands` відповідає очікуваним варіантам таб‑комплішн, які показує TUI.

4. Якщо команда виконується на сервері, додай обробник у `HermesCLI.process_command()` у `cli.py`:
   ```python
   elif canonical == "commandname":
       self._handle_commandname(cmd_original)
   ```

5. Для команд, доступних через gateway, додай обробник у `gateway/run.py`:
   ```python
   if canonical == "commandname":
       return await self._handle_commandname(event)
   ```

## Поширені проблеми

1. **Команда показується в TUI, але не в автодоповненні.** Команда визначена в коді TUI, але відсутня в `COMMAND_REGISTRY` у `hermes_cli/commands.py`. Дані автодоповнення надходять з Python.

2. **Команда показується в автодоповненні, але не працює.** Перевір обробник команди у `tui_gateway/server.py` та фронтенд‑обробник у `ui-tui/src/app/createSlashHandler.ts`. Якщо команда локальна лише в Ink, її треба обробляти у вбудованій гілці `app.tsx`; інакше вона переходить до `slash.exec` і потребує Python‑обробника.

3. **Поведінка команди різна між CLI та TUI.** Можливі різні реалізації. Перевір і `cli.py::process_command`, і локальний обробник TUI. Локальні обробники TUI мають пріоритет над диспетчером gateway.

4. **Команда зберігає конфіг, але не застосовується в живому режимі.** Для локальних TUI‑команд оновлення `config.set` недостатньо. Потрібно також одразу патчити відповідний стан nanostore (зазвичай `patchUiState(...)`) і передати новий стан через компоненти рендерингу. Приклад: `/details collapsed` має оновлювати видимість деталей у реальному часі, а не лише зберігати `details_mode`; глобальна команда `/details <mode>` у сесії може потребувати окремого прапорця‑перевизначення, щоб живі команди могли переоприділити типові налаштування розділів, тоді як синхронізація старту/конфігурації зберігає поведінку за замовчуванням.

5. **Gateway ігнорує команду без повідомлення.** Gateway розсилає лише ті команди, які знає. Переконайся, що `GATEWAY_KNOWN_COMMANDS` (генерується автоматично з `COMMAND_REGISTRY`) містить канонічну назву. Якщо команда `cli_only` з `gateway_config_gate`, перевір, що значення конфігурації істинне.

## Тактики налагодження

Коли поверхневий огляд не виявляє проблему:

- **Проблеми на стороні Python:** використай навичку `python-debugpy` для зупинки всередині `_SlashWorker.exec` або обробника команди. `remote-pdb` у точці входу — найшвидший шлях.
- **Ink‑сторона не реагує:** використай навичку `node-inspect-debugger` для зупинки у `app.tsx` під час диспетчування slash або у локальній гілці команди. `sb('dist/app.js', <line>)` після `npm run build`.
- **Невідповідність реєстрів / незрозуміло, яка сторона помилкова:** порівняй канонічний запис `COMMAND_REGISTRY` з локальним списком команд TUI бок‑за‑бок.

## Підводні камені

- Не забудь встановити відповідну категорію для команди в `CommandDef` (наприклад, "Session", "Configuration", "Tools & Skills", "Info", "Exit").
- Переконайся, що всі псевдоніми правильно зареєстровані у кортежі `aliases` — інші зміни файлів не потрібні, все нижче (меню Telegram, мапа Slack, автодоповнення, довідка) генерується автоматично.
- Для команд з підкомандами `subcommands` у `CommandDef` має точно відповідати тому, що є у коді TUI.
- Команди з `cli_only=True` не працюватимуть у gateway/платформах обміну повідомленнями — хіба що додати `gateway_config_gate` і щоб гейт був істинним.
- Після додавання живого стану UI знайди кожного споживача старого пропу/хелпера і передай новий стан через усі шляхи рендерингу, а не лише активний потоковий шлях. Рендеринг деталей TUI має принаймні два важливі шляхи: живий `StreamingAssistant`/`ToolTrail` та рядки транскрипту/очікування `MessageLine`. Прохід `/clean` має явно перевіряти обидва.
- Перебудуй TUI (`npm --prefix ui-tui run build`) перед тестуванням — режим спостереження tsx може відставати при першому запуску.

## Перевірка

Після виправлення:

1. Перебудуй TUI:
   ```bash
   cd /home/bb/hermes-agent && npm --prefix ui-tui run build
   ```

2. Запусти TUI і протестуй команду:
   ```bash
   hermes --tui
   ```

3. Введи `/` і переконайся, що команда з’являється в підказках автодоповнення з очікуваним описом та підказками аргументів.

4. Виконай команду і підтверди:
   - Очікувана поведінка спрацьовує
   - Будь‑які збережені конфігурації оновлюються коректно (`read_file ~/.hermes/config.yaml`)
   - Живий стан UI відображає зміни миттєво (не лише після перезапуску)

5. Якщо команда також доступна через gateway, протестуй її хоча б на одній платформі обміну повідомленнями (або запусти тести gateway: `scripts/run_tests.sh tests/gateway/`).