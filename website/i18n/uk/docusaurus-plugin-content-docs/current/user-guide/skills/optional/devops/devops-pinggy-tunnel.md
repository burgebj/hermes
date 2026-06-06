---
title: "Pinggy Tunnel — тунелі localhost без встановлення через SSH за допомогою Pinggy"
sidebar_label: "Pinggy Tunnel"
description: "Тунелі localhost без встановлення через SSH за допомогою Pinggy"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Pinggy Tunnel

Тунелі localhost без встановлення через SSH за допомогою Pinggy.
## Метадані навички

| | |
|---|---|
| Джерело | Опціонально — встановити за допомогою `hermes skills install official/devops/pinggy-tunnel` |
| Шлях | `optional-skills/devops/pinggy-tunnel` |
| Версія | `0.1.0` |
| Автор | Teknium (teknium1), Hermes Agent |
| Ліцензія | MIT |
| Платформи | linux, macos, windows |
| Теги | `Pinggy`, `Tunnel`, `Networking`, `SSH`, `Webhook`, `Localhost` |
| Пов’язані навички | `cloudflared-quick-tunnel`, [`webhook-subscriptions`](/docs/user-guide/skills/bundled/devops/devops-webhook-subscriptions) |
:::info
Наступне — повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції, коли навичка активна.
:::

# Навичка Pinggy Tunnel

Відкрий локальну службу (dev‑сервер, отримувач веб‑хуків, MCP‑endpoint, демо) у публічний інтернет за допомогою зворотного SSH‑тунелю Pinggy. Не потрібно встановлювати демон — стандартний SSH‑клієнт користувача підключається до `a.pinggy.io:443`, а Pinggy повертає публічну URL‑адресу HTTP/HTTPS.

Безкоштовний тариф: 60‑хвилинні тунелі, випадковий піддомен, без реєстрації. Платний тариф ($3/міс) — опціональний, за токеном.
## Коли використовувати

- Користувач просить «викрити це локально», «поділитися моїм dev‑сервером», «зробити цей URL публічним», «тунелювати порт N», «отримати публічний URL для webhook».
- Потрібно отримати зворотний виклик webhook під час локального завдання (Stripe, GitHub, Discord, AgentMail).
- Потрібно поділитися одноразовою HTTP‑демо (MCP‑сервер, Ollama/vLLM endpoint, dashboard) з віддаленою стороною.
- На хості є SSH, але немає бінарника `cloudflared` / `ngrok`, і його встановлення було б зайвим.

Якщо на хості вже налаштовано `cloudflared`, віддавай перевагу навичці `cloudflared-quick-tunnel` — швидкі тунелі Cloudflare не закінчуються через 60 хвилин.
## Вимоги

- `ssh` у PATH (`ssh -V`). За замовчуванням на Linux, macOS та Windows 10+. Інших встановлень не потрібно.
- Локальна служба, що слухає `127.0.0.1:<port>` до запуску тунелю. Pinggy поверне URL‑и, але вони будуть повертати 502, доки локальна служба не запуститься.

**Необов’язково:**

- змінна середовища `PINGGY_TOKEN` для платних Pro‑функцій (постійний піддомен, власний домен, кілька тунелів, без обмеження у 60 хвилин). Безкоштовний рівень не потребує облікових даних.
## Коротка довідка

```bash
# Plain HTTP/HTTPS tunnel for port 8000 (free tier)
ssh -p 443 -o StrictHostKeyChecking=no -o ServerAliveInterval=30 \
    -R0:localhost:8000 free@a.pinggy.io

# TCP tunnel (databases, raw SSH, etc.)
ssh -p 443 -o StrictHostKeyChecking=no -R0:localhost:5432 tcp@a.pinggy.io

# TLS tunnel (Pinggy can't decrypt — bring your own certs at origin)
ssh -p 443 -o StrictHostKeyChecking=no -R0:localhost:443 tls@a.pinggy.io

# Basic auth gate (b:user:pass)
ssh -p 443 -o StrictHostKeyChecking=no -R0:localhost:8000 \
    "b:admin:secret+free@a.pinggy.io"

# Bearer token gate (k:token)
ssh -p 443 -o StrictHostKeyChecking=no -R0:localhost:8000 \
    "k:mysecrettoken+free@a.pinggy.io"

# IP whitelist (w:CIDR)
ssh -p 443 -o StrictHostKeyChecking=no -R0:localhost:8000 \
    "w:203.0.113.0/24+free@a.pinggy.io"

# Enable CORS + force HTTPS redirect
ssh -p 443 -o StrictHostKeyChecking=no -R0:localhost:8000 \
    "co+x:https+free@a.pinggy.io"

# Pro tier (persistent URL, no 60-min cap)
ssh -p 443 -o StrictHostKeyChecking=no -R0:localhost:8000 "$PINGGY_TOKEN+a.pinggy.io"
```
## Процедура — Запуск тунелю та отримання URL

