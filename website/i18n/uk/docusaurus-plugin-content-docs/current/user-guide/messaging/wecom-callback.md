---
sidebar_position: 15
---

# WeCom Callback (Self‑Built App)

Підключи Hermes до WeCom (Enterprise WeChat) як самостійно створений корпоративний застосунок, використовуючи модель callback/webhook.

:::info WeCom Bot vs WeCom Callback
Hermes підтримує два режими інтеграції з WeCom:
- **[WeCom Bot](wecom.md)** — бот‑стиль, підключається через WebSocket. Простіше налаштування, працює в групових чатах.
- **WeCom Callback** (ця сторінка) — самостійно створений застосунок, отримує зашифровані XML‑callback’и. Відображається як повноцінний застосунок у боковій панелі користувачів WeCom. Підтримує маршрутизацію між кількома корпораціями.
:::

Дивись також: [WeCom Bot](./wecom.md) для інтеграції в бот‑стилі.

> Запусти `hermes gateway setup` і обери **WeCom Callback** для покрокового налаштування.

## Як це працює

1. Реєструєш самостійно створений застосунок у консолі адміністрування WeCom.
2. WeCom надсилає зашифрований XML на твій HTTP‑endpoint callback.
3. Hermes розшифровує повідомлення, ставить його в чергу для агента.
4. Одразу надсилає підтвердження (тихо — користувач нічого не бачить).
5. Агент обробляє запит (зазвичай 3–30 хв).
6. Відповідь надсилається проактивно через API WeCom `message/send`.

## Передумови

- Корпоративний обліковий запис WeCom з правами адміністратора.
- Пакети Python `aiohttp` і `httpx` (включені в стандартну інсталяцію).
- Публічно доступний сервер для URL callback (або тунель типу ngrok).

## Налаштування

### 1. Створи самостійно створений застосунок у WeCom

