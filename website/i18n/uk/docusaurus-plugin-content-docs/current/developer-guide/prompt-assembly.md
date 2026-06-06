---
sidebar_position: 5
title: "Збірка підказок"
description: "Як Hermes створює системний підказку, зберігає стабільність кешу та впроваджує ефемерні шари"
---

# Збірка підказки

Hermes навмисно розділяє:

- **кешований стан системної підказки**
- **епхемерні додатки під час виклику API**

Це один із найважливіших дизайнерських рішень у проєкті, оскільки він впливає на:

- використання токенів
- ефективність кешування підказки
- безперервність сесії
- правильність пам’яті

Основні файли:

- `run_agent.py`
- `agent/prompt_builder.py`
- `tools/memory_tool.py`

## Шари кешованої системної підказки

Кешована системна підказка збирається приблизно у такому порядку:

1. ідентичність агента — `SOUL.md` з `HERMES_HOME`, якщо доступний, інакше використовується запасний (варіант) `DEFAULT_AGENT_IDENTITY` у `prompt_builder.py`
2. керівництво поведінки, орієнтоване на інструменти
3. статичний блок Honcho (коли активний)
4. необов’язкове системне повідомлення
5. заморожений знімок MEMORY
6. заморожений знімок USER профілю
7. індекс навичок
8. файли контексту (`AGENTS.md`, `.cursorrules`, `.cursor/rules/*.mdc`) — `SOUL.md` **не** включається тут, коли вже завантажений як ідентичність у кроці 1
9. мітка часу / необов’язковий ідентифікатор сесії
10. підказка платформи

Коли встановлено `skip_context_files` (наприклад, делегування підагенту), `SOUL.md` не завантажується і використовується жорстко закодований `DEFAULT_AGENT_IDENTITY`.

### Конкретний приклад: зібрана системна підказка

Ось спрощений вигляд фінальної системної підказки, коли присутні всі шари (коментарі показують джерело кожного розділу):

```
# Layer 1: Agent Identity (from ~/.hermes/SOUL.md)
You are Hermes, an AI assistant created by Nous Research.
You are an expert software engineer and researcher.
You value correctness, clarity, and efficiency.
...

# Layer 2: Tool-aware behavior guidance
You have persistent memory across sessions. Save durable facts using
the memory tool: user preferences, environment details, tool quirks,
and stable conventions. Memory is injected into every turn, so keep
it compact and focused on facts that will still matter later.
...
When the user references something from a past conversation or you
suspect relevant cross-session context exists, use session_search
to recall it before asking them to repeat themselves.

# Tool-use enforcement (for GPT/Codex models only)
You MUST use your tools to take action — do not describe what you
would do or plan to do without actually doing it.
...

# Layer 3: Honcho static block (when active)
[Honcho personality/context data]

# Layer 4: Optional system message (from config or API)
[User-configured system message override]

# Layer 5: Frozen MEMORY snapshot
## Persistent Memory
- User prefers Python 3.12, uses pyproject.toml
- Default editor is nvim
- Working on project "atlas" in ~/code/atlas
- Timezone: US/Pacific

# Layer 6: Frozen USER profile snapshot
## User Profile
- Name: Alice
- GitHub: alice-dev

# Layer 7: Skills index
## Skills (mandatory)
Before replying, scan the skills below. If one clearly matches
your task, load it with skill_view(name) and follow its instructions.
...
<available_skills>
  software-development:
    - code-review: Structured code review workflow
    - test-driven-development: TDD methodology
  research:
    - arxiv: Search and summarize arXiv papers
</available_skills>

# Layer 8: Context files (from project directory)
# Project Context
The following project context files have been loaded and should be followed:

## AGENTS.md
This is the atlas project. Use pytest for testing. The main
entry point is src/atlas/main.py. Always run `make lint` before
committing.

# Layer 9: Timestamp + session
Current time: 2026-03-30T14:30:00-07:00
Session: abc123

# Layer 10: Platform hint
You are a CLI AI Agent. Try not to use markdown but simple text
renderable inside a terminal.
```

