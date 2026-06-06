# Spotify

Hermes може керувати Spotify безпосередньо — відтворенням, чергою, пошуком, плейлистами, збереженими треками/альбомами та історією прослуховувань — використовуючи офіційний Web API Spotify з PKCE OAuth. Токени зберігаються у `~/.hermes/auth.json` і автоматично оновлюються при отриманні 401; ти входиш лише один раз на цей комп’ютер.

На відміну від вбудованих OAuth‑інтеграцій Hermes (Google, GitHub Copilot, Codex), Spotify вимагає, щоб кожен користувач зареєстрував власний легковаговий додаток‑розробника. Spotify не дозволяє стороннім розробникам розповсюджувати публічний OAuth‑додаток, яким може користуватися будь‑хто. Це займає близько двох хвилин, а `hermes auth spotify` проведе тебе через процес.
## Prerequisites

- Обліковий запис Spotify. **Free** підходить для інструментів пошуку, списків відтворення, бібліотеки та активності. **Premium** потрібен для керування відтворенням (play, pause, skip, seek, volume, queue add, transfer).
- Hermes Agent встановлений і запущений.
- Для інструментів відтворення: **активний пристрій Spotify Connect** — додаток Spotify має бути відкритим хоча б на одному пристрої (телефон, комп’ютер, веб‑плеєр, колонка), щоб Web API мав що керувати. Якщо жоден пристрій не активний, ти отримаєш `403 Forbidden` з повідомленням «no active device»; відкрий Spotify на будь‑якому пристрої та спробуй ще раз.
## Налаштування

### One-shot: `hermes tools` або налаштування під час першого запуску

Найшвидший шлях. Запусти:

```bash
hermes tools
```

Прокрути до `🎵 Spotify`, натисни пробіл, щоб увімкнути, потім `s` — зберегти. Така ж перемикач доступна під час першого запуску `hermes setup` / `hermes setup tools`. Spotify залишається opt‑in, тому його увімкнення виконує ту саму конфігурацію, орієнтовану на провайдера, що й `hermes tools`.

Hermes відразу переводить тебе у OAuth‑потік — якщо у тебе ще немає додатку Spotify, він проведе тебе через створення його вбудовано. Після завершення набір інструментів увімкнено **ТА** автентифіковано за один прохід.

Якщо ти хочеш виконати кроки окремо (або повторно автентифікуєшся пізніше), скористайся двокроковим процесом нижче.

### Двокроковий процес

#### 1. Увімкни набір інструментів

```bash
hermes tools
```

Увімкни `🎵 Spotify`, збережи, і коли відкриється вбудований майстер, закрий його (Ctrl+C). Набір інструментів залишиться увімкненим; лише крок автентифікації відкладено.

#### 2. Запусти майстер входу

```bash
hermes auth spotify
```

7 інструментів Spotify з’являються в наборі інструментів агента лише після кроку 1 — за замовчуванням вони вимкнені, щоб користувачі, які їх не потребують, не передавали зайві схеми інструментів у кожному API‑запиті.

Якщо `HERMES_SPOTIFY_CLIENT_ID` не встановлено, Hermes проведе тебе через реєстрацію додатку вбудовано:

1. Відкриває `https://developer.spotify.com/dashboard` у твоєму браузері
2. Виводить точні значення, які треба вставити у форму **Create app** Spotify
3. Запитує у тебе Client ID, який ти отримав
4. Зберігає його у `~/.hermes/.env`, щоб майбутні запуски пропускали цей крок
5. Переправляє одразу у OAuth‑потік згоди

Після підтвердження токени записуються у `providers.spotify` у `~/.hermes/auth.json`. Активний провайдер інференції **НЕ** змінюється — автентифікація Spotify незалежна від твого провайдера LLM.

### Створення додатку Spotify (що запитує майстер)

Коли відкриється панель, натисни **Create app** і заповни:

| Поле | Значення |
|------|----------|
| App name | будь‑що (наприклад `hermes-agent`) |
| App description | будь‑що (наприклад `personal Hermes integration`) |
| Website | залишити порожнім |
| Redirect URI | `http://127.0.0.1:43827/spotify/callback` |
| Which API/SDKs? | позначити **Web API** |

Погодься з умовами та натисни **Save**. На наступній сторінці вибери **Settings** → скопіюй **Client ID** і встав його у запит Hermes. Це єдине значення, яке потрібне Hermes — PKCE не використовує client secret.

