---
title: "Llm Wiki — Karpathy's LLM Wiki: створювати/запитувати взаємопов’язані markdown KB"
sidebar_label: "Llm Wiki"
description: "Wiki LLM Karpathy: створювати/запитувати взаємопов’язану markdown KB"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Llm Wiki

Wiki LLM Карпарті: створювати/запитувати взаємопов’язані markdown‑KB.
## Метадані навички

| | |
|---|---|
| Джерело | Вбудовано (встановлено за замовчуванням) |
| Шлях | `skills/research/llm-wiki` |
| Версія | `2.1.0` |
| Автор | Hermes Agent |
| Ліцензія | MIT |
| Платформи | linux, macos, windows |
| Теги | `wiki`, `knowledge-base`, `research`, `notes`, `markdown`, `rag-alternative` |
| Пов’язані навички | [`obsidian`](/docs/user-guide/skills/bundled/note-taking/note-taking-obsidian), [`arxiv`](/docs/user-guide/skills/bundled/research/research-arxiv) |
:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Вікі LLM Карпатрі

Створи та підтримуй постійну, наростаючу базу знань у вигляді взаємопов’язаних markdown‑файлів.
Засновано на [шаблоні LLM Wiki Андрія Карпатрі](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

На відміну від традиційного RAG (який заново відкриває знання для кожного запиту), вікі
компілює знання один раз і підтримує їх актуальними. Перехресні посилання вже є.
Протиріччя вже позначені. Синтез відображає все, що було поглинуто.

**Розподіл праці:** Людина підбирає джерела та керує аналізом. Агент
резюмує, створює перехресні посилання, зберігає файли та підтримує узгодженість.
## Коли активується цей skill

Використовуй цей skill, коли користувач:
- Питає створити, збудувати або запустити wiki чи базу знань
- Питає імпортувати, додати або обробити джерело у їхній wiki
- Питає питання, і існуюча wiki присутня за налаштованим шляхом
- Питає провести lint, аудит або health‑check їхньої wiki
- Посилається на їхню wiki, базу знань або «нотатки» у контексті дослідження
## Розташування Wiki

**Розташування:** Встановлюється за допомогою змінної середовища `WIKI_PATH` (наприклад, у `~/.hermes/.env`).

Якщо не встановлено, за замовчуванням використовується `~/wiki`.

```bash
WIKI="${WIKI_PATH:-$HOME/wiki}"
```

Wiki — це просто каталог файлів markdown — відкрий його в Obsidian, VS Code або будь‑якому редакторі. Жодної бази даних, жодних спеціальних інструментів не потрібно.
## Архітектура: три рівні

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

**Layer 1 — Raw Sources:** Незмінний. Агент лише читає їх, не змінюючи.
**Layer 2 — The Wiki:** markdown‑файли, що належать агенту. Створені, оновлені та перехресно пов’язані агентом.
**Layer 3 — The Schema:** `SCHEMA.md` визначає структуру, конвенції та таксономію тегів.
## Відновлення існуючої Wiki (CRITICAL — роби це кожну сесію)

Коли у користувача вже є Wiki, **завжди орієнтуйся перед тим, як щось робити**:

① **Прочитай `SCHEMA.md`** — зрозумій домен, конвенції та таксономію тегів.
② **Прочитай `index.md`** — дізнайся, які сторінки існують і їхні резюме.
③ **Переглянь останні `log.md`** — прочитай останні 20‑30 записів, щоб зрозуміти недавню активність.

```bash
WIKI="${WIKI_PATH:-$HOME/wiki}"
# Orientation reads at session start
read_file "$WIKI/SCHEMA.md"
read_file "$WIKI/index.md"
read_file "$WIKI/log.md" offset=<last 30 lines>
```

Лише після орієнтації слід виконувати `ingest`, `query` або `lint`. Це запобігає:
- Створенню дублікатних сторінок для сутностей, які вже існують
- Відсутності крос‑посилань на існуючий контент
- Порушенню конвенцій схеми
- Повторенню вже задокументованої роботи

Для великих Wiki (100+ сторінок) також запусти швидкий `search_files` за темою, яка розглядається, перед створенням чогось нового.
## Ініціалізація нової Wiki

Коли користувач просить створити або запустити wiki:

1. Визнач шлях до wiki (з змінної оточення `$WIKI_PATH` або запитай у користувача; за замовчуванням `~/wiki`)
2. Створи структуру каталогів, зазначену вище
3. Запитай у користувача, який домен охоплює wiki — будь конкретним
4. Запиши `SCHEMA.md`, адаптований до домену (дивись шаблон нижче)
5. Запиши початковий `index.md` із заголовком, розділеним секціями
6. Запиши початковий `log.md` із записом про створення
7. Підтверди, що wiki готова, і запропонуй перші джерела для імпорту

### Шаблон SCHEMA.md

Адаптуй до домену користувача. Схема обмежує поведінку агента і забезпечує послідовність:

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

`confidence` і `contested` — необов’язкові, але рекомендовані для тем, насичених думками або швидко змінюваних. Lint виявляє сторінки з `contested: true` і `confidence: low` для перегляду, щоб слабкі твердження не закріплювалися в wiki як прийняті факти.

### raw/ Frontmatter

Сирі джерела ТАКОЖ отримують невеликий блок frontmatter, щоб повторні імпорти могли виявляти відхилення:

```yaml
---
source_url: https://example.com/article   # original URL, if applicable
ingested: YYYY-MM-DD
sha256: &lt;hex digest of the raw content below the frontmatter>
---
```

`sha256:` дозволяє майбутньому повторному імпорту того ж URL пропускати обробку, коли вміст не змінився, і позначати відхилення, коли він змінився. Обчислюй хеш лише над тілом (все після закриваючого `---`), а не над самим frontmatter.
## Таксономія тегів
[Визнач 10‑20 тегів верхнього рівня для домену. Додай нові теги тут ПЕРЕД їх використанням.]

Приклад для AI/ML:
- Models: model, architecture, benchmark, training
- People/Orgs: person, company, lab, open-source
- Techniques: optimization, fine-tuning, inference, alignment, data
- Meta: comparison, timeline, controversy, prediction

Правило: кожен тег на сторінці має бути присутнім у цій таксономії. Якщо потрібен новий тег,
спочатку додай його тут, а потім використай. Це запобігає розростанню тегів.
## Пороги сторінок
- **Створити сторінку**, коли сутність/концепція з’являється у 2+ джерелах АБО є центральною в одному джерелі
- **Додати до існуючої сторінки**, коли джерело згадує щось, що вже покрито
- **НЕ створювати сторінку** для мимохідних згадок, незначних деталей або речей поза доменом
- **Розділити сторінку**, коли вона перевищує ~200 рядків — розбити на підтеми з крос‑посиланнями
- **Архівувати сторінку**, коли її вміст повністю замінений — перемістити до `_archive/`, видалити з індексу
## Сторінки сутностей
Одна сторінка для кожної значущої сутності. Включай:
- Огляд / що це таке
- Ключові факти та дати
- Відношення до інших сутностей ([[wikilinks]])
- Посилання на джерела
## Сторінки концепцій
Одна сторінка на концепцію або тему. Містить:
- Визначення / пояснення
- Поточний стан знань
- Відкриті питання або дискусії
- Пов’язані концепції ([[wikilinks]])
## Сторінки порівняння
Порівняльний аналіз. Включають:
- Що порівнюється і чому
- Показники порівняння (бажано у форматі таблиці)
- Висновок або синтез
- Джерела
## Політика оновлення
Коли нова інформація суперечить існуючому вмісту:
1. Перевір дати — новіші джерела, як правило, переважають старіші.
2. Якщо суперечність дійсно суттєва, зазначи обидві позиції разом із датами та джерелами.
3. Познач протиріччя у frontmatter: `contradictions: [page-name]`
4. Познач для перегляду користувачем у звіті lint.
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

**Правило масштабування:** Якщо будь‑яка секція містить понад 50 записів, розділи її на підсекції за першою літерою або піддоменом. Якщо індекс усього містить понад 200 записів, створюй файл `_meta/topic-map.md`, який групує сторінки за темами для швидшої навігації.

### Шаблон log.md
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
## Core Operations

### 1. Ingest

Коли користувач надає джерело (URL, файл, вставка), інтегруй його у вікі:

① **Захопити сире джерело:**
   - URL → використай `web_extract`, щоб отримати markdown, збережи в `raw/articles/`
   - PDF → використай `web_extract` (обробляє PDF), збережи в `raw/papers/`
   - Вставлений текст → збережи у відповідний підкаталог `raw/`
   - Дай файлу описову назву: `raw/articles/karpathy-llm-wiki-2026.md`
   - **Додай сирий frontmatter** (`source_url`, `ingested`, `sha256` тіла).
     При повторному ingest того ж URL: переобчисли `sha256`, порівняй зі збереженим значенням —
     пропусти, якщо ідентичний, познач відхилення і онови, якщо різний. Це досить дешево виконати
     при кожному повторному ingest і ловить тихі зміни джерела.

② **Обговори висновки** з користувачем — що цікаве, що важливо для домену.
   (Пропусти це в автоматизованих/cron‑контекстах — переходь одразу.)

③ **Перевір, що вже існує** — шукай у `index.md` і використай `search_files`, щоб знайти існуючі сторінки для згаданих сутностей/концепцій. Це різниця між зростаючою вікі та купою дублікатів.

④ **Напиши або онови сторінки вікі:**
   - **Нові сутності/концепції:** Створюй сторінки лише якщо вони відповідають порогам *Page Thresholds* у `SCHEMA.md` (2+ згадки джерела, або центральні для одного джерела).
   - **Існуючі сторінки:** Додавай нову інформацію, оновлюй факти, оновлюй дату `updated`.
     Коли нова інформація суперечить існуючому вмісту, дотримуйся *Update Policy*.
   - **Перехресні посилання:** Кожна нова або оновлена сторінка повинна посилатися принаймні на 2 інші сторінки через `[[wikilinks]]`. Перевір, щоб існуючі сторінки посилалися назад.
   - **Теги:** Використовуй лише теги з таксономії у `SCHEMA.md`.
   - **Провенанс:** На сторінках, що синтезують 3+ джерела, додавай маркери `^[raw/articles/source.md]` до абзаців, чиї твердження походять з конкретного джерела.
   - **Впевненість:** Для заяв, що базуються на одній точці зору, швидко змінюються або мають одне джерело, встанови `confidence: medium` або `low` у frontmatter. Не став `high`, якщо твердження не підкріплене кількома джерелами.

⑤ **Онови навігацію:**
   - Додай нові сторінки до `index.md` у відповідний розділ, в алфавітному порядку.
   - Онови лічильник «Total pages» та дату «Last updated» у заголовку індексу.
   - Додай до `log.md`: `## [YYYY-MM-DD] ingest | Source Title`.
   - Перерахуйте кожен файл, створений або оновлений, у записі журналу.

⑥ **Повідом, що змінилося** — перелічи всі створені або оновлені файли користувачу.

Один джерело може викликати оновлення у 5‑15 сторінок вікі. Це нормально і бажано — це ефект накопичення.

### 2. Query

Коли користувач ставить питання про домен вікі:

① **Прочитай `index.md`**, щоб визначити релевантні сторінки.
② **Для вікі з 100+ сторінками** також використай `search_files` по всім `.md` файлам за ключовими термінами — індекс сам по собі може пропускати важливий вміст.
③ **Прочитай релевантні сторінки** за допомогою `read_file`.
④ **Синтезуй відповідь** з зібраних знань. Цитуй сторінки вікі, з яких бралося: «Based on [[page-a]] and [[page-b]]…».
⑤ **Збережи цінні відповіді** — якщо відповідь є суттєвим порівнянням, глибоким аналізом або новим синтезом, створи сторінку у `queries/` або `comparisons/`. Не зберігай тривіальні запити — лише відповіді, які важко відтворити.
⑥ **Онови `log.md`** з записом запиту та інформацією, чи була відповідь збережена.

### 3. Lint

Коли користувач просить провести lint, health‑check або аудит вікі:

① **Orphan pages:** знайди сторінки без вхідних `[[wikilinks]]` з інших сторінок.
```python
# Use execute_code for this — programmatic scan across all wiki pages
import os, re
from collections import defaultdict
wiki = "<WIKI_PATH>"
# Scan all .md files in entities/, concepts/, comparisons/, queries/
# Extract all [[wikilinks]] — build inbound link map
# Pages with zero inbound links are orphans
```

② **Broken wikilinks:** знайди `[[links]]`, що вказують на неіснуючі сторінки.

③ **Повнота індексу:** кожна сторінка вікі повинна бути в `index.md`. Порівняй файлову систему з записами індексу.

④ **Валідація frontmatter:** кожна сторінка вікі має мати всі обов’язкові поля (title, created, updated, type, tags, sources). Теги мають бути в таксономії.

⑤ **Застарілий вміст:** сторінки, у яких дата `updated` старша >90 днів від найновішого джерела, що згадує ті ж сутності.

⑥ **Протиріччя:** сторінки на одну тему з конфліктними твердженнями. Шукай сторінки, що ділять теги/сутності, але містять різні факти. Виведи всі сторінки з `contested: true` або `contradictions:` у frontmatter для огляду.

⑦ **Сигнали якості:** перелічи сторінки з `confidence: low` та будь‑які, що цитують лише одне джерело без встановленого поля `confidence` — це кандидати або для пошуку підтвердження, або для зниження до `confidence: medium`.

⑧ **Зсув джерела:** для кожного файлу в `raw/` з `sha256:` у frontmatter переобчисли хеш і познач невідповідності. Невідповідність означає, що сирий файл був змінений (не повинно траплятись — `raw/` має бути незмінним) або ingestовано з URL, що змінився. Це не критична помилка, але варто повідомити.

⑨ **Розмір сторінки:** познач сторінки понад 200 рядків — кандидати на розділення.

⑩ **Аудит тегів:** перелічи всі використані теги, познач будь‑які, що не входять у таксономію `SCHEMA.md`.

⑪ **Ротація журналу:** якщо `log.md` містить більше 500 записів, виконай його ротацію.

⑫ **Повідом результати** з конкретними шляхами файлів та пропозиціями дій, згрупованими за серйозністю (broken links > orphans > source drift > contested pages > stale content > style issues).

⑬ **Додай до `log.md`:** `## [YYYY-MM-DD] lint | N issues found`
## Робота з Wiki

### Пошук

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

### Масове завантаження

При завантаженні кількох джерел одночасно, групуй оновлення:
1. Спочатку прочитай усі джерела
2. Визнач усі сутності та концепції у всіх джерелах
3. Перевір існуючі сторінки для всіх них (один прохід пошуку, а не N)
4. Створи/онови сторінки в один прохід (уникає надмірних оновлень)
5. Онови `index.md` один раз у кінці
6. Запиши один запис у журнал, що охоплює пакет

### Архівування

Коли вміст повністю замінений або область домену змінюється:
1. Створи каталог `_archive/`, якщо його ще немає
2. Перемести сторінку до `_archive/` зі її початковим шляхом (наприклад, `_archive/entities/old-page.md`)
3. Видали її з `index.md`
4. Онови будь‑які сторінки, які посилалися на неї — заміни wikilink на простий текст + «(archived)»
5. Зафіксуй дію архівування у журналі

### Інтеграція з Obsidian

Каталог wiki працює як сховище Obsidian «з коробки»:
- `[[wikilinks]]` відображаються як клікабельні посилання
- Graph View візуалізує мережу знань
- YAML frontmatter живить запити Dataview
- Папка `raw/assets/` містить зображення, на які посилаються через `![[image.png]]`

Для кращих результатів:
- Встанови папку вкладень Obsidian у `raw/assets/`
- Увімкни «Wikilinks» у налаштуваннях Obsidian (зазвичай увімкнено за замовчуванням)
- Встанови плагін Dataview для запитів типу `TABLE tags FROM "entities" WHERE contains(tags, "company")`

Якщо використовуєш навичку Obsidian разом з цією, встанови `OBSIDIAN_VAULT_PATH` у той же каталог, що й шлях до wiki.

### Obsidian Headless (сервери та безголові машини)

На машинах без дисплея використовуйте `obsidian-headless` замість настільного додатку.
Він синхронізує сховища через Obsidian Sync без GUI — ідеально для агентів, що працюють на серверах і записують у wiki, тоді як Obsidian desktop читає його на іншому пристрої.

**Налаштування:**
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

**Безперервна фонова синхронізація через systemd:**
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

Це дозволяє агенту записувати у `~/wiki` на сервері, поки ти переглядаєш те саме сховище в Obsidian на ноутбуці/телефоні — зміни з’являються протягом кількох секунд.
## Підводні камені

- **Ніколи не змінюй файли в `raw/`** — джерела незмінні. Виправлення додаються у wiki‑сторінки.
- **Завжди орієнтуйся спочатку** — прочитай SCHEMA + index + останній log перед будь‑якою операцією в новій сесії. Пропуск цього кроку призводить до дублювань і пропущених крос‑посилань.
- **Завжди оновлюй `index.md` і `log.md`** — пропуск оновлення погіршує wiki. Це навігаційний каркас.
- **Не створюй сторінки для випадкових згадок** — дотримуйся Page Thresholds у SCHEMA.md. Ім’я, що з’являється один раз у виносці, не вимагає створення сторінки сутності.
- **Не створюй сторінки без крос‑посилань** — ізольовані сторінки невидимі. Кожна сторінка повинна посилатися принаймні на 2 інші сторінки.
- **Frontmatter обов’язковий** — він дозволяє пошук, фільтрацію та виявлення застарілості.
- **Теги мають походити з таксономії** — довільні теги перетворюються на шум. Спочатку додай нові теги до SCHEMA.md, потім використай їх.
- **Тримай сторінки сканованими** — wiki‑сторінка має читатися за 30 секунд. Розбивай сторінки, якщо вони перевищують 200 рядків. Детальний аналіз переміщуй у спеціальні deep‑dive сторінки.
- **Запитуй перед масовим оновленням** — якщо інжест зачепить 10+ існуючих сторінок, спочатку підтверди обсяг з користувачем.
- **Ротируй log** — коли `log.md` перевищує 500 записів, перейменуй його в `log-YYYY.md` і створи новий. Агент має перевіряти розмір логу під час lint.
- **Обробляй протиріччя явно** — не перезаписуй мовчки. Зафіксуй обидва твердження з датами, познач у frontmatter, позначи для перегляду користувачем.
## Пов’язані інструменти

[llm-wiki-compiler](https://github.com/atomicmemory/llm-wiki-compiler) — це Node.js CLI, який
компілює джерела у концептуальну вікі з тією ж натхненістю Карпаті. Він сумісний з Obsidian,
тому користувачі, які хочуть мати запланований/CLI‑керований конвеєр компіляції, можуть вказати його на той самий vault, який
цей **skill** підтримує. Компроміси: він відповідає за генерацію сторінок (замінює судження агента щодо створення
сторінок) і налаштований для невеликих корпусів. Використовуй цей **skill**, коли потрібна курація з участю агента;
використовуй llmwiki, коли потрібна пакетна компіляція каталогу джерел.