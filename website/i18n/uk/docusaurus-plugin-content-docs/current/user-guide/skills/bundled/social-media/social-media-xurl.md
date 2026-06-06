---
title: "Xurl — X/Twitter через xurl CLI: post, search, DM, media, v2 API"
sidebar_label: "Xurl"
description: "X/Twitter через xurl CLI: пост, пошук, DM, медіа, v2 API"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Xurl

X/Twitter за допомогою xurl CLI: post, search, DM, media, v2 API.
## Метадані навички

| | |
|---|---|
| Джерело | Вбудовано (встановлено за замовчуванням) |
| Шлях | `skills/social-media/xurl` |
| Версія | `1.1.1` |
| Автор | xdevplatform + openclaw + Hermes Agent |
| Ліцензія | MIT |
| Платформи | linux, macos |
| Теги | `twitter`, `x`, `social-media`, `xurl`, `official-api` |
:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це інструкції, які бачить агент під час роботи навички.
:::

# xurl — X (Twitter) API через офіційний CLI

`xurl` — офіційний CLI платформи розробників X для X API. Він підтримує скорочені команди для типових дій **та** доступ у стилі `curl` до будь‑якого кінцевого пункту v2. Усі команди повертають JSON у stdout.

Використовуй цю навичку для:
- публікації, відповіді, цитування, видалення дописів
- пошуку дописів та читання стрічок/згадок
- лайків, репостів, закладок
- підписки, відписки, блокування, вимкнення сповіщень
- прямих повідомлень
- завантаження медіа (зображень та відео)
- прямого доступу до будь‑якого кінцевого пункту X API v2
- робочих процесів з кількома додатками / кількома обліковими записами

Ця навичка замінює старішу навичку `xitter` (яка обгортала сторонній Python CLI). `xurl` підтримується командою платформи розробників X, підтримує OAuth 2.0 PKCE з автоматичним оновленням токену та охоплює значно ширший набір API.

---
## Secret Safety (MANDATORY)

Критичні правила під час роботи всередині **agent/LLM сесії**:

- **Ніколи** не читай, не виводь, не аналізуй, не підсумовуй, не завантажуй і не надсилай `~/.xurl` у контекст LLM.
- **Ніколи** не проси користувача вставляти облікові дані/токени в чат.
- Користувач повинен самостійно заповнити `~/.xurl` секретами на своїй машині. У Docker це має бути `~`, який бачать підпроцеси Hermes tool; дивись примітку про Docker нижче.
- **Ніколи** не рекомендуй і не виконуй команди автентифікації з вбудованими секретами в agent сесіях.
- **Ніколи** не використовуйте `--verbose` / `-v` в agent сесіях — це може розкрити заголовки/токени автентифікації.
- Щоб перевірити наявність облікових даних, використовуйте лише: `xurl auth status`.

**Заборонені прапорці** в командах agent (вони приймають вбудовані секрети):
`--bearer-token`, `--consumer-key`, `--consumer-secret`, `--access-token`, `--token-secret`, `--client-id`, `--client-secret`

Реєстрація облікових даних додатка та їх ротація мають виконуватись користувачем вручну, поза межами agent сесії. Після реєстрації облікових даних користувач автентифікується за допомогою `xurl auth oauth2` — також поза межами agent сесії. Токени зберігаються у `~/.xurl` у форматі YAML. Кожен додаток має ізольовані токени. Токени OAuth 2.0 автоматично оновлюються.

---
## Встановлення

Вибери ОДИН метод. На Linux найпростіші — shell‑скрипт або `go install`.

```bash
# Shell script (installs to ~/.local/bin, no sudo, works on Linux + macOS)
curl -fsSL https://raw.githubusercontent.com/xdevplatform/xurl/main/install.sh | bash

# Homebrew (macOS)
brew install --cask xdevplatform/tap/xurl

# npm
npm install -g @xdevplatform/xurl

# Go
go install github.com/xdevplatform/xurl@latest
```

