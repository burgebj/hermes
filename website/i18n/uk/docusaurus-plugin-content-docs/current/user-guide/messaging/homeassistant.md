---
title: Домашній помічник
description: Керуй своїм розумним будинком за допомогою Hermes Agent через інтеграцію Home Assistant.
sidebar_label: Home Assistant
sidebar_position: 5
---

# Home Assistant Integration

Hermes Agent інтегрується з [Home Assistant](https://www.home-assistant.io/) двома способами:

1. **Платформа шлюзу** — підписується на зміни стану в реальному часі через WebSocket і реагує на події
2. **Інструменти розумного будинку** — чотири інструменти, доступні для виклику LLM, які дозволяють запитувати та керувати пристроями через REST API

## Налаштування

### 1. Створити Long‑Lived Access Token

1. Відкрий свою інстанцію Home Assistant
2. Перейди до **Профіль** (клацни на своє ім’я у боковій панелі)
3. Прокрути до **Long‑Lived Access Tokens**
4. Натисни **Create Token**, дай йому назву, наприклад «Hermes Agent»
5. Скопіюй токен

### 2. Налаштувати змінні середовища

```bash
# Add to ~/.hermes/.env

# Required: your Long-Lived Access Token
HASS_TOKEN=your-long-lived-access-token

# Optional: HA URL (default: http://homeassistant.local:8123)
HASS_URL=http://192.168.1.100:8123
```

:::info
The `homeassistant` toolset is automatically enabled when `HASS_TOKEN` is set. Both the gateway platform and the device control tools activate from this single token.
:::

### 3. Запустити шлюз

```bash
hermes gateway
```

Home Assistant з’явиться як підключена платформа поряд з іншими платформами обміну повідомленнями (Telegram, Discord тощо).

## Доступні інструменти

Hermes Agent реєструє чотири інструменти для керування розумним будинком:

### `ha_list_entities`

Перелік сутностей Home Assistant, за потреби відфільтрованих за доменом або областю.

**Parameters:**
- `domain` *(optional)* — Фільтр за доменом сутності: `light`, `switch`, `climate`, `sensor`, `binary_sensor`, `cover`, `fan`, `media_player` тощо.
- `area` *(optional)* — Фільтр за назвою області/кімнати (збігається з дружніми іменами): `living room`, `kitchen`, `bedroom` тощо.

**Example:**
```
List all lights in the living room
```

Повертає ідентифікатори сутностей, їх стани та дружні імена.

### `ha_get_state`

Отримати докладний стан однієї сутності, включаючи всі атрибути (яскравість, колір, встановлену температуру, показники датчиків тощо).

**Parameters:**
- `entity_id` *(required)* — Сутність, яку треба запитати, напр., `light.living_room`, `climate.thermostat`, `sensor.temperature`

**Example:**
```
What's the current state of climate.thermostat?
```

Повертає: стан, всі атрибути, часові мітки останньої зміни/оновлення.

### `ha_list_services`

Перелік доступних сервісів (дій) для керування пристроями. Показує, які дії можна виконати для кожного типу пристрою та які параметри вони приймають.

**Parameters:**
- `domain` *(optional)* — Фільтр за доменом, напр., `light`, `climate`, `switch`

**Example:**
```
What services are available for climate devices?
```

### `ha_call_service`

Виклик сервісу Home Assistant для керування пристроєм.

**Parameters:**
- `domain` *(required)* — Домен сервісу: `light`, `switch`, `climate`, `cover`, `media_player`, `fan`, `scene`, `script`
- `service` *(required)* — Назва сервісу: `turn_on`, `turn_off`, `toggle`, `set_temperature`, `set_hvac_mode`, `open_cover`, `close_cover`, `set_volume_level`
- `entity_id` *(optional)* — Цільова сутність, напр., `light.living_room`
- `data` *(optional)* — Додаткові параметри у вигляді JSON‑об’єкта

**Examples:**

```
Turn on the living room lights
→ ha_call_service(domain="light", service="turn_on", entity_id="light.living_room")
```

```
Set the thermostat to 22 degrees in heat mode
→ ha_call_service(domain="climate", service="set_temperature",
    entity_id="climate.thermostat", data={"temperature": 22, "hvac_mode": "heat"})
```

```
Set living room lights to blue at 50% brightness
→ ha_call_service(domain="light", service="turn_on",
    entity_id="light.living_room", data={"brightness": 128, "color_name": "blue"})
```

## Платформа шлюзу: події в реальному часі

Адаптер платформи шлюзу Home Assistant підключається через WebSocket і підписується на події `state_changed`. Коли стан пристрою змінюється і відповідає твоїм фільтрам, він пересилається агенту у вигляді повідомлення.

### Фільтрація подій

:::warning Required Configuration
За замовчуванням **жодні події не пересилаються**. Потрібно налаштувати хоча б один із параметрів `watch_domains`, `watch_entities` або `watch_all`, щоб отримувати події. Без фільтрів при запуску виводиться попередження, а всі зміни стану просто ігноруються.
:::

Налаштуй, які події агент бачить, у `~/.hermes/config.yaml` у розділі `extra` платформи Home Assistant:

```yaml
platforms:
  homeassistant:
    enabled: true
    extra:
      watch_domains:
        - climate
        - binary_sensor
        - alarm_control_panel
        - light
      watch_entities:
        - sensor.front_door_battery
      ignore_entities:
        - sensor.uptime
        - sensor.cpu_usage
        - sensor.memory_usage
      cooldown_seconds: 30
```

| Setting | Default | Description |
|---------|---------|-------------|
| `watch_domains` | *(none)* | Слідкувати лише за цими доменами сутностей (наприклад, `climate`, `light`, `binary_sensor`) |
| `watch_entities` | *(none)* | Слідкувати лише за вказаними ідентифікаторами сутностей |
| `watch_all` | `false` | Встановити `true`, щоб отримувати **всі** зміни стану (не рекомендовано для більшості налаштувань) |
| `ignore_entities` | *(none)* | Завжди ігнорувати ці сутності (застосовується перед фільтрами домену/сутності) |
| `cooldown_seconds` | `30` | Мінімальна кількість секунд між подіями для однієї сутності |

:::tip
Почни з вузького набору доменів — `climate`, `binary_sensor` і `alarm_control_panel` охоплюють найбільш корисні автоматизації. Додавай інші за потреби. Використовуй `ignore_entities`, щоб придушити шумні датчики, наприклад, температуру CPU чи лічильники часу роботи.
:::

### Форматування подій

Зміни стану форматуються у зрозумілі повідомлення залежно від домену:

| Domain | Format |
|--------|--------|
| `climate` | "HVAC mode changed from 'off' to 'heat' (current: 21, target: 23)" |
| `sensor` | "changed from 21°C to 22°C" |
| `binary_sensor` | "triggered" / "cleared" |
| `light`, `switch`, `fan` | "turned on" / "turned off" |
| `alarm_control_panel` | "alarm state changed from 'armed_away' to 'triggered'" |
| *(other)* | "changed from 'old' to 'new'" |

### Відповіді агента

Вихідні повідомлення агента надсилаються як **постійні сповіщення Home Assistant** (через `persistent_notification.create`). Вони з’являються у панелі сповіщень HA з заголовком «Hermes Agent».

### Керування з’єднанням

- **WebSocket** з 30‑секундним heartbeat для подій у реальному часі
- **Automatic reconnection** з backoff: 5 s → 10 s → 30 s → 60 s
- **REST API** для вихідних сповіщень (окремий сеанс, щоб уникнути конфліктів WebSocket)
- **Authorization** — події HA завжди авторизовані (не потрібен allowlist користувачів, оскільки `HASS_TOKEN` автентифікує з’єднання)

## Безпека

Інструменти Home Assistant застосовують обмеження безпеки:

:::warning Blocked Domains
Наступні домени сервісів **заблоковані**, щоб запобігти виконанню довільного коду на хості HA:

- `shell_command` — довільні shell‑команди
- `command_line` — датчики/перемикачі, що виконують команди
- `python_script` — виконання скриптів Python
- `pyscript` — розширена інтеграція скриптів
- `hassio` — керування аддонами, вимкнення/перезавантаження хоста
- `rest_command` — HTTP‑запити з сервера HA (вектор SSRF)

Спроба викликати сервіси в цих доменах поверне помилку.
:::

Ідентифікатори сутностей перевіряються за шаблоном `^[a-z_][a-z0-9_]*\.[a-z0-9_]+$`, щоб запобігти ін’єкціям.

## Приклади автоматизацій

### Morning Routine

```
User: Start my morning routine

Agent:
1. ha_call_service(domain="light", service="turn_on",
     entity_id="light.bedroom", data={"brightness": 128})
2. ha_call_service(domain="climate", service="set_temperature",
     entity_id="climate.thermostat", data={"temperature": 22})
3. ha_call_service(domain="media_player", service="turn_on",
     entity_id="media_player.kitchen_speaker")
```

### Security Check

```
User: Is the house secure?

Agent:
1. ha_list_entities(domain="binary_sensor")
     → checks door/window sensors
2. ha_get_state(entity_id="alarm_control_panel.home")
     → checks alarm status
3. ha_list_entities(domain="lock")
     → checks lock states
4. Reports: "All doors closed, alarm is armed_away, all locks engaged."
```

### Reactive Automation (via Gateway Events)

Коли підключено як платформа шлюзу, агент може реагувати на події:

```
[Home Assistant] Front Door: triggered (was cleared)

Agent automatically:
1. ha_get_state(entity_id="binary_sensor.front_door")
2. ha_call_service(domain="light", service="turn_on",
     entity_id="light.hallway")
3. Sends notification: "Front door opened. Hallway lights turned on."
```

## Устранення проблем

**Environment variables not picked up.**
Адаптер читає облікові дані з `~/.hermes/.env` (автоматично злиті під час запуску) або з `config.yaml`. Переконайся, що файл знаходиться у домашній теці активного профілю Hermes і що навколо URL/токену немає зайвих лапок. Перезапусти шлюз після правок — зміни змінних середовища застосовуються лише під час старту процесу.

**`conversation entity not found` / agent never replies.**
API розмов Home Assistant вимагає налаштованого *Assist* агента розмов. У HA відкрий **Settings → Voice assistants → Add assistant** і запиши отриманий ідентифікатор сутності (виглядає як `conversation.home_assistant` або `conversation.openai_<name>`). Вкажи цей ідентифікатор у параметрі `conversation_entity` адаптера; за замовчуванням його може не бути у твоїй інстанції.

**REST auth failing (`401 Unauthorized`).**
Токен має бути *Long‑Lived Access Token*, створений на сторінці профілю користувача HA (**Profile → Security → Long‑lived access tokens**). Токени короткочасних UI‑сесій не працюватимуть. Також переконайся, що базовий URL містить схему та порт (наприклад, `http://homeassistant.local:8123`) і доступний з хоста, на якому працює Hermes — `curl -H "Authorization: Bearer <token>" <url>/api/` має повернути `{"message": "API running."}`.