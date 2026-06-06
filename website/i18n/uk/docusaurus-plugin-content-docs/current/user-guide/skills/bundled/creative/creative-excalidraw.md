---
title: "Excalidraw — рукописні діаграми Excalidraw у форматі JSON (arch, flow, seq)"
sidebar_label: "Excalidraw"
description: "Ручні Excalidraw JSON діаграми (arch, flow, seq)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Excalidraw

Ручні діаграми Excalidraw у форматі JSON (архітектура, flow, seq).

## Метадані навички

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/creative/excalidraw` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Excalidraw`, `Diagrams`, `Flowcharts`, `Architecture`, `Visualization`, `JSON` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Excalidraw Diagram Skill

Створюй діаграми, записуючи стандартний Excalidraw‑element JSON і зберігаючи їх у файли `.excalidraw`. Ці файли можна перетягнути на [excalidraw.com](https://excalidraw.com) для перегляду та редагування. Ніяких облікових записів, API‑ключів, бібліотек рендерингу — лише JSON.

## When to use

Генеруй файли `.excalidraw` для архітектурних діаграм, flowchart‑ів, діаграм послідовностей, мап концепцій тощо. Файли можна відкривати на excalidraw.com або завантажувати для отримання поширюваних посилань.

## Workflow

1. **Load this skill** (you already did)
2. **Write the elements JSON** — масив об’єктів Excalidraw element
3. **Save the file** за допомогою `write_file`, створюючи файл `.excalidraw`
4. **Optionally upload** для отримання поширюваного посилання, використовуючи `scripts/upload.py` у терміналі

### Saving a Diagram

Обгорни масив елементів у стандартний конверт `.excalidraw` і збережи за допомогою `write_file`:

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "hermes-agent",
  "elements": [ ...your elements array here... ],
  "appState": {
    "viewBackgroundColor": "#ffffff"
  }
}
```

Збережи у будь‑якому шляху, напр. `~/diagrams/my_diagram.excalidraw`.

### Uploading for a Shareable Link

Запусти скрипт завантаження (розташований у каталозі `scripts/` цієї навички) у терміналі:

```bash
python skills/diagramming/excalidraw/scripts/upload.py ~/diagrams/my_diagram.excalidraw
```

Скрипт завантажує файл на excalidraw.com (без потреби в обліковому записі) і виводить поширюване URL. Потрібен pip‑пакет `cryptography` (`pip install cryptography`).

---

## Element Format Reference

### Required Fields (all elements)
`type`, `id` (унікальний рядок), `x`, `y`, `width`, `height`

### Defaults (skip these — вони застосовуються автоматично)

- `strokeColor`: `"#1e1e1e"`
- `backgroundColor`: `"transparent"`
- `fillStyle`: `"solid"`
- `strokeWidth`: `2`
- `roughness`: `1` (hand‑drawn look)
- `opacity`: `100`

Тло канви — біле.

### Element Types

**Rectangle**:
```json
{ "type": "rectangle", "id": "r1", "x": 100, "y": 100, "width": 200, "height": 100 }
```
- `roundness: { "type": 3 }` — для заокруглених кутів
- `backgroundColor: "#a5d8ff"`, `fillStyle: "solid"` — для заповнених

**Ellipse**:
```json
{ "type": "ellipse", "id": "e1", "x": 100, "y": 100, "width": 150, "height": 150 }
```

**Diamond**:
```json
{ "type": "diamond", "id": "d1", "x": 100, "y": 100, "width": 150, "height": 150 }
```

**Labeled shape (container binding)** — створи текстовий елемент, прив’язаний до форми:

> **WARNING:** Не використовуйте `"label": { "text": "..." }` у формах. Це НЕ валідна властивість Excalidraw і буде проігнорована, в результаті ви отримаєте порожні форми. Потрібно застосовувати підхід контейнерного зв’язку, описаний нижче.

Форма повинна містити `boundElements` зі списком тексту, а текст — `containerId`, що вказує назад:

```json
{ "type": "rectangle", "id": "r1", "x": 100, "y": 100, "width": 200, "height": 80,
  "roundness": { "type": 3 }, "backgroundColor": "#a5d8ff", "fillStyle": "solid",
  "boundElements": [{ "id": "t_r1", "type": "text" }] },
{ "type": "text", "id": "t_r1", "x": 105, "y": 110, "width": 190, "height": 25,
  "text": "Hello", "fontSize": 20, "fontFamily": 1, "strokeColor": "#1e1e1e",
  "textAlign": "center", "verticalAlign": "middle",
  "containerId": "r1", "originalText": "Hello", "autoResize": true }
