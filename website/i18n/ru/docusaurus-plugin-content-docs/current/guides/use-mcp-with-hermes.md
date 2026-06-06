---
sidebar_position: 6
title: "Используй MCP с Hermes"
description: "Практическое руководство по подключению серверов MCP к Hermes Agent, фильтрации их инструментов и безопасному использованию в реальных рабочих процессах"
---

# Использовать MCP с Hermes

Это руководство показывает, как действительно использовать MCP с Hermes Agent в повседневных рабочих процессах.

Если страница функции объясняет, что такое MCP, то это руководство о том, как быстро и безопасно извлечь из него пользу.

## Когда следует использовать MCP?

Используй MCP, когда:
- уже существует инструмент в виде MCP и ты не хочешь создавать нативный инструмент Hermes
- ты хочешь, чтобы Hermes работал с локальной или удалённой системой через чистый RPC‑слой
- тебе нужен тонко настроенный контроль доступа к каждому серверу
- ты хочешь подключить Hermes к внутренним API, базам данных или системам компании без изменения ядра Hermes

Не используй MCP, когда:
- встроенный инструмент Hermes уже хорошо решает задачу
- сервер раскрывает огромную опасную поверхность инструментов, и ты не готов её фильтровать
- тебе нужна лишь одна очень узкая интеграция, и нативный инструмент был бы проще и безопаснее

## Ментальная модель

Думай о MCP как об адаптерном слое:

- Hermes остаётся агентом
- серверы MCP предоставляют инструменты
- Hermes обнаруживает эти инструменты при запуске или перезагрузке
- модель может использовать их как обычные инструменты
- ты контролируешь, какая часть каждого сервера видима

Эта последняя часть имеет значение. Хорошее использование MCP — это не просто «подключить всё». Это «подключить нужное, с минимально полезной поверхностью».

## Шаг 1: установить поддержку MCP

Если ты установил Hermes с помощью стандартного скрипта установки, поддержка MCP уже включена (установщик запускает `uv pip install -e ".[all]"`).

Если ты установил без дополнительных пакетов и нужно добавить MCP отдельно:

```bash
cd ~/.hermes/hermes-agent
uv pip install -e ".[mcp]"
```

Для серверов на npm убедись, что Node.js и `npx` доступны.

Для многих Python‑серверов MCP удобно использовать `uvx`.

## Шаг 2: добавить один сервер сначала

Начни с одного безопасного сервера.

Пример: доступ к файловой системе только в одном каталоге проекта.

```yaml
mcp_servers:
  project_fs:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/my-project"]
```

Затем запусти Hermes:

```bash
hermes chat
```

Теперь задай что‑то конкретное:

```text
Inspect this project and summarize the repo layout.
```

## Шаг 3: проверить, что MCP загружен

Проверить MCP можно несколькими способами:

- баннер/статус Hermes должен показывать интеграцию MCP, если она настроена
- спроси у Hermes, какие инструменты доступны
- используй `/reload-mcp` после изменения конфигурации
- проверь логи, если сервер не смог подключиться

Практический тестовый запрос:

```text
Tell me which MCP-backed tools are available right now.
```

## Шаг 4: сразу начать фильтрацию

Не жди позже, если сервер раскрывает множество инструментов.

### Пример: включить в whitelist только то, что нужно

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "***"
    tools:
      include: [list_issues, create_issue, search_code]
```

Обычно это лучший вариант по умолчанию для чувствительных систем.

## WSL2: мост Hermes в WSL к Windows Chrome

Это практическая настройка, когда:

- Hermes работает внутри WSL2
- браузер, которым ты хочешь управлять, — обычный входящий в систему Chrome в Windows
- `/browser connect` неудобен или ненадёжен из WSL

В этой схеме Hermes **не** подключается к Chrome напрямую. Вместо этого:

- Hermes работает в WSL
- Hermes запускает локальный stdio‑сервер MCP
- этот сервер MCP запускается через Windows‑interop (`cmd.exe` или `powershell.exe`)
- сервер MCP присоединяется к текущей сессии Chrome в Windows

Ментальная модель:

```text
Hermes (WSL) -> MCP stdio bridge -> Windows Chrome
```

### Почему этот режим полезен

- ты сохраняешь реальный профиль, куки и входы в браузере Windows
- Hermes остаётся в поддерживаемой Unix‑среде (WSL2)
- управление браузером раскрывается как инструменты MCP вместо зависимости от ядра Hermes

### Рекомендуемый сервер

Используй `chrome-devtools-mcp`.

Если в твоём Windows‑Chrome уже включён живой удалённый отладчик (`chrome://inspect/#remote-debugging`), добавь его из WSL так:

```bash
hermes mcp add chrome-devtools-win --command cmd.exe --args /c npx -y chrome-devtools-mcp@latest --autoConnect --no-usage-statistics
```

После сохранения сервера:

```bash
hermes mcp test chrome-devtools-win
```

Затем запусти новую сессию Hermes или выполни:

```text
/reload-mcp
```

### Типичный запрос

После загрузки Hermes может напрямую использовать инструменты браузера с префиксом `mcp`. Например:

```text
调用 MCP 工具 mcp_chrome_devtools_win_list_pages，列出当前浏览器标签页。
```

### Когда `/browser connect` — не тот инструмент

Если Hermes работает в WSL, а Chrome — в Windows, `/browser connect` может не сработать, даже если Chrome открыт и доступен для отладки.

Распространённые причины:

- WSL не может достичь того же локального эндпоинта, который Chrome раскрывает Windows‑инструментам
- новые потоки живой отладки Chrome отличаются от классического `ws://localhost:9222`
- к браузеру проще подключиться из Windows‑помощника, например `chrome-devtools-mcp`

В этих случаях оставляй `/browser connect` для одноокружных настроек и используй MCP для мостов браузера WSL → Windows.

### Известные подводные камни

- Запускай Hermes из пути, смонтированного в Windows, например `/mnt/c/Users/<you>` или `/mnt/c/workspace/...`, когда используешь Windows‑stdio‑исполняемые файлы через MCP.
- Если ты запускаешь Hermes из `/root` или `/home/...`, Windows может выдать предупреждение `UNC` о текущем каталоге до старта сервера MCP.
- Если `chrome-devtools-mcp --autoConnect` истекает при перечислении страниц, уменьшай количество фоновых/замороженных вкладок в Chrome и повтори попытку.

### Пример: blacklist опасных действий

```yaml
mcp_servers:
  stripe:
    url: "https://mcp.stripe.com"
    headers:
      Authorization: "Bearer ***"
    tools:
      exclude: [delete_customer, refund_payment]
```

### Пример: отключить утилитарные обёртки тоже

```yaml
mcp_servers:
  docs:
    url: "https://mcp.docs.example.com"
    tools:
      prompts: false
      resources: false
```

## Что именно фильтрация влияет?

В Hermes есть два типа функций, раскрываемых MCP:

1. Инструменты сервера‑native MCP
   - фильтруются через:
     - `tools.include`
     - `tools.exclude`

2. Утилитарные обёртки, добавленные Hermes
   - фильтруются через:
     - `tools.resources`
     - `tools.prompts`

### Утилитарные обёртки, которые ты можешь увидеть

Resources:
- `list_resources`
- `read_resource`

Prompts:
- `list_prompts`
- `get_prompt`

Эти обёртки появляются только если:
- твоя конфигурация их разрешает, и
- сессия сервера MCP действительно поддерживает эти возможности

Поэтому Hermes не будет притворяться, что у сервера есть ресурсы/промпты, если их нет.

## Распространённые шаблоны

### Шаблон 1: локальный помощник проекта

Используй MCP для файловой системы или git‑сервера, привязанного к репозиторию, когда нужен Hermes, рассуждающий в ограничённом рабочем пространстве.

```yaml
mcp_servers:
  fs:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/project"]

  git:
    command: "uvx"
    args: ["mcp-server-git", "--repository", "/home/user/project"]
```

Хорошие запросы:

```text
Review the project structure and identify where configuration lives.
```

```text
Check the local git state and summarize what changed recently.
```

### Шаблон 2: помощник по триажу GitHub

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "***"
    tools:
      include: [list_issues, create_issue, update_issue, search_code]
      prompts: false
      resources: false
```

Хорошие запросы:

```text
List open issues about MCP, cluster them by theme, and draft a high-quality issue for the most common bug.
```

```text
Search the repo for uses of _discover_and_register_server and explain how MCP tools are registered.
```

### Шаблон 3: помощник внутреннего API

```yaml
mcp_servers:
  internal_api:
    url: "https://mcp.internal.example.com"
    headers:
      Authorization: "Bearer ***"
    tools:
      include: [list_customers, get_customer, list_invoices]
      resources: false
      prompts: false
