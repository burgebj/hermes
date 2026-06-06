# QQ Bot

Підключи Hermes до QQ через **Official QQ Bot API (v2)** — підтримка приватних (C2C), групових @‑згадок, гільдій та прямих повідомлень із транскрипцією голосу.

## Огляд

Адаптер QQ Bot використовує [Official QQ Bot API](https://bot.q.qq.com/wiki/develop/api-v2/) для:

- Отримання повідомлень через постійне **WebSocket** з’єднання з QQ **gateway**
- Надсилання текстових та markdown‑відповідей через **REST API**
- Завантаження та обробки зображень, голосових повідомлень і файлових вкладень
- Транскрипції голосових повідомлень за допомогою вбудованого ASR від Tencent або налаштовуваного провайдера STT

## Передумови

1. **QQ Bot Application** — зареєструйся на [q.qq.com](https://q.qq.com):
   - Створи новий застосунок і запиши **App ID** та **App Secret**
   - Увімкни необхідні інтенти: C2C‑повідомлення, групові @‑повідомлення, повідомлення гільдій
   - Налаштуй бота в режимі sandbox для тестування або опублікуй для продакшн

2. **Залежності** — адаптер потребує `aiohttp` та `httpx`:
   ```bash
   pip install aiohttp httpx
   ```

## Конфігурація

### Інтерактивне налаштування

```bash
hermes gateway setup
```

Вибери **QQ Bot** у списку платформ і слідуй підказкам.

### Ручне налаштування

Встанови необхідні змінні середовища у `~/.hermes/.env`:

```bash
QQ_APP_ID=your-app-id
QQ_CLIENT_SECRET=your-app-secret
```

## Змінні середовища

| Variable | Description | Default |
|---|---|---|
| `QQ_APP_ID` | QQ Bot App ID (required) | — |
| `QQ_CLIENT_SECRET` | QQ Bot App Secret (required) | — |
| `QQBOT_HOME_CHANNEL` | OpenID для доставки cron/повідомлень | — |
| `QQBOT_HOME_CHANNEL_NAME` | Відображувана назва домашнього каналу | `Home` |
| `QQ_ALLOWED_USERS` | Список OpenID користувачів, розділений комами, для доступу до DM | open (all users) |
| `QQ_GROUP_ALLOWED_USERS` | Список OpenID груп, розділений комами, для доступу до груп | — |
| `QQ_ALLOW_ALL_USERS` | Встанови `true`, щоб дозволити всі DM | `false` |
| `QQ_PORTAL_HOST` | Перевизначити хост QQ portal (встанови `sandbox.q.qq.com` для sandbox‑маршрутизації) | `q.qq.com` |
| `QQ_STT_API_KEY` | API‑ключ для провайдера voice‑to‑text | — |
| `QQ_STT_BASE_URL` | (Не читається безпосередньо — встанови `platforms.qqbot.extra.stt.baseUrl` у `config.yaml` замість) | n/a |
| `QQ_STT_MODEL` | Назва моделі STT | `glm-asr` |

## Розширена конфігурація

Для детального контролю додай налаштування платформи у `~/.hermes/config.yaml`:

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

## Голосові повідомлення (STT)

Транскрипція голосу працює у два етапи:

1. **QQ built-in ASR** (безкоштовний, завжди пробується першим) — QQ надає `asr_refer_text` у вкладеннях голосових повідомлень, що використовує власне розпізнавання мови Tencent
2. **Налаштований провайдер STT** (запасний варіант) — Якщо ASR від QQ не повертає текст, адаптер викликає сумісний з OpenAI STT API:
   - **Zhipu/GLM (zai)**: провайдер за замовчуванням, використовує модель `glm-asr`
   - **OpenAI Whisper**: встанови `QQ_STT_BASE_URL` та `QQ_STT_MODEL`
   - Будь‑яка сумісна з OpenAI STT‑точка

## Устранення проблем

### Bot disconnects immediately (quick disconnect)

Зазвичай це означає:
- **Invalid App ID / Secret** — перевір свої облікові дані на q.qq.com
- **Missing permissions** — переконайся, що у бота увімкнено потрібні інтенти
- **Sandbox‑only bot** — якщо бот працює в режимі sandbox, він може отримувати повідомлення лише з тестового каналу sandbox QQ

### Voice messages not transcribed

1. Перевір, чи присутній вбудований `asr_refer_text` від QQ у даних вкладення
2. Якщо використовується кастомний STT‑провайдер, переконайся, що `QQ_STT_API_KEY` правильно встановлений
3. Переглянь логи шлюзу на предмет повідомлень про помилки STT

### Messages not delivered

- Переконайся, що **intents** бота увімкнено на q.qq.com
- Перевір `QQ_ALLOWED_USERS`, якщо доступ до DM обмежений
- Для групових повідомлень впевнись, що бот **@згаданий** (політика групи може вимагати whitelist)
- Перевір `QQBOT_HOME_CHANNEL` для доставки cron/повідомлень

### Connection errors

- Переконайся, що `aiohttp` та `httpx` встановлені: `pip install aiohttp httpx`
- Перевір мережеве з’єднання з `api.sgroup.qq.com` та WebSocket‑шлюзом
- Переглянь логи шлюзу для детальних повідомлень про помилки та поведінку перепідключення