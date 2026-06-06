---
title: "Pptx Author — Створюй презентації PowerPoint без графічного інтерфейсу за допомогою python-pptx"
sidebar_label: "Pptx Author"
description: "Створюй PowerPoint презентації без графічного інтерфейсу за допомогою python-pptx"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Pptx Author

Створюй презентації PowerPoint без графічного інтерфейсу за допомогою `python-pptx`. Поєднується з `excel-author` для модель‑підтримуваних презентацій, де кожне число прив’язане до клітинки у робочій книзі. Використовуй для пітч‑презентацій, IC‑мемо, нотаток про прибутки.

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
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# pptx-author

Створює файл `.pptx` на диску за допомогою `python-pptx`. Використовуй, коли потрібно надати презентацію як файл‑артефакт, а не вести живу сесію PowerPoint.

Adapted from Anthropic's `pptx-author` and `pitch-deck` skills in [anthropics/financial-services](https://github.com/anthropics/financial-services). Гілки MCP / Office‑JS оригіналів вилучені — передбачається використання headless Python.

Для більш широкої, вже постаченої функції створення PowerPoint (слайди, нотатки доповідача, вбудовані медіа) дивись вбудований skill `powerpoint`. Цей skill — легша реалізація, налаштована для модель‑підтримуваних презентацій (пітч‑дек, IC‑мемо, нотатки про прибутки), де кожне число має бути простеженим до вихідної робочої книги.

## Output contract

- Записати у `./out/<name>.pptx`. Створити `./out/`, якщо його немає.
- Повернути відносний шлях у фінальному повідомленні.

## Setup

```bash
pip install "python-pptx>=0.6"
```

## Core conventions

### One idea per slide
Заголовок формулює головний висновок; основний текст його підтримує. Слайд з назвою «Q3 Revenue» слабкий; «Revenue growth accelerated to 14% Y/Y in Q3» — сильний.

### Every number traces to the model
Якщо цифра на слайді взята з `./out/model.xlsx`, вкажи у підписі лист і клітинку.

```
Revenue: $1,250M  (Source: model.xlsx, Inputs!C3)
```

Ніколи не копіюй числа з пам’яті або з підсумку — відкрий робочу книгу, прочитай іменований діапазон і прив’яжи значення до слайду програмно, коли це можливо.

### Use the firm template when one is mounted
Якщо існує `./templates/firm-template.pptx`, завантаж його, щоб презентація успадкувала брендовані кольори, шрифти та макети.

```python
from pptx import Presentation
from pathlib import Path

template = Path("./templates/firm-template.pptx")
prs = Presentation(str(template)) if template.exists() else Presentation()
```

### Charts: PNG-from-model beats native pptx charts
Коли важлива точність (стиль діаграми моделі має точно відповідати презентації), згенеруй діаграму у PNG безпосередньо з робочої книги та встав зображення. Вбудовані діаграми `pptx.chart` крихкі і часто не відповідають корпоративним стандартам.

```python
from pptx.util import Inches
slide.shapes.add_picture("./out/charts/football_field.png",
                         Inches(1), Inches(2),
                         width=Inches(8))
```

### No external sends
Цей skill лише записує файл. Він не надсилає електронну пошту, не завантажує і не публікує його. Шари оркестрації відповідають за доставку.

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

Читай іменовані діапазони або конкретні клітинки з твоєї Excel‑моделі, щоб числа в презентації не відхилялися.

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

Потім формуй вміст слайдів, використовуючи ці значення:
```python
slide.shapes.title.text = f"Implied share price of ${implied_mid:.2f} (base case)"
```

Пам’ятай переобчислити робочу книгу перед читанням — `openpyxl` бачить лише вже обчислені значення. Спочатку запусти допоміжну функцію переобчислення в skill `excel-author` або відкрий/збережи файл у реальній сесії Excel.

## Slide-type checklist for pitch decks

Типова структура банківської пітч‑презентації виглядає так. Не є жорстким шаблоном, а слугує стартовим каркасом:

1. Cover / title
2. Disclaimer
3. Table of contents
4. Situation overview
5. Company snapshot (the target)
6. Market / sector context
7. Valuation summary (football field) — the money slide
8. Trading comps detail
9. Precedent transactions detail
10. DCF summary
11. Illustrative LBO / sponsor case
12. Process considerations
13. Appendix

## When NOT to use this skill

- Користувачі в живій сесії PowerPoint з доступним Office MCP — керуйте їхнім живим документом замість цього.
- Презентації, не пов’язані з фінансами (щоквартальні all‑hands, маркетингові деки) — використовуйте більш універсальний skill `powerpoint`.
- Презентації з інтенсивною анімацією, переходами або нотатками доповідача — використовуйте більш універсальний skill `powerpoint`.

## Attribution

Conventions adapted from Anthropic's Claude for Financial Services plugin suite, Apache-2.0 licensed. Original: https://github.com/anthropics/financial-services/tree/main/plugins/agent-plugins/pitch-agent/skills/pptx-author