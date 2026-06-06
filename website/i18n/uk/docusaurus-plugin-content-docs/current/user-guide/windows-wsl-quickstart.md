---
title: "Посібник Windows (WSL2)"
description: "Запусти Hermes Agent у Windows через WSL2 — налаштування, доступ до файлової системи між Windows і Linux, мережа та типові підводні камені"
sidebar_label: "Windows (WSL2)"
sidebar_position: 2
---

# Посібник по Windows (WSL2)

Hermes Agent тепер підтримує **обидва** — native Windows і WSL2.  Ця сторінка охоплює шлях WSL2; для встановлення в native PowerShell дивись окремий **[Windows (Native) Guide](./windows-native.md)**.

**Коли обирати WSL2 замість native:**
- Ти хочеш використовувати вбудований термінал дашборду (`/chat` tab) — ця панель потребує POSIX PTY і працює лише в WSL2.
- Ти займаєшся розробкою, орієнтованою на POSIX, і хочеш, щоб твої Hermes сесії ділили одну файлову систему / шляхи з інструментами розробки.
- У тебе вже є середовище WSL2 і ти не хочеш підтримувати друге встановлення.

**Коли native підходить (або краще):**
- Інтерактивний чат, шлюз (Telegram/Discord/тощо), планувальник cron, інструмент браузера, MCP‑сервери та більшість функцій Hermes працюють нативно в Windows.
- Ти не хочеш думати про перетин межі WSL↔Windows щоразу, коли посилаєшся на файл або відкриваєш URL.

У WSL2 фактично працюють два комп’ютери: твій Windows‑хост і Linux‑VM, якою керує WSL.  Більшість плутанини виникає через те, що не зрозуміло, на якій системі ти знаходишся в даний момент.

Цей посібник охоплює частини цього розподілу, які безпосередньо впливають на Hermes: встановлення WSL2, передавання файлів між Windows і Linux, мережу в обох напрямках та підводні камені, з якими стикаються користувачі.

:::info 简体中文
A Chinese-language walkthrough of the minimum install path is maintained on this same page — switch via the **language** menu (top right) and select **简体中文**.
:::
## Чому WSL2 (на відміну від нативного Windows)

Нативна інсталяція Windows працює безпосередньо в Windows: твій Windows‑термінал (PowerShell, Windows Terminal тощо), шляхи файлової системи Windows (`C:\Users\…`) і процеси Windows. Hermes використовує Git Bash для виконання команд оболонки, саме так Claude Code та інші агенти працюють у Windows — це обхід розриву між POSIX і Windows без повного перепису.

WSL2 запускає справжнє ядро Linux у легкій віртуальній машині, тому Hermes всередині неї практично ідентичний запуску на Ubuntu. Це цінно, коли потрібне реальне POSIX‑середовище: `fork`, `/tmp`, UNIX‑сокети, семантика сигналів, PTY‑базовані термінали, оболонки типу `bash`/`zsh` і інструменти типу `rg`, `git`, `ffmpeg`, які працюють так само, як у Linux.

Практичні наслідки WSL2:

- CLI Hermes, **gateway**, сесії, пам'ять, навички та середовища інструментів живуть всередині Linux‑VM.
- Програми Windows (браузери, нативні додатки, Chrome з твоїм увійшовшим профілем) живуть поза нею.
- Кожного разу, коли ти хочеш, щоб вони взаємодіяли — обмінювалися файлами, відкривали URL, керували Chrome, зверталися до локального сервера моделі, відкривали **gateway** Hermes на телефоні — ти перетинаєш межу. Саме про ці межі й йдеться в цьому посібнику.
## Встановити WSL2

З **Admin PowerShell** або Windows Terminal:

```powershell
wsl --install
```

На новій системі Windows 10 22H2+ або Windows 11 це встановить ядро WSL2, функцію Virtual Machine Platform та дистрибутив Ubuntu за замовчуванням. Перезавантажся, коли буде запропоновано. Після перезавантаження Ubuntu відкриється і попросить ввести ім’я користувача Linux + пароль — це **новий користувач Linux**, не пов’язаний з твоїм обліковим записом Windows.

