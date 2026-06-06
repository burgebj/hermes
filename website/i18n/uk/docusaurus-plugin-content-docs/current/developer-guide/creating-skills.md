---
sidebar_position: 3
title: "Створення Skills"
description: "Як створювати навички для Hermes Agent — формат SKILL.md, рекомендації та публікація"
---

# Створення skill‑ів

Skill‑и — це переважний спосіб додати нові можливості до Hermes Agent. Вони простіші у створенні, ніж інструменти, не вимагають змін коду агента та можуть бути поширені серед спільноти.
## Чи має це бути **Skill** чи **Tool**?

Зроби це **Skill**, коли:
- Функціональність можна виразити інструкціями + командами оболонки + існуючими інструментами
- Вона обгортає зовнішній CLI або API, який агент може викликати через `terminal` або `web_extract`
- Не потрібна кастомна інтеграція Python або управління API‑ключами, вбудоване в агента
- Приклади: пошук в arXiv, робочі процеси git, управління Docker, обробка PDF, електронна пошта через CLI‑інструменти

Зроби це **Tool**, коли:
- Потрібна повна інтеграція з API‑ключами, процесами автентифікації або багатокомпонентною конфігурацією
- Потрібна кастомна логіка обробки, яка має виконуватись точно щоразу
- Потрібна обробка бінарних даних, потокова передача або події в реальному часі
- Приклади: автоматизація браузера, TTS, аналіз зображень
## Структура каталогу навичок

Вбудовані навички розташовані в `skills/`, організовані за категоріями. Офіційні необов’язкові навички використовують ту ж структуру в `optional-skills/`:

```text
skills/
├── research/
│   └── arxiv/
│       ├── SKILL.md              # Required: main instructions
│       └── scripts/              # Optional: helper scripts
│           └── search_arxiv.py
├── productivity/
│   └── ocr-and-documents/
│       ├── SKILL.md
│       ├── scripts/
│       └── references/
└── ...
```
## Формат SKILL.md

```markdown
---
name: my-skill
description: Brief description (shown in skill search results)
version: 1.0.0
author: Your Name
license: MIT
platforms: [macos, linux]          # Optional — restrict to specific OS platforms
                                   #   Valid: macos, linux, windows
                                   #   Omit to load on all platforms (default)
metadata:
  hermes:
    tags: [Category, Subcategory, Keywords]
    related_skills: [other-skill-name]
    requires_toolsets: [web]            # Optional — only show when these toolsets are active
    requires_tools: [web_search]        # Optional — only show when these tools are available
    fallback_for_toolsets: [browser]    # Optional — hide when these toolsets are active
    fallback_for_tools: [browser_navigate]  # Optional — hide when these tools exist
    config:                              # Optional — config.yaml settings the skill needs
      - key: my.setting
        description: "What this setting controls"
        default: "sensible-default"
        prompt: "Display prompt for setup"
required_environment_variables:          # Optional — env vars the skill needs
  - name: MY_API_KEY
    prompt: "Enter your API key"
    help: "Get one at https://example.com"
    required_for: "API access"
---

# Skill Title

Brief intro.

## When to Use
Trigger conditions — when should the agent load this skill?

## Quick Reference
Table of common commands or API calls.

## Procedure
Step-by-step instructions the agent follows.

## Pitfalls
Known failure modes and how to handle them.

## Verification
How the agent confirms it worked.
```

### Платформо‑специфічні навички

Навички можуть обмежувати себе певними операційними системами за допомогою поля `platforms`:

```yaml
platforms: [macos]            # macOS only (e.g., iMessage, Apple Reminders)
platforms: [macos, linux]     # macOS and Linux
platforms: [windows]          # Windows only
```

Якщо поле вказано, навичка автоматично приховується у системному підказці, у `skills_list()` та у слеш‑командах на несумісних платформах. Якщо поле пропущено або залишено порожнім, навичка завантажується на всіх платформах (зворотна сумісність).

### Умовна активація навички

Навички можуть оголошувати залежності від конкретних інструментів або наборів інструментів. Це визначає, чи з’явиться навичка у системному підказці для даної сесії.

```yaml
metadata:
  hermes:
    requires_toolsets: [web]           # Hide if the web toolset is NOT active
    requires_tools: [web_search]       # Hide if web_search tool is NOT available
    fallback_for_toolsets: [browser]   # Hide if the browser toolset IS active
    fallback_for_tools: [browser_navigate]  # Hide if browser_navigate IS available
```

