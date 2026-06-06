---
title: "Windows (Native) Посібник — рання бета"
description: "Ранній BETA: запуск Hermes Agent нативно на Windows 10/11 — встановлення, матриця функцій, консоль UTF‑8, Git Bash, шлюз як заплановане завдання, обробка редактора, PATH, видалення та типові підводні камені"
sidebar_label: "Windows (Native) — Beta"
sidebar_position: 3
---

# Посібник по Windows (нативно) — рання бета

:::warning Early BETA
Підтримка Windows у **ранньому бета‑режимі**. Вона встановлюється, працює і проходить наш Windows‑footgun lint, проте ще не проходила масштабних випробувань, як це було з Linux/macOS/WSL2. Очікуй деякі недоліки — особливо щодо обробки підпроцесів, особливостей шляхів і виводу в консолі не‑ASCII символів. Будь ласка, [повідомляй про проблеми](https://github.com/NousResearch/hermes-agent/issues) з кроками відтворення, коли щось не працює. Якщо потрібне стабільне рішення вже сьогодні, скористайся [Linux/macOS‑встановлювачем у WSL2](./windows-wsl-quickstart.md) замість цього.
:::

Hermes працює нативно на Windows 10 та Windows 11 — без WSL, без Cygwin, без Docker. Ця сторінка — детальний огляд: що працює нативно, що лише у WSL, що саме робить інсталятор і які специфічні налаштування Windows можуть знадобитися.

Якщо треба лише встановити, достатньо однорядка з [головної сторінки](/) або [сторінки встановлення](../getting-started/installation#windows-native-powershell--early-beta). Повернись сюди, коли щось здивує.

:::tip Want WSL instead?
Якщо тобі потрібне справжнє POSIX‑середовище (для вбудованого терміналу в панелі, семантики `fork`, файлових спостерігачів у стилі Linux тощо), переглянь **[Windows (WSL2) Guide](./windows-wsl-quickstart.md)**. Обидва варіанти співіснують без конфліктів: нативні дані розташовані в `%LOCALAPPDATA%\hermes`, дані WSL — у `~/.hermes`.
:::
## Швидке встановлення

Відкрий **PowerShell** (або Windows Terminal) і виконай:

```powershell
iex (irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1)
```

Не потрібні права адміністратора. Інсталятор розміщується у `%LOCALAPPDATA%\hermes\` і додає `hermes` до твого **User PATH** — відкрий новий термінал після завершення.

**Параметри інсталятора** (вимагає форму `scriptblock` для передачі параметрів):

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1))) -NoVenv -SkipSetup -Branch main
```

| Parameter | Default | Purpose |
|---|---|---|
| `-Branch` | `main` | Клонувати конкретну гілку (корисно для тестування PR) |
| `-Commit` | unset | Зафіксувати встановлення на конкретному SHA‑коміті (перезаписує `-Branch`) |
| `-Tag` | unset | Зафіксувати встановлення на конкретному git‑тегу (наприклад `v0.14.0`) |
| `-NoVenv` | off | Пропустити створення venv (просунуто — ти сам керуєш Python) |
| `-SkipSetup` | off | Пропустити майстер налаштування `hermes setup` після інсталяції |
| `-HermesHome` | `%LOCALAPPDATA%\hermes` | Перевизначити каталог даних |
| `-InstallDir` | `%LOCALAPPDATA%\hermes\hermes-agent` | Перевизначити розташування коду |

Інсталятор автоматично повторює невдалі git‑запити та видаляє BOM з будь‑якого завантаженого `install.ps1`‑payload, тому UTF‑8 BOM, отриманий під час HTTP‑транзиту, більше не руйнує форму `[scriptblock]::Create((irm ...))`.

### Десктопний інсталятор (альтернатива)

Легкий GUI‑інсталятор також доступний — корисний, якщо ти віддаєш перевагу двічі клацнути `.exe`, а не відкривати PowerShell. Завантаж Hermes Desktop, запусти інсталятор, і при першому запуску GUI викликає `install.ps1` під капотом, щоб підготувати Python (через `uv`), Node, PortableGit та інші залежності, описані нижче. Після першого запуску десктопний додаток і `hermes` CLI, встановлені через PowerShell, ділять один і той же каталог `%LOCALAPPDATA%\hermes\hermes-agent` та каталог даних `%USERPROFILE%\.hermes` — перемикайся між GUI та CLI довільно.

Використовуй десктопний інсталятор, коли потрібен знайомий Windows‑досвід встановлення або ти передаєш Hermes користувачеві без технічних навичок; використай PowerShell‑однорядковий скрипт, коли вже працюєш у терміналі.

### Bootstrap залежностей (`dep_ensure`)

При першому запуску (і за запитом, коли виявлено відсутній інструмент) Hermes запускає невеликий Python‑bootstrapper — `hermes_cli/dep_ensure.py` — який перевіряє і ліниво встановлює необхідні не‑Python залежності. На Windows це:

| Dependency | Чому Hermes це потребує |
|---|---|
| **PortableGit** | Надає `bash.exe` для інструменту терміналу та `git` для клонувань під час сесії. Поставляється під час інсталяції, а не `dep_ensure`. |
| **Node.js 22** | Потрібен для браузерного інструменту (`agent-browser`), веб‑моста TUI та моста WhatsApp. |
| **ffmpeg** | Конвертація аудіоформатів для TTS / голосових повідомлень. |
| **ripgrep** | Швидкий пошук файлів — при відсутності повертається до `grep`. |
| **npm packages** | `agent-browser`, Playwright Chromium та будь‑які Node‑залежності інструментів встановлюються один раз при першому використанні браузерного інструменту. |

Кожна залежність перевіряється за допомогою `shutil.which(...)`; якщо бінарник відсутній і запуск інтерактивний, `dep_ensure` пропонує його встановити (запускаючи `scripts\install.ps1 -ensure <dep>` для реальної логіки інсталяції). У неінтерактивних запусках (gateway, cron, безголові десктопні запуски) запит пропускається, а замість нього виводиться чітка помилка `this feature needs <dep>`.
## Що насправді робить інсталятор

Зверху донизу, у зазначеному порядку:

1. **Bootstraps `uv`** — швидкий менеджер Python від Astral. Встановлюється у `%USERPROFILE%\.local\bin`.
2. **Installs Python 3.11** через `uv`. Не потрібен вже встановлений Python.
3. **Installs Node.js 22** (winget, якщо доступний, інакше портативний tar‑ball Node, розпакований у `%LOCALAPPDATA%\hermes\node`). Використовується для інструменту браузера та моста WhatsApp.
4. **Installs portable Git** — якщо `git` вже є в PATH, інсталятор його використовує; інакше завантажує обрізаний, самодостатній **PortableGit** (~45 МБ, з офіційного релізу `git-for-windows`) у `%LOCALAPPDATA%\hermes\git`. Без прав адміністратора, без реєстру Windows‑інсталятора, без впливу на інші програми в системі.
5. **Clones the repo** у `%LOCALAPPDATA%\hermes\hermes-agent` і створює в ньому virtualenv.
6. **Tiered `uv pip install`** — спочатку пробує `.[all]`, у випадку невдачі переходить до поступово менших наборів (`[messaging,dashboard,ext]` → `[messaging]` → `.`), якщо залежність `git+https` падає через обмеження GitHub. Запобігає режиму помилки «одна помилка переводить у чисту інсталяцію».
7. **Auto‑installs messaging SDKs** згідно `.env` — якщо присутні `TELEGRAM_BOT_TOKEN` / `DISCORD_BOT_TOKEN` / `SLACK_BOT_TOKEN` / `SLACK_APP_TOKEN` / `WHATSAPP_ENABLED`, виконує `python -m ensurepip --upgrade` та цільові виклики `pip install`, щоб SDK кожної платформи був імпортований.
8. **Sets `HERMES_GIT_BASH_PATH`** до знайденого `bash.exe`, щоб Hermes визначав його однозначно у нових оболонках.
9. **Adds `%LOCALAPPDATA%\hermes\bin` to User PATH** — робить команду `hermes` доступною після відкриття нового терміналу.
10. **Runs `hermes setup`** — звичний майстер першого запуску (модель, провайдер, toolsets). Пропусти за допомогою `-SkipSetup`.

:::tip Пропусти пошук провайдера у Windows
Native Windows ще в ранній бета‑версії, і налаштування API‑ключів для кожного інструменту (Firecrawl, FAL, Browser Use, OpenAI TTS) є найскладнішою частиною отримання корисного агента. Підписка на [Nous Portal](/user-guide/features/tool-gateway) охоплює модель **і** всі ці інструменти через один OAuth‑вхід. Після завершення інсталяції запусти `hermes setup --portal`, щоб підключити все.
:::
## Матриця функцій

Все, крім вбудованої панелі терміналу в дашборді, працює нативно у Windows.

| Функція | Нативний Windows | WSL2 |
|---|---|---|
| CLI (`hermes chat`, `hermes setup`, `hermes gateway`, …) | ✓ | ✓ |
| Інтерактивний TUI (`hermes --tui`) | ✓ | ✓ |
| Шлюз обміну повідомленнями (Telegram, Discord, Slack, WhatsApp, 15+ платформ) | ✓ | ✓ |
| Планувальник cron | ✓ | ✓ |
| Інструмент браузера (Chromium через Node) | ✓ | ✓ |
| Сервери MCP (stdio та HTTP) | ✓ | ✓ |
| Локальний Ollama / LM Studio / llama-server | ✓ | ✓ (через мережу WSL) |
| Веб‑дашборд (сесії, завдання, метрики, конфіг) | ✓ | ✓ |
| Вбудована панель терміналу `/chat` у дашборді | ✗ (потрібен POSIX PTY) | ✓ |
| Автозапуск при вході в систему | ✓ (schtasks) | ✓ (systemd) |

Вкладка `/chat` у дашборді вбудовує реальний термінал через POSIX PTY (`ptyprocess`). У нативному Windows немає еквівалентного примітиву; `pywinpty` / Windows ConPTY могли б працювати, але це окрема реалізація — вважаємо це майбутньою роботою. **Решта дашборду працює нативно** — лише ця вкладка показує банер «використовуй WSL2 для цього».
## Як Hermes запускає shell‑команди у Windows

Інструмент терміналу Hermes виконує команди через **Git Bash**, таку ж стратегію, яку використовує Claude Code. Це обминає розрив між POSIX і Windows без переписування кожного інструмента.

Порядок пошуку `bash.exe`:

1. Змінна середовища `HERMES_GIT_BASH_PATH`, якщо встановлена.
2. `%LOCALAPPDATA%\hermes\git\usr\bin\bash.exe` (PortableGit, керований інсталятором).
3. `%LOCALAPPDATA%\hermes\git\bin\bash.exe` (старий розташунок Git‑for‑Windows).
4. Системна інсталяція Git‑for‑Windows (`%ProgramFiles%\Git\bin\bash.exe` тощо).
5. MSYS2, Cygwin або будь‑який `bash.exe` у PATH як останній варіант.

Інсталятор явно встановлює `HERMES_GIT_BASH_PATH`, тому нові сеанси PowerShell не треба його повторно шукати. Перевизнач її, якщо хочеш, щоб Hermes використовував конкретний bash — наприклад, системний Git Bash або bash у WSL через символічне посилання.

**Підводний камінь:** Розташування MinGit відрізняється від повного інсталятору Git‑for‑Windows — bash знаходиться у `usr\bin\bash.exe`, а не в `bin\bash.exe`. Hermes перевіряє обидва варіанти. Якщо розпаковуєш zip‑архів MinGit вручну, переконайся, що вибрав **не‑busybox** варіант (`MinGit-*-64-bit.zip`, а не `MinGit-*-busybox*.zip`) — збірки busybox постачають `ash` замість `bash`, і більшість coreutils відсутні.
## UTF-8 консоль у Windows

Типове stdio Python у Windows використовує активну кодову сторінку консолі (зазвичай cp1252 або cp437). Банер Hermes, список slash‑команд, стрічка інструментів, панелі Rich та описи навичок містять Unicode. Без втручання будь‑яке з цього призведе до збою з `UnicodeEncodeError: 'charmap' codec can't encode character…`.

Виправлення знаходиться у `hermes_cli/stdio.py::configure_windows_stdio()`, викликається на початку кожної точки входу (`cli.py::main`, `hermes_cli/main.py::main`, `gateway/run.py::main`). Воно:

1. Перемикає кодову сторінку консолі на CP_UTF8 (65001) за допомогою `kernel32.SetConsoleCP` / `SetConsoleOutputCP`.
2. Переналаштовує `sys.stdout` / `sys.stderr` / `sys.stdin` на UTF-8 з `errors='replace'`.
3. Встановлює `PYTHONIOENCODING=utf-8` і `PYTHONUTF8=1` (через `setdefault`, тому явні значення користувача мають перевагу), щоб дочірні процеси Python успадковували UTF-8.
4. Встановлює `EDITOR=notepad`, якщо не задано ні `EDITOR`, ні `VISUAL` (дивись розділ Editor нижче).

Ідемпотентний. Нічого не робить на не‑Windows системах.

**Вимкнення:** `HERMES_DISABLE_WINDOWS_UTF8=1` у середовищі повертає до старого шляху cp1252 stdio. Корисно для діагностики проблем кодування; навряд чи це правильне налаштування у звичайній роботі.
## Редактор (`Ctrl‑X Ctrl‑E`, `/edit`)

До #21561 натискання `Ctrl‑X Ctrl‑E` або введення `/edit` безшумно нічого не робило у Windows. `prompt_toolkit` має жорстко закодований список запасних POSIX‑абсолютних шляхів (`/usr/bin/nano`, `/usr/bin/pico`, `/usr/bin/vi`, …), який ніколи не розв’язується у Windows — навіть при повністю встановленому Git for Windows.

Шім Windows stdio у Hermes тепер встановлює `EDITOR=notepad` за замовчуванням. Notepad постачається з кожною інсталяцією Windows і працює як блокуючий редактор — `subprocess.call(["notepad", file])` блокує, доки вікно не закриється.

**Перевизначення користувачем все ще мають пріоритет** (вони перевіряються перед `setdefault`):

| Editor | команда PowerShell |
|---|---|
| VS Code | `$env:EDITOR = "code --wait"` |
| Notepad++ | `$env:EDITOR = "'C:\Program Files\Notepad++\notepad++.exe' -multiInst -nosession"` |
| Neovim | `$env:EDITOR = "nvim"` |
| Helix | `$env:EDITOR = "hx"` |

Прапорець `--wait` у VS Code критичний — без нього редактор повертається одразу, і Hermes отримує порожній буфер.

Встанови його назавжди у своєму профілі PowerShell:

```powershell
# In $PROFILE
$env:EDITOR = "code --wait"
```

Або як змінну середовища користувача у налаштуваннях системи, щоб кожна нова оболонка її підхоплювала.
## `Ctrl+Enter` для нового рядка в CLI

Windows Terminal передає `Ctrl+Enter` як окрему послідовність клавіш. Hermes прив’язує його до «вставити новий рядок», тож ти можеш створювати багаторядкові підказки в CLI, не повертаючись до `Esc`‑потім‑`Enter`. Працює у Windows Terminal, інтегрованому терміналі VS Code та будь‑якій сучасній Windows‑консолі, що підтримує VT‑послідовності escape.

У застарілих консолях `cmd.exe` `Ctrl+Enter` зводиться до простого `Enter` — використай `Esc Enter` замість цього, або оновись до Windows Terminal (це безкоштовно і встановлюється за замовчуванням у Windows 11).
## Запуск gateway під час входу в Windows

`hermes gateway install` у Windows використовує **Scheduled Tasks** з запасним (варіантом) у папці Startup — без потреби в адміністраторських правах.

### Встановлення

```powershell
hermes gateway install
```

Що відбувається «під капотом»:

1. `schtasks /Create /SC ONLOGON /RL LIMITED /TN HermesGateway` — реєструє завдання, яке запускається під час входу з стандартними (не підвищеними) правами. Без запиту UAC.
2. Якщо `schtasks` заблоковано груповою політикою, використовується запасний (варіант) запису ярлика `start /min cmd.exe /d /c <wrapper>` у `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`. Такий же ефект, трохи грубіший.
3. Запускає gateway **відокремлено через `pythonw.exe`** — не `python.exe`. `pythonw.exe` не має підключеної консолі, що захищає його від широкомовних `CTRL_C_EVENT` від процесів‑сиблінгів (реальна проблема, яка раніше вбивала gateway, коли ти натискав Ctrl +C у будь‑якому процесі тієї ж групи).

Прапори, що використовуються при запуску: `DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW | CREATE_BREAKAWAY_FROM_JOB`.

### Керування

```powershell
hermes gateway status      # Merged view: schtasks + Startup folder + running PID
hermes gateway start       # Starts the scheduled task now
hermes gateway stop        # Graceful SIGTERM equivalent (TerminateProcess via psutil)
hermes gateway restart
hermes gateway uninstall   # Removes schtasks entry, Startup shortcut, pid file
```

`hermes gateway status` ідемпотентний — виклич його тисячу разів підряд, і він ніколи випадково не вб’є gateway. (До PR #21561 він тихо робив це, через `os.kill(pid, 0)`, що конфліктувало з `CTRL_C_EVENT` на рівні C — дивись «внутрішня робота процесів» нижче, якщо тебе цікавить ця історія.)

### Чому не Windows Service?

Сервіси вимагають прав адміністратора для встановлення і прив’язують життєвий цикл gateway до завантаження машини, а не до входу користувача. Типовий користувач Hermes хоче: вхід → gateway доступний, вихід → gateway зникає. Scheduled Tasks робить саме це без підвищення прав. Якщо ти дійсно хочеш сервіс, використай `nssm` або `sc create` вручну — але, ймовірно, це не потрібно.
## Макет даних

| Шлях | Вміст |
|---|---|
| `%LOCALAPPDATA%\hermes\hermes-agent\` | Git checkout + venv. Безпечно `Remove-Item -Recurse` і перевстановити. |
| `%LOCALAPPDATA%\hermes\git\` | PortableGit (лише якщо інсталятор його підготував). |
| `%LOCALAPPDATA%\hermes\node\` | Portable Node.js (лише якщо інсталятор його підготував). |
| `%LOCALAPPDATA%\hermes\bin\` | `hermes.cmd` shim, додано до User PATH. |
| `%USERPROFILE%\.hermes\` | Твоя конфігурація, auth, skills, сесії, logs. **Залишається після перевстановлення.** |

Розподіл навмисний: `%LOCALAPPDATA%\hermes` — це одноразова інфраструктура (можеш її видалити, а однорядковий скрипт відновить). `%USERPROFILE%\.hermes` — це твої дані — конфігурація, пам'ять, skills, історія сесій — і має таку ж структуру, як у Linux‑встановлення. Синхронізуй її між машинами, і твій Hermes буде з тобою.

**Перевизнач `HERMES_HOME`:** встанови змінну середовища, щоб вказати інший каталог даних. Працює так само, як у Linux.
## Browser tool

Інструмент браузера використовує `agent-browser` (допоміжний модуль Node) для керування Chromium. На Windows:

- Інсталятор додає `agent-browser` у `PATH` за допомогою npm.
- `shutil.which("agent-browser", path=…)` автоматично знаходить shim‑файл `.cmd` — `CreateProcessW` не може виконати скрипт без розширення, тому Hermes завжди звертається до обгортки `.CMD`. Не викликай скрипт‑shebang вручну; завжди використовуйте `.cmd`.
- Playwright Chromium встановлюється автоматично під час першого запуску (`npx playwright install chromium`). Якщо встановлення не вдається, `hermes doctor` повідомляє про це з підказкою щодо виправлення.
## Запуск Hermes на Windows — практичні нотатки

### PATH після встановлення

Інсталятор додає `%LOCALAPPDATA%\hermes\bin` до твого **User PATH** за допомогою `[Environment]::SetEnvironmentVariable`. Існуючі термінали цього не помічають — відкрий нове вікно PowerShell (або вкладку Windows Terminal) після інсталяції. Закрий‑і‑відкрий, не додавай `$env:PATH += …` вручну, якщо не знаєш, що робиш.

Перевірка:

```powershell
Get-Command hermes        # should print C:\Users\<you>\AppData\Local\hermes\bin\hermes.cmd
hermes --version
```

### Змінні середовища

Hermes підтримує як `$env:X` (у межах процесу), так і змінні середовища користувача (постійні, встановлені в **System Properties → Environment Variables**). Зберігання API‑ключів у `%USERPROFILE%\.hermes\.env` — це звичний шлях, аналогічний Linux:

```
OPENROUTER_API_KEY=sk-or-...
TELEGRAM_BOT_TOKEN=...
```

Не розміщуй секрети у змінних середовища користувача, якщо ти не хочеш, щоб їх бачили всі процеси Windows (це не те, чого ти прагнеш).

### Специфічні для Windows змінні середовища

Вони впливають лише на нативні інсталяції Windows:

| Variable | Effect |
|---|---|
| `HERMES_GIT_BASH_PATH` | Перевизначає пошук `bash.exe`. Вкажи будь‑який bash — повний Git‑for‑Windows, WSL bash через symlink, MSYS2, Cygwin. Інсталятор встановлює це автоматично. |
| `HERMES_DISABLE_WINDOWS_UTF8` | Встанови `1`, щоб вимкнути shim UTF‑8 stdio і повернутись до кодової сторінки локалі. Корисно для діагностики помилки кодування. |
| `EDITOR` / `VISUAL` | Твій редактор для `/edit` та `Ctrl‑X Ctrl‑E`. Hermes за замовчуванням використовує `notepad`, якщо обидві змінні не задані. |
## Видалення

З PowerShell:

```powershell
hermes uninstall
```

Це чистий спосіб — видаляє запис `schtasks`, ярлик у папці **Startup**, shim `hermes.cmd`, видаляє `%LOCALAPPDATA%\hermes\hermes-agent\` і скорочує змінну середовища **PATH** користувача. Директорію `%USERPROFILE%\.hermes\` залишає недоторканою (твої конфіг, автентифікація, skills, сесії, логи) на випадок повторної інсталяції.

Щоб повністю очистити все:

```powershell
hermes uninstall
Remove-Item -Recurse -Force "$env:USERPROFILE\.hermes"
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\hermes"
```

Підкоманда CLI `hermes uninstall` також обробляє випадок, коли запис `schtasks` був зареєстрований під іншим ім’ям завдання (старі інсталяції) — вона шукає за шляхом інсталяції, а не за жорстко закодованим ім’ям завдання.
## Внутрішнє управління процесами

Це фоновий матеріал — пропусти, якщо лише не діагностуєш дивний випадок «він вбиває самого себе».

У Linux та macOS ідіома POSIX `os.kill(pid, 0)` є безопераційною перевіркою прав: «чи цей PID живий і чи можу я послати йому сигнал?». У Windows функція Python `os.kill` відображає `sig=0` у `CTRL_C_EVENT` — вони збігаються за цілим значенням 0 — і передає його через `GenerateConsoleCtrlEvent(0, pid)`, що розсилає Ctrl+C **всю групу процесів консолі**, що містить цільовий PID. Це [bpo-14484](https://bugs.python.org/issue14484), відкрито ще у 2012 році. Виправлення не планується, оскільки зміна поведінки зламає скрипти, які покладаються на поточну.

Наслідок: будь‑який код, який сказав «перевірити, чи PID живий» за допомогою `os.kill(pid, 0)` у Windows, тихо вбивав ціль. Hermes переніс усі такі місця (14 у 11 файлах) на `gateway.status._pid_exists()`, який використовує `psutil.pid_exists()` (а той, у свою чергу, користується `OpenProcess + GetExitCodeProcess` у Windows — без сигналів). Якщо ти пишеш плагін або патч, використай безпосередньо `psutil.pid_exists()` або `gateway.status._pid_exists()` — ніколи `os.kill(pid, 0)`.

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1))) -NoVenv -SkipSetup -Branch main
``` `scripts/check-windows-footguns.py` забезпечує це в CI: будь‑який новий виклик `os.kill(pid, 0)` провалює перевірку `Windows footguns (blocking)`, якщо лише рядок не містить маркера `# windows-footgun: ok — <reason>`.
## Common pitfalls

**`hermes: command not found` right after install.**
Відкрий нове вікно PowerShell. Інсталятор додав `%LOCALAPPDATA%\hermes\bin` до **User** PATH, але вже запущені оболонки потрібно перезапустити, щоб вони його підхапали. Поки що можна виконати `& "$env:LOCALAPPDATA\hermes\bin\hermes.cmd"`.

**`WinError 193: %1 is not a valid Win32 application` when running a tool.**
Ти викликав скрипт‑shebang, який обійшов `.cmd`‑шім. Hermes шукає команди через `shutil.which(cmd, path=local_bin)`, тому `PATHEXT` підхоплює `.CMD`. Якщо ти викликаєш інструмент за жорстко заданим шляхом, перейди на варіант з розширенням `.cmd` (наприклад, `npx.cmd`, а не `npx`).

**`[scriptblock]::Create(...)` fails with `The assignment expression is not valid`.**
Твій завантажений `install.ps1` містить UTF‑8 BOM. Форма `irm | iex` автоматично видаляє BOM, а `[scriptblock]::Create((irm ...))` — ні. Перезапусти за допомогою простого `irm | iex` або завантаж скрипт вручну і збережи його без BOM, використовуючи `[IO.File]::WriteAllText($path, $text, (New-Object Text.UTF8Encoding $false))`.

**Gateway won't stay running after restart.**
Перевір `hermes gateway status` — він об’єднує запис у **schtasks**, ярлик у папці **Startup** (якщо використовується) і поточний PID. Якщо **schtasks** зареєстровано, але він не працює, групова політика може блокувати тригери `ONLOGON`. Запусти `schtasks /Query /TN HermesGateway /V /FO LIST`, щоб дізнатися причину збою, або повернись до шляху **Startup** шляхом видалення та повторної інсталяції з `HERMES_GATEWAY_FORCE_STARTUP=1`.

**`/edit` still does nothing after setting `$env:EDITOR`.**
Ти встановив змінну лише в поточному процесі; закрий і відкрий оболонку знову, або задай її у **User**‑scope в **System Properties → Environment Variables**. Перевір за допомогою `echo $env:EDITOR` у новому вікні PowerShell.

**Browser tool launches but tools time out.**
Chromium автоматично встановлюється під час першого запуску. Якщо інсталяція не вдалася (обмеження швидкості GitHub, проблеми з CDN Playwright), запусти `hermes doctor` — він покаже відсутній Chromium і виведе точну команду `npx playwright install chromium` для виправлення.

**`agent-browser` fails with a weird Node version error.**
Інсталятор розгортає Node 22 у `%LOCALAPPDATA%\hermes\node`, але у твоєму PATH може бути старіший системний Node 18, який стоїть раніше. Перемести каталог Node Hermes вище в PATH або видали системну інсталяцію, якщо Node тобі не потрібен.

**Chinese / Japanese / Arabic characters show as `?` in the CLI.**
UTF‑8 stdio shim не активувався. Переконайся, що змінна `HERMES_DISABLE_WINDOWS_UTF8` **не** встановлена (`Get-ChildItem env:HERMES_DISABLE_WINDOWS_UTF8`). Якщо вона порожня, а `?` все ще бачиш, консольний хост (дуже старий `cmd.exe`) може взагалі не підтримувати UTF‑8 — перейди на Windows Terminal.

**Gateway can't send Telegram photos — "`BadRequest: payload contains invalid characters`".**
Це не пов’язано з Windows, але часто проявляється саме тут. Зазвичай це означає, що у JSON‑тілі шлях до файлу містить неекрановані зворотні слеші. Telegram має отримувати шляхи, які нормалізує Hermes, а не «сырі» Windows‑шляхи — у власному плагіні передавай шлях, який повертає Hermes, а не `str(Path(...))` з вводу користувача.

**"Works on my other machine" encoding weirdness after `git pull`.**
Якщо ти редагував конфіг Hermes або скіл на Windows у не‑UTF‑8 редакторі (старий Notepad, деякі китайські IME), файл міг бути збережений з BOM. Hermes tolerates `utf-8-sig` у більшості читань конфігів, але BOM всередині складеного YAML‑скаляра (`description: >`) тихо ламає парсинг YAML. Перезапиши файл у чистий UTF‑8 без BOM.
## Куди далі

- **[Installation](../getting-started/installation.md)** — повна сторінка інсталяції, включаючи Linux/macOS/WSL2/Termux.
- **[Windows (WSL2) Guide](./windows-wsl-quickstart.md)** — якщо ти хочеш POSIX‑семантику або панель терміналу в дашборді.
- **[CLI Reference](../reference/cli-commands.md)** — усі підкоманди `hermes`.
- **[FAQ](../reference/faq.md)** — поширені питання, не пов’язані з Windows.
- **[Messaging Gateway](./messaging/index.md)** — запуск Telegram/Discord/Slack у Windows.