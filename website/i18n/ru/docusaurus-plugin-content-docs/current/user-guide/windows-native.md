---
title: "Windows (Native) руководство — ранняя бета"
description: "Ранний BETA: запуск Hermes Agent нативно в Windows 10 / 11 — установка, матрица функций, консоль UTF‑8, Git Bash, шлюз как запланированная задача, обработка редактора, PATH, удаление и типичные подводные камни"
sidebar_label: "Windows (Native) — Beta"
sidebar_position: 3
---

# Руководство по Windows (нативно) — ранняя бета

:::warning Early BETA
Поддержка Windows Native находится в **раннем бета‑тестировании**. Инсталлятор работает, запускается и проходит наш Windows‑footgun lint, но он ещё не проходил масштабных испытаний, как пути для Linux/macOS/WSL2. Ожидай шероховатости — особенно в обработке подпроцессов, особенностях путей и выводе не‑ASCII символов в консоль. Пожалуйста, [сообщай об ошибках](https://github.com/NousResearch/hermes-agent/issues) с шагами воспроизведения, когда что‑то пойдёт не так. Если нужен проверенный в боевых условиях набор сегодня, используй [инсталлятор для Linux/macOS под WSL2](./windows-wsl-quickstart.md) вместо этого.
:::

Hermes работает нативно на Windows 10 и Windows 11 — без WSL, без Cygwin, без Docker. Эта страница — подробный разбор: что работает нативно, что доступно только в WSL, что делает инсталлятор и какие Windows‑специфичные настройки могут понадобиться.

Если тебе нужно просто установить, достаточно выполнить однострочник с [главной страницы](/) или со [страницы установки](../getting-started/installation#windows-native-powershell--early-beta). Возвращайся сюда, если что‑то тебя удивит.

:::tip Want WSL instead?
Если ты предпочитаешь настоящий POSIX‑окружение (для встроенного терминала дашборда, семантики `fork`, Linux‑подобных наблюдателей за файлами и т.д.), смотри **[Windows (WSL2) Guide](./windows-wsl-quickstart.md)**. Оба варианта сосуществуют без конфликтов: нативные данные находятся в `%LOCALAPPDATA%\hermes`, данные WSL — в `~/.hermes`.
:::
## Быстрая установка

Открой **PowerShell** (или Windows Terminal) и выполни:

```powershell
iex (irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1)
```

Административные права не требуются. Установщик помещает файлы в `%LOCALAPPDATA%\hermes\` и добавляет `hermes` в **User PATH** — открой новый терминал после завершения.

**Параметры установщика** (требуется форма `scriptblock` для передачи параметров):

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1))) -NoVenv -SkipSetup -Branch main
```

| Параметр | По умолчанию | Назначение |
|---|---|---|
| `-Branch` | `main` | Клонировать определённую ветку (полезно для тестирования PR) |
| `-Commit` | unset | Зафиксировать установку на конкретном SHA коммита (перезаписывает `-Branch`) |
| `-Tag` | unset | Зафиксировать установку на конкретном git‑теге (например `v0.14.0`) |
| `-NoVenv` | off | Пропустить создание venv (продвинутое — ты сам управляешь Python) |
| `-SkipSetup` | off | Пропустить пост‑установочный мастер `hermes setup` |
| `-HermesHome` | `%LOCALAPPDATA%\hermes` | Переопределить каталог данных |
| `-InstallDir` | `%LOCALAPPDATA%\hermes\hermes-agent` | Переопределить расположение кода |

Установщик автоматически повторяет неудачные git‑запросы и удаляет BOM из любого загруженного `install.ps1`‑payload, поэтому UTF‑8 BOM, полученный во время HTTP‑транзита, больше не ломает форму `[scriptblock]::Create((irm ...))`.

### Десктопный установщик (альтернатива)

Легковесный GUI‑установщик также доступен — удобно, если ты предпочитаешь дважды кликнуть `.exe`, а не открывать PowerShell. Скачай Hermes Desktop, запусти установщик, и при первом запуске GUI вызывает `install.ps1` под капотом, чтобы подготовить Python (через `uv`), Node, PortableGit и остальные зависимости, описанные ниже. После первого запуска десктопное приложение и установленный через PowerShell `hermes` CLI используют один и тот же каталог установки `%LOCALAPPDATA%\hermes\hermes-agent` и каталог данных `%USERPROFILE%\.hermes` — свободно переключайся между GUI и CLI.

Используй десктопный установщик, когда нужен привычный Windows‑опыт установки или ты передаёшь Hermes неразработчику; используй однострочник PowerShell, когда уже находишься в терминале.

### Bootstrap зависимостей (`dep_ensure`)

При первом запуске (и по требованию, когда обнаружена отсутствующая утилита) Hermes запускает небольшой Python‑bootstrapper — `hermes_cli/dep_ensure.py` — который проверяет и при необходимости «лениво» устанавливает нужные не‑Python зависимости. На Windows это:

| Зависимость | Зачем Hermes это нужно |
|---|---|
| **PortableGit** | Предоставляет `bash.exe` для терминального инструмента и `git` для клонирования в сессии. Устанавливается во время установки, а не `dep_ensure`. |
| **Node.js 22** | Требуется для браузерного инструмента (`agent-browser`), веб‑моста TUI и моста WhatsApp. |
| **ffmpeg** | Конвертация аудио‑форматов для TTS / голосовых сообщений. |
| **ripgrep** | Быстрый поиск файлов — при отсутствии переходит к `grep`. |
| **npm packages** | `agent-browser`, Playwright Chromium и любые зависимости Node для каждого набора инструментов устанавливаются один раз при первом использовании браузерного инструмента. |

Каждая зависимость проверяется с помощью `shutil.which(...)`; если бинарник отсутствует и запуск интерактивный, `dep_ensure` предлагает установить её (передавая управление в `scripts\install.ps1 -ensure <dep>` для реальной установки). В неинтерактивных запусках (gateway, cron, безголовые десктопные запуски) запрос пропускается, а вместо него выводится чёткая ошибка `this feature needs <dep>`.
## Что на самом деле делает установщик

Сверху вниз, по порядку:

1. **Bootstrap `uv`** — быстрый менеджер Python от Astral. Устанавливается в `%USERPROFILE%\.local\bin`.
2. **Устанавливает Python 3.11** через `uv`. Не требуется установленный Python.
3. **Устанавливает Node.js 22** (через `winget`, если доступно, иначе портативный tar‑архив Node, распакованный в `%LOCALAPPDATA%\hermes\node`). Используется для инструмента браузера и моста WhatsApp.
4. **Устанавливает портативный Git** — если `git` уже есть в `PATH`, установщик использует его; иначе скачивает обрезанную, автономную **PortableGit** (~45 МБ, из официального релиза `git-for-windows`) в `%LOCALAPPDATA%\hermes\git`. Без прав администратора, без реестра Windows‑установщика, без вмешательства в остальное окружение.
5. **Клонирует репозиторий** в `%LOCALAPPDATA%\hermes\hermes-agent` и создаёт внутри него `virtualenv`.
6. **Пошаговый `uv pip install`** — сначала пытается `.[all]`, при неудаче переходит к постепенно меньшим наборам (`[messaging,dashboard,ext]` → `[messaging]` → `.`), если зависимость `git+https` падает из‑за ограничения скорости GitHub. Предотвращает ситуацию, когда один сбой приводит к «чистой» установке.
7. **Автоустанавливает SDK для обмена сообщениями** на основе `.env` — если присутствуют `TELEGRAM_BOT_TOKEN`, `DISCORD_BOT_TOKEN`, `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN` или `WHATSAPP_ENABLED`, выполняет `python -m ensurepip --upgrade` и целевые вызовы `pip install`, чтобы SDK каждой платформы действительно можно было импортировать.
8. **Устанавливает `HERMES_GIT_BASH_PATH`** в найденный `bash.exe`, чтобы Hermes определённо находил его в новых оболочках.
9. **Добавляет `%LOCALAPPDATA%\hermes\bin` в пользовательский `PATH`** — делает команду `hermes` доступной после открытия нового терминала.
10. **Запускает `hermes setup`** — обычный мастер первого запуска (модель, провайдер, наборы инструментов). Пропустить можно с `-SkipSetup`.

:::tip Пропусти поиск провайдера в Windows
Native Windows всё ещё находится в ранней бета‑версии, а настройка API‑ключей для каждого инструмента (Firecrawl, FAL, Browser Use, OpenAI TTS) является самым трудоёмким шагом для получения полезного агента. Подписка на [Nous Portal](/user-guide/features/tool-gateway) покрывает модель **и** все эти инструменты через один OAuth‑вход. После завершения установки запусти `hermes setup --portal`, чтобы всё настроить.
:::
## Матрица возможностей

Все, кроме встроенной панели терминала дашборда, работает нативно в Windows.

| Возможность | Нативный Windows | WSL2 |
|---|---|---|
| CLI (`hermes chat`, `hermes setup`, `hermes gateway`, …) | ✓ | ✓ |
| Интерактивный TUI (`hermes --tui`) | ✓ | ✓ |
| Шлюз обмена сообщениями (Telegram, Discord, Slack, WhatsApp, 15+ платформ) | ✓ | ✓ |
| Планировщик cron | ✓ | ✓ |
| Инструмент браузера (Chromium через Node) | ✓ | ✓ |
| MCP‑серверы (stdio и HTTP) | ✓ | ✓ |
| Локальный Ollama / LM Studio / llama-server | ✓ | ✓ (через сетевое взаимодействие WSL) |
| Веб‑дашборд (сессии, задачи, метрики, конфигурация) | ✓ | ✓ |
| Встроенная панель терминала дашборда `/chat` | ✗ (нужен POSIX PTY) | ✓ |
| Автозапуск при входе в систему | ✓ (schtasks) | ✓ (systemd) |

Вкладка `/chat` дашборда встраивает реальный терминал через POSIX PTY (`ptyprocess`). В нативном Windows нет эквивалентного примитива; `pywinpty` / Windows ConPTY могли бы работать, но это отдельная реализация — рассматривается как будущая работа. **Остальная часть дашборда работает нативно** — только эта вкладка показывает баннер «используй WSL2 для этого».
## Как Hermes запускает shell‑команды в Windows

Инструмент терминала Hermes выполняет команды через **Git Bash**, та же стратегия, что использует Claude Code. Это позволяет обойти разрыв между POSIX и Windows без переписывания каждого инструмента.

Порядок разрешения для `bash.exe`:

1. Переменная окружения `HERMES_GIT_BASH_PATH`, если она задана.
2. `%LOCALAPPDATA%\hermes\git\usr\bin\bash.exe` (PortableGit, управляемый установщиком).
3. `%LOCALAPPDATA%\hermes\git\bin\bash.exe` (старый макет Git‑for‑Windows).
4. Системная установка Git‑for‑Windows (`%ProgramFiles%\Git\bin\bash.exe` и др.).
5. MSYS2, Cygwin или любой `bash.exe` в `PATH` как последний вариант.

Установщик явно задаёт `HERMES_GIT_BASH_PATH`, чтобы новые сеансы PowerShell не приходилось заново искать Bash. Переопредели её, если хочешь, чтобы Hermes использовал конкретный Bash — например, системный Git Bash или Bash, размещённый в WSL, через символическую ссылку.

**Подводный камень:** Структура MinGit отличается от полного установщика Git‑for‑Windows — Bash находится в `usr\bin\bash.exe`, а не в `bin\bash.exe`. Hermes проверяет оба пути. Если ты распаковываешь zip‑архив MinGit вручную, убедись, что выбираешь **не‑busybox** вариант (`MinGit-*-64-bit.zip`, а не `MinGit-*-busybox*.zip`) — сборки busybox поставляют `ash` вместо `bash`, и большинство coreutils отсутствуют.
## UTF‑8 консоль в Windows

Стандартный ввод‑вывод Python в Windows использует активную кодовую страницу консоли (обычно cp1252 или cp437). Баннер Hermes, список слеш‑команд, поток инструментов, панели Rich и описания навыков содержат Unicode. Без вмешательства любой из них приводит к сбою с `UnicodeEncodeError: 'charmap' codec can't encode character…`.

Исправление находится в `hermes_cli/stdio.py::configure_windows_stdio()`, вызывается рано в каждой точке входа (`cli.py::main`, `hermes_cli/main.py::main`, `gateway/run.py::main`). Оно:

1. Переключает кодовую страницу консоли на CP_UTF8 (65001) через `kernel32.SetConsoleCP` / `SetConsoleOutputCP`.
2. Перенастраивает `sys.stdout` / `sys.stderr` / `sys.stdin` на UTF‑8 с `errors='replace'`.
3. Устанавливает `PYTHONIOENCODING=utf-8` и `PYTHONUTF8=1` (через `setdefault`, поэтому явные пользовательские значения имеют приоритет), чтобы дочерние подпроцессы Python наследовали UTF‑8.
4. Устанавливает `EDITOR=notepad`, если не задано ни `EDITOR`, ни `VISUAL` (см. раздел Editor ниже).

Идемпотентно. Не делает ничего на не‑Windows системах.

**Отключение:** `HERMES_DISABLE_WINDOWS_UTF8=1` в окружении возвращает к устаревшему пути cp1252 stdio. Полезно для изоляции ошибки кодировки; в обычной работе обычно не требуется.
## Редактор (`Ctrl‑X Ctrl‑E`, `/edit`)

До #21561 нажатие `Ctrl‑X Ctrl‑E` или ввод `/edit` молча ничего не делали в Windows. `prompt_toolkit` имеет жёстко закодированный список абсолютных POSIX‑путей fallback (`/usr/bin/nano`, `/usr/bin/pico`, `/usr/bin/vi`, …), который никогда не разрешается в Windows — даже при полностью установленном Git for Windows.

Shim `stdio` для Windows в Hermes теперь задаёт `EDITOR=notepad` по умолчанию. Notepad поставляется с каждой установкой Windows и работает как блокирующий редактор — `subprocess.call(["notepad", file])` блокирует выполнение, пока окно не будет закрыто.

**Пользовательские переопределения всё равно имеют приоритет** (они проверяются до установки значения по умолчанию):

| Редактор | Команда PowerShell |
|---|---|
| VS Code | `$env:EDITOR = "code --wait"` |
| Notepad++ | `$env:EDITOR = "'C:\Program Files\Notepad++\notepad++.exe' -multiInst -nosession"` |
| Neovim | `$env:EDITOR = "nvim"` |
| Helix | `$env:EDITOR = "hx"` |

Флаг `--wait` для VS Code критичен — без него редактор сразу возвращает управление, и Hermes получает пустой буфер.

Установи его постоянно в профиле PowerShell:

```powershell
# In $PROFILE
$env:EDITOR = "code --wait"
```

Или как переменную окружения User в настройках системы, чтобы каждый новый терминал её использовал.
## `Ctrl+Enter` для переноса строки в CLI

Windows Terminal передаёт `Ctrl+Enter` как отдельную последовательность клавиш. Hermes привязывает её к функции «вставить новую строку», чтобы ты мог писать многострочные подсказки в CLI, не прибегая к комбинации `Esc`‑`Enter`. Работает в Windows Terminal, интегрированном терминале VS Code и любом современном консольном хосте Windows, поддерживающем VT‑последовательности.

В устаревших консолях `cmd.exe` `Ctrl+Enter` сводится к обычному `Enter` — используй `Esc Enter` или обнови Windows Terminal (он бесплатный и установлен по умолчанию в Windows 11).
## Запуск шлюза при входе в Windows

`hermes gateway install` в Windows использует **Scheduled Tasks** с запасным (вариантом) в папке Startup — без прав администратора.

### Установка

```powershell
hermes gateway install
```

Что происходит «под капотом»:

1. `schtasks /Create /SC ONLOGON /RL LIMITED /TN HermesGateway` — регистрирует задачу, которая запускается при входе с обычными (неповышенными) правами. Без запроса UAC.
2. Если `schtasks` заблокирован групповой политикой, используется запасной (вариант) — создаётся ярлык `start /min cmd.exe /d /c <wrapper>` в `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`. Тот же эффект, немного более грубый.
3. Запускает шлюз **отсоединённо через `pythonw.exe`** — не `python.exe`. `pythonw.exe` не имеет привязанного консольного окна, что защищает его от широковещательных `CTRL_C_EVENT` от соседних процессов (реальная проблема, из‑за которой раньше шлюз погибал, когда ты нажимал Ctrl+C в том же процессе).

Флаги, используемые при запуске: `DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW | CREATE_BREAKAWAY_FROM_JOB`.

### Управление

```powershell
hermes gateway status      # Merged view: schtasks + Startup folder + running PID
hermes gateway start       # Starts the scheduled task now
hermes gateway stop        # Graceful SIGTERM equivalent (TerminateProcess via psutil)
hermes gateway restart
hermes gateway uninstall   # Removes schtasks entry, Startup shortcut, pid file
```

`hermes gateway status` идемпотентен — можешь вызвать его тысячу раз подряд, и он никогда случайно не убьёт шлюз. (До PR #21561 он молча делал это через `os.kill(pid, 0)`, конфликтуя с `CTRL_C_EVENT` на уровне C — см. раздел «внутреннее управление процессами» ниже, если интересна история.)

### Почему не Windows Service?

Службы требуют прав администратора для установки и привязывают жизненный цикл шлюза к загрузке машины, а не к входу пользователя. Типичный пользователь Hermes хочет: вход → шлюз доступен, выход → шлюз исчезает. Scheduled Tasks делают именно это без повышения прав. Если действительно нужен сервис, используй `nssm` или `sc create` вручную — но, скорее всего, это не требуется.
## Структура данных

| Путь | Содержимое |
|---|---|
| `%LOCALAPPDATA%\hermes\hermes-agent\` | Git‑checkout + venv. Можно безопасно выполнить `Remove-Item -Recurse` и переустановить. |
| `%LOCALAPPDATA%\hermes\git\` | PortableGit (только если установщик его подготовил). |
| `%LOCALAPPDATA%\hermes\node\` | Portable Node.js (только если установщик его подготовил). |
| `%LOCALAPPDATA%\hermes\bin\` | shim `hermes.cmd`, добавлен в PATH пользователя. |
| `%USERPROFILE%\.hermes\` | Твоя конфигурация, аутентификация, skills, сессии, логи. **Сохраняется при переустановках.** |

Разделение намеренно: `%LOCALAPPDATA%\hermes` — временная инфраструктура (можно удалить, а однострочная команда восстановит её). `%USERPROFILE%\.hermes` — твои данные — конфигурация, память, skills, история сессий — и имеет тот же вид, что и установка в Linux. Синхронизируй её между машинами, и твой Hermes будет с тобой.

**Переопределить `HERMES_HOME`:** установи переменную окружения, указывающую на другой каталог данных. Работает так же, как в Linux.
## Инструмент браузера

Инструмент браузера использует `agent‑browser` (Node‑помощник) для управления Chromium. На Windows:

- Установщик помещает `agent‑browser` в PATH через npm.
- `shutil.which("agent‑browser", path=…)` автоматически находит `.cmd`‑shim — `CreateProcessW` не может выполнить скрипт без расширения, поэтому Hermes всегда разрешает его к обёртке `.CMD`. Не вызывай вручную скрипт‑shebang; всегда используй `.cmd`.
- Playwright Chromium автоматически устанавливается при первом запуске (`npx playwright install chromium`). Если установка не удалась, `hermes doctor` выводит подсказку с рекомендацией исправления.
## Запуск Hermes на Windows — практические заметки

### PATH после установки

Установщик добавляет `%LOCALAPPDATA%\hermes\bin` в **PATH пользователя** через `[Environment]::SetEnvironmentVariable`. Открытые терминалы этого не видят — открой новое окно PowerShell (или вкладку Windows Terminal) после установки. Закрой и открой его заново, не делай `$env:PATH += …` вручную, если только точно не знаешь, что делаешь.

Проверь:

```powershell
Get-Command hermes        # should print C:\Users\<you>\AppData\Local\hermes\bin\hermes.cmd
hermes --version
```

### Переменные окружения

Hermes учитывает как `$env:X` (область процесса), так и переменные окружения пользователя (постоянные, задаются в **System Properties → Environment Variables**). Установка API‑ключей в `%USERPROFILE%\.hermes\.env` — обычный путь, такой же как в Linux:

```
OPENROUTER_API_KEY=sk-or-...
TELEGRAM_BOT_TOKEN=...
```

Не размещай секреты в переменных окружения пользователя, если только ты специально не хочешь, чтобы каждый процесс Windows их видел (это обычно не то, что тебе нужно).

### Специфичные для Windows переменные окружения

Эти переменные влияют только на нативные установки Windows:

| Variable | Effect |
|---|---|
| `HERMES_GIT_BASH_PATH` | Переопределяет поиск `bash.exe`. Укажи любой bash — полный Git‑for‑Windows, bash из WSL через символьную ссылку, MSYS2, Cygwin. Установщик задаёт её автоматически. |
| `HERMES_DISABLE_WINDOWS_UTF8` | Установи в `1`, чтобы отключить shim UTF‑8 stdio и вернуться к кодовой странице локали. Полезно для изоляции ошибки кодировки. |
| `EDITOR` / `VISUAL` | Твой редактор для `/edit` и `Ctrl‑X Ctrl‑E`. Hermes использует `notepad` по умолчанию, если обе переменные не заданы. |
## Удаление

From PowerShell:

```powershell
hermes uninstall
```

Это чистый способ — удаляет запись `schtasks`, ярлык в папке **Startup**, обёртку `hermes.cmd`, удаляет `%LOCALAPPDATA%\hermes\hermes-agent\` и сокращает переменную среды **PATH** пользователя. Папка `%USERPROFILE%\.hermes\` (твоё конфигурационные файлы, учётные данные, skills, sessions, logs) остаётся нетронутой на случай переустановки.

Чтобы полностью удалить всё:

```powershell
hermes uninstall
Remove-Item -Recurse -Force "$env:USERPROFILE\.hermes"
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\hermes"
```

Подкоманда CLI `hermes uninstall` также обрабатывает случай, когда запись `schtasks` была зарегистрирована под другим именем задачи (старые установки) — она ищет по пути установки, а не по жёстко заданному имени задачи.
## Внутреннее управление процессами

Это справочный материал — пропусти, если только не отлаживаешь странную ситуацию «процесс сам себя убивает».

В Linux и macOS идиома POSIX `os.kill(pid, 0)` является проверкой прав доступа без действия: «жив ли этот PID и могу ли я послать ему сигнал?». В Windows `os.kill` в Python сопоставляет `sig=0` с `CTRL_C_EVENT` — они совпадают по целочисленному значению 0 — и направляет его через `GenerateConsoleCtrlEvent(0, pid)`, который рассылает Ctrl+C **всей группе процессов консоли**, содержащей целевой PID. Это [bpo-14484](https://bugs.python.org/issue14484), открытый с 2012 года. Исправить его нельзя, потому что изменение сломает скрипты, полагающиеся на текущее поведение.

Последствие: любой код, который проверял «жив ли PID» через `os.kill(pid, 0)` в Windows, тихо убивал цель. Hermes перенёс все такие места (14 в 11 файлах) на `gateway.status._pid_exists()`, который использует `psutil.pid_exists()` (а тот, в свою очередь, использует `OpenProcess + GetExitCodeProcess` в Windows — без сигналов). Если ты пишешь плагин или патч, используй напрямую `psutil.pid_exists()` или `gateway.status._pid_exists()` — никогда `os.kill(pid, 0)`.

`scripts/check-windows-footguns.py` принудительно проверяет это в CI: любой новый вызов `os.kill(pid, 0)` не проходит проверку `Windows footguns (blocking)`, если только строка не содержит маркер `# windows-footgun: ok — <reason>`.
## Распространённые подводные камни

**`hermes: command not found` сразу после установки.**
Открой новое окно PowerShell. Установщик добавил `%LOCALAPPDATA%\hermes\bin` в пользовательский PATH, но уже запущенные оболочки нужно перезапустить, чтобы они его подхватили. Пока можно выполнить `& "$env:LOCALAPPDATA\hermes\bin\hermes.cmd"`.

**`WinError 193: %1 is not a valid Win32 application` при запуске инструмента.**
Ты попал на вызов shebang‑скрипта, который обошёл `.cmd`‑обёртку. Hermes разрешает команды через `shutil.which(cmd, path=local_bin)`, поэтому PATHEXT подхватывает `.CMD`. Если ты вызываешь инструмент по жёстко заданному пути, переключись на вариант с `.cmd` (например, `npx.cmd`, а не `npx`).

**`[scriptblock]::Create(...)` падает с `The assignment expression is not valid`.**
Твой загруженный `install.ps1` содержит UTF‑8 BOM. Форма `irm | iex` автоматически удаляет BOM; `[scriptblock]::Create((irm ...))` этого не делает. Запусти снова простую форму `irm | iex` или скачай скрипт вручную и сохрани его без BOM через `[IO.File]::WriteAllText($path, $text, (New-Object Text.UTF8Encoding $false))`.

**Gateway не остаётся запущенным после перезагрузки.**
Проверь `hermes gateway status` — он объединяет запись `schtasks`, ярлык в папке **Startup** (если использовался) и текущий PID. Если `schtasks` зарегистрирован, но не запущен, групповая политика может блокировать триггеры `ONLOGON`. Выполни `schtasks /Query /TN HermesGateway /V /FO LIST`, чтобы увидеть причину сбоя, либо вернись к пути **Startup**, удалив и переустановив шлюз с `HERMES_GATEWAY_FORCE_STARTUP=1`.

**`/edit` всё ещё ничего не делает после установки `$env:EDITOR`.**
Ты задала переменную только в текущем процессе; закрой и открой оболочку заново, либо задай её в пользовательском масштабе в **System Properties → Environment Variables**. Проверь с помощью `echo $env:EDITOR` в новом окне PowerShell.

**Инструмент браузера запускается, но инструменты таймаутятся.**
Chromium автоматически устанавливается при первом запуске. Если установка не удалась (ограничение скорости GitHub, сбой CDN Playwright), запусти `hermes doctor` — он покажет отсутствие Chromium и выведет точную команду `npx playwright install chromium` для исправления.

**`agent-browser` падает с странной ошибкой версии Node.**
Установщик помещает Node 22 в `%LOCALAPPDATA%\hermes\node`, но в PATH может быть более старый системный Node 18, который находится первым. Перемести каталог `node` Hermes выше в PATH или удали системную установку, если ты не используешь Node в других местах.

**Китайские / японские / арабские символы отображаются как `?` в CLI.**
UTF‑8 shim для stdio не активировался. Убедись, что `HERMES_DISABLE_WINDOWS_UTF8` НЕ установлен (`Get-ChildItem env:HERMES_DISABLE_WINDOWS_UTF8`). Если переменная пуста, а `?` всё равно появляются, консольный хост (очень старый `cmd.exe`) может вообще не поддерживать UTF‑8 — переключись на Windows Terminal.

**Gateway не может отправлять фотографии в Telegram — "`BadRequest: payload contains invalid characters`".**
Это не связано напрямую с Windows, но часто проявляется сначала здесь. Обычно это значит, что путь к файлу содержит неэкранированные обратные слеши в JSON‑теле. Telegram должен получать пути, нормализованные Hermes, а не сырые Windows‑пути — если ошибка возникает в кастомном плагине, убедись, что передаёшь путь, предоставленный Hermes, а не `str(Path(...))` из пользовательского ввода.

**Странности с кодировкой после `git pull` — "Works on my other machine".**
Если ты редактировал конфигурацию Hermes или skill на Windows в редакторе, не поддерживающем UTF‑8 (старый Notepad, некоторые китайские IME), файл мог быть сохранён с BOM. Hermes допускает `utf-8-sig` при большинстве чтений конфигураций, но BOM внутри свернутого скалярного YAML (`description: >`) тихо ломает парсинг YAML. Сохрани файл как обычный UTF‑8 без BOM.
## Куда идти дальше

- **[Установка](../getting-started/installation.md)** — полная страница установки, включая Linux/macOS/WSL2/Termux.
- **[Руководство по Windows (WSL2)](./windows-wsl-quickstart.md)** — если тебе нужны POSIX‑семантика или панель терминала в дашборде.
- **[Справочник CLI](../reference/cli-commands.md)** — все подкоманды `hermes`.
- **[FAQ](../reference/faq.md)** — часто задаваемые вопросы, не связанные с Windows.
- **[Шлюз обмена сообщениями](./messaging/index.md)** — запуск Telegram/Discord/Slack в Windows.