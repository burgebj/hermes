---
title: "Memento Flashcards — система карточек с интервальным повторением"
sidebar_label: "Memento Flashcards"
description: "Система карточек с интервальным повторением"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Memento Flashcards

Система флеш‑карт с интервальным повторением. Создавай карты из фактов или текста, общайся с флеш‑картами, отвечая свободным текстом, который оценивается агентом, генерируй викторины из транскриптов YouTube, просматривай просроченные карты с адаптивным планированием и экспортируй/импортируй колоды в формате CSV.
## Метаданные навыка

| | |
|---|---|
| Источник | Необязательно — установить с помощью `hermes skills install official/productivity/memento-flashcards` |
| Путь | `optional-skills/productivity/memento-flashcards` |
| Версия | `1.0.0` |
| Автор | Memento AI |
| Лицензия | MIT |
| Платформы | macos, linux |
| Теги | `Education`, `Flashcards`, `Spaced Repetition`, `Learning`, `Quiz`, `YouTube` |
:::info
Следующее — полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции, когда навык включён.
:::

# Memento Flashcards — навык карточек с интервальным повторением
## Обзор

Memento — это локальная файловая система карточек с планированием повторения по методу интервального повторения.
Пользователи могут «общаться» со своими карточками, отвечая свободным текстом, а агент оценивает ответ и планирует следующее повторение.

Используй Memento, когда пользователь хочет:

- **Запомнить факт** — преврати любое утверждение в карточку В/О
- **Учиться с интервальным повторением** — просматривай карточки, срок которых наступил, с адаптивными интервалами и оценкой свободного текста агентом
- **Создать викторину из видео YouTube** — получи транскрипт и сгенерируй викторину из 5 вопросов
- **Управлять колодами** — организуй карточки в коллекции, экспортируй/импортируй CSV

Все данные карточек хранятся в одном JSON‑файле. Внешние API‑ключи не требуются — ты (агент) генерируешь содержимое карточек и вопросы викторины напрямую.

**Стиль ответов, видимых пользователю, для карточек Memento**
- Используй только обычный текст. Не используй форматирование Markdown в ответах пользователю.
- Делай обратную связь по обзору и викторине короткой и нейтральной. Избегай лишних похвал, подбадривания и длинных объяснений.
## Когда использовать

Используй этот **skill**, когда пользователь хочет:
- Сохранять факты в виде флеш‑карт для последующего повторения
- Просматривать карты, срок которых наступил, с помощью метода интервального повторения
- Создавать викторину из транскрипта видео на YouTube
- Импортировать, экспортировать, просматривать или удалять данные флеш‑карт

Не используй этот **skill** для общих вопросов‑ответов, помощи с кодом или задач, не связанных с памятью.
## Быстрая справка

| Намерение пользователя | Действие |
|---|---|
| «Remember that X» / «save this as a flashcard» | Сгенерировать карточку Q/A, вызвать `memento_cards.py add` |
| Отправляет факт без упоминания flashcards | Спросить «Хочешь, чтобы я сохранил это как flashcard Memento?» — создать только после подтверждения |
| «Create a flashcard» | Спросить вопрос, ответ и коллекцию; вызвать `memento_cards.py add` |
| «Review my cards» | Вызвать `memento_cards.py due`, показывать карточки по одной |
| «Quiz me on [YouTube URL]» | Вызвать `youtube_quiz.py fetch VIDEO_ID`, сгенерировать 5 вопросов, вызвать `memento_cards.py add-quiz` |
| «Export my cards» | Вызвать `memento_cards.py export --output PATH` |
| «Import cards from CSV» | Вызвать `memento_cards.py import --file PATH --collection NAME` |
| «Show my stats» | Вызвать `memento_cards.py stats` |
| «Delete a card» | Вызвать `memento_cards.py delete --id ID` |
| «Delete a collection» | Вызвать `memento_cards.py delete-collection --collection NAME` |
## Хранилище карт

Карты сохраняются в JSON‑файле по пути:

```
~/.hermes/skills/productivity/memento-flashcards/data/cards.json
```

**Никогда не редактируй этот файл вручную.** Всегда используй подкоманды `memento_cards.py`. Скрипт выполняет атомарные записи (запись во временный файл, затем переименование), чтобы избежать повреждения.

Файл создаётся автоматически при первом использовании.
## Процедура

### Создание карточек из фактов

### Правила активации

Не каждое фактическое утверждение должно становиться flashcard. Используй эту трёхуровневую проверку:

