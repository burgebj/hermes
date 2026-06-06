---
title: "Руководство Windows (WSL2)"
description: "Запусти Hermes Agent на Windows через WSL2 — настройка, доступ к файловой системе между Windows и Linux, сеть и типичные подводные камни"
sidebar_label: "Windows (WSL2)"
sidebar_position: 2
---
# Руководство по Windows (WSL2)

Hermes Agent теперь поддерживает **оба** варианта: нативный Windows и WSL2. Эта страница описывает путь через WSL2; для нативной установки в PowerShell смотри отдельный **[Windows (Native) Guide](./windows-native.md)**.

**Когда выбирать WSL2 вместо нативного:**
- Ты хочешь использовать встроенный терминал дашборда (`/chat`‑вкладка) — эта панель требует POSIX PTY и работает только в WSL2.
- Ты занимаешься тяжёлой POSIX‑разработкой и хочешь, чтобы сессии Hermes использовали одну файловую систему/пути с твоими dev‑инструментами.
- У тебя уже есть окружение WSL2, и ты не хочешь поддерживать вторую установку.

**Когда нативный вариант подходит (или лучше):**
- Интерактивный чат, шлюз (Telegram/Discord/и т.п.), планировщик cron, браузер‑инструмент, серверы MCP и большинство функций Hermes работают нативно в Windows.
- Ты не хочешь думать о переходе границы WSL↔Windows каждый раз, когда обращаешься к файлу или открываешь URL.

В WSL2 фактически задействованы два компьютера: твой Windows‑хост и Linux‑VM, управляемая WSL. Большинство недоразумений возникает из‑за того, что ты не уверен, где находишься в данный момент.

Это руководство охватывает те части разделения, которые непосредственно влияют на Hermes: установка WSL2, обмен файлами между Windows и Linux, сетевые настройки в обоих направлениях и подводные камни, с которыми действительно сталкиваются пользователи.

:::info 简体中文
Китайская версия пошагового руководства по минимальному пути установки поддерживается на этой же странице — переключайся через меню **language** (вверху справа) и выбирай **简体中文**.
:::

## Почему WSL2 (а не нативный Windows)

Нативная установка Windows работает напрямую в Windows: твой Windows‑терминал (PowerShell, Windows Terminal и т.п.), пути файловой системы Windows (`C:\Users\…`) и процессы Windows. Hermes использует Git Bash для выполнения команд оболочки, что так делают Claude Code и другие агенты в Windows — это обходится без полного переписывания, минуя разрыв между POSIX и Windows.

WSL2 запускает реальное ядро Linux в лёгкой VM, поэтому Hermes внутри неё почти идентичен запуску на Ubuntu. Это ценно, когда нужен настоящий POSIX: `fork`, `/tmp`, UNIX‑сокеты, семантика сигналов, терминалы на базе PTY, оболочки `bash`/`zsh` и инструменты `rg`, `git`, `ffmpeg`, которые работают так же, как в Linux.

Практические последствия WSL2:

- CLI Hermes, шлюз, сессии, память, навыки и среды выполнения инструментов живут внутри Linux‑VM.
- Программы Windows (браузеры, нативные приложения, Chrome с твоим профилем) находятся снаружи.
- Каждый раз, когда нужно, чтобы они «поговорили» — обменяться файлами, открыть URL, управлять Chrome, обратиться к локальному серверу модели, открыть шлюз Hermes на телефоне — ты пересекаешь границу. Именно об этом и рассказывает данное руководство.

## Install WSL2

Из **Admin PowerShell** или Windows Terminal:

```powershell
wsl --install
```

На свежей Windows 10 22H2+ или Windows 11 это установит ядро WSL2, функцию Virtual Machine Platform и дистрибутив Ubuntu по умолчанию. Перезагрузися, когда будет предложено. После перезагрузки Ubuntu откроется и запросит имя пользователя Linux + пароль — это **новый пользователь Linux**, не связанный с твоей учётной записью Windows.

Проверь, что ты действительно в WSL2 (а не в устаревшем WSL1):

```powershell
wsl --list --verbose
```

Ты должен увидеть `VERSION  2`. Если дистрибутив показывает `VERSION  1`, конвертируй его:

```powershell
wsl --set-version Ubuntu 2
wsl --set-default-version 2
```

Hermes не работает надёжно в WSL1 — WSL1 переводит системные вызовы Linux «на лету», и некоторые поведения (procfs, сигналы, сеть) отличаются от реального Linux.

### Выбор дистрибутива

