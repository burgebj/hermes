---
sidebar_position: 14
title: "API сервер"
description: "Відкрити hermes-agent як сумісний з OpenAI API для будь‑якого фронтенду"
---

# API Server

API‑сервер надає hermes-agent як HTTP‑endpoint, сумісний з OpenAI. Будь‑який фронтенд, який підтримує формат OpenAI — Open WebUI, LobeChat, LibreChat, NextChat, ChatBox та сотні інших — може підключитися до hermes-agent і використовувати його як бекенд.

Твій агент обробляє запити зі своїм повним набором інструментів (термінал, файлові операції, веб‑пошук, пам'ять, навички) і повертає остаточну відповідь. При потоковій передачі індикатори прогресу інструментів відображаються в рядку, щоб фронтенди могли показувати, що саме робить агент.

:::tip One backend covers models + tools
Hermes сам потребує налаштованого провайдера та бекендів інструментів, щоб API‑сервер був корисним. Підписка [Nous Portal](/user-guide/features/tool-gateway) забезпечує обидва — 300+ моделей плюс веб/зображення/TTS/браузер через шлюз інструментів (Tool Gateway). Запусти `hermes setup --portal` один раз перед запуском API‑сервера, і фронтенди типу Open WebUI або LobeChat отримають повністю оснащений інструментами бекенд.
:::
## Швидкий старт

### 1. Увімкнути API‑сервер

Додай до `~/.hermes/.env`:

```bash
API_SERVER_ENABLED=true
API_SERVER_KEY=change-me-local-dev
# Optional: only if a browser must call Hermes directly
# API_SERVER_CORS_ORIGINS=http://localhost:3000
```

### 2. Запустити шлюз

```bash
hermes gateway
```

Ти побачиш:

```
[API Server] API server listening on http://127.0.0.1:8642
```

### 3. Підключити фронтенд

Налаштуй будь‑який клієнт, сумісний з OpenAI, на `http://localhost:8642/v1`:

```bash
# Test with curl
curl http://localhost:8642/v1/chat/completions \
  -H "Authorization: Bearer change-me-local-dev" \
  -H "Content-Type: application/json" \
  -d '{"model": "hermes-agent", "messages": [{"role": "user", "content": "Hello!"}]}'
```

Або підключи Open WebUI, LobeChat чи будь‑який інший фронтенд — дивись [посібник з інтеграції Open WebUI](/user-guide/messaging/open-webui) для покрокових інструкцій.
## Кінцеві точки

### POST /v1/chat/completions

Стандартний формат OpenAI Chat Completions. Stateless — повна розмова включається в кожен запит через масив `messages`.

**Запит:**
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

**Відповідь:**
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

**Вбудоване зображення:** повідомлення користувача можуть надсилати `content` як масив частин `text` та `image_url`. Підтримуються як віддалені `http(s)` URL, так і `data:image/...` URL:

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

Завантажені файли (`file` / `input_file` / `file_id`) та не‑зображення `data:` URL повертають `400 unsupported_content_type`.

**Стрімінг** (`"stream": true`): повертає Server‑Sent Events (SSE) з токен‑за‑токеном фрагментами відповіді. Для **Chat Completions** стрім використовує стандартні події `chat.completion.chunk` плюс власну подію Hermes `hermes.tool.progress` для UX запуску інструменту. Для **Responses** стрім використовує типи подій OpenAI Responses, такі як `response.created`, `response.output_text.delta`, `response.output_item.added`, `response.output_item.done` та `response.completed`.

**Прогрес інструменту у стрімах:**
- **Chat Completions:** Hermes надсилає `event: hermes.tool.progress` для відображення запуску інструменту без забруднення збереженого тексту асистента.
- **Responses:** Hermes надсилає нативні `function_call` та `function_call_output` елементи під час SSE‑стріму, щоб клієнти могли у реальному часі рендерити структурований UI інструменту.

### POST /v1/responses

Формат OpenAI Responses API. Підтримує стан розмови на боці сервера через `previous_response_id` — сервер зберігає повну історію розмови (включаючи виклики інструментів та їх результати), тому контекст багатократних ходів зберігається без управління з боку клієнта.

**Запит:**
```json
{
  "model": "hermes-agent",
  "input": "What files are in my project?",
  "instructions": "You are a helpful coding assistant.",
  "store": true
}
```

**Відповідь:**
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

**Вбудоване зображення:** `input[].content` може містити частини `input_text` та `input_image`. Підтримуються як віддалені URL, так і `data:image/...` URL:

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

Завантажені файли (`input_file` / `file_id`) та не‑зображення `data:` URL повертають `400 unsupported_content_type`.

#### Багатократний діалог з `previous_response_id`

Ланцюжок відповідей для збереження повного контексту (включаючи виклики інструментів) між ходами:

```json
{
  "input": "Now show me the README",
  "previous_response_id": "resp_abc123"
}
```

Сервер відновлює повну розмову з збереженого ланцюжка відповідей — усі попередні виклики інструментів та їх результати зберігаються. Ланцюжкові запити також ділять одну сесію, тому багатократні діалоги відображаються як один запис у панелі інструментів та історії сесій.

#### Іменовані розмови

Використовуй параметр `conversation` замість відстеження ідентифікаторів відповідей:

```json
{"input": "Hello", "conversation": "my-project"}
{"input": "What's in src/?", "conversation": "my-project"}
{"input": "Run the tests", "conversation": "my-project"}
```

Сервер автоматично ланцюжить до останньої відповіді в цій розмові. Подібно до команди `/title` для сесій шлюзу.

### GET /v1/responses/\{id\}

Отримати раніше збережену відповідь за її ID.

### DELETE /v1/responses/\{id\}

Видалити збережену відповідь.

### GET /v1/models

Перелічує агента як доступну модель. Рекламна назва моделі за замовчуванням відповідає імені [profile](/user-guide/profiles) (або `hermes-agent` для типового профілю). Потрібно більшості фронтендів для виявлення моделей.

### GET /v1/capabilities

Повертає машинозчитуваний опис стабільного інтерфейсу API‑сервера для зовнішніх UI, оркестраторів та мостів плагінів.

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

Використовуй цю кінцеву точку при інтеграції панелей, браузерних UI або контрольних площин, щоб вони могли дізнатися, чи підтримує запущена версія Hermes запуск, стрімінг, скасування та безперервність сесій без залежності від приватних Python‑внутрішностей.

### GET /health

Перевірка працездатності. Повертає `{"status": "ok"}`. Доступно також за **GET /v1/health** для клієнтів, сумісних з OpenAI, які очікують префікс `/v1/`.

### GET /health/detailed

Розширена перевірка працездатності, яка також повідомляє про активні сесії, запущені агенти та використання ресурсів. Корисно для інструментів моніторингу/спостереження.
## Runs API (альтернатива, дружня до потокової передачі)

На додачу до `/v1/chat/completions` та `/v1/responses` сервер надає **runs** API для довготривалих сесій, коли клієнт хоче підписатися на події прогресу замість того, щоб самостійно керувати потоковою передачею.

### POST /v1/runs

Створює новий запуск агента. Повертає `run_id`, який можна використати для підписки на події прогресу.

```json
{
  "run_id": "run_abc123",
  "status": "started"
}
```

Runs приймає простий рядок `input` та необов’язкові `session_id`, `instructions`, `conversation_history` або `previous_response_id`. Коли вказано `session_id`, Hermes відображає його у статусі запуску, щоб зовнішні UI могли корелювати запуски зі своїми ідентифікаторами розмов.

### GET /v1/runs/\{run_id\}

Опитує поточний стан запуску. Це корисно для панелей інструментів, яким потрібен статус без постійного відкритого SSE‑з’єднання, або для UI, які перепідключаються після навігації.

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

Статуси зберігаються короткий час після завершальних станів (`completed`, `failed` або `cancelled`) для опитування та узгодження UI.

### GET /v1/runs/\{run_id\}/events

Server‑Sent Events — потік прогресу викликів інструментів, дельт токенів та подій життєвого циклу запуску. Призначений для панелей інструментів та товстих клієнтів, які хочуть підключатися/відключатися без втрати стану.

### POST /v1/runs/\{run_id\}/stop

Перериває поточний хід агента. Кінцева точка повертає одразу `{"status": "stopping"}`, поки Hermes просить активного агента зупинитися на наступній безпечній точці переривання.
## Jobs API (background scheduled work)

Сервер надає легковаговий CRUD‑інтерфейс для керування запланованими / фоновими запусками агентів з віддаленого клієнта. Всі кінцеві точки захищені одною bearer‑автентифікацією.

### GET /api/jobs

Отримати список усіх запланованих завдань.

### POST /api/jobs

Створити нове заплановане завдання. Тіло запиту приймає ту ж структуру, що й `hermes cron` — prompt, schedule, skills, provider override, delivery target.

### GET /api/jobs/\{job_id\}

Отримати визначення окремого завдання та стан його останнього запуску.

### PATCH /api/jobs/\{job_id\}

Оновити поля існуючого завдання (prompt, schedule тощо). Часткові оновлення зливаються.

### DELETE /api/jobs/\{job_id\}

Видалити завдання. Також скасовує будь‑який запущений процес.

### POST /api/jobs/\{job_id\}/pause

Призупинити завдання без його видалення. Мітки часу наступного запланованого запуску призупиняються до відновлення.

### POST /api/jobs/\{job_id\}/resume

Відновити раніше призупинене завдання.

### POST /api/jobs/\{job_id\}/run

Запустити завдання негайно, поза розкладом.
## API сесій (керування сесіями через REST)

Зовнішні UI можуть керувати сесіями Hermes через REST, не запускаючи панель управління. Усі кінцеві точки захищені `API_SERVER_KEY` і розташовані під `/api/sessions/*`.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/sessions` | Список сесій (посторінковий — `limit`, `offset`, `source`, `include_children`) |
| `POST` | `/api/sessions` | Створити порожню сесію |
| `GET` | `/api/sessions/{id}` | Прочитати метадані сесії |
| `PATCH` | `/api/sessions/{id}` | Оновити назву або `end_reason` |
| `DELETE` | `/api/sessions/{id}` | Видалити сесію |
| `GET` | `/api/sessions/{id}/messages` | Історія повідомлень для сесії |
| `POST` | `/api/sessions/{id}/fork` | Розгалуження сесії через лінійку `SessionDB` (відповідає семантиці CLI `/branch`) |
| `POST` | `/api/sessions/{id}/chat` | Виконати один синхронний хід агента |
| `POST` | `/api/sessions/{id}/chat/stream` | SSE‑обгортка над одним ходом — генерує події `assistant.delta`, `tool.started`, `tool.completed`, `run.completed` |

`/v1/capabilities` оголошує повний набір можливостей через прапорці `session_*` та записи `endpoints.session_*`, щоб зовнішні UI могли виявити підтримку та безпечно перейти до запасного (варіанту). Вбудовані зображення підтримуються у навантаженнях `chat` та `chat/stream` (шлях, що враховує мультимодальність).

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
## Виявлення навичок та наборів інструментів

`GET /v1/skills` і `GET /v1/toolsets` дозволяють зовнішнім клієнтам детерміновано перераховувати можливості агента через REST замість запиту моделі. Обидва запити лише для читання та захищені `API_SERVER_KEY`.

```bash
curl http://localhost:8642/v1/skills \
  -H "Authorization: Bearer $API_SERVER_KEY"
# → [{"name": "github-pr-workflow", "description": "...", "category": "..."}, ...]

curl http://localhost:8642/v1/toolsets \
  -H "Authorization: Bearer $API_SERVER_KEY"
# → [{"name": "core", "label": "...", "description": "...", "enabled": true,
#     "configured": true, "tools": ["read_file", "write_file", ...]}, ...]
```

`/v1/skills` повертає ті ж метадані, які внутрішньо використовує **skills hub**. `/v1/toolsets` повертає набори інструментів, розв’язані для платформи `api_server`, разом із конкретним списком `tools`, який розширює кожен набір. Обидва зазначені в `endpoints.*` у `/v1/capabilities`.
## Довготривала пам'ять (scoping) (`X-Hermes-Session-Key`)

Багатокористувацькі інтерфейси, такі як Open WebUI, потребують стабільного ідентифікатора каналу для довготривалої пам'яті (Honcho тощо), який **не залежить** від `X-Hermes-Session-Id`, прив’язаного до транскрипту (який оновлюється при `/new`). Передавай `X-Hermes-Session-Key` у запитах `/v1/chat/completions`, `/v1/responses` або `/v1/runs`, і Hermes передасть його в `AIAgent(gateway_session_key=...)`, де провайдер пам’яті Honcho використовує його для отримання стабільного простору.

```http
POST /v1/chat/completions HTTP/1.1
Authorization: Bearer ***
X-Hermes-Session-Id: transcript-alpha
X-Hermes-Session-Key: agent:main:webui:dm:user-42
```

Правила: максимум 256 символів, контрольні символи (`\r`, `\n`, `\x00`) відхиляються, а значення повертається у відповідях (JSON + SSE). `/v1/capabilities` оголошує підтримку через `"session_key_header": "X-Hermes-Session-Key"`. Без ключа стратегія Honcho `per-session` створює різний простір для кожного `session_id` — саме таке поводження було у Hermes раніше.
## Обробка system prompt

Коли фронтенд надсилає повідомлення `system` (Chat Completions) або поле `instructions` (Responses API), hermes-agent **накладає його поверх** основного system prompt. Твій агент зберігає всі свої інструменти, пам’ять і навички — system prompt від фронтенду додає додаткові інструкції.

Це означає, що ти можеш налаштовувати поведінку для кожного фронтенду, не втрачаючи можливостей:
- system prompt Open WebUI: «You are a Python expert. Always include type hints.»
- Агент все одно має інструменти терміналу, роботи з файлами, веб‑пошук, пам’ять тощо.
## Автентифікація

Автентифікація за допомогою токену Bearer у заголовку `Authorization`:

```
Authorization: Bearer ***
```

Налаштуй ключ через змінну середовища `API_SERVER_KEY`. Якщо потрібен браузер для прямого виклику Hermes, також встанови `API_SERVER_CORS_ORIGINS` зі списком дозволених джерел.

:::warning Security
Сервер API надає повний доступ до інструментів hermes-agent, **включаючи термінальні команди**. `API_SERVER_KEY` **обов’язковий для кожного розгортання**, включаючи типове прив’язування до `127.0.0.1`. Зроби `API_SERVER_CORS_ORIGINS` вузьким, щоб контролювати доступ браузера, коли ти явно дозволяєш виклики з браузера.
:::
## Конфігурація

### Змінні середовища

| Змінна | За замовчуванням | Опис |
|----------|----------------|------|
| `API_SERVER_ENABLED` | `false` | Увімкнути API‑сервер |
| `API_SERVER_PORT` | `8642` | Порт HTTP‑сервера |
| `API_SERVER_HOST` | `127.0.0.1` | Адреса прив’язки (за замовчуванням лише localhost) |
| `API_SERVER_KEY` | _(required)_ | Bearer‑токен для автентифікації |
| `API_SERVER_CORS_ORIGINS` | _(none)_ | Дозволені походження браузера, розділені комами |
| `API_SERVER_MODEL_NAME` | _(profile name)_ | Назва моделі на `/v1/models`. За замовчуванням — назва профілю, або `hermes-agent` для типового профілю. |

### config.yaml

```yaml
# Not yet supported — use environment variables.
# config.yaml support coming in a future release.
```
## Заголовки безпеки

Усі відповіді містять заголовки безпеки:
- `X-Content-Type-Options: nosniff` — запобігає визначенню MIME‑типу
- `Referrer-Policy: no-referrer` — запобігає витоку реферера
## CORS

API‑сервер **не** вмикає CORS у браузері за замовчуванням.

Для прямого доступу з браузера встанови явний **allowlist**:

```bash
API_SERVER_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Коли CORS увімкнено:
- **Preflight responses** включають `Access-Control-Max-Age: 600` (кеш на 10 хвилин)
- **SSE streaming responses** включають заголовки CORS, тож клієнти браузера EventSource працюють правильно
- **`Idempotency‑Key`** є дозволеним заголовком запиту — клієнти можуть надсилати його для дедуплікації (відповіді кешуються за ключем 5 хвилин)

Більшість задокументованих фронтендів, таких як Open WebUI, підключаються сервер‑до‑сервера і зовсім не потребують CORS.
## Сумісні фронтенди

Будь‑який фронтенд, який підтримує формат OpenAI API, працює. Перевірені/задокументовані інтеграції:

| Фронтенд | Зірки | З’єднання |
|----------|-------|------------|
| [Open WebUI](/user-guide/messaging/open-webui) | 126k | Повний посібник |
| LobeChat | 73k | Кастомна точка провайдера |
| LibreChat | 34k | Кастомна точка в `librechat.yaml` |
| AnythingLLM | 56k | Генеричний провайдер OpenAI |
| NextChat | 87k | Змінна середовища `BASE_URL` |
| ChatBox | 39k | Налаштування `API Host` |
| Jan | 26k | Конфігурація віддаленої моделі |
| HF Chat-UI | 8k | `OPENAI_BASE_URL` |
| big-AGI | 7k | Кастомна точка |
| OpenAI Python SDK | — | `OpenAI(base_url="http://localhost:8642/v1")` |
| curl | — | Прямі HTTP‑запити |
## Налаштування багатокористувацького режиму з профілями

Щоб надати кільком користувачам їхні власні ізольовані інстанції Hermes (окремі конфіг, пам’ять, інструменти), використай [профілі](/user-guide/profiles):

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

API‑сервер кожного профілю автоматично оголошує назву профілю як ідентифікатор моделі:

- `http://localhost:8643/v1/models` → модель `alice`
- `http://localhost:8644/v1/models` → модель `bob`

У Open WebUI додай кожен профіль як окреме з’єднання. У випадаючому списку моделей буде показано `alice` і `bob` як різні моделі, кожна з яких підтримується повністю ізольованою інстанцією Hermes. Переглянь [посібник Open WebUI](/user-guide/messaging/open-webui#multi-user-setup-with-profiles) для деталей.
## Обмеження

- **Зберігання відповідей** — збережені відповіді (для `previous_response_id`) зберігаються в SQLite і залишаються після перезапуску **gateway**. Максимум 100 збережених відповідей (видалення за принципом LRU).
- **Немає завантаження файлів** — вбудовані зображення підтримуються як на `/v1/chat/completions`, так і на `/v1/responses`, але завантажені файли (`file`, `input_file`, `file_id`) та документи, що не є зображеннями, не підтримуються через API.
- **Поле `model` лише косметичне** — поле `model` у запитах приймається, проте фактична модель LLM, яка використовується, налаштовується на боці сервера у `config.yaml`.
## Режим проксі

API‑сервер також слугує бекендом для **gateway proxy mode**. Коли інший екземпляр Hermes gateway налаштований з `GATEWAY_PROXY_URL`, що вказує на цей API‑сервер, він пересилає всі повідомлення сюди замість запуску власного агента. Це дозволяє розподілені розгортання — наприклад, Docker‑контейнер, який обробляє Matrix E2EE і передає їх агенту на хості.

Дивись [Matrix Proxy Mode](/user-guide/messaging/matrix#proxy-mode-e2ee-on-macos) для повного посібника з налаштування.