## Як `SOUL.md` з’являється у підказці

`SOUL.md` знаходиться за шляхом `~/.hermes/SOUL.md` і слугує ідентичністю агента — першим розділом системної підказки. Логіка завантаження у `prompt_builder.py` працює так:

```python
# From agent/prompt_builder.py (simplified)
def load_soul_md() -> Optional[str]:
    soul_path = get_hermes_home() / "SOUL.md"
    if not soul_path.exists():
        return None
    content = soul_path.read_text(encoding="utf-8").strip()
    content = _scan_context_content(content, "SOUL.md")  # Security scan
    content = _truncate_content(content, "SOUL.md")       # Cap at 20k chars
    return content
```

Коли `load_soul_md()` повертає вміст, він замінює жорстко закодований `DEFAULT_AGENT_IDENTITY`. Потім викликається функція `build_context_files_prompt()` з параметром `skip_soul=True`, щоб запобігти дворазовому появленню `SOUL.md` (одноразово як ідентичність, одноразово як файл контексту).

Якщо `SOUL.md` не існує, система переходить до запасного (варіанту):

```
You are Hermes Agent, an intelligent AI assistant created by Nous Research.
You are helpful, knowledgeable, and direct. You assist users with a wide
range of tasks including answering questions, writing and editing code,
analyzing information, creative work, and executing actions via your tools.
You communicate clearly, admit uncertainty when appropriate, and prioritize
being genuinely useful over being verbose unless otherwise directed below.
Be targeted and efficient in your exploration and investigations.
```

## Як ін’єктуються файли контексту

`build_context_files_prompt()` використовує **систему пріоритетів** — завантажується лише один тип контексту проєкту (перший збіг виграє):

```python
# From agent/prompt_builder.py (simplified)
def build_context_files_prompt(cwd=None, skip_soul=False):
    cwd_path = Path(cwd).resolve()

    # Priority: first match wins — only ONE project context loaded
    project_context = (
        _load_hermes_md(cwd_path)       # 1. .hermes.md / HERMES.md (walks to git root)
        or _load_agents_md(cwd_path)    # 2. AGENTS.md (cwd only)
        or _load_claude_md(cwd_path)    # 3. CLAUDE.md (cwd only)
        or _load_cursorrules(cwd_path)  # 4. .cursorrules / .cursor/rules/*.mdc
    )

    sections = []
    if project_context:
        sections.append(project_context)

    # SOUL.md from HERMES_HOME (independent of project context)
    if not skip_soul:
        soul_content = load_soul_md()
        if soul_content:
            sections.append(soul_content)

    if not sections:
        return ""

    return (
        "# Project Context\n\n"
        "The following project context files have been loaded "
        "and should be followed:\n\n"
        + "\n".join(sections)
    )
```

### Деталі виявлення файлів контексту

| Пріоритет | Файли | Область пошуку | Примітки |
|----------|-------|----------------|----------|
| 1 | `.hermes.md`, `HERMES.md` | CWD до кореня git | Hermes‑рідний конфіг проєкту |
| 2 | `AGENTS.md` | лише CWD | Спільний файл інструкцій агента |
| 3 | `CLAUDE.md` | лише CWD | Сумісність з Claude Code |
| 4 | `.cursorrules`, `.cursor/rules/*.mdc` | лише CWD | Сумісність з Cursor |

Усі файли контексту:
- **Перевіряються на безпеку** — скануються на шаблони ін’єкції підказок (невидимий юнікод, «ignore previous instructions», спроби викрадення облікових даних)
- **Обрізаються** — обмежуються 20 000 символами за співвідношенням 70/20 head/tail з маркером обрізки
- **Видаляються YAML‑frontmatter** — frontmatter у `.hermes.md` видаляється (зарезервовано для майбутніх перевизначень конфігурації)

## Шари лише під час виклику API

Ці елементи навмисно *не* зберігаються як частина кешованої системної підказки:

- `ephemeral_system_prompt`
- повідомлення‑заповнювачі
- контекстні накладання, отримані через шлюз
- подальший виклик Honcho, ін’єктований у поточне повідомлення користувача

Таке розділення зберігає стабільний префікс для кешування.

## Знімки пам’яті

Локальна пам’ять та дані профілю користувача ін’єктуються як заморожені знімки на початку сесії. Записи під час сесії оновлюють стан на диску, але не змінюють вже зібрану системну підказку, доки не буде нової сесії або примусової перебудови.

## Файли контексту

`agent/prompt_builder.py` сканує та санітує файли контексту проєкту, використовуючи **систему пріоритетів** — завантажується лише один тип (перший збіг виграє):

1. `.hermes.md` / `HERMES.md` (пошук до кореня git)
2. `AGENTS.md` (CWD під час запуску; підкаталоги виявляються поступово під час сесії через `agent/subdirectory_hints.py`)
3. `CLAUDE.md` (лише CWD)
4. `.cursorrules` / `.cursor/rules/*.mdc` (лише CWD)

`SOUL.md` завантажується окремо через `load_soul_md()` для слоту ідентичності. Коли завантаження успішне, `build_context_files_prompt(skip_soul=True)` запобігає його подвійному появленню.

Довгі файли обрізаються перед ін’єкцією.

## Індекс навичок

Система навичок додає компактний індекс навичок до підказки, коли інструменти навичок доступні.

## Підтримувані поверхні налаштування підказки

Більшість користувачів мають працювати з `agent/prompt_builder.py` як з кодом реалізації, а не як з конфігураційною поверхнею. Підтримуваний шлях налаштування — змінювати вхідні дані підказки, які Hermes вже завантажує, а не редагувати шаблони Python безпосередньо.

### Спочатку використай ці поверхні

- `~/.hermes/SOUL.md` — заміни вбудований блок ідентичності на власну персональність агента та бажану поведінку.
- `~/.hermes/MEMORY.md` і `~/.hermes/USER.md` — надай довготривалі факти між сесіями та дані профілю користувача, які мають бути зняті у нових сесіях.
- Файли контексту проєкту, такі як `.hermes.md`, `HERMES.md`, `AGENTS.md`, `CLAUDE.md` або `.cursorrules` — ін’єктують правила роботи репозиторію.
- Навички — пакуй повторно використовувані робочі процеси та посилання без редагування ядра підказки.
- Необов’язкові налаштування системної підказки / перевизначення API — додавай інструкції, специфічні для розгортання, без форку Hermes.
- Ефемерні накладання, такі як `HERMES_EPHEMERAL_SYSTEM_PROMPT` або повідомлення‑заповнювачі — додавай керування на рівні туру, яке не повинно стати частиною кешованого префіксу підказки.

### Коли варто редагувати код

Редагуй `agent/prompt_builder.py` лише якщо ти навмисно підтримуєш форк або вносиш зміни до поведінки upstream. Цей файл збирає «трубопровід» підказки, межі кешу та порядок ін’єкції для кожної сесії. Прямі зміни там — це глобальні зміни продукту, а не налаштування підказки окремого користувача.

Іншими словами:

- якщо ти хочеш іншу ідентичність асистента, редагуй `SOUL.md`
- якщо ти хочеш інші правила репозиторію, редагуй файли контексту проєкту
- якщо ти хочеш повторно використовувані операційні процедури, додавай або змінюй навички
- якщо ти хочеш змінити спосіб, у який Hermes збирає підказки для всіх, змінюй Python і розглядай це як внесок у код

## Чому збірка підказки розділена саме так

Архітектура навмисно оптимізована для:

- збереження кешування підказок на боці провайдера
- уникнення зайвих мутацій історії
- зрозумілості семантики пам’яті
- дозволу шлюзу/ACP/CLI додавати контекст без отруєння постійного стану підказки

## Пов’язані документи

- [Context Compression & Prompt Caching](./context-compression-and-caching.md)
- [Session Storage](./session-storage.md)
- [Gateway Internals](./gateway-internals.md)