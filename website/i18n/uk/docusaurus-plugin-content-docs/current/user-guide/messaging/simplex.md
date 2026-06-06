# SimpleX Chat

[SimpleX Chat](https://simplex.chat/) — це приватна, децентралізована платформа обміну повідомленнями, де користувачі володіють своїми контактами та групами. На відміну від інших платформ, SimpleX не присвоює постійних ідентифікаторів користувачів — кожен контакт ідентифікується непрозорим внутрішнім ID, створеним під час підключення, що робить його одним із найприватніших месенджерів.

> Запусти `hermes gateway setup` і вибери **SimpleX** для покрокового налаштування.

## Передумови

- CLI **simplex-chat**, встановлений і запущений як демон
- Python‑пакет **websockets** (`pip install websockets`)

## Встановити simplex-chat

Завантажте останній реліз зі сторінки [simplex-chat GitHub releases](https://github.com/simplex-chat/simplex-chat/releases):

```bash
# Linux / macOS binary
curl -L https://github.com/simplex-chat/simplex-chat/releases/latest/download/simplex-chat-ubuntu-22_04-x86-64 -o simplex-chat
chmod +x simplex-chat
```

Проект SimpleX Chat не публікує готовий Docker‑образ для клієнта чату; щоб запустити його в Docker, зберіть його з вихідного коду з [репозиторію simplex-chat](https://github.com/simplex-chat/simplex-chat).

## Запуск демона

```bash
simplex-chat -p 5225
```

Демон за замовчуванням слухає WebSocket за адресою `ws://127.0.0.1:5225`.

## Налаштування Hermes

### Через майстер налаштувань

```bash
hermes setup gateway
```

Виберіть **SimpleX Chat** і дотримуйтесь підказок.

### Через змінні середовища

Додайте наступне до `~/.hermes/.env`:

```
SIMPLEX_WS_URL=ws://127.0.0.1:5225
SIMPLEX_ALLOWED_USERS=<contact-id-1>,<contact-id-2>
SIMPLEX_HOME_CHANNEL=<contact-id>
```

| Змінна | Обов’язково | Опис |
|---|---|---|
| `SIMPLEX_WS_URL` | Так | URL WebSocket демона simplex-chat |
| `SIMPLEX_ALLOWED_USERS` | Рекомендовано | Список ID контактів, розділених комами, яким дозволено користуватися агентом |
| `SIMPLEX_ALLOW_ALL_USERS` | Необов’язково | Встанови `true`, щоб дозволити всім контактам (використовуй обережно) |
| `SIMPLEX_HOME_CHANNEL` | Необов’язково | ID контакту за замовчуванням для доставки cron‑завдань |
| `SIMPLEX_HOME_CHANNEL_NAME` | Необов’язково | Людська назва домашнього каналу |

## Дізнатися свій ID контакту

Після запуску демона відкрий розмову зі своїм контактом‑агентом. ID контакту з’явиться в логах сесії або за допомогою `hermes send_message action=list`.

## Авторизація

За замовчуванням **всі контакти заборонені**. Потрібно виконати одне з наступного:

1. Встановити `SIMPLEX_ALLOWED_USERS` зі списком ID контактів, розділених комами, або
2. Використати **DM pairing** — надішли будь‑яке повідомлення боту, і він відповість кодом парування. Введи цей код через `hermes gateway pair`.

## Використання SimpleX з cron‑завданнями

```python
cronjob(
    action="create",
    schedule="every 1h",
    deliver="simplex",          # uses SIMPLEX_HOME_CHANNEL
    prompt="Check for alerts and summarise."
)
```

Або вкажи конкретний контакт:

```python
send_message(target="simplex:<contact-id>", message="Done!")
```

## Примітки щодо приватності

- SimpleX ніколи не розкриває номери телефонів чи електронні адреси — контакти використовують непрозорі ID
- З’єднання між Hermes і демоном локальне WebSocket (`ws://127.0.0.1:5225`) — жодні дані не покидають твій комп’ютер
- Повідомлення шифруються наскрізно протоколом SimpleX ще до передачі демону

## Усунення проблем

**"Cannot reach daemon"** — Переконайся, що `simplex-chat -p 5225` запущений і порт збігається з `SIMPLEX_WS_URL`.

**"websockets not installed"** — Запусти `pip install websockets`.

**Messages not received** — Перевір, чи ID контакту присутній у `SIMPLEX_ALLOWED_USERS` або підтверди його через DM pairing.