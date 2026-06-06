---
sidebar_position: 3
---

# Налаштування моделей

Hermes використовує два типи слотів моделей:

- **Основна модель** — те, чим агент мислить. Кожне повідомлення користувача, кожен цикл виклику інструменту, кожна потокова відповідь проходять через цю модель.
- **Допоміжні моделі** — менші допоміжні завдання, які агент делегує: стиснення контексту, зір (аналіз зображень), підсумовування веб‑сторінок, оцінка схвалення, маршрутизація інструментів MCP, генерація назви сесії та пошук навичок. Кожна має свій власний слот і може бути перевизначена незалежно.

Ця сторінка охоплює налаштування обох моделей з панелі управління. Якщо ти віддаєш перевагу файлам конфігурації або CLI, переходь до [альтернативних методів](#alternative-methods) внизу.

:::tip Найшвидший шлях: Nous Portal
[Nous Portal](/user-guide/features/tool-gateway) надає понад 300 моделей в рамках однієї підписки. Після чистої інсталяції виконай `hermes setup --portal`, щоб увійти та встановити Nous як твого провайдера однією командою. Перевір, що підключено, за допомогою `hermes portal status`.

- Передплатники Portal також отримують **10 % знижки на провайдерів, що оплачуються токенами**.
:::

:::note `model:` schema — порожній рядок vs. мапа
У новій інсталяції вбудована конфігурація має `model: ""` (порожній рядок‑сентинел, що означає «ще не налаштовано»). Перший раз, коли ти виконуєш `hermes setup` або `hermes model`, цей ключ оновлюється на місці до мапи з підключами `provider`, `default`, `base_url` та `api_mode` — форма, показана на цій сторінці та в [`profiles.md`](./profiles.md) / [`configuration.md`](./configuration.md). Якщо ти коли‑небудь побачиш порожній рядок у `config.yaml`, виконай `hermes model` (або натисни **Change** у панелі) і Hermes запише для тебе словникову форму.
:::
## Сторінка Models

Відкрий панель управління та натисни **Models** у боковій панелі. Ти побачиш два розділи:

1. **Model Settings** — верхня панель, де ти призначаєш моделі до слотів.
2. **Usage analytics** — ранжовані картки, що показують кожну модель, яка запускала сесію у вибраному періоді, з кількістю токенів, вартістю та значками можливостей.

![Models page overview](/img/docs/dashboard-models/overview.png)

Верхня картка — це панель **Model Settings**. Основний рядок завжди показує, яку модель агент запустить для нових сесій. Натисни **Change**, щоб відкрити вибірник.
## Налаштування основної моделі

Натисни **Change** у рядку **Main model**:

![Model picker dialog](/img/docs/dashboard-models/picker-dialog.png)

У вікні вибору два стовпці:

- **Left** — автентифіковані провайдери. Показуються лише провайдери, які ти налаштував (встановлений API‑key, OAuth або визначений як власна кінцева точка). Якщо потрібного провайдера немає, перейди до **Keys** і додай його облікові дані.
- **Right** — підготовлений список моделей для обраного провайдера. Це агентські моделі, які Hermes рекомендує для цього провайдера, а не необроблений дамп `/models` (у OpenRouter він містить 400+ моделей, включаючи TTS, генератори зображень та ранжери).

Введи текст у поле фільтра, щоб звузити пошук за назвою провайдера, slug або ID моделі.

Вибери модель, натисни **Switch**, і Hermes запише її у `~/.hermes/config.yaml` у розділі `model`. **Це застосовується лише до нових сесій** — будь‑яка відкрита вкладка чату продовжує працювати з моделлю, якою вона була запущена. Щоб швидко замінити модель у поточному чаті, використай слеш‑команду `/model` всередині нього.
## Налаштування допоміжних моделей

Натисни **Show auxiliary**, щоб відкрити вісім слотів завдань:

![Auxiliary panel expanded](/img/docs/dashboard-models/auxiliary-expanded.png)

Кожне допоміжне завдання за замовчуванням має `auto` — це означає, що Hermes використовує твою основну модель і для цього завдання. Перевизнач конкретне завдання, коли потрібна дешевша або швидша модель для побічної роботи.

### Типові шаблони перевизначення

| Завдання | Коли перевизначати |
|---|---|
| **Title Gen** | Майже завжди. Модель $0.10/M flash пише назви сесій так само, як Opet. У конфігурації за замовчуванням встановлено `google/gemini-3-flash-preview` на OpenRouter. |
| **Vision** | Коли твоя основна модель не підтримує бачення. Вкажи `google/gemini-2.5-flash` або `gpt-4o-mini`. |
| **Compression** | Коли ти витрачаєш токени на міркування в Opus/M2.7 лише для підсумовування контексту. Швидка чат‑модель виконує це за 1/50 вартості. |
| **Approval** | Для `approval_mode: smart` — швидка/дешевша модель (haiku, flash, gpt-5-mini) вирішує, чи автоматично схвалювати низькоризикові команди. Дорогі моделі тут — марна трата. |
| **Web Extract** | Коли ти часто використовуєш `web_extract`. Та сама логіка, що й у стисненні — підсумовування не потребує міркувань. |
| **Skills Hub** | `hermes skills search` використовує це. Зазвичай підходить `auto`. |
| **MCP** | Маршрутизація інструменту MCP. Зазвичай підходить `auto`. |

### Перевизначення для окремого завдання

Натисни **Change** у будь‑якому рядку допоміжної моделі. Відкриється той самий селектор, та сама поведінка — вибери провайдера + модель, натисни **Switch**. Рядок оновиться і покаже `provider · model` замість `auto (use main model)`.

### Скинути всі налаштування до auto

Якщо ти надто підлаштував параметри і хочеш почати спочатку, натисни **Reset all to auto** у верхній частині розділу допоміжних моделей. Усі слоти повернуться до використання твоєї основної моделі.
## Скорочення «Use as»

Кожна картка моделі на сторінці має випадаючий список **Use as**. Це швидкий шлях — вибираєш модель, яку бачиш у своїй аналітиці, натискаєш **Use as** і призначаєш її у головний слот або будь‑яке конкретне допоміжне завдання одним кліком:

![Use as dropdown](/img/docs/dashboard-models/use-as-dropdown.png)

У випадаючому списку є:

- **Main model** — те саме, що натискання **Change** у головному рядку.
- **All auxiliary tasks** — призначає цю модель усім 8 допоміжним слотам одночасно. Корисно, коли потрібно, щоб усі побічні завдання виконувалися на дешевій flash‑моделі.
- **Individual task options** — Vision, Web Extract, Compression тощо. Поточна модель, призначена для кожного завдання, позначена `current`.

Картки мають бейджі `main` або `aux · <task>`, коли вони зараз призначені до чогось — так ти одразу бачиш, які з твоїх історичних моделей підключені куди.
## Що записується у `config.yaml`

When you save via the dashboard, Hermes writes to `~/.hermes/config.yaml`:

**Головна модель:**
```yaml
model:
  provider: openrouter
  default: anthropic/claude-opus-4.7
  base_url: ''        # cleared on provider switch
  api_mode: chat_completions
```

**Додаткове перевизначення (приклад — vision on gemini-flash):**
```yaml
auxiliary:
  vision:
    provider: openrouter
    model: google/gemini-2.5-flash
    base_url: ''
    api_key: ''
    timeout: 120
    extra_body: {}
    download_timeout: 30
```

**Додаткове в режимі auto (за замовчуванням):**
```yaml
auxiliary:
  compression:
    provider: auto
    model: ''
    base_url: ''
    # ... other fields unchanged
```

`provider: auto` з `model: ''` вказує Hermes використовувати головну модель для цього завдання.
## Коли це набуває сили?

- **CLI** (`hermes chat`): наступний виклик `hermes chat`.
- **Gateway** (Telegram, Discord, Slack тощо): наступна *нова* session. Існуючі session зберігають свою модель. Перезапусти **gateway** (`hermes gateway restart`), якщо хочеш примусово застосувати зміну до всіх session.
- **Dashboard chat tab** (`/chat`): наступний новий PTY. Поточний відкритий чат зберігає свою модель — використай `/model` всередині нього для гарячої заміни.

Зміни ніколи не анулюють кеші підказок у запущених session. Це навмисно: заміна основної моделі всередині session потребує скидання кешу (системна підказка містить модель‑специфічний вміст), і ми залишаємо це лише для явної slash‑команди `/model` у чаті.
## Усунення проблем

### «No authenticated providers» у picker

Hermes показує провайдера лише якщо у нього є дієва **credential**. Перевір **Keys** у боковій панелі — ти маєш бачити один із: API‑ключ, успішний OAuth або власний URL‑endpoint. Якщо потрібного провайдера немає, запусти `hermes setup`, щоб підключити його, або перейди до **Keys** і додай відповідну змінну середовища.

### Основна модель не змінилася у запущеному чаті

Очікувана поведінка. Приладна панель записує `config.yaml`, який читають нові сесії. Поточний відкритий чат — це живий процес агента, який зберігає ту модель, якою був запущений. Використай `/model <name>` у чаті, щоб «гаряче» переключити саме цю сесію.

### Додаткове перевизначення «не спрацювало»

Перевір три речі:

1. **Чи запустив ти нову сесію?** Існуючі чати не перечитують конфіг.
2. **Чи встановлено `provider` не в `auto`?** Якщо поле показує `auto`, завдання все ще використовує твою основну модель. Натисни **Change** і вибери реального провайдера.
3. **Чи провайдер автентифікований?** Якщо ти призначив `minimax` завданню, а у тебе немає MiniMax API‑ключа, це завдання перейде до стандартного провайдера OpenRouter і запише попередження в `agent.log`.

### Я вибрав модель, а Hermes змінив провайдера

На OpenRouter (або будь‑якому агрегаторі) «голі» назви моделей спочатку розв’язуються *всередині* агрегатора. Тому `claude-sonnet-4` на OpenRouter стає `anthropic/claude-sonnet-4.6`, залишаючись під твоєю OpenRouter‑автентифікацією. Але якщо ти ввів `claude-sonnet-4` у власному Anthropic‑автентифікації, воно залишиться `claude-sonnet-4-6`. Якщо бачиш неочікуване переключення провайдера, перевір, чи поточний провайдер відповідає твоїм очікуванням — picker завжди показує поточний основний провайдер у верхній частині діалогу.
## Альтернативні методи

### CLI slash‑команда

У будь‑якій сесії `hermes chat`:

```
/model gpt-5.4 --provider openrouter             # session-only
/model gpt-5.4 --provider openrouter --global    # also persists to config.yaml
```

`--global` робить те саме, що кнопка **Change** на панелі управління, плюс переключає поточну сесію на місці.

### Користувацькі псевдоніми

Визнач свої короткі назви для моделей, які часто використовуєш, а потім застосовуй `/model <alias>` у CLI або будь‑якій платформі обміну повідомленнями. Є два еквівалентних формати — обери той, що підходить твоєму робочому процесу.

**Канонічний (верхній рівень `model_aliases:`)** — повний контроль над провайдером + `base_url`:

```yaml
# ~/.hermes/config.yaml
model_aliases:
  fav:
    model: claude-sonnet-4.6
    provider: anthropic
  grok:
    model: grok-4
    provider: x-ai
```

**Коротка рядкова форма (`model.aliases.<name>: provider/model`)** — зручна в оболонці, бо `hermes config set` записує лише скалярні значення, але не може передати власний `base_url`:

```bash
hermes config set model.aliases.fav anthropic/claude-opus-4.6
hermes config set model.aliases.grok x-ai/grok-4
```

Обидва шляхи передають один і той же завантажувач (`hermes_cli/model_switch.py`). Записи, оголошені в `model_aliases:`, мають пріоритет над записами в `model.aliases:` з тією ж назвою.

Потім `/model fav` або `/model grok` у чаті. Користувацькі псевдоніми перекривають вбудовані короткі назви (`sonnet`, `kimi`, `opus` тощо). Дивись [Custom model aliases](/reference/slash-commands#custom-model-aliases) для повної довідки.

### Підкоманда `hermes model`

```bash
hermes model            # Interactive provider + model picker (the canonical way to switch defaults)
```

`hermes model` проводить тебе через вибір провайдера, автентифікацію (OAuth‑потоки відкривають браузер; провайдери з API‑ключем запитують ключ), а потім вибір конкретної моделі з каталогом провайдера. Вибір записується в `model.provider` та `model.model` у `~/.hermes/config.yaml`.

Щоб перелічити провайдери/моделі без запуску майстра, використай панель управління або REST‑ендпоінти нижче. Щоб подивитися, що CLI фактично використовує зараз: `hermes config get model` та `hermes status`.

### Пряме редагування конфігурації

Відредагуй `~/.hermes/config.yaml` і перезапусти те, що його читає. Дивись [Configuration reference](./configuration.md) для повної схеми.

### REST API

Панель управління використовує три ендпоінти. Корисно для скриптів:

```bash
# List authenticated providers + curated model lists
curl -H "X-Hermes-Session-Token: $TOKEN" http://localhost:PORT/api/model/options

# Read current main + auxiliary assignments
curl -H "X-Hermes-Session-Token: $TOKEN" http://localhost:PORT/api/model/auxiliary

# Set the main model
curl -X POST -H "Content-Type: application/json" -H "X-Hermes-Session-Token: $TOKEN" \
  -d '{"scope":"main","provider":"openrouter","model":"anthropic/claude-opus-4.7"}' \
  http://localhost:PORT/api/model/set

# Override a single auxiliary task
curl -X POST -H "Content-Type: application/json" -H "X-Hermes-Session-Token: $TOKEN" \
  -d '{"scope":"auxiliary","task":"vision","provider":"openrouter","model":"google/gemini-2.5-flash"}' \
  http://localhost:PORT/api/model/set

# Assign one model to every auxiliary task
curl -X POST -H "Content-Type: application/json" -H "X-Hermes-Session-Token: $TOKEN" \
  -d '{"scope":"auxiliary","task":"","provider":"openrouter","model":"google/gemini-2.5-flash"}' \
  http://localhost:PORT/api/model/set

# Reset all auxiliary tasks to auto
curl -X POST -H "Content-Type: application/json" -H "X-Hermes-Session-Token: $TOKEN" \
  -d '{"scope":"auxiliary","task":"__reset__","provider":"","model":""}' \
  http://localhost:PORT/api/model/set
```

Токен сесії ін’єкціюється в HTML панелі управління під час запуску і оновлюється при кожному перезапуску сервера. Отримай його з інструментів розробника браузера (`window.__HERMES_SESSION_TOKEN__`), якщо пишеш скрипт проти запущеної панелі управління.