Модель ПОВИННА використовувати інструмент `terminal`. Тунель має залишатися активним протягом усього часу спільного доступу, тому запусти його як фоновий процес і отримай публічний URL зі stdout.

### 1. Підтверди, що локальна сесія працює

```bash
curl -sI http://127.0.0.1:8000/ | head -1
# expect HTTP/1.x 200 (or any non-connection-refused response)
```

Якщо ще нічого не слухає, спочатку запусти її (наприклад `python3 -m http.server 8000 --bind 127.0.0.1`). Pinggy з радістю поверне URL, який вказує ніде — користувач побачить 502, доки сесія не підніметься.

### 2. Запусти тунель як фоновий процес

Використай `terminal(background=True)` і збережи вивід у файл журналу (Pinggy виводить URL у stdout, а потім тримає з’єднання відкритим):

```bash
LOG=/tmp/pinggy-8000.log
nohup ssh -p 443 \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    -R0:localhost:8000 free@a.pinggy.io \
    > "$LOG" 2>&1 &
echo $! > /tmp/pinggy-8000.pid
```

`StrictHostKeyChecking=no` + `UserKnownHostsFile=/dev/null` пропускає запит про ключ хоста під час першого запуску. `ServerAliveInterval=30` запобігає розриву SSH‑сесії через бездіяльність NAT.

### 3. Витягни URL з журналу

```bash
sleep 4
grep -oE 'https://[a-z0-9-]+\.[a-z]+\.pinggy\.link' /tmp/pinggy-8000.log | head -1
```

Очікуваний вивід виглядає так:

```
You are not authenticated.
Your tunnel will expire in 60 minutes.
http://yqycl-98-162-69-48.a.free.pinggy.link
https://yqycl-98-162-69-48.a.free.pinggy.link
```

Передай користувачеві URL `https://...pinggy.link`.

### 4. Перевірка

```bash
curl -sI https://<the-url>/ | head -3
# expect 200/302/whatever the local origin actually returns
```

Якщо отримуєш `502 Bad Gateway`, SSH‑сесія активна, але локальна сесія не слухає — спочатку виправ крок 1.

### 5. Припинення роботи

```bash
kill "$(cat /tmp/pinggy-8000.pid)"
# or, if the pid file got lost:
pkill -f 'ssh -p 443 .* free@a\.pinggy\.io'
```

Якщо у тебе є `session_id` від `terminal(background=True)`, віддай перевагу `process(action='kill', session_id=...)`.
## Контроль доступу за допомогою ключових слів у імені користувача

Pinggy збирає прапорці керування в ім’я користувача SSH, розділяючи їх символом `+`. Завжди беріть у лапки весь аргумент `user@host`, коли він містить `+`:

| Ключове слово | Ефект |
|---------------|-------|
| `b:user:pass` | gateway HTTP Basic auth |
| `k:token` | gateway заголовка Bearer‑token (`Authorization: Bearer <token>`) |
| `w:CIDR` | білий список IP (один IP або CIDR, можна повторювати) |
| `co` | Додати `Access-Control-Allow-Origin: *` (CORS) |
| `x:https` | Примусово HTTPS — автоматичне перенаправлення HTTP на HTTPS |
| `a:Name:Value` | Додати заголовок запиту |
| `u:Name:Value` | Оновити заголовок запиту |
| `r:Name` | Видалити заголовок запиту |
| `qr` | Вивести QR‑код URL у stdout (зручно для мобільного поширення) |

Комбінуйте довільно: `"b:admin:secret+co+x:https+free@a.pinggy.io"`.
## Web Debugger (optional)

Pinggy може дзеркалити вхідний трафік до `localhost:4300` для перевірки. Додай локальне перенаправлення до команди SSH:

```bash
ssh -p 443 -L4300:localhost:4300 -R0:localhost:8000 free@a.pinggy.io
```

Потім відкрий `http://localhost:4300` у браузері, щоб побачити живі пари запит/відповідь.
## Підводні камені