Перевірка:

```bash
xurl --help
xurl auth status
```

Якщо `xurl` встановлено, але `auth status` не показує жодних додатків або токенів, користувачеві потрібно завершити автентифікацію вручну — дивись наступний розділ.

---
## Одноразове налаштування користувача (користувач виконує це поза агентом)

Ці кроки має виконати користувач безпосередньо, **НЕ** агент, оскільки вони передбачають вставлення секретів. Перенаправ користувача до цього блоку; не виконуй їх за нього.

1. Створи або відкрий додаток за адресою https://developer.x.com/en/portal/dashboard
2. Встанови **redirect URI** на `http://localhost:8080/callback`
3. Скопіюй **Client ID** та **Client Secret** додатку
4. Зареєструй додаток локально (користувач виконує це):
      ```bash
   xurl auth apps add my-app --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
   ```
5. Авторизуйся (вкажи `--app`, щоб прив’язати токен до твого додатку):
      ```bash
   xurl auth oauth2 --app my-app
   ```
   (Це відкриє браузер для потоку OAuth 2.0 PKCE.)

   Якщо X повертає помилку `UsernameNotFound` або 403 під час запиту `/2/users/me` після OAuth, передай свій **handle** явно (xurl v1.1.0+):
      ```bash
   xurl auth oauth2 --app my-app YOUR_USERNAME
   ```
   Це прив’язує токен до твого **handle** і пропускає поламаний виклик `/2/users/me`.
6. Встанови додаток як типовий, щоб усі команди його використовували:
      ```bash
   xurl auth default my-app
   ```
7. Перевір:
      ```bash
   xurl auth status
   xurl whoami
   ```

Після цього агент може використовувати будь‑яку команду нижче без додаткового налаштування. Токени OAuth 2.0 автоматично оновлюються.

> **Поширена помилка:** Якщо пропустити `--app my-app` у `xurl auth oauth2`, OAuth‑токен зберігається у вбудованому профілі `default`, у якому немає **client‑id** або **client‑secret**. Команди завершаться помилками автентифікації, хоча потік OAuth здавався успішним. Якщо це сталося, повторно запусти `xurl auth oauth2 --app my-app` та `xurl auth default my-app`.

> **Помилка Docker HOME:** У офіційному розташуванні Hermes Docker, `/opt/data` є `HERMES_HOME`, але підпроцеси інструменту Hermes використовують `/opt/data/home` як `HOME`. Це означає, що `~/.xurl` розв’язується у `/opt/data/home/.xurl` для команд `xurl`, запущених Hermes, а не у `/opt/data/.xurl`. Запусти налаштування користувача з тим самим `HOME`:
> ```bash
> HOME=/opt/data/home xurl auth apps add my-app --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
> HOME=/opt/data/home xurl auth oauth2 --app my-app YOUR_USERNAME
> HOME=/opt/data/home xurl auth default my-app YOUR_USERNAME
> HOME=/opt/data/home xurl auth status
> ```
> Якщо `HOME=/opt/data xurl auth status` проходить успішно, а `HOME=/opt/data/home xurl auth status` не показує жодних додатків чи токенів, виклики інструменту Hermes не побачать облікові дані.
## Швидка довідка

