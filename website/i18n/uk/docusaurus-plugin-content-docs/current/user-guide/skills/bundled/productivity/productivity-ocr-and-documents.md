---
title: "Ocr і документи — Витягнути текст з PDF/сканів (pymupdf, marker-pdf)"
sidebar_label: "Ocr And Documents"
description: "Витягнути текст з PDF/сканів (pymupdf, marker-pdf)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# OCR та документи

Витяг тексту з PDF/сканів (pymupdf, marker-pdf).

## Метадані навички

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/productivity/ocr-and-documents` |
| Version | `2.3.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `PDF`, `Documents`, `Research`, `Arxiv`, `Text-Extraction`, `OCR` |
| Related skills | [`powerpoint`](/docs/user-guide/skills/bundled/productivity/productivity-powerpoint) |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# Витяг PDF та документів

Для DOCX: використовуйте `python-docx` (парсить реальну структуру документа, значно краще, ніж OCR).
Для PPTX: дивіться навичку `powerpoint` (використовує `python-pptx` з повною підтримкою слайдів/нотаток).
Ця навичка охоплює **PDF та скановані документи**.

## Крок 1: Доступний віддалений URL?

Якщо документ має URL, **завжди спочатку спробуйте `web_extract`**:

```
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])
web_extract(urls=["https://example.com/report.pdf"])
```

Це виконує конвертацію PDF у markdown за допомогою Firecrawl без локальних залежностей.

Локальний витяг використовуйте лише коли: файл локальний, `web_extract` не вдається, або потрібна пакетна обробка.

## Крок 2: Виберіть локальний екстрактор

| Feature | pymupdf (~25 MB) | marker-pdf (~3‑5 GB) |
|---------|-----------------|---------------------|
| **Текстовий PDF** | ✅ | ✅ |
| **Сканований PDF (OCR)** | ❌ | ✅ (90+ мов) |
| **Таблиці** | ✅ (базові) | ✅ (висока точність) |
| **Рівняння / LaTeX** | ❌ | ✅ |
| **Блоки коду** | ❌ | ✅ |
| **Форми** | ❌ | ✅ |
| **Видалення колонтитулів** | ❌ | ✅ |
| **Визначення порядку читання** | ❌ | ✅ |
| **Витяг зображень** | ✅ (вбудовані) | ✅ (з контекстом) |
| **Зображення → текст (OCR)** | ❌ | ✅ |
| **EPUB** | ✅ | ✅ |
| **Вивід у Markdown** | ✅ (через pymupdf4llm) | ✅ (нативний, вища якість) |
| **Розмір встановлення** | ~25 MB | ~3‑5 GB (PyTorch + моделі) |
| **Швидкість** | Миттєво | ~1‑14 s/сторінка (CPU), ~0.2 s/сторінка (GPU) |

**Вирішення**: використовуй pymupdf, якщо не потрібні OCR, рівняння, форми або складний аналіз розмітки.

Якщо користувач потребує можливостей marker, а в системі немає ~5 GB вільного місця:
> "Цей документ потребує OCR/розширеного витягу (marker-pdf), що вимагає ~5 GB для PyTorch і моделей. У вашій системі є [X] GB вільного місця. Варіанти: звільнити простір, надати URL, щоб я міг використати `web_extract`, або я можу спробувати pymupdf, який працює з текстовими PDF, але не зі сканованими документами чи рівняннями."

---

## pymupdf (легковаговий)

```bash
pip install pymupdf pymupdf4llm
```

**Через допоміжний скрипт**:
```bash
python scripts/extract_pymupdf.py document.pdf              # Plain text
python scripts/extract_pymupdf.py document.pdf --markdown    # Markdown
python scripts/extract_pymupdf.py document.pdf --tables      # Tables
python scripts/extract_pymupdf.py document.pdf --images out/ # Extract images
python scripts/extract_pymupdf.py document.pdf --metadata    # Title, author, pages
python scripts/extract_pymupdf.py document.pdf --pages 0-4   # Specific pages
```

**Вбудовано**:
```bash
python3 -c "
import pymupdf
doc = pymupdf.open('document.pdf')
for page in doc:
    print(page.get_text())
"
```

---

## marker-pdf (високоякісний OCR)

```bash
# Check disk space first
python scripts/extract_marker.py --check

pip install marker-pdf
```

**Через допоміжний скрипт**:
```bash
python scripts/extract_marker.py document.pdf                # Markdown
python scripts/extract_marker.py document.pdf --json         # JSON with metadata
python scripts/extract_marker.py document.pdf --output_dir out/  # Save images
python scripts/extract_marker.py scanned.pdf                 # Scanned PDF (OCR)
python scripts/extract_marker.py document.pdf --use_llm      # LLM-boosted accuracy
```

**CLI** (встановлюється разом з marker-pdf):
```bash
marker_single document.pdf --output_dir ./output
marker /path/to/folder --workers 4    # Batch
```

---

## Arxiv статті

```
# Abstract only (fast)
web_extract(urls=["https://arxiv.org/abs/2402.03300"])

# Full paper
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])

# Search
web_search(query="arxiv GRPO reinforcement learning 2026")
```

## Розділення, об’єднання та пошук

pymupdf виконує це нативно — використовуйте `execute_code` або вбудований Python:

```python
# Split: extract pages 1-5 to a new PDF
import pymupdf
doc = pymupdf.open("report.pdf")
new = pymupdf.open()
for i in range(5):
    new.insert_pdf(doc, from_page=i, to_page=i)
new.save("pages_1-5.pdf")
```

```python
# Merge multiple PDFs
import pymupdf
result = pymupdf.open()
for path in ["a.pdf", "b.pdf", "c.pdf"]:
    result.insert_pdf(pymupdf.open(path))
result.save("merged.pdf")
```

```python
# Search for text across all pages
import pymupdf
doc = pymupdf.open("report.pdf")
for i, page in enumerate(doc):
    results = page.search_for("revenue")
    if results:
        print(f"Page {i+1}: {len(results)} match(es)")
        print(page.get_text("text"))
```

Додаткові залежності не потрібні — pymupdf охоплює розділення, об’єднання, пошук та витяг тексту в одному пакеті.

---

## Примітки

- `web_extract` завжди перший вибір для URL
- pymupdf — безпечний за замовчуванням: миттєво, без моделей, працює скрізь
- marker-pdf — для OCR, сканованих документів, рівнянь, складних макетів; встановлюйте лише за потреби
- Обидва допоміжні скрипти підтримують `--help` для повного використання
- marker-pdf завантажує ~2.5 GB моделей у `~/.cache/huggingface/` при першому запуску
- Для Word‑документів: `pip install python-docx` (краще, ніж OCR — парсить реальну структуру)
- Для PowerPoint: дивіться навичку `powerpoint` (використовує python-pptx)