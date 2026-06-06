---
sidebar_position: 5
title: "Сборка подсказок"
description: "Как Hermes формирует системный запрос, сохраняет стабильность кэша и внедряет эфемерные слои"
---

# Сборка подсказки

Hermes намеренно разделяет:

- **кешированное состояние системной подсказки**
- **эпхемерные добавления во время вызова API**

Это один из самых важных дизайнерских выборов в проекте, поскольку он влияет на:

- использование токенов
- эффективность кеширования подсказки
- непрерывность сессии
- корректность памяти

Основные файлы:

- `run_agent.py`
- `agent/prompt_builder.py`
- `tools/memory_tool.py`

## Слои кешированной системной подсказки

Кешированная системная подсказка собирается примерно в следующем порядке:

1. идентичность агента — `SOUL.md` из `HERMES_HOME`, если доступен, иначе используется `DEFAULT_AGENT_IDENTITY` в `prompt_builder.py`
2. руководство по поведению с учётом инструментов
3. статический блок Honcho (если активен)
4. необязательное системное сообщение
5. замороженный снимок памяти
6. замороженный снимок профиля пользователя
7. индекс навыков
8. файлы контекста (`AGENTS.md`, `.cursorrules`, `.cursor/rules/*.mdc`) — `SOUL.md` **не** включается здесь, если он уже был загружен как идентичность на шаге 1
9. метка времени / необязательный идентификатор сессии
10. подсказка о платформе

Когда установлен `skip_context_files` (например, делегирование субагенту), `SOUL.md` не загружается и вместо него используется жёстко заданный `DEFAULT_AGENT_IDENTITY`.

### Конкретный пример: собранная системная подсказка

Ниже упрощённый вид окончательной системной подсказки, когда присутствуют все слои (комментарии показывают источник каждой секции):

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

## Как `SOUL.md` появляется в подсказке

`SOUL.md` находится в `~/.hermes/SOUL.md` и служит идентичностью агента — первой секцией системной подсказки. Логика загрузки в `prompt_builder.py` работает так:

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

Когда `load_soul_md()` возвращает содержимое, оно заменяет жёстко заданный `DEFAULT_AGENT_IDENTITY`. Затем вызывается функция `build_context_files_prompt()` с параметром `skip_soul=True`, чтобы предотвратить двойное появление `SOUL.md` (один раз как идентичность, один раз как файл контекста).

Если `SOUL.md` не существует, система переходит к:

```
You are Hermes Agent, an intelligent AI assistant created by Nous Research.
You are helpful, knowledgeable, and direct. You assist users with a wide
range of tasks including answering questions, writing and editing code,
analyzing information, creative work, and executing actions via your tools.
You communicate clearly, admit uncertainty when appropriate, and prioritize
being genuinely useful over being verbose unless otherwise directed below.
Be targeted and efficient in your exploration and investigations.
```

## Как файлы контекста внедряются

`build_context_files_prompt()` использует **систему приоритетов** — загружается только один тип контекста проекта (первый найденный):

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

### Подробности обнаружения файлов контекста

| Приоритет | Файлы | Область поиска | Примечания |
|----------|-------|----------------|------------|
| 1 | `.hermes.md`, `HERMES.md` | Текущий каталог вверх до корня git | Конфигурация проекта Hermes |
| 2 | `AGENTS.md` | Только текущий каталог | Общий файл инструкций агента |
| 3 | `CLAUDE.md` | Только текущий каталог | Совместимость с Claude Code |
| 4 | `.cursorrules`, `.cursor/rules/*.mdc` | Только текущий каталог | Совместимость с Cursor |

Все файлы контекста:
- **Проверяются на безопасность** — сканируются на паттерны внедрения подсказок (невидимый юникод, «ignore previous instructions», попытки кражи учётных данных)
- **Обрезаются** — ограничиваются 20 000 символами с соотношением 70/20 «голова/хвост» и маркером обрезки
- **Удаляется YAML‑frontmatter** — frontmatter из `.hermes.md` удаляется (зарезервировано для будущих переопределений конфигурации)

## Слои, действительные только во время вызова API

