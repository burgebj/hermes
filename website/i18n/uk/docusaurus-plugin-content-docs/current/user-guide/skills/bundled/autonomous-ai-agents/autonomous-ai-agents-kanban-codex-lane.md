---
title: "Kanban Codex колона"
sidebar_label: "Kanban Codex Lane"
description: "Використовуй, коли працівник Hermes Kanban хоче запустити Codex CLI як ізольовану lane реалізації, поки Hermes зберігає власність над життєвим циклом завдання, узгодженням, тестуванням."
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Kanban Codex Lane

Використовуй, коли Hermes Kanban worker хоче запустити Codex CLI як ізольовану lane‑реалізацію, при цьому Hermes зберігає контроль над життєвим циклом завдання, його узгодженням, тестуванням і передачою.
## Метадані навички

| | |
|---|---|
| Джерело | Вбудовано (встановлено за замовчуванням) |
| Шлях | `skills/autonomous-ai-agents/kanban-codex-lane` |
| Версія | `1.0.0` |
| Автор | Hermes Agent |
| Ліцензія | MIT |
| Теги | `kanban`, `codex`, `worktrees`, `autonomous-agents`, `prediction-market-bot` |
| Пов’язані навички | [`kanban-worker`](/docs/user-guide/skills/bundled/devops/devops-kanban-worker), [`codex`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-codex), [`hermes-agent`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-hermes-agent) |
:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції, коли навичка активна.
:::

# Kanban Codex Lane
## Огляд

Цей **skill** визначає легковагову конвенцію подвійного lane Hermes+Codex для працівників Kanban. Hermes завжди є власником завдання: він викликає `kanban_show`, вирішує, чи підходить Codex, створює або вибирає ізольовану робочу область, запускає та моніторить Codex, узгоджує будь‑які відмінності, виконує верифікацію та записує остаточний `kanban_complete` або `kanban_block` як передачу. Codex є лише вхідним lane. Вихід Codex не є сигналом завершення завдання, не є довіреним рецензентом і не має права безпосередньо записувати стійкий стан Kanban.

Конвенція існує, щоб працівник Hermes міг використовувати Codex для обмеженої допомоги в реалізації без зміни диспетчера. Диспетчер все одно має spawn Hermes‑workers. Працівник може за бажанням запустити Codex у власному процесі, а потім прийняти, частково прийняти або відхилити lane після незалежного перегляду та тестів.
## Коли використовувати

Використовуй lane Codex, коли виконуються всі наступні умови:

- Завдання Kanban — це кодинг, рефакторинг, документація, тестування або механічна міграція з чіткими критеріями приймання.
- Обмежений diff можна оцінити Hermes за один запуск.
- Репозиторій можна скопіювати або перевірити в ізольованому git‑worktree/branch.
- Hermes може самостійно запустити відповідні тести після завершення роботи Codex.
- Промпт може містити всі обмеження безпеки та файли, які не повинні змінюватися.

Не використовуйте lane Codex, якщо виконується будь‑яка з наступних умов:

- Завдання вимагає людського судження, яке ще не зафіксовано в описі Kanban.
- Робітник не має доступу до репозиторію, автентифікації Codex або часу на узгодження результату.
- Зміна торкається секретів, сховищ облікових даних, приватних даних користувачів або виробничих систем обробки замовлень.
- Невелика пряма правка швидша та безпечніша, ніж запуск іншого агента.
- Завдання є лише дослідницьким і має призвести до написаного результату, а не до diff.
- Робітник може бути спокусений позначити Done лише на підставі самозвітності Codex.
## Правила власності