| Дія | Команда |
| --- | --- |
| Створити пост | `xurl post "Hello world!"` |
| Відповісти | `xurl reply POST_ID "Nice post!"` |
| Цитувати | `xurl quote POST_ID "My take"` |
| Видалити пост | `xurl delete POST_ID` |
| Прочитати пост | `xurl read POST_ID` |
| Пошук постів | `xurl search "QUERY" -n 10` |
| Хто я | `xurl whoami` |
| Пошук користувача | `xurl user @handle` |
| Головна стрічка | `xurl timeline -n 20` |
| Згадки | `xurl mentions -n 10` |
| Лайк / Скасувати лайк | `xurl like POST_ID` / `xurl unlike POST_ID` |
| Репост / Скасувати репост | `xurl repost POST_ID` / `xurl unrepost POST_ID` |
| Закладка / Видалити закладку | `xurl bookmark POST_ID` / `xurl unbookmark POST_ID` |
| Список закладок / лайків | `xurl bookmarks -n 10` / `xurl likes -n 10` |
| Підписатися / Відписатися | `xurl follow @handle` / `xurl unfollow @handle` |
| Підписки / Підписники | `xurl following -n 20` / `xurl followers -n 20` |
| Заблокувати / Розблокувати | `xurl block @handle` / `xurl unblock @handle` |
| Заглушити / Розглушити | `xurl mute @handle` / `xurl unmute @handle` |
| Надіслати DM | `xurl dm @handle "message"` |
| Список DM | `xurl dms -n 10` |
| Завантажити медіа | `xurl media upload path/to/file.mp4` |
| Статус медіа | `xurl media status MEDIA_ID` |
| Список додатків | `xurl auth apps list` |
| Видалити додаток | `xurl auth apps remove NAME` |
| Встановити додаток за замовчуванням | `xurl auth default APP_NAME [USERNAME]` |
| Додаток для конкретного запиту | `xurl --app NAME /2/users/me` |
| Статус автентифікації | `xurl auth status` |

Примітки:
- `POST_ID` приймає повні URL‑адреси (наприклад `https://x.com/user/status/1234567890`) — xurl витягує ID.
- Імена користувачів працюють як з префіксом `@`, так і без нього.
## Деталі команди

### Публікація

```bash
xurl post "Hello world!"
xurl post "Check this out" --media-id MEDIA_ID
xurl post "Thread pics" --media-id 111 --media-id 222

xurl reply 1234567890 "Great point!"
xurl reply https://x.com/user/status/1234567890 "Agreed!"
xurl reply 1234567890 "Look at this" --media-id MEDIA_ID

xurl quote 1234567890 "Adding my thoughts"
xurl delete 1234567890
```

### Читання та пошук

```bash
xurl read 1234567890
xurl read https://x.com/user/status/1234567890

xurl search "golang"
xurl search "from:elonmusk" -n 20
xurl search "#buildinpublic lang:en" -n 15
```

### Користувачі, хронологія, згадки

```bash
xurl whoami
xurl user elonmusk
xurl user @XDevelopers

xurl timeline -n 25
xurl mentions -n 20
```

### Взаємодія

```bash
xurl like 1234567890
xurl unlike 1234567890

xurl repost 1234567890
xurl unrepost 1234567890

xurl bookmark 1234567890
xurl unbookmark 1234567890

xurl bookmarks -n 20
xurl likes -n 20
```

### Соціальний граф

```bash
xurl follow @XDevelopers
xurl unfollow @XDevelopers

xurl following -n 50
xurl followers -n 50

# Another user's graph
xurl following --of elonmusk -n 20
xurl followers --of elonmusk -n 20

xurl block @spammer
xurl unblock @spammer
xurl mute @annoying
xurl unmute @annoying
```

### Прямі повідомлення

```bash
xurl dm @someuser "Hey, saw your post!"
xurl dms -n 25
```

### Завантаження медіа

```bash
# Auto-detect type
xurl media upload photo.jpg
xurl media upload video.mp4

# Explicit type/category
xurl media upload --media-type image/jpeg --category tweet_image photo.jpg

# Videos need server-side processing — check status (or poll)
xurl media status MEDIA_ID
xurl media status --wait MEDIA_ID

# Full workflow
xurl media upload meme.png                  # returns media id
xurl post "lol" --media-id MEDIA_ID
```

---
## Доступ до Raw API

Комбінації клавіш охоплюють поширені операції. Для всього іншого використай режим у стилі `curl` проти будь‑якої кінцевої точки X API v2:

