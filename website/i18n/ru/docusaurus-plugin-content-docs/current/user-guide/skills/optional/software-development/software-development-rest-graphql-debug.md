---
title: "Rest Graphql Debug — отладка REST/GraphQL API: коды статуса, auth, схемы, repro"
sidebar_label: "Rest Graphql Debug"
description: "Отладка REST/GraphQL API: коды статуса, аутентификация, схемы, воспроизведение"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Отладка Rest Graphql

Отладка REST/GraphQL API: коды статусов, аутентификация, схемы, воспроизведение.

## Метаданные навыка

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/software-development/rest-graphql-debug` |
| Path | `optional-skills/software-development/rest-graphql-debug` |
| Version | `1.2.0` |
| Author | eren-karakus0 |
| License | MIT |
| Tags | `api`, `rest`, `graphql`, `http`, `debugging`, `testing`, `curl`, `integration` |
| Related skills | [`systematic-debugging`](/docs/user-guide/skills/bundled/software-development/software-development-systematic-debugging), [`test-driven-development`](/docs/user-guide/skills/bundled/software-development/software-development-test-driven-development) |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции, когда навык включён.
:::

# Тестирование и отладка API

Проводите диагностику REST и GraphQL через инструменты Hermes — `terminal` для `curl`, `execute_code` для Python `requests`, `web_extract` для документации поставщика. Изолируй проблемный слой до того, как пытаться угадывать решение.

## Когда использовать

- API возвращает неожиданный статус или тело
- Аутентификация не проходит (401/403 после обновления токена, OAuth, API‑key)
- Работает в Postman, но падает в коде
- Отладка интеграции веб‑хуков / колбэков
- Создание или ревью тестов интеграции API
- Проблемы с ограничением запросов или пагинацией

Пропускай для отладки UI‑рендеринга, настройки запросов к БД или инфраструктуры DNS/фаервола (эскалация).

## Основной принцип

**Изолируй слой, затем исправляй.** 200 OK может скрывать сломанные данные. 500 может маскировать опечатку в аутентификации. Проходи цепочку последовательно; никогда не пропускай шаг.

```
1. Connectivity   → can we reach the host at all?
1.5 Timeouts      → connect-slow vs read-slow?
2. TLS/SSL        → cert valid and trusted?
3. Auth           → credentials correct and unexpired?
4. Request format → payload shape match server expectations?
5. Response parse → does our code accept what came back?
6. Semantics      → does the data mean what we assume?
```

## Быстрый старт за 5 минут

### REST через терминал

```python
# Verbose request/response exchange
terminal('curl -v https://api.example.com/users/1')

# POST with JSON
terminal("""curl -X POST https://api.example.com/users \\
  -H 'Content-Type: application/json' \\
  -H "Authorization: Bearer $TOKEN" \\
  -d '{"name":"test","email":"test@example.com"}'""")

# Headers only
terminal('curl -sI https://api.example.com/health')

# Pretty-print JSON
terminal('curl -s https://api.example.com/users | python3 -m json.tool')
```

### GraphQL через терминал

```python
terminal("""curl -X POST https://api.example.com/graphql \\
  -H 'Content-Type: application/json' \\
  -H "Authorization: Bearer $TOKEN" \\
  -d '{"query":"{ user(id: 1) { name email } }"}'""")
```

**Подводный камень GraphQL:** серверы часто возвращают HTTP 200 даже когда запрос завершился ошибкой. Всегда проверяй поле `errors`, независимо от кода статуса:

```python
execute_code('''
import os, requests
resp = requests.post(
    "https://api.example.com/graphql",
    json={"query": "{ user(id: 1) { name email } }"},
    headers={"Authorization": f"Bearer {os.environ['TOKEN']}"},
    timeout=10,
)
data = resp.json()
if data.get("errors"):
    for err in data["errors"]:
        print(f"GraphQL error: {err['message']} (path: {err.get('path')})")
print(data.get("data"))
''')
```

### Python (requests) через execute_code

```python
execute_code('''
import requests
resp = requests.get(
    "https://api.example.com/users/1",
    headers={"Authorization": "Bearer <TOKEN>"},
    timeout=(3.05, 30),  # (connect, read)
)
print(resp.status_code, dict(resp.headers))
print(resp.text[:500])
''')
```

## Поэтапный поток отладки

### Шаг 1 — Связность

```python
terminal('nslookup api.example.com')
terminal('curl -v --connect-timeout 5 https://api.example.com/health')
```

Сбои: DNS не резолвит, фаервол, требуется VPN, отсутствует прокси.

### Шаг 1.5 — Тайм‑ауты

Различай *не может достучаться* от *достучается, но медленно*:

```python
terminal('''curl -w "dns:%{time_namelookup}s connect:%{time_connect}s tls:%{time_appconnect}s ttfb:%{time_starttransfer}s total:%{time_total}s\\n" \\
  -o /dev/null -s https://api.example.com/endpoint''')
