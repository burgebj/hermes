---
title: "Контент Youtube — транскрипції YouTube в резюме, теми, блоги"
sidebar_label: "Youtube Content"
description: "Транскрипції YouTube в резюме, теми, блоги"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Youtube Content

Транскрипції YouTube в резюме, треди, блоги.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/media/youtube-content` |
| Platforms | linux, macos, windows |

## Reference: full SKILL.md

:::info
Нижче наведено повний опис навички, який Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# YouTube Content Tool

## When to use

Використовуй, коли користувач ділиться URL‑адресою YouTube або посиланням на відео, просить підсумувати відео, запитує транскрипцію або хоче витягнути та переформатувати вміст будь‑якого відео YouTube. Перетворює транскрипції у структурований контент (глави, резюме, треди, блоги).

Витягати транскрипції з відео YouTube і конвертувати їх у корисні формати.

## Setup

```bash
pip install youtube-transcript-api
```

## Helper Script

`SKILL_DIR` — це каталог, що містить цей SKILL.md файл. Скрипт приймає будь‑який стандартний формат URL‑адреси YouTube, короткі посилання (youtu.be), Shorts, embed‑посилання, live‑посилання або «чистий» 11‑символьний ідентифікатор відео.

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

## Output Formats

Після отримання транскрипції форматувати її згідно з запитом користувача:

- **Chapters**: Групувати за зміною тем, вивести список глав з мітками часу
- **Summary**: Короткий огляд у 5‑10 реченнях всього відео
- **Chapter summaries**: Глави з коротким абзацом‑резюме для кожної
- **Thread**: Формат треду Twitter/X — нумеровані пости, кожен до 280 символів
- **Blog post**: Повна стаття з заголовком, розділами та ключовими висновками
- **Quotes**: Помітні цитати з мітками часу

### Example — Chapters Output

```
00:00 Introduction — host opens with the problem statement
03:45 Background — prior work and why existing solutions fall short
12:20 Core method — walkthrough of the proposed approach
24:10 Results — benchmark comparisons and key takeaways
31:55 Q&A — audience questions on scalability and next steps
```

## Workflow

1. **Fetch** транскрипцію за допомогою допоміжного скрипту з `--text-only --timestamps`.
2. **Validate**: переконатися, що результат не порожній і на потрібній мові. Якщо порожньо, повторити без `--language`, щоб отримати будь‑яку доступну транскрипцію. Якщо і далі порожньо, повідомити користувачу, що у відео, ймовірно, вимкнено субтитри.
3. **Chunk if needed**: якщо транскрипція перевищує ~50 К символів, розбити її на перекриваючі частини (~40 К з перекриттям 2 К) і підсумувати кожну частину перед об’єднанням.
4. **Transform** у запитаний формат виводу. Якщо користувач не вказав формат, за замовчуванням — резюме.
5. **Verify**: перечитати перетворений результат, перевірити узгодженість, правильність міток часу та повноту перед представленням.

## Error Handling

- **Transcript disabled**: повідомити користувача; запропонувати перевірити, чи доступні субтитри на сторінці відео.
- **Private/unavailable video**: передати помилку і попросити користувача перевірити URL.
- **No matching language**: повторити без `--language`, щоб отримати будь‑яку доступну транскрипцію, потім зазначити фактичну мову користувачу.
- **Dependency missing**: виконати `pip install youtube-transcript-api` і повторити.