---
title: "Xurl — X/Twitter через xurl CLI: post, search, DM, media, v2 API"
sidebar_label: "Xurl"
description: "X/Twitter через xurl CLI: post, search, DM, media, v2 API"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Xurl

Через CLI `xurl`: публикация, поиск, прямые сообщения (DM), медиа, API v2.
## Метаданные навыка

| | |
|---|---|
| Источник | Встроенный (устанавливается по умолчанию) |
| Путь | `skills/social-media/xurl` |
| Версия | `1.1.1` |
| Автор | xdevplatform + openclaw + Hermes Agent |
| Лицензия | MIT |
| Платформы | linux, macos |
| Теги | `twitter`, `x`, `social-media`, `xurl`, `official-api` |
:::info
Следующее — полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции, когда навык включён.
:::

# xurl — X (Twitter) API через официальную CLI

`xurl` — официальная CLI платформы разработчиков X для X API. Она поддерживает ярлыковые команды для часто используемых действий **и** доступ в стиле raw curl к любому эндпоинту v2. Все команды возвращают JSON в stdout.

Используй этот навык для:
- публикации, ответа, цитирования, удаления постов
- поиска постов и чтения лент/упоминаний
- лайков, репостов, добавления в закладки
- подписки, отписки, блокировки, отключения уведомлений
- прямых сообщений
- загрузки медиа (изображения и видео)
- raw‑доступа к любому эндпоинту X API v2
- многоприложных / мультиаккаунтных рабочих процессов

Этот навык заменяет более старый навык `xitter` (который обёртывал стороннюю Python‑CLI). `xurl` поддерживается командой платформы разработчиков X, использует OAuth 2.0 PKCE с автообновлением и покрывает существенно более широкую поверхность API.

---
## Secret Safety (MANDATORY)

Критические правила при работе внутри сессии агента/LLM:

- **Никогда** не читай, не выводи, не разбирай, не суммируй, не загружай и не отправляй `~/.xurl` в контекст LLM.
- **Никогда** не проси пользователя вставлять учётные данные/токены в чат.
- Пользователь должен заполнять `~/.xurl` секретами вручную на своей машине. В Docker это должен быть `~`, видимый подпроцессам Hermes tool; см. примечание о Docker ниже.
- **Никогда** не рекомендовать и не выполнять команды аутентификации с встроенными секретами в сессиях агента.
- **Никогда** не использовать `--verbose` / `-v` в сессиях агента — это может раскрыть заголовки аутентификации/токены.
- Чтобы проверить наличие учётных данных, используйте только: `xurl auth status`.

Запрещённые флаги в командах агента (они принимают встроенные секреты):
`--bearer-token`, `--consumer-key`, `--consumer-secret`, `--access-token`, `--token-secret`, `--client-id`, `--client-secret`

Регистрация учётных данных приложения и их ротация должны выполняться пользователем вручную, вне сессии агента. После регистрации учётных данных пользователь аутентифицируется с помощью `xurl auth oauth2` — также вне сессии агента. Токены сохраняются в `~/.xurl` в формате YAML. У каждого приложения изолированные токены. Токены OAuth 2.0 автоматически обновляются.
## Установка

Выбери ОДИН метод. На Linux скрипт оболочки или `go install` — самый простой.

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

Проверь:

```bash
xurl --help
xurl auth status
```

Если `xurl` установлен, но `auth status` не показывает приложений или токенов, пользователю необходимо вручную завершить аутентификацию — см. следующий раздел.

---
## Одноразовая настройка пользователя (пользователь выполняет эти команды вне агента)

Эти шаги должен выполнить пользователь напрямую, НЕ агент, потому что они требуют вставки секретов. Направляй пользователя к этому блоку; не выполняй их за него.

1. Создай или открой приложение на https://developer.x.com/en/portal/dashboard
2. Установи redirect URI в `http://localhost:8080/callback`
3. Скопируй **Client ID** и **Client Secret** приложения
4. Зарегистрируй приложение локально (пользователь запускает это):
   ```bash
   xurl auth apps add my-app --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
   ```
