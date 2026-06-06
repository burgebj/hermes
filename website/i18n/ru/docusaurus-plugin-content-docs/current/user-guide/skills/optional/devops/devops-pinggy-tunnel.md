---
title: "Pinggy Tunnel — туннели localhost без установки через SSH с помощью Pinggy"
sidebar_label: "Pinggy Tunnel"
description: "Туннели localhost без установки через SSH с помощью Pinggy"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Туннель Pinggy

Туннели localhost без установки, работающие через SSH, с помощью Pinggy.
## Метаданные навыка

| | |
|---|---|
| Источник | Необязательно — установить с помощью `hermes skills install official/devops/pinggy-tunnel` |
| Путь | `optional-skills/devops/pinggy-tunnel` |
| Версия | `0.1.0` |
| Автор | Teknium (teknium1), Hermes Agent |
| Лицензия | MIT |
| Платформы | linux, macos, windows |
| Теги | `Pinggy`, `Tunnel`, `Networking`, `SSH`, `Webhook`, `Localhost` |
| Связанные навыки | `cloudflared-quick-tunnel`, [`webhook-subscriptions`](/docs/user-guide/skills/bundled/devops/devops-webhook-subscriptions) |
:::info
Следующее — полное определение навыка, которое Hermes загружает, когда этот навык вызывается. Это то, что агент видит как инструкции, когда навык активен.
:::

# Навык Pinggy Tunnel

Открой локальный сервис (dev‑сервер, получатель веб‑хуков, MCP‑endpoint, демо) в публичный интернет с помощью обратного SSH‑туннеля Pinggy. Не требуется установка демона — штатный SSH‑клиент пользователя подключается к `a.pinggy.io:443`, а Pinggy возвращает публичный URL HTTP/HTTPS.

Бесплатный тариф: туннели до 60 минут, случайный поддомен, без регистрации. Платный тариф ($3/мес) — опциональный, с токеном.
## Когда использовать

- Пользователь хочет «выставить это локально», «поделиться моим dev‑сервером», «сделать этот URL публичным», «прокинуть порт N», «получить публичный URL для веб‑хука».
- Нужно получать обратный вызов веб‑хука во время локальной задачи (Stripe, GitHub, Discord, AgentMail).
- Требуется быстро продемонстрировать HTTP‑демо (сервер MCP, конечную точку Ollama/vLLM, дашборд) удалённому участнику.
- На хосте есть SSH, но нет бинарников `cloudflared` / `ngrok`, и их установка была бы избыточной.

Если на хосте уже настроен `cloudflared`, предпочтительнее использовать навык `cloudflared-quick-tunnel` — быстрые туннели Cloudflare не истекают через 60 минут.
## Предварительные требования

- `ssh` в PATH (`ssh -V`). По умолчанию установлен в Linux, macOS и Windows 10+. Других установок не требуется.
- Локальный сервис, прослушивающий `127.0.0.1:<port>` до запуска туннеля. Pinggy будет возвращать URL‑адреса, но они будут выдавать 502, пока локальный сервис недоступен.

Опционально:

- переменная окружения `PINGGY_TOKEN` для платных функций Pro (постоянный поддомен, пользовательский домен, несколько туннелей, отсутствие ограничения в 60 минут). На бесплатном уровне учётные данные не требуются.
## Быстрая справка

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
## Процедура — Запуск туннеля и получение URL

Модель ДОЛЖНА использовать инструмент `terminal`. Туннель должен оставаться активным на протяжении всего сеанса share, поэтому запускай его как фоновый процесс и извлекай публичный URL из stdout.

### 1. Убедись, что локальный источник работает

```bash
curl -sI http://127.0.0.1:8000/ | head -1
# expect HTTP/1.x 200 (or any non-connection-refused response)
```

Если ничего ещё не слушает, запусти его сначала (например, `python3 -m http.server 8000 --bind 127.0.0.1`). Pinggy без проблем вернёт URL, указывающий ни на что — пользователь увидит 502, пока источник не поднимется.

### 2. Запусти туннель как фоновый процесс

Используй `terminal(background=True)` и перенаправь вывод в лог‑файл (Pinggy печатает URL в stdout, а затем держит соединение открытым):

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

