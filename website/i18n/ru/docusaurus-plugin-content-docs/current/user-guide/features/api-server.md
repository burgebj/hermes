---
sidebar_position: 14
title: "API сервер"
description: "Открой hermes-agent как совместимый с OpenAI API для любого фронтенда"
---

# API Server

API‑сервер предоставляет hermes-agent в виде HTTP‑конечной точки, совместимой с OpenAI. Любой фронтенд, поддерживающий формат OpenAI — Open WebUI, LobeChat, LibreChat, NextChat, ChatBox и сотни других — может подключиться к hermes-agent и использовать его как backend.

Твой агент обрабатывает запросы со своим полным набором инструментов (терминал, операции с файлами, веб‑поиск, память, навыки) и возвращает окончательный ответ. При стриминге индикаторы прогресса инструмента отображаются inline, чтобы фронтенды могли показывать, что делает агент.

:::tip One backend covers models + tools
Hermes сам нуждается в настроенном провайдере и бэкендах инструментов, чтобы API‑сервер был полезен. Подписка [Nous Portal](/user-guide/features/tool-gateway) покрывает и то, и другое — более 300 моделей плюс веб/изображения/TTS/браузер через шлюз инструментов. Запусти `hermes setup --portal` один раз перед запуском API‑сервера, и такие фронтенды, как Open WebUI или LobeChat, получат полностью оснащённый инструментами backend.
:::
## Быстрый старт

### 1. Включить API‑сервер

Добавь в `~/.hermes/.env`:

```bash
API_SERVER_ENABLED=true
API_SERVER_KEY=change-me-local-dev
# Optional: only if a browser must call Hermes directly
# API_SERVER_CORS_ORIGINS=http://localhost:3000
```

### 2. Запустить шлюз

```bash
hermes gateway
```

Ты увидишь:

```
[API Server] API server listening on http://127.0.0.1:8642
```

### 3. Подключить фронтенд

Укажи любому клиенту, совместимому с OpenAI, адрес `http://localhost:8642/v1`:

```bash
# Test with curl
curl http://localhost:8642/v1/chat/completions \
  -H "Authorization: Bearer change-me-local-dev" \
  -H "Content-Type: application/json" \
  -d '{"model": "hermes-agent", "messages": [{"role": "user", "content": "Hello!"}]}'
```

Или подключи Open WebUI, LobeChat или любой другой фронтенд — смотри [руководство по интеграции Open WebUI](/user-guide/messaging/open-webui) для пошаговых инструкций.
## Конечные точки

### POST /v1/chat/completions

Стандартный формат OpenAI Chat Completions. Без состояния — полный диалог включён в каждый запрос через массив `messages`.

**Запрос:**
```json
{
  "model": "hermes-agent",
  "messages": [
    {"role": "system", "content": "You are a Python expert."},
    {"role": "user", "content": "Write a fibonacci function"}
  ],
  "stream": false
}
```

