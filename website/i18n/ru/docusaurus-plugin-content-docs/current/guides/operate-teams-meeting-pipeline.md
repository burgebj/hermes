---
title: "Запусти конвейер встречи Teams"
description: "Runbook, чеклист go-live и рабочий лист оператора для конвейера встреч Microsoft Teams"
---

# Управление конвейером встреч Teams

Используй это руководство после того, как уже включил функцию в разделе [Teams Meetings](/user-guide/messaging/teams-meetings).

На этой странице рассматривается:
- потоки CLI оператора
- рутинное обслуживание подписок
- диагностика сбоев
- проверки перед запуском
- рабочий лист развертывания

## Основные команды оператора

### Проверка снимка конфигурации

```bash
hermes teams-pipeline validate
```

Выполняй это первым делом после любого изменения конфигурации.

### Проверка состояния токена

```bash
hermes teams-pipeline token-health
hermes teams-pipeline token-health --force-refresh
```

Используй `--force-refresh`, если подозреваешь устаревшее состояние аутентификации.

### Проверка подписок

```bash
hermes teams-pipeline subscriptions
```

### Обновление подписок, срок действия которых скоро истечёт

```bash
hermes teams-pipeline maintain-subscriptions
hermes teams-pipeline maintain-subscriptions --dry-run
```

### Автоматическое обновление подписок (ОБЯЗАТЕЛЬНО для продакшна)

**Подписки Microsoft Graph истекают не более чем через 72 часа.** Если их никто не обновляет, уведомления о встречах тихо прекращаются после 3 дней, и конвейер выглядит «сломанным». Это основной режим отказа любой интеграции, основанной на Graph.

Тебе НЕОБХОДИМО запускать `maintain-subscriptions` по расписанию. Выбери один из трёх вариантов:

#### Вариант 1: Hermes cron (рекомендовано, если уже используешь шлюз Hermes)

Hermes поставляется со встроенным планировщиком cron. Режим `--no-agent` запускает скрипт как задачу (вместо использования LLM), а `--script` должен указывать на файл в `~/.hermes/scripts/`. Сначала создай скрипт:

```bash
mkdir -p ~/.hermes/scripts
cat > ~/.hermes/scripts/maintain-teams-subscriptions.sh <<'EOF'
#!/usr/bin/env bash
exec hermes teams-pipeline maintain-subscriptions
EOF
chmod +x ~/.hermes/scripts/maintain-teams-subscriptions.sh
```

Затем зарегистрируй cron‑задачу, которая будет запускаться каждые 12 часов (это даёт запас 6× против окна истечения 72 ч):

```bash
hermes cron create "0 */12 * * *" \
  --name "teams-pipeline-maintain-subscriptions" \
  --no-agent \
  --script maintain-teams-subscriptions.sh \
  --deliver local
```

Проверь, что задача зарегистрирована, и посмотри время следующего запуска:

```bash
hermes cron list
hermes cron status        # scheduler status
```

#### Вариант 2: systemd‑таймер (рекомендовано для продакшн‑развёртываний Linux)

Создай файл `/etc/systemd/system/hermes-teams-pipeline-maintain.service`:

```ini
[Unit]
Description=Hermes Teams pipeline subscription maintenance
After=network-online.target

[Service]
Type=oneshot
User=hermes
EnvironmentFile=/etc/hermes/env
ExecStart=/usr/local/bin/hermes teams-pipeline maintain-subscriptions
```

И файл `/etc/systemd/system/hermes-teams-pipeline-maintain.timer`:

```ini
[Unit]
Description=Run Hermes Teams pipeline subscription maintenance every 12 hours

[Timer]
OnBootSec=5min
OnUnitActiveSec=12h
Persistent=true

[Install]
WantedBy=timers.target
```