Мы тестируем на Ubuntu (LTS). Debian тоже работает. Arch и NixOS подходят тем, кто их хочет, но однострочный установщик предполагает Debian‑производную систему `apt` — смотри [Nix setup guide](/getting-started/nix-setup) для этого пути.

### Включить systemd (рекомендовано)

Шлюз Hermes (и всё, что ты хочешь держать запущенным) проще управлять через systemd. На современных WSL включи его один раз внутри дистрибутива:

```bash
sudo tee /etc/wsl.conf >/dev/null <<'EOF'
[boot]
systemd=true

[interop]
enabled=true
appendWindowsPath=true

[automount]
options = "metadata,umask=22,fmask=11"
EOF
```

Затем из PowerShell:

```powershell
wsl --shutdown
```

Перезапусти терминал WSL. Команда `ps -p 1 -o comm=` должна вывести `systemd`.

Опция монтирования `metadata`, указанная выше, важна — без неё файлы в `/mnt/c/...` не могут хранить реальные битовые права Linux, что ломает такие вещи, как `chmod +x` скриптов в путях Windows.

### Install Hermes inside WSL

Когда открылся shell WSL2:

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
source ~/.bashrc
hermes
```

Установщик рассматривает WSL2 как обычный Linux — ничего специфичного для WSL не требуется. См. [Installation](/getting-started/installation) для полной структуры.

## Filesystem: crossing the Windows ↔ WSL2 boundary

Это самая частая «препона». Есть **две файловые системы**, и место размещения файлов имеет значение — для производительности, корректности и доступности инструментов.

### Два направления

| Direction | Path inside | Path you use |
|---|---|---|
| Windows‑диск, видимый из WSL | `C:\Users\you\Documents` | `/mnt/c/Users/you/Documents` |
| WSL‑диск, видимый из Windows | `/home/you/code` | `\\wsl$\Ubuntu\home\you\code` (или `\\wsl.localhost\Ubuntu\...` в новых сборках) |

Оба реальны и работают, но **это не одна и та же файловая система** — они соединены протоколом 9P под капотом. Это имеет реальные последствия для скорости и семантики.

### Где размещать Hermes и проекты

**Краткое правило: держи всё «Linux‑ish» внутри Linux‑файловой системы.**

- Твоя установка Hermes (`~/.hermes/`) — Linux‑сторона. Установщик уже делает это.
- Твои git‑репозитории, с которыми работаешь из WSL — Linux‑сторона (`~/code/...`, `~/projects/...`).
- Модели, датасеты, виртуальные окружения — Linux‑сторона.

Что ты получаешь, следуя правилу:

- **Быстрый ввод‑вывод.** Операции в `/mnt/c/...` проходят через 9P и в 10–100 раз медленнее, чем нативный ext4. `git status` в репозитории из 10 к файлов, мгновенно работающий в `~/code`, может занять 15+ секунд в `/mnt/c`.
- **Корректные права.** Права Linux‑файлов на `/mnt/c` — лишь приближённая эмуляция. Часто встречаются ошибки `ssh` «bad permissions» или тихие провалы `chmod +x`.
- **Надёжные наблюдатели файлов.** inotify через 9P нестабилен — наблюдатели (dev‑серверы, тест‑раннеры) часто пропускают изменения в `/mnt/c`.
- **Отсутствие сюрпризов с регистром.** Путь Windows по умолчанию нечувствителен к регистру; Linux — чувствителен. Проекты с `Readme.md` и `README.md` ведут себя по‑разному в зависимости от стороны.

Размещай файлы в `/mnt/c` только тогда, когда **нужно**, чтобы файл жил на стороне Windows — например, ты хочешь открыть его в Windows‑GUI‑приложении, или MCP Chrome требует путь, доступный из Windows.

### Перемещение файлов туда‑обратно

**Из Windows → в WSL:** проще всего открыть Explorer и в адресной строке ввести `\\wsl.localhost\Ubuntu`. Затем перетащи файлы в `\home\<you>\...`. Или из PowerShell:

```powershell
wsl cp /mnt/c/Users/you/Downloads/file.pdf ~/incoming/
```

**Из WSL → в Windows:** скопируй в `/mnt/c/Users/<you>/...` — файл сразу появится в Проводнике Windows:

```bash
cp ~/reports/output.pdf /mnt/c/Users/you/Desktop/
```

**Открыть файл WSL в Windows‑приложении** (GUI‑редактор, браузер и т.п.): используй `explorer.exe` или `wslview`:

```bash
sudo apt install wslu     # once — gives you wslview, wslpath, wslopen, etc.
wslview ~/reports/output.pdf    # opens with the Windows default handler
explorer.exe .                  # opens the current WSL dir in Windows Explorer
```

**Конвертация путей между двумя мирами:**

```bash
wslpath -w ~/code/project        # → \\wsl.localhost\Ubuntu\home\you\code\project
wslpath -u 'C:\Users\you'        # → /mnt/c/Users/you
```

### Концы строк, BOM и git

Если редактировать файлы на стороне Windows в Windows‑редакторе, они могут получить окончания `CRLF`. Когда `bash` или Python в Linux читают их, скрипты ломаются с `bad interpreter: /bin/bash^M`, а Python может упасть на файлах `.env` с BOM.

Решение — sane‑настройка git внутри WSL (не в Windows):

```bash
git config --global core.autocrlf input
git config --global core.eol lf
```

Для уже имеющих `CRLF` файлов:

```bash
sudo apt install dos2unix
dos2unix path/to/script.sh
```

### «Клонировать внутри WSL или в `/mnt/c`?»

Клонируй внутри WSL. Всегда, если нет особой причины иначе. Типичный рабочий процесс Hermes (`hermes chat`, вызовы инструментов, `rg`/`ripgrep` репо, наблюдатели файлов, фоновой шлюз) будет значительно быстрее и надёжнее в `~/code/myrepo`, чем в `/mnt/c/Users/you/myrepo`.

Исключение: **MCP‑мосты, запускающие Windows‑бинарники.** Если ты используешь `chrome-devtools-mcp` через `cmd.exe` (см. [MCP guide: WSL → Windows Chrome](/guides/use-mcp-with-hermes#wsl2-bridge-hermes-in-wsl-to-windows-chrome)), Windows может выдать предупреждение `UNC`, если текущий каталог Hermes — `~`. В этом случае запускай Hermes из каталога под `/mnt/c/`, чтобы процесс Windows получил путь с буквой диска.

## Networking: WSL ↔ Windows

WSL2 работает в лёгкой VM со своим сетевым стеком. Поэтому `localhost` внутри WSL — **не то же самое**, что `localhost` в Windows; это два разных хоста. Нужно решить, в каком направлении идёт трафик для каждой службы, и выбрать правильный мост.

Часто встречаются два случая.

### Случай 1 — Hermes в WSL обращается к сервису в Windows

Самый распространённый: ты запустил **Ollama, LM Studio или llama‑server в Windows**, а Hermes (внутри WSL) должен к нему подключиться.

Канонический гайд находится в провайдер‑документации: **[WSL2 Networking for Local Models →](/integrations/providers#wsl2-networking-windows-users)**

Кратко:

- **Windows 11 22H2+:** включи режим зеркального сетевого взаимодействия (`networkingMode=mirrored` в `%USERPROFILE%\.wslconfig`, затем `wsl --shutdown`). После этого `localhost` работает в обеих направлениях.
- **Windows 10 или более старые сборки:** используй IP‑адрес хоста Windows (шлюз по умолчанию виртуальной сети WSL) и убедись, что сервер в Windows привязан к `0.0.0.0`, а не только к `127.0.0.1`. Обычно также требуется правило в брандмауэре Windows для нужного порта.

Для полной таблицы (адреса привязки Ollama / LM Studio / vLLM / SGLang, однострочники правил firewall, динамические помощники IP, обходы Hyper‑V firewall) переходи по ссылке выше — не дублируй её.

### Случай 2 — Что‑то в Windows (или в твоей LAN) обращается к Hermes в WSL

Это обратное направление, реже документировано, но необходимо для:

- Доступа к **веб‑дашборду Hermes** из браузера Windows.
- Доступа к **API‑серверу (OpenAI‑совместимому)**, который включается `hermes gateway` при `API_SERVER_ENABLED=true`, из инструмента на стороне Windows. См. страницу [API Server feature](/user-guide/features/api-server).
- Тестирования **шлюза обмена сообщениями** (Telegram, Discord и т.п.), где платформа посылает запросы на локальный webhook — обычно используют `cloudflared`/`ngrok`, а не чистый проброс портов.

#### Подслучай 2a: из самого хоста Windows

На **Windows 11 22H2+ с включённым зеркальным режимом** ничего делать не нужно. Процесс в WSL, привязанный к `0.0.0.0:8080` (или даже `127.0.0.1:8080`), будет доступен из браузера Windows по `http://localhost:8080`. WSL автоматически публикует привязку обратно в хост.

