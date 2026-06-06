---
sidebar_position: 8
title: "Контекстні файли"
description: "Файли контексту проєкту — .hermes.md, AGENTS.md, CLAUDE.md, global SOUL.md та .cursorrules — автоматично додаються до кожної розмови"
---

# Файли контексту

Hermes Agent автоматично виявляє та завантажує файли контексту, які формують його поведінку. Деякі з них локальні для проєкту і виявляються у вашій робочій директорії. `SOUL.md` тепер глобальний для екземпляра Hermes і завантажується лише з `HERMES_HOME`.

## Підтримувані файли контексту

| Файл | Призначення | Виявлення |
|------|-------------|-----------|
| **.hermes.md** / **HERMES.md** | Інструкції проєкту (найвищий пріоритет) | Пошук до кореня git |
| **AGENTS.md** | Інструкції проєкту, конвенції, архітектура | CWD під час запуску + піддиректорії поступово |
| **CLAUDE.md** | Файли контексту Claude Code (також виявляються) | CWD під час запуску + піддиректорії поступово |
| **SOUL.md** | Глобальна персональність та налаштування тону для цього екземпляра Hermes | лише `HERMES_HOME/SOUL.md` |
| **.cursorrules** | Конвенції кодування Cursor IDE | лише CWD |
| **.cursor/rules/*.mdc** | Модулі правил Cursor IDE | лише CWD |

:::info Пріоритетна система
Завантажується лише **один** тип контексту проєкту за сесію (перший збіг виграє): `.hermes.md` → `AGENTS.md` → `CLAUDE.md` → `.cursorrules`. **SOUL.md** завжди завантажується окремо як ідентичність агента (слот #1).
:::

## AGENTS.md

`AGENTS.md` — основний файл контексту проєкту. Він повідомляє агенту, як структурований ваш проєкт, які конвенції слід дотримуватись і які особливі інструкції є.

### Поступове виявлення піддиректорій

На початку сесії Hermes завантажує `AGENTS.md` з вашої робочої директорії у системний підказник. Коли агент переходить у піддиректорії під час сесії (через `read_file`, `terminal`, `search_files` тощо), він **поступово виявляє** файли контексту в цих директоріях і вставляє їх у розмову в момент, коли вони стають релевантними.

```
my-project/
├── AGENTS.md              ← Loaded at startup (system prompt)
├── frontend/
│   └── AGENTS.md          ← Discovered when agent reads frontend/ files
├── backend/
│   └── AGENTS.md          ← Discovered when agent reads backend/ files
└── shared/
    └── AGENTS.md          ← Discovered when agent reads shared/ files
```

Такий підхід має два переваги над завантаженням усього одразу:
- **Без надмірного розміру системного підказника** — підказки піддиректорій з’являються лише за потреби
- **Збереження кешу підказника** — системний підказник залишається стабільним між ходами

Кожна піддиректорія перевіряється максимум один раз за сесію. Виявлення також піднімається до батьківських директорій, тому читання `backend/src/main.py` виявить `backend/AGENTS.md`, навіть якщо в `backend/src/` немає власного файлу контексту.

:::info
Файли контексту піддиректорій проходять той самий [скан безпеки](#security-prompt-injection-protection), що й файли контексту під час запуску. Шкідливі файли блокуються.
:::

### Приклад AGENTS.md

```markdown
# Project Context

This is a Next.js 14 web application with a Python FastAPI backend.

## Architecture
- Frontend: Next.js 14 with App Router in `/frontend`
- Backend: FastAPI in `/backend`, uses SQLAlchemy ORM
- Database: PostgreSQL 16
- Deployment: Docker Compose on a Hetzner VPS

## Conventions
- Use TypeScript strict mode for all frontend code
- Python code follows PEP 8, use type hints everywhere
- All API endpoints return JSON with `{data, error, meta}` shape
- Tests go in `__tests__/` directories (frontend) or `tests/` (backend)

## Important Notes
- Never modify migration files directly — use Alembic commands
- The `.env.local` file has real API keys, don't commit it
- Frontend port is 3000, backend is 8000, DB is 5432
```

## SOUL.md

`SOUL.md` керує персональністю, тоном і стилем спілкування агента. Дивись сторінку [Personality](/user-guide/features/personality) для повних деталей.

**Розташування:**

- `~/.hermes/SOUL.md`
- або `$HERMES_HOME/SOUL.md`, якщо ти запускаєш Hermes з кастомною домашньою директорією

Важливі деталі:

- Hermes автоматично створює типовий `SOUL.md`, якщо його ще немає
- Hermes завантажує `SOUL.md` лише з `HERMES_HOME`
- Hermes не шукає `SOUL.md` у робочій директорії
- Якщо файл порожній, нічого з `SOUL.md` не додається до підказника
- Якщо файл містить контент, він вставляється дослівно після сканування та обрізки

## .cursorrules

Hermes сумісний з файлом `.cursorrules` Cursor IDE та модулями правил `.cursor/rules/*.mdc`. Якщо ці файли існують у корені твого проєкту і не знайдено файлів контексту вищого пріоритету (`.hermes.md`, `AGENTS.md` або `CLAUDE.md`), вони завантажуються як контекст проєкту.

Тобто твої існуючі конвенції Cursor автоматично застосовуються при використанні Hermes.

## Як завантажуються файли контексту

### При запуску (системний підказник)

Файли контексту завантажуються функцією `build_context_files_prompt()` у `agent/prompt_builder.py`:

1. **Сканування робочої директорії** — перевіряє `.hermes.md` → `AGENTS.md` → `CLAUDE.md` → `.cursorrules` (перший збіг виграє)
2. **Читання вмісту** — кожен файл читається як UTF‑8 текст
3. **Скан безпеки** — вміст перевіряється на шаблони ін’єкції підказок
4. **Обрізка** — файли, що перевищують 20 000 символів, обрізаються (70 % початку, 20 % кінця, з маркером посередині)
5. **Збірка** — всі секції комбінуються під заголовком `# Project Context`
6. **Вставка** — зібраний контент додається до системного підказника

### Під час сесії (поступове виявлення)

`SubdirectoryHintTracker` у `agent/subdirectory_hints.py` стежить за аргументами викликів інструментів, що містять шляхи до файлів:

1. **Видобуток шляхів** — після кожного виклику інструменту шляхи витягуються з аргументів (`path`, `workdir`, shell‑команди)
2. **Прохід по предках** — перевіряються директорія та до 5 батьківських директорій (зупиняючись на вже відвіданих)
3. **Завантаження підказки** — якщо знайдено `AGENTS.md`, `CLAUDE.md` або `.cursorrules`, він завантажується (перший збіг у директорії)
4. **Скан безпеки** — та ж перевірка ін’єкції підказок, що й для файлів під час запуску
5. **Обрізка** — обмеження 8 000 символів на файл
6. **Вставка** — додається до результату інструменту, так що модель бачить це в контексті природно

Фінальна секція підказника виглядає приблизно так:

```text
# Project Context

The following project context files have been loaded and should be followed:

## AGENTS.md

[Your AGENTS.md content here]

## .cursorrules

[Your .cursorrules content here]

[Your SOUL.md content here]
```

Зверни увагу, що вміст SOUL вставляється без додаткового обгорткового тексту.

## Безпека: захист від ін’єкції підказок

Усі файли контексту скануються на потенційну ін’єкцію підказок перед включенням. Сканер шукає:

- **Спроби переопреділення інструкцій**: “ignore previous instructions”, “disregard your rules”
- **Шаблони обману**: “do not tell the user”
- **Перевизначення системного підказника**: “system prompt override”
- **Приховані HTML‑коментарі**: `<!-- ignore instructions -->`
- **Приховані div‑елементи**: `<div style="display:none">`
- **Витік облікових даних**: `curl ... $API_KEY`
- **Доступ до секретних файлів**: `cat .env`, `cat credentials`
- **Невидимі символи**: нуль‑ширинні пробіли, бідірекційні переопреділення, word joiners

Якщо виявлено будь‑який шаблон загрози, файл блокується:

```
[BLOCKED: AGENTS.md contained potential prompt injection (prompt_injection). Content not loaded.]
```

:::warning
Цей сканер захищає від поширених шаблонів ін’єкції, але не замінює перевірку файлів контексту в спільних репозиторіях. Завжди перевіряй вміст AGENTS.md у проєктах, які ти не створював.
:::

## Обмеження розмірів

| Обмеження | Значення |
|----------|----------|
| Макс. кількість символів у файлі | 20 000 (~7 000 токенів) |
| Співвідношення обрізки початку | 70 % |
| Співвідношення обрізки кінця | 20 % |
| Маркер обрізки | 10 % (показує кількість символів і пропонує використати інструменти файлів) |

Коли файл перевищує 20 000 символів, повідомлення про обрізку виглядає так:

```
[...truncated AGENTS.md: kept 14000+4000 of 25000 chars. Use file tools to read the full file.]
```

## Поради для ефективних файлів контексту

:::tip Кращі практики для AGENTS.md
1. **Тримай їх лаконічними** — залишайся значно нижче 20 К символів; агент читає їх кожен хід
2. **Структуруй за заголовками** — використовуйте секції `##` для архітектури, конвенцій, важливих нотаток
3. **Додавай конкретні приклади** — показуй бажані шаблони коду, форми API, правила іменування
4. **Вказуй, чого НЕ робити** — “never modify migration files directly”
5. **Перелічуй ключові шляхи та порти** — агент використовує їх у командах терміналу
6. **Оновлюй по мірі розвитку проєкту** — застарілий контекст гірший, ніж його відсутність
:::

### Контекст per‑піддиректорія

Для монорепозиторіїв розміщуйте інструкції, специфічні для піддиректорій, у вкладених файлах AGENTS.md:

```markdown
<!-- frontend/AGENTS.md -->
# Frontend Context

- Use `pnpm` not `npm` for package management
- Components go in `src/components/`, pages in `src/app/`
- Use Tailwind CSS, never inline styles
- Run tests with `pnpm test`
```

```markdown
<!-- backend/AGENTS.md -->
# Backend Context

- Use `poetry` for dependency management
- Run the dev server with `poetry run uvicorn main:app --reload`
- All endpoints need OpenAPI docstrings
- Database models are in `models/`, schemas in `schemas/`
```