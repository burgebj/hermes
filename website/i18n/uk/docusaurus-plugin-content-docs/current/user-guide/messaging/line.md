---
sidebar_position: 17
title: "лінія"
description: "Налаштуй Hermes Agent як бота LINE Messaging API"
---

# Налаштування LINE

Запусти Hermes Agent як [LINE](https://line.me/) бота через офіційний LINE Messaging API. Адаптер знаходиться у вигляді вбудованого плагіна платформи в `plugins/platforms/line/` — без змін у ядрі, просто ввімкни його, як будь‑яку іншу платформу.

LINE — домінуючий додаток для обміну повідомленнями в Японії, Тайвані та Таїланді. Якщо твої користувачі живуть там, саме так вони зможуть з тобою зв’язатися.

> Запусти `hermes gateway setup` і обери **LINE** для покрокового налаштування.

## Як реагує бот

| Контекст | Поведінка |
|----------|-----------|
| **1:1 чат** (`U` ID) | Відповідає на кожне повідомлення |
| **Груповий чат** (`C` ID) | Відповідає, коли група в білому списку |
| **Кімната для кількох користувачів** (`R` ID) | Відповідає, коли кімната в білому списку |

Вхідний текст, зображення, аудіо, відео, файли, стікери та локації обробляються. Вихідний текст спочатку використовує **безкоштовний токен відповіді** (одноразовий, вікно ~60 с) і переходить до платного Push API, коли токен закінчився.

---

## Крок 1: Створи канал LINE Messaging API

1. Перейди до [LINE Developers Console](https://developers.line.biz/console/).
2. Створи Provider, а потім у ньому **Messaging API** канал.
3. На вкладці **Basic settings** каналу скопіюй **Channel secret**.
4. На вкладці **Messaging API** прокрути до **Channel access token (long-lived)** і натисни **Issue**. Скопіюй токен.
5. На вкладці **Messaging API** також вимкни **Auto-reply messages** та **Greeting messages**, щоб вони не конфліктували з відповідями твого бота.

---

## Крок 2: Відкрий порт вебхука

LINE надсилає вебхуки через публічний HTTPS. Порт за замовчуванням — `8646` — при потребі перевизнач його змінною `LINE_PORT`.

```bash
# Cloudflare Tunnel (recommended for production — fixed hostname)
cloudflared tunnel --url http://localhost:8646

# ngrok (good for dev)
ngrok http 8646

# devtunnel
devtunnel create hermes-line --allow-anonymous
devtunnel port create hermes-line -p 8646 --protocol https
devtunnel host hermes-line
```

Скопіюй URL `https://...` — ти встановиш його як URL вебхука нижче. **Тримай тунель запущеним** під час тестування. Для продакшну налаштуй постійний Cloudflare named tunnel, щоб URL вебхука не змінювався після перезапуску.

---

## Крок 3: Налаштуй Hermes

Додай у `~/.hermes/.env`:

```env
LINE_CHANNEL_ACCESS_TOKEN=YOUR_LONG_LIVED_TOKEN
LINE_CHANNEL_SECRET=YOUR_CHANNEL_SECRET

# Allowlist — at least one of these (or LINE_ALLOW_ALL_USERS=true for dev)
LINE_ALLOWED_USERS=U1234567890abcdef...           # comma-separated U-prefixed IDs
LINE_ALLOWED_GROUPS=C1234567890abcdef...          # optional group IDs
LINE_ALLOWED_ROOMS=R1234567890abcdef...           # optional room IDs

# Required for image / audio / video sends — the public HTTPS base URL
# the tunnel resolves to.  Without it, send_image/voice/video will refuse.
LINE_PUBLIC_URL=https://my-tunnel.example.com
```

Потім у `~/.hermes/config.yaml`:

```yaml
gateway:
  platforms:
    line:
      enabled: true
```

Цього достатньо — сканування bundled‑plugin у `gateway/config.py` автоматично знаходить `plugins/platforms/line/`. Не потрібно редагувати enum `Platform.LINE` чи реєстрацію `_create_adapter`.

---

## Крок 4: Встанови URL вебхука

Повернись у консоль LINE:

1. Відкрий свій канал → вкладка **Messaging API**.
2. У розділі **Webhook settings** → **Webhook URL** встав `https://<your-tunnel>/line/webhook` (зверни увагу на шлях `/line/webhook` — адаптер слухає його).
3. Натисни **Verify**. LINE відправить запит; ти маєш отримати 200.
4. Перемкни **Use webhook** в **On**.

---

## Крок 5: Запусти шлюз

```bash
hermes gateway
```

У журналі агента з’явиться:

```
LINE: webhook listening on 0.0.0.0:8646/line/webhook (public: https://my-tunnel.example.com)
```

Додай бота у друзі з додатку LINE (відскануй QR‑код у вкладці **Messaging API** каналу) і надішли йому повідомлення.

---

## Повільні відповіді LLM

Токен відповіді LINE одноразовий і закінчується приблизно через 60 с після вхідної події. Повільні LLM не встигають відповісти вчасно, що зазвичай змушує робити платний виклик Push API.

Коли LLM працює довше `LINE_SLOW_RESPONSE_THRESHOLD` секунд (за замовчуванням `45`), адаптер використовує початковий токен, щоб надіслати бульбашку **Template Buttons**:

> 🤔 Still thinking. Tap below to fetch the answer when it's ready.
>
> [ Get answer ]

Користувач натискає **Get answer**, коли зручно — цей postback доставляє *новий* токен, який адаптер використовує для надсилання кешованої відповіді (все ще безкоштовно).

Машина станів: `PENDING → READY → DELIVERED`, плюс `ERROR` для скасованих запусків (орфанний `PENDING` перетворюється на «Run was interrupted before completion.» після `/stop`, щоб постійна кнопка не зациклювалася).

Щоб вимкнути кнопку postback і завжди робити Push‑fallback:

```env
LINE_SLOW_RESPONSE_THRESHOLD=0
```

Щоб flow postback спрацьовував надійно, придуши зайві повідомлення, які могли б використати токен до досягнення порогу:

```yaml
# ~/.hermes/config.yaml
display:
  interim_assistant_messages: false
  platforms:
    line:
      tool_progress: off
```

---

## Cron / доставка сповіщень

```env
LINE_HOME_CHANNEL=Uxxxxxxxxxxxxxxxxxxxx     # default delivery target
```

Cron‑завдання з `deliver: line` маршрутизуються до `LINE_HOME_CHANNEL`. Адаптер постачає окремий Push‑only відправник, тому cron‑завдання працюють навіть коли cron запускається в окремому процесі від шлюзу.

---

## Довідка щодо змінних середовища

| Змінна | Обов’язково | За замовчуванням | Опис |
|---|---|---|---|
| `LINE_CHANNEL_ACCESS_TOKEN` | так | — | Токен доступу каналу (довгоживучий) |
| `LINE_CHANNEL_SECRET` | так | — | Секрет каналу (HMAC‑SHA256 перевірка вебхука) |
| `LINE_HOST` | ні | `0.0.0.0` | Хост для прив’язки вебхука |
| `LINE_PORT` | ні | `8646` | Порт для прив’язки вебхука |
| `LINE_PUBLIC_URL` | для медіа | — | Публічний HTTPS базовий URL; потрібен для надсилання зображень/голосу/відео |
| `LINE_ALLOWED_USERS` | один з | — | Список ID користувачів (U‑prefixed), розділених комами |
| `LINE_ALLOWED_GROUPS` | один з | — | Список ID груп (C‑prefixed), розділених комами |
| `LINE_ALLOWED_ROOMS` | один з | — | Список ID кімнат (R‑prefixed), розділених комами |
| `LINE_ALLOW_ALL_USERS` | лише для dev | `false` | Вимкнути білий список повністю |
| `LINE_HOME_CHANNEL` | ні | — | Цільовий канал за замовчуванням для cron / сповіщень |
| `LINE_SLOW_RESPONSE_THRESHOLD` | ні | `45` | Секунд перед появою кнопки postback (`0` = вимкнено) |
| `LINE_PENDING_TEXT` | ні | "🤔 Still thinking…" | Текст бульбашки поряд з кнопкою postback |
| `LINE_BUTTON_LABEL` | ні | "Get answer" | Текст кнопки |
| `LINE_DELIVERED_TEXT` | ні | "Already replied ✅" | Відповідь, коли вже доставлена кнопка натискається знову |
| `LINE_INTERRUPTED_TEXT` | ні | "Run was interrupted before completion." | Відповідь, коли натискається кнопка орфанного `/stop` |

---

## Устранення проблем

**«invalid signature» під час перевірки вебхука.** `Channel secret` скопійовано неправильно, або тунель змінив тіло запиту. Спочатку перевір за допомогою `curl -i https://<tunnel>/line/webhook/health` — має повернути `{"status":"ok","platform":"line"}`.

**Бот нічого не отримує в групах.** Переконайся, що `LINE_ALLOWED_GROUPS` містить ID групи `C...`. Щоб знайти ID групи, надішли тестове повідомлення і пошукай у `~/.hermes/logs/gateway.log` рядок `LINE: rejecting unauthorized source` — у словнику відхиленої джерела будуть потрібні ID.

**`send_image` повертає «LINE_PUBLIC_URL must be set».** LINE Messaging API не приймає бінарні завантаження — зображення, аудіо та відео мають бути доступними за HTTPS URL. Встанови `LINE_PUBLIC_URL` на публічний хост тунелю, і адаптер автоматично буде подавати файли за `/line/media/<token>/<filename>`.

**Кнопка postback не з’являється.** Або LLM відповів швидше, ніж `LINE_SLOW_RESPONSE_THRESHOLD`, або інша бульбашка (tool‑progress, streaming) використала токен спочатку. Дивись блок придушення у розділі «Повільні відповіді LLM».

**«already in use by another profile».** Той самий токен доступу каналу прив’язаний до іншого запущеного Hermes профілю. Зупини інший шлюз або використай окремий канал.

---

## Обмеження

* **Одна бульбашка на фрагмент.** Кожна текстова бульбашка LINE обмежена 5000 символами, і максимум 5 бульбашок надсилаються за один виклик Reply/Push. Довгі відповіді обрізаються з еліпсисом.
* **Немає рідного редагування повідомлень.** У LINE немає API редагування — потокові відповіді завжди надсилаються новими бульбашками, без редагування попередніх.
* **Немає рендерингу Markdown.** Жирний (`**`), курсив (`*`), блоки коду та заголовки відображаються як звичайний текст. Адаптер видаляє їх перед надсиланням; URL зберігаються (`[label](url)` стає `label (url)`).
* **Індикатор завантаження лише в DM.** LINE відхиляє API typing/loading для груп і кімнат, тому індикатор набору тексту показується лише в 1:1 чатах.