В **режиме NAT** (Windows 10 / более старый Windows 11) стандартный «localhost forwarding» в WSL2 обычно перенаправляет привязки `127.0.0.1` из Linux в `localhost` Windows, так что сервис Hermes, запущенный с `--host 127.0.0.1`, обычно доступен как `http://localhost:PORT` из Windows. Если нет:

- Явно привязывайся к `0.0.0.0` внутри WSL.
- Найди IP‑адрес VM WSL командой `ip -4 addr show eth0 | grep inet` и обращайся к нему из Windows.

#### Подслучай 2b: с другого устройства в LAN (телефон, планшет, ПК)

Это настоящая головная боль. Трафик идёт **LAN‑устройство → Windows‑хост → WSL‑VM**, и нужно настроить оба перехода:

1. **Привязывайся ко всем интерфейсам внутри WSL.** Процесс, слушающий только `127.0.0.1`, будет недоступен извне VM. Используй `0.0.0.0`.
2. **Проброс портов Windows → WSL VM.** В зеркальном режиме это автоматом. В режиме NAT нужно сделать вручную, порт за портом, в Admin PowerShell:

         ```powershell
   # Grab the WSL VM's current IP (it changes on every WSL restart under NAT)
   $wslIp = (wsl hostname -I).Trim().Split(' ')[0]

   # Forward Windows port 8080 → WSL:8080
   netsh interface portproxy add v4tov4 `
     listenaddress=0.0.0.0 listenport=8080 `
     connectaddress=$wslIp connectport=8080

   # Allow it through Windows Firewall
   New-NetFirewallRule -DisplayName "Hermes WSL 8080" `
     -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow
   ```

   Удалить позже можно командой `netsh interface portproxy delete v4tov4 listenaddress=0.0.0.0 listenport=8080`.
3. **Указать устройству LAN адрес `http://<windows-lan-ip>:8080`.**