`StrictHostKeyChecking=no` + `UserKnownHostsFile=/dev/null` отключают запрос о подтверждении ключа при первом запуске. `ServerAliveInterval=30` не даёт SSH‑сессии завершиться из‑за простоя NAT.

### 3. Выдели URL из лога

```bash
sleep 4
grep -oE 'https://[a-z0-9-]+\.[a-z]+\.pinggy\.link' /tmp/pinggy-8000.log | head -1
```

Ожидаемый вывод выглядит примерно так:

```
You are not authenticated.
Your tunnel will expire in 60 minutes.
http://yqycl-98-162-69-48.a.free.pinggy.link
https://yqycl-98-162-69-48.a.free.pinggy.link
```

Передай пользователю URL вида `https://...pinggy.link`.

### 4. Проверка

```bash
curl -sI https://<the-url>/ | head -3
# expect 200/302/whatever the local origin actually returns
```

Если получаешь `502 Bad Gateway`, SSH‑сессия установлена, но локальный источник не слушает — сначала исправь шаг 1.

### 5. Завершение

```bash
kill "$(cat /tmp/pinggy-8000.pid)"
# or, if the pid file got lost:
pkill -f 'ssh -p 443 .* free@a\.pinggy\.io'
```

Если у тебя есть `session_id`, полученный из `terminal(background=True)`, предпочтительно использовать `process(action='kill', session_id=…)`.
## Управление доступом через ключевые слова в имени пользователя

Pinggy складывает флаги управления в имя пользователя SSH, разделяя их символом `+`. Всегда заключай весь аргумент `user@host` в кавычки, если он содержит `+`:

| Ключевое слово | Эффект |
|----------------|--------|
| `b:user:pass` | шлюз HTTP Basic auth |
| `k:token` | шлюз заголовка Bearer-token (`Authorization: Bearer <token>`) |
| `w:CIDR` | белый список IP (один IP или CIDR, можно указывать несколько раз) |
| `co` | добавить `Access-Control-Allow-Origin: *` (CORS) |
| `x:https` | принудительно HTTPS — автоматическое перенаправление HTTP на HTTPS |
| `a:Name:Value` | добавить заголовок запроса |
| `u:Name:Value` | обновить заголовок запроса |
| `r:Name` | удалить заголовок запроса |
| `qr` | вывести QR‑код URL в stdout (удобно для мобильного обмена) |

Комбинируй произвольно: `"b:admin:secret+co+x:https+free@a.pinggy.io"`.
## Веб‑отладчик (необязательно)

Pinggy может зеркалировать входящий трафик на `localhost:4300` для анализа. Добавь локальный форвард к команде SSH:

```bash
ssh -p 443 -L4300:localhost:4300 -R0:localhost:8000 free@a.pinggy.io
```

Затем открой `http://localhost:4300` в браузере, чтобы увидеть активные пары запрос‑ответ.
## Подводные камни

- **60‑минутный жёсткий лимит на бесплатном тарифе.** SSH‑сессия завершается ровно через 60 минут; URL перестаёт работать. Для более длительных подключений используй `PINGGY_TOKEN` (Pro) или авто‑перезапуск с помощью цикла в оболочке (заметь, что URL меняется при каждом перезапуске в бесплатном тарифе).
- **URL бесплатного тарифа случайный и меняется при перезапуске.** Не сохраняй его в закладки и не вставляй в конфигурационный файл. Каждый раз извлекай его из журнала.
- **Одновременные бесплатные туннели ограничены одним на каждый IP‑источник.** Запуск второго туннеля с той же машины обычно завершает первый. В Pro‑тарифе это ограничение снято.
- **`+` в именах пользователей должно быть заключено в кавычки.** Простой `ssh ... b:admin:secret+free@a.pinggy.io` работает в bash, но ломается в оболочках, которые обрабатывают `+` особым образом, или при программной сборке команды. Всегда оборачивай в двойные кавычки.
- **Не туннелируй ничего конфиденциального без флага контроля доступа.** Обычный HTTP‑туннель доступен каждому, у кого есть URL. Используй `b:`, `k:` или `w:` для непубличных сервисов.
- **`process(action='log')` может пропустить вывод баннера SSH.** Pinggy выводит URL, а затем SSH‑сессия переходит в интерактивный режим. Всегда перенаправляй вывод в файл журнала и ищи его с помощью `grep` — тот же шаблон, что и в `cloudflared-quick-tunnel`.
- **Запрос подтверждения ключа хоста при первом запуске.** Стандартная конфигурация OpenSSH запрашивает у пользователя подтверждение ключа хоста Pinggy. Для автоматических запусков всегда передавай `-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null`.
- **TCP и TLS туннели возвращают пару `<subdomain>.a.pinggy.online:<port>`, а не https‑URL.** Парсить их нужно другим регулярным выражением (`tcp://` и порт). Не предполагай, что каждый туннель Pinggy — это HTTP.
- **В Pro‑режиме токен указывается как имя пользователя, а не как флаг.** Используй `"$PINGGY_TOKEN+a.pinggy.io"` (без `free@`). С токеном также можно добавить `:persistent` для стабильного поддомена — см. `pinggy.io/docs/`.
## Рецепты

