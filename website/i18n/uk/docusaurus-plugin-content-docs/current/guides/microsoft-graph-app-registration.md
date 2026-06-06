---
title: "Зареєструй застосунок Microsoft Graph"
description: "Покроковий посібник у Azure portal зі створення реєстрації додатку, що живить конвеєр зустрічей Teams"
---

# Зареєструвати застосунок Microsoft Graph

Конвеєр Teams meeting читає транскрипти зустрічей, записи та пов’язані артефакти з Microsoft Graph за допомогою **app‑only** (демон) автентифікації — без входу користувача, без інтерактивної згоди під час кожної зустрічі. Для цього потрібна реєстрація додатку Azure AD з дозволами, наданими адміністратором.

У цьому посібнику розглянуто:

1. Створення реєстрації застосунку
2. Створення клієнтського секрету
3. Надання дозволів Graph API, які потрібні конвеєру
4. Адміністраторське надання згоди на ці дозволи
5. (Необов’язково) Обмеження застосунку конкретними користувачами за допомогою Application Access Policy

Тобі потрібні **права адміністратора тенанта** (або адміністратор, який надасть згоду від твого імені), щоб завершити процес. Запиши значення, які збираєш — вони підуть у `~/.hermes/.env` в кінці.

## Передумови

- Тенант Microsoft 365 з ліцензіями Teams Premium або Teams, які генерують транскрипти та записи зустрічей
- Доступ адміністратора до порталу Azure за адресою [entra.microsoft.com](https://entra.microsoft.com)
- Публічно доступна HTTPS‑точка для сповіщень про зміни Graph (буде налаштована пізніше, у кроці налаштування веб‑хука)

## Крок 1: Створити реєстрацію застосунку

1. Увійди до [entra.microsoft.com](https://entra.microsoft.com) як адміністратор тенанта.
2. Перейди до **Identity → Applications → App registrations**.
3. Натисни **New registration**.
4. Заповни:
   - **Name:** `Hermes Teams Meeting Pipeline` (або будь‑яку назву, яку ти впізнаєш).
   - **Supported account types:** *Accounts in this organizational directory only (Single tenant)*.
   - **Redirect URI:** залиш порожнім — для app‑only автентифікації URI не потрібен.
5. Натисни **Register**.

Ти потрапиш на сторінку огляду застосунку. Скопіюй два значення:

- **Application (client) ID** → `MSGRAPH_CLIENT_ID`
- **Directory (tenant) ID** → `MSGRAPH_TENANT_ID`

## Крок 2: Створити клієнтський секрет

1. У лівій навігації відкрий **Certificates & secrets**.
2. Натисни **New client secret**.
3. **Description:** `hermes-graph-secret`. **Expires:** вибери значення, що відповідає твоїй політиці ротації (зазвичай 6‑24 міс.)
4. Натисни **Add**.
5. Одразу скопіюй колонку **Value** — вона показується лише один раз. Це значення `MSGRAPH_CLIENT_SECRET`.

> Колонка **Secret ID** не є секретом. Потрібна колонка **Value**.

## Крок 3: Надати дозволи Graph API

Конвеєр використовує мінімальний набір дозволів застосунку. Додай лише те, що потрібно; кожен додатковий дозвіл розширює доступ застосунку до даних у всьому тенанті.

1. У лівій навігації відкрий **API permissions**.
2. Натисни **Add a permission** → **Microsoft Graph** → **Application permissions**.
3. Додай дозволи з таблиці нижче, які відповідають потрібним функціям конвеєру.
4. Після додавання натисни **Grant admin consent for `<your tenant>`**. У колонці **Status** має з’явитися зелена галочка для кожного дозволу.

### Потрібно для резюмування на основі транскрипту

| Дозвіл | Що дозволяє застосунку |
|--------|------------------------|
| `OnlineMeetings.Read.All` | Читати метадані онлайн‑зустрічей Teams (тема, учасники, URL приєднання). |
| `OnlineMeetingTranscript.Read.All` | Читати транскрипти зустрічей, створені Teams. |

### Потрібно для резервного запису (коли транскрипт недоступний)

| Дозвіл | Що дозволяє застосунку |
|--------|------------------------|
| `OnlineMeetingRecording.Read.All` | Завантажувати записи зустрічей Teams для офлайн‑обробки STT. |
| `CallRecords.Read.All` | Визначати зустрічі за записами викликів, коли відомий лише URL приєднання. |

### Потрібно для зовнішньої доставки резюме (лише режим Graph)

Якщо `platforms.teams.extra.delivery_mode` має значення `graph`, конвеєр надсилає резюме у канал або чат Teams через Graph API. Пропусти ці дозволи, якщо використовуєш режим доставки `incoming_webhook`.

| Дозвіл | Що дозволяє застосунку |
|--------|------------------------|
| `ChannelMessage.Send` | Публікувати повідомлення у каналах Teams від імені застосунку. |
| `Chat.ReadWrite.All` | Публікувати повідомлення у 1:1 та групових чатах (лише якщо вказано `chat_id` як ціль доставки). |

### Не рекомендовано

- `OnlineMeetings.ReadWrite.All` / `Chat.ReadWrite` без `.All` — надто широкі права.
- Делеговані дозволи — конвеєр працює в режимі app‑only (client‑credentials); делеговані дозволи не працюватимуть без входу користувача.

## Крок 4: (Рекомендовано) Обмежити застосунок Application Access Policy

За замовчуванням дозволи типу `OnlineMeetings.Read.All` дають доступ до **кожної** зустрічі в тенанті. Для демонстрацій і тестових тенантів це прийнятно; для продакшн‑тенанту, швидше за все, треба обмежити, чиї зустрічі може читати застосунок.

Microsoft надає **Application Access Policies** саме для цього. Політика налаштовується лише через PowerShell; у порталі UI її немає.

З адміністраторського PowerShell з встановленим модулем `MicrosoftTeams` та підключенням (`Connect-MicrosoftTeams`):

```powershell
# Create a policy scoped to the Hermes app
New-CsApplicationAccessPolicy `
  -Identity "Hermes-Meeting-Pipeline-Policy" `
  -AppIds "<MSGRAPH_CLIENT_ID>" `
  -Description "Restrict Hermes meeting pipeline to allow-listed users"

# Grant the policy to specific users whose meetings the pipeline may read
Grant-CsApplicationAccessPolicy `
  -PolicyName "Hermes-Meeting-Pipeline-Policy" `
  -Identity "alice@example.com"

Grant-CsApplicationAccessPolicy `
  -PolicyName "Hermes-Meeting-Pipeline-Policy" `
  -Identity "bob@example.com"
```

Розповсюдження може зайняти до 30 хвилин після надання. Перевірити можна за допомогою:

```powershell
Test-CsApplicationAccessPolicy -Identity "alice@example.com" -AppId "<MSGRAPH_CLIENT_ID>"
```

Без політики **будь‑які** зустрічі користувачів будуть доступні — це саме те, що дозволяє дозвіл. Не пропускай цей крок у продакшн‑тенанті.

## Крок 5: Записати облікові дані у файл `.env`

Помісти три зібрані значення у `~/.hermes/.env`:

```bash
MSGRAPH_TENANT_ID=<directory-tenant-id>
MSGRAPH_CLIENT_ID=<application-client-id>
MSGRAPH_CLIENT_SECRET=<client-secret-value>
```

Встанови права доступу, щоб лише ти міг читати секрет:

```bash
chmod 600 ~/.hermes/.env
```

## Крок 6: Перевірити потік токену

Hermes постачається з тестом автентифікації Graph. З твоєї інсталяції Hermes:

```python
python -c "
import asyncio
from tools.microsoft_graph_auth import MicrosoftGraphTokenProvider
provider = MicrosoftGraphTokenProvider.from_env()
token = asyncio.run(provider.get_access_token())
print('Token acquired, length:', len(token))
print(provider.inspect_token_health())
"
```

Успішний запуск виводить довгий рядок токену та словник стану зі значенням `cached: True` і `expires_in_seconds` приблизно 3600. При помилках з’являється `MicrosoftGraphTokenError` з кодом помилки Azure — найчастіші:

| Помилка Azure | Значення | Виправлення |
|---------------|----------|-------------|
| `AADSTS7000215: Invalid client secret` | Неправильне або прострочене значення секрету. | Створи новий секрет у кроці 2; онови `.env`. |
| `AADSTS700016: Application not found` | Неправильний `MSGRAPH_CLIENT_ID` або неправильний тенант. | Перевір, чи значення з кроку 1 належать одному й тому ж застосунку. |
| `AADSTS90002: Tenant not found` | Помилка в `MSGRAPH_TENANT_ID`. | Знову скопіюй Directory (tenant) ID з огляду застосунку. |
| `insufficient_claims` під час виклику (не під час отримання токену) | Токен отримано, але Graph повертає 401/403. | Пропущено крок 3 з наданням згоди, або додані дозволи без повторного надання згоди. Знову відкрий **API permissions** і натисни **Grant admin consent**. |

## Ротація клієнтського секрету

Секрети Azure мають жорсткий термін дії. Перш ніж він закінчиться:

1. У кроці 2 створи другий клієнтський секрет, не видаляючи перший.
2. Онови `MSGRAPH_CLIENT_SECRET` у `~/.hermes/.env` новим значенням.
3. Перезапусти шлюз, щоб новий секрет підхопився: `hermes gateway restart`.
4. Перевір за допомогою тесту вище.
5. Видали старий секрет у порталі Azure.

## Наступні кроки

Після успішної перевірки облікових даних продовжуй:

- **Налаштування веб‑хука** — розгорни платформу `msgraph_webhook` шлюзу, що приймає сповіщення про зміни Graph.
- **Конфігурація конвеєру** — налаштуй середовище виконання Teams meeting pipeline та CLI оператора.
- **Зовнішня доставка** — підключи резюме до каналу або чату Teams.

Ці сторінки розташовані поруч із PR, які додають відповідне середовище виконання. Налаштування облікових даних — окрема передумова, яку безпечно виконати заздалегідь.