# Учебник по Kanban

Пошаговое руководство по четырём сценариям использования системы Hermes Kanban с открытой в браузере панелью управления. Если ты ещё не читал [Kanban overview](./kanban), начни с него — это руководство предполагает, что ты знаешь, что такое task, run, assignee и dispatcher.
## Setup

```bash
hermes kanban init           # optional; first `hermes kanban <anything>` auto-inits
hermes dashboard             # opens http://127.0.0.1:9119 in your browser
# click Kanban in the left nav
```

Dashboard — самое удобное место для **тебя**, чтобы наблюдать за системой. Рабочие агенты, которых порождает диспетчер, никогда не видят dashboard или CLI — они управляют доской через специальный `kanban_*` [toolset](./kanban#how-workers-interact-with-the-board) (`kanban_show`, `kanban_list`, `kanban_complete`, `kanban_block`, `kanban_heartbeat`, `kanban_comment`, `kanban_create`, `kanban_link`, `kanban_unblock`). Все три поверхности — dashboard, CLI, инструменты рабочих — работают через одну и ту же SQLite‑БД на доске (`~/.hermes/kanban.db` для доски по умолчанию, `~/.hermes/kanban/boards/<slug>/kanban.db` для любой доски, которую ты создашь позже), поэтому каждая доска остаётся согласованной независимо от того, с какой стороны забора пришло изменение.

В этом руководстве используется доска `default`. Если тебе нужны несколько изолированных очередей (по одной на проект / репозиторий / домен), смотри раздел [Boards (multi-project)](./kanban#boards-multi-project) в обзоре — те же CLI / dashboard / потоки рабочих применимы к каждой доске, и рабочие физически не могут видеть задачи на других досках.

Во всём руководстве **блоки кода, помеченные `bash`, — это команды, которые *ты* выполняешь.** Блоки кода, помеченные `# worker tool calls`, показывают, какие вызовы инструментов генерирует модель запущенного рабочего — они приведены здесь, чтобы ты мог увидеть цикл от начала до конца, а не потому, что тебе когда‑либо придётся их запускать.
## Доска в двух словах

![Kanban board overview](/img/kanban-tutorial/01-board-overview.png)

Шесть колонок слева направо:

- **Triage** — сырые идеи. По умолчанию диспетчер автоматически запускает **decomposer** (fan‑out, управляемый оркестратором) для задач здесь: он читает ваш список профилей + описания и формирует граф дочерних задач, направленных к наиболее подходящим специалистам, при этом исходная задача остаётся живой как родитель, чтобы оркестратор проснулся и оценил завершение, когда всё закончится. Переключи переключатель **Orchestration: Auto/Manual** в верхней части страницы канбан, чтобы сменить режим. В режиме Manual (или при настройках без профиля оркестратора) нажми **⚗ Decompose** на карточке или выполни `hermes kanban decompose <id>` / `/kanban decompose <id>`. Для одиночных задач, которым не нужен fan‑out, **✨ Specify** делает одноразовую перезапись спецификации (цель, подход, критерии приёмки) и переводит её в `todo`. Настрой модели в `auxiliary.kanban_decomposer` и `auxiliary.triage_specifier` в `config.yaml`. См. [Auto vs Manual orchestration](./kanban#auto-vs-manual-orchestration) в основном руководстве по Kanban.
- **Todo** — создано, но ждёт зависимостей или ещё не назначено.
- **Ready** — назначено и ждёт, пока диспетчер возьмёт задачу.
- **In progress** — работник активно исполняет задачу. При включённом `Lanes by profile` (по умолчанию) эта колонка дополнительно группируется по исполнителю, чтобы ты мог сразу увидеть, чем каждый работник занят.
- **Blocked** — работник запросил человеческий ввод или сработал предохранитель.
- **Done** — завершено.

В верхней панели есть фильтры для поиска, арендатора и исполнителя, а также переключатель `Lanes by profile` и кнопка `Nudge dispatcher`, которая запускает один цикл диспетчеризации прямо сейчас вместо ожидания следующего интервала демона. Нажатие любой карточки открывает её ящик справа.

### Плоский вид

Если lanes профилей слишком шумные, отключи `Lanes by profile`, и колонка **In progress** свернётся в один плоский список, упорядоченный по времени захвата:

![Board with lanes by profile off](/img/kanban-tutorial/02-board-flat.png)
## История 1 — Один разработчик выпускает фичу

Ты создаёшь фичу. Классический процесс: проектировать схему, реализовать API, написать тесты. Три задачи с зависимостями «родитель → потомок».

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

Поскольку `API` имеет `SCHEMA` в качестве родителя, а `tests` имеет `API` в качестве родителя, только `SCHEMA` находится в состоянии `ready`. Остальные две находятся в `todo`, пока их родители не завершатся. Это движок продвижения зависимостей делает свою работу — ни один другой работник не возьмёт написание тестов, пока не появится API для тестирования.

На следующем тике диспетчера (по умолчанию каждые 60 с, или сразу, если нажать **Nudge dispatcher**) профиль `backend-dev` запускается как работник с переменной окружения `HERMES_KANBAN_TASK=$SCHEMA`. Вот как выглядит цикл вызова инструмента работника изнутри агента:

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

`kanban_show` по умолчанию подставляет `task_id` из `$HERMES_KANBAN_TASK`, поэтому работнику не нужно знать свой собственный идентификатор. `kanban_complete` записывает сводку + метаданные в текущую строку `task_runs`, закрывает этот запуск и переводит задачу в `done` — всё в одном атомарном переходе через `kanban_db`.

Когда `SCHEMA` переходит в `done`, движок зависимостей автоматически продвигает `API` в `ready`. Работник API, когда возьмёт задачу, вызовет `kanban_show()` и увидит сводку и метаданные `SCHEMA`, прикреплённые к передаче родителя — так он узнает решения по схеме без повторного чтения длинного документа дизайна.

Кликни по завершённой задаче схемы на доске, и в ящике отобразятся все детали:

![Solo dev — completed schema task drawer](/img/kanban-tutorial/03-drawer-schema-task.png)

Раздел «Run History» внизу — ключовое дополнение. Одна попытка: результат `completed`, работник `@backend-dev`, длительность, метка времени и полная сводка передачи. Блоб метаданных (`changed_files`, `decisions`) также хранится в запуске и показывается любому downstream‑работнику, который читает этого родителя.

Ты можешь просмотреть те же данные из терминала в любой момент — эти команды **ты** используешь для просмотра доски, а не работник:

```bash
hermes kanban show $SCHEMA
hermes kanban runs $SCHEMA
# #  OUTCOME       PROFILE       ELAPSED  STARTED
# 1  completed     backend-dev        0s  2026-04-27 19:34
#     → users(id, email, pw_hash), sessions(id, user_id, jti, expires_at); refresh tokens ...
```
## История 2 — Fleet farming

У тебя есть три работника (переводчик, транскрибатор, копирайтер) и куча независимых задач. Ты хочешь, чтобы все трое работали параллельно и делали видимый прогресс. Это самый простой сценарий канбан и тот, для которого изначальный дизайн был оптимизирован.

Создай работу:

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

Запусти шлюз и отойди — он хостит встроенный диспетчер, который подбирает задачи всех трёх профильных специалистов из того же `kanban.db`:

```bash
hermes gateway start
```

Теперь отфильтруй доску по `content-ops` (или просто найди «Transcribe») и ты увидишь следующее:

![Fleet view filtered to transcribe tasks](/img/kanban-tutorial/07-fleet-transcribes.png)

Две транскрипции выполнены, одна запущена, две готовы, ожидая следующего тика диспетчера. Столбец «In Progress» сгруппирован по профилю (по умолчанию «Lanes by profile»), поэтому ты видишь активную задачу каждого работника без необходимости просматривать смешанный список. Диспетчер продвинет следующую готовую задачу в состояние **running**, как только текущая завершится. С тремя демонами, работающими над тремя пулами исполнителей параллельно, вся очередь контента опустеет без дальнейшего вмешательства человека.

**Всё, что сказано в Истории 1 о структурированной передаче, по‑прежнему применимо здесь.** Работник‑переводчик, завершив вызов, генерирует `kanban_complete(summary="translated 4 pages, style matched existing marketing voice", metadata={"duration_seconds": 720, "tokens_used": 2100})` — полезно для аналитики и для любой последующей задачи, зависящей от этой.
## История 3 — Конвейер ролей с повторной попыткой

Здесь Kanban доказывает свою ценность по сравнению с плоским списком TODO. Менеджер проекта пишет спецификацию. Инженер реализует её. Рецензент отклоняет первую попытку. Инженер пытается снова с изменениями. Рецензент одобряет.

Представление панели, отфильтрованное по `auth-project`:

![Pipeline view for a multi-role feature](/img/kanban-tutorial/08-pipeline-auth.png)

Трёхэтапная цепочка видна сразу: `Spec: password reset flow` (DONE, pm), `Implement password reset flow` (DONE, backend-dev), `Review password reset PR` (READY, reviewer). У каждой есть родитель внизу, отмеченный зелёным, и дочерние элементы как зависимости.

Интересна задача реализации, потому что она была заблокирована и повторно запущена. Ниже полная хореография трёх агентов, показанная как вызовы инструментов каждой модели воркера:

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

Теперь ты (человек или отдельный профиль рецензента) читаешь причину блокировки, решаешь, что направление исправления ясно, и разблокируешь её кнопкой «Unblock» на панели — либо через CLI / slash‑команду:

```bash
hermes kanban unblock $IMPL
# or from a chat: /kanban unblock $IMPL
```

Диспетчер переводит `$IMPL` обратно в `ready` и, на следующем тике, возрождает воркера `backend-dev`. Это второе создание — **новый запуск** той же задачи:

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

Кликни задачу реализации. Выдвижной блок показывает **две попытки**:

![Implementation task with two runs — blocked then completed](/img/kanban-tutorial/04b-drawer-retry-history-scrolled.png)

- **Run 1** — `blocked` пользователем `@backend-dev`. Обратная связь от рецензента находится сразу под результатом: «отсутствует проверка силы пароля, ссылка сброса не одноразовая (может быть использована повторно в течение 30 мин)».
- **Run 2** — `completed` пользователем `@backend-dev`. Свежая сводка, свежие метаданные.

Каждый запуск — это строка в `task_runs` со своим результатом, сводкой и метаданными. История повторных попыток — это не концептуальное дополнение к задаче «последнее состояние», а её основное представление. Когда повторно работающий воркер открывает задачу, `build_worker_context` показывает ему предыдущие попытки, поэтому воркер второго прохода видит, почему первая попытка была заблокирована, и устраняет именно эти находки, а не запускает процесс заново.

Рецензент берёт задачу дальше. Когда он открывает `Review password reset PR`, он видит:

![Reviewer's drawer view of the pipeline](/img/kanban-tutorial/09-drawer-pipeline-review.png)

Ссылка на родителя — завершённая реализация. Когда воркер рецензента спаунился на `Review password reset PR` и вызывает `kanban_show()`, возвращённый `worker_context` включает сводку + метаданные самого последнего завершённого запуска родителя, так что рецензент читает «добавлена проверка силы пароля zxcvbn, токены сброса теперь одноразовые» и имеет список изменённых файлов под рукой перед тем, как смотреть diff.
## Story 4 — Circuit breaker and crash recovery

Real workers fail. Missing credentials, OOM kills, transient network errors. The dispatcher has two lines of defense: a **circuit breaker** that auto‑blocks after N consecutive failures so the board doesn't thrash forever, and **crash detection** that reclaims a task whose worker PID went away before its TTL expired.

### Circuit breaker — permanent‑looking failure

A deploy task that can't spawn its worker because `AWS_ACCESS_KEY_ID` isn't set in the profile's environment:

```bash
hermes kanban create "Deploy to staging (missing creds)" \
    --assignee deploy-bot --tenant ops \
    --max-retries 3
```

The dispatcher tries to spawn the worker. Spawn fails (`RuntimeError: AWS_ACCESS_KEY_ID not set`). The dispatcher releases the claim, increments a failure counter, and tries again next tick. Because this example sets `--max-retries 3`, the circuit trips after three consecutive failures: the task goes to `blocked` with outcome `gave_up`. If you omit the flag, Hermes uses `kanban.failure_limit` (default: 2). No more retries until a human unblocks it.

Click the blocked task:

![Circuit breaker — 2 spawn_failed + 1 gave_up](/img/kanban-tutorial/11-drawer-gave-up.png)

Three runs, all with the same error on the `error` field. The first two are `spawn_failed` (retryable), the third is `gave_up` (terminal). The event log above shows the full sequence: `created → claimed → spawn_failed → claimed → spawn_failed → claimed → gave_up`.

On the terminal:

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

If Telegram / Discord / Slack is wired in, a gateway notification fires on the `gave_up` event so you hear about the outage without having to check the board.

### Crash recovery — worker dies mid‑flight

Sometimes the spawn succeeds but the worker process dies later — segfault, OOM, `systemctl stop`. The dispatcher polls `kill(pid, 0)` and detects the dead pid; the claim releases, the task goes back to `ready`, and the next tick gives it to a fresh worker.

The example in the seed data is a migration that was running out of memory:

```bash
# Worker claims, starts scanning 2.4M rows, OOM kills it at ~2.3M
# Dispatcher detects dead pid, releases claim, increments attempt counter
# Retry with a chunked strategy succeeds
```

The drawer shows the full two‑attempt history:

![Crash and recovery — 1 crashed + 1 completed](/img/kanban-tutorial/06-drawer-crash-recovery.png)

Run 1 — `crashed`, with the error `OOM kill at row 2.3M (process 99999 gone)`. Run 2 — `completed`, with `"strategy": "chunked with LIMIT + WHERE id > last_id"` in its metadata. The retrying worker saw the crash of run 1 in its context and picked a safer strategy; the metadata makes it obvious to a future observer (or post‑mortem writer) what changed.
## Структурная передача — почему `summary` и `metadata` важны

Во всех историях выше работники вызывают `kanban_complete(summary=…, metadata=…)` в конце. Это не декоративный элемент — основной канал передачи данных между этапами рабочего процесса.

Когда создаётся работник для задачи B и вызывается `kanban_show()`, возвращаемый `worker_context` содержит:

- **Предыдущие попытки** B (предыдущие запуски: результат, `summary`, ошибка, `metadata`), чтобы повторяющийся работник не проходил тот же неудачный путь.
- **Результаты родительских задач** — для каждой родительской задачи последние завершённые `summary` и `metadata`, чтобы downstream‑работники видели, почему и как была выполнена upstream‑работа.

Это заменяет «просеивание комментариев и вывода работы», которое мучает плоские kanban‑системы. PM пишет критерии приёмки в `metadata` спецификации, а работник инженера видит их структурно в передаче от родителя. Инженер фиксирует, какие тесты он запускал и сколько прошло, и у работника ревьюера этот список уже есть под рукой перед открытием диффа.

Защита массового закрытия существует потому, что эти данные привязаны к отдельному запуску. `hermes kanban complete a b c --summary X` (ты, из CLI) отклоняется — копировать один и тот же `summary` в три задачи почти всегда неправильно. Массовое закрытие без флагов передачи всё равно работает для типичного случая «я закончил кучу административных задач». Интерфейс инструмента вовсе не предоставляет массовый вариант; `kanban_complete` всегда работает с одной задачей за раз по той же причине.
## Проверка текущей выполняющейся задачи

Для полноты картины — вот «drawer» задачи, которая всё ещё в процессе (реализация API из Story 1, заявлена `backend-dev`, но ещё не завершена):

![Claimed, in-flight task](/img/kanban-tutorial/10-drawer-in-flight.png)

Статус — `Running`. Активный запуск отображается в разделе **Run History** с результатом `active` и без `ended_at`. Если этот воркер завершится аварийно или истечёт время ожидания, диспетчер закроет этот запуск с соответствующим результатом и откроет новый при следующем заявлении — строка попытки никогда не исчезает.
## Следующие шаги

- [Kanban overview](./kanban) — полная модель данных, словарь событий и справочник CLI.
- `hermes kanban --help` — все подкоманды и все флаги.
- `hermes kanban watch --kinds completed,gave_up,timed_out` — живой поток терминальных событий по всей доске.
- `hermes kanban notify-subscribe <task> --platform telegram --chat-id <id>` — получай ping от gateway, когда конкретная задача завершится.