Поскольку IP‑адрес VM WSL меняется при каждой перезагрузке в режиме NAT, правило «один‑раз» живёт лишь до следующего `wsl --shutdown`. Для постоянного решения либо используй зеркальный режим, либо добавляй шаг проброса портов в скрипт, запускаемый при входе в Windows.

Для веб‑хуков от облачных провайдеров сообщений (Telegram `setWebhook`, Slack‑events и т.п.) не борись с пробросом портов — используй туннели `cloudflared`. См. [webhooks guide](/user-guide/messaging/webhooks).

## Запуск долгоживущих сервисов Hermes в Windows

[Tool Gateway](/user-guide/features/tool-gateway) и API‑сервер — процессы, которые должны работать постоянно. В WSL2 есть несколько вариантов их удержания.

### Ярлык рабочего стола для быстрого запуска Hermes

Если нужен двойной клик для интерактивного шелла Hermes, создай ярлык в Windows, который переключит тебя в WSL:

1. Правой кнопкой по рабочему столу → **New → Shortcut**.
2. В качестве цели укажи имя дистрибутива (замени `Ubuntu`, если нужно):

         ```text
   wt.exe -w 0 -p "Ubuntu" wsl.exe -d Ubuntu --cd ~ -- bash -ic "hermes"
   ```

3. Дай понятное имя, например `Hermes`.

Это откроет Windows Terminal, запустит выбранный дистрибутив WSL, переместит тебя в домашний каталог Linux и запустит Hermes. Если `hermes` ещё не в PATH, открой WSL вручную и выполните `source ~/.bashrc`, либо замени команду на `uv run hermes` внутри каталога проекта.

Дополнительные штрихи:

- **Свой значок:** свойства → **Change Icon** → укажи `.ico`, например фавикон Hermes из репозитория.
- **Закрепление:** после проверки ярлыка закрепи его в меню Пуск или на панели задач, чтобы не искать каждый раз.

### Внутри WSL с systemd (рекомендовано)

Если ты включил systemd, `hermes gateway` и API‑сервер работают как на любой Linux‑машине. Запусти мастер настройки шлюза:

```bash
hermes gateway setup
```

Он предложит установить пользовательскую unit systemd, чтобы шлюз поднимался автоматически при старте WSL.

### Автозапуск WSL при входе в Windows

VM WSL живёт только пока что‑то её использует. Чтобы шлюз был доступен без открытого терминала, запусти процесс WSL при входе в Windows через Планировщик задач:

- **Триггер:** При входе (твой пользователь).
- **Действие:** Запуск программы
  - Программа: `C:\Windows\System32\wsl.exe`
  - Аргументы: `-d Ubuntu --exec /bin/sh -c "sleep infinity"`

Это удержит VM в живом состоянии, чтобы systemd‑управляемый шлюз продолжал работать. На Windows 11 также работает более новый поток `wsl --install --no-launch` + авто‑старт; трюк `sleep infinity` — самый переносимый.

## GPU passthrough (локальные модели)

