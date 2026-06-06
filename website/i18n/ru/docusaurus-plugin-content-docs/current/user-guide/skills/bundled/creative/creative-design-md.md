---
title: "Design Md — Автор/валидация/экспорт DESIGN от Google"
sidebar_label: "Design Md"
description: "Автор/проверить/экспортировать Google's DESIGN"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Design Md

Авторство/валидация/экспорт файлов спецификации токенов DESIGN.md от Google.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/creative/design-md` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `design`, `design-system`, `tokens`, `ui`, `accessibility`, `wcag`, `tailwind`, `dtcg`, `google` |
| Related skills | [`popular-web-designs`](/docs/user-guide/skills/bundled/creative/creative-popular-web-designs), [`claude-design`](/docs/user-guide/skills/bundled/creative/creative-claude-design), [`excalidraw`](/docs/user-guide/skills/bundled/creative/creative-excalidraw), [`architecture-diagram`](/docs/user-guide/skills/bundled/creative/creative-architecture-diagram) |

## Reference: full SKILL.md

:::info
Ниже представлено полное определение скилла, которое Hermes загружает при его активации. Это то, что агент видит в виде инструкций, когда скилл включён.
:::

# DESIGN.md Skill

DESIGN.md — открытая спецификация Google (Apache‑2.0, `google-labs-code/design.md`) для описания визуальной идентичности агентам‑кодерам. Один файл объединяет:

- **YAML front matter** — машинно‑читаемые токены дизайна (нормативные значения)
- **Markdown body** — человекочитаемое обоснование, разбитое на канонические разделы

Токены задают точные значения. Проза объясняет агентам *почему* эти значения нужны и как их применять. CLI (`npx @google/design.md`) проверяет структуру + контрастность по WCAG, сравнивает версии для обнаружения регрессий и экспортирует в Tailwind или W3C DTCG JSON.

## When to use this skill

- Пользователь запрашивает файл DESIGN.md, токены дизайна или спецификацию дизайн‑системы
- Пользователь хочет единый UI/бренд во множестве проектов или инструментов
- Пользователь вставил существующий DESIGN.md и просит проверить, сравнить, экспортировать или расширить его
- Пользователь хочет перенести гайдлайн стилей в формат, пригодный для агентов
- Пользователь нуждается в проверке контрастности / доступности WCAG своей цветовой палитры

Для чисто визуального вдохновения или примеров разметки используй `popular-web-designs`. Для *процесса и вкуса* при создании одноразового HTML‑артефакта с нуля (прототип, презентация, лендинг, лаборатория компонентов) используй `claude-design`. Этот скилл предназначен для работы с *формальным файлом‑спецификацией*.

## File anatomy

```md
---
version: alpha
name: Heritage
description: Architectural minimalism meets journalistic gravitas.
colors:
  primary: "#1A1C1E"
  secondary: "#6C7278"
  tertiary: "#B8422E"
  neutral: "#F7F5F2"
typography:
  h1:
    fontFamily: Public Sans
    fontSize: 3rem
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  body-md:
    fontFamily: Public Sans
    fontSize: 1rem
rounded:
  sm: 4px
  md: 8px
  lg: 16px
spacing:
  sm: 8px
  md: 16px
  lg: 24px
components:
  button-primary:
    backgroundColor: "{colors.tertiary}"
    textColor: "#FFFFFF"
    rounded: "{rounded.sm}"
    padding: 12px
  button-primary-hover:
    backgroundColor: "{colors.primary}"
---

## Overview

Architectural Minimalism meets Journalistic Gravitas...

## Colors

