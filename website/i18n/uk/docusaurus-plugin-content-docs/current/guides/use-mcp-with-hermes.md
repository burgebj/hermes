---
sidebar_position: 6
title: "Використовуй MCP з Hermes"
description: "Практичний посібник з підключення серверів MCP до Hermes Agent, фільтрації їх інструментів та безпечного використання у реальних робочих процесах"
---

# Використання MCP з Hermes

Цей посібник показує, як на практиці застосовувати MCP разом із Hermes Agent у щоденних робочих процесах.

Якщо сторінка функції пояснює, що таке MCP, то цей посібник розповідає, як швидко та безпечно отримати від нього користь.
## Коли слід використовувати MCP?

Використовуй MCP, коли:
- інструмент вже існує у формі MCP і ти не хочеш створювати власний інструмент Hermes
- ти хочеш, щоб Hermes працював з локальною або віддаленою системою через чистий RPC‑шар
- тобі потрібен детальний контроль експозиції на рівні кожного сервера
- ти хочеш підключити Hermes до внутрішніх API, баз даних або систем компанії, не змінюючи ядро Hermes

Не використай MCP, коли:
- вбудований інструмент Hermes вже добре вирішує завдання
- сервер відкриває величезну небезпечну поверхню інструментів, і ти не готовий її фільтрувати
- тобі потрібна лише одна дуже вузька інтеграція, і нативний інструмент був би простішим і безпечнішим
## Ментальна модель

Уяви MCP як шар‑адаптер:

- Hermes залишається агентом
- Сервери MCP надають інструменти
- Hermes виявляє ці інструменти при запуску або перезавантаженні
- Модель може використовувати їх як звичайні інструменти
- Ти контролюєш, яку частину кожного сервера видно

Остання частина має значення. Хороше використання MCP — це не просто «підключити все». Це «підключити потрібне, з мінімальною корисною поверхнею».
## Крок 1: встановити підтримку MCP

Якщо ти встановив Hermes за допомогою стандартного скрипту інсталяції, підтримка MCP вже включена (установник виконує `uv pip install -e ".[all]"`).

Якщо ти встановив без extras і потрібно додати MCP окремо:

```bash
cd ~/.hermes/hermes-agent
uv pip install -e ".[mcp]"
```

Для серверів на базі npm переконайся, що Node.js та `npx` доступні.

Для багатьох Python MCP‑серверів `uvx` є хорошим варіантом за замовчуванням.
## Крок 2: додай спочатку один сервер

Почни з одного безпечного сервера.

Приклад: доступ до файлової системи лише до однієї директорії проєкту.

```yaml
mcp_servers:
  project_fs:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/my-project"]
```

Потім запусти Hermes:

```bash
hermes chat
```

Тепер запитай щось конкретне:

```text
Inspect this project and summarize the repo layout.
```
## Крок 3: перевірка завантаження MCP

Ти можеш перевірити MCP кількома способами:

- банер або статус Hermes має показувати інтеграцію MCP, коли вона налаштована
- запитай у Hermes, які інструменти доступні
- використай `/reload-mcp` після змін у конфігурації
- перевір логи, якщо сервер не зміг підключитися

Практичний тестовий запит:

```text
Tell me which MCP-backed tools are available right now.
```
## Крок 4: почати фільтрування одразу

Не чекай, доки сервер відкриє багато інструментів.

### Приклад: додати до білого списку лише те, що потрібне

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

Зазвичай це найкраще налаштування за замовчуванням для чутливих систем.
## WSL2: мостити Hermes у WSL до Windows Chrome

Це практичне налаштування, коли:

- Hermes працює всередині WSL2
- браузер, яким ти хочеш керувати, — це твій звичайний увійшовший у Chrome на Windows
- `/browser connect` незручний або ненадійний з WSL

У цьому налаштуванні Hermes **не** підключається до Chrome безпосередньо. Натомість:

- Hermes працює у WSL
- Hermes запускає локальний stdio MCP‑сервер
- цей MCP‑сервер запускається через Windows‑interop (`cmd.exe` або `powershell.exe`)
- MCP‑сервер під’єднується до твоєї активної сесії Windows Chrome

Ментальна модель:

```text
Hermes (WSL) -> MCP stdio bridge -> Windows Chrome
```

### Чому цей режим корисний

- ти зберігаєш реальний профіль браузера Windows, куки та логіни
- Hermes залишається у підтримуваному Unix‑оточенні (WSL2)
- керування браузером представлено інструментами MCP замість того, щоб покладатися на ядром‑транспортом Hermes

### Рекомендований сервер

Використовуй `chrome-devtools-mcp`.

Якщо у твоєму Windows Chrome вже ввімкнено живе віддалене налагодження через `chrome://inspect/#remote-debugging`, додай його так з WSL:

```bash
hermes mcp add chrome-devtools-win --command cmd.exe --args /c npx -y chrome-devtools-mcp@latest --autoConnect --no-usage-statistics
```

Після збереження сервера:

```bash
hermes mcp test chrome-devtools-win
```

Потім запусти нову сесію Hermes або виконай:

```text
/reload-mcp
```

### Типова підказка

Після завантаження Hermes може безпосередньо використовувати інструменти браузера з префіксом MCP. Наприклад:

```text
调用 MCP 工具 mcp_chrome_devtools_win_list_pages，列出当前浏览器标签页。
```

### Коли `/browser connect` — не той інструмент

Якщо Hermes працює у WSL, а Chrome — у Windows, `/browser connect` може не спрацювати, навіть коли Chrome відкритий і доступний для налагодження.

Типові причини:

- WSL не може досягти того ж локального кінцевого пункту, який Chrome експонує інструментам Windows
- нові потоки живого налагодження Chrome відрізняються від класичного `ws://localhost:9222`
- браузер простіше під’єднати через допоміжний інструмент Windows, такий як `chrome-devtools-mcp`

У таких випадках залишай `/browser connect` для налаштувань у одному середовищі і використай MCP для мосту браузера WSL‑to‑Windows.

### Відомі підводні камені

- Запускай Hermes з шляху, змонтованого Windows, наприклад `/mnt/c/Users/<you>` або `/mnt/c/workspace/...`, коли використовуєш Windows‑stdio виконуваних файлів через MCP.
- Якщо ти запускаєш Hermes з `/root` або `/home/...`, Windows може вивести попередження `UNC` про поточний каталог перед стартом MCP‑сервера.
- Якщо `chrome-devtools-mcp --autoConnect` завершується тайм‑аутом під час перерахунку сторінок, зменши кількість фонових/заморожених вкладок у Chrome і спробуй ще раз.

### Приклад: чорний список небезпечних дій

```yaml
mcp_servers:
  stripe:
    url: "https://mcp.stripe.com"
    headers:
      Authorization: "Bearer ***"
    tools:
      exclude: [delete_customer, refund_payment]
```

### Приклад: вимкнути також утилітарні обгортки

```yaml
mcp_servers:
  docs:
    url: "https://mcp.docs.example.com"
    tools:
      prompts: false
      resources: false
```
## На що саме впливає фільтрація?

Існує два типи функціональності, що експонується MCP у Hermes:

1. Інструменти MCP, які працюють на сервері
   - фільтруються за допомогою:
     - `tools.include`
     - `tools.exclude`

2. Утилітарні обгортки, додані Hermes
   - фільтруються за допомогою:
     - `tools.resources`
     - `tools.prompts`

### Утилітарні обгортки, які ти можеш бачити

**Resources**:
- `list_resources`
- `read_resource`

**Prompts**:
- `list_prompts`
- `get_prompt`

Ці обгортки з’являються лише якщо:
- твоя конфігурація їх дозволяє, і
- сесія сервера MCP фактично підтримує ці можливості.

Отже, Hermes не буде вдавати, що у сервера є ресурси/промпти, якщо їх немає.
## Common patterns

### Pattern 1: local project assistant

Use MCP for a repo-local filesystem or git server when you want Hermes to reason over a bounded workspace.

```yaml
mcp_servers:
  fs:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/project"]

  git:
    command: "uvx"
    args: ["mcp-server-git", "--repository", "/home/user/project"]
```

Good prompts:

```text
Review the project structure and identify where configuration lives.
```

```text
Check the local git state and summarize what changed recently.
```

### Pattern 2: GitHub triage assistant

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

Good prompts:

```text
List open issues about MCP, cluster them by theme, and draft a high-quality issue for the most common bug.
```

```text
Search the repo for uses of _discover_and_register_server and explain how MCP tools are registered.
```

### Pattern 3: internal API assistant

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

Good prompts:

```text
Look up customer ACME Corp and summarize recent invoice activity.
```

This is the sort of place where a strict whitelist is far better than an exclude list.

### Pattern 4: documentation / knowledge servers

Some MCP servers expose prompts or resources that are more like shared knowledge assets than direct actions.

```yaml
mcp_servers:
  docs:
    url: "https://mcp.docs.example.com"
    tools:
      prompts: true
      resources: true
```

Good prompts:

```text
List available MCP resources from the docs server, then read the onboarding guide and summarize it.
```

```text
List prompts exposed by the docs server and tell me which ones would help with incident response.
```
## Посібник: налаштування end‑to‑end з фільтрацією

Ось практичний приклад.

### Фаза 1: додати GitHub MCP з жорстким білим списком

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

Запусти Hermes і запитай:

```text
Search the codebase for references to MCP and summarize the main integration points.
```

### Фаза 2: розширювати лише за потреби

Якщо пізніше знадобляться оновлення issue:

```yaml
tools:
  include: [list_issues, create_issue, update_issue, search_code]
```

Потім перезавантажити:

```text
/reload-mcp
```

### Фаза 3: додати другий сервер з іншою політикою

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

Тепер Hermes може їх об’єднати:

```text
Inspect the local project files, then create a GitHub issue summarizing the bug you find.
```

Ось де MCP набирає потужності: багатосистемні робочі процеси без зміни ядра Hermes.
## Рекомендації щодо безпечного використання

### Надавай перевагу allowlist‑ам для небезпечних систем

Для будь‑яких фінансових, клієнт‑орієнтованих або руйнівних випадків:
- використовуйте `tools.include`
- починайте з найменшого можливого набору

### Вимикай невикористані утиліти

Якщо ти не хочеш, щоб модель переглядала ресурси/підказки, надані сервером, вимкни їх:

```yaml
tools:
  resources: false
  prompts: false
```

### Обмежуй область дії серверів

Приклади:
- сервер файлової системи, прив’язаний до однієї директорії проєкту, а не до всього твого домашнього каталогу
- git‑сервер, що працює лише з одним репозиторієм
- внутрішній API‑сервер з типово активним інструментом лише для читання

### Перезавантажуй після змін конфігурації

```text
/reload-mcp
```

Роби це після зміни:
- списків включення/виключення
- увімкнених прапорців
- перемикачів ресурсів/підказок
- заголовків автентифікації / змінних середовища
## Усунення проблем за симптомом

### «Сервер підключається, але інструменти, які я очікував, відсутні»

Можливі причини:
- фільтрація за `tools.include`
- виключення за `tools.exclude`
- обгортки інструментів вимкнено через `resources: false` або `prompts: false`
- сервер фактично не підтримує resources/prompts

### «Сервер налаштовано, але нічого не завантажується»

Перевір:
- `enabled: false` не залишився у конфігурації
- існує команда/середовище виконання (`npx`, `uvx` тощо)
- HTTP‑endpoint доступний
- змінні середовища або заголовки автентифікації правильні

### «Чому я бачу менше інструментів, ніж рекламує сервер MCP?»

Тому що Hermes тепер дотримується вашої політики per‑server та реєстрації з урахуванням можливостей. Це очікувана і, зазвичай, бажана поведінка.

### «Як видалити сервер MCP, не видаляючи конфігурацію?»

Використай:

```yaml
enabled: false
```

Це залишає конфігурацію, але запобігає підключенню та реєстрації.
## Рекомендовані перші налаштування MCP

Хороші перші сервери для більшості користувачів:
- filesystem
- git
- GitHub
- fetch / documentation MCP servers
- one narrow internal API

Недоречні перші сервери:
- giant business systems with lots of destructive actions and no filtering
- anything you do not understand well enough to constrain
## Пов’язані документи

- [MCP (Model Context Protocol)](/user-guide/features/mcp)
- [FAQ](/reference/faq)
- [Slash Commands](/reference/slash-commands)