```

В Python всегда передавай кортеж тайм‑аутов — у `requests` нет значения по умолчанию и он будет ждать вечно:

```python
execute_code('''
import requests
from requests.exceptions import ConnectTimeout, ReadTimeout
try:
    requests.get(url, timeout=(3.05, 30))
except ConnectTimeout:
    print("Cannot reach host — DNS, firewall, VPN")
except ReadTimeout:
    print("Connected but server is slow")
''')
```

Диагностика: высокий `time_connect` — сеть/фаервол; высокий `time_starttransfer` при низком `time_connect` — медленный сервер.

### Шаг 2 — TLS/SSL

```python
terminal('curl -vI https://api.example.com 2>&1 | grep -E "SSL|subject|expire|issuer"')
```

Сбои: просроченный сертификат, самоподписанный, несовпадение имени хоста, отсутствие CA‑bundle. Используй `-k` только для ад‑хок отладки, никогда в продакшене.

### Шаг 3 — Аутентификация

```python
# Token validity check
terminal('curl -s -o /dev/null -w "%{http_code}\\n" -H "Authorization: Bearer $TOKEN" https://api.example.com/me')

# Decode JWT exp claim — handles base64url padding correctly
execute_code('''
import json, base64, os
tok = os.environ["TOKEN"]
payload = tok.split(".")[1]
payload += "=" * (-len(payload) % 4)
print(json.dumps(json.loads(base64.urlsafe_b64decode(payload)), indent=2))
''')
```

Контрольный список:
- Токен просрочен? (`exp`‑клейм в JWT)
- Правильная схема? Bearer vs Basic vs Token vs `X-Api-Key`
- Правильное окружение? Ключ staging в продакшене — классика
- API‑key в заголовке vs параметре запроса (`?api_key=…`)?

### Шаг 4 — Формат запроса

```python
terminal("""curl -v -X POST https://api.example.com/endpoint \\
  -H 'Content-Type: application/json' \\
  -d '{"key":"value"}' 2>&1""")
```

**Несоответствие Content‑Type / тела — тихий 415/400:**

```python
# WRONG — data= sends form-encoded, header lies
requests.post(url, data='{"k":"v"}', headers={"Content-Type": "application/json"})

# RIGHT — json= auto-sets header AND serializes
requests.post(url, json={"k": "v"})

# WRONG — Accept says XML, code calls .json()
requests.get(url, headers={"Accept": "text/xml"})