- **Primary (#1A1C1E):** Deep ink for headlines and core text.
- **Tertiary (#B8422E):** "Boston Clay" — the sole driver for interaction.

## Typography

Public Sans for everything except small all-caps labels...

## Components

`button-primary` is the only high-emphasis action on a page...
```

## Token types

| Type | Format | Example |
|------|--------|---------|
| Color | `#` + hex (sRGB) | `"#1A1C1E"` |
| Dimension | number + unit (`px`, `em`, `rem`) | `48px`, `-0.02em` |
| Token reference | `{path.to.token}` | `{colors.primary}` |
| Typography | объект с полями `fontFamily`, `fontSize`, `fontWeight`, `lineHeight`, `letterSpacing`, `fontFeature`, `fontVariation` | см. выше |

Белый список свойств компонентов: `backgroundColor`, `textColor`, `typography`, `rounded`, `padding`, `size`, `height`, `width`. Варианты (hover, active, pressed) задаются **отдельными записями компонентов** с соответствующими именами ключей (`button-primary-hover`), а не вложенными.

## Canonical section order

Разделы опциональны, но присутствующие ДОЛЖНЫ идти в указанном порядке. Дублирующиеся заголовки делают файл недействительным.

1. Overview (alias: Brand & Style)
2. Colors
3. Typography
4. Layout (alias: Layout & Spacing)
5. Elevation & Depth (alias: Elevation)
6. Shapes
7. Components
8. Do's and Don'ts

Неизвестные разделы сохраняются, ошибки не вызывают. Неизвестные имена токенов принимаются, если тип значения корректен. Неизвестные свойства компонентов вызывают предупреждение.

## Workflow: authoring a new DESIGN.md

1. **Спроси пользователя** (или выведи) тон бренда, основной цвет и направление типографики. Если он предоставил сайт, изображение или «вайб», преобразуй их в токены согласно схеме выше.
2. **Создай `DESIGN.md`** в корне проекта с помощью `write_file`. Обязательно укажи `name:` и `colors:`; остальные разделы опциональны, но желательны.
3. **Используй ссылки на токены** (`{colors.primary}`) в разделе `components:` вместо повторного указания HEX‑значений. Это обеспечивает единственный источник правды для палитры.
4. **Проверь файл** (см. ниже). Исправь все битые ссылки и нарушения WCAG перед возвратом результата.
5. **Если у пользователя уже есть проект**, также создай экспорты для Tailwind или DTCG рядом с файлом (`tailwind.theme.json`, `tokens.json`).

## Workflow: lint / diff / export

CLI — `@google/design.md` (Node). Запускай через `npx` — глобальная установка не требуется.

```bash
# Validate structure + token references + WCAG contrast
npx -y @google/design.md lint DESIGN.md

# Compare two versions, fail on regression (exit 1 = regression)
npx -y @google/design.md diff DESIGN.md DESIGN-v2.md

# Export to Tailwind theme JSON
npx -y @google/design.md export --format tailwind DESIGN.md > tailwind.theme.json

# Export to W3C DTCG (Design Tokens Format Module) JSON
npx -y @google/design.md export --format dtcg DESIGN.md > tokens.json

# Print the spec itself — useful when injecting into an agent prompt
npx -y @google/design.md spec --rules-only --format json
```

Все команды принимают `-` для чтения из stdin. `lint` возвращает код 1 при ошибках. Используй флаг `--format json` и парси вывод, если нужно структурировано представить результаты.

### Lint rule reference (what the 7 rules catch)

- `broken-ref` (error) — `{colors.missing}` ссылается на несуществующий токен
- `duplicate-section` (error) — один и тот же `## Heading` встречается дважды
- `invalid-color`, `invalid-dimension`, `invalid-typography` (error)
- `wcag-contrast` (warning/info) — соотношение `textColor` и `backgroundColor` проверяется по WCAG AA (4.5:1) и AAA (7:1)
- `unknown-component-property` (warning) — свойство не входит в белый список выше

Когда пользователь интересуется доступностью, явно укажи это в своём резюме — выводы WCAG часто являются главным поводом использовать CLI.

## Pitfalls

- **Не вкладывай варианты компонентов.** `button-primary.hover` — неверно; правильный вариант — отдельный ключ `button-primary-hover`.
- **HEX‑цвета должны быть строками в кавычках.** Иначе YAML «падает» на `#` или обрезает значение, например `#1A1C1E`.
- **Отрицательные размеры тоже требуют кавычек.** `letterSpacing: -0.02em` парсится как YAML‑поток — запиши `letterSpacing: "-0.02em"`.
- **Порядок разделов обязателен.** Если пользователь предоставил текст в произвольном порядке, переставь его согласно каноническому списку перед сохранением.
- **`version: alpha` — текущая версия спецификации** (по состоянию на апрель 2026). Спецификация помечена как альфа — следи за возможными ломающими изменениями.
- **Ссылки на токены разрешаются по точечной цепочке.** `{colors.primary}` работает; `{primary}` — нет.

## Spec source of truth

- Репозиторий: https://github.com/google-labs-code/design.md (Apache‑2.0)
- CLI: `@google/design.md` в npm
- Лицензия сгенерированных файлов DESIGN.md: та, что использует проект пользователя; сама спецификация лицензирована под Apache‑2.0.