Включи:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now hermes-teams-pipeline-maintain.timer
systemctl list-timers hermes-teams-pipeline-maintain.timer
```

#### Вариант 3: обычный crontab

```cron
0 */12 * * * /usr/local/bin/hermes teams-pipeline maintain-subscriptions >> /var/log/hermes/teams-pipeline-maintain.log 2>&1
```

Убедись, что в окружении cron присутствуют учётные данные `MSGRAPH_*`. Самый простой способ — добавить `source ~/.hermes/.env` в начало обёрточного скрипта, вызываемого из crontab.

#### Проверка, что обновление работает

После настройки расписания проверь активность обновления после первого запланированного запуска:

```bash
hermes teams-pipeline subscriptions   # should show expirationDateTime advanced
hermes teams-pipeline maintain-subscriptions --dry-run   # should show "0 expiring soon" most of the time
```

Если ты когда‑нибудь увидишь, что веб‑хук Graph «перестал работать» ровно через ≈ 72 часа, это первое, что нужно проверить: действительно ли задача обновления выполнилась?

### Проверка последних задач

```bash
hermes teams-pipeline list
hermes teams-pipeline list --status failed
hermes teams-pipeline show <job-id>
```

### Повторное воспроизведение сохранённой задачи

```bash
hermes teams-pipeline run <job-id>
```

### Пробный запуск получения артефактов встречи

```bash
hermes teams-pipeline fetch --meeting-id <meeting-id>
hermes teams-pipeline fetch --join-web-url "<join-url>"
```

## Рутинный план действий

### После первой настройки

Выполняй последовательно:

```bash
hermes teams-pipeline validate
hermes teams-pipeline token-health --force-refresh
hermes teams-pipeline subscriptions
```

Затем инициируй или дождись реального события встречи и проверь:

```bash
hermes teams-pipeline list
hermes teams-pipeline show <job-id>
```

### Ежедневные или периодические проверки

- запусти `hermes teams-pipeline maintain-subscriptions --dry-run`
- проверь `hermes teams-pipeline list --status failed`
- убедись, что цель доставки в Teams всё ещё правильный чат или канал

### Перед изменением URL веб‑хука или целей доставки

- обнови публичный URL уведомления или конфигурацию цели в Teams
- запусти `hermes teams-pipeline validate`
- обнови или пересоздай затронутые подписки
- убедись, что новые события попадают в ожидаемый приёмник

## Диагностика сбоев

### Не создаются задачи

Проверь:
- включён `msgraph_webhook`
- публичный URL уведомления указывает на `/msgraph/webhook`
- состояние клиента в подписке совпадает с `MSGRAPH_WEBHOOK_CLIENT_STATE`
- подписки всё ещё существуют удалённо и не истекли

### Задачи остаются в состоянии retry или fail до суммирования

Проверь:
- разрешения и доступность транскриптов
- разрешения и доступность записей
- наличие `ffmpeg`, если включён запасной вариант записи
- состояние токена Graph

### Сводки генерируются, но не доставляются в Teams

Проверь:
- `platforms.teams.enabled: true`
- `delivery_mode`
- `incoming_webhook_url` для режима веб‑хука
- `chat_id` или `team_id` + `channel_id` для режима Graph
- конфигурацию аутентификации Teams, если используется публикация через Graph

### Дублирующиеся или неожиданные воспроизведения

Проверь:
- не запускал ли ты вручную повтор задачи с `hermes teams-pipeline run`
- не существует ли уже запись приёмника для этой встречи
- не включил ли ты намеренно путь повторной отправки в локальной конфигурации

## Чек‑лист перед запуском в продакшн

- [ ] Учётные данные Graph присутствуют и корректны
- [ ] `msgraph_webhook` включён и доступен из публичного интернета
- [ ] `MSGRAPH_WEBHOOK_CLIENT_STATE` установлен и совпадает с подписками
- [ ] Создана подписка на транскрипты
- [ ] Создана подписка на записи, если требуется запасной вариант STT
- [ ] `ffmpeg` установлен, если включён запасной вариант записи
- [ ] Настроена и проверена цель исходящей доставки в Teams
- [ ] Синки Notion и Linear настроены только при реальной необходимости
- [ ] `hermes teams-pipeline validate` возвращает ОК‑снимок
- [ ] `hermes teams-pipeline token-health --force-refresh` проходит успешно
- [ ] **`maintain-subscriptions` запланирован** (Hermes cron, systemd‑таймер или crontab — см. [Автоматическое обновление подписок](#automating-subscription-renewal-required-for-production)). Без этого подписки Graph тихо истекают через 72 часа.
- [ ] Реальное сквозное событие встречи создало сохранённую задачу
- [ ] По крайней мере одна сводка достигла целевого приёмника

## Руководство по выбору режима доставки

| Режим               | Когда использовать                               | Компромисс                                   |
|--------------------|--------------------------------------------------|----------------------------------------------|
| `incoming_webhook` | нужен простой постинг в Teams                    | самая простая настройка, меньше контроля     |
| `graph`            | требуется постинг в канал или чат через Graph    | больше контроля, больше аутентификации и конфигурации цели |

## Рабочий лист оператора

Заполни перед развертыванием:

| Пункт                                   | Значение |
|----------------------------------------|----------|
| Публичный URL уведомления               | |
| ID арендатора Graph                    | |
| ID клиента Graph                       | |
| Состояние клиента веб‑хука             | |
| Подписка на ресурс транскриптов        | |
| Подписка на ресурс записей            | |
| Режим доставки в Teams                 | |
| ID чата Teams или команда/канал        | |
| ID базы данных Notion                  | |
| ID команды Linear                      | |
| Переопределение пути хранилища, если есть | |
| Ответственный за ежедневные проверки  | |

## Рабочий лист обзора изменений

Используй перед изменением развертывания:

| Вопрос                                 | Ответ |
|----------------------------------------|-------|
| Меняем ли мы публичный URL веб‑хука?   | |
| Поворачиваем ли мы учётные данные Graph?| |
| Меняем ли мы режим доставки в Teams?   | |
| Переходим ли мы в новый чат или канал Teams? | |
| Нужно ли пересоздать или обновить подписки? | |
| Нужен ли нам свежий сквозной проверочный запуск? | |

## Связанные документы

- [Настройка встреч Teams](/user-guide/messaging/teams-meetings)
- [Настройка бота Microsoft Teams](/user-guide/messaging/teams)