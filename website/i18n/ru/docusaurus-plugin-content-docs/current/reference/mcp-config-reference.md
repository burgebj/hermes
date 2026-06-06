---
sidebar_position: 8
title: "Справочник конфигурации MCP"
description: "Справочник по Hermes Agent MCP ключам конфигурации, семантике фильтрации и политике utility-tool"
---

# Справочник по конфигурации MCP

Эта страница — компактный справочный материал к основной документации по MCP.

Для концептуального руководства см.:
- [MCP (Model Context Protocol)](/user-guide/features/mcp)
- [Использование MCP с Hermes](/guides/use-mcp-with-hermes)

## Форма корневой конфигурации

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

## Ключи сервера

| Ключ | Тип | Применяется к | Значение |
|---|---|---|---|
| `command` | string | stdio | Выполняемый файл для запуска |
| `args` | list | stdio | Аргументы для подпроцесса |
| `env` | mapping | stdio | Окружение, передаваемое подпроцессу |
| `url` | string | HTTP | Удалённая конечная точка MCP |
| `headers` | mapping | HTTP | Заголовки для запросов к удалённому серверу |
| `ssl_verify` | bool or string | HTTP | Проверка TLS. `true` (по умолчанию) использует системные CA, `false` отключает проверку (небезопасно) или строковый путь к пользовательскому набору CA (PEM) |
| `client_cert` | string or list | HTTP | mTLS‑клиентский сертификат. Строка = путь к PEM‑файлу, содержащему сертификат + ключ. Список `[cert, key]` = отдельные файлы. Список `[cert, key, password]` = зашифрованный ключ |
| `client_key` | string | HTTP | Путь к приватному ключу клиента, когда `client_cert` указан как строка и ключ находится в отдельном файле |
| `enabled` | bool | both | Пропустить сервер полностью, если `false` |
| `timeout` | number | both | Таймаут вызова инструмента |
| `connect_timeout` | number | both | Таймаут начального соединения |
| `supports_parallel_tool_calls` | bool | both | Разрешить одновременный запуск инструментов с этого сервера |
| `tools` | mapping | both | Политика фильтрации и утилитных инструментов |
| `auth` | string | HTTP | Метод аутентификации. Установи `oauth` для включения OAuth 2.1 с PKCE |
| `sampling` | mapping | both | Политика запросов LLM, инициируемая сервером (см. руководство MCP) |

## Ключи политики `tools`

| Ключ | Тип | Значение |
|---|---|---|
| `include` | string or list | Белый список нативных MCP‑инструментов сервера |
| `exclude` | string or list | Чёрный список нативных MCP‑инструментов сервера |
| `resources` | bool-like | Включить/отключить `list_resources` + `read_resource` |
| `prompts` | bool-like | Включить/отключить `list_prompts` + `get_prompt` |

## Семантика фильтрации

### `include`

Если задан `include`, регистрируются только указанные нативные MCP‑инструменты сервера.

```yaml
tools:
  include: [create_issue, list_issues]
```

### `exclude`

Если задан `exclude` и `include` не задан, регистрируются все нативные MCP‑инструменты сервера, кроме указанных в `exclude`.

```yaml
tools:
  exclude: [delete_customer]
```

### Приоритет

Если заданы оба параметра, приоритет имеет `include`.

```yaml
tools:
  include: [create_issue]
  exclude: [create_issue, delete_issue]
```

**Результат**
- `create_issue` — всё ещё разрешён
- `delete_issue` — игнорируется, потому что `include` имеет приоритет

## Политика утилитных инструментов

Hermes может регистрировать эти утилитные обёртки для каждого MCP‑сервера:

**Ресурсы**
- `list_resources`
- `read_resource`

**Подсказки**
- `list_prompts`
- `get_prompt`

### Отключить ресурсы

```yaml
tools:
  resources: false
```

### Отключить подсказки