5. Пройди аутентификацию (укажи `--app`, чтобы привязать токен к твоему приложению):
   ```bash
   xurl auth oauth2 --app my-app
   ```
   (Откроется браузер для OAuth 2.0 PKCE‑потока.)

   Если X возвращает ошибку `UsernameNotFound` или 403 при запросе `/2/users/me` после OAuth, укажи свой **handle** явно (xurl v1.1.0+):
   ```bash
   xurl auth oauth2 --app my-app YOUR_USERNAME
   ```
   Это привязывает токен к твоему **handle** и пропускает сломанный вызов `/2/users/me`.
6. Установи приложение как приложение по умолчанию, чтобы все команды использовали его:
   ```bash
   xurl auth default my-app
   ```
7. Проверь:
   ```bash
   xurl auth status
   xurl whoami
   ```

После этого агент может использовать любые команды ниже без дополнительной настройки. Токены OAuth 2.0 автоматически обновляются.

> **Распространённая ошибка:** Если ты пропустишь `--app my-app` в `xurl auth oauth2`, OAuth‑токен будет сохранён во встроенный профиль `default`, у которого нет **client-id** и **client-secret**. Команды будут падать с ошибками аутентификации, хотя OAuth‑поток, казалось, завершился успешно. Если это случилось, повторно запусти `xurl auth oauth2 --app my-app` и `xurl auth default my-app`.

> **Проблема с HOME в Docker:** В официальном образе Hermes Docker каталог `/opt/data` является `HERMES_HOME`, но подпроцессы Hermes‑инструментов используют `/opt/data/home` как `HOME`. Это значит, что `~/.xurl` разрешается в `/opt/data/home/.xurl` для команд `xurl`, запущенных через Hermes, а не в `/opt/data/.xurl`. Выполняй пользовательскую настройку с тем же `HOME`:
> ```bash
> HOME=/opt/data/home xurl auth apps add my-app --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
> HOME=/opt/data/home xurl auth oauth2 --app my-app YOUR_USERNAME
> HOME=/opt/data/home xurl auth default my-app YOUR_USERNAME
> HOME=/opt/data/home xurl auth status
> ```
> Если `HOME=/opt/data xurl auth status` проходит успешно, а `HOME=/opt/data/home xurl auth status` не показывает приложений или токенов, вызовы Hermes‑инструментов не увидят учётные данные.
## Быстрая справка

| Действие | Команда |
| --- | --- |
| Создать пост | `xurl post "Hello world!"` |
| Ответить | `xurl reply POST_ID "Nice post!"` |
| Цитировать | `xurl quote POST_ID "My take"` |
| Удалить пост | `xurl delete POST_ID` |
| Прочитать пост | `xurl read POST_ID` |
| Поиск постов | `xurl search "QUERY" -n 10` |
| Кто я | `xurl whoami` |
| Найти пользователя | `xurl user @handle` |
| Лента «домой» | `xurl timeline -n 20` |
| Упоминания | `xurl mentions -n 10` |
| Поставить/снять лайк | `xurl like POST_ID` / `xurl unlike POST_ID` |
| Репост/отменить репост | `xurl repost POST_ID` / `xurl unrepost POST_ID` |
| Добавить/удалить закладку | `xurl bookmark POST_ID` / `xurl unbookmark POST_ID` |
| Список закладок/лайков | `xurl bookmarks -n 10` / `xurl likes -n 10` |
| Подписаться/отписаться | `xurl follow @handle` / `xurl unfollow @handle` |
| Подписки/подписчики | `xurl following -n 20` / `xurl followers -n 20` |
| Заблокировать/разблокировать | `xurl block @handle` / `xurl unblock @handle` |
| Отключить/включить звук | `xurl mute @handle` / `xurl unmute @handle` |
| Отправить ЛС | `xurl dm @handle "message"` |
| Список ЛС | `xurl dms -n 10` |
| Загрузить медиа | `xurl media upload path/to/file.mp4` |
| Статус медиа | `xurl media status MEDIA_ID` |
| Список приложений | `xurl auth apps list` |
| Удалить приложение | `xurl auth apps remove NAME` |
| Установить приложение по умолчанию | `xurl auth default APP_NAME [USERNAME]` |
| Приложение для отдельного запроса | `xurl --app NAME /2/users/me` |
| Статус аутентификации | `xurl auth status` |

