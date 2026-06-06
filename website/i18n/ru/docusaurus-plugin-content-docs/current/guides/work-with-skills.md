---
sidebar_position: 12
title: "Работа со Skills"
description: "Найти, установить, использовать и создавать skills — знания по запросу, которые обучают Hermes новым рабочим процессам"
---

# Работа со skill’ами

Skill’ы — это документы знаний по запросу, которые обучают Hermes выполнять конкретные задачи — от генерации ASCII‑искусства до управления Pull‑Request’ами на GitHub. Это руководство проведёт тебя через их ежедневное использование.

Для полного технического справочника смотри [Skills System](/user-guide/features/skills).

---

## Поиск skill’ов

Каждая установка Hermes поставляется с набором встроенных skill’ов. Посмотри, что доступно:

```bash
# In any chat session:
/skills

# Or from the CLI:
hermes skills list
```

Это показывает компактный список с названиями и описаниями:

```
ascii-art         Generate ASCII art using pyfiglet, cowsay, boxes...
arxiv             Search and retrieve academic papers from arXiv...
github-pr-workflow Full PR lifecycle — create branches, commit...
plan              Plan mode — inspect context, write a markdown...
excalidraw        Create hand-drawn style diagrams using Excalidraw...
```

### Поиск skill’а

```bash
# Search by keyword
/skills search docker
/skills search music
```

### Центр skill’ов

Официальные необязательные skill’ы (более тяжёлые или нишевые, не активные по умолчанию) доступны через Центр:

```bash
# Browse official optional skills
/skills browse

# Search the hub
/skills search blockchain
```

---

## Использование skill’а

Каждый установленный skill автоматически становится slash‑командой. Просто введи его название:

```bash
# Load a skill and give it a task
/ascii-art Make a banner that says "HELLO WORLD"
/plan Design a REST API for a todo app
/github-pr-workflow Create a PR for the auth refactor

# Just the skill name (no task) loads it and lets you describe what you need
/excalidraw
```

Ты также можешь вызвать skill через обычный диалог — попроси Hermes использовать конкретный skill, и он загрузит его через инструмент `skill_view`.

### Прогрессивное раскрытие

Skill’ы используют токен‑экономичный шаблон загрузки. Агент не загружает всё сразу:

1. **`skills_list()`** — компактный список всех skill’ов (~3 k токенов). Загружается при старте сессии.
2. **`skill_view(name)`** — полное содержимое `SKILL.md` для одного skill’а. Загружается, когда агент решает, что нужен этот skill.
3. **`skill_view(name, file_path)`** — конкретный файл‑ссылка внутри skill’а. Загружается только при необходимости.

Это значит, что skill’ы не тратят токены, пока их действительно не используют.

---

## Установка из Центра

Официальные необязательные skill’ы поставляются с Hermes, но не активны по умолчанию. Установи их явно:

```bash
# Install an official optional skill
hermes skills install official/research/arxiv

# Install from the hub in a chat session
/skills install official/creative/songwriting-and-ai-music

# Install a single-file SKILL.md directly from any HTTP(S) URL
hermes skills install https://sharethis.chat/SKILL.md
/skills install https://example.com/SKILL.md --name my-skill
```

Что происходит:
1. Каталог skill’а копируется в `~/.hermes/skills/`.
2. Он появляется в выводе `skills_list`.
3. Он становится доступным как slash‑команда.

:::tip
Установленные skill’ы начинают работать в новых сессиях. Если нужно, чтобы они были доступны в текущей сессии, используй `/reset` для перезапуска либо добавь `--now`, чтобы сразу сбросить кэш подсказки (это стоит больше токенов на следующем ходу).
:::

### Проверка установки

```bash
# Check it's there
hermes skills list | grep arxiv

# Or in chat
/skills search arxiv
```

---

## Skill’ы, предоставляемые плагинами

Плагины могут включать свои собственные skill’ы, используя имена с пространством имён (`plugin:skill`). Это предотвращает конфликты имён с встроенными skill’ами.

```bash
# Load a plugin skill by its qualified name
skill_view("superpowers:writing-plans")

# Built-in skill with the same base name is unaffected
skill_view("writing-plans")
```

Skill’ы плагина **не** перечисляются в системной подсказке и не появляются в `skills_list`. Они опциональны — загружай их явно, когда знаешь, что плагин их предоставляет. При загрузке агент показывает баннер со списком соседних skill’ов того же плагина.

