---
title: "Spotify — Spotify: відтворювати, шукати, додавати в чергу, керувати плейлистами та пристроями"
sidebar_label: "Spotify"
description: "Spotify: відтворювати, шукати, ставити в чергу, керувати плейлистами та пристроями"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Spotify

Spotify: відтворення, пошук, черга, керування плейлистами та пристроями.

## Метадані навички

| | |
|---|---|
| Джерело | Bundled (installed by default) |
| Шлях | `skills/media/spotify` |
| Версія | `1.0.0` |
| Автор | Hermes Agent |
| Ліцензія | MIT |
| Платформи | linux, macos, windows |
| Теги | `spotify`, `music`, `playback`, `playlists`, `media` |
| Пов’язані навички | [`gif-search`](/docs/user-guide/skills/bundled/media/media-gif-search) |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# Spotify

Керуйте обліковим записом користувача Spotify за допомогою набору інструментів Hermes Spotify (7 інструментів). Посібник з налаштування: https://hermes-agent.nousresearch.com/docs/user-guide/features/spotify

## Коли використовувати цю навичку

Користувач каже щось на кшталт «play X», «pause», «skip», «queue up X», «what's playing», «search for X», «add to my X playlist», «make a playlist», «save this to my library» тощо.

## 7 інструментів

- `spotify_playback` — play, pause, next, previous, seek, set_repeat, set_shuffle, set_volume, get_state, get_currently_playing, recently_played
- `spotify_devices` — list, transfer
- `spotify_queue` — get, add
- `spotify_search` — search the catalog
- `spotify_playlists` — list, get, create, add_items, remove_items, update_details
- `spotify_albums` — get, tracks
- `spotify_library` — list/save/remove with `kind: "tracks"|"albums"`

Дії, що змінюють відтворення, вимагають Spotify Premium; пошук/бібліотека/операції з плейлистами працюють у безкоштовному режимі.

## Канонічні шаблони (мінімізуйте виклики інструментів)

### "Play &lt;artist/track/album>"
Один пошук, потім відтворення за URI. НЕ перебирайте результати пошуку, описуючи їх, якщо користувач не просив варіанти.

```
spotify_search({"query": "miles davis kind of blue", "types": ["album"], "limit": 1})
→ got album URI spotify:album:1weenld61qoidwYuZ1GESA
spotify_playback({"action": "play", "context_uri": "spotify:album:1weenld61qoidwYuZ1GESA"})
```

Для «play some &lt;artist>» (без конкретної пісні) використовуйте `types: ["artist"]` і відтворюйте URI контексту артиста — Spotify самостійно здійснює розумне перемішування. Якщо користувач каже «the song» або «that track», шукайте `types: ["track"]` і передайте `uris: [track_uri]` для відтворення.

### "What's playing?" / "What am I listening to?"
Один виклик — не ланцюжте `get_state` після `get_currently_playing`.

```
spotify_playback({"action": "get_currently_playing"})
```

Якщо повертає 204/empty (`is_playing: false`), повідомте користувачу, що нічого не відтворюється. Не повторюйте запит.

### "Pause" / "Skip" / "Volume 50"
Пряма дія, попередня перевірка не потрібна.

```
spotify_playback({"action": "pause"})
spotify_playback({"action": "next"})
spotify_playback({"action": "set_volume", "volume_percent": 50})
```

### "Add to my &lt;playlist name> playlist"
1. `spotify_playlists list` — знайти ID плейлиста за назвою
2. Отримати URI треку (з поточного відтворення або пошуку)
3. `spotify_playlists add_items` з `playlist_id` та `uris`

```
spotify_playlists({"action": "list"})
→ found "Late Night Jazz" = 37i9dQZF1DX4wta20PHgwo
spotify_playback({"action": "get_currently_playing"})
→ current track uri = spotify:track:0DiWol3AO6WpXZgp0goxAV
spotify_playlists({"action": "add_items",
                   "playlist_id": "37i9dQZF1DX4wta20PHgwo",
                   "uris": ["spotify:track:0DiWol3AO6WpXZgp0goxAV"]})
```

### "Create a playlist called X and add the last 3 songs I played"
```
spotify_playback({"action": "recently_played", "limit": 3})
spotify_playlists({"action": "create", "name": "Focus 2026"})
→ got playlist_id back in response
spotify_playlists({"action": "add_items", "playlist_id": <id>, "uris": [<3 uris>]})
```

### "Save / unsave / is this saved?"
Використовуйте `spotify_library` з відповідним `kind`.

```
spotify_library({"kind": "tracks", "action": "save", "uris": ["spotify:track:..."]})
spotify_library({"kind": "albums", "action": "list", "limit": 50})
```

### "Transfer playback to my &lt;device>"
```
spotify_devices({"action": "list"})
→ pick the device_id by matching name/type
spotify_devices({"action": "transfer", "device_id": "<id>", "play": true})
```

## Критичні режими відмов

**`403 Forbidden — No active device found`** при будь‑якій дії відтворення означає, що Spotify не запущений ніде. Скажи користувачу: «Спочатку відкрий Spotify на телефоні/десктопі/веб‑плеєрі, запусти будь‑яку композицію на секунду, потім спробуй ще раз». Не повторюй виклик інструмента бездумно — він знову завершиться помилкою. Можеш викликати `spotify_devices list` для перевірки; порожній список означає відсутність активного пристрою.

**`403 Forbidden — Premium required`** означає, що користувач користується Free‑версією і спробував змінити відтворення. Не повторюй; повідом його, що ця дія потребує Premium. Читання (пошук, плейлисти, бібліотека, `get_state`) працює.

**`204 No Content` на `get_currently_playing`** НЕ є помилкою — це означає, що нічого не відтворюється. Інструмент повертає `is_playing: false`. Просто повідом це користувачу.

**`429 Too Many Requests`** = обмеження швидкості. Зачекай і спробуй ще раз один раз. Якщо продовжується, ти зациклився — зупинись.

**`401 Unauthorized` після повторної спроби** — токен оновлення відкликано. Скажи користувачу запустити `hermes auth spotify` знову.

## Формати URI та ID

Spotify використовує три взаємозамінні формати ID. Інструменти приймають усі три і нормалізують їх:

- URI: `spotify:track:0DiWol3AO6WpXZgp0goxAV` (рекомендовано)
- URL: `https://open.spotify.com/track/0DiWol3AO6WpXZgp0goxAV`
- Bare ID: `0DiWol3AO6WpXZgp0goxAV`

У разі сумніву використовуйте повні URI. Результати пошуку повертають URI у полі `uri` — передавайте їх без змін.

Типи сутностей: `track`, `album`, `artist`, `playlist`, `show`, `episode`. Використовуйте правильний тип для дії — `spotify_playback.play` з `context_uri` очікує `album`/`playlist`/`artist`; `uris` очікує масив URI треків.

## Чого НЕ робити

- **Не викликайте `get_state` перед кожною дією.** Spotify приймає play/pause/skip без попередньої перевірки. Перевіряйте стан лише коли користувач запитав «what's playing» або коли потрібно розібратись з пристроєм/треком.
- **Не описуйте результати пошуку, якщо про це не просять.** Якщо користувач сказав «play X», шукайте, беріть верхній URI і відтворюйте його. Він почує, якщо це не те, що треба.
- **Не повторюйте запит при `403 Premium required` або `403 No active device`.** Це постійні помилки, доки користувач не виконає дії.
- **Не використовуйте `spotify_search` для пошуку плейлиста за назвою** — цей пошук працює по публічному каталогу Spotify. Користувацькі плейлисти отримуються через `spotify_playlists list`.
- **Не змішуйте `kind: "tracks"` з URI альбомів** у `spotify_library` (і навпаки). Інструмент нормалізує ID, але кінцева точка API різна.