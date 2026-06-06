---
title: "Design Md — Автор/перевірка/експорт DESIGN Google"
sidebar_label: "Design Md"
description: "Автор/перевірити/експортувати Google's DESIGN"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Design Md

Автор/перевірка/експорт файлів специфікації токенів Google DESIGN.md.

## Метадані навички

| | |
|---|---|
| Джерело | Вбудовано (встановлюється за замовчуванням) |
| Шлях | `skills/creative/design-md` |
| Версія | `1.0.0` |
| Автор | Hermes Agent |
| Ліцензія | MIT |
| Платформи | linux, macos, windows |
| Теги | `design`, `design-system`, `tokens`, `ui`, `accessibility`, `wcag`, `tailwind`, `dtcg`, `google` |
| Пов’язані навички | [`popular-web-designs`](/docs/user-guide/skills/bundled/creative/creative-popular-web-designs), [`claude-design`](/docs/user-guide/skills/bundled/creative/creative-claude-design), [`excalidraw`](/docs/user-guide/skills/bundled/creative/creative-excalidraw), [`architecture-diagram`](/docs/user-guide/skills/bundled/creative/creative-architecture-diagram) |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# Навичка DESIGN.md

DESIGN.md — це відкритий специфікаційний документ Google (Apache‑2.0, `google-labs-code/design.md`) для опису візуальної ідентичності для кодуючих агентів. Один файл поєднує:

- **YAML front matter** — машинозчитувані токени дизайну (нормативні значення)
- **Markdown body** — зрозумілий людям зміст, організований у канонічні розділи

Токени дають точні значення. Проза пояснює агентам *чому* ці значення існують і як їх застосовувати. CLI (`npx @google/design.md`) перевіряє структуру + контраст WCAG, порівнює версії для регресій і експортує у Tailwind або W3C DTCG JSON.

## Коли використовувати цю навичку

- Користувач просить файл DESIGN.md, токени дизайну або специфікацію системи дизайну
- Користувач хоче послідовний UI/бренд у кількох проектах або інструментах
- Користувач вставляє існуючий DESIGN.md і просить перевірити, порівняти, експортувати або розширити його
- Користувач просить перенести гайд у формат, який можуть споживати агенти
- Користувач хоче перевірку контрасту / доступності WCAG у своїй кольоровій палітрі

Для чисто візуального натхнення або прикладів макетів використовуйте `popular-web-designs`. Для *процесу та смаку* при створенні одноразового HTML‑артефакту з нуля (прототип, презентація, посадкова сторінка, лабораторія компонентів) використовуйте `claude-design`. Ця навичка призначена саме для *офіційного файлу специфікації*.

## Будова файлу

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

## Типи токенів

| Тип | Формат | Приклад |
|------|--------|---------|
| Колір | `#` + hex (sRGB) | `"#1A1C1E"` |
| Розмір | число + одиниця (`px`, `em`, `rem`) | `48px`, `-0.02em` |
| Посилання на токен | `{path.to.token}` | `{colors.primary}` |
| Типографіка | об’єкт з `fontFamily`, `fontSize`, `fontWeight`, `lineHeight`, `letterSpacing`, `fontFeature`, `fontVariation` | див. вище |

Білий список властивостей компонентів: `backgroundColor`, `textColor`, `typography`, `rounded`, `padding`, `size`, `height`, `width`. Варіанти (hover, active, pressed) — це **окремі записи компонентів** з відповідними іменами ключів (`button-primary-hover`), а не вкладені.

## Канонічний порядок розділів

Розділи необов’язкові, але присутні повинні йти в цьому порядку. Дублікати заголовків призводять до відхилення файлу.

1. Огляд (alias: Brand & Style)
2. Кольори
3. Типографіка
4. Макет (alias: Layout & Spacing)
5. Елевація та Глибина (alias: Elevation)
6. Форми
7. Компоненти
8. Do's and Don'ts

Невідомі розділи зберігаються, помилок не викликають. Невідомі імена токенів приймаються, якщо тип значення коректний. Невідомі властивості компонентів викликають попередження.

## Робочий процес: створення нового DESIGN.md

1. **Запитай у користувача** (або визначи) тон бренду, акцентний колір і напрямок типографіки. Якщо він надав сайт, зображення або «вайб», переклади це у форму токену вище.
2. **Напиши `DESIGN.md`** у корені його проєкту за допомогою `write_file`. Завжди включай `name:` і `colors:`; інші розділи необов’язкові, але бажані.
3. **Використовуй посилання на токени** (`{colors.primary}`) у розділі `components:` замість повторного введення hex‑значень. Це підтримує єдине джерело палітри.
4. **Перевір файл** (див. нижче). Виправ будь‑які пошкоджені посилання або помилки WCAG перед поверненням.
5. **Якщо у користувача є існуючий проєкт**, також запиши експорти Tailwind або DTCG поруч із файлом (`tailwind.theme.json`, `tokens.json`).

## Робочий процес: lint / diff / export

CLI — `@google/design.md` (Node). Використовуй `npx` — глобальна інсталяція не потрібна.

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

Усі команди приймають `-` для stdin. `lint` повертає код виходу 1 при помилках. Використовуй прапорець `--format json` і обробляй вивід, якщо треба структурувати звіт.

### Довідка правил lint (що охоплює 7 правил)

- `broken-ref` (error) — `{colors.missing}` вказує на неіснуючий токен
- `duplicate-section` (error) — однакова `## Heading` зустрічається двічі
- `invalid-color`, `invalid-dimension`, `invalid-typography` (error)
- `wcag-contrast` (warning/info) — співвідношення `textColor` до `backgroundColor` проти WCAG AA (4.5:1) та AAA (7:1)
- `unknown-component-property` (warning) — поза білим списком вище

Коли користувач турбується про доступність, обов’язково підкресли це у підсумку — результати WCAG є головною причиною використання CLI.

## Підводні камені

- **Не вкладайте варіанти компонентів.** `button-primary.hover` — неправильно; `button-primary-hover` як окремий ключ — правильно.
- **Hex‑кольори мають бути рядками в лапках.** Інакше YAML «запнеться» на `#` або обрізатиме значення типу `#1A1C1E`.
- **Від’ємні розміри теж потребують лапок.** `letterSpacing: -0.02em` парситься як YAML flow — пишіть `letterSpacing: "-0.02em"`.
- **Порядок розділів обов’язковий.** Якщо користувач надає текст у випадковому порядку, перестав його відповідно до канонічного списку перед збереженням.
- **`version: alpha` — поточна версія специфікації** (станом на квітень 2026). Специфікація позначена як alpha — слідкуй за можливими змінами.
- **Посилання на токени розв’язуються за допомогою крапкових шляхів.** `{colors.primary}` працює; `{primary}` — ні.

## Джерело правди специфікації

- Репозиторій: https://github.com/google-labs-code/design.md (Apache‑2.0)
- CLI: `@google/design.md` в npm
- Ліцензія згенерованих файлів DESIGN.md: залежить від проєкту користувача; сама специфікація — Apache‑2.0.