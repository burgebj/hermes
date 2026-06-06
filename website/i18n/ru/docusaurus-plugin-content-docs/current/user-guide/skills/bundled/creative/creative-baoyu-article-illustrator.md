---
title: "Baoyu Article Illustrator — Иллюстрации статей: тип × стиль × согласованность палитры"
sidebar_label: "Baoyu Article Illustrator"
description: "Иллюстрации статьи: тип × стиль × согласованность палитры"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Иллюстратор статей Baoyu

Иллюстрации статей: тип × стиль × согласованность палитры.
## Метаданные навыка

| | |
|---|---|
| Source | Встроенный (устанавливается по умолчанию) |
| Path | `skills/creative/baoyu-article-illustrator` |
| Version | `1.57.0` |
| Author | 宝玉 (JimLiu) |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `article-illustration`, `creative`, `image-generation` |
:::info
Следующее — полное определение **skill**, которое Hermes загружает, когда этот **skill** активируется. Это то, что агент видит как инструкции, когда **skill** активен.
:::

# Иллюстратор статей

Адаптировано из [baoyu-article-illustrator](https://github.com/JimLiu/baoyu-skills) для экосистемы инструментов Hermes Agent.

Анализируй статьи, определяй позиции иллюстраций, генерируй изображения с согласованностью **Type × Style × Palette**.
## Когда использовать

Запусти этот skill, когда пользователь просит проиллюстрировать статью, добавить изображения к статье, сгенерировать иллюстрации для контента или использует фразы вроде «为文章配图», «illustrate article» или «add images». Пользователь предоставляет статью (путь к файлу или вставленный текст) и по желанию указывает тип, стиль, палитру или плотность.
## Три измерения

| Измерение | Параметры | Примеры |
|-----------|-----------|---------|
| **Тип** | Структура информации | infographic, scene, flowchart, comparison, framework, timeline |
| **Стиль** | Подход к рендерингу | notion, warm, minimal, blueprint, watercolor, elegant |
| **Палитра** | Цветовая схема (необязательно) | macaron, warm, neon — переопределяет цвета по умолчанию стиля |

Комбинируй свободно: `type=infographic, style=vector-illustration, palette=macaron`.

Или используй предустановки: `edu-visual` → type + style + palette за один раз. See [style-presets.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-article-illustrator/references/style-presets.md).
## Типы

| Тип | Наилучшее применение |
|------|----------------------|
| `infographic` | Данные, метрики, технические |
| `scene` | Нарративы, эмоциональные |
| `flowchart` | Процессы, рабочие процессы |
| `comparison` | Сравнение, варианты |
| `framework` | Модели, архитектура |
| `timeline` | История, эволюция |
## Стили

См. [references/styles.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-article-illustrator/references/styles.md) для основных стилей, полной галереи и совместимости Type × Style.
## Структура вывода

<!-- ascii-guard-ignore -->
```
{output-dir}/
├── source-{slug}.{ext}    # Only for pasted content
├── outline.md
├── prompts/
│   └── NN-{type}-{slug}.md
└── NN-{type}-{slug}.png
```
<!-- ascii-guard-ignore-end -->

**Каталог вывода по умолчанию**:

| Входные данные | Каталог вывода | Путь вставки Markdown |
|----------------|----------------|-----------------------|
| Путь к файлу статьи | `{article-dir}/imgs/` | `imgs/NN-{type}-{slug}.png` |
| Вставленное содержимое | `illustrations/{topic-slug}/` (cwd) | `illustrations/{topic-slug}/NN-{type}-{slug}.png` |

Если пользователь запрашивает другой макет (например, изображения рядом со статьей или подкаталог `illustrations/`), следует выполнить запрос.

**Slug**: 2‑4 слова, kebab-case. **Конфликт**: добавить `-YYYYMMDD-HHMMSS`.
## Основные принципы

- **Визуализируй концепции, а не метафоры** — если статья использует метафору (например, «电锯切西瓜»), иллюстрируй лежащую в основе концепцию, а не буквальное изображение.
- **Метки используют данные из статьи** — реальные числа, термины и цитаты из статьи, а не общие заполнители.
- **Файлы запросов — записи воспроизводимости** — каждый иллюстративный материал должен иметь сохранённый файл запроса в `prompts/` до того, как будет сгенерировано любое изображение.
- **Удаляй конфиденциальные данные** — проверяй исходный контент на наличие API‑ключей, токенов или учётных данных перед записью чего‑либо на диск.
## Рабочий процесс

```
- [ ] Step 1: Detect reference images (if provided)
- [ ] Step 2: Analyze content
- [ ] Step 3: Confirm settings (clarify tool, one question at a time)
- [ ] Step 4: Generate outline
- [ ] Step 5: Generate prompts
- [ ] Step 6: Generate images (image_generate)
- [ ] Step 7: Finalize
```

### Шаг 1: Обнаружение референс‑изображений

Если пользователь предоставляет референс‑изображения (пути, вставленные inline, вложения или URL):

1. Для каждой ссылки вызвать `vision_analyze` с путём/URL и вопросом о стиле, палитре, композиции и предмете. Сохранить полученное описание в `{output-dir}/references/NN-ref-{slug}.md` через `write_file`.
2. **Не** пытайтесь копировать бинарный файл через `write_file` / `read_file` — они работают только с текстом. Если нужна локальная копия для записи, используйте `terminal` (`cp "$src" "{output-dir}/references/NN-ref-{slug}.{ext}"`). Сам навык никогда не читает бинарный файл; он работает с описанием, полученным от vision.
3. Поскольку `image_generate` не принимает изображения, именно описание vision будет встроено в подсказки на Шаге 5.

Полные процедуры: [references/workflow.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-article-illustrator/references/workflow.md#step-1-detect-reference-images).

### Шаг 2: Анализ

| Анализ | Вывод |
|----------|--------|
| Тип контента | Технический / Учебный / Методологический / Нарративный |
| Цель | информация / визуализация / воображение |
| Основные аргументы | 2‑5 ключевых пунктов |
| Позиции | Где иллюстрации добавляют ценность |

Прочитай источник (путь к файлу → `read_file` или вставленный текст) и запиши анализ в `{output-dir}/analysis.md` с помощью `write_file`.

Полные процедуры: [references/workflow.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-article-illustrator/references/workflow.md#step-2-analyze).

### Шаг 3: Подтверждение настроек

Используй инструмент `clarify`. Поскольку `clarify` обрабатывает один вопрос за раз, задавай сначала самый важный вопрос. Пропускай любой вопрос, если ответ уже присутствует в запросе пользователя.

| Порядок | Вопрос | Варианты |
|-------|----------|---------|
| Q1 | **Пресет или тип** | [Recommended preset], [alt preset] или вручную: инфографика, сцена, блок‑схема, сравнение, фреймворк, таймлайн, смешанный |
| Q2 | **Плотность** | минимальная (1‑2), сбалансированная (3‑5), по‑разделам (Recommended), насыщенная (6+) |
| Q3 | **Стиль** *(пропустить, если выбран пресет в Q1)* | [Recommended], minimal-flat, sci‑fi, hand‑drawn, editorial, scene, poster |
| Q4 | **Палитра** *(опционально)* | Default (цвета стиля), macaron, warm, neon |
| Q5 | **Язык** *(только если язык статьи неоднозначен)* | язык статьи / язык пользователя |

Не задавай более 2‑3 вопросов `clarify` подряд. Если пользователь уже указал эти параметры в запросе, полностью пропусти их.

Полные процедуры: [references/workflow.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-article-illustrator/references/workflow.md#step-3-confirm-settings).

### Шаг 4: Генерация плана → `outline.md`

Сохрани `{output-dir}/outline.md` через `write_file` с фронт‑маттером (type, density, style, palette, image_count) и одной записью на каждую иллюстрацию:

```yaml
## Illustration 1
**Position**: [section/paragraph]
**Purpose**: [why]
**Visual Content**: [what to show]
**Filename**: 01-infographic-concept-name.png
```

Полный шаблон: [references/workflow.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-article-illustrator/references/workflow.md#step-4-generate-outline).

### Шаг 5: Генерация подсказок

**БЛОКИРУЮЩЕЕ**: Каждая иллюстрация должна иметь сохранённый файл подсказки до генерации любого изображения — файл подсказки служит записью воспроизводимости.

Для каждой иллюстрации:

1. Создай файл подсказки согласно [references/prompt-construction.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-article-illustrator/references/prompt-construction.md).
2. Сохрани в `{output-dir}/prompts/NN-{type}-{slug}.md` через `write_file` с YAML‑фронт‑маттером.
3. Подсказки ДОЛЖНЫ использовать шаблоны, специфичные для типа, с структурированными секциями (ZONES / LABELS / COLORS / STYLE / ASPECT).
4. LABELS ДОЛЖНЫ включать данные из статьи: реальные цифры, термины, метрики, цитаты.
5. Обрабатывай референсы (`direct` / `style` / `palette`) согласно фронт‑маттеру подсказки — для использования `direct` вставляй текстовое описание референса в подсказку (поскольку `image_generate` не принимает изображения).

### Шаг 6: Генерация изображений

Для каждого файла подсказки:

1. Вызови `image_generate(prompt=..., aspect_ratio=...)`. `image_generate` возвращает JSON‑результат с URL изображения; он НЕ записывает файл на диск и НЕ принимает путь вывода.
2. Преобразуй `ASPECT` подсказки в перечисление `image_generate`: `16:9` → `landscape`, `9:16` → `portrait`, `1:1` → `square`. Пользовательские соотношения — к ближайшему именованному аспекту.
3. Скачай полученный URL в `{output-dir}/NN-{type}-{slug}.png` через `terminal` (например, `curl -sSL -o "{output-dir}/NN-{type}-{slug}.png" "{url}"`).
4. При ошибке генерации выполнить автоматический повтор один раз.

Примечание: бекенд генерации изображений настраивается пользователем (по умолчанию: FAL FLUX 2 Klein 9B) и НЕ выбирается агентом через `image_generate`. Не указывай названия моделей в подсказках в надежде, что они будут использованы.

### Шаг 7: Финализация

Вставь `![description](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-article-illustrator/{relative-path}/NN-{type}-{slug}.png)` после соответствующего абзаца. Alt‑текст: краткое описание на языке статьи.

Отчёт:

```
Article Illustration Complete!
Article: [path] | Type: [type] | Density: [level] | Style: [style] | Palette: [palette or default]
Images: X/N generated
```
## Модификация

| Действие | Шаги |
|----------|------|
| Редактировать | Обновить подсказку → Перегенерировать → Обновить ссылку |
| Добавить | Позиция → Подсказка → Сгенерировать → Обновить план → Вставить |
| Удалить | Удалить файлы → Удалить ссылку → Обновить план |
## Ссылки

| File | Содержание |
|------|------------|
| [references/workflow.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-article-illustrator/references/workflow.md) | Подробные процедуры |
| [references/usage.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-article-illustrator/references/usage.md) | Примеры вызова |
| [references/styles.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-article-illustrator/references/styles.md) | Галерея стилей + галерея палитр |
| [references/style-presets.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-article-illustrator/references/style-presets.md) | Сокращения пресетов (тип + стиль + палитра) |
| [references/prompt-construction.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-article-illustrator/references/prompt-construction.md) | Шаблоны подсказок |
## Подводные камни

1. **Целостность данных имеет первостепенное значение** — никогда не суммируй, не перефразируй и не изменяй исходные статистические данные. «73% increase» остаётся «73% increase».
2. **Удаляй секреты** — просканируй исходный контент на наличие API‑ключей, токенов или учётных данных перед включением в любой выводимый файл.
3. **Не иллюстрируй метафоры буквально** — визуализируй заложенную концепцию.
4. **Prompt‑файлы обязательны** — без сохранённого prompt‑файла нельзя генерировать изображения. Этот файл позволяет позже регенерировать запрос или переключить бэкенд.
5. **`image_generate` — соотношения сторон** — инструмент поддерживает `landscape`, `portrait` и `square`. Пользовательские соотношения сопоставляются с ближайшим вариантом.
6. **`image_generate` возвращает URL, а не локальный файл** — всегда скачивай его через `terminal` (`curl`) перед тем, как вставлять локальные пути к изображениям в статью.
7. **Выбор бэкенда не осуществляется агентом** — `image_generate` использует модель, которую пользователь настроил (по умолчанию: FAL FLUX 2 Klein 9B). Не пишите `"use <model> to generate this"` в prompt‑файлах, ожидая, что это будет перенаправлено.