# RIGHT — let requests build multipart with boundary
requests.post(url, files={"file": open("doc.pdf", "rb")})
```

Часто: form‑encoded vs JSON, отсутствуют обязательные поля, неверный HTTP‑метод, неэкранированные параметры запроса.

### Шаг 5 — Парсинг ответа

Всегда проверяй `content-type` перед вызовом `.json()`:

```python
execute_code('''
import requests
resp = requests.post(url, json=payload, timeout=10)
print(f"status={resp.status_code}")
print(f"headers={dict(resp.headers)}")
ct = resp.headers.get("Content-Type", "")
if "application/json" in ct:
    print(resp.json())
else:
    print(f"unexpected content-type {ct!r}, body={resp.text[:500]!r}")
''')
```

Сбои: HTML‑страница ошибки вместо ожидаемого JSON, пустое тело, неверная кодировка.

### Шаг 6 — Семантическая валидация

Ответ успешно распарсен — но данные *правильные*?

- Значит ли `"status": "active"` то, что ожидает твой код?
- Совпадает ли ID в ответе с запрошенным?
- В нужном ли часовом поясе тайм‑стемпы?
- Пагинация возвращает все результаты или только страницу 1?

## Справочник по HTTP‑статусам

### 401 Unauthorized — отсутствуют или недействительны учётные данные

1. Заголовок `Authorization` действительно присутствует? (`curl -v` для проверки)
2. Токен корректен и не просрочен?
3. Правильная схема аутентификации? (`Bearer` vs `Basic` vs `Token`)
4. Некоторые API используют параметр запроса (`?api_key=…`) вместо заголовка.

### 403 Forbidden — аутентифицирован, но нет доступа

1. Токен имеет необходимые scopes/permissions?
2. Ресурс принадлежит другому аккаунту?
3. Список разрешённых IP‑адресов блокирует тебя?
4. CORS в браузере? (проверь `Access-Control-Allow-Origin`)

### 404 Not Found — ресурс не существует или URL неверен

1. Путь правильный? (конечный слеш, опечатка, префикс версии)
2. Существует ли указанный ID ресурса?
3. Правильная версия API (`/v1/` vs `/v2/`)?
4. Правильный базовый URL (staging vs prod)?

### 409 Conflict — конфликт состояния

1. Ресурс уже существует (повторное создание)?
2. Устаревший `ETag` / `If-Match`?
3. Одновременное изменение другим процессом?

### 422 Unprocessable Entity — корректный JSON, некорректные данные

Тело ошибки обычно указывает плохие поля. Проверь:
- Типы полей (string vs int, формат даты)
- Обязательные vs необязательные
- Значения enum находятся в разрешённом наборе

### 429 Too Many Requests — ограничение по частоте

Проверь заголовки `Retry-After` и `X-RateLimit-*`. Экспоненциальный бэкофф:

```python
execute_code('''
import time, requests

def with_backoff(method, url, **kwargs):
    for attempt in range(5):
        resp = requests.request(method, url, **kwargs)
        if resp.status_code != 429:
            return resp
        wait = int(resp.headers.get("Retry-After", 2 ** attempt))
        time.sleep(wait)
    return resp
''')
```

### 5xx — ошибки сервера, обычно не твоя вина

- **500** — баг сервера. Сохрани correlation ID, открой тикет у провайдера.
- **502** — upstream недоступен. Бэкофф + повтор.
- **503** — перегрузка / обслуживание. Проверь статус‑страницу.
- **504** — тайм‑аут upstream. Уменьши нагрузку или увеличь тайм‑аут.

Для всех 5xx: бэкофф с джиттером, сигнализировать при постоянных ошибках.

## Пагинация и идемпотентность

**Пагинация.** Убедись, что получаешь *все* результаты. Ищи `next_cursor`, `next_page`, `total_count`. Два паттерна:
- Offset (`?limit=100&offset=200`) — простой, может пропустить элементы при сдвиге данных.
- Cursor (`?cursor=abc123`) — предпочтительный для живых или больших наборов данных.

**Идемпотентность.** Для неидемпотентных операций (POST) отправляй `Idempotency-Key: <uuid>`, чтобы повторные запросы не приводили к двойному списанию / двойному созданию. Обязательно для платежей и заказов.

## Валидация контракта

Лови дрейф схемы до того, как он попадёт в продакшн:

```python
execute_code('''
import requests

def validate_user(data: dict) -> list[str]:
    errors = []
    required = {"id": int, "email": str, "created_at": str}
    for field, expected in required.items():
        if field not in data:
            errors.append(f"missing field: {field}")
        elif not isinstance(data[field], expected):
            errors.append(f"{field}: want {expected.__name__}, got {type(data[field]).__name__}")
    return errors

resp = requests.get(f"{BASE}/users/1", headers=HEADERS, timeout=10)
issues = validate_user(resp.json())
if issues:
    print(f"contract violations: {issues}")
''')
```

Запускай после обновления API, при интеграции новых сторонних сервисов или в CI‑smoke‑тестах.

## Correlation IDs

Всегда сохраняй ID запроса от провайдера — самый быстрый путь к поддержке поставщика:

```python
execute_code('''
import requests
resp = requests.post(url, json=payload, headers=headers, timeout=10)
request_id = (
    resp.headers.get("X-Request-Id")
    or resp.headers.get("X-Trace-Id")
    or resp.headers.get("CF-Ray")  # Cloudflare
)
if resp.status_code >= 400:
    print(f"failed status={resp.status_code} req_id={request_id} ts={resp.headers.get('Date')}")
''')
```

**Шаблон отчёта об ошибке поставщика:**

```
Endpoint:    POST /api/v1/orders
Request ID:  req_abc123xyz
Timestamp:   2026-03-17T14:30:00Z
Status:      500
Expected:    201 with order object
Actual:      500 {"error":"internal server error"}
Repro:       curl -X POST … (auth: <REDACTED>)
```

## Шаблон регрессионного теста

Помести это в `tests/` и запусти через `terminal('pytest tests/test_api_smoke.py -v')`:

```python
import os, requests, pytest

BASE_URL = os.environ.get("API_BASE_URL", "https://api.example.com")
TOKEN    = os.environ.get("API_TOKEN", "")
HEADERS  = {"Authorization": f"Bearer {TOKEN}"}

