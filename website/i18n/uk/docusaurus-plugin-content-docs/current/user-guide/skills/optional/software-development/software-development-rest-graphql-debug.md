---
title: "Rest Graphql Debug — Налагодження REST/GraphQL API: коди стану, автентифікація, схеми, відтворення"
sidebar_label: "Rest Graphql Debug"
description: "Налагоджуй REST/GraphQL APIs: коди статусу, автентифікація, схеми, відтворення"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Rest Graphql Debug

Налагодження REST/GraphQL API: коди статусу, автентифікація, схеми, відтворення.

## Метадані навички

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/software-development/rest-graphql-debug` |
| Path | `optional-skills/software-development/rest-graphql-debug` |
| Version | `1.2.0` |
| Author | eren-karakus0 |
| License | MIT |
| Tags | `api`, `rest`, `graphql`, `http`, `debugging`, `testing`, `curl`, `integration` |
| Related skills | [`systematic-debugging`](/docs/user-guide/skills/bundled/software-development/software-development-systematic-debugging), [`test-driven-development`](/docs/user-guide/skills/bundled/software-development/software-development-test-driven-development) |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# Тестування та налагодження API

Керуйте діагностикою REST і GraphQL за допомогою інструментів Hermes — `terminal` для `curl`, `execute_code` для Python `requests`, `web_extract` для документації постачальника. Ізолюйте проблемний шар перед тим, як вгадувати виправлення.

## Коли використовувати

- API повертає неочікуваний статус або тіло
- Автентифікація не проходить (401/403 після оновлення токену, OAuth, API‑ключ)
- Працює в Postman, але не в коді
- Налагодження інтеграції вебхуків / колбеків
- Створення або перегляд тестів інтеграції API
- Проблеми з обмеженням швидкості або пагінацією

Пропускай для рендерингу UI, налаштування запитів до БД або інфраструктури DNS/фаєрволу (ескаліруй).

## Основний принцип

**Ізолюй шар, потім виправляй.** 200 OK може приховувати пошкоджені дані. 500 може маскувати однобуквену помилку автентифікації. Пройди ланцюжок послідовно; ніколи не пропускай крок.

```
1. Connectivity   → can we reach the host at all?
1.5 Timeouts      → connect-slow vs read-slow?
2. TLS/SSL        → cert valid and trusted?
3. Auth           → credentials correct and unexpired?
4. Request format → payload shape match server expectations?
5. Response parse → does our code accept what came back?
6. Semantics      → does the data mean what we assume?
```

## 5‑хвилинний швидкий старт

### REST через terminal

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

### GraphQL через terminal

```python
terminal("""curl -X POST https://api.example.com/graphql \\
  -H 'Content-Type: application/json' \\
  -H "Authorization: Bearer $TOKEN" \\
  -d '{"query":"{ user(id: 1) { name email } }"}'""")
```

**Підводка в GraphQL:** сервери часто повертають HTTP 200, навіть коли запит не вдався. Завжди перевіряй поле `errors` незалежно від коду статусу:

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

## Багаторівневий процес налагодження

### Крок 1 — З’єднання

```python
terminal('nslookup api.example.com')
terminal('curl -v --connect-timeout 5 https://api.example.com/health')
```

Помилки: DNS не розв’язується, фаєрвол, потрібен VPN, відсутній проксі.

### Крок 1.5 — Тайм‑аути

Відрізняй *не можна дістатися* від *доступно, але повільно*:

```python
terminal('''curl -w "dns:%{time_namelookup}s connect:%{time_connect}s tls:%{time_appconnect}s ttfb:%{time_starttransfer}s total:%{time_total}s\\n" \\
  -o /dev/null -s https://api.example.com/endpoint''')
