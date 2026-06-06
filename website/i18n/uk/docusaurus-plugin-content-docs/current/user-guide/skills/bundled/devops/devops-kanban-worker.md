---
title: "Kanban Worker — підводні камені, приклади та крайні випадки для Hermes Kanban workers"
sidebar_label: "Kanban Worker"
description: "Підводні камені, приклади та крайні випадки для Hermes Kanban workers"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Kankan Worker

Підводні камені, приклади та крайові випадки для Hermes Kanban workers. Сам цикл життя автоматично вставляється у системний підказник кожного worker‑а як `KANBAN_GUIDANCE` (з `agent/prompt_builder.py`); цей skill завантажується, коли потрібні детальніші відомості про конкретні сценарії.
## Метадані навички

| | |
|---|---|
| Джерело | Вбудовано (встановлюється за замовчуванням) |
| Шлях | `skills/devops/kanban-worker` |
| Версія | `2.0.0` |
| Платформи | linux, macos, windows |
| Теги | `kanban`, `multi-agent`, `collaboration`, `workflow`, `pitfalls` |
| Пов’язані навички | [`kanban-orchestrator`](/docs/user-guide/skills/bundled/devops/devops-kanban-orchestrator) |
:::info
Наступне — повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції, коли навичка активна.
:::

# Kanban Worker — підводні камені та приклади

> Ви бачите цю навичку, тому що диспетчер Hermes Kanban запустив вас як робітника з `--skills kanban-worker` — вона завантажується автоматично для кожного диспетчерованого робітника. **Життєвий цикл** (6 кроків: orient → work → heartbeat → block/complete) також міститься у блоці `KANBAN_GUIDANCE`, який автоматично вставляється у ваш системний підказник. Ця навичка — детальніший опис: правильна передача, діагностика повторних спроб, крайові випадки.
## Обробка робочого простору

Твій тип робочого простору визначає, як ти маєш поводитися всередині `$HERMES_KANBAN_WORKSPACE`:

| Тип | Що це | Як працювати |
|---|---|---|
| `scratch` | Свіжий тимчасовий каталог, лише твій | Читати/писати довільно; буде видалено (GC) після архівації завдання. |
| `dir:<path>` | Спільний постійний каталог | Інші запуски будуть читати те, що ти записав. Розглядай його як довготривалу пам'ять. Шлях гарантовано абсолютний (ядро відхиляє відносні шляхи). |
| `worktree` | Git worktree у розв’язному шляху | Якщо `.git` не існує, спочатку виконай `git worktree add <path> ${HERMES_KANBAN_BRANCH:-wt/$HERMES_KANBAN_TASK}` у головному репозиторії, потім `cd` і працюй звично. Робити коміти тут. |
## Ізоляція орендаря

Якщо встановлено `$HERMES_TENANT`, завдання належить до простору імен орендаря. При читанні або записі постійної пам’яті додавай префікс орендаря до записів пам’яті, щоб контекст не протікав між орендарями:

- Good: `business-a: Acme is our biggest customer`
- Bad (leaks): `Acme is our biggest customer`
## Good summary + metadata shapes

`kanban_complete(summary=..., metadata=...)` — це спосіб, яким downstream‑робітники дізнаються, що ти зробив. Працюючі шаблони:

**Coding task:**
```python
kanban_complete(
    summary="shipped rate limiter — token bucket, keys on user_id with IP fallback, 14 tests pass",
    metadata={
        "changed_files": ["rate_limiter.py", "tests/test_rate_limiter.py"],
        "tests_run": 14,
        "tests_passed": 14,
        "decisions": ["user_id primary, IP fallback for unauthenticated requests"],
    },
)
```

**Coding task that needs human review (review‑required):**

Для більшості завдань, що змінюють код, роботу не можна вважати *завершеною*, доки її не переглянув людина‑рецензент. Тому використай `kanban_block` замість `kanban_complete`, вказавши `reason` з префіксом `review-required: `, щоб дашборд позначив рядок як такий, що потребує перегляду. Спочатку занеси структуровані метадані (змінені файли, кількість тестів, diff/PR‑url) у коментар, бо `kanban_block` передає лише людсько‑читабельну причину — коментарі є стійким каналом анотацій. Рецензент або схвалює і виконує `hermes kanban unblock <id>` (що повертає тебе до теми коментаря для подальших дій), або просить внести зміни іншим коментарем.

```python
import json

kanban_comment(
    body="review-required handoff:\n" + json.dumps({
        "changed_files": ["rate_limiter.py", "tests/test_rate_limiter.py"],
        "tests_run": 14,
        "tests_passed": 14,
        "diff_path": "/path/to/worktree",  # or PR url if pushed
        "decisions": ["user_id primary, IP fallback for unauthenticated requests"],
    }, indent=2),
)
kanban_block(
    reason="review-required: rate limiter shipped, 14/14 tests pass — needs eyes on the user_id/IP fallback choice before merging",
)
```

Використовуй `kanban_complete` лише коли завдання дійсно завершене — наприклад, виправлення однорядкової помилки, зміна документації без функціональних наслідків або дослідницьке завдання, де артефакт — це сам запис.

**Research task:**
```python
kanban_complete(
    summary="3 competing libraries reviewed; vLLM wins on throughput, SGLang on latency, Tensorrt-LLM on memory efficiency",
    metadata={
        "sources_read": 12,
        "recommendation": "vLLM",
        "benchmarks": {"vllm": 1.0, "sglang": 0.87, "trtllm": 0.72},
    },
)
```

**Review task:**
```python
kanban_complete(
    summary="reviewed PR #123; 2 blocking issues found (SQL injection in /search, missing CSRF on /settings)",
    metadata={
        "pr_number": 123,
        "findings": [
            {"severity": "critical", "file": "api/search.py", "line": 42, "issue": "raw SQL concat"},
            {"severity": "high", "file": "api/settings.py", "issue": "missing CSRF middleware"},
        ],
        "approved": False,
    },
)
```

Формуй `metadata` так, щоб downstream‑парсери (рецензенти, агрегатори, планувальники) могли їх використовувати без повторного читання твоєї прозової частини.
## Присвоєння карток, які ти справді створив

Якщо під час виконання твоєї програми були створені нові kanban‑завдання (за допомогою `kanban_create`), передай їхні ідентифікатори у `created_cards` під час виклику `kanban_complete`. Ядро перевіряє, чи існує кожен ідентифікатор і чи був він створений твоїм профілем; будь‑який фантомний ідентифікатор блокує завершення з помилкою, у якій перераховано, що саме пішло не так, а відхилена спроба назавжди записується у журнал подій завдання. **Перелічуй лише ті ідентифікатори, які ти отримав з успішного результату `kanban_create` — ніколи не вигадуй ідентифікатори в тексті, не копіюй їх з попередніх запусків, не претендуй на картки, створені іншим виконавцем.**

```python
# GOOD — capture return values, then claim them.
c1 = kanban_create(title="remediate SQL injection", assignee="security-worker")
c2 = kanban_create(title="fix CSRF middleware", assignee="web-worker")

kanban_complete(
    summary="Review done; spawned remediations for both findings.",
    metadata={"pr_number": 123, "approved": False},
    created_cards=[c1["task_id"], c2["task_id"]],
)
```

```python
# BAD — claiming ids you don't have captured return values for.
kanban_complete(
    summary="Created remediation cards t_a1b2c3d4, t_deadbeef",  # hallucinated
    created_cards=["t_a1b2c3d4", "t_deadbeef"],                   # → gate rejects
)
```

Якщо виклик `kanban_create` завершився помилкою (exception, tool_error), картка НЕ була створена — не додавай для неї фантомний ідентифікатор. Спробуй створити ще раз або опусти ідентифікатор і згадай про помилку у своєму підсумку. Перевірка prose‑scan також виявляє посилання типу `t_<hex>` у твоєму вільному підсумку, які не розв’язуються; вони не блокують завершення, а відображаються як рекомендаційні попередження у завданні на панелі інструментів.
## Причини блокування, на які швидко відповідають

Bad: `"stuck"` — у людини немає контексту.

Good: одне речення, що називає конкретне рішення, яке потрібно прийняти. Довший контекст залиш у вигляді коментаря.

```python
kanban_comment(
    task_id=os.environ["HERMES_KANBAN_TASK"],
    body="Full context: I have user IPs from Cloudflare headers but some users are behind NATs with thousands of peers. Keying on IP alone causes false positives.",
)
kanban_block(reason="Rate limit key choice: IP (simple, NAT-unsafe) or user_id (requires auth, skips anonymous endpoints)?")
```

Повідомлення про блокування — це те, що відображається в дашборді / сповіщенні шлюзу. Коментар — це більш глибокий контекст, який читає людина, коли відкриває завдання.
## Серцебиття, які варто надсилати

Хороші heartbeat‑повідомлення називають прогрес: `"epoch 12/50, loss 0.31"`, `"scanned 1.2M/2.4M rows"`, `"uploaded 47/120 videos"`.

Погані heartbeat‑повідомлення: `"still working"`, порожні нотатки, інтервали менше секунди. Надсилай їх максимум кожні кілька хвилин; для завдань тривалістю менше ~2 хвилин їх можна повністю пропускати.
## Сценарії повторних спроб

Якщо ти відкриваєш задачу і `kanban_show` повертає `runs: [...]` з однією або кількома закритими спробами, це повторна спроба. `outcome` / `summary` / `error` попередніх спроб підкажуть, що саме не спрацювало. Не повторюй цей шлях. Типові діагностики повторних спроб:

- `outcome: "timed_out"` — попередня спроба досягла `max_runtime_seconds`. Можливо, треба розбити роботу на частини або скоротити її.
- `outcome: "crashed"` — OOM або segfault. Зменши використання пам’яті.
- `outcome: "spawn_failed"` + `error: "..."` — зазвичай проблема в конфігурації профілю (відсутні облікові дані, неправильний PATH). Запитай у людини через `kanban_block` замість сліпого повторення.
- `outcome: "reclaimed"` + `summary: "task archived..."` — оператор архівував задачу, залишивши її недоступною для попередньої спроби; ймовірно, тобі взагалі не слід її виконувати, ретельно перевір статус.
- `outcome: "blocked"` — попередня спроба була заблокована; коментар розблокування має вже бути в темі.
## Маршрутизація сповіщень

Ти можеш налаштувати шлюз для отримання сповіщень про завдання Kanban з різних профілів, додавши `notification_sources` у `~/.hermes/config.yaml`.
- `notification_sources: ['*']` приймає підписки від усіх профілів.
- `notification_sources: ['default', 'zilor-ppt']` або `"default,zilor-ppt"` обмежує підписки вказаними профілями.
- Якщо ключ пропущено, зберігається поведінка за замовчуванням (ізоляція профілів).
## Не робити

- Не викликай `delegate_task` як заміну `kanban_create`. `delegate_task` призначений для коротких підзадач розуміння всередині ТВОГО запуску; `kanban_create` використовується для передачі між агентами, які тривають довше одного циклу API.
- Не змінюй файли поза `$HERMES_KANBAN_WORKSPACE`, якщо тільки тіло завдання не вказує інше.
- Не створюй подальші завдання, призначені собі — призначай їх відповідному спеціалісту.
- Не завершуй завдання, яке ти фактично не завершив. Замість цього заблокуй його.
## Підводні камені

**Стан завдання може змінитися між відправленням та запуском.** Після того, як диспетчер отримав завдання і до того, як процес фактично завантажився, завдання могло бути заблоковано, переназначено або заархівовано. Завжди спочатку виконуй `kanban_show`. Якщо він повідомляє `blocked` або `archived`, зупинись — не слід його виконувати.

**Робочий простір може містити застарілі артефакти.** Особливо робочі простори `dir:` та `worktree` можуть містити файли від попередніх запусків. Прочитай ланцюжок коментарів — зазвичай там пояснюється, чому ти запускаєш знову і який стан має робочий простір.

**Не покладайся лише на CLI, коли доступна інструкція.** Інструменти `kanban_*` працюють у всіх термінальних бекендах (Docker, Modal, SSH). `hermes kanban <verb>` у твоєму термінальному інструменті не спрацює в контейнеризованих бекендах, бо CLI там не встановлено. Якщо сумніваєшся, використай інструмент.
## CLI запасний варіант (для скриптів)

Кожен інструмент має CLI‑еквівалент для людських операторів та скриптів:
- `kanban_show` ↔ `hermes kanban show <id> --json`
- `kanban_complete` ↔ `hermes kanban complete <id> --summary "..." --metadata '{...}'`
- `kanban_block` ↔ `hermes kanban block <id> "reason"`
- `kanban_create` ↔ `hermes kanban create "title" --assignee <profile> [--parent <id>]`
- тощо.

Використовуй інструменти всередині агента; CLI призначений для людини в терміналі.