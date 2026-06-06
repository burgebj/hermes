---
title: "Kanban Worker — Подводные камни, примеры и крайние случаи для Hermes Kanban workers"
sidebar_label: "Kanban Worker"
description: "Подводные камни, примеры и граничные случаи для Hermes Kanban workers"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Kanban Worker

Ловушки, примеры и крайние случаи для Hermes Kanban workers. Сам жизненный цикл автоматически внедряется в системный запрос каждого worker'а как `KANBAN_GUIDANCE` (из `agent/prompt_builder.py`); этот навык загружается, когда требуется более подробная информация о конкретных сценариях.
## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/devops/kanban-worker` |
| Version | `2.0.0` |
| Platforms | linux, macos, windows |
| Tags | `kanban`, `multi-agent`, `collaboration`, `workflow`, `pitfalls` |
| Related skills | [`kanban-orchestrator`](/docs/user-guide/skills/bundled/devops/devops-kanban-orchestrator) |
:::info
Следующее — полное определение навыка, которое Hermes загружает, когда этот навык активируется. Это то, что агент видит как инструкции, когда навык активен.
:::

# Kanban Worker — подводные камни и примеры

> Ты видишь этот навык, потому что диспетчер Kanban в Hermes запустил тебя как рабочего с `--skills kanban-worker` — он загружается автоматически для каждого диспетчируемого рабочего. **Жизненный цикл** (6 шагов: orient → work → heartbeat → block/complete) также находится в блоке `KANBAN_GUIDANCE`, который автоматически вставляется в твой системный запрос. Этот навык содержит более подробную информацию: правильные формы передачи, диагностика повторных попыток, граничные случаи.
## Работа с рабочим пространством

Тип рабочего пространства определяет, как тебе следует вести себя внутри `$HERMES_KANBAN_WORKSPACE`:

| Тип | Что это | Как работать |
|---|---|---|
| `scratch` | Свежий временный каталог, только твой | Чтение/запись без ограничений; будет удалён сборщиком мусора, когда задача будет заархивирована. |
| `dir:<path>` | Общий постоянный каталог | Другие запуски будут читать то, что ты записываешь. Рассматривай его как долговременное состояние. Путь гарантированно абсолютный (ядро отклоняет относительные пути). |
| `worktree` | Git worktree по разрешённому пути | Если `.git` не существует, сначала выполни `git worktree add <path> ${HERMES_KANBAN_BRANCH:-wt/$HERMES_KANBAN_TASK}` из основного репозитория, затем перейди в каталог и работай как обычно. Делай коммиты здесь. |
## Изоляция арендаторов

Если установлен `$HERMES_TENANT`, задача принадлежит пространству имён арендатора. При чтении или записи постоянной памяти добавляй префикс арендатора к записям памяти, чтобы контекст не просачивался между арендаторами:

- Правильно: `business-a: Acme is our biggest customer`
- Неправильно (утечка): `Acme is our biggest customer`
## Хорошее резюме + формы метаданных

`kanban_complete(summary=..., metadata=...)` — это способ, которым downstream‑работники читают, что ты сделал. Работают такие шаблоны:

**Задача по программированию:**
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

**Задача по программированию, требующая человеческого обзора (review‑required):**

Для большинства задач, меняющих код, работа не считается действительно *завершённой*, пока её не проверил человек. Блокируй вместо завершения, добавив `reason` с префиксом `review-required: `, чтобы dashboard отображал строку как требующую обзора. Сначала выложи структурированные метаданные (изменённые файлы, количество тестов, diff/PR‑url) в комментарий, поскольку `kanban_block` передаёт только человекочитаемую причину — комментарии являются надёжным каналом аннотаций. Рецензент либо одобряет и запускает `hermes kanban unblock <id>` (который перезапускает тебя с цепочкой комментариев для дальнейших вопросов), либо запрашивает изменения через другой комментарий.

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

Используй `kanban_complete` только когда задача действительно завершена — например, исправление опечатки в одну строку, изменение документации без функциональных последствий или исследовательская задача, где артефакт — это сам текст отчёта.

**Исследовательская задача:**
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

**Задача обзора:**
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

Формируй `metadata` так, чтобы downstream‑парсеры (рецензенты, агрегаторы, планировщики) могли использовать их без повторного чтения твоего текста.
## Утверждение карточек, которые ты действительно создал

Если твой запуск создал новые задачи kanban (через `kanban_create`), передай их идентификаторы в `created_cards` при вызове `kanban_complete`. Ядро проверит, что каждый идентификатор существует и был создан твоим профилем; любой «фантомный» идентификатор блокирует завершение с ошибкой, в которой перечислено, что пошло не так, а отклонённая попытка навсегда фиксируется в журнале событий задачи. **Указывай только те идентификаторы, которые ты получил из успешного возвращаемого значения `kanban_create` — никогда не выдумывай идентификаторы в тексте, никогда не копируй их из предыдущих запусков, никогда не заявляй карточки, созданные другим работником.**

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

Если вызов `kanban_create` завершился неудачей (исключение, `tool_error`), карточка НЕ была создана — не включай для неё фантомный идентификатор. Повтори попытку создания или опусти идентификатор и упомяни о неудаче в своём резюме. Проход «prose‑scan» также обнаруживает ссылки вида `t_<hex>` в твоём свободном резюме, которые не разрешаются; они не блокируют завершение, но отображаются как advisory‑предупреждения в задаче на панели управления.
## Причины блокировки, на которые быстро отвечают

Bad: `"stuck"` — у человека нет контекста.

Good: одно предложение, назвавшее конкретное решение, которое тебе нужно принять. Более длинный контекст оставь в виде комментария.

```python
kanban_comment(
    task_id=os.environ["HERMES_KANBAN_TASK"],
    body="Full context: I have user IPs from Cloudflare headers but some users are behind NATs with thousands of peers. Keying on IP alone causes false positives.",
)
kanban_block(reason="Rate limit key choice: IP (simple, NAT-unsafe) or user_id (requires auth, skips anonymous endpoints)?")
```

Сообщение блокировки — это то, что отображается в dashboard / gateway notifier. Комментарий — более глубокий контекст, который человек читает, открывая задачу.
## Heartbeats, которые стоит отправлять

Хорошие heartbeats, описывающие прогресс: `"epoch 12/50, loss 0.31"`, `"scanned 1.2M/2.4M rows"`, `"uploaded 47/120 videos"`.

Плохие heartbeats: `"still working"`, пустые заметки, интервалы менее секунды. Отправляй не чаще, чем раз в несколько минут; полностью пропускай для задач короче ~2 минут.
## Сценарии повторных попыток

Если ты открываешь задачу и `kanban_show` возвращает `runs: [...]` с одним или несколькими закрытыми запусками, это повтор. `outcome` / `summary` / `error` предыдущих запусков подскажут, что не сработало. Не повторяй тот же путь. Типичная диагностика повторов:

- `outcome: "timed_out"` — предыдущая попытка достигла `max_runtime_seconds`. Возможно, потребуется разбить работу на части или сократить её.
- `outcome: "crashed"` — OOM или segfault. Снизь объём памяти.
- `outcome: "spawn_failed"` + `error: "..."` — обычно проблема конфигурации профиля (отсутствуют учётные данные, неверный PATH). Спроси человека через `kanban_block` вместо слепого повторения.
- `outcome: "reclaimed"` + `summary: "task archived..."` — оператор архивировал задачу, и предыдущий запуск больше не актуален; скорее всего, тебе не следует её выполнять, проверь статус внимательно.
- `outcome: "blocked"` — предыдущая попытка была заблокирована; комментарий о разблокировке уже должен быть в ветке обсуждения.
## Маршрутизация уведомлений

Ты можешь настроить шлюз для получения кросс‑профильных уведомлений о задачах Kanban, добавив `notification_sources` в `~/.hermes/config.yaml`.
- `notification_sources: ['*']` принимает подписки со всех профилей.
- `notification_sources: ['default', 'zilor-ppt']` или `"default,zilor-ppt"` ограничивает подписки указанными профилями.
- Если ключ опустить, сохраняется поведение по умолчанию (изоляция профилей).
## Не делай

- Не вызывай `delegate_task` вместо `kanban_create`. `delegate_task` предназначен для коротких подзадач рассуждения внутри ТВОЁГО выполнения; `kanban_create` используется для передачи задач между агентами, которые продолжаются дольше одного цикла API.
- Не изменяй файлы за пределами `$HERMES_KANBAN_WORKSPACE`, если только тело задачи не указывает иначе.
- Не создавай последующие задачи, назначенные себе — назначай их нужному специалисту.
- Не завершай задачу, которую на самом деле не закончил. Заблокируй её вместо этого.
## Подводные камни

**Состояние задачи может измениться между отправкой и запуском.** Между тем, как диспетчер заявил задачу, и тем, как ваш процесс действительно запустился, задача могла быть заблокирована, переназначена или заархивирована. Сначала всегда вызывай `kanban_show`. Если он сообщает `blocked` или `archived`, остановись — тебе не следует её выполнять.

**Рабочее пространство может содержать устаревшие артефакты.** Особенно рабочие пространства `dir:` и `worktree` могут иметь файлы от предыдущих запусков. Прочитай цепочку комментариев — обычно там объясняется, почему ты запускаешься повторно и в каком состоянии находится рабочее пространство.

**Не полагайся на CLI, если доступно руководство.** Инструменты `kanban_*` работают во всех терминальных бэкендах (Docker, Modal, SSH). `hermes kanban <verb>` из твоего терминального инструмента не будет работать в контейнерных бэкендах, потому что CLI там не установлен. При сомнениях используй инструмент.
## CLI fallback (для скриптов)

Каждый инструмент имеет эквивалент в виде CLI для человеческих операторов и скриптов:
- `kanban_show` ↔ `hermes kanban show <id> --json`
- `kanban_complete` ↔ `hermes kanban complete <id> --summary "..." --metadata '{...}'`
- `kanban_block` ↔ `hermes kanban block <id> "reason"`
- `kanban_create` ↔ `hermes kanban create "title" --assignee <profile> [--parent <id>]`
- и т.д.

Используй инструменты внутри агента; CLI предназначен для человека в терминале.