```

У Python завжди передавай кортеж тайм‑ауту — `requests` не має значення за замовчуванням і буде зависати вічно:

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

Діагностика: високий `time_connect` — мережа/фаєрвол; високий `time_starttransfer` при низькому `time_connect` — повільний сервер.

### Крок 2 — TLS/SSL

```python
terminal('curl -vI https://api.example.com 2>&1 | grep -E "SSL|subject|expire|issuer"')
```

Помилки: прострочений сертифікат, самопідписаний, невідповідність імені хоста, відсутній CA‑bundle. Використовуй `-k` лише для ад‑хок налагодження, ніколи в коді.

### Крок 3 — Автентифікація

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

Контрольний список:
- Токен прострочений? (`exp` claim у JWT)
- Правильна схема? Bearer vs Basic vs Token vs `X-Api-Key`
- Правильне середовище? Ключ staging у продакшені — класика
- API‑ключ у заголовку чи в параметрі запиту (`?api_key=…`)?

### Крок 4 — Формат запиту

```python
terminal("""curl -v -X POST https://api.example.com/endpoint \\
  -H 'Content-Type: application/json' \\
  -d '{"key":"value"}' 2>&1""")
```

**Невідповідність Content‑Type / тіла — тихі 415/400:**

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

Типово: form‑encoded vs JSON, відсутні обов’язкові поля, неправильний HTTP‑метод, неекрановані параметри запиту.

### Крок 5 — Парсинг відповіді

Завжди перевіряй content‑type перед викликом `.json()`:

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

Помилки: HTML‑сторінка помилки замість очікуваного JSON, порожнє тіло, неправильна charset.

### Крок 6 — Семантична валідація

Парсинг успішний — але чи *правильні* дані?

- Чи означає `"status": "active"` те, що твій код очікує?
- Чи збігається ID у відповіді з запитаним?
- Чи у правильному часовому поясі таймстампи?
- Чи повертає пагінація всі результати, чи лише сторінку 1?

## Плейбук HTTP‑статусів

### 401 Unauthorized — відсутні або недійсні облікові дані

1. Чи присутній заголовок `Authorization`? (`curl -v` для перевірки)
2. Токен правильний і не прострочений?
3. Правильна схема автентифікації? (`Bearer` vs `Basic` vs `Token`)
4. Деякі API використовують параметр запиту (`?api_key=…`) замість заголовка.

### 403 Forbidden — автентифіковано, але без дозволу

1. Чи має токен необхідні області/дозволи?
2. Чи належить ресурс іншому акаунту?
3. Чи блокує вас IP‑allowlist?
4. CORS у браузері? (перевірте `Access-Control-Allow-Origin`)

### 404 Not Found — ресурс не існує або URL неправильний

1. Чи правильний шлях? (завершальний слеш, помилка, префікс версії)
2. Чи існує ID ресурсу?
3. Правильна версія API (`/v1/` vs `/v2/`)?
4. Правильний базовий URL (staging vs prod)?

### 409 Conflict — конфлікт стану

1. Ресурс вже існує (дублювання створення)?
2. Застарілий `ETag` / `If-Match`?
3. Конкурентна модифікація іншим процесом?

### 422 Unprocessable Entity — валідний JSON, неправильні дані

Тіло помилки зазвичай називає неправильні поля. Перевірте:
- Типи полів (string vs int, формат дати)
- Обов’язкові vs необов’язкові
- Значення enum у дозволеному наборі

### 429 Too Many Requests — обмеження швидкості

Перевірте заголовки `Retry-After` та `X-RateLimit-*`. Експоненціальне зворотне очікування:

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

### 5xx — помилки сервера, зазвичай не ваша провина

- **500** — баг сервера. Захопіть correlation ID, повідомте провайдера.
- **502** — upstream недоступний. Backoff + retry.
- **503** — перевантаження / технічне обслуговування. Перевірте сторінку статусу.
- **504** — тайм‑аут upstream. Зменшіть payload або збільшіть тайм‑аут.

Для всіх 5xx: backoff з jitter, сповіщення при постійності.

## Пагінація та ідемпотентність

**Пагінація.** Переконайся, що отримуєш *всі* результати. Шукай `next_cursor`, `next_page`, `total_count`. Два патерни:
- Offset (`?limit=100&offset=200`) — простий, може пропускати елементи при зсуві даних.
- Cursor (`?cursor=abc123`) — перевага для живих або великих наборів даних.

**Ідемпотентність.** Для неідемпотентних операцій (POST) надсилай `Idempotency-Key: <uuid>`, щоб повтори не створювали дублікати/подвійні платежі. Обов’язково для платежів та замовлень.

## Валідація контракту

Злови зсув схеми до того, як він потрапить у продакшн:

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

Запускай після оновлень API, при інтеграції нових третіх сторін, або в CI‑smoke тестах.

## Correlation IDs

Завжди захоплюй request ID провайдера — найшвидший шлях до підтримки постачальника:

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

**Шаблон звіту про баг у постачальника:**

```
Endpoint:    POST /api/v1/orders
Request ID:  req_abc123xyz
Timestamp:   2026-03-17T14:30:00Z
Status:      500
Expected:    201 with order object
Actual:      500 {"error":"internal server error"}
Repro:       curl -X POST … (auth: <REDACTED>)
```

## Шаблон регресійного тесту

Помістіть це у `tests/` і запустіть через `terminal('pytest tests/test_api_smoke.py -v')`:

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

## Безпека

### Обробка токенів
- Ніколи не логуй повні токени. Редагуй: `Bearer <REDACTED>`.
- Ніколи не хардкодь токени в скриптах. Читай їх з env (`os.environ["API_TOKEN"]`) або `~/.hermes/.env`.
- Одразу ротируй, якщо токен з’явився в логах, повідомленнях про помилки або історії git.

### Безпечне логування

```python
def redact_auth(headers: dict) -> dict:
    sensitive = {"authorization", "x-api-key", "cookie", "set-cookie"}
    return {k: ("<REDACTED>" if k.lower() in sensitive else v) for k, v in headers.items()}
