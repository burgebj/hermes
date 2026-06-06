---
title: "Hermes S6 нагляд за контейнером"
sidebar_label: "Hermes S6 Container Supervision"
description: "Модифікуй, налагоджуй або розширюй дерево нагляду s6-overlay у Docker‑образі Hermes Agent — додавай нові сервіси, налагоджуй шлюзи профілів, розбирайся..."
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Hermes S6 Container Supervision

Модифікуй, налагоджуй або розширюй дерево нагляду s6-overlay всередині Docker‑образу Hermes Agent — додавай нові сервіси, налагоджуй шлюзи профілів, розбирайся у шаблоні головної програми Architecture B.
## Метадані навички

| | |
|---|---|
| Джерело | Вбудовано (встановлено за замовчуванням) |
| Шлях | `skills/software-development/hermes-s6-container-supervision` |
| Версія | `1.0.0` |
| Автор | Hermes Agent |
| Ліцензія | MIT |
| Теги | `docker`, `s6`, `supervision`, `gateway`, `profiles` |
| Пов’язані навички | [`hermes-agent`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-hermes-agent), `hermes-agent-dev` |
:::info
Нижче наведено повне визначення **skill**, яке Hermes завантажує, коли цей **skill** активовано. Це те, що агент бачить як інструкції під час активної роботи **skill**.
:::

# Hermes s6-overlay Container Supervision
## Коли використовувати цей інструмент

Завантаж цей інструмент, коли ти працюєш над:
- Додаванням або видаленням статичної служби у образі Hermes Docker (те, що має контролюватися при кожному запуску контейнера, наприклад, dashboard)
- Діагностикою, чому шлюз per‑profile не запускається, не перезапускається або не виживає після `docker restart`
- Розумінням, чому CMD контейнера — це `/opt/hermes/docker/main-wrapper.sh` і як аргументи з префіксом `-` передаються до програми користувача
- Модифікацією скриптів завантаження `cont-init.d` (переназначення UID, заповнення томів, узгодження профілів)
- Зміною згенерованого run‑script для шлюзів per‑profile (Фаза 4)

Якщо ти просто запускаєш Hermes Agent і хочеш використовувати Docker, дивись `website/docs/user-guide/docker.md` замість цього.
## Архітектура в огляді

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
## Ключові файли

| Шлях | Роль |
|---|---|
| `Dockerfile` | встановлення s6-overlay + налаштування cont-init.d + `ENTRYPOINT ["/init", "/opt/hermes/docker/main-wrapper.sh"]` |
| `docker/stage2-hook.sh` | «Стара логіка entrypoint» — переназначення UID, `chown`, seed, синхронізація **skills**. Виконується як `cont-init.d/01-hermes-setup`. |
| `docker/cont-init.d/02-reconcile-profiles` | Викликає `hermes_cli.container_boot` при кожному запуску для відновлення слотів шлюзу профілів з постійного тому. |
| `docker/main-wrapper.sh` | CMD контейнера. Маршрутизує аргументи користувача, переходить до hermes через `s6-setuidgid`, виконує обрану програму. |
| `docker/s6-rc.d/main-hermes/run` | No‑op `sleep infinity` — слот існує, щоб пакет користувача s6‑rc був валідним; основний hermes запускається як CMD, а не як керована служба. |
| `docker/s6-rc.d/dashboard/run` | Умовна служба — `exec sleep infinity`, якщо `HERMES_DASHBOARD` істинний. |
| `docker/entrypoint.sh` | Shim зворотної сумісності, який `exec`‑ить stage2 hook. Зовнішні скрипти, жорстко закодовані на старий шлях entrypoint, все ще працюють. |
| `hermes_cli/service_manager.py` | `S6ServiceManager`: `register_profile_gateway`, `unregister_profile_gateway`, `start/stop/restart/is_running`, `list_profile_gateways`. |
| `hermes_cli/container_boot.py` | `reconcile_profile_gateways()` — обходить постійні профілі, регенерує слоти s6, створює `container-boot.log`. |
| `hermes_cli/gateway.py::_dispatch_via_service_manager_if_s6` | Перехоплює `hermes gateway start/stop/restart` і перенаправляє до s6, коли працює в контейнері. |
## Чому Архітектура B (CMD як головна програма, а не s6-supervised)

Початковий план (v1–v3) передбачав запуск основного **hermes** як керованої s6‑rc служби. Два реальних механізми s6‑overlay v3 блокували це:

1. **cont-init.d скрипти не отримують аргументи CMD** — тому hook stage2 не може розпарсити `docker run <image> chat -q "hi"` і встановити `HERMES_ARGS` для скрипту `run` служби.
2. **`/run/s6/basedir/bin/halt` НЕ передає код виходу**, записаний у `/run/s6-linux-init-container-results/exitcode`. Контейнери завжди завершуються з кодом 143 (SIGTERM) незалежно. Підтверджено skarnet (автор s6) у [issue #477](https://github.com/just-containers/s6-overlay/issues/477): _"if you want a container shutdown, you need to either have your CMD exit, or, if you have no CMD, write the container exit code you want then call halt"_.

Тому ми використовуємо патерн s6‑overlay‑native CMD: `ENTRYPOINT ["/init", "/opt/hermes/docker/main-wrapper.sh"]`. `/init` автоматично додає обгортку до користувацьких аргументів — тому `docker run <image> --version` стає `/init main-wrapper.sh --version`, і `--version` не перехоплюється POSIX‑shell `/init`. Обгортка переходить до **hermes** через `s6-setuidgid`, а потім `exec`‑ить обрану програму. Код виходу програми стає кодом виходу контейнера, точно відповідаючи попередньому контракту з **tini**.

Компроміс: основний **hermes** не керується s6. Це точно відповідає його поведінці під **tini** (у попередньому образі). Нагляд за **Dashboard** — єдина **нова** гарантія, і шлюзи per‑profile у `/run/service/` отримують повний нагляд.
## Швидкі рецепти

### Перевірити, що s6 є PID 1 у запущеному контейнері

```sh
docker exec <c> sh -c 'cat /proc/1/comm; readlink /proc/1/exe'
# Expect: s6-svscan or init / /package/admin/s6/.../s6-svscan
```

### Переглянути службу шлюзу профілю

```sh
# /command/ isn't on docker-exec PATH — use absolute path
docker exec <c> /command/s6-svstat /run/service/gateway-<name>
# "up (pid …) … seconds"            → running
# "down (exitcode N) … seconds, normally up, want up, …" → s6 wants it up but the process keeps exiting (crash loop)
# "down … normally up, ready …"     → user stopped it
```

### Запустити/зупинити сервіс вручну

```sh
docker exec <c> /command/s6-svc -u /run/service/gateway-<name>   # up
docker exec <c> /command/s6-svc -d /run/service/gateway-<name>   # down
docker exec <c> /command/s6-svc -t /run/service/gateway-<name>   # SIGTERM (restart)
```

### Спостерігати журнал cont‑init reconciler‑а

```sh
docker exec <c> tail -n 50 /opt/data/logs/container-boot.log
# 2026-05-21T06:18:05+0000 profile=coder prior_state=running action=started
# 2026-05-21T06:18:05+0000 profile=writer prior_state=stopped action=registered
```

### Додати новий статичний сервіс

1. Створи `docker/s6-rc.d/<name>/type` з вмістом `longrun\n` і `docker/s6-rc.d/<name>/run` (використай `#!/command/with-contenv sh` + `# shellcheck shell=sh`).
2. Переключись на hermes за допомогою `s6-setuidgid hermes` у верхній частині `run` (якщо тобі не потрібен root).
3. Створи порожній `docker/s6-rc.d/<name>/dependencies.d/base`, щоб він чекав на базовий пакет.
4. Створи порожній `docker/s6-rc.d/user/contents.d/<name>`, щоб він приєднався до користувацького пакету.
5. `COPY docker/s6-rc.d/` у Dockerfile підхоплює його автоматично — інших змін не потрібно.

### Змінити команду запуску шлюзу профілю

Відредагуй `S6ServiceManager._render_run_script` у `hermes_cli/service_manager.py`. Ця функція також викликається `hermes_cli/container_boot.py::_register_service` під час запуску reconciler‑а, тому вона є єдиним джерелом правди. Онови відповідне твердження у `tests/hermes_cli/test_service_manager.py::test_s6_register_creates_service_dir_and_triggers_scan`.

### Запустити тестовий стенд Docker

```sh
docker build -t hermes-agent-harness:latest .
HERMES_TEST_IMAGE=hermes-agent-harness:latest scripts/run_tests.sh tests/docker/ -v
# Expect 19 passed, 0 xfailed against the s6 image
```

Стенд розташований у `tests/docker/` і пропускається, коли Docker недоступний. Тайм‑аут для кожного тесту збільшено до 180 сек (див. `tests/docker/conftest.py`).
## Поширені підводні камені

### «command not found» через `docker exec`

`/command/` (де s6‑overlay розміщує свої бінарники) знаходиться у `PATH` лише для процесів, запущених деревом супервізії — services, cont‑init.d, main-wrapper.sh. `docker exec <c> s6-svstat …` завершиться помилкою «command not found»; завжди використовуйте абсолютний шлях `/command/s6-svstat`. Бінарник `hermes` працює, бо Dockerfile додає `/opt/hermes/.venv/bin` до змінної середовища `ENV PATH`.

### Власність каталогу профілю

cont‑init reconciler працює від імені `hermes` (`s6-setuidgid hermes` у `02-reconcile-profiles`). Якщо каталог профілю виявиться власністю `root` (наприклад, коли `docker exec <c> hermes profile create …` за замовчуванням виконується від `root`), reconciler не зможе прочитати `SOUL.md` і завершиться `PermissionError`. Мітиґація: `stage2-hook.sh` змінює власника `$HERMES_HOME/profiles` на `hermes` **при кожному** завантаженні, ідempotентно. Не видаляй цей блок.

### Файли, створені `docker exec`, належать `root`

`docker exec` за замовчуванням працює від `root`. Або передай `--user hermes`, або покладися на sweep‑chown у stage2 під час наступного перезапуску. Не створюй файли в `$HERMES_HOME/profiles/<name>/` від `root` вручну — наступний прохід reconciler їх прибере, але операції, що виконуються в цей момент, можуть отримати помилки доступу.

### Слот сервісу існує, а `s6-svstat` повідомляє «s6-supervise not running»

Каталог сервісу розташований у `tmpfs` і був стертий при перезапуску контейнера. Або cont‑init reconciler ще не запустився (дай йому час після `docker restart`), або він зазнав помилки. Перевір `docker logs <c> | grep '02-reconcile'`.

### Шлюз стартує, а потім одразу виходить (`down (exitcode 1)` у svstat)

Найчастіше профіль не має налаштованої моделі або автентифікації. Слот сервісу правильний — сам шлюз не налаштований. Спочатку виконай `hermes -p <profile> setup`. s6‑supervisor буде перезапускати його; це очікувана поведінка (коли виправиш конфігурацію, наступна спроба завершиться успішно і залишиться працювати).

### Reconciler пропустив профіль

Reconciler орієнтується на **наявність `SOUL.md`** як маркера «справжнього профілю». `hermes profile create` завжди створює його. Якщо в каталозі профілю відсутній `SOUL.md` (загублений каталог, часткове відновлення, резервна копія в процесі), reconciler навмисно його пропускає. Додай `SOUL.md` (навіть порожній), щоб повернути профіль у облік.

### «Help, the container exits 143!»

Перевір, чи не викликає щось `s6-svscanctl -t` або `/run/s6/basedir/bin/halt` — обидва запускають `/init` на завершення stage 3, повертаючи 143 (SIGTERM) замість бажаного коду виходу. Це був перехід архітектури Phase 2 від A до B. Для завершення контейнера з реальним кодом виходу треба дозволити `CMD` (`main-wrapper.sh`) завершитися нормально; **не** намагайся керувати кодом виходу зі скрипту завершення.
## Пов'язані навички

- `hermes-agent-dev`: Загальна навігація по кодовій базі hermes-agent
- `hermes-tool-quirks`: Конкретні обхідні рішення Hermes-tool (sed/grep/etc.) — завантажити під час налагодження взаємодії стеку s6 з вбудованими інструментами hermes.