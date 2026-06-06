---
title: "Here.Now — Опублікуй статичні сайти до {slug}"
sidebar_label: "Here.Now"
description: "Публікуй статичні сайти до {slug}"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Here.Now

Публікуй статичні сайти на &#123;slug&#125;.here.now і зберігай приватні файли в хмарних Drives для передачі між агентами.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/productivity/here-now` |
| Path | `optional-skills/productivity/here-now` |
| Version | `1.15.3` |
| Author | here.now |
| License | MIT |
| Platforms | macos, linux |
| Tags | `here.now`, `herenow`, `publish`, `deploy`, `hosting`, `static-site`, `web`, `share`, `URL`, `drive`, `storage` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# here.now

here.now дозволяє агентам публікувати веб‑сайти та зберігати приватні файли в хмарних Drives.

Використовуй here.now для двох завдань:

- **Sites**: публікуй веб‑сайти та файли за `{slug}.here.now`.
- **Drives**: зберігай приватні файли агента в хмарних папках.

## Current docs

**Before answering questions about here.now capabilities, features, or workflows, read the current docs:**

→ **https://here.now/docs**

Читай документацію:

- під час першої взаємодії, пов’язаної з here.now, у розмові
- будь‑коли, коли користувач запитує, як щось зробити
- будь‑коли, коли користувач запитує, що можливе, підтримуване або рекомендоване
- перед тим, як повідомляти користувачу, що функція не підтримується

Теми, які вимагають актуальної документації (не покладайтеся лише на локальний текст навички):

- Drives і їхнє поширення
- кастомні домени
- платежі та обмеження доступу до них
- форкінг
- проксі‑маршрути та змінні сервісу
- хендли та посилання
- ліміти та квоти
- SPA‑маршрутизація
- обробка помилок та їх виправлення
- доступність функцій

**If docs and live API behavior disagree, trust the live API behavior.**

If the docs fetch fails or times out, continue with the local skill and live API/script output. Prefer live API behavior for active operations.

## Requirements

- Required binaries: `curl`, `file`, `jq`
- Optional environment variable: `$HERENOW_API_KEY`
- Optional Drive token variable: `$HERENOW_DRIVE_TOKEN`
- Optional credentials file: `~/.herenow/credentials`
- Skill helper paths:
  - `${HERMES_SKILL_DIR}/scripts/publish.sh` for publishing sites
  - `${HERMES_SKILL_DIR}/scripts/drive.sh` for private Drive storage

## Create a site

```bash
PUBLISH="${HERMES_SKILL_DIR}/scripts/publish.sh"
bash "$PUBLISH" {file-or-dir} --client hermes
```

Виводить живу URL (наприклад `https://bright-canvas-a7k2.here.now/`).

За лаштунками це три кроки: створити/оновити → завантажити файли → завершити. Сайт не стає живим, доки не завершиться фіналізація.

Без API‑ключа створюється **анонімний сайт**, який закінчується через 24 години.
Збережений API‑ключ робить сайт постійним.

**Структура файлів:** Для HTML‑сайтів розмісти `index.html` у корені каталогу, який публікуєш, а не у підкаталозі. Вміст каталогу стає коренем сайту. Наприклад, публікуй `my-site/`, у якому є `my-site/index.html` — не публікуй батьківську папку, що містить `my-site/`.

Можна також публікувати «чисті» файли без HTML. Окремі файли відкриваються у вбудованому переглядачі (зображення, PDF, відео, аудіо). Кілька файлів отримують автоматично згенерований список каталогів з навігацією та галереєю зображень.

## Update an existing site

```bash
PUBLISH="${HERMES_SKILL_DIR}/scripts/publish.sh"
bash "$PUBLISH" {file-or-dir} --slug {slug} --client hermes
```

Скрипт автоматично завантажує `claimToken` з `.herenow/state.json` під час оновлення анонімних сайтів. Щоб перевизначити, передай `--claim-token {token}`.

Аутентифіковані оновлення вимагають збереженого API‑ключа.

## Use a Drive

Використовуй Drive, коли користувач потребує приватного хмарного сховища для файлів агента: документи, контекст, пам’ять, плани, активи, медіа, дослідження, код та інше, що має зберігатися без публікації як веб‑сайт.

Кожен підключений обліковий запис має типовий Drive під назвою `My Drive`.

```bash
DRIVE="${HERMES_SKILL_DIR}/scripts/drive.sh"
bash "$DRIVE" default
bash "$DRIVE" ls "My Drive"
bash "$DRIVE" put "My Drive" notes/today.md --from ./notes/today.md
bash "$DRIVE" cat "My Drive" notes/today.md
bash "$DRIVE" share "My Drive" --perms write --prefix notes/ --ttl 7d
```

Використовуй scoped Drive‑токени для передачі між агентами. Якщо отримано блок `herenow_drive`, використай його `token` як `Authorization: Bearer <token>` проти `api_base`, дотримуйся `pathPrefix`, коли він присутній, і зберігай ETag під час запису. `pathPrefix: null` означає доступ до всього Drive. Якщо навичка доступна, віддавай перевагу `drive.sh`; інакше викликай зазначені API‑операції безпосередньо.

## API key storage

Скрипт `publish.sh` читає API‑ключ у такому порядку (перший збіг виграє):