```bash
# GET
xurl /2/users/me

# POST with JSON body
xurl -X POST /2/tweets -d '{"text":"Hello world!"}'

# DELETE / PUT / PATCH
xurl -X DELETE /2/tweets/1234567890

# Custom headers
xurl -H "Content-Type: application/json" /2/some/endpoint

# Force streaming
xurl -s /2/tweets/search/stream

# Full URLs also work
xurl https://api.x.com/2/users/me
```

---
## Глобальні прапорці

| Прапорець | Коротка | Опис |
| --- | --- | --- |
| `--app` |  | Використати конкретний зареєстрований застосунок (перезаписує типове) |
| `--auth` |  | Примусово задати тип автентифікації: `oauth1`, `oauth2` або `app` |
| `--username` | `-u` | Який обліковий запис OAuth2 використовувати (якщо їх кілька) |
| `--verbose` | `-v` | **Заборонено в сесіях агента** — розкриває заголовки автентифікації |
| `--trace` | `-t` | Додати заголовок трасування `X‑B3‑Flags: 1` |

---
## Стрімінг

Кінцеві точки стрімінгу автоматично виявляються. Відомі з них:

- `/2/tweets/search/stream`
- `/2/tweets/sample/stream`
- `/2/tweets/sample10/stream`

Примусово ввімкнути стрімінг для будь‑якої кінцевої точки за допомогою `-s`.

---
## Формат виводу

Усі команди повертають JSON у `stdout`. Структура відповідає X API v2:

```json
{ "data": { "id": "1234567890", "text": "Hello world!" } }
```

Помилки також у форматі JSON:

```json
{ "errors": [ { "message": "Not authorized", "code": 403 } ] }
```

---
## Спільні робочі процеси

### Опублікувати повідомлення з зображенням
```bash
xurl media upload photo.jpg
xurl post "Check out this photo!" --media-id MEDIA_ID
```

### Відповісти в розмові
```bash
xurl read https://x.com/user/status/1234567890
xurl reply 1234567890 "Here are my thoughts..."
```

### Пошук і взаємодія
```bash
xurl search "topic of interest" -n 10
xurl like POST_ID_FROM_RESULTS
xurl reply POST_ID_FROM_RESULTS "Great point!"
```

### Перевір свою активність
```bash
xurl whoami
xurl mentions -n 20
xurl timeline -n 20
```

### Кілька додатків (облікові дані налаштовано вручну)
```bash
xurl auth default prod alice               # prod app, alice user
xurl --app staging /2/users/me             # one-off against staging
```

---
## Обробка помилок

- Ненульовий код завершення при будь‑якій помилці.
- Помилки API все ще виводяться у форматі JSON у `stdout`, тому їх можна парсити.
- Помилки автентифікації → попроси користувача повторно виконати `xurl auth oauth2` поза сесією агента.
- Команди, яким потрібен ID користувача викликувача (наприклад, like, repost, bookmark, follow тощо), автоматично отримують його через `/2/users/me`. Невдача автентифікації в цьому запиті відображається як помилка автентифікації.

---
## Робочий процес агента

1. Перевір передумови: `xurl --help` та `xurl auth status`.
2. **Перевір, чи має типова програма облікові дані.** Проаналізуй вивід `auth status`. Типова програма позначена `▸`. Якщо типова програма показує `oauth2: (none)`, а інша програма має дійсний користувач oauth2, повідом користувачеві запустити `xurl auth default <that-app>`, щоб виправити це. Це найпоширеніша помилка налаштування — користувач додав програму з власною назвою, але ніколи не встановив її як типову, тому `xurl` продовжує використовувати порожній профіль `default`.
3. Якщо автентифікація відсутня взагалі, зупинись і направ користувача до розділу **«One-Time User Setup»** — НЕ намагайся реєструвати програми або передавати секрети самостійно.
4. Почни з недорогої перевірки (`xurl whoami`, `xurl user @handle`, `xurl search … -n 3`), щоб підтвердити доступність.
5. Підтверджуй цільовий пост/користувача та намір користувача перед будь‑якою дією запису (пост, відповідь, лайк, репост, DM, підписка, блокування, видалення).
6. Використовуй безпосередньо JSON‑вивід — кожна відповідь вже структурована.
7. Ніколи не вставляй вміст `~/.xurl` назад у розмову.
## Устранення проблем

