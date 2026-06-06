---
sidebar_position: 4
title: "Toolsets довідка"
description: "Довідка для Hermes core, composite, platform та dynamic toolsets"
---

# Довідник з наборів інструментів

Набори інструментів — це іменовані збірки інструментів, які визначають, що агент може робити. Вони є основним механізмом налаштування доступності інструментів для платформи, сесії або завдання.
## Як працюють набори інструментів

Кожен інструмент належить саме до одного набору інструментів. Коли ти вмикаєш набір інструментів, усі інструменти в цьому наборі стають доступними агенту. Набори інструментів поділяються на три типи:

- **Core** — Одна логічна група пов’язаних інструментів (наприклад, `file` містить `read_file`, `write_file`, `patch`, `search_files`);
- **Composite** — Поєднує кілька core‑наборів інструментів для спільного сценарію (наприклад, `debugging` містить інструменти `file`, `terminal` та `web`);
- **Platform** — Повна конфігурація інструментів для конкретного контексту розгортання (наприклад, `hermes-cli` є за замовчуванням для інтерактивних CLI‑сесій).
## Налаштування наборів інструментів

### Для сесії (CLI)

```bash
hermes chat --toolsets web,file,terminal
hermes chat --toolsets debugging        # composite — expands to file + terminal + web
hermes chat --toolsets all              # everything
```

### Для платформи (config.yaml)

```yaml
toolsets:
  - hermes-cli          # default for CLI
  # - hermes-telegram   # override for Telegram gateway
```

### Інтерактивне керування

```bash
hermes tools                            # curses UI to enable/disable per platform
```

Або під час сесії:

```
/tools list
/tools disable browser
/tools enable homeassistant
```
## Core Toolsets

