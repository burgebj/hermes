---
title: Автоматизація браузера
description: Керуй браузерами з кількома провайдерами, локальними браузерами сімейства Chromium через CDP, або хмарними браузерами для веб‑взаємодії, заповнення форм, скрапінгу та іншого.
sidebar_label: Browser
sidebar_position: 5
---

# Автоматизація браузера

Hermes Agent включає повний інструментальний набір автоматизації браузера з кількома варіантами бекенду:

- **Browserbase cloud mode** через [Browserbase](https://browserbase.com) для керованих хмарних браузерів і інструментів проти ботів
- **Browser Use cloud mode** через [Browser Use](https://browser-use.com) як альтернативний провайдер хмарних браузерів
- **Firecrawl cloud mode** через [Firecrawl](https://firecrawl.dev) для хмарних браузерів із вбудованим скрапінгом
- **Camofox local mode** через [Camofox](https://github.com/jo-inc/camofox-browser) для локального браузингу з анти‑детекційним захистом (фальсифікація відбитка на базі Firefox)
- **Local Chromium-family CDP** — підключення інструментів браузера до власного екземпляра Chrome, Brave, Chromium або Edge за допомогою `/browser connect`
- **Local browser mode** через CLI `agent-browser` та локальну інсталяцію Chromium

У всіх режимах агент може переглядати веб‑сайти, взаємодіяти з елементами сторінки, заповнювати форми та витягувати інформацію.
## Огляд

Сторінки представляються як **дерева доступності** (текстові знімки), що робить їх ідеальними для LLM‑агентів. Інтерактивні елементи отримують ref‑ідентифікатори (наприклад `@e1`, `@e2`), які агент використовує для кліків та вводу тексту.

**Ключові можливості**:

- **Багатопровайдерне хмарне виконання** — Browserbase, Browser Use або Firecrawl — без потреби у локальному браузері
- **Локальна інтеграція з Chromium‑подібними браузерами** — підключення до запущеного Chrome, Brave, Chromium або Edge через CDP для ручного перегляду
- **Вбудований стелс‑режим** — випадкові відбитки пальців, розв’язання CAPTCHA, резидентні проксі (Browserbase)
- **Ізоляція сесій** — кожне завдання отримує власну браузерну сесію
- **Автоматичне очищення** — неактивні сесії закриваються після тайм‑ауту
- **Візуальний аналіз** — скріншот + AI‑аналіз для розуміння зображень
## Setup

:::tip Передплатники Nous
Якщо у тебе є платна підписка на [Nous Portal](https://portal.nousresearch.com), ти можеш користуватися автоматизацією браузера через **[Tool Gateway](tool-gateway.md)** без окремих API‑ключів. При новій інсталяції можна виконати `hermes setup --portal`, щоб увійти в систему та одночасно увімкнути всі інструменти шлюзу; при існуючій інсталяції можна вибрати **Nous Subscription** як провайдера браузера за допомогою `hermes model` або `hermes tools`.
:::
### Хмарний режим Browserbase

Щоб використовувати керовані Browserbase хмарні браузери, додай:

```bash
# Add to ~/.hermes/.env
BROWSERBASE_API_KEY=***
BROWSERBASE_PROJECT_ID=your-project-id-here
```

Отримай свої облікові дані на [browserbase.com](https://browserbase.com).
### Browser Use у хмарному режимі

Щоб використовувати Browser Use як провайдера хмарного браузера, додай:

```bash
# Add to ~/.hermes/.env
BROWSER_USE_API_KEY=***
```

Отримай свій API‑ключ на [browser-use.com](https://browser-use.com). Browser Use надає хмарний браузер через свій REST API. Якщо вказані облікові дані як Browserbase, так і Browser Use, пріоритет має Browserbase.
### Режим хмарного браузера Firecrawl

Щоб використовувати Firecrawl як провайдер хмарного браузера, додай:

```bash
# Add to ~/.hermes/.env
FIRECRAWL_API_KEY=fc-***
```

Отримай свій API‑ключ на [firecrawl.dev](https://firecrawl.dev). Потім обери Firecrawl як провайдер браузера:

```bash
hermes setup tools
# → Browser Automation → Firecrawl
```

Додаткові налаштування:

```bash
# Self-hosted Firecrawl instance (default: https://api.firecrawl.dev)
FIRECRAWL_API_URL=http://localhost:3002

# Session TTL in seconds (default: 300)
FIRECRAWL_BROWSER_TTL=600
```
### Гібридна маршрутизація: хмара для публічних URL, локальна для LAN/localhost

Коли налаштовано хмарного провайдера, Hermes автоматично створює **локальний Chromium sidecar** для URL‑адрес, які резольвяться в приватну/loopback/LAN адресу (`localhost`, `127.0.0.1`, `192.168.x.x`, `10.x.x.x`, `172.16-31.x.x`, `*.local`, `*.lan`, `*.internal`, IPv6 loopback `::1`, link‑local `169.254.x.x`). Публічні URL‑адреси продовжують використовувати хмарного провайдера в тому ж діалозі.

Це вирішує поширений робочий процес «я розробляю локально, але використовую Browserbase» — агент може зробити скріншот твоєї панелі за `http://localhost:3000` **і** скрапити `https://github.com` без переключення провайдерів або вимкнення захисту SSRF. Хмарний провайдер ніколи не бачить приватну URL‑адресу.

Функція **увімкнена за замовчуванням**. Щоб вимкнути її (усі URL‑адреси йдуть до налаштованого хмарного провайдера, як раніше):

```yaml
# ~/.hermes/config.yaml
browser:
  cloud_provider: browserbase
  auto_local_for_private_urls: false
```

При вимкненій автоматичній маршрутизації приватні URL‑адреси відхиляються з повідомленням
`"Blocked: URL targets a private or internal address"` — якщо ти не встановиш `browser.allow_private_urls: true` (це дозволяє хмарному провайдеру спробувати їх, зазвичай не працює, оскільки Browserbase тощо не можуть дістатися до твоєї LAN).

Вимоги: локальний sidecar використовує той самий CLI `agent-browser`, що й у чисто локальному режимі, тому його треба встановити (`hermes setup tools → Browser Automation` авто‑встановлює його). Перенаправлення після навігації з публічної URL‑адреси на приватну адресу все одно блокуються (не можна використати трюк з redirect‑to‑internal, щоб дістатися до твоєї LAN через публічний шлях).
### Camofox локальний режим

[Camofox](https://github.com/jo-inc/camofox-browser) — це самостійно розгорнутий Node.js сервер, який обгортає Camoufox (форк Firefox з підміною C++ fingerprint). Він забезпечує локальне анти‑детекційне браузерне середовище без хмарних залежностей.

```bash
# Clone the Camofox browser server first
git clone https://github.com/jo-inc/camofox-browser
cd camofox-browser

# Build and start with Docker using the default container settings
# (auto-detects arch: aarch64 on M1/M2, x86_64 on Intel)
make up

# Stop and remove the default container
make down

# Force a clean rebuild (for example, after upgrading VERSION/RELEASE)
make reset

# Just download binaries without building
make fetch

# Override arch or version explicitly
make up ARCH=x86_64
make up VERSION=135.0.1 RELEASE=beta.24
```

`make up` запускає контейнер за замовчуванням одразу. Якщо потрібні власні налаштування середовища, наприклад збільшений Node heap, VNC або постійний каталог профілю, спочатку збудуйте образ, а потім запустіть його самостійно:

```bash
# Build the image without starting the default container
make build

# Start with persistence, VNC live view, and a larger Node heap
mkdir -p ~/.camofox-docker
docker run -d \
  --name camofox-browser \
  --restart unless-stopped \
  -p 9377:9377 \
  -p 6080:6080 \
  -p 5901:5900 \
  -e CAMOFOX_PORT=9377 \
  -e ENABLE_VNC=1 \
  -e VNC_BIND=0.0.0.0 \
  -e VNC_RESOLUTION=1920x1080 \
  -e MAX_OLD_SPACE_SIZE=2048 \
  -v ~/.camofox-docker:/root/.camofox \
  camofox-browser:135.0.1-aarch64
```

При ввімкненому VNC браузер працює в headed‑режимі і його можна переглядати в реальному часі у вашому браузері за адресою `http://localhost:6080` (noVNC). Також можна під’єднати нативний VNC‑клієнт до `localhost:5901`.

Якщо ви вже запускали `make up`, зупиніть і видаліть цей контейнер за замовчуванням перед запуском кастомного:

```bash
make down
# then run the custom docker run command above
```

Потім встановіть у `~/.hermes/.env`:

```bash
CAMOFOX_URL=http://localhost:9377
```

Якщо Camofox працює в Docker і ви хочете, щоб він відкривав веб‑додатки, що сервісуються з хост‑машини, увімкніть переписування loopback. `CAMOFOX_URL` має й надалі вказувати на контрольний API, опублікований хостом, але URL‑и сторінок типу `http://127.0.0.1:3000` мають відкриватися всередині контейнера як `http://host.docker.internal:3000`:

```yaml
# ~/.hermes/config.yaml
browser:
  camofox:
    rewrite_loopback_urls: true
    loopback_host_alias: host.docker.internal  # default; use a LAN IP if needed
```

Еквівалентні змінні середовища:

```bash
CAMOFOX_REWRITE_LOOPBACK_URLS=true
CAMOFOX_LOOPBACK_HOST_ALIAS=host.docker.internal
```

Переписування застосовується лише до URL‑ів навігації сторінок з loopback‑хостами (`localhost`, `127.0.0.1`, `::1`). Воно не змінює `CAMOFOX_URL`. Залиште його вимкненим для інсталяцій Camofox поза Docker, коли браузер вже працює на хості і loopback‑URL‑и правильні.

Або налаштуйте через `hermes tools` → Browser Automation → Camofox.

Коли `CAMOFOX_URL` встановлено, усі інструменти браузера автоматично маршрутизуються через Camofox замість Browserbase або agent-browser.

#### Постійні сесії браузера

За замовчуванням кожна Camofox‑сесія отримує випадкову ідентичність — куки та логіни не зберігаються між перезапусками агента. Щоб увімкнути постійні сесії браузера, додайте наступне до `~/.hermes/config.yaml`:

```yaml
browser:
  camofox:
    managed_persistence: true
```

Потім повністю перезапустіть Hermes, щоб нова конфігурація була застосована.

:::warning Nested path matters
Hermes читає `browser.camofox.managed_persistence`, **не** верхньорівневий `managed_persistence`. Поширена помилка — записати:

```yaml
# ❌ Wrong — Hermes ignores this
managed_persistence: true
```

Якщо прапорець розташовано не за правильним шляхом, Hermes тихо повернеться до випадкового епхемерного `userId`, і ваш стан входу буде втрачено у кожній сесії.
:::

##### Що робить Hermes
- Надсилає детермінований, прив’язаний до профілю `userId` у Camofox, щоб сервер міг повторно використовувати один і той самий Firefox‑профіль між сесіями.
- Пропускає знищення контексту на боці сервера під час очистки, тому куки та логіни виживають між завданнями агента.
- Прив’язує `userId` до активного профілю Hermes, тож різні профілі Hermes отримують різні браузерні профілі (ізоляція профілів).

##### Що Hermes НЕ робить
- Він не змушує сервер Camofox зберігати дані. Hermes лише надсилає стабільний `userId`; сервер повинен його поважати, прив’язуючи `userId` до постійного каталогу профілю Firefox.
- Якщо ваша збірка Camofox розглядає кожен запит як епхемерний (наприклад, завжди викликає `browser.newContext()` без завантаження збереженого профілю), Hermes не зможе зробити сесії постійними. Переконайтеся, що ви використовуєте збірку Camofox, яка реалізує збереження профілю на основі `userId`.

##### Перевірка роботи

1. Запустіть Hermes і ваш сервер Camofox.
2. Відкрийте Google (або будь‑який сайт входу) у браузерному завданні і ввійдіть вручну.
3. Завершіть браузерне завдання звичайним способом.
4. Запустіть нове браузерне завдання.
5. Відкрийте той самий сайт ще раз — ви маєте залишитися ввійшлим.

Якщо на кроці 5 ви виходите з системи, сервер Camofox не поважає стабільний `userId`. Перевірте шлях у конфігурації, переконайтеся, що ви повністю перезапустили Hermes після редагування `config.yaml`, і впевніться, що ваша версія сервера Camofox підтримує постійні профілі для користувачів.

##### Де зберігається стан

Hermes отримує стабільний `userId` з каталогу, прив’язаного до профілю `~/.hermes/browser_auth/camofox/` (або еквівалентного під `$HERMES_HOME` для нестандартних профілів). Самі дані браузерного профілю зберігаються на боці сервера Camofox, індексовані цим `userId`. Щоб повністю скинути постійний профіль, очистіть його на сервері Camofox і видаліть відповідний каталог стану профілю Hermes.

#### Зовнішньо керовані Camofox‑сесії

Коли інша програма керує видимим браузером Camofox (десктоп‑асистент, кастомна інтеграція, інший агент), налаштуйте Hermes працювати в межах тієї ж ідентичності замість створення власного ізольованого профілю.

Три налаштування контролюють поведінку:

| Setting | Env var | Effect |
|---------|---------|--------|
| `browser.camofox.user_id` | `CAMOFOX_USER_ID` | `userId` Camofox, який Hermes використовує при створенні вкладок. Встановлення цього переводить сесію в режим «зовнішньо керований». |
| `browser.camofox.session_key` | `CAMOFOX_SESSION_KEY` | `sessionKey` (a.k.a. `listItemId`), що надсилається при створенні вкладки. Використовується для підбору існуючої вкладки під час прийняття. За замовчуванням генерується значення per‑task, якщо не вказано. |
| `browser.camofox.adopt_existing_tab` | `CAMOFOX_ADOPT_EXISTING_TAB` | Якщо `true`, Hermes виконує `GET /tabs?userId=<user_id>` при першому використанні і повторно використовує існуючу вкладку перед створенням нової. |

Змінні середовища мають пріоритет над `config.yaml`. Працює будь‑яка форма:

```yaml
browser:
  camofox:
    user_id: shared-camofox
    session_key: visible-tab
    adopt_existing_tab: true
```

```bash
CAMOFOX_USER_ID=shared-camofox
CAMOFOX_SESSION_KEY=visible-tab
CAMOFOX_ADOPT_EXISTING_TAB=true
```

**Що змінюється, коли встановлено `user_id`:**

- Hermes пропускає руйнівну очистку в кінці завдання (те саме, що `managed_persistence: true`). Вкладка/куки/профіль іншої програми залишаються.
- Hermes **не** викликає `DELETE /sessions/<user_id>` — цей endpoint стирає всі дані користувача, що могло б знищити сесію зовнішньої програми.

**Як працює прийняття вкладки (коли `adopt_existing_tab: true`):**

1. При першому виклику браузерного інструмента після старту процесу Hermes надсилає `GET /tabs?userId=<user_id>` (таймаут 5 сек).
2. Якщо у відповіді є вкладка з `listItemId == session_key`, Hermes приймає найновішу у цій групі.
3. Інакше Hermes приймає найновішу вкладку користувача (будь‑який `listItemId`).
4. Якщо вкладок немає або запит не вдається, Hermes переходить до створення нової вкладки.

Прийняття триває, доки `tab_id` не заповниться для сесії. Якщо зовнішня програма закриє прийняту вкладку під час роботи, наступний виклик браузерного інструмента поверне помилку Camofox — Hermes не буде повторно опитувати нову вкладку при кожному виклику.

**Вибір `session_key`**: якщо потрібно, щоб Hermes надійно під’єднався до *конкретної* існуючої вкладки, встановіть `session_key` у `listItemId`, який зовнішня програма використала при її створенні. Якщо залишити `session_key` порожнім і задати лише `user_id`, Hermes згенерує `session_key` per‑task (`task_<id>`) — Hermes поділиться куками та профілем із зовнішньою програмою, але відкриє свою власну вкладку поруч, а не повторно використає існуючу.

**Примітка про конкурентність**: зовнішня програма та Hermes можуть одночасно працювати з тим самим `userId` у Camofox, проте Camofox не координує фокус вкладок між клієнтами. Керуйте власністю на рівні застосунку (наприклад, зовнішня програма паузить роботу, доки працює Hermes).

#### VNC живий перегляд

Коли Camofox працює в headed‑режимі (з видимим вікном браузера), він відкриває VNC‑порт у відповіді health‑check. Hermes автоматично виявляє це і включає VNC‑URL у відповіді навігації, щоб агент міг поділитися посиланням для перегляду браузера в реальному часі.
### Локальний браузер сімейства Chromium через CDP (`/browser connect`)

Замість хмарного провайдера ти можеш під’єднати інструменти Hermes browser до власного запущеного Chrome, Brave, Chromium або Edge через Chrome DevTools Protocol (CDP). Це корисно, коли хочеш бачити, що агент робить у реальному часі, взаємодіяти зі сторінками, які потребують твоїх власних cookie/сесій, або уникнути витрат на хмарний браузер.

:::note
`/browser connect` — це **інтерактивна CLI slash‑команда**; вона не передається шлюзом. Якщо спробувати виконати її всередині WebUI, Telegram, Discord чи іншого чат‑шлюзу, повідомлення буде надіслано агенту як звичайний текст, і команда не виконається. Запусти Hermes з терміналу (`hermes` або `hermes chat`) і введи `/browser connect` там.
:::

У CLI використай:

```
/browser connect                 # Auto-launch/connect to a local Chromium-family browser at http://127.0.0.1:9222
/browser connect ws://host:port  # Connect to a specific CDP endpoint
/browser status                  # Check current connection
/browser disconnect              # Detach and return to cloud/local mode
```

Якщо браузер ще не запущений з віддаленим налагодженням, Hermes спробує автоматично запустити підтримуваний браузер сімейства Chromium з параметром `--remote-debugging-port=9222`. Виявлення включає Brave, Google Chrome, Chromium та Microsoft Edge, з типовими шляхами встановлення в Linux, наприклад `/opt/brave-bin/brave` та `/snap/bin/brave`.

:::tip
Щоб вручну запустити браузер сімейства Chromium з увімкненим CDP, використай окремий `user-data-dir`, щоб порт налагодження справді відкрився, навіть якщо браузер вже працює з твоїм звичайним профілем:

```bash
# Linux — Brave
brave-browser \
  --remote-debugging-port=9222 \
  --user-data-dir=$HOME/.hermes/chrome-debug \
  --no-first-run \
  --no-default-browser-check &

# Linux — Google Chrome
google-chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=$HOME/.hermes/chrome-debug \
  --no-first-run \
  --no-default-browser-check &

# macOS — Brave
"/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.hermes/chrome-debug" \
  --no-first-run \
  --no-default-browser-check &

# macOS — Google Chrome
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.hermes/chrome-debug" \
  --no-first-run \
  --no-default-browser-check &
```

Потім запусти Hermes CLI і виконай `/browser connect`.

**Навіщо `--user-data-dir`?** Без цього параметра запуск браузера сімейства Chromium, коли вже працює звичайний екземпляр, зазвичай відкриває нове вікно в існуючому процесі — а цей процес не був запущений з `--remote-debugging-port`, тому порт 9222 не відкривається. Окремий `user-data-dir` примушує створити новий процес браузера, де порт налагодження дійсно слухає. Параметри `--no-first-run --no-default-browser-check` пропускають майстер першого запуску для нового профілю.
:::

Коли під’єднано через CDP, всі інструменти браузера (`browser_navigate`, `browser_click` тощо) працюють у твоєму живому екземплярі браузера замість створення хмарної сесії.
### WSL2 + Windows Chrome: надавай перевагу MCP замість `/browser connect`

Якщо Hermes працює всередині WSL2, а вікно Chrome, яким ти хочеш керувати, запущене на хості Windows, `/browser connect` часто не є найкращим шляхом.

Чому:

- `/browser connect` очікує, що сам Hermes зможе дістатися до доступної кінцевої точки CDP
- сучасні сеанси живого налагодження Chrome часто відкривають локальну кінцеву точку на хості, яка не доступна безпосередньо з WSL так само, як класичний порт `9222`
- навіть коли Windows Chrome відлагоджується, найчистіша інтеграція часто полягає в тому, щоб сервер MCP браузера на стороні Windows підключився до Chrome, а Hermes спілкувався з цим сервером MCP

Для такої конфігурації надавай перевагу `chrome-devtools-mcp` через підтримку Hermes MCP.

Дивись посібник MCP для практичної налаштування:

- [Use MCP with Hermes](../../guides/use-mcp-with-hermes.md#wsl2-bridge-hermes-in-wsl-to-windows-chrome)
### Режим локального браузера

Якщо ти **не** вказуєш жодних хмарних облікових даних і не використовуєш `/browser connect`, Hermes все одно може користуватися інструментами браузера через локальну інсталяцію Chromium, якою керує `agent-browser`.
### Опціональні змінні середовища

```bash
# Residential proxies for better CAPTCHA solving (default: "true")
BROWSERBASE_PROXIES=true

# Advanced stealth with custom Chromium — requires Scale Plan (default: "false")
BROWSERBASE_ADVANCED_STEALTH=false

# Session reconnection after disconnects — requires paid plan (default: "true")
BROWSERBASE_KEEP_ALIVE=true

# Custom session timeout in milliseconds (default: project default)
# Examples: 600000 (10min), 1800000 (30min)
BROWSERBASE_SESSION_TIMEOUT=600000

# Inactivity timeout before auto-cleanup in seconds (default: 120)
BROWSER_INACTIVITY_TIMEOUT=120

# Extra Chromium launch flags (comma- or newline-separated). Hermes auto-injects
# `--no-sandbox,--disable-dev-shm-usage` when it detects root or AppArmor-restricted
# unprivileged user namespaces (Ubuntu 23.10+, DGX Spark, many container images),
# so most users don't need to set this. Set it manually only if you need a flag
# Hermes doesn't add automatically; setting it disables the auto-injection.
AGENT_BROWSER_ARGS=--no-sandbox
```
### Встановити agent-browser CLI

```bash
npm install -g agent-browser
# Or install locally in the repo:
npm install
```

:::info
Набір інструментів `browser` має бути включений у список `toolsets` вашої конфігурації або активований за допомогою `hermes config set toolsets '["hermes-cli", "browser"]'`.
:::
## Доступні інструменти

### `browser_navigate`

Перехід за URL. Має бути викликаний перед будь‑яким іншим інструментом браузера. Ініціалізує сесію Browserbase.

```
Navigate to https://github.com/NousResearch
```

:::tip
Для простого отримання інформації краще використовувати `web_search` або `web_extract` — вони швидші та дешевші. Використовуй інструменти браузера, коли потрібно **взаємодіяти** зі сторінкою (клацати кнопки, заповнювати форми, працювати з динамічним вмістом).
:::

### `browser_snapshot`

Отримати текстовий знімок дерева доступності поточної сторінки. Повертає інтерактивні елементи з ref‑ID типу `@e1`, `@e2` для використання у `browser_click` та `browser_type`.

- **`full=false`** (за замовчуванням): компактний вигляд, лише інтерактивні елементи
- **`full=true`**: повний вміст сторінки

Знімки понад 8000 символів автоматично підсумовуються LLM.

### `browser_click`

Клацнути елемент, ідентифікований його ref‑ID зі знімка.

```
Click @e5 to press the "Sign In" button
```

### `browser_type`

Ввести текст у поле вводу. Спочатку очищає поле, потім вводить новий текст.

```
Type "hermes agent" into the search field @e3
```

### `browser_scroll`

Прокрутити сторінку вгору або вниз, щоб відкрити більше вмісту.

```
Scroll down to see more results
```

### `browser_press`

Натиснути клавішу клавіатури. Корисно для відправки форм або навігації.

```
Press Enter to submit the form
```

Підтримувані клавіші: `Enter`, `Tab`, `Escape`, `ArrowDown`, `ArrowUp` та інші.

### `browser_back`

Повернутися на попередню сторінку в історії браузера.

### `browser_get_images`

Перелічити всі зображення на поточній сторінці разом з їх URL та alt‑текстом. Корисно для пошуку зображень для аналізу.

### `browser_vision`

Зробити скріншот і проаналізувати його за допомогою vision AI. Використовуй, коли текстові знімки не захоплюють важливу візуальну інформацію — особливо корисно для CAPTCHA, складних макетів або візуальних перевірок.

Скріншот зберігається постійно, а шлях до файлу повертається разом з результатом AI‑аналізу. На платформах обміну повідомленнями (Telegram, Discord, Slack, WhatsApp) можна попросити агента поділитися скріншотом — він буде надісланий як нативне фото‑вкладення через механізм `MEDIA:`.

```
What does the chart on this page show?
```

Скріншоти зберігаються в `~/.hermes/cache/screenshots/` і автоматично видаляються через 24 години.

### `browser_console`

Отримати вивід консолі браузера (log/warn/error) та неперехоплені виключення JavaScript з поточної сторінки. Необхідно для виявлення тихих JS‑помилок, які не з’являються в дереві доступності.

```
Check the browser console for any JavaScript errors
```

Використай `clear=True`, щоб очистити консоль після читання, так що наступні виклики покажуть лише нові повідомлення.

`browser_console` також виконує JavaScript, якщо передати аргумент `expression` — такий же синтаксис, як у консолі DevTools, результат повертається розпарсеним (JSON‑серіалізовані об’єкти стають dict, примітивні значення залишаються примітивами).

```
browser_console(expression="document.querySelector('h1').textContent")
browser_console(expression="JSON.stringify(performance.timing)")
```

Коли для поточної сесії активний CDP‑супервізор (зазвичай для будь‑якої сесії, що виконує `browser_navigate` проти CDP‑сумісного бекенду), оцінка виконується через постійний WebSocket супервізора — без витрат на запуск підпроцесу. Інакше використовується стандартний шлях agent‑browser CLI. Поведінка ідентична, змінюється лише затримка.

### `browser_cdp`

Прямий прохід Chrome DevTools Protocol — «escape hatch» для операцій браузера, які не охоплені іншими інструментами. Використовуй для обробки нативних діалогів, оцінки в межах iframe, керування cookie/мережею або будь‑якої CDP‑команди, потрібної агенту.

**Доступно лише коли CDP‑endpoint досяжний під час старту сесії** — тобто `/browser connect` під’єднався до запущеного Chrome, Brave, Chromium або Edge, або `browser.cdp_url` заданий у `config.yaml`. Типовий локальний режим agent‑browser, Camofox та хмарні провайдери (Browserbase, Browser Use, Firecrawl) наразі не відкривають CDP для цього інструменту — у хмарних провайдерів є CDP‑URL‑и per‑session, але маршрутизація live‑session ще в розробці.

**Посилання на методи CDP:** https://chromedevtools.github.io/devtools-protocol/ — агент може `web_extract` сторінку конкретного методу, щоб дізнатися параметри та форму відповіді.

Типові шаблони:

```
# List tabs (browser-level, no target_id)
browser_cdp(method="Target.getTargets")

# Handle a native JS dialog on a tab
browser_cdp(method="Page.handleJavaScriptDialog",
            params={"accept": true, "promptText": ""},
            target_id="<tabId>")

# Evaluate JS in a specific tab
browser_cdp(method="Runtime.evaluate",
            params={"expression": "document.title", "returnByValue": true},
            target_id="<tabId>")

# Get all cookies
browser_cdp(method="Network.getAllCookies")
```

Методи рівня браузера (`Target.*`, `Browser.*`, `Storage.*`) не потребують `target_id`. Методи рівня сторінки (`Page.*`, `Runtime.*`, `DOM.*`, `Emulation.*`) вимагають `target_id`, отриманий з `Target.getTargets`. Кожен безстановий виклик незалежний — сесії не зберігаються між викликами.

**Cross‑origin iframes:** передай `frame_id` (з `browser_snapshot.frame_tree.children[]`, де `is_oopif=true`), щоб маршрутизувати CDP‑виклик через живу сесію супервізора для цього iframe. Так працює `Runtime.evaluate` всередині крос‑оригінального iframe на Browserbase, де безстанові CDP‑з’єднання стикалися б із закінченням терміну підписаного URL. Приклад:

```
browser_cdp(
  method="Runtime.evaluate",
  params={"expression": "document.title", "returnByValue": True},
  frame_id="<frame_id from browser_snapshot>",
)
```

Same‑origin iframe не потребують `frame_id` — використай `document.querySelector('iframe').contentDocument` у верхньому `Runtime.evaluate`.

### `browser_dialog`

Відповідає на нативний JS‑діалог (`alert` / `confirm` / `prompt` / `beforeunload`). До появи цього інструменту діалоги тихо блокували JavaScript‑потік сторінки, і подальші виклики `browser_*` зависали або кидали помилку; тепер агент бачить очікуючі діалоги у виводі `browser_snapshot` і реагує явно.

**Процес:**
1. Викликати `browser_snapshot`. Якщо діалог блокує сторінку, він з’явиться у `pending_dialogs: [{"id": "d-1", "type": "alert", "message": "..."}]`.
2. Викликати `browser_dialog(action="accept")` або `browser_dialog(action="dismiss")`. Для діалогів `prompt()` передай `prompt_text="..."`, щоб надати відповідь.
3. Знову зробити знімок — `pending_dialogs` буде порожнім; JS‑потік сторінки відновився.

**Виявлення відбувається автоматично** через постійний CDP‑супервізор — один WebSocket на задачу, який підписується на події Page/Runtime/Target. Супервізор також заповнює поле `frame_tree` у знімку, щоб агент бачив структуру iframe поточної сторінки, включаючи крос‑оригінальні (OOPIF) iframe.

**Матриця доступності:**

| Backend | Виявлення через `pending_dialogs` | Відповідь (`browser_dialog`) |
|---|---|---|
| Local Chrome via `/browser connect` або `browser.cdp_url` | ✓ | ✓ повний workflow |
| Browserbase | ✓ | ✓ повний workflow (через ін’єкований XHR‑мост) |
| Camofox / default local agent‑browser | ✗ | ✗ (немає CDP‑endpoint) |

**Як це працює на Browserbase.** Проксі CDP Browserbase автоматично відхиляє реальні нативні діалоги на сервері за ~10 мс, тому ми не можемо використовувати `Page.handleJavaScriptDialog`. Супервізор ін’єкціює невеликий скрипт через `Page.addScriptToEvaluateOnNewDocument`, який переопреділяє `window.alert`/`confirm`/`prompt` синхронним XHR. Ми перехоплюємо ці XHR через `Fetch.enable` — JS‑потік сторінки залишається заблокованим, доки не викличемо `Fetch.fulfillRequest` з відповіддю агента. Повернені значення `prompt()` проходять назад у JS без змін.

**Політика діалогів** налаштовується у `config.yaml` під `browser.dialog_policy`:

| Політика | Поведінка |
|--------|----------|
| `must_respond` (за замовчуванням) | Захоплює, показує у знімку, чекає явного виклику `browser_dialog()`. Авто‑відхилення після `browser.dialog_timeout_s` (за замовчуванням 300 s), щоб баганий агент не зависав назавжди. |
| `auto_dismiss` | Захоплює, відхиляє одразу. Агент все ще бачить діалог у історії `browser_state`, але не повинен діяти. |
| `auto_accept` | Захоплює, приймає одразу. Корисно при навігації сторінок з агресивними `beforeunload`‑підказками. |

**Дерево кадрів** у `browser_snapshot.frame_tree` обмежене 30 кадрами та глибиною OOPIF 2, щоб не перевантажувати корисне навантаження на сторінках з великою кількістю реклами. Прапорець `truncated: true` з’являється, коли обмеження досягнуті; агенти, яким потрібне повне дерево, можуть скористатися `browser_cdp` з `Page.getFrameTree`.
## Практичні приклади

### Заповнення веб‑форми

```
User: Sign up for an account on example.com with my email john@example.com

Agent workflow:
1. browser_navigate("https://example.com/signup")
2. browser_snapshot()  → sees form fields with refs
3. browser_type(ref="@e3", text="john@example.com")
4. browser_type(ref="@e5", text="SecurePass123")
5. browser_click(ref="@e8")  → clicks "Create Account"
6. browser_snapshot()  → confirms success
```

### Дослідження динамічного контенту

```
User: What are the top trending repos on GitHub right now?

Agent workflow:
1. browser_navigate("https://github.com/trending")
2. browser_snapshot(full=true)  → reads trending repo list
3. Returns formatted results
```
## Запис сесії

Автоматично записувати браузерні сесії у відеофайли формату WebM:

```yaml
browser:
  record_sessions: true  # default: false
```

Коли ввімкнено, запис починається автоматично під час першого `browser_navigate` і зберігається у `~/.hermes/browser_recordings/` після закриття сесії. Працює як у локальному, так і у хмарному (Browserbase) режимах. Записи старші 72 години автоматично видаляються.
## Функції Stealth

Browserbase provides automatic stealth capabilities:

| Функція | За замовчуванням | Примітки |
|---------|-------------------|----------|
| Basic Stealth | Завжди увімкнено | Випадкові відбитки, рандомізація viewport, розв’язання CAPTCHA |
| Residential Proxies | Увімкнено | Маршрутизація через резидентські IP для кращого доступу |
| Advanced Stealth | Вимкнено | Кастомна збірка Chromium, потрібен план Scale |
| Keep Alive | Увімкнено | Перепідключення сесії після мережевих збоїв |

:::note
Якщо платні функції недоступні у твоєму плані, Hermes автоматично переходить до **запасного (варіанту)** — спочатку вимикає `keepAlive`, потім проксі — щоб браузинг все одно працював на безкоштовних планах.
:::
## Управління сесіями

- Кожне завдання отримує ізольовану сесію браузера через Browserbase
- Сесії автоматично видаляються після бездіяльності (за замовчуванням: 2 хв)
- Фоновий потік перевіряє кожні 30 секунд наявність застарілих сесій
- Аварійне очищення виконується під час завершення процесу, щоб запобігти осиротілим сесіям
- Сесії звільняються через API Browserbase (`REQUEST_RELEASE` статус)
## Обмеження

- **Text-based interaction** — покладається на дерево доступності, а не на координати пікселів
- **Snapshot size** — великі сторінки можуть бути обрізані або підсумовані LLM до 8000 символів
- **Session timeout** — хмарні сесії завершуються згідно налаштувань плану твого провайдера
- **Cost** — хмарні сесії споживають кредити провайдера; сесії автоматично очищуються, коли розмова закінчується або після бездіяльності. Використовуй `/browser connect` для безкоштовного локального перегляду.
- **No file downloads** — неможливо завантажувати файли з браузера