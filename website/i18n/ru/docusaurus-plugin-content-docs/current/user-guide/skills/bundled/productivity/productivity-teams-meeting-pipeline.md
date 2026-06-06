---
title: "Teams конвейер встречи"
sidebar_label: "Teams Meeting Pipeline"
description: "Управляй конвейером резюмирования встреч Teams через Hermes CLI — резюмируй встречи, проверяй статус конвейера, воспроизводи задания, управляй подписками Microsoft Graph"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Конвейер сводок встреч Teams

Оперативно управляй конвейером сводок встреч Teams через Hermes CLI — подводи итоги встреч, проверяй статус конвейера, воспроизводи задания, управляй подписками Microsoft Graph.

## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/productivity/teams-meeting-pipeline` |
| Version | `1.1.0` |
| Author | Hermes Agent + Teknium |
| License | MIT |
| Tags | `Teams`, `Microsoft Graph`, `Meetings`, `Productivity`, `Operations` |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции, когда навык включён.
:::

# Конвейер сводок встреч Teams

Используй этот навык, когда пользователь спрашивает о сводках встреч Microsoft Teams, транскриптах, записях, действиях, подписках Graph или любом операционном вопросе о конвейере встреч Teams. Работает на любом языке — приведённые ниже триггеры являются примерами, а не исчерпывающим списком.

Всё, что относится к оператору, представляет собой подкоманду `hermes teams-pipeline`, запускаемую через терминальный инструмент. Для этого конвейера нет новых инструментов модели — CLI является интерфейсом.

## Когда использовать этот навык

Пользователь просит:
- подвести итоги встречи Teams / извлечь действия / получить заметки встречи
- проверить статус конвейера, просмотреть сохранённое задание встречи или увидеть последние встречи
- воспроизвести / повторно запустить сохранённое задание, которое не удалось выполнить или требует свежего резюме
- проверить настройку Microsoft Graph после изменения переменных окружения или конфигурации
- устранить проблему «сводка встречи не пришла» или «новые встречи не поступают»
- управлять подписками webhook Graph (создать, обновить, удалить, просмотреть)
- настроить автоматическое обновление подписок (см. подводный камень ниже)

Примеры многоязычных триггеров (не исчерпывающий список):
- English: "summarize the Teams meeting", "pipeline status", "replay job X"
- Turkish: "Teams meeting özetle", "action item çıkar", "toplantı notu", "pipeline durumu", "replay job"

## Предварительные условия

Перед использованием конвейера убедись, что в `~/.hermes/.env` заданы следующие параметры:

```bash
MSGRAPH_TENANT_ID=...
MSGRAPH_CLIENT_ID=...
MSGRAPH_CLIENT_SECRET=...
```

Если чего‑то не хватает, направь пользователя к руководству по регистрации приложения Azure по адресу `/docs/guides/microsoft-graph-app-registration` — им нужна регистрация приложения Azure AD с разрешениями Graph, согласованными администратором, прежде чем конвейер начнёт работать.

## Справочник команд

### Статус и проверка (начни здесь)

```bash
hermes teams-pipeline validate              # config snapshot — run first after any change
hermes teams-pipeline token-health          # Graph token status
hermes teams-pipeline token-health --force-refresh   # force a fresh token acquisition
hermes teams-pipeline list                  # recent meeting jobs
hermes teams-pipeline list --status failed  # only failed jobs
hermes teams-pipeline show <job-id>         # full detail of one job
hermes teams-pipeline subscriptions         # current Graph webhook subscriptions
```

### Повторный запуск / отладка

```bash
hermes teams-pipeline run <job-id>          # replay a stored job (re-summarize, re-deliver)
hermes teams-pipeline fetch --meeting-id <id>   # dry-run: resolve meeting + transcript without persisting
hermes teams-pipeline fetch --join-web-url "<url>"   # dry-run by join URL
```

### Управление подписками