| Toolset | Tools | Purpose |
|---------|-------|---------|
| `browser` | `browser_back`, `browser_cdp`, `browser_click`, `browser_console`, `browser_dialog`, `browser_get_images`, `browser_navigate`, `browser_press`, `browser_scroll`, `browser_snapshot`, `browser_type`, `browser_vision`, `web_search` | Основна автоматизація браузера. Включає `web_search` як запасний (варіант) для швидких пошуків. `browser_cdp` і `browser_dialog` активуються під час виконання — реєструються лише коли CDP‑endpoint доступний на старті сесії (через `/browser connect`, конфіг `browser.cdp_url`, Browserbase або Camofox). `browser_dialog` працює разом з полями `pending_dialogs` і `frame_tree`, які додає `browser_snapshot`, коли підключений супервізор CDP. |
| `clarify` | `clarify` | Запитати користувача, коли агент потребує уточнення. |
| `code_execution` | `execute_code` | Запускати Python‑скрипти, які програмно викликають інструменти Hermes. |
| `cronjob` | `cronjob` | Планувати та керувати повторюваними завданнями. |
| `debugging` | composite (`file` + `terminal` + `web`) | Пакет налагодження — файл, процес/термінал, веб‑витяг/пошук. |
| `delegation` | `delegate_task` | Створювати ізольовані під‑агенти для паралельної роботи. |
| `discord` | `discord` | Основні дії Discord (текст/embed/DM) (лише шлюз). Активний у наборі інструментів `hermes-discord`. |
| `discord_admin` | `discord_admin` | Модерація Discord (бан, зміна ролей, управління каналами). Активний у наборі інструментів `hermes-discord`; потребує, щоб бот мав відповідні дозволи Discord. |
| `feishu_doc` | `feishu_doc_read` | Читання вмісту документів Feishu/Lark. Використовується інтелектуальним обробником коментарів до документів Feishu. |
| `feishu_drive` | `feishu_drive_add_comment`, `feishu_drive_list_comments`, `feishu_drive_list_comment_replies`, `feishu_drive_reply_comment` | Операції з коментарями у Feishu/Lark Drive. Обмежено агентом коментарів; не доступно в `hermes-cli` чи інших наборах інструментів обміну повідомленнями. |
| `file` | `patch`, `read_file`, `search_files`, `write_file` | Читання, запис, пошук та редагування файлів. |
| `homeassistant` | `ha_call_service`, `ha_get_state`, `ha_list_entities`, `ha_list_services` | Керування розумним будинком через Home Assistant. Доступно лише коли встановлено `HASS_TOKEN`. |
| `computer_use` | `computer_use` | Фонове керування робочим столом macOS через `cua-driver` — не перехоплює курсор/фокус. Працює з будь‑якою моделлю, що підтримує інструменти. Тільки macOS; потребує `cua-driver` у `$PATH`. |
| `image_gen` | `image_generate` | Генерація зображень за текстом через FAL.ai (з опціональними бекендами OpenAI / xAI). |
| `video_gen` | `video_generate` | Генерація відео за текстом та перетворення зображень у відео через плагін‑зареєстровані бекенди (xAI Grok‑Imagine, FAL.ai Veo 3.1 / Pixverse v6 / Kling O3). Передай `image_url`, щоб анімувати зображення; опусти його для текст‑до‑відео. |
| `kanban` | `kanban_block`, `kanban_comment`, `kanban_complete`, `kanban_create`, `kanban_heartbeat`, `kanban_link`, `kanban_list`, `kanban_show`, `kanban_unblock` | Інструменти координації багатьох агентів. Зареєстровано для робітників‑диспетчерів (`HERMES_KANBAN_TASK`) та профілів, які явно вмикають набір `kanban`. Робітники позначають завдання виконаними, блокують, надсилають heartbeat, коментують та створюють/пов’язують подальші завдання; профілі‑оркестратори отримують додаткові інструменти маршрутизації дошки, такі як list/unblock. |
| `memory` | `memory` | Управління постійною пам’яттю між сесіями. |
| `messaging` | `send_message` | Надсилання повідомлень на інші платформи (Telegram, Discord тощо) зсередини сесії. |
| `moa` | `mixture_of_agents` | Консенсус між моделями через Mixture of Agents. |
| `safe` | `image_generate`, `vision_analyze`, `web_extract`, `web_search` (via `includes`) | Дослідження лише для читання + генерація медіа. Без запису файлів, без терміналу, без виконання коду. |
| `search` | `web_search` | Тільки веб‑пошук (без витягування). |
| `session_search` | `session_search` | Пошук у минулих розмовних сесіях. |
| `skills` | `skill_manage`, `skill_view`, `skills_list` | CRUD та перегляд навичок. |
| `spotify` | `spotify_albums`, `spotify_devices`, `spotify_library`, `spotify_playback`, `spotify_playlists`, `spotify_queue`, `spotify_search` | Нативне керування Spotify (відтворення, черга, пошук, плейлисти, альбоми, бібліотека). Зареєстровано плагіном `spotify`. |
| `terminal` | `process`, `terminal` | Виконання команд оболонки та управління фоновими процесами. |
| `todo` | `todo` | Управління списком завдань у межах сесії. |
| `tts` | `text_to_speech` | Генерація аудіо з тексту. |
| `vision` | `vision_analyze` | Аналіз зображень за допомогою моделей, що підтримують vision. |
| `video` | `video_analyze` | Інструменти аналізу та розуміння відео (опціонально, не у наборі за замовчуванням — додаються явно через `--toolsets`). |
| `web` | `web_extract`, `web_search` | Веб‑пошук та витяг вмісту сторінок. |
| `x_search` | `x_search` | Пошук постів і тем у X (Twitter) через вбудований інструмент `x_search` від xAI. Вимкнено за замовчуванням; вмикається через `hermes tools`. Схема реєструється лише коли налаштовані облікові дані xAI (SuperGrok OAuth або `XAI_API_KEY`). |
| `yuanbao` | `yb_query_group_info`, `yb_query_group_members`, `yb_search_sticker`, `yb_send_dm`, `yb_send_sticker` | Дії DM/групи та пошук стікерів у Yuanbao. Зареєстровано лише в `hermes-yuanbao`. |
## Platform Toolsets

Platform toolsets define the complete tool configuration for a deployment target. Most messaging platforms use the same set as `hermes-cli`:

| Toolset | Differences from `hermes-cli` |
|---------|-------------------------------|
| `hermes-cli` | Повний набір інструментів — типове значення для інтерактивних CLI‑сесій. Містить інструменти `file`, `terminal`, `web`, `browser`, `memory`, `skills`, `vision`, `image_gen`, `todo`, `tts`, `delegation`, `code_execution`, `cronjob`, `session_search`, `clarify` та `safe` (read‑only) bundles плюс стандартні інструменти обміну повідомленнями. |
| `hermes-acp` | Виключає `clarify`, `cronjob`, `image_generate`, `send_message`, `text_to_speech` та всі чотири інструменти Home Assistant. Орієнтовано на завдання кодування в контексті IDE. |
| `hermes-api-server` | Виключає `clarify`, `send_message` та `text_to_speech`. Залишає все інше — підходить для програмного доступу, коли взаємодія користувача неможлива. |
| `hermes-cron` | Той самий, що `hermes-cli`. |
| `hermes-telegram` | Той самий, що `hermes-cli`. |
| `hermes-discord` | Додає `discord` і `discord_admin` до набору `hermes-cli`. |
| `hermes-slack` | Той самий, що `hermes-cli`. |
| `hermes-whatsapp` | Той самий, що `hermes-cli`. |
| `hermes-signal` | Той самий, що `hermes-cli`. |
| `hermes-matrix` | Той самий, що `hermes-cli`. |
| `hermes-mattermost` | Той самий, що `hermes-cli`. |
| `hermes-email` | Той самий, що `hermes-cli`. |
| `hermes-sms` | Той самий, що `hermes-cli`. |
| `hermes-bluebubbles` | Той самий, що `hermes-cli`. |
| `hermes-dingtalk` | Той самий, що `hermes-cli`. |
| `hermes-feishu` | Додає п'ять інструментів `feishu_doc_*` / `feishu_drive_*` (використовуються лише обробником *document‑comment*, а не звичайним чат‑адаптером). |
| `hermes-qqbot` | Той самий, що `hermes-cli`. |
| `hermes-wecom` | Той самий, що `hermes-cli`. |
| `hermes-wecom-callback` | Той самий, що `hermes-cli`. |
| `hermes-weixin` | Той самий, що `hermes-cli`. |
| `hermes-yuanbao` | Додає п'ять інструментів `yb_*` (DM/group/sticker) до набору `hermes-cli`. |
| `hermes-homeassistant` | Той самий, що `hermes-cli` (інструменти Home Assistant вже присутні за замовчуванням і активуються, коли встановлено `HASS_TOKEN`). |
| `hermes-webhook` | Той самий, що `hermes-cli`. |
| `hermes-gateway` | Внутрішній інструмент‑оркестратор шлюзу — об’єднання всіх наборів `hermes-<platform>`; використовується, коли шлюз має приймати будь‑яке джерело повідомлень. |
## Динамічні набори інструментів

### Набори інструментів MCP‑серверу

Кожен налаштований MCP‑сервер генерує під час виконання набір інструментів `mcp-<server>`. Наприклад, якщо ти налаштуєш MCP‑сервер `github`, буде створено набір інструментів `mcp-github`, який містить усі інструменти, що їх цей сервер надає.

```yaml
# config.yaml
mcp_servers:
  github:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
```

Це створює набір інструментів `mcp-github`, який ти можеш вказати в `--toolsets` або в конфігураціях платформи.

### Набори інструментів плагінів

Плагіни можуть реєструвати власні набори інструментів через `ctx.register_tool()` під час ініціалізації плагіна. Вони з’являються поряд із вбудованими наборами інструментів і їх можна вмикати/вимикати тим же способом.

### Користувацькі набори інструментів

Визначай користувацькі набори інструментів у `config.yaml`, щоб створювати проєктно‑специфічні пакети:

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

### Шаблони

- `all` або `*` — розширюється до всіх зареєстрованих наборів інструментів (вбудованих + динамічних + плагінових)
## Відношення до `hermes tools`

Команда `hermes tools` надає інтерфейс на базі curses для перемикання окремих інструментів вкл/вимк для кожної платформи. Це працює на рівні інструменту (детальніше, ніж набори інструментів) і записує зміни у `config.yaml`. Вимкнені інструменти відфільтровуються, навіть якщо їх набір інструментів увімкнено.

Дивись також: [Tools Reference](./tools-reference.md) для повного списку окремих інструментів та їх параметрів.