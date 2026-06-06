---
sidebar_position: 12
title: "Робота зі Skills"
description: "Знайди, встанови, використай і створи skills — знання на вимогу, які навчають Hermes новим робочим процесам"
---

# Робота зі Skill‑ами

Skill‑и — це документи‑знання за запитом, які навчають Hermes виконувати конкретні завдання — від генерації ASCII‑арт до керування PR‑ами GitHub. Цей посібник покаже, як користуватися ними щодня.

Для повного технічного довідника дивіться [Skills System](/user-guide/features/skills).

---

## Пошук Skill‑ів

Кожна інсталяція Hermes постачається з вбудованими skill‑ами. Перегляньте, що доступно:

```bash
# In any chat session:
/skills

# Or from the CLI:
hermes skills list
```

Тут показано компактний список з назвами та описами:

```
ascii-art         Generate ASCII art using pyfiglet, cowsay, boxes...
arxiv             Search and retrieve academic papers from arXiv...
github-pr-workflow Full PR lifecycle — create branches, commit...
plan              Plan mode — inspect context, write a markdown...
excalidraw        Create hand-drawn style diagrams using Excalidraw...
```

### Пошук Skill‑у

```bash
# Search by keyword
/skills search docker
/skills search music
```

### Skills Hub

Офіційні необов’язкові skill‑и (більш важкі або вузькоспеціалізовані, які не активні за замовчуванням) доступні через Hub:

```bash
# Browse official optional skills
/skills browse

# Search the hub
/skills search blockchain
```

---

## Використання Skill‑у

Кожен встановлений skill автоматично стає slash‑командою. Просто введи його назву:

```bash
# Load a skill and give it a task
/ascii-art Make a banner that says "HELLO WORLD"
/plan Design a REST API for a todo app
/github-pr-workflow Create a PR for the auth refactor

# Just the skill name (no task) loads it and lets you describe what you need
/excalidraw
```

Ти також можеш запускати skill‑и у природній розмові — попроси Hermes використати конкретний skill, і він завантажить його за допомогою інструмента `skill_view`.

### Прогресивне розкриття

Skill‑и використовують токен‑ефективний патерн завантаження. Агент не завантажує все одразу:

1. **`skills_list()`** — компактний список усіх skill‑ів (~3 k токенів). Завантажується на початку сесії.
2. **`skill_view(name)`** — повний вміст SKILL.md для одного skill‑у. Завантажується, коли агент вирішує, що цей skill потрібен.
3. **`skill_view(name, file_path)`** — конкретний файл‑посилання всередині skill‑у. Завантажується лише за потреби.

Тобто skill‑и не вартують токенів, доки їх фактично не використано.

---

## Встановлення з Hub

Офіційні необов’язкові skill‑и постачаються з Hermes, але не активні за замовчуванням. Встанови їх явно:

```bash
# Install an official optional skill
hermes skills install official/research/arxiv

# Install from the hub in a chat session
/skills install official/creative/songwriting-and-ai-music

# Install a single-file SKILL.md directly from any HTTP(S) URL
hermes skills install https://sharethis.chat/SKILL.md
/skills install https://example.com/SKILL.md --name my-skill
```

Що відбувається:
1. Каталог skill‑у копіюється до `~/.hermes/skills/`.
2. Він з’являється у виводі `skills_list`.
3. Стає доступним як slash‑команда.

:::tip
Встановлені skill‑и набувають чинності в нових сесіях. Якщо потрібен доступ у поточній сесії, використай `/reset` для перезапуску або додай `--now`, щоб негайно скасувати кеш підказки (вартує більше токенів у наступному кроці).
:::

### Перевірка встановлення

```bash
# Check it's there
hermes skills list | grep arxiv

# Or in chat
/skills search arxiv
```

---

## Skill‑и, надані плагінами

Плагіни можуть пакувати власні skill‑и, використовуючи просторові імена (`plugin:skill`). Це запобігає конфліктам імен з вбудованими skill‑ами.

```bash
# Load a plugin skill by its qualified name
skill_view("superpowers:writing-plans")

# Built-in skill with the same base name is unaffected
skill_view("writing-plans")
```

Skill‑и плагіна **не** включені у системний підказник і не з’являються у `skills_list`. Вони opt‑in — завантажуй їх явно, коли знаєш, що плагін їх надає. Після завантаження агент показує банер зі списком sibling‑skill‑ів того ж плагіна.