**Примечания**
- `POST_ID` принимает как чистый идентификатор, так и полные URL (например, `https://x.com/user/status/1234567890`) — `xurl` извлекает идентификатор.
- Имена пользователей работают как с ведущим `@`, так и без него.
## Подробности команды

### Публикация

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

### Чтение и поиск

```bash
xurl read 1234567890
xurl read https://x.com/user/status/1234567890

xurl search "golang"
xurl search "from:elonmusk" -n 20
xurl search "#buildinpublic lang:en" -n 15
```

### Пользователи, лента, упоминания

```bash
xurl whoami
xurl user elonmusk
xurl user @XDevelopers

xurl timeline -n 25
xurl mentions -n 20
```

### Вовлечённость

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

### Социальный граф

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

### Прямые сообщения

```bash
xurl dm @someuser "Hey, saw your post!"
xurl dms -n 25
```

### Загрузка медиа‑файлов

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
## Прямой доступ к API

Ярлыки охватывают распространённые операции. Для остальных случаев используй режим raw curl‑style против любого эндпоинта X API v2:

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
## Глобальные флаги

| Флаг | Краткое | Описание |
| --- | --- | --- |
| `--app` |  | Использовать конкретное зарегистрированное приложение (перезаписывает значение по умолчанию) |
| `--auth` |  | Принудительно задать тип аутентификации: `oauth1`, `oauth2` или `app` |
| `--username` | `-u` | Какой аккаунт OAuth2 использовать (если их несколько) |
| `--verbose` | `-v` | **Запрещено в сессиях агента** — утечка заголовков аутентификации |
| `--trace` | `-t` | Добавить заголовок трассировки `X-B3-Flags: 1` |
## Потоковая передача

Конечные точки потоковой передачи автоматически обнаруживаются. Известные:

- `/2/tweets/search/stream`
- `/2/tweets/sample/stream`
- `/2/tweets/sample10/stream`

Принудительно включить потоковую передачу для любой конечной точки с помощью `-s`.

---
## Формат вывода

Все команды выводят JSON в `stdout`. Структура соответствует структуре X API v2:

```json
{ "data": { "id": "1234567890", "text": "Hello world!" } }
```

Ошибки также выводятся в формате JSON:

```json
{ "errors": [ { "message": "Not authorized", "code": 403 } ] }
```

---
## Общие рабочие процессы

### Создать пост с изображением
```bash
xurl media upload photo.jpg
xurl post "Check out this photo!" --media-id MEDIA_ID
```

### Ответить в разговоре
```bash
xurl read https://x.com/user/status/1234567890
xurl reply 1234567890 "Here are my thoughts..."
```

### Поиск и взаимодействие
```bash
xurl search "topic of interest" -n 10
xurl like POST_ID_FROM_RESULTS
xurl reply POST_ID_FROM_RESULTS "Great point!"
```

### Проверить свою активность
```bash
xurl whoami
xurl mentions -n 20
xurl timeline -n 20
```

### Несколько приложений (учётные данные настроены вручную)
```bash
xurl auth default prod alice               # prod app, alice user
xurl --app staging /2/users/me             # one-off against staging
```

---
## Обработка ошибок

- Ненулевой код выхода при любой ошибке.
- Ошибки API по‑прежнему выводятся в виде JSON в `stdout`, поэтому их можно разбирать.
- Ошибки аутентификации → попроси пользователя повторно выполнить `xurl auth oauth2` вне сессии агента.
- Команды, которым требуется ID пользователя вызывающего (например, `like`, `repost`, `bookmark`, `follow` и т.п.), автоматически получают его через `/2/users/me`. Ошибка аутентификации в этом запросе будет отображена как ошибка аутентификации.
## Рабочий процесс агента