```
- Працює з rectangle, ellipse, diamond
- Текст автоматично центрований Excalidraw, коли встановлено `containerId`
- Параметри `x`/`y`/`width`/`height` у тексту приблизні — Excalidraw перераховує їх при завантаженні
- `originalText` має збігатися з `text`
- Завжди вказуйте `fontFamily: 1` (шрифт Virgil/hand‑drawn)

**Labeled arrow** — те ж саме, контейнерний зв’язок:

```json
{ "type": "arrow", "id": "a1", "x": 300, "y": 150, "width": 200, "height": 0,
  "points": [[0,0],[200,0]], "endArrowhead": "arrow",
  "boundElements": [{ "id": "t_a1", "type": "text" }] },
{ "type": "text", "id": "t_a1", "x": 370, "y": 130, "width": 60, "height": 20,
  "text": "connects", "fontSize": 16, "fontFamily": 1, "strokeColor": "#1e1e1e",
  "textAlign": "center", "verticalAlign": "middle",
  "containerId": "a1", "originalText": "connects", "autoResize": true }
```

**Standalone text** (лише заголовки та анотації, без контейнера):

```json
{ "type": "text", "id": "t1", "x": 150, "y": 138, "text": "Hello", "fontSize": 20,
  "fontFamily": 1, "strokeColor": "#1e1e1e", "originalText": "Hello", "autoResize": true }
```
- `x` — ліва межа. Щоб центровано розташувати елемент у позиції `cx`: `x = cx - (text.length * fontSize * 0.5) / 2`
- Не покладайтеся на `textAlign` або `width` для позиціонування

**Arrow**:

```json
{ "type": "arrow", "id": "a1", "x": 300, "y": 150, "width": 200, "height": 0,
  "points": [[0,0],[200,0]], "endArrowhead": "arrow" }
```
- `points`: `[dx, dy]` — зміщення від `x`, `y` елемента
- `endArrowhead`: `null` | `"arrow"` | `"bar"` | `"dot"` | `"triangle"`
- `strokeStyle`: `"solid"` (за замовчуванням) | `"dashed"` | `"dotted"`

### Arrow Bindings (connect arrows to shapes)

```json
{
  "type": "arrow", "id": "a1", "x": 300, "y": 150, "width": 150, "height": 0,
  "points": [[0,0],[150,0]], "endArrowhead": "arrow",
  "startBinding": { "elementId": "r1", "fixedPoint": [1, 0.5] },
  "endBinding": { "elementId": "r2", "fixedPoint": [0, 0.5] }
}
```

`fixedPoint` координати: `top=[0.5,0]`, `bottom=[0.5,1]`, `left=[0,0.5]`, `right=[1,0.5]`

### Drawing Order (z-order)

- Порядок у масиві = z‑order (перший — ззаду, останній — спереду)
- Емісіюй поступово: background zones → shape → її прив’язаний текст → її стрілки → наступна shape
- Погано: спочатку всі rectangles, потім всі texts, потім всі arrows
- Добре: bg_zone → shape1 → text_for_shape1 → arrow1 → arrow_label_text → shape2 → text_for_shape2 → …
- Прив’язаний текст розташовуй одразу після його контейнера

### Sizing Guidelines

**Font sizes**:
- Мінімальний `fontSize`: **16** для основного тексту, міток, описів
- Мінімальний `fontSize`: **20** для заголовків та титулів
- Мінімальний `fontSize`: **14** для другорядних анотацій (рідко)
- НІКОЛИ не використовуйте `fontSize` менше 14

**Element sizes**:
- Мінімальний розмір форми: 120 × 60 px для підписаних rectangles/ellipses
- Мінімальний проміжок між елементами — 20‑30 px
- Краще мати менше, але більші елементи, ніж багато дрібних

### Color Palette

Див. `references/colors.md` для повних таблиць кольорів. Швидка довідка:

| Use | Fill Color | Hex |
|-----|-----------|-----|
| Primary / Input | Light Blue | `#a5d8ff` |
| Success / Output | Light Green | `#b2f2bb` |
| Warning / External | Light Orange | `#ffd8a8` |
| Processing / Special | Light Purple | `#d0bfff` |
| Error / Critical | Light Red | `#ffc9c9` |
| Notes / Decisions | Light Yellow | `#fff3bf` |
| Storage / Data | Light Teal | `#c3fae8` |

### Tips

- Використовуй палітру кольорів послідовно у всій діаграмі
- **Контраст тексту КРИТИЧНИЙ** — ніколи не став світло‑сірий текст на білому тлі. Мінімальний колір тексту на білому: `#757575`
- Не використовуйте emoji у тексті — вони не відображаються шрифтом Excalidraw
- Для діаграм у темному режимі дивіться `references/dark-mode.md`
- Для більших прикладів дивіться `references/examples.md`