Составные шаблоны, комбинирующие локальный origin с туннелем Pinggy. Каждый рецепт автономен — запускай origin, запускай туннель, разбирай URL, передавай его пользователю.

### Рецепт 1 — Получить обратный вызов webhook

Используй, когда внешнему сервису (Stripe, GitHub, Discord, AgentMail и т.д.) нужно выполнить POST на публично доступный URL во время локальной задачи.

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

Передай `$URL` сервису, который должен вызвать тебя. Отключение: `kill $(cat /tmp/webhook-server.pid) $(cat /tmp/webhook-pinggy.pid)`.

### Рецепт 2 — Открыть MCP‑сервер через HTTP/SSE

Используй, когда удалённому MCP‑клиенту (Claude Desktop на другой машине, редактору коллеги и т.п.) нужно подключиться к MCP‑серверу, запущенному на локальном компьютере. Работает только с MCP‑серверами, поддерживающими HTTP‑транспорт — серверы в режиме stdio нельзя туннелировать.

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

Удалённый клиент подключается к `$URL` с заголовком `Authorization: Bearer $TOKEN`. Конфигурация собственного нативного MCP‑клиента Hermes: `{"transport": "http", "url": "<URL>", "headers": {"Authorization": "Bearer <TOKEN>"}}`.

### Рецепт 3 — Открыть локальную точку доступа LLM (Ollama / vLLM / llama.cpp)

Поделись локальной моделью с удалённым вызывающим (другим агентом, телефоном, коллегой). Ollama слушает на `:11434`, vLLM и llama.cpp обычно на `:8000`.

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

`co` включает CORS, чтобы браузерный клиент мог обращаться к точке доступа. Отключи `co` для вызовов только с бекенда. Для совместимой с OpenAI точки доступа vLLM/llama.cpp вызывающие используют базовый URL `$URL/v1` с заголовком `Authorization: Bearer $TOKEN` — но учти, что Pinggy ничего не удаляет и не заменяет в теле запроса, поэтому сервер модели видит токен Pinggy; локальный сервер следует настроить на игнорирование аутентификации (он уже работает на `127.0.0.1`) и позволить Pinggy выполнять проверку доступа.

### Рецепт 4 — Поделиться dev‑сервером с одноразовым паролем

Самый быстрый шаблон «позволь коллеге поиграть с моим запущенным приложением». Случайный пароль выводится один раз, процесс завершается при Ctrl‑C.

```bash
PASS=$(openssl rand -base64 12 | tr -d '+/=' | head -c 12)
echo "Dev server password: $PASS"
ssh -p 443 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    -o ServerAliveInterval=30 \
    -R0:localhost:3000 "b:dev:$PASS+co+x:https+free@a.pinggy.io"
# URL prints to the terminal. Share URL + password. Ctrl-C to tear down.
```

`b:dev:$PASS` защищает URL базовой HTTP‑аутентификацией. `x:https` принудительно включает TLS. `co` добавляет CORS для SPA‑фронтендов.
## Проверка

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

Ожидается: URL `pinggy.link` и статус `HTTP/2 200` в заголовке ответа curl.