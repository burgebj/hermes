---
title: "Memento Flashcards — система карток із інтервальним повторенням"
sidebar_label: "Memento Flashcards"
description: "Система карток зі spaced-repetition"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Memento Flashcards

Система флеш‑карт із інтервальним повторенням. Створюй картки з фактів або тексту, спілкуйся з флеш‑картами за допомогою вільнотекстових відповідей, оцінених агентом, генеруй вікторини з транскриптів YouTube, переглядай заплановані картки за адаптивним розкладом і експортуй/імпортуй колоди у форматі CSV.
## Метадані навички

| | |
|---|---|
| Джерело | Опційно — встановити за допомогою `hermes skills install official/productivity/memento-flashcards` |
| Шлях | `optional-skills/productivity/memento-flashcards` |
| Версія | `1.0.0` |
| Автор | Memento AI |
| Ліцензія | MIT |
| Платформи | macos, linux |
| Теги | `Education`, `Flashcards`, `Spaced Repetition`, `Learning`, `Quiz`, `YouTube` |
:::info
Нижче наведено повне визначення skill, яке Hermes завантажує під час його активації. Це інструкції, які бачить агент, коли skill активний.
:::

# Memento Flashcards — Спейcед‑репетиція карток
## Огляд

Memento надає тобі локальну, файлову систему флешкарток зі спейсед‑репетіцією.
Користувачі можуть спілкуватися зі своїми флешкартками, відповідаючи вільним текстом, а агент оцінює відповідь перед плануванням наступного повторення.
Використовуй його, коли користувач хоче:

- **Запам’ятати факт** — перетвори будь‑яке твердження у флешкарту Q/A
- **Навчатися за допомогою спейсед‑репетіції** — переглядай картки, що підлягають повторенню, з адаптивними інтервалами та оцінкою вільного тексту агентом
- **Створювати вікторину за відео YouTube** — отримай транскрипт і згенеруй вікторину з 5 питань
- **Керувати колодами** — організовуй картки в колекції, експортуй/імпортуй CSV

Всі дані карток зберігаються в одному JSON‑файлі. Жодних зовнішніх API‑ключів не потрібно — ти (агент) генеруєш вміст флешкарток і питання вікторини безпосередньо.

**Стиль відповіді, орієнтований на користувача, для Memento Flashcards:**
- Використовуй лише простий текст. Не використовуйте форматування Markdown у відповідях користувачеві.
- Тримай відгуки про перегляд і вікторину короткими та нейтральними. Уникай зайвих похвал, підбадьорень або довгих пояснень.
## Коли використовувати

Використовуй цей **skill**, коли користувач хоче:
- Зберігати факти у вигляді флеш‑карток для подальшого перегляду
- Переглядати картки, які треба повторити, за допомогою інтервального повторення
- Генерувати вікторину за транскриптом відео з YouTube
- Імпорт, експорт, перегляд або видалення даних флеш‑карток

Не використовуйте цей **skill** для загальних питань‑відповідей, допомоги з кодом або завдань, не пов’язаних з пам’яттю.
## Швидке посилання

| Намір користувача | Дія |
|---|---|
| «Запам’ятати X» / «зберегти це як флешкарту» | Згенерувати картку Q/A, викликати `memento_cards.py add` |
| Надсилає факт без згадки про флешкарти | Запитати «Хочеш, щоб я зберіг це як флешкарту Memento?» — створювати лише після підтвердження |
| «Створити флешкарту» | Запитати питання, відповідь, колекцію; викликати `memento_cards.py add` |
| «Переглянути мої картки» | Викликати `memento_cards.py due`, показувати картки по одній |
| «Задай мені питання по [YouTube URL]» | Викликати `youtube_quiz.py fetch VIDEO_ID`, згенерувати 5 питань, викликати `memento_cards.py add-quiz` |
| «Експортувати мої картки» | Викликати `memento_cards.py export --output PATH` |
| «Імпортувати картки з CSV» | Викликати `memento_cards.py import --file PATH --collection NAME` |
| «Показати мою статистику» | Викликати `memento_cards.py stats` |
| «Видалити картку» | Викликати `memento_cards.py delete --id ID` |
| «Видалити колекцію» | Викликати `memento_cards.py delete-collection --collection NAME` |
## Сховище карток

Картки зберігаються у файлі JSON за шляхом:

```
~/.hermes/skills/productivity/memento-flashcards/data/cards.json
```

**Ніколи не редагуй цей файл безпосередньо.** Завжди використовуйте підкоманди `memento_cards.py`. Скрипт виконує атомарні записи (запис у тимчасовий файл, потім перейменування), щоб запобігти пошкодженню.

Файл створюється автоматично при першому використанні.
## Процедура