Эти слои намеренно *не* сохраняются в кешированной системной подсказке:

- `ephemeral_system_prompt`
- сообщения‑заполнители
- наложения контекста сессии, полученные от шлюза
- последующее воспоминание Honcho, внедрённое в сообщение пользователя текущего хода

Такое разделение сохраняет стабильный префикс для кеширования.

## Снимки памяти

Локальная память и данные профиля пользователя внедряются как замороженные снимки в начале сессии. Записи во время сессии обновляют состояние на диске, но не изменяют уже построенную системную подсказку до начала новой сессии или принудительной пересборки.

## Файлы контекста

`agent/prompt_builder.py` сканирует и санитизирует файлы контекста проекта, используя **систему приоритетов** — загружается только один тип (первый найденный):

1. `.hermes.md` / `HERMES.md` (переход к корню git)
2. `AGENTS.md` (текущий каталог при старте; подкаталоги обнаруживаются постепенно в ходе сессии через `agent/subdirectory_hints.py`)
3. `CLAUDE.md` (только текущий каталог)
4. `.cursorrules` / `.cursor/rules/*.mdc` (только текущий каталог)

`SOUL.md` загружается отдельно через `load_soul_md()` для слота идентичности. При успешной загрузке `build_context_files_prompt(skip_soul=True)` предотвращает двойное появление.

Длинные файлы обрезаются перед внедрением.

## Индекс навыков

Система навыков добавляет компактный индекс навыков в подсказку, когда инструменты навыков доступны.

## Поддерживаемые поверхности кастомизации подсказки

Большинству пользователей следует рассматривать `agent/prompt_builder.py` как реализацию, а не как конфигурационную поверхность. Поддерживаемый путь кастомизации — изменять входные подсказки, которые Hermes уже загружает, а не править шаблоны Python на месте.

### Сначала используйте эти поверхности

- `~/.hermes/SOUL.md` — замените встроенный блок идентичности на свою собственную персону и поведение агента.
- `~/.hermes/MEMORY.md` и `~/.hermes/USER.md` — предоставьте долговременные факты между сессиями и данные профиля пользователя, которые должны быть зафиксированы в новых сессиях.
- Файлы контекста проекта, такие как `.hermes.md`, `HERMES.md`, `AGENTS.md`, `CLAUDE.md` или `.cursorrules` — внедряют правила работы, специфичные для репозитория.
- Навыки — упакуйте переиспользуемые рабочие процессы и ссылки без изменения ядра подсказки.
- Необязательная конфигурация системной подсказки / переопределения API — добавьте текст инструкций, специфичный для развертывания, без форка Hermes.
- Эпхемерные наложения, такие как `HERMES_EPHEMERAL_SYSTEM_PROMPT` или сообщения‑заполнители — добавляют руководство, ограниченное текущим ходом, которое не должно становиться частью кешированного префикса подсказки.

### Когда следует править код

Редактировать `agent/prompt_builder.py` имеет смысл только если ты намеренно поддерживаешь форк или вносишь изменения в основное поведение. Этот файл собирает «трубопровод» подсказки, границы кеша и порядок внедрения для каждой сессии. Прямые правки здесь влияют на продукт глобально, а не на кастомизацию отдельного пользователя.

Иными словами:

- если нужен другой образ ассистента, редактируй `SOUL.md`
- если нужны другие правила репозитория, редактируй файлы контекста проекта
- если нужны переиспользуемые процедуры, добавляй или меняй навыки
- если нужно изменить способ, которым Hermes собирает подсказки для всех, меняй Python‑код и рассматривай это как вклад в кодовую базу

## Почему сборка подсказки разделена именно так

Архитектура намеренно оптимизирована для:

- сохранения кеширования подсказки на стороне провайдера
- избежания ненужных мутаций истории
- понятности семантики памяти
- возможности шлюза/ACP/CLI добавлять контекст без загрязнения постоянного состояния подсказки

## Связанные документы

- [Context Compression & Prompt Caching](./context-compression-and-caching.md)
- [Session Storage](./session-storage.md)
- [Gateway Internals](./gateway-internals.md)