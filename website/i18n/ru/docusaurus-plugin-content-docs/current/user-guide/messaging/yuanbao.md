---
sidebar_position: 16
title: "Юаньбао"
description: "Подключи Hermes Agent к корпоративной платформе обмена сообщениями Yuanbao через WebSocket gateway"
---

# Yuanbao

Подключи Hermes к [Yuanbao](https://yuanbao.tencent.com/), корпоративной платформе обмена сообщениями Tencent. Адаптер использует шлюз WebSocket для доставки сообщений в реальном времени и поддерживает как прямые (C2C), так и групповые беседы.

:::info
Yuanbao — это корпоративная платформа обмена сообщениями, в основном используемая внутри Tencent и в корпоративных средах. Она использует WebSocket для коммуникации в реальном времени, аутентификацию на основе HMAC и поддерживает богатые медиа, включая изображения, файлы и голосовые сообщения.
:::
## Предварительные требования

- Учётная запись Yuanbao с правами создания ботов
- APP_ID и APP_SECRET Yuanbao (от администратора платформы)
- Пакеты Python: `websockets` и `httpx`
- Для поддержки медиа: `aiofiles`

Установи необходимые зависимости:

```bash
pip install websockets httpx aiofiles
```
## Настройка

### 1. Создай бота в Yuanbao

1. Скачай приложение Yuanbao по ссылке [https://yuanbao.tencent.com/](https://yuanbao.tencent.com/)
2. В приложении перейди в **PAI → My Bot** и создай нового бота
3. После создания бота скопируй **APP_ID** и **APP_SECRET**

### 2. Запусти мастер настройки

Самый простой способ настроить Yuanbao — через интерактивный мастер:

```bash
hermes gateway setup
```

Выбери **Yuanbao**, когда будет предложено. Мастер выполнит:

1. Запросит твой **APP_ID**
2. Запросит твой **APP_SECRET**
3. Сохранит конфигурацию автоматически

:::tip
WebSocket URL и API Domain имеют разумные значения по умолчанию. Тебе нужно указать только **APP_ID** и **APP_SECRET**, чтобы начать работу.
:::

### 3. Настрой переменные окружения

После первоначальной настройки проверь эти переменные в файле `~/.hermes/.env`:

```bash
# Required
YUANBAO_APP_ID=your-app-id
YUANBAO_APP_SECRET=your-app-secret
YUANBAO_WS_URL=wss://api.yuanbao.example.com/ws
YUANBAO_API_DOMAIN=https://api.yuanbao.example.com

# Optional: bot account ID (normally obtained automatically from sign-token)
# YUANBAO_BOT_ID=your-bot-id

# Optional: internal routing environment (e.g. test/staging/production)
# YUANBAO_ROUTE_ENV=production

# Optional: home channel for cron/notifications (format: direct:<account> or group:<group_code>)
YUANBAO_HOME_CHANNEL=direct:bot_account_id
YUANBAO_HOME_CHANNEL_NAME="Bot Notifications"

# Optional: restrict access (legacy, see Access Control below for fine-grained policies)
YUANBAO_ALLOWED_USERS=user_account_1,user_account_2
```

### 4. Запусти шлюз

```bash
hermes gateway
```

Адаптер подключится к шлюзу WebSocket Yuanbao, аутентифицируется с помощью HMAC‑подписей и начнёт обрабатывать сообщения.
## Возможности

- **WebSocket gateway** — двунаправленная связь в реальном времени
- **HMAC authentication** — безопасное подписание запросов с помощью `APP_ID`/`APP_SECRET`
- **C2C messaging** — прямые беседы пользователь‑бота
- **Group messaging** — беседы в групповых чатах
- **Media support** — изображения, файлы и голосовые сообщения через COS (Cloud Object Storage)
- **Markdown formatting** — сообщения автоматически разбиваются на части в соответствии с ограничениями размера Yuanbao
- **Message deduplication** — предотвращает повторную обработку одного и того же сообщения
- **Heartbeat/keep-alive** — поддерживает стабильность соединения WebSocket
- **Typing indicators** — показывает статус «typing…», пока агент обрабатывает запрос
- **Automatic reconnection** — обрабатывает разрывы WebSocket с экспоненциальным увеличением интервала
- **Group information queries** — получение сведений о группе и списков участников
- **Sticker/Emoji support** — отправка стикеров TIMFaceElem и эмодзи в беседах
- **Auto-sethome** — первый пользователь, написавший боту, автоматически назначается владельцем домашнего канала
- **Slow-response notification** — отправляет сообщение ожидания, когда агент работает дольше ожидаемого
## Параметры конфигурации

### Форматы идентификаторов чатов

Yuanbao использует префиксные идентификаторы в зависимости от типа беседы:

| Тип чата | Формат | Пример |
|-----------|--------|---------|
| Прямое сообщение (C2C) | `direct:<account>` | `direct:user123` |
| Групповое сообщение | `group:<group_code>` | `group:grp456` |

### Загрузка медиа‑файлов

Адаптер Yuanbao автоматически обрабатывает загрузку медиа‑файлов через COS (Tencent Cloud Object Storage):

- **Изображения**: Поддерживает JPEG, PNG, GIF, WebP
- **Файлы**: Поддерживает все распространённые типы документов
- **Голос**: Поддерживает WAV, MP3, OGG

URL‑адреса медиа‑файлов автоматически проверяются и скачиваются перед загрузкой, чтобы предотвратить атаки SSRF.
## Канал «домой»

Используй команду `/sethome` в любом чате Yuanbao (личном или групповом), чтобы назначить его **домашним каналом**. Запланированные задачи (cron‑jobs) будут отправлять свои результаты в этот канал.

:::tip Auto-sethome
Если домашний канал не настроен, первым пользователем, написавшим боту, будет автоматически назначен владелец домашнего канала. Если текущий домашний канал — групповой чат, первое личное сообщение превратит его в прямой чат.
:::

Ты также можешь задать его вручную в `~/.hermes/.env`:

```bash
YUANBAO_HOME_CHANNEL=direct:user_account_id
# or for a group:
# YUANBAO_HOME_CHANNEL=group:group_code
YUANBAO_HOME_CHANNEL_NAME="My Bot Updates"
```

### Пример: установить домашний канал

1. Начни разговор с ботом в Yuanbao
2. Отправь команду: `/sethome`
3. Бот ответит: «Домашний канал установлен на [chat_name] с ID [chat_id]. Cron‑задачи будут доставлять результаты сюда».
4. Будущие cron‑задачи и уведомления будут отправляться в этот канал

### Пример: доставка cron‑задачи

Создай cron‑задачу:

```bash
/cron "0 9 * * *" Check server status
```

Запланированный вывод будет доставлен в твой домашний канал Yuanbao каждый день в 9 утра.
## Советы по использованию

### Начало разговора

Отправь любое сообщение боту в Yuanbao:

```
hello
```

Бот отвечает в той же ветке беседы.

### Доступные команды

Все стандартные команды Hermes работают в Yuanbao:

| Command | Description |
|---------|-------------|
| `/new` | Начать новый разговор |
| `/model [provider:model]` | Показать или изменить модель |
| `/sethome` | Установить этот чат как домашний канал |
| `/status` | Показать информацию о сессии |
| `/help` | Показать доступные команды |

### Отправка файлов

Чтобы отправить файл боту, просто прикрепи его напрямую в чате Yuanbao. Бот автоматически скачает и обработает вложенный файл.

Можно также добавить сообщение к вложению:

```
Please analyze this document
```

### Получение файлов

Когда ты просишь бота создать или экспортировать файл, он отправляет файл напрямую в твой чат Yuanbao.
## Устранение неполадок

### Бот онлайн, но не отвечает на сообщения

**Причина**: Ошибка аутентификации во время рукопожатия WebSocket.

**Решение**:
1. Убедись, что `APP_ID` и `APP_SECRET` указаны правильно.
2. Проверь, доступен ли URL WebSocket.
3. Убедись, что у учётной записи бота есть необходимые разрешения.
4. Просмотри логи шлюза: `tail -f ~/.hermes/logs/gateway.log`

### Ошибка «Connection refused»

**Причина**: URL WebSocket недоступен или указан неверно.

**Решение**:
1. Проверь формат URL WebSocket (должен начинаться с `wss://`).
2. Проверь сетевое соединение с доменом API Yuanbao.
3. Убедись, что брандмауэр пропускает соединения WebSocket.
4. Протестируй URL с помощью: `curl -I https://[YUANBAO_API_DOMAIN]`

### Не удаётся загрузить медиа

**Причина**: Учётные данные COS недействительны или сервер медиа недоступен.

**Решение**:
1. Убедись, что `API_DOMAIN` указан правильно.
2. Проверь, включены ли разрешения на загрузку медиа для твоего бота.
3. Убедись, что медиа‑файл доступен и не повреждён.
4. Проверь конфигурацию бакета COS у администратора платформы.

### Сообщения не доставляются в домашний канал

**Причина**: Формат ID домашнего канала неверен или cron‑задача не сработала.

**Решение**:
1. Убедись, что `YUANBAO_HOME_CHANNEL` задан в правильном формате.
2. Протестируй с командой `/sethome` для автоматического определения формата.
3. Проверь расписание cron‑задачи с помощью `/status`.
4. Убедись, что у бота есть разрешения на отправку в целевом чате.

### Частые разрывы соединения

**Причина**: Соединение WebSocket нестабильно или сеть ненадёжна.

**Решение**:
1. Проверь логи шлюза на наличие шаблонов ошибок.
2. Увеличь таймаут heartbeat в настройках соединения.
3. Обеспечь стабильное сетевое соединение с Yuanbao API.
4. Рассмотри возможность включения подробного логирования: `HERMES_LOG_LEVEL=debug`
## Управление доступом

Yuanbao поддерживает тонко настроенный контроль доступа как для прямых сообщений (DM), так и для групповых бесед:

```bash
# DM policy: open (default) | allowlist | disabled
YUANBAO_DM_POLICY=open
# Comma-separated user IDs allowed to DM the bot (only used when DM_POLICY=allowlist)
YUANBAO_DM_ALLOW_FROM=user_id_1,user_id_2

# Group policy: open (default) | allowlist | disabled
YUANBAO_GROUP_POLICY=open
# Comma-separated group codes allowed (only used when GROUP_POLICY=allowlist)
YUANBAO_GROUP_ALLOW_FROM=group_code_1,group_code_2
```

Эти параметры также можно задать в `config.yaml`:

```yaml
platforms:
  yuanbao:
    extra:
      dm_policy: allowlist
      dm_allow_from: "user1,user2"
      group_policy: open
      group_allow_from: ""
```
## Расширенная конфигурация

### Разбиение сообщений

У Yuanbao есть максимальный размер сообщения. Hermes автоматически разбивает большие ответы, учитывая разметку Markdown (сохраняя блоки кода, таблицы и границы абзацев).

### Параметры подключения

Следующие параметры подключения встроены в адаптер с разумными значениями по умолчанию:

| Parameter | Default Value | Description |
|-----------|---------------|-------------|
| WebSocket connect timeout | 15 seconds | Время ожидания рукопожатия WS |
| Heartbeat interval | 30 seconds | Частота ping‑ов для поддержания соединения |
| Max reconnect attempts | 100 | Максимальное количество попыток переподключения |
| Reconnect backoff | 1s → 60s (exponential) | Время ожидания между попытками переподключения |
| Reply heartbeat interval | 2 seconds | Частота отправки статуса RUNNING |
| Send timeout | 30 seconds | Таймаут для исходящих сообщений WS |

:::note
Эти значения в текущей версии нельзя изменить через переменные окружения. Они оптимизированы для типовых развертываний Yuanbao.
:::

### Подробное логирование

Включи отладочный журнал для устранения проблем с подключением:

```bash
HERMES_LOG_LEVEL=debug hermes gateway
```
## Интеграция с другими функциями

### Cron Jobs

Планируй задачи, которые запускаются на Yuanbao:

```
/cron "0 */4 * * *" Report system health
```

Результаты доставляются в твой домашний канал.

### Background Tasks

Запускай фоновые задачи без блокировки диалога:

```
/background Analyze all files in the archive
```

### Cross-Platform Messages

Отправляй кроссплатформенные сообщения из CLI в Yuanbao:

```bash
hermes chat -q "Send 'Hello from CLI' to yuanbao:group:group_code"
```
## Связанная документация

- [Обзор шлюза обмена сообщениями](./index.md)
- [Справочник слеш‑команд](/reference/slash-commands)
- [Cron‑задачи](/user-guide/features/cron)
- [Фоновые сессии](/user-guide/cli#background-sessions)