Як пакувати skill‑и у власному плагіні, дивіться [Build a Hermes Plugin → Bundle skills](/guides/build-a-hermes-plugin#bundle-skills).

---

## Налаштування параметрів Skill‑а

Деякі skill‑и оголошують конфігурацію у своєму frontmatter:

```yaml
metadata:
  hermes:
    config:
      - key: tenor.api_key
        description: "Tenor API key for GIF search"
        prompt: "Enter your Tenor API key"
        url: "https://developers.google.com/tenor/guides/quickstart"
```

Коли skill з конфігом вперше завантажується, Hermes запитує у тебе значення. Вони зберігаються у `config.yaml` під `skills.config.*`.

Керуй конфігурацією skill‑а через CLI:

```bash
# Interactive config for a specific skill
hermes skills config gif-search

# View all skill config
hermes config get skills.config
```

---

## Створення власного Skill‑а

Skill‑и — це просто markdown‑файли з YAML‑frontmatter. Створити їх можна за кілька хвилин.

### 1. Створи каталог

```bash
mkdir -p ~/.hermes/skills/my-category/my-skill
```

### 2. Напиши SKILL.md

```markdown title="~/.hermes/skills/my-category/my-skill/SKILL.md"
---
name: my-skill
description: Brief description of what this skill does
version: 1.0.0
metadata:
  hermes:
    tags: [my-tag, automation]
    category: my-category
---

# My Skill

## When to Use
Use this skill when the user asks about [specific topic] or needs to [specific task].

## Procedure
1. First, check if [prerequisite] is available
2. Run `command --with-flags`
3. Parse the output and present results

## Pitfalls
- Common failure: [description]. Fix: [solution]
- Watch out for [edge case]

## Verification
Run `check-command` to confirm the result is correct.
```

### 3. Додай файли‑посилання (необов’язково)

Skill‑и можуть містити допоміжні файли, які агент завантажує за запитом:

```
my-skill/
├── SKILL.md                    # Main skill document
├── references/
│   ├── api-docs.md             # API reference the agent can consult
│   └── examples.md             # Example inputs/outputs
├── templates/
│   └── config.yaml             # Template files the agent can use
└── scripts/
    └── setup.sh                # Scripts the agent can execute
```

Посилайся на них у своєму SKILL.md:

```markdown
For API details, load the reference: `skill_view("my-skill", "references/api-docs.md")`
```

### 4. Протести

Запусти нову сесію і спробуй свій skill:

```bash
hermes chat -q "/my-skill help me with the thing"
```

Skill з’явиться автоматично — реєстрація не потрібна. Поклади його у `~/.hermes/skills/`, і він буде активний.

:::info
Агент також може створювати та оновлювати skill‑и сам за допомогою `skill_manage`. Після вирішення складної задачі Hermes може запропонувати зберегти підхід як skill для майбутнього.
:::

---

## Управління Skill‑ами за платформами

Контролюй, які skill‑и доступні на яких платформах:

```bash
hermes skills
```

Відкривається інтерактивний TUI, де можна вмикати або вимикати skill‑и для конкретних платформ (CLI, Telegram, Discord тощо). Корисно, коли треба, щоб певні skill‑и були доступні лише в певних контекстах — наприклад, не показувати development‑skill‑и у Telegram.

---

## Skill‑и vs Пам’ять

Обидва зберігаються між сесіями, але служать різним цілям:

| | Skill‑и | Пам’ять |
|---|---|---|
| **Що** | Процедурне знання — як щось робити | Фактичне знання — що таке |
| **Коли** | Завантажується за запитом, лише коли потрібне | Вбудовується у кожну сесію автоматично |
| **Розмір** | Може бути великим (сотні рядків) | Має бути компактним (лише ключові факти) |
| **Вартість** | 0 токенів, доки не завантажено | Невелика, але постійна токен‑вартість |
| **Приклади** | “Як розгорнути в Kubernetes” | “Користувач віддає перевагу темному режиму, живе в PST” |
| **Хто створює** | Ти, агент або встановлено з Hub | Агент, на основі розмов |

**Загальне правило:** Якщо це можна розмістити у довідковому документі, це skill. Якщо це нотатка на стікері, це пам’ять.

---

## Поради

**Тримай skill‑и сфокусованими.** Skill, який намагається охопити “весь DevOps”, буде занадто довгим і розпливчастим. Skill, який описує “розгорнути Python‑додаток у Fly.io”, достатньо конкретний і корисний.

**Дозволь агенту створювати skill‑и.** Після складного багатокрокового завдання Hermes часто пропонує зберегти підхід як skill. Скажи “так” — такі skill‑и, створені агентом, фіксують точний робочий процес разом із підводними каменями, які були виявлені.

**Використовуй категорії.** Організуй skill‑и у підкаталоги (`~/.hermes/skills/devops/`, `~/.hermes/skills/research/` тощо). Це робить список керованим і допомагає агенту швидше знаходити потрібні skill‑и.

**Оновлюй skill‑и, коли вони застарівають.** Якщо під час використання skill‑у виникають проблеми, повідом Hermes оновити skill новою інформацією. Необслуговувані skill‑и стають ризиком.

---

*Для повного довідника по skill‑ах — поля frontmatter, умовна активація, зовнішні каталоги та інше — дивіться [Skills System](/user-guide/features/skills).*