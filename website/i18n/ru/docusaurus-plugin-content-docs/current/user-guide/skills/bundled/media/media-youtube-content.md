---
title: "Youtube Content — транскрипты YouTube в резюме, ветки, блоги"
sidebar_label: "Youtube Content"
description: "Транскрипты YouTube в резюме, ветки, блоги"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# YouTube Content

Транскрипты YouTube в резюме, ветки, блоги.

## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/media/youtube-content` |
| Platforms | linux, macos, windows |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции, когда навык включён.
:::

# YouTube Content Tool

## Когда использовать

Используй, когда пользователь делится URL‑адресом YouTube или ссылкой на видео, просит сделать резюме видео, запросить транскрипт или хочет извлечь и переформатировать контент из любого видео YouTube. Преобразует транскрипты в структурированный контент (главы, резюме, ветки, статьи).

Извлекает транскрипты из видео YouTube и конвертирует их в полезные форматы.

## Настройка

```bash
pip install youtube-transcript-api
```

## Вспомогательный скрипт

`SKILL_DIR` — каталог, содержащий этот файл SKILL.md. Скрипт принимает любой стандартный формат URL‑адреса YouTube, короткие ссылки (youtu.be), Shorts, embed‑ссылки, ссылки на прямой эфир или «сырой» 11‑символьный идентификатор видео.

```bash
# JSON output with metadata
python3 SKILL_DIR/scripts/fetch_transcript.py "https://youtube.com/watch?v=VIDEO_ID"

# Plain text (good for piping into further processing)
python3 SKILL_DIR/scripts/fetch_transcript.py "URL" --text-only

# With timestamps
python3 SKILL_DIR/scripts/fetch_transcript.py "URL" --timestamps

# Specific language with fallback chain
python3 SKILL_DIR/scripts/fetch_transcript.py "URL" --language tr,en
```

## Форматы вывода

После получения транскрипта форматируй его в соответствии с запросом пользователя:

- **Chapters**: группировка по смене тем, вывод списка глав с отметками времени
- **Summary**: лаконичное 5‑10‑предложное резюме всего видео
- **Chapter summaries**: главы с коротким абзацем‑резюме для каждой
- **Thread**: формат ветки Twitter/X — нумерованные посты, каждый до 280 символов
- **Blog post**: полная статья с заголовком, разделами и ключевыми выводами
- **Quotes**: заметные цитаты с отметками времени

### Пример — Вывод глав

```
00:00 Introduction — host opens with the problem statement
03:45 Background — prior work and why existing solutions fall short
12:20 Core method — walkthrough of the proposed approach
24:10 Results — benchmark comparisons and key takeaways
31:55 Q&A — audience questions on scalability and next steps
```

## Рабочий процесс

1. **Fetch** транскрипт с помощью вспомогательного скрипта, используя `--text-only --timestamps`.
2. **Validate**: убедись, что вывод не пустой и на ожидаемом языке. Если пустой, повтори без `--language`, чтобы получить любой доступный транскрипт. Если всё равно пусто, сообщи пользователю, что у видео, вероятно, отключены транскрипты.
3. **Chunk if needed**: если транскрипт превышает ~50 К символов, разбей его на перекрывающиеся фрагменты (~40 К с перекрытием 2 К) и сделай резюме каждого фрагмента перед объединением.
4. **Transform** в запрошенный формат вывода. Если пользователь не указал формат, по умолчанию используй резюме.
5. **Verify**: перечитай преобразованный вывод, проверь связность, правильность отметок времени и полноту перед представлением.

## Обработка ошибок

- **Transcript disabled**: сообщи пользователю; предложи проверить, доступны ли субтитры на странице видео.
- **Private/unavailable video**: передай ошибку и попроси пользователя проверить URL.
- **No matching language**: повтори без `--language`, чтобы получить любой доступный транскрипт, затем укажи фактический язык пользователю.
- **Dependency missing**: выполните `pip install youtube-transcript-api` и повторите попытку.