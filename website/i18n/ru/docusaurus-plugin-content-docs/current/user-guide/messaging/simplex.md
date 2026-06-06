# SimpleX Chat

[SimpleX Chat](https://simplex.chat/) — это приватная децентрализованная платформа обмена сообщениями, где пользователи владеют своими контактами и группами. В отличие от других платформ, SimpleX не назначает постоянные идентификаторы пользователей — каждый контакт идентифицируется непрозрачным внутренним ID, генерируемым во время соединения, что делает его одним из самых приватных мессенджеров.

> Запусти `hermes gateway setup` и выбери **SimpleX** для пошагового руководства.

## Требования

- Установленный CLI **simplex-chat**, работающий как демон
- Python‑пакет **websockets** (`pip install websockets`)

## Установка simplex-chat

Скачай последнюю версию со страницы [simplex-chat GitHub releases](https://github.com/simplex-chat/simplex-chat/releases):

```bash
# Linux / macOS binary
curl -L https://github.com/simplex-chat/simplex-chat/releases/latest/download/simplex-chat-ubuntu-22_04-x86-64 -o simplex-chat
chmod +x simplex-chat
```

Проект SimpleX Chat не публикует готовый Docker‑образ для клиента чата; чтобы запустить его в Docker, собери образ из исходников репозитория [simplex-chat](https://github.com/simplex-chat/simplex-chat).

## Запуск демона

```bash
simplex-chat -p 5225
```

По умолчанию демон слушает WebSocket по адресу `ws://127.0.0.1:5225`.

## Настройка Hermes

### Через мастер настройки

```bash
hermes setup gateway
```

Выбери **SimpleX Chat** и следуй подсказкам.

### Через переменные окружения

Добавь следующее в `~/.hermes/.env`:

```
SIMPLEX_WS_URL=ws://127.0.0.1:5225
SIMPLEX_ALLOWED_USERS=<contact-id-1>,<contact-id-2>
SIMPLEX_HOME_CHANNEL=<contact-id>
```

| Variable | Required | Description |
|---|---|---|
| `SIMPLEX_WS_URL` | Yes | WebSocket URL демона simplex-chat |
| `SIMPLEX_ALLOWED_USERS` | Recommended | Список ID контактов, разделённых запятыми, которым разрешено использовать агент |
| `SIMPLEX_ALLOW_ALL_USERS` | Optional | Установи `true`, чтобы разрешить всем контактам (используй с осторожностью) |
| `SIMPLEX_HOME_CHANNEL` | Optional | ID контакта по умолчанию для доставки cron‑задач |
| `SIMPLEX_HOME_CHANNEL_NAME` | Optional | Человекочитаемая метка домашнего канала |

## Как найти свой ID контакта

После запуска демона открой разговор со своим контакт‑агентом. ID контакта появится в логах сессии или через `hermes send_message action=list`.

## Авторизация

По умолчанию **все контакты отклоняются**. Нужно выполнить одно из следующих действий:

1. Установить `SIMPLEX_ALLOWED_USERS` со списком ID контактов, разделённых запятыми, или
2. Использовать **DM‑паринг** — отправь любое сообщение боту, и он ответит кодом паринга. Введи этот код через `hermes gateway pair`.

## Использование SimpleX с cron‑задачами

```python
cronjob(
    action="create",
    schedule="every 1h",
    deliver="simplex",          # uses SIMPLEX_HOME_CHANNEL
    prompt="Check for alerts and summarise."
)
```

Или указать конкретный контакт:

```python
send_message(target="simplex:<contact-id>", message="Done!")
```

## Примечания о приватности

- SimpleX никогда не раскрывает номера телефонов или адреса электронной почты — контакты используют непрозрачные ID
- Соединение между Hermes и демоном локальное, через WebSocket (`ws://127.0.0.1:5225`) — данные не покидают твой компьютер
- Сообщения защищены сквозным шифрованием протокола SimpleX до передачи демону

## Устранение неполадок

**"Cannot reach daemon"** — убедись, что `simplex-chat -p 5225` запущен и порт совпадает с `SIMPLEX_WS_URL`.

**"websockets not installed"** — выполни `pip install websockets`.

**Messages not received** — проверь, что ID контакта присутствует в `SIMPLEX_ALLOWED_USERS` или одобри его через DM‑паринг.