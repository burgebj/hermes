---
title: Home Assistant
description: Управляй своим умным домом с Hermes Agent через интеграцию Home Assistant.
sidebar_label: Home Assistant
sidebar_position: 5
---

# Интеграция Home Assistant

Hermes Agent интегрируется с [Home Assistant](https://www.home-assistant.io/) двумя способами:

1. **Платформа шлюза** — подписывается на изменения состояний в реальном времени через WebSocket и реагирует на события
2. **Инструменты умного дома** — четыре инструмента, вызываемых LLM, для запросов и управления устройствами через REST API

## Настройка

### 1. Создать долгоживущий токен доступа

1. Открой свой экземпляр Home Assistant
2. Перейди в **Profile** (кликни своё имя в боковой панели)
3. Прокрути до **Long-Lived Access Tokens**
4. Нажми **Create Token**, дай ему имя, например «Hermes Agent»
5. Скопируй токен

### 2. Настроить переменные окружения

```bash
# Add to ~/.hermes/.env

# Required: your Long-Lived Access Token
HASS_TOKEN=your-long-lived-access-token

# Optional: HA URL (default: http://homeassistant.local:8123)
HASS_URL=http://192.168.1.100:8123
```

:::info
Набор инструментов `homeassistant` автоматически включается, когда установлен `HASS_TOKEN`. И платформа шлюза, и инструменты управления устройствами активируются с помощью этого единственного токена.
:::

### 3. Запустить шлюз

```bash
hermes gateway
```

Home Assistant появится как подключённая платформа рядом с другими платформами обмена сообщениями (Telegram, Discord и т.д.).

## Доступные инструменты

Hermes Agent регистрирует четыре инструмента для управления умным домом:

### `ha_list_entities`

Список сущностей Home Assistant, при желании отфильтрованных по домену или зоне.

**Параметры:**
- `domain` *(optional)* — Фильтр по домену сущности: `light`, `switch`, `climate`, `sensor`, `binary_sensor`, `cover`, `fan`, `media_player` и др.
- `area` *(optional)* — Фильтр по названию зоны/комнаты (сравнивается с дружественными именами): `living room`, `kitchen`, `bedroom` и др.

**Пример:**
```
List all lights in the living room
```

Возвращает ID сущностей, их состояния и дружественные имена.

### `ha_get_state`

Получить подробное состояние одной сущности, включая все атрибуты (яркость, цвет, заданная температура, показания датчиков и т.д.).

**Параметры:**
- `entity_id` *(required)* — Сущность для запроса, например `light.living_room`, `climate.thermostat`, `sensor.temperature`

**Пример:**
```
What's the current state of climate.thermostat?
```

Возвращает: состояние, все атрибуты, метки времени последнего изменения/обновления.

### `ha_list_services`

Список доступных сервисов (действий) для управления устройствами. Показывает, какие действия можно выполнить для каждого типа устройства и какие параметры они принимают.

**Параметры:**
- `domain` *(optional)* — Фильтр по домену, например `light`, `climate`, `switch`

**Пример:**
```
What services are available for climate devices?
```

### `ha_call_service`

Вызов сервиса Home Assistant для управления устройством.

**Параметры:**
- `domain` *(required)* — Домен сервиса: `light`, `switch`, `climate`, `cover`, `media_player`, `fan`, `scene`, `script`
- `service` *(required)* — Имя сервиса: `turn_on`, `turn_off`, `toggle`, `set_temperature`, `set_hvac_mode`, `open_cover`, `close_cover`, `set_volume_level`
- `entity_id` *(optional)* — Целевая сущность, например `light.living_room`
- `data` *(optional)* — Дополнительные параметры в виде JSON‑объекта

**Примеры:**

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

## Платформа шлюза: события в реальном времени

Адаптер шлюза Home Assistant подключается через WebSocket и подписывается на события `state_changed`. Когда состояние устройства меняется и соответствует твоим фильтрам, оно пересылается агенту в виде сообщения.

### Фильтрация событий

:::warning Required Configuration
По умолчанию **никакие события не пересылаются**. Нужно настроить хотя бы один из параметров `watch_domains`, `watch_entities` или `watch_all`, чтобы получать события. Без фильтров при запуске выводится предупреждение, а все изменения состояний тихо отбрасываются.
:::

Настрой, какие события видит агент, в `~/.hermes/config.yaml` в разделе `extra` платформы Home Assistant:

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
|--------|---------|-------------|
| `watch_domains` | *(none)* | Следить только за этими доменами сущностей (например, `climate`, `light`, `binary_sensor`) |
| `watch_entities` | *(none)* | Следить только за этими конкретными ID сущностей |
| `watch_all` | `false` | Установи `true`, чтобы получать **все** изменения состояний (не рекомендуется для большинства конфигураций) |
| `ignore_entities` | *(none)* | Всегда игнорировать эти сущности (применяется до фильтров доменов/сущностей) |
| `cooldown_seconds` | `30` | Минимальное время в секундах между событиями одной и той же сущности |

:::tip
Начни с узкого набора доменов — `climate`, `binary_sensor` и `alarm_control_panel` покрывают большинство полезных автоматизаций. Добавляй остальные по мере необходимости. Используй `ignore_entities`, чтобы подавлять шумные датчики, такие как температура CPU или счётчики времени работы.
:::

### Форматирование событий

Изменения состояний форматируются в человекочитаемые сообщения в зависимости от домена:

| Domain | Format |
|--------|--------|
| `climate` | "HVAC mode changed from 'off' to 'heat' (current: 21, target: 23)" |
| `sensor` | "changed from 21°C to 22°C" |
| `binary_sensor` | "triggered" / "cleared" |
| `light`, `switch`, `fan` | "turned on" / "turned off" |
| `alarm_control_panel` | "alarm state changed from 'armed_away' to 'triggered'" |
| *(other)* | "changed from 'old' to 'new'" |

### Ответы агента

Исходящие сообщения агента доставляются как **постоянные уведомления Home Assistant** (через `persistent_notification.create`). Они появляются в панели уведомлений HA с заголовком «Hermes Agent».

### Управление соединением

- **WebSocket** с 30‑секундным heartbeat для событий в реальном времени
- **Автоматическое повторное подключение** с экспоненциальным откатом: 5 s → 10 s → 30 s → 60 s
- **REST API** для исходящих уведомлений (отдельная сессия, чтобы не конфликтовать с WebSocket)
- **Авторизация** — события HA всегда авторизованы (список разрешённых пользователей не нужен, так как `HASS_TOKEN` аутентифицирует соединение)

## Безопасность

Инструменты Home Assistant применяют ограничения безопасности:

:::warning Blocked Domains
Следующие домены сервисов **заблокированы**, чтобы предотвратить произвольное выполнение кода на хосте HA:

- `shell_command` — произвольные shell‑команды
- `command_line` — датчики/переключатели, выполняющие команды
- `python_script` — выполнение скриптов Python
- `pyscript` — более широкая интеграция скриптов
- `hassio` — управление аддонами, выключение/перезагрузка хоста
- `rest_command` — HTTP‑запросы с сервера HA (вектор SSRF)

Попытка вызвать сервисы из этих доменов вернёт ошибку.
:::

ID сущностей проверяются по шаблону `^[a-z_][a-z0-9_]*\.[a-z0-9_]+$`, чтобы предотвратить инъекции.

## Примеры автоматизаций

### Утренний ритуал

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

### Проверка безопасности

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

### Реактивная автоматизация (через события шлюза)

Когда подключён как платформа шлюза, агент может реагировать на события:

```
[Home Assistant] Front Door: triggered (was cleared)

Agent automatically:
1. ha_get_state(entity_id="binary_sensor.front_door")
2. ha_call_service(domain="light", service="turn_on",
     entity_id="light.hallway")
3. Sends notification: "Front door opened. Hallway lights turned on."
```

## Устранение неполадок

**Переменные окружения не подхватываются.**
Адаптер читает учётные данные из `~/.hermes/.env` (автоматически объединяется при запуске) или из `config.yaml`. Убедись, что файл находится в домашней директории активного профиля Hermes и что вокруг URL/токена нет лишних кавычек. Перезапусти шлюз после правок — изменения переменных применяются только при старте процесса.

**`conversation entity not found` / агент не отвечает.**
API разговоров Home Assistant требует настроенного *Assist*‑агента. В HA открой **Settings → Voice assistants → Add assistant** и запиши полученный ID сущности (выглядит как `conversation.home_assistant` или `conversation.openai_<name>`). Укажи этот ID в настройке адаптера `conversation_entity`; значение по умолчанию может отсутствовать в твоей инсталляции.

**REST‑аутентификация не проходит (`401 Unauthorized`).**
Токен должен быть *Long-Lived Access Token*, созданный на странице профиля пользователя HA (**Profile → Security → Long-lived access tokens**). Краткоживущие токены UI не работают. Также проверь, что базовый URL включает схему и порт (например, `http://homeassistant.local:8123`) и доступен с хоста, где запущен Hermes — команда `curl -H "Authorization: Bearer <token>" <url>/api/` должна вернуть `{"message": "API running."}`.