- **60‑хвилинний жорсткий ліміт у безкоштовному тарифі.** SSH‑сесія завершується на 60‑й хвилині; URL стає недоступним. Для довших підключень використай `PINGGY_TOKEN` (Pro) або автоперезапуск у циклі оболонки (зауваж, що URL змінюється при кожному перезапуску у безкоштовному тарифі).
- **URL безкоштовного тарифу випадковий і змінюється при перезапуску.** Не додавай його в закладки, не вставляй у файл конфігурації. Перепарсь його щоразу з журналу.
- **Одночасні безкоштовні тунелі обмежені одним на IP‑джерело.** Запуск другого тунелю з того ж комп’ютера зазвичай вбиває перший. У Pro‑тарифі це обмеження знято.
- **`+` у іменах користувачів треба брати в лапки.** Прямий `ssh ... b:admin:secret+free@a.pinggy.io` працює в bash, але ламається в оболонках, які спеціально обробляють `+`, або при програмному складанні. Завжди обгорни в подвійні лапки.
- **Не тунелюй нічого конфіденційного без прапорця контролю доступу.** Прямий HTTP‑тунель доступний будь‑кому, хто має URL. Використовуй `b:`, `k:` або `w:` для непублічних сервісів.
- **`process(action='log')` може пропустити вивід банера SSH.** Pinggy виводить URL, а потім SSH‑сесія переходить у інтерактивний режим. Завжди перенаправляй у файл журналу і `grep` його безпосередньо — той самий шаблон, що й у `cloudflared-quick-tunnel`.
- **Запит ключа хоста під час першого запуску.** За замовчуванням конфігурація OpenSSH просить користувача прийняти хост‑ключ Pinggy. Для безконтрольних запусків завжди додавай `-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null`.
- **TCP‑ і TLS‑тунелі повертають пару `<subdomain>.a.pinggy.online:<port>`, а не https‑URL.** Парсь їх іншим регулярним виразом (`tcp://` і порт). Не припускай, що кожен тунель Pinggy — це HTTP.
- **У Pro‑режимі токен використовується як ім’я користувача, а не як прапорець.** Використовуй `"$PINGGY_TOKEN+a.pinggy.io"` (без `free@`). З токеном можна також додати `:persistent` для стабільного піддомену — дивись `pinggy.io/docs/`.
## Рецепти

Комбіновані шаблони, що поєднують локальне походження з тунелем Pinggy. Кожен рецепт самодостатній — запусти походження, запусти тунель, розбери URL, передай його користувачеві.

### Рецепт 1 — Отримати виклик веб‑хука

Використовуй, коли зовнішня служба (Stripe, GitHub, Discord, AgentMail тощо) повинна виконати `POST` на публічно доступний URL під час локального завдання.

```bash
# 1. Tiny capturing server: every request gets appended to /tmp/webhook-hits.log
cat >/tmp/webhook-server.py <<'PY'
import http.server, json, datetime, pathlib
LOG = pathlib.Path("/tmp/webhook-hits.log")
class H(http.server.BaseHTTPRequestHandler):
    def _capture(self):
        n = int(self.headers.get("content-length") or 0)
        body = self.rfile.read(n).decode("utf-8", "replace") if n else ""
        rec = {"t": datetime.datetime.utcnow().isoformat(), "path": self.path,
               "method": self.command, "headers": dict(self.headers), "body": body}
        with LOG.open("a") as f: f.write(json.dumps(rec) + "\n")
        self.send_response(200); self.send_header("content-type","application/json")
        self.end_headers(); self.wfile.write(b'{"ok":true}\n')
    def do_GET(self): self._capture()
    def do_POST(self): self._capture()
    def log_message(self,*a,**k): pass
http.server.HTTPServer(("127.0.0.1", 18080), H).serve_forever()
PY
nohup python3 /tmp/webhook-server.py >/tmp/webhook-server.log 2>&1 &
echo $! >/tmp/webhook-server.pid

# 2. Tunnel — bearer-token-gate so randos can't pollute the capture log
nohup ssh -p 443 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    -o ServerAliveInterval=30 \
    -R0:localhost:18080 "k:$(openssl rand -hex 12)+free@a.pinggy.io" \
    >/tmp/webhook-pinggy.log 2>&1 &
echo $! >/tmp/webhook-pinggy.pid
sleep 5
URL=$(grep -oE 'https://[a-z0-9-]+\.[a-z]+\.pinggy\.link' /tmp/webhook-pinggy.log | head -1)
echo "Webhook URL: $URL"

# 3. While the agent works, watch hits land
tail -f /tmp/webhook-hits.log
```

Передай `$URL` службі, якій потрібно викликати тебе. При завершенні: `kill $(cat /tmp/webhook-server.pid) $(cat /tmp/webhook-pinggy.pid)`.

### Рецепт 2 — Відкрити сервер MCP через HTTP/SSE

Використовуй, коли віддалений клієнт MCP (Claude Desktop на іншій машині, редактор колеги тощо) потребує доступу до сервера MCP, що працює на локальній машині. Працює лише для серверів MCP, які спілкуються по HTTP‑транспорту — сервери у режимі stdio‑mode не можна тунелювати.

