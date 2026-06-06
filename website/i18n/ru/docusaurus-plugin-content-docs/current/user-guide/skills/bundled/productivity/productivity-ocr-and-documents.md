---
title: "OCR и документы — извлечение текста из PDF/сканов (pymupdf, marker-pdf)"
sidebar_label: "Ocr And Documents"
description: "Извлекать текст из PDF/сканов (pymupdf, marker-pdf)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# OCR и документы

Извлечение текста из PDF/сканов (pymupdf, marker-pdf).

## Метаданные навыка

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

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции при активном навыке.
:::

# Извлечение PDF и документов

Для DOCX : используй `python-docx` (парсит реальную структуру документа, гораздо лучше, чем OCR).
Для PPTX : смотри навык `powerpoint` (использует `python-pptx` с полной поддержкой слайдов/заметок).
Этот навык охватывает **PDF и отсканированные документы**.

## Шаг 1: Доступен удалённый URL?

Если у документа есть URL, **всегда сначала пробуй `web_extract`**:

```
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])
web_extract(urls=["https://example.com/report.pdf"])
```

Это выполняет конвертацию PDF → Markdown через Firecrawl без локальных зависимостей.

Локальное извлечение используем только когда: файл локальный, `web_extract` не сработал, или требуется пакетная обработка.

## Шаг 2: Выбери локальный экстрактор

| Возможность | pymupdf (~25 МБ) | marker-pdf (~3‑5 ГБ) |
|-------------|------------------|----------------------|
| **PDF с текстом** | ✅ | ✅ |
| **Отсканированный PDF (OCR)** | ❌ | ✅ (90 + языков) |
| **Таблицы** | ✅ (базовые) | ✅ (высокая точность) |
| **Уравнения / LaTeX** | ❌ | ✅ |
| **Блоки кода** | ❌ | ✅ |
| **Формы** | ❌ | ✅ |
| **Удаление колонтитулов** | ❌ | ✅ |
| **Определение порядка чтения** | ❌ | ✅ |
| **Извлечение изображений** | ✅ (встроенные) | ✅ (с контекстом) |
| **Изображения → текст (OCR)** | ❌ | ✅ |
| **EPUB** | ✅ | ✅ |
| **Вывод в Markdown** | ✅ (через pymupdf4llm) | ✅ (нативный, более качественный) |
| **Размер установки** | ~25 МБ | ~3‑5 ГБ (PyTorch + модели) |
| **Скорость** | Мгновенно | ~1‑14 с/страница (CPU), ~0.2 с/страница (GPU) |

**Решение**: использовать pymupdf, если только не нужен OCR, уравнения, формы или сложный анализ разметки.

Если пользователь требует возможностей marker, но в системе нет ~5 ГБ свободного места:
> "Этот документ требует OCR/расширенного извлечения (marker-pdf), что требует ~5 ГБ для PyTorch и моделей. На твоей системе доступно [X] ГБ свободного места. Варианты: освободить место, предоставить URL, чтобы я мог использовать `web_extract`, или я могу попробовать pymupdf, который работает с PDF, содержащими текст, но не со сканами или уравнениями."

---

## pymupdf (легковесный)

```bash
pip install pymupdf pymupdf4llm
```

**Через вспомогательный скрипт**:
```bash
python scripts/extract_pymupdf.py document.pdf              # Plain text
python scripts/extract_pymupdf.py document.pdf --markdown    # Markdown
python scripts/extract_pymupdf.py document.pdf --tables      # Tables
python scripts/extract_pymupdf.py document.pdf --images out/ # Extract images
python scripts/extract_pymupdf.py document.pdf --metadata    # Title, author, pages
python scripts/extract_pymupdf.py document.pdf --pages 0-4   # Specific pages
```

**Встроенно**:
```bash
python3 -c "
import pymupdf
doc = pymupdf.open('document.pdf')
for page in doc:
    print(page.get_text())
"
```

---

## marker-pdf (высококачественный OCR)

```bash
# Check disk space first
python scripts/extract_marker.py --check

pip install marker-pdf
```

**Через вспомогательный скрипт**:
```bash
python scripts/extract_marker.py document.pdf                # Markdown
python scripts/extract_marker.py document.pdf --json         # JSON with metadata
python scripts/extract_marker.py document.pdf --output_dir out/  # Save images
python scripts/extract_marker.py scanned.pdf                 # Scanned PDF (OCR)
python scripts/extract_marker.py document.pdf --use_llm      # LLM-boosted accuracy
```

**CLI** (устанавливается вместе с marker-pdf):
```bash
marker_single document.pdf --output_dir ./output
marker /path/to/folder --workers 4    # Batch
```

---

## Статьи из Arxiv

```
# Abstract only (fast)
web_extract(urls=["https://arxiv.org/abs/2402.03300"])

# Full paper
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])

# Search
web_search(query="arxiv GRPO reinforcement learning 2026")
```

## Разделение, объединение и поиск

pymupdf справляется с этим нативно — используй `execute_code` или встроенный Python:

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

Дополнительные зависимости не нужны — pymupdf покрывает разделение, объединение, поиск и извлечение текста в одном пакете.

---

## Примечания

- `web_extract` всегда первый выбор для URL
- pymupdf — безопасный вариант по умолчанию: мгновенно, без моделей, работает везде
- marker-pdf нужен для OCR, сканированных документов, уравнений, сложных макетов — устанавливай только при необходимости
- Оба вспомогательных скрипта поддерживают `--help` для полного списка опций
- marker-pdf скачивает ~2.5 ГБ моделей в `~/.cache/huggingface/` при первом запуске
- Для Word‑документов: `pip install python-docx` (лучше, чем OCR — парсит реальную структуру)
- Для PowerPoint: смотри навык `powerpoint` (использует python-pptx)