1. **Явный запрос** — пользователь упоминает «memento», «flashcard», «remember this», «save this card», «add a card» или аналогичную формулировку, явно запрашивая карточку → **создай карточку сразу**, подтверждение не требуется.
2. **Неявный запрос** — пользователь отправляет фактическое утверждение без упоминания карточек (например, «Скорость света — 299 792 км/с») → **спроси сначала**: «Хочешь, чтобы я сохранил это как карточку Memento?» Создай карточку только после подтверждения.
3. **Отсутствие запроса** — сообщение является задачей по коду, вопросом, инструкцией, обычным разговором или чем‑то, явно не предназначенным для запоминания → **не активируй этот навык**. Позволь другим навыкам или стандартному поведению обработать его.

Когда активация подтверждена (уровень 1 напрямую, уровень 2 после подтверждения), сгенерируй flashcard:

**Шаг 1:** Преобразуй утверждение в пару «вопрос/ответ». Используй внутренний формат:

```
Turn the factual statement into a front-back pair.
Return exactly two lines:
Q: <question text>
A: <answer text>

Statement: "{statement}"
```

**Правила:**
- Вопрос должен проверять запоминание ключевого факта.
- Ответ должен быть лаконичным и точным.

**Шаг 2:** Вызови скрипт для сохранения карточки:

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py add \
  --question "What year did World War 2 end?" \
  --answer "1945" \
  --collection "History"
```

Если пользователь не указал коллекцию, используй `"General"` по умолчанию.

Скрипт выводит JSON‑подтверждение о созданной карточке.

### Ручное создание карточек

Когда пользователь явно просит создать flashcard, спроси у него:
1. Вопрос (лицевая сторона карточки)
2. Ответ (обратная сторона)
3. Название коллекции (необязательно — по умолчанию `"General"`)

Затем вызови `memento_cards.py add`, как указано выше.

### Обзор карточек, срок которых наступил

Когда пользователь хочет провести обзор, получи все карточки, срок которых наступил:

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py due
```

Скрипт возвращает массив JSON карточек, где `next_review_at <= now`. Если нужен фильтр по коллекции:

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py due --collection "History"
```

**Процесс обзора (оценка свободным текстом):**

Ниже пример точного шаблона взаимодействия, которому необходимо следовать. Пользователь отвечает, ты оцениваешь, сообщаешь правильный ответ, затем ставишь оценку карточке.

**Пример взаимодействия:**

> **Agent:** В каком году упал Берлинский стен?
> **User:** 1991
> **Agent:** Не совсем. Берлинская стена упала в 1989. Следующий обзор — завтра.
> *(агент вызывает: `memento_cards.py rate --id ABC --rating hard --user-answer "1991"`)*
> Следующий вопрос: Кто был первым человеком, ступившим на Луну?

**Правила:**

1. Показывай только вопрос. Жди ответа пользователя.
2. После получения ответа сравни его с ожидаемым и оцени:
   - **correct** → пользователь правильно воспроизвёл ключевой факт (даже если формулировка отличается)
   - **partial** → близко, но не хватает основной детали
   - **incorrect** → неверно или не по теме
3. **Обязательно сообщи пользователю правильный ответ и результат оценки.** Делай это коротко в виде простого текста. Формат:
   - correct: `Correct. Answer: {answer}. Next review in 7 days.`
   - partial: `Close. Answer: {answer}. {what they missed}. Next review in 3 days.`
   - incorrect: `Not quite. Answer: {answer}. Next review tomorrow.`
4. Затем вызови команду `rate`: correct → `easy`, partial → `good`, incorrect → `hard`.
5. После этого показывай следующий вопрос.

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py rate \
  --id CARD_ID --rating easy --user-answer "what the user said"
```

**Никогда не пропускай шаг 3.** Пользователь всегда должен увидеть правильный ответ и обратную связь перед переходом к следующему вопросу.

Если карточек, срок которых наступил, нет, скажи: «No cards due for review right now. Check back later!»

**Переопределение «retire»:** В любой момент пользователь может сказать «retire this card», чтобы навсегда удалить её из обзоров. Используй `--rating retire`.

### Алгоритм интервального повторения

Оценка определяет следующий интервал обзора:

| Оценка | Интервал | ease_streak | Изменение статуса |
|---|---|---|---|
| **hard** | +1 день | сброс до 0 | остаётся в learning |
| **good** | +3 дня | сброс до 0 | остаётся в learning |
| **easy** | +7 дней | +1 | при `ease_streak >= 3` → retired |
| **retire** | навсегда | сброс до 0 | → retired |

- **learning**: карточка активно участвует в обзорах
- **retired**: карточка больше не появляется в обзорах (пользователь её освоил или вручную удалил)
- Три последовательные оценки «easy» автоматически переводят карточку в статус retired.

### Генерация викторины из YouTube

Когда пользователь присылает URL YouTube и просит викторину:

**Шаг 1:** Выдели ID видео из URL (например, `dQw4w9WgXcQ` из `https://www.youtube.com/watch?v=dQw4w9WgXcQ`).