```bash
hermes teams-pipeline subscribe \
  --resource communications/onlineMeetings/getAllTranscripts \
  --notification-url https://<your-public-host>/msgraph/webhook \
  --client-state "$MSGRAPH_WEBHOOK_CLIENT_STATE"

hermes teams-pipeline renew-subscription <sub-id> --expiration <iso-8601>
hermes teams-pipeline delete-subscription <sub-id>
hermes teams-pipeline maintain-subscriptions            # renew near-expiry ones
hermes teams-pipeline maintain-subscriptions --dry-run  # show what would be renewed
```

## Дерево решений для типовых запросов

- Пользователь спрашивает «почему я не получил сводку сегодняшней встречи?» → начни с `list --status failed`, затем `show <job-id>` для соответствующей строки. Если задания вообще нет, проверь `subscriptions` — возможно, webhook истёк (см. подводный камень ниже).
- Пользователь спрашивает «работает ли настройка?» → `validate`, затем `token-health`, затем `subscriptions`. Если все три прошли, запроси тестовую встречу и проверь `list` на наличие новой строки.
- Пользователь спрашивает «перезапусти сводку для встречи X» → используй `list`, чтобы найти ID задания, затем `run <job-id>` для воспроизведения. Если снова не удалось, `show <job-id>` для изучения ошибки и `fetch --meeting-id` для сухого прогона разрешения артефактов.
- Пользователь спрашивает «добавить встречу X в конвейер» → обычно не нужно — конвейер управляется подписками, а не отдельными встречами. Если нужна сводка конкретной прошлой встречи, используй `fetch` для получения транскрипта + `run` после создания задания.

## Критический подводный камень: подписки Graph истекают через 72 часа

Microsoft Graph ограничивает подписки webhook 72‑часовым сроком и **не будет автоматически их продлять**. Если `maintain-subscriptions` не запланирован, уведомления о встречах тихо перестанут приходить через 3 дня после любой ручной создания подписки.

Когда пользователь сообщает «вчера конвейер работал, а сегодня ничего не приходит»:
1. Выполни `hermes teams-pipeline subscriptions` — если список пуст или все записи показывают `expirationDateTime` в прошлом, это причина.
2. Воссоздай подписку с помощью `subscribe`, как показано выше.
3. **Немедленно настрой автоматическое обновление** через `hermes cron add`, таймер systemd или обычный crontab. Руководство оператора по адресу `/docs/guides/operate-teams-meeting-pipeline#automating-subscription-renewal-required-for-production` содержит все три варианта. Интервал в 12 часов безопасен (6‑кратный запас против ограничения в 72 часа).

## Другие подводные камни

- **Транскрипт ещё недоступен.** Teams требуется время после завершения встречи, чтобы сгенерировать артефакт транскрипта. `fetch --meeting-id` для только что завершённой встречи может вернуть пустой результат. Подожди 2‑5 минут и повтори запрос, либо позволь webhook Graph автоматически выполнить загрузку.
- **Несоответствие режима доставки.** Если сводки созданы (`list` показывает успех), но ничего не появляется в Teams, проверь `platforms.teams.extra.delivery_mode` и соответствующую целевую конфигурацию (`incoming_webhook_url` ИЛИ `chat_id` ИЛИ `team_id`+`channel_id`). Писатель читает эти параметры из `config.yaml` или переменных окружения `TEAMS_*`.
- **Разрешения приложения Graph.** Токен успешно получен (`token-health` проходит), но вызовы API Graph возвращают 401/403, когда разрешения были добавлены, но согласие администратора не было повторно предоставлено. Попроси пользователя заново открыть регистрацию приложения в портале Azure и нажать «Grant admin consent».

## Связанные документы

Направь пользователя к этим материалам, если требуется более глубокое погружение, чем покрывает навык:
- Пошаговое руководство по регистрации приложения Azure: `/docs/guides/microsoft-graph-app-registration`
- Полная настройка конвейера: `/docs/user-guide/messaging/teams-meetings`
- Руководство оператора (автоматизация обновления, отладка, чек‑лист запуска): `/docs/guides/operate-teams-meeting-pipeline`
- Настройка прослушивателя webhook: `/docs/user-guide/messaging/msgraph-webhook`