---
sidebar_position: 3
title: "Куратор"
description: "Фоновое обслуживание созданных агентом навыков — отслеживание использования, устаревание, архивирование и проверка на основе LLM"
---

# Curator

Куратор — это фоновый процесс обслуживания **навыков, созданных агентом**. Он отслеживает, как часто каждый навык просматривается, используется и патчится, перемещает давно неиспользуемые навыки через состояния `active → stale → archived` и периодически запускает короткий обзор вспомогательной модели, предлагающий консолидацию или исправление дрейфа.

Он существует, чтобы навыки, создаваемые через [цикл самообучения](/user-guide/features/skills#agent-managed-skills-skill_manage-tool), не накапливались бесконечно. Каждый раз, когда агент решает новую задачу и сохраняет навык, этот навык попадает в `~/.hermes/skills/`. Без обслуживания в каталоге появляются десятки узких почти‑дубликатов, загрязняющих каталог и тратящих токены.

Куратор **никогда не трогает** встроенные навыки (поставляемые с репозиторием) или навыки, установленные из хаба (с [agentskills.io](https://agentskills.io)). Он проверяет только навыки, написанные самим агентом. Также он **никогда не удаляет автоматически** — наихудший результат — архивирование в `~/.hermes/skills/.archive/`, откуда их можно восстановить.

Отслеживает [issue #7816](https://github.com/NousResearch/hermes-agent/issues/7816).
## Как это работает

Куратор запускается проверкой бездействия, а не демоном cron. При старте CLI‑сессии и при периодическом тике внутри потока cron‑ticker шлюза Hermes проверяется, выполнено ли следующее:

1. Прошло достаточное время с последнего запуска куратора (`interval_hours`, по умолчанию **7 дней**), и
2. Агент был бездействующим достаточно долго (`min_idle_hours`, по умолчанию **2 часа**).

Если оба условия истинны, создаётся фоновой форк `AIAgent` — тот же шаблон, что используется для подсказок самообучающегося агента памяти/skill. Форк работает в собственном кэше подсказок и никогда не трогает активную беседу.

:::info First-run behavior
При новой установке (или при первом тике предкураторской установки после `hermes update`) куратор **не запускается сразу**. Первое наблюдение задаёт `last_run_at` значением «сейчас» и откладывает первый реальный проход на полный `interval_hours`. Это даёт тебе полный интервал для обзора библиотеки skill, закрепления важных элементов или полного отказа от куратора, прежде чем он коснётся её.

Если хочешь увидеть, что куратор *сделал бы* до реального запуска, выполни `hermes curator run --dry-run` — он выдаст тот же отчёт обзора, не изменяя библиотеку.
:::

Запуск состоит из двух фаз:

1. **Автоматические переходы** (детерминированные, без LLM). Skill, не использованные в течение `stale_after_days` (30), становятся `stale`; skill, не использованные в течение `archive_after_days` (90), перемещаются в `~/.hermes/skills/.archive/`.
2. **Обзор LLM** (один проход вспомогательной модели, `max_iterations=8`). Форк‑агент обследует созданные агентом skill, может прочитать любой из них с помощью `skill_view` и решает для каждого skill, сохранять, исправлять (через `skill_manage`), консолидировать перекрывающиеся или архивировать через терминальный инструмент. Консолидация рассматривает skill как полноценный пакет: если у skill есть `references/`, `templates/`, `scripts/`, `assets/` или относительные ссылки на эти пути, куратор должен либо оставить его автономным, пере‑разместить необходимые вспомогательные файлы и переписать пути, либо архивировать весь пакет без изменений — а не «сплющивать» только `SKILL.md` в файл `references/` другого skill.

Закреплённые skill недоступны ни для автоматических переходов куратора, ни для собственного инструмента агента `skill_manage`. См. [Pinning a skill](#pinning-a-skill) ниже.
## Конфигурация

Все настройки находятся в `config.yaml` в разделе `curator:` (не в `.env` — это не секрет). Значения по умолчанию:

```yaml
curator:
  enabled: true
  interval_hours: 168          # 7 days
  min_idle_hours: 2
  stale_after_days: 30
  archive_after_days: 90
```

Чтобы полностью отключить, установи `curator.enabled: false`.

### Запуск проверки на более дешёвой вспомогательной модели

Проход проверки LLM куратора — обычный слот вспомогательной задачи — `auxiliary.curator` — наряду с Vision, Compression, Session Search и т.д. «Auto» означает «использовать мою основную чат‑модель»; переопредели слот, чтобы привязать конкретного провайдера + модель для прохода проверки.

**Самый простой способ — `hermes model`:**

```bash
hermes model                   # → "Auxiliary models — side-task routing"
                               # → pick "Curator" → pick provider → pick model
```

Тот же выбор доступен в веб‑панели управления во вкладке **Models**.

**Прямая запись в `config.yaml` (эквивалент):**

```yaml
auxiliary:
  curator:
    provider: openrouter
    model: google/gemini-3-flash-preview
    timeout: 600               # generous — reviews can take several minutes
```

Оставив `provider: auto` (значение по умолчанию), ты направляешь проход проверки через любую свою основную чат‑модель, что соответствует поведению всех остальных вспомогательных задач.

:::note Legacy config
В более ранних версиях использовался одноразовый блок `curator.auxiliary.{provider,model}`. Этот путь всё ещё работает, но выводит строку журнала о депрецировании — пожалуйста, перейди к `auxiliary.curator`, как указано выше, чтобы куратор использовал ту же инфраструктуру (`hermes model`, вкладка Models в панели, `base_url`, `api_key`, `timeout`, `extra_body`) что и любая другая вспомогательная задача.
:::
## CLI

```bash
hermes curator status         # last run, counts, pinned list, LRU top 5
hermes curator run            # trigger a review now (blocks until the LLM pass finishes)
hermes curator run --background  # fire-and-forget: start the LLM pass in a background thread
hermes curator run --dry-run  # preview only — report without any mutations
hermes curator backup         # take a manual snapshot of ~/.hermes/skills/
hermes curator rollback       # restore from the newest snapshot
hermes curator rollback --list     # list available snapshots
hermes curator rollback --id <ts>  # restore a specific snapshot
hermes curator rollback -y         # skip the confirmation prompt
hermes curator pause          # stop runs until resumed
hermes curator resume
hermes curator pin <skill>    # never auto-transition this skill
hermes curator unpin <skill>
hermes curator restore <skill>  # move an archived skill back to active
```
## Резервные копии и откат

Перед каждым реальным проходом куратора Hermes делает tar.gz‑снимок каталога `~/.hermes/skills/` в `~/.hermes/skills/.curator_backups/<utc-iso>/skills.tar.gz`. Если проход архивирует или консолидирует что‑то, чего ты не хотел трогать, можно отменить весь запуск одной командой:

```bash
hermes curator rollback        # restore newest snapshot (with confirmation)
hermes curator rollback -y     # skip the prompt
hermes curator rollback --list # see all snapshots with reason + size
```

Сам откат обратим: перед заменой дерева навыков Hermes делает ещё один снимок с меткой `pre-rollback to <target-id>`, так что ошибочный откат можно отменить, прокатив вперёд к нему с помощью `--id`.

Также можно делать ручные снимки в любой момент командой `hermes curator backup --reason "before-refactor"`. Строка `--reason` попадает в `manifest.json` снимка и отображается в `--list`.

Снимки удаляются, оставляя только `curator.backup.keep` (по умолчанию 5) последних, чтобы ограничить использование диска:

```yaml
curator:
  backup:
    enabled: true
    keep: 5
```

Установи `curator.backup.enabled: false`, чтобы отключить автоматическое создание снимков. Ручная команда `hermes curator backup` всё равно работает, когда резервные копии отключены, только если сначала установить `enabled: true` — флаг управляет обоими путями симметрично, поэтому невозможно случайно пропустить предзапускный снимок перед изменяющими запусками.

`hermes curator status` также выводит пять наименее недавно использованных навыков — быстрый способ увидеть, какие из них скорее всего станут устаревшими следующими.

Те же подкоманды доступны как слеш‑команда `/curator` внутри запущенной сессии (CLI или платформ шлюза).
## Что означает «agent-created»

Навык считается созданным агентом, если его имя **не** присутствует в:

- `~/.hermes/skills/.bundled_manifest` (навыки, скопированные из репозитория при установке), и
- `~/.hermes/skills/.hub/lock.json` (навыки, установленные через `hermes skills install`).

Всё остальное в `~/.hermes/skills/` доступно куратору. Это включает:

- Навыки, которые агент сохранил через `skill_manage(action="create")` во время разговора.
- Навыки, созданные вручную с помощью собственного `SKILL.md`.
- Навыки, добавленные через внешние каталоги навыков, указанные в Hermes.

:::warning Ваши вручную написанные навыки выглядят так же, как сохранённые агентом
Происхождение здесь **бинарное** (bundled/hub vs. всё остальное). Куратор не может отличить вручную написанный навык, используемый в приватных рабочих процессах, от навыка, сохранённого циклом самообучения в середине сессии. Оба попадают в категорию «agent-created».

Перед первым реальным проходом (по умолчанию через 7 дней после установки) найди время, чтобы:

1. Запустить `hermes curator run --dry-run`, чтобы увидеть, что именно предложит куратор.
2. Использовать `hermes curator pin <name>`, чтобы закрепить всё, что не должно быть изменено.
3. Или установить `curator.enabled: false` в `config.yaml`, если ты предпочитаешь управлять библиотекой самостоятельно.

Архивы всегда можно восстановить через `hermes curator restore <name>`, но проще закрепить их заранее, чем потом собирать всё обратно.
:::

Если нужно защитить конкретный навык от любых изменений — например, вручную написанный навык, от которого ты зависишь — используй `hermes curator pin <name>`. См. следующий раздел.
## Pinning a skill

Pinning protects a skill from deletion — both the curator's automated archive passes and the agent's `skill_manage(action="delete")` tool call. Once a skill is pinned:

- The **curator** skips it during auto‑transitions (`active → stale → archived`), and its LLM review pass is instructed to leave it alone.
- The agent's `skill_manage` tool refuses a `delete` request for it, pointing the user to `hermes curator unpin <name>`. Patches and edits still go through, so the agent can improve a pinned skill's content as pitfalls arise without a pin/unpin/re‑pin dance.

Pin and unpin with:

```bash
hermes curator pin <skill>
hermes curator unpin <skill>
```

The flag is stored as `"pinned": true` on the skill's entry in `~/.hermes/skills/.usage.json`, so it survives across sessions.

Only **agent‑created** skills can be pinned — bundled and hub‑installed skills are never subject to curator mutation in the first place, and `hermes curator pin` will refuse with an explanatory message if you try.

If you want a stronger guarantee than “no deletion” — for instance, freezing a skill's content entirely while the agent still reads it — edit `~/.hermes/skills/<name>/SKILL.md` directly with your editor. The pin guards tool‑driven deletion, not your own filesystem access.
## Телеметрия использования

Куратор поддерживает сайдкар в `~/.hermes/skills/.usage.json` с одной записью на каждый **skill**:

```json
{
  "my-skill": {
    "use_count": 12,
    "view_count": 34,
    "last_used_at": "2026-04-24T18:12:03Z",
    "last_viewed_at": "2026-04-23T09:44:17Z",
    "patch_count": 3,
    "last_patched_at": "2026-04-20T22:01:55Z",
    "created_at": "2026-03-01T14:20:00Z",
    "state": "active",
    "pinned": false,
    "archived_at": null
  }
}
```

Счётчики увеличиваются, когда:

- `view_count`: агент вызывает `skill_view` для **skill**.
- `use_count`: **skill** загружается в подсказку беседы.
- `patch_count`: `skill_manage patch/edit/write_file/remove_file` выполняется для **skill**.

Встроенные и установленные из хаба **skill** явно исключены из записей телеметрии.
## Отчёты за каждый запуск

Каждый запуск куратора записывает каталог с меткой времени в `~/.hermes/logs/curator/`:

```
~/.hermes/logs/curator/
└── 20260429-111512/
    ├── run.json      # machine-readable: full fidelity, stats, LLM output
    └── REPORT.md     # human-readable summary
```

`REPORT.md` — быстрый способ увидеть, что сделал конкретный запуск: какие навыки были переключены, что сказал LLM‑рецензент, какие навыки он исправил. Удобно для аудита без необходимости искать в `agent.log`.

### Карта переименований в сводке

Если запуск консолидировал несколько навыков под одной «зонтичной» группой (или объединил почти одинаковые), пользовательская сводка, выводимая в конце запуска, содержит явную карту переименований, показывающую каждую пару `old-name → new-name`, применённую куратором. Это дополнительно к строкам переходов по каждому навыку, так что когда происходит волна переименований, их можно сразу увидеть без сравнения JSON‑отчёта. Подсказка также появляется под `hermes curator pin`, чтобы ты мог сразу закрепить новое название, если хочешь зафиксировать новую метку.
## Восстановление архивированного skill

Если куратор архивировал то, что тебе всё ещё нужно:

```bash
hermes curator restore <skill-name>
```

Это перемещает skill из `~/.hermes/skills/.archive/` в активное дерево и сбрасывает его состояние в `active`. Восстановление отклоняется, если под тем же именем уже установлен связанный или из хаба установленный skill (он будет перекрывать upstream).
## Отключение по среде

Куратор включён по умолчанию. Чтобы отключить его:

- **Только для одного профиля:** отредактируй `~/.hermes/config.yaml` (или конфигурацию активного профиля) и установи `curator.enabled: false`.
- **Только на один запуск:** `hermes curator pause` — пауза сохраняется между сессиями; используй `resume`, чтобы снова включить.

Куратор также не запускается, если не прошёл `min_idle_hours`, поэтому на активной машине разработки он естественно работает только в периоды простоя.
## См. также

- [Skills System](/user-guide/features/skills) — как работают навыки в целом и цикл самообучения, который их создаёт
- [Memory](/user-guide/features/memory) — параллельный фоновый процесс, поддерживающий долгосрочную память
- [Bundled Skills Catalog](/reference/skills-catalog)
- [Issue #7816](https://github.com/NousResearch/hermes-agent/issues/7816) — оригинальное предложение и обсуждение дизайна