1. прапорець `--api-key {key}` (лише для CI/скриптів — у інтерактивному режимі уникай)
2. змінна середовища `$HERENOW_API_KEY`
3. файл `~/.herenow/credentials` (рекомендовано для агентів)

Щоб зберегти ключ, запиши його у файл облікових даних:

```bash
mkdir -p ~/.herenow && echo "{API_KEY}" > ~/.herenow/credentials && chmod 600 ~/.herenow/credentials
```

**IMPORTANT**: Після отримання API‑ключа збережи його одразу — виконай команду самостійно. Не проси користувача робити це вручну. Уникай передачі ключа через CLI‑прапорці (наприклад `--api-key`) у інтерактивних сесіях; файл облікових даних — бажаний спосіб зберігання.

Ніколи не коміти файли облікових даних або локального стану (`~/.herenow/credentials`, `.herenow/state.json`) у сховище коду.

## Getting an API key

Щоб перейти від анонімних (24 год) до постійних сайтів:

1. Запитай у користувача його електронну адресу.
2. Запроси одноразовий код входу:

```bash
curl -sS https://here.now/api/auth/agent/request-code \
  -H "content-type: application/json" \
  -d '{"email": "user@example.com"}'
```

3. Скажи користувачу: «Перевірте свою поштову скриньку — там має бути код входу від here.now, скопіюйте його сюди».
4. Перевір код і отримай API‑ключ:

```bash
curl -sS https://here.now/api/auth/agent/verify-code \
  -H "content-type: application/json" \
  -d '{"email":"user@example.com","code":"ABCD-2345"}'
```

5. Збережи отриманий `apiKey` самостійно (не проси користувача робити це):

```bash
mkdir -p ~/.herenow && echo "{API_KEY}" > ~/.herenow/credentials && chmod 600 ~/.herenow/credentials
```

## State file

Після кожного створення чи оновлення сайту скрипт записує `.herenow/state.json` у робочому каталозі:

```json
{
  "publishes": {
    "bright-canvas-a7k2": {
      "siteUrl": "https://bright-canvas-a7k2.here.now/",
      "claimToken": "abc123",
      "claimUrl": "https://here.now/claim?slug=bright-canvas-a7k2&token=abc123",
      "expiresAt": "2026-02-18T01:00:00.000Z"
    }
  }
}
```

Перед створенням або оновленням сайтів можеш переглянути цей файл, щоб знайти попередні slug‑и. Сприймай `.herenow/state.json` лише як внутрішній кеш. Не показуй цей локальний шлях як URL і не використовуйте його як джерело правди щодо режиму автентифікації, терміну дії чи claim‑URL.

## What to tell the user

Для опублікованих сайтів:

- Завжди ділись `siteUrl`, отриманим під час поточного запуску скрипту.
- Читай і дотримуйся рядків `publish_result.*` зі stderr, щоб визначити режим автентифікації.
- Якщо `publish_result.auth_mode=authenticated`: повідом користувачу, що сайт **постійний** і збережений у його обліковому записі. Claim‑URL не потрібен.
- Якщо `publish_result.auth_mode=anonymous`: повідом, що сайт **закінчується через 24 години**. Поділись claim‑URL (якщо `publish_result.claim_url` не порожній і починається з `https://`), щоб користувач міг зберегти його назавжди. Попереджай, що claim‑токени повертаються лише один раз і їх не можна відновити.
- Ніколи не проси користувача переглядати `.herenow/state.json` для claim‑URL або статусу автентифікації.

Для Drives:

- Не називай файли Drive публічними URL.
- Поясни, що вміст Drive приватний, якщо його не поділено scoped‑токеном.
- При передачі доступу іншому агенту віддавай перевагу scoped‑токену з вузьким `pathPrefix` і коротким TTL.

## publish.sh options

| Flag                   | Description                                  |
| ---------------------- | -------------------------------------------- |
| `--slug {slug}`        | Оновити існуючий сайт замість створення       |
| `--claim-token {token}`| Перевизначити claim‑токен для анонімних оновлень |
| `--title {text}`       | Заголовок переглядача (для не‑HTML сайтів)   |
| `--description {text}`| Опис переглядача                             |
| `--ttl {seconds}`      | Встановити термін дії (лише для автентифікованих) |
| `--client {name}`      | Ім’я агента для атрибуції (наприклад `hermes`) |
| `--base-url {url}`     | Базовий URL API (за замовчуванням `https://here.now`) |
| `--allow-nonherenow-base-url` | Дозволити надсилати автентифікацію до нестандартного `--base-url` |
| `--api-key {key}`      | Перевизначення API‑ключа (рекомендовано файл облікових даних) |
| `--spa`                | Увімкнути SPA‑маршрутизацію (служити `index.html` для невідомих шляхів) |
| `--forkable`           | Дозволити іншим форкнути цей сайт            |

## Beyond publish.sh

Для операцій з Drive використовуйте `drive.sh` або Drive API. Для розширеного керування обліковим записом і сайтами — видалення, метадані, паролі, платежі, домени, хендли, посилання, змінні, проксі‑маршрути, форкінг, дублювання тощо — дивіться актуальну документацію:

→ **https://here.now/docs**

Full docs: https://here.now/docs