Перевір, що ти дійсно на WSL2 (а не на застарілому WSL1):

```powershell
wsl --list --verbose
```

Ти маєш бачити `VERSION  2`. Якщо дистрибутив показує `VERSION  1`, перетвори його:

```powershell
wsl --set-version Ubuntu 2
wsl --set-default-version 2
```

Hermes не працює надійно на WSL1 — WSL1 перекладає системні виклики Linux «на льоту», і деяка поведінка (procfs, сигнали, мережа) відрізняється від реального Linux.

### Вибір дистрибутива

Ubuntu (LTS) — це те, проти чого ми тестуємо. Debian працює. Arch і NixOS працюють для тих, хто їх хоче, але однорядковий інсталятор передбачає систему `apt`, похідну від Debian — дивись [посібник з налаштування Nix](/getting-started/nix-setup) для цього шляху.

### Увімкнути systemd (рекомендовано)

Шлюз hermes (і будь‑що інше, що ти хочеш, щоб працювало постійно) легше керувати за допомогою systemd. На сучасному WSL увімкни його один раз у своєму дистрибутиві:

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

Потім у PowerShell:

```powershell
wsl --shutdown
```

Відкрий знову термінал WSL. `ps -p 1 -o comm=` має вивести `systemd`.

Опція монтування `metadata`, зазначена вище, важлива — без неї файли в `/mnt/c/...` не можуть зберігати реальні бітові дозволи Linux, що руйнує такі речі, як `chmod +x` для скриптів у шляхах Windows.

### Встановити Hermes всередині WSL