```

Хорошие запросы:

```text
Look up customer ACME Corp and summarize recent invoice activity.
```

Здесь строгий whitelist гораздо лучше, чем список исключений.

### Шаблон 4: серверы документации / знаний

Некоторые MCP‑серверы раскрывают промпты или ресурсы, которые больше похожи на общие знания, чем на прямые действия.

```yaml
mcp_servers:
  docs:
    url: "https://mcp.docs.example.com"
    tools:
      prompts: true
      resources: true
```

Хорошие запросы:

```text
List available MCP resources from the docs server, then read the onboarding guide and summarize it.
```

```text
List prompts exposed by the docs server and tell me which ones would help with incident response.
```

## Учебник: сквозная настройка с фильтрацией

Практический план развития.

### Фаза 1: добавить GitHub MCP с жёстким whitelist

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "***"
    tools:
      include: [list_issues, create_issue, search_code]
      prompts: false
      resources: false
```

Запусти Hermes и спроси:

```text
Search the codebase for references to MCP and summarize the main integration points.
```

### Фаза 2: расширять только при необходимости

Если позже понадобится обновлять задачи:

```yaml
tools:
  include: [list_issues, create_issue, update_issue, search_code]
```

Затем перезагрузи:

```text
/reload-mcp
```

### Фаза 3: добавить второй сервер с иной политикой

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "***"
    tools:
      include: [list_issues, create_issue, update_issue, search_code]
      prompts: false
      resources: false

  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/project"]
```

Теперь Hermes может комбинировать их:

```text
Inspect the local project files, then create a GitHub issue summarizing the bug you find.
```

Вот где MCP становится мощным: многосистемные рабочие процессы без изменения ядра Hermes.

## Рекомендации по безопасному использованию

### Предпочитай whitelist для опасных систем

Для финансовых, клиентских или разрушительных систем:
- используй `tools.include`
- начинай с минимального набора

### Отключи неиспользуемые утилиты

Если ты не хочешь, чтобы модель просматривала ресурсы/промпты, предоставляемые сервером, выключи их:

```yaml
tools:
  resources: false
  prompts: false
```

### Ограничивай область серверов

Примеры:
- сервер файловой системы, корневой в одном каталоге проекта, а не в домашнем каталоге полностью
- git‑сервер, указывающий на один репозиторий
- внутренний API‑сервер, по умолчанию раскрывающий только чтение

### Перезагружай после изменения конфигурации

```text
/reload-mcp
```

Делай это после изменения:
- списков `include`/`exclude`
- флагов `enabled`
- переключателей `resources`/`prompts`
- заголовков/переменных окружения для аутентификации

## Устранение неполадок по симптомам

### «Сервер подключён, но ожидаемых инструментов нет»

Возможные причины:
- отфильтровано `tools.include`
- исключено `tools.exclude`
- утилитарные обёртки отключены через `resources: false` или `prompts: false`
- сервер фактически не поддерживает ресурсы/промпты

### «Сервер сконфигурирован, но ничего не загружается»

Проверь:
- `enabled: false` не остался в конфиге
- команда/среда выполнения существует (`npx`, `uvx` и т.д.)
- HTTP‑эндпоинт доступен
- переменные окружения или заголовки аутентификации корректны

### «Почему я вижу меньше инструментов, чем рекламирует сервер MCP?»

Потому что Hermes теперь учитывает твою политику per‑server и регистрацию, учитывающую возможности. Это ожидаемо и обычно желаемо.

### «Как удалить сервер MCP, не удаляя конфиг?»

Используй:

```yaml
enabled: false
```

Это оставит конфиг, но предотвратит подключение и регистрацию.

## Рекомендуемые первые настройки MCP

Хорошие первые серверы для большинства пользователей:
- файловая система
- git
- GitHub
- fetch / documentation MCP‑серверы
- один узкий внутренний API

Неидеальные первые серверы:
- огромные бизнес‑системы с множеством разрушительных действий и без фильтрации
- всё, что ты недостаточно хорошо понимаешь, чтобы ограничить

## Связанные документы

- [MCP (Model Context Protocol)](/user-guide/features/mcp)
- [FAQ](/reference/faq)
- [Slash Commands](/reference/slash-commands)