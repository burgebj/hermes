---
title: "Native Mcp — MCP‑клиент: подключать серверы, регистрировать инструменты (stdio/HTTP)"
sidebar_label: "Native Mcp"
description: "MCP client: подключай серверы, регистрируй инструменты (stdio/HTTP)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Native MCP

MCP‑клиент: подключение к серверам, регистрация инструментов (stdio/HTTP).
## Метаданные навыка

| | |
|---|---|
| Источник | Bundled (установлен по умолчанию) |
| Путь | `skills/mcp/native-mcp` |
| Версия | `1.0.0` |
| Автор | Hermes Agent |
| Лицензия | MIT |
| Платформы | linux, macos, windows |
| Теги | `MCP`, `Tools`, `Integrations` |
| Связанные навыки | [`mcporter`](/docs/user-guide/skills/optional/mcp/mcp-mcporter) |
:::info
Следующий текст — полное определение навыка, которое Hermes загружает при срабатывании этого навыка. Это то, что агент видит как инструкции, когда навык активен.
:::

# Встроенный клиент MCP

Hermes Agent имеет встроенный клиент MCP, который подключается к серверам MCP при запуске, обнаруживает их инструменты и делает их доступными как полноценные инструменты, которые агент может вызывать напрямую. CLI‑мост не требуется — инструменты с серверов MCP появляются рядом со встроенными инструментами, такими как `terminal`, `read_file` и т.д.
## Когда использовать

Используй это, когда нужно:
- Подключиться к серверам MCP и использовать их инструменты из Hermes Agent
- Добавить внешние возможности (доступ к файловой системе, GitHub, базы данных, API) через MCP
- Запустить локальные MCP‑серверы, работающие через stdio (npx, uvx или любую другую команду)
- Подключиться к удалённым HTTP/StreamableHTTP MCP‑серверам
- Чтобы инструменты MCP автоматически обнаруживались и были доступны в любой беседе

Для одноразовых вызовов MCP‑инструментов из терминала без какой‑либо настройки смотри навык `mcporter`.
## Предварительные требования

- **mcp Python package** — необязательная зависимость; установить с помощью `pip install mcp`. Если пакет не установлен, поддержка MCP будет отключена без предупреждения.
- **Node.js** — требуется для MCP‑серверов, работающих через `npx` (большинство серверов сообщества).
- **uv** — требуется для MCP‑серверов, работающих через `uvx` (серверы на Python).

Установи MCP SDK:

```bash
pip install mcp
# or, if using uv:
uv pip install mcp
```
## Быстрый старт

Добавь MCP‑серверы в `~/.hermes/config.yaml` под ключом `mcp_servers`:

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]
```

Перезапусти Hermes Agent. При запуске он:
1. Подключится к серверу
2. Обнаружит доступные инструменты
3. Зарегистрирует их с префиксом `mcp_time_*`
4. Внедрит их во все наборы инструментов платформы

После этого ты можешь использовать инструменты как обычно — просто попроси агента получить текущее время.
## Справочник конфигурации

Каждая запись в `mcp_servers` — это имя сервера, сопоставленное с его конфигурацией. Существует два типа транспорта: **stdio** (на основе команды) и **HTTP** (на основе URL).

### Транспорт stdio (команда + аргументы)

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

### Транспорт HTTP (url)

```yaml
mcp_servers:
  server_name:
    url: "https://my-server.example.com/mcp"   # (required) server URL
    headers:                                     # (optional) HTTP headers
      Authorization: "Bearer sk-..."
    timeout: 180               # (optional) per-tool-call timeout in seconds, default: 120
    connect_timeout: 60        # (optional) initial connection timeout in seconds, default: 60
