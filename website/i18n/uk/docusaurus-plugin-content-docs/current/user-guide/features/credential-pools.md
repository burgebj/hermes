---
title: пули облікових даних
description: Об’єднуй кілька API‑ключів або OAuth‑токенів на кожного provider для автоматичної ротації та відновлення після обмеження швидкості.
sidebar_label: Credential Pools
sidebar_position: 9
---

# Пули облікових даних

Пули облікових даних дозволяють реєструвати кілька API‑ключів або OAuth‑токенів для одного й того ж провайдера. Коли один ключ досягає ліміту запитів або квоти, Hermes автоматично переключається на наступний здоровий ключ — підтримуючи вашу **сесію** активною без зміни провайдера.

Це відрізняється від [запасних провайдерів](./fallback-providers.md), які переключаються на *інший* провайдер повністю. Пули облікових даних — це ротація в межах одного провайдера; запасні провайдери — це відмовостійкість між провайдерами. Спочатку перевіряються пули — якщо всі ключі в пулі вичерпані, *тоді* активується запасний провайдер.

:::tip
Пули облікових даних в основному призначені для провайдерів, що працюють за API‑ключами (OpenRouter, Anthropic). Одиний OAuth у [Nous Portal](/integrations/nous-portal) охоплює 300+ моделей, тому більшості користувачів пул не потрібен, коли вони працюють через Portal.
:::

## Як це працює

```
Your request
  → Pick key from pool (round_robin / least_used / fill_first / random)
  → Send to provider
  → 429 rate limit?
      → Plan/usage limit reached (e.g. ChatGPT/Codex "usage limit reached")?
          → Rotate to next pool key immediately (no retry — the cap won't clear on retry)
      → Generic / transient 429?
          → Retry same key once (transient blip)
          → Second 429 → rotate to next pool key
      → All keys exhausted → fallback_model (different provider)
  → 402 billing error?
      → Immediately rotate to next pool key (24h cooldown)
  → 401 auth expired?
      → Try refreshing the token (OAuth)
      → Refresh failed → rotate to next pool key
  → Success → continue normally
```

## Швидкий старт

Якщо у тебе вже є API‑ключ у файлі `.env`, Hermes автоматично виявляє його як пул з 1 ключа. Щоб скористатися перевагами пулу, додай ще кілька ключів:

```bash
# Add a second OpenRouter key
hermes auth add openrouter --api-key sk-or-v1-your-second-key

# Add a second Anthropic key
hermes auth add anthropic --type api-key --api-key sk-ant-api03-your-second-key

# Add an Anthropic OAuth credential (requires Claude Max plan + extra usage credits)
hermes auth add anthropic --type oauth
# Opens browser for OAuth login
```

Перевір свої пули:

```bash
hermes auth list
```

Вивід:
```
openrouter (2 credentials):
  #1  OPENROUTER_API_KEY   api_key env:OPENROUTER_API_KEY ←
  #2  backup-key           api_key manual

anthropic (3 credentials):
  #1  hermes_pkce          oauth   hermes_pkce ←
  #2  claude_code          oauth   claude_code
  #3  ANTHROPIC_API_KEY    api_key env:ANTHROPIC_API_KEY
```

Стрілка `←` позначає поточно обраний обліковий запис.

## Інтерактивне керування

Запусти `hermes auth` без підкоманди, щоб відкрити інтерактивний майстер:

```bash
hermes auth
```

Він показує повний статус пулу та пропонує меню:

```
What would you like to do?
  1. Add a credential
  2. Remove a credential
  3. Reset cooldowns for a provider
  4. Set rotation strategy for a provider
  5. Exit
```

Для провайдерів, які підтримують і API‑ключі, і OAuth (Anthropic, Nous, Codex), процес додавання запитує тип:

```
anthropic supports both API keys and OAuth login.
  1. API key (paste a key from the provider dashboard)
  2. OAuth login (authenticate via browser)
Type [1/2]:
```

## Команди CLI

| Команда | Опис |
|---------|------|
| `hermes auth` | Інтерактивний майстер керування пулом |
| `hermes auth list` | Показати всі пули та облікові дані |
| `hermes auth list <provider>` | Показати пул конкретного провайдера |
| `hermes auth add <provider>` | Додати обліковий запис (запит типу та ключа) |
| `hermes auth add <provider> --type api-key --api-key <key>` | Додати API‑ключ без інтерактиву |
| `hermes auth add <provider> --type oauth` | Додати OAuth‑обліковий запис через вхід у браузері |
| `hermes auth remove <provider> <index>` | Видалити обліковий запис за індексом (починаючи з 1) |
| `hermes auth reset <provider>` | Очистити всі статуси охолодження/вичерпання |

## Стратегії ротації

Налаштуй через `hermes auth` → «Set rotation strategy» або у `config.yaml`:

```yaml
credential_pool_strategies:
  openrouter: round_robin
  anthropic: least_used
```

| Стратегія | Поведінка |
|----------|----------|
| `fill_first` (за замовчуванням) | Використовувати перший здоровий ключ, доки він не вичерпається, потім перейти до наступного |
| `round_robin` | Рівномірно обходити ключі, переключаючись після кожного вибору |
| `least_used` | Завжди вибирати ключ з найменшою кількістю запитів |
| `random` | Випадковий вибір серед здорових ключів |

## Відновлення після помилок

Пул обробляє різні помилки по‑різному:

| Помилка | Поведінка | Охолодження |
|---------|----------|--------------|
| **429 Rate Limit** | Повторити запит тим же ключем один раз (транзитна помилка). Другий послідовний 429 — переключення на наступний ключ | 1 година |
| **402 Billing/Quota** | Негайно переключитися на наступний ключ | 24 години |
| **401 Auth Expired** | Спочатку спробувати оновити OAuth‑токен. Переключитися лише, якщо оновлення не вдається | — |
| **All keys exhausted** | Перейти до `fallback_model`, якщо він налаштований | — |