Как упаковать skill’ы в собственном плагине, смотри [Build a Hermes Plugin → Bundle skills](/guides/build-a-hermes-plugin#bundle-skills).

---

## Настройка параметров skill’а

Некоторые skill’ы объявляют конфигурацию, необходимую им в frontmatter:

```yaml
metadata:
  hermes:
    config:
      - key: tenor.api_key
        description: "Tenor API key for GIF search"
        prompt: "Enter your Tenor API key"
        url: "https://developers.google.com/tenor/guides/quickstart"
```

Когда skill с конфигурацией загружается впервые, Hermes запрашивает у тебя значения. Они сохраняются в `config.yaml` под `skills.config.*`.

Управляй конфигурацией skill’ов через CLI:

```bash
# Interactive config for a specific skill
hermes skills config gif-search

# View all skill config
hermes config get skills.config
```

---

## Создание собственного skill’а

Skill’ы — это просто markdown‑файлы с YAML‑frontmatter. Создать их можно менее чем за пять минут.

### 1. Создай каталог

```bash
mkdir -p ~/.hermes/skills/my-category/my-skill
```

### 2. Напиши `SKILL.md`

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

### 3. Добавь вспомогательные файлы (по желанию)

Skill’ы могут включать поддерживающие файлы, которые агент загружает по запросу:

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

Ссылайся на них в своём `SKILL.md`:

```markdown
For API details, load the reference: `skill_view("my-skill", "references/api-docs.md")`
```

### 4. Протестируй

Запусти новую сессию и попробуй свой skill:

```bash
hermes chat -q "/my-skill help me with the thing"
```

Skill появляется автоматически — регистрация не требуется. Помести его в `~/.hermes/skills/`, и он будет активен.

:::info
Агент также может создавать и обновлять skill’ы сам, используя `skill_manage`. После решения сложной задачи Hermes может предложить сохранить подход как skill для будущих использований.
:::

---

## Управление skill’ами по платформам

Контролируй, какие skill’ы доступны на каких платформах:

```bash
hermes skills
```

Откроется интерактивный TUI, где можно включать или отключать skill’ы для каждой платформы (CLI, Telegram, Discord и т.д.). Это полезно, когда нужно, чтобы некоторые skill’ы были доступны только в определённых контекстах — например, держать навыки разработки вне Telegram.

---

## Skill’ы vs память

Оба хранятся между сессиями, но служат разным целям:

| | Skill’ы | Память |
|---|---|---|
| **Что** | Процедурные знания — как что‑то делать | Фактические знания — что такое |
| **Когда** | Загружаются по запросу, только при необходимости | Встраиваются в каждую сессию автоматически |
| **Размер** | Может быть большим (сотни строк) | Должен быть компактным (только ключевые факты) |
| **Стоимость** | Ноль токенов, пока не загружен | Небольшая, но постоянная токенная стоимость |
| **Примеры** | «Как развернуть приложение в Kubernetes» | «Пользователь предпочитает тёмный режим, живёт в PST» |
| **Кто создаёт** | Ты, агент или установленный из Центра | Агент, на основе диалогов |

**Практический совет:** Если бы ты поместил это в справочный документ, это skill. Если бы записал на стикер — это память.

---

## Советы

**Делай skill’ы узконаправленными.** Skill, пытающийся охватить «весь DevOps», будет слишком длинным и расплывчатым. Skill, описывающий «развёртывание Python‑приложения в Fly.io», достаточно конкретен и действительно полезен.

**Позволь агенту создавать skill’ы.** После сложной многошаговой задачи Hermes часто предлагает сохранить подход как skill. Скажи «да» — эти skill’ы, созданные агентом, фиксируют точный рабочий процесс вместе с подводными камнями, которые были обнаружены.

**Используй категории.** Организуй skill’ы в подкаталогах (`~/.hermes/skills/devops/`, `~/.hermes/skills/research/` и т.д.). Это делает список управляемым и помогает агенту быстрее находить нужные skill’ы.

**Обновляй устаревшие skill’ы.** Если ты используешь skill и сталкиваешься с проблемами, не покрытыми им, попроси Hermes обновить skill с учётом полученного опыта. Не поддерживаемые skill’ы становятся риском.

---

*Для полного справочника по skill’ам — поля frontmatter, условная активация, внешние каталоги и прочее — смотри [Skills System](/user-guide/features/skills).*