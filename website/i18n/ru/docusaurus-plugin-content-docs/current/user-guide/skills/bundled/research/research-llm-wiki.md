---
title: "Llm Wiki — Wiki Карпати: построение/запрос взаимосвязанной markdown базы знаний"
sidebar_label: "Llm Wiki"
description: "Wiki LLM Карпати: создание/запрос взаимосвязанной markdown KB"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Llm Wiki

Karpathy's LLM Wiki: построить/запросить взаимосвязанную базу знаний в формате markdown.
## Метаданные навыка

| | |
|---|---|
| Источник | Встроенный (устанавливается по умолчанию) |
| Путь | `skills/research/llm-wiki` |
| Версия | `2.1.0` |
| Автор | Hermes Agent |
| Лицензия | MIT |
| Платформы | linux, macos, windows |
| Теги | `wiki`, `knowledge-base`, `research`, `notes`, `markdown`, `rag-alternative` |
| Связанные навыки | [`obsidian`](/docs/user-guide/skills/bundled/note-taking/note-taking-obsidian), [`arxiv`](/docs/user-guide/skills/bundled/research/research-arxiv) |
:::info
Следующее — полное определение навыка, которое Hermes загружает при срабатывании этого навыка. Это то, что агент видит как инструкции, когда навык активен.
:::

# Вики LLM Карпати

Создавай и поддерживай постоянную, нарастающую базу знаний в виде взаимосвязанных markdown‑файлов.
Основано на [шаблоне LLM Wiki Андрея Карпати](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

В отличие от традиционного RAG (который заново открывает знания с нуля для каждого запроса), вики
компилирует знания один раз и поддерживает их актуальность. Перекрёстные ссылки уже созданы.
Противоречия уже помечены. Синтез отражает всё, что было поглощено.

**Разделение труда:** человек курирует источники и задаёт направление анализа. Агент резюмирует, создаёт перекрёстные ссылки, сохраняет файлы и поддерживает согласованность.
## Когда активируется этот skill

Используй этот skill, когда пользователь:
- Просит создать, собрать или запустить вики или базу знаний
- Просит импортировать, добавить или обработать источник в их вики
- Задает вопрос, а существующая вики находится по настроенному пути
- Просит выполнить lint, аудит или проверку состояния их вики
- Ссылается на свою вики, базу знаний или «заметки» в исследовательском контексте
## Расположение вики

**Расположение:** задаётся переменной окружения `WIKI_PATH` (например, в `~/.hermes/.env`).

Если переменная не задана, используется значение по умолчанию — `~/wiki`.

```bash
WIKI="${WIKI_PATH:-$HOME/wiki}"
```

Вики — это просто каталог markdown‑файлов; открой его в Obsidian, VS Code или любом другом редакторе. Нет базы данных, нет специального инструментария.
## Архитектура: три уровня

<!-- ascii-guard-ignore -->
```
wiki/
├── SCHEMA.md           # Conventions, structure rules, domain config
├── index.md            # Sectioned content catalog with one-line summaries
├── log.md              # Chronological action log (append-only, rotated yearly)
├── raw/                # Layer 1: Immutable source material
│   ├── articles/       # Web articles, clippings
│   ├── papers/         # PDFs, arxiv papers
│   ├── transcripts/    # Meeting notes, interviews
│   └── assets/         # Images, diagrams referenced by sources
├── entities/           # Layer 2: Entity pages (people, orgs, products, models)
├── concepts/           # Layer 2: Concept/topic pages
├── comparisons/        # Layer 2: Side-by-side analyses
└── queries/            # Layer 2: Filed query results worth keeping
```
<!-- ascii-guard-ignore-end -->

**Уровень 1 — Исходные источники:** неизменяемые. Агент читает их, но никогда не изменяет.
**Уровень 2 — Вики:** markdown‑файлы, принадлежащие агенту. Создаваемые, обновляемые и взаимосвязанные агентом.
**Уровень 3 — Схема:** `SCHEMA.md` определяет структуру, конвенции и таксономию тегов.
## Возобновление существующей wiki (CRITICAL — делай это каждый сеанс)

Когда у пользователя уже есть wiki, **всегда ориентируйся перед тем, как что‑то делать**:

① **Прочитай `SCHEMA.md`** — пойми домен, конвенции и таксономию тегов.
② **Прочитай `index.md`** — узнай, какие страницы существуют и какие у них резюме.
③ **Просмотри `log.md`** — прочитай последние 20‑30 записей, чтобы понять недавнюю активность.

```bash
WIKI="${WIKI_PATH:-$HOME/wiki}"
# Orientation reads at session start
read_file "$WIKI/SCHEMA.md"
read_file "$WIKI/index.md"
read_file "$WIKI/log.md" offset=<last 30 lines>
```

Только после ориентации следует выполнять `ingest`, `query` или `lint`. Это предотвращает:
- Создание дублирующих страниц для уже существующих сущностей
- Пропуск перекрёстных ссылок на существующий контент
- Противоречие конвенциям схемы
- Повторение уже задокументированной работы

Для больших wiki (100+ страниц) также запусти быстрый `search_files` по текущей теме перед созданием чего‑либо нового.
## Инициализация новой Wiki

Когда пользователь просит создать или запустить wiki:

1. Определить путь к wiki (из переменной окружения `$WIKI_PATH` или спросить у пользователя; по умолчанию `~/wiki`)
2. Создать вышеописанную структуру каталогов
3. Спросить пользователя, какую область охватывает wiki — будь конкретен
4. Создать `SCHEMA.md`, адаптированный под эту область (см. шаблон ниже)
5. Создать начальный `index.md` с заголовками разделов
6. Создать начальный `log.md` с записью о создании
7. Подтвердить, что wiki готова, и предложить первые источники для загрузки

### Шаблон SCHEMA.md

Адаптировать под область пользователя. Схема ограничивает поведение агента и обеспечивает согласованность:

```markdown
# Wiki Schema

## Domain
[What this wiki covers — e.g., "AI/ML research", "personal health", "startup intelligence"]

## Conventions
- File names: lowercase, hyphens, no spaces (e.g., `transformer-architecture.md`)
- Every wiki page starts with YAML frontmatter (see below)
- Use `[[wikilinks]]` to link between pages (minimum 2 outbound links per page)
- When updating a page, always bump the `updated` date
- Every new page must be added to `index.md` under the correct section
- Every action must be appended to `log.md`
- **Provenance markers:** On pages that synthesize 3+ sources, append `^[raw/articles/source-file.md]`
  at the end of paragraphs whose claims come from a specific source. This lets a reader trace each
  claim back without re-reading the whole raw file. Optional on single-source pages where the
  `sources:` frontmatter is enough.

## Frontmatter
  ```yaml
  ---
  title: Page Title
  created: YYYY-MM-DD
  updated: YYYY-MM-DD
  type: entity | concept | comparison | query | summary
  tags: [from taxonomy below]
  sources: [raw/articles/source-name.md]
  # Optional quality signals:
  confidence: high | medium | low        # how well-supported the claims are
  contested: true                        # set when the page has unresolved contradictions
  contradictions: [other-page-slug]      # pages this one conflicts with
  ---
  ```

`confidence` и `contested` являются необязательными, но рекомендуется использовать их для тем с множеством мнений или быстро меняющихся вопросов. Lint выделяет страницы с `contested: true` и `confidence: low` для проверки, чтобы слабые утверждения не превратились в принятые факты wiki без внимания.

### raw/ Frontmatter

Сырые источники ТАКЖЕ получают небольшой блок frontmatter, чтобы повторные загрузки могли обнаруживать отклонения:

```yaml
---
source_url: https://example.com/article   # original URL, if applicable
ingested: YYYY-MM-DD
sha256: &lt;hex digest of the raw content below the frontmatter>
---
```

`sha256:` позволяет будущей повторной загрузке того же URL пропустить обработку, если содержимое не изменилось, и пометить отклонение, когда оно изменилось. Вычислять хеш только по телу (всё после закрывающего `---`), а не по самому frontmatter.
## Таксономия тегов
[Определи 10–20 основных тегов для области. Добавь новые теги здесь ПРЕЖЕ их использования.]

Пример для AI/ML:
- Models: model, architecture, benchmark, training
- People/Orgs: person, company, lab, open-source
- Techniques: optimization, fine‑tuning, inference, alignment, data
- Meta: comparison, timeline, controversy, prediction

**Правило:** каждый тег на странице должен присутствовать в этой таксономии. Если нужен новый тег, сначала добавь его здесь, а затем используй. Это предотвращает разрастание тегов.
## Пороги страниц
- **Создать страницу**, когда сущность/концепция встречается в 2 и более источниках ИЛИ является центральной в одном источнике
- **Добавить к существующей странице**, когда источник упоминает уже освещённую тему
- **Не создавать страницу** для мимолётных упоминаний, незначительных деталей или вещей, не относящихся к области
- **Разделить страницу**, когда её объём превышает ~200 строк — разбить на подтемы с перекрёстными ссылками
- **Архивировать страницу**, когда её содержание полностью вытеснено — переместить в `_archive/`, удалить из индекса
## Страницы сущностей
Одна страница на каждую значимую сущность. Содержит:
- Обзор / что это
- Ключевые факты и даты
- Отношения с другими сущностями ([[wikilinks]])
- Ссылки на источники
## Страницы концепций
Одна страница на каждую концепцию или тему. Включай:
- Определение / объяснение
- Текущее состояние знаний
- Открытые вопросы или дискуссии
- Связанные концепции ([[wikilinks]])
## Страницы сравнения
Сравнительный анализ «один рядом с другим». Включает:
- Что сравнивается и почему
- Критерии сравнения (предпочтительно в табличном формате)
- Вердикт или синтез
- Источники
## Политика обновления
Когда новая информация противоречит существующему содержимому:
1. Проверь даты — более новые источники обычно заменяют более старые
2. Если противоречие действительно существенное, зафиксируй обе позиции с указанием дат и источников
3. Отметь противоречие во frontmatter: `contradictions: [page-name]`
4. Пометь для проверки пользователем в отчёте lint
```

### index.md Template

The index is sectioned by type. Each entry is one line: wikilink + summary.

```markdown
# Wiki Index

> Content catalog. Every wiki page listed under its type with a one-line summary.
> Read this first to find relevant pages for any query.
> Last updated: YYYY-MM-DD | Total pages: N

## Entities
<!-- Alphabetical within section -->

## Concepts

## Comparisons

## Queries
```

**Правило масштабирования:** Если любой раздел превышает 50 записей, разбей его на подразделы по первой букве или поддомену. Когда общий индекс превышает 200 записей, создай файл `_meta/topic-map.md`, который группирует страницы по темам для более быстрой навигации.

### Шаблон `log.md`

```markdown
# Wiki Log

> Chronological record of all wiki actions. Append-only.
> Format: `## [YYYY-MM-DD] action | subject`
> Actions: ingest, update, query, lint, create, archive, delete
> When this file exceeds 500 entries, rotate: rename to log-YYYY.md, start fresh.

## [YYYY-MM-DD] create | Wiki initialized
- Domain: [domain]
- Structure created with SCHEMA.md, index.md, log.md
```
## Основные операции

### 1. Интеграция

Когда пользователь предоставляет источник (URL, файл, вставка), интегрируй его в вики:

① **Захватить исходный материал:**
   - URL → использовать `web_extract` для получения markdown, сохранить в `raw/articles/`
   - PDF → использовать `web_extract` (обрабатывает PDF), сохранить в `raw/papers/`
   - Вставленный текст → сохранить в соответствующий подкаталог `raw/`
   - Дать файлу описательное имя: `raw/articles/karpathy-llm-wiki-2026.md`
   - **Добавить raw‑frontmatter** (`source_url`, `ingested`, `sha256` тела).
     При повторной интеграции того же URL: пересчитать `sha256`, сравнить с сохранённым значением — пропустить, если идентично, отметить отклонение и обновить, если отличается. Это достаточно дешево, чтобы выполнять при каждой повторной интеграции, и ловит скрытые изменения источника.

② **Обсудить выводы** с пользователем — что интересного, что важно для домена. (Пропустить в автоматических/cron‑контекстах — перейти сразу.)

③ **Проверить, что уже существует** — поискать в `index.md` и использовать `search_files` для нахождения существующих страниц по упомянутым сущностям/концепциям. Это и есть разница между растущей вики и кучей дубликатов.

④ **Создать или обновить страницы вики:**
   - **Новые сущности/концепции:** создавать страницы только если они удовлетворяют порогам в `SCHEMA.md` (2 + упоминания в источниках или центральны для одного источника).
   - **Существующие страницы:** добавлять новую информацию, обновлять факты, обновлять дату `updated`. Когда новая информация противоречит существующему содержимому, следовать Политике обновления.
   - **Кросс‑ссылка:** каждая новая или обновлённая страница должна ссылаться как минимум на 2 другие страницы через `[[wikilinks]]`. Проверить, что существующие страницы ссылаются обратно.
   - **Теги:** использовать только теги из таксономии в `SCHEMA.md`.
   - **Происхождение:** на страницах, синтезирующих 3 + источника, добавлять маркеры `^[raw/articles/source.md]` к абзацам, чьи утверждения прослеживаются к конкретному источнику.
   - **Уверенность:** для утверждений, насыщенных мнением, быстро меняющихся или из одного источника, ставить `confidence: medium` или `low` в frontmatter. Не ставить `high`, если утверждение не подкреплено несколькими источниками.

⑤ **Обновить навигацию:**
   - Добавить новые страницы в `index.md` в соответствующий раздел, в алфавитном порядке.
   - Обновить счётчик «Всего страниц» и дату «Последнее обновление» в заголовке индекса.
   - Добавить в `log.md`: `## [YYYY-MM-DD] ingest | Source Title`.
   - Перечислить каждый созданный или обновлённый файл в записи лога.

⑥ **Сообщить, что изменилось** — перечислить каждый созданный или обновлённый файл пользователю.

Один источник может вызвать обновления на 5‑15 страницах вики. Это нормально и желаемо — это эффект накопления.

### 2. Запрос

Когда пользователь задаёт вопрос о домене вики:

① **Прочитать `index.md`**, чтобы определить релевантные страницы.
② **Для вики с 100 + страницами** также выполнить `search_files` по всем `.md`‑файлам для ключевых терминов — один лишь индекс может упустить нужный контент.
③ **Прочитать релевантные страницы** с помощью `read_file`.
④ **Синтезировать ответ** из собранных знаний. Цитировать страницы вики, из которых черпал информацию: «На основе [[page-a]] и [[page-b]]…».
⑤ **Сохранить ценные ответы** — если ответ представляет собой существенное сравнение, глубокий разбор или новую синтезу, создать страницу в `queries/` или `comparisons/`. Не сохранять тривиальные запросы — только ответы, которые было бы трудно воссоздать.
⑥ **Обновить `log.md`** с запросом и указанием, был ли он сохранён.

### 3. Проверка (Lint)

Когда пользователь просит выполнить lint, проверку состояния или аудит вики:

① **Одинокие страницы:** найти страницы без входящих `[[wikilinks]]` от других страниц.
```python
# Use execute_code for this — programmatic scan across all wiki pages
import os, re
from collections import defaultdict
wiki = "<WIKI_PATH>"
# Scan all .md files in entities/, concepts/, comparisons/, queries/
# Extract all [[wikilinks]] — build inbound link map
# Pages with zero inbound links are orphans
```

② **Сломанные wikilinks:** найти `[[links]]`, указывающие на несуществующие страницы.

③ **Полнота индекса:** каждая страница вики должна присутствовать в `index.md`. Сравнить файловую систему с записями индекса.

④ **Валидация frontmatter:** каждая страница вики должна иметь все обязательные поля (title, created, updated, type, tags, sources). Теги должны соответствовать таксономии.

⑤ **Устаревший контент:** страницы, у которых дата `updated` более чем на 90 дней старше самого последнего источника, упоминающего те же сущности.

⑥ **Противоречия:** страницы по одной теме с конфликтующими утверждениями. Ищем страницы, которые делят теги/сущности, но формулируют разные факты. Выводим все страницы с `contested: true` или `contradictions:` в frontmatter для обзора пользователем.

⑦ **Сигналы качества:** список страниц с `confidence: low` и любой страницы, ссылающейся только на один источник, но без установленного поля уверенности — это кандидаты либо для поиска подтверждения, либо для понижения до `confidence: medium`.

⑧ **Смещение источника:** для каждого файла в `raw/` с полем `sha256:` в frontmatter пересчитать хеш и отметить несоответствия. Несоответствия указывают, что raw‑файл был изменён (не должно происходить — raw/ неизменяем) или интегрирован из URL, который изменился. Это не критическая ошибка, но стоит сообщить.

⑨ **Размер страницы:** пометить страницы более 200 строк — кандидаты для разделения.

⑩ **Аудит тегов:** перечислить все используемые теги, отметить те, что отсутствуют в таксономии `SCHEMA.md`.

⑪ **Ротация лога:** если `log.md` превышает 500 записей, выполнить ротацию.

⑫ **Сообщить результаты** с конкретными путями файлов и предложенными действиями, сгруппированными по уровню серьёзности (сломанные ссылки > одинокие > смещение источника > спорные страницы > устаревший контент > стилистические проблемы).

⑬ **Добавить в `log.md`:** `## [YYYY-MM-DD] lint | N issues found`
## Работа с Wiki

### Поиск

```bash
# Find pages by content
search_files "transformer" path="$WIKI" file_glob="*.md"

# Find pages by filename
search_files "*.md" target="files" path="$WIKI"

# Find pages by tag
search_files "tags:.*alignment" path="$WIKI" file_glob="*.md"

# Recent activity
read_file "$WIKI/log.md" offset=<last 20 lines>
```

### Массовый импорт

При импорте нескольких источников одновременно группируй обновления:
1. Сначала прочитай все источники.
2. Выяви все сущности и концепции во всех источниках.
3. Проверь существующие страницы для всех них (один проход поиска, а не N).
4. Создай/обнови страницы за один проход (избегает избыточных обновлений).
5. Обнови `index.md` один раз в конце.
6. Запиши одну запись в журнал, охватывающую пакет обновлений.

### Архивирование

Когда контент полностью заменён или область домена меняется:
1. Создай каталог `_archive/`, если его нет.
2. Перемести страницу в `_archive/` с её оригинальным путём (например, `_archive/entities/old-page.md`).
3. Удали её из `index.md`.
4. Обнови любые страницы, которые ссылались на неё — заменив wikilink обычным текстом + «(archived)».
5. Запиши действие архивирования в журнал.

### Интеграция с Obsidian

Каталог wiki работает как хранилище Obsidian «из коробки»:
- `[[wikilinks]]` отображаются как кликабельные ссылки.
- Вид **Graph View** визуализирует сеть знаний.
- YAML‑frontmatter поддерживает запросы Dataview.
- Папка `raw/assets/` хранит изображения, на которые ссылаются через `![[image.png]]`.

Для наилучших результатов:
- Установи папку вложений Obsidian в `raw/assets/`.
- Включи **Wikilinks** в настройках Obsidian (обычно включено по умолчанию).
- Установи плагин Dataview для запросов вроде `TABLE tags FROM "entities" WHERE contains(tags, "company")`.

Если используешь навык Obsidian вместе с этим, задай `OBSIDIAN_VAULT_PATH` в тот же каталог, что и путь к wiki.

### Obsidian Headless (серверы и безголовые машины)

На машинах без дисплея используй `obsidian-headless` вместо настольного приложения. Он синхронизирует хранилища через Obsidian Sync без GUI — идеально для агентов, работающих на серверах и записывающих в wiki, пока Obsidian Desktop читает его на другом устройстве.

**Настройка:**
```bash
# Requires Node.js 22+
npm install -g obsidian-headless

# Login (requires Obsidian account with Sync subscription)
ob login --email <email> --password '<password>'

# Create a remote vault for the wiki
ob sync-create-remote --name "LLM Wiki"

# Connect the wiki directory to the vault
cd ~/wiki
ob sync-setup --vault "<vault-id>"

# Initial sync
ob sync

# Continuous sync (foreground — use systemd for background)
ob sync --continuous
```

**Непрерывная фоновая синхронизация через systemd:**
```ini
# ~/.config/systemd/user/obsidian-wiki-sync.service
[Unit]
Description=Obsidian LLM Wiki Sync
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/path/to/ob sync --continuous
WorkingDirectory=/home/user/wiki
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now obsidian-wiki-sync
# Enable linger so sync survives logout:
sudo loginctl enable-linger $USER
```

Это позволяет агенту писать в `~/wiki` на сервере, пока ты просматриваешь то же хранилище в Obsidian на ноутбуке/телефоне — изменения появляются в течение секунд.
## Подводные камни

- **Never modify files in `raw/`** — sources are immutable. Corrections go in wiki pages.
- **Always orient first** — read SCHEMA + index + recent log before any operation in a new session. Skipping this causes duplicates and missed cross‑references.
- **Always update `index.md` and `log.md`** — skipping this makes the wiki degrade. These are the navigational backbone.
- **Don't create pages for passing mentions** — follow the Page Thresholds in `SCHEMA.md`. A name appearing once in a footnote doesn't warrant an entity page.
- **Don't create pages without cross‑references** — isolated pages are invisible. Every page must link to at least 2 other pages.
- **Frontmatter is required** — it enables search, filtering, and staleness detection.
- **Tags must come from the taxonomy** — freeform tags decay into noise. Add new tags to `SCHEMA.md` first, then use them.
- **Keep pages scannable** — a wiki page should be readable in 30 seconds. Split pages over 200 lines. Move detailed analysis to dedicated deep‑dive pages.
- **Ask before mass‑updating** — if an ingest would touch 10+ existing pages, confirm the scope with the user first.
- **Rotate the log** — when `log.md` exceeds 500 entries, rename it `log-YYYY.md` and start fresh. The agent should check log size during lint.
- **Handle contradictions explicitly** — don't silently overwrite. Note both claims with dates, mark in frontmatter, flag for user review.
## Связанные инструменты

[llm-wiki-compiler](https://github.com/atomicmemory/llm-wiki-compiler) — это CLI на Node.js, который компилирует источники в концептуальную вики, вдохновлённую Карпати. Она совместима с Obsidian, поэтому пользователи, желающие иметь запланированный/CLI‑управляемый конвейер компиляции, могут указать её на тот же vault, который поддерживает этот skill. Компромиссы: она управляет генерацией страниц (заменяет суждение агента о создании страниц) и оптимизирована для небольших корпусов. Используй этот skill, когда нужна курирование с участием агента; используй llmwiki, когда требуется пакетная компиляция каталога источников.