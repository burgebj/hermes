---
title: "Pptx Author — Создавай PowerPoint‑презентации без графического интерфейса с помощью python-pptx"
sidebar_label: "Pptx Author"
description: "Создавай презентации PowerPoint без графического интерфейса с помощью python-pptx"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Pptx Author

Создавай презентации PowerPoint в безголовом режиме с помощью `python-pptx`. Парыруется с `excel-author` для моделей‑поддерживаемых презентаций, где каждое число привязано к ячейке рабочей книги. Используй для питч‑деков, IC‑мемо, отчётов о доходах.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/finance/pptx-author` |
| Path | `optional-skills/finance/pptx-author` |
| Version | `1.0.0` |
| Author | Anthropic (adapted by Nous Research) |
| License | Apache-2.0 |
| Platforms | linux, macos, windows |
| Tags | `powerpoint`, `pptx`, `python-pptx`, `presentation`, `finance` |
| Related skills | [`excel-author`](/docs/user-guide/skills/optional/finance/finance-excel-author), [`powerpoint`](/docs/user-guide/skills/bundled/productivity/productivity-powerpoint) |

## Reference: full SKILL.md

:::info
Ниже полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции, когда навык включён.
:::

# pptx-author

Создай файл `.pptx` на диске с помощью `python-pptx`. Используй, когда нужно предоставить презентацию как файловый артефакт, а не вести живую сессию PowerPoint.

Адаптировано из `pptx-author` и `pitch-deck` навыков Anthropic в [anthropics/financial-services](https://github.com/anthropics/financial-services). Ветки MCP / Office‑JS оригиналов удалены — предполагается безголовый Python.

Для более широкого, уже поставляемого навыка создания PowerPoint (слайды, заметки докладчика, вложения, медиа) смотри встроенный навык `powerpoint`. Этот навык — облегчённый шаблон, настроенный для моделей‑поддерживаемых презентаций (питч‑деки, IC‑мемо, отчёты о доходах), где каждое число должно быть привязано к исходной рабочей книге.

## Output contract

- Запиши в `./out/<name>.pptx`. Создай `./out/`, если его нет.
- Верни относительный путь в своём финальном сообщении.

## Setup

```bash
pip install "python-pptx>=0.6"
```

## Core conventions

### One idea per slide
Заголовок формулирует основной вывод; тело его поддерживает. Слайд с заголовком «Q3 Revenue» слабый; «Revenue growth accelerated to 14% Y/Y in Q3» — сильный.

### Every number traces to the model
Если цифра на слайде взята из `./out/model.xlsx`, укажи лист и ячейку в сноске.

```
Revenue: $1,250M  (Source: model.xlsx, Inputs!C3)
```

Никогда не переписывай числа из памяти или из резюме — открой рабочую книгу, прочитай именованный диапазон и привяжи значение к слайду программно, когда это возможно.

### Use the firm template when one is mounted
Если существует `./templates/firm-template.pptx`, загрузите его, чтобы презентация унаследовала фирменные цвета, шрифты и мастер‑макеты.

```python
from pptx import Presentation
from pathlib import Path

template = Path("./templates/firm-template.pptx")
prs = Presentation(str(template)) if template.exists() else Presentation()
```

### Charts: PNG-from-model beats native pptx charts
Когда важна точность (стилизация графика модели должна точно соответствовать презентации), отрендери график в PNG из исходной рабочей книги и вставь изображение. Нативные графики `pptx.chart` хрупки и часто не соответствуют фирменным требованиям.

```python
from pptx.util import Inches
slide.shapes.add_picture("./out/charts/football_field.png",
                         Inches(1), Inches(2),
                         width=Inches(8))
```

### No external sends
Этот навык только пишет файл. Он никогда не отправляет email, не загружает и не публикует. Слои оркестрации отвечают за доставку.

## Skeleton

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pathlib import Path

template = Path("./templates/firm-template.pptx")
prs = Presentation(str(template)) if template.exists() else Presentation()

# Title slide
slide = prs.slides.add_slide(prs.slide_layouts[0])
slide.shapes.title.text = "Project Aurora — Strategic Alternatives"
slide.placeholders[1].text = "Preliminary Discussion Materials"

# Valuation summary slide (title-only layout)
slide = prs.slides.add_slide(prs.slide_layouts[5])
slide.shapes.title.text = "Valuation implies $38–$52 per share across methodologies"

# Add a table bound to model outputs
rows, cols = 5, 4
tbl_shape = slide.shapes.add_table(rows, cols,
                                   Inches(0.5), Inches(1.5),
                                   Inches(9), Inches(3))
tbl = tbl_shape.table
headers = ["Methodology", "Low ($)", "Mid ($)", "High ($)"]
for c, h in enumerate(headers):
    tbl.cell(0, c).text = h

# In a real deck, read these from the model workbook with openpyxl
data = [
    ("Trading comps",     "35", "41", "48"),
    ("Precedent M&A",     "39", "45", "52"),
    ("DCF (base)",        "36", "43", "51"),
    ("LBO (10% IRR)",     "33", "38", "44"),
]
for r, row in enumerate(data, start=1):
    for c, val in enumerate(row):
        tbl.cell(r, c).text = val

# Embed a chart rendered from the model
slide = prs.slides.add_slide(prs.slide_layouts[5])
slide.shapes.title.text = "Football field — current price $42"
slide.shapes.add_picture("./out/charts/football_field.png",
                         Inches(1), Inches(1.8), width=Inches(8))

Path("./out").mkdir(exist_ok=True)
prs.save("./out/pitch-aurora.pptx")
```

## Binding deck numbers to the source workbook

Читай именованные диапазоны или конкретные ячейки из своей Excel‑модели, чтобы числа в презентации никогда не отклонялись.

```python
from openpyxl import load_workbook

wb = load_workbook("./out/model.xlsx", data_only=True)
def nr(name):
    """Resolve a named range to its current computed value."""
    rng = wb.defined_names[name]
    sheet, coord = next(rng.destinations)
    return wb[sheet][coord].value

revenue_fy24 = nr("RevenueFY24")
implied_mid  = nr("ImpliedSharePriceBase")
```

Затем формируй содержимое слайдов, используя эти значения:
```python
slide.shapes.title.text = f"Implied share price of ${implied_mid:.2f} (base case)"
```

Не забудь пересчитать рабочую книгу перед чтением — `openpyxl` видит только вычисленные значения, если лист уже был рассчитан. Сначала запусти вспомогательную функцию пересчёта в навыке `excel-author`, либо открой/сохрани файл через реальную сессию Excel.

## Slide-type checklist for pitch decks

Типичная банковская презентация следует этой структуре. Не является строгим шаблоном, но полезна как отправная точка:

1. Обложка / название
2. Дисклеймер
3. Оглавление
4. Обзор ситуации
5. Снимок компании (цель)
6. Контекст рынка / сектора
7. Сводка оценки (football field) — слайд с деньгами
8. Детали сравнения компаний‑трейдеров
9. Детали аналогичных транзакций
10. Сводка DCF
11. Иллюстративный LBO / кейс спонсора
12. Соображения процесса
13. Приложения

## When NOT to use this skill

- Пользователи в живой сессии PowerPoint с доступным Office MCP — управляй их живым документом вместо этого.
- Слайды не финансовой тематики (квартальные all‑hands, маркетинговые презентации) — используй более широкий навык `powerpoint`.
- Презентации с тяжёлой анимацией, переходами или заметками докладчика — используй более широкий навык `powerpoint`.

## Attribution

Конвенции адаптированы из набора плагинов Claude for Financial Services от Anthropic, лицензировано под Apache-2.0. Оригинал: https://github.com/anthropics/financial-services/tree/main/plugins/agent-plugins/pitch-agent/skills/pptx-author