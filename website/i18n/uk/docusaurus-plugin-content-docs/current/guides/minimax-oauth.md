---
sidebar_position: 15
title: "MiniMax OAuth"
description: "Увійди в MiniMax через браузер OAuth і використай моделі MiniMax-M2.7 у Hermes Agent — ключ API не потрібен"
---

# MiniMax OAuth

Hermes Agent підтримує **MiniMax** через браузерний OAuth‑вхід, використовуючи ті ж облікові дані, що й [MiniMax portal](https://www.minimax.io). Ключ API чи кредитна картка не потрібні — увійди один раз, і Hermes автоматично оновлює твою сесію.

Транспорт повторно використовує адаптер `anthropic_messages` (MiniMax надає сумісну з Anthropic Messages точку доступу за `/anthropic`), тому всі існуючі функції виклику інструментів, потокової передачі та контексту працюють без змін адаптера.

## Огляд

| Пункт | Значення |
|------|----------|
| Provider ID | `minimax-oauth` |
| Display name | MiniMax (OAuth) |
| Auth type | Browser OAuth (PKCE redirect flow) |
| Transport | Anthropic Messages‑compatible (`anthropic_messages`) |
| Models | `MiniMax-M2.7`, `MiniMax-M2.7-highspeed` |
| Global endpoint | `https://api.minimax.io/anthropic` |
| China endpoint | `https://api.minimaxi.com/anthropic` |
| Requires env var | No (`MINIMAX_API_KEY` **не** використовується для цього провайдера) |

## Передумови

- Python 3.9+
- Hermes Agent встановлений
- Обліковий запис MiniMax на [minimax.io](https://www.minimax.io) (глобальний) або [minimaxi.com](https://www.minimaxi.com) (Китай)
- Браузер, доступний на локальній машині (або використай `--no-browser` для віддалених сесій)

## Швидкий старт

```bash
# Launch the provider and model picker
hermes model
# → Select "MiniMax (OAuth)" from the provider list
# → Hermes opens your browser to the MiniMax authorization page
# → Approve access in the browser
# → Select a model (MiniMax-M2.7 or MiniMax-M2.7-highspeed)
# → Start chatting

hermes
```

Після першого входу облікові дані зберігаються у `~/.hermes/auth.json` і автоматично оновлюються перед кожною сесією.

## Ручний вхід

Ти можеш ініціювати вхід без використання вибору моделі:

```bash
hermes auth add minimax-oauth
```

### Китайський регіон

Якщо твій обліковий запис знаходиться на китайській платформі (`minimaxi.com`), використай провайдера на основі API‑ключа `minimax-cn` — `minimax-cn` зареєстрований лише з `auth_type="api_key"` (без OAuth‑потоку). Налаштуй `MINIMAX_CN_API_KEY` (і за потреби `MINIMAX_CN_BASE_URL`) безпосередньо:

```bash
echo 'MINIMAX_CN_API_KEY=your-key' >> ~/.hermes/.env
```

### Віддалені / безголові сесії

На серверах або в контейнерах, де немає браузера:

```bash
hermes auth add minimax-oauth --no-browser
```

Hermes виведе URL‑перевірки та код користувача — відкрий URL на будь‑якому пристрої та введи код, коли буде запропоновано.

## OAuth‑потік

Hermes реалізує PKCE‑браузерний OAuth‑потік проти кінцевих точок MiniMax OAuth:

1. Hermes генерує пару PKCE‑verifier/challenge та випадкове значення `state`.
2. Він надсилає POST‑запит до `{base_url}/oauth/code` з `challenge` і отримує `user_code` та `verification_uri`.
3. Твій браузер відкриває `verification_uri`. Якщо запитують, введи `user_code`.
4. Hermes опитує `{base_url}/oauth/token`, доки токен не надійде (або не мине термін).
5. Токени (`access_token`, `refresh_token`, expiry) зберігаються у `~/.hermes/auth.json` під ключем `minimax-oauth`.

Оновлення токену (стандартний OAuth‑grant `refresh_token`) виконується автоматично при кожному запуску сесії, коли `access_token` залишився менше 60 секунд до закінчення терміну дії.

## Перевірка стану входу

```bash
hermes doctor
```

У розділі `◆ Auth Providers` буде показано:

```
✓ MiniMax OAuth  (logged in, region=global)
```

або, якщо не ввійшов:

```
⚠ MiniMax OAuth  (not logged in)
```

## Перемикання моделей

```bash
hermes model
# → Select "MiniMax (OAuth)"
# → Pick from the model list
```

Або встанови модель безпосередньо:

```bash
hermes config set model.default MiniMax-M2.7
hermes config set model.provider minimax-oauth
```

## Довідка з налаштувань

Після входу у `~/.hermes/config.yaml` будуть записані подібні записи:

```yaml
model:
  default: MiniMax-M2.7
  provider: minimax-oauth
  base_url: https://api.minimax.io/anthropic
```

### Кінцеві точки регіонів

| Provider id | Портал | Точка інференсу |
|-------------|--------|-----------------|
| `minimax-oauth` (global) | `https://api.minimax.io` | `https://api.minimax.io/anthropic` |
| `minimax-cn` (China) | `https://api.minimaxi.com` | `https://api.minimaxi.com/anthropic` |

### Псевдоніми провайдера

Усі нижченаведені імена резольвються в `minimax-oauth`:

```bash
hermes --provider minimax-oauth    # canonical
hermes --provider minimax-portal   # alias
hermes --provider minimax-global   # alias
hermes --provider minimax_oauth    # alias (underscore form)
```

## Змінні середовища

Провайдер `minimax-oauth` **не** використовує `MINIMAX_API_KEY` або `MINIMAX_BASE_URL`. Ці змінні призначені лише для провайдерів `minimax` та `minimax-cn`, які працюють за API‑ключем.

| Змінна | Ефект |
|--------|-------|
| `MINIMAX_API_KEY` | Використовується лише провайдером `minimax` — ігнорується для `minimax-oauth` |
| `MINIMAX_CN_API_KEY` | Використовується лише провайдером `minimax-cn` — ігнорується для `minimax-oauth` |

Щоб використовувати `minimax-oauth` як активний провайдер, встанови `model.provider: minimax-oauth` у `config.yaml` (використай `hermes setup` для покрокового налаштування) або передай `--provider minimax-oauth` для однократного виклику:

```bash
hermes --provider minimax-oauth
```

## Моделі

| Модель | Найкраще підходить для |
|--------|------------------------|
| `MiniMax-M2.7` | Довгоконтекстне мислення, складний виклик інструментів |
| `MiniMax-M2.7-highspeed` | Нижча затримка, легкі завдання, допоміжні виклики |

Обидві моделі підтримують до 200 000 токенів контексту.

`MiniMax-M2.7-highspeed` також використовується автоматично як допоміжна модель для візуальних та делегувальних завдань, коли `minimax-oauth` є основним провайдером.

## Усунення проблем

### Токен прострочений — автоматичний повторний вхід не спрацьовує

Hermes оновлює токен при кожному запуску сесії, якщо залишилось менше 60 секунд до закінчення терміну. Якщо `access_token` вже прострочений (наприклад, після тривалого офлайн‑періоду), оновлення відбувається автоматично під час наступного запиту. Якщо оновлення завершується помилкою `refresh_token_reused` або `invalid_grant`, Hermes позначає сесію як потребуючу повторного входу.

Коли помилка оновлення є фатальною (HTTP 4xx, `invalid_grant`, відкликаний грант тощо), Hermes позначає `refresh_token` як «мертвий» і карантинує його локально, щоб він більше не повторював невдалий обмін. Агент виводить єдине повідомлення «потрібна повторна автентифікація» і не заважає, доки ти не ввійдеш знову.

**Виправлення:** запусти `hermes auth add minimax-oauth` ще раз, щоб розпочати новий вхід. Карантин знімається після успішного обміну.

### Час очікування авторизації вичерпано

У device‑code потоку є обмежений час дії. Якщо ти не підтвердив вхід вчасно, Hermes піднімає помилку тайм‑ауту.

**Виправлення:** повторно запусти `hermes auth add minimax-oauth` (або `hermes model`). Потік стартує заново.

### Невідповідність стану (можливий CSRF)

Hermes виявив, що значення `state`, повернуте сервером авторизації, не збігається з тим, що було відправлено.

**Виправлення:** повторно пройди вхід. Якщо проблема зберігається, перевір проксі або перенаправлення, які можуть змінювати відповідь OAuth.

### Вхід з віддаленого сервера

Якщо `hermes` не може відкрити вікно браузера, використай `--no-browser`:

```bash
hermes auth add minimax-oauth --no-browser
```

Hermes виводить URL та код. Відкрий URL на будь‑якому пристрої та заверши процес там.

### Помилка «Not logged into MiniMax OAuth» під час виконання

У сховищі автентифікації немає облікових даних для `minimax-oauth`. Ти ще не ввійшов, або файл облікових даних був видалений.

**Виправлення:** запусти `hermes model` і вибери MiniMax (OAuth), або виконай `hermes auth add minimax-oauth`.

## Вихід з облікового запису

Щоб видалити збережені облікові дані MiniMax OAuth:

```bash
hermes auth remove minimax-oauth
```

## Дивись також

- [AI Providers reference](../integrations/providers.md)
- [Environment Variables](../reference/environment-variables.md)
- [Configuration](../user-guide/configuration.md)
- [hermes doctor](../reference/cli-commands.md)