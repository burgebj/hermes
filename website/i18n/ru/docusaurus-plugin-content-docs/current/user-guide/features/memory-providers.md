---
sidebar_position: 4
title: "Поставщики памяти"
description: "Внешние плагины поставщика памяти — Honcho, OpenViking, Mem0, Hindsight, Holographic, RetainDB, ByteRover, Supermemory"
---

# Поставщики памяти

Hermes Agent поставляется с 8 внешними плагинами‑поставщиками памяти, которые дают агенту постоянные знания, сохраняющиеся между сессиями, — вне рамок встроенных MEMORY.md и USER.md. Одновременно может быть активен **только один** внешний поставщик — встроенная память всегда активна вместе с ним.
## Быстрый старт

```bash
hermes memory setup      # interactive picker + configuration
hermes memory status     # check what's active
hermes memory off        # disable external provider
```

Ты также можешь выбрать активный провайдер памяти через `hermes plugins` → Provider Plugins → Memory Provider.

Или задать его вручную в `~/.hermes/config.yaml`:

```yaml
memory:
  provider: openviking   # or honcho, mem0, hindsight, holographic, retaindb, byterover, supermemory
```
## Как это работает

Когда провайдер памяти активен, Hermes автоматически:

1. **Внедряет контекст провайдера** в системный запрос (что знает провайдер)
2. **Предзагружает релевантные воспоминания** перед каждым ходом (в фоне, без блокировки)
3. **Синхронно отправляет ходы разговора** провайдеру после каждого ответа
4. **Извлекает воспоминания в конце сессии** (для провайдеров, которые это поддерживают)
5. **Отзеркаливает записи встроенной памяти** во внешнего провайдера
6. **Добавляет специфичные для провайдера инструменты**, чтобы агент мог искать, сохранять и управлять памятью

Встроенная память (MEMORY.md / USER.md) продолжает работать точно так же, как и раньше. Внешний провайдер является добавочным.
## Доступные провайдеры

### Honcho

AI‑нативное кросс‑сессионное моделирование пользователя с диалектическим рассуждением, внедрением контекста в пределах сессии, семантическим поиском и постоянными выводами. Базовый контекст теперь включает резюме сессии вместе с представлением пользователя и карточками пиров, давая агенту осведомлённость о том, что уже обсуждалось.

| | |
|---|---|
| **Лучше всего подходит** | Мультиагентные системы с кросс‑сессионным контекстом, согласованность пользователь‑агент |
| **Требования** | `pip install honcho-ai` + [API‑ключ](https://app.honcho.dev) или самостоятельный экземпляр |
| **Хранение данных** | Honcho Cloud или самостоятельный |
| **Стоимость** | Цены Honcho (облако) / бесплатно (самостоятельный) |

**Инструменты (5):** `honcho_profile` (чтение/обновление карточки пира), `honcho_search` (семантический поиск), `honcho_context` (контекст сессии — резюме, представление, карточка, сообщения), `honcho_reasoning` (LLM‑синтез), `honcho_conclude` (создание/удаление выводов)

**Архитектура:** Двухуровневое внедрение контекста — базовый слой (резюме сессии + представление + карточка пира, обновляется по `contextCadence`) плюс диалектическое дополнение (рассуждение LLM, обновляется по `dialecticCadence`). Диалектический механизм автоматически выбирает холодные подсказки (общие факты о пользователе) или тёплые подсказки (контекст в пределах сессии) в зависимости от наличия базового контекста.

**Три независимых параметра конфигурации** управляют стоимостью и глубиной независимо:

- `contextCadence` — как часто обновляется базовый слой (частота API‑вызовов)
- `dialecticCadence` — как часто срабатывает диалектический LLM (частота вызовов LLM)
- `dialecticDepth` — сколько проходов `.chat()` выполняется за один диалектический вызов (1–3, глубина рассуждения)

**Мастер настройки:**
```bash
hermes memory setup        # select "honcho" — runs the Honcho-specific post-setup
```

Устаревшая команда `hermes honcho setup` всё ещё работает (теперь перенаправляет на `hermes memory setup`), но регистрируется только после выбора Honcho в качестве активного провайдера памяти.

**Конфигурация:** `$HERMES_HOME/honcho.json` (локальная для профиля) или `~/.honcho/config.json` (глобальная). Порядок разрешения: `$HERMES_HOME/honcho.json` > `~/.hermes/honcho.json` > `~/.honcho/config.json`. См. [справочник конфигурации](https://github.com/hermes-ai/hermes-agent/blob/main/plugins/memory/honcho/README.md) и [руководство по интеграции Honcho](https://docs.honcho.dev/v3/guides/integrations/hermes).

<details>
<summary>Полный справочник конфигурации</summary>

| Ключ | По умолчанию | Описание |
|-----|--------------|----------|
| `apiKey` | -- | API‑ключ из [app.honcho.dev](https://app.honcho.dev) |
| `baseUrl` | -- | Базовый URL для самостоятельного Honcho |
| `peerName` | -- | Идентификатор пользовательского пира |
| `aiPeer` | host key | Идентификатор AI‑пира (по одному на профиль) |
| `workspace` | host key | Идентификатор общего рабочего пространства |
| `contextTokens` | `null` (без ограничения) | Бюджет токенов для автоматически внедряемого контекста за ход. Обрезается на границах слов |
| `contextCadence` | `1` | Минимальное количество ходов между вызовами `context()` (обновление базового слоя) |
| `dialecticCadence` | `2` | Минимальное количество ходов между вызовами `peer.chat()` LLM. Рекомендуется 1–5. Применяется только к режимам `hybrid`/`context` |
| `dialecticDepth` | `1` | Количество проходов `.chat()` за диалектический вызов. Ограничено 1–3. Проход 0: холодная/тёплая подсказка, проход 1: самопроверка, проход 2: согласование |
| `dialecticDepthLevels` | `null` | Необязательный массив уровней рассуждения для каждого прохода, например `["minimal", "low", "medium"]`. Переопределяет пропорциональные значения по умолчанию |
| `dialecticReasoningLevel` | `'low'` | Базовый уровень рассуждения: `minimal`, `low`, `medium`, `high`, `max` |
| `dialecticDynamic` | `true` | При `true` модель может переопределять уровень рассуждения для каждого вызова через параметр инструмента |
| `dialecticMaxChars` | `600` | Максимальное количество символов диалектического результата, внедряемого в системный промпт |
| `recallMode` | `'hybrid'` | `hybrid` (авто‑внедрение + инструменты), `context` (только внедрение), `tools` (только инструменты) |
| `writeFrequency` | `'async'` | Когда сбрасывать сообщения: `async` (фоновый поток), `turn` (синхронно), `session` (пакетно в конце), либо целое N |
| `saveMessages` | `true` | Сохранять ли сообщения в API Honcho |
| `observationMode` | `'directional'` | `directional` (все включены) или `unified` (общий пул). Переопределяется объектом `observation` |
| `messageMaxChars` | `25000` | Максимум символов в сообщении (при превышении разбивается на чанки) |
| `dialecticMaxInputChars` | `10000` | Максимум символов входных данных диалектики для `peer.chat()` |
| `sessionStrategy` | `'per-directory'` | `per-directory`, `per-repo`, `per-session`, `global` |
</details>

<details>
<summary>Минимальный honcho.json (облако)</summary>

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
<summary>Минимальный honcho.json (самостоятельный)</summary>

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

:::tip Миграция из `hermes honcho`
Если ты ранее использовал `hermes honcho setup`, твоя конфигурация и все серверные данные сохранены. Просто снова включи их через мастер настройки или вручную установи `memory.provider: honcho`, чтобы активировать в новой системе.
:::

**Настройка мульти‑пиров:**

Honcho моделирует диалоги как обмен сообщениями между пирами — один пользовательский пир плюс один AI‑пир на каждый профиль Hermes, все они используют общее рабочее пространство. Рабочее пространство — общая среда: пользовательский пир глобален для всех профилей, каждый AI‑пир имеет свою собственную личность. Каждый AI‑пир формирует независимое представление/карточку из собственных наблюдений, поэтому профиль `coder` остаётся ориентированным на код, а профиль `writer` — на редактуру, даже при работе с тем же пользователем.

| Понятие | Что это |
|---------|----------|
| **Workspace** | Общая среда. Все профили Hermes в одном рабочем пространстве видят одну и ту же пользовательскую личность. |
| **User peer** (`peerName`) | Человек. Общий для всех профилей в рабочем пространстве. |
| **AI peer** (`aiPeer`) | По одному на профиль Hermes. Ключ хоста `hermes` → по умолчанию; `hermes.<profile>` — для остальных. |
| **Observation** | Переключатели пиров, определяющие, что Honcho моделирует из чьих сообщений. `directional` (по умолчанию, все четыре включены) или `unified` (единственный пул наблюдателя). |

### Новый профиль, свежий пир Honcho

```bash
hermes profile create coder --clone
```

`--clone` создаёт блок хоста `hermes.coder` в `honcho.json` с `aiPeer: "coder"`, общим `workspace`, унаследованным `peerName`, `recallMode`, `writeFrequency`, `observation` и т.д. AI‑пир создаётся в Honcho заранее, до первого сообщения.

### Существующие профили, заполнение пиров Honcho

```bash
hermes honcho sync
```

Сканирует каждый профиль Hermes, создаёт блоки хостов для профилей без них, наследует настройки из блока `hermes` по умолчанию и создаёт новые AI‑пиры сразу. Идемпотентно — пропускает профили, у которых уже есть блок хоста.

### Наблюдение per‑profile

Каждый блок хоста может независимо переопределять конфигурацию наблюдения. Пример: профиль, ориентированный на код, где AI‑пир наблюдает за пользователем, но не моделирует себя:

```json
"hermes.coder": {
  "aiPeer": "coder",
  "observation": {
    "user": { "observeMe": true, "observeOthers": true },
    "ai":   { "observeMe": false, "observeOthers": true }
  }
}
```

**Переключатели наблюдения (по одному набору на пир):**

| Переключатель | Эффект |
|----------------|--------|
| `observeMe` | Honcho строит представление этого пира из его собственных сообщений |
| `observeOthers` | Этот пир наблюдает сообщения другого пира (подаёт данные для кросс‑пирного рассуждения) |

Пресеты через `observationMode`:

- **`"directional"`** (по умолчанию) — все четыре флага включены. Полное взаимное наблюдение; включает кросс‑пирный диалектический процесс.
- **`"unified"`** — пользователь `observeMe: true`, AI `observeOthers: true`, остальные — false. Один пул наблюдателя; AI моделирует пользователя, но не себя, пользователь моделирует только себя.

Переключения, установленные на сервере через [панель управления Honcho](https://app.honcho.dev), имеют приоритет над локальными значениями — они синхронно подгружаются при инициализации сессии.

См. [страницу Honcho](./honcho.md#observation-directional-vs-unified) для полного справочника по наблюдению.

<details>
<summary>Полный пример honcho.json (мульти‑профиль)</summary>

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

См. [справочник конфигурации](https://github.com/hermes-ai/hermes-agent/blob/main/plugins/memory/honcho/README.md) и [руководство по интеграции Honcho](https://docs.honcho.dev/v3/guides/integrations/hermes).

---

### OpenViking

База контекста от Volcengine (ByteDance) с иерархией знаний в стиле файловой системы, уровневым извлечением и автоматическим выделением памяти в 6 категорий.

| | |
|---|---|
| **Лучше всего подходит** | Самостоятельное управление знаниями со структурированным просмотром |
| **Требования** | `pip install openviking` + запущенный сервер |
| **Хранение данных** | Самостоятельный (локально или в облаке) |
| **Стоимость** | Бесплатно (open‑source, AGPL‑3.0) |

**Инструменты:** `viking_search` (семантический поиск), `viking_read` (уровневый: абстракт/обзор/полный), `viking_browse` (навигация по файловой системе), `viking_remember` (сохранение фактов), `viking_add_resource` (импорт URL/документов)

**Настройка:**
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

**Ключевые возможности:**
- Уровневое загрузка контекста: L0 (~100 токенов) → L1 (~2 k) → L2 (полный)
- Автоматическое извлечение памяти при фиксации сессии (профиль, предпочтения, сущности, события, кейсы, паттерны)
- Схема URI `viking://` для иерархического просмотра знаний

---

### Mem0

Серверный LLM‑экстрактор фактов с семантическим поиском, переранжированием и автоматическим удалением дубликатов.

| | |
|---|---|
| **Лучше всего подходит** | Полностью автоматическое управление памятью — Mem0 сам обрабатывает извлечение |
| **Требования** | `pip install mem0ai` + API‑ключ |
| **Хранение данных** | Mem0 Cloud |
| **Стоимость** | Цены Mem0 |

**Инструменты:** `mem0_profile` (все сохранённые воспоминания), `mem0_search` (семантический поиск + переранжирование), `mem0_conclude` (сохранение дословных фактов)

**Настройка:**
```bash
hermes memory setup    # select "mem0"
# Or manually:
hermes config set memory.provider mem0
echo "MEM0_API_KEY=your-key" >> ~/.hermes/.env
```

**Конфигурация:** `$HERMES_HOME/mem0.json`

| Ключ | По умолчанию | Описание |
|-----|--------------|----------|
| `user_id` | `hermes-user` | Идентификатор пользователя |
| `agent_id` | `hermes` | Идентификатор агента |

---

### Hindsight

Долгосрочная память с графом знаний, разрешением сущностей и мульти‑стратегическим поиском. Инструмент `hindsight_reflect` обеспечивает кросс‑памятное синтезирование, недоступное у других провайдеров. Автоматически сохраняет полные ходы диалога (включая вызовы инструментов) с отслеживанием документов на уровне сессии.

| | |
|---|---|
| **Лучше всего подходит** | Поиск по графу знаний с отношениями между сущностями |
| **Требования** | Облако: API‑ключ из [ui.hindsight.vectorize.io](https://ui.hindsight.vectorize.io). Локально: API‑ключ LLM (OpenAI, Groq, OpenRouter и др.) |
| **Хранение данных** | Hindsight Cloud или локальная встроенная PostgreSQL |
| **Стоимость** | Цены Hindsight (облако) или бесплатно (локально) |

**Инструменты:** `hindsight_retain` (сохранение с извлечением сущностей), `hindsight_recall` (мульти‑стратегический поиск), `hindsight_reflect` (кросс‑памятное синтезирование)

**Настройка:**
```bash
hermes memory setup    # select "hindsight"
# Or manually:
hermes config set memory.provider hindsight
echo "HINDSIGHT_API_KEY=your-key" >> ~/.hermes/.env
```

Мастер установки автоматически ставит зависимости, необходимые только для выбранного режима (`hindsight-client` — облако, `hindsight-all` — локально). Требуется `hindsight-client >= 0.4.22` (авто‑обновляется при старте сессии, если устарел).

**Локальный UI:** `hindsight-embed -p hermes ui start`

**Конфигурация:** `$HERMES_HOME/hindsight/config.json`

| Ключ | По умолчанию | Описание |
|-----|--------------|----------|
| `mode` | `cloud` | `cloud` или `local` |
| `bank_id` | `hermes` | Идентификатор банка памяти |
| `recall_budget` | `mid` | Тщательность поиска: `low` / `mid` / `high` |
| `memory_mode` | `hybrid` | `hybrid` (контекст + инструменты), `context` (только авто‑внедрение), `tools` (только инструменты) |
| `auto_retain` | `true` | Автоматически сохранять ходы диалога |
| `auto_recall` | `true` | Автоматически извлекать память перед каждым ходом |
| `retain_async` | `true` | Обрабатывать сохранение асинхронно на сервере |
| `retain_context` | `conversation between Hermes Agent and the User` | Метка контекста для сохраняемых воспоминаний |
| `retain_tags` | — | Теги по умолчанию, применяемые к сохраняемым воспоминаниям; объединяются с тегами инструмента |
| `retain_source` | — | Необязательный `metadata.source`, прикрепляемый к сохраняемым воспоминаниям |
| `retain_user_prefix` | `User` | Метка перед пользовательскими ходами в авто‑сохраняемых транскриптах |
| `retain_assistant_prefix` | `Assistant` | Метка перед ходами ассистента в авто‑сохраняемых транскриптах |
| `recall_tags` | — | Теги для фильтрации при извлечении |

См. [README плагина](https://github.com/NousResearch/hermes-agent/blob/main/plugins/memory/hindsight/README.md) для полного справочника конфигурации.

---

### Holographic

Локальное хранилище фактов SQLite с полнотекстовым поиском FTS5, оценкой доверия и HRR (Holographic Reduced Representations) для композиционных алгебраических запросов.

| | |
|---|---|
| **Лучше всего подходит** | Локальная память только с продвинутым поиском, без внешних зависимостей |
| **Требования** | Ничего (SQLite всегда доступен). NumPy опционально для HRR‑алгебры. |
| **Хранение данных** | Локальный SQLite |
| **Стоимость** | Бесплатно |

**Инструменты:** `fact_store` (9 действий: add, search, probe, related, reason, contradict, update, remove, list), `fact_feedback` (оценка полезности, обучающая доверительные баллы)

**Настройка:**
```bash
hermes memory setup    # select "holographic"
# Or manually:
hermes config set memory.provider holographic
```

**Конфигурация:** `config.yaml` в `plugins.hermes-memory-store`

| Ключ | По умолчанию | Описание |
|-----|--------------|----------|
| `db_path` | `$HERMES_HOME/memory_store.db` | Путь к базе SQLite |
| `auto_extract` | `false` | Авто‑извлечение фактов в конце сессии |
| `default_trust` | `0.5` | Доверительный балл по умолчанию (0.0–1.0) |

**Уникальные возможности:**
- `probe` — алгебраическое воспоминание по конкретной сущности (все факты о человеке/вещи)
- `reason` — композиционные запросы AND между несколькими сущностями
- `contradict` — автоматическое обнаружение противоречивых фактов
- Оценка доверия с асимметричной обратной связью (+0.05 полезно / -0.10 не полезно)

---

### RetainDB

Облачный API памяти с гибридным поиском (Vector + BM25 + Reranking), 7 типами памяти и дельта‑компрессией.

| | |
|---|---|
| **Лучше всего подходит** | Команды, уже использующие инфраструктуру RetainDB |
| **Требования** | Учётная запись RetainDB + API‑ключ |
| **Хранение данных** | RetainDB Cloud |
| **Стоимость** | $20/мес |

**Инструменты:** `retaindb_profile` (профиль пользователя), `retaindb_search` (семантический поиск), `retaindb_context` (контекст, релевантный задаче), `retaindb_remember` (сохранение с типом + важностью), `retaindb_forget` (удаление воспоминаний)

**Настройка:**
```bash
hermes memory setup    # select "retaindb"
# Or manually:
hermes config set memory.provider retaindb
echo "RETAINDB_API_KEY=your-key" >> ~/.hermes/.env
```

---

### ByteRover

Постоянная память через CLI `brv` — иерархическое дерево знаний с уровневым извлечением (нечёткий текст → поиск, управляемый LLM). Локально‑первоочередно с опциональной синхронизацией в облаке.

| | |
|---|---|
| **Лучше всего подходит** | Разработчики, желающие портативную локальную память с CLI |
| **Требования** | ByteRover CLI (`npm install -g byterover-cli` или [скрипт установки](https://byterover.dev)) |
| **Хранение данных** | Локально (по умолчанию) или ByteRover Cloud (опциональная синхронизация) |
| **Стоимость** | Бесплатно (локально) или цены ByteRover (облако) |

**Инструменты:** `brv_query` (поиск по дереву знаний), `brv_curate` (сохранение фактов/решений/паттернов), `brv_status` (версия CLI + статистика дерева)

**Настройка:**
```bash
# Install the CLI first
curl -fsSL https://byterover.dev/install.sh | sh

# Then configure Hermes
hermes memory setup    # select "byterover"
# Or manually:
hermes config set memory.provider byterover
```

**Ключевые возможности:**
- Автоматическое предкомпрессирующее извлечение (сохраняет инсайты до того, как сжатие контекста их удалит)
- Дерево знаний хранится в `$HERMES_HOME/byterover/` (по профилю)
- Облачная синхронизация сертифицирована SOC2 Type II (опционально)

---

### Supermemory

Семантическая долгосрочная память с профилем recall, семантическим поиском, явными инструментами памяти и загрузкой диалогов в конце сессии через графовый API Supermemory.

| | |
|---|---|
| **Лучше всего подходит** | Семантическое воспоминание с профилированием пользователя и построением графа на уровне сессии |
| **Требования** | `pip install supermemory` + [API‑ключ](https://supermemory.ai) |
| **Хранение данных** | Supermemory Cloud |
| **Стоимость** | Цены Supermemory |

**Инструменты:** `supermemory_store` (сохранение явных воспоминаний), `supermemory_search` (поиск по семантическому сходству), `supermemory_forget` (удаление по ID или лучшему совпадению), `supermemory_profile` (постоянный профиль + недавний контекст)

**Настройка:**
```bash
hermes memory setup    # select "supermemory"
# Or manually:
hermes config set memory.provider supermemory
echo 'SUPERMEMORY_API_KEY=***' >> ~/.hermes/.env
```

**Конфигурация:** `$HERMES_HOME/supermemory.json`

| Ключ | По умолчанию | Описание |
|-----|--------------|----------|
| `container_tag` | `hermes` | Тег контейнера, используемый для поиска и записи. Поддерживает шаблон `{identity}` для профильно‑ограниченных тегов. |
| `auto_recall` | `true` | Внедрять релевантный контекст памяти перед ходами |
| `auto_capture` | `true` | Сохранять очищенные пользователь‑ассистентские ходы после каждого ответа |
| `max_recall_results` | `10` | Максимальное количество найденных элементов для формирования контекста |
| `profile_frequency` | `50` | Включать факты профиля в первом ходе и каждые N ходов |
| `capture_mode` | `all` | По умолчанию пропускать мелкие или тривиальные ходы |
| `search_mode` | `hybrid` | Режим поиска: `hybrid`, `memories` или `documents` |
| `api_timeout` | `5.0` | Таймаут для SDK и запросов ingest |

**Переменные окружения:** `SUPERMEMORY_API_KEY` (обязательно), `SUPERMEMORY_CONTAINER_TAG` (переопределяет конфиг).

**Ключевые возможности:**
- Автоматическое ограничение контекста — удаляет извлечённые воспоминания из захваченных ходов, предотвращая рекуррентное загрязнение памяти
- Загрузка диалогов в конце сессии для обогащения графа знаний
- Внедрение фактов профиля в первом ходе и через настраиваемые интервалы
- Фильтрация тривиальных сообщений (пропуск «ok», «thanks» и т.п.)
- **Контейнеры, ограниченные профилем** — используй `{identity}` в `container_tag` (например `hermes-{identity}` → `hermes-coder`) для изоляции памяти по профилям Hermes
- **Мульти‑контейнерный режим** — включи `enable_custom_container_tags` с массивом `custom_containers`, чтобы агент мог читать/писать в несколько именованных контейнеров. Авто‑операции (синхронизация, предзагрузка) остаются на основном контейнере.

<details>
<summary>Пример мульти‑контейнеров</summary>

```json
{
  "container_tag": "hermes",
  "enable_custom_container_tags": true,
  "custom_containers": ["project-alpha", "shared-knowledge"],
  "custom_container_instructions": "Use project-alpha for coding context."
}
```

</details>

**Поддержка:** [Discord](https://supermemory.link/discord) · [support@supermemory.com](mailto:support@supermemory.com)

### Memori

Структурированная долгосрочная память на базе Memori Cloud, с захватом завершённых ходов в фоне, контекстом, учитывающим инструменты, и явными инструментами recall для фактов, резюме, квот, регистрации и обратной связи.

| | |
|---|---|
| **Лучше всего подходит** | Управление воспоминаниями агентом с проектной и сессионной атрибуцией |
| **Требования** | `pip install hermes-memori` + `hermes-memori install` + [API‑ключ Memori](https://app.memorilabs.ai/signup) |
| **Хранение данных** | Memori Cloud |
| **Стоимость** | Цены Memori |

**Инструменты:** `memori_recall` (поиск в долгосрочной памяти), `memori_recall_summary` (контекст в виде резюме), `memori_quota` (использование/квоты), `memori_signup` (запрос email для регистрации), `memori_feedback` (отправка обратной связи по интеграции)

**Настройка:**
```bash
pip install hermes-memori
hermes-memori install
hermes config set memory.provider memori
hermes memory setup
```
## Сравнение провайдеров

| Провайдер | Хранилище | Стоимость | Инструменты | Зависимости | Уникальная особенность |
|----------|-----------|-----------|-------------|-------------|------------------------|
| **Honcho** | Облако | Платно | 5 | `honcho-ai` | Диалектическое моделирование пользователя + контекст, ограниченный сессией |
| **OpenViking** | Самохостинг | Бесплатно | 5 | `openviking` + server | Иерархия файловой системы + поуровневая загрузка |
| **Mem0** | Облако | Платно | 3 | `mem0ai` | Извлечение LLM на стороне сервера |
| **Hindsight** | Облако/Локально | Бесплатно/Платно | 3 | `hindsight-client` | Граф знаний + синтез отражения |
| **Holographic** | Локально | Бесплатно | 2 | None | Алгебра HRR + оценка доверия |
| **RetainDB** | Облако | $20/mo | 5 | `requests` | Дельта‑компрессия |
| **ByteRover** | Локально/Облако | Бесплатно/Платно | 3 | `brv` CLI | Извлечение перед сжатием |
| **Supermemory** | Облако | Платно | 4 | `supermemory` | Ограничение контекста + загрузка графа сессий + мультиконтейнер |
| **Memori** | Облако | Бесплатно/Платно | 5 | `hermes-memori` | Память, учитывающая инструменты + структурированный вызов |
## Изоляция профилей

Данные каждого провайдера изолированы **для** [профиля](/user-guide/profiles):

- **Local storage providers** (Holographic, ByteRover) используют пути `$HERMES_HOME/`, которые различаются для каждого профиля
- **Config file providers** (Honcho, Mem0, Hindsight, Supermemory) хранят конфигурацию в `$HERMES_HOME/`, поэтому у каждого профиля свои учётные данные
- **Cloud providers** (RetainDB) автоматически формируют имена проектов, привязанные к профилю
- **Env var providers** (OpenViking) настраиваются через файл `.env` каждого профиля
## Создание провайдера памяти

См. [Руководство разработчика: Плагины провайдеров памяти](/developer-guide/memory-provider-plugin) для создания собственного.