WSL2 поддерживает **NVIDIA** GPU нативно, начиная с ядра WSL 5.10.43+ — установи обычный драйвер NVIDIA в Windows (не устанавливай Linux‑драйвер внутри WSL), и `nvidia-smi` в WSL увидит GPU. Далее CUDA‑toolkit, `torch`, `vllm`, `sglang` и `llama-server` работают с реальным GPU как обычно.

Поддержка AMD ROCm и Intel Arc в WSL2 ещё развивается и не входит в матрицу тестов Hermes — может работать с текущими драйверами, но у нас нет проверенного рецепта.

Если ты запускаешь **нативный** сервер локальных моделей в Windows (Ollama, LM Studio), который уже использует GPU через драйверы Windows, тебе вовсе не нужен GPU‑passthrough в WSL — просто используй случай 1 выше и подключайся к нему по сети из WSL.

## Частые подводные камни

**«Connection refused» к Ollama / LM Studio в Windows.** См. [WSL2 Networking](/integrations/providers#wsl2-networking-windows-users). В 90 % случаев сервер привязан к `127.0.0.1` и нужен `0.0.0.0` (Ollama: `OLLAMA_HOST=0.0.0.0`), либо отсутствует правило firewall.

**Сильная задержка `git status` / `hermes chat` в репозитории.** Скорее всего ты работаешь в `/mnt/c/...`. Перемести репо в `~/code/...` (Linux‑сторона). Будет в разы быстрее.

**`bad interpreter: /bin/bash^M` в скриптах.** Концы строк `CRLF` из Windows‑редактора. Выполни `dos2unix script.sh` и в конфиге git установи `core.autocrlf input`.

**Предупреждение «UNC paths are not supported» от Windows‑бинарников, запущенных через MCP.** Текущий каталог Hermes находится в Linux‑файловой системе, а `cmd.exe` не понимает такой путь. Запусти Hermes из `/mnt/c/...` для этой сессии или используй обёртку, которая `cd`‑нётся в путь, доступный Windows, перед вызовом Windows‑исполняемого файла.

**Сдвиг часов после сна/гибернации.** Часы WSL2 могут отставать на несколько минут после возобновления хоста, что ломает сертификат‑зависимые операции (OAuth, HTTPS API). Исправь по требованию:

```bash
sudo hwclock -s
```

Или установи `ntpdate` и запускай его при входе.

**DNS перестаёт работать после включения зеркального режима или при подключённом VPN.** Зеркальный режим проксирует сетевые настройки хоста в WSL — если DNS Windows «плохой» (split‑tunnel VPN, корпоративный резольвер), WSL унаследует проблему. Обход: вручную переопредели `resolv.conf` (установи `generateResolvConf=false` в `/etc/wsl.conf`, затем создай свой `/etc/resolv.conf` с `nameserver 1.1.1.1` или DNS VPN).

**`hermes` не найден после установки.** Установщик добавил `~/.local/bin` в PATH через `~/.bashrc`. Нужно выполнить `source ~/.bashrc` (или открыть новый терминал), чтобы изменения вступили в силу.

**Windows Defender медленно сканирует файлы WSL.** Defender сканирует файлы через 9P‑мост, когда они открыты из Windows, что усиливает медлительность доступа к `/mnt/c`. Если ты работаешь только внутри WSL, это не проблема. Если часто используешь Windows‑инструменты с `\\wsl$\...`, подумай об исключении пути дистрибутива из реального сканирования.

**Не хватает места на диске.** Диск VM WSL2 хранится как разрежённый VHDX в `%LOCALAPPDATA%\Packages\...`. Он растёт, но не сжимается автоматически при удалении файлов. Чтобы освободить место: `wsl --shutdown`, затем в Admin PowerShell выполните `Optimize-VHD -Path <path-to-ext4.vhdx> -Mode Full` (нужны инструменты Hyper‑V) — либо используйте более простой путь через `diskpart`, описанный в официальной документации WSL.

## Что дальше

- **[Installation](/getting-started/installation)** — полные шаги установки (Linux/WSL2/Termux используют один и тот же установщик).
- **[Integrations → Providers → WSL2 Networking](/integrations/providers#wsl2-networking-windows-users)** — канонический глубокий разбор сетевых настроек для локальных моделей.
- **[MCP guide → WSL → Windows Chrome](/guides/use-mcp-with-hermes#wsl2-bridge-hermes-in-wsl-to-windows-chrome)** — управление подписанным Chrome в Windows из Hermes в WSL.
- **[Tool Gateway](/user-guide/features/tool-gateway)** и **[Web Dashboard](/user-guide/features/web-dashboard)** — долгоживущие сервисы, которые чаще всего хочется открыть из WSL в остальную сеть.