```

### Все параметры конфигурации

| Option            | Type   | Default | Description                                             |
|-------------------|--------|---------|---------------------------------------------------------|
| `command`         | string | --      | Исполняемый файл (транспорт stdio, обязателен)          |
| `args`            | list   | `[]`    | Аргументы, передаваемые в команду                        |
| `env`             | dict   | `{}`    | Дополнительные переменные окружения для подпроцесса     |
| `url`             | string | --      | URL сервера (транспорт HTTP, обязателен)               |
| `headers`         | dict   | `{}`    | HTTP‑заголовки, отправляемые с каждым запросом           |
| `timeout`         | int    | `120`   | Таймаут вызова инструмента (в секундах)                 |
| `connect_timeout` | int    | `60`    | Таймаут начального соединения и обнаружения            |

**Примечание:** Конфигурация сервера должна содержать либо `command` (stdio), либо `url` (HTTP), но не оба одновременно.
## Как это работает

### Обнаружение при запуске

Когда Hermes Agent стартует, `discover_mcp_tools()` вызывается во время инициализации инструментов:

1. Читает `mcp_servers` из `~/.hermes/config.yaml`
2. Для каждого сервера создаёт соединение в отдельном фоновом `event loop`
3. Инициализирует MCP‑сессию и вызывает `list_tools()` для обнаружения доступных инструментов
4. Регистрирует каждый инструмент в реестре инструментов Hermes

### Конвенция именования инструментов

Инструменты MCP регистрируются по шаблону имени:

```
mcp_{server_name}_{tool_name}
```

Дефисы и точки в именах заменяются подчёркиваниями для совместимости с API LLM.

Примеры:
- Сервер `filesystem`, инструмент `read_file` → `mcp_filesystem_read_file`
- Сервер `github`, инструмент `list-issues` → `mcp_github_list_issues`
- Сервер `my-api`, инструмент `fetch.data` → `mcp_my_api_fetch_data`

### Авто‑внедрение

После обнаружения инструменты MCP автоматически внедряются во все наборы платформенных инструментов `hermes-*` (CLI, Discord, Telegram и т.д.). Это значит, что инструменты MCP доступны в каждом разговоре без дополнительной настройки.

### Жизненный цикл соединения

- Каждый сервер работает как длительная `asyncio`‑задача в фоновом демо‑потоке
- Соединения сохраняются на протяжении всего процесса агента
- Если соединение прерывается, запускается автоматическое повторное подключение с экспоненциальным откатом (до 5 попыток, максимум 60 с отката)
- При завершении работы агента все соединения корректно закрываются

### Идемпотентность

`discover_mcp_tools()` идемпотентен — вызов его несколько раз подключает только те серверы, к которым ещё нет соединения. Неудавшиеся серверы повторно пытаются подключиться при последующих вызовах.
## Типы транспортов

### Stdio Transport

Самый распространённый транспорт. Hermes запускает сервер MCP как подпроцесс и общается через `stdin`/`stdout`.

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"]
```

Подпроцесс наследует **отфильтрованную** среду (см. раздел Security ниже) плюс любые переменные, которые ты укажешь в `env`.

### HTTP / StreamableHTTP Transport

Для удалённых или общих серверов MCP. Требует, чтобы пакет `mcp` включал поддержку HTTP‑клиента (`mcp.client.streamable_http`).

```yaml
mcp_servers:
  remote_api:
    url: "https://mcp.example.com/mcp"
    headers:
      Authorization: "Bearer sk-..."
```

Если поддержка HTTP недоступна в установленной версии `mcp`, сервер завершит работу с `ImportError`, а другие серверы продолжат работу нормально.
## Безопасность

### Фильтрация переменных окружения

Для серверов stdio Hermes НЕ передаёт полное окружение оболочки в подпроцессы MCP. Наследуются только безопасные базовые переменные:

- `PATH`, `HOME`, `USER`, `LANG`, `LC_ALL`, `TERM`, `SHELL`, `TMPDIR`
- Любые переменные `XDG_*`

