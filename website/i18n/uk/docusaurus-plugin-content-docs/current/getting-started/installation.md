---
sidebar_position: 2
title: "Встановлення"
description: "Встанови Hermes Agent на Linux, macOS, WSL2, native Windows (early beta), або Android через Termux"
---

# Встановлення

Запусти Hermes Agent і запусти його за менше ніж дві хвилини за допомогою одно‑рядкового інсталятору.
## Швидка установка

### Однорядковий інсталятор (Linux / macOS / WSL2)

Для встановлення через git, яке відстежує `main` і одразу дає останні зміни:

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

### Windows (нативний, PowerShell) — рання бета

:::warning Early BETA
Нативна підтримка Windows є **ранньою бетою**. Вона встановлюється і працює для типових шляхів, але ще не пройшла широкого дорожнього тестування, як наші POSIX‑інсталятори. Будь ласка, [повідомляй про проблеми](https://github.com/NousResearch/hermes-agent/issues), коли натрапляєш на недоліки. Для найперевіреніших налаштувань Windows сьогодні використай однорядковий інсталятор Linux/macOS у **WSL2**.
:::

Відкрий PowerShell і виконай:

```powershell
iex (irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1)
```

Інсталятор обробляє **все**: `uv`, Python 3.11, Node.js 22, `ripgrep`, `ffmpeg`, **і портативний Git Bash** (PortableGit — самодостатній дистрибутив Git‑for‑Windows, який постачається з `bash.exe` та повним POSIX‑інструментарієм, що Hermes використовує для команд оболонки; на 32‑бітних Windows інсталятор переходить на MinGit, у якому немає bash і вимикаються функції terminal‑tool / agent‑browser). Він клонуватиме репозиторій у `%LOCALAPPDATA%\hermes\hermes-agent`, створить virtualenv і додасть `hermes` до **User PATH**. Перезапусти термінал (або відкрий нове вікно PowerShell) після встановлення, щоб PATH оновився.

**Як обробляється Git:**
1. Якщо `git` вже є у PATH, інсталятор використовує існуючу інсталяцію.
2. Інакше завантажується портативний **PortableGit** (~50 МБ, з офіційного релізу `git-for-windows` на GitHub) і розпаковується у `%LOCALAPPDATA%\hermes\git`. Потрібних прав адміністратора немає. Повністю ізольовано — не буде конфлікту з будь‑якою системною інсталяцією Git, навіть якщо вона пошкоджена. (На 32‑бітних Windows інсталятор переходить на MinGit, бо PortableGit постачається лише з 64‑бітними та ARM64‑активами; функції Hermes, що залежать від bash, не працюватимуть на 32‑бітних хостах.)

**Чому не використовувати winget?** Раніші проєкти автоматично встановлювали Git через `winget install Git.Git`, але winget часто падає, коли системний Git частково або пошкоджений (саме тоді користувачі потребують простого інсталятора). Портативний підхід до Git обходить winget, реєстр Windows‑інсталятора та будь‑який існуючий системний Git. Якщо інсталяція Git у Hermes коли‑небудь зламається, виконай `Remove-Item %LOCALAPPDATA%\hermes\git` і запусти інсталятор знову — без впливу на систему, без драматичних видалень.

Інсталятор також встановлює `HERMES_GIT_BASH_PATH` до знайденого `bash.exe`, щоб Hermes визначав його однозначно у нових оболонках.

Якщо тобі зручніше WSL2, Linux‑інсталятор вище працює всередині нього; нативна та WSL‑версії можуть співіснувати без конфліктів (нативні дані живуть у `%LOCALAPPDATA%\hermes`, дані WSL — у `~/.hermes`).

**Десктоп‑інсталятор (альтернатива):** Доступний тонкий GUI‑інсталятор — завантаж `Hermes Desktop`, запусти `.exe`, і при першому запуску він викликає `install.ps1` під капотом, щоб підготувати Python (через `uv`), Node, PortableGit та інші залежності. Десктоп‑додаток і CLI, встановлені через PowerShell, ділять ті ж каталоги інсталяції та даних, тому можеш користуватись будь‑яким або обома варіантами. Дивись [Windows (Native) guide](../user-guide/windows-native#desktop-installer-alternative) для деталей.

### Android / Termux

Hermes тепер постачається і з інсталятором, сумісним з Termux:

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

Інсталятор автоматично виявляє Termux і переходить до перевіреного Android‑потоку:
- використовує `pkg` Termux для системних залежностей (`git`, `python`, `nodejs`, `ripgrep`, `ffmpeg`, інструменти збірки)
- створює virtualenv за допомогою `python -m venv`
- автоматично експортує `ANDROID_API_LEVEL` для збірок Android‑wheel
- надає перевагу широкому екстрату `.[termux-all]` і, у разі невдачі, переходить до меншого `.[termux]` (і, в кінці, до базової інсталяції)
- за замовчуванням пропускає неперевірений браузер/WhatsApp‑бустрап

Якщо потрібен повністю явний шлях, слідуй спеціальному [Termux guide](./termux.md).

:::note Windows Feature Parity (Early Beta)

Нативна Windows знаходиться у **ранній бета‑версії**. Все, окрім браузерного чат‑терміналу у панелі інструментів, працює нативно на Windows:
- **CLI (`hermes chat`, `hermes setup`, `hermes gateway`, …)** — нативно, використовує твій стандартний термінал
- **Gateway (Telegram, Discord, Slack, …)** — нативно, працює як фоновий процес PowerShell
- **Cron scheduler** — нативно
- **Browser tool** — нативно (Chromium через Node.js)
- **MCP servers** — нативно (підтримуються як stdio, так і HTTP‑транспорти)
- **Dashboard `/chat` terminal pane** — **лише WSL2** (використовує POSIX PTY; у нативній Windows немає еквіваленту). Решта панелі (сесії, завдання, метрики) працює нативно — лише вбудована вкладка PTY‑терміналу обмежена.

Встанови `HERMES_DISABLE_WINDOWS_UTF8=1` у середовище, якщо стикаєшся з помилкою кодування і хочеш повернутись до застарілого шляху cp1252 stdio (корисно для бісекції).
:::

### Що робить інсталятор

Інсталятор автоматично виконує все — всі залежності (Python, Node.js, ripgrep, ffmpeg), клонування репозиторію, створення віртуального середовища, глобальну настройку команди `hermes` та конфігурацію провайдера LLM. Після завершення ти готовий до спілкування.

#### Макет інсталяції

Куди інсталятор розміщує файли, залежить від того, чи встановлюєш ти як звичайний користувач, чи як root:

| Інсталятор | Де розташований код | Бінарник `hermes` | Каталог даних |
|---|---|---|---|
| pip install | Python site-packages | `~/.local/bin/hermes` (console_scripts) | `~/.hermes/` |
| Для користувача (git‑інсталятор) | `~/.hermes/hermes-agent/` | `~/.local/bin/hermes` (symlink) | `~/.hermes/` |
| Root‑mode (`sudo curl … \| sudo bash`) | `/usr/local/lib/hermes-agent/` | `/usr/local/bin/hermes` | `/root/.hermes/` (або `$HERMES_HOME`) |

Root‑mode **FHS‑layout** (`/usr/local/lib/…`, `/usr/local/bin/hermes`) відповідає розташуванню інших системних інструментів розробника у Linux. Це зручно для розгортання на спільних машинах, коли одна системна інсталяція має обслуговувати всіх користувачів. Переконфігурація (автентифікація, інструменти, сесії) все ще зберігається у `~/.hermes/` кожного користувача або у вказаному `HERMES_HOME`.

### Після встановлення

Перезавантаж shell і розпочинай чат:

```bash
source ~/.bashrc   # or: source ~/.zshrc
hermes             # Start chatting!
```

Щоб пізніше переналаштувати окремі параметри, використай спеціальні команди:

```bash
hermes model          # Choose your LLM provider and model
hermes tools          # Configure which tools are enabled
hermes gateway setup  # Set up messaging platforms
hermes config set     # Set individual config values
hermes setup          # Or run the full setup wizard to configure everything at once
```

:::tip Найшвидший шлях: Nous Portal
Один підпис охоплює 300+ моделей плюс [Tool Gateway](/user-guide/features/tool-gateway) (веб‑пошук, генерація зображень, TTS, хмарний браузер). Не треба крутити ключі для кожного інструменту:

```bash
hermes setup --portal
```

Це входить у систему, встановлює Nous як провайдера і вмикає Tool Gateway однією командою.
:::
## Prerequisites

**pip install:** Ніяких додаткових вимог, окрім Python 3.11+. Усе інше встановлюється автоматично.

**Git installer:** Єдина вимога — **Git**. Інсталятор самостійно впорається з усім іншим:

- **uv** (швидкий менеджер пакетів Python)
- **Python 3.11** (через uv, без sudo)
- **Node.js v22** (для автоматизації браузера та мосту WhatsApp)
- **ripgrep** (швидкий пошук файлів)
- **ffmpeg** (перетворення аудіоформатів для TTS)

:::info
Ти **не** потрібно встановлювати Python, Node.js, ripgrep або ffmpeg вручну. Інсталятор визначає, чого не вистачає, і встановлює це за тебе. Просто переконайся, що `git` доступний (`git --version`).
:::

:::tip Nix users
Якщо ти користуєшся Nix (на NixOS, macOS або Linux), існує спеціальний шлях налаштування з Nix‑flake, декларативним модулем NixOS та необов’язковим режимом контейнера. Дивись посібник **[Nix & NixOS Setup](./nix-setup.md)**.
:::

---
## Посібник / Встановлення для розробників

Якщо ти хочеш клонувати репозиторій і встановити з вихідного коду — для внесення, запуску з певної гілки або повного контролю над віртуальним середовищем — дивись розділ [Development Setup](../developer‑guide/contributing.md#development-setup) у посібнику зі внесенням змін.
## Встановлення без sudo / користувач сервісу системи

Запуск Hermes від імені спеціального непривілейованого користувача (наприклад, облікового запису сервісу `hermes` у systemd або будь‑якого користувача без доступу `sudo`) підтримується. Єдина частина шляху встановлення, яка дійсно потребує root, — це крок Playwright `--with-deps`, який `apt`‑встановлює спільні бібліотеки (`libnss3`, `libxkbcommon` тощо), що використовуються Chromium. Інсталятор визначає, чи доступний sudo, і при його відсутності коректно переходить у режим без sudo — він встановить бінарник Chromium у кеш Playwright користувача сервісу та виведе точну команду, яку адміністратор має виконати окремо.

**Рекомендований розподіл (Debian/Ubuntu):**

1. **Одноразово, як користувач‑адміністратор з sudo**, встановити системні бібліотеки, необхідні Chromium:
   ```bash
   sudo npx playwright install-deps chromium
   ```
   (Цю команду можна запускати з будь‑якої теки — `npx` завантажить Playwright «на льоту».)

2. **Від імені непривілейованого користувача сервісу**, запустити звичайний інсталятор. Він виявить відсутність sudo, пропустить `--with-deps` і встановить Chromium у локальний кеш Playwright користувача:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
   ```

   Якщо хочеш повністю пропустити крок Playwright — наприклад, тому що працюєш у headless‑режимі і не потребуєш автоматизації браузера — передай `--skip-browser`:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash -s -- --skip-browser
   ```

3. **Зробити `hermes` доступним у оболонках користувача сервісу.** Інсталятор записує запускник у `~/.local/bin/hermes`. У облікових записів системних сервісів часто мінімальний `PATH`, який не включає `~/.local/bin`. Додай його до середовища користувача або створити символічне посилання на запускник у системному каталозі:
   ```bash
   # Option A — add to the service user's profile
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

   # Option B — symlink system-wide (run as an admin)
   sudo ln -s /home/hermes/.hermes/hermes-agent/venv/bin/hermes /usr/local/bin/hermes
   ```

4. **Перевірка:** `hermes doctor` має тепер виконуватись без помилок. Якщо отримуєш `ModuleNotFoundError: No module named 'dotenv'`, ти викликаєш файл `hermes` з репозиторію (`~/.hermes/hermes-agent/hermes`) за допомогою системного Python замість запускника venv (`~/.hermes/hermes-agent/venv/bin/hermes`) — виправ крок 3.

Той самий підхід працює в Arch (інсталятор використовує pacman з тією ж логікою визначення sudo), Fedora/RHEL та openSUSE — у цих дистрибутивах `--with-deps` взагалі не підтримується, тому адміністратор завжди встановлює системні бібліотеки окремо. Відповідні команди `dnf`/`zypper` виводяться інсталятором.
## Усунення проблем

| Проблема | Рішення |
|---------|----------|
| `hermes: command not found` | Перезапусти свою оболонку (`source ~/.bashrc`) або перевір PATH |
| `API key not set` | Виконай `hermes model`, щоб налаштувати свого провайдера, або `hermes config set OPENROUTER_API_KEY your_key` |
| Відсутня конфігурація після оновлення | Виконай `hermes config check`, а потім `hermes config migrate` |

Для додаткової діагностики виконай `hermes doctor` — він точно скаже, чого не вистачає і як це виправити.
## Автоматичне визначення методу встановлення

Hermes автоматично визначає, чи було встановлено його за допомогою `pip`, git‑установника, Homebrew або NixOS, і `hermes update` виводить відповідну команду оновлення для цього шляху. Змінної середовища для налаштування немає — визначення базується на структурі встановлення (Python site-packages, `~/.hermes/hermes-agent/`, префікс Homebrew або шлях у сховищі Nix). `hermes doctor` також показує виявлений метод у підсумку середовища.