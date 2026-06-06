---
sidebar_position: 2
title: "Установка"
description: "Установи Hermes Agent на Linux, macOS, WSL2, нативный Windows (ранняя бета) или Android через Termux"
---

# Установка

Запусти Hermes Agent и получи работающий сервис менее чем за две минуты с помощью однострочного установщика.
## Быстрая установка

### Однострочный установщик (Linux / macOS / WSL2)

Для установки из git, отслеживающей `main` и сразу получающей последние изменения:

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

### Windows (нативный, PowerShell) — ранняя бета‑версия

:::warning Early BETA
Нативная поддержка Windows находится в **ранней бете**. Она устанавливается и работает для типовых путей, но не проходила столь же масштабного дорожного тестирования, как наши POSIX‑установщики. Пожалуйста, [сообщай об ошибках](https://github.com/NousResearch/hermes-agent/issues), когда сталкиваешься с проблемами. Для наиболее проверенной конфигурации Windows сегодня используй однострочный установщик для Linux/macOS внутри **WSL2**.
:::

Открой PowerShell и выполни:

```powershell
iex (irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1)
```

Установщик берёт на себя **всё**: `uv`, Python 3.11, Node.js 22, `ripgrep`, `ffmpeg`, **и портативный Git Bash** (PortableGit — автономный дистрибутив Git‑for‑Windows, включающий `bash.exe` и полный POSIX‑инструментарий, который Hermes использует для команд оболочки; на 32‑битных Windows установщик переходит к MinGit, у которого нет bash и отключены функции terminal‑tool / agent‑browser). Он клонирует репозиторий в `%LOCALAPPDATA%\hermes\hermes-agent`, создаёт virtualenv и добавляет `hermes` в твой **User PATH**. Перезапусти терминал (или открой новое окно PowerShell) после установки, чтобы PATH обновился.

**Как обрабатывается Git:**
1. Если `git` уже есть в PATH, установщик использует существующую установку.
2. Иначе он скачивает портативный **PortableGit** (~50 МБ, из официального релиза `git-for-windows` на GitHub) и распаковывает его в `%LOCALAPPDATA%\hermes\git`. Административные права не требуются. Полностью изолировано — не будет конфликтов с системным Git, даже если он сломан. (На 32‑битных Windows происходит откат к MinGit, потому что PortableGit поставляется только с 64‑битными и ARM64‑бинарниками; функции Hermes, зависящие от bash, не работают на 32‑битных хостах.)

**Почему не использовать winget?** Ранние варианты автоматически устанавливали Git через `winget install Git.Git`, но winget сильно ломается, когда системный Git находится в частичном или сломанном состоянии (именно тогда пользователям нужен простой установщик). Портативный Git обходится без winget, реестра установщика Windows и любых существующих системных Git‑установок. Если установка Git от Hermes когда‑нибудь сломается, выполни `Remove-Item %LOCALAPPDATA%\hermes\git` и запусти установщик снова — никаких последствий для системы, никаких проблем с удалением.

Установщик также задаёт `HERMES_GIT_BASH_PATH` к найденному `bash.exe`, чтобы Hermes deterministically находил его в новых оболочках.

Если ты предпочитаешь WSL2, Linux‑установщик выше работает внутри него; нативные и WSL‑установки могут сосуществовать без конфликтов (нативные данные находятся в `%LOCALAPPDATA%\hermes`, данные WSL — в `~/.hermes`).

**Десктопный установщик (альтернатива):** Тонкий GUI‑установщик также доступен — скачай Hermes Desktop, запусти `.exe`, и при первом запуске он вызывает `install.ps1` под капотом, чтобы установить Python (через `uv`), Node, PortableGit и остальные зависимости. Десктопное приложение и CLI, установленный через PowerShell, используют одни и те же каталоги установки и данных, так что можешь пользоваться любым из них. См. [руководство Windows (Native)](../user-guide/windows-native#desktop-installer-alternative) для деталей.

### Android / Termux

Hermes теперь поставляется с поддержкой установочного пути, ориентированного на Termux:

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

Установщик автоматически обнаруживает Termux и переключается на проверенный Android‑поток:
- использует `pkg` Termux для системных зависимостей (`git`, `python`, `nodejs`, `ripgrep`, `ffmpeg`, build‑tools);
- создаёт virtualenv через `python -m venv`;
- автоматически экспортирует `ANDROID_API_LEVEL` для сборки Android‑wheel;
- предпочитает расширение `.[termux-all]` и откатывается к более небольшому `.[termux]` (и в конце к базовой установке), если первая попытка не удаётся собрать;
- по умолчанию пропускает непроверенный bootstrap браузера / WhatsApp.

Если нужен полностью явный путь, следуй посвящённому [руководству по Termux](./termux.md).

:::note Windows Feature Parity (Early Beta)

Нативный Windows находится в **ранней бете**. Всё, кроме браузерного терминала дашборда, работает нативно на Windows:
- **CLI (`hermes chat`, `hermes setup`, `hermes gateway`, …)** — нативно, использует твой терминал по умолчанию;
- **Gateway (Telegram, Discord, Slack, …)** — нативно, работает как фоновый процесс PowerShell;
- **Cron‑планировщик** — нативно;
- **Browser tool** — нативно (Chromium через Node.js);
- **MCP‑серверы** — нативно (поддерживаются как stdio, так и HTTP‑транспорты);
- **Dashboard `/chat` terminal pane** — **только WSL2** (использует POSIX PTY; в нативном Windows эквивалента нет). Остальная часть дашборда (сессии, задачи, метрики) работает нативно — только встроенная вкладка PTY‑терминала ограничена.

Установи `HERMES_DISABLE_WINDOWS_UTF8=1` в окружении, если столкнёшься с ошибкой кодировки и хочешь откатиться к старому пути cp1252 stdio (полезно для бисекции).
:::

### Что делает установщик

Установщик автоматически берёт на себя всё — все зависимости (Python, Node.js, ripgrep, ffmpeg), клонирование репозитория, виртуальное окружение, глобальную настройку команды `hermes` и конфигурацию провайдера LLM. К концу ты будешь готов к общению.

#### Структура установки

Куда установщик кладёт файлы, зависит от того, устанавливаешь ли ты как обычный пользователь или как root:

| Установщик | Код находится в | Бинарник `hermes` | Каталог данных |
|---|---|---|---|
| pip install | Python site-packages | `~/.local/bin/hermes` (console_scripts) | `~/.hermes/` |
| Per-user (git installer) | `~/.hermes/hermes-agent/` | `~/.local/bin/hermes` (symlink) | `~/.hermes/` |
| Root‑mode (`sudo curl … \| sudo bash`) | `/usr/local/lib/hermes-agent/` | `/usr/local/bin/hermes` | `/root/.hermes/` (или `$HERMES_HOME`) |

Разметка **FHS** в режиме root (`/usr/local/lib/…`, `/usr/local/bin/hermes`) соответствует тому, куда обычно попадают системные инструменты разработчика на Linux. Это удобно для развертываний на совместно используемых машинах, где одна системная установка обслуживает всех пользователей. Персональная конфигурация (auth, skills, sessions) всё равно хранится в `~/.hermes/` каждого пользователя или в явно заданном `HERMES_HOME`.

### После установки

Перезагрузи оболочку и начни общение:

```bash
source ~/.bashrc   # or: source ~/.zshrc
hermes             # Start chatting!
```

Чтобы позже переустановить отдельные параметры, используй специальные команды:

```bash
hermes model          # Choose your LLM provider and model
hermes tools          # Configure which tools are enabled
hermes gateway setup  # Set up messaging platforms
hermes config set     # Set individual config values
hermes setup          # Or run the full setup wizard to configure everything at once
```

:::tip Fastest path: Nous Portal
Одна подписка покрывает 300+ моделей плюс [Tool Gateway](/user-guide/features/tool-gateway) (веб‑поиск, генерация изображений, TTS, облачный браузер). Не трать время на отдельные ключи для каждого инструмента:

```bash
hermes setup --portal
```

Это выполнит вход, установит Nous в качестве провайдера и включит Tool Gateway одной командой.
:::
## Предварительные требования

**pip install:** Нет требований, кроме Python 3.11+. Всё остальное устанавливается автоматически.

**Git‑installer:** Единственное требование — **Git**. Установщик автоматически обрабатывает всё остальное:

- **uv** (быстрый менеджер пакетов Python)
- **Python 3.11** (через uv, без sudo)
- **Node.js v22** (для автоматизации браузера и моста WhatsApp)
- **ripgrep** (быстрый поиск файлов)
- **ffmpeg** (конвертация аудио‑форматов для TTS)

:::info
Тебе **не** нужно вручную устанавливать Python, Node.js, ripgrep или ffmpeg. Установщик определит, чего не хватает, и установит это за тебя. Просто убедись, что `git` доступен (`git --version`).
:::

:::tip Nix‑пользователи
Если ты используешь Nix (на NixOS, macOS или Linux), существует отдельный путь настройки с Nix‑flake, декларативным модулем NixOS и опциональным режимом контейнера. Смотри руководство **[Nix & NixOS Setup](./nix-setup.md)**.
:::

---
## Руководство / Установка для разработчиков

Если ты хочешь клонировать репозиторий и установить из исходного кода — для участия в разработке, запуска из конкретной ветки или полного контроля над виртуальной средой — смотри раздел [Настройка разработки](../developer-guide/contributing.md#development-setup) в руководстве по внесению вклада.

---
## Установки без sudo / Пользователь системных служб

Запуск Hermes от имени выделенного непривилегированного пользователя (например, учётной записи службы `systemd` `hermes` или любого пользователя без доступа `sudo`) поддерживается. Единственное, что действительно требует root в пути установки, — шаг Playwright `--with-deps`, который через `apt` устанавливает общие библиотеки (`libnss3`, `libxkbcommon` и т.д.), используемые Chromium. Установщик определяет, доступен ли sudo, и при его отсутствии корректно переходит в упрощённый режим — он установит бинарный файл Chromium в собственный кэш Playwright пользователя‑службы и выведет точную команду, которую администратор должен выполнить отдельно.

**Рекомендуемое разделение (Debian/Ubuntu):**

1. **Однократно, от имени администратора с sudo**, установить системные библиотеки, необходимые Chromium:
   ```bash
   sudo npx playwright install-deps chromium
   ```
   (Запустить это можно из любого места — `npx` загрузит Playwright «на лету».)

2. **От имени непривилегированного пользователя службы**, запустить обычный установщик. Он обнаружит отсутствие sudo, пропустит `--with-deps` и установит Chromium в локальный кэш Playwright пользователя:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
   ```

   Если хочется полностью пропустить шаг Playwright — например, потому что ты работаешь в headless‑режиме и не нуждаешься в автоматизации браузера — передай `--skip-browser`:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash -s -- --skip-browser
   ```

3. **Сделать `hermes` доступным в оболочках пользователя службы.** Установщик записывает запускатор в `~/.local/bin/hermes`. У учётных записей системных служб часто минимальный `PATH`, который не включает `~/.local/bin`. Добавь его в окружение пользователя или создай символическую ссылку на запускатор в системном месте:
   ```bash
   # Option A — add to the service user's profile
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

   # Option B — symlink system-wide (run as an admin)
   sudo ln -s /home/hermes/.hermes/hermes-agent/venv/bin/hermes /usr/local/bin/hermes
   ```

4. **Проверь:** `hermes doctor` теперь должен выполниться без ошибок. Если появляется `ModuleNotFoundError: No module named 'dotenv'`, ты вызываешь файл исходного репозитория `hermes` (`~/.hermes/hermes-agent/hermes`) с системным Python вместо запускатора из виртуального окружения (`~/.hermes/hermes-agent/venv/bin/hermes`) — исправь шаг 3.

Тот же шаблон работает в Arch (установщик использует `pacman` с той же логикой определения sudo), Fedora/RHEL и openSUSE — в этих дистрибутивах `--with-deps` вообще не поддерживается, поэтому администратор всегда устанавливает системные библиотеки отдельно. Соответствующие команды `dnf`/`zypper` выводятся установщиком.
## Устранение неполадок

| Проблема | Решение |
|----------|---------|
| `hermes: command not found` | Перезапусти оболочку (`source ~/.bashrc`) или проверь PATH |
| `API key not set` | Выполни `hermes model` для настройки провайдера, либо `hermes config set OPENROUTER_API_KEY your_key` |
| Missing config after update | Выполни `hermes config check`, затем `hermes config migrate` |

Для более подробной диагностики запусти `hermes doctor` — он точно покажет, чего не хватает, и как это исправить.
## Автоматическое определение метода установки

Hermes автоматически определяет, была ли она установлена через `pip`, git‑инсталлятор, Homebrew или NixOS, и `hermes update` выводит соответствующую команду обновления для этого пути. Переменной окружения для задания метода нет — определение происходит на основе структуры установки (Python site‑packages, `~/.hermes/hermes-agent/`, префикс Homebrew или путь в Nix store). `hermes doctor` также отображает обнаруженный метод в сводке среды.