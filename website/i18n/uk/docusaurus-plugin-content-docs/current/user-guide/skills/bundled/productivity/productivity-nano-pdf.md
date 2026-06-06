---
title: "Nano Pdf — Редагуй текст/помилки/заголовки PDF за допомогою nano-pdf CLI (NL підказки)"
sidebar_label: "Nano Pdf"
description: "Редагуй текст/помилки/заголовки PDF за допомогою nano-pdf CLI (NL підказки)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Nano PDF

Редагуй текст, виправляй помилки та змінюй заголовки у PDF за допомогою nano-pdf CLI (NL prompts).

## Метадані навички

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/productivity/nano-pdf` |
| Version | `1.0.0` |
| Author | community |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `PDF`, `Documents`, `Editing`, `NLP`, `Productivity` |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# nano-pdf

Редагуй PDF за допомогою інструкцій природною мовою. Вкажи сторінку та опиши, що потрібно змінити.

## Передумови

```bash
# Install with uv (recommended — already available in Hermes)
uv pip install nano-pdf

# Or with pip
pip install nano-pdf
```

## Використання

```bash
nano-pdf edit <file.pdf> <page_number> "<instruction>"
```

## Приклади

```bash
# Change a title on page 1
nano-pdf edit deck.pdf 1 "Change the title to 'Q3 Results' and fix the typo in the subtitle"

# Update a date on a specific page
nano-pdf edit report.pdf 3 "Update the date from January to February 2026"

# Fix content
nano-pdf edit contract.pdf 2 "Change the client name from 'Acme Corp' to 'Acme Industries'"
```

## Примітки

- Номери сторінок можуть бути 0‑based або 1‑based залежно від версії — якщо редагування потрапило не на ту сторінку, спробуй ще раз з ±1
- Завжди перевіряй вихідний PDF після редагування (використовуй `read_file` для перевірки розміру файлу або відкрий його)
- Інструмент використовує LLM у фоні — потрібен API‑ключ (перевір `nano-pdf --help` для налаштувань)
- Добре підходить для змін тексту; складні зміни розкладки можуть вимагати іншого підходу