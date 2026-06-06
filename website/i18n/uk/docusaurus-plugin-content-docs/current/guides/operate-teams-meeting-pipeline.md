---
title: "Керувати конвеєром Teams Meeting"
description: "Runbook, чек‑лист запуску та робочий лист оператора для конвеєра зустрічей Microsoft Teams"
---

# Операція конвеєра Teams Meeting

Використовуй цей посібник після того, як вже ввімкнув функцію в [Teams Meetings](/user-guide/messaging/teams-meetings).

На цій сторінці розглядаються:
- CLI‑потоки оператора
- рутинне обслуговування підписок
- діагностика збоїв
- перевірки перед запуском
- робочий лист розгортання

## Основні команди оператора

### Перевірка знімка конфігурації

```bash
hermes teams-pipeline validate
```

Використовуй це спочатку після будь‑якої зміни конфігурації.

### Перевірка стану токену

```bash
hermes teams-pipeline token-health
hermes teams-pipeline token-health --force-refresh
```

Використовуй `--force-refresh`, коли підозрюєш застарілий стан автентифікації.

### Перевірка підписок

```bash
hermes teams-pipeline subscriptions
```

### Оновлення підписок, що скоро закінчуються

```bash
hermes teams-pipeline maintain-subscriptions
hermes teams-pipeline maintain-subscriptions --dry-run
```

### Автоматизація оновлення підписок (ОБОВʼЯЗКОВО для продакшну)

**Підписки Microsoft Graph закінчуються не пізніше ніж за 72 години.** Якщо їх ніщо не оновлює, сповіщення про зустрічі тихо припиняються після 3 днів, і конвеєр виглядає «зламаним». Це головний режим операційного збою для будь‑якої інтеграції, що базується на Graph.

ТИ ПОВИНЕН запускати `maintain-subscriptions` за розкладом. Вибери один із трьох варіантів:

#### Варіант 1: Hermes cron (рекомендовано, якщо вже працюєш з шлюзом Hermes)

Hermes постачається зі вбудованим планувальником cron. Режим `--no-agent` запускає скрипт як завдання (замість використання LLM), а `--script` має вказувати на файл у `~/.hermes/scripts/`. Спочатку створи скрипт:

```bash
mkdir -p ~/.hermes/scripts
cat > ~/.hermes/scripts/maintain-teams-subscriptions.sh <<'EOF'
#!/usr/bin/env bash
exec hermes teams-pipeline maintain-subscriptions
EOF
chmod +x ~/.hermes/scripts/maintain-teams-subscriptions.sh
```

Потім зареєструй cron‑завдання лише зі скриптом, яке виконується кожні 12 годин (дає 6‑х кратний запас проти 72‑годинного вікна закінчення):

```bash
hermes cron create "0 */12 * * *" \
  --name "teams-pipeline-maintain-subscriptions" \
  --no-agent \
  --script maintain-teams-subscriptions.sh \
  --deliver local
```

Перевір, що завдання зареєстровано, і подивись час наступного запуску:

```bash
hermes cron list
hermes cron status        # scheduler status
```

#### Варіант 2: systemd timer (рекомендовано для продакшн‑розгортань Linux)

Створи `/etc/systemd/system/hermes-teams-pipeline-maintain.service`:

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

І `/etc/systemd/system/hermes-teams-pipeline-maintain.timer`:

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

