---
title: "Dogfood — исследовательское QA веб‑приложений: поиск багов, доказательств, отчётов"
sidebar_label: "Dogfood"
description: "Исследовательское QA веб‑приложений: поиск багов, доказательств, отчётов"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Dogfood

Исследовательское QA веб‑приложений: поиск багов, сбор доказательств, составление отчётов.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/dogfood` |
| Version | `1.0.0` |
| Platforms | linux, macos, windows |
| Tags | `qa`, `testing`, `browser`, `web`, `dogfood` |

## Reference: full SKILL.md

:::info
Ниже представлено полное определение скилла, которое Hermes загружает при его активации. Это то, что агент видит в виде инструкций, когда скилл включён.
:::

# Dogfood: Систематическое тестирование веб‑приложений (QA)

## Overview

Этот скилл проводит тебя через систематическое исследовательское QA тестирование веб‑приложений с использованием набора инструментов `browser`. Ты будешь перемещаться по приложению, взаимодействовать с элементами, фиксировать доказательства проблем и формировать структурированный баг‑репорт.

## Prerequisites

- Набор инструментов `browser` должен быть доступен (`browser_navigate`, `browser_snapshot`, `browser_click`, `browser_type`, `browser_vision`, `browser_console`, `browser_scroll`, `browser_back`, `browser_press`)
- URL‑адрес цели и область тестирования, полученные от пользователя

## Inputs

Пользователь предоставляет:
1. **Target URL** — точка входа для тестирования
2. **Scope** — какие области/фичи проверять (или «full site» для полного охвата)
3. **Output directory** (необязательно) — куда сохранять скриншоты и отчёт (по умолчанию: `./dogfood-output`)

## Workflow

Следуй 5‑фазному систематическому рабочему процессу:

### Phase 1: Plan

1. Создай структуру каталога вывода:
<!-- ascii-guard-ignore -->
   ```
   {output_dir}/
   ├── screenshots/       # Evidence screenshots
   └── report.md          # Final report (generated in Phase 5)
   ```
<!-- ascii-guard-ignore-end -->
2. Определи область тестирования на основе ввода пользователя.
3. Сформируй черновую карту сайта, планируя, какие страницы и функции проверять:
   - Главная/лендинг‑страница
   - Навигационные ссылки (header, footer, sidebar)
   - Ключевые пользовательские потоки (регистрация, вход, поиск, оформление заказа и т.д.)
   - Формы и интерактивные элементы
   - Пограничные случаи (пустые состояния, страницы ошибок, 404)

### Phase 2: Explore

Для каждой страницы или функции из плана:

1. **Navigate** к странице:
   ```
   browser_navigate(url="https://example.com/page")
   ```

2. **Take a snapshot** для понимания структуры DOM:
   ```
   browser_snapshot()
   ```

3. **Check the console** на наличие JavaScript‑ошибок:
   ```
   browser_console(clear=true)
   ```
   Делай это после каждой навигации и после каждого значимого взаимодействия. Тихие JS‑ошибки — ценные находки.

4. **Take an annotated screenshot** для визуального осмотра страницы и идентификации интерактивных элементов:
   ```
   browser_vision(question="Describe the page layout, identify any visual issues, broken elements, or accessibility concerns", annotate=true)
   ```
   Флаг `annotate=true` накладывает нумерованные метки `[N]` на интерактивные элементы. Каждая `[N]` соответствует ссылке `@eN` для последующих команд браузера.

5. **Test interactive elements** систематически:
   - Клик по кнопкам и ссылкам: `browser_click(ref="@eN")`
   - Заполнение форм: `browser_type(ref="@eN", text="test input")`
   - Тест клавиатурной навигации: `browser_press(key="Tab")`, `browser_press(key="Enter")`
   - Прокрутка содержимого: `browser_scroll(direction="down")`
   - Тест валидации форм некорректными данными
   - Тест отправки пустых форм

6. **After each interaction**, проверяй:
   - Ошибки консоли: `browser_console()`
   - Визуальные изменения: `browser_vision(question="What changed after the interaction?")`
   - Ожидаемое vs фактическое поведение

### Phase 3: Collect Evidence

Для каждой найденной проблемы:

1. **Take a screenshot** с отображением проблемы:
   ```
   browser_vision(question="Capture and describe the issue visible on this page", annotate=false)
   ```
   Сохрани `screenshot_path`, полученный в ответе — он понадобится в отчёте.

2. **Record the details**:
   - URL, где возникла проблема
   - Шаги для воспроизведения
   - Ожидаемое поведение
   - Фактическое поведение
   - Ошибки консоли (если есть)
   - Путь к скриншоту

3. **Classify the issue** согласно таксономии (см. `references/issue-taxonomy.md`):
   - Severity: Critical / High / Medium / Low
   - Category: Functional / Visual / Accessibility / Console / UX / Content

### Phase 4: Categorize

1. Просмотри все собранные проблемы.
2. Удалить дубликаты — объединить баги, проявляющиеся в разных местах, но являющиеся одной проблемой.
3. Присвоить окончательную Severity и Category каждому багу.
4. Сортировать по Severity (Critical → High → Medium → Low).
5. Подсчитать количество проблем по Severity и Category для executive summary.

### Phase 5: Report

Сгенерируй финальный отчёт, используя шаблон `templates/dogfood-report-template.md`.

Отчёт должен включать:
1. **Executive summary** с общим числом проблем, разбивкой по Severity и областью тестирования
2. **Per‑issue sections** с:
   - Номером и заголовком проблемы
   - Бейджами Severity и Category
   - URL, где обнаружена
   - Описанием проблемы
   - Шагами воспроизведения
   - Ожидаемым vs фактическим поведением
   - Ссылками на скриншоты (используй `MEDIA:<screenshot_path>` для встроенных изображений)
   - Ошибками консоли, если релевантно
3. **Summary table** всех проблем
4. **Testing notes** — что было протестировано, что нет, какие блокеры возникли

Сохрани отчёт в `{output_dir}/report.md`.

## Tools Reference

| Tool | Purpose |
|------|---------|
| `browser_navigate` | Перейти по URL |
| `browser_snapshot` | Получить текстовый снимок DOM (дерево доступности) |
| `browser_click` | Кликнуть элемент по ссылке (`@eN`) или тексту |
| `browser_type` | Ввести текст в поле ввода |
| `browser_scroll` | Прокрутить страницу вверх/вниз |
| `browser_back` | Вернуться в истории браузера |
| `browser_press` | Нажать клавишу клавиатуры |
| `browser_vision` | Скриншот + AI‑анализ; используйте `annotate=true` для меток элементов |
| `browser_console` | Получить вывод и ошибки JS‑консоли |

## Tips

- **Всегда проверяй `browser_console()` после навигации и после значимых взаимодействий.** Тихие JS‑ошибки — одни из самых ценных находок.
- **Используй `annotate=true` с `browser_vision`**, когда нужно понять расположение интерактивных элементов или когда ссылки в снимке неочевидны.
- **Тестируй как валидные, так и невалидные вводы** — баги валидации форм встречаются часто.
- **Прокручивай длинные страницы** — контент ниже «fold» может иметь проблемы с рендерингом.
- **Тестируй навигационные потоки** — проходи сквозь многошаговые процессы от начала до конца.
- **Проверяй адаптивность**, отмечая любые проблемы с разметкой, видимые на скриншотах.
- **Не забывай о пограничных случаях**: пустые состояния, очень длинный текст, специальные символы, быстрые клики.
- При предоставлении скриншотов пользователю включай `MEDIA:<screenshot_path>`, чтобы они отображались inline.