class TestAPISmoke:
    def test_health(self):
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        assert resp.status_code == 200

    def test_list_users_returns_array(self):
        resp = requests.get(f"{BASE_URL}/users", headers=HEADERS, timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data.get("data", data), list)

    def test_get_user_required_fields(self):
        resp = requests.get(f"{BASE_URL}/users/1", headers=HEADERS, timeout=10)
        assert resp.status_code in (200, 404)
        if resp.status_code == 200:
            user = resp.json()
            assert "id" in user and "email" in user

    def test_invalid_auth_returns_401(self):
        resp = requests.get(
            f"{BASE_URL}/users",
            headers={"Authorization": "Bearer invalid-token"},
            timeout=10,
        )
        assert resp.status_code == 401
```

## Безопасность

### Обращение с токенами
- Никогда не логируй полные токены. Замаскируй: `Bearer <REDACTED>`.
- Никогда не хардкодь токены в скриптах. Читай из переменных окружения (`os.environ["API_TOKEN"]`) или `~/.hermes/.env`.
- Немедленно ротируй, если токен попал в логи, сообщения об ошибках или историю git.

### Безопасное логирование

```python
def redact_auth(headers: dict) -> dict:
    sensitive = {"authorization", "x-api-key", "cookie", "set-cookie"}
    return {k: ("<REDACTED>" if k.lower() in sensitive else v) for k, v in headers.items()}
```

### Чек‑лист утечек

- [ ] **Учётные данные в URL.** API‑key в строке запроса попадают в логи сервера, историю браузера, заголовки referrer — используй заголовки.
- [ ] **PII в ошибочных ответах.** `404 on /users/123` не должен раскрывать, существует ли пользователь (enumeration).
- [ ] **Стек‑трейсы в продакшене.** 500‑ки не должны раскрывать пути к файлам, версии фреймворков.
- [ ] **Внутренние имена хостов/IP.** `10.x.x.x`, `internal-api.corp.local` в теле ошибки.
- [ ] **Токены, отражённые обратно.** Некоторые API включают токен в детали ошибки. Убедись, что они не попадают наружу.
- [ ] **Подробный `Server` / `X-Powered-By`.** Утечки информации о стеке. Учти при аудите безопасности.

## Шаблоны инструментов Hermes

### terminal — для curl, dig, openssl

```python
terminal('curl -sI https://api.example.com')
terminal('openssl s_client -connect api.example.com:443 -servername api.example.com </dev/null 2>/dev/null | openssl x509 -noout -dates')
```

### execute_code — для многошаговых Python‑процессов

Когда отладка охватывает auth → fetch → paginate → validate, используй `execute_code`. Переменные сохраняются в скрипте, результаты выводятся в stdout, риск спама токенов в контексте отсутствует:

```python
execute_code('''
import os, requests

token = os.environ["API_TOKEN"]
base  = "https://api.example.com"
H     = {"Authorization": f"Bearer {token}"}

# 1. auth
me = requests.get(f"{base}/me", headers=H, timeout=10)
print(f"auth {me.status_code}")

# 2. paginate
all_users, cursor = [], None
while True:
    params = {"cursor": cursor} if cursor else {}
    r = requests.get(f"{base}/users", headers=H, params=params, timeout=10)
    body = r.json()
    all_users.extend(body["data"])
    cursor = body.get("next_cursor")
    if not cursor:
        break
print(f"users={len(all_users)}")
''')
```

### web_extract — для документации API поставщика

Получай спецификацию нужного эндпоинта вместо угадываний:

```python
web_extract(urls=["https://docs.example.com/api/v1/users"])
```

### delegate_task — для полного тестового охвата CRUD

```python
delegate_task(
    goal="Test all CRUD endpoints for /api/v1/users",
    context="""
Follow the rest-graphql-debug skill (optional-skills/software-development/rest-graphql-debug).
Base URL: https://api.example.com
Auth: Bearer token from API_TOKEN env var.

For each verb (POST, GET, PATCH, DELETE):
  - happy path: assert status + response schema
  - error cases: 400, 404, 422
  - log a repro curl for any failure (redact tokens)

Output: pass/fail per endpoint + correlation IDs for failures.
""",
    toolsets=["terminal", "file"],
)
```

## Формат вывода

При отчёте о находках:

```
## Finding
Endpoint: POST /api/v1/users
Status:   422 Unprocessable Entity
Req ID:   req_abc123xyz

## Repro
curl -X POST https://api.example.com/api/v1/users \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <REDACTED>' \
  -d '{"name":"test"}'

## Root Cause
Missing required field `email`. Server validation rejects before processing.

## Fix
-d '{"name":"test","email":"test@example.com"}'
```

## Связанные

- `systematic-debugging` — после изоляции проблемного слоя API, выяви коренную причину в коде
- `test-driven-development` — напиши регрессионный тест перед тем, как выпускать исправление