Коли відкрито оболонку WSL2:

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
source ~/.bashrc
hermes
```

Інсталятор розглядає WSL2 як звичайний Linux — нічого специфічного для WSL не потрібно. Дивись [Installation](/getting-started/installation) для повного опису структури.
## Файлова система: перетин кордону Windows ↔ WSL2

Це частина, яка збиває з пантелику найбільше людей. Є **дві файлові системи**, і те, куди ти кладеш свої файлі, має значення — для продуктивності, коректності та того, які інструменти їх бачать.

### Два напрямки

| Напрямок | Шлях всередині | Шлях, який ти використовуєш |
|---|---|---|
| Диск Windows, видимий з WSL | `C:\Users\you\Documents` | `/mnt/c/Users/you/Documents` |
| Диск WSL, видимий з Windows | `/home/you/code` | `\\wsl$\Ubuntu\home\you\code` (або `\\wsl.localhost\Ubuntu\...` у новіших збірках) |

Обидва реальні, обидва працюють, але це **не одна і та ж файлова система** — вони з’єднані протоколом мережі 9P під капотом. Це має реальні наслідки для продуктивності та семантики.

### Куди класти Hermes і свої проєкти

**Загальне правило: тримай усе Linux‑подібне всередині файлової системи Linux.**

- Твоя установка Hermes (`~/.hermes/`) — Linux‑сторона. Інсталятор вже робить це.
- Твої git‑репозиторії, над якими працюєш з WSL — Linux‑сторона (`~/code/...`, `~/projects/...`).
- Твої моделі, набори даних, venv‑и — Linux‑сторона.

Що ти отримуєш, дотримуючись цього правила:

- **Швидке I/O.** Операції в `/mnt/c/...` проходять через 9P і в 10–100 раз повільніші, ніж нативний ext4. `git status` у репозиторії з 10 тис. файлів, який здається миттєвим у `~/code`, може зайняти 15+ секунд у `/mnt/c`.
- **Коректні дозволи.** Права Linux‑а на `/mnt/c` — лише емуляція. Такі випадки, як `ssh`, що відмовляє у ключі через «погані дозволи», або `chmod +x`, що тихо не працює, трапляються часто.
- **Надійні спостерігачі файлів.** `inotify` через 9P нестабільний — спостерігачі файлів (dev‑сервери, тест‑раннери) регулярно пропускають зміни в `/mnt/c`.
- **Немає сюрпризів з чутливістю до регістру.** Шляхи Windows за замовчуванням нечутливі до регістру; Linux — чутливий. Проєкти з одночасними `Readme.md` і `README.md` поводяться по‑різному залежно від того, з якої сторони ти працюєш.

Розміщуй файли в `/mnt/c` лише тоді, коли **потрібно**, щоб файл жив на стороні Windows — напр., ти хочеш відкрити його в Windows‑GUI‑додатку, або MCP Chrome DevTools потребує поточного каталогу, доступного з Windows.

### Перенесення файлів туди й назад

**З Windows → у WSL:** найпростіше відкрити Explorer і ввести `\\wsl.localhost\Ubuntu` у рядок адреси. Потім можна перетягнути файли у `\home\<you>\...`. Або з PowerShell:

```powershell
wsl cp /mnt/c/Users/you/Downloads/file.pdf ~/incoming/
```

**З WSL → у Windows:** скопіюй у `/mnt/c/Users/<you>/...`, і файл одразу з’явиться в Windows Explorer:

```bash
cp ~/reports/output.pdf /mnt/c/Users/you/Desktop/
```

**Відкрити файл WSL у Windows‑додатку** (GUI‑редактор, браузер тощо): використай `explorer.exe` або `wslview`:

```bash
sudo apt install wslu     # once — gives you wslview, wslpath, wslopen, etc.
wslview ~/reports/output.pdf    # opens with the Windows default handler
explorer.exe .                  # opens the current WSL dir in Windows Explorer
```

**Конвертувати шляхи між двома всесвітами:**

```bash
wslpath -w ~/code/project        # → \\wsl.localhost\Ubuntu\home\you\code\project
wslpath -u 'C:\Users\you'        # → /mnt/c/Users/you
```

### Кінцеві символи рядків, BOM та git

Якщо ти редагуєш файли на стороні Windows у Windows‑редакторі, вони можуть отримати кінцеві символи `CRLF`. Коли `bash` або Python на стороні Linux читають їх, скрипти Bash ламаються з помилкою `bad interpreter: /bin/bash^M`, а Python може збоїти на `.env`‑файлах з BOM.

Виправлення — правильна конфігурація git у WSL (не у Windows):

```bash
git config --global core.autocrlf input
git config --global core.eol lf
```

Для файлів, які вже мають `CRLF`:

```bash
sudo apt install dos2unix
dos2unix path/to/script.sh
```

### «Клонити всередині WSL чи на `/mnt/c`?»

Клонуй всередині WSL. Завжди, якщо немає конкретної причини не робити цього. Типовий робочий процес Hermes (`hermes chat`, виклики інструментів, що `rg`/`ripgrep` репозиторій, спостерігачі файлів, фоновий шлюз) буде значно швидшим і надійнішим у `~/code/myrepo`, ніж у `/mnt/c/Users/you/myrepo`.

Одне виключення: **MCP‑мости, що запускають Windows‑бінарники.** Якщо ти використовуєш `chrome-devtools-mcp` через `cmd.exe` (див. [MCP guide: WSL → Windows Chrome](/guides/use-mcp-with-hermes#wsl2-bridge-hermes-in-wsl-to-windows-chrome)), Windows може попереджати про `UNC`, якщо поточний робочий каталог Hermes — `~`. У цьому випадку запусти Hermes з якоїсь теки під `/mnt/c/`, щоб процес Windows мав cwd з буквою диска.
## Мережа: WSL ↔ Windows

WSL2 працює в легкій віртуальній машині зі своїм стеком мережі. Це означає, що `localhost` всередині WSL **не є тим самим**, що `localhost` у Windows — це два окремих хости з точки зору мережі. Тобі потрібно вирішити, для кожної служби, в якому напрямку йде трафік, і вибрати правильний міст.

Два випадки постійно виникають.

### Випадок 1 — Hermes у WSL спілкується зі службою у Windows

Найпоширеніший: ти запускаєш **Ollama, LM Studio або llama‑server у Windows**, і Hermes (всередині WSL) має до нього підключитися.

Канонічна інструкція з цього питання знаходиться у посібнику провайдерів: **[WSL2 Networking for Local Models →](/integrations/providers#wsl2-networking-windows-users)**

Коротка версія:

- **Windows 11 22H2+:** увімкни режим дзеркальної мережі (`networkingMode=mirrored` у `%USERPROFILE%\.wslconfig`, потім `wsl --shutdown`). Після цього `localhost` працює в обох напрямках.
- **Windows 10 або старіші збірки:** використай IP‑хосту Windows (дефолтний шлюз віртуальної мережі WSL) і переконайся, що сервер у Windows прив’язується до `0.0.0.0`, а не лише до `127.0.0.1`. Windows Firewall зазвичай також потребує правило для порту.

Для повної таблиці (адреси прив’язки Ollama / LM Studio / vLLM / SGLang, однорядкові правила firewall, динамічні IP‑помічники, обхід Hyper‑V firewall) переходь за вказаним вище посиланням — не дублюй його.

### Випадок 2 — Щось у Windows (або у твоїй LAN) спілкується з Hermes у WSL

Це зворотний напрямок і менш задокументований, проте саме він потрібен для:

- Використання **веб‑дашборду Hermes** у браузері Windows.
- Використання **API‑сервера, сумісного з OpenAI** (який відкриває `hermes gateway`, коли `API_SERVER_ENABLED=true`) з інструменту на стороні Windows. Дивись сторінку [API Server feature page](/user-guide/features/api-server).
- Тестування **шлюзу обміну повідомленнями** (Telegram, Discord тощо), коли платформа надсилає запит на локальний webhook‑URL — зазвичай використовується `cloudflared`/`ngrok`, а не «чисте» перенаправлення портів.

#### Підвипадок 2a: з самого хоста Windows

На **Windows 11 22H2+ з увімкненим режимом дзеркалювання** нічого робити не потрібно. Процес у WSL, який прив’язується до `0.0.0.0:8080` (або навіть `127.0.0.1:8080`), доступний у браузері Windows за `http://localhost:8080`. WSL автоматично публікує прив’язку назад до хоста.