1. Hermes володіє життєвим циклом Kanban. Codex ніколи не повинен викликати `kanban_complete`, `kanban_block`, `kanban_create`, **gateway messaging** або будь‑який CLI дошки Hermes як заміну робітнику.
2. Hermes володіє остаточним прийняттям. Розглядай коміти/дифи Codex як ненадійні патчі, доки вони не будуть переглянуті та підтверджені.
3. Hermes володіє виконанням тестів. Codex може запускати тести, але ці запуски є лише рекомендаційними; необхідно повторно виконати перевірку від Hermes за допомогою канонічної обгортки репозиторію.
4. Hermes володіє безпекою. Якщо Codex змінює межі безпеки, ризикові шлюзи, поведінку живої торгівлі або обробку секретів, відхили lane, навіть якщо тести проходять.
5. Hermes володіє очищенням. Зупиняй завислі процеси Codex і видаляй тимчасові робочі дерева, коли вони більше не потрібні.
## Необхідний worktree та шаблон гілки

Ніколи не запускай Codex безпосередньо у спільному «брудному» checkout. Використовуй назву гілки/worktree, яка пов’язує lane із завданням Kanban і ізолює недовірені зміни.

Рекомендовані змінні:

```bash
TASK_ID="${HERMES_KANBAN_TASK:-t_manual}"
REPO="/path/to/repo"
BASE="$(git -C "$REPO" rev-parse --abbrev-ref HEAD)"
SAFE_TASK="$(printf '%s' "$TASK_ID" | tr -cd '[:alnum:]_-')"
BRANCH="codex/${SAFE_TASK}/$(date -u +%Y%m%d%H%M%S)"
WORKTREE="/tmp/${SAFE_TASK}-codex-lane"
```

Створи ізольований lane:

```bash
git -C "$REPO" fetch --all --prune
git -C "$REPO" worktree add -b "$BRANCH" "$WORKTREE" "$BASE"
git -C "$WORKTREE" status --short --branch
```

Якщо поточний робочий простір Kanban вже є ізольованим git worktree, створеним для цього завдання, ти можеш створити супутню гілку Codex всередині нього лише за умови, що `git status --short` чистий, окрім навмисних правок Hermes. Інакше створи окремий тимчасовий worktree і cherry-pick або скопіюй прийняті коміти назад після узгодження.

Очищення після узгодження:

```bash
git -C "$REPO" worktree remove "$WORKTREE"
git -C "$REPO" branch -D "$BRANCH"  # only after accepted commits were copied/cherry-picked or intentionally rejected
```

Збережи worktree, якщо він потрібен як артефакт для перегляду; запиши його у `codex_lane.artifacts` і згадай у handoff.
## Перевірки можливостей Codex

Запусти їх перед створенням процесу Codex. Відсутність Codex — це нормальна причина пропустити lane, а не блокувальник завдання, якщо Hermes може виконати його безпосередньо.

```bash
command -v codex
codex --version
codex features list | grep -i goals || true
```

Якщо потрібна підтримка `/goal`, увімкни або запусти її з прапорцем функції лише після перевірки доступності:

```bash
codex features enable goals || true
codex --enable goals --version
```

Автентифікація може здійснюватися через `OPENAI_API_KEY` або стан OAuth CLI Codex (зазвичай `~/.codex/auth.json`). Не виводь файли токенів. Відсутність `OPENAI_API_KEY` не є доказом того, що автентифікація недоступна.
## Вибір режиму

Використовуй `codex exec` для обмежених одноразових правок, коли Codex має самостійно завершитися:

```python
terminal(
    command="codex exec --full-auto '$(cat /tmp/codex_prompt.md)'",
    workdir=WORKTREE,
    background=True,
    pty=True,
    notify_on_complete=True,
)
```

Використовуй Codex `/goal` лише для більш масштабної багатокрокової роботи, яка виграє від довготривалого відстеження цілей. Запусти інтерактивно в сесії PTY/tmux або за допомогою `codex --enable goals`, якщо функція вимкнена за замовчуванням. Тримай ціль самодостатньою: шлях до репозиторію, ідентифікатор завдання, обмеження безпеки, дозволений обсяг, критерії прийняття, тести та очікування щодо комітів.

Приклад тексту цілі `/goal` для вставки в Codex:

```text
/goal Work in this repository only: <WORKTREE>. Task: <TASK_ID> <TITLE>.
Hermes owns the Kanban lifecycle; do not call Hermes kanban tools or messaging.
Create small commits on branch <BRANCH>. Follow the PMB safety constraints in the prompt.
Run the requested verification commands and report exact outputs. Stop after producing a diff and summary.
```