```yaml
tools:
  prompts: false
```

### Регистрация с учётом возможностей

Даже если `resources: true` или `prompts: true`, Hermes регистрирует утилитные инструменты только тогда, когда сессия MCP действительно предоставляет соответствующую возможность.

То есть это нормально:
- ты включил подсказки
- но утилиты подсказок не появляются
- потому что сервер не поддерживает подсказки

## `enabled: false`

```yaml
mcp_servers:
  legacy:
    url: "https://mcp.legacy.internal"
    enabled: false
```

**Поведение**
- попытка соединения не производится
- обнаружение не происходит
- регистрация инструментов не выполняется
- конфигурация остаётся на месте для последующего использования

## Поведение при пустом результате

Если фильтрация удаляет все нативные инструменты сервера и ни один утилитный инструмент не зарегистрирован, Hermes не создаёт пустой набор MCP‑инструментов для этого сервера.

## Примеры конфигураций

### Безопасный белый список GitHub

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

### Чёрный список Stripe

```yaml
mcp_servers:
  stripe:
    url: "https://mcp.stripe.com"
    headers:
      Authorization: "Bearer ***"
    tools:
      exclude: [delete_customer, refund_payment]
```

### Сервер документации только с ресурсами

```yaml
mcp_servers:
  docs:
    url: "https://mcp.docs.example.com"
    tools:
      include: []
      resources: true
      prompts: false
```

### Клиентский сертификат TLS (mTLS)

Для HTTP/SSE‑серверов, требующих клиентский сертификат, укажи `client_cert` (и при необходимости `client_key`):

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

**Примечания**
- Пути поддерживают расширение `~`. Отсутствующие файлы вызывают быструю ошибку при подключении с сообщением, относящимся к серверу.
- `ssl_verify: false` полностью отключает проверку сертификата сервера. Не используй это с реальными сервисами.
- Работает как с потоковым HTTP, так и с SSE‑транспортом.

## Перезагрузка конфигурации

После изменения конфигурации MCP перезагрузи серверы командой:

```text
/reload-mcp
```

## Именование инструментов

Нативные MCP‑инструменты сервера получают префикс:

```text
mcp_<server>_<tool>
```

**Примеры**
- `mcp_github_create_issue`
- `mcp_filesystem_read_file`
- `mcp_my_api_query_data`

Утилитные инструменты следуют той же схеме префикса:
- `mcp_<server>_list_resources`
- `mcp_<server>_read_resource`
- `mcp_<server>_list_prompts`
- `mcp_<server>_get_prompt`

### Санитизация имени

Дефисы (`-`) и точки (`.`) в названиях серверов и инструментов заменяются подчёркиваниями перед регистрацией. Это гарантирует, что имена инструментов являются допустимыми идентификаторами для API вызова функций LLM.

Например, сервер `my-api`, предоставляющий инструмент `list-items.v2`, будет преобразован в:

```text
mcp_my_api_list_items_v2
```

Имей это в виду, когда пишешь фильтры `include` / `exclude` — используй **исходное** имя MCP‑инструмента (с дефисами/точками), а не санитизированную версию.

## Аутентификация OAuth 2.1

Для HTTP‑серверов, требующих OAuth, укажи `auth: oauth` в записи сервера:

```yaml
mcp_servers:
  protected_api:
    url: "https://mcp.example.com/mcp"
    auth: oauth
```

**Поведение**
- Hermes использует OAuth 2.1 PKCE flow из MCP SDK (обнаружение метаданных, динамическая регистрация клиента, обмен токеном и обновление)
- При первом подключении открывается окно браузера для авторизации
- Токены сохраняются в `~/.hermes/mcp-tokens/<server>.json` и переиспользуются между сессиями
- Обновление токена происходит автоматически; повторная авторизация требуется только при неудачном обновлении
- Применяется только к транспортам HTTP/StreamableHTTP (серверы, основанные на `url`)