На **режимі NAT** (Windows 10 / старіші Windows 11) стандартне «перенаправлення localhost» у WSL2 зазвичай переспрямовує прив’язки Linux‑сторони `127.0.0.1` до Windows `localhost`, тому сервіс Hermes, запущений з `--host 127.0.0.1`, зазвичай доступний як `http://localhost:PORT` у Windows. Якщо це не так:

- Явно прив’яжи до `0.0.0.0` всередині WSL.
- Знайди IP‑адресу VM WSL командою `ip -4 addr show eth0 | grep inet` і підключайся до неї з Windows.

#### Підвипадок 2b: з іншого пристрою у твоїй LAN (телефон, планшет, інший ПК)

Ось справжня головна проблема. Трафік проходить **пристрій LAN → хост Windows → VM WSL**, і треба налаштувати обидва «стрибки»:

1. **Прив’язка на всі інтерфейси всередині WSL.** Процес, який слухає `127.0.0.1`, ніколи не буде доступний зовні VM. Використовуй `0.0.0.0`.

2. **Перенаправлення портів Windows → VM WSL.** У режимі дзеркалювання це автоматично. У режимі NAT треба робити це вручну, порт за портом, у PowerShell з правами адміністратора:

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

   Пізніше видали правило за допомогою `netsh interface portproxy delete v4tov4 listenaddress=0.0.0.0 listenport=8080`.

3. **Вкажи пристрою LAN URL `http://<windows-lan-ip>:8080`.**

Оскільки IP‑адреса VM WSL змінюється при кожному перезапуску в режимі NAT, правило «один раз» діє лише до наступного `wsl --shutdown`. Для постійного рішення або використай режим дзеркалювання, або додай крок port‑proxy у скрипт, який запускається при вході в Windows.

Для webhook‑ів від хмарних провайдерів повідомлень (Telegram `setWebhook`, події Slack тощо) не борись з перенаправленням портів — використай тунелі `cloudflared`. Дивись [webhooks guide](/user-guide/messaging/webhooks).
## Запуск сервісів Hermes у довгостроковій перспективі на Windows

