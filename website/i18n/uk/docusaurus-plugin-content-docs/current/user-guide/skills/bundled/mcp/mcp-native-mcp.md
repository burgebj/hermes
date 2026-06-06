---
title: "Native Mcp — клієнт MCP: підключати сервери, реєструвати інструменти (stdio/HTTP)"
sidebar_label: "Native Mcp"
description: "MCP клієнт: підключати сервери, реєструвати інструменти (stdio/HTTP)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Рідний MCP

Клієнт MCP: підключає сервери, реєструє інструменти (stdio/HTTP).
## Метадані навички

| | |
|---|---|
| Джерело | Bundled (installed by default) |
| Шлях | `skills/mcp/native-mcp` |
| Версія | `1.0.0` |
| Автор | Hermes Agent |
| Ліцензія | MIT |
| Платформи | linux, macos, windows |
| Теги | `MCP`, `Tools`, `Integrations` |
| Пов’язані навички | [`mcporter`](/docs/user-guide/skills/optional/mcp/mcp-mcporter) |
:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Вбудований MCP‑клієнт

Hermes Agent має вбудований MCP‑клієнт, який під час запуску підключається до серверів MCP, виявляє їхні інструменти та робить їх доступними як інструменти першого рівня, які агент може викликати безпосередньо. Не потрібен проміжний CLI — інструменти з серверів MCP з’являються поряд із вбудованими інструментами, такими як `terminal`, `read_file` тощо.
## Коли використовувати

Використовуй це, коли потрібно:
- Підключитися до серверів MCP і використовувати їх інструменти з Hermes Agent
- Додати зовнішні можливості (доступ до файлової системи, GitHub, бази даних, API) через MCP
- Запускати локальні stdio‑базовані сервери MCP (npx, uvx або будь‑яка команда)
- Підключатися до віддалених HTTP/StreamableHTTP серверів MCP
- Мати інструменти MCP, які автоматично виявляються та доступні в кожній сесії

Для одноразових викликів інструментів MCP з терміналу без налаштувань дивись навичку `mcporter`.
## Передумови

- **mcp Python package** — необов’язкова залежність; встановіть за допомогою `pip install mcp`. Якщо не встановлено, підтримка MCP буде тихо вимкнено.
- **Node.js** — необхідний для серверів MCP на базі `npx` (більшість серверів спільноти)
- **uv** — необхідний для серверів MCP на базі `uvx` (сервери на Python)

Встановіть MCP SDK:

```bash
pip install mcp
# or, if using uv:
uv pip install mcp
```
## Швидкий старт

Додай сервери MCP у `~/.hermes/config.yaml` під ключем `mcp_servers`:

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]
```

Перезапусти Hermes Agent. При запуску він:
1. Під’єднається до сервера
2. Виявить доступні інструменти
3. Зареєструє їх з префіксом `mcp_time_*`
4. Вставить їх у всі інструментальні набори платформи

Тепер ти можеш користуватися інструментами природно — просто попроси агента отримати поточний час.
## Довідник конфігурації

Кожен запис у `mcp_servers` — це назва сервера, що відповідає його конфігурації. Існує два типи транспорту: **stdio** (на основі команди) та **HTTP** (на основі URL).

### Транспорт Stdio (команда + аргументи)

```yaml
mcp_servers:
  server_name:
    command: "npx"             # (required) executable to run
    args: ["-y", "pkg-name"]   # (optional) command arguments, default: []
    env:                       # (optional) environment variables for the subprocess
      SOME_API_KEY: "value"
    timeout: 120               # (optional) per-tool-call timeout in seconds, default: 120
    connect_timeout: 60        # (optional) initial connection timeout in seconds, default: 60
```

### Транспорт HTTP (URL)

```yaml
mcp_servers:
  server_name:
    url: "https://my-server.example.com/mcp"   # (required) server URL
    headers:                                     # (optional) HTTP headers
      Authorization: "Bearer sk-..."
    timeout: 180               # (optional) per-tool-call timeout in seconds, default: 120
    connect_timeout: 60        # (optional) initial connection timeout in seconds, default: 60