### Запуск через SSH / у безголовому середовищі

Якщо встановлено `SSH_CLIENT` або `SSH_TTY`, Hermes пропускає автоматичне відкриття браузера під час майстра та OAuth‑кроку. Скопіюй URL панелі та URL авторизації, які виводить Hermes, відкрий їх у браузері на локальній машині та продовжуй звичайно — локальний HTTP‑слухач все ще працює на віддаленому хості на порту `43827`. Браузер твого ноутбука не зможе дістатися до віддаленого loopback без SSH‑перенаправлення:

```bash
ssh -N -L 43827:127.0.0.1:43827 user@remote-host
```

Для налаштувань jump‑box / bastion та інших нюансів (mosh, tmux, конфлікти портів) дивись [OAuth over SSH / Remote Hosts](../../guides/oauth-over-ssh.md).
## Перевірка

```bash
hermes auth status spotify
```

Показує, чи присутні токени і коли закінчується термін дії токена доступу. Оновлення виконується автоматично: коли будь‑який виклик Spotify API повертає 401, клієнт обмінює токен оновлення і повторює запит один раз. Токени оновлення зберігаються між перезапуском Hermes, тому тобі потрібно лише повторно авторизуватись, якщо ти відкликав доступ застосунку в налаштуваннях свого облікового запису Spotify або виконав `hermes auth logout spotify`.
## Використання

Після входу агент має доступ до 7 інструментів Spotify. Ти спілкуєшся з агентом природно — він вибирає потрібний інструмент і дію. Для кращої поведінки агент завантажує супутній **skill**, який навчає канонічним шаблонам використання (single-search-then-play, коли не треба попередньо виконувати `get_state` тощо).

```
> play some miles davis
> what am I listening to
> add this track to my Late Night Jazz playlist
> skip to the next song
> make a new playlist called "Focus 2026" and add the last three songs I played
> which of my saved albums are by Radiohead
> search for acoustic covers of Blackbird
> transfer playback to my kitchen speaker
```

### Довідка по інструментах

Усі дії, що змінюють відтворення, приймають необов’язковий `device_id` для вказання конкретного пристрою. Якщо його не вказано, Spotify використовує поточний активний пристрій.

#### `spotify_playback`
Керування та перегляд відтворення, а також отримання історії нещодавно відтворених треків.

| Дія | Призначення | Преміум? |
|--------|---------|----------|
| `get_state` | Повний стан відтворення (трек, пристрій, прогрес, перемішування/повтор) | No |
| `get_currently_playing` | Тільки поточний трек (повертає порожнє при 204 — дивись нижче) | No |
| `play` | Запуск/відновлення відтворення. Необов’язково: `context_uri`, `uris`, `offset`, `position_ms` | Yes |
| `pause` | Пауза відтворення | Yes |
| `next` / `previous` | Перехід до наступного/попереднього треку | Yes |
| `seek` | Перехід до `position_ms` | Yes |
| `set_repeat` | `state` = `track` / `context` / `off` | Yes |
| `set_shuffle` | `state` = `true` / `false` | Yes |
| `set_volume` | `volume_percent` = 0‑100 | Yes |
| `recently_played` | Останні відтворені треки. Необов’язково `limit`, `before`, `after` (Unix ms) | No |

#### `spotify_devices`
| Дія | Призначення |
|--------|---------|
| `list` | Усі пристрої Spotify Connect, видимі в твоєму обліковому записі |
| `transfer` | Перемістити відтворення до `device_id`. Необов’язково `play: true` запускає відтворення під час перенесення |

### Спікери, якими керує Home Assistant

Якщо Home Assistant керує спікерами, які вже підтримують Spotify Connect (наприклад Sonos, Echo, Nest або інші спікери з підтримкою Connect), вони автоматично з’являються в `spotify_devices list`, коли Spotify їх бачить. Hermes не потребує мосту Home Assistant ↔ Spotify для цього шляху — Spotify самостійно маршрутизує пристрої.

Попроси Hermes перенести відтворення за назвою спікера (наприклад, “transfer Spotify to the kitchen speaker”), або виклич `spotify_devices list` і передай точний `device_id` у `spotify_devices transfer` під час скрипту. Якщо спікер відсутній, відкрий додаток Spotify або інтеграцію спікера в Spotify один раз, щоб Spotify зареєстрував його як активну ціль Connect.