Hermes [шлюз інструментів (Tool Gateway)](/user-guide/features/tool-gateway) та API‑сервер – це довгоживучі процеси. У WSL2 у тебе є кілька варіантів, як їх підтримувати.

### Ярлик на робочому столі для швидкого відкриття Hermes

Якщо потрібен запускатор — двічі клацни — для інтерактивної оболонки Hermes, створи його у Windows і нехай він переходить у WSL за тебе:

1. Клацни правою кнопкою миші на робочому столі Windows і вибери **New → Shortcut**.
2. У полі **Target** вкажи назву дистрибутива (за потреби заміни `Ubuntu`):

   ```text
   wt.exe -w 0 -p "Ubuntu" wsl.exe -d Ubuntu --cd ~ -- bash -ic "hermes"
   ```

3. Дай ярлику зрозумілу назву, наприклад `Hermes`.

Тепер відкривається Windows Terminal, запускається твій дистрибутив WSL, переходить у домашню теку Linux і стартує Hermes. Якщо `hermes` ще не в PATH, відкрий WSL вручну один раз і виконай `source ~/.bashrc`, або заміни команду на `uv run hermes` у каталозі проєкту.

**Додаткові налаштування**

- **Власна іконка:** відкрий **Properties → Change Icon** і вкажи файл `.ico`, наприклад favicon Hermes з репозиторію.
- **Закріплений запуск:** після того, як ярлик працює, закріпи його на **Start** або **Taskbar**, щоб не шукати щоразу.

### Усередині WSL за допомогою systemd (рекомендовано)

Якщо ти увімкнув systemd згідно розділу налаштування вище, `hermes gateway` і API‑сервер працюватимуть так само, як на будь‑якому Linux‑комп’ютері. Скористайся майстром налаштування шлюзу:

```bash
hermes gateway setup
```

Він запропонує встановити юніт користувача systemd, щоб шлюз піднімався автоматично під час старту WSL.

### Щоб WSL сам запускалося при вході в Windows

Віртуальна машина WSL живе лише доки її хтось використовує. Щоб твій шлюз був доступний без відкритого вікна терміналу, запусти процес WSL під час входу в Windows через Планувальник завдань:

- **Тригер:** At log on (твоїй користувачеві).
- **Дія:** Start a program
  - **Program:** `C:\Windows\System32\wsl.exe`
  - **Arguments:** `-d Ubuntu --exec /bin/sh -c "sleep infinity"`

Так віртуальна машина залишатиметься активною, і шлюз, керований systemd, продовжуватиме працювати. На Windows 11 також працює новіший підхід — `wsl --install --no-launch` + автозапуск; трюк `sleep infinity` є портативною версією.
## GPU passthrough (local models)

WSL2 підтримує **NVIDIA** GPU нативно, починаючи з ядра WSL 5.10.43+ — встанови стандартний драйвер NVIDIA у Windows (не встановлюй Linux‑драйвер NVIDIA всередині WSL), і `nvidia-smi` у WSL побачить GPU. Після цього CUDA‑toolkits, `torch`, `vllm`, `sglang` та `llama-server` будуються проти реального GPU, як зазвичай.

Підтримка AMD ROCm та Intel Arc у WSL2 ще розвивається і знаходиться поза тест‑матрицею Hermes — можливо, працюватиме з поточними драйверами, але у нас немає готового рецепту.

Якщо ти запускаєш **Windows‑native** сервер локальних моделей (Ollama for Windows, LM Studio), який вже використовує твій GPU через драйвери Windows, WSL GPU passthrough взагалі не потрібен — просто слідуй інструкції з Case 1 вище і підключайся до нього по мережі з WSL.
## Типові підводні камені