### Створення карток із фактів

### Правила активації

Не кожне фактичне твердження має ставати флеш‑карткою. Використовуй цю трирівневу перевірку:

1. **Явний намір** — користувач згадує «memento», «flashcard», «remember this», «save this card», «add a card» або подібну формулювання, що явно запитує флеш‑картку → **створи картку одразу**, підтвердження не потрібне.
2. **Неявний намір** — користувач надсилає фактичне твердження без згадки про картки (наприклад «Швидкість світла — 299 792 км/с») → **спершу запитай**: «Хочеш, щоб я зберіг це як Memento flashcard?» Створи картку лише після підтвердження користувача.
3. **Відсутність наміру** — повідомлення є завданням коду, питанням, інструкцією, звичайною розмовою або будь‑що, що явно не є фактом для запам’ятовування → **не активуй цей навик**. Нехай інші навички або стандартна поведінка оброблять його.

Коли активація підтверджена (рівень 1 одразу, рівень 2 після підтвердження), згенеруй флеш‑картку:

**Крок 1:** Перетвори твердження у пару П/В. Використовуй внутрішній формат:

```
Turn the factual statement into a front-back pair.
Return exactly two lines:
Q: <question text>
A: <answer text>

Statement: "{statement}"
```

**Правила:**
- Питання має перевіряти запам’ятовування ключового факту.
- Відповідь має бути стислою та прямою.

**Крок 2:** Виклич скрипт для збереження картки:

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py add \
  --question "What year did World War 2 end?" \
  --answer "1945" \
  --collection "History"
```

Якщо користувач не вказав колекцію, використай `"General"` за замовчуванням.

Скрипт виводить JSON, що підтверджує створену картку.

### Ручне створення карток

Коли користувач явно просить створити флеш‑картку, запитай у нього:
1. Питання (лице картки)
2. Відповідь (зворотний бік)
3. Назву колекції (необов’язково — за замовчуванням `"General"`)

Потім виклич `memento_cards.py add` як вище.

### Огляд карток, що підлягають повторенню

Коли користувач хоче переглянути картки, отримай усі картки, що підлягають повторенню:

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py due
```

Скрипт повертає JSON‑масив карток, у яких `next_review_at <= now`. Якщо потрібен фільтр за колекцією:

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py due --collection "History"
```

**Процес огляду (вільний текст для оцінки):**

Нижче наведено точний шаблон взаємодії, якого треба дотримуватись. Користувач відповідає, ти оцінюєш, повідомляєш правильну відповідь, а потім оцінюєш картку.

**Приклад взаємодії:**

> **Agent:** Якого року впав Берлінський мур?
>
> **User:** 1991
>
> **Agent:** Не зовсім. Берлінський мур впав у 1989. Наступний огляд — завтра.
> *(агент викликає: `memento_cards.py rate --id ABC --rating hard --user-answer "1991"`)*
>
> Наступне питання: Хто був першим, хто ступив на місяць?

**Правила:**

1. Показуй лише питання. Чекай на відповідь користувача.
2. Після отримання відповіді порівняй її з очікуваною і оцініть:
   - **correct** → користувач правильно назвав ключовий факт (навіть іншими словами)
   - **partial** → на правильному шляху, але бракує суті
   - **incorrect** → помилково або не по темі
3. **Ти ПОВИНЕН повідомити користувачу правильну відповідь і результат оцінки.** Коротко, у простому тексті. Формат:
   - correct: `Correct. Answer: {answer}. Next review in 7 days.`
   - partial: `Close. Answer: {answer}. {what they missed}. Next review in 3 days.`
   - incorrect: `Not quite. Answer: {answer}. Next review tomorrow.`
4. Потім виклич команду `rate`: correct → `easy`, partial → `good`, incorrect → `hard`.
5. Після цього покажи наступне питання.

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py rate \
  --id CARD_ID --rating easy --user-answer "what the user said"
```

**Ніколи не пропускай крок 3.** Користувач завжди має бачити правильну відповідь і зворотний зв’язок перед наступним питанням.

Якщо немає карток, що підлягають повторенню, скажи: «No cards due for review right now. Check back later!»

**Перевизначення «retire»:** У будь‑який момент користувач може сказати «retire this card», щоб назавжди вилучити її з повторень. Використай `--rating retire`.

### Алгоритм просторового повторення

Оцінка визначає інтервал наступного повторення:

| Оцінка | Інтервал | ease_streak | Зміна статусу |
|---|---|---|---|
| **hard** | +1 день | скидає до 0 | залишається в learning |
| **good** | +3 дні | скидає до 0 | залишається в learning |
| **easy** | +7 днів | +1 | якщо `ease_streak >= 3` → retired |
| **retire** | назавжди | скидає до 0 | → retired |

