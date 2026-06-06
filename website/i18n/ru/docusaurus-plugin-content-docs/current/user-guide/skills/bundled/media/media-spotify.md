---
title: "Spotify — Spotify: воспроизводить, искать, ставить в очередь, управлять плейлистами и устройствами"
sidebar_label: "Spotify"
description: "Spotify: воспроизводить, искать, ставить в очередь, управлять плейлистами и устройствами"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Spotify

Spotify: воспроизведение, поиск, очередь, управление плейлистами и устройствами.

## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/media/spotify` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `spotify`, `music`, `playback`, `playlists`, `media` |
| Related skills | [`gif-search`](/docs/user-guide/skills/bundled/media/media-gif-search) |

## Ссылка: полный SKILL.md

:::info
Ниже полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции, когда навык активен.
:::

# Spotify

Управляй учётной записью Spotify пользователя через набор инструментов Hermes Spotify (7 инструментов). Руководство по настройке: https://hermes-agent.nousresearch.com/docs/user-guide/features/spotify

## Когда использовать этот навык

Пользователь говорит что‑то вроде «play X», «pause», «skip», «queue up X», «what's playing», «search for X», «add to my X playlist», «make a playlist», «save this to my library» и т.д.

## 7 инструментов

- `spotify_playback` — play, pause, next, previous, seek, set_repeat, set_shuffle, set_volume, get_state, get_currently_playing, recently_played
- `spotify_devices` — list, transfer
- `spotify_queue` — get, add
- `spotify_search` — search the catalog
- `spotify_playlists` — list, get, create, add_items, remove_items, update_details
- `spotify_albums` — get, tracks
- `spotify_library` — list/save/remove with `kind: "tracks"|"albums"`

Действия, изменяющие воспроизведение, требуют Spotify Premium; операции поиска, библиотеки и плейлистов работают в бесплатной версии.

## Канонические паттерны (минимизировать вызовы инструментов)

### «Play <artist/track/album>»

Один поиск, затем воспроизведение по URI. НЕ перебирай результаты поиска, описывая их, если пользователь не запросил варианты.

```
spotify_search({"query": "miles davis kind of blue", "types": ["album"], "limit": 1})
→ got album URI spotify:album:1weenld61qoidwYuZ1GESA
spotify_playback({"action": "play", "context_uri": "spotify:album:1weenld61qoidwYuZ1GESA"})
```

Для «play some <artist>» (без конкретной песни) предпочтительно `types: ["artist"]` и воспроизведение URI контекста артиста — Spotify сам делает умный shuffle. Если пользователь говорит «the song» или «that track», ищи `types: ["track"]` и передай `uris: [track_uri]` для воспроизведения.

### «What's playing?» / «What am I listening to?»

Один вызов — не цепляй `get_state` после `get_currently_playing`.

```
spotify_playback({"action": "get_currently_playing"})
```

Если возвращается 204/пусто (`is_playing: false`), сообщи пользователю, что ничего не воспроизводится. Не повторяй запрос.

### «Pause» / «Skip» / «Volume 50»

Прямое действие, проверка состояния не нужна.

```
spotify_playback({"action": "pause"})
spotify_playback({"action": "next"})
spotify_playback({"action": "set_volume", "volume_percent": 50})
```

### «Add to my <playlist name> playlist»

1. `spotify_playlists list` — найти ID плейлиста по имени
2. Получить URI трека (из текущего воспроизведения или поиска)
3. `spotify_playlists add_items` с `playlist_id` и `uris`

```
spotify_playlists({"action": "list"})
→ found "Late Night Jazz" = 37i9dQZF1DX4wta20PHgwo
spotify_playback({"action": "get_currently_playing"})
→ current track uri = spotify:track:0DiWol3AO6WpXZgp0goxAV
spotify_playlists({"action": "add_items",
                   "playlist_id": "37i9dQZF1DX4wta20PHgwo",
                   "uris": ["spotify:track:0DiWol3AO6WpXZgp0goxAV"]})
```

### «Create a playlist called X and add the last 3 songs I played»

```
spotify_playback({"action": "recently_played", "limit": 3})
spotify_playlists({"action": "create", "name": "Focus 2026"})
→ got playlist_id back in response
spotify_playlists({"action": "add_items", "playlist_id": <id>, "uris": [<3 uris>]})
```

### «Save / unsave / is this saved?»

Используй `spotify_library` с нужным `kind`.

```
spotify_library({"kind": "tracks", "action": "save", "uris": ["spotify:track:..."]})
spotify_library({"kind": "albums", "action": "list", "limit": 50})
```

### «Transfer playback to my <device>»

```
spotify_devices({"action": "list"})
→ pick the device_id by matching name/type
spotify_devices({"action": "transfer", "device_id": "<id>", "play": true})
```

## Критические режимы отказа

**`403 Forbidden — No active device found`** при любой операции воспроизведения означает, что Spotify не запущен ни на одном устройстве. Скажи пользователю: «Открой Spotify на телефоне/компьютере/веб‑плеере, запусти любую дорожку на секунду, затем повтори запрос». Не повторяй вызов инструмента слепо — он снова завершится ошибкой. Можно вызвать `spotify_devices list` для проверки; пустой список значит отсутствие активного устройства.

**`403 Forbidden — Premium required`** значит, что пользователь использует бесплатный план и попытался изменить воспроизведение. Не повторяй запрос; сообщи, что для этого действия нужен Premium. Чтение (поиск, плейлисты, библиотека, `get_state`) работает.

**`204 No Content` на `get_currently_playing`** НЕ является ошибкой — значит ничего не воспроизводится. Инструмент возвращает `is_playing: false`. Просто передай эту информацию пользователю.

**`429 Too Many Requests`** = ограничение по частоте. Подожди и попробуй один раз повторить. Если ошибка продолжается, ты зациклился — остановись.

**`401 Unauthorized` после повторной попытки** — токен доступа отозван. Попроси пользователя выполнить `hermes auth spotify` снова.

## Форматы URI и ID

Spotify использует три взаимозаменяемых формата ID. Инструменты принимают все три и нормализуют:

- URI: `spotify:track:0DiWol3AO6WpXZgp0goxAV` (предпочтительно)
- URL: `https://open.spotify.com/track/0DiWol3AO6WpXZgp0goxAV`
- Чистый ID: `0DiWol3AO6WpXZgp0goxAV`

При сомнении используй полные URI. Результаты поиска возвращают URI в поле `uri` — передавай их напрямую.

Типы сущностей: `track`, `album`, `artist`, `playlist`, `show`, `episode`. Используй правильный тип для действия — `spotify_playback.play` с `context_uri` ожидает album/playlist/artist; `uris` ожидает массив URI треков.

## Что НЕ делать

- **Не вызывай `get_state` перед каждым действием.** Spotify принимает play/pause/skip без предварительной проверки. Проверяй состояние только когда пользователь спрашивает «what's playing» или когда нужно рассуждать о устройстве/треке.
- **Не описывай результаты поиска, если об этом не просят.** Если пользователь сказал «play X», ищи, берём верхний URI и воспроизводим его. Пользователь сразу заметит, если это неверно.
- **Не повторяй запрос при `403 Premium required` или `403 No active device`.** Эти ошибки постоянны до действий пользователя.
- **Не используй `spotify_search` для поиска плейлиста по имени** — этот поиск проходит по публичному каталогу Spotify. Пользовательские плейлисты получаются через `spotify_playlists list`.
- **Не смешивай `kind: "tracks"` с URI альбомов** в `spotify_library` (и наоборот). Инструмент нормализует ID, но конечные точки API различаются.