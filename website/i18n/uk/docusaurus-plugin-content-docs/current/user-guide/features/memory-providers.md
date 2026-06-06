---
sidebar_position: 4
title: "провайдери пам'яті"
description: "Зовнішні плагіни постачальника пам'яті — Honcho, OpenViking, Mem0, Hindsight, Holographic, RetainDB, ByteRover, Supermemory"
---

# Провайдери пам'яті

Hermes Agent постачається з 8 плагінами зовнішніх провайдерів пам'яті, які надають агенту постійні, міжсесійні знання поза вбудованими `MEMORY.md` і `USER.md`. Тільки **один** зовнішній провайдер може бути активним одночасно — вбудована пам'ять завжди активна разом із ним.
## Швидкий старт

```bash
hermes memory setup      # interactive picker + configuration
hermes memory status     # check what's active
hermes memory off        # disable external provider
```

Ти також можеш вибрати активний провайдер пам'яті через `hermes plugins` → Provider Plugins → Memory Provider.

Або встанови вручну у файлі `~/.hermes/config.yaml`:

```yaml
memory:
  provider: openviking   # or honcho, mem0, hindsight, holographic, retaindb, byterover, supermemory
```
## Як це працює

Коли провайдер пам’яті активний, Hermes автоматично:

1. **Вставляє контекст провайдера** у системний підказник (те, що знає провайдер)
2. **Попередньо отримує релевантні пам’яті** перед кожним ходом (у фоні, без блокування)
3. **Синхронізує ходи розмови** з провайдером після кожної відповіді
4. **Витягує пам’яті в кінці сесії** (для провайдерів, які це підтримують)
5. **Дзеркально записує вбудовану пам’ять** у зовнішнього провайдера
6. **Додає інструменти, специфічні для провайдера**, щоб агент міг шукати, зберігати та керувати пам’яттю

Вбудована пам’ять (MEMORY.md / USER.md) продовжує працювати точно так само, як і раніше. Зовнішній провайдер додається додатково.
## Доступні провайдери
### Honcho

AI‑нативне крос‑сесійне моделювання користувача з діалектичним міркуванням, ін’єкцією контексту у межах сесії, семантичним пошуком та стійкими висновками. Базовий контекст тепер включає підсумок сесії разом із представленням користувача та картками співрозмовників, що дає агенту усвідомлення того, що вже було обговорено.

