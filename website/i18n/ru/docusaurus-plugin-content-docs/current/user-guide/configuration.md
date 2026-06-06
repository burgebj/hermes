---
sidebar_position: 2
title: "Конфигурация"
description: "Настрой Hermes Agent — config.yaml, провайдеры, модели, API‑ключи и прочее"
---

# Конфигурация

Все настройки хранятся в каталоге `~/.hermes/` для удобного доступа.

:::tip Самый простой путь к рабочему `config.yaml`
Запусти `hermes setup --portal` — один OAuth даст тебе провайдера модели и все четыре инструмента шлюза инструментов без ручного редактирования YAML. Подписчики Nous Portal также получают 10 % скидку на провайдеров с оплатой по токенам. Смотри [Nous Portal](/integrations/nous-portal).
:::
## Структура каталогов

```text
~/.hermes/
├── config.yaml     # Settings (model, terminal, TTS, compression, etc.)
├── .env            # API keys and secrets
├── auth.json       # OAuth provider credentials (Nous Portal, etc.)
├── SOUL.md         # Primary agent identity (slot #1 in system prompt)
├── memories/       # Persistent memory (MEMORY.md, USER.md)
├── skills/         # Agent-created skills (managed via skill_manage tool)
├── cron/           # Scheduled jobs
├── sessions/       # Gateway sessions
└── logs/           # Logs (errors.log, gateway.log — secrets auto-redacted)
```
## Управление конфигурацией

```bash
hermes config              # View current configuration
hermes config edit         # Open config.yaml in your editor
hermes config set KEY VAL  # Set a specific value
hermes config check        # Check for missing options (after updates)
hermes config migrate      # Interactively add missing options

# Examples:
hermes config set model anthropic/claude-opus-4
hermes config set terminal.backend docker
hermes config set OPENROUTER_API_KEY sk-or-...  # Saves to .env
```

:::tip
Команда `hermes config set` автоматически перенаправляет значения в нужный файл — API‑ключи сохраняются в `.env`, всё остальное — в `config.yaml`.
:::
## Приоритет конфигурации

Настройки разрешаются в следующем порядке (сначала самые приоритетные):

1. **CLI‑аргументы** — например, `hermes chat --model anthropic/claude-sonnet-4` (переопределение для конкретного вызова)
2. **`~/.hermes/config.yaml`** — основной файл конфигурации для всех не‑секретных настроек
3. **`~/.hermes/.env`** — запасной (вариант) для переменных окружения; **обязательно** для секретов (API‑ключи, токены, пароли)
4. **Встроенные значения по умолчанию** — жёстко закодированные безопасные значения, когда ничего другого не задано

:::info Правило большого пальца
Секреты (API‑ключи, токены ботов, пароли) помещаются в `.env`. Всё остальное (модель, бекенд терминала, настройки сжатия, ограничения памяти, наборы инструментов) помещается в `config.yaml`. Когда оба файла заданы, `config.yaml` имеет приоритет для не‑секретных настроек.
:::
## Подстановка переменных окружения

Ты можешь ссылаться на переменные окружения в `config.yaml`, используя синтаксис `${VAR_NAME}`:

```yaml
auxiliary:
  vision:
    api_key: ${GOOGLE_API_KEY}
    base_url: ${CUSTOM_VISION_URL}

delegation:
  api_key: ${DELEGATION_KEY}
```

Несколько ссылок в одном значении работают: `url: "${HOST}:${PORT}"`. Если ссылка указывает на неустановленную переменную, плейсхолдер остаётся без изменений (`${UNDEFINED_VAR}` остаётся как есть). Поддерживается только синтаксис `${VAR}` — «голый» `$VAR` не расширяется.

Для настройки провайдеров ИИ (OpenRouter, Anthropic, Copilot, пользовательские эндпоинты, само‑хостинг LLM, запасные модели и т.д.) см. [AI Providers](/integrations/providers).

### Тайм‑ауты провайдера

Ты можешь задать `providers.<id>.request_timeout_seconds` для глобального тайм‑аута запросов провайдера, а также `providers.<id>.models.<model>.timeout_seconds` для переопределения тайм‑аута конкретной модели. Это применяется к основному клиенту turn на каждом транспорте (OpenAI‑wire, native Anthropic, совместимый с Anthropic), к цепочке запасных вариантов, к пересборкам после ротации учётных данных и (для OpenAI‑wire) к аргументу `timeout` в запросе — поэтому сконфигурированное значение имеет приоритет над устаревшей переменной окружения `HERMES_API_TIMEOUT`.

Ты также можешь задать `providers.<id>.stale_timeout_seconds` для детектора «застрявших» вызовов без стриминга, а также `providers.<id>.models.<model>.stale_timeout_seconds` для переопределения тайм‑аута конкретной модели. Это имеет приоритет над устаревшей переменной окружения `HERMES_API_CALL_STALE_TIMEOUT`.

Если эти параметры не заданы, сохраняются устаревшие значения по умолчанию (`HERMES_API_TIMEOUT=1800`s, `HERMES_API_CALL_STALE_TIMEOUT=300`s, native Anthropic 900s). Сейчас не реализовано для AWS Bedrock (оба пути `bedrock_converse` и AnthropicBedrock SDK используют boto3 со своей конфигурацией тайм‑аутов). См. закомментированный пример в [`cli-config.yaml.example`](https://github.com/NousResearch/hermes-agent/blob/main/cli-config.yaml.example).
## Конфигурация терминального бэкенда

Hermes поддерживает шесть терминальных бэкендов. Каждый из них определяет, где именно будут выполняться команды оболочки агента — на твоей локальной машине, в контейнере Docker, на удалённом сервере через SSH, в облачном песочном окружении Modal (напрямую или через управляемый Nous шлюз), в рабочем пространстве Daytona или в контейнере Singularity/Apptainer.

```yaml
terminal:
  backend: local    # local | docker | ssh | modal | daytona | singularity
  cwd: "."          # Gateway/cron working directory (CLI always uses launch dir)
  timeout: 180      # Per-command timeout in seconds
  env_passthrough: []  # Env var names to forward to sandboxed execution (terminal + execute_code)
  singularity_image: "docker://nikolaik/python-nodejs:python3.11-nodejs20"  # Container image for Singularity backend
  modal_image: "nikolaik/python-nodejs:python3.11-nodejs20"                 # Container image for Modal backend
  daytona_image: "nikolaik/python-nodejs:python3.11-nodejs20"               # Container image for Daytona backend
```

Для облачных песочниц, таких как Modal и Daytona, `container_persistent: true` означает, что Hermes будет пытаться сохранять состояние файловой системы между пересозданиями песочницы. Это не гарантирует, что та же живущая песочница, PID‑пространство или фоновые процессы будут работать позже.

### Обзор бэкендов

| Бэкенд | Где выполняются команды | Изоляция | Лучшее применение |
|--------|------------------------|----------|-------------------|
| **local** | Твоя машина напрямую | Нет | Разработка, личное использование |
| **docker** | Один постоянный контейнер Docker (общий для сессии, `/new`, субагентов) | Полная (namespaces, cap‑drop) | Безопасное песочничество, CI/CD |
| **ssh** | Удалённый сервер через SSH | Сетевой барьер | Удалённая разработка, мощное оборудование |
| **modal** | Облачная песочница Modal | Полная (облачная VM) | Эфемерные облачные вычисления, оценки |
| **daytona** | Рабочее пространство Daytona | Полная (облачный контейнер) | Управляемые облачные среды разработки |
| **singularity** | Контейнер Singularity/Apptainer | Namespaces (`--containall`) | Кластеры HPC, общие машины |

### Локальный бэкенд

По умолчанию. Команды выполняются напрямую на твоей машине без изоляции. Специальная настройка не требуется.

```yaml
terminal:
  backend: local
```

:::warning
Агент имеет такой же доступ к файловой системе, как и твой пользователь. Используй `hermes tools`, чтобы отключить инструменты, которые не нужны, или переключись на Docker для изоляции.
:::

### Docker‑бэкенд

Запускает команды внутри контейнера Docker с жёсткой изоляцией (все возможности удалены, эскалация привилегий запрещена, ограничения PID).

**Один постоянный контейнер, общий для всех процессов Hermes.** Hermes запускает ОДИН длительно живущий контейнер при первом использовании и направляет каждый терминал, файл и вызов `execute_code` через `docker exec` в тот же контейнер — между сессиями, `/new`, `/reset` и субагентами `delegate_task`. Изменения текущего каталога, установленные пакеты, файлы в `/workspace` и **фоновые процессы** сохраняются от одного вызова инструмента к другому и от одного процесса Hermes к другому. Когда ты закрываешь TUI‑сессию, выполняешь `/quit` или запускаешь новый вызов `hermes`, контейнер продолжает работать, а следующий процесс Hermes переиспользует его через поиск по метке. См. **Жизненный цикл контейнера** ниже для точных правил завершения.

```yaml
terminal:
  backend: docker
  docker_image: "nikolaik/python-nodejs:python3.11-nodejs20"
  docker_mount_cwd_to_workspace: false  # Mount launch dir into /workspace
  docker_run_as_host_user: false   # See "Running container as host user" below
  docker_forward_env:              # Host env vars to forward into container
    - "GITHUB_TOKEN"
  docker_env:                      # Literal env vars to inject (KEY=value)
    DEBUG: "1"
    PYTHONUNBUFFERED: "1"
  docker_volumes:                  # Host directory mounts
    - "/home/user/projects:/workspace/projects"
    - "/home/user/data:/data:ro"   # :ro for read-only
  docker_extra_args:               # Extra flags appended verbatim to `docker run`
    - "--gpus=all"
    - "--network=host"

  # Resource limits
  container_cpu: 1                 # CPU cores (0 = unlimited)
  container_memory: 5120           # MB (0 = unlimited)
  container_disk: 51200            # MB (requires overlay2 on XFS+pquota)
  container_persistent: true       # Persist /workspace and /root bind-mount dirs

  # Cross-process container reuse (defaults match the "one long-lived
  # container shared across sessions" contract — see Container lifecycle).
  docker_persist_across_processes: true   # Reuse container across Hermes restarts
  docker_orphan_reaper: true              # Sweep abandoned Exited containers at startup

  # Cross-backend lifecycle settings (apply to docker as well)
  timeout: 180                     # Per-command timeout in seconds
  lifetime_seconds: 300            # Idle-reaper window; also feeds 2× orphan-reaper threshold
```

**`docker_env`** vs **`docker_forward_env`**: первое внедряет буквальные пары `KEY=value`, указанные в конфиге (значения находятся в твоём `config.yaml` или передаются как JSON‑словарь через `TERMINAL_DOCKER_ENV='{"DEBUG":"1"}'`). Второе пересылает значения из твоей оболочки или `~/.hermes/.env`, так что реальный секрет никогда не появляется в файле конфигурации. Используй `docker_forward_env` для токенов и `docker_env` для статических параметров, необходимых контейнеру.

**`terminal.docker_extra_args`** (также переопределяется через `TERMINAL_DOCKER_EXTRA_ARGS='["--gpus=all"]'`) позволяет передать произвольные флаги `docker run`, которые Hermes не выводит как отдельные ключи — `--gpus`, `--network`, `--add-host`, альтернативные переопределения `--security-opt` и т.д. Каждый элемент должен быть строкой; список добавляется в конец сформированной команды `docker run`, поэтому может переопределять значения по умолчанию Hermes при необходимости. Используй умеренно — флаги, конфликтующие с жёсткой изоляцией (удаление возможностей, `--user`, монтирование рабочего каталога) будут тихо ослаблять изоляцию.

**Требования:** установлен и запущен Docker Desktop или Docker Engine. Hermes ищет `$PATH` и типичные места установки macOS (`/usr/local/bin/docker`, `/opt/homebrew/bin/docker`, пакет приложения Docker Desktop). Podman поддерживается из коробки: задай `HERMES_DOCKER_BINARY=podman` (или полный путь), чтобы принудительно использовать его, если оба установлены.

#### Жизненный цикл контейнера

Каждый контейнер, управляемый Hermes, помечен тремя метками, чтобы последующие процессы (и «сборщик‑сирот») могли его идентифицировать:

- `hermes-agent=1` — пометка как управляемый Hermes
- `hermes-task-id=<sanitized task_id>` — ключ для проверки повторного использования по задаче
- `hermes-profile=<sanitized profile name>` — ограничивает повторное использование и сборку текущим профилем Hermes

При старте Hermes выполняет

```bash
docker ps --filter label=hermes-task-id=<id> --filter label=hermes-profile=<profile>
```

и **подключается к существующему контейнеру**, если он найден. Если контейнер `exited` (например, после перезапуска демона Docker), его `docker start`‑ит и переиспользует — состояние файловой системы и установленные пакеты сохраняются, но фоновые процессы внутри контейнера — нет.

Когда процесс Hermes завершается — `/quit`, закрытие TUI‑сессии, выключение шлюза, даже SIGKILL — путь очистки **ничего не делает** с контейнером в режиме по умолчанию. Контейнер продолжает работать. Следующий процесс Hermes подключается к нему за миллисекунды через проверку меток. Это поведение, требуемое «один длительно живущий контейнер, общий для всех сессий».

**Контейнер удаляется (остановка и `docker rm -f`) только в следующих случаях:**

| Триггер | Когда срабатывает |
|---|---|
| `docker_persist_across_processes: false` | Явная изоляция per‑process. Каждый `cleanup()` делает `stop` + `rm -f`. Соответствует поведению до issue #20561. |
| Поглотитель простоя (`lifetime_seconds`, по умолчанию 300 s) | Только когда `persist_across_processes=false`. В режимах persist‑mode поглотитель не действует; контейнер переживает простой. |
| Сборщик‑сирот при следующем старте | Удаляет **Exited**‑контейнеры с меткой Hermes, старше `2 × lifetime_seconds` (по умолчанию 600 s = 10 мин), в пределах текущего профиля. **Запущенные контейнеры никогда не трогаются** — безопасность соседних процессов. Отключить можно `docker_orphan_reaper: false`. |
| Прямое действие пользователя | `docker rm -f`, `docker system prune`, перезапуск Docker Desktop. Мы не ставим `--restart=always`, поэтому после перезагрузки хоста контейнер будет `Exited` (его CoW‑слой сохраняется и переиспользуется при следующем старте, но фоновые процессы исчезают). |

Особые случаи, о которых стоит знать:

- **OOM‑kill PID 1 внутри контейнера** переводит контейнер в состояние `Exited`. При следующем использовании он будет `docker start`‑нут; файловая система сохраняется, фоновые процессы — нет.
- **Смена профилей** изолирует контейнеры друг от друга — контейнер с меткой `hermes-profile=work` невидим процессу Hermes, работающему под `hermes-profile=research`. Сборщик‑сирот также привязан к профилю, поэтому контейнеры разных профилей не удаляются случайно, но и не очищаются автоматически, пока ты не запустишь Hermes под их исходным профилем.

Параллельные субагенты, запущенные через `delegate_task(tasks=[...])`, используют один и тот же контейнер — одновременные `cd`, изменения окружения и записи в один и тот же путь будут конфликтовать. Если субагенту нужен изолированный песочный контейнер, он должен зарегистрировать переопределение образа per‑task через `register_task_env_overrides()`, что делают RL‑ и benchmark‑окружения (TerminalBench2, HermesSweEnv и др.) автоматически для своих Docker‑образов.

**Жёсткая безопасность:**
- `--cap-drop ALL` с возвратом только `DAC_OVERRIDE`, `CHOWN`, `FOWNER`
- `--security-opt no-new-privileges`
- `--pids-limit 256`
- Ограниченный tmpfs для `/tmp` (512 MB), `/var/tmp` (256 MB), `/run` (64 MB)

**Пересылка учётных данных:** переменные окружения, указанные в `docker_forward_env`, сначала берутся из твоей оболочки, затем из `~/.hermes/.env`. Инструменты (skills) могут также объявлять `required_environment_variables`, которые автоматически объединяются.

#### Переопределения переменных окружения

Каждый ключ под `terminal:` имеет переопределение через переменную вида `TERMINAL_<KEY_UPPERCASE>`. Наиболее полезные для Docker‑бэкенда:

| Переменная | Соответствует | Примечания |
|---|---|---|
| `TERMINAL_DOCKER_IMAGE` | `docker_image` | Базовый образ |
| `TERMINAL_DOCKER_FORWARD_ENV` | `docker_forward_env` | JSON‑массив: `'["GITHUB_TOKEN","OPENAI_API_KEY"]'` |
| `TERMINAL_DOCKER_ENV` | `docker_env` | JSON‑словарь: `'{"DEBUG":"1"}'` |
| `TERMINAL_DOCKER_VOLUMES` | `docker_volumes` | JSON‑массив строк `"host:container[:ro]"` |
| `TERMINAL_DOCKER_EXTRA_ARGS` | `docker_extra_args` | JSON‑массив |
| `TERMINAL_DOCKER_MOUNT_CWD_TO_WORKSPACE` | `docker_mount_cwd_to_workspace` | `true` / `false` |
| `TERMINAL_DOCKER_RUN_AS_HOST_USER` | `docker_run_as_host_user` | `true` / `false` |
| `TERMINAL_DOCKER_PERSIST_ACROSS_PROCESSES` | `docker_persist_across_processes` | `true` / `false` — по умолчанию `true` |
| `TERMINAL_DOCKER_ORPHAN_REAPER` | `docker_orphan_reaper` | `true` / `false` — по умолчанию `true` |
| `TERMINAL_CONTAINER_CPU` | `container_cpu` | Ядра CPU |
| `TERMINAL_CONTAINER_MEMORY` | `container_memory` | MB |
| `TERMINAL_CONTAINER_DISK` | `container_disk` | MB |
| `TERMINAL_CONTAINER_PERSISTENT` | `container_persistent` | `true` / `false` — управляет bind‑mount‑директориями workspace, отдельно от `docker_persist_across_processes` |
| `TERMINAL_LIFETIME_SECONDS` | `lifetime_seconds` | Окно простоя для сборщика |
| `TERMINAL_TIMEOUT` | `timeout` | Таймаут команды |
| `HERMES_DOCKER_BINARY` | _none_ | Принудительно задать путь к docker/podman бинарнику |

### SSH‑бэкенд

Запускает команды на удалённом сервере через SSH. Использует ControlMaster для переиспользования соединения (5‑минутный keepalive простоя). По умолчанию включён постоянный шелл — состояние (cwd, переменные окружения) сохраняется между командами.

```yaml
terminal:
  backend: ssh
  persistent_shell: true           # Keep a long-lived bash session (default: true)
```

**Обязательные переменные окружения:**

```bash
TERMINAL_SSH_HOST=my-server.example.com
TERMINAL_SSH_USER=ubuntu
```

**Опциональные:**

| Переменная | По умолчанию | Описание |
|---|---|---|
| `TERMINAL_SSH_PORT` | `22` | Порт SSH |
| `TERMINAL_SSH_KEY` | (системный по умолчанию) | Путь к приватному ключу SSH |
| `TERMINAL_SSH_PERSISTENT` | `true` | Включить постоянный шелл |

**Как работает:** При инициализации соединяется с `BatchMode=yes` и `StrictHostKeyChecking=accept-new`. Постоянный шелл держит один процесс `bash -l` живым на удалённом хосте, общаясь через временные файлы. Команды, требующие `stdin_data` или `sudo`, автоматически переключаются в одноразовый режим.

### Modal‑бэкенд

Запускает команды в облачной песочнице [Modal](https://modal.com). Каждая задача получает изолированную VM с настраиваемыми CPU, памятью и диском. Файловая система может быть снапшотирована/восстановлена между сессиями.

```yaml
terminal:
  backend: modal
  container_cpu: 1                 # CPU cores
  container_memory: 5120           # MB (5GB)
  container_disk: 51200            # MB (50GB)
  container_persistent: true       # Snapshot/restore filesystem
```

**Требуется:** либо переменные `MODAL_TOKEN_ID` + `MODAL_TOKEN_SECRET`, либо файл конфигурации `~/.modal.toml`.

**Сохранение:** При включении файловая система песочницы сохраняется в снапшот при очистке и восстанавливается в следующей сессии. Снапшоты хранятся в `~/.hermes/modal_snapshots.json`. Это сохраняет состояние файловой системы, но не живые процессы, PID‑пространство или фоновые задачи.

**Файлы учётных данных:** Автоматически монтируются из `~/.hermes/` (OAuth‑токены и т.п.) и синхронезируются перед каждой командой.

### Daytona‑бэкенд

Запускает команды в управляемом рабочем пространстве [Daytona](https://daytona.io). Поддерживает остановку/возобновление для сохранения состояния.

```yaml
terminal:
  backend: daytona
  container_cpu: 1                 # CPU cores
  container_memory: 5120           # MB → converted to GiB
  container_disk: 10240            # MB → converted to GiB (max 10 GiB)
  container_persistent: true       # Stop/resume instead of delete
```

**Требуется:** переменная окружения `DAYTONA_API_KEY`.

**Сохранение:** При включении песочницы останавливаются (не удаляются) при очистке и возобновляются в следующей сессии. Имена песочниц следуют шаблону `hermes-{task_id}`.

**Ограничение диска:** Daytona накладывает максимум 10 GiB. Запросы выше этого лимита обрезаются с предупреждением.

### Singularity/Apptainer‑бэкенд

Запускает команды в контейнере [Singularity/Apptainer](https://apptainer.org). Предназначен для кластеров HPC и общих машин, где Docker недоступен.

```yaml
terminal:
  backend: singularity
  singularity_image: "docker://nikolaik/python-nodejs:python3.11-nodejs20"
  container_cpu: 1                 # CPU cores
  container_memory: 5120           # MB
  container_persistent: true       # Writable overlay persists across sessions
```

**Требования:** бинарник `apptainer` или `singularity` в `$PATH`.

**Работа с образами:** Docker‑URL (`docker://...`) автоматически конвертируются в SIF‑файлы и кэшируются. Существующие `.sif`‑файлы используются напрямую.

**Каталог scratch:** Определяется в порядке: `TERMINAL_SCRATCH_DIR` → `TERMINAL_SANDBOX_DIR/singularity` → `/scratch/$USER/hermes-agent` (конвенция HPC) → `~/.hermes/sandboxes/singularity`.

**Изоляция:** Использует `--containall --no-home` для полной изоляции namespaces без монтирования домашней директории хоста.

### Распространённые проблемы терминальных бэкендов

Если команды терминала сразу падают или инструмент терминала отмечен как отключённый:

- **Local** — никаких особых требований. Самый безопасный вариант для начала.
- **Docker** — запусти `docker version`, чтобы убедиться, что Docker работает. Если нет, исправь Docker или переключись `hermes config set terminal.backend local`.
- **SSH** — должны быть заданы `TERMINAL_SSH_HOST` и `TERMINAL_SSH_USER`. Hermes выводит чёткую ошибку, если чего‑то не хватает.
- **Modal** — нужен `MODAL_TOKEN_ID` или `~/.modal.toml`. Выполни `hermes doctor` для проверки.
- **Daytona** — нужен `DAYTONA_API_KEY`. SDK Daytona управляет конфигурацией URL сервера.
- **Singularity** — нужен `apptainer` или `singularity` в `$PATH`. Часто встречается на кластерах HPC.

При сомнениях переключи `terminal.backend` обратно на `local` и проверь, что команды работают там.

### Синхронизация файлов с хостом при завершении

Для бэкендов **SSH**, **Modal** и **Daytona** (когда рабочее дерево агента находится на другой машине, чем хост, запускающий Hermes) Hermes отслеживает файлы, изменённые агентом внутри удалённой песочницы, и при завершении сессии/очистке песочницы **синхронезирует изменённые файлы обратно на хост** в `~/.hermes/cache/remote-syncs/<session-id>/`.

- Срабатывает при: закрытии сессии, `/new`, `/reset`, тайм‑ауте сообщения шлюза, завершении субагента `delegate_task`, когда дочерний процесс использовал удалённый бэкенд.
- Охватывает всё дерево, которое агент изменил, а не только явно открытые файлы. Добавления, правки и удаления фиксируются.
- К моменту обращения удалённая песочница может уже быть уничтожена; локальная копия в `~/.hermes/cache/remote-syncs/…` является официальным журналом изменений.
- Большие бинарные выводы (модели, наборы данных) ограничены размером — синхронизация пропускает файлы больше `file_sync_max_mb` (по умолчанию `100`). Увеличь значение, если ожидаешь более крупные артефакты.

```yaml
terminal:
  file_sync_max_mb: 100     # default — sync files up to 100 MB each
  file_sync_enabled: true   # default — set false to skip the sync entirely
```

Так восстанавливаются результаты из эфемерных облачных песочниц, которые уничтожаются после завершения сессии, без необходимости заставлять агента явно выполнять `scp` или `modal volume put` для каждого артефакта.

### Монтирование томов Docker

При использовании Docker‑бэкенда `docker_volumes` позволяет делиться директориями хоста с контейнером. Каждый элемент использует стандартный синтаксис Docker `-v`: `host_path:container_path[:options]`.

```yaml
terminal:
  backend: docker
  docker_volumes:
    - "/home/user/projects:/workspace/projects"   # Read-write (default)
    - "/home/user/datasets:/data:ro"              # Read-only
    - "/home/user/.hermes/cache/documents:/output" # Gateway-visible exports
```

Это удобно для:
- **Предоставления файлов** агенту (датасеты, конфиги, референсный код)
- **Получения файлов** от агента (сгенерированный код, отчёты, экспорты)
- **Общих рабочих пространств**, где и ты, и агент имеете доступ к тем же файлам

Если ты используешь шлюз обмена сообщениями и хочешь, чтобы агент отправлял сгенерированные файлы через `MEDIA:/...`, предпочтительно создать отдельный монтируемый каталог, видимый хосту, например `/home/user/.hermes/cache/documents:/output`.

- Пиши файлы внутри Docker в `/output/...`
- В `MEDIA:` указывай **путь на хосте**, например: `MEDIA:/home/user/.hermes/cache/documents/report.txt`
- Не используй `/workspace/...` или `/output/...`, если только такой же путь не существует у процесса шлюза на хосте

:::warning
YAML‑ключи, повторяющиеся в файле, тихо переопределяют предыдущие. Если у тебя уже есть блок `docker_volumes:`, объединяй новые монтирования в тот же список, а не добавляй ещё один ключ `docker_volumes:` позже в файле.
:::

Можно также задать через переменную окружения: `TERMINAL_DOCKER_VOLUMES='["/host:/container"]'` (JSON‑массив).

### Пересылка учётных данных в Docker

По умолчанию сессии Docker‑терминала не наследуют произвольные учётные данные хоста. Если нужен конкретный токен внутри контейнера, добавь его в `terminal.docker_forward_env`.

```yaml
terminal:
  backend: docker
  docker_forward_env:
    - "GITHUB_TOKEN"
    - "NPM_TOKEN"
```

Hermes разрешает каждую указанную переменную сначала из текущей оболочки, затем из `~/.hermes/.env`, если она была сохранена через `hermes config set`.

:::warning
Все, что указано в `docker_forward_env`, становится видимым командам внутри контейнера. Пересылай только те учётные данные, которые готов раскрыть терминальной сессии.
:::

### Запуск контейнера от имени текущего пользователя хоста

По умолчанию контейнеры Docker работают от `root` (UID 0). Файлы, созданные внутри `/workspace` или других bind‑mount‑директорий, оказываются принадлежащими root на хосте, поэтому после сессии придётся выполнять `sudo chown`. Флаг `terminal.docker_run_as_host_user` решает эту проблему:

```yaml
terminal:
  backend: docker
  docker_run_as_host_user: true   # default: false
```

Когда включён, Hermes добавляет `--user $(id -u):$(id -g)` к команде `docker run`, так что файлы в bind‑mount‑директориях (`/workspace`, `/root`, любые `docker_volumes`) принадлежат твоему пользователю, а не root. Компромисс: контейнер больше не может выполнять `apt install` или писать в пути, принадлежащие root (например, `/root/.npm`). Используй базовый образ, где `HOME` принадлежит непривилегированному пользователю (или добавляй нужные инструменты на этапе сборки образа), если нужны обе возможности.

Оставляй `false` (по умолчанию) для совместимости со старыми настройками. Включай, когда основной рабочий процесс — «редактировать смонтированные файлы хоста» и тебя раздражает постоянный `sudo chown -R`.

### Опционально: монтировать каталог запуска в `/workspace`

По умолчанию Docker‑песочницы изолированы. Hermes **не** передаёт текущий рабочий каталог хоста в контейнер, если ты явно не включил эту опцию.

Включи в `config.yaml`:

```yaml
terminal:
  backend: docker
  docker_mount_cwd_to_workspace: true
```

Когда включено:
- если ты запускаешь Hermes из `~/projects/my-app`, этот каталог хоста монтируется в контейнер как `/workspace`
- Docker‑бэкенд стартует в `/workspace`
- инструменты файлов и терминальные команды видят один и тот же смонтированный проект

Когда отключено, `/workspace` остаётся полностью внутри песочницы, если только ты не смонтировал что‑то вручную через `docker_volumes`.

Безопасный компромисс:
- `false` сохраняет границу песочницы
- `true` даёт песочнице прямой доступ к каталогу, из которого запущен Hermes

Включай только тогда, когда действительно хочешь, чтобы контейнер работал с живыми файлами хоста.

### Постоянный шелл

По умолчанию каждая терминальная команда запускается в отдельном подпроцессе — рабочий каталог, переменные окружения и shell‑переменные сбрасываются между командами. При включённом **постоянном шелле** один длительно живущий процесс `bash` сохраняется между вызовами `execute()`, поэтому состояние сохраняется.

Это особенно полезно для **SSH‑бэкенда**, где также устраняются накладные расходы на соединение для каждой команды. Постоянный шелл **включён по умолчанию для SSH** и отключён для локального бэкенда.

```yaml
terminal:
  persistent_shell: true   # default — enables persistent shell for SSH
```

Чтобы отключить:

```bash
hermes config set terminal.persistent_shell false
```

**Что сохраняется между командами:**
- Текущий каталог (`cd /tmp` остаётся для следующей команды)
- Экспортированные переменные окружения (`export FOO=bar`)
- Shell‑переменные (`MY_VAR=hello`)

**Приоритеты:**

| Уровень | Переменная | По умолчанию |
|---|---|---|
| Конфиг | `terminal.persistent_shell` | `true` |
| Переопределение SSH | `TERMINAL_SSH_PERSISTENT` | следует конфигу |
| Переопределение Local | `TERMINAL_LOCAL_PERSISTENT` | `false` |

Переменные окружения конкретного бэкенда имеют наивысший приоритет. Если хочешь постоянный шелл и для локального бэкенда:

```bash
export TERMINAL_LOCAL_PERSISTENT=true
```

:::note
Команды, требующие `stdin_data` или `sudo`, автоматически переключаются в одноразовый режим, поскольку stdin постоянного шелла уже занят IPC‑протоколом.
:::

См. [Выполнение кода](features/code-execution.md) и раздел **Terminal** в README ([features/tools.md]) для подробностей по каждому бэкенду.
## Настройки навыков

Навыки могут объявлять собственные параметры конфигурации через frontmatter в файле **SKILL.md**. Это не секретные значения (пути, предпочтения, настройки домена), хранящиеся в пространстве имён `skills.config` в файле `config.yaml`.

```yaml
skills:
  config:
    myplugin:
      path: ~/myplugin-data   # Example — each skill defines its own keys
```

**Как работают настройки навыков:**

- `hermes config migrate` сканирует все включённые навыки, ищет не настроенные параметры и предлагает их задать
- `hermes config show` отображает все параметры навыков в разделе «Skill Settings» вместе с соответствующим навыком
- При загрузке навыка его разрешённые значения конфигурации автоматически внедряются в контекст навыка

**Установка значений вручную:**

```bash
hermes config set skills.config.myplugin.path ~/myplugin-data
```

Подробности о объявлении параметров конфигурации в собственных навыках см. в разделе [Creating Skills — Config Settings](/developer-guide/creating-skills#config-settings-configyaml).

### Защита записей навыков, создаваемых агентом

Когда агент использует `skill_manage` для создания, редактирования, патча или удаления навыка, Hermes может опционально сканировать новое/обновлённое содержимое на наличие опасных шаблонов ключевых слов (сбор учётных данных, очевидные инъекции подсказок, инструкции по exfil). Сканер **выключен по умолчанию** — реальные рабочие процессы агента, которые легитимно обращаются к `~/.ssh/` или упоминают `$OPENAI_API_KEY`, слишком часто срабатывали на эвристике. Включи его обратно, если хочешь, чтобы сканер запрашивал подтверждение перед тем, как записи навыков агента будут применены:

```yaml
skills:
  guard_agent_created: true   # default: false
```

Когда включён, любое помеченное действие `skill_manage` появляется как запрос на одобрение с объяснением сканера. Принятые записи применяются; отклонённые возвращают агенту поясняющую ошибку.
## Конфигурация памяти

```yaml
memory:
  memory_enabled: true
  user_profile_enabled: true
  memory_char_limit: 2200   # ~800 tokens
  user_char_limit: 1375     # ~500 tokens
```
## Безопасность чтения файлов

Контролирует, сколько контента может вернуть один вызов `read_file`. Чтения, превышающие лимит, отклоняются с ошибкой, предлагающей агенту использовать `offset` и `limit` для меньшего диапазона. Это предотвращает заполнение окна контекста одним чтением минифицированного JS‑бандла или большого файла данных.

```yaml
file_read_max_chars: 100000  # default — ~25-35K tokens
```

Увеличь значение, если ты работаешь с моделью с большим окном контекста и часто читаешь большие файлы. Понизь его для моделей с небольшим контекстом, чтобы чтения оставались эффективными:

```yaml
# Large context model (200K+)
file_read_max_chars: 200000

# Small local model (16K context)
file_read_max_chars: 30000
```

Агент также автоматически удаляет дублирование чтений файлов — если один и тот же регион файла читается дважды и файл не изменился, вместо повторной отправки содержимого возвращается лёгкая заглушка. Это сбрасывается при сжатии контекста, чтобы агент мог повторно читать файлы после того, как их содержимое было суммировано.
## Ограничения усечения вывода инструмента

Три связанных лимита контролируют, сколько необработанного вывода может вернуть инструмент, прежде чем Hermes усечёт его:

```yaml
tool_output:
  max_bytes: 50000        # terminal output cap (chars)
  max_lines: 2000         # read_file pagination cap
  max_line_length: 2000   # per-line cap in read_file's line-numbered view
```

- **`max_bytes`** — Когда команда `terminal` генерирует более указанного количества символов совмещённого `stdout`/`stderr`, Hermes сохраняет первые 40 % и последние 60 % и вставляет между ними уведомление `[OUTPUT TRUNCATED]`. По умолчанию `50000` (≈12‑15 K токенов для типичных токенизаторов).
- **`max_lines`** — Верхняя граница параметра `limit` в отдельном вызове `read_file`. Запросы, превышающие это значение, ограничиваются, чтобы один вызов чтения не заполнял окно контекста. По умолчанию `2000`.
- **`max_line_length`** — Ограничение длины строки, применяемое при выводе `read_file` в виде нумерованного списка. Строки, превышающие это значение, усекаются до указанного количества символов с последующим `... [truncated]`. По умолчанию `2000`.

Повышай лимиты для моделей с большими окнами контекста, которые могут позволить больший объём необработанного вывода за один вызов. Понижай их для моделей с небольшим контекстом, чтобы результаты инструментов оставались компактными:

```yaml
# Large context model (200K+)
tool_output:
  max_bytes: 150000
  max_lines: 5000

# Small local model (16K context)
tool_output:
  max_bytes: 20000
  max_lines: 500
```
## Отключение глобального набора инструментов

Чтобы отключить конкретные наборы инструментов во всём CLI и на каждой платформе шлюза в одном месте, укажи их имена в `agent.disabled_toolsets`:

```yaml
agent:
  disabled_toolsets:
    - memory       # hide memory tools + MEMORY_GUIDANCE injection
    - web          # no web_search / web_extract anywhere
```

Это применяется **после** конфигурации инструментов для каждой платформы (`platform_toolsets`, записываемой командой `hermes tools`), поэтому набор инструментов, указанный здесь, всегда удаляется — даже если сохранённая конфигурация платформы всё ещё содержит его. Используй это, когда нужен единый переключатель для «выключить X везде», вместо редактирования более чем 15 строк платформ в UI `hermes tools`.

Оставление списка пустым или отсутствие ключа ничего не делает.
## Изоляция git worktree

Включи изолированные git worktree для одновременного запуска нескольких агентов в одном репозитории:

```yaml
worktree: true    # Always create a worktree (same as hermes -w)
# worktree: false # Default — only when -w flag is passed
```

Когда опция включена, каждая CLI‑сессия создаёт свежий worktree в каталоге `.worktrees/` со своей веткой. Агенты могут изменять файлы, выполнять commit, push и создавать PR, не мешая друг другу. Чистые worktree удаляются при выходе; «грязные» сохраняются для ручного восстановления.

Также можно перечислить файлы, игнорируемые git, которые следует копировать в worktree, с помощью файла `.worktreeinclude` в корне репозитория:

```
# .worktreeinclude
.env
.venv/
node_modules/
```
## Сжатие контекста

Hermes автоматически сжимает длинные беседы, чтобы оставаться в пределах окна контекста твоей модели. Суммаризатор сжатия — это отдельный вызов LLM — его можно направить к любому провайдеру или конечной точке.

Все настройки сжатия находятся в `config.yaml` (без переменных окружения).

### Полная справка

```yaml
compression:
  enabled: true                                     # Toggle compression on/off
  threshold: 0.50                                   # Compress at this % of context limit
  target_ratio: 0.20                                # Fraction of threshold to preserve as recent tail
  protect_last_n: 20                                # Min recent messages to keep uncompressed
  protect_first_n: 3                                # Non-system head messages pinned across compactions (0 = pin nothing)
  hygiene_hard_message_limit: 400                   # Gateway safety valve — see below

# The summarization model/provider is configured under auxiliary:
auxiliary:
  compression:
    model: ""                                       # Empty = use main chat model. Override with e.g. "google/gemini-3-flash-preview" for cheaper/faster compression.
    provider: "auto"                                # Provider: "auto", "openrouter", "nous", "codex", "main", etc.
    base_url: null                                  # Custom OpenAI-compatible endpoint (overrides provider)
```

:::info Миграция устаревшей конфигурации
Старые конфиги с `compression.summary_model`, `compression.summary_provider` и `compression.summary_base_url` автоматически мигрируют в `auxiliary.compression.*` при первой загрузке (версия конфига 17). Ручные действия не требуются.
:::

`hygiene_hard_message_limit` — это **предварительный предохранитель сжатия** только для gateway. Сессии с тысячами сообщений могут превысить лимит контекста модели до того, как сработает обычный порог процента контекста; когда количество сообщений пересекает этот потолок, Hermes принудительно выполняет сжатие независимо от использования токенов. По умолчанию `400` — увеличь значение для платформ, где обычны очень длинные сессии, уменьшай — чтобы заставить более агрессивное сжатие. Изменение этого параметра на работающем gateway вступает в силу со следующим сообщением (см. ниже).

`protect_first_n` определяет, сколько **не‑системных** начальных сообщений фиксируются при каждой компрессии. По умолчанию `3` — первый обмен пользователь/ассистент сохраняется после каждого прохода суммаризатора, чтобы исходная цель оставалась видимой. В длительных сессиях с «скользящей» компрессией, когда начальный ход уже не актуален, установи `protect_first_n: 0`, чтобы фиксировать только системный запрос + резюме + конец. Сам системный запрос всегда сохраняется независимо от этой настройки.

:::tip Горячая перезагрузка gateway для сжатия и длины контекста
Начиная с недавних релизов, изменение `model.context_length` или любого ключа `compression.*` в `config.yaml` на работающем gateway вступает в силу со следующим сообщением — перезапуск gateway, `/reset` или ротация сессии не требуются. Кешированная подпись агента включает эти ключи, поэтому gateway прозрачно перестраивает агента при обнаружении изменения. API‑ключи и конфиги инструментов/навыков всё ещё требуют обычных путей перезагрузки.
:::

### Распространённые варианты настройки

**По умолчанию (автоопределение) — никакой конфиг не нужен:**
```yaml
compression:
  enabled: true
  threshold: 0.50
```
Использует твоего основного провайдера и основную модель. Переопредели per‑task (например, `auxiliary.compression.provider: openrouter` + `model: google/gemini-2.5-flash`), если хочешь сжимать на более дешёвой модели, чем основная чат‑модель.

**Принудительно задать конкретного провайдера** (на основе OAuth или API‑ключа):
```yaml
auxiliary:
  compression:
    provider: nous
    model: gemini-3-flash
```
Работает с любым провайдером: `nous`, `openrouter`, `codex`, `anthropic`, `main` и т.д.

**Собственная конечная точка** (self‑hosted, Ollama, zai, DeepSeek и пр.):
```yaml
auxiliary:
  compression:
    model: glm-4.7
    base_url: https://api.z.ai/api/coding/paas/v4
```
Направляет запрос к пользовательской совместимой с OpenAI конечной точке. Для аутентификации использует `OPENAI_API_KEY`.

### Как взаимодействуют три настройки

| `auxiliary.compression.provider` | `auxiliary.compression.base_url` | Результат |
|----------------------------------|----------------------------------|-----------|
| `auto` (по умолчанию)            | не задано                        | Автоопределение лучшего доступного провайдера |
| `nous` / `openrouter` / и др.    | не задано                        | Принудительно использовать этот провайдер, использовать его аутентификацию |
| любой                            | задано                           | Напрямую использовать указанную конечную точку (провайдер игнорируется) |

:::warning Требование к длине контекста модели‑резюмера
Модель резюмера **должна** иметь окно контекста не меньше, чем у основной модели агента. Компрессор отправляет полную среднюю часть беседы модели‑резюмера — если окно контекста этой модели меньше, чем у основной модели, вызов суммаризации завершится ошибкой длины контекста. В этом случае средние ходы **отбрасываются без резюме**, и контекст беседы теряется без уведомления. Если переопределяешь модель, убедись, что её длина контекста соответствует или превышает длину контекста основной модели.
:::
## Движок контекста

Движок контекста управляет тем, как ведутся диалоги при приближении к лимиту токенов модели. Встроенный движок `compressor` использует сжатие с потерями (см. [Сжатие контекста](/developer-guide/context-compression-and-caching)). Движки‑плагины могут заменить его альтернативными стратегиями.

```yaml
context:
  engine: "compressor"    # default — built-in lossy summarization
```

Чтобы использовать движок‑плагин (например, LCM для безпотерьного управления контекстом):

```yaml
context:
  engine: "lcm"          # must match the plugin's name
```

Движки‑плагины **никогда не активируются автоматически** — необходимо явно задать `context.engine` в имя плагина. Доступные движки можно просмотреть и выбрать через `hermes plugins` → Provider Plugins → Context Engine.

См. [Поставщики памяти](/user-guide/features/memory-providers) для аналогичной системы единственного выбора для плагинов памяти.
## Давление бюджета итераций

Когда агент работает над сложной задачей с множеством вызовов инструментов, он может исчерпать свой бюджет итераций (по умолчанию: 90 ходов), не заметив, что подходит к концу. Давление бюджета автоматически предупреждает модель по мере приближения к лимиту:

| Порог | Уровень | Что видит модель |
|-----------|-------|---------------------|
| **70%** | Осторожно | `[BUDGET: 63/90. 27 iterations left. Start consolidating.]` |
| **90%** | Предупреждение | `[BUDGET WARNING: 81/90. Only 9 left. Respond NOW.]` |

Предупреждения внедряются в JSON последнего результата инструмента (как поле `_budget_warning`), а не как отдельные сообщения — это сохраняет кэширование подсказок и не нарушает структуру диалога.

```yaml
agent:
  max_turns: 90                # Max iterations per conversation turn (default: 90)
  api_max_retries: 3           # Retries per provider before fallback engages (default: 3)
```

Давление бюджета включено по умолчанию. Агент видит предупреждения естественно как часть результатов инструментов, что побуждает его консолидировать работу и предоставить ответ до исчерпания итераций.

Когда бюджет итераций полностью исчерпан, CLI выводит пользователю уведомление: `⚠ Iteration budget reached (90/90) — response may be incomplete`. Если бюджет заканчивается во время активной работы, агент генерирует сводку выполненного перед остановкой.

`agent.api_max_retries` управляет тем, сколько раз Hermes повторяет вызов API провайдера при временных ошибках (ограничения скорости, обрывы соединения, 5xx) **до** переключения на fallback‑provider. По умолчанию `3` — всего четыре попытки. Если у тебя настроены [fallback providers](/user-guide/features/fallback-providers) и ты хочешь переключаться быстрее, установи значение `0`, чтобы первая временная ошибка на основном провайдере сразу передавалась fallback‑провайдеру, а не тратилась на повторные попытки.

### Тайм‑ауты API

Hermes имеет отдельные уровни тайм‑аутов для потоковой передачи, а также детектор «застоя» для непотоковых вызовов. Детекторы застоя автоматически настраиваются для локальных провайдеров только при использовании их неявных значений по умолчанию.

| Тайм‑аут | По умолчанию | Локальные провайдеры | Конфиг / env |
|---------|--------------|----------------------|--------------|
| Тайм‑аут чтения сокета | 120s | Автоматически повышен до 1800s | `HERMES_STREAM_READ_TIMEOUT` |
| Детекция застоя потока | 180s | Автоотключено | `HERMES_STREAM_STALE_TIMEOUT` |
| Детекция застоя непотока | 300s | Автоотключено при неявных настройках | `providers.<id>.stale_timeout_seconds` или `HERMES_API_CALL_STALE_TIMEOUT` |
| Вызов API (не потоковый) | 1800s | Без изменений | `providers.<id>.request_timeout_seconds` / `timeout_seconds` или `HERMES_API_TIMEOUT` |

**Тайм‑аут чтения сокета** определяет, как долго httpx ждёт следующий кусок данных от провайдера. Локальные LLM могут тратить минуты на предварительную загрузку больших контекстов перед выдачей первого токена, поэтому Hermes повышает его до 30 минут, когда обнаруживает локальный эндпоинт. Если явно задать `HERMES_STREAM_READ_TIMEOUT`, это значение всегда используется независимо от детекции эндпоинта.

**Детекция застоя потока** завершает соединения, получающие keep‑alive ping SSE, но без реального контента. Для локальных провайдеров она полностью отключена, поскольку они не отправляют keep‑alive ping во время предварительной загрузки.

**Детекция застоя непотока** завершает непотоковые вызовы, которые слишком долго не дают ответа. По умолчанию Hermes отключает её на локальных эндпоинтах, чтобы избежать ложных срабатываний во время длительной предварительной загрузки. Если явно задать `providers.<id>.stale_timeout_seconds`, `providers.<id>.models.<model>.stale_timeout_seconds` или `HERMES_API_CALL_STALE_TIMEOUT`, это значение будет учитываться даже для локальных эндпоинтов.
## Предупреждения о давлении контекста

Отдельно от давления бюджета итераций, **контекстное давление** отслеживает, насколько беседа приближается к **порогу уплотнения** — точке, в которой срабатывает сжатие контекста для суммирования более старых сообщений. Это помогает и тебе, и агенту понять, когда разговор становится слишком длинным.

| Прогресс | Уровень | Что происходит |
|----------|---------|----------------|
| **≥ 60 %** до порога | Info | CLI показывает голубую полосу прогресса; gateway отправляет информационное уведомление |
| **≥ 85 %** до порога | Warning | CLI показывает ярко‑жёлтую полосу прогресса; gateway предупреждает, что уплотнение неизбежно |

В CLI давление контекста отображается в виде полосы прогресса в ленте вывода инструмента:

```
  ◐ context ████████████░░░░░░░░ 62% to compaction  48k threshold (50%) · approaching compaction
```

На платформах обмена сообщениями отправляется простое текстовое уведомление:

```
◐ Context: ████████████░░░░░░░░ 62% to compaction (threshold: 50% of window).
```

Если автосжатие отключено, предупреждение сообщает, что контекст может быть усечён вместо этого.

Контекстное давление работает автоматически — настройка не требуется. Оно срабатывает исключительно как пользовательское уведомление и не изменяет поток сообщений и не внедряет ничего в контекст модели.
## Стратегии пула учётных данных

Когда у тебя есть несколько API‑ключей или OAuth‑токенов для одного и того же провайдера, настрой стратегию ротации:

```yaml
credential_pool_strategies:
  openrouter: round_robin    # cycle through keys evenly
  anthropic: least_used      # always pick the least-used key
```

Варианты: `fill_first` (по умолчанию), `round_robin`, `least_used`, `random`. См. [Пулы учётных данных](/user-guide/features/credential-pools) для полной документации.
## Кеширование подсказок

Hermes автоматически включает кросс‑сессионное кеширование подсказок, когда активный провайдер это поддерживает — без необходимости пользовательской конфигурации.

Для Claude на **native Anthropic**, **OpenRouter** и **Nous Portal** Hermes добавляет контрольные точки `cache_control` с TTL = 1 час (`ttl: "1h"`) к системной подсказке и блокам навыков. Первая отправка в течение свежего часа оплачивается по полной ставке ввода; последующие отправки в любой сессии в течение того же часа берут данные из кеша по сниженной ставке чтения из кеша. Это означает, что системная подсказка, загруженный контент навыков и начальная часть любого длинного контекста переиспользуются в разных сессиях `hermes` и в форкнутых субагентах в течение первого часа.

В Qwen Cloud (Alibaba DashScope) верхний предел TTL кеша установлен в 5 минут, поэтому Hermes использует TTL = 5 минут для контрольных точек там. Другие пути Claude через сторонних провайдеров (AWS Bedrock, Azure Foundry) переходят к кэшированию по умолчанию у провайдера. xAI Grok использует отдельный механизм привязки к идентификатору разговора на уровне сессии — см. [xAI prompt caching](/integrations/providers#xai-grok--responses-api--prompt-caching).

Флажка для отключения этой функции нет — кеширование всегда включено и экономит деньги даже в однобоких диалогах, поскольку сама системная подсказка составляет значительную часть количества входных токенов.
## Вспомогательные модели

Hermes использует «auxiliary» модели для побочных задач, таких как анализ изображений, суммирование веб‑страниц, анализ скриншотов браузера, генерация названия сессии и сжатие контекста. По умолчанию (`auxiliary.*.provider: "auto"`), Hermes направляет каждую auxiliary‑задачу к твоей **основной чат‑модели** — тому же провайдеру/модели, который ты выбрал в `hermes model`. Дополнительная настройка не требуется, но имей в виду, что на дорогих моделях рассуждения (Opus, MiniMax M2.7 и т.п.) auxiliary‑задачи добавляют заметные затраты. Если нужны дешёвые и быстрые побочные задачи независимо от основной модели, явно укажи `auxiliary.<task>.provider` и `auxiliary.<task>.model` (например, Gemini Flash на OpenRouter для vision и web‑extract).

:::note Почему «auto» использует твою основную модель
В более ранних сборках агрегаторы (OpenRouter, Nous Portal) использовали дешёвый провайдер‑по‑умолчанию. Это было неожиданно — пользователи с подпиской на агрегатор видели, как их auxiliary‑трафик обрабатывается другой моделью. Сейчас `auto` использует основную модель для всех, а переопределения per‑task в `config.yaml` по‑прежнему имеют приоритет (см. [Полный справочник конфигурации вспомогательных моделей](#full-auxiliary-config-reference) ниже).
:::

### Настройка вспомогательных моделей интерактивно

Вместо ручного редактирования YAML запусти `hermes model` и выбери **«Configure auxiliary models»** в меню. Появится интерактивный picker задачи:

```
$ hermes model
→ Configure auxiliary models

[ ] vision               currently: auto / main model
[ ] web_extract          currently: auto / main model
[ ] title_generation     currently: openrouter / google/gemini-3-flash-preview
[ ] compression          currently: auto / main model
[ ] approval             currently: auto / main model
[ ] triage_specifier     currently: auto / main model
[ ] kanban_decomposer    currently: auto / main model
[ ] profile_describer    currently: auto / main model
```

Выбери задачу, провайдера (OAuth‑потоки откроют браузер; провайдеры с API‑ключом запросят его), модель. Изменения сохраняются в `auxiliary.<task>.*` в `config.yaml`. Тот же механизм, что и у выбора основной модели — дополнительных синтаксисов не требуется.

### Видео‑урок

<div style={{position: 'relative', width: '100%', aspectRatio: '16 / 9', marginBottom: '1.5rem'}}>
  <iframe
    src="https://www.youtube.com/embed/NoF-YajElIM"
    title="Hermes Agent — Auxiliary Models Tutorial"
    style={{position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', border: 0}}
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
    allowFullScreen
  />
</div>

### Универсальный шаблон конфигурации

Каждый слот модели в Hermes — auxiliary‑задачи, compression, fallback — использует одинаковые три параметра:

| Ключ | Что делает | По‑умолчанию |
|-----|-------------|--------------|
| `provider` | Какой провайдер использовать для аутентификации и маршрутизации | `"auto"` |
| `model` | Какую модель запрашивать | провайдер‑по‑умолчанию |
| `base_url` | Пользовательский совместимый с OpenAI эндпоинт (перезаписывает провайдера) | не задан |

Когда задан `base_url`, Hermes игнорирует `provider` и обращается напрямую к этому эндпоинту (используя `api_key` или `OPENAI_API_KEY` для аутентификации). Если указан только `provider`, Hermes использует встроенную аутентификацию и базовый URL провайдера.

Доступные провайдеры для auxiliary‑задач: `auto`, `main`, плюс любой провайдер из [реестра провайдеров](/reference/environment-variables) — `openrouter`, `nous`, `openai-codex`, `copilot`, `copilot-acp`, `anthropic`, `gemini`, `google-gemini-cli`, `qwen-oauth`, `zai`, `kimi-coding`, `kimi-coding-cn`, `minimax`, `minimax-cn`, `minimax-oauth`, `deepseek`, `nvidia`, `xai`, `xai-oauth`, `ollama-cloud`, `alibaba`, `bedrock`, `huggingface`, `arcee`, `xiaomi`, `kilocode`, `opencode-zen`, `opencode-go`, `azure-foundry` — или любой именованный пользовательский провайдер из списка `custom_providers` (например, `provider: "beans"`).

:::tip MiniMax OAuth
`minimax-oauth` выполняет вход через браузер OAuth (API‑ключ не нужен). Запусти `hermes model` и выбери **MiniMax (OAuth)** для аутентификации. Вспомогательные задачи автоматически используют `MiniMax-M2.7-highspeed`. См. [руководство MiniMax OAuth](../guides/minimax-oauth.md).
:::

:::tip xAI Grok OAuth
`xai-oauth` выполняет вход через браузер OAuth для подписчиков SuperGrok и X Premium+ (API‑ключ не нужен). Запусти `hermes model` и выбери **xAI Grok OAuth (SuperGrok / Premium+)** для аутентификации. Тот же OAuth‑токен переиспользуется для всех прямых запросов к xAI (чат, auxiliary‑задачи, TTS, генерация изображений, видео, транскрипция). См. [руководство xAI Grok OAuth](../guides/xai-grok-oauth.md), а если Hermes работает на удалённом хосте — [OAuth через SSH / удалённые хосты](../guides/oauth-over-ssh.md).
:::

:::warning `"main"` используется только для auxiliary‑задач
Опция провайдера `"main"` означает «использовать тот же провайдер, что и у моего основного агента» — она действительна лишь внутри конфигураций `auxiliary:`, `compression:` и `fallback_model:`. Это **не** допустимое значение для верхнеуровневой настройки `model.provider`. Если ты используешь пользовательский совместимый с OpenAI эндпоинт, укажи `provider: custom` в секции `model:`. См. [AI Providers](/integrations/providers) для полного списка вариантов провайдеров основной модели.
:::

### Полный справочник конфигурации вспомогательных моделей

```yaml
auxiliary:
  # Image analysis (vision_analyze tool + browser screenshots)
  vision:
    provider: "auto"           # "auto", "openrouter", "nous", "codex", "main", etc.
    model: ""                  # e.g. "openai/gpt-4o", "google/gemini-2.5-flash"
    base_url: ""               # Custom OpenAI-compatible endpoint (overrides provider)
    api_key: ""                # API key for base_url (falls back to OPENAI_API_KEY)
    timeout: 120               # seconds — LLM API call timeout; vision payloads need generous timeout
    download_timeout: 30       # seconds — image HTTP download; increase for slow connections

  # Web page summarization + browser page text extraction
  web_extract:
    provider: "auto"
    model: ""                  # e.g. "google/gemini-2.5-flash"
    base_url: ""
    api_key: ""
    timeout: 360               # seconds (6min) — per-attempt LLM summarization

  # Dangerous command approval classifier
  approval:
    provider: "auto"
    model: ""
    base_url: ""
    api_key: ""
    timeout: 30                # seconds

  # Context compression timeout (separate from compression.* config)
  compression:
    timeout: 120               # seconds — compression summarizes long conversations, needs more time

  # Skills hub — skill matching and search
  skills_hub:
    provider: "auto"
    model: ""
    base_url: ""
    api_key: ""
    timeout: 30

  # MCP tool dispatch
  mcp:
    provider: "auto"
    model: ""
    base_url: ""
    api_key: ""
    timeout: 30

  # Kanban triage specifier — `hermes kanban specify <id>` (or the
  # dashboard's ✨ Specify button on Triage-column cards) uses this
  # slot to expand a one-liner into a concrete spec and promote the
  # task to `todo`. Cheap fast models work well here; spec expansion
  # is short and doesn't need reasoning depth.
  triage_specifier:
    provider: "auto"
    model: ""
    base_url: ""
    api_key: ""
    timeout: 120
```

:::tip
У каждой auxiliary‑задачи есть настраиваемый `timeout` (в секундах). По‑умолчанию: vision 120 s, web_extract 360 s, approval 30 s, compression 120 s. Увеличь их, если используешь медленные локальные модели для auxiliary‑задач. Для vision также есть отдельный `download_timeout` (по‑умолчанию 30 s) для загрузки изображений по HTTP — увеличь его при медленном соединении или при работе с собственными серверами изображений.
:::

:::info
Сжатие контекста имеет собственный блок `compression:` для порогов и блок `auxiliary.compression:` для настроек провайдера/модели — см. [Context Compression](#context-compression) выше. Запасный (вариант) использует блок `fallback_model:` — см. [Fallback Model](/integrations/providers#fallback-providers). Все три следуют одной схеме provider/model/base_url.
:::

### Маршрутизация OpenRouter и Pareto Code для auxiliary‑задач

Когда auxiliary‑задача попадает в OpenRouter (явно или через `provider: "main"` при основной модели на OpenRouter), настройки `provider_routing` и `openrouter.min_coding_score` основного агента **не передаются** — так задумано, каждая auxiliary‑задача независима. Чтобы задать предпочтения провайдера OpenRouter или использовать [маршрутизатор Pareto Code](/integrations/providers#openrouter-pareto-code-router) для конкретной auxiliary‑задачи, укажи их per‑task через `extra_body`:

```yaml
auxiliary:
  compression:
    provider: openrouter
    model: openrouter/pareto-code         # use the Pareto Code router for this task
    extra_body:
      provider:                            # OpenRouter provider routing prefs
        order: [anthropic, google]         # try these providers in order
        sort: throughput                   # or "price" | "latency"
        # only: [anthropic]                # restrict to a specific provider
        # ignore: [deepinfra]              # exclude specific providers
      plugins:                             # OpenRouter Pareto Code router knob
        - id: pareto-router
          min_coding_score: 0.5            # 0.0–1.0; higher = stronger coders
```

Структура соответствует тому, что принимает OpenRouter в теле запроса chat completions. Hermes передаёт весь `extra_body` дословно, поэтому любые другие поля тела запроса, описанные в [openrouter.ai/docs](https://openrouter.ai/docs), работают так же.

### Смена модели Vision

Чтобы использовать GPT‑4o вместо Gemini Flash для анализа изображений:

```yaml
auxiliary:
  vision:
    model: "openai/gpt-4o"
```

Или через переменную окружения (в `~/.hermes/.env`):

```bash
AUXILIARY_VISION_MODEL=openai/gpt-4o
```

### Параметры провайдера

Эти параметры относятся к **конфигурациям auxiliary‑задач** (`auxiliary:`, `compression:`, `fallback_model:`), а не к основной настройке `model.provider`.

| Провайдер | Описание | Требования |
|----------|----------|------------|
| `"auto"` | Лучший доступный (по‑умолчанию). Vision пробует OpenRouter → Nous → Codex. | — |
| `"openrouter"` | Принудительно OpenRouter — маршрутизирует к любой модели (Gemini, GPT‑4o, Claude и др.) | `OPENROUTER_API_KEY` |
| `"nous"` | Принудительно Nous Portal | `hermes auth` |
| `"codex"` | Принудительно Codex OAuth (учётная запись ChatGPT). Поддерживает vision (gpt-5.3-codex). | `hermes model` → Codex |
| `"minimax-oauth"` | Принудительно MiniMax OAuth (вход через браузер, без API‑ключа). Использует MiniMax-M2.7-highspeed для auxiliary‑задач. | `hermes model` → MiniMax (OAuth) |
| `"xai-oauth"` | Принудительно xAI Grok OAuth (вход через браузер для подписчиков SuperGrok или X Premium+, без API‑ключа). Тот же токен покрывает чат, TTS, генерацию изображений, видео и транскрипцию. | `hermes model` → xAI Grok OAuth (SuperGrok / Premium+) |
| `"main"` | Использовать твой активный пользовательский/основной эндпоинт. Может быть получен из `OPENAI_BASE_URL` + `OPENAI_API_KEY` или из пользовательского эндпоинта, сохранённого через `hermes model` / `config.yaml`. Работает с OpenAI, локальными моделями или любой совместимой API. **Только для auxiliary‑задач — недопустимо в `model.provider`.** | Учётные данные пользовательского эндпоинта + base URL |

Провайдеры с прямыми API‑ключами из основного каталога также работают здесь, если ты хочешь, чтобы побочные задачи обходили твой стандартный роутер. `gmi` доступен после настройки `GMI_API_KEY`:

```yaml
auxiliary:
  compression:
    provider: "gmi"
    model: "anthropic/claude-opus-4.6"
```

Для маршрутизации GMI указывай точный ID модели, возвращаемый эндпоинтом `/v1/models` GMI.

### Распространённые настройки

**Использование прямого пользовательского эндпоинта** (чётче, чем `provider: "main"` для локальных/самохостинг‑API):
```yaml
auxiliary:
  vision:
    base_url: "http://localhost:1234/v1"
    api_key: "local-key"
    model: "qwen2.5-vl"
```

`base_url` имеет приоритет над `provider`, поэтому это самый явный способ направить auxiliary‑задачу к конкретному эндпоинту. При переопределении эндпоинта Hermes использует указанный `api_key` или, если его нет, `OPENAI_API_KEY`; он не переиспользует `OPENROUTER_API_KEY` для этого кастомного эндпоинта.

**Использование OpenAI API‑ключа для vision:**
```yaml
# In ~/.hermes/.env:
# OPENAI_BASE_URL=https://api.openai.com/v1
# OPENAI_API_KEY=sk-...

auxiliary:
  vision:
    provider: "main"
    model: "gpt-4o"       # or "gpt-4o-mini" for cheaper
```

**Использование OpenRouter для vision** (маршрутизация к любой модели):
```yaml
auxiliary:
  vision:
    provider: "openrouter"
    model: "openai/gpt-4o"      # or "google/gemini-2.5-flash", etc.
```

**Использование Codex OAuth** (учётная запись ChatGPT Pro/Plus — API‑ключ не нужен):
```yaml
auxiliary:
  vision:
    provider: "codex"     # uses your ChatGPT OAuth token
    # model defaults to gpt-5.3-codex (supports vision)
```

**Использование MiniMax OAuth** (вход через браузер, без API‑ключа):
```yaml
model:
  default: MiniMax-M2.7
  provider: minimax-oauth
  base_url: https://api.minimax.io/anthropic
```
Запусти `hermes model` и выбери **MiniMax (OAuth)** для входа и автоматической настройки. Для региона China базовый URL будет `https://api.minimaxi.com/anthropic`. См. [руководство MiniMax OAuth](../guides/minimax-oauth.md) для полного пошагового описания.

**Использование локальной/самохостинг‑модели:**
```yaml
auxiliary:
  vision:
    provider: "main"      # uses your active custom endpoint
    model: "my-local-model"
```

`provider: "main"` использует тот же провайдер, что и у Hermes для обычного чата — будь то именованный пользовательский провайдер (например, `beans`), встроенный провайдер вроде `openrouter` или наследованный эндпоинт `OPENAI_BASE_URL`.

:::tip
Если ты используешь Codex OAuth в качестве провайдера основной модели, vision работает автоматически — дополнительная настройка не требуется. Codex включён в цепочку автоопределения для vision.
:::

:::warning
**Vision требует мультимодальную модель.** Если ты задаёшь `provider: "main"`, убедись, что твой эндпоинт поддерживает мультимодальность/vision — иначе анализ изображений завершится ошибкой.
:::

### Переменные окружения (устаревшие)

Auxiliary‑модели также можно настроить через переменные окружения. Однако предпочтительнее использовать `config.yaml` — так проще управлять и доступны все опции, включая `base_url` и `api_key`.

| Параметр | Переменная окружения |
|----------|----------------------|
| Vision‑provider | `AUXILIARY_VISION_PROVIDER` |
| Vision‑model | `AUXILIARY_VISION_MODEL` |
| Vision‑endpoint | `AUXILIARY_VISION_BASE_URL` |
| Vision‑API‑key | `AUXILIARY_VISION_API_KEY` |
| Web‑extract provider | `AUXILIARY_WEB_EXTRACT_PROVIDER` |
| Web‑extract model | `AUXILIARY_WEB_EXTRACT_MODEL` |
| Web‑extract endpoint | `AUXILIARY_WEB_EXTRACT_BASE_URL` |
| Web‑extract API‑key | `AUXILIARY_WEB_EXTRACT_API_KEY` |

Настройки compression и fallback‑model доступны только через `config.yaml`.

:::tip
Запусти `hermes config`, чтобы увидеть текущие настройки auxiliary‑моделей. Переопределения отображаются только тогда, когда они отличаются от значений по‑умолчанию.
:::
## Усилие рассуждения

Контролируй, сколько «размышлений» модель выполняет перед ответом:

```yaml
agent:
  reasoning_effort: ""   # empty = medium (default). Options: none, minimal, low, medium, high, xhigh (max)
```

Если параметр не установлен (по умолчанию), усилие рассуждения принимает значение «medium» — сбалансированный уровень, который хорошо подходит для большинства задач. Установка значения переопределяет его: более высокое усилие рассуждения даёт лучшие результаты на сложных задачах за счёт большего количества токенов и задержки.

Ты также можешь изменить усилие рассуждения во время выполнения с помощью команды `/reasoning`:

```
/reasoning           # Show current effort level and display state
/reasoning high      # Set reasoning effort to high
/reasoning none      # Disable reasoning
/reasoning show      # Show model thinking above each response
/reasoning hide      # Hide model thinking
```
## Принудительное использование инструментов

Некоторые модели иногда описывают предполагаемые действия в виде текста вместо реального вызова инструмента («Я бы запустил тесты…» вместо фактического вызова терминала). Принудительное использование инструментов внедряет в подсказку системы руководство, которое заставляет модель действительно вызывать инструменты.

```yaml
agent:
  tool_use_enforcement: "auto"   # "auto" | true | false | ["model-substring", ...]
```

| Value | Behavior |
|-------|----------|
| `"auto"` (default) | Включено для моделей, соответствующих: `gpt`, `codex`, `gemini`, `gemma`, `grok`. Отключено для всех остальных (Claude, DeepSeek, Qwen и т.д.). |
| `true` | Всегда включено, независимо от модели. Полезно, если ты замечаешь, что текущая модель описывает действия вместо их выполнения. |
| `false` | Всегда отключено, независимо от модели. |
| `["gpt", "codex", "qwen", "llama"]` | Включено только когда имя модели содержит одну из указанных подстрок (без учёта регистра). |

### Что внедряется

Когда включено, в подсказку системы могут быть добавлены три уровня руководства:

1. **Общее принудительное использование инструментов** (для всех совпадающих моделей) — инструктирует модель сразу вызывать инструменты вместо описания намерений, продолжать работу до завершения задачи и никогда не завершать ход обещанием выполнить действие в будущем.

2. **Дисциплина выполнения OpenAI** (только модели GPT и Codex) — дополнительное руководство, учитывающее специфические сбои GPT: отказ от работы над частичными результатами, пропуск предварительных запросов, галлюцинации вместо использования инструментов и объявление «завершено» без проверки.

3. **Оперативное руководство Google** (только модели Gemini и Gemma) — лаконичность, абсолютные пути, параллельные вызовы инструментов и паттерн «проверить‑прежде‑чем‑редактировать».

Это прозрачно для пользователя и влияет только на подсказку системы. Модели, которые уже надёжно используют инструменты (например, Claude), не нуждаются в этом руководстве, поэтому `"auto"` их исключает.

### Когда включать

Если ты используешь модель, не входящую в список по умолчанию, и замечаешь, что она часто описывает, что *сделала бы*, вместо фактического выполнения, установи `tool_use_enforcement: true` или добавь подстроку модели в список:

```yaml
agent:
  tool_use_enforcement: ["gpt", "codex", "gemini", "grok", "my-custom-model"]
```
## Конфигурация TTS

```yaml
tts:
  provider: "edge"              # "edge" | "elevenlabs" | "openai" | "minimax" | "mistral" | "gemini" | "xai" | "neutts"
  speed: 1.0                    # Global speed multiplier (fallback for all providers)
  edge:
    voice: "en-US-AriaNeural"   # 322 voices, 74 languages
    speed: 1.0                  # Speed multiplier (converted to rate percentage, e.g. 1.5 → +50%)
  elevenlabs:
    voice_id: "pNInz6obpgDQGcFmaJgB"
    model_id: "eleven_multilingual_v2"
  openai:
    model: "gpt-4o-mini-tts"
    voice: "alloy"              # alloy, echo, fable, onyx, nova, shimmer
    speed: 1.0                  # Speed multiplier (clamped to 0.25–4.0 by the API)
    base_url: "https://api.openai.com/v1"  # Override for OpenAI-compatible TTS endpoints
  minimax:
    speed: 1.0                  # Speech speed multiplier
    # base_url: ""              # Optional: override for OpenAI-compatible TTS endpoints
  mistral:
    model: "voxtral-mini-tts-2603"
    voice_id: "c69964a6-ab8b-4f8a-9465-ec0925096ec8"  # Paul - Neutral (default)
  gemini:
    model: "gemini-2.5-flash-preview-tts"   # or gemini-2.5-pro-preview-tts
    voice: "Kore"               # 30 prebuilt voices: Zephyr, Puck, Kore, Enceladus, etc.
  xai:
    voice_id: "eve"             # xAI TTS voice
    language: "en"              # ISO 639-1
    sample_rate: 24000
    bit_rate: 128000            # MP3 bitrate
    # base_url: "https://api.x.ai/v1"
  neutts:
    ref_audio: ''
    ref_text: ''
    model: neuphonic/neutts-air-q4-gguf
    device: cpu
```

Это управляет как инструментом `text_to_speech`, так и озвученными ответами в голосовом режиме (`/voice tts` в CLI или шлюзе обмена сообщениями).

**Иерархия запасных вариантов скорости:** скорость, специфичная для провайдера (например, `tts.edge.speed`) → глобальная `tts.speed` → значение по умолчанию `1.0`. Установи глобальную `tts.speed`, чтобы задать одинаковую скорость для всех провайдеров, либо переопредели её для отдельного провайдера для более точного контроля.
## Настройки отображения

```yaml
display:
  tool_progress: all      # off | new | all | verbose
  tool_progress_command: false  # Enable /verbose slash command in messaging gateway
  platforms: {}           # Per-platform display overrides (see below)
  tool_progress_overrides: {}  # DEPRECATED — use display.platforms instead
  interim_assistant_messages: true  # Gateway: send natural mid-turn assistant updates as separate messages
  skin: default           # Built-in or custom CLI skin (see user-guide/features/skins)
  personality: "kawaii"  # Legacy cosmetic field still surfaced in some summaries
  compact: false          # Compact output mode (less whitespace)
  resume_display: full    # full (show previous messages on resume) | minimal (one-liner only)
  bell_on_complete: false # Play terminal bell when agent finishes (great for long tasks)
  show_reasoning: false   # Show model reasoning/thinking above each response (toggle with /reasoning show|hide)
  streaming: false        # Stream tokens to terminal as they arrive (real-time output)
  show_cost: false        # Show estimated $ cost in the CLI status bar
  timestamps: false       # When true, prefixes user and assistant labels with [HH:MM] timestamps in the CLI / TUI transcript
  tool_preview_length: 0  # Max chars for tool call previews (0 = no limit, show full paths/commands)
  runtime_footer:         # Gateway: append a runtime-context footer to final replies
    enabled: false
    fields: ["model", "context_pct", "cwd"]
  file_mutation_verifier: true    # Append an advisory footer when write_file/patch calls failed this turn
  language: en            # UI language for static messages (approval prompts, some gateway replies). en | zh | zh-hant | ja | de | es | fr | tr | uk | af | ko | it | ga | pt | ru | hu
```

### Проверка изменения файлов

Когда `display.file_mutation_verifier` установлен в `true` (по умолчанию), Hermes добавляет однострочное advisory к окончательному ответу ассистента каждый раз, когда вызов `write_file` или `patch` завершился неудачей в течение хода и никогда не был заменён успешной записью в тот же путь. Это ловит класс переутверждений типа «пакет параллельных патчей, половина тихо падает, модель подводит итог успеха», без необходимости вручную запускать `git status` после каждого изменения.

Пример нижнего колонтитула:

```
⚠️ File-mutation verifier: 3 file(s) were NOT modified this turn despite any wording above that may suggest otherwise. Run `git status` or `read_file` to confirm.
  • concepts/automatic-organization.md — [patch] Could not find match for old_string
  • concepts/lora.md — [patch] Could not find match for old_string
  • concepts/rag-pipeline.md — [patch] Could not find match for old_string
```

Установи `file_mutation_verifier: false` (или `HERMES_FILE_MUTATION_VERIFIER=0`), чтобы отключить нижний колонтитул. Проверка срабатывает только когда в конце хода остаются реальные неудачи — модель, которая повторно пытается применить неудавшийся патч и succeeds в том же ходе, не вызовет её для этого файла.

### Язык UI для статических сообщений

Параметр `display.language` переводит небольшой набор статических сообщений, видимых пользователю — подсказку подтверждения в CLI, несколько ответов шлюза на slash‑команды (например, уведомления restart‑drain, «approval expired», «goal cleared»). Он **не** переводит ответы агента, строки журналов, вывод инструментов, трассировки ошибок или описания slash‑команд — они остаются на английском. Если нужно, чтобы сам агент отвечал на другом языке, просто укажи это в своём запросе или системном сообщении.

Поддерживаемые значения: `en` (по умолчанию), `zh` (упрощённый китайский), `ja` (японский), `de` (немецкий), `es` (испанский), `fr` (французский), `tr` (турецкий), `uk` (украинский). Неизвестные значения возвращаются к английскому.

Также можно задать это для отдельной сессии через переменную окружения `HERMES_LANGUAGE`, которая переопределяет значение из конфигурации.

```yaml
display:
  language: zh   # CLI approval prompts appear in Chinese
```

| Режим   | Что отображается                              |
|---------|-----------------------------------------------|
| `off`   | Тихо — только окончательный ответ             |
| `new`   | Индикатор инструмента только при смене инструмента |
| `all`   | Каждый вызов инструмента с коротким превью (по умолчанию) |
| `verbose` | Полные аргументы, результаты и отладочные логи |

В CLI переключай эти режимы командой `/verbose`. Чтобы использовать `/verbose` в мессенджерах (Telegram, Discord, Slack и т.д.), включи `tool_progress_command: true` в секции `display` выше. Команда будет переключать режим и сохранять его в конфигурацию.

### Нижний колонтитул метаданных выполнения (только шлюз)

Когда `display.runtime_footer.enabled: true`, Hermes добавляет небольшой нижний колонтитул с контекстом выполнения к **окончательному** сообщению каждого хода шлюза — ту же информацию, которую CLI показывает в строке состояния (модель, % контекста, cwd, длительность сессии, токены, стоимость). По умолчанию отключено; включайте по желанию для каждого шлюза, если ваша команда хочет, чтобы каждый ответ содержал provenance.

```yaml
display:
  runtime_footer:
    enabled: true
    fields: ["model", "context_pct", "cwd"]   # any of: model, context_pct, cwd, duration, tokens, cost
```

Slash‑команда `/footer` переключает это во время выполнения в любой сессии.

Пример нижнего колонтитула, добавленного к ответу в Telegram/Discord/Slack:

```
— claude-opus-4.7 · 12 tool calls · 2m 14s · $0.042
```

Нижний колонтитул добавляется только к **окончательному** сообщению хода; промежуточные обновления остаются чистыми.

### Переопределения прогресса по платформам

Разные платформы требуют разного уровня детализации. Например, Signal не может редактировать сообщения, поэтому каждое обновление прогресса становится отдельным сообщением — это шумно. Используй `display.platforms`, чтобы задать режимы для каждой платформы:

```yaml
display:
  tool_progress: all          # global default
  platforms:
    signal:
      tool_progress: 'off'    # silence progress on Signal
    telegram:
      tool_progress: verbose  # detailed progress on Telegram
    slack:
      tool_progress: 'off'    # quiet in shared Slack workspace
```

Платформы без переопределения используют глобальное значение `tool_progress`. Допустимые ключи платформ: `telegram`, `discord`, `slack`, `signal`, `whatsapp`, `matrix`, `mattermost`, `email`, `sms`, `homeassistant`, `dingtalk`, `feishu`, `wecom`, `weixin`, `bluebubbles`, `qqbot`. Устаревший ключ `display.tool_progress_overrides` всё ещё загружается для обратной совместимости, но помечен как устаревший и при первом загрузке мигрирует в `display.platforms`.

`interim_assistant_messages` работает только в шлюзе. Когда включено, Hermes отправляет завершённые промежуточные обновления ассистента как отдельные сообщения чата. Это независимо от `tool_progress` и не требует потоковой передачи в шлюзе.
## Конфиденциальность

```yaml
privacy:
  redact_pii: false  # Strip PII from LLM context (gateway only)
```

Когда `redact_pii` имеет значение `true`, шлюз редактирует персонально идентифицируемую информацию в системном подсказке перед отправкой её в LLM на поддерживаемых платформах:

| Поле | Обработка |
|-------|-----------|
| Номера телефонов (идентификатор пользователя в WhatsApp/Signal) | Хэшируется в `user_<12-char-sha256>` |
| Идентификаторы пользователей | Хэшируется в `user_<12-char-sha256>` |
| Идентификаторы чатов | Хэшируется числовая часть, префикс платформы сохраняется (`telegram:<hash>`) |
| Идентификаторы домашних каналов | Хэшируется числовая часть |
| Имена / пользовательские имена | **Не изменяется** (выбираются пользователем, публично видимы) |

**Поддержка платформ:** Редактирование применяется к WhatsApp, Signal и Telegram. Discord и Slack исключены, потому что их системы упоминаний (`<@user_id>`) требуют реального идентификатора в контексте LLM.

Хэши детерминированы — один и тот же пользователь всегда получает один и тот же хэш, поэтому модель всё ещё может различать пользователей в групповых чатах. Маршрутизация и доставка используют оригинальные значения внутри системы.
## Speech-to-Text (STT)

```yaml
stt:
  provider: "local"            # "local" | "groq" | "openai" | "mistral"
  local:
    model: "base"              # tiny, base, small, medium, large-v3
  openai:
    model: "whisper-1"         # whisper-1 | gpt-4o-mini-transcribe | gpt-4o-transcribe
  # model: "whisper-1"         # Legacy fallback key still respected
```

Поведение провайдера:

- `local` использует `faster-whisper`, работающий на твоём устройстве. Установи его отдельно командой `pip install faster-whisper`.
- `groq` использует совместимый с Whisper эндпоинт Groq и читает переменную `GROQ_API_KEY`.
- `openai` использует speech‑API OpenAI и читает переменную `VOICE_TOOLS_OPENAI_KEY`.

Если запрошенный провайдер недоступен, Hermes автоматически переходит к следующему в этом порядке: `local` → `groq` → `openai`.

Переопределения моделей Groq и OpenAI управляются переменными окружения:

```bash
STT_GROQ_MODEL=whisper-large-v3-turbo
STT_OPENAI_MODEL=whisper-1
GROQ_BASE_URL=https://api.groq.com/openai/v1
STT_OPENAI_BASE_URL=https://api.openai.com/v1
```
## Режим голоса (CLI)

```yaml
voice:
  record_key: "ctrl+b"         # Push-to-talk key inside the CLI
  max_recording_seconds: 120    # Hard stop for long recordings
  auto_tts: false               # Enable spoken replies automatically when /voice on
  beep_enabled: true            # Play record start/stop beeps in CLI voice mode
  silence_threshold: 200        # RMS threshold for speech detection
  silence_duration: 3.0         # Seconds of silence before auto-stop
```

Используй `/voice on` в CLI, чтобы включить режим микрофона, `record_key` — для начала/остановки записи, и `/voice tts` — для переключения голосовых ответов. Смотри [Режим голоса](/user-guide/features/voice-mode) для полной настройки и поведения, зависящего от платформы.
## Streaming

Передавай токены в терминал или мессенджеры по мере их появления, вместо ожидания полного ответа.

### CLI Streaming

```yaml
display:
  streaming: true         # Stream tokens to terminal in real-time
  show_reasoning: true    # Also stream reasoning/thinking tokens (optional)
```

Когда включено, ответы отображаются токен за токеном внутри окна потоковой передачи. Вызовы инструментов всё равно захватываются без вывода. Если провайдер не поддерживает стриминг, происходит автоматический откат к обычному отображению.

### Gateway Streaming (Telegram, Discord, Slack)

```yaml
streaming:
  enabled: true           # Enable progressive message editing
  transport: edit         # "edit" (progressive message editing) or "off"
  edit_interval: 0.3      # Seconds between message edits
  buffer_threshold: 40    # Characters before forcing an edit flush
  cursor: " ▉"            # Cursor shown during streaming
  fresh_final_after_seconds: 60   # Send fresh final (Telegram) when preview is this old; 0 = always edit in place
```

При включении бот отправляет сообщение с первым токеном, а затем постепенно редактирует его по мере поступления новых токенов. Платформы, не поддерживающие редактирование сообщений (Signal, Email, Home Assistant), автоматически определяются при первой попытке — стриминг для этой сессии отключается без спама сообщениями.

Для отдельных естественных обновлений помощника без прогрессивного редактирования токенов установи `display.interim_assistant_messages: true`.

**Обработка переполнения:** Если потоковый текст превышает ограничение длины сообщения платформы (~4096 символов), текущее сообщение завершается, и автоматически начинается новое.

**Fresh final (Telegram):** Метод Telegram `editMessageText` сохраняет оригинальную метку времени сообщения, поэтому длительный потоковый ответ будет иметь метку времени первого токена даже после завершения. Когда `fresh_final_after_seconds > 0` (по умолчанию `60`), завершённый ответ отправляется как новое сообщение (со старая версия предпросмотра по возможности удаляется), чтобы видимая метка времени Telegram отражала время завершения. Краткие предпросмотры всё ещё завершаются на месте. Установи `0`, чтобы всегда редактировать на месте.

:::note
Streaming отключён по умолчанию. Включи его в `~/.hermes/config.yaml`, чтобы попробовать UX стриминга.
:::
## Изоляция сессий группового чата

Управляй тем, сохраняет ли общий чат одну беседу на комнату или одну беседу на участника:

```yaml
group_sessions_per_user: true  # true = per-user isolation in groups/channels, false = one shared session per chat
```

- `true` — значение по умолчанию и рекомендуемая настройка. В каналах Discord, группах Telegram, каналах Slack и аналогичных общих контекстах каждый отправитель получает свою собственную **сессию**, когда платформа предоставляет идентификатор пользователя.
- `false` — возвращает старое поведение общего помещения. Это может быть полезно, если ты явно хочешь, чтобы Hermes рассматривал канал как одну совместную беседу, но также означает, что пользователи делят контекст, затраты токенов и состояние прерываний.
- Прямые сообщения не затрагиваются. Hermes по‑прежнему использует идентификатор чата/DM в качестве ключа для DMs, как обычно.
- Потоки остаются изолированными от их родительского канала в любом случае; при `true` каждый участник также получает свою собственную **сессию** внутри потока.

Подробности поведения и примеры смотри в разделе [Sessions](/user-guide/sessions) и в [руководстве по Discord](/user-guide/messaging/discord).
## Неавторизованное поведение в личных сообщениях

Контролируй, что делает Hermes, когда неизвестный пользователь отправляет личное сообщение:

```yaml
unauthorized_dm_behavior: pair

whatsapp:
  unauthorized_dm_behavior: ignore
```

- `pair` — значение по умолчанию. Hermes отклоняет запрос, но отвечает одноразовым кодом сопряжения в личных сообщениях.
- `ignore` — тихо отбрасывает неавторизованные личные сообщения.
- Разделы платформ переопределяют глобальное значение по умолчанию, так что можно оставить сопряжение включённым в целом, а для отдельной платформы сделать его тихим.
## Быстрые команды

Определяй пользовательские команды, которые либо выполняют shell‑команды без обращения к LLM, либо делают alias одной slash‑команды к другой. `exec`‑быстрые команды не тратят токены и полезны из мессенджеров (Telegram, Discord и т.д.) для быстрых проверок сервера или утилитных скриптов.

```yaml
quick_commands:
  status:
    type: exec
    command: systemctl status hermes-agent
  disk:
    type: exec
    command: df -h /
  update:
    type: exec
    command: cd ~/.hermes/hermes-agent && git pull && pip install -e .
  gpu:
    type: exec
    command: nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total --format=csv,noheader
  restart:
    type: alias
    target: /gateway restart
```

Использование: вводи `/status`, `/disk`, `/update`, `/gpu` или `/restart` в CLI или в любом мессенджере. Команды `exec` выполняются локально на хосте и сразу возвращают вывод — без вызова LLM, без расхода токенов. Команды `alias` переписывают запрос к настроенной цели slash‑команды.

- **30‑секундный тайм‑аут** — длительные команды завершаются с сообщением об ошибке
- **Приоритет** — быстрые команды проверяются раньше команд skill, поэтому ты можешь переопределять имена skill
- **Автодополнение** — быстрые команды разрешаются во время диспетчеризации и не отображаются в встроенных таблицах автодополнения slash‑команд
- **Тип** — поддерживаемые типы: `exec` и `alias`; остальные типы вызывают ошибку
- **Работают везде** — CLI, Telegram, Discord, Slack, WhatsApp, Signal, Email, Home Assistant

Подсказки, состоящие только из строки, не являются действительными быстрыми командами. Для переиспользуемых рабочих процессов подсказок создай skill или alias к существующей slash‑команде.
## Человеческая задержка

Имитация темпа ответов, похожего на человеческий, в платформах обмена сообщениями:

```yaml
human_delay:
  mode: "off"                  # off | natural | custom
  min_ms: 800                  # Minimum delay (custom mode)
  max_ms: 2500                 # Maximum delay (custom mode)
```
## Выполнение кода

Настройте инструмент `execute_code`:

```yaml
code_execution:
  mode: project                # project (default) | strict
  timeout: 300                 # Max execution time in seconds
  max_tool_calls: 50           # Max tool calls within code execution
```

**`mode`** управляет рабочим каталогом и интерпретатором Python для скриптов:

- **`project`** (по умолчанию) — скрипты запускаются в рабочем каталоге сессии с активным virtualenv/conda‑окружением Python. Зависимости проекта (`pandas`, `torch`, пакеты проекта) и относительные пути (`.env`, `./data.csv`) разрешаются естественно, так же как это видит `terminal()`.
- **`strict`** — скрипты запускаются во временном каталоге‑staging с `sys.executable` (собственный Python Hermes). Обеспечивает максимальную воспроизводимость, но зависимости проекта и относительные пути не будут разрешаться.

Очистка окружения (удаляет `*_API_KEY`, `*_TOKEN`, `*_SECRET`, `*_PASSWORD`, `*_CREDENTIAL`, `*_PASSWD`, `*_AUTH`) и белый список инструментов применяются одинаково в обоих режимах — переключение режима не меняет уровень безопасности.
## Бэкенды веб‑поиска

Инструменты `web_search` и `web_extract` поддерживают пять провайдеров бэкенда. Настрой бэкенд в `config.yaml` или через `hermes tools`:

```yaml
web:
  backend: firecrawl    # firecrawl | searxng | parallel | tavily | exa

  # Or use per-capability keys to mix providers (e.g. free search + paid extract):
  search_backend: "searxng"
  extract_backend: "firecrawl"
```

| Backend | Env Var | Search | Extract |
|---------|---------|--------|---------|
| **Firecrawl** (по умолчанию) | `FIRECRAWL_API_KEY` | ✔ | ✔ |
| **SearXNG** | `SEARXNG_URL` | ✔ | — |
| **Parallel** | `PARALLEL_API_KEY` | ✔ | ✔ |
| **Tavily** | `TAVILY_API_KEY` | ✔ | ✔ |
| **Exa** | `EXA_API_KEY` | ✔ | ✔ |

**Выбор бэкенда:** Если `web.backend` не задан, бэкенд определяется автоматически из доступных API‑ключей. Если установлен только `SEARXNG_URL`, используется SearXNG. Если установлен только `EXA_API_KEY`, используется Exa. Если установлен только `TAVILY_API_KEY`, используется Tavily. Если установлен только `PARALLEL_API_KEY`, используется Parallel. Во всех остальных случаях по умолчанию используется Firecrawl.

**SearXNG** — бесплатный, самохостинг‑ориентированный, уважающий конфиденциальность метапоисковый движок, который опрашивает более 70 поисковых систем. Ключ API не требуется — просто укажи `SEARXNG_URL` на свой экземпляр (например, `http://localhost:8080`). SearXNG поддерживает только поиск; `web_extract` требует отдельного провайдера извлечения (укажи `web.extract_backend`). См. [Руководство по настройке Web Search](/user-guide/features/web-search) для инструкций по Docker‑настройке.

**Самохостинг Firecrawl:** Укажи `FIRECRAWL_API_URL`, чтобы направить запросы на свой экземпляр. Когда задаётся пользовательский URL, ключ API становится необязательным (установи `USE_DB_AUTHENTICATION=***` на сервере, чтобы отключить аутентификацию).

**Режимы поиска Parallel:** Установи `PARALLEL_SEARCH_MODE`, чтобы управлять поведением поиска — `fast`, `one-shot` или `agentic` (по умолчанию: `agentic`).

**Exa:** Укажи `EXA_API_KEY` в `~/.hermes/.env`. Поддерживает фильтрацию по `category` (`company`, `research paper`, `news`, `people`, `personal site`, `pdf`) и фильтры домена/даты.
## Браузер

Настройка поведения автоматизации браузера:

```yaml
browser:
  inactivity_timeout: 120        # Seconds before auto-closing idle sessions
  command_timeout: 30             # Timeout in seconds for browser commands (screenshot, navigate, etc.)
  record_sessions: false         # Auto-record browser sessions as WebM videos to ~/.hermes/browser_recordings/
  # Optional CDP override — when set, Hermes attaches directly to your own
  # Chromium-family browser (via /browser connect) rather than starting a headless browser.
  cdp_url: ""
  # Dialog supervisor — controls how native JS dialogs (alert / confirm / prompt)
  # are handled when a CDP backend is attached (Browserbase, local Chromium-family
  # browser via /browser connect). Ignored on Camofox and default local agent-browser mode.
  dialog_policy: must_respond    # must_respond | auto_dismiss | auto_accept
  dialog_timeout_s: 300          # Safety auto-dismiss under must_respond (seconds)
  camofox:
    managed_persistence: false   # When true, Camofox sessions persist cookies/logins across restarts
    user_id: ""                  # Optional externally managed Camofox userId
    session_key: ""              # Optional session key sent when Hermes creates a tab
    adopt_existing_tab: false    # Reuse an existing tab for this identity before creating one
```

**Политики диалогов:**

- `must_respond` (по умолчанию) — перехватывает диалог, отображает его в `browser_snapshot.pending_dialogs` и ждёт, пока агент вызовет `browser_dialog(action=…)`. После `dialog_timeout_s` секунд без ответа диалог автоматически отклоняется, чтобы предотвратить бесконечную блокировку JS‑потока страницы.
- `auto_dismiss` — перехватывает, отклоняет сразу. Агент всё равно видит запись диалога в `browser_snapshot.recent_dialogs` с `closed_by="auto_policy"` после этого.
- `auto_accept` — перехватывает, принимает сразу. Полезно для страниц с навязчивыми запросами `beforeunload`.

См. [страницу функции браузера](./features/browser.md#browser_dialog) для полного описания рабочего процесса диалогов.

Набор инструментов браузера поддерживает несколько провайдеров. Подробнее о Browserbase, Browser Use и локальной настройке CDP семейства Chromium см. на [странице функции Browser](/user-guide/features/browser).
## Часовой пояс

Переопределить локальный часовой пояс сервера, указав строку IANA. Влияет на метки времени в журналах, расписание cron и вставку времени в системный запрос.

```yaml
timezone: "America/New_York"   # IANA timezone (default: "" = server-local time)
```

Поддерживаемые значения: любой идентификатор часового пояса IANA (например, `America/New_York`, `Europe/London`, `Asia/Kolkata`, `UTC`). Оставьте пустым или не указывайте значение, чтобы использовать локальное время сервера.
## Discord

Настройка поведения, специфичного для Discord, в шлюзе сообщений:

```yaml
discord:
  require_mention: true          # Require @mention to respond in server channels
  free_response_channels: ""     # Comma-separated channel IDs where bot responds without @mention
  auto_thread: true              # Auto-create threads on @mention in channels
```

- `require_mention` — когда `true` (по умолчанию), бот отвечает в каналах сервера только при упоминании `@BotName`. В личных сообщениях (DM) упоминание не требуется.
- `free_response_channels` — список идентификаторов каналов, разделённых запятыми, в которых бот отвечает на каждое сообщение без необходимости упоминания.
- `auto_thread` — когда `true` (по умолчанию), упоминания в каналах автоматически создают ветку (thread) для разговора, поддерживая чистоту каналов (аналогично ветвлению в Slack).
## Безопасность

Сканирование безопасности перед выполнением и маскирование секретов:

```yaml
security:
  redact_secrets: false          # Redact API key patterns in tool output and logs (off by default)
  tirith_enabled: true           # Enable Tirith security scanning for terminal commands
  tirith_path: "tirith"          # Path to tirith binary (default: "tirith" in $PATH)
  tirith_timeout: 5              # Seconds to wait for tirith scan before timing out
  tirith_fail_open: true         # Allow command execution if tirith is unavailable
  website_blocklist:             # See Website Blocklist section below
    enabled: false
    domains: []
    shared_files: []
```

- `redact_secrets` — когда `true`, автоматически обнаруживает и маскирует шаблоны, похожие на API‑ключи, токены и пароли в выводе инструмента до того, как они попадут в контекст разговора и в журналы. **Выключено по умолчанию** — включи, если часто работаешь с реальными учётными данными в выводе инструмента и хочешь иметь защитный слой. Установи `true` явно, чтобы включить.
- `tirith_enabled` — когда `true`, команды терминала сканируются [Tirith](https://github.com/sheeki03/tirith) перед выполнением для обнаружения потенциально опасных операций.
- `tirith_path` — путь к бинарному файлу `tirith`. Укажи, если `tirith` установлен в нестандартном месте.
- `tirith_timeout` — максимальное количество секунд ожидания сканирования `tirith`. Команды продолжаются, если сканирование превышает время ожидания.
- `tirith_fail_open` — когда `true` (по умолчанию), команды разрешаются к выполнению, если `tirith` недоступен или произошёл сбой. Установи `false`, чтобы блокировать команды, когда `tirith` не может их проверить.
## Блокировка доменов

Блокировать доступ к определённым доменам для веб‑ и браузерных инструментов агента:

```yaml
security:
  website_blocklist:
    enabled: false               # Enable URL blocking (default: false)
    domains:                     # List of blocked domain patterns
      - "*.internal.company.com"
      - "admin.example.com"
      - "*.local"
    shared_files:                # Load additional rules from external files
      - "/etc/hermes/blocked-sites.txt"
```

Когда включено, любой URL, соответствующий шаблону заблокированного домена, отклоняется до выполнения инструментов `web_search`, `web_extract`, `browser_navigate` и любого другого инструмента, который обращается к URL.

Поддерживаемые правила доменов:
- Точные домены: `admin.example.com`
- Поддомены с подстановкой: `*.internal.company.com` (блокирует все поддомены)
- Подстановки уровня домена: `*.local`

В общих файлах содержится по одному правилу домена на строку (пустые строки и комментарии, начинающиеся с `#`, игнорируются). Отсутствие файлов или невозможность их чтения приводит к записи предупреждения, но не отключает остальные веб‑инструменты.

Политика кэшируется на 30 секунд, поэтому изменения конфигурации вступают в силу быстро без перезапуска.
## Умные одобрения

Контролируй, как Hermes обрабатывает потенциально опасные команды:

```yaml
approvals:
  mode: manual   # manual | smart | off
```

| Режим | Поведение |
|------|-----------|
| `manual` (по умолчанию) | Запрашивает подтверждение у пользователя перед выполнением любой помеченной команды. В CLI отображает интерактивный диалог одобрения. В мессенджерах ставит запрос в очередь ожидания одобрения. |
| `smart` | Использует вспомогательный LLM для оценки, действительно ли помеченная команда опасна. Команды с низким риском автоматически одобряются с сохранением на уровне сессии. По‑настоящему рискованные команды передаются пользователю. |
| `off` | Пропускает все проверки одобрения. Эквивалентно `HERMES_YOLO_MODE=true`. **Используй с осторожностью.** |

Режим `smart` особенно полезен для снижения усталости от одобрений — он позволяет агенту работать более автономно над безопасными операциями, одновременно перехватывая действительно разрушительные команды.

:::warning
Установка `approvals.mode: off` отключает все проверки безопасности для команд терминала. Используй это только в доверенных, изолированных средах.
:::
## Контрольные точки

Автоматические снимки файловой системы перед деструктивными файловыми операциями. См. [Контрольные точки и откат](/user-guide/checkpoints-and-rollback) для получения подробной информации.

```yaml
checkpoints:
  enabled: false                 # Enable automatic checkpoints (also: hermes chat --checkpoints). Default: false (opt-in).
  max_snapshots: 20              # Max checkpoints to keep per directory (default: 20)
```
## Делегирование

Настрой поведение субагентов для инструмента делегирования:

```yaml
delegation:
  # model: "google/gemini-3-flash-preview"  # Override model (empty = inherit parent)
  # provider: "openrouter"                  # Override provider (empty = inherit parent)
  # base_url: "http://localhost:1234/v1"    # Direct OpenAI-compatible endpoint (takes precedence over provider)
  # api_key: "local-key"                    # API key for base_url (falls back to OPENAI_API_KEY)
  # api_mode: ""                            # Wire protocol for base_url: "chat_completions", "codex_responses", or "anthropic_messages". Empty = auto-detect from URL (e.g. /anthropic suffix → anthropic_messages). Set explicitly for non-standard endpoints the heuristic can't detect.
  max_concurrent_children: 3                # Parallel children per batch (floor 1, no ceiling). Also via DELEGATION_MAX_CONCURRENT_CHILDREN env var.
  max_spawn_depth: 1                        # Delegation tree depth cap (1-3, clamped). 1 = flat (default): parent spawns leaves that cannot delegate. 2 = orchestrator children can spawn leaf grandchildren. 3 = three levels.
  orchestrator_enabled: true                # Global kill switch. When false, role="orchestrator" is ignored and every child is forced to leaf regardless of max_spawn_depth.
```

**Переопределение provider:model субагента:** По умолчанию субагенты наследуют провайдера и модель родительского агента. Установи `delegation.provider` и `delegation.model`, чтобы направить субагентов к другой паре провайдер : модель — например, использовать дешёвую / быструю модель для узконаправленных подзадач, пока основной агент работает с дорогой моделью рассуждения.

**Прямое переопределение конечной точки:** Если нужен явный путь к пользовательской конечной точке, задай `delegation.base_url`, `delegation.api_key` и `delegation.model`. Это отправит субагентов напрямую к указанной совместимой с OpenAI конечной точке и имеет приоритет над `delegation.provider`. Если `delegation.api_key` опущен, Hermes переходит к `OPENAI_API_KEY` только.

**Протокол передачи (`api_mode`):** Hermes автоматически определяет протокол передачи из `delegation.base_url` (например, пути, заканчивающиеся на `/anthropic` → `anthropic_messages`; хосты Codex / native Anthropic / Kimi-coding сохраняют своё текущее определение). Для конечных точек, которые эвристика не может классифицировать — например, Azure AI Foundry, MiniMax, Zhipu GLM или прокси LiteLLM, фасадирующие Anthropic‑подобный бекенд — установи `delegation.api_mode` явно в одно из `chat_completions`, `codex_responses` или `anthropic_messages`. Оставь пустым (по умолчанию), чтобы сохранить автоопределение.

Провайдер делегирования использует тот же механизм разрешения учётных данных, что и запуск CLI/gateway. Поддерживаются все настроенные провайдеры: `openrouter`, `nous`, `copilot`, `zai`, `kimi-coding`, `minimax`, `minimax-cn`. Когда провайдер задан, система автоматически определяет правильный базовый URL, API‑ключ и режим API — ручная проводка учётных данных не требуется.

**Приоритет:** `delegation.base_url` в конфиге → `delegation.provider` в конфиге → провайдер родителя (унаследовано). `delegation.model` в конфиге → модель родителя (унаследовано). Установка только `model` без `provider` меняет лишь название модели, сохраняя учётные данные родителя (полезно для переключения моделей внутри одного провайдера, например OpenRouter).

**Ширина и глубина:** `max_concurrent_children` ограничивает количество субагентов, работающих параллельно в одной партии (по умолчанию `3`, минимум 1, без верхнего предела). Можно также задать через переменную окружения `DELEGATION_MAX_CONCURRENT_CHILDREN`. Когда модель отправляет массив `tasks` длиннее лимита, `delegate_task` возвращает ошибку инструмента, объясняющую ограничение, вместо тихого усечения. `max_spawn_depth` контролирует глубину дерева делегирования (ограничено 1‑3). При значении по умолчанию `1` делегирование плоское: дочерние агенты не могут порождать внуков, а передача `role="orchestrator"` тихо понижается до `leaf`. Установи `2`, чтобы дочерние оркестраторы могли порождать листовые внуки; `3` — для трёхуровневых деревьев. Агент включает оркестрацию per‑call через `role="orchestrator"`; `orchestrator_enabled: false` принудительно делает каждый дочерний агент листовым независимо от роли. Стоимость масштабируется мультипликативно — при `max_spawn_depth: 3` и `max_concurrent_children: 3` дерево может достигать 3×3×3 = 27 одновременно работающих листовых агентов. См. [Subagent Delegation → Depth Limit and Nested Orchestration](features/delegation.md#depth-limit-and-nested-orchestration) для примеров использования.
## Уточнение

Настройте поведение подсказки уточнения:

```yaml
clarify:
  timeout: 120                 # Seconds to wait for user clarification response
```
## Файлы контекста (SOUL.md, AGENTS.md)

Hermes использует два разных уровня контекста:

| Файл | Назначение | Область |
|------|------------|---------|
| `SOUL.md` | **Основная идентичность агента** — определяет, кто такой агент (слот #1 в системном запросе) | `~/.hermes/SOUL.md` или `$HERMES_HOME/SOUL.md` |
| `.hermes.md` / `HERMES.md` | Инструкции, специфичные для проекта (наивысший приоритет) | Переход к корню репозитория Git |
| `AGENTS.md` | Инструкции, специфичные для проекта, соглашения о кодировании | Рекурсивный обход каталогов |
| `CLAUDE.md` | Файлы контекста Claude Code (также обнаруживаются) | Только текущий рабочий каталог |
| `.cursorrules` | Правила Cursor IDE (также обнаруживаются) | Только текущий рабочий каталог |
| `.cursor/rules/*.mdc` | Файлы правил Cursor (также обнаруживаются) | Только текущий рабочий каталог |

- **SOUL.md** — это основная идентичность агента. Он занимает слот #1 в системном запросе, полностью заменяя встроенную идентичность по умолчанию. Отредактируй его, чтобы полностью настроить, кто такой агент.
- Если SOUL.md отсутствует, пустой или не может быть загружен, Hermes переходит к встроенной идентичности по умолчанию.
- **Файлы контекста проекта используют систему приоритетов** — загружается только один тип (первое совпадение выигрывает): `.hermes.md` → `AGENTS.md` → `CLAUDE.md` → `.cursorrules`. SOUL.md всегда загружается независимо.
- **AGENTS.md** — иерархичен: если в подкаталогах также есть AGENTS.md, они объединяются.
- Hermes автоматически создаёт файл `SOUL.md` по умолчанию, если он ещё не существует.
- Все загруженные файлы контекста ограничены 20 000 символами с умным усечением.

См. также:
- [Personality & SOUL.md](/user-guide/features/personality)
- [Context Files](/user-guide/features/context-files)
## Рабочий каталог

| Контекст | По умолчанию |
|----------|--------------|
| **CLI (`hermes`)** | Текущий каталог, из которого запускается команда |
| **Messaging gateway** | Домашний каталог `~` (можно переопределить с помощью `MESSAGING_CWD`) |
| **Docker / Singularity / Modal / SSH** | Домашний каталог пользователя внутри контейнера или удалённой машины |

Переопределить рабочий каталог:
```bash
# In ~/.hermes/.env or ~/.hermes/config.yaml:
MESSAGING_CWD=/home/myuser/projects    # Gateway sessions
TERMINAL_CWD=/workspace                # All terminal sessions
```