Увімкни:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now hermes-teams-pipeline-maintain.timer
systemctl list-timers hermes-teams-pipeline-maintain.timer
```

#### Варіант 3: Прямий crontab

```cron
0 */12 * * * /usr/local/bin/hermes teams-pipeline maintain-subscriptions >> /var/log/hermes/teams-pipeline-maintain.log 2>&1
```

Переконайся, що в середовищі cron присутні облікові дані `MSGRAPH_*`. Найпростіше виправлення: підключити `~/.hermes/.env` на початку обгорткового скрипту, який викликає crontab.

#### Перевірка, що оновлення працює

Після налаштування розкладу перевір активність оновлення після першого запланованого запуску:

```bash
hermes teams-pipeline subscriptions   # should show expirationDateTime advanced
hermes teams-pipeline maintain-subscriptions --dry-run   # should show "0 expiring soon" most of the time
```

Якщо коли‑небудь бачиш, що твій Graph webhook таємно «перестає працювати» саме через ~72 години, це перше, що треба перевірити: чи дійсно запущено завдання оновлення?

### Перевірка останніх завдань

```bash
hermes teams-pipeline list
hermes teams-pipeline list --status failed
hermes teams-pipeline show <job-id>
```

### Повторне відтворення збереженого завдання

```bash
hermes teams-pipeline run <job-id>
```

### Сухий запуск отримання артефактів зустрічі

```bash
hermes teams-pipeline fetch --meeting-id <meeting-id>
hermes teams-pipeline fetch --join-web-url "<join-url>"
```

## Рутинний Runbook

### Після першого налаштування

Виконуй у зазначеному порядку:

```bash
hermes teams-pipeline validate
hermes teams-pipeline token-health --force-refresh
hermes teams-pipeline subscriptions
```

Потім ініціюй або дочекайся реальної події зустрічі та підтверди:

```bash
hermes teams-pipeline list
hermes teams-pipeline show <job-id>
```

### Щоденні або періодичні перевірки

- запусти `hermes teams-pipeline maintain-subscriptions --dry-run`
- перевір `hermes teams-pipeline list --status failed`
- переконайся, що ціль доставки в Teams все ще правильний чат або канал

### Перед зміною URL‑ів webhook або цілей доставки

- онови публічний URL сповіщення або конфігурацію цілі Teams
- запусти `hermes teams-pipeline validate`
- онови або створи заново відповідні підписки
- підтвердь, що нові події потрапляють у очікуваний сховищ

## Діагностика збоїв

### Не створюються жодні завдання

Перевір:
- `msgraph_webhook` увімкнено
- публічний URL сповіщення вказує на `/msgraph/webhook`
- стан клієнта у підписці відповідає `MSGRAPH_WEBHOOK_CLIENT_STATE`
- підписки ще існують віддалено і не прострочені

### Завдання залишаються в стані retry або fail до підсумовування

Перевір:
- дозволи та доступність транскрипту
- дозволи та доступність запису
- доступність `ffmpeg`, якщо включено резервний запис
- стан токену Graph

### Підсумки створюються, але не доставляються в Teams

Перевір:
- `platforms.teams.enabled: true`
- `delivery_mode`
- `incoming_webhook_url` для режиму webhook
- `chat_id` або `team_id` плюс `channel_id` для режиму Graph
- конфігурацію автентифікації Teams, якщо використовується публікація через Graph

### Дублювання або неочікувані повтори

Перевір:
- чи ти вручну не відтворив завдання за допомогою `hermes teams-pipeline run`
- чи запис у сховищі вже існує для цієї зустрічі
- чи навмисно не ввімкнув шлях повторної відправки у локальній конфігурації

## Чек‑лист перед запуском у продакшн

- [ ] Облікові дані Graph присутні та правильні
- [ ] `msgraph_webhook` увімкнено та доступно з публічного інтернету
- [ ] `MSGRAPH_WEBHOOK_CLIENT_STATE` встановлено і відповідає підпискам
- [ ] Підписка на транскрипт створена
- [ ] Підписка на запис створена, якщо потрібен резервний STT
- [ ] `ffmpeg` встановлено, якщо включено резервний запис
- [ ] Ціль вихідної доставки Teams налаштована та перевірена
- [ ] Сховища Notion та Linear налаштовані лише за потреби
- [ ] `hermes teams-pipeline validate` повертає ОК‑знімок
- [ ] `hermes teams-pipeline token-health --force-refresh` успішний
- [ ] **`maintain-subscriptions` заплановано** (Hermes cron, systemd timer або crontab — див. [Автоматизація оновлення підписок](#automating-subscription-renewal-required-for-production)). Без цього підписки Graph тихо прострочуються протягом 72 годин.
- [ ] Реальна end-to-end подія зустрічі створила збережене завдання
- [ ] Принаймні один підсумок досягнув запланованого сховища доставки

## Посібник з вибору режиму доставки

| Режим | Коли використовувати | Компроміс |
|------|----------------------|-----------|
| `incoming_webhook` | потрібне лише просте постинг у Teams | найпростіше налаштування, менше контролю |
| `graph` | потрібен постинг у канал або чат через Graph | більше контролю, більше автентифікації та налаштувань цілі |

## Робочий лист оператора

Заповни перед розгортанням:

| Пункт | Значення |
|------|----------|
| Публічний URL сповіщення | |
| Graph tenant ID | |
| Graph client ID | |
| Webhook client state | |
| Підписка на ресурс транскрипту | |
| Підписка на ресурс запису | |
| Режим доставки Teams | |
| Teams chat ID або team/channel | |
| Notion database ID | |
| Linear team ID | |
| Перевизначення шляху сховища, якщо є | |
| Власник для щоденних перевірок | |

## Робочий лист огляду змін

Використай перед зміною розгортання:

| Питання | Відповідь |
|----------|-----------|
| Чи змінюємо публічний URL webhook? | |
| Чи оновлюємо облікові дані Graph? | |
| Чи змінюємо режим доставки Teams? | |
| Чи переходимо до нового чату або каналу Teams? | |
| Чи потрібно відтворити або оновити підписки? | |
| Чи потрібен новий end-to-end верифікаційний запуск? | |

## Пов’язані документи

- [Налаштування Teams Meetings](/user-guide/messaging/teams-meetings)
- [Налаштування бота Microsoft Teams](/user-guide/messaging/teams)