| | |
|---|---|
| **Best for** | Multi‑agent системи з крос‑сесійним контекстом, узгодження користувач‑агент |
| **Requires** | `pip install honcho-ai` + [API key](https://app.honcho.dev) або self‑hosted інстанція |
| **Data storage** | Honcho Cloud або self‑hosted |
| **Cost** | Honcho pricing (cloud) / free (self‑hosted) |

**Tools (5):** `honcho_profile` (читання/оновлення картки співрозмовника), `honcho_search` (семантичний пошук), `honcho_context` (контекст сесії — підсумок, представлення, картка, повідомлення), `honcho_reasoning` (LLM‑синтез), `honcho_conclude` (створення/видалення висновків)

**Architecture:** Дворівнева ін’єкція контексту — базовий шар (підсумок сесії + представлення + картка співрозмовника, оновлюється за `contextCadence`) плюс діалектичний додаток (LLM‑міркування, оновлюється за `dialecticCadence`). Діалектика автоматично обирає холодні підказки (загальні факти про користувача) чи теплі підказки (контекст у межах сесії) залежно від наявності базового контексту.

**Three orthogonal config knobs** керують вартістю та глибиною незалежно:

- `contextCadence` — як часто оновлюється базовий шар (частота API‑викликів)
- `dialecticCadence` — як часто спрацьовує діалектичний LLM (частота LLM‑викликів)
- `dialecticDepth` — скільки проходів `.chat()` виконується за один діалектичний виклик (1–3, глибина міркування)

**Setup Wizard:**
```bash
hermes memory setup        # select "honcho" — runs the Honcho-specific post-setup
```

Застаріла команда `hermes honcho setup` все ще працює (тепер перенаправляє на `hermes memory setup`), але вона реєструється лише після вибору Honcho як активного провайдера пам’яті.

**Config:** `$HERMES_HOME/honcho.json` (локальний профіль) або `~/.honcho/config.json` (глобальний). Порядок розв’язання: `$HERMES_HOME/honcho.json` > `~/.hermes/honcho.json` > `~/.honcho/config.json`. Дивись [config reference](https://github.com/hermes-ai/hermes-agent/blob/main/plugins/memory/honcho/README.md) та [Honcho integration guide](https://docs.honcho.dev/v3/guides/integrations/hermes).

<details>
<summary>Full config reference</summary>

| Key | Default | Description |
|-----|---------|-------------|
| `apiKey` | -- | API key from [app.honcho.dev](https://app.honcho.dev) |
| `baseUrl` | -- | Base URL for self‑hosted Honcho |
| `peerName` | -- | User peer identity |
| `aiPeer` | host key | AI peer identity (one per profile) |
| `workspace` | host key | Shared workspace ID |
| `contextTokens` | `null` (uncapped) | Token budget for auto‑injected context per turn. Truncates at word boundaries |
| `contextCadence` | `1` | Minimum turns between `context()` API calls (base layer refresh) |
| `dialecticCadence` | `2` | Minimum turns between `peer.chat()` LLM calls. Recommended 1–5. Only applies to `hybrid`/`context` modes |
| `dialecticDepth` | `1` | Number of `.chat()` passes per dialectic invocation. Clamped 1–3. Pass 0: cold/warm prompt, pass 1: self‑audit, pass 2: reconciliation |
| `dialecticDepthLevels` | `null` | Optional array of reasoning levels per pass, e.g. `["minimal", "low", "medium"]`. Overrides proportional defaults |
| `dialecticReasoningLevel` | `'low'` | Base reasoning level: `minimal`, `low`, `medium`, `high`, `max` |
| `dialecticDynamic` | `true` | When `true`, model can override reasoning level per‑call via tool param |
| `dialecticMaxChars` | `600` | Max chars of dialectic result injected into system prompt |
| `recallMode` | `'hybrid'` | `hybrid` (auto‑inject + tools), `context` (inject only), `tools` (tools only) |
| `writeFrequency` | `'async'` | When to flush messages: `async` (background thread), `turn` (sync), `session` (batch on end), or integer N |
| `saveMessages` | `true` | Whether to persist messages to Honcho API |
| `observationMode` | `'directional'` | `directional` (all on) or `unified` (shared pool). Override with `observation` object |
| `messageMaxChars` | `25000` | Max chars per message (chunked if exceeded) |
| `dialecticMaxInputChars` | `10000` | Max chars for dialectic query input to `peer.chat()` |
| `sessionStrategy` | `'per-directory'` | `per-directory`, `per-repo`, `per-session`, `global` |

</details>

<details>
<summary>Minimal honcho.json (cloud)</summary>

```json
{
  "apiKey": "your-key-from-app.honcho.dev",
  "hosts": {
    "hermes": {
      "enabled": true,
      "aiPeer": "hermes",
      "peerName": "your-name",
      "workspace": "hermes"
    }
  }
}
```

</details>

<details>
<summary>Minimal honcho.json (self‑hosted)</summary>

```json
{
  "baseUrl": "http://localhost:8000",
  "hosts": {
    "hermes": {
      "enabled": true,
      "aiPeer": "hermes",
      "peerName": "your-name",
      "workspace": "hermes"
    }
  }
}
```

</details>

:::tip Migrating from `hermes honcho`
If you previously used `hermes honcho setup`, your config and all server‑side data are intact. Just re‑enable through the setup wizard again or manually set `memory.provider: honcho` to reactivate via the new system.
:::

**Multi‑peer setup:**

Honcho моделює розмови як peers, що обмінюються повідомленнями — один user peer плюс один AI peer на кожен Hermes profile, всі ділять workspace. Workspace — це спільне середовище: user peer глобальний для всіх профілів, кожен AI peer має свою ідентичність. Кожен AI peer будує незалежне представлення/картку зі своїх спостережень, тому профіль `coder` залишається орієнтованим на код, а профіль `writer` — на редактуру, працюючи з тим самим користувачем.

The mapping:

| Concept | What it is |
|---------|-----------|
| **Workspace** | Shared environment. All Hermes profiles under one workspace see the same user identity. |
| **User peer** (`peerName`) | The human. Shared across profiles in the workspace. |
| **AI peer** (`aiPeer`) | One per Hermes profile. Host key `hermes` → default; `hermes.<profile>` for others. |
| **Observation** | Per‑peer toggles controlling what Honcho models from whose messages. `directional` (default, all four on) or `unified` (single‑observer pool). |
### Новий профіль, свіжий Honcho peer

```bash
hermes profile create coder --clone
```

`--clone` створює блок хоста `hermes.coder` у `honcho.json` з `aiPeer: "coder"`, спільним `workspace`, успадкованим `peerName`, `recallMode`, `writeFrequency`, `observation` тощо. AI‑peer створюється в Honcho одразу, тому він існує ще до першого повідомлення.
### Існуючі профілі, заповнити недостаючі Honcho‑піри

```bash
hermes honcho sync
```

Сканує кожен Hermes‑профіль, створює блоки хостів для будь‑якого профілю без них, успадковує налаштування з типового блоку `hermes` і активно створює нових AI‑піри. Ідемпотентний — пропускає профілі, які вже мають блок хоста.
### Спостереження за профілем

Кожен блок **host** може незалежно перевизначати конфігурацію спостереження. Приклад: профіль, орієнтований на код, де AI‑пір спостерігає за користувачем, але не створює власну модель:

```json
"hermes.coder": {
  "aiPeer": "coder",
  "observation": {
    "user": { "observeMe": true, "observeOthers": true },
    "ai":   { "observeMe": false, "observeOthers": true }
  }
}
```

**Перемикачі спостереження (по одному набору на кожного піра):**

| Перемикач | Ефект |
|-----------|-------|
| `observeMe` | Honcho створює представлення цього піра на основі його власних повідомлень |
| `observeOthers` | Цей пір спостерігає за повідомленнями іншого піра (забезпечує крос‑піровий роздум) |

Пресети через `observationMode`:

- **`"directional"`** (за замовчуванням) — увімкнено всі чотири прапорці. Повне взаємне спостереження; включає крос‑піровий діалектичний процес.
- **`"unified"`** — користувач `observeMe: true`, AI `observeOthers: true`, інші — false. Один спостерігач; AI моделює користувача, але не себе, а користувач‑пір лише самостійно моделює себе.

Перемикачі на боці сервера, встановлені через [панель Honcho](https://app.honcho.dev), мають пріоритет над локальними значеннями за замовчуванням — синхронізуються під час ініціалізації **сесії**.

Дивись [сторінку Honcho](./honcho.md#observation-directional-vs-unified) для повного довідника з налаштувань спостереження.

<details>
<summary>Повний приклад **honcho.json** (мульти‑профіль)</summary>

```json
{
  "apiKey": "your-key",
  "workspace": "hermes",
  "peerName": "eri",
  "hosts": {
    "hermes": {
      "enabled": true,
      "aiPeer": "hermes",
      "workspace": "hermes",
      "peerName": "eri",
      "recallMode": "hybrid",
      "writeFrequency": "async",
      "sessionStrategy": "per-directory",
      "observation": {
        "user": { "observeMe": true, "observeOthers": true },
        "ai": { "observeMe": true, "observeOthers": true }
      },
      "dialecticReasoningLevel": "low",
      "dialecticDynamic": true,
      "dialecticCadence": 2,
      "dialecticDepth": 1,
      "dialecticMaxChars": 600,
      "contextCadence": 1,
      "messageMaxChars": 25000,
      "saveMessages": true
    },
    "hermes.coder": {
      "enabled": true,
      "aiPeer": "coder",
      "workspace": "hermes",
      "peerName": "eri",
      "recallMode": "tools",
      "observation": {
        "user": { "observeMe": true, "observeOthers": false },
        "ai": { "observeMe": true, "observeOthers": true }
      }
    },
    "hermes.writer": {
      "enabled": true,
      "aiPeer": "writer",
      "workspace": "hermes",
      "peerName": "eri"
    }
  },
  "sessions": {
    "/home/user/myproject": "myproject-main"
  }
}
```

</details>

Дивись [довідник конфігурації](https://github.com/hermes-ai/hermes-agent/blob/main/plugins/memory/honcho/README.md) та [посібник з інтеграції Honcho](https://docs.honcho.dev/v3/guides/integrations/hermes).
### OpenViking

Контекстна база даних від Volcengine (ByteDance) з ієрархією знань у стилі файлової системи, багаторівневим отриманням та автоматичним видобутком пам’яті у 6 категорій.

| | |
|---|---|
| **Best for** | Самохостинг управління знаннями зі структурованим переглядом |
| **Requires** | `pip install openviking` + запуск сервера |
| **Data storage** | Самохостинг (локально або в хмарі) |
| **Cost** | Безкоштовно (open‑source, AGPL‑3.0) |

**Tools:** `viking_search` (семантичний пошук), `viking_read` (багаторівневий: абстракт/огляд/повний), `viking_browse` (навігація по файловій системі), `viking_remember` (зберігання фактів), `viking_add_resource` (завантаження URL/документів)

**Setup:**
```bash
# Start the OpenViking server first
pip install openviking
openviking-server

# Then configure Hermes
hermes memory setup    # select "openviking"
# Or manually:
hermes config set memory.provider openviking
echo "OPENVIKING_ENDPOINT=http://localhost:1933" >> ~/.hermes/.env
```

**Key features:**
- Багаторівневе завантаження контексту: L0 (~100 токенів) → L1 (~2 k) → L2 (повний)
- Автоматичний видобуток пам’яті при фіксації сесії (профіль, налаштування, сутності, події, випадки, шаблони)
- Схема URI `viking://` для ієрархічного перегляду знань
### Mem0

Витяг фактів LLM на боці сервера за допомогою семантичного пошуку, переранжирування та автоматичного усунення дублікатів.

| | |
|---|---|
| **Найкраще підходить для** | Автоматичне керування пам'яттю — Mem0 виконує витяг самостійно |
| **Вимоги** | `pip install mem0ai` + API‑ключ |
| **Зберігання даних** | Mem0 Cloud |
| **Вартість** | Mem0 pricing |

**Інструменти:** `mem0_profile` (всі збережені пам’яті), `mem0_search` (семантичний пошук + переранжирування), `mem0_conclude` (збереження дослівних фактів)

**Налаштування:**
```bash
hermes memory setup    # select "mem0"
# Or manually:
hermes config set memory.provider mem0
echo "MEM0_API_KEY=your-key" >> ~/.hermes/.env
```

**Конфіг:** `$HERMES_HOME/mem0.json`

| Ключ | За замовчуванням | Опис |
|-----|------------------|------|
| `user_id` | `hermes-user` | Ідентифікатор користувача |
| `agent_id` | `hermes` | Ідентифікатор агента |
---
### Hindsight

Довготривала пам’ять із графом знань, розв’язанням сутностей та багатостратегічним пошуком. Інструмент `hindsight_reflect` забезпечує крос‑пам’яттєвий синтез, який не пропонує жоден інший провайдер. Автоматично зберігає повні ходи розмови (включно з викликами інструментів) з відстеженням документів на рівні сесії.

| | |
|---|---|
| **Найкраще підходить для** | Відновлення на основі графа знань із зв’язками сутностей |
| **Вимоги** | Cloud: API‑ключ з [ui.hindsight.vectorize.io](https://ui.hindsight.vectorize.io). Local: API‑ключ LLM (OpenAI, Groq, OpenRouter тощо) |
| **Зберігання даних** | Hindsight Cloud або локальний вбудований PostgreSQL |
| **Вартість** | Тариф Hindsight (cloud) або безкоштовно (local) |

**Tools:** `hindsight_retain` (зберігання з видобутком сутностей), `hindsight_recall` (багатостратегічний пошук), `hindsight_reflect` (крос‑пам’яттєвий синтез)

**Setup:**
```bash
hermes memory setup    # select "hindsight"
# Or manually:
hermes config set memory.provider hindsight
echo "HINDSIGHT_API_KEY=your-key" >> ~/.hermes/.env
```

Майстер налаштування автоматично встановлює залежності та інсталює лише те, що потрібно для обраного режиму (`hindsight-client` для cloud, `hindsight-all` для local). Потрібен `hindsight-client >= 0.4.22` (автооновлюється при старті сесії, якщо застарілий).

**Local mode UI:** `hindsight-embed -p hermes ui start`

**Config:** `$HERMES_HOME/hindsight/config.json`

| Key | Default | Description |
|-----|---------|-------------|
| `mode` | `cloud` | `cloud` або `local` |
| `bank_id` | `hermes` | Ідентифікатор банку пам’яті |
| `recall_budget` | `mid` | Тщательність відновлення: `low` / `mid` / `high` |
| `memory_mode` | `hybrid` | `hybrid` (контекст + інструменти), `context` (тільки авто‑вставка), `tools` (тільки інструменти) |
| `auto_retain` | `true` | Автоматично зберігати ходи розмови |
| `auto_recall` | `true` | Автоматично відновлювати пам’ять перед кожним ходом |
| `retain_async` | `true` | Обробляти збереження асинхронно на сервері |
| `retain_context` | `conversation between Hermes Agent and the User` | Мітка контексту для збережених спогадів |
| `retain_tags` | — | Теги за замовчуванням, що застосовуються до збережених спогадів; об’єднуються з тегами інструменту для кожного виклику |
| `retain_source` | — | Додатковий `metadata.source`, прикріплений до збережених спогадів |
| `retain_user_prefix` | `User` | Мітка перед ходами користувача в автозбережених транскриптах |
| `retain_assistant_prefix` | `Assistant` | Мітка перед ходами асистента в автозбережених транскриптах |
| `recall_tags` | — | Теги для фільтрації під час відновлення |

Дивись [plugin README](https://github.com/NousResearch/hermes-agent/blob/main/plugins/memory/hindsight/README.md) для повної довідки щодо конфігурації.
### Holographic

Локальне сховище фактів SQLite з повнотекстовим пошуком FTS5, оцінкою довіри та HRR (Holographic Reduced Representations) для композиційних алгебраїчних запитів.

| | |
|---|---|
| **Best for** | Локальна пам’ять без зовнішніх залежностей, з розширеним пошуком |
| **Requires** | Нічого (SQLite завжди доступний). NumPy — необов’язково для HRR‑алгебри. |
| **Data storage** | Локальний SQLite |
| **Cost** | Безкоштовно |

**Tools:** `fact_store` (9 actions: add, search, probe, related, reason, contradict, update, remove, list), `fact_feedback` (оцінка helpful/unhelpful, що навчає оцінки довіри)

**Setup:**
```bash
hermes memory setup    # select "holographic"
# Or manually:
hermes config set memory.provider holographic
```

**Config:** `config.yaml` під `plugins.hermes-memory-store`

| Key | Default | Description |
|-----|---------|-------------|
| `db_path` | `$HERMES_HOME/memory_store.db` | Шлях до SQLite‑бази даних |
| `auto_extract` | `false` | Автоматичне вилучення фактів у кінці сесії |
| `default_trust` | `0.5` | Типова оцінка довіри (0.0–1.0) |

**Unique capabilities:**
- `probe` — сутність‑специфічне алгебраїчне відтворення (всі факти про особу/річ)
- `reason` — композиційні AND‑запити між кількома сутностями
- `contradict` — автоматичне виявлення конфліктних фактів
- Оцінка довіри з асиметричним зворотним зв’язком (+0.05 helpful / -0.10 unhelpful)
### RetainDB

API хмарної пам’яті з гібридним пошуком (Vector + BM25 + Reranking), 7 типів пам’яті та дельта‑компресією.

| | |
|---|---|
| **Оптимально підходить для** | Команд, які вже використовують інфраструктуру RetainDB |
| **Вимоги** | Обліковий запис RetainDB + API‑ключ |
| **Зберігання даних** | RetainDB Cloud |
| **Вартість** | $20/місяць |

**Інструменти:** `retaindb_profile` (профіль користувача), `retaindb_search` (семантичний пошук), `retaindb_context` (контекст, релевантний завданню), `retaindb_remember` (зберігання з типом та важливістю), `retaindb_forget` (видалення пам’яті)

**Налаштування:**
```bash
hermes memory setup    # select "retaindb"
# Or manually:
hermes config set memory.provider retaindb
echo "RETAINDB_API_KEY=your-key" >> ~/.hermes/.env
```

---
### ByteRover

Постійна пам'ять через CLI `brv` — ієрархічне дерево знань з багаторівневим отриманням (нечіткий текст → пошук, керований LLM). Локально‑перша з можливістю синхронізації в хмару.

| | |
|---|---|
| **Краще підходить** | Розробники, які хочуть портативну, локально‑першу пам'ять з CLI |
| **Вимоги** | ByteRover CLI (`npm install -g byterover-cli` або [install script](https://byterover.dev)) |
| **Зберігання даних** | Локально (за замовчуванням) або ByteRover Cloud (опційна синхронізація) |
| **Вартість** | Безкоштовно (локально) або за тарифами ByteRover (хмара) |

**Інструменти:** `brv_query` (пошук у дереві знань), `brv_curate` (зберігання фактів/рішень/шаблонів), `brv_status` (версія CLI + статистика дерева)

**Налаштування:**
```bash
# Install the CLI first
curl -fsSL https://byterover.dev/install.sh | sh

# Then configure Hermes
hermes memory setup    # select "byterover"
# Or manually:
hermes config set memory.provider byterover
```

**Ключові особливості:**
- Автоматичне попереднє стискання та вилучення (зберігає інсайти до того, як стискання контексту їх видалить)
- Дерево знань зберігається у `$HERMES_HOME/byterover/` (в межах профілю)
- Сертифікована SOC2 Type II хмарна синхронізація (опційно)
### Supermemory

Семантична довготривала пам'ять із відновленням профілю, семантичним пошуком, інструментами явної пам'яті та збором розмови в кінці сесії через API графа Supermemory.

| | |
|---|---|
| **Best for** | Семантичне відновлення з профілюванням користувачів та побудовою графа на рівні сесії |
| **Requires** | `pip install supermemory` + [API key](https://supermemory.ai) |
| **Data storage** | Supermemory Cloud |
| **Cost** | Supermemory pricing |

**Tools:** `supermemory_store` (зберігати явні спогади), `supermemory_search` (семантичний пошук схожості), `supermemory_forget` (забути за ID або запитом найкращого збігу), `supermemory_profile` (постійний профіль + недавній контекст)

**Setup:**
```bash
hermes memory setup    # select "supermemory"
# Or manually:
hermes config set memory.provider supermemory
echo 'SUPERMEMORY_API_KEY=***' >> ~/.hermes/.env
```

**Config:** `$HERMES_HOME/supermemory.json`

| Key | Default | Description |
|-----|---------|-------------|
| `container_tag` | `hermes` | Тег контейнера, що використовується для пошуку та запису. Підтримує шаблон `{identity}` для тегів, прив'язаних до профілю. |
| `auto_recall` | `true` | Вставляє релевантний контекст пам'яті перед ходами |
| `auto_capture` | `true` | Зберігає очищені діалоги користувач‑асистент після кожної відповіді |
| `max_recall_results` | `10` | Максимальна кількість відновлених елементів, які формуються у контекст |
| `profile_frequency` | `50` | Додавати факти профілю у першому ході та кожні N ходів |
| `capture_mode` | `all` | За замовчуванням пропускати малі або тривіальні ходи |
| `search_mode` | `hybrid` | Режим пошуку: `hybrid`, `memories` або `documents` |
| `api_timeout` | `5.0` | Тайм‑аут для SDK та запитів інжесту |

**Environment variables:** `SUPERMEMORY_API_KEY` (обов’язково), `SUPERMEMORY_CONTAINER_TAG` (перезаписує конфігурацію).

**Key features:**
- Автоматичне обмеження контексту — видаляє відновлені спогади з захоплених ходів, щоб запобігти рекурсивному забрудненню пам'яті
- Збір розмови в кінці сесії для більш багатого побудови знань на рівні графа
- Факти профілю вставляються у першому ході та за налаштованими інтервалами
- Фільтрація тривіальних повідомлень (пропускає «ok», «thanks» тощо)
- **Контейнери, прив'язані до профілю** — використовуйте `{identity}` у `container_tag` (наприклад `hermes-{identity}` → `hermes-coder`) для ізоляції спогадів per Hermes profile
- **Multi‑container mode** — увімкніть `enable_custom_container_tags` зі списком `custom_containers`, щоб агент міг читати/писати в різних іменованих контейнерах. Автоматичні операції (синхронізація, попереднє завантаження) залишаються у первинному контейнері.

<details>
<summary>Multi‑container example</summary>

```json
{
  "container_tag": "hermes",
  "enable_custom_container_tags": true,
  "custom_containers": ["project-alpha", "shared-knowledge"],
  "custom_container_instructions": "Use project-alpha for coding context."
}
```

</details>

**Support:** [Discord](https://supermemory.link/discord) · [support@supermemory.com](mailto:support@supermemory.com)
### Memori

Структурована довготривала пам'ять за допомогою Memori Cloud, з захопленням завершених ходів у фоні, контекстом ходів, що враховує інструменти, та явними інструментами виклику для фактів, резюме, квоти, реєстрації та зворотного зв’язку.

| | |
|---|---|
| **Best for** | Відновлення, контрольоване агентом, зі структурованою атрибуцією проєкту та сесії |
| **Requires** | `pip install hermes-memori` + `hermes-memori install` + [Memori API key](https://app.memorilabs.ai/signup) |
| **Data storage** | Memori Cloud |
| **Cost** | Memori pricing |

**Tools:** `memori_recall` (search long-term memory), `memori_recall_summary` (summarized context), `memori_quota` (usage/quota), `memori_signup` (request signup email), `memori_feedback` (send integration feedback)

**Setup:**
```bash
pip install hermes-memori
hermes-memori install
hermes config set memory.provider memori
hermes memory setup
```

---
## Порівняння провайдерів

| Провайдер | Сховище | Вартість | Інструменти | Залежності | Унікальна особливість |
|----------|---------|----------|-------------|------------|------------------------|
| **Honcho** | Хмара | Платно | 5 | `honcho-ai` | Діалектичне моделювання користувача + контекст, прив’язаний до сесії |
| **OpenViking** | Самостійно розгорнутий | Безкоштовно | 5 | `openviking` + server | Ієрархія файлової системи + багаторівневе завантаження |
| **Mem0** | Хмара | Платно | 3 | `mem0ai` | Витяг LLM на боці сервера |
| **Hindsight** | Хмара/Локально | Безкоштовно/Платно | 3 | `hindsight-client` | Граф знань + синтез рефлексії |
| **Holographic** | Локально | Безкоштовно | 2 | None | Алгебра HRR + оцінка довіри |
| **RetainDB** | Хмара | $20/mo | 5 | `requests` | Дельта-стиснення |
| **ByteRover** | Локально/Хмара | Безкоштовно/Платно | 3 | `brv` CLI | Витяг перед стисканням |
| **Supermemory** | Хмара | Платно | 4 | `supermemory` | Обмеження контексту + інжест графа сесій + мульти‑контейнер |
| **Memori** | Хмара | Безкоштовно/Платно | 5 | `hermes-memori` | Пам'ять, орієнтована на інструменти + структуроване відтворення |
## Ізоляція профілю

Кожного провайдера дані ізольовані окремо для кожного [profile](/user-guide/profiles):

- **Local storage providers** (Holographic, ByteRover) використовують шляхи `$HERMES_HOME/`, які різняться між профілями
- **Config file providers** (Honcho, Mem0, Hindsight, Supermemory) зберігають конфігурацію в `$HERMES_HOME/`, тому у кожного профілю свої облікові дані
- **Cloud providers** (RetainDB) автоматично формують назви проєктів, прив’язані до профілю
- **Env var providers** (OpenViking) налаштовуються через `.env`‑файл кожного профілю
## Створення провайдера пам’яті

Дивись [Посібник розробника: Плагіни провайдерів пам’яті](/developer-guide/memory-provider-plugin), щоб створити свій власний.