- **learning**: картка активно в обігу
- **retired**: картка більше не з’являється в оглядах (користувач її освоїв або вручну вилучив)
- Три послідовні оцінки «easy» автоматично переводять картку у статус *retired*.

### Генерація вікторини з YouTube

Коли користувач надсилає URL YouTube і просить вікторину:

**Крок 1:** Витягни ID відео з URL (наприклад `dQw4w9WgXcQ` з `https://www.youtube.com/watch?v=dQw4w9WgXcQ`).

**Крок 2:** Отримай транскрипт:

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/youtube_quiz.py fetch VIDEO_ID
```

Скрипт повертає `{"title": "...", "transcript": "..."}` або помилку.

Якщо скрипт повідомляє `missing_dependency`, скажи користувачу встановити його:

```bash
pip install youtube-transcript-api
```

**Крок 3:** Згенеруй 5 питань вікторини з транскрипту. Використовуй правила:

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

Використовуй перші 15 000 символів транскрипту як контекст. Питання генеруєш сам (ти — LLM).

**Крок 4:** Перевір, що результат — валідний JSON з точно 5 елементами, у кожному з яких непорожні рядки `question` і `answer`. Якщо валідація не проходить, спробуй ще раз.

**Крок 5:** Збережи картки вікторини:

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py add-quiz \
  --video-id "VIDEO_ID" \
  --questions '[{"question":"...","answer":"..."},...]' \
  --collection "Quiz - Episode Title"
```

Скрипт дедуплікує за `video_id` — якщо картки для цього відео вже існують, створення пропускається і скрипт повідомляє про існуючі картки.

**Крок 6:** Представляй питання одне за одним, використовуючи той самий процес вільного тексту для оцінки:
1. Показуй «Question 1/5: …» і чекай відповіді. Не розкривай відповідь і не давай підказок.
2. Чекай, доки користувач відповість своїми словами.
3. Оціни відповідь згідно з правилами з розділу «Огляд карток, що підлягають повторенню».
4. **ВАЖЛИВО:** Спершу дай користувачу зворотний зв’язок. Приклад: `Not quite. Answer: {answer}. Next review tomorrow.`
5. **Після зворотного зв’язку** виклич команду `rate`, а потім у тому ж повідомленні покажи наступне питання:
```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py rate \
  --id CARD_ID --rating easy --user-answer "what the user said"
```
6. Повтори. Кожна відповідь МАЄ отримати видимий зворотний зв’язок перед наступним питанням.

### Експорт/Імпорт CSV

**Експорт:**
```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py export \
  --output ~/flashcards.csv
```

Створює CSV з 3 колонками: `question,answer,collection` (без заголовка).

**Імпорт:**
```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py import \
  --file ~/flashcards.csv \
  --collection "Imported"
```

Читає CSV з колонками: питання, відповідь і, за потреби, колекція (третя колонка). Якщо колонка колекції відсутня, використовується аргумент `--collection`.

### Статистика

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py stats
```

Повертає JSON з полями:
- `total` — загальна кількість карток
- `learning` — картки в активному обігу
- `retired` — освоєні картки
- `due_now` — картки, що підлягають огляду зараз
- `collections` — розподіл за назвами колекцій
## Підводні камені

- **Ніколи не редагуй `cards.json` безпосередньо** — завжди використовуй підкоманди скрипту, щоб уникнути пошкодження файлу
- **Помилки транскрипції** — у деяких відео на YouTube немає англійської транскрипції або вона вимкнена; повідом користувача і запропонуй інше відео
- **Необов’язкова залежність** — `youtube_quiz.py` потребує `youtube-transcript-api`; якщо вона відсутня, скажи користувачеві виконати `pip install youtube-transcript-api`
- **Великі імпорти** — імпорт CSV з тисячами рядків працює коректно, проте JSON‑вивід може бути надмірно деталізованим; підсумуй результат для користувача
- **Видобування ID відео** — підтримуй формати URL `youtube.com/watch?v=ID` та `youtu.be/ID`
## Перевірка

Перевір допоміжні скрипти безпосередньо:

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py stats
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py add --question "Capital of France?" --answer "Paris" --collection "General"
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py due
```

Якщо тестуєш з копії репозиторію, запусти:

```bash
pytest tests/skills/test_memento_cards.py tests/skills/test_youtube_quiz.py -q
```

Перевірка на рівні агента:
- Запусти огляд і переконайся, що відгук — простий текст, короткий і завжди містить правильну відповідь перед наступною картою
- Запусти потік вікторини YouTube і переконайся, що кожна відповідь отримує видимий відгук перед наступним питанням