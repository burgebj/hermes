---
sidebar_position: 2
title: "Skills система"
description: "Документи знань за запитом — поступове розкриття, навички, керовані агентом, та Skills Hub"
---

# Система навичок

Навички — це документи знань за запитом, які агент може завантажити за потреби. Вони слідують шаблону **progressive disclosure**, щоб мінімізувати використання токенів, і сумісні з відкритим стандартом [agentskills.io](https://agentskills.io/specification).

Усі навички розташовані в **`~/.hermes/skills/`** — основному каталозі та єдиному джерелі правди. При свіжій інсталяції вбудовані навички копіюються з репозиторію. Навички, встановлені через Hub, та створені агентом, також розміщуються тут. Агент може змінювати або видаляти будь‑яку навичку.

Ти також можеш вказати Hermes на **зовнішні каталоги навичок** — додаткові папки, які скануються разом із локальним каталогом. Дивись розділ [External Skill Directories](#external-skill-directories) нижче.

Дивись також:

- [Bundled Skills Catalog](/reference/skills-catalog)
- [Official Optional Skills Catalog](/reference/optional-skills-catalog)
## Використання skill

Кожен встановлений skill автоматично доступний як slash‑команда:

```bash
# In the CLI or any messaging platform:
/gif-search funny cats
/axolotl help me fine-tune Llama 3 on my dataset
/github-pr-workflow create a PR for the auth refactor
/plan design a rollout for migrating our auth provider

# Just the skill name loads it and lets the agent ask what you need:
/excalidraw
```

Вбудований skill `plan` — хороший приклад. Виконання `/plan [request]` завантажує інструкції skill, змушуючи Hermes за потреби перевіряти контекст, створювати план реалізації у форматі markdown замість виконання завдання та зберігати результат у `.hermes/plans/` відносно активної робочої теки/теки бекенду.

Ти також можеш взаємодіяти зі skill через природну розмову:

```bash
hermes chat --toolsets skills -q "What skills do you have?"
hermes chat --toolsets skills -q "Show me the axolotl skill"
```
## Прогресивне розкриття

Навички використовують токен‑ефективний шаблон завантаження:

```
Level 0: skills_list()           → [{name, description, category}, ...]   (~3k tokens)
Level 1: skill_view(name)        → Full content + metadata       (varies)
Level 2: skill_view(name, path)  → Specific reference file       (varies)
```

Агент завантажує повний вміст навички лише тоді, коли це дійсно потрібно.
## Формат SKILL.md

```markdown
---
name: my-skill
description: Brief description of what this skill does
version: 1.0.0
platforms: [macos, linux]     # Optional — restrict to specific OS platforms
metadata:
  hermes:
    tags: [python, automation]
    category: devops
    fallback_for_toolsets: [web]    # Optional — conditional activation (see below)
    requires_toolsets: [terminal]   # Optional — conditional activation (see below)
    config:                          # Optional — config.yaml settings
      - key: my.setting
        description: "What this controls"
        default: "value"
        prompt: "Prompt for setup"
---

# Skill Title

## When to Use
Trigger conditions for this skill.

## Procedure
1. Step one
2. Step two

## Pitfalls
- Known failure modes and fixes

## Verification
How to confirm it worked.
```

### Навички, специфічні для платформи

Навички можуть обмежувати себе конкретними операційними системами за допомогою поля `platforms`:

| Значення | Відповідність |
|----------|---------------|
| `macos`   | macOS (Darwin) |
| `linux`   | Linux |
| `windows` | Windows |

```yaml
platforms: [macos]            # macOS only (e.g., iMessage, Apple Reminders, FindMy)
platforms: [macos, linux]     # macOS and Linux
```

Коли встановлено, навичка автоматично приховується від системного підказника, `skills_list()`, та слеш‑команд на несумісних платформах. Якщо не вказано, навичка завантажується на всіх платформах.
## Виведення навичок та доставка медіа

Коли відповідь навички (або будь‑яка відповідь агента) містить голий абсолютний шлях до медіа‑файлу — наприклад `/home/user/screenshots/diagram.png` — шлюз автоматично його розпізнає, видаляє зі видимого тексту і доставляє файл у рідному вигляді в чат користувача (фото в Telegram, вкладення в Discord тощо) замість того, щоб залишати сирий шлях у повідомленні.

Для аудіо спеціально директива `[[audio_as_voice]]` підвищує аудіофайли до нативних голосових повідомлень на платформах, які їх підтримують (Telegram, WhatsApp).

### Примусова доставка у вигляді документа: `[[as_document]]`

Іноді потрібне **протилежне** до попереднього перегляду: файл треба доставити як завантажуване вкладення, а не як перезапаковану бульбашку‑зображення. Класичний приклад — скріншот або діаграма високої роздільної здатності: `sendPhoto` у Telegram стискає їх до ~200 KB при 1280 px, руйнуючи читабельність. PNG розміром 1‑2 MB, надісланий через `sendDocument`, зберігає оригінальні байти.

Якщо відповідь (або будь‑який текст у ній — зазвичай останній рядок) містить буквальну директиву `[[as_document]]`, кожен шлях до медіа, витягнутий з цієї відповіді, доставляється як документ/вкладення, а не як бульбашка‑зображення:

```
Here is your rendered chart:

/home/user/.hermes/cache/chart-q4-2025.png

[[as_document]]
```

Директива видаляється перед доставкою, тому користувачі її не бачать. Гранулярність навмисно «все‑або‑нічого» для кожної відповіді: вставте `[[as_document]]` один раз, і всі шляхи до зображень у цій відповіді будуть доставлені як документи. Це відповідає області дії `[[audio_as_voice]]`.

Використовуй це в навичці, коли:

- Ти створюєш скріншоти або діаграми, які користувачеві потрібні у вигляді файлів (для редагування в іншому інструменті, архівування, поділу без змін).
- Типовий втратний попередній перегляд затьмарює деталі (малий текст, піксельно‑точні діаграми, кольорово‑чутливі рендери).

Платформи без окремого шляху до документа (наприклад SMS) повертаються до будь‑якого доступного механізму вкладень.

### Умовна активація (запасні навички)

Навички можуть автоматично показуватися або приховуватися залежно від того, які інструменти доступні у поточній сесії. Це найкорисніше для **запасних навичок** — безкоштовних або локальних альтернатив, які мають з’являтися лише коли преміум‑інструмент недоступний.

```yaml
metadata:
  hermes:
    fallback_for_toolsets: [web]      # Show ONLY when these toolsets are unavailable
    requires_toolsets: [terminal]     # Show ONLY when these toolsets are available
    fallback_for_tools: [web_search]  # Show ONLY when these specific tools are unavailable
    requires_tools: [terminal]        # Show ONLY when these specific tools are available
```

| Поле | Поведінка |
|------|-----------|
| `fallback_for_toolsets` | Навичка **прихована**, коли зазначені набори інструментів доступні. Показується, коли їх немає. |
| `fallback_for_tools` | Те ж саме, але перевіряє окремі інструменти замість наборів. |
| `requires_toolsets` | Навичка **прихована**, коли зазначені набори інструментів недоступні. Показується, коли вони присутні. |
| `requires_tools` | Те ж саме, але перевіряє окремі інструменти. |

**Приклад:** Вбудована навичка `duckduckgo-search` використовує `fallback_for_toolsets: [web]`. Коли у тебе встановлений `FIRECRAWL_API_KEY`, набір інструментів `web` доступний, і агент користується `web_search` — навичка DuckDuckGo залишається прихованою. Якщо ключ API відсутній, набір `web` недоступний, і навичка DuckDuckGo автоматично з’являється як запасна.

Навички без будь‑яких умовних полів працюють так само, як і раніше — їх завжди показують.
## Безпечне налаштування під час завантаження

Навички можуть оголошувати необхідні змінні середовища, не зникаючи з виявлення:

```yaml
required_environment_variables:
  - name: TENOR_API_KEY
    prompt: Tenor API key
    help: Get a key from https://developers.google.com/tenor
    required_for: full functionality
```

Коли виявляється відсутнє значення, Hermes запитує його безпечно лише тоді, коли навичка фактично завантажується в локальному CLI. Ти можеш пропустити налаштування і продовжити використовувати навичку. Інтерфейси обміну повідомленнями ніколи не запитують секрети в чаті — вони радять скористатися `hermes setup` або `~/.hermes/.env` локально.

Після встановлення оголошені змінні середовища **автоматично передаються** у пісочниці `execute_code` та `terminal` — скрипти навички можуть використовувати `$TENOR_API_KEY` безпосередньо. Для змінних середовища, не пов’язаних з навичкою, використай параметр конфігурації `terminal.env_passthrough`. Дивіться [Environment Variable Passthrough](/user-guide/security#environment-variable-passthrough) для деталей.

### Параметри конфігурації навички

Навички також можуть оголошувати неконфіденційні параметри конфігурації (шляхи, уподобання), що зберігаються у `config.yaml`:

```yaml
metadata:
  hermes:
    config:
      - key: myplugin.path
        description: Path to the plugin data directory
        default: "~/myplugin-data"
        prompt: Plugin data directory path
```

Параметри зберігаються під `skills.config` у твоєму `config.yaml`. `hermes config migrate` запитує про неналаштовані параметри, а `hermes config show` їх відображає. Коли навичка завантажується, її розв’язані значення конфігурації впроваджуються в контекст, тож агент автоматично знає налаштовані значення.

Дивіться [Skill Settings](/user-guide/configuration#skill-settings) та [Creating Skills — Config Settings](/developer-guide/creating-skills#config-settings-configyaml) для деталей.
## Структура каталогу навичок

```text
~/.hermes/skills/                  # Single source of truth
├── mlops/                         # Category directory
│   ├── axolotl/
│   │   ├── SKILL.md               # Main instructions (required)
│   │   ├── references/            # Additional docs
│   │   ├── templates/             # Output formats
│   │   ├── scripts/               # Helper scripts callable from the skill
│   │   └── assets/                # Supplementary files
│   └── vllm/
│       └── SKILL.md
├── devops/
│   └── deploy-k8s/                # Agent-created skill
│       ├── SKILL.md
│       └── references/
├── .hub/                          # Skills Hub state
│   ├── lock.json
│   ├── quarantine/
│   └── audit.log
└── .bundled_manifest              # Tracks seeded bundled skills
```
## Зовнішні каталоги навичок

Якщо ти підтримуєш навички поза Hermes — наприклад, спільний каталог `~/.agents/skills/`, яким користуються кілька інструментів ШІ — ти можеш налаштувати Hermes сканувати і ці каталоги.

Додай `external_dirs` у розділ `skills` у файлі `~/.hermes/config.yaml`:

```yaml
skills:
  external_dirs:
    - ~/.agents/skills
    - /home/shared/team-skills
    - ${SKILLS_REPO}/skills
```

Шляхи підтримують розширення `~` та підстановку змінних оточення `${VAR}`.

### Як це працює

- **Створювати локально, оновлювати на місці**: нові навички, створені агентом, записуються у `~/.hermes/skills/`. Існуючі навички змінюються там, де вони знаходяться, включаючи навички у `external_dirs`, коли агент використовує дії `skill_manage`, такі як `patch`, `edit`, `write_file`, `remove_file` або `delete`.
- **Зовнішні каталоги не є межою захисту від запису**: якщо зовнішній каталог навичок доступний для запису процесом Hermes, оновлення навичок, керованих агентом, можуть змінювати файли в цьому каталозі. Використовуй дозволи файлової системи або окрему конфігурацію профілю/набору інструментів, якщо спільні зовнішні навички мають залишатися лише для читання.
- **Локальний пріоритет**: якщо однакова назва навички існує і в локальному, і в зовнішньому каталозі, перевагу має локальна версія.
- **Повна інтеграція**: зовнішні навички з’являються в індексі системної підказки, `skills_list`, `skill_view` та як слеш‑команди `/skill-name` — без відмінностей від локальних навичок.
- **Неіснуючі шляхи пропускаються без повідомлень**: якщо налаштований каталог не існує, Hermes ігнорує його без помилок. Це корисно для необов’язкових спільних каталогів, які можуть бути відсутніми на окремих машинах.

### Приклад

```text
~/.hermes/skills/               # Local (primary, read-write)
├── devops/deploy-k8s/
│   └── SKILL.md
└── mlops/axolotl/
    └── SKILL.md

~/.agents/skills/               # External (shared, mutable if writable)
├── my-custom-workflow/
│   └── SKILL.md
└── team-conventions/
    └── SKILL.md
```

У твоєму індексі навичок з’являються всі чотири навички. Якщо ти створиш нову навичку під назвою `my-custom-workflow` локально, вона перекриє зовнішню версію.
## Пакети навичок

Пакети навичок — це невеликі YAML‑файли, які групують кілька навичок під одну slash‑команду. Коли ти виконуєш `/<bundle-name>`, усі навички, зазначені в пакеті, завантажуються одночасно — це зручно, коли певне завдання завжди виграє від однакового набору навичок разом.

### Швидкий приклад

```bash
# Create a bundle for backend feature work
hermes bundles create backend-dev \
  --skill github-code-review \
  --skill test-driven-development \
  --skill github-pr-workflow \
  -d "Backend feature work — review, test, PR workflow"
```

Потім у CLI або будь‑якій платформі шлюзу:

```
/backend-dev refactor the auth middleware
```

Агент отримує всі три навички, завантажені в одне повідомлення користувача, а будь‑який текст після slash‑команди додається як інструкція користувача.

### Схема YAML

Пакети розташовані в **`~/.hermes/skill-bundles/<slug>.yaml`** і виглядають так:

```yaml
name: backend-dev
description: Backend feature work — review, test, PR workflow.
skills:
  - github-code-review
  - test-driven-development
  - github-pr-workflow
instruction: |
  Always start by writing failing tests, then implement.
  Open the PR through the standard workflow with co-author tags.
```

**Поля:**
- `name` (необов’язково — за замовчуванням використовується назва файлу) — відображувана назва пакету. Нормалізується у slug з дефісом для slash‑команди (`Backend Dev` → `/backend-dev`).
- `description` (необов’язково) — короткий текст, що показується в `/bundles` та `hermes bundles list`.
- `skills` (обов’язково, непорожній список) — назви навичок або шляхи, відносні до твоєї директорії навичок. Використовуй той самий ідентифікатор, який передавав би в `/<skill-name>`.
- `instruction` (необов’язково) — додаткові вказівки, які додаються перед вмістом завантаженої навички. Корисно для кодування «як ми завжди використовуємо їх разом».

### Керування пакетами

```bash
# List all installed bundles
hermes bundles list

# Inspect one bundle
hermes bundles show backend-dev

# Create a bundle interactively (omit --skill flags to enter them one per line)
hermes bundles create research

# Overwrite an existing bundle
hermes bundles create backend-dev --skill ... --force

# Delete a bundle
hermes bundles delete backend-dev

# Re-scan ~/.hermes/skill-bundles/ and report changes
hermes bundles reload
```

Зсередини чат‑сесії команда `/bundles` виводить усі встановлені пакети та їх навички.

### Поведінка

- **Пакети мають пріоритет над окремими навичками**, коли їх slug'и збігаються. Якщо ти назвав пакет `research` і також маєш навичку `research`, `/research` викликає пакет. Це навмисно — ти обрав пакет, назвавши його.
- **Відсутні навички пропускаються, а не викликають помилку.** Якщо пакет містить `skill-foo`, а ти її не встановив, пакет все одно завантажить ті навички, які знайде, і агент отримає нотатку зі списком пропущених.
- **Пакети працюють на будь‑якій поверхні** — інтерактивному CLI, TUI, чат‑дашборді та на всіх платформах шлюзу (Telegram, Discord, Slack, …) — оскільки диспетчеризація централізована в тому ж місці, що й окремі команди навичок.
- **Пакети не анулюють кеш підказок.** Вони генерують нове повідомлення користувача під час виклику, так само, як `/<skill-name>` — без зміни системної підказки.

### Коли пакети кращі за ручне встановлення кожної навички

Використовуй пакет, коли:
- Ти завжди поєднуєш одні й ті ж навички для повторюваного завдання (`/backend-dev`, `/release-prep`, `/incident-response`).
- Тобі потрібна модель, коротша на один символ, ніж вводити кілька `/skill` послідовно.
- Хочеш розповсюдити «профіль завдання» по всій команді, додавши YAML пакету в спільний репозиторій dotfiles і створивши символічне посилання в `~/.hermes/skill-bundles/`.

Пакет — це лише YAML‑аліас, він не встановлює навички за тебе. Самі навички мають бути вже присутні (у `~/.hermes/skills/` або зовнішній директорії навичок). Інакше виклик пакету просто пропустить відсутні.
## Навички, якими керує агент (інструмент **skill_manage**)

Агент може створювати, оновлювати та видаляти власні навички за допомогою інструмента `skill_manage`. Це **процедурна пам'ять** агента — коли він розробляє нетривіальний робочий процес, він зберігає підхід як навичку для майбутнього використання.

### Коли агент створює навички

- Після успішного завершення складного завдання (5+ викликів інструментів)
- Коли він зіткнувся з помилками або глухими кутами і знайшов працюючий шлях
- Коли користувач виправив його підхід
- Коли він виявив нетривіальний робочий процес

### Дії

| Дія | Для чого | Ключові параметри |
|--------|---------|------------|
| `create` | Нова навичка з нуля | `name`, `content` (повний SKILL.md), необов’язковий `category` |
| `patch` | Цілеспрямовані виправлення (переважно) | `name`, `old_string`, `new_string` |
| `edit` | Значні структурні переписування | `name`, `content` (повна заміна SKILL.md) |
| `delete` | Повне видалення навички | `name` |
| `write_file` | Додавання/оновлення допоміжних файлів | `name`, `file_path`, `file_content` |
| `remove_file` | Видалення допоміжного файлу | `name`, `file_path` |

:::tip
Дія `patch` переважає для оновлень — вона більш ефективна за токени, ніж `edit`, оскільки в виклику інструмента передається лише змінений текст.
:::
## Центр навичок

Переглядай, шукай, встановлюй і керуй навичками з онлайн‑реєстрів, `skills.sh`, прямих відомих кінцевих точок навичок та офіційних додаткових навичок.
### Загальні команди

```bash
hermes skills browse                              # Browse all hub skills (official first)
hermes skills browse --source official            # Browse only official optional skills
hermes skills search kubernetes                   # Search all sources
hermes skills search react --source skills-sh     # Search the skills.sh directory
hermes skills search https://mintlify.com/docs --source well-known
hermes skills inspect openai/skills/k8s           # Preview before installing
hermes skills install openai/skills/k8s           # Install with security scan
hermes skills install official/security/1password
hermes skills install skills-sh/vercel-labs/json-render/json-render-react --force
hermes skills install well-known:https://mintlify.com/docs/.well-known/skills/mintlify
hermes skills install https://sharethis.chat/SKILL.md              # Direct URL (single-file SKILL.md)
hermes skills install https://example.com/SKILL.md --name my-skill # Override name when frontmatter has none
hermes skills list --source hub                   # List hub-installed skills
hermes skills check                               # Check installed hub skills for upstream updates
hermes skills update                              # Reinstall hub skills with upstream changes when needed
hermes skills audit                               # Re-scan all hub skills for security
hermes skills uninstall k8s                       # Remove a hub skill
hermes skills reset google-workspace              # Un-stick a bundled skill from "user-modified" (see below)
hermes skills reset google-workspace --restore    # Also restore the bundled version, deleting your local edits
hermes skills publish skills/my-skill --to github --repo owner/repo
hermes skills snapshot export setup.json          # Export skill config
hermes skills tap add myorg/skills-repo           # Add a custom GitHub source
```
### Підтримувані джерела hub

| Джерело | Приклад | Примітки |
|--------|---------|----------|
| `official` | `official/security/1password` | Опціональні навички, що постачаються з Hermes. |
| `skills-sh` | `skills-sh/vercel-labs/agent-skills/vercel-react-best-practices` | Доступно через `hermes skills search <query> --source skills-sh`. Hermes розв’язує навички у стилі псевдоніма, коли slug у skills.sh відрізняється від папки репозиторію. |
| `well-known` | `well-known:https://mintlify.com/docs/.well-known/skills/mintlify` | Навички, що подаються безпосередньо з `/.well-known/skills/index.json` на веб‑сайті. Пошук за URL сайту або документації. |
| `url` | `https://sharethis.chat/SKILL.md` | Прямий HTTP(S) URL до однофайлового `SKILL.md`. Розв’язання назви: frontmatter → URL slug → інтерактивний запит → прапорець `--name`. |
| `github` | `openai/skills/k8s` | Прямі встановлення з репозиторію/шляху GitHub та власні tap‑и. |
| `clawhub`, `lobehub`, `browse-sh` | Ідентифікатори, специфічні для джерела | Інтеграції спільноти або маркетплейсу. |
### Інтегровані хаби та реєстри

Hermes наразі інтегрується з цими екосистемами навичок та джерелами виявлення:

#### 1. Офіційні необов’язкові навички (`official`)

Вони підтримуються безпосередньо в репозиторії Hermes і встановлюються з вбудованою довірою.

- Каталог: [Official Optional Skills Catalog](../../reference/optional-skills-catalog)
- Джерело в репо: `optional-skills/`
- Приклад:

```bash
hermes skills browse --source official
hermes skills install official/security/1password
```

#### 2. skills.sh (`skills-sh`)

Це публічний каталог навичок Vercel. Hermes може шукати його безпосередньо, переглядати сторінки деталей навичок, розв’язувати псевдоніми‑стилі slug‑ів і встановлювати з підлеглого репозиторію джерела.

- Каталог: [skills.sh](https://skills.sh/)
- Репо інструментів/CLI: [vercel-labs/skills](https://github.com/vercel-labs/skills)
- Офіційний репо навичок Vercel: [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills)
- Приклад:

```bash
hermes skills search react --source skills-sh
hermes skills inspect skills-sh/vercel-labs/json-render/json-render-react
hermes skills install skills-sh/vercel-labs/json-render/json-render-react --force
```

#### 3. Відомі кінцеві точки навичок (`well-known`)

Це URL‑базоване виявлення з сайтів, які публікують `/.well-known/skills/index.json`. Це не єдиний централізований хаб — це веб‑конвенція виявлення.

- Приклад живої кінцевої точки: [Mintlify docs skills index](https://mintlify.com/docs/.well-known/skills/index.json)
- Реалізація серверу‑референса: [vercel-labs/skills-handler](https://github.com/vercel-labs/skills-handler)
- Приклад:

```bash
hermes skills search https://mintlify.com/docs --source well-known
hermes skills inspect well-known:https://mintlify.com/docs/.well-known/skills/mintlify
hermes skills install well-known:https://mintlify.com/docs/.well-known/skills/mintlify
```

#### 4. Прямі навички GitHub (`github`)

Hermes може встановлювати безпосередньо з репозиторіїв GitHub та tap‑ів на їх основі. Це корисно, коли ти вже знаєш репо/шлях або хочеш додати власний кастомний репозиторій джерела.

Типові tap‑и (доступні без налаштувань):
- [openai/skills](https://github.com/openai/skills)
- [anthropics/skills](https://github.com/anthropics/skills)
- [huggingface/skills](https://github.com/huggingface/skills)
- [garrytan/gstack](https://github.com/garrytan/gstack)

- Приклад:

```bash
hermes skills install openai/skills/k8s
hermes skills tap add myorg/skills-repo
```

#### 5. ClawHub (`clawhub`)

Маркетплейс навичок сторонніх розробників, інтегрований як спільне джерело.

- Сайт: [clawhub.ai](https://clawhub.ai/)
- Hermes source id: `clawhub`

#### 6. Репо у стилі маркетплейсу Claude (`claude-marketplace`)

Hermes підтримує репо‑маркетплейси, які публікують сумісні з Claude маніфести плагінів/маркетплейсу.

Відомі інтегровані джерела:
- [anthropics/skills](https://github.com/anthropics/skills)
- [aiskillstore/marketplace](https://github.com/aiskillstore/marketplace)

Hermes source id: `claude-marketplace`

#### 7. LobeHub (`lobehub`)

Hermes може шукати та конвертувати записи агентів з публічного каталогу LobeHub у встановлювані навички Hermes.

- Сайт: [LobeHub](https://lobehub.com/)
- Публічний індекс агентів: [chat-agents.lobehub.com](https://chat-agents.lobehub.com/)
- Репо‑джерело: [lobehub/lobe-chat-agents](https://github.com/lobehub/lobe-chat-agents)
- Hermes source id: `lobehub`

#### 8. browse.sh (`browse-sh`)

Hermes інтегрується з [browse.sh](https://browse.sh), каталогом Browserbase, що містить понад 200 файлів `SKILL.md` для конкретних сайтів (Airbnb, Amazon, arXiv, 12306.cn, Etsy, Xero тощо). Кожна навичка описує, як повністю автоматизувати роботу з певним сайтом, і підходить для використання інструментами браузера Hermes та будь‑якими вже встановленими навичками автоматизації браузера.

- Сайт: [browse.sh](https://browse.sh/)
- API каталогу: `https://browse.sh/api/skills`
- Hermes source id: `browse-sh`
- Рівень довіри: `community`

```bash
hermes skills search airbnb --source browse-sh
hermes skills inspect browse-sh/airbnb.com/search-listings-ddgioa
hermes skills install browse-sh/airbnb.com/search-listings-ddgioa
```

Ідентифікатори мають форму `browse-sh/<hostname>/<task-id>` і відповідають slug‑у, що експонується каталогом browse.sh. Вміст розв’язується через endpoint детальної навички (`/api/skills/<slug>` → `skillMdUrl`), а не через `sourceUrl` репо GitHub каталогу.

#### 9. Прямий URL (`url`)

Встанови одиночний файл `SKILL.md` безпосередньо з будь‑якого HTTP(S) URL — корисно, коли автор розміщує навичку на власному сайті (без списку в хабі, без шляху GitHub). Hermes завантажує URL, парсить YAML frontmatter, сканує безпеку і встановлює.

- Hermes source id: `url`
- Ідентифікатор: сам URL (префікс не потрібен)
- Область застосування: **лише одиночний файл `SKILL.md`**. Навички з кількома файлами (`references/` або `scripts/`) потребують маніфесту і мають публікуватися через одне з інших джерел вище.

```bash
hermes skills install https://sharethis.chat/SKILL.md
hermes skills install https://example.com/my-skill/SKILL.md --category productivity
```

Розв’язання імені, у порядку:
1. Поле `name:` у YAML frontmatter файлу `SKILL.md` (рекомендовано — кожна коректна навичка має його).
2. Ім’я батьківської теки з шляху URL (наприклад, `.../my-skill/SKILL.md` → `my-skill`, або `.../my-skill.md` → `my-skill`), коли це дійсний ідентифікатор (`^[a-z][a-z0-9_-]*$`).
3. Інтерактивний запит у терміналі з TTY.
4. На неінтерактивних поверхнях (команда `/skills install` у TUI, шлюзи, скрипти) — чітка помилка з підказкою про параметр `--name`.

```bash
# Frontmatter has no name and the URL slug is unhelpful — supply one:
hermes skills install https://example.com/SKILL.md --name sharethis-chat

# Or inside a chat session:
/skills install https://example.com/SKILL.md --name sharethis-chat
```

Рівень довіри завжди `community` — та сама безпекова перевірка виконується, як і для будь‑якого іншого джерела. URL зберігається як ідентифікатор встановлення, тому `hermes skills update` автоматично повторно завантажує його з того ж URL при оновленні.
### Сканування безпеки та `--force`

Усі навички, встановлені через hub, проходять **сканер безпеки**, який перевіряє на витік даних, ін’єкцію підказок, шкідливі команди, сигнали ланцюга постачання та інші загрози.

`hermes skills inspect ...` тепер також показує метадані джерела, якщо вони доступні:
- URL репозиторію
- URL сторінки деталей `skills.sh`
- команда встановлення
- кількість встановлень за тиждень
- статуси аудиту безпеки джерела
- відомі URL‑и індексів/кінцевих точок

Використовуй `--force`, коли ти переглянув навичку стороннього розробника і хочеш перевизначити блокування політики, яке не є небезпечним:

```bash
hermes skills install skills-sh/anthropics/skills/pdf --force
```

Важлива поведінка:
- `--force` може перевизначити блокування політики для попереджень/застережень.
- `--force` **не** перевизначає вердикт сканування `dangerous`.
- Офіційні додаткові навички (`official/...`) розглядаються як вбудована довіра і не показують панель попередження про сторонню навичку.
### Рівні довіри

| Рівень | Джерело | Політика |
|-------|--------|----------|
| `builtin` | Поставляється з Hermes | Завжди довірений |
| `official` | `optional-skills/` у репозиторії | Довіра як у вбудованих, без попередження про сторонні |
| `trusted` | Довірені реєстри/репозиторії, такі як `openai/skills`, `anthropics/skills`, `huggingface/skills` | Більш ліберальна політика, ніж у джерелах спільноти |
| `community` | Все інше (`skills.sh`, відомі кінцеві точки, кастомні репозиторії GitHub, більшість маркетплейсів) | Не небезпечні результати можна перевизначити за допомогою `--force`; рішення `dangerous` залишаються заблокованими |
### Оновлення життєвого циклу

Hub тепер відстежує достатньо даних про походження, щоб повторно перевіряти копії встановлених **skill** у upstream‑сховищі:

```bash
hermes skills check          # Report which installed hub skills changed upstream
hermes skills update         # Reinstall only the skills with updates available
hermes skills update react   # Update one specific installed hub skill
```

Для цього використовується збережений ідентифікатор джерела плюс поточний хеш вмісту upstream‑пакету, що дозволяє виявляти відхилення.

:::tip GitHub rate limits
Операції **Skills hub** використовують API GitHub, який має обмеження в 60 запитів/годину для неавтентифікованих користувачів. Якщо під час встановлення або пошуку ти бачиш помилки обмеження швидкості, встанови `GITHUB_TOKEN` у файл `.env`, щоб підвищити ліміт до 5 000 запитів/годину. Повідомлення про помилку містить дієву підказку, коли це трапляється.
:::
### Публікація власного skill‑tap

Якщо ти хочеш поділитися підготовленим набором навичок — для своєї команди, організації або публічно — ти можеш опублікувати їх як **tap**: репозиторій GitHub, який інші користувачі Hermes додають за допомогою `hermes skills tap add <owner/repo>`. Ніякого сервера, реєстрації в реєстрі, конвеєра випуску. Просто каталог файлів `SKILL.md`.

#### Макет репозиторію

Tap — це будь‑який репозиторій GitHub (публічний або приватний — приватний потребує `GITHUB_TOKEN`), розташований так:

```
owner/repo
├── skills/                       # default path; configurable per-tap
│   ├── my-workflow/
│   │   ├── SKILL.md              # required
│   │   ├── references/           # optional supporting files
│   │   ├── templates/
│   │   └── scripts/
│   ├── another-skill/
│   │   └── SKILL.md
│   └── third-skill/
│       └── SKILL.md
└── README.md                     # optional but helpful
```

**Правила**
- Кожна навичка живе у власному каталозі під кореневим шляхом tap (за замовчуванням `skills/`).
- Ім’я каталогу стає slug для встановлення навички.
- У кожному каталозі навички має бути файл `SKILL.md` зі стандартним [SKILL.md frontmatter](#skillmd-format) (`name`, `description`, а також необов’язкові `metadata.hermes.tags`, `version`, `author`, `platforms`, `metadata.hermes.config`).
- Підкаталоги типу `references/`, `templates/`, `scripts/`, `assets/` завантажуються разом з `SKILL.md` під час встановлення.
- Навички, чиї імена каталогів починаються з `.` або `_`, ігноруються.

Hermes виявляє навички, перераховуючи усі підкаталоги шляху tap і перевіряючи кожен на наявність `SKILL.md`.

#### Мінімальний приклад tap

```
my-org/hermes-skills
└── skills/
    └── deploy-runbook/
        └── SKILL.md
```

`skills/deploy-runbook/SKILL.md`:

```markdown
---
name: deploy-runbook
description: Our deployment runbook — services, rollback, Slack channels
version: 1.0.0
author: My Org Platform Team
metadata:
  hermes:
    tags: [deployment, runbook, internal]
---

# Deploy Runbook

Step 1: ...
```

Після того, як цей репозиторій буде запушений у GitHub, будь‑який користувач Hermes може підписатися та встановити:

```bash
hermes skills tap add my-org/hermes-skills
hermes skills search deploy
hermes skills install my-org/hermes-skills/deploy-runbook
```

#### Нестандартні шляхи

Якщо твої навички не розташовані у `skills/` (це часто трапляється, коли ти додаєш піддерево `skills/` до існуючого проєкту), відредагуй запис tap у `~/.hermes/.hub/taps.json`:

```json
{
  "taps": [
    {"repo": "my-org/platform-docs", "path": "internal/skills/"}
  ]
}
```

CLI `hermes skills tap add` за замовчуванням створює нові tap зі шляхом `path: "skills/"`; відредагуй файл безпосередньо, якщо потрібен інший шлях. `hermes skills tap list` показує фактичний шлях для кожного tap.

#### Встановлення окремих навичок без додавання tap

Користувачі також можуть встановити одну навичку з будь‑якого публічного репозиторію GitHub без додавання всього репозиторію як tap:

```bash
hermes skills install owner/repo/skills/my-workflow
```

Корисно, коли ти хочеш поділитися однією навичкою, не змушуючи користувача підписуватись на весь твій реєстр.

#### Рівні довіри для tap

Новим tap за замовчуванням присвоюється довіра `community`. Навички, встановлені з них, проходять стандартне сканування безпеки та показують панель попередження про сторонні компоненти під час першого встановлення. Якщо твоїй організації або широко довіреному джерелу потрібен вищий рівень довіри, додай його репозиторій до `TRUSTED_REPOS` у `tools/skills_hub.py` (вимагає PR до ядра Hermes).

#### Керування tap

```bash
hermes skills tap list                                # show all configured taps
hermes skills tap add myorg/skills-repo               # add (default path: skills/)
hermes skills tap remove myorg/skills-repo            # remove
```

У межах запущеної сесії:

```
/skills tap list
/skills tap add myorg/skills-repo
/skills tap remove myorg/skills-repo
```

Tap зберігаються у `~/.hermes/.hub/taps.json` (створюються за потреби).
## Оновлення вбудованих навичок (`hermes skills reset`)

Hermes постачається з набором вбудованих навичок у `skills/` всередині репозиторію. При встановленні та під час кожного `hermes update` проходження синхронізації копіює їх у `~/.hermes/skills/` і записує маніфест у `~/.hermes/skills/.bundled_manifest`, який відображає назву кожної навички на хеш вмісту на момент синхронізації ( **оригінальний хеш**).

При кожній синхронізації Hermes переобчислює хеш вашої локальної копії і порівнює його з оригінальним хешем:

- **Unchanged** → безпечно витягнути зміни з upstream, скопіювати нову вбудовану версію, записати новий оригінальний хеш.
- **Changed** → розглядається як **user-modified** і пропускається назавжди, тому ваші правки ніколи не будуть перезаписані.

Захист хороший, але має один гострий недолік. Якщо ти відредагував вбудовану навичку, а потім захотів відмовитися від змін і повернутися до вбудованої версії, просто скопіювавши її з `~/.hermes/hermes-agent/skills/`, маніфест все ще містить *старий* оригінальний хеш з моменту останньої успішної синхронізації. Твій новий скопійований вміст (поточний вбудований хеш) не збігається зі застарілим оригінальним хешем, тому синхронізація продовжує позначати його як user-modified.

`hermes skills reset` — це вихідний шлях:

```bash
# Safe: clears the manifest entry for this skill. Your current copy is preserved,
# but the next sync re-baselines against it so future updates work normally.
hermes skills reset google-workspace

# Full restore: also deletes your local copy and re-copies the current bundled
# version. Use this when you want the pristine upstream skill back.
hermes skills reset google-workspace --restore

# Non-interactive (e.g. in scripts or TUI mode) — skip the --restore confirmation.
hermes skills reset google-workspace --restore --yes
```

Ту ж саму команду можна виконати в чаті як slash‑command:

```text
/skills reset google-workspace
/skills reset google-workspace --restore
```

:::note Profiles
Кожен профіль має свій власний `.bundled_manifest` у своєму `HERMES_HOME`, тому `hermes -p coder skills reset <name>` впливає лише на цей профіль.
:::

### Slash‑команди (всередині чату)

Усі ті ж команди працюють з `/skills`:

```text
/skills browse
/skills search react --source skills-sh
/skills search https://mintlify.com/docs --source well-known
/skills inspect skills-sh/vercel-labs/json-render/json-render-react
/skills install openai/skills/skill-creator --force
/skills check
/skills update
/skills reset google-workspace
/skills list
```

Офіційні додаткові навички все ще використовують ідентифікатори типу `official/security/1password` та `official/migration/openclaw-migration`.