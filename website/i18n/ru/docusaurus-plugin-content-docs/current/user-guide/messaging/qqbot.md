# QQ Bot

Подключи Hermes к QQ через **Official QQ Bot API (v2)** — поддержка личных (C2C), групповых @‑упоминаний, гильдий и прямых сообщений с транскрипцией голоса.

## Overview

Адаптер QQ Bot использует [Official QQ Bot API](https://bot.q.qq.com/wiki/develop/api-v2/) для:

- Приёма сообщений через постоянное **WebSocket**‑соединение с QQ gateway
- Отправки текстовых и markdown‑ответов через **REST API**
- Загрузки и обработки изображений, голосовых сообщений и вложений файлов
- Транскрибирования голосовых сообщений с помощью встроенного ASR от Tencent или настраиваемого провайдера STT

## Prerequisites

1. **QQ Bot Application** — зарегистрируйся на [q.qq.com](https://q.qq.com):
   - Создай новое приложение и запиши **App ID** и **App Secret**
   - Включи необходимые intents: C2C‑сообщения, групповые @‑сообщения, сообщения гильдий
   - Настрой бота в режиме sandbox для тестирования или опубликуй для продакшн

2. **Dependencies** — адаптер требует `aiohttp` и `httpx`:
   ```bash
   pip install aiohttp httpx
   ```

## Configuration

### Interactive setup

```bash
hermes gateway setup
```

Выбери **QQ Bot** из списка платформ и следуй подсказкам.

### Manual configuration

Установи необходимые переменные окружения в `~/.hermes/.env`:

```bash
QQ_APP_ID=your-app-id
QQ_CLIENT_SECRET=your-app-secret
```

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `QQ_APP_ID` | QQ Bot App ID (required) | — |
| `QQ_CLIENT_SECRET` | QQ Bot App Secret (required) | — |
| `QQBOT_HOME_CHANNEL` | OpenID для доставки cron/уведомлений | — |
| `QQBOT_HOME_CHANNEL_NAME` | Отображаемое имя домашнего канала | `Home` |
| `QQ_ALLOWED_USERS` | Список OpenID пользователей через запятую для доступа к DM | open (all users) |
| `QQ_GROUP_ALLOWED_USERS` | Список OpenID групп через запятую для доступа к группам | — |
| `QQ_ALLOW_ALL_USERS` | Установи `true`, чтобы разрешить все DM | `false` |
| `QQ_PORTAL_HOST` | Переопределить хост QQ portal (установи `sandbox.q.qq.com` для маршрутизации в sandbox) | `q.qq.com` |
| `QQ_STT_API_KEY` | API‑ключ провайдера voice‑to‑text | — |
| `QQ_STT_BASE_URL` | (Не читается напрямую — вместо этого установи `platforms.qqbot.extra.stt.baseUrl` в `config.yaml`) | n/a |
| `QQ_STT_MODEL` | Название модели STT | `glm-asr` |

## Advanced Configuration

Для более тонкой настройки добавь параметры платформы в `~/.hermes/config.yaml`:

```yaml
platforms:
  qqbot:
    enabled: true
    extra:
      app_id: "your-app-id"
      client_secret: "your-secret"
      markdown_support: true       # enable QQ markdown (msg_type 2). Config-only; no env-var equivalent.
      dm_policy: "open"          # open | allowlist | disabled
      allow_from:
        - "user_openid_1"
      group_policy: "open"       # open | allowlist | disabled
      group_allow_from:
        - "group_openid_1"
      stt:
        provider: "zai"          # zai (GLM-ASR), openai (Whisper), etc.
        baseUrl: "https://open.bigmodel.cn/api/coding/paas/v4"
        apiKey: "your-stt-key"
        model: "glm-asr"
```

## Voice Messages (STT)

Транскрипция голоса происходит в два этапа:

1. **QQ built-in ASR** (бесплатно, всегда пробуется первой) — QQ предоставляет `asr_refer_text` в вложениях голосовых сообщений, используя собственный распознаватель речи Tencent
2. **Configured STT provider** (запасной вариант) — если ASR от QQ не вернул текст, адаптер вызывает совместимый с OpenAI STT API:
   - **Zhipu/GLM (zai)**: провайдер по умолчанию, использует модель `glm-asr`
   - **OpenAI Whisper**: укажи `QQ_STT_BASE_URL` и `QQ_STT_MODEL`
   - Любой совместимый с OpenAI STT endpoint

## Troubleshooting

### Bot disconnects immediately (quick disconnect)

Обычно это означает:
- **Invalid App ID / Secret** — проверь свои учётные данные на q.qq.com
- **Missing permissions** — убедись, что у бота включены необходимые intents
- **Sandbox-only bot** — если бот работает в sandbox‑режиме, он может получать сообщения только из тестового канала sandbox QQ

### Voice messages not transcribed

1. Проверь, присутствует ли `asr_refer_text` от QQ в данных вложения
2. Если используется кастомный STT‑провайдер, убедись, что `QQ_STT_API_KEY` правильно установлен
3. Проверь логи шлюза на наличие сообщений об ошибках STT

### Messages not delivered

- Убедись, что **intents** бота включены на q.qq.com
- Проверь `QQ_ALLOWED_USERS`, если доступ к DM ограничен
- Для групповых сообщений убедись, что бот **@упомянут** (политика группы может требовать whitelist)
- Проверь `QQBOT_HOME_CHANNEL` для доставки cron/уведомлений

### Connection errors

- Убедись, что `aiohttp` и `httpx` установлены: `pip install aiohttp httpx`
- Проверь сетевое соединение с `api.sgroup.qq.com` и WebSocket‑шлюзом
- Просмотри логи шлюза для детальных сообщений об ошибках и поведении при переподключении