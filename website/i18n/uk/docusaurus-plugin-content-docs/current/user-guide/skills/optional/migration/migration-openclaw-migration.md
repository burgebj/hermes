---
title: "Міграція Openclaw — Перенести налаштування користувача OpenClaw у Hermes Agent"
sidebar_label: "Openclaw Migration"
description: "Перенести налаштування користувача OpenClaw у Hermes Agent"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Міграція Openclaw

Перенеси налаштування користувача OpenClaw у Hermes Agent. Імпортує сумісні з Hermes пам’яті, `SOUL.md`, списки дозволених команд, навички користувача та вибрані активи робочого простору з `~/.openclaw`, а потім повідомляє точно, що не вдалося перенести і чому.
## Метадані навички

| | |
|---|---|
| Джерело | Необов’язково — встановити за допомогою `hermes skills install official/migration/openclaw-migration` |
| Шлях | `optional-skills/migration/openclaw-migration` |
| Версія | `1.0.0` |
| Автор | Hermes Agent (Nous Research) |
| Ліцензія | MIT |
| Платформи | linux, macos, windows |
| Теги | `Migration`, `OpenClaw`, `Hermes`, `Memory`, `Persona`, `Import` |
| Пов’язані навички | [`hermes-agent`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-hermes-agent) |
:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Міграція OpenClaw → Hermes

Використовуй цей **skill**, коли користувач хоче перенести свої налаштування OpenClaw у Hermes Agent з мінімальними ручними діями.
## CLI Command

Для швидкої, неінтерактивної міграції використай вбудовану CLI‑команду:

```bash
hermes claw migrate              # Full interactive migration
hermes claw migrate --dry-run    # Preview what would be migrated
hermes claw migrate --preset user-data   # Migrate without secrets
hermes claw migrate --overwrite  # Overwrite existing conflicts
hermes claw migrate --source /custom/path/.openclaw  # Custom source
```

CLI‑команда виконує той самий скрипт міграції, який описано нижче. Використовуй цей **skill** (через агента), коли потрібна інтерактивна, керована міграція з попереднім переглядом у режимі dry‑run та розв’язанням конфліктів по‑елементно.

**First-time setup:** Майстер `hermes setup` автоматично виявляє `~/.openclaw` і пропонує міграцію перед початком налаштування.
## Що робить цей skill

Він використовує `scripts/openclaw_to_hermes.py` для:

- імпорту `SOUL.md` у домашню директорію Hermes як `SOUL.md`
- перетворення OpenClaw `MEMORY.md` та `USER.md` у записи пам’яті Hermes
- об’єднання шаблонів схвалення команд OpenClaw у `command_allowlist` Hermes
- міграції сумісних налаштувань обміну повідомленнями Hermes, таких як `TELEGRAM_ALLOWED_USERS` та `MESSAGING_CWD`
- копіювання навичок OpenClaw у `~/.hermes/skills/openclaw-imports/`
- за потреби копіювання файлу інструкцій робочого простору OpenClaw у вибраний робочий простір Hermes
- відображення сумісних ресурсів робочого простору, таких як `workspace/tts/`, у `~/.hermes/tts/`
- архівація несекретних документів, які не мають прямого призначення в Hermes
- створення структурованого звіту зі списком перенесених елементів, конфліктів, пропущених елементів та причин
## Розв’язання шляху

Скрипт‑помічник знаходиться в цьому каталозі **skill** за адресою:

- `scripts/openclaw_to_hermes.py`

Коли ця **skill** встановлюється з Skills Hub, типове розташування таке:

- `~/.hermes/skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py`

Не варто вгадувати коротший шлях типу `~/.hermes/skills/openclaw-migration/...`.

Перед запуском помічника:

1. Віддавай перевагу встановленому шляху у `~/.hermes/skills/migration/openclaw-migration/`.
2. Якщо цей шлях не працює, перевір каталог встановленої **skill** і визначи скрипт відносно встановленого `SKILL.md`.
3. Використовуй `find` лише як запасний варіант, якщо встановлене розташування відсутнє або **skill** була переміщена вручну.
4. При виклику інструменту терміналу не передавай `workdir: "~"`. Використовуй абсолютний каталог, наприклад домашній каталог користувача, або просто не вказуй `workdir`.

З параметром `--migrate-secrets` також буде імпортовано невеликий дозволений набір сумісних з Hermes секретів, наразі:

- `TELEGRAM_BOT_TOKEN`
## Типовий робочий процес

