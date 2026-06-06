# Туторіал з Kanban

Огляд чотирьох випадків використання, для яких створена система Hermes Kanban, з відкритою в браузері панеллю управління. Якщо ти ще не читав [огляд Kanban](./kanban), розпочни саме звідти — це передбачає, що ти знаєш, що таке завдання, запуск, виконавець і диспетчер.
## Налаштування

```bash
hermes kanban init           # optional; first `hermes kanban <anything>` auto-inits
hermes dashboard             # opens http://127.0.0.1:9119 in your browser
# click Kanban in the left nav
```

Дашборд — це найзручніше місце для **тебе**, щоб спостерігати за системою. Робітники‑агенти, яких створює диспетчер, ніколи не бачать дашборд або CLI — вони керують дошкою через спеціальний `kanban_*` [toolset](./kanban#how-workers-interact-with-the-board) (`kanban_show`, `kanban_list`, `kanban_complete`, `kanban_block`, `kanban_heartbeat`, `kanban_comment`, `kanban_create`, `kanban_link`, `kanban_unblock`). Усі три поверхні — дашборд, CLI, інструменти робітника — працюють через одну й ту ж SQLite‑БД на дошці (`~/.hermes/kanban.db` для дошки за замовчуванням, `~/.hermes/kanban/boards/<slug>/kanban.db` для будь‑якої дошки, яку ти створиш пізніше), тому кожна дошка залишається послідовною, незалежно від того, з якої сторони огорожі прийшли зміни.

У цьому посібнику використовується дошка `default`. Якщо ти хочеш кілька ізольованих черг (по одній на проєкт / репозиторій / домен), дивись [Boards (multi-project)](./kanban#boards-multi-project) в огляді — ті ж CLI / дашборд / потоки робітника застосовуються до кожної дошки, і робітники фізично не можуть бачити завдання на інших дошках.

Протягом усього посібника **блоки коду з міткою `bash` — це команди, які *ти* виконуєш.** Блоки коду з міткою `# worker tool calls` — це те, що модель запущеного робітника генерує як виклики інструментів — показано тут, щоб ти міг бачити цикл від початку до кінця, а не тому, що ти коли‑небудь їх запускатимеш.
## Дошка з першого погляду

![Kanban board overview](/img/kanban-tutorial/01-board-overview.png)

Шість колонок зліва направо:

- **Triage** — необроблені ідеї. За замовчуванням диспетчер автоматично запускає **decomposer** (оркестратор‑запусканий fan‑out) для задач у цій колонці: він читає ваш профіль‑ростер + описи і створює граф дочірніх задач, спрямованих до найкращих спеціалістів, залишаючи оригінальну задачу живою як батьківську, щоб оркестратор прокинувся і оцінив завершення, коли все закінчиться. Перемкни **Orchestration: Auto/Manual**‑таблетку у верхній частині сторінки kanban, щоб змінити режим. У режимі Manual (або для налаштувань без профілю оркестратора) натисни **⚗ Decompose** на картці або виконай `hermes kanban decompose <id>` / `/kanban decompose <id>`. Для одиничних задач, які не потребують fan‑out, **✨ Specify** виконує одноразове переписання специфікації (мета, підхід, критерії прийняття) і переводить у `todo`. Налаштуй моделі у `auxiliary.kanban_decomposer` та `auxiliary.triage_specifier` у `config.yaml`. Дивись [Auto vs Manual orchestration](./kanban#auto-vs-manual-orchestration) у головному посібнику Kanban.
- **Todo** — створені, але чекають залежностей або ще не призначені.
- **Ready** — призначені і чекають, поки диспетчер їх забере.
- **In progress** — виконавець активно працює над задачею. При ввімкненому «Lanes by profile» (за замовчуванням) ця колонка підгрупується за виконавцем, щоб ти міг одразу бачити, що робить кожен працівник.
- **Blocked** — виконавець запросив людську допомогу або спрацював circuit breaker.
- **Done** — завершено.

У верхній панелі є фільтри для пошуку, орендаря та виконавця, а також перемикач `Lanes by profile` і кнопка `Nudge dispatcher`, яка запускає один цикл диспетчеризації прямо зараз замість очікування наступного інтервалу демона. Клікнувши будь‑яку картку, ти відкриваєш її панель праворуч.

### Плоский вигляд

Якщо lanes профілю занадто шумні, вимкни «Lanes by profile», і колонка **In progress** згорнеться в один плоский список, впорядкований за часом захоплення:

![Board with lanes by profile off](/img/kanban-tutorial/02-board-flat.png)
## Історія 1 — Самостійний розробник, що випускає функцію

Ти створюєш функцію. Класичний процес: проєктуєш схему, реалізуєш API, пишеш тести. Три завдання з залежностями батько→дитина.

```bash
SCHEMA=$(hermes kanban create "Design auth schema" \
    --assignee backend-dev --tenant auth-project --priority 2 \
    --body "Design the user/session/token schema for the auth module." \
    --json | jq -r .id)

API=$(hermes kanban create "Implement auth API endpoints" \
    --assignee backend-dev --tenant auth-project --priority 2 \
    --parent $SCHEMA \
    --body "POST /register, POST /login, POST /refresh, POST /logout." \
    --json | jq -r .id)

hermes kanban create "Write auth integration tests" \
    --assignee qa-dev --tenant auth-project --priority 2 \
    --parent $API \
    --body "Cover happy path, wrong password, expired token, concurrent refresh."
```

Оскільки `API` має `SCHEMA` як батька, а `tests` має `API` як батька, лише `SCHEMA` починає в стані `ready`. Інші два залишаються в `todo`, доки їхні батьки не завершаться. Це працює механізм просування залежностей — інший worker не підхопить написання тестів, доки не з’явиться API для тестування.

На наступному тику диспетчера (за замовчуванням 60 секунд, або одразу, якщо ти натиснеш **Nudge dispatcher**) профіль `backend-dev` spawn ається як worker з `HERMES_KANBAN_TASK=$SCHEMA` у своєму середовищі. Ось як виглядає цикл виклику інструменту worker’а зсередини агента:

```python
# worker tool calls — NOT commands you run
kanban_show()
# → returns title, body, worker_context, parents, prior attempts, comments

# (worker reads worker_context, uses terminal/file tools to design the schema,
#  write migrations, run its own checks, commit — the real work happens here)

kanban_heartbeat(note="schema drafted, writing migrations now")

kanban_complete(
    summary="users(id, email, pw_hash), sessions(id, user_id, jti, expires_at); "
            "refresh tokens stored as sessions with type='refresh'",
    metadata={
        "changed_files": ["migrations/001_users.sql", "migrations/002_sessions.sql"],
        "decisions": ["bcrypt for hashing", "JWT for session tokens",
                      "7-day refresh, 15-min access"],
    },
)
```

`kanban_show` за замовчуванням підставляє `task_id` зі значення `$HERMES_KANBAN_TASK`, тому worker не потребує знати свій власний ідентифікатор. `kanban_complete` записує підсумок + метадані у поточний рядок `task_runs`, закриває цей запуск і переводить завдання у стан `done` — все це в один атомарний крок через `kanban_db`.

Коли `SCHEMA` переходить у `done`, механізм залежностей автоматично просуває `API` до `ready`. Worker API, коли підхопить завдання, викликає `kanban_show()` і бачить підсумок та метадані `SCHEMA`, прикріплені до передачі батька — тому він знає рішення схеми без повторного читання довгого документу дизайну.

Клацни на завершеному завданні схеми на дошці, і висувна панель покаже все:

![Solo dev — completed schema task drawer](/img/kanban-tutorial/03-drawer-schema-task.png)

Розділ «Run History» внизу — це ключове доповнення. Один запуск: результат `completed`, worker `@backend-dev`, тривалість, мітка часу та повний підсумок передачі. Blob метаданих (`changed_files`, `decisions`) зберігається також у запуску і доступний будь‑якому наступному worker’у, який читає цього батька.

Ти можеш переглянути ті ж дані у своєму терміналі в будь‑який момент — ці команди **ти** використовуєш, щоб подивитися на дошку, а не worker:

```bash
hermes kanban show $SCHEMA
hermes kanban runs $SCHEMA
# #  OUTCOME       PROFILE       ELAPSED  STARTED
# 1  completed     backend-dev        0s  2026-04-27 19:34
#     → users(id, email, pw_hash), sessions(id, user_id, jti, expires_at); refresh tokens ...
```
## Історія 2 — Fleet farming

У тебе є три worker’и (перекладач, транскрибатор, копірайтер) і купа незалежних завдань. Ти хочеш, щоб усі троє працювали паралельно і робили видимий прогрес. Це найпростіший kanban‑випадок, для якого оптимізовано оригінальний дизайн.

Створи роботу:

```bash
for lang in Spanish French German; do
    hermes kanban create "Translate homepage to $lang" \
        --assignee translator --tenant content-ops
done
for i in 1 2 3 4 5; do
    hermes kanban create "Transcribe Q3 customer call #$i" \
        --assignee transcriber --tenant content-ops
done
for sku in 1001 1002 1003 1004; do
    hermes kanban create "Generate product description: SKU-$sku" \
        --assignee copywriter --tenant content-ops
done
```

Запусти шлюз і відійди — він хостить вбудований диспетчер,
який підбирає завдання всіх трьох профілів спеціалістів у тому ж
`kanban.db`:

```bash
hermes gateway start
```

Тепер відфільтруй дошку до `content-ops` (або просто пошукай «Transcribe») і ти побачиш це:

![Fleet view filtered to transcribe tasks](/img/kanban-tutorial/07-fleet-transcribes.png)

Два транскрипти завершено, один виконується, два готові, чекають наступного тикання диспетчера. Стовпець *In Progress* згруповано за профілем (за замовчуванням «Lanes by profile»), тож ти бачиш активне завдання кожного worker’а без перегляду змішаного списку. Диспетчер підвищить наступне готове завдання до стану *running*, як тільки поточне завершиться. Завдяки трьом демонічним процесам, які працюють над трьома пулами виконавців паралельно, вся черга контенту споживається без подальшого людського втручання.

**Все, що сказано в Історії 1 про структуровану передачу, застосовується і тут.** Працівник‑перекладач, завершивши виклик, генерує `kanban_complete(summary="translated 4 pages, style matched existing marketing voice", metadata={"duration_seconds": 720, "tokens_used": 2100})` — корисно для аналітики та будь‑якого наступного завдання, що залежить від цього.
## Історія 3 — Конвеєр ролей з повторною спробою

Саме тут Kanban виправдовує свою перевагу над плоским списком TODO. PM пише специфікацію. Інженер її реалізує. Рев’юер відхиляє першу спробу. Інженер пробує ще раз із змінами. Рев’юер схвалює.

Вид панелі, відфільтрований за `auth-project`:

![Pipeline view for a multi-role feature](/img/kanban-tutorial/08-pipeline-auth.png)

Трьохетапний ланцюжок, видимий одночасно: `Spec: password reset flow` (DONE, pm), `Implement password reset flow` (DONE, backend-dev), `Review password reset PR` (READY, reviewer). Кожен має свого батька зеленим внизу та дітей як залежності.

Цікавим є завдання реалізації, бо воно було заблоковано і повторно запущено. Ось повна хореографія трьох агентів, показана як виклики інструменту кожної моделі робітника:

```python
# --- PM worker spawns on $SPEC and writes the acceptance criteria ---
# worker tool calls
kanban_show()
kanban_complete(
    summary="spec approved; POST /forgot-password sends email, "
            "GET /reset/:token renders form, POST /reset applies new password",
    metadata={"acceptance": [
        "expired token returns 410",
        "reused last-3 password returns 400 with message",
        "successful reset invalidates all active sessions",
    ]},
)
# → $SPEC is done; $IMPL auto-promotes from todo to ready

# --- Engineer worker spawns on $IMPL (first attempt) ---
# worker tool calls
kanban_show()   # reads $SPEC's summary + acceptance metadata in worker_context
# (engineer writes code, runs tests, opens PR)
# Reviewer feedback arrives — engineer decides the concerns are valid and blocks
kanban_block(
    reason="Review: password strength check missing, reset link isn't "
           "single-use (can be replayed within 30min)",
)
# → $IMPL transitions to blocked; run 1 closes with outcome='blocked'
```

Тепер ти (людина або окремий профіль рев’юера) читаєш причину блокування, вирішуєш, що напрямок виправлення зрозумілий, і розблоковуєш за допомогою кнопки «Unblock» на панелі — або через CLI / slash‑команду:

```bash
hermes kanban unblock $IMPL
# or from a chat: /kanban unblock $IMPL
```

Диспетчер переводить `$IMPL` назад у стан `ready` і, на наступному тикі, перезапускає робітника `backend-dev`. Це друге створення — **новий запуск** того ж завдання:

```python
# --- Engineer worker spawns on $IMPL (second attempt) ---
# worker tool calls
kanban_show()
# → worker_context now includes the run 1 block reason, so this worker knows
#   which two things to fix instead of re-reading the whole spec
# (engineer adds zxcvbn check, makes reset tokens single-use, re-runs tests)
kanban_complete(
    summary="added zxcvbn strength check, reset tokens are now single-use "
            "(stored + deleted on success)",
    metadata={
        "changed_files": [
            "auth/reset.py",
            "auth/tests/test_reset.py",
            "migrations/003_single_use_reset_tokens.sql",
        ],
        "tests_run": 11,
        "review_iteration": 2,
    },
)
```

Клацни на завданні реалізації. У drawer’і показані **дві спроби**:

![Implementation task with two runs — blocked then completed](/img/kanban-tutorial/04b-drawer-retry-history-scrolled.png)

- **Run 1** — `blocked` користувачем `@backend-dev`. Відгук рев’ю розташований одразу під результатом: «відсутня перевірка сили пароля, посилання для скидання не одноразове (можна використати протягом 30 хв)».
- **Run 2** — `completed` користувачем `@backend-dev`. Свіже резюме, свіжі метадані.

Кожен запуск — це рядок у `task_runs` зі своїм результатом, резюме та метаданими. Історія повторних спроб — це не лише концептуальне доповнення поверх «останнього» стану задачі, а її основне представлення. Коли робітник, що повторно запускає задачу, відкриває її, `build_worker_context` показує йому попередні спроби, тож робітник другого проходу бачить, чому перша спроба була заблокована, і вирішує саме ці проблеми, а не запускає все заново.

Рев’юер продовжує. Коли він відкриває `Review password reset PR`, бачить:

![Reviewer's drawer view of the pipeline](/img/kanban-tutorial/09-drawer-pipeline-review.png)

Посилання на батька — це завершена реалізація. Коли робітник рев’юера спаунається на `Review password reset PR` і викликає `kanban_show()`, повернутий `worker_context` містить резюме та метадані останнього завершеного запуску батька — тому рев’юер читає «додана перевірка сили пароля zxcvbn, токени скидання тепер одноразові» і має список змінених файлів під рукою перед переглядом diff.
## Story 4 — Circuit breaker and crash recovery

Реальні воркери можуть падати: відсутні облікові дані, OOM‑вбивства, короткочасні мережеві помилки. Диспетчер має два рівні захисту: **circuit breaker**, який автоматично блокує після N послідовних помилок, щоб дошка не «трясло» вічно, і **crash detection**, який повертає задачу, чиїй PID процесу воркера зник до закінчення TTL.

### Circuit breaker — постійна помилка

Задача розгортання, яка не може запустити воркера, бо `AWS_ACCESS_KEY_ID` не встановлено в середовищі профілю:

```bash
hermes kanban create "Deploy to staging (missing creds)" \
    --assignee deploy-bot --tenant ops \
    --max-retries 3
```

Диспетчер намагається запустити воркера. Запуск не вдається (`RuntimeError: AWS_ACCESS_KEY_ID not set`). Диспетчер звільняє claim, збільшує лічильник помилок і спробує ще на наступному тикі. Оскільки в цьому прикладі вказано `--max-retries 3`, circuit breaker спрацьовує після трьох послідовних помилок: задача переходить у стан `blocked` з результатом `gave_up`. Якщо прапорець не вказано, Hermes використовує `kanban.failure_limit` (за замовчуванням — 2). Подальші спроби не будуть виконані, доки людина не розблокує задачу.

Клацни на заблоковану задачу:

![Circuit breaker — 2 spawn_failed + 1 gave_up](/img/kanban-tutorial/11-drawer-gave-up.png)

Три запуску, усі з однаковою помилкою у полі `error`. Перші два — `spawn_failed` (можна повторити), третій — `gave_up` (кінцева). Журнал подій вище показує повну послідовність: `created → claimed → spawn_failed → claimed → spawn_failed → claimed → gave_up`.

У терміналі:

```bash
hermes kanban runs t_ef5d
# #   OUTCOME        PROFILE        ELAPSED  STARTED
# 1   spawn_failed   deploy-bot          0s  2026-04-27 19:34
#       ! AWS_ACCESS_KEY_ID not set in deploy-bot env
# 2   spawn_failed   deploy-bot          0s  2026-04-27 19:34
#       ! AWS_ACCESS_KEY_ID not set in deploy-bot env
# 3   gave_up        deploy-bot          0s  2026-04-27 19:34
#       ! AWS_ACCESS_KEY_ID not set in deploy-bot env
```

Якщо підключено Telegram / Discord / Slack, шлюз надсилає сповіщення про подію `gave_up`, і ти дізнаєшся про збій, не відкриваючи дошку.

### Crash recovery — воркер гине посеред роботи

Іноді запуск проходить успішно, а процес воркера помирає пізніше — segfault, OOM, `systemctl stop`. Диспетчер опитує `kill(pid, 0)` і виявляє мертвий PID; claim звільняється, задача повертається у стан `ready`, і на наступному тикі її отримує новий воркер.

У прикладі seed‑даних це міграція, яка вичерпала пам’ять:

```bash
# Worker claims, starts scanning 2.4M rows, OOM kills it at ~2.3M
# Dispatcher detects dead pid, releases claim, increments attempt counter
# Retry with a chunked strategy succeeds
```

Drawer показує повну історію двох спроб:

![Crash and recovery — 1 crashed + 1 completed](/img/kanban-tutorial/06-drawer-crash-recovery.png)

Запуск 1 — `crashed` з помилкою `OOM kill at row 2.3M (process 99999 gone)`. Запуск 2 — `completed` з метаданими `"strategy": "chunked with LIMIT + WHERE id > last_id"`. Повторний воркер побачив крах першого запуску у своєму контексті і обрав безпечнішу стратегію; метадані явно показують майбутньому спостерігачеві (або автору постмортему), що саме змінилося.
## Structured handoff — чому `summary` і `metadata` важливі

У кожній історії вище працівники викликають `kanban_complete(summary=..., metadata=...)` в кінці. Це не просто прикраса — це основний канал передачі даних між етапами робочого процесу.

Коли працівник у завданні **B** створюється і викликає `kanban_show()`, `worker_context`, який він отримує, містить:

- **Попередні спроби** **B** (попередні запуски: outcome, `summary`, error, `metadata`), щоб повторний працівник не повторював невдалий шлях.
- **Результати батьківських завдань** — для кожного батька останній завершений запуск з `summary` і `metadata`, щоб downstream‑worker бачили, чому і як була виконана upstream‑work.

Це замінює «перегортання коментарів і виводу роботи», яке мучить плоскі kanban‑системи. PM пише критерії приймання у `metadata` специфікації, і працівник інженера бачить їх структуровано у батьківському handoff. Інженер записує, які тести він запустив і скільки пройшло, і у працівника рев’юера цей список вже в руках перед відкриттям diff.

Захист bulk‑close існує, бо ці дані прив’язані до окремого запуску. `hermes kanban complete a b c --summary X` (ти, з CLI) відхиляється — копіювання одного і того ж `summary` у три завдання майже завжди помилкове. Bulk‑close без прапорців handoff все ще працює для типового випадку «я завершив купу адміністративних завдань». Інтерфейс інструменту взагалі не пропонує bulk‑варіант; `kanban_complete` завжди виконується по одному завданню одночасно з тієї ж причини.
## Перевірка завдання, яке зараз виконується

Для повноти — ось вікно завдання, яке ще в процесі (реалізація API з Story 1, заявлена `backend-dev`, але ще не завершена):

![Claimed, in-flight task](/img/kanban-tutorial/10-drawer-in-flight.png)

Статус — `Running`. Активний запуск відображається у розділі **Run History** з результатом `active` і без `ended_at`. Якщо цей воркер завершиться або вийде за час, диспетчер закриє цей запуск з відповідним результатом і відкриє новий при наступному запиті — рядок спроби ніколи не зникає.
## Наступні кроки

- [Kanban overview](./kanban) — повна модель даних, словник подій та довідка CLI.
- `hermes kanban --help` — усі підкоманди, усі прапорці.
- `hermes kanban watch --kinds completed,gave_up,timed_out` — живий потік подій терміналу по всій дошці.
- `hermes kanban notify-subscribe <task> --platform telegram --chat-id <id>` — отримати ping шлюзу, коли конкретне завдання завершується.