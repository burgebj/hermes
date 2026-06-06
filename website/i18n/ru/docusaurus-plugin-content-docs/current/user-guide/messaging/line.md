---
sidebar_position: 17
title: "ЛИНИЯ"
description: "Настрой Hermes Agent как бота LINE Messaging API"
---

# Настройка LINE

Запусти Hermes Agent как бота [LINE](https://line.me/) через официальное LINE Messaging API. Адаптер находится в виде встроенного плагина платформы в `plugins/platforms/line/` — правок ядра не требуется, просто включи его как любую другую платформу.

LINE — доминирующее приложение для обмена сообщениями в Японии, Тайване и Таиланде. Если твои пользователи находятся там, именно так они смогут с тобой связаться.

> Выполни `hermes gateway setup` и выбери **LINE** для пошагового руководства.

## Как реагирует бот

| Контекст | Поведение |
|---------|----------|
| **1:1 чат** (`U` ID) | Отвечает на каждое сообщение |
| **Групповой чат** (`C` ID) | Отвечает, если группа находится в списке разрешённых |
| **Комната для нескольких пользователей** (`R` ID) | Отвечает, если комната находится в списке разрешённых |

Входящие текст, изображения, аудио, видео, файлы, стикеры и локации обрабатываются. Исходящий текст использует **бесплатный токен ответа первым** (одноразовый, окно ≈ 60 с) и переходит к платному Push API, когда токен истёк.

---

## Шаг 1: Создай канал LINE Messaging API

1. Перейди в [LINE Developers Console](https://developers.line.biz/console/).
2. Создай Provider, затем в нём канал **Messaging API**.
3. На вкладке **Basic settings** канала скопируй **Channel secret**.
4. На вкладке **Messaging API** прокрути до **Channel access token (long-lived)** и нажми **Issue**. Скопируй токен.
5. На той же вкладке **Messaging API** отключи **Auto-reply messages** и **Greeting messages**, чтобы они не конфликтовали с ответами твоего бота.

---

## Шаг 2: Открой порт веб‑хука

LINE отправляет веб‑хуки через публичный HTTPS. Порт по умолчанию — `8646` — при необходимости переопредели его переменной `LINE_PORT`.

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

Скопируй URL `https://...` — ты укажешь его ниже как URL веб‑хука. **Оставляй туннель работающим** во время тестов. Для продакшна настрой постоянный именованный туннель Cloudflare, чтобы URL веб‑хука не менялся после перезапуска.

---

## Шаг 3: Настрой Hermes

Добавь в `~/.hermes/.env`:

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

Затем в `~/.hermes/config.yaml`:

```yaml
gateway:
  platforms:
    line:
      enabled: true
```

Этого достаточно — сканирование встроенного плагина в `gateway/config.py` автоматически найдёт `plugins/platforms/line/`. Не требуется правка enum `Platform.LINE` и регистрация `_create_adapter`.

---

## Шаг 4: Укажи URL веб‑хука

Вернись в консоль LINE:

1. Открой свой канал → вкладка **Messaging API**.
2. В разделе **Webhook settings** → **Webhook URL** вставь `https://<your-tunnel>/line/webhook` (обрати внимание на путь `/line/webhook` — адаптер слушает его).
3. Нажми **Verify**. LINE проверит URL; ты должен увидеть статус 200.
4. Переключи **Use webhook** в положение **On**.

---

## Шаг 5: Запусти шлюз

```bash
hermes gateway
```

В журнале агента появится:

```
LINE: webhook listening on 0.0.0.0:8646/line/webhook (public: https://my-tunnel.example.com)
```

Добавь бота в друзья из приложения LINE (отсканируй QR‑код на вкладке **Messaging API** канала) и отправь ему сообщение.

---

## Медленные ответы LLM

Токен ответа LINE одноразовый и истекает примерно через 60 секунд после входящего события. Медленные LLM не успевают ответить, что обычно приводит к платному вызову Push API.

Когда LLM работает дольше `LINE_SLOW_RESPONSE_THRESHOLD` секунд (по умолчанию `45`), адаптер использует исходный токен ответа, чтобы отправить пузырёк **Template Buttons**:

> 🤔 Всё ещё обдумываю. Нажми ниже, чтобы получить ответ, когда он будет готов.
>
> [ Get answer ]

Пользователь нажимает **Get answer** в удобный момент — этот postback доставляет *новый* токен ответа, который адаптер использует для отправки кэшированного ответа (по‑прежнему бесплатно).

Состояния машины: `PENDING → READY → DELIVERED`, плюс `ERROR` для отменённых запусков (состояние `PENDING`, оставшееся «сиротским», преобразуется в «Run was interrupted before completion.» после `/stop`, чтобы постоянная кнопка не зацикливалась).

Чтобы отключить кнопку postback и всегда использовать Push‑fallback:

```env
LINE_SLOW_RESPONSE_THRESHOLD=0
```

Чтобы поток postback срабатывал надёжно, подавляй чат, который мог бы израсходовать токен ответа до наступления порога:

```yaml
# ~/.hermes/config.yaml
display:
  interim_assistant_messages: false
  platforms:
    line:
      tool_progress: off
```

---

## Cron / доставка уведомлений

```env
LINE_HOME_CHANNEL=Uxxxxxxxxxxxxxxxxxxxx     # default delivery target
```

Cron‑задачи с `deliver: line` направляются в `LINE_HOME_CHANNEL`. Адаптер поставляет отдельный отправитель только для Push, поэтому cron‑задачи работают даже если cron запускается в отдельном процессе от шлюза.

---

## Справочник переменных окружения

| Переменная | Обязательно | По умолчанию | Описание |
|---|---|---|---|
| `LINE_CHANNEL_ACCESS_TOKEN` | да | — | Долгоживущий токен доступа канала |
| `LINE_CHANNEL_SECRET` | да | — | Секрет канала (HMAC‑SHA256 проверка веб‑хука) |
| `LINE_HOST` | нет | `0.0.0.0` | Хост привязки веб‑хука |
| `LINE_PORT` | нет | `8646` | Порт привязки веб‑хука |
| `LINE_PUBLIC_URL` | для медиа | — | Публичный HTTPS‑базовый URL; требуется для отправки изображений/голоса/видео |
| `LINE_ALLOWED_USERS` | один из | — | Список ID пользователей через запятую (с префиксом U) |
| `LINE_ALLOWED_GROUPS` | один из | — | Список ID групп через запятую (с префиксом C) |
| `LINE_ALLOWED_ROOMS` | один из | — | Список ID комнат через запятую (с префиксом R) |
| `LINE_ALLOW_ALL_USERS` | только для разработки | `false` | Отключить проверку списка разрешённых полностью |
| `LINE_HOME_CHANNEL` | нет | — | Канал по умолчанию для cron / доставки уведомлений |
| `LINE_SLOW_RESPONSE_THRESHOLD` | нет | `45` | Секунд до срабатывания кнопки postback (`0` = отключено) |
| `LINE_PENDING_TEXT` | нет | "🤔 Still thinking…" | Текст пузырька рядом с кнопкой postback |
| `LINE_BUTTON_LABEL` | нет | "Get answer" | Надпись на кнопке |
| `LINE_DELIVERED_TEXT` | нет | "Already replied ✅" | Ответ, когда уже доставленная кнопка нажата повторно |
| `LINE_INTERRUPTED_TEXT` | нет | "Run was interrupted before completion." | Ответ, когда нажата «сиротская» кнопка после `/stop` |

---

## Устранение неполадок

**«invalid signature» при проверке веб‑хука.** Секрет канала скопирован неверно, либо туннель изменил тело запроса. Сначала проверь с помощью `curl -i https://<tunnel>/line/webhook/health` — должен вернуться `{"status":"ok","platform":"line"}`.

**Бот ничего не получает в группах.** Убедись, что `LINE_ALLOWED_GROUPS` содержит ID группы `C…`. Чтобы узнать ID группы, отправь тестовое сообщение и найди в `~/.hermes/logs/gateway.log` строку `LINE: rejecting unauthorized source` — в словаре отказа указаны ID.

**`send_image` падает с «LINE_PUBLIC_URL must be set».** LINE Messaging API не принимает бинарные загрузки — изображения, аудио и видео должны быть доступны по HTTPS‑URL. Установи `LINE_PUBLIC_URL` в публичный хост туннеля, и адаптер будет обслуживать файлы автоматически по пути `/line/media/<token>/<filename>`.

**Кнопка postback не появляется.** Либо LLM ответил быстрее `LINE_SLOW_RESPONSE_THRESHOLD`, либо другой пузырёк (прогресс инструмента, стриминг) израсходовал токен ответа первым. Смотри блок подавления в разделе «Медленные ответы LLM».

**«already in use by another profile».** Тот же токен доступа канала привязан к другому запущенному профилю Hermes. Останови другой шлюз или используй отдельный канал.

---

## Ограничения

* **Один пузырёк на фрагмент.** Каждый текстовый пузырёк LINE ограничен 5000 символами, и за один вызов Reply/Push можно отправить не более 5 пузырьков. Более длинные ответы обрезаются с многоточием.
* **Нет нативного редактирования сообщений.** У LINE нет API редактирования сообщений — потоковые ответы всегда отправляют новые пузырьки, без изменения предыдущих.
* **Нет рендеринга Markdown.** Жирный (`**`), курсив (`*`), блоки кода и заголовки отображаются как обычный текст. Адаптер удаляет их перед отправкой; URL сохраняются (`[label](url)` превращается в `label (url)`).
* **Индикатор загрузки только в личных чатах.** LINE отклоняет API индикатора набора для групп и комнат, поэтому индикатор печати отображается только в 1:1 чатах.