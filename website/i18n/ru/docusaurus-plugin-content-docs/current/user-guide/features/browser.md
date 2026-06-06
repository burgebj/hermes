---
title: Автоматизация браузера
description: Управляй браузерами с несколькими provider, локальными браузерами семейства Chromium через CDP или облачными браузерами для веб‑взаимодействия, заполнения форм, скрапинга и прочего.
sidebar_label: Browser
sidebar_position: 5
---

# Автоматизация браузера

Hermes Agent включает полный набор инструментов для автоматизации браузера с несколькими вариантами бэкенда:

- **Browserbase cloud mode** через [Browserbase](https://browserbase.com) для управляемых облачных браузеров и средств против ботов
- **Browser Use cloud mode** через [Browser Use](https://browser-use.com) как альтернативного поставщика облачных браузеров
- **Firecrawl cloud mode** через [Firecrawl](https://firecrawl.dev) для облачных браузеров со встроенным скрапингом
- **Camofox local mode** через [Camofox](https://github.com/jo-inc/camofox-browser) для локального антидетекционного браузинга (подделка отпечатка на базе Firefox)
- **Local Chromium-family CDP** — подключай инструменты браузера к своему Chrome, Brave, Chromium или Edge с помощью `/browser connect`
- **Local browser mode** через CLI `agent-browser` и локальную установку Chromium

Во всех режимах агент может перемещаться по веб‑сайтам, взаимодействовать с элементами страниц, заполнять формы и извлекать информацию.
## Обзор

Страницы представлены в виде **деревьев доступности** (текстовых снимков), что делает их идеальными для LLM‑агентов. Интерактивные элементы получают ref‑идентификаторы (например `@e1`, `@e2`), которые агент использует для кликов и ввода текста.

**Ключевые возможности**

- **Мультипровайдерное облачное выполнение** — Browserbase, Browser Use или Firecrawl — без необходимости локального браузера
- **Локальная интеграция с семейством Chromium** — подключение к запущенному Chrome, Brave, Chromium или Edge через CDP для интерактивного браузинга
- **Встроенный стелс‑режим** — случайные отпечатки, решение CAPTCHA, резидентные прокси (Browserbase)
- **Изоляция сессий** — каждая задача получает собственную браузерную сессию
- **Автоматическая очистка** — неактивные сессии закрываются после тайм‑аута
- **Визуальный анализ** — скриншот + AI‑анализ для понимания визуального контента
## Настройка

:::tip Nous Subscribers
Если у тебя есть платная подписка [Nous Portal](https://portal.nousresearch.com), ты можешь использовать автоматизацию браузера через **[Tool Gateway](tool-gateway.md)** без каких‑либо отдельных API‑ключей. При новой установке можно выполнить `hermes setup --portal`, чтобы войти в систему и включить все инструменты шлюза сразу; при существующей установке можно выбрать **Nous Subscription** в качестве провайдера браузера через `hermes model` или `hermes tools`.
:::

### Browserbase cloud mode

Чтобы использовать управляемые Browserbase облачные браузеры, добавь:

```bash
# Add to ~/.hermes/.env
BROWSERBASE_API_KEY=***
BROWSERBASE_PROJECT_ID=your-project-id-here
```

Получить учётные данные можно на [browserbase.com](https://browserbase.com).

### Browser Use cloud mode

Чтобы использовать Browser Use в качестве облачного провайдера браузера, добавь:

```bash
# Add to ~/.hermes/.env
BROWSER_USE_API_KEY=***
```

Получить API‑ключ можно на [browser-use.com](https://browser-use.com). Browser Use предоставляет облачный браузер через свой REST API. Если заданы учётные данные как для Browserbase, так и для Browser Use, приоритет будет у Browserbase.

### Firecrawl cloud mode

Чтобы использовать Firecrawl в качестве облачного провайдера браузера, добавь:

```bash
# Add to ~/.hermes/.env
FIRECRAWL_API_KEY=fc-***
```

Получить API‑ключ можно на [firecrawl.dev](https://firecrawl.dev). Затем выбери Firecrawl в качестве провайдера браузера:

```bash
hermes setup tools
# → Browser Automation → Firecrawl
```

Дополнительные настройки:

```bash
# Self-hosted Firecrawl instance (default: https://api.firecrawl.dev)
FIRECRAWL_API_URL=http://localhost:3002

# Session TTL in seconds (default: 300)
FIRECRAWL_BROWSER_TTL=600
```

### Гибридный роутинг: облако для публичных URL, локально для LAN/localhost

Когда настроен облачный провайдер, Hermes автоматически запускает **локальный Chromium sidecar** для URL‑ов, которые разрешаются в частный/loopback/LAN‑адрес (`localhost`, `127.0.0.1`, `192.168.x.x`, `10.x.x.x`, `172.16-31.x.x`, `*.local`, `*.lan`, `*.internal`, IPv6 loopback `::1`, link‑local `169.254.x.x`). Публичные URL продолжают использовать облачного провайдера в том же разговоре.

Это решает типичный рабочий процесс «я разрабатываю локально, но использую Browserbase» — агент может сделать скриншот твоей панели по `http://localhost:3000` И собрать `https://github.com` без переключения провайдеров или отключения защиты SSRF. Облачный провайдер никогда не видит частный URL.

Функция **включена по умолчанию**. Чтобы отключить её (все URL идут к настроенному облачному провайдеру, как раньше):

```yaml
# ~/.hermes/config.yaml
browser:
  cloud_provider: browserbase
  auto_local_for_private_urls: false
```

При отключённом авто‑роутинге частные URL отклоняются с сообщением
`"Blocked: URL targets a private or internal address"` unless you also set `browser.allow_private_urls: true` (что позволяет облачному провайдеру попытаться их открыть — обычно не сработает, так как Browserbase и др. не могут достичь твоей LAN).

Требования: локальный sidecar использует тот же CLI `agent-browser`, что и в чистом локальном режиме, поэтому его нужно установить (`hermes setup tools → Browser Automation` установит его автоматически). Перенаправления после навигации с публичного URL на частный адрес всё равно блокируются (нельзя использовать трюк с redirect‑to‑internal, чтобы попасть в LAN через публичный путь).

### Camofox local mode

[Camofox](https://github.com/jo-inc/camofox-browser) — это самохостинг‑сервер Node.js, оборачивающий Camoufox (форк Firefox с C++ подделкой отпечатка). Он обеспечивает локальный анти‑детекшн браузинг без облачных зависимостей.

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

`make up` сразу запускает контейнер по умолчанию. Если нужны пользовательские параметры среды, такие как больший heap Node, VNC или постоянный каталог профиля, сначала собери образ, а затем запусти его самостоятельно:

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

С включённым VNC браузер работает в headed‑режиме и его можно наблюдать в реальном времени в браузере по `http://localhost:6080` (noVNC). Также можно подключить нативный VNC‑клиент к `localhost:5901`.

Если ты уже запустил `make up`, останови и удали этот контейнер по умолчанию перед запуском кастомного:

```bash
make down
# then run the custom docker run command above
```

Затем укажи в `~/.hermes/.env`:

```bash
CAMOFOX_URL=http://localhost:9377
```

Если Camofox работает в Docker и ты хочешь, чтобы он открывал веб‑приложения, обслуживаемые хост‑машиной, включи переписывание loopback. `CAMOFOX_URL` всё равно должен указывать на опубликованный контролирующий API хоста, но URL‑ы страниц вроде `http://127.0.0.1:3000` нужно открывать из контейнера как `http://host.docker.internal:3000`:

```yaml
# ~/.hermes/config.yaml
browser:
  camofox:
    rewrite_loopback_urls: true
    loopback_host_alias: host.docker.internal  # default; use a LAN IP if needed
```

Эквивалентные переменные окружения:

```bash
CAMOFOX_REWRITE_LOOPBACK_URLS=true
CAMOFOX_LOOPBACK_HOST_ALIAS=host.docker.internal
```

Переписывание применяется только к URL‑ам навигации страниц с loopback‑хостами (`localhost`, `127.0.0.1`, `::1`). Оно не меняет `CAMOFOX_URL`. Оставляй его отключённым для установок Camofox вне Docker, где браузер уже работает на хосте и loopback‑URL корректны.

Или настрой через `hermes tools` → Browser Automation → Camofox.

Когда `CAMOFOX_URL` установлен, все инструменты браузера автоматически маршрутизируются через Camofox вместо Browserbase или `agent-browser`.

#### Постоянные сессии браузера

По умолчанию каждая сессия Camofox получает случайную идентичность — куки и входы не сохраняются между перезапусками агента. Чтобы включить постоянные сессии браузера, добавь следующее в `~/.hermes/config.yaml`:

```yaml
browser:
  camofox:
    managed_persistence: true
```

Затем полностью перезапусти Hermes, чтобы новая конфигурация была применена.

:::warning Nested path matters
Hermes читает `browser.camofox.managed_persistence`, **не** верхнеуровневый `managed_persistence`. Частая ошибка — написать:

```yaml
# ❌ Wrong — Hermes ignores this
managed_persistence: true
```

Если флаг помещён не по тому пути, Hermes тихо переходит к случайному эфемерному `userId`, и состояние входа будет теряться в каждой сессии.
:::

##### Что делает Hermes
- Отправляет детерминированный профиль‑скоупный `userId` в Camofox, чтобы сервер мог переиспользовать тот же профиль Firefox между сессиями.
- Пропускает уничтожение контекста на сервере при очистке, поэтому куки и входы сохраняются между задачами агента.
- Привязывает `userId` к активному профилю Hermes, так что разные профили Hermes получают разные профили браузера (изоляция профилей).

##### Что Hermes НЕ делает
- Он не принуждает сервер Camofox к постоянству. Hermes лишь отправляет стабильный `userId`; сервер должен уважать его, сопоставляя `userId` с постоянным каталогом профиля Firefox.
- Если твоя сборка Camofox создаёт каждый запрос как эфемерный (например, всегда вызывает `browser.newContext()` без загрузки сохранённого профиля), Hermes не сможет сделать эти сессии постоянными. Убедись, что ты используешь сборку Camofox, реализующую постоянство профилей на основе `userId`.

##### Проверка работы

1. Запусти Hermes и сервер Camofox.
2. Открой Google (или любой сайт входа) в задаче браузера и войди вручную.
3. Заверши задачу браузера обычным способом.
4. Запусти новую задачу браузера.
5. Открой тот же сайт снова — ты должен оставаться вошедшим.

Если на шаге 5 происходит выход, сервер Camofox не учитывает стабильный `userId`. Проверь путь конфигурации, убедись, что полностью перезапустил Hermes после изменения `config.yaml`, и убедись, что версия сервера Camofox поддерживает постоянные профили per‑user.

##### Где хранится состояние

Hermes получает стабильный `userId` из каталога, привязанного к профилю `~/.hermes/browser_auth/camofox/` (или эквивалентного под `$HERMES_HOME` для нестандартных профилей). Сами данные профиля браузера находятся на стороне сервера Camofox, ключом является этот `userId`. Чтобы полностью сбросить постоянный профиль, очисти его на сервере Camofox и удали соответствующий каталог состояния профиля Hermes.

#### Внешне управляемые сессии Camofox

Когда другое приложение управляет видимым браузером Camofox (настольный помощник, кастомная интеграция, другой агент), настрой Hermes работать внутри той же идентичности вместо создания собственного изолированного профиля.

Три параметра управляют поведением:

| Setting | Env var | Effect |
|---------|---------|--------|
| `browser.camofox.user_id` | `CAMOFOX_USER_ID` | `userId` Camofox, который Hermes использует при создании вкладок. Установка переводит сессию в режим «внешне управляемый». |
| `browser.camofox.session_key` | `CAMOFOX_SESSION_KEY` | `sessionKey` (aka `listItemId`), отправляемый при создании вкладки. Используется для сопоставления существующей вкладки при адопции. По умолчанию генерируется значение per‑task, если не задано. |
| `browser.camofox.adopt_existing_tab` | `CAMOFOX_ADOPT_EXISTING_TAB` | При `true` Hermes делает `GET /tabs?userId=<user_id>` при первом использовании и переиспользует существующую вкладку вместо создания новой. |

Переменные окружения имеют приоритет над `config.yaml`. Оба способа работают:

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

**Что меняется, когда установлен `user_id`:**

- Hermes пропускает разрушительную очистку в конце задачи (аналог `managed_persistence: true`). Вкладка/куки/профиль другого приложения сохраняются.
- Hermes **не** вызывает `DELETE /sessions/<user_id>` — этот эндпоинт стирает все данные пользователя, что уничтожило бы сессию внешнего приложения.

**Как работает адопция вкладки (при `adopt_existing_tab: true`):**

1. При первом вызове инструмента браузера после старта процесса Hermes делает `GET /tabs?userId=<user_id>` (таймаут 5 сек).
2. Если в ответе есть вкладка с `listItemId == session_key`, Hermes принимает наиболее недавно созданную в этой группе.
3. Иначе Hermes принимает наиболее недавно созданную вкладку для данного пользователя (любой `listItemId`).
4. Если вкладок нет или запрос не удался, Hermes переходит к созданию новой вкладки при следующей операции.

Адопция происходит только до тех пор, пока `tab_id` не заполнен для сессии. Если внешнее приложение закроет принятые вкладки в середине выполнения, следующий вызов инструмента браузера выдаст ошибку Camofox — Hermes не будет повторно опрашивать свежую вкладку каждый раз.

**Выбор `session_key`:** если нужно, чтобы Hermes надёжно присоединился к *конкретной* существующей вкладке, задай `session_key` равным `listItemId`, использованному внешним приложением при её создании. Если оставить `session_key` пустым и задать только `user_id`, Hermes генерирует `session_key` per‑task (`task_<id>`) — Hermes будет делить куки и профиль с внешним приложением, но откроет свою вкладку рядом, а не переиспользует существующую.

**Замечание о конкуренции:** внешнее приложение и Hermes могут одновременно работать с одним `userId`, но Camofox не координирует фокус вкладок между клиентами. Согласовывайте владение на уровне приложения (например, внешнее приложение ставит на паузу, пока работает Hermes).

#### VNC живой просмотр

Когда Camofox работает в headed‑режиме (с видимым окном браузера), он возвращает VNC‑порт в ответе health‑check. Hermes автоматически обнаруживает его и включает VNC‑URL в ответы навигации, чтобы агент мог поделиться ссылкой для живого просмотра браузера.

### Локальный браузер семейства Chromium через CDP (`/browser connect`)

Вместо облачного провайдера ты можешь подключить инструменты браузера Hermes к своему запущенному Chrome, Brave, Chromium или Edge через Chrome DevTools Protocol (CDP). Это удобно, когда хочется видеть действия агента в реальном времени, взаимодействовать со страницами, требующими твоих куков/сессий, или избежать расходов на облачные браузеры.

:::note
`/browser connect` — это **интерактивная CLI‑команда со слешем** — её не обрабатывает шлюз. Если попытаться выполнить её в WebUI, Telegram, Discord или другом чат‑шлюзе, сообщение будет отправлено агенту как обычный текст и команда не выполнится. Запусти Hermes из терминала (`hermes` или `hermes chat`) и введи `/browser connect` там.
:::

В CLI используй:

```
/browser connect                 # Auto-launch/connect to a local Chromium-family browser at http://127.0.0.1:9222
/browser connect ws://host:port  # Connect to a specific CDP endpoint
/browser status                  # Check current connection
/browser disconnect              # Detach and return to cloud/local mode
```

Если браузер ещё не запущен с удалённой отладкой, Hermes попытается автоматически запустить поддерживаемый браузер семейства Chromium с `--remote-debugging-port=9222`. Обнаруживаются Brave, Google Chrome, Chromium и Microsoft Edge, с типичными путями установки в Linux, например `/opt/brave-bin/brave` и `/snap/bin/brave`.

:::tip
Чтобы вручную запустить браузер семейства Chromium с включённым CDP, используй отдельный `--user-data-dir`, чтобы порт отладки действительно открылся, даже если браузер уже запущен с твоим обычным профилем:

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

Затем запусти CLI Hermes и выполни `/browser connect`.

**Зачем `--user-data-dir`?** Без него запуск Chromium, когда уже работает обычный экземпляр, обычно открывает новое окно в существующем процессе — а тот процесс не был запущен с `--remote-debugging-port`, поэтому порт 9222 не открывается. Отдельный `--user-data-dir` заставляет запустить свежий процесс браузера, где порт отладки действительно слушает. Параметры `--no-first-run --no-default-browser-check` пропускают мастер‑настройку первого запуска для нового профиля.
:::

После подключения через CDP все инструменты браузера (`browser_navigate`, `browser_click` и др.) работают на твоём живом браузере вместо создания облачной сессии.

### WSL2 + Windows Chrome: предпочтительнее MCP, а не `/browser connect`

Если Hermes работает внутри WSL2, а окно Chrome, которым ты хочешь управлять, запущено на Windows‑хосте, `/browser connect` часто не лучший путь.

Почему:

- `/browser connect` требует, чтобы сам Hermes мог достучаться до CDP‑эндпоинта.
- Современные сессии живой отладки Chrome часто выставляют локальный хост‑эндпоинт, который из WSL недоступен так же, как классический порт `9222`.
- Даже когда Windows Chrome отлаживаем, более чистая интеграция обычно достигается через сервер MCP на стороне Windows, к которому Hermes подключается.

Для такой схемы предпочтительнее `chrome-devtools-mcp` через поддержку MCP в Hermes.

См. руководство по MCP для практической настройки:

- [Use MCP with Hermes](../../guides/use-mcp-with-hermes.md#wsl2-bridge-hermes-in-wsl-to-windows-chrome)

### Локальный режим браузера

Если ты **не** задаёшь облачные учётные данные и не используешь `/browser connect`, Hermes всё равно может использовать инструменты браузера через локальную установку Chromium, управляемую `agent-browser`.

### Опциональные переменные окружения

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

### Установка CLI agent-browser

```bash
npm install -g agent-browser
# Or install locally in the repo:
npm install
```

:::info
Набор инструментов `browser` должен быть включён в список `toolsets` твоей конфигурации или активирован через `hermes config set toolsets '["hermes-cli", "browser"]'`.
:::
## Доступные инструменты

### `browser_navigate`

Переход к URL. Должен быть вызван до любого другого инструмента браузера. Инициализирует сессию Browserbase.

```
Navigate to https://github.com/NousResearch
```

:::tip
Для простого получения информации предпочтительнее использовать `web_search` или `web_extract` — они быстрее и дешевле. Используй инструменты браузера, когда нужно **взаимодействовать** со страницей (кликать кнопки, заполнять формы, работать с динамическим контентом).
:::

### `browser_snapshot`

Получить текстовый снимок текущего дерева доступности страницы. Возвращает интерактивные элементы с ref‑ID, например `@e1`, `@e2`, для использования с `browser_click` и `browser_type`.

- **`full=false`** (по умолчанию): компактный вид, показывающий только интерактивные элементы
- **`full=true`**: полное содержимое страницы

Снимки более 8000 символов автоматически суммируются LLM.

### `browser_click`

Клик по элементу, идентифицированному его ref‑ID из снимка.

```
Click @e5 to press the "Sign In" button
```

### `browser_type`

Ввод текста в поле ввода. Сначала очищает поле, затем вводит новый текст.

```
Type "hermes agent" into the search field @e3
```

### `browser_scroll`

Прокрутка страницы вверх или вниз для отображения дополнительного контента.

```
Scroll down to see more results
```

### `browser_press`

Нажатие клавиши клавиатуры. Полезно для отправки форм или навигации.

```
Press Enter to submit the form
```

Поддерживаемые клавиши: `Enter`, `Tab`, `Escape`, `ArrowDown`, `ArrowUp` и другие.

### `browser_back`

Возврат к предыдущей странице в истории браузера.

### `browser_get_images`

Список всех изображений на текущей странице с их URL и alt‑текстом. Полезно для поиска изображений для анализа.

### `browser_vision`

Сделать скриншот и проанализировать его с помощью vision AI. Используй, когда текстовые снимки не передают важную визуальную информацию — особенно полезно для CAPTCHA, сложных макетов или задач визуальной верификации.

Скриншот сохраняется постоянно, а путь к файлу возвращается вместе с результатом AI‑анализа. На платформах обмена сообщениями (Telegram, Discord, Slack, WhatsApp) можно попросить агента поделиться скриншотом — он будет отправлен как нативное фото‑вложение через механизм `MEDIA:`.

```
What does the chart on this page show?
```

Скриншоты хранятся в `~/.hermes/cache/screenshots/` и автоматически удаляются через 24 часа.

### `browser_console`

Получить вывод консоли браузера (сообщения `log`/`warn`/`error`) и непойманные исключения JavaScript с текущей страницы. Необходимо для обнаружения тихих JS‑ошибок, которые не попадают в дерево доступности.

```
Check the browser console for any JavaScript errors
```

Используй `clear=True`, чтобы очистить консоль после чтения, тогда последующие вызовы покажут только новые сообщения.

`browser_console` также выполняет JavaScript, если вызвать его с аргументом `expression` — форма аналогична консоли DevTools, результат возвращается разобранным (JSON‑сериализованные объекты становятся `dict`, примитивные значения остаются примитивами).

```
browser_console(expression="document.querySelector('h1').textContent")
browser_console(expression="JSON.stringify(performance.timing)")
```

Когда для текущей сессии активен CDP‑supervisor (обычно для любой сессии, где был выполнен `browser_navigate` к CDP‑совместимому бэкенду), оценка происходит через постоянный WebSocket супервизора — без затрат на запуск подпроцесса. В остальных случаях используется стандартный путь CLI агент‑браузер. Поведение идентично, меняется только задержка.

### `browser_cdp`

Прямой проход Chrome DevTools Protocol — «выход» для операций браузера, не покрытых другими инструментами. Используется для работы с нативными диалогами, оценкой в iframe, управлением cookie/сетевыми запросами или любой другой CDP‑командой, необходимой агенту.

**Доступно только когда CDP‑endpoint достижим при старте сессии** — то есть `/browser connect` подключён к запущенному Chrome, Brave, Chromium или Edge, либо `browser.cdp_url` указан в `config.yaml`. Стандартный локальный режим агент‑браузер, Camofox и облачные провайдеры (Browserbase, Browser Use, Firecrawl) в текущий момент не раскрывают CDP этому инструменту — у облачных провайдеров есть CDP‑URL per‑session, но маршрутизация живой сессии пока в разработке.

**Справочник методов CDP:** https://chromedevtools.github.io/devtools-protocol/ — агент может `web_extract` страницу конкретного метода, чтобы посмотреть параметры и форму возвращаемого значения.

Типичные шаблоны:

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

Методы уровня браузера (`Target.*`, `Browser.*`, `Storage.*`) не требуют `target_id`. Методы уровня страницы (`Page.*`, `Runtime.*`, `DOM.*`, `Emulation.*`) требуют `target_id`, полученный из `Target.getTargets`. Каждый безсостояний вызов независим — сессии не сохраняются между вызовами.

**Кросс‑origin iframe:** передай `frame_id` (из `browser_snapshot.frame_tree.children[]`, где `is_oopif=true`), чтобы направить CDP‑вызов через живую сессию супервизора для этого iframe. Так работает `Runtime.evaluate` внутри кросс‑origin iframe на Browserbase, где безсостояные CDP‑соединения сталкивались бы с истечением срока подписанного URL. Пример:

```
browser_cdp(
  method="Runtime.evaluate",
  params={"expression": "document.title", "returnByValue": True},
  frame_id="<frame_id from browser_snapshot>",
)
```

Iframe того же происхождения `frame_id` не нужен — используй `document.querySelector('iframe').contentDocument` из верхнего `Runtime.evaluate`.

### `browser_dialog`

Ответ на нативный JS‑диалог (`alert` / `confirm` / `prompt` / `beforeunload`). До появления этого инструмента диалоги молча блокировали поток JavaScript страницы, и последующие вызовы `browser_*` зависали или бросали ошибки; теперь агент видит ожидающие диалоги в выводе `browser_snapshot` и может явно на них реагировать.

**Рабочий процесс:**
1. Вызови `browser_snapshot`. Если диалог блокирует страницу, он появится как `pending_dialogs: [{"id": "d-1", "type": "alert", "message": "..."}]`.
2. Вызови `browser_dialog(action="accept")` или `browser_dialog(action="dismiss")`. Для диалогов `prompt()` передай `prompt_text="..."`, чтобы задать ответ.
3. Сделай новый снимок — `pending_dialogs` будет пустым; поток JS страницы возобновится.

**Обнаружение происходит автоматически** через постоянный CDP‑supervisor — один WebSocket на задачу, подписанный на события Page/Runtime/Target. Супервизор также заполняет поле `frame_tree` в снимке, чтобы агент видел структуру iframe текущей страницы, включая кросс‑origin (OOPIF) iframe.

**Матрица доступности:**

| Бэкенд | Обнаружение через `pending_dialogs` | Ответ (`browser_dialog`) |
|---|---|---|
| Локальный Chrome через `/browser connect` или `browser.cdp_url` | ✓ | ✓ полный рабочий процесс |
| Browserbase | ✓ | ✓ полный рабочий процесс (через внедрённый XHR‑мост) |
| Camofox / стандартный локальный агент‑браузер | ✗ | ✗ (нет CDP‑endpoint) |

**Как работает на Browserbase.** Прокси CDP Browserbase автоматически отклоняет реальные нативные диалоги на сервере за ~10 мс, поэтому мы не можем использовать `Page.handleJavaScriptDialog`. Супервизор внедряет небольшой скрипт через `Page.addScriptToEvaluateOnNewDocument`, переопределяющий `window.alert`/`confirm`/`prompt` синхронным XHR. Мы перехватываем эти XHR через `Fetch.enable` — поток JS страницы остаётся заблокированным до вызова `Fetch.fulfillRequest` с ответом агента. Возврат значений `prompt()` проходит обратно в JS без изменений.

**Политика диалогов** задаётся в `config.yaml` под `browser.dialog_policy`:

| Политика | Поведение |
|--------|----------|
| `must_respond` (по умолчанию) | Захват, отображение в снимке, ожидание явного вызова `browser_dialog()`. Авто‑отклонение после `browser.dialog_timeout_s` (по умолчанию 300 с), чтобы баговый агент не мог зависнуть бесконечно. |
| `auto_dismiss` | Захват, мгновенное отклонение. Агент всё равно видит диалог в истории `browser_state`, но не обязан действовать. |
| `auto_accept` | Захват, мгновенное принятие. Полезно при навигации по страницам с агрессивными `beforeunload`‑промптами. |

**Дерево фреймов** в `browser_snapshot.frame_tree` ограничено 30 фреймами и глубиной OOPIF 2, чтобы ограничить размер полезной нагрузки на страницах с множеством рекламных элементов. Флаг `truncated: true` появляется, когда ограничения достигнуты; агент, нуждающийся в полном дереве, может воспользоваться `browser_cdp` с `Page.getFrameTree`.
## Практические примеры

### Заполнение веб‑формы

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

### Исследование динамического контента

```
User: What are the top trending repos on GitHub right now?

Agent workflow:
1. browser_navigate("https://github.com/trending")
2. browser_snapshot(full=true)  → reads trending repo list
3. Returns formatted results
```
## Запись сессии

Автоматически записывать браузерные сессии в виде файлов WebM:

```yaml
browser:
  record_sessions: true  # default: false
```

Когда включено, запись начинается автоматически при первом `browser_navigate` и сохраняется в `~/.hermes/browser_recordings/` при закрытии сессии. Работает как в локальном, так и в облачном (Browserbase) режимах. Записи старше 72 часов автоматически удаляются.
## Функции скрытности

Browserbase предоставляет автоматические возможности скрытности:

| Функция | По умолчанию | Примечания |
|---------|--------------|------------|
| Базовая скрытность | Всегда включено | Случайные отпечатки, рандомизация области просмотра, решение CAPTCHA |
| Резидентные прокси | Включено | Маршрутизация через резидентные IP для лучшего доступа |
| Продвинутая скрытность | Выключено | Пользовательская сборка Chromium, требуется план Scale |
| Keep Alive | Включено | Восстановление сессии после сетевых сбоев |

:::note
Если платные функции недоступны в твоём плане, Hermes автоматически переходит к запасному варианту — сначала отключая `keepAlive`, затем прокси — так что браузинг всё равно работает в бесплатных планах.
:::
## Управление сессиями

- Каждая задача получает изолированную браузерную сессию через Browserbase
- Сессии автоматически удаляются после бездействия (по умолчанию — 2 минуты)
- Фоновый поток каждые 30 секунд проверяет наличие устаревших сессий
- При аварийном завершении процесса запускается очистка, чтобы предотвратить оставшиеся сессии
- Сессии освобождаются через API Browserbase (`REQUEST_RELEASE` status)
## Ограничения

- **Text-based interaction** — опирается на дерево доступности, а не на координаты пикселей
- **Snapshot size** — большие страницы могут быть усечены или суммированы LLM при 8000 символах
- **Session timeout** — облачные сессии истекают в соответствии с настройками плана твоего провайдера
- **Cost** — облачные сессии потребляют кредиты провайдера; сессии автоматически удаляются после завершения разговора или после простоя. Используй `/browser connect` для бесплатного локального просмотра.
- **No file downloads** — невозможно загружать файлы из браузера