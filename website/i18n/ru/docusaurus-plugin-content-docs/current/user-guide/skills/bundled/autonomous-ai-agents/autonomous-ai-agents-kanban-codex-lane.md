---
title: "Kanban Codex полоса"
sidebar_label: "Kanban Codex Lane"
description: "Используй, когда worker Kanban Hermes хочет запустить Codex CLI в изолированном канале реализации, пока Hermes сохраняет владение жизненным циклом задачи, согласованием, тест…"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Канбан Codex Lane

Используй, когда рабочий Hermes Kanban хочет запустить Codex CLI в изолированном lane реализации, при этом Hermes сохраняет владение жизненным циклом задачи, согласованием, тестированием и передачей.
## Метаданные навыка

| | |
|---|---|
| Источник | Bundled (installed by default) → Встроенный (устанавливается по умолчанию) |
| Путь | `skills/autonomous-ai-agents/kanban-codex-lane` |
| Версия | `1.0.0` |
| Автор | Hermes Agent |
| Лицензия | MIT |
| Теги | `kanban`, `codex`, `worktrees`, `autonomous-agents`, `prediction-market-bot` |
| Связанные навыки | [`kanban-worker`](/docs/user-guide/skills/bundled/devops/devops-kanban-worker), [`codex`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-codex), [`hermes-agent`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-hermes-agent) |
:::info
Ниже представлено полное определение навыка, которое Hermes загружает при срабатывании этого навыка. Это то, что агент видит как инструкции, когда навык активен.
:::

# Kanban Codex Lane
## Обзор

Эта skill определяет облегчённую двойную‑канальную конвенцию Hermes+Codex для рабочих Kanban. Hermes всегда является владельцем задачи: он вызывает `kanban_show`, решает, уместен ли Codex, создаёт или выбирает изолированное рабочее пространство, запускает и контролирует Codex, сводит любые различия, выполняет проверку и записывает окончательный `kanban_complete` или `kanban_block` в качестве передачи. Codex используется только как входной канал. Вывод Codex не является сигналом завершения задачи, не является надёжным рецензентом и не имеет права напрямую записывать устойчивое состояние Kanban.

Конвенция существует, чтобы работник Hermes мог использовать Codex для ограниченной помощи в реализации без изменения диспетчера. Диспетчер всё равно должен запускать работников Hermes. Работник может при желании запустить Codex внутри собственного выполнения, а затем принять, частично принять или отклонить канал после независимого обзора и тестов.
## Когда использовать

Используй lane Codex, когда выполнены все условия:

- Задача Kanban относится к написанию кода, рефакторингу, документации, тестированию или механической миграции и имеет чёткие критерии приёмки.
- Ограниченный diff может быть оценён Hermes за один запуск.
- Репозиторий можно скопировать или проверить в изолированном git worktree/branch.
- Hermes может самостоятельно запустить соответствующие тесты после завершения Codex.
- Промпт может указать все ограничения безопасности и файлы, которые не должны изменяться.

Не используй lane Codex, если выполнено любое из следующих условий:

- Задача требует человеческого суждения, которое не отражено в теле Kanban.
- У работника нет доступа к репозиторию, аутентификации Codex или времени на согласование результата.
- Изменения затрагивают секреты, хранилища учётных данных, приватные пользовательские данные или производственные системы ввода заказов.
- Небольшое прямое редактирование быстрее и безопаснее, чем запуск другого агента.
- Задача носит исследовательский характер и должна привести к написанному документу, а не к diff.
- Работник может быть склонен пометить задачу как «Done», опираясь только на саморепорт Codex.
## Правила владения

1. Hermes отвечает за жизненный цикл Kanban. Codex никогда не должен вызывать `kanban_complete`, `kanban_block`, `kanban_create`, gateway messaging или любой CLI доски Hermes вместо рабочего процесса.
2. Hermes отвечает за окончательное принятие. Рассматривай коммиты/диффы Codex как недоверенные патчи до их проверки и верификации.
3. Hermes отвечает за выполнение тестов. Codex может запускать тесты, но эти запуски носят рекомендательный характер; требуемую верификацию необходимо повторить от Hermes с использованием канонической обёртки репозитория.
4. Hermes отвечает за безопасность. Если Codex изменяет границы безопасности, risk gates, поведение живой торговли или обработку секретов, отклоняй задачу, даже если тесты проходят.
5. Hermes отвечает за очистку. Убивай зависшие процессы Codex и удаляй временные рабочие деревья, когда они больше не нужны.
## Требуемый шаблон рабочей директории и ветки

Никогда не запускай Codex напрямую в совместном «грязном» checkout. Используй имя ветки/рабочей директории, которое связывает lane с задачей Kanban и изолирует недоверённые изменения.

Рекомендуемые переменные:

```bash
TASK_ID="${HERMES_KANBAN_TASK:-t_manual}"
REPO="/path/to/repo"
BASE="$(git -C "$REPO" rev-parse --abbrev-ref HEAD)"
SAFE_TASK="$(printf '%s' "$TASK_ID" | tr -cd '[:alnum:]_-')"
BRANCH="codex/${SAFE_TASK}/$(date -u +%Y%m%d%H%M%S)"
WORKTREE="/tmp/${SAFE_TASK}-codex-lane"
```

Создай изолированную lane:

```bash
git -C "$REPO" fetch --all --prune
git -C "$REPO" worktree add -b "$BRANCH" "$WORKTREE" "$BASE"
git -C "$WORKTREE" status --short --branch
```

Если текущая рабочая область Kanban уже является изолированным git‑worktree, созданным для этой задачи, ты можешь создать соседнюю ветку Codex внутри неё только в том случае, если `git status --short` чист, за исключением преднамерённых правок Hermes. В противном случае создай отдельный временный worktree и cherry-pick или скопируй принятые коммиты обратно после согласования.

Очистка после согласования:

```bash
git -C "$REPO" worktree remove "$WORKTREE"
git -C "$REPO" branch -D "$BRANCH"  # only after accepted commits were copied/cherry-picked or intentionally rejected
```

Сохрани worktree, если он нужен как артефакт для ревью; запиши его в `codex_lane.artifacts` и упомяни в handoff.
## Проверка возможностей Codex

Выполняй их перед запуском Codex. Отсутствие Codex — обычная причина пропустить lane, но не блокирующая задача, если Hermes может выполнить её напрямую.

⟦HOLD_3⟦

Если требуется поддержка `/goal`, включай или запускай с флагом функции только после проверки доступности:

⟦HOLD_4⟦

Аутентификация может происходить через `OPENAI_API_KEY` или состояние OAuth CLI Codex (обычно `~/.codex/auth.json`). Не выводи файлы токенов. Отсутствие `OPENAI_API_KEY` не является доказательством недоступности аутентификации.
## Выбор режима

Используй `codex exec` для ограниченных одноразовых правок, когда Codex должен завершиться сам:

```python
terminal(
    command="codex exec --full-auto '$(cat /tmp/codex_prompt.md)'",
    workdir=WORKTREE,
    background=True,
    pty=True,
    notify_on_complete=True,
)
```

Используй Codex `/goal` только для более широких многошаговых задач, которые выигрывают от долговременного отслеживания целей. Запусти интерактивно в PTY/tmux‑сессии или с `codex --enable goals`, если функция отключена по умолчанию. Держи цель самодостаточной: путь к репозиторию, идентификатор задачи, ограничения безопасности, разрешённый объём, критерии приёма, тесты и ожидания коммита.

Пример текста цели `/goal` для вставки в Codex:

```text
/goal Work in this repository only: <WORKTREE>. Task: <TASK_ID> <TITLE>.
Hermes owns the Kanban lifecycle; do not call Hermes kanban tools or messaging.
Create small commits on branch <BRANCH>. Follow the PMB safety constraints in the prompt.
Run the requested verification commands and report exact outputs. Stop after producing a diff and summary.
```

Не используй `--yolo` для репозиториев `prediction-market-bot` или задач, чувствительных к безопасности. Предпочитай `--full-auto` внутри изолированного рабочего дерева, а затем полагайся на согласование Hermes.
## Конструирование Prompt

Используй связанный шаблон в `templates/pmb-codex-lane-prompt.md` для работы над **prediction-market-bot**. Для остальных репозиториев сохраняй ту же структуру и заменяй блок безопасности, специфичный для PMB, на инварианты, характерные для конкретного репозитория.

Каждый Prompt для Codex должен включать:

- `task_id`, заголовок и полные критерии приёмки Kanban.
- Путь к репозиторию, путь к рабочему дереву, имя ветки и разрешённый диапазон файлов.
- Явное заявление: Hermes владеет жизненным циклом Kanban; Codex — только входной lane.
- Требуемый вывод: краткое резюме, изменённые файлы, коммиты, запущенные тесты и известные риски.
- Запрещённые действия: доступ к секретам, внешняя рассылка сообщений, изменение доски, нерелевантные рефакторинги, обновление зависимостей, если это не требуется.
- Команды проверки, которые Codex может выполнить, и команды, которые запустит Hermes после него.

Для PMB включи эти обязательные ограничения безопасности дословно:

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
## Мониторинг, тайм‑аут и поведение при принудительном завершении

Запускай длительные lanes Codex в фоне с PTY и уведомлением о завершении:

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

Отслеживай без вмешательства:

```python
process(action="poll", session_id=session_id)
process(action="log", session_id=session_id, limit=200)
process(action="wait", session_id=session_id, timeout=300)
```

Отправляй heartbeat Kanban каждые несколько минут для lanes длительностью более двух минут, например `kanban_heartbeat(note="Codex lane running in <WORKTREE>; waiting for tests/diff")`.

Условия завершения:

- Нет полезного вывода в течение оставшегося бюджета времени задачи.
- Codex запрашивает секреты, производственные учётные данные или внешние разрешения.
- Codex пытается изменять файлы за пределами worktree.
- Codex запускает несвязанные переписывания или «захламление» зависимостей.
- Codex всё ещё работает близко к тайм‑ауту воркера, и безопасного частичного артефакта нет.

Команда завершения:

```python
process(action="kill", session_id=session_id)
```

После завершения проверь `git status --short`, сохрани полезные патчи только если это безопасно, и запиши `codex_lane.result: timed_out` или `rejected` с конкретной `rejected_reason`.
## Список проверок согласования

Hermes должен выполнить этот чек‑лист перед принятием любого результата lane Codex:

- [ ] `git -C <WORKTREE> status --short --branch` показывает только ожидаемые файлы.
- [ ] `git -C <WORKTREE> diff --stat` и `git diff` были проверены Hermes.
- [ ] Не включены секреты, учётные данные, сгенерированные кэши, несвязанные данные или локальные артефакты.
- [ ] Ограничения безопасности PMB сохранены: нет живого ввода заказов REST, нет рыночных ордеров, нет пересечения исполнения, нет поддельных пассивных заполнений/PnL, нет ослабления риск‑гейта, нет секретов.
- [ ] Коммиты Codex достаточно малы, чтобы их можно было чисто cherry‑pick или squash.
- [ ] Hermes запустил канонические тесты самостоятельно, используя `scripts/run_tests.sh` для Hermes Agent или задокументированный обёрткой репозитория способ для других репозиториев.
- [ ] Любые тесты, запущенные Codex, перечислены отдельно от тестов, запущенных Hermes.
- [ ] Принятые коммиты/диффы были применены к рабочему пространству/ветке, принадлежащей Hermes.
- [ ] Отклонённая или частичная работа имеет конкретную причину и путь к артефакту, если это полезно.

Результаты принятия:

- `accepted`: дифф/коммиты Codex были проверены, применены и подтверждены.
- `partial`: часть работы Codex была принята после правок или cherry‑pick; отклонённые части задокументированы.
- `rejected`: изменения Codex не были приняты; причина задокументирована.
- `timed_out`: Codex превысил бюджет lane; полезные артефакты могут существовать или нет.
## kanban_complete Схема метаданных

Включи этот объект в `metadata.codex_lane` для каждой задачи, где рассматривалась lane. Если Codex не использовался, установи `used: false` и объясни причину в `rejected_reason` или в соседнем поле `notes`.

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

Для задач, в которых намеренно пропускается Codex:

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
## Распространённые подводные камни

1. Считать самóотчёт Codex подтверждением. Всегда проверяй `diff` и повторно запускай тесты от Hermes.
2. Запускать Codex в грязном основном checkout‑е пользователя. Всегда изолируй в `worktree/branch`.
3. Позволять Codex управлять Kanban. Codex может суммировать прогресс, но Hermes записывает состояние доски.
4. Забывать инварианты безопасности PMB в подсказке. Отсутствие текста безопасности — ошибка настройки lane.
5. Использовать `/goal` для быстрых правок. Предпочитай `codex exec`, если не требуется долговременное многошаговое продолжение.
6. Убивать зависший lane без записи причины. `rejected_reason` должен объяснять решение.
7. Принимать широкую несвязанную очистку только потому, что тесты проходят. Отклоняй или cherry‑pick только изменения в рамках задачи.
## Контрольный список проверки верификации

- [ ] Codex был пропущен или запущен только после проверок `command -v codex`, `codex --version` и, при необходимости, проверки функций целей.
- [ ] Codex запускался только в изолированном рабочем дереве/ветке.
- [ ] Промпт включал область задачи, правила владения, ограничения безопасности PMB при необходимости и команды проверки.
- [ ] Hermes проверил `git diff` и файлы, чувствительные к безопасности.
- [ ] Hermes запустил канонические тесты независимо.
- [ ] `kanban_complete.metadata.codex_lane` соответствует схеме выше.
- [ ] Временные процессы и лишние рабочие деревья были удалены.