**«Connection refused» до Ollama / LM Studio, запущених у Windows.**
Дивись [WSL2 Networking](/integrations/providers#wsl2-networking-windows-users). У 90 % випадків сервер прив’язаний до `127.0.0.1` і потребує `0.0.0.0` (Ollama: `OLLAMA_HOST=0.0.0.0`), або у тебе відсутнє правило брандмауера.

**Сильне сповільнення `git status` / `hermes chat` у репозиторії.**
Швидше за все ти працюєш у каталозі `/mnt/c/...`. Перемісти репозиторій у `~/code/...` (Linux‑частина). Працюватиме в десятки разів швидше.

**`bad interpreter: /bin/bash^M` у скриптах.**
Кінці рядків CRLF з Windows‑редактора. Використай `dos2unix script.sh` і встанови `core.autocrlf input` у конфігурації Git у WSL.

**Попередження «UNC paths are not supported» від Windows‑бінарників, запущених через MCP.**
Поточна директорія Hermes знаходиться у файловій системі Linux, а `cmd.exe` у Windows не знає, як її обробити. Запусти Hermes із `/mnt/c/...` для цієї сесії або використай обгортку, яка спочатку `cd` у шлях, доступний Windows, перед викликом Windows‑виконуваного файлу.

**Зсув системного часу після сну/гібернації.**
Годинник WSL2 може відставати на кілька хвилин після пробудження хоста, що порушує роботу всіх сертифікат‑залежних сервісів (OAuth, HTTPS‑API). Виправити за потреби:

```bash
sudo hwclock -s
```

Або встанови `ntpdate` і запускай його при вході в систему.

**DNS перестає працювати після ввімкнення режиму mirrored або підключення VPN.**
Режим mirrored прокидує налаштування мережі хоста у WSL — якщо DNS у Windows «поганий» (split‑tunnel VPN, корпоративний резолвер), WSL успадковує це. Обхідний шлях: вручну перевизначити `resolv.conf` (встанови `generateResolvConf=false` у `/etc/wsl.conf`, потім створити власний `/etc/resolv.conf` з `1.1.1.1` або DNS‑сервером твого VPN).

**`hermes` не знайдено після запуску інсталятору.**
Інсталятор додає `~/.local/bin` до `PATH` у твоєму `~/.bashrc`. Потрібно виконати `source ~/.bashrc` (або відкрити новий термінал), щоб зміни набули чинності в поточній сесії.

**Windows Defender уповільнює роботу з файлами WSL.**
Defender сканує файли через 9P‑мост, коли вони доступні з Windows, що значно уповільнює доступ до файлів у `/mnt/c`. Якщо ти працюєш лише з файлами всередині WSL, це не має значення. Якщо часто використовуєш Windows‑інструменти до `\\wsl$\...`, розглянь виключення шляху дистрибутива WSL з реального часу сканування.

**Недостатньо вільного місця на диску.**
WSL2 зберігає диск віртуальної машини у вигляді розрідженого VHDX у `%LOCALAPPDATA%\Packages\...`. Він росте, але не стискається автоматично після видалення файлів. Щоб звільнити простір: виконай `wsl --shutdown`, а потім у PowerShell з правами адміністратора запусти `Optimize-VHD -Path <шлях‑до‑ext4.vhdx> -Mode Full` (потрібні інструменти Hyper‑V) — або скористайся простішим способом через `diskpart`, описаним у документації WSL.
## Куди далі

- **[Встановлення](/getting-started/installation)** — фактичні кроки інсталяції (Linux/WSL2/Termux використовують один і той самий інсталятор).
- **[Інтеграції → Провайдери → WSL2 Networking](/integrations/providers#wsl2-networking-windows-users)** — канонічний глибокий огляд мережі для локальних серверів моделей.
- **[Посібник MCP → WSL → Windows Chrome](/guides/use-mcp-with-hermes#wsl2-bridge-hermes-in-wsl-to-windows-chrome)** — керування підключеним Windows Chrome з Hermes у WSL.
- **[Шлюз інструментів (Tool Gateway)](/user-guide/features/tool-gateway)** та **[Веб‑дашборд](/user-guide/features/web-dashboard)** — довготривалі сервіси, які найчастіше потрібно експортувати з WSL у решту мережі.