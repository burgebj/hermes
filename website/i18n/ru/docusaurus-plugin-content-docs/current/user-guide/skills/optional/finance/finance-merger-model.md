---
title: "Модель слияния — построение моделей аккреции/разбавления (слияния) в Excel — про‑форма P&L, синергии, структура финансирования, влияние на EPS"
sidebar_label: "Merger Model"
description: "Создай модели аккреции/разводнения (слияния) в Excel — про‑форма P&L, синергии, структура финансирования, влияние на EPS"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Merger Model

Создавай модели аккреции/разводнения (слияния) в Excel — про‑форму P&L, синергии, структура финансирования, влияние на EPS. Работает в паре с `excel-author`. Используй для M&A‑презентаций, материалов для совета директоров или оценки сделки.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/finance/merger-model` |
| Path | `optional-skills/finance/merger-model` |
| Version | `1.0.0` |
| Author | Anthropic (adapted by Nous Research) |
| License | Apache-2.0 |
| Platforms | linux, macos, windows |
| Tags | `finance`, `m-and-a`, `merger`, `accretion-dilution`, `excel`, `openpyxl`, `modeling`, `investment-banking` |
| Related skills | [`excel-author`](/docs/user-guide/skills/optional/finance/finance-excel-author), [`pptx-author`](/docs/user-guide/skills/optional/finance/finance-pptx-author), [`dcf-model`](/docs/user-guide/skills/optional/finance/finance-dcf-model), [`3-statement-model`](/docs/user-guide/skills/optional/finance/finance-3-statement-model) |

## Reference: full SKILL.md

:::info
Ниже приведено полное определение скилла, которое Hermes загружает при его активации. Это то, что агент видит в виде инструкций, когда скилл включён.
:::

## Environment

Скилл предполагает **headless openpyxl** — ты генерируешь файл `.xlsx` на диске.
Следуй конвенциям скилла `excel-author` для раскраски ячеек, формул, именованных диапазонов и таблиц чувствительности.
Пересчитай перед выдачей: `python /path/to/excel-author/scripts/recalc.py ./out/model.xlsx`.

# Merger Model

Построй анализ аккреции/разводнения для M&A‑транзакций. Моделирует влияние на EPS в про‑форме, чувствительность к синергиям и распределение цены покупки. Используй при оценке потенциального приобретения, подготовке анализа последствий слияния для презентации или консультировании по условиям сделки.

## Workflow

### Step 1: Gather Inputs

**Acquirer (покупатель):**
- Название компании, текущая цена акции, количество акций в обращении
- LTM и NTM EPS (GAAP и скорректированный)
- Мультипликатор P/E
- Предналоговая стоимость долга, ставка налога
- Денежные средства на балансе, существующий долг

**Target (цель):**
- Название компании, текущая цена акции, количество акций в обращении (если публичная)
- LTM и NTM EPS или чистая прибыль
- Стоимость предприятия (Enterprise Value) или стоимость капитала (Equity Value)

**Deal Terms (условия сделки):**
- Цена предложения за акцию (или премия к текущей цене)
- Состав оплаты: % наличных vs. % акций
- Новый долг, привлекаемый для финансирования наличной части
- Ожидаемые синергии (выручка и издержки) и график их внедрения
- Транзакционные издержки и расходы на финансирование
- Ожидаемая дата закрытия

### Step 2: Purchase Price Analysis

| Item | Value |
|------|-------|
| Offer price per share | |
| Premium to current | |
| Equity value | |
| Plus: net debt assumed | |
| Enterprise value | |
| EV / EBITDA implied | |
| P/E implied | |

### Step 3: Sources & Uses

| Sources | $ | Uses | $ |
|---------|---|------|---|
| New debt | | Equity purchase price | |
| Cash on hand | | Refinance target debt | |
| New equity issued | | Transaction fees | |
| | | Financing fees | |
| **Total** | | **Total** | |

### Step 4: Pro Forma EPS (Accretion / Dilution)

Расчёт по годам (Year 1‑Year 3):

| | Standalone | Pro Forma | Accretion/(Dilution) |
|---|-----------|-----------|---------------------|
| Acquirer net income | | | |
| Target net income | | | |
| Synergies (after tax) | | | |
| Foregone interest on cash (after tax) | | | |
| New debt interest (after tax) | | | |
| Intangible amortization (after tax) | | | |
| Pro forma net income | | | |
| Pro forma shares | | | |
| **Pro forma EPS** | | | |
| **Accretion / (Dilution) %** | | | |

### Step 5: Sensitivity Analysis

**Accretion/Dilution vs. Synergies and Offer Premium:**

| | $0 M syn | $25 M syn | $50 M syn | $75 M syn | $100 M syn |
|---|---------|----------|----------|----------|-----------|
| 15% premium | | | | | |
| 20% premium | | | | | |
| 25% premium | | | | | |
| 30% premium | | | | | |

**Accretion/Dilution vs. Cash/Stock Mix:**

| | 100% cash | 75/25 | 50/50 | 25/75 | 100% stock |
|---|-----------|-------|-------|-------|------------|
| Year 1 | | | | | |
| Year 2 | | | | | |

### Step 6: Breakeven Synergies

Рассчитай минимальный объём синергий, необходимый для нейтрального влияния на EPS в Year 1.

### Step 7: Output

- Excel‑книга со следующими листами:
  - Assumptions (входные допущения)
  - Sources & Uses
  - Pro forma income statement
  - Accretion/Dilution summary
  - Таблицы чувствительности
  - Анализ точки безубыточности
- Одностраничное резюме последствий слияния для презентации

## Important Notes

- Всегда показывай как GAAP, так и скорректированный (cash) EPS, где это уместно.
- При сделках с акциями используй текущую цену покупателя для расчёта коэффициента обмена, указывай разводнение от новых акций.
- Включай распределение цены покупки — гудвилл и амортизация нематериальных активов влияют на GAAP EPS.
- Фаза внедрения синергий критична — в Year 1 обычно реализуется только 25‑50 % от полной нормы.
- Не забудь учесть упущенный доход от наличных (foregone interest) и новые процентные расходы по привлечённому долгу.
- Ставка налога для корректировок по синергиям и процентам должна соответствовать предельной ставке покупателя.

## Data sources — MCP first, web fallback

Во многих местах указано «use the S&P Kensho MCP / Daloopa MCP / FactSet MCP». Это коммерческие финансовые MCP из оригинального контекста Cowork. В Hermes:

- **Если у тебя настроен любой структурированный финансовый MCP** (Hermes поддерживает MCP — см. скилл `native-mcp`), используй его в первую очередь для точечных сравнений, прецедентных сделок и документов.
- **Иначе** переходи к резервным источникам:
  - `web_search` / `web_extract` по SEC EDGAR (`https://www.sec.gov/cgi-bin/browse-edgar`) для американских отчётов;
  - Страницы IR компаний для пресс‑релизов и презентаций результатов;
  - `browser_navigate` для интерактивных порталов данных;
  - Данные, предоставленные пользователем (спрашивай явно, если контекст их не содержит).
- **Никогда не выдумывай** данные. Если множитель, прецедент или цифра из документа недоступны, пометь ячейку как `[UNSOURCED]` и донеси это до пользователя.

## Attribution

Этот скилл адаптирован из набора плагинов Claude for Financial Services от Anthropic (Apache‑2.0). Путь Office‑JS / Cowork live‑Excel удалён; данная версия ориентирована на headless openpyxl и использует конвенции скилла `excel-author`. Оригинал: https://github.com/anthropics/financial-services