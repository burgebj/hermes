---
title: "Excel Автор"
sidebar_label: "Excel Author"
description: "Створюй аудиторські Excel‑книги в безголовому режимі за допомогою openpyxl — конвенції кольорів клітинок синій/чорний/зелений, формули замість жорстких значень, іменовані діапазони, перевірки балансу, чутливість…"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Excel Author

Створюй аудиторські Excel‑книги без інтерфейсу за допомогою **openpyxl** — конвенції кольорів клітинок синій/чорний/зелений, формули замість жорстких значень, іменовані діапазони, перевірки балансу, таблиці чутливості. Використовуй для фінансових моделей, аудиту результатів, звірок.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/finance/excel-author` |
| Path | `optional-skills/finance/excel-author` |
| Version | `1.0.0` |
| Author | Anthropic (adapted by Nous Research) |
| License | Apache-2.0 |
| Platforms | linux, macos, windows |
| Tags | `excel`, `openpyxl`, `finance`, `spreadsheet`, `modeling` |
| Related skills | [`pptx-author`](/docs/user-guide/skills/optional/finance/finance-pptx-author), [`dcf-model`](/docs/user-guide/skills/optional/finance/finance-dcf-model), [`comps-analysis`](/docs/user-guide/skills/optional/finance/finance-comps-analysis), [`lbo-model`](/docs/user-guide/skills/optional/finance/finance-lbo-model), [`3-statement-model`](/docs/user-guide/skills/optional/finance/finance-3-statement-model) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# excel-author

Створи файл **.xlsx** на диску за допомогою `openpyxl`. Дотримуйся банківських конвенцій нижче, щоб модель була аудиторською, гнучкою та перевіряною ким‑небудь іншим, крім автора.

Adapted from Anthropic's `xlsx-author` and `audit-xls` skills in the [anthropics/financial-services](https://github.com/anthropics/financial-services) repo. The MCP / Office‑JS / Cowork‑specific гілки оригіналів вилучено — цей скіл передбачає headless Python.

## Output contract

- Записуй у `./out/<name>.xlsx`. Створи `./out/`, якщо його немає.
- Поверни відносний шлях у фінальному повідомленні, щоб downstream‑інструменти могли його підхватити.
- По одному логічному моделлю на файл. Не додавай дані до існуючої книги, якщо не про це явно просять.

## Setup

```bash
pip install "openpyxl>=3.0"
```

## Core conventions (non-negotiable)

### Blue / black / green cell color
- **Blue** (`Font(color="0000FF")`) — жорстко закодований вхід, введений користувачем. Драйвери доходу, WACC‑вхід, термінальний зріст, ринкові дані.
- **Black** (за замовчуванням) — формула. Кожна похідна клітинка — живий Excel‑формула.
- **Green** (`Font(color="006100")`) — посилання на інший лист або зовнішній файл.

Рецензент може швидко просканувати лист і одразу побачити, що є припущенням, а що обчисленим.

### Formulas over hardcodes
Кожна клітинка з розрахунком ПОВИННА містити формулу, а не число, обчислене в Python і вставлене як значення.

```python
# WRONG — silent bug waiting to happen
ws["D20"] = revenue_prior_year * (1 + growth)

# CORRECT — flexes when the user changes the assumption
ws["D20"] = "=D19*(1+$B$8)"
```

Єдині дозволені жорсткі числа:
1. Сировинні історичні входи (фактичний дохід, звітний EBITDA тощо).
2. Припущення, які користувач має змінювати (темпи росту, WACC‑входи, термінальний g).
3. Поточні ринкові дані (ціна акції, залишок боргу) — з коментарем у клітинці, що документує джерело + дату.

Якщо помітиш, що обчислюєш значення в Python і записуєш його, зупинись.

### Named ranges for cross-sheet references
Використовуй іменовані діапазони для будь‑якої цифри, що посилається з іншого листа, презентації або мемо.

```python
from openpyxl.workbook.defined_name import DefinedName
wb.defined_names["WACC"] = DefinedName("WACC", attr_text="Inputs!$C$8")
# then elsewhere:
calc["D30"] = "=D29/WACC"
```

### Balance checks tab
Додай вкладку `Checks`, яка зв’язує все та повертає TRUE/FALSE:
- Баланс листа (assets = liabilities + equity)
- Cash‑flow зв’язок з зміною готівки між періодами на BS
- Sum‑of‑parts зв’язок з консолідованими підсумками
- Відсутність «злочинних» жорстких чисел у розрахункових діапазонах

Приклад:
```python
checks = wb.create_sheet("Checks")
checks["A2"] = "BS balances"
checks["B2"] = "=IS!D20-IS!D21-IS!D22"
checks["C2"] = "=ABS(B2)<0.01"  # TRUE/FALSE
```

### Cell comments on every hardcoded input
Додавай коментар **під час створення** клітинки, а не пізніше.

```python
from openpyxl.comments import Comment
ws["C2"] = 1_250_000_000
ws["C2"].font = Font(color="0000FF")
ws["C2"].comment = Comment("Source: 10-K FY2024, p.47, revenue line", "analyst")
```

Формат: `Source: [System/Document], [Date], [Reference], [URL if applicable]`.

Ніколи не відкладайте вказання джерела. Не пишіть `TODO: add source`.

## Skeleton: typical financial model

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.comments import Comment
from openpyxl.utils import get_column_letter
from pathlib import Path

BLUE = Font(color="0000FF")
BLACK = Font(color="000000")
GREEN = Font(color="006100")
BOLD = Font(bold=True)
HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
HEADER_FONT = Font(color="FFFFFF", bold=True)

wb = Workbook()

# --- Inputs tab ---
inp = wb.active
inp.title = "Inputs"
inp["A1"] = "MARKET DATA & KEY INPUTS"
inp["A1"].font = HEADER_FONT
inp["A1"].fill = HEADER_FILL
inp.merge_cells("A1:C1")

inp["B3"] = "Revenue FY2024"
inp["C3"] = 1_250_000_000
inp["C3"].font = BLUE
inp["C3"].comment = Comment("Source: 10-K FY2024 p.47", "model")

inp["B4"] = "Growth Rate"
inp["C4"] = 0.12
inp["C4"].font = BLUE

# --- Calc tab ---
calc = wb.create_sheet("DCF")
calc["B2"] = "Projected Revenue"
calc["C2"] = "=Inputs!C3*(1+Inputs!C4)"   # formula, black

# --- Checks tab ---
chk = wb.create_sheet("Checks")
chk["A2"] = "BS balances"
chk["B2"] = "=ABS(BS!D20-BS!D21-BS!D22)<0.01"

Path("./out").mkdir(exist_ok=True)
wb.save("./out/model.xlsx")
```

## Section headers with merged cells

Особливість openpyxl: при злитті задавай значення у верхньо‑лівій клітинці та стилізуй весь діапазон окремо.

```python
ws["A7"] = "CASH FLOW PROJECTION"
ws["A7"].font = HEADER_FONT
ws.merge_cells("A7:H7")
for col in range(1, 9):  # A..H
    ws.cell(row=7, column=col).fill = HEADER_FILL
```

## Sensitivity tables

Будуй за допомогою циклів, а не жорстко прописаних формул у кожній клітинці. Правила:

- **Непарна кількість рядків/стовпців** (5×5 або 7×7) — гарантує справжню центральну клітинку.
- **Центральна клітинка = базовий випадок.** Заголовок середнього рядка/стовпця має дорівнювати фактичному WACC та термінальному g моделі, щоб центральний результат дорівнював базовій оцінці ціни акції. Це контрольна перевірка.
- **Виділи центральну клітинку** заповненням середньо‑синього кольору (`"BDD7EE"`) та жирним шрифтом.
- Заповнюй кожну клітинку повною формулою переобчислення — без апроксимацій.

```python
# 5x5 WACC (rows) x terminal growth (cols) sensitivity
wacc_axis = [0.08, 0.085, 0.09, 0.095, 0.10]        # center row = base 9.0%
term_axis = [0.02, 0.025, 0.03, 0.035, 0.04]        # center col = base 3.0%

start_row = 40
ws.cell(row=start_row, column=1).value = "Implied Share Price ($)"
ws.cell(row=start_row, column=1).font = BOLD

for j, g in enumerate(term_axis):
    ws.cell(row=start_row+1, column=2+j).value = g
    ws.cell(row=start_row+1, column=2+j).font = BLUE

for i, w in enumerate(wacc_axis):
    r = start_row + 2 + i
    ws.cell(row=r, column=1).value = w
    ws.cell(row=r, column=1).font = BLUE
    for j, g in enumerate(term_axis):
        c = 2 + j
        # Full DCF recalc formula (simplified for illustration).
        # In a real model this references the full projection block.
        ws.cell(row=r, column=c).value = (
            f"=SUMPRODUCT(FCF_range,1/(1+{w})^year_offset) + "
            f"FCF_terminal*(1+{g})/({w}-{g})/(1+{w})^terminal_year"
        )

# Highlight center cell (base case)
center = ws.cell(row=start_row+2+len(wacc_axis)//2,
                 column=2+len(term_axis)//2)
center.fill = PatternFill("solid", fgColor="BDD7EE")
center.font = BOLD
```

## Recalculating before delivery

openpyxl записує лише рядки‑формули і не обчислює їх. Excel переобчислює при відкритті, але downstream‑споживачі (auto‑check скрипти, CI) потребують готових значень.

Запусти LibreOffice або окремий крок переобчислення перед доставкою:

```bash
# LibreOffice headless recalc
libreoffice --headless --calc --convert-to xlsx ./out/model.xlsx --outdir ./out/
```

Або скористайся Python‑helper‑ом для переобчислення (див. `scripts/recalc.py` у цьому скілі).

## Model layout planning

Перед записом будь‑якої формули:
1. Визнач **всі** позиції рядків секцій
2. Запиши **всі** заголовки та підписи
3. Додай **всі** розділові рядки та порожні рядки
4. ТІЛЬКИ потім записуй формули, використовуючи зафіксовані позиції рядків

Так запобігаєш патерну «зламаних» формул, коли додавання заголовка після запису формул зсуває всі downstream‑посилання.

## Verify step-by-step with the user

Для великих моделей (DCF, 3‑statement, LBO) зупиняйся і показуй користувачеві проміжні артефакти перед продовженням. Виявлення помилкового припущення маржі до побудови downstream‑таблиць чутливості економить години.

Патерн контрольних точок:
- Після блоку **Inputs** → покажи сирі входи, підтвердь перед проекцією
- Після проекції **Revenue** → підтвердь верхню лінію + темпи росту
- Після побудови **FCF** → підтвердь повний графік
- Після **WACC** → підтвердь входи
- Після **valuation** → підтвердь equity‑bridge
- ТІЛЬКИ після цього будуй таблиці чутливості

## When NOT to use this skill

- Користувачі в живій сесії Excel з доступним Office MCP — керуй їхньою живою книгою.
- Чистий експорт табличних даних без формул — `csv` або `pandas.to_excel` простіший.
- Дашборди/графіки з інтенсивною інтерактивністю — використай справжній BI‑інструмент.

## Attribution

Конвенції (синій/чорний/зелений, формули‑замість‑жорстких значень, іменовані діапазони, правила чутливості) адаптовано з Claude for Financial Services від Anthropic, ліцензія Apache‑2.0. Оригінал: https://github.com/anthropics/financial-services/tree/main/plugins/vertical-plugins/financial-analysis/skills/xlsx-author