| Симптом | Причина | Виправлення |
| --- | --- | --- |
| Помилки автентифікації після успішного OAuth‑потоку | Токен збережено в додатку `default` (без client-id/secret) замість вашого іменованого додатку | `xurl auth oauth2 --app my-app` потім `xurl auth default my-app` |
| `unauthorized_client` під час OAuth | Тип додатку встановлено як **Native App** у X dashboard | Перевести в **Web app, automated app or bot** у налаштуваннях User Authentication Settings |
| `UsernameNotFound` або 403 на `/2/users/me` одразу після OAuth | X не повертає надійно ім'я користувача з `/2/users/me` | Перезапустити `xurl auth oauth2 --app my-app YOUR_USERNAME` (xurl v1.1.0+) і явно передати хендл |
| 401 на кожному запиті | Токен прострочений або вказано неправильний додаток за замовчуванням | Перевірити `xurl auth status` — впевнитися, що `▸` вказує на додаток з oauth2‑токенами |
| `client-forbidden` / `client-not-enrolled` | Проблема реєстрації на платформі X | Dashboard → Apps → Manage → Перемістити до пакету **Pay-per-use** → Середовище **Production** |
| `CreditsDepleted` | Баланс $0 у X API | Придбати кредити (мінімум $5) у Developer Console → Billing |
| `media processing failed` під час завантаження зображення | Типова категорія — `amplify_video` | Додати `--category tweet_image --media-type image/png` |
| Два значення «Client Secret» у X dashboard | Помилка UI — перше фактично **Client ID** | Перевірити на сторінці **Keys and tokens**; ID закінчується на `MTpjaQ` |
## Примітки

- **Обмеження швидкості:** X застосовує обмеження швидкості на рівні кожного кінцевого пункту. 429 означає, що треба зачекати і повторити запит. Записувальні кінцеві точки (post, reply, like, repost) мають суворіші обмеження, ніж читальні.
- **Області:** Токени OAuth 2.0 використовують широкі області. 403 на конкретну дію зазвичай означає, що токену не вистачає потрібної області — попроси користувача повторно виконати `xurl auth oauth2`.
- **Оновлення токену:** Токени OAuth 2.0 автоматично оновлюються. Нічого робити не потрібно.
- **Кілька додатків:** Кожен додаток має ізольовані облікові дані/токени. Перемикайся за допомогою `xurl auth default` або `--app`.
- **Кілька облікових записів на додаток:** Вибирай за допомогою `-u / --username`, або встанови типове значення за допомогою `xurl auth default APP USER`.
- **Зберігання токену:** `~/.xurl` — це YAML. У Docker використовуйте домашню теку підпроцесу Hermes (`/opt/data/home` в офіційному образі), щоб токени потрапляли до `/opt/data/home/.xurl`. Ніколи не читайте і не надсилайте цей файл у контекст LLM.
- **Вартість:** Доступ до API X зазвичай оплачується за змістовне використання. Більшість помилок пов’язані з планом/правами, а не з кодом.
## Атрибуція

- Upstream CLI: https://github.com/xdevplatform/xurl (X developer platform team, Chris Park et al.)
- Upstream agent skill: https://github.com/openclaw/openclaw/blob/main/skills/xurl/SKILL.md
- Адаптація Hermes: переформатовано відповідно до конвенцій навичок Hermes; запобіжні механізми безпеки збережено дослівно.