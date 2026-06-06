---
title: "Автор Excel"
sidebar_label: "Excel Author"
description: "Создавай проверяемые Excel‑книги в безголовом режиме с помощью openpyxl — соблюдай цветовые конвенции ячеек (синий/чёрный/зелёный), используй формулы вместо жёстких значений, именованные диапазоны, проверки баланса, чувствительность…"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Excel Author

Создавай проверяемые Excel‑книги в безголовом режиме с помощью openpyxl — конвенции цветов ячеек синий/чёрный/зелёный, формулы вместо жёстко заданных значений, именованные диапазоны, проверки баланса, таблицы чувствительности. Используй для финансовых моделей, аудита результатов, сверок.

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

Создай файл .xlsx на диске с помощью `openpyxl`. Следуй нижеописанным конвенциям банковского уровня, чтобы модель была проверяемой, гибкой и доступной для ревью другими людьми, а не только её создателем.

Адаптировано из навыков Anthropic `xlsx-author` и `audit-xls` в репозитории [anthropics/financial-services](https://github.com/anthropics/financial-services). Ветки MCP / Office‑JS / Cowork оригиналов удалены — этот навык предполагает безголовый Python.

## Output contract

- Запиши в `./out/<name>.xlsx`. Создай `./out/`, если его нет.
- Верни относительный путь в своём финальном сообщении, чтобы downstream‑tools могли его подобрать.
- Одна логическая модель на файл. Не добавляй данные в существующую книгу, если явно не просят.

## Setup

```bash
pip install "openpyxl>=3.0"
```

## Core conventions (non-negotiable)

### Blue / black / green cell color
- **Blue** (`Font(color="0000FF")`) — жёстко заданный ввод, введённый человеком. Драйверы доходов, вводы WACC, терминальный рост, рыночные данные.
- **Black** (по умолчанию) — формула. Каждая вычисляемая ячейка содержит живую формулу Excel.
- **Green** (`Font(color="006100")`) — ссылка на другой лист или внешний файл.

Ревьюер может быстро просканировать лист и увидеть, что является предположением, а что вычисленным.

### Formulas over hardcodes
Каждая ячейка расчёта ДОЛЖНА быть строкой‑формулой, а не числом, вычисленным в Python и вставленным как значение.

```python
# WRONG — silent bug waiting to happen
ws["D20"] = revenue_prior_year * (1 + growth)

# CORRECT — flexes when the user changes the assumption
ws["D20"] = "=D19*(1+$B$8)"
```

Разрешённые жёстко заданные числа:
1. Сырые исторические вводы (фактические доходы, заявленный EBITDA и т.д.)
2. Драйверы‑предположения, которые пользователь должен менять (темпы роста, вводы WACC, терминальный g)
3. Текущие рыночные данные (цена акции, баланс долга) — с комментарием ячейки, документирующим источник + дату

Если ты замечаешь, что вычисляешь значение в Python и записываешь результат, остановись.

### Named ranges for cross-sheet references
Используй именованные диапазоны для любой величины, на которую ссылаются с другого листа, из презентации или мемо.

```python
from openpyxl.workbook.defined_name import DefinedName
wb.defined_names["WACC"] = DefinedName("WACC", attr_text="Inputs!$C$8")
# then elsewhere:
calc["D30"] = "=D29/WACC"
```

### Balance checks tab
Добавь лист `Checks`, который связывает всё вместе и выводит TRUE/FALSE:
- Баланс листа (активы = пассивы + капитал)
- Связи cash flow с изменением наличности по периодам на BS
- Сумма частей = консолидированные итоги
- Нет «злостных» жёстких чисел внутри расчётных диапазонов

Пример:
```python
checks = wb.create_sheet("Checks")
checks["A2"] = "BS balances"
checks["B2"] = "=IS!D20-IS!D21-IS!D22"
checks["C2"] = "=ABS(B2)<0.01"  # TRUE/FALSE
```

### Cell comments on every hardcoded input
Добавляй комментарий ПРИ создании ячейки, а не позже.

```python
from openpyxl.comments import Comment
ws["C2"] = 1_250_000_000
ws["C2"].font = Font(color="0000FF")
ws["C2"].comment = Comment("Source: 10-K FY2024, p.47, revenue line", "analyst")
```

Формат: `Source: [System/Document], [Date], [Reference], [URL if applicable]`.

Никогда не откладывай указание источника. Никогда не пишите `TODO: add source`.

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

особенность openpyxl: при объединении задавай значение в ячейке‑верхнем‑левом углу и стилизуй весь диапазон отдельно.

```python
ws["A7"] = "CASH FLOW PROJECTION"
ws["A7"].font = HEADER_FONT
ws.merge_cells("A7:H7")
for col in range(1, 9):  # A..H
    ws.cell(row=7, column=col).fill = HEADER_FILL
```

## Sensitivity tables

Строй с помощью циклов, а не жёстко прописанных формул для каждой ячейки. Правила:

- **Нечётное количество строк/столбцов** (5×5 или 7×7) — гарантирует истинную центральную ячейку.
- **Центральная ячейка = базовый случай.** Заголовок средней строки/столбца должен соответствовать реальному WACC модели и терминальному g, чтобы центральный вывод равнялся базовому подразумеваемому курсу акции. Это проверка здравого смысла.
- **Выдели центральную ячейку** средне‑синим заливкой (`"BDD7EE"`) и полужирным шрифтом.
- Заполни каждую ячейку полной формулой пересчёта — никогда не используй приближение.

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

openpyxl записывает строки‑формулы, но не вычисляет их. Excel пересчитывает при открытии, однако downstream‑tools (скрипты авто‑проверки, CI) нуждаются в вычисленных значениях.

Запусти LibreOffice или отдельный шаг пересчёта перед доставкой:

```bash
# LibreOffice headless recalc
libreoffice --headless --calc --convert-to xlsx ./out/model.xlsx --outdir ./out/
```

Или используй вспомогательный скрипт Python для пересчёта (см. `scripts/recalc.py` в этом навыке).

## Model layout planning

Перед записью любой формулы:
1. Определи ВСЕ позиции строк секций
2. Запиши ВСЕ заголовки и подписи
3. Запиши ВСЕ разделители секций и пустые строки
4. ТОЛЬКО после этого записывай формулы, используя зафиксированные позиции строк

Это предотвращает проблему «сломанных» формул, когда вставка строки‑заголовка после записи формул смещает все downstream‑ссылки.

## Verify step-by-step with the user

Для больших моделей (DCF, 3‑statement, LBO) останавливайся и показывай пользователю промежуточные артефакты перед продолжением. Выявление неверного предположения о марже до построения downstream‑таблиц чувствительности экономит час.

Шаблон контрольных точек:
- После блока ввода → показать сырые вводы, подтвердить перед проекцией
- После проекций доходов → подтвердить топ‑лайн + рост
- После построения FCF → подтвердить полный график
- После WACC → подтвердить вводы
- После оценки → подтвердить equity‑bridge
- ЗАТЕМ построить таблицы чувствительности

## When NOT to use this skill

- Пользователи в живой сессии Excel с доступным Office MCP — управляй их живой книгой вместо этого.
- Чистый экспорт табличных данных без формул — проще `csv` или `pandas.to_excel`.
- Дашборды / графики с интенсивной интерактивностью — используй полноценный BI‑инструмент.

## Attribution

Конвенции (синий/чёрный/зелёный, формулы‑вместо‑жёстких‑чисел, именованные диапазоны, правила чувствительности) адаптированы из плагин‑suite Claude for Financial Services от Anthropic, лицензия Apache-2.0. Оригинал: https://github.com/anthropics/financial-services/tree/main/plugins/vertical-plugins/financial-analysis/skills/xlsx-author