1. Спочатку виконати сухий запуск.
2. Представити простий підсумок того, що можна перенести, чого не можна перенести та що буде заархівовано.
3. Якщо інструмент `clarify` доступний, використати його для рішень користувача замість запиту вільної форми відповіді.
4. Якщо під час сухого запуску виявлені конфлікти каталогів імпортованих **skill**, запитати, як їх обробити перед виконанням.
5. Запитати у користувача вибір між двома підтримуваними режимами міграції перед виконанням.
6. Запитати шлях до цільового **workspace**, лише якщо користувач хоче, щоб файл інструкцій **workspace** був перенесений.
7. Виконати міграцію з відповідним пресетом і прапорцями.
8. Підсумувати результати, зокрема:
   - що було перенесено;
   - що було заархівовано для ручного перегляду;
   - що було пропущено і чому.
## Протокол взаємодії з користувачем

Hermes CLI підтримує інструмент `clarify` для інтерактивних підказок, проте його можливості обмежені:

- один вибір за раз
- до 4‑х заздалегідь визначених варіантів
- автоматичний варіант `Other` для вільного тексту

Він **не** підтримує справжні багатовибіркові чекбокси в одному запиті.

Для кожного виклику `clarify`:

- завжди вказуй непорожнє поле `question`
- додавай `choices` лише для реальних вибіркових підказок
- залишай `choices` 2‑4 простих рядкових варіанти
- ніколи не виводь заповнювачі чи скорочені варіанти типу `...`
- не додавай зайві пробіли чи стилізацію до варіантів
- не включай фіктивні поля форми в запитання, наприклад `enter directory here`, порожні рядки для заповнення або підкреслення типу `_____`
- для відкритих питань про шлях запитуй лише просте речення; користувач вводить відповідь у звичайному CLI‑запиті під панеллю

Якщо виклик `clarify` повертає помилку, проаналізуй текст помилки, виправ payload і спробуй ще раз один раз з коректним `question` та чистими варіантами.

Коли `clarify` доступний і сухий запуск виявляє будь‑яке необхідне рішення користувача, твоя **наступна дія має бути викликом інструмента `clarify`**.
Не завершуй хід звичайним повідомленням асистента типу:

- «Дозволь мені показати варіанти»
- «Що ти хочеш зробити?»
- «Ось опції»

Якщо потрібне рішення користувача, збирай його через `clarify` перед тим, як генерувати подальший текст.
Якщо залишаються кілька нерозв’язаних рішень, не вставляй пояснювальне повідомлення між ними. Після отримання відповіді на один `clarify` твоя наступна дія зазвичай буде наступний необхідний виклик `clarify`.

Розглядай `workspace-agents` як нерозв’язане рішення, коли сухий запуск повідомляє:

- `kind="workspace-agents"`
- `status="skipped"`
- причина, що містить `No workspace target was provided`

У такому випадку треба запитати інструкції щодо робочого простору перед виконанням. Не ігноруй це як рішення про пропуск.

Через ці обмеження використай спрощений потік рішень:

1. Для конфліктів `SOUL.md` використай `clarify` з варіантами:
   - `keep existing`
   - `overwrite with backup`
   - `review first`
2. Якщо сухий запуск показує один або більше елементів `kind="skill"` зі `status="conflict"`, використай `clarify` з варіантами:
   - `keep existing skills`
   - `overwrite conflicting skills with backup`
   - `import conflicting skills under renamed folders`
3. Для інструкцій робочого простору використай `clarify` з варіантами:
   - `skip workspace instructions`
   - `copy to a workspace path`
   - `decide later`
4. Якщо користувач обирає копіювання інструкцій робочого простору, задай додаткове відкрите питання `clarify`, запитуючи **абсолютний шлях**.
5. Якщо користувач обирає `skip workspace instructions` або `decide later`, продовжуй без `--workspace-target`.
6. Для режиму міграції використай `clarify` з цими трьома варіантами:
   - `user-data only`
   - `full compatible migration`
   - `cancel`
7. `user-data only` означає: мігрувати лише дані користувача та сумісну конфігурацію, **не** імпортуючи дозволені секрети.
8. `full compatible migration` означає: мігрувати ті ж сумісні дані користувача плюс дозволені секрети, якщо вони присутні.
9. Якщо `clarify` недоступний, задавай те саме питання у звичайному тексті, але обмежуй відповіді до `user-data only`, `full compatible migration` або `cancel`.

Виконавчі обмеження:

- Не виконуй, доки залишається нерозв’язане пропускання `workspace-agents` через `No workspace target was provided`.
- Єдині валідні способи розв’язати це:
  - користувач явно обирає `skip workspace instructions`
  - користувач явно обирає `decide later`
  - користувач надає шлях до робочого простору після вибору `copy to a workspace path`