Все остальные переменные окружения (ключи API, токены, секреты) исключаются, если ты явно не добавишь их через параметр конфигурации `env`. Это предотвращает случайную утечку учётных данных на недоверенные серверы MCP.

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      # Only this token is passed to the subprocess
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_..."
```

### Удаление учётных данных из сообщений об ошибках

Если вызов инструмента MCP завершился ошибкой, любые шаблоны, похожие на учётные данные, в сообщении об ошибке автоматически замаскированы перед тем, как показать их LLM. Это охватывает:

- PAT‑ы GitHub (`ghp_...`)
- Ключи в стиле OpenAI (`sk-...`)
- Токены Bearer
- Общие шаблоны `token=`, `key=`, `API_KEY=`, `password=`, `secret=`
## Устранение неполадок

### «MCP SDK not available -- skipping MCP tool discovery»

Пакет Python `mcp` не установлен. Установи его:

```bash
pip install mcp
```

### «No MCP servers configured»

В `~/.hermes/config.yaml` отсутствует ключ `mcp_servers` или он пустой. Добавь хотя бы один сервер.

### «Failed to connect to MCP server 'X'»

Распространённые причины:
- **Command not found**: Исполняемый файл `command` не найден в `PATH`. Убедись, что установлен `npx`, `uvx` или соответствующая команда.
- **Package not found**: Для серверов npx npm‑пакет может не существовать или требуется добавить `-y` в аргументы для автоматической установки.
- **Timeout**: Серверу потребовалось слишком много времени для запуска. Увеличь `connect_timeout`.
- **Port conflict**: Для HTTP‑серверов URL может быть недоступен.

### «MCP server 'X' requires HTTP transport but mcp.client.streamable_http is not available»

Твоя версия пакета `mcp` не включает поддержку HTTP‑клиента. Обнови её:

```bash
pip install --upgrade mcp
```

### Инструменты не отображаются

- Проверь, что сервер указан в `mcp_servers` (а не в `mcp` или `servers`).
- Убедись, что отступы в YAML правильные.
- Посмотри логи запуска Hermes Agent для сообщений о подключении.
- Имена инструментов имеют префикс `mcp_{server}_{tool}` — ищи этот шаблон.

### Соединение постоянно прерывается

Клиент повторяет попытки до 5 раз с экспоненциальным увеличением интервала (1 с, 2 с, 4 с, 8 с, 16 с, максимум 60 с). Если сервер фундаментально недоступен, после 5‑ти попыток попытки прекращаются. Проверь процесс сервера и сетевое соединение.
## Примеры

### Сервер времени (uvx)

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]
```

Регистрируются инструменты, такие как `mcp_time_get_current_time`.

### Сервер файловой системы (npx)

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/documents"]
    timeout: 30
```

Регистрируются инструменты, такие как `mcp_filesystem_read_file`, `mcp_filesystem_write_file`, `mcp_filesystem_list_directory`.

### Сервер GitHub с аутентификацией

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"
    timeout: 60
```

Регистрируются инструменты, такие как `mcp_github_list_issues`, `mcp_github_create_pull_request` и т.д.

### Удалённый HTTP‑сервер

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

### Несколько серверов

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

Все инструменты со всех серверов регистрируются и доступны одновременно. Инструменты каждого сервера получают префикс с его именем, чтобы избежать конфликтов.
## Сэмплинг (Запросы LLM, инициированные сервером)

Hermes поддерживает возможность MCP `sampling/createMessage` — серверы MCP могут запрашивать завершения LLM через агента во время выполнения инструмента. Это позволяет создавать рабочие процессы с участием агента (анализ данных, генерация контента, принятие решений).

Сэмплинг **включён по умолчанию**. Настраивается для каждого сервера:

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

Серверы также могут включать `tools` в запросы сэмплинга для многошаговых рабочих процессов, расширенных инструментами. Параметр конфигурации `max_tool_rounds` предотвращает бесконечные циклы инструментов. Метрики аудита для каждого сервера (запросы, ошибки, токены, количество использований инструмента) отслеживаются через `get_mcp_status()`.

Отключи сэмплинг для недоверенных серверов, указав `sampling: { enabled: false }`.
## Примечания

- Инструменты MCP вызываются синхронно с точки зрения агента, но работают асинхронно в выделенном фоновом цикле событий
- Результаты инструмента возвращаются в виде JSON либо `{"result": "..."}` либо `{"error": "..."}`
- Нативный клиент MCP независим от `mcporter` — ты можешь использовать их одновременно
- Соединения с сервером постоянны и общие для всех разговоров в одном процессе агента
- Добавление или удаление серверов требует перезапуска агента (горячая перезагрузка пока недоступна)