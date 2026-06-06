---
sidebar_position: 4
title: "Справочник наборов инструментов"
description: "Справочник по ядру Hermes, составным, платформенным и динамическим наборам инструментов"
---

# Справочник наборов инструментов

Наборы инструментов — это именованные наборы инструментов, которые определяют, что может делать агент. Они являются основным механизмом настройки доступности инструментов для каждой платформы, каждой сессии или каждой задачи.
## Как работают наборы инструментов

Каждый инструмент принадлежит ровно одному набору инструментов. Когда ты включаешь набор инструментов, все инструменты в этом наборе становятся доступными агенту. Наборы инструментов бывают трёх типов:

- **Core** — Одна логическая группа связанных инструментов (например, `file` включает `read_file`, `write_file`, `patch`, `search_files`)
- **Composite** — Объединяет несколько наборов Core для общего сценария (например, `debugging` включает инструменты `file`, `terminal` и `web`)
- **Platform** — Полная конфигурация инструментов для конкретного контекста развертывания (например, `hermes-cli` является набором по умолчанию для интерактивных CLI‑сессий)
## Настройка наборов инструментов

### Для каждой сессии (CLI)

```bash
hermes chat --toolsets web,file,terminal
hermes chat --toolsets debugging        # composite — expands to file + terminal + web
hermes chat --toolsets all              # everything
```

### Для каждой платформы (config.yaml)

```yaml
toolsets:
  - hermes-cli          # default for CLI
  # - hermes-telegram   # override for Telegram gateway
```

### Интерактивное управление

```bash
hermes tools                            # curses UI to enable/disable per platform
```

Или в рамках сессии:

```
/tools list
/tools disable browser
/tools enable homeassistant
```
## Core Toolsets