Не використовуйте `--yolo` для `prediction-market-bot` або репозиторіїв, чутливих до безпеки. Надавайте перевагу `--full-auto` в ізольованому робочому дереві, а потім покладайтеся на узгодження Hermes.
## Конструювання Prompt

Використовуй шаблон за посиланням у `templates/pmb-codex-lane-prompt.md` для роботи **prediction‑market‑bot**. Для інших репозиторіїв зберігай ту саму структуру і заміни безпековий блок, специфічний для PMB, на інваріанти, характерні для даного репозиторію.

Кожен Codex‑prompt має містити:

- `task_id`, назву та повні критерії прийняття у форматі Kanban.
- Шлях до репозиторію, шлях до робочого дерева, назву гілки та дозволений діапазон файлів.
- Явне твердження: **Hermes** керує життєвим циклом Kanban; **Codex** — лише lane‑вхід.
- Обов’язковий результат: короткий підсумок, список змінених файлів, коміти, запущені тести та відомі ризики.
- Заборонені дії: доступ до секретів, зовнішня передача повідомлень, зміна дошки, нерелевантні рефакторинги, оновлення залежностей, якщо це не потрібно.
- Команди верифікації, які **Codex** може виконати, та команди, які **Hermes** запустить після цього.

Для PMB включи ці обов’язкові безпекові обмеження **дослівно**:

```text
PMB safety constraints:
- live-SIM is paper-only; do not add or enable live REST order entry.
- Never use market orders.
- Do not add execution crossing or bypass price/risk checks.
- Do not fake passive fills, fills, PnL, order states, or reconciliation evidence.
- Do not weaken risk gates, limits, kill switches, or fail-closed behavior.
- Keep research/selection outside the C++ hot path unless explicitly requested.
- Do not read, print, write, or require secrets/tokens/credentials.
```
## Моніторинг, тайм‑аут та поведінка при kill

Запускай довгі lanes Codex у фоні з PTY та сповіщенням про завершення:

```python
result = terminal(
    command="codex exec --full-auto '$(cat /tmp/codex_prompt.md)'",
    workdir=WORKTREE,
    background=True,
    pty=True,
    notify_on_complete=True,
)
session_id = result["session_id"]
```

Моніторинг без втручання:

```python
process(action="poll", session_id=session_id)
process(action="log", session_id=session_id, limit=200)
process(action="wait", session_id=session_id, timeout=300)
```

Надсилай heartbeat Kanban кожні кілька хвилин для lanes, тривалість яких більше двох хвилин, напр. `kanban_heartbeat(note="Codex lane running in <WORKTREE>; waiting for tests/diff")`.

Умови kill:

- Відсутність корисного виводу протягом залишкового часу виконання завдання.
- Codex запитує секрети, виробничі облікові дані або зовнішні дозволи.
- Codex намагається змінювати файли поза межами worktree.
- Codex запускає несумісні переписування або надмірну зміну залежностей.
- Codex все ще працює близько до тайм‑ауту воркера, і безпечного часткового артефакту немає.

Команда kill:

```python
process(action="kill", session_id=session_id)
```

Після kill переглянь `git status --short`, збережи корисні патчі лише якщо це безпечно, і запиши `codex_lane.result: timed_out` або `rejected` разом із конкретним `rejected_reason`.
## Перелік перевірки узгодження

Hermes має виконати цей чек‑лист перед прийняттям будь‑якого результату **lane** Codex:

- [ ] `git -C <WORKTREE> status --short --branch` показує лише очікувані файли.
- [ ] `git -C <WORKTREE> diff --stat` і `git diff` були переглянуті Hermes.
- [ ] Не включено секрети, облікові дані, згенеровані кеші, несуміжні дані чи локальні артефакти.
- [ ] Обмеження безпеки PMB збережено: немає живого REST‑введення замовлень, ринкових замовлень, перетинів виконання, підроблених пасивних заповнень/PnL, ослаблення risk‑gate, секретів.
- [ ] Коміти Codex достатньо малі, щоб їх можна було чисто **cherry‑pick** або **squash**.
- [ ] Hermes сам запустив канонічні тести, використовуючи `scripts/run_tests.sh` для **Hermes Agent** або задокументований обгортковий скрипт репозиторію для інших репозиторіїв.
- [ ] Будь‑які тести, запущені **Codex**, перелічені окремо від тестів, запущених Hermes.
- [ ] Прийняті коміти/діфи були застосовані до робочого простору/гілки, що належить Hermes.
- [ ] Відхилена або часткова робота має конкретну причину та шлях до артефакту, якщо це корисно.

### Результати прийняття

- `accepted`: діф/коміти Codex були переглянуті, застосовані та підтверджені.
- `partial`: частину роботи Codex прийнято після правок або **cherry‑pick**; відхилені частини задокументовано.
- `rejected`: жодних змін Codex не прийнято; причина задокументована.
- `timed_out`: Codex перевищив бюджет **lane**; корисні артефакти можуть бути або не бути.
## kanban_complete Metadata Schema

Включи цей об’єкт у `metadata.codex_lane` для кожного завдання, у якому розглядалася доріжка. Якщо Codex не використовувався, встанови `used: false` і поясни причину в `rejected_reason` або в суміжному полі `notes`.

```json
{
  "codex_lane": {
    "used": true,
    "mode": "exec | goal | skipped",
    "worktree": "/absolute/path/to/codex/worktree",
    "branch": "codex/t_caa69668/20260508100000",
    "command": "codex exec --full-auto ...",
    "result": "accepted | rejected | partial | timed_out",
    "accepted_commits": ["<sha1>", "<sha2>"],
    "rejected_reason": "empty when fully accepted; otherwise concrete reason",
    "tests_run": [
      {"command": "scripts/run_tests.sh tests/tools/test_x.py", "exit_code": 0, "owner": "hermes"},
      {"command": "codex-reported: npm test", "exit_code": 0, "owner": "codex"}
    ],
    "artifacts": ["/absolute/path/to/log-or-patch"]
  }
}
```

Для завдань, які навмисно пропускають Codex:

```json
{
  "codex_lane": {
    "used": false,
    "mode": "skipped",
    "worktree": null,
    "branch": null,
    "command": null,
    "result": "rejected",
    "accepted_commits": [],
    "rejected_reason": "Direct Hermes edit was smaller and safer than spawning Codex.",
    "tests_run": [],
    "artifacts": []
  }
}
```
## Поширені підводні камені

1. Сприймати самозвіт Codex як верифікацію. Завжди переглядай diff і повторно запускай тести з Hermes.
2. Запускати Codex у «брудному» головному checkout користувача. Завжди ізолюй його у worktree/branch.
3. Дозволяти Codex керувати Kanban. Codex може підсумовувати прогрес, але Hermes записує стан дошки.
4. Забувати про інваріанти безпеки PMB у підказці. Відсутність тексту безпеки — це помилка налаштування lane.
5. Використовувати `/goal` для швидких правок. Надавай перевагу `codex exec`, якщо потрібне стійке багатокрокове продовження.
6. Припиняти «застряглий» lane без запису причин. `rejected_reason` має пояснювати рішення.
7. Приймати широке несумісне очищення лише тому, що тести проходять. Відхиляй або cherry‑pick лише зміни в межах області.
## Перелік перевірки

- [ ] Codex був пропущений або запущений лише після перевірки `command -v codex`, `codex --version` та, за потреби, перевірок функції **optional goals**.
- [ ] Codex працював лише в ізольованому **worktree/branch**.
- [ ] Prompt включав область завдання, правила власності, обмеження безпеки PMB (за потреби) та команди перевірки.
- [ ] Hermes переглянув `git diff` і файли, чутливі до безпеки.
- [ ] Hermes запустив канонічні тести самостійно.
- [ ] `kanban_complete.metadata.codex_lane` відповідає схемі вище.
- [ ] Тимчасові процеси та непотрібні **worktree** були очищені.