**Ответ:**
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1710000000,
  "model": "hermes-agent",
  "choices": [{
    "index": 0,
    "message": {"role": "assistant", "content": "Here's a fibonacci function..."},
    "finish_reason": "stop"
  }],
  "usage": {"prompt_tokens": 50, "completion_tokens": 200, "total_tokens": 250}
}
```

**Встроенный ввод изображений:** сообщения пользователя могут отправлять `content` как массив частей `text` и `image_url`. Поддерживаются как удалённые `http(s)` URL, так и `data:image/...` URL:

```json
{
  "model": "hermes-agent",
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "What is in this image?"},
        {"type": "image_url", "image_url": {"url": "https://example.com/cat.png", "detail": "high"}}
      ]
    }
  ]
}
```

Загруженные файлы (`file` / `input_file` / `file_id`) и URL `data:`, не являющиеся изображениями, возвращают `400 unsupported_content_type`.

**Потоковая передача** (`"stream": true`): возвращает Server‑Sent Events (SSE) с фрагментами ответа токен за токеном. Для **Chat Completions** поток использует стандартные события `chat.completion.chunk` плюс пользовательское событие Hermes `hermes.tool.progress` для отображения начала инструмента без загрязнения сохранённого текста ассистента. Для **Responses** поток использует типы событий OpenAI Responses, такие как `response.created`, `response.output_text.delta`, `response.output_item.added`, `response.output_item.done` и `response.completed`.

**Прогресс инструмента в потоках:**
- **Chat Completions:** Hermes генерирует `event: hermes.tool.progress` для визуализации начала инструмента без загрязнения текста ассистента.
- **Responses:** Hermes генерирует нативные элементы `function_call` и `function_call_output` во время SSE‑потока, чтобы клиенты могли отображать структурированный UI инструмента в реальном времени.

### POST /v1/responses

Формат OpenAI Responses API. Поддерживает состояние разговора на стороне сервера через `previous_response_id` — сервер хранит полную историю диалога (включая вызовы инструментов и их результаты), поэтому контекст сохраняется между ходами без необходимости управления им клиентом.

**Запрос:**
```json
{
  "model": "hermes-agent",
  "input": "What files are in my project?",
  "instructions": "You are a helpful coding assistant.",
  "store": true
}
```

**Ответ:**
```json
{
  "id": "resp_abc123",
  "object": "response",
  "status": "completed",
  "model": "hermes-agent",
  "output": [
    {"type": "function_call", "name": "terminal", "arguments": "{\"command\": \"ls\"}", "call_id": "call_1"},
    {"type": "function_call_output", "call_id": "call_1", "output": "README.md src/ tests/"},
    {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "Your project has..."}]}
  ],
  "usage": {"input_tokens": 50, "output_tokens": 200, "total_tokens": 250}
}
```

**Встроенный ввод изображений:** `input[].content` может содержать части `input_text` и `input_image`. Поддерживаются как удалённые URL, так и `data:image/...` URL:

```json
{
  "model": "hermes-agent",
  "input": [
    {
      "role": "user",
      "content": [
        {"type": "input_text", "text": "Describe this screenshot."},
        {"type": "input_image", "image_url": "data:image/png;base64,iVBORw0K..."}
      ]
    }
  ]
}
```

Загруженные файлы (`input_file` / `file_id`) и URL `data:`, не являющиеся изображениями, возвращают `400 unsupported_content_type`.

#### Многоходовой диалог с `previous_response_id`

Связывайте ответы, чтобы сохранять полный контекст (включая вызовы инструментов) между ходами:

```json
{
  "input": "Now show me the README",
  "previous_response_id": "resp_abc123"
}
```

Сервер восстанавливает полный диалог из сохранённой цепочки ответов — все предыдущие вызовы инструментов и их результаты сохраняются. Связанные запросы также используют одну и ту же сессию, поэтому многоходовые диалоги отображаются как единый элемент в панели управления и истории сессий.

#### Именованные разговоры

Используйте параметр `conversation` вместо отслеживания идентификаторов ответов:

```json
{"input": "Hello", "conversation": "my-project"}
{"input": "What's in src/?", "conversation": "my-project"}
{"input": "Run the tests", "conversation": "my-project"}
```

Сервер автоматически связывает с последним ответом в этом разговоре. Как команда `/title` для сессий шлюза.

### GET /v1/responses/\{id\}

Получить ранее сохранённый ответ по идентификатору.

### DELETE /v1/responses/\{id\}

Удалить сохранённый ответ.

### GET /v1/models

Возвращает агента как доступную модель. Рекламируемое имя модели по умолчанию соответствует имени [профиля](/user-guide/profiles) (или `hermes-agent` для профиля по умолчанию). Требуется большинством фронтендов для обнаружения моделей.

### GET /v1/capabilities

Возвращает машинно‑читаемое описание стабильного API‑поверхности сервера для внешних UI, оркестраторов и мостов плагинов.

```json
{
  "object": "hermes.api_server.capabilities",
  "platform": "hermes-agent",
  "model": "hermes-agent",
  "auth": {"type": "bearer", "required": true},
  "features": {
    "chat_completions": true,
    "responses_api": true,
    "run_submission": true,
    "run_status": true,
    "run_events_sse": true,
    "run_stop": true
  }
}
```

Используйте эту конечную точку при интеграции панелей управления, браузерных UI или контрольных плоскостей, чтобы они могли определить, поддерживает ли текущая версия Hermes запуск, потоковую передачу, отмену и непрерывность сессий без обращения к внутренностям Python.

### GET /health

Проверка работоспособности. Возвращает `{"status": "ok"}`. Также доступно по **GET /v1/health** для клиентов, совместимых с OpenAI, ожидающих префикс `/v1/`.

### GET /health/detailed

Расширенная проверка работоспособности, которая также сообщает о активных сессиях, запущенных агентах и использовании ресурсов. Полезно для инструментов мониторинга/наблюдаемости.
## Runs API (альтернатива, удобная для потоковой передачи)

Помимо `/v1/chat/completions` и `/v1/responses`, сервер предоставляет **runs** API для длительных сессий, когда клиент хочет подписаться на события прогресса вместо самостоятельного управления потоковой передачей.

### POST /v1/runs

Создать новый запуск агента. Возвращает `run_id`, который можно использовать для подписки на события прогресса.

```json
{
  "run_id": "run_abc123",
  "status": "started"
}
```

Запуски принимают простую строку `input` и необязательные `session_id`, `instructions`, `conversation_history` или `previous_response_id`. Когда указан `session_id`, Hermes отображает его в статусе запуска, чтобы внешние UI могли сопоставлять запуски со своими идентификаторами диалогов.

### GET /v1/runs/\{run_id\}

Запрос текущего состояния запуска. Полезно для панелей мониторинга, которым нужен статус без открытого SSE‑соединения, или для UI, которые переподключаются после навигации.

```json
{
  "object": "hermes.run",
  "run_id": "run_abc123",
  "status": "completed",
  "session_id": "space-session",
  "model": "hermes-agent",
  "output": "Done.",
  "usage": {"input_tokens": 50, "output_tokens": 200, "total_tokens": 250}
}
```

Статусы сохраняются короткое время после терминальных состояний (`completed`, `failed` или `cancelled`) для опроса и согласования UI.

### GET /v1/runs/\{run_id\}/events

Server‑Sent Events‑поток с прогрессом вызова инструментов, дельтами токенов и событиями жизненного цикла запуска. Предназначен для панелей мониторинга и тяжёлых клиентов, которые хотят подключаться/отключаться без потери состояния.

### POST /v1/runs/\{run_id\}/stop

Прервать текущий ход агента. Конечная точка сразу возвращает `{"status": "stopping"}`, пока Hermes просит активного агента остановиться в следующей безопасной точке прерывания.
## Jobs API (фоновые запланированные задачи)

Сервер предоставляет лёгковесный CRUD‑интерфейс для управления запланированными / фоновыми запусками агента из удалённого клиента. Все эндпоинты защищены той же bearer‑аутентификацией.

### GET /api/jobs

Получить список всех запланированных задач.

### POST /api/jobs

Создать новую запланированную задачу. Тело запроса принимает ту же структуру, что и `hermes cron` — prompt, schedule, skills, provider override, delivery target.

### GET /api/jobs/\{job_id\}

Получить определение конкретной задачи и состояние её последнего запуска.

### PATCH /api/jobs/\{job_id\}

Обновить поля существующей задачи (prompt, schedule и т.д.). Частичные обновления объединяются.

### DELETE /api/jobs/\{job_id\}

Удалить задачу. Также отменяется любой запущенный в данный момент процесс.

### POST /api/jobs/\{job_id\}/pause

Приостановить задачу без её удаления. Метки времени следующего запланированного запуска приостановлены до возобновления.

### POST /api/jobs/\{job_id\}/resume

Возобновить ранее приостановленную задачу.

### POST /api/jobs/\{job_id\}/run

Запустить задачу немедленно, вне расписания.
## API сессий (управление сессиями через REST)

Внешние UI могут управлять сессиями Hermes через REST, не запуская dashboard. Все endpoints защищены `API_SERVER_KEY` и находятся под `/api/sessions/*`.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/sessions` | Список сессий (постранично — `limit`, `offset`, `source`, `include_children`) |
| `POST` | `/api/sessions` | Создать пустую сессию |
| `GET` | `/api/sessions/{id}` | Прочитать метаданные сессии |
| `PATCH` | `/api/sessions/{id}` | Обновить заголовок или `end_reason` |
| `DELETE` | `/api/sessions/{id}` | Удалить сессию |
| `GET` | `/api/sessions/{id}/messages` | История сообщений для сессии |
| `POST` | `/api/sessions/{id}/fork` | Разветвить сессию через наследование `SessionDB` (соответствует семантике CLI `/branch`) |
| `POST` | `/api/sessions/{id}/chat` | Выполнить один синхронный ход агента |
| `POST` | `/api/sessions/{id}/chat/stream` | SSE‑обёртка для одного хода — генерирует события `assistant.delta`, `tool.started`, `tool.completed`, `run.completed` |

`/v1/capabilities` объявляет полный набор возможностей через флаги `session_*` и записи `endpoints.session_*`, чтобы внешние UI могли определить поддержку и безопасно выполнить запасной (вариант). Встроенные изображения поддерживаются в полезных нагрузках `chat` и `chat/stream` (мультимодальный путь).

```bash
# fork a session and run one turn
curl -X POST http://localhost:8642/api/sessions/$ID/fork \
  -H "Authorization: Bearer $API_SERVER_KEY" \
  -d '{"title": "explore alt path"}'

# stream a turn over SSE
curl -N -X POST http://localhost:8642/api/sessions/$ID/chat/stream \
  -H "Authorization: Bearer $API_SERVER_KEY" \
  -d '{"input": "what files changed in the last hour?"}'
```
## Обнаружение навыков и наборов инструментов

`GET /v1/skills` и `GET /v1/toolsets` позволяют внешним клиентам детерминированно перечислять возможности агента через REST вместо обращения к модели. Оба эндпоинта только для чтения и защищены `API_SERVER_KEY`.

```bash
curl http://localhost:8642/v1/skills \
  -H "Authorization: Bearer $API_SERVER_KEY"
# → [{"name": "github-pr-workflow", "description": "...", "category": "..."}, ...]

curl http://localhost:8642/v1/toolsets \
  -H "Authorization: Bearer $API_SERVER_KEY"
# → [{"name": "core", "label": "...", "description": "...", "enabled": true,
#     "configured": true, "tools": ["read_file", "write_file", ...]}, ...]
```

`/v1/skills` возвращает те же метаданные, которые внутренне использует хаб навыков. `/v1/toolsets` возвращает наборы инструментов, разрешённые для платформы `api_server`, с конкретным списком `tools`, в который каждый из них разворачивается. Оба рекламируются в `endpoints.*` в `/v1/capabilities`.
## Область долгосрочной памяти (`X-Hermes-Session-Key`)

Многопользовательские фронтенды, такие как Open WebUI, нуждаются в стабильном идентификаторе — на каждый канал — для долгосрочной памяти (Honcho и др.), **независимом** от `X-Hermes-Session-Id`, ограниченного транскриптом (он меняется при запросе `/new`). Передавай `X-Hermes-Session-Key` в запросах `/v1/chat/completions`, `/v1/responses` или `/v1/runs`, и Hermes пробрасывает его в `AIAgent(gateway_session_key=…)`, где провайдер памяти Honcho использует его для получения стабильной области.

```http
POST /v1/chat/completions HTTP/1.1
Authorization: Bearer ***
X-Hermes-Session-Id: transcript-alpha
X-Hermes-Session-Key: agent:main:webui:dm:user-42
```

Правила: максимум 256 символов, управляющие символы (`\r`, `\n`, `\x00`) отклоняются, а значение возвращается в ответах (JSON + SSE). `/v1/capabilities` объявляет поддержку через `"session_key_header": "X-Hermes-Session-Key"`. Без ключа стратегия Honcho `per-session` создаёт отдельную область для каждого `session_id` — именно то поведение, которое было у Hermes ранее.
## Обработка системного промпта

Когда фронтенд отправляет сообщение `system` (Chat Completions) или поле `instructions` (Responses API), hermes-agent **накладывает его поверх** своего базового системного промпта. Твой агент сохраняет все свои инструменты, память и навыки — системный промпт фронтенда добавляет дополнительные инструкции.

Это позволяет настраивать поведение для каждого фронтенда, не теряя возможностей:
- Системный промпт Open WebUI: «Ты — эксперт по Python. Всегда указывай типы.»
- Агент по‑прежнему имеет терминал, файловые инструменты, веб‑поиск, память и т.д.
## Аутентификация

Аутентификация по токену Bearer через заголовок `Authorization`:

```
Authorization: Bearer ***
```

Настройте ключ через переменную окружения `API_SERVER_KEY`. Если нужен браузер для прямого вызова Hermes, также задайте `API_SERVER_CORS_ORIGINS` со списком разрешённых источников.

:::warning Security
Сервер API предоставляет полный доступ к набору инструментов hermes-agent, **включая команды терминала**. `API_SERVER_KEY` **обязателен для каждого развертывания**, включая привязку по умолчанию к `127.0.0.1`. Сужайте `API_SERVER_CORS_ORIGINS`, чтобы контролировать доступ из браузера, когда ты явно разрешаешь вызовы из браузера.
:::
## Конфигурация

### Переменные окружения

| Переменная | Значение по умолчанию | Описание |
|------------|-----------------------|----------|
| `API_SERVER_ENABLED` | `false` | Включить API‑сервер |
| `API_SERVER_PORT` | `8642` | Порт HTTP‑сервера |
| `API_SERVER_HOST` | `127.0.0.1` | Адрес привязки (по умолчанию только localhost) |
| `API_SERVER_KEY` | _(required)_ | Bearer‑токен для аутентификации |
| `API_SERVER_CORS_ORIGINS` | _(none)_ | Список разрешённых источников браузера, разделённых запятыми |
| `API_SERVER_MODEL_NAME` | _(profile name)_ | Имя модели на `/v1/models`. По умолчанию берётся имя профиля, либо `hermes-agent` для профиля по умолчанию. |

### config.yaml

```yaml
# Not yet supported — use environment variables.
# config.yaml support coming in a future release.
```
## Заголовки безопасности

Все ответы включают заголовки безопасности:
- `X-Content-Type-Options: nosniff` — предотвращает определение MIME‑типа по содержимому
- `Referrer-Policy: no-referrer` — предотвращает утечку реферера
## CORS

API‑сервер **не** включает CORS для браузера по умолчанию.

Для прямого доступа из браузера задайте явный **allowlist**:

```bash
API_SERVER_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Когда CORS включён:
- **Preflight‑ответы** содержат `Access-Control-Max-Age: 600` (кеш на 10 минут)
- **SSE‑стриминговые ответы** включают заголовки CORS, чтобы клиенты `EventSource` в браузере работали корректно
- **`Idempotency-Key`** является разрешённым заголовком запроса — клиенты могут отправлять его для дедупликации (ответы кешируются по ключу в течение 5 минут)

Большинство документированных фронтендов, таких как Open WebUI, соединяются сервер‑к‑серверу и CORS им не требуется.
## Совместимые фронтенды

Любой фронтенд, поддерживающий формат API OpenAI, работает. Тестированные/задокументированные интеграции:

| Frontend | Stars | Connection |
|----------|-------|------------|
| [Open WebUI](/user-guide/messaging/open-webui) | 126k | Полное руководство доступно |
| LobeChat | 73k | Пользовательская точка доступа провайдера |
| LibreChat | 34k | Пользовательская точка доступа в librechat.yaml |
| AnythingLLM | 56k | Универсальный провайдер OpenAI |
| NextChat | 87k | Переменная окружения `BASE_URL` |
| ChatBox | 39k | Настройка API Host |
| Jan | 26k | Конфигурация удалённой модели |
| HF Chat-UI | 8k | `OPENAI_BASE_URL` |
| big-AGI | 7k | Пользовательская точка доступа |
| OpenAI Python SDK | — | `OpenAI(base_url="http://localhost:8642/v1")` |
| curl | — | Прямые HTTP‑запросы |
## Мультипользовательская настройка с профилями

Чтобы предоставить нескольким пользователям их собственные изолированные экземпляры Hermes (отдельные конфигурации, память, навыки), используй [профили](/user-guide/profiles):

```bash
# Create a profile per user
hermes profile create alice
hermes profile create bob

# Configure each profile's API server on a different port. API_SERVER_* are env
# vars (not config.yaml keys), so write them to each profile's .env:
cat >> ~/.hermes/profiles/alice/.env <<EOF
API_SERVER_ENABLED=true
API_SERVER_PORT=8643
API_SERVER_KEY=alice-secret
EOF

cat >> ~/.hermes/profiles/bob/.env <<EOF
API_SERVER_ENABLED=true
API_SERVER_PORT=8644
API_SERVER_KEY=bob-secret
EOF

# Start each profile's gateway
hermes -p alice gateway &
hermes -p bob gateway &
```

API‑сервер каждого профиля автоматически объявляет имя профиля как идентификатор модели:

- `http://localhost:8643/v1/models` → модель `alice`
- `http://localhost:8644/v1/models` → модель `bob`

В Open WebUI добавь каждый как отдельное подключение. Выпадающий список моделей показывает `alice` и `bob` как отдельные модели, каждая из которых работает на полностью изолированном экземпляре Hermes. Смотри [руководство по Open WebUI](/user-guide/messaging/open-webui#multi-user-setup-with-profiles) для подробностей.
## Ограничения

- **Хранение ответов** — сохранённые ответы (для `previous_response_id`) сохраняются в SQLite и остаются после перезапуска шлюза. Максимум 100 сохранённых ответов (удаление по принципу LRU – наименее недавно использованные).
- **Отсутствие загрузки файлов** — встроенные изображения поддерживаются как в `/v1/chat/completions`, так и в `/v1/responses`, но загрузка файлов (`file`, `input_file`, `file_id`) и ввод не‑изображающих документов через API не поддерживается.
- **Поле model является косметическим** — поле `model` в запросах принимается, но фактическая модель LLM, используемая сервером, задаётся в `config.yaml`.
## Режим прокси

API‑сервер также выступает в качестве бэкенда для **gateway proxy mode**. Когда другой экземпляр шлюза Hermes настроен с `GATEWAY_PROXY_URL`, указывающим на этот API‑сервер, он перенаправляет все сообщения сюда вместо запуска собственного агента. Это позволяет выполнять разделённые развертывания — например, контейнер Docker, обрабатывающий Matrix E2EE и передающий сообщения агенту, работающему на хосте.

См. [Matrix Proxy Mode](/user-guide/messaging/matrix#proxy-mode-e2ee-on-macos) для полного руководства по настройке.