```

### Чек‑лист витоків

- [ ] **Облікові дані в URL.** API‑ключі в рядках запиту потрапляють у серверні логи, історію браузера, заголовки реферера — використовуйте заголовки.
- [ ] **PII у відповідях про помилки.** `404 on /users/123` не повинно розкривати, чи існує користувач (enumeration).
- [ ] **Стек‑трейси у продакшн.** 500‑ки не повинні розкривати шляхи файлів, версії фреймворків.
- [ ] **Внутрішні імена хостів/IP.** `10.x.x.x`, `internal-api.corp.local` у тілах помилок.
- [ ] **Токени, що повертаються назад.** Деякі API включають токен у деталі помилки. Переконайся, що їх не розкривають.
- [ ] **Verbose `Server` / `X-Powered-By`.** Витік інформації про стек. Врахуй у ревізії безпеки.

## Шаблони інструментів Hermes

### terminal — для curl, dig, openssl

```python
terminal('curl -sI https://api.example.com')
terminal('openssl s_client -connect api.example.com:443 -servername api.example.com </dev/null 2>/dev/null | openssl x509 -noout -dates')
```

### execute_code — для багатокрокових Python процесів

Коли налагоджуєш ланцюжок auth → fetch → paginate → validate, використай `execute_code`. Змінні зберігаються протягом скрипту, результати виводяться у stdout, без ризику спаму токенами у твоєму контексті:

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

### web_extract — для документації API постачальника

Отримай специфікацію для кінцевої точки, яку налагоджуєш, замість вгадування:

```python
web_extract(urls=["https://docs.example.com/api/v1/users"])
```

### delegate_task — для повних CRUD тестових прогонів

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

## Формат виводу

При звітуванні результатів:

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

## Пов’язані

- `systematic-debugging` — коли проблемний шар API ізольовано, знайди корінь проблеми у коді
- `test-driven-development` — напиши регресійний тест перед випуском виправлення