---
title: Codex App-Server Runtime (опціонально)
sidebar_label: Codex App-Server Runtime
---

# Codex App-Server Runtime

Hermes може за бажанням передавати `openai/*` і `openai-codex/*` у [Codex CLI app-server](https://github.com/openai/codex) замість запуску власного циклу інструментів. Коли це увімкнено, термінальні команди, редагування файлів, пісочниця та виклики інструменту MCP виконуються всередині середовища виконання Codex — Hermes стає оболонкою навколо нього (база даних сесій, slash‑команди, шлюз, пам'ять та огляд навичок).

Це **лише за згодою**. Типова поведінка Hermes не змінюється, доки ти не перемкнеш прапорець. Hermes ніколи автоматично не перенаправляє тебе на це середовище виконання.

:::tip
Не використовуєш OpenAI Codex? `hermes setup --portal` налаштовує бекенд без Codex з Claude/Gemini/тощо в один крок. Дивись [Nous Portal](/integrations/nous-portal).
:::
## Чому

- Запуск агента OpenAI працює на твоїй **підписці ChatGPT** (не потрібен API‑ключ), використовуючи той самий процес автентифікації, що й у `Codex CLI`.
- Використовуй **власний набір інструментів та пісочницю Codex** — `shell` для терміналу/читання/запису/пошуку, `apply_patch` для структурованих правок, `update_plan` для планування, все працює всередині пісочниці seatbelt/landlock.
- **Рідні плагіни Codex** — Linear, GitHub, Gmail, Calendar, Canva тощо — встановлені через `codex plugin` автоматично мігруються та активні у твоїй сесії Hermes.
- **Багатші інструменти Hermes** — web_search, web_extract, автоматизація браузера, vision, генерація зображень, skills та TTS працюють через зворотний виклик MCP. Codex викликає Hermes для інструментів, яких у ньому немає.
- **Пам'ять і підказки навичок продовжують працювати** — події Codex проєктуються у форму повідомлень Hermes, тож цикл самонавчання бачить звичайний транскрипт.
## Які інструменти фактично має модель

Це та частина, яку більшість користувачів хочуть знати одразу. Коли цей runtime увімкнено, модель, що виконує твій хід, має три незалежні джерела інструментів:

### 1. Вбудований набір інструментів Codex (завжди увімкнено)

Вони постачаються разом з `codex app-server` — без участі Hermes, без MCP, без плагінів. Усі п’ять доступні з моменту старту runtime:

- **`shell`** — виконує довільні shell‑команди всередині пісочниці. Так модель читає файли (`cat`, `head`, `tail`), записує їх (`echo > foo`, heredocs), шукає їх (`find`, `rg`, `grep`), навігує по каталогах (`ls`, `cd`), запускає збірки, керує процесами та робить усе, що ти робив би в bash.
- **`apply_patch`** — застосовує структурований багатофайловий diff у форматі патчів Codex. Модель використовує його для нетривіальних правок коду (додавання функції, рефакторинг у кількох файлах); shell‑heredocs залишаються доступними для одноразових записів.
- **`update_plan`** — внутрішній трекер todo / плану Codex. Еквівалент інструменту Hermes `todo`, але керується повністю всередині runtime Codex.
- **`view_image`** — завантажує локальний файл зображення у розмову, щоб модель могла його бачити.
- **`web_search`** — Codex має власний вбудований веб‑пошук, коли він налаштований. Hermes також експонує `web_search` (на базі Firecrawl) через колбек нижче; модель обирає той, який їй зручніше.

Отже **будь‑що, що ти робиш у терміналі — читання/запис/пошук/знаходження/запуск — Codex робить нативно**. Профіль пісочниці (`:workspace` за замовчуванням, коли ти вмикаєш runtime) контролює, що можна записувати.

### 2. Нативні плагіни Codex (автоматично мігруються з твоєї інсталяції `codex plugin`)

Коли ти вмикаєш runtime, Hermes запитує у Codex RPC `plugin/list` і записує запис `[plugins."<name>@openai-curated"]` для кожного плагіну, який ти встановив. Самі плагіни керуються Codex і авторизуються один раз через UI Codex.

Приклади (ті, що OpenClaw‑тред позначив як «варті YouTube‑відео»):

- **Linear** — знаходити/оновлювати задачі
- **GitHub** — шукати код, переглядати PR, коментувати
- **Gmail** — читати/надсилати листи
- **Google Calendar** — створювати/знаходити події
- **Outlook calendar/email** — та ж функціональність через конектор Microsoft
- **Canva** — генерація дизайну
- …будь‑що інше, що ти встановив через `codex plugin marketplace add openai-curated` + `codex plugin install ...`

Що НЕ мігрується:
- Плагіни, які ти ще не встановив — спочатку встанови їх у Codex.
- Записи маркетплейсу ChatGPT app (`app/list`) — вони вже активовані в Codex завдяки твоїй автентифікації облікового запису.

### 3. Колбек інструментів Hermes (сервер MCP, зареєстрований у `~/.codex/config.toml`)

Hermes реєструє себе як сервер MCP, щоб Codex міг викликати інструменти, які не входять до його базового набору. Доступні через колбек:

- **`web_search`** / **`web_extract`** — на базі Firecrawl; зазвичай чистіші, ніж скрапінг для структурованого контенту.
- **`browser_navigate` / `browser_click` / `browser_type` / `browser_press` / `browser_snapshot` / `browser_scroll` / `browser_back` / `browser_get_images` / `browser_console` / `browser_vision`** — повна автоматизація браузера через Camofox або Browserbase.
- **`vision_analyze`** — виклик окремої vision‑моделі для аналізу зображення (відрізняється від `view_image` Codex, який лише завантажує його у розмову).
- **`image_generate`** — генерація зображень через ланцюжок плагінів Hermes `image_gen`.
- **`skill_view` / `skills_list`** — читання бібліотеки навичок Hermes.
- **`text_to_speech`** — TTS через налаштованого провайдера Hermes.

Коли модель потребує одного з цих інструментів, Codex запускає підпроцес `hermes_tools_mcp_server` через stdio MCP, виклик диспетчеризується через `model_tools.handle_function_call()` (той же шлях коду, що й у стандартному runtime Hermes), і результат повертається до Codex як будь‑яка інша відповідь MCP.

### Що НЕ доступно в цьому runtime

Ці чотири інструменти Hermes потребують контексту запущеного AIAgent (стан середнього циклу), щоб їх можна було диспатчити, а безстановий колбек MCP їх не керує. Повернись до стандартного runtime (`/codex-runtime auto`), коли потрібен будь‑який із них:

- **`delegate_task`** — створює під‑агенти
- **`memory`** — постійне сховище пам’яті Hermes
- **`session_search`** — пошук між сесіями
- **`todo`** — сховище задач Hermes (`update_plan` Codex — це еквівалент у runtime)
## Функції робочого процесу (`/goal`, kanban, cron`)

### `/goal` (цикл Ральфа)

**Працює в цьому середовищі виконання.** Цілі зберігаються в `state_meta`, ключовані ідентифікатором **сесії**, підказка продовження повертається як звичайне повідомлення користувача через `run_conversation()`, а codex виконує наступний хід нативно. Суддя цілі запускається через допоміжний клієнт (налаштований у `auxiliary.goal_judge` у `config.yaml`), незалежно від того, яке середовище виконання активне. Вердикт судді «заблоковано, потрібен ввід користувача» є чистим виходом, якщо codex зависає на схваленнях.

**Одне, про що варто знати:** кожна підказка продовження — це новий хід codex, що означає, що codex переоцінює політику схвалення команд з нуля. Якщо ти виконуєш довготривалу ціль з великою кількістю записів, очікуй більше запитів схвалення, ніж під час однієї задачі в сесії. Встанови `default_permissions = ":workspace"` (що Hermes робить автоматично, коли ти вмикаєш середовище виконання), щоб прості записи у робочий простір не вимагали запиту.

### Kanban (диспетчерізація робочого дерева багатьох агентів)

**Працює в цьому середовищі виконання, з однією тонкою залежністю.** Диспетчер kanban створює кожного працівника як окремий підпроцес `hermes chat -q`, який читає конфігурацію користувача — це означає, що якщо `model.openai_runtime: codex_app_server` встановлено глобально, працівники також піднімаються у середовищі codex.

**Що працює всередині працівника codex‑runtime:**
- Повний набір інструментів Codex (`shell`, `apply_patch`, `update_plan`, `view_image`, `web_search`) — працівник виконує свою фактичну роботу нативно
- Перенесені плагіни codex — Linear, GitHub тощо
- Колбек інструменту Hermes для `browser_*`, `vision`, `image_gen`, `skills`, `TTS`

**Що також працює, бо колбек MCP їх експонує:**
- **`kanban_complete` / `kanban_block` / `kanban_comment` / `kanban_heartbeat`** — інструменти передачі управління працівнику. Вони читають `HERMES_KANBAN_TASK` з середовища (встановлює диспетчер), правильно контролюють доступ і записують у SQLite‑БД дошки, прив’язану до `HERMES_KANBAN_DB`. Без цих у колбеку працівник у цьому середовищі може виконувати свою задачу, але не зможе повідомити про завершення, зависаючи до тайм‑ауту диспетчера.
- **`kanban_show` / `kanban_list`** — запити лише для читання дошки, щоб працівник перевірив власний контекст.
- **`kanban_create` / `kanban_unblock` / `kanban_link`** — операції лише для оркестратора. Доступні оркестратору‑агентам, що працюють у середовищі codex і потребують диспетчеризувати нові задачі.

Інструменти kanban контролюються змінною середовища `HERMES_KANBAN_TASK`, яку встановлює диспетчер — ця змінна передається у підпроцес codex (codex успадковує середовище) і звідти у запущений підпроцес сервера MCP `hermes-tools`. Тому інструменти бачать правильний ідентифікатор задачі та правильно контролюють доступ. Для працівників Codex app‑server Hermes також передає вузькі перевизначення пісочниці app‑server, коли присутня `HERMES_KANBAN_TASK`: зберігає пісочницю `workspace-write`, додає **каталог БД дошки плюс кожен шлях Kanban, який закріпив диспетчер** як додаткові записувані корені (`HERMES_KANBAN_WORKSPACES_ROOT`, `HERMES_KANBAN_WORKSPACE`, застарілий `HERMES_KANBAN_ROOT` — дедупліковано, спочатку каталог БД), і залишає мережу вимкненою за замовчуванням. Це уникає крихкого обходу `:danger-no-sandbox`, дозволяючи `kanban_complete` / `kanban_block` оновлювати БД дошки **і** дозволяючи працівникам записувати звіти/артефакти у монтування робочих просторів, що живуть поза каталогом БД (наприклад, `/media/.../kanban-workspaces/...` на окремому диску —    ```bash
   codex login                  # writes tokens to ~/.codex/auth.json
   ```).

### Cron‑завдання

**Не тестувалося спеціально.** Cron‑завдання запускаються через `cronjob` → `AIAgent.run_conversation`, той самий шлях коду, що і у CLI. Якщо у конфігурації cron‑завдання вказано `openai_runtime: codex_app_server`, воно працюватиме у codex. Правила доступності інструментів залишаються тими ж — вбудовані інструменти codex + плагіни + колбек MCP працюють, інструменти циклу агента (`delegate_task`, `memory`, `session_search`, `todo`) — ні. Якщо твоє cron‑завдання покладається на ці інструменти, обмеж його профілем, який використовує середовище виконання за замовчуванням.
## Компроміси

|  | Типове середовище Hermes | Codex app‑server (опціонально) |
|---|---|---|
| `delegate_task` subagents | так | недоступно — потрібен контекст циклу агента |
| `memory`, `session_search`, `todo` | так | недоступно — потрібен контекст циклу агента |
| `web_search`, `web_extract` | так | так (через MCP callback) |
| Browser automation (Camofox/Browserbase) | так | так (через MCP callback) |
| `vision_analyze`, `image_generate` | так | так (через MCP callback) |
| `skill_view`, `skills_list` | так | так (через MCP callback) |
| `text_to_speech` | так | так (через MCP callback) |
| Codex `shell` (terminal/read/write/search/find/run) | — | так (вбудований Codex) |
| Codex `apply_patch` (structured multi‑file edits) | — | так (вбудований Codex) |
| Codex `update_plan` (in‑runtime todo) | — | так (вбудований Codex) |
| Codex `view_image` (load image into conversation) | — | так (вбудований Codex) |
| Codex sandbox (seatbelt/landlock, profiles) | — | так (вбудований Codex) |
| ChatGPT subscription auth | — | так (через `openai-codex` provider) |
| Native Codex plugins (Linear, GitHub, etc.) | — | так (автоматично мігрується) |
| User MCP servers | так | так (автоматично мігрується до Codex) |
| Memory + skill review (background) | так | так (через проекцію елементів) |
| Multi‑turn conversations | так | так |
| `/goal` (Ralph loop) | так | так |
| Kanban worker dispatch | так | так (через callback) |
| Kanban orchestrator tools | так | так (через callback) |
| All gateway platforms | так | так |
| Non‑OpenAI providers | так | н/д — у межах OpenAI/Codex |
## Передумови

1. **Codex CLI встановлений:**
   ```bash
   npm i -g @openai/codex
   codex --version   # 0.130.0 or newer
   ```

2. **Codex OAuth логін.** Підпроцес `codex` читає `~/.codex/auth.json`. Є два способи заповнити його:
   ```bash
   codex login                  # writes tokens to ~/.codex/auth.json
   ```
   Власна команда Hermes `hermes auth login codex` записує у `~/.hermes/auth.json` — це окрема сесія. **Запусти `codex login` окремо**, якщо ти ще не зробив цього.

3. **(Необов’язково) Встанови потрібні плагіни Codex.** Коли ти вмикаєш runtime, Hermes автоматично мігрує будь‑які підготовлені плагіни, які вже встановлені через Codex CLI:
   ```bash
   codex plugin marketplace add openai-curated
   # then via codex's TUI, install Linear / GitHub / Gmail / etc.
   ```
   Hermes виявить їх і автоматично запише записи `[plugins."<name>@openai-curated"]` у `~/.codex/config.toml`.
## Увімкнення

У Hermes‑сесії:

```
/codex-runtime codex_app_server
```

Ця команда:
- Перевіряє, чи встановлений CLI `codex` (блокує з підказкою встановлення, якщо його немає).
- Зберігає `model.openai_runtime: codex_app_server` у твоєму `config.yaml`.
- Переносить сервери MCP користувача з `~/.hermes/config.yaml` до `~/.codex/config.toml`.
- **Виявляє та переносить встановлені нативні плагіни Codex** (Linear, GitHub, Gmail, Calendar, Canva тощо), запитуючи `plugin/list` RPC Codex.
- **Реєструє власні інструменти Hermes як сервер MCP**, щоб підпроцес codex міг викликати інструменти, які не входять до складу codex.
- **Записує `default_permissions = ":workspace"`**, щоб пісочниця дозволяла запис у робочий простір без запиту підтвердження для кожної операції.
- Повідомляє, що було перенесено. Набирає чинності в **наступній** сесії — поточний кешований агент зберігає попереднє середовище виконання, тому кеші підказок залишаються дійсними.

Синоніми: `/codex-runtime on`, `/codex-runtime off`, `/codex-runtime auto`.

Щоб перевірити поточний стан без змін:
```
/codex-runtime
```

Ти також можеш встановити це вручну у `~/.hermes/config.yaml`:
```yaml
model:
  openai_runtime: codex_app_server   # default is "auto" (= Hermes runtime)
```
## Цикл самовдосконалення (пам'ять + підказки навичок)

Фонове самовдосконалення Hermes спрацьовує при досягненні порогових значень:

- Кожні 10 запитів користувача → форк‑агент огляду переглядає розмову і вирішує, чи варто щось зберегти в **пам'ять**.
- Кожні 10 ітерацій інструменту в одному ході → те саме, але для **навичок** (`skill_manage` записує).

**Обидва працюють у середовищі codex runtime.** Шлях *codex* проєктує кожен завершений `commandExecution` / `fileChange` / `mcpToolCall` / `dynamicToolCall` у синтетичне повідомлення `assistant tool_call` + результат `tool`, тому коли запускається огляд, він бачить ту саму структуру, що й у звичайному середовищі Hermes.

### Як з’єднання залишається еквівалентним

| | Звичайне середовище | Codex runtime |
|---|---|---|
| `_turns_since_memory` збільшується | при кожному запиті користувача, у `run_conversation` перед циклом | той самий кодовий шлях, перед раннім поверненням |
| `_iters_since_skill` збільшується | при кожній ітерації інструменту в циклі `chat-completions` | за `turn.tool_iterations` після повернення codex‑ходу |
| Тригер пам'яті (`_turns_since_memory >= _memory_nudge_interval`) | обчислюється у передциклі, спрацьовує після відповіді | обчислюється у передциклі, передається до допоміжної функції *codex* |
| Тригер навички (`_iters_since_skill >= _skill_nudge_interval`) | обчислюється після циклу | обчислюється після codex‑ходу |
| `_spawn_background_review(messages_snapshot=..., review_memory=..., review_skills=...)` | викликається, коли спрацьовує будь‑який тригер | викликається ідентично, коли спрацьовує будь‑який тригер |

Один нюанс: сам форк огляду має викликати інструменти циклу агента Hermes (`memory`, `skill_manage`), які потребують власного диспетчера Hermes. Тому коли батьківський агент працює на `codex_app_server`, форк огляду **перемикається на `codex_responses`** — ті ж OAuth‑облікові дані, той самий провайдер `openai-codex`, але звертається безпосередньо до API *Responses* OpenAI, тому Hermes керує циклом і інструменти циклу агента працюють. Це не помітно користувачеві.

**Загальний ефект:** увімкнути *codex* runtime, і твої підказки пам'яті та навичок продовжуватимуть спрацьовувати точно так само, як і раніше.
## Як працює схвалення

Codex запитує схвалення перед виконанням команд або застосуванням патчів. Це перетворюється у стандартний запит Hermes «Dangerous Command»:

```
╭───────────────────────────────────────╮
│ Dangerous Command                     │
│                                       │
│ /bin/bash -lc 'echo hello > foo.txt'  │
│                                       │
│ ❯ 1. Allow once                       │
│   2. Allow for this session           │
│   3. Deny                             │
│                                       │
│ Codex requests exec in /your/cwd      │
╰───────────────────────────────────────╯
```

- **Allow once** → дозволити цю одну команду.
- **Allow for this session** → Codex більше не буде запитувати схвалення для подібних команд у цій сесії.
- **Deny** → команда відхилена; Codex продовжує працювати в режимі лише читання.

Для схвалень `apply_patch` (редагування файлів) Hermes показує підсумок змін (`1 add, 1 update: /tmp/new.py, /tmp/old.py`), коли Codex надає дані через відповідний елемент `fileChange`.
## Профілі дозволів

Codex має три вбудованих профілі дозволів:
- `:read-only` — без записів; кожна команда оболонки вимагає схвалення
- `:workspace` — записи в межах поточної робочої області дозволені без запитів (за замовчуванням Hermes, коли ти вмикаєш середовище виконання)
- `:danger-no-sandbox` — зовсім без пісочниці (не використовуйте це, якщо не розумієте)

Ти можеш перевизначити значення за замовчуванням у `~/.codex/config.toml` поза блоком, яким керує Hermes:

```toml
default_permissions = ":read-only"
```

(Hermes збереже твоє перевизначення під час повторної міграції, доки воно знаходиться поза маркерами `# managed by hermes-agent`.)
## Додаткові завдання та вартість токенів підписки ChatGPT

Коли цей runtime увімкнено з провайдером `openai-codex`, **допоміжні завдання (генерація заголовків, стиснення контексту, автоматичне розпізнавання зображень, форк огляду самонавчального агента) також за замовчуванням проходять через твою підписку ChatGPT**, оскільки допоміжний клієнт Hermes використовує основного провайдера/модель, коли не встановлено переозначення для конкретного завдання.

Це не специфічно для `codex_app_server` — так само працює і для існуючого шляху `codex_responses` — але тут це більш помітно, бо ти явно погодився на оплату підписки.

Щоб перенаправити певні допоміжні завдання на дешевішу/іншу модель, встанови явні переозначення у `~/.hermes/config.yaml`:

```yaml
auxiliary:
  title_generation:
    provider: openrouter
    model: google/gemini-3-flash-preview
  context_compression:
    provider: openrouter
    model: google/gemini-3-flash-preview
  vision_detect:
    provider: openrouter
    model: google/gemini-3-flash-preview
  goal_judge:
    provider: openrouter
    model: google/gemini-3-flash-preview
```

Форк огляду самонавчального агента успадковує основний runtime через `_current_main_runtime()` і Hermes автоматично знижує його з `codex_app_server` до `codex_responses` (щоб форк міг фактично викликати `memory` та `skill_manage` — інструменти власного циклу агента Hermes). Цей форк все ще використовує твою автентифікацію підписки, якщо ти не перенаправив допоміжні завдання кудись інше.
## Редагування `~/.codex/config.toml` безпечно

Hermes обгортає все, чим керує, між двома маркерними коментарями:

```toml
# managed by hermes-agent — `hermes codex-runtime migrate` regenerates this section
default_permissions = ":workspace"
[mcp_servers.filesystem]
...
[plugins."github@openai-curated"]
...
# end hermes-agent managed section
```

Все **поза** цим блоком — це твоє. Повторний запуск міграції (через `/codex-runtime codex_app_server` або коли ти вмикаєш runtime) замінює керований блок на місці, але зберігає вміст користувача вище та нижче його дослівно. Це означає, що ти можеш:

- Додати власні MCP‑сервери, про які Hermes не знає
- Перевизначити `default_permissions` на `:read-only`, якщо ти хочеш, щоб запитували підтвердження
- Налаштувати лише codex‑only опції (model, providers, otel тощо)
- Додати визначені користувачем профілі дозволів у таблицях `[permissions.<name>]`

Все, що ти додастиш **всередині** керованого блоку, буде перезаписано під час наступної міграції. Якщо потрібне налаштування, яке вимагає зміни керованого блоку, створи issue, і ми додамо відповідний параметр.
## Налаштування з кількома профілями / багатокористувацькі середовища

За замовчуванням Hermes спрямовує підпроцес **Codex** у `~/.codex/` незалежно від того, який профіль Hermes активний. Це означає, що `hermes -p work` і `hermes -p personal` ділять одну й ту ж автентифікацію Codex, плагіни та конфігурацію. Для більшості користувачів це правильна поведінка — вона відповідає тому, що робило б пряме використання CLI `codex`.

Якщо потрібна ізоляція Codex для кожного профілю (окремі дані автентифікації, окремі встановлені плагіни, окрема конфігурація), встанови `CODEX_HOME` явно для кожного профілю. Найпростіший спосіб — вказати каталог у твоєму `HERMES_HOME`:

```bash
# Inside the work profile, you might wrap hermes:
CODEX_HOME=~/.hermes/profiles/work/codex hermes chat
```

Тобі потрібно буде один раз повторно виконати `codex login` з встановленим `CODEX_HOME`, щоб токени OAuth потрапили у розташування, прив’язане до профілю. Після цього `hermes -p work` працюватиме з ізольованим станом Codex.

Ми не робимо це автоматично, бо переміщення існуючого `~/.codex/` користувача без попередження призведе до втрати їхньої автентифікації CLI Codex — будь‑хто, хто вже виконав `codex login`, доведеться повторно аутентифікуватися. Опція «опт‑ін» виглядає безпечнішою, ніж несподіванка для користувачів.
## Перехід змінної середовища HOME

Hermes НЕ переписує `HOME` під час створення підпроцесу серверу додатка **codex** (ми використовуємо `os.environ.copy()` і лише накладаємо `CODEX_HOME` та `RUST_LOG`). Це означає:

- Команди, які **codex** запускає через свій інструмент `shell`, бачать реальний `HOME` користувача і правильно знаходять `~/.gitconfig`, `~/.gh/`, `~/.aws/`, `~/.npmrc` тощо.
- Внутрішній стан **Codex** залишається ізольованим завдяки `CODEX_HOME` (який за замовчуванням вказує на `~/.codex/`).

Це відповідає межі, до якої прийшов **OpenClaw** після ранніх експериментів: ізолювати стан **Codex**, залишивши домашню директорію користувача недоторканою. (Cf. openclaw/openclaw#81562.)
## Міграція сервера MCP

Конфігурація `mcp_servers` Hermes автоматично перекладається у формат TOML, який очікує Codex. Міграція виконується щоразу, коли ти вмикаєш runtime, і є ідемпотентною — повторні запуски замінюють керовану секцію, зберігаючи будь‑які користувачем відредаговані конфігурації Codex.

Що перекладається:

| Hermes (`config.yaml`) | Codex (`config.toml`) |
|---|---|
| `command` + `args` + `env` | stdio transport |
| `url` + `headers` | streamable_http transport |
| `timeout` | `tool_timeout_sec` |
| `connect_timeout` | `startup_timeout_sec` |
| `enabled: false` | `enabled = false` |

Що не мігрує:
- Ключі, специфічні для Hermes, такі як `sampling` (у клієнта MCP Codex немає еквіваленту — вони відкидаються з попередженням для кожного сервера).
## Міграція плагінів Native Codex

Плагіни, встановлені за допомогою `codex plugin` (Linear, GitHub, Gmail, Calendar, Canva тощо), виявляються через RPC `plugin/list` Codex. Для кожного плагіна, у якому `installed: true`, Hermes записує блок `[plugins."<name>@openai-curated"]`, що вмикає його у твоїй сесії Hermes.

Тобто: коли твій друг каже «У мене налаштовано Calendar і GitHub у Codex CLI» і він вмикає runtime Hermes, Hermes активує їх автоматично. Переналаштування не потрібне.

Що НЕ мігрується:
- Плагіни, які ти ще не встановив — спочатку встанови їх у Codex.
- Плагіни, у яких Codex повертає `availability != AVAILABLE` (пошкоджена інсталяція, прострочений OAuth, видалено з маркетплейсу тощо). Вони пропускаються, щоб уникнути запису конфігурації, яка не зможе активуватись.
- Записи маркетплейсу додатків ChatGPT (результати `app/list` для конкретного облікового запису — вони вже ввімкнені в Codex завдяки автентифікації твого облікового запису).
- OAuth плагіна — ти авторизуєш кожен плагін один раз у самому Codex; Hermes не торкається облікових даних.
## Hermes tool callback (the new MCP server)

Вбудований набір інструментів Codex охоплює операції з оболонкою/файлами/патчами, але не має веб‑пошуку, автоматизації браузера, зору, генерації зображень тощо. Щоб ці можливості залишалися доступними під час обробки запиту Codex, Hermes реєструє себе як MCP‑сервер у `~/.codex/config.toml`:

```toml
[mcp_servers.hermes-tools]
command = "/path/to/python"
args = ["-m", "agent.transports.hermes_tools_mcp_server"]
env = { HERMES_HOME = "/your/.hermes", PYTHONPATH = "...", HERMES_QUIET = "1" }
startup_timeout_sec = 30.0
tool_timeout_sec = 600.0
```

Коли модель викликає `web_search` (або інший відкритий інструмент Hermes), codex запускає підпроцес `hermes_tools_mcp_server` через stdio, запит передається через `model_tools.handle_function_call()`, а результат повертається до codex так само, як будь‑яка інша відповідь MCP.

**Інструменти, доступні через callback:** `web_search`, `web_extract`, `browser_navigate`, `browser_click`, `browser_type`, `browser_press`, `browser_snapshot`, `browser_scroll`, `browser_back`, `browser_get_images`, `browser_console`, `browser_vision`, `vision_analyze`, `image_generate`, `skill_view`, `skills_list`, `text_to_speech`.

**Інструменти, НЕ доступні:** `delegate_task`, `memory`, `session_search`, `todo`. Для їх використання потрібен контекст запущеного AIAgent, щоб розсилати їх (стан у середині циклу навчання), а безстанний MCP‑callback їх не може керувати. Використовуй типове середовище Hermes (`/codex-runtime auto`), коли потрібні ці інструменти.
## Вимкнення

Повернутись у будь‑який момент:

```
/codex-runtime auto
```

Діє з наступної сесії. Блок, керований Codex, зберігається у `~/.codex/config.toml`, тож ти можеш повторно ввімкнути його пізніше без втрати налаштувань — або видалити вручну, якщо бажаєш.
## Обмеження

Цей runtime **opt-in beta**. Працює у Hermes Agent 2026.5 + Codex CLI 0.130.0:

- Багатокрокові розмови
- `commandExecution` та `fileChange` (apply_patch) схвалення через Hermes UI
- Виклики інструменту MCP (перевірено проти `@modelcontextprotocol/server-filesystem` та нового зворотного виклику `hermes-tools`)
- Міграція нативних плагінів Codex (перевірено проти інвентарю Linear / GitHub / Calendar)
- Шляхи deny/cancel
- Перемикач увімкнення/вимкнення циклу
- Лічильники підказок пам'яті та навичок (перевірено в реальному часі за допомогою інтеграційних тестів)
- Hermes web_search через codex (перевірено в реальному часі: «OpenAI Codex CLI – Getting Started» повернув end-to-end)

Відомі обмеження:

- **Hermes auth та codex auth – окремі сесії.** Потрібно виконати одночасно `codex login` І `hermes auth login codex` для найзручнішого UX (runtime використовує сесію codex для виклику LLM). Це навмисний дизайн у Hermes `_import_codex_cli_tokens` — Hermes не ділиться станом OAuth з codex CLI, щоб уникнути конфліктів під час оновлення токенів.
- **`delegate_task`, `memory`, `session_search`, `todo` недоступні в цьому runtime.** Вони потребують контексту запущеного AIAgent, який stateless‑callback MCP не може надати. Використовуй `/codex-runtime auto`, коли потрібні ці функції.
- **Немає попереднього перегляду патчу в рядку у запитах схвалення, коли codex не відстежує changeset.** Параметри схвалення `fileChange` у Codex не завжди містять changeset. Hermes кешує дані з відповідного сповіщення `item/started`, коли це можливо, але якщо схвалення надходить до того, як елемент був переданий, запит повертається до будь‑якого `reason`, який надає codex.
- **Гарантії скасування за підсекунду немає.** Переривання посеред потоку (Ctrl+C під час відповіді codex) надсилаються через `turn/interrupt`, проте якщо codex вже відправив фінальне повідомлення, ти все одно отримаєш відповідь.

Якщо знайдеш баг, [відкрий issue](https://github.com/NousResearch/hermes-agent/issues) з виводом `hermes logs --since 5m`. Зазнач `codex-runtime` у заголовку, щоб його легше було розглянути.
## Архітектура

```
                ┌─── Hermes shell (CLI / TUI / gateway) ───┐
                │  sessions DB · slash commands · memory   │
                │  & skill review · cron · session pickers │
                └──┬──────────────────────────────────────┬┘
                   │ user_message               final     │
                   ▼                            text +    │
        ┌──────────────────────────────────┐   projected  │
        │  AIAgent.run_conversation()       │   messages   │
        │   if api_mode == codex_app_server │              │
        │     → CodexAppServerSession       │              │
        │   else: chat_completions / codex_responses (default)
        └────┬─────────────────────────────┘              │
             │ JSON-RPC over stdio                        │
             ▼                                            │
        ┌──────────────────────────────────┐              │
        │  codex app-server (subprocess)    │──────────────┘
        │   thread/start, turn/start        │
        │   item/* notifications            │
        │   shell + apply_patch + update_plan│
        │   view_image + sandbox            │
        │   ┌─────────────────────────┐     │
        │   │  MCP client             │     │
        │   │  ├─ user MCP servers    │     │
        │   │  ├─ native plugins      │     │
        │   │  │   (linear, github,   │     │
        │   │  │    gmail, calendar,  │     │
        │   │  │    canva, ...)       │     │
        │   │  └─ hermes-tools ───────┼─────────────────┐
        │   │       (callback to     │     │           │
        │   │        Hermes' richer  │     │           │
        │   │        tools)          │     │           │
        │   └─────────────────────────┘     │           │
        └──────────────────────────────────┘           │
                                                        │
                                                        ▼
        ┌──────────────────────────────────────────────────────────┐
        │  hermes_tools_mcp_server.py (subprocess on demand)        │
        │   web_search, web_extract, browser_*, vision_analyze,    │
        │   image_generate, skill_view, skills_list, text_to_speech│
        └──────────────────────────────────────────────────────────┘
```

Для деталей реалізації дивись [PR #24182](https://github.com/NousResearch/hermes-agent/pull/24182) та [Codex app-server protocol README](https://github.com/openai/codex/blob/main/codex-rs/app-server/README.md).