1. Перейди до [WeCom Admin Console](https://work.weixin.qq.com/) → **Applications** → **Create App**.
2. Запиши **Corp ID** (відображається у верхній частині консолі).
3. У налаштуваннях застосунку створи **Corp Secret**.
4. Запиши **Agent ID** зі сторінки огляду застосунку.
5. У розділі **Receive Messages** вкажи URL callback:
   - URL: `http://YOUR_PUBLIC_IP:8645/wecom/callback`
   - Token: згенеруй випадковий токен (WeCom надає).
   - EncodingAESKey: згенеруй ключ (WeCom надає).

### 2. Налаштуй змінні середовища

Додай у файл `.env`:

```bash
WECOM_CALLBACK_CORP_ID=your-corp-id
WECOM_CALLBACK_CORP_SECRET=your-corp-secret
WECOM_CALLBACK_AGENT_ID=1000002
WECOM_CALLBACK_TOKEN=your-callback-token
WECOM_CALLBACK_ENCODING_AES_KEY=your-43-char-aes-key

# Optional
WECOM_CALLBACK_HOST=0.0.0.0
WECOM_CALLBACK_PORT=8645
WECOM_CALLBACK_ALLOWED_USERS=user1,user2
```

### 3. Запусти шлюз

```bash
hermes gateway
```

(Використовуй `hermes gateway start` лише після того, як `hermes gateway install` зареєстрував службу systemd/launchd.)

Адаптер callback запускає HTTP‑сервер на вказаному порту. WeCom перевіряє URL callback за допомогою GET‑запиту, після чого починає надсилати повідомлення через POST.

## Довідник конфігурації

Вкажи ці параметри у `config.yaml` під `platforms.wecom_callback.extra` або за допомогою змінних середовища:

| Параметр | За замовчуванням | Опис |
|---------|------------------|------|
| `corp_id` | — | Corp ID корпорації WeCom (обов’язково) |
| `corp_secret` | — | Corp Secret для самостійно створеного застосунку (обов’язково) |
| `agent_id` | — | Agent ID застосунку (обов’язково) |
| `token` | — | Токен для верифікації callback (обов’язково) |
| `encoding_aes_key` | — | 43‑символьний AES‑ключ для шифрування callback (обов’язково) |
| `host` | `0.0.0.0` | Адреса прив’язки HTTP‑серверу callback |
| `port` | `8645` | Порт HTTP‑серверу callback |
| `path` | `/wecom/callback` | Шлях URL для endpoint‑а callback |

## Маршрутизація між кількома застосунками

Для корпорацій, що використовують кілька самостійно створених застосунків (наприклад, у різних підрозділах чи дочірніх компаніях), налаштуй список `apps` у `config.yaml`:

```yaml
platforms:
  wecom_callback:
    enabled: true
    extra:
      host: "0.0.0.0"
      port: 8645
      apps:
        - name: "dept-a"
          corp_id: "ww_corp_a"
          corp_secret: "secret-a"
          agent_id: "1000002"
          token: "token-a"
          encoding_aes_key: "key-a-43-chars..."
        - name: "dept-b"
          corp_id: "ww_corp_b"
          corp_secret: "secret-b"
          agent_id: "1000003"
          token: "token-b"
          encoding_aes_key: "key-b-43-chars..."
```

Користувачі розмежовуються за `corp_id:user_id`, щоб уникнути колізій між корпораціями. Коли користувач надсилає повідомлення, адаптер фіксує, до якої корпорації (застосунку) він належить, і маршрутизує відповіді через відповідний токен доступу.

## Контроль доступу

Обмежи, які користувачі можуть взаємодіяти із застосунком:

```bash
# Allowlist specific users
WECOM_CALLBACK_ALLOWED_USERS=zhangsan,lisi,wangwu

# Or allow all users
WECOM_CALLBACK_ALLOW_ALL_USERS=true
```

## Endpoint‑и

Адаптер надає такі endpoint‑и:

| Метод | Шлях | Призначення |
|-------|------|--------------|
| GET | `/wecom/callback` | Перевірка URL (handshake) під час налаштування |
| POST | `/wecom/callback` | За­шифрований callback‑повідомлення (користувацькі повідомлення) |
| GET | `/health` | Перевірка працездатності — повертає `{"status": "ok"}` |

## Шифрування

Усі payload‑и callback зашифровані AES‑CBC за допомогою `EncodingAESKey`. Адаптер виконує:

- **Вхідне**: розшифровка XML‑payload, перевірка SHA1‑підпису.
- **Вихідне**: відповіді надсилаються проактивно через API (відповідь у callback не шифрується).

Реалізація криптографії сумісна з офіційним SDK Tencent WXBizMsgCrypt.

## Обмеження

- **Без потокової передачі** — відповіді надходять повністю після завершення роботи агента.
- **Без індикаторів набору** — модель callback не підтримує статус набору.
- **Тільки текст** — наразі підтримуються лише текстові повідомлення на вхід; вхідні зображення/файли/голос ще не реалізовано. Агент знає про можливості вихідних медіа (зображення, документи, відео, голос) через підказки платформи WeCom.
- **Затримка відповіді** — сесії агента тривають 3–30 хв; користувач бачить відповідь лише після завершення обробки.

## Устранення проблем

**Не вдається перевірити підпис.**
WeCom підписує кожен запит токеном **Token**, який ти зареєстрував у консолі адміністрування. Найчастіша причина — розбіжність між токеном, вказаним у Hermes, і токеном, очікуваним консоллю. Перепиши **Token** і **EncodingAESKey** з консолі — їх легко обрізати. Пробіли у значеннях `~/.hermes/.env` навколо `=` також порушують перевірку підпису. Після виправлення перезапусти `hermes gateway run`.

**URL callback недоступний / не проходить верифікація.**
WeCom звертається до публічного URL, який ти вказав. Перевір:
1. Твій reverse‑proxy або тунель переспрямовує `/wecom/callback` на порт шлюзу.
2. URL у консолі адміністрування — HTTPS (WeCom відхиляє простий HTTP).
3. Ззовні мережі команда `curl -i https://<your-domain>/wecom/callback` повертає не timeout (4xx без параметрів запиту підходить — це лише підтверджує, що listener доступний).

**Порт недоступний / listener не прив’язаний.**
Переглянь логи `hermes gateway run` щодо прив’язаного host/port. Якщо адаптер прив’язався до `127.0.0.1`, потрібно розмістити його за reverse‑proxy або тунелем — сервери WeCom не можуть дістатися loopback. Встанови `extra.host: 0.0.0.0` у `config.yaml` (і, за потреби, `allowed_source_cidrs`, якщо відкриваєш напряму) або залишай loopback і використай тунель типу Cloudflare Tunnel або nginx.