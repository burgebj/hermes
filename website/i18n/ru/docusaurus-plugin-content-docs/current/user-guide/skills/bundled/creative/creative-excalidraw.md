---
title: "Excalidraw — Рисованные от руки JSON‑диаграммы Excalidraw (arch, flow, seq)"
sidebar_label: "Excalidraw"
description: "Рисованные от руки Excalidraw JSON‑диаграммы (arch, flow, seq)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Excalidraw

Рисованные от руки JSON‑диаграммы Excalidraw (архитектура, поток, последовательность).

## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/creative/excalidraw` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Excalidraw`, `Diagrams`, `Flowcharts`, `Architecture`, `Visualization`, `JSON` |

## Ссылка: полный SKILL.md

:::info
Ниже представлено полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции, когда навык включён.
:::

# Навык диаграмм Excalidraw

Создавай диаграммы, записывая стандартный JSON элементов Excalidraw и сохраняя их как файлы `.excalidraw`. Эти файлы можно перетаскивать на [excalidraw.com](https://excalidraw.com) для просмотра и редактирования. Без учётных записей, без API‑ключей, без библиотек рендеринга — только JSON.

## Когда использовать

Генерируй файлы `.excalidraw` для архитектурных диаграмм, блок‑схем, диаграмм последовательностей, концептуальных карт и прочего. Файлы можно открыть на excalidraw.com или загрузить для получения ссылки.

## Рабочий процесс

1. **Загрузи этот навык** (ты уже сделал)
2. **Напиши JSON элементов** — массив объектов элементов Excalidraw
3. **Сохрани файл** с помощью `write_file`, создав файл `.excalidraw`
4. **При желании загрузить** для получения ссылки, используя `scripts/upload.py` через `terminal`

### Сохранение диаграммы

Обёрни массив элементов в стандартную оболочку `.excalidraw` и сохрани через `write_file`:

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

Сохрани в любой путь, например `~/diagrams/my_diagram.excalidraw`.

### Загрузка для получения ссылки

Запусти скрипт загрузки (находится в каталоге `scripts/` этого навыка) через терминал:

```bash
python skills/diagramming/excalidraw/scripts/upload.py ~/diagrams/my_diagram.excalidraw
```

Это загружает на excalidraw.com (учётная запись не требуется) и выводит общедоступный URL. Требуется пакет `cryptography` (`pip install cryptography`).

---

## Справочник формата элементов

### Обязательные поля (для всех элементов)
`type`, `id` (уникальная строка), `x`, `y`, `width`, `height`

### Значения по умолчанию (можно опускать — применяются автоматически)
- `strokeColor`: `"#1e1e1e"`
- `backgroundColor`: `"transparent"`
- `fillStyle`: `"solid"`
- `strokeWidth`: `2`
- `roughness`: `1` (вид от руки)
- `opacity`: `100`

Фон холста — белый.

### Типы элементов

**Прямоугольник**:
```json
{ "type": "rectangle", "id": "r1", "x": 100, "y": 100, "width": 200, "height": 100 }
```
- `roundness: { "type": 3 }` — скруглённые углы
- `backgroundColor: "#a5d8ff"`, `fillStyle: "solid"` — заполнение

**Эллипс**:
```json
{ "type": "ellipse", "id": "e1", "x": 100, "y": 100, "width": 150, "height": 150 }
```

**Ромб**:
```json
{ "type": "diamond", "id": "d1", "x": 100, "y": 100, "width": 150, "height": 150 }
```

**Помечённая фигура (привязка контейнера)** — создай текстовый элемент, привязанный к фигуре:

> **WARNING:** Не используй `"label": { "text": "..." }` у фигур. Это НЕвалидное свойство Excalidraw и будет тихо проигнорировано, в результате получатся пустые фигуры. Ты должен использовать подход привязки контейнера, описанный ниже.

Фигуре нужен `boundElements` со списком текста, а тексту — `containerId`, указывающий обратно:
```json
{ "type": "rectangle", "id": "r1", "x": 100, "y": 100, "width": 200, "height": 80,
  "roundness": { "type": 3 }, "backgroundColor": "#a5d8ff", "fillStyle": "solid",
  "boundElements": [{ "id": "t_r1", "type": "text" }] },
{ "type": "text", "id": "t_r1", "x": 105, "y": 110, "width": 190, "height": 25,
  "text": "Hello", "fontSize": 20, "fontFamily": 1, "strokeColor": "#1e1e1e",
  "textAlign": "center", "verticalAlign": "middle",
  "containerId": "r1", "originalText": "Hello", "autoResize": true }
```
- Работает с прямоугольником, эллипсом, ромбом
- Текст автоматически центрируется Excalidraw, когда установлен `containerId`
- `x`/`y`/`width`/`height` текста приблизительные — Excalidraw пересчитывает их при загрузке
- `originalText` должен совпадать с `text`
- Всегда указывай `fontFamily: 1` (шрифт Virgil/hand‑drawn)

**Помечённая стрелка** — тот же подход привязки контейнера:
```json
{ "type": "arrow", "id": "a1", "x": 300, "y": 150, "width": 200, "height": 0,
  "points": [[0,0],[200,0]], "endArrowhead": "arrow",
  "boundElements": [{ "id": "t_a1", "type": "text" }] },
{ "type": "text", "id": "t_a1", "x": 370, "y": 130, "width": 60, "height": 20,
  "text": "connects", "fontSize": 16, "fontFamily": 1, "strokeColor": "#1e1e1e",
  "textAlign": "center", "verticalAlign": "middle",
  "containerId": "a1", "originalText": "connects", "autoResize": true }
```

**Отдельный текст** (только заголовки и аннотации — без контейнера):
```json
{ "type": "text", "id": "t1", "x": 150, "y": 138, "text": "Hello", "fontSize": 20,
  "fontFamily": 1, "strokeColor": "#1e1e1e", "originalText": "Hello", "autoResize": true }
```
- `x` — левая граница. Чтобы центрировать по позиции `cx`: `x = cx - (text.length * fontSize * 0.5) / 2`
- Не полагайся на `textAlign` или `width` для позиционирования

**Стрелка**:
```json
{ "type": "arrow", "id": "a1", "x": 300, "y": 150, "width": 200, "height": 0,
  "points": [[0,0],[200,0]], "endArrowhead": "arrow" }
```
- `points`: `[dx, dy]` — смещения от `x`, `y` элемента
- `endArrowhead`: `null` | `"arrow"` | `"bar"` | `"dot"` | `"triangle"`
- `strokeStyle`: `"solid"` (по умолчанию) | `"dashed"` | `"dotted"`

### Привязки стрелок (соединение стрелок с фигурами)

```json
{
  "type": "arrow", "id": "a1", "x": 300, "y": 150, "width": 150, "height": 0,
  "points": [[0,0],[150,0]], "endArrowhead": "arrow",
  "startBinding": { "elementId": "r1", "fixedPoint": [1, 0.5] },
  "endBinding": { "elementId": "r2", "fixedPoint": [0, 0.5] }
}
```

Координаты `fixedPoint`: `top=[0.5,0]`, `bottom=[0.5,1]`, `left=[0,0.5]`, `right=[1,0.5]`

### Порядок отрисовки (z‑order)
- Порядок в массиве = z‑order (первый — задний, последний — передний)
- Выводи последовательно: фоновые зоны → фигура → её привязанный текст → её стрелки → следующая фигура
- **ПЛОХО:** все прямоугольники, затем все тексты, затем все стрелки
- **ХОРОШО:** bg_zone → shape1 → text_for_shape1 → arrow1 → arrow_label_text → shape2 → text_for_shape2 → …
- Всегда размещай привязанный текстовый элемент сразу после его контейнерной фигуры

### Руководство по размерам

**Размеры шрифта:**
- Минимальный `fontSize`: **16** для основного текста, меток, описаний
- Минимальный `fontSize`: **20** для заголовков и титулов
- Минимальный `fontSize`: **14** для вторичных аннотаций (использовать экономно)
- НИКОГДА не используй `fontSize` ниже 14

**Размеры элементов:**
- Минимальный размер фигуры: 120 × 60 px для помечённых прямоугольников/эллипсов
- Оставляй промежутки минимум 20–30 px между элементами
- Предпочитай меньше, но крупнее элементов, а не множество мелких

### Цветовая палитра

Смотри `references/colors.md` для полной таблицы цветов. Быстрая справка:

| Применение | Цвет заливки | Hex |
|-----|-----------|-----|
| Primary / Input | Light Blue | `#a5d8ff` |
| Success / Output | Light Green | `#b2f2bb` |
| Warning / External | Light Orange | `#ffd8a8` |
| Processing / Special | Light Purple | `#d0bfff` |
| Error / Critical | Light Red | `#ffc9c9` |
| Notes / Decisions | Light Yellow | `#fff3bf` |
| Storage / Data | Light Teal | `#c3fae8` |

### Советы
- Используй цветовую палитру последовательно по всей диаграмме
- **Контраст текста КРИТИЧЕН** — никогда не используй светло‑серый на белом фоне. Минимальный цвет текста на белом: `#757575`
- Не используй эмодзи в тексте — они не отображаются шрифтом Excalidraw
- Для диаграмм в тёмном режиме смотри `references/dark-mode.md`
- Для более крупных примеров смотри `references/examples.md`