```bash
# 1. Start the MCP server in HTTP mode (example: a FastMCP server on port 8765)
nohup python3 my_mcp_server.py --transport http --port 8765 \
    >/tmp/mcp-server.log 2>&1 &
echo $! >/tmp/mcp-server.pid

# 2. Tunnel with a bearer token — MCP traffic should not be open to the internet
TOKEN=$(openssl rand -hex 16)
nohup ssh -p 443 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    -o ServerAliveInterval=30 \
    -R0:localhost:8765 "k:$TOKEN+free@a.pinggy.io" \
    >/tmp/mcp-pinggy.log 2>&1 &
echo $! >/tmp/mcp-pinggy.pid
sleep 5
URL=$(grep -oE 'https://[a-z0-9-]+\.[a-z]+\.pinggy\.link' /tmp/mcp-pinggy.log | head -1)
echo "MCP URL: $URL"
echo "Bearer token: $TOKEN"
```

Віддалений клієнт підключається до `$URL` з заголовком `Authorization: Bearer $TOKEN`. Конфігурація власного нативного клієнта MCP Hermes: `{"transport": "http", "url": "<URL>", "headers": {"Authorization": "Bearer <TOKEN>"}}`.

### Рецепт 3 — Відкрити локальну точку доступу LLM (Ollama / vLLM / llama.cpp)

Поділися локальною моделлю з віддаленим викликачем (іншим агентом, телефоном, колегою). Ollama слухає на `:11434`, vLLM і llama.cpp зазвичай на `:8000`.

```bash
# Pre-req: the model server is already running on 127.0.0.1:11434 (Ollama default)
TOKEN=$(openssl rand -hex 16)
nohup ssh -p 443 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    -o ServerAliveInterval=30 \
    -R0:localhost:11434 "k:$TOKEN+co+free@a.pinggy.io" \
    >/tmp/llm-pinggy.log 2>&1 &
echo $! >/tmp/llm-pinggy.pid
sleep 5
URL=$(grep -oE 'https://[a-z0-9-]+\.[a-z]+\.pinggy\.link' /tmp/llm-pinggy.log | head -1)
echo "Endpoint: $URL"
echo "Token:    $TOKEN"

# Verify
curl -s "$URL/api/tags" -H "Authorization: Bearer $TOKEN" | head
```

`co` вмикає CORS, щоб викликач у браузері міг звертатися до точки доступу. Прибери `co` для викликачів лише бекенду. Для сумісної з OpenAI точки доступу vLLM/llama.cpp викликачі використовують базовий URL `$URL/v1` з заголовком `Authorization: Bearer $TOKEN` — але зауваж, що Pinggy не змінює і не видаляє нічого в тілі запиту, тому сервер моделі бачить токен Pinggy; локальний сервер слід налаштувати ігнорувати автентифікацію (він вже працює на `127.0.0.1`) і дозволити Pinggy виконувати контроль доступу.

### Рецепт 4 — Поділитися dev‑сервером з одноразовим паролем

Найшвидший шаблон «дозволь колезі поекспериментувати з моїм запущеним застосунком». Випадковий пароль, виводиться один раз, завершується при `Ctrl‑C`.

```bash
PASS=$(openssl rand -base64 12 | tr -d '+/=' | head -c 12)
echo "Dev server password: $PASS"
ssh -p 443 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    -o ServerAliveInterval=30 \
    -R0:localhost:3000 "b:dev:$PASS+co+x:https+free@a.pinggy.io"
# URL prints to the terminal. Share URL + password. Ctrl-C to tear down.
```

`b:dev:$PASS` захищає URL за допомогою HTTP Basic auth. `x:https` примушує використання TLS. `co` додає CORS для SPA‑фронтендів.
## Перевірка

```bash
# End-to-end: spin up a trivial origin, tunnel it, hit it, tear down
python3 -m http.server 18000 --bind 127.0.0.1 >/tmp/origin.log 2>&1 &
ORIGIN_PID=$!

nohup ssh -p 443 \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -R0:localhost:18000 free@a.pinggy.io >/tmp/pinggy-verify.log 2>&1 &
SSH_PID=$!

sleep 5
URL=$(grep -oE 'https://[a-z0-9-]+\.[a-z]+\.pinggy\.link' /tmp/pinggy-verify.log | head -1)
echo "URL: $URL"
curl -sI "$URL/" | head -1

kill "$SSH_PID" "$ORIGIN_PID"
```

Очікується: URL `pinggy.link` та статус `HTTP/2 200` у відповіді curl (HEAD).