Прапорець `has_retried_429` скидається після кожного успішного API‑виклику, тому одиничний транзитний 429 не викликає ротації.

## Пули користувацьких кінцевих точок

Користувацькі сумісні з OpenAI кінцеві точки (Together.ai, RunPod, локальні сервери) отримують власні пули, ключовані назвою кінцевої точки з `custom_providers` у `config.yaml`.

Коли ти налаштовуєш користувацьку кінцеву точку через `hermes model`, автоматично генерується назва типу «Together.ai» або «Local (localhost:8080)». Ця назва стає ключем пулу.

```bash
# After setting up a custom endpoint via hermes model:
hermes auth list
# Shows:
#   Together.ai (1 credential):
#     #1  config key    api_key config:Together.ai ←

# Add a second key for the same endpoint:
hermes auth add Together.ai --api-key sk-together-second-key
```

Пули користувацьких кінцевих точок зберігаються у `auth.json` під `credential_pool` з префіксом `custom:`:

```json
{
  "credential_pool": {
    "openrouter": [...],
    "custom:together.ai": [...]
  }
}
```

## Автовиявлення

Hermes автоматично виявляє облікові дані з різних джерел і заповнює пул під час запуску:

| Джерело | Приклад | Автозаповнено? |
|---------|---------|----------------|
| Змінні середовища | `OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY` | Так |
| OAuth‑токени (auth.json) | Codex device code, Nous device code | Так |
| Claude Code credentials | `~/.claude/.credentials.json` | Так (Anthropic) |
| Hermes PKCE OAuth | `~/.hermes/auth.json` | Так (Anthropic) |
| Конфіг користувацької кінцевої точки | `model.api_key` у `config.yaml` | Так (custom endpoints) |
| Ручні записи | Додані через `hermes auth add` | Зберігаються у auth.json |

Автозаповнені записи оновлюються при кожному завантаженні пулу — якщо ти видаляєш змінну середовища, її запис у пулі автоматично видаляється. Ручні записи (додані через `hermes auth add`) ніколи не видаляються автоматично.

Запозичені секрети під час виконання (наприклад, змінні середовища, посилання Bitwarden/Vault/keyring/systemd та користувацькі значення конфігурації) є лише посиланням на межі `auth.json`. Hermes може використати розв’язане значення в пам’яті під час поточного запуску, але зберігає лише метадані: джерело, мітку, статус, лічильники запитів та незворотний відбиток. Ручні записи та стан OAuth/device‑code, яким керує Hermes, зберігають довготривалі токени, необхідні для оновлення.

## Делегування та спільний доступ субагентів

Коли агент створює субагенти через `delegate_task`, пул облікових даних батька автоматично ділиться з дітьми:

- **Той самий провайдер** — дитина отримує повний пул батька, що дозволяє ротацію ключів при лімітах
- **Інший провайдер** — дитина завантажує власний пул цього провайдера (за потреби)
- **Пул не налаштовано** — дитина використовує успадкований одиночний API‑ключ

Тобто субагенти користуються тією ж стійкістю до лімітів, що і батько, без додаткових налаштувань. Оренда облікових даних per‑task гарантує, що діти не конфліктують під час одночасної ротації ключів.

## Безпека потоків

Пул облікових даних використовує блокування потоків для всіх змін стану (`select()`, `mark_exhausted_and_rotate()`, `try_refresh_current()`, `mark_used()`). Це забезпечує безпечний одночасний доступ, коли шлюз обробляє кілька чат‑сесій одночасно.

## Архітектура

Для повної діаграми потоку даних дивіться [`docs/credential-pool-flow.excalidraw`](https://excalidraw.com/#json=2Ycqhqpi6f12E_3ITyiwh,c7u9jSt5BwrmiVzHGbm87g) у репозиторії.

Пул облікових даних інтегрується на рівні розв’язання провайдера:

1. **`agent/credential_pool.py`** — менеджер пулу: зберігання, вибір, ротація, охолодження
2. **`hermes_cli/auth_commands.py`** — команди CLI та інтерактивний майстер
3. **`hermes_cli/runtime_provider.py`** — розв’язання облікових даних з урахуванням пулу
4. **`run_agent.py`** — відновлення після помилок: 429/402/401 → ротація пулу → запасний провайдер

## Зберігання

Стан пулу зберігається у `~/.hermes/auth.json` під ключем `credential_pool`:

```json
{
  "version": 1,
  "credential_pool": {
    "openrouter": [
      {
        "id": "abc123",
        "label": "OPENROUTER_API_KEY",
        "auth_type": "api_key",
        "priority": 0,
        "source": "env:OPENROUTER_API_KEY",
        "secret_source": "bitwarden",
        "secret_fingerprint": "sha256:12ab34cd56ef7890",
        "last_status": "ok",
        "request_count": 142
      }
    ],
    "anthropic": [
      {
        "id": "manual1",
        "label": "personal-api-key",
        "auth_type": "api_key",
        "priority": 0,
        "source": "manual",
        "access_token": "sk-ant-api03-..."
      }
    ]
  }
}
```

Запис OpenRouter вище був запозичений з зовнішнього джерела, тому сирий ключ не зберігається у `auth.json`. Запис Anthropic був навмисно доданий у сховище облікових даних Hermes, тому його токен залишається зберігаємим.

Стратегії зберігаються у `config.yaml` (не в `auth.json`):

```yaml
credential_pool_strategies:
  openrouter: round_robin
  anthropic: least_used
```