1. Проверь предварительные условия: `xurl --help` и `xurl auth status`.
2. **Проверь, есть ли у приложения по умолчанию учётные данные.** Разбери вывод `auth status`. Приложение по умолчанию отмечено `▸`. Если у него отображается `oauth2: (none)`, но у другого приложения есть действительный пользователь oauth2, сообщи пользователю выполнить `xurl auth default <that-app>` для исправления. Это самая распространённая ошибка настройки — пользователь добавил приложение с пользовательским именем, но никогда не сделал его приложением по умолчанию, поэтому xurl продолжает использовать пустой профиль `default`.
3. Если аутентификация полностью отсутствует, остановись и направь пользователя в раздел «One-Time User Setup» — НЕ пытайся регистрировать приложения или передавать секреты самостоятельно.
4. Начни с дешёвого чтения (`xurl whoami`, `xurl user @handle`, `xurl search … -n 3`), чтобы подтвердить доступность.
5. Подтверди целевой пост/пользователя и намерения пользователя перед любой записью (пост, ответ, лайк, репост, DM, подписка, блокировка, удаление).
6. Используй вывод в формате JSON напрямую — каждый ответ уже структурирован.
7. Никогда не вставляй содержимое `~/.xurl` обратно в разговор.
## Устранение неполадок

| Симптом | Причина | Решение |
| --- | --- | --- |
| Ошибки аутентификации после успешного OAuth‑потока | Токен сохранён в приложении `default` (без client-id/secret) вместо твоего именованного приложения | `xurl auth oauth2 --app my-app` → `xurl auth default my-app` |
| `unauthorized_client` во время OAuth | Тип приложения в X‑дашборде установлен как **Native App** | Перейди в **User Authentication Settings** и измени тип на **Web app, automated app or bot** |
| `UsernameNotFound` или 403 на `/2/users/me` сразу после OAuth | X ненадёжно возвращает имя пользователя из `/2/users/me` | Выполни `xurl auth oauth2 --app my-app YOUR_USERNAME` (xurl v1.1.0+) и явно укажи handle |
| 401 на каждом запросе | Токен просрочен или выбран неверный app по умолчанию | Проверь `xurl auth status` — убедись, что `▸` указывает на приложение с oauth2‑токенами |
| `client-forbidden` / `client-not-enrolled` | Проблема с регистрацией в X‑платформе | Dashboard → Apps → Manage → Перемести в пакет **Pay-per-use** → Production environment |
| `CreditsDepleted` | Баланс $0 в X API | Купи кредиты (мин. $5) в **Developer Console** → **Billing** |
| `media processing failed` при загрузке изображения | Категория по умолчанию — `amplify_video` | Добавь `--category tweet_image --media-type image/png` |
| Два значения «Client Secret» в X‑дашборде | Ошибка UI — первое значение на самом деле **Client ID** | Проверь на странице **Keys and tokens**; ID заканчивается на `MTpjaQ` |
## Примечания

- **Ограничения скорости:** X применяет ограничения скорости на каждый эндпоинт. Код 429 означает «подожди и попробуй снова». У эндпоинтов записи (post, reply, like, repost) ограничения строже, чем у эндпоинтов чтения.
- **Области доступа:** Токены OAuth 2.0 используют широкие области доступа. Ошибка 403 при выполнении конкретного действия обычно означает, что токену не хватает нужной области — попроси пользователя повторно выполнить `xurl auth oauth2`.
- **Обновление токена:** Токены OAuth 2.0 автоматически обновляются. Делать ничего не нужно.
- **Несколько приложений:** У каждого приложения свои изолированные учётные данные/токены. Переключайся с помощью `xurl auth default` или `--app`.
- **Несколько учётных записей на приложение:** Выбирай с помощью `-u / --username`, либо установи значение по умолчанию через `xurl auth default APP USER`.
- **Хранение токенов:** `~/.xurl` — файл в формате YAML. В Docker используй домашний каталог подпроцесса Hermes (`/opt/data/home` в официальном образе), чтобы токены сохранялись в `/opt/data/home/.xurl`. Никогда не читай и не отправляй этот файл в контекст LLM.
- **Стоимость:** Доступ к API X обычно платный за значительное использование. Большинство ошибок связаны с планом/правами доступа, а не с кодом.
## Атрибуция

- Upstream CLI: https://github.com/xdevplatform/xurl (X developer platform team, Chris Park et al.)
- Upstream agent skill: https://github.com/openclaw/openclaw/blob/main/skills/xurl/SKILL.md
- Hermes adaptation: переформатировано в соответствии с конвенциями навыков Hermes; меры безопасности сохранены дословно.