**Шаг 2:** Получи транскрипт:

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/youtube_quiz.py fetch VIDEO_ID
```

Скрипт возвращает `{"title": "...", "transcript": "..."}` или ошибку.

Если скрипт сообщает `missing_dependency`, скажи пользователю установить требуемый пакет:

```bash
pip install youtube-transcript-api
```

**Шаг 3:** Сгенерируй 5 вопросов викторины из транскрипта. Правила:

```
You are creating a 5-question quiz for a podcast episode.
Return ONLY a JSON array with exactly 5 objects.
Each object must contain keys 'question' and 'answer'.

Selection criteria:
- Prioritize important, surprising, or foundational facts.
- Skip filler, obvious details, and facts that require heavy context.
- Never return true/false questions.
- Never ask only for a date.

Question rules:
- Each question must test exactly one discrete fact.
- Use clear, unambiguous wording.
- Prefer What, Who, How many, Which.
- Avoid open-ended Describe or Explain prompts.

Answer rules:
- Each answer must be under 240 characters.
- Lead with the answer itself, not preamble.
- Add only minimal clarifying detail if needed.
```

Используй первые 15 000 символов транскрипта как контекст. Генерировать вопросы должен сам LLM.

**Шаг 4:** Проверь, что вывод — корректный JSON с ровно 5 элементами, каждый из которых содержит непустые строки `question` и `answer`. При провале валидации повтори попытку один раз.

**Шаг 5:** Сохрани карточки викторины:

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py add-quiz \
  --video-id "VIDEO_ID" \
  --questions '[{"question":"...","answer":"..."},...]' \
  --collection "Quiz - Episode Title"
```

Скрипт дедуплицирует по `video_id` — если карточки для этого видео уже существуют, он пропускает создание и сообщает о существующих карточках.

**Шаг 6:** Представляй вопросы по одному, используя тот же процесс свободного текстового оценивания:
1. Показывай «Question 1/5: …» и жди ответа пользователя. Не раскрывай ответ и не давай подсказок.
2. Жди, пока пользователь ответит своими словами.
3. Оцени его ответ согласно правилам из раздела «Обзор карточек, срок которых наступил».
4. **ВАЖНО:** Сначала дай пользователю обратную связь (оценку, правильный ответ и срок следующего обзора). Не переходи к следующему вопросу без этого. Пример: `Not quite. Answer: {answer}. Next review tomorrow.`
5. После обратной связи вызови команду `rate`, а затем покажи следующий вопрос в том же сообщении:
```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py rate \
  --id CARD_ID --rating easy --user-answer "what the user said"
```
6. Повторяй. Каждый ответ обязан получать видимую обратную связь перед следующим вопросом.

### Экспорт/Импорт CSV

**Экспорт:**
```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py export \
  --output ~/flashcards.csv
```

Создаёт CSV из 3 столбцов: `question,answer,collection` (без заголовка).

**Импорт:**
```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py import \
  --file ~/flashcards.csv \
  --collection "Imported"
```

Читает CSV со столбцами: вопрос, ответ и опционально коллекция (третья колонка). Если колонка коллекции отсутствует, используется аргумент `--collection`.

### Статистика

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py stats
```

Возвращает JSON с полями:
- `total` — общее количество карточек
- `learning` — карточки в активном обороте
- `retired` — освоенные карточки
- `due_now` — карточки, срок которых наступил сейчас
- `collections` — разбивка по названиям коллекций
## Подводные камни

- **Never edit `cards.json` directly** — никогда не редактируй `cards.json` вручную, а всегда используй подкоманды скрипта, чтобы избежать порчи данных
- **Transcript failures** — у некоторых видео на YouTube нет английской расшифровки или она отключена; сообщи пользователю и предложи другое видео
- **Optional dependency** — `youtube_quiz.py` требует `youtube-transcript-api`; если она отсутствует, скажи пользователю выполнить `pip install youtube-transcript-api`
- **Large imports** — импорт CSV с тысячами строк работает нормально, однако JSON‑вывод может быть громоздким; предоставь пользователю сводку результата
- **Video ID extraction** — поддерживай оба формата URL: `youtube.com/watch?v=ID` и `youtu.be/ID`
## Проверка

Проверь вспомогательные скрипты напрямую:

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py stats
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py add --question "Capital of France?" --answer "Paris" --collection "General"
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py due
```

Если ты тестируешь из checkout репозитория, запусти:

```bash
pytest tests/skills/test_memento_cards.py tests/skills/test_youtube_quiz.py -q
```

Проверка на уровне агента:
- Запусти обзор и убедись, что обратная связь представлена простым текстом, кратка и всегда содержит правильный ответ перед следующей карточкой
- Запусти поток викторины YouTube и убедись, что каждый ответ получает видимую обратную связь перед следующим вопросом