#### `spotify_queue`
| Дія | Призначення | Преміум? |
|--------|---------|----------|
| `get` | Поточна черга треків | No |
| `add` | Додати `uri` у кінець черги | Yes |

#### `spotify_search`
Пошук у каталозі. Параметр `query` обов’язковий. Необов’язково: `types` (масив `track` / `album` / `artist` / `playlist` / `show` / `episode`), `limit`, `offset`, `market`.

#### `spotify_playlists`
| Дія | Призначення | Обов’язкові аргументи |
|--------|---------|---------------|
| `list` | Плейлисти користувача | — |
| `get` | Один плейлист + треки | `playlist_id` |
| `create` | Новий плейлист | `name` (+ необов’язково `description`, `public`, `collaborative`) |
| `add_items` | Додати треки | `playlist_id`, `uris` (необов’язково `position`) |
| `remove_items` | Видалити треки | `playlist_id`, `uris` (+ необов’язково `snapshot_id`) |
| `update_details` | Перейменувати / редагувати | `playlist_id` + будь‑які з `name`, `description`, `public`, `collaborative` |

#### `spotify_albums`
| Дія | Призначення | Обов’язкові аргументи |
|--------|---------|---------------|
| `get` | Метадані альбому | `album_id` |
| `tracks` | Список треків альбому | `album_id` |

#### `spotify_library`
Уніфікований доступ до збережених треків і альбомів. Вибирай колекцію за аргументом `kind`.

| Дія | Призначення |
|--------|---------|
| `list` | Пагіноване перелічення бібліотеки |
| `save` | Додати `ids` / `uris` до бібліотеки |
| `remove` | Видалити `ids` / `uris` з бібліотеки |

Обов’язково: `kind` = `tracks` або `albums`, плюс `action`.

### Матриця функцій: Free vs Premium

Інструменти лише для читання працюють у безкоштовних акаунтах. Все, що змінює відтворення або чергу, вимагає Premium.

| Працює у Free | Потрібен Premium |
|---------------|------------------|
| `spotify_search` (всі) | `spotify_playback` — play, pause, next, previous, seek, set_repeat, set_shuffle, set_volume |
| `spotify_playback` — get_state, get_currently_playing, recently_played | `spotify_queue` — add |
| `spotify_devices` — list | `spotify_devices` — transfer |
| `spotify_queue` — get | |
| `spotify_playlists` (всі) | |
| `spotify_albums` (всі) | |
| `spotify_library` (всі) | |
## Планування: Spotify + cron

Оскільки інструменти Spotify є звичайними інструментами Hermes, cron‑завдання, що виконується в сесії Hermes, може запускати відтворення за будь‑яким розкладом. Новий код не потрібен.

### Плейлист для пробудження вранці

```bash
hermes cron add \
  --name "morning-commute" \
  "0 7 * * 1-5" \
  "Transfer playback to my kitchen speaker and start my 'Morning Commute' playlist. Volume to 40. Shuffle on."
```

Що відбувається о 7:00 кожного буднього дня:
1. Cron піднімає безголову сесію Hermes.
2. Агент читає prompt, викликає `spotify_devices list`, щоб знайти «kitchen speaker» за назвою, потім `spotify_devices transfer` → `spotify_playback set_volume` → `spotify_playback set_shuffle` → `spotify_search` + `spotify_playback play`.
3. Музика починає грати на цільовому динаміку. Загальна вартість: одна сесія, кілька викликів інструментів, без людського вводу.

### Відпочинок ввечері

```bash
hermes cron add \
  --name "wind-down" \
  "30 22 * * *" \
  "Pause Spotify. Then set volume to 20 so it's quiet when I start it again tomorrow."
```

### Підводні камені

- **Активний пристрій має існувати, коли спрацьовує cron.** Якщо жоден клієнт Spotify не запущений (телефон/десктоп/Connect‑динамік), дії відтворення повертають `403 no active device`. Для ранкових плейлистів трюк полягає в тому, щоб націлюватися на пристрій, який завжди увімкнений (Sonos, Echo, смарт‑динамік), а не на телефон.
- **Для будь‑яких змін відтворення потрібен Premium** — відтворення, пауза, пропуск, гучність, передача. Cron‑завдання лише для читання (наприклад, «надішли мені електронною поштою мої останні прослухані треки») працюють у безкоштовному режимі.
- **Cron‑агент успадковує твої активні набори інструментів.** Spotify має бути ввімкнено в `hermes tools`, щоб cron‑сесія бачила інструменти Spotify.
- **Cron‑завдання працюють з `skip_memory=True`**, тому вони не записують у твою пам’ять.

Повна довідка по cron: [Cron Jobs](./cron).
## Вихід

```bash
hermes auth logout spotify
```

Видаляє токени з `~/.hermes/auth.json`. Щоб також очистити конфігурацію програми, видали `HERMES_SPOTIFY_CLIENT_ID` (і `HERMES_SPOTIFY_REDIRECT_URI`, якщо ти його встановив) з `~/.hermes/.env`, або запусти майстра ще раз.

Щоб відкликати доступ програми на стороні Spotify, відвідай [Apps connected to your account](https://www.spotify.com/account/apps/) і натисни **REMOVE ACCESS**.
## Устранення проблем

**`403 Forbidden — Player command failed: No active device found`** — Потрібно, щоб Spotify працював хоча б на одному пристрої. Відкрий додаток Spotify на телефоні, комп’ютері або у веб‑плеєрі, запусти будь‑який трек на секунду, щоб зареєструвати його, і спробуй ще раз. `spotify_devices list` показує, що зараз видно.

**`403 Forbidden — Premium required`** — Ти використовуєш Free акаунт і намагаєшся виконати дію, що змінює відтворення. Дивись матрицю функцій вище.

**`204 No Content` on `get_currently_playing`** — На жодному пристрої нічого не відтворюється. Це нормальна відповідь Spotify, а не помилка; Hermes представляє її як пояснювальний порожній результат (`is_playing: false`).

**`INVALID_CLIENT: Invalid redirect URI`** — URI перенаправлення у налаштуваннях твого додатку Spotify не збігається з тим, що використовує Hermes. За замовчуванням це `http://127.0.0.1:43827/spotify/callback`. Додай його до дозволених URI у своєму додатку або встанови `HERMES_SPOTIFY_REDIRECT_URI` у `~/.hermes/.env` на те, що ти зареєстрував.

**`429 Too Many Requests`** — Ліміт запитів Spotify. Hermes повертає дружню помилку; зачекай хвилину і спробуй ще раз. Якщо це триває, ймовірно, ти запускаєш щільний цикл у скрипті — квота Spotify скидається приблизно кожні 30 секунд.

**`401 Unauthorized` keeps coming back** — Твій токен оновлення був відкликаний (зазвичай через те, що ти видалив додаток зі свого акаунту або додаток був видалений). Запусти `hermes auth spotify` знову.

**Wizard doesn't open the browser** — Якщо ти працюєш через SSH або в контейнері без дисплея, Hermes це виявляє і пропускає автоматичне відкриття. Скопіюй URL панелі, який виводиться, і відкрий його вручну.
## Розширені: власні області доступу

За замовчуванням Hermes запитує області доступу, необхідні для кожного вбудованого інструмента. Перевизнач, якщо хочеш обмежити доступ:

```bash
hermes auth spotify --scope "user-read-playback-state user-modify-playback-state playlist-read-private"
```

Довідка щодо областей доступу: [Spotify Web API scopes](https://developer.spotify.com/documentation/web-api/concepts/scopes). Якщо ти запитаєш менше областей, ніж потребує інструмент, його виклики завершаться помилкою 403.
## Розширені: власний client ID / redirect URI

```bash
hermes auth spotify --client-id <id> --redirect-uri http://localhost:3000/callback
```

Або встанови їх постійно у `~/.hermes/.env`:

```
HERMES_SPOTIFY_CLIENT_ID=<your_id>
HERMES_SPOTIFY_REDIRECT_URI=http://localhost:3000/callback
```

Redirect URI має бути включений у список дозволених у налаштуваннях твого додатку Spotify. За замовчуванням підходить майже всім — змінюй його лише якщо порт 43827 зайнятий.
## Де розташовані файли

| Файл | Вміст |
|------|----------|
| `~/.hermes/auth.json` → `providers.spotify` | токен доступу, токен оновлення, термін дії, область, URI перенаправлення |
| `~/.hermes/.env` | `HERMES_SPOTIFY_CLIENT_ID`, необов’язковий `HERMES_SPOTIFY_REDIRECT_URI` |
| Spotify app | належить тобі на [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard); містить Client ID та список дозволених URI перенаправлення |