- Відсутність цілі робочого простору у сухому запуску сама по собі не дає дозволу на виконання.
- Не виконуй, доки будь‑яке необхідне рішення `clarify` залишається нерозв’язаним.

Використовуй наступні шаблони payload для `clarify` як базовий патерн:

- `{"question":"Your existing SOUL.md conflicts with the imported one. What should I do?","choices":["keep existing","overwrite with backup","review first"]}`
- `{"question":"One or more imported OpenClaw skills already exist in Hermes. How should I handle those skill conflicts?","choices":["keep existing skills","overwrite conflicting skills with backup","import conflicting skills under renamed folders"]}`
- `{"question":"Choose migration mode: migrate only user data, or run the full compatible migration including allowlisted secrets?","choices":["user-data only","full compatible migration","cancel"]}`
- `{"question":"Do you want to copy the OpenClaw workspace instructions file into a Hermes workspace?","choices":["skip workspace instructions","copy to a workspace path","decide later"]}`
- `{"question":"Please provide an absolute path where the workspace instructions should be copied."}`
**План команди (простою мовою)**

1. **Обробка `SOUL.md`**
   - Якщо ти вибрав **«keep existing»**, команда **не** міститиме `--overwrite`.
   - Якщо ти вибрав **«overwrite with backup»**, команда **міститиме** `--overwrite`.

2. **Вирішення конфліктів навичок**
   - **«keep existing skills»** → додати `--skill-conflict skip`.
   - **«overwrite conflicting skills with backup»** → додати `--skill-conflict overwrite`.
   - **«import conflicting skills under renamed folders»** → додати `--skill-conflict rename`.

3. **Вибір пресету**
   - **«user‑data only»** → додати `--preset user-data` **і не** додавати `--migrate-secrets`.
   - **«full compatible migration»** → додати `--preset full --migrate-secrets`.

4. **Ціль робочого простору**
   - Додати `--workspace-target <absolute‑path>` **лише**, якщо ти явно вказав абсолютний шлях до робочого простору.
   - Якщо ти вибрав **«skip workspace instructions»** або **«decide later»**, **не** додавати `--workspace-target`.

5. **Крок перегляду**
   - Якщо ти вибрав **«review first»**, процес зупиниться перед виконанням, щоб ти міг переглянути відповідні файли.

**Наступний крок:** Підтвердь, що наведене відображає твої вибори. Після підтвердження буде сформовано остаточну команду.
## Правила звітування після виконання

Після виконання розглядай JSON‑вивід скрипту як єдине джерело правди.

1. Базуй усі підрахунки на `report.summary`.
2. Включай пункт у розділ **Successfully Migrated** лише тоді, коли його `status` точно дорівнює `migrated`.
3. Не стверджуй, що конфлікт був вирішений, якщо звіт не показує цей пункт як `migrated`.
4. Не повідомляй, що `SOUL.md` був перезаписаний, якщо пункт звіту з `kind="soul"` **не** має `status="migrated"`.
5. Якщо `report.summary.conflict > 0`, додай розділ конфліктів замість того, щоб мовчки натякати на успіх.
6. Якщо підрахунки та перелік пунктів не збігаються, виправ список так, щоб він відповідав звіту, перед тим як відповідати.
7. Додай шлях `output_dir` із звіту, коли він доступний, щоб користувач міг переглянути `report.json`, `summary.md`, резервні копії та заархівовані файли.
8. При переповненні пам'яті або профілю користувача не повідомляй, що записи були заархівовані, якщо звіт явно не вказує шлях до архіву. Якщо існує `details.overflow_file`, повідом, що повний список переповнення був експортований туди.
9. Якщо skill був імпортований у папку з новою назвою, вкажи остаточне місце призначення та згадай `details.renamed_from`.
10. Якщо присутній `report.skill_conflict_mode`, використай його як джерело правди для політики конфліктів імпортованих skill.
11. Якщо пункт має `status="skipped"`, не описуй його як перезаписаний, резервний, мігруваний чи вирішений.
12. Якщо `kind="soul"` має `status="skipped"` з причиною `Target already matches source`, скажи, що він залишився без змін, і не згадуй резервну копію.
13. Якщо імпортований skill був перейменований, а `details.backup` порожній, не натякай, що існуючу skill Hermes було перейменовано або резервовано. Скажи лише, що імпортована копія була розміщена у новому місці, і посилайся на `details.renamed_from` як на попередню папку, яка залишилася на місці.
## Presets міграції

Рекомендуються ці два пресети у звичайному використанні:

- `user-data`
- `full`

`user-data` включає:

- `soul`
- `workspace-agents`
- `memory`
- `user-profile`
- `messaging-settings`
- `command-allowlist`
- `skills`
- `tts-assets`
- `archive`

`full` включає все, що є в `user-data`, плюс:

- `secret-settings`

Скрипт‑помічник все ще підтримує категорії рівня `--include` / `--exclude`, але розглядай це як розширений запасний (фолбек) варіант, а не як типове UX.
## Команди

Dry run with full discovery:

```bash
python3 ~/.hermes/skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py
```

When using the terminal tool, prefer an absolute invocation pattern such as:

```json
{"command":"python3 /home/USER/.hermes/skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py","workdir":"/home/USER"}
```

Dry run with the user-data preset:

```bash
python3 ~/.hermes/skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py --preset user-data
```

Execute a user-data migration:

```bash
python3 ~/.hermes/skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py --execute --preset user-data --skill-conflict skip
```

Execute a full compatible migration:

```bash
python3 ~/.hermes/skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py --execute --preset full --migrate-secrets --skill-conflict skip
```

Execute with workspace instructions included:

```bash
python3 ~/.hermes/skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py --execute --preset user-data --skill-conflict rename --workspace-target "/absolute/workspace/path"
```

Do not use `$PWD` or the home directory as the workspace target by default. Ask for an explicit workspace path first.
## Важливі правила

1. Виконай сухий запуск перед виконанням, якщо користувач явно не вказав продовжувати одразу.
2. За замовчуванням не мігруй секрети. Токени, auth‑blobs, облікові дані пристроїв та сирі налаштування шлюзу мають залишатися поза **Hermes**, якщо користувач явно не попросив про міграцію секретів.
3. Не перезаписуй безмовно непорожні цілі **Hermes**, якщо користувач явно не бажає цього. Допоміжний скрипт збереже резервні копії, коли перезапис увімкнено.
4. Завжди надавай користувачеві звіт про пропущені елементи. Цей звіт є частиною міграції, а не необов’язковим доповненням.
5. Пріоритетно використовуйте основний робочий простір OpenClaw (`~/.openclaw/workspace/`) замість `workspace.default/`. Використовуйте робочий простір за замовчуванням лише як запасний (варіант), коли основні файли відсутні.
6. Навіть у режимі міграції секретів мігруй лише секрети до чистого призначення **Hermes**. Непідтримувані auth‑blobs все одно мають бути зазначені як пропущені.
7. Якщо сухий запуск показує копіювання великого активу, конфліктний `SOUL.md` або переповнені записи пам’яті, виділи це окремо перед виконанням.
8. За замовчуванням обирай `user-data only`, якщо користувач не впевнений.
9. Включай `workspace-agents` лише коли користувач явно вказав шлях до цільового робочого простору.
10. Розглядай `--include` / `--exclude` на рівні категорій як розширений спосіб обходу, а не як звичайний потік.
11. Не завершуй підсумок сухого запуску розпливчастим “Що ти хочеш робити?”, якщо доступний `clarify`. Використовуй структуровані підказки для подальших дій.
12. Не використовуйте відкриту підказку `clarify`, коли підходить реальна вибіркова підказка. Спочатку пропонуй вибіркові варіанти, а вільний текст – лише для абсолютних шляхів або запитів перегляду файлів.
13. Після сухого запуску ніколи не зупиняйся після підсумку, якщо залишилося невирішене рішення. Одразу використай `clarify` для найвищопріоритетного блокуючого рішення.
14. Порядок пріоритету для подальших питань:
    - конфлікт `SOUL.md`
    - конфлікти імпортованих **skill**‑ів
    - режим міграції
    - призначення інструкцій робочого простору
15. Не обіцяй представити варіанти пізніше в тому ж повідомленні. Представ їх, фактично викликавши `clarify`.
16. Після відповіді щодо режиму міграції явно перевіряй, чи залишилося невирішеним `workspace-agents`. Якщо так, твоєю наступною дією має бути виклик `clarify` для інструкцій робочого простору.
17. Після будь‑якої відповіді `clarify`, якщо залишаються інші необхідні рішення, не описуй лише що було вирішено. Одразу задавай наступне необхідне питання.
## Очікуваний результат

- стан персональності Hermes імпортовано
- файли пам'яті Hermes заповнено перетвореними знаннями OpenClaw
- навички OpenClaw доступні за шляхом `~/.hermes/skills/openclaw-imports/`
- звіт міграції, що показує будь‑які конфлікти, пропуски чи непідтримувані дані