```

### Усі параметри конфігурації

| Option            | Type   | Default | Description                                       |
|-------------------|--------|---------|---------------------------------------------------|
| `command`         | string | --      | Виконуваний файл (транспорт stdio, обов’язково) |
| `args`            | list   | `[]`    | Аргументи, що передаються команді                 |
| `env`             | dict   | `{}`    | Додаткові змінні середовища для підпроцесу        |
| `url`             | string | --      | URL сервера (транспорт HTTP, обов’язково)        |
| `headers`         | dict   | `{}`    | HTTP‑заголовки, що надсилаються з кожним запитом  |
| `timeout`         | int    | `120`   | Тайм‑аут виклику інструмента в секундах            |
| `connect_timeout` | int    | `60`    | Тайм‑аут початкового підключення та виявлення     |

Примітка: конфігурація сервера повинна містити або `command` (stdio), або `url` (HTTP), але не обидва.
## Як це працює

### Виявлення під час запуску

Коли Hermes Agent запускається, під час ініціалізації інструментів викликається `discover_mcp_tools()`:

1. Читає `mcp_servers` з `~/.hermes/config.yaml`
2. Для кожного сервера створює з’єднання у окремому фонoвому циклі подій
3. Ініціалізує сесію MCP і викликає `list_tools()`, щоб виявити доступні інструменти
4. Реєструє кожен інструмент у реєстрі інструментів Hermes

### Конвенція іменування інструментів

Інструменти MCP реєструються за шаблоном імені:

```
mcp_{server_name}_{tool_name}
```

Тире та крапки в іменах замінюються підкресленнями для сумісності з API LLM.

Приклади:
- Сервер `filesystem`, інструмент `read_file` → `mcp_filesystem_read_file`
- Сервер `github`, інструмент `list-issues` → `mcp_github_list_issues`
- Сервер `my-api`, інструмент `fetch.data` → `mcp_my_api_fetch_data`

### Авто‑вставка

Після виявлення інструменти MCP автоматично вставляються у всі набори інструментів платформи `hermes-*` (CLI, Discord, Telegram тощо). Це означає, що інструменти MCP доступні в кожній розмові без додаткових налаштувань.

### Життєвий цикл з’єднання

- Кожен сервер працює як довгоживуче завдання `asyncio` у фоні демона
- З’єднання зберігаються протягом усього часу роботи процесу агента
- Якщо з’єднання розривається, запускається автоматичне повторне підключення з експоненціальним збільшенням інтервалу (до 5 спроб, максимум 60 с затримки)
- При завершенні роботи агента всі з’єднання коректно закриваються

### Ідемпотентність

`discover_mcp_tools()` є ідемпотентною — виклик її кілька разів підключає лише ті сервери, які ще не підключені. Сервери, які не вдалося підключити, будуть повторно спробовані під час наступних викликів.
## Типи транспорту

### Stdio Transport

Найпоширеніший транспорт. Hermes запускає сервер MCP як підпроцес і взаємодіє через `stdin`/`stdout`.

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"]
```

Підпроцес успадковує **відфільтроване** середовище (див. розділ Security нижче) плюс будь‑які змінні, які ти вказав у `env`.

### HTTP / StreamableHTTP Transport

Для віддалених або спільних серверів MCP. Потрібно, щоб пакет `mcp` включав підтримку HTTP‑клієнта (`mcp.client.streamable_http`).

```yaml
mcp_servers:
  remote_api:
    url: "https://mcp.example.com/mcp"
    headers:
      Authorization: "Bearer sk-..."
```

Якщо підтримка HTTP недоступна у встановленій версії `mcp`, сервер завершить роботу з помилкою `ImportError`, а інші сервери продовжать працювати нормально.
## Security

### Фільтрація змінних середовища

Для серверів stdio Hermes НЕ передає твоє повне середовище оболонки підпроцесам MCP. Наслідуються лише безпечні базові змінні:

- `PATH`, `HOME`, `USER`, `LANG`, `LC_ALL`, `TERM`, `SHELL`, `TMPDIR`
- Будь‑які змінні `XDG_*`

Всі інші змінні середовища (API‑ключі, токени, секрети) виключаються, якщо ти явно їх не додаси за допомогою ключа конфігурації `env`. Це запобігає випадковому витоку облікових даних до недовірених серверів MCP.

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      # Only this token is passed to the subprocess
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_..."
```

### Видалення облікових даних у повідомленнях про помилки

Якщо виклик інструменту MCP завершується помилкою, будь‑які шаблони, схожі на облікові дані, у повідомленні про помилку автоматично видаляються перед показом LLM. Це охоплює:

- GitHub PAT (`ghp_...`)
- Ключі у стилі OpenAI (`sk-...`)
- Bearer‑токени
- Загальні шаблони `token=`, `key=`, `API_KEY=`, `password=`, `secret=`
## Усунення неполадок

### «MCP SDK not available -- skipping MCP tool discovery»

Пакет Python `mcp` не встановлений. Встанови його:

```bash
pip install mcp
```

### «No MCP servers configured»

У файлі `~/.hermes/config.yaml` відсутній ключ `mcp_servers` або він порожній. Додай принаймні один сервер.

### «Failed to connect to MCP server 'X'»

Типові причини:
- **Command not found**: Виконавчий файл `command` відсутній у `PATH`. Переконайся, що встановлені `npx`, `uvx` або відповідна команда.
- **Package not found**: Для серверів npx npm‑пакет може не існувати або потребує прапорця `-y` у аргументах для автоматичної інсталяції.
- **Timeout**: Сервер занадто довго запускався. Збільш `connect_timeout`.
- **Port conflict**: Для HTTP‑серверів URL може бути недоступним.

### «MCP server 'X' requires HTTP transport but mcp.client.streamable_http is not available»

Твоя версія пакету `mcp` не містить підтримки HTTP‑клієнта. Онови його:

```bash
pip install --upgrade mcp
```

### Інструменти не з’являються

- Перевір, чи сервер зазначений у `mcp_servers` (а не у `mcp` або `servers`).
- Переконайся, що відступи у YAML правильні.
- Подивись журнали запуску Hermes Agent для повідомлень про підключення.
- Імена інструментів мають префікс `mcp_{server}_{tool}` — шукай цей шаблон.

### З’єднання постійно розривається

Клієнт повторює спроби до 5 разів з експоненціальним збільшенням інтервалу (1 s, 2 s, 4 s, 8 s, 16 s, максимум 60 s). Якщо сервер фундаментально недоступний, після 5‑ї спроби процес припиняє спроби. Перевір процес сервера та мережеве з’єднання.
## Приклади

### Сервер часу (uvx)

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]
```

Реєструє інструменти, такі як `mcp_time_get_current_time`.

### Сервер файлової системи (npx)

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/documents"]
    timeout: 30
```

Реєструє інструменти, такі як `mcp_filesystem_read_file`, `mcp_filesystem_write_file`, `mcp_filesystem_list_directory`.

### Сервер GitHub з автентифікацією

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"
    timeout: 60
```

Реєструє інструменти, такі як `mcp_github_list_issues`, `mcp_github_create_pull_request` тощо.

### Віддалений HTTP‑сервер

```yaml
mcp_servers:
  company_api:
    url: "https://mcp.mycompany.com/v1/mcp"
    headers:
      Authorization: "Bearer sk-xxxxxxxxxxxxxxxxxxxx"
      X-Team-Id: "engineering"
    timeout: 180
    connect_timeout: 30
```

### Кілька серверів

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]

  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]

  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"

  company_api:
    url: "https://mcp.internal.company.com/mcp"
    headers:
      Authorization: "Bearer sk-xxxxxxxxxxxxxxxxxxxx"
    timeout: 300
```

Усі інструменти з усіх серверів зареєстровані та доступні одночасно. Інструменти кожного сервера мають префікс з назвою сервера, щоб уникнути конфліктів.
## Sampling (Server-Initiated LLM Requests)

Hermes підтримує можливість MCP `sampling/createMessage` — сервери MCP можуть запитувати завершення LLM через агента під час виконання інструменту. Це дозволяє створювати робочі процеси «агент‑у‑циклі» (аналіз даних, генерація контенту, прийняття рішень).

Sampling **увімкнено за замовчуванням**. Налаштовується для кожного сервера:

```yaml
mcp_servers:
  my_server:
    command: "npx"
    args: ["-y", "my-mcp-server"]
    sampling:
      enabled: true           # default: true
      model: "gemini-3-flash" # model override (optional)
      max_tokens_cap: 4096    # max tokens per request
      timeout: 30             # LLM call timeout (seconds)
      max_rpm: 10             # max requests per minute
      allowed_models: []      # model whitelist (empty = all)
      max_tool_rounds: 5      # tool loop limit (0 = disable)
      log_level: "info"       # audit verbosity
```

Сервери також можуть включати `tools` у запити sampling для багатокрокових робочих процесів з використанням інструментів. Конфігурація `max_tool_rounds` запобігає нескінченним циклам інструментів. Метрики аудиту для кожного сервера (запити, помилки, токени, кількість використань інструменту) відстежуються за допомогою `get_mcp_status()`.

Вимкнути sampling для недовірених серверів можна за допомогою `sampling: { enabled: false }`.
## Примітки

- Інструменти MCP викликаються синхронно з точки зору агента, але виконуються асинхронно у спеціальному фонового циклі подій
- Результати інструментів повертаються у форматі JSON у вигляді `{"result": "..."}` або `{"error": "..."}`
- Вбудований клієнт MCP незалежний від `mcporter` — можна використовувати обидва одночасно
- З’єднання з сервером є постійними та спільними для всіх розмов у одному процесі агента
- Додавання або видалення серверів вимагає перезапуску агента (на даний момент гарячого перезапуску немає)