---
title: "Hermes S6 Container надзор"
sidebar_label: "Hermes S6 Container Supervision"
description: "Измени, отладь или расширь дерево супервизии s6-overlay внутри Docker‑образа Hermes Agent — добавляя новые сервисы, отлаживая шлюзы профилей, понимая…"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Hermes S6 Container Supervision

Измени, отладь или расширь дерево надзора s6-overlay внутри Docker‑образа Hermes Agent — добавляй новые сервисы, отлаживай шлюзы профилей, разбирайся в шаблоне основной программы Architecture B.
## Метаданные навыка

| | |
|---|---|
| Источник | Встроенный (устанавливается по умолчанию) |
| Путь | `skills/software-development/hermes-s6-container-supervision` |
| Версия | `1.0.0` |
| Автор | Hermes Agent |
| Лицензия | MIT |
| Теги | `docker`, `s6`, `supervision`, `gateway`, `profiles` |
| Связанные навыки | [`hermes-agent`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-hermes-agent), `hermes-agent-dev` |
## Справка: полный SKILL.md

:::info
Ниже представлено полное определение навыка, которое Hermes загружает при срабатывании этого навыка. Это то, что агент видит как инструкции, когда навык активен.
:::

# Hermes s6-overlay Container Supervision
## Когда использовать этот skill

Load this skill when you're working on:
- Добавление или удаление статической службы в образе Hermes Docker (то, что должно контролироваться при каждом запуске контейнера, например dashboard)
- Диагностика, почему шлюз per‑profile не запускается, не перезапускается или не сохраняется после `docker restart`
- Понимание, почему CMD контейнера — `/opt/hermes/docker/main-wrapper.sh` и как аргументы, начинающиеся с тире, попадают в программу пользователя
- Модификация загрузочных скриптов `cont-init.d` (переназначение UID, заполнение томов, согласование профилей)
- Изменение сгенерированного run‑script для шлюзов per‑profile (Phase 4)

Если ты просто запускаешь Hermes Agent и хочешь использовать Docker, см. `website/docs/user-guide/docker.md`.
## Обзор архитектуры

<!-- ascii-guard-ignore -->
```
/init                                  ← PID 1 (s6-overlay v3.2.3.0)
├── cont-init.d                        ← oneshot setup, runs as root
│   ├── 01-hermes-setup                ← docker/stage2-hook.sh
│   │   ├── UID/GID remap
│   │   ├── chown /opt/data
│   │   ├── chown /opt/data/profiles (every boot)
│   │   ├── seed .env / config.yaml / SOUL.md
│   │   └── skills_sync.py
│   └── 02-reconcile-profiles          ← hermes_cli.container_boot
│       ├── chown /run/service (hermes-writable for runtime register)
│       └── walk $HERMES_HOME/profiles/<name>/gateway_state.json
│           → recreate /run/service/gateway-<name>/
│           → auto-start only those with prior_state == "running"
│
├── s6-rc.d (static services, in /etc/s6-overlay/s6-rc.d/)
│   ├── main-hermes/run                ← exec sleep infinity (no-op slot)
│   └── dashboard/run                  ← if HERMES_DASHBOARD=1, runs `hermes dashboard`
│
├── /run/service (s6-svscan watches; tmpfs)
│   ├── gateway-coder/                 ← runtime-registered per-profile
│   │   ├── type        ("longrun")
│   │   ├── run         ("#!/command/with-contenv sh ... exec s6-setuidgid hermes hermes -p coder gateway run")
│   │   ├── down        (marker — present means "registered but don't auto-start")
│   │   └── log/run     (s6-log → $HERMES_HOME/logs/gateways/coder/current)
│   └── ...
│
└── CMD ("main program")               ← /opt/hermes/docker/main-wrapper.sh
    └── routes user args: bare exec | hermes subcommand | hermes (no args)
        — exec'd by /init with stdin/stdout/stderr inherited (TTY for --tui)
```
<!-- ascii-guard-ignore-end -->
## Ключевые файлы

| Путь | Роль |
|---|---|
| `Dockerfile` | установка s6-overlay + настройка `cont-init.d` + `ENTRYPOINT ["/init", "/opt/hermes/docker/main-wrapper.sh"]` |
| `docker/stage2-hook.sh` | «Старая логика entrypoint» — переименование UID, `chown`, инициализация, синхронизация навыков. Запускается как `cont-init.d/01-hermes-setup`. |
| `docker/cont-init.d/02-reconcile-profiles` | Вызывает `hermes_cli.container_boot` при каждой загрузке для восстановления слотов шлюза профилей из постоянного тома. |
| `docker/main-wrapper.sh` | `CMD` контейнера. Маршрутизирует пользовательские аргументы, переключается на hermes через `s6-setuidgid`, `exec` выбранной программы. |
| `docker/s6-rc.d/main-hermes/run` | Пустая операция `sleep infinity` — слот существует, чтобы пакет пользователя s6-rc был валиден; основной hermes запускается как `CMD`, а не как управляемый сервис. |
| `docker/s6-rc.d/dashboard/run` | Условный сервис — `exec sleep infinity`, если `HERMES_DASHBOARD` не истинно. |
| `docker/entrypoint.sh` | shim обратной совместимости, который `exec`'ит hook stage2. Внешние скрипты, жёстко зафиксировавшие старый путь entrypoint, продолжают работать. |
| `hermes_cli/service_manager.py` | `S6ServiceManager`: `register_profile_gateway`, `unregister_profile_gateway`, `start/stop/restart/is_running`, `list_profile_gateways`. |
| `hermes_cli/container_boot.py` | `reconcile_profile_gateways()` — проходит по постоянным профилям, регенерирует слоты s6, генерирует `container-boot.log`. |
| `hermes_cli/gateway.py::_dispatch_via_service_manager_if_s6` | Перехватывает `hermes gateway start/stop/restart` и перенаправляет к s6 при работе в контейнере. |
## Почему Архитектура B (CMD как основная программа, а не s6‑supervised)

Исходный план (v1–v3) предполагал запуск основного **hermes** как обслуживаемой службы **s6‑rc**. Два реальных механизма **s6‑overlay v3** блокировали это:

1. **скрипты `cont‑init.d` не получают аргументы CMD** — поэтому hook `stage2` не может разобрать `docker run <image> chat -q "hi"` и установить `HERMES_ARGS` для скрипта `run` службы.
2. **`/run/s6/basedir/bin/halt` НЕ передаёт код выхода**, записанный в `/run/s6-linux-init-container-results/exitcode`. Контейнеры всегда завершаются с кодом 143 (SIGTERM) независимо от него. Подтверждено автором **skarnet** (s6) в [issue #477](https://github.com/just-containers/s6-overlay/issues/477): _"if you want a container shutdown, you need to either have your CMD exit, or, if you have no CMD, write the container exit code you want then call halt"_.

Поэтому мы используем паттерн **s6‑overlay‑native CMD**: `ENTRYPOINT ["/init", "/opt/hermes/docker/main-wrapper.sh"]`. `/init` автоматически добавляет обёртку к пользовательским аргументам — так `docker run <image> --version` превращается в `/init main-wrapper.sh --version`, и `--version` не перехватывается POSIX‑shell‑ом `/init`. Обёртка передаёт управление **hermes** через `s6-setuidgid`, а затем `exec` выбранной программы. Код выхода программы становится кодом выхода контейнера, точно соответствуя контракту **pre‑s6 tini**.

Компромисс: основной **hermes** работает без надзора **s6**. Это точно повторяет его поведение под **tini** (образ до **s6**). Надзор **Dashboard** — единственная **новая** гарантия, а шлюзы per‑profile в `/run/service/` получают полноценный надзор.
## Быстрые рецепты

### Проверить, что s6 имеет PID 1 в работающем контейнере

```sh
docker exec <c> sh -c 'cat /proc/1/comm; readlink /proc/1/exe'
# Expect: s6-svscan or init / /package/admin/s6/.../s6-svscan
```

### Просмотреть службу шлюза профиля

```sh
# /command/ isn't on docker-exec PATH — use absolute path
docker exec <c> /command/s6-svstat /run/service/gateway-<name>
# "up (pid …) … seconds"            → running
# "down (exitcode N) … seconds, normally up, want up, …" → s6 wants it up but the process keeps exiting (crash loop)
# "down … normally up, ready …"     → user stopped it
```

### Запустить/остановить сервис вручную

```sh
docker exec <c> /command/s6-svc -u /run/service/gateway-<name>   # up
docker exec <c> /command/s6-svc -d /run/service/gateway-<name>   # down
docker exec <c> /command/s6-svc -t /run/service/gateway-<name>   # SIGTERM (restart)
```

### Смотреть журнал reconciler'а cont‑init

```sh
docker exec <c> tail -n 50 /opt/data/logs/container-boot.log
# 2026-05-21T06:18:05+0000 profile=coder prior_state=running action=started
# 2026-05-21T06:18:05+0000 profile=writer prior_state=stopped action=registered
```

### Добавить новый статический сервис

1. Создай `docker/s6-rc.d/<name>/type` со строкой `longrun\n` и `docker/s6-rc.d/<name>/run` (используй `#!/command/with-contenv sh` + `# shellcheck shell=sh`).
2. Перейди к hermes через `s6-setuidgid hermes` в начале `run` (если только не нужен root).
3. Создай пустой `docker/s6-rc.d/<name>/dependencies.d/base`, чтобы он ожидал базовый бандл.
4. Создай пустой `docker/s6-rc.d/user/contents.d/<name>`, чтобы он присоединился к пользовательскому бандлу.
5. Инструкция `COPY docker/s6-rc.d/` в Dockerfile автоматически подхватит её — никаких других изменений не требуется.

### Изменить команду запуска шлюза per‑profile

Отредактируй `S6ServiceManager._render_run_script` в `hermes_cli/service_manager.py`. Эта функция также вызывается из `hermes_cli/container_boot.py::_register_service` во время согласования при загрузке, поэтому является единственным источником правды. Обнови соответствующее утверждение в `tests/hermes_cli/test_service_manager.py::test_s6_register_creates_service_dir_and_triggers_scan`.

### Запустить тестовый стенд Docker

```sh
docker build -t hermes-agent-harness:latest .
HERMES_TEST_IMAGE=hermes-agent-harness:latest scripts/run_tests.sh tests/docker/ -v
# Expect 19 passed, 0 xfailed against the s6 image
```

Стенд находится в `tests/docker/` и пропускается, если Docker недоступен. Таймаут для каждого теста увеличен до 180 с (см. `tests/docker/conftest.py`).
## Общие подводные камни

### «command not found» при `docker exec`

`/command/` (куда s6‑overlay помещает свои бинарники) находится в `PATH` только для процессов, запущенных деревом супервизии — служб, `cont-init.d`, `main-wrapper.sh`. `docker exec <c> s6-svstat …` завершится с ошибкой «command not found»; всегда используй абсолютный путь `/command/s6-svstat`. Бинарник `hermes` работает, потому что в `Dockerfile` в `ENV PATH` добавлен `/opt/hermes/.venv/bin`.

### Владельцы каталога профиля

`cont-init`‑reconciler запускается от имени `hermes` (`s6-setuidgid hermes` в `02-reconcile-profiles`). Если каталог профиля оказывается принадлежащим `root` (например, потому что `docker exec <c> hermes profile create …` по умолчанию запускался от `root`), reconciler не может прочитать `SOUL.md` и падает с `PermissionError`. Обход: `stage2-hook.sh` меняет владельца `$HERMES_HOME/profiles` на `hermes` **при каждой** загрузке, идемпотентно. Не удаляй этот блок.

### Файлы, созданные `docker exec`, принадлежат `root`

По умолчанию `docker exec` работает от `root`. Либо передай `--user hermes`, либо полагайся на очистку `chown` в `stage2` при следующей перезагрузке. Не создавай файлы вручную в `$HERMES_HOME/profiles/<name>/` от `root` — следующий проход reconciler их удалит, но текущие операции могут столкнуться с ошибками прав.

### Слот службы существует, но `s6-svstat` пишет «s6-supervise not running»

Каталог службы находится в `tmpfs` и стирается при перезапуске контейнера. Либо `cont-init`‑reconciler ещё не запустился (подожди немного после `docker restart`), либо он завершился с ошибкой. Проверь `docker logs <c> | grep '02-reconcile'`.

### Шлюз стартует и сразу завершается (`down (exitcode 1)` в `svstat`)

Чаще всего профиль не имеет настроенной модели или аутентификации. Слот службы корректен — сам шлюз не сконфигурирован. Сначала выполни `hermes -p <profile> setup`. s6‑супервизор будет перезапускать его; это ожидаемое поведение (после исправления конфигурации следующая попытка succeeds и остаётся запущенной).

### Reconciler пропустил профиль

Reconciler ориентируется на **наличие `SOUL.md`** как маркера «реального профиля». `hermes profile create` всегда создаёт его. Если в каталоге профиля нет `SOUL.md` (лишний каталог, частичное восстановление, резервное копирование в процессе), reconciler намеренно его пропускает. Добавь `SOUL.md` (даже пустой), чтобы снова включить профиль.

### «Помогите, контейнер выходит с кодом 143!»

Проверь, не вызывается ли `s6-svscanctl -t` или `/run/s6/basedir/bin/halt` — оба инициируют завершение `/init` со стадией 2 shutdown и возвращают 143 (SIGTERM) вместо желаемого кода выхода. Это было изменением архитектуры с Phase 2 от A к B. Чтобы контейнер завершался с реальным кодом выхода, дай `CMD` (`main-wrapper.sh`) завершиться нормально; **не** пытайся управлять кодом выхода из скрипта завершения.
## Связанные навыки

- `hermes-agent-dev`: Общее навигация по базе кода hermes-agent
- `hermes-tool-quirks`: Конкретные обходные решения Hermes-tool (sed/grep/etc.) — загружать при отладке взаимодействия стека s6 со встроенными инструментами hermes