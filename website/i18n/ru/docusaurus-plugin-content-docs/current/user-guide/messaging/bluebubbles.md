# BlueBubbles (iMessage)

Подключи Hermes к Apple iMessage через [BlueBubbles](https://bluebubbles.app/) — бесплатный, открытый сервер macOS, который соединяет iMessage с любым устройством.

## Требования

- **Mac** (всегда включённый) с запущенным [BlueBubbles Server](https://bluebubbles.app/)
- Apple ID, вошедший в Messages.app на этом Mac
- BlueBubbles Server v1.0.0+ (веб‑хуки требуют эту версию)
- Сетевое соединение между Hermes и сервером BlueBubbles

## Настройка

### 1. Установи BlueBubbles Server

Скачай и установи с [bluebubbles.app](https://bluebubbles.app/). Заверши мастер настройки — войди с Apple ID и выбери метод подключения (локальная сеть, Ngrok, Cloudflare или Dynamic DNS).

### 2. Получи URL сервера и пароль

В BlueBubbles Server → **Settings → API** запиши:
- **Server URL** (например, `http://192.168.1.10:1234`)
- **Server Password**

### 3. Настрой Hermes

Запусти мастер настройки:

```bash
hermes gateway setup
```

Выбери **BlueBubbles (iMessage)** и введи URL сервера и пароль.

Или задай переменные окружения напрямую в `~/.hermes/.env`:

```bash
BLUEBUBBLES_SERVER_URL=http://192.168.1.10:1234
BLUEBUBBLES_PASSWORD=your-server-password
```

### 4. Авторизуй пользователей

Выбери один из подходов:

**DM Pairing (рекомендовано):**
Когда кто‑то пишет тебе в iMessage, Hermes автоматически отправит ему код сопряжения. Подтверди его с помощью:

```bash
hermes pairing approve bluebubbles <CODE>
```

Используй `hermes pairing list`, чтобы увидеть ожидающие коды и одобренных пользователей.

**Предварительно авторизовать конкретных пользователей** (в `~/.hermes/.env`):

```bash
BLUEBUBBLES_ALLOWED_USERS=user@icloud.com,+15551234567
```

**Открытый доступ** (в `~/.hermes/.env`):

```bash
BLUEBUBBLES_ALLOW_ALL_USERS=true
```

### 5. Запусти шлюз

```bash
hermes gateway run
```

Hermes подключится к твоему серверу BlueBubbles, зарегистрирует веб‑хук и начнёт слушать сообщения iMessage.

## Как это работает

```
iMessage → Messages.app → BlueBubbles Server → Webhook → Hermes
Hermes → BlueBubbles REST API → Messages.app → iMessage
```

- **Входящие:** BlueBubbles отправляет события веб‑хука локальному слушателю при поступлении новых сообщений. Нет опроса — мгновенная доставка.
- **Исходящие:** Hermes отправляет сообщения через REST API BlueBubbles.
- **Медиа:** Поддерживаются изображения, голосовые сообщения, видео и документы в обоих направлениях. Входящие вложения скачиваются и кэшируются локально для обработки агентом.

## Переменные окружения

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BLUEBUBBLES_SERVER_URL` | Yes | — | URL сервера BlueBubbles |
| `BLUEBUBBLES_PASSWORD` | Yes | — | Пароль сервера |
| `BLUEBUBBLES_WEBHOOK_HOST` | No | `127.0.0.1` | Адрес привязки слушателя веб‑хука |
| `BLUEBUBBLES_WEBHOOK_PORT` | No | `8645` | Порт слушателя веб‑хука |
| `BLUEBUBBLES_WEBHOOK_PATH` | No | `/bluebubbles-webhook` | Путь URL веб‑хука |
| `BLUEBUBBLES_HOME_CHANNEL` | No | — | Телефон/почта для доставки cron |
| `BLUEBUBBLES_ALLOWED_USERS` | No | — | Список разрешённых пользователей через запятую |
| `BLUEBUBBLES_ALLOW_ALL_USERS` | No | `false` | Разрешить всех пользователей |

Автоматическая пометка сообщений как прочитанных управляется ключом `send_read_receipts` в `platforms.bluebubbles.extra` файла `~/.hermes/config.yaml` (по умолчанию — `true`). Соответствующей переменной окружения нет.

## Возможности

### Текстовые сообщения
Отправка и получение iMessage. Markdown автоматически удаляется для чистой доставки в виде простого текста.

### Богатые медиа
- **Изображения:** Фото отображаются нативно в разговоре iMessage
- **Голосовые сообщения:** Аудиофайлы отправляются как голосовые сообщения iMessage
- **Видео:** Видеовложения
- **Документы:** Файлы отправляются как вложения iMessage

### Реакции Tapback
Любовь, лайк, дизлайк, смех, акцент и вопрос. Требуется [Private API helper](https://docs.bluebubbles.app/helper-bundle/installation) BlueBubbles.

### Индикаторы набора
Показывает «typing…» в разговоре iMessage, пока агент обрабатывает запрос. Требуется Private API.

### Квитанции о прочтении
Автоматически помечает сообщения как прочитанные после обработки. Требуется Private API.

### Адресация чатов
Можно обращаться к чатам по email или номеру телефона — Hermes автоматически преобразует их в GUID‑ы чатов BlueBubbles. Не нужно использовать сырой формат GUID.

## Private API

Некоторые функции требуют [Private API helper](https://docs.bluebubbles.app/helper-bundle/installation) BlueBubbles:
- Реакции Tapback
- Индикаторы набора
- Квитанции о прочтении
- Создание новых чатов по адресу

Без Private API работают базовые текстовые сообщения и медиа.

## Устранение неполадок

### «Cannot reach server»
- Проверь, что URL сервера правильный и Mac включён
- Убедись, что BlueBubbles Server запущен
- Проверь сетевое соединение (фаервол, проброс портов)

### Сообщения не приходят
- Убедись, что веб‑хук зарегистрирован в BlueBubbles Server → Settings → API → Webhooks
- Проверь, что URL веб‑хука доступен с Mac
- Посмотри `hermes logs gateway` на ошибки веб‑хука (или `hermes logs -f` для реального времени)

### «Private API helper not connected»
- Установи Private API helper: [docs.bluebubbles.app](https://docs.bluebubbles.app/helper-bundle/installation)
- Базовые сообщения работают без него — только реакции, индикаторы набора и квитанции о прочтении требуют его.