| Toolset | Tools | Purpose |
|---------|-------|---------|
| `browser` | `browser_back`, `browser_cdp`, `browser_click`, `browser_console`, `browser_dialog`, `browser_get_images`, `browser_navigate`, `browser_press`, `browser_scroll`, `browser_snapshot`, `browser_type`, `browser_vision`, `web_search` | Основная автоматизация браузера. Включает `web_search` как запасной вариант для быстрых запросов. `browser_cdp` и `browser_dialog` включаются во время выполнения — регистрируются только когда конечная точка CDP доступна при старте сессии (через `/browser connect`, конфигурацию `browser.cdp_url`, Browserbase или Camofox). `browser_dialog` работает совместно с полями `pending_dialogs` и `frame_tree`, которые добавляет `browser_snapshot`, когда к нему присоединён супервизор CDP. |
| `clarify` | `clarify` | Задать пользователю вопрос, когда агенту требуется уточнение. |
| `code_execution` | `execute_code` | Выполнять Python‑скрипты, вызывающие инструменты Hermes программно. |
| `cronjob` | `cronjob` | Планировать и управлять периодическими задачами. |
| `debugging` | composite (`file` + `terminal` + `web`) | Набор отладки — файлы, процесс/терминал, извлечение/поиск в вебе. |
| `delegation` | `delegate_task` | Запуск изолированных подагентов для параллельной работы. |
| `discord` | `discord` | Основные действия в Discord (текст/встроенные сообщения/DM) (только шлюз). Активно в наборе `hermes-discord`. |
| `discord_admin` | `discord_admin` | Модерация Discord (баны, изменения ролей, управление каналами). Активно в наборе `hermes-discord`; требует, чтобы бот имел соответствующие разрешения Discord. |
| `feishu_doc` | `feishu_doc_read` | Чтение содержимого документов Feishu/Lark. Используется обработчиком интеллектуального ответа на комментарии к документу Feishu. |
| `feishu_drive` | `feishu_drive_add_comment`, `feishu_drive_list_comments`, `feishu_drive_list_comment_replies`, `feishu_drive_reply_comment` | Операции с комментариями в Feishu/Lark Drive. Ограничено агентом комментариев; недоступно в `hermes-cli` или других наборах обмена сообщениями. |
| `file` | `patch`, `read_file`, `search_files`, `write_file` | Чтение, запись, поиск и редактирование файлов. |
| `homeassistant` | `ha_call_service`, `ha_get_state`, `ha_list_entities`, `ha_list_services` | Управление умным домом через Home Assistant. Доступно только при установленном `HASS_TOKEN`. |
| `computer_use` | `computer_use` | Фоновое управление macOS‑рабочим столом через `cua-driver` — не захватывает курсор/фокус. Работает с любой моделью, поддерживающей инструменты. Только macOS; требует `cua-driver` в `$PATH`. |
| `image_gen` | `image_generate` | Генерация изображений из текста через FAL.ai (с включёнными бэкендами OpenAI / xAI). |
| `video_gen` | `video_generate` | Генерация видео из текста и из изображения через плагины‑бэкенды (xAI Grok-Imagine, FAL.ai Veo 3.1 / Pixverse v6 / Kling O3). Передай `image_url`, чтобы анимировать изображение; опусти его для генерации из текста. |
| `kanban` | `kanban_block`, `kanban_comment`, `kanban_complete`, `kanban_create`, `kanban_heartbeat`, `kanban_link`, `kanban_list`, `kanban_show`, `kanban_unblock` | Инструменты координации мульти‑агентов. Регистрируются для задач‑рабочих, создаваемых диспетчером (`HERMES_KANBAN_TASK`), и для профилей, явно включающих набор `kanban`. Рабочие отмечают задачи выполненными, блокируют, отправляют heartbeat, комментируют и создают/связывают последующие задачи; профили‑оркестраторы дополнительно получают инструменты маршрутизации доски, такие как list/unblock. |
| `memory` | `memory` | Управление постоянной памятью между сессиями. |
| `messaging` | `send_message` | Отправка сообщений на другие платформы (Telegram, Discord и др.) изнутри сессии. |
| `moa` | `mixture_of_agents` | Консенсус нескольких моделей через Mixture of Agents. |
| `safe` | `image_generate`, `vision_analyze`, `web_extract`, `web_search` (via `includes`) | Исследования только для чтения + генерация медиа. Без записи файлов, без терминала, без выполнения кода. |
| `search` | `web_search` | Только веб‑поиск (без извлечения). |
| `session_search` | `session_search` | Поиск по прошлым сессиям диалога. |
| `skills` | `skill_manage`, `skill_view`, `skills_list` | CRUD и просмотр навыков. |
| `spotify` | `spotify_albums`, `spotify_devices`, `spotify_library`, `spotify_playback`, `spotify_playlists`, `spotify_queue`, `spotify_search` | Нативное управление Spotify (воспроизведение, очередь, поиск, плейлисты, альбомы, библиотека). Регистрируется плагином `spotify`. |
| `terminal` | `process`, `terminal` | Выполнение команд оболочки и управление фоновыми процессами. |
| `todo` | `todo` | Управление списком задач внутри сессии. |
| `tts` | `text_to_speech` | Генерация аудио из текста. |
| `vision` | `vision_analyze` | Анализ изображений через модели с поддержкой vision. |
| `video` | `video_analyze` | Инструменты анализа и понимания видео (по желанию, не включены в набор по умолчанию — добавить явно через `--toolsets`). |
| `web` | `web_extract`, `web_search` | Веб‑поиск и извлечение содержимого страниц. |
| `x_search` | `x_search` | Поиск постов и веток в X (Twitter) через встроенный инструмент `x_search` от xAI. Отключено по умолчанию; включается через `hermes tools`. Схема регистрируется только при наличии учётных данных xAI (SuperGrok OAuth или `XAI_API_KEY`). |
| `yuanbao` | `yb_query_group_info`, `yb_query_group_members`, `yb_search_sticker`, `yb_send_dm`, `yb_send_sticker` | Действия DM/группы и поиск стикеров в Yuanbao. Регистрируется только в `hermes-yuanbao`. |
## Наборы инструментов платформы

Platform toolsets define the complete tool configuration for a deployment target. Most messaging platforms use the same set as `hermes-cli`:

| Набор инструментов | Отличия от `hermes-cli` |
|--------------------|------------------------|
| `hermes-cli` | Полный набор инструментов — по умолчанию для интерактивных CLI‑сессий. Включает `file`, `terminal`, `web`, `browser`, `memory`, `skills`, `vision`, `image_gen`, `todo`, `tts`, `delegation`, `code_execution`, `cronjob`, `session_search`, `clarify` и `safe` (только для чтения)‑пакеты плюс стандартные инструменты обмена сообщениями. |
| `hermes-acp` | Убирает `clarify`, `cronjob`, `image_gen`, `send_message`, `text_to_speech` и все четыре инструмента Home Assistant. Ориентирован на задачи кодирования в контексте IDE. |
| `hermes-api-server` | Убирает `clarify`, `send_message` и `text_to_speech`. Сохраняет всё остальное — подходит для программного доступа, когда взаимодействие с пользователем невозможно. |
| `hermes-cron` | То же, что и `hermes-cli`. |
| `hermes-telegram` | То же, что и `hermes-cli`. |
| `hermes-discord` | Добавляет `discord` и `discord_admin` к `hermes-cli`. |
| `hermes-slack` | То же, что и `hermes-cli`. |
| `hermes-whatsapp` | То же, что и `hermes-cli`. |
| `hermes-signal` | То же, что и `hermes-cli`. |
| `hermes-matrix` | То же, что и `hermes-cli`. |
| `hermes-mattermost` | То же, что и `hermes-cli`. |
| `hermes-email` | То же, что и `hermes-cli`. |
| `hermes-sms` | То же, что и `hermes-cli`. |
| `hermes-bluebubbles` | То же, что и `hermes-cli`. |
| `hermes-dingtalk` | То же, что и `hermes-cli`. |
| `hermes-feishu` | Добавляет пять инструментов `feishu_doc_*` / `feishu_drive_*` (используются только обработчиком **document‑comment**, а не обычным чат‑адаптером). |
| `hermes-qqbot` | То же, что и `hermes-cli`. |
| `hermes-wecom` | То же, что и `hermes-cli`. |
| `hermes-wecom-callback` | То же, что и `hermes-cli`. |
| `hermes-weixin` | То же, что и `hermes-cli`. |
| `hermes-yuanbao` | Добавляет пять инструментов `yb_*` (DM/группа/стикер) к `hermes-cli`. |
| `hermes-homeassistant` | То же, что и `hermes-cli` (инструменты Home Assistant уже присутствуют по умолчанию и активируются при установленном `HASS_TOKEN`). |
| `hermes-webhook` | То же, что и `hermes-cli`. |
| `hermes-gateway` | Внутренний набор инструментов оркестратора **шлюза инструментов** — объединение всех наборов `hermes-<platform>`; используется, когда шлюзу необходимо принимать сообщения из любого источника. |
## Динамические наборы инструментов

### Наборы инструментов сервера MCP

Каждый настроенный сервер MCP генерирует набор инструментов `mcp-<server>` во время выполнения. Например, если ты настраиваешь сервер MCP `github`, создаётся набор `mcp-github`, содержащий все инструменты, которые предоставляет этот сервер.

```yaml
# config.yaml
mcp_servers:
  github:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
```

Это создаёт набор `mcp-github`, который ты можешь указать в `--toolsets` или в конфигурациях платформы.

### Наборы инструментов плагинов

Плагины могут регистрировать свои собственные наборы инструментов через `ctx.register_tool()` во время инициализации плагина. Они появляются рядом со встроенными наборами инструментов и могут быть включены/отключены тем же способом.

### Пользовательские наборы инструментов

Определяй пользовательские наборы инструментов в `config.yaml`, чтобы создавать наборы, специфичные для проекта:

```yaml
toolsets:
  - hermes-cli
custom_toolsets:
  data-science:
    - file
    - terminal
    - code_execution
    - web
    - vision
```

### Шаблоны

- `all` или `*` — расширяется до всех зарегистрированных наборов инструментов (встроенные + динамические + плагины)
## Отношения к `hermes tools`

Команда `hermes tools` предоставляет curses‑based UI для включения или отключения отдельных **инструментов** на каждой платформе. Она работает на уровне инструмента (тоньше, чем наборы инструментов) и сохраняет изменения в `config.yaml`. Отключённые инструменты фильтруются, даже если их набор инструментов включён.

См. также: [Tools Reference](./tools-reference.md) для полного списка отдельных инструментов и их параметров.