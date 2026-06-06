---
title: "Nano Pdf — Редактировать текст/опечатки/заголовки PDF через nano-pdf CLI (NL подсказки)"
sidebar_label: "Nano Pdf"
description: "Редактировать текст/опечатки/заголовки PDF через nano-pdf CLI (NL prompts)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Nano Pdf

Редактируй текст/опечатки/заголовки в PDF с помощью nano-pdf CLI (NL prompts).

## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/productivity/nano-pdf` |
| Version | `1.0.0` |
| Author | community |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `PDF`, `Documents`, `Editing`, `NLP`, `Productivity` |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции, когда навык включён.
:::

# nano-pdf

Редактируй PDF с помощью инструкций на естественном языке. Укажи страницу и опиши, что изменить.

## Предварительные требования

```bash
# Install with uv (recommended — already available in Hermes)
uv pip install nano-pdf

# Or with pip
pip install nano-pdf
```

## Использование

```bash
nano-pdf edit <file.pdf> <page_number> "<instruction>"
```

## Примеры

```bash
# Change a title on page 1
nano-pdf edit deck.pdf 1 "Change the title to 'Q3 Results' and fix the typo in the subtitle"

# Update a date on a specific page
nano-pdf edit report.pdf 3 "Update the date from January to February 2026"

# Fix content
nano-pdf edit contract.pdf 2 "Change the client name from 'Acme Corp' to 'Acme Industries'"
```

## Примечания

- Номера страниц могут быть 0‑based или 1‑based в зависимости от версии — если правка попала не на ту страницу, повтори с ±1
- Всегда проверяй полученный PDF после редактирования (используй `read_file` для проверки размера файла или открой его)
- Инструмент использует LLM под капотом — требуется API‑ключ (см. `nano-pdf --help` для настройки)
- Хорошо подходит для изменения текста; сложные изменения макета могут потребовать другого подхода