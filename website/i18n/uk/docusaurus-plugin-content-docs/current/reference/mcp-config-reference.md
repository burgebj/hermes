---
sidebar_position: 8
title: "Довідник конфігурації MCP"
description: "Посилання на ключі конфігурації Hermes Agent MCP, семантику фільтрації та політику utility-tool"
---

# Довідка щодо конфігурації MCP

Ця сторінка — компактний довідковий посібник до основної документації MCP.

Для концептуального керівництва дивись:
- [MCP (Model Context Protocol)](/user-guide/features/mcp)
- [Використання MCP з Hermes](/guides/use-mcp-with-hermes)

## Форма кореневого конфігураційного файлу

```yaml
mcp_servers:
  <server_name>:
    command: "..."      # stdio servers
    args: []
    env: {}

    # OR
    url: "..."          # HTTP servers
    headers: {}

    # Optional HTTP/SSE TLS settings:
    ssl_verify: true                # bool or path to a CA bundle (PEM)
    client_cert: "/path/to/cert.pem"  # mTLS client certificate (see below)
    # client_key: "/path/to/key.pem"  # optional, when key lives in a separate file

    enabled: true
    timeout: 120
    connect_timeout: 60
    supports_parallel_tool_calls: false
    tools:
      include: []
      exclude: []
      resources: true
      prompts: true
```

## Ключі сервера

| Ключ | Тип | Застосовується до | Значення |
|---|---|---|---|
| `command` | string | stdio | Виконуваний файл для запуску |
| `args` | list | stdio | Аргументи для підпроцесу |
| `env` | mapping | stdio | Середовище, передане підпроцесу |
| `url` | string | HTTP | Віддалена точка MCP |
| `headers` | mapping | HTTP | Заголовки для запитів до віддаленого сервера |
| `ssl_verify` | bool or string | HTTP | Перевірка TLS. `true` (за замовчуванням) використовує системні CA, `false` вимикає перевірку (незахищено) або рядок‑шлях до власного набору CA (PEM) |
| `client_cert` | string or list | HTTP | mTLS клієнтський сертифікат. Рядок = шлях до PEM‑файлу, що містить сертифікат + ключ. Список `[cert, key]` = окремі файли. Список `[cert, key, password]` = зашифрований ключ |
| `client_key` | string | HTTP | Шлях до приватного ключа клієнта, коли `client_cert` — рядок і ключ знаходиться в окремому файлі |
| `enabled` | bool | both | Пропустити сервер повністю, коли `false` |
| `timeout` | number | both | Тайм‑аут виклику інструменту |
| `connect_timeout` | number | both | Тайм‑аут початкового з’єднання |
| `supports_parallel_tool_calls` | bool | both | Дозволити інструментам з цього сервера виконуватись одночасно |
| `tools` | mapping | both | Політика фільтрації та утилітних інструментів |
| `auth` | string | HTTP | Метод автентифікації. Встанови `oauth` для ввімкнення OAuth 2.1 з PKCE |
| `sampling` | mapping | both | Політика запитів LLM, ініційованих сервером (див. посібник MCP) |

## Ключі політики `tools`

| Ключ | Тип | Значення |
|---|---|---|
| `include` | string or list | Білий список серверних інструментів MCP |
| `exclude` | string or list | Чорний список серверних інструментів MCP |
| `resources` | bool-like | Увімкнути/вимкнути `list_resources` + `read_resource` |
| `prompts` | bool-like | Увімкнути/вимкнути `list_prompts` + `get_prompt` |

## Семантика фільтрації

### `include`

Якщо встановлено `include`, реєструються лише вказані серверні інструменти MCP.

```yaml
tools:
  include: [create_issue, list_issues]
```

### `exclude`

Якщо встановлено `exclude` і `include` не задано, реєструються всі серверні інструменти MCP, окрім зазначених у `exclude`.

```yaml
tools:
  exclude: [delete_customer]
```

### Пріоритет

Якщо задано обидва, перевага надається `include`.

```yaml
tools:
  include: [create_issue]
  exclude: [create_issue, delete_issue]
```

Результат:
- `create_issue` все ще дозволений
- `delete_issue` ігнорується, бо `include` має пріоритет

## Політика утилітних інструментів

Hermes може зареєструвати такі утилітарні обгортки для кожного сервера MCP:

**Ресурси:**
- `list_resources`
- `read_resource`

**Промпти:**
- `list_prompts`
- `get_prompt`

### Вимкнути ресурси

```yaml
tools:
  resources: false
```

### Вимкнути промпти

```yaml
tools:
  prompts: false
```

### Реєстрація з урахуванням можливостей

Навіть коли `resources: true` або `prompts: true`, Hermes реєструє ці утиліти лише якщо сесія MCP дійсно надає відповідну можливість.

Тож це нормальна поведінка:
- ти ввімкнув промпти
- але жодних утиліт промптів не з’явилось
- бо сервер не підтримує промпти

## `enabled: false`

```yaml
mcp_servers:
  legacy:
    url: "https://mcp.legacy.internal"
    enabled: false
```

Поведінка:
- не робиться спроба підключення
- не виконується виявлення
- не реєструються інструменти
- конфігурація залишається на місці для подальшого використання

## Поведінка при порожньому результаті

Якщо фільтрація видаляє всі серверні інструменти і жодні утиліти не зареєстровані, Hermes не створює порожній набір інструментів MCP для цього сервера.

## Приклади конфігурацій

### Безпечний білий список GitHub

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "***"
    tools:
      include: [list_issues, create_issue, update_issue, search_code]
      resources: false
      prompts: false
```

### Чорний список Stripe

```yaml
mcp_servers:
  stripe:
    url: "https://mcp.stripe.com"
    headers:
      Authorization: "Bearer ***"
    tools:
      exclude: [delete_customer, refund_payment]
```

### Сервер документів лише з ресурсами

```yaml
mcp_servers:
  docs:
    url: "https://mcp.docs.example.com"
    tools:
      include: []
      resources: true
      prompts: false
```

### Клієнтський сертифікат TLS (mTLS)

Для HTTP/SSE серверів, які вимагають клієнтський сертифікат, встанови `client_cert` (і за потреби `client_key`):

```yaml
mcp_servers:
  # Combined cert + key in a single PEM file
  internal_api:
    url: "https://mcp.internal.example.com/mcp"
    client_cert: "~/secrets/mcp-client.pem"

  # Separate cert and key files
  partner_api:
    url: "https://mcp.partner.example.com/mcp"
    client_cert: "~/secrets/client.crt"
    client_key: "~/secrets/client.key"

  # Encrypted key with a passphrase (3-element list form)
  bank_api:
    url: "https://mcp.bank.example.com/mcp"
    client_cert: ["~/secrets/client.crt", "~/secrets/client.key", "my-passphrase"]

  # Custom CA bundle (private CA / self-signed server)
  lab_api:
    url: "https://mcp.lab.local/mcp"
    ssl_verify: "~/secrets/lab-ca.pem"
    client_cert: "~/secrets/lab-client.pem"
```

Примітки:
- Шляхи підтримують розширення `~`. Відсутні файли швидко викликають помилку під час підключення з повідомленням про помилку, прив’язане до сервера.
- `ssl_verify: false` вимикає перевірку сертифіката сервера повністю. Не використовуйте це з реальними сервісами.
- Працює як з транспортом Streamable HTTP, так і з SSE.

## Перезавантаження конфігурації

Після зміни конфігурації MCP перезавантаж сервери за допомогою:

```text
/reload-mcp
```

## Іменування інструментів

Серверні інструменти MCP отримують такі імена:

```text
mcp_<server>_<tool>
```

Приклади:
- `mcp_github_create_issue`
- `mcp_filesystem_read_file`
- `mcp_my_api_query_data`

Утилітарні інструменти слідують тому ж шаблону префікса:
- `mcp_<server>_list_resources`
- `mcp_<server>_read_resource`
- `mcp_<server>_list_prompts`
- `mcp_<server>_get_prompt`

### Санітизація імен

Тире (`-`) та крапки (`.`) у назвах серверів і інструментів замінюються підкресленнями перед реєстрацією. Це гарантує, що імена інструментів є коректними ідентифікаторами для API викликів функцій LLM.

Наприклад, сервер з назвою `my-api`, що надає інструмент `list-items.v2`, буде мати ім’я:

```text
mcp_my_api_list_items_v2
```

Пам’ятай про це, коли пишеш фільтри `include` / `exclude` — використовуйте **оригінальну** назву інструмента MCP (з тире/крапками), а не санітизовану версію.

## Автентифікація OAuth 2.1

Для HTTP серверів, які вимагають OAuth, встанови `auth: oauth` у записі сервера:

```yaml
mcp_servers:
  protected_api:
    url: "https://mcp.example.com/mcp"
    auth: oauth
```

Поведінка:
- Hermes використовує OAuth 2.1 PKCE потік SDK MCP (виявлення метаданих, динамічна реєстрація клієнта, обмін токенами та оновлення)
- При першому підключенні відкривається вікно браузера для авторизації
- Токени зберігаються у `~/.hermes/mcp-tokens/<server>.json` і повторно використовуються в різних сесіях
- Оновлення токену виконується автоматично; повторна авторизація відбувається лише при невдачі оновлення
- Застосовується лише до транспорту HTTP/StreamableHTTP (сервери, що базуються на `url`)