| Поле | Поведінка |
|-------|----------|
| `requires_toolsets` | Навичка **приховується**, коли **будь‑який** зазначений набір інструментів **не** доступний |
| `requires_tools` | Навичка **приховується**, коли **будь‑який** зазначений інструмент **не** доступний |
| `fallback_for_toolsets` | Навичка **приховується**, коли **будь‑який** зазначений набір інструментів **доступний** |
| `fallback_for_tools` | Навичка **приховується**, коли **будь‑який** зазначений інструмент **доступний** |

**Випадок використання `fallback_for_*`**: створити навичку, яка слугує запасним (фолбек) варіантом, коли основний інструмент недоступний. Наприклад, навичка `duckduckgo-search` з `fallback_for_tools: [web_search]` буде показана лише тоді, коли інструмент веб‑пошуку (який потребує API‑ключа) не налаштовано.

**Випадок використання `requires_*`**: створити навичку, яка має сенс лише за наявності певних інструментів. Наприклад, навичка робочого процесу веб‑скрапінгу з `requires_toolsets: [web]` не буде захаращувати підказку, коли веб‑інструменти вимкнено.

### Вимоги до змінних середовища

Навички можуть оголошувати змінні середовища, які їм потрібні. Коли навичка завантажується через `skill_view`, її необхідні змінні автоматично реєструються для передачі у пісочничі середовища виконання (термінал, `execute_code`).

```yaml
required_environment_variables:
  - name: TENOR_API_KEY
    prompt: "Tenor API key"               # Shown when prompting user
    help: "Get your key at https://tenor.com"  # Help text or URL
    required_for: "GIF search functionality"   # What needs this var
```

Кожен запис підтримує:
- `name` (обов’язково) — назва змінної середовища
- `prompt` (необов’язково) — текст підказки при запиті у користувача значення
- `help` (необов’язково) — довідковий текст або URL для отримання значення
- `required_for` (необов’язково) — опис того, яка функція потребує цю змінну

Користувачі також можуть вручну налаштувати передані змінні у `config.yaml`:

```yaml
terminal:
  env_passthrough:
    - MY_CUSTOM_VAR
    - ANOTHER_VAR
```

Дивись `skills/apple/` для прикладів навичок, доступних лише на macOS.
## Безпечна налаштування під час завантаження

Використовуй `required_environment_variables`, коли навичка потребує API‑ключа або токена. Відсутні значення **не** приховують навичку від виявлення. Натомість Hermes запитує їх безпечно, коли навичка завантажується в локальному CLI.

```yaml
required_environment_variables:
  - name: TENOR_API_KEY
    prompt: Tenor API key
    help: Get a key from https://developers.google.com/tenor
    required_for: full functionality
```

Користувач може пропустити налаштування і продовжити завантаження навички. Hermes ніколи не розкриває необроблене секретне значення моделі. Сесії шлюзу та обміну повідомленнями показують локальні інструкції з налаштування замість збору секретів у потоці.

:::tip Sandbox Passthrough
Коли твоя навичка завантажується, будь‑які оголошені `required_environment_variables`, які встановлені, **автоматично передаються** у пісочниці `execute_code` та `terminal` — включаючи віддалені бекенди типу Docker і Modal. Скрипти твоєї навички можуть отримати доступ до `$TENOR_API_KEY` (або `os.environ["TENOR_API_KEY"]` у Python) без додаткових налаштувань користувача. Дивись [Environment Variable Passthrough](/user-guide/security#environment-variable-passthrough) для деталей.
:::

Застарілий `prerequisites.env_vars` залишається підтримуваним як зворотно‑сумісний псевдонім.

### Налаштування конфігурації (config.yaml)

Навички можуть оголошувати не‑секретні налаштування, які зберігаються в `config.yaml` у просторі імен `skills.config`. На відміну від змінних середовища (які є секретами у `.env`), налаштування конфігурації призначені для шляхів, уподобань та інших нечутливих значень.

```yaml
metadata:
  hermes:
    config:
      - key: myplugin.path
        description: Path to the plugin data directory
        default: "~/myplugin-data"
        prompt: Plugin data directory path
      - key: myplugin.domain
        description: Domain the plugin operates on
        default: ""
        prompt: Plugin domain (e.g., AI/ML research)
```

Кожен запис підтримує:
- `key` (обов’язково) — dot‑path для налаштування (наприклад, `myplugin.path`)
- `description` (обов’язково) — пояснює, що контролює налаштування
- `default` (необов’язково) — значення за замовчуванням, якщо користувач його не вказав
- `prompt` (необов’язково) — текст запиту, що показується під час `hermes config migrate`; використовується `description`, якщо не вказано

**Як це працює:**

1. **Зберігання:** Значення записуються у `config.yaml` під `skills.config.<key>`:
   ```yaml
   skills:
     config:
       myplugin:
         path: ~/my-data
   ```

2. **Виявлення:** `hermes config migrate` сканує всі увімкнені навички, знаходить неналаштовані параметри та запитує користувача. Налаштування також відображаються у `hermes config show` у розділі «Skill Settings».

3. **Ін’єкція під час виконання:** Коли навичка завантажується, її значення конфігурації резольвуються і додаються до повідомлення навички:
   ```
   [Skill config (from ~/.hermes/config.yaml):
     myplugin.path = /home/user/my-data
   ]
   ```
   Агент бачить налаштовані значення без необхідності читати `config.yaml` безпосередньо.

4. **Ручне налаштування:** Користувачі також можуть встановити значення безпосередньо:
   ```bash
   hermes config set skills.config.myplugin.path ~/my-data
   ```

:::tip Коли що використовувати
Використовуй `required_environment_variables` для API‑ключів, токенів та інших **секретів** (зберігаються у `~/.hermes/.env`, ніколи не показуються моделі). Використовуй `config` для **шляхів, уподобань та нечутливих налаштувань** (зберігаються у `config.yaml`, видимі у `config show`).
:::

### Вимоги до файлів облікових даних (OAuth‑токени тощо)

Навички, які працюють з OAuth або обліковими даними у вигляді файлів, можуть оголошувати файли, які потрібно змонтувати в віддалені пісочниці. Це стосується облікових даних, збережених **у вигляді файлів** (а не змінних середовища) — зазвичай це файли токенів OAuth, створені скриптом налаштування.

```yaml
required_credential_files:
  - path: google_token.json
    description: Google OAuth2 token (created by setup script)
  - path: google_client_secret.json
    description: Google OAuth2 client credentials
```

Кожен запис підтримує:
- `path` (обов’язково) — шлях до файлу відносно `~/.hermes/`
- `description` (необов’язково) — пояснює, що це за файл і як його створити

Після завантаження Hermes перевіряє наявність цих файлів. Якщо файл відсутній, генерується `setup_needed`. Існуючі файли автоматично:
- **Монтуються в Docker‑контейнери** як bind‑mount лише для читання
- **Синхронізуються в Modal‑пісочниці** (при створенні + перед кожною командою, щоб OAuth працював у середині сесії)
- Доступні на **локальному** бекенді без спеціальної обробки

:::tip Коли що використовувати
Використовуй `required_environment_variables` для простих API‑ключів і токенів (рядки, що зберігаються у `~/.hermes/.env`). Використовуй `required_credential_files` для файлів токенів OAuth, клієнтських секретів, JSON‑файлів сервісних облікових записів, сертифікатів або будь‑яких облікових даних, що зберігаються у файлі.
:::

Дивись `skills/productivity/google-workspace/SKILL.md` для повного прикладу, що використовує обидва підходи.
## Керівництво щодо навичок

### Без зовнішніх залежностей

Надавай перевагу стандартній бібліотеці Python, `curl` та існуючим інструментам Hermes (`web_extract`, `terminal`, `read_file`). Якщо потрібна додаткова залежність, задокументуй кроки її встановлення у навичці.

### Прогресивне розкриття

Розміщуй найпоширеніший робочий процес першим. Крайові випадки та розширене використання розміщуй внизу. Це знижує використання токенів для типових завдань.

### Додай допоміжні скрипти

Для парсингу XML/JSON або складної логіки розміщуй допоміжні скрипти у `scripts/` — не очікуй, що LLM буде писати парсери вбудовано щоразу.

### Доставляй медіа як документи (`[[as_document]]`)

Якщо твоя навичка створює скріншот високої роздільної здатності, діаграму чи будь‑яке зображення, де втрата якості через попередній перегляд шкодить, встав буквальну директиву `[[as_document]]` десь у відповіді (зазвичай у останньому рядку). Шлюз видаляє директиву та доставляє кожен шлях до витягнутого медіа у цій відповіді як завантажуваний файл‑вкладення замість вбудованого зображення. Дивись [Вихід навички та доставка медіа](../user-guide/features/skills.md#skill-output-and-media-delivery) для повної семантики.

#### Посилання на вбудовані скрипти з SKILL.md

Коли навичка завантажується, повідомлення про активацію розкриває абсолютний каталог навички у вигляді `[Skill directory: /abs/path]` і підставляє два шаблонних токени у будь‑якому місці тіла SKILL.md:

| Токен | Замінюється на |
|---|---|
| `${HERMES_SKILL_DIR}` | Абсолютний шлях до каталогу навички |
| `${HERMES_SESSION_ID}` | Ідентифікатор активної сесії (залишається без змін, якщо сесії немає) |

Тому SKILL.md може вказати агенту виконати вбудований скрипт безпосередньо:

```markdown
To analyse the input, run:

    node ${HERMES_SKILL_DIR}/scripts/analyse.js <input>
```

Агент бачить підставлений абсолютний шлях і викликає інструмент `terminal` з готовою до виконання командою — без обчислення шляхів, без додаткового раун‑трипу `skill_view`. Вимкнути підстановку глобально можна за допомогою `skills.template_vars: false` у `config.yaml`.

#### Вбудовані фрагменти оболонки (за згодою)

Навички також можуть вбудовувати фрагменти оболонки у вигляді ``!`cmd` `` у тілі SKILL.md. При увімкненні `stdout` кожного фрагмента вбудовується у повідомлення перед тим, як агент його прочитає, тож навички можуть вставляти динамічний контекст:

```markdown
Current date: !`date -u +%Y-%m-%d`
Git branch: !`git -C ${HERMES_SKILL_DIR} rev-parse --abbrev-ref HEAD`
```

Це **вимкнено за замовчуванням** — будь‑який фрагмент у SKILL.md виконується на хості без підтвердження, тому вмикай його лише для джерел навичок, яким довіряєш:

```yaml
# config.yaml
skills:
  inline_shell: true
  inline_shell_timeout: 10   # seconds per snippet
```

Фрагменти виконуються у каталозі навички як робочій директорії, а вивід обмежений 4000 символами. Помилки (тайм‑аут, ненульовий код виходу) відображаються як короткий маркер `[inline-shell error: ...]` замість того, щоб порушити всю навичку.

### Перевірка

Запусти навичку і переконайся, що агент виконує інструкції правильно:

```bash
hermes chat --toolsets skills -q "Use the X skill to do Y"
```
## Де має жити skill?

Bundled skills (in `skills/`) ship with every Hermes install. They should be **broadly useful to most users**:

- Обробка документів, веб‑пошук, типові робочі процеси розробки, системне адміністрування
- Використовуються регулярно широким колом користувачів

If your skill is official and useful but not universally needed (e.g., a paid service integration, a heavyweight dependency), put it in **`optional-skills/`** — it ships with the repo, is discoverable via `hermes skills browse` (labeled "official"), and installs with builtin trust.

If your skill is specialized, community‑contributed, or niche, it's better suited for a **Skills Hub** — upload it to a registry and share it via `hermes skills install`.
## Публікація навичок

### У центр навичок

```bash
hermes skills publish skills/my-skill --to github --repo owner/repo
```

### У власний репозиторій

Додай свій репозиторій як tap:

```bash
hermes skills tap add owner/repo
```

Користувачі зможуть шукати та встановлювати пакети з твого репозиторію.
## Security Scanning

Усі встановлені в hub `skills` проходять через сканер безпеки, який перевіряє:

- шаблони виведення даних
- спроби ін’єкції підказок
- руйнівні команди
- ін’єкції оболонки

Рівні довіри:
- `builtin` — постачається з Hermes (завжди довірений)
- `official` — з `optional-skills/` у репозиторії (вбудована довіра, без попередження про сторонні `skills`)
- `trusted` — з `openai/skills`, `anthropics/skills`, `huggingface/skills`
- `community` — небезпечні результати можна перевизначити за допомогою `--force`; рішення `dangerous` залишаються заблокованими

Тепер Hermes може споживати сторонні `skills` за допомогою кількох зовнішніх моделей виявлення:
- прямі ідентифікатори GitHub (наприклад `openai/skills/k8s`)
- ідентифікатори `skills.sh` (наприклад `skills-sh/vercel-labs/json-render/json-render-react`)
- відомі кінцеві точки, що обслуговуються за `/.well-known/skills/index.json`

Якщо ти хочеш, щоб твої `skills` були доступні без встановлювача, специфічного для GitHub, розглянь можливість їх розміщення на відомій кінцевій точці, окрім публікації в репозиторії чи маркетплейсі.