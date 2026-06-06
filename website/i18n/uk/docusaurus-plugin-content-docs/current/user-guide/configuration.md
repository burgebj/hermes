---
sidebar_position: 2
title: "Конфігурація"
description: "Налаштуй Hermes Agent — config.yaml, провайдери, моделі, API‑ключі та інше"
---

# Конфігурація

Усі налаштування зберігаються в каталозі `~/.hermes/` для зручного доступу.

:::tip Найпростіший шлях до робочого `config.yaml`
Запусти `hermes setup --portal` — один OAuth дає тобі провайдера моделей і всі чотири інструменти шлюзу інструментів без ручного редагування YAML. Підписники Portal також отримують 10 % знижки на провайдерів, що оплачуються токенами. Дивись [Nous Portal](/integrations/nous-portal).
:::

---
## Структура каталогів

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
## Керування конфігурацією

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
Команда `hermes config set` автоматично перенаправляє значення у правильний файл — API‑ключі зберігаються у `.env`, все інше — у `config.yaml`.
:::
## Пріоритет конфігурації

Налаштування визначаються у цьому порядку (спочатку найвищий пріоритет):

1. **CLI‑аргументи** — напр., `hermes chat --model anthropic/claude-sonnet-4` (перевизначення під час виклику)
2. **`~/.hermes/config.yaml`** — основний файл конфігурації для всіх не‑секретних налаштувань
3. **`~/.hermes/.env`** — запасний (варіант) для змінних середовища; **обов’язковий** для секретів (API‑ключі, токени, паролі)
4. **Вбудовані типові значення** — жорстко закодовані безпечні значення, коли нічого іншого не задано

:::info Правило великого пальця
Секрети (API‑ключі, токени ботів, паролі) розміщуються у `.env`. Усе інше (модель, бекенд терміналу, налаштування стиснення, обмеження пам’яті, набори інструментів) — у `config.yaml`. Якщо обидва задані, `config.yaml` переважає для не‑секретних налаштувань.
:::
## Підстановка змінних середовища

Ти можеш посилатися на змінні середовища у `config.yaml`, використовуючи синтаксис `${VAR_NAME}`:

```yaml
auxiliary:
  vision:
    api_key: ${GOOGLE_API_KEY}
    base_url: ${CUSTOM_VISION_URL}

delegation:
  api_key: ${DELEGATION_KEY}
```

Кілька посилань у одному значенні працюють: `url: "${HOST}:${PORT}"`. Якщо посилана змінна не встановлена, заповнювач залишиться без змін (`${UNDEFINED_VAR}` залишиться як є). Підтримується лише синтаксис `${VAR}` — голий `$VAR` не розширюється.

Для налаштування AI‑провайдерів (OpenRouter, Anthropic, Copilot, власні кінцеві точки, самохостовані LLM, запасні моделі тощо) дивись [AI Providers](/integrations/providers).

### Тайм‑аути провайдерів

Ти можеш встановити `providers.<id>.request_timeout_seconds` для глобального тайм‑ауту запиту провайдера, а також `providers.<id>.models.<model>.timeout_seconds` для перевизначення тайм‑ауту конкретної моделі. Це застосовується до основного turn‑клієнта на кожному транспорті (OpenAI‑wire, native Anthropic, Anthropic‑compatible), ланцюжка запасних варіантів, перебудов після ротації облікових даних і (для OpenAI‑wire) параметра `timeout` у запиті — тому налаштоване значення переважає застарілу змінну середовища `HERMES_API_TIMEOUT`.

Ти також можеш встановити `providers.<id>.stale_timeout_seconds` для детектора «застарілих» не‑стрімових викликів, а також `providers.<id>.models.<model>.stale_timeout_seconds` для перевизначення тайм‑ауту конкретної моделі. Це переважає застарілу змінну середовища `HERMES_API_CALL_STALE_TIMEOUT`.

Якщо залишити ці параметри незаданими, будуть використані застарілі значення за замовчуванням (`HERMES_API_TIMEOUT=1800 s`, `HERMES_API_CALL_STALE_TIMEOUT=300 s`, native Anthropic 900 s). Наразі не налаштовано для AWS Bedrock (обидва шляхи `bedrock_converse` та AnthropicBedrock SDK використовують boto3 зі своїми налаштуваннями тайм‑ауту). Дивись закоментований приклад у [`cli-config.yaml.example`](https://github.com/NousResearch/hermes-agent/blob/main/cli-config.yaml.example).
## Конфігурація термінального бекенду

Hermes підтримує шість термінальних бекендів. Кожен визначає, де саме виконуються команди оболонки агента — на твоїй локальній машині, у Docker‑контейнері, на віддаленому сервері через SSH, у хмарній пісочниці Modal (напрямо або через керований шлюз Nous), у робочому просторі Daytona або у контейнері Singularity/Apptainer.

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

Для хмарних пісочниць, таких як Modal і Daytona, `container_persistent: true` означає, що Hermes спробує зберегти стан файлової системи під час відтворення пісочниці. Це не гарантує, що та сама жива пісочниця, простір PID або фонові процеси залишаться активними пізніше.
### Огляд бекенду

| Backend | Де виконуються команди | Ізоляція | Найкраще для |
|---------|------------------------|----------|--------------|
| **local** | Твоя машина безпосередньо | Немає | Розробка, особисте використання |
| **docker** | Окремий постійний Docker‑контейнер (спільний між сесіями, `/new`, підагентами) | Повна (namespaces, cap‑drop) | Безпечна пісочниця, CI/CD |
| **ssh** | Віддалений сервер через SSH | Мережева межа | Віддалена розробка, потужне обладнання |
| **modal** | Хмарна пісочниця Modal | Повна (хмарна VM) | Ефемерні хмарні обчислення, evals |
| **daytona** | Робочий простір Daytona | Повна (хмарний контейнер) | Керовані хмарні середовища розробки |
| **singularity** | Контейнер Singularity/Apptainer | Namespaces (--containall) | Кластери HPC, спільні вузли |
### Локальний бекенд

За замовчуванням. Команди виконуються безпосередньо на твоєму комп’ютері без ізоляції. Не потребує спеціального налаштування.

```yaml
terminal:
  backend: local
```

:::warning
Агент має такий самий доступ до файлової системи, як і твій користувач. Використовуй `hermes tools`, щоб вимкнути інструменти, які не потрібні, або перейди на Docker для пісочниці.
:::
### Docker Backend

Запускає команди всередині Docker‑контейнера з підвищеною безпекою (усі можливості скинуті, без підвищення привілеїв, обмеження PID).

**Один довгоживучий контейнер, спільний для процесів Hermes.** Hermes запускає ОДИН довгоживучий контейнер під час першого використання і маршрутизує кожен виклик терміналу, файлу та `execute_code` через `docker exec` у той самий контейнер — між сесіями, `/new`, `/reset` та підагентами `delegate_task`. Зміни робочого каталогу, встановлені пакети, файли в `/workspace` та **фонові процеси** переносяться від одного виклику інструмента до іншого і від одного процесу Hermes до іншого. Коли ти закриваєш TUI‑сесію, виконуєш `/quit` або запускаєш новий виклик `hermes`, контейнер продовжує працювати, а наступний процес Hermes повторно використовує його через пошук за міткою. Дивись **Container lifecycle** нижче для точних правил зупинки.

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

**`docker_env`** проти **`docker_forward_env`**: перший інжектує буквальні пари `KEY=value`, які ти вказуєш у конфігурації (значення живуть у твоєму `config.yaml` або передаються як JSON‑словник через `TERMINAL_DOCKER_ENV='{"DEBUG":"1"}'`). Другий передає значення з твоєї оболонки або `~/.hermes/.env`, тому фактичний секрет ніколи не з’являється у файлі конфігурації. Використовуй `docker_forward_env` для токенів і `docker_env` для статичних параметрів, потрібних контейнеру.

**`terminal.docker_extra_args`** (також можна перевизначити через `TERMINAL_DOCKER_EXTRA_ARGS='["--gpus=all"]'`) дозволяє передавати довільні прапорці `docker run`, які Hermes не експонує як ключі першого класу — `--gpus`, `--network`, `--add-host`, альтернативні `--security-opt` тощо. Кожен елемент має бути рядком; список додається в кінець зібраного виклику `docker run`, тому може переоприділити типові значення Hermes за потреби. Використовуй помірно — прапорці, що конфліктують із жорстким режимом пісочниці (скидання можливостей, `--user`, монтування робочого простору), без повідомлення послаблюватимуть ізоляцію.

**Вимоги:** Docker Desktop або Docker Engine, встановлені та запущені. Hermes сканує `$PATH` та типові місця встановлення macOS (`/usr/local/bin/docker`, `/opt/homebrew/bin/docker`, пакет Docker Desktop). Підтримується Podman «з коробки»: встанови `HERMES_DOCKER_BINARY=podman` (або повний шлях), щоб примусово використовувати його, коли встановлені обидва.

#### Container lifecycle

Кожен контейнер, яким керує Hermes, має три мітки, щоб наступні процеси (і збирач‑сирот) могли його ідентифікувати:

- `hermes-agent=1` — позначає, що контейнер керується Hermes
- `hermes-task-id=<sanitized task_id>` — ключ для повторного використання за завданням
- `hermes-profile=<sanitized profile name>` — обмежує повторне використання та збірку до активного профілю Hermes

При запуску Hermes виконує `docker ps --filter label=hermes-task-id=<id> --filter label=hermes-profile=<profile>` і **приєднується до існуючого контейнера**, якщо такий знайдено. Якщо контейнер `exited` (наприклад, після перезапуску Docker‑демона), його запускає `docker start` і повторно використовує — стан файлової системи та встановлені пакети зберігаються, а фонові процеси всередині контейнера — ні.

Коли процес Hermes завершується — `/quit`, закриття TUI‑сесії, вимкнення шлюзу, навіть SIGKILL — шлях очищення є **no‑op для контейнера у режимі за замовчуванням**. Контейнер продовжує працювати. Наступний процес Hermes під’єднується до нього за мілісекунди через пошук мітки. Це саме та поведінка, яку вимагає контракт «один довгоживучий контейнер, спільний між сесіями»: лише так фонові процеси (npm‑watchers, dev‑сервери, довготривалі pytest) виживають між сесіями.

**Контейнер знищується (зупиняється та `docker rm -f`), лише у таких випадках:**

| Trigger | When it fires |
|---|---|
| `docker_persist_across_processes: false` | Явна ізоляція per‑process. Кожен `cleanup()` виконує `stop` + `rm -f`. Відповідає поведінці до issue‑#20561. |
| Idle reaper (`lifetime_seconds`, default 300 s) | Тільки коли `persist_across_processes=false`. У режимі persist‑mode збирач нічого не робить; контейнер виживає під час бездіяльності. |
| Orphan reaper at next startup | Очищає **Exited** контейнери з міткою Hermes, старші `2 × lifetime_seconds` (за замовчуванням 600 s = 10 хв), у межах поточного профілю. **Running** контейнери ніколи не торкаються — безпека між процесами. Встанови `docker_orphan_reaper: false`, щоб вимкнути. |
| Direct user action | `docker rm -f`, `docker system prune`, перезапуск Docker Desktop. Ми не ставимо `--restart=always`, тому після перезавантаження хоста контейнер залишиться `Exited` (його CoW‑шар виживає і буде повторно використаний при наступному запуску, але фонова робота зникає). |

Особливі випадки, які варто знати:

- **OOM‑kill процесу PID 1 всередині контейнера** переводить його у стан `Exited`. При наступному використанні його знову запускає `docker start`; файловий стан зберігається, фонова робота — ні.
- **Перемикання профілів** ізолює контейнери один від одного — контейнер з міткою `hermes-profile=work` невидимий для процесу Hermes, запущеного під `hermes-profile=research`. Збирач‑сирот також працює в межах профілю, тому контейнери між профілями не будуть випадково знищені, але й не будуть автоматично очищені, доки ти знову не запустиш Hermes у їхньому оригінальному профілі.

Паралельні підагенти, створені через `delegate_task(tasks=[...])`, ділять цей один контейнер — одночасні `cd`, зміни середовища та записи у той самий шлях можуть конфліктувати. Якщо підагент потребує ізольованої пісочниці, він має зареєструвати переозначення образу за завданням через `register_task_env_overrides()`, що роблять RL‑ та benchmark‑середовища (TerminalBench2, HermesSweEnv тощо) автоматично для їхніх Docker‑образів.

**Жорстке посилення безпеки:**
- `--cap-drop ALL` з поверненням лише `DAC_OVERRIDE`, `CHOWN`, `FOWNER`
- `--security-opt no-new-privileges`
- `--pids-limit 256`
- Обмежений за розміром tmpfs для `/tmp` (512 МБ), `/var/tmp` (256 МБ), `/run` (64 МБ)

**Перенаправлення облікових даних:** змінні середовища, зазначені в `docker_forward_env`, спочатку беруться з твоєї оболонки, потім з `~/.hermes/.env`. Навички також можуть оголошувати `required_environment_variables`, які автоматично зливаються.

#### Environment variable overrides

Кожен ключ під `terminal:` має перевизначення змінної середовища у вигляді `TERMINAL_<KEY_UPPERCASE>`. Найкорисніші для Docker‑бекенду:

| Env var | Maps to | Notes |
|---|---|---|
| `TERMINAL_DOCKER_IMAGE` | `docker_image` | Базовий образ |
| `TERMINAL_DOCKER_FORWARD_ENV` | `docker_forward_env` | JSON‑масив: `'["GITHUB_TOKEN","OPENAI_API_KEY"]'` |
| `TERMINAL_DOCKER_ENV` | `docker_env` | JSON‑словник: `'{"DEBUG":"1"}'` |
| `TERMINAL_DOCKER_VOLUMES` | `docker_volumes` | JSON‑масив рядків `"host:container[:ro]"` |
| `TERMINAL_DOCKER_EXTRA_ARGS` | `docker_extra_args` | JSON‑масив |
| `TERMINAL_DOCKER_MOUNT_CWD_TO_WORKSPACE` | `docker_mount_cwd_to_workspace` | `true` / `false` |
| `TERMINAL_DOCKER_RUN_AS_HOST_USER` | `docker_run_as_host_user` | `true` / `false` |
| `TERMINAL_DOCKER_PERSIST_ACROSS_PROCESSES` | `docker_persist_across_processes` | `true` / `false` — за замовчуванням `true` |
| `TERMINAL_DOCKER_ORPHAN_REAPER` | `docker_orphan_reaper` | `true` / `false` — за замовчуванням `true` |
| `TERMINAL_CONTAINER_CPU` | `container_cpu` | Кількість ядер CPU |
| `TERMINAL_CONTAINER_MEMORY` | `container_memory` | МБ |
| `TERMINAL_CONTAINER_DISK` | `container_disk` | МБ |
| `TERMINAL_CONTAINER_PERSISTENT` | `container_persistent` | `true` / `false` — керує монтуванням робочих директорій, окремо від `docker_persist_across_processes` |
| `TERMINAL_LIFETIME_SECONDS` | `lifetime_seconds` | Вік бездіяльності для збирача |
| `TERMINAL_TIMEOUT` | `timeout` | Тайм‑аут на команду |
| `HERMES_DOCKER_BINARY` | _none_ | Примусово вказати шлях до конкретного docker/podman‑бінарника |
### SSH Backend

Виконує команди на віддаленому сервері через SSH. Використовує ControlMaster для повторного використання з’єднання (5‑хвилинний keepalive під час бездіяльності). Постійна оболонка увімкнена за замовчуванням — стан (cwd, змінні середовища) зберігається між командами.

```yaml
terminal:
  backend: ssh
  persistent_shell: true           # Keep a long-lived bash session (default: true)
```

**Обов’язкові змінні середовища:**

```bash
TERMINAL_SSH_HOST=my-server.example.com
TERMINAL_SSH_USER=ubuntu
```

**Необов’язкові:**

| Variable | Default | Description |
|----------|---------|-------------|
| `TERMINAL_SSH_PORT` | `22` | SSH‑порт |
| `TERMINAL_SSH_KEY` | (system default) | Шлях до приватного ключа SSH |
| `TERMINAL_SSH_PERSISTENT` | `true` | Увімкнути постійну оболонку |

**Як це працює:** Підключається під час ініціалізації з `BatchMode=yes` та `StrictHostKeyChecking=accept-new`. Постійна оболонка тримає один процес `bash -l` живим на віддаленому хості, спілкуючись через тимчасові файли. Команди, які потребують `stdin_data` або `sudo`, автоматично переходять у режим одноразового виконання.
### Modal Backend

Запускає команди в хмарному пісочному середовищі [Modal](https://modal.com). Кожне завдання отримує ізольовану ВМ із налаштовуваними CPU, пам’яттю та диском. Файлова система може бути знята/відновлена між сесіями.

```yaml
terminal:
  backend: modal
  container_cpu: 1                 # CPU cores
  container_memory: 5120           # MB (5GB)
  container_disk: 51200            # MB (50GB)
  container_persistent: true       # Snapshot/restore filesystem
```

**Required:** Either `MODON_TOKEN_ID` + `MODON_TOKEN_SECRET` environment variables, or a `~/.modal.toml` config file.

**Persistence:** When enabled, the sandbox filesystem is snapshotted on cleanup and restored on next session. Snapshots are tracked in `~/.hermes/modal_snapshots.json`. This preserves filesystem state, not live processes, PID space, or background jobs.

**Credential files:** Automatically mounted from `~/.hermes/` (OAuth tokens, etc.) and synced before each command.
### Daytona Backend

Запускає команди у керованому робочому просторі [Daytona](https://daytona.io). Підтримує зупинку/відновлення для збереження стану.

```yaml
terminal:
  backend: daytona
  container_cpu: 1                 # CPU cores
  container_memory: 5120           # MB → converted to GiB
  container_disk: 10240            # MB → converted to GiB (max 10 GiB)
  container_persistent: true       # Stop/resume instead of delete
```

**Required:** `DAYTONA_API_KEY` environment variable.

**Persistence:** При увімкненні пісочниці зупиняються (не видаляються) під час очищення та відновлюються в наступній сесії. Імена пісочниць слідують шаблону `hermes-{task_id}`.

**Disk limit:** Daytona обмежує розмір до 10 GiB. Запити, що перевищують це значення, обрізаються з попередженням.
### Singularity/Apptainer Backend

Runs commands in a [Singularity/Apptainer](https://apptainer.org) container. Designed for HPC clusters and shared machines where Docker isn't available.

```yaml
terminal:
  backend: singularity
  singularity_image: "docker://nikolaik/python-nodejs:python3.11-nodejs20"
  container_cpu: 1                 # CPU cores
  container_memory: 5120           # MB
  container_persistent: true       # Writable overlay persists across sessions
```

**Requirements:** `apptainer` або `singularity` бінарник у `$PATH`.

**Image handling:** Docker‑URL (`docker://…`) автоматично конвертуються у SIF‑файли та кешуються. Існуючі `.sif` файли використовуються без змін.

**Scratch directory:** Визначається у такому порядку: `TERMINAL_SCRATCH_DIR` → `TERMINAL_SANDBOX_DIR/singularity` → `/scratch/$USER/hermes-agent` (HPC‑конвенція) → `~/.hermes/sandboxes/singularity`.

**Isolation:** Використовує `--containall --no-home` для повної ізоляції простору імен без монтування домашньої теки хоста.
### Загальні проблеми бекенду терміналу

Якщо команди терміналу не виконуються одразу або інструмент терміналу позначений як вимкнений:

- **Local** — Ніяких особливих вимог. Найбезпечніший варіант за замовчуванням для початку роботи.
- **Docker** — Запусти `docker version`, щоб перевірити, чи працює Docker. Якщо команда не проходить, виправ Docker або виконай `hermes config set terminal.backend local`.
- **SSH** — Потрібно задати і `TERMINAL_SSH_HOST`, і `TERMINAL_SSH_USER`. Hermes записує чітку помилку, якщо будь‑яке з них відсутнє.
- **Modal** — Потрібна змінна середовища `MODAL_TOKEN_ID` або файл `~/.modal.toml`. Запусти `hermes doctor` для перевірки.
- **Daytona** — Потрібен `DAYTONA_API_KEY`. SDK Daytona самостійно налаштовує URL сервера.
- **Singularity** — Потрібен `apptainer` або `singularity` у `$PATH`. Поширено на кластерах HPC.

Якщо сумніваєшся, встанови `terminal.backend` назад на `local` і спочатку переконайся, що команди працюють у цьому режимі.
### Синхронізація файлів Remote-to-Host під час завершення

Для **SSH**, **Modal** та **Daytona** бекендів (коли робоче дерево агента знаходиться на іншій машині, ніж хост, на якому запущений Hermes) Hermes відстежує файли, до яких агент звертався всередині віддаленої пісочниці, і під час завершення сесії / очищення пісочниці **синхронізує змінені файли назад на хост** у `~/.hermes/cache/remote-syncs/<session-id>/`.

- Спрацьовує при: закритті сесії, `/new`, `/reset`, тайм‑ауті повідомлення шлюзу, завершенні підзавдання `delegate_task`, коли дочірній процес використовував віддалений бекенд.
- Охоплює все дерево, яке агент модифікував, а не лише файли, які він явно відкрив. Додавання, редагування та видалення фіксуються.
- Віддалена пісочниця могла бути вже знищена, коли ти шукаєш файли; локальна копія `~/.hermes/cache/remote-syncs/…` є остаточним записом змін агента.
- Великі бінарні вихідні дані (контрольні точки моделей, сирі набори даних) обмежені за розміром — синхронізація пропускає файли, розмір яких перевищує `file_sync_max_mb` (за замовчуванням `100`). Збільш це значення, якщо очікуєш більші артефакти.

```yaml
terminal:
  file_sync_max_mb: 100     # default — sync files up to 100 MB each
  file_sync_enabled: true   # default — set false to skip the sync entirely
```

Таким чином ти відновлюєш результати з короткоживучих хмарних пісочниць, які знищуються після завершення сесії, без необхідності просити агента явно виконати `scp` або `modal volume put` для кожного артефакту.
### Docker Volume Mounts

При використанні бекенду Docker, `docker_volumes` дозволяє ділитися каталогами хоста з контейнером. Кожен запис використовує стандартний синтаксис Docker `-v`: `host_path:container_path[:options]`.

```yaml
terminal:
  backend: docker
  docker_volumes:
    - "/home/user/projects:/workspace/projects"   # Read-write (default)
    - "/home/user/datasets:/data:ro"              # Read-only
    - "/home/user/.hermes/cache/documents:/output" # Gateway-visible exports
```

Це корисно для:
- **Надання файлів** агенту (набори даних, конфігурації, референтний код)
- **Отримання файлів** від агента (згенерований код, звіти, експорти)
- **Спільних робочих просторів**, де і ти, і агент маєте доступ до однакових файлів

Якщо ти використовуєш шлюз повідомлень і хочеш, щоб агент надсилав згенеровані файли через
`MEDIA:/...`, віддай перевагу спеціальному видимому на хості експортному монтуванню, наприклад
`/home/user/.hermes/cache/documents:/output`.

- Записуй файли всередині Docker у `/output/...`
- Виводь **шлях хоста** у `MEDIA:`, наприклад:
  `MEDIA:/home/user/.hermes/cache/documents/report.txt`
- **Не** виводь `/workspace/...` або `/output/...`, якщо цей точний шлях не існує також для процесу шлюзу на хості

:::warning
YAML duplicate keys silently override earlier ones. Якщо у тебе вже є блок
`docker_volumes:`, об’єднуй нові монти у той самий список, а не додавай інший ключ `docker_volumes:` пізніше у файлі.
:::

Можна також задати через змінну середовища: `TERMINAL_DOCKER_VOLUMES='["/host:/container"]'` (JSON‑масив).
### Docker Credential Forwarding

За замовчуванням термінальні сесії Docker не успадковують довільні облікові дані хоста. Якщо потрібен певний токен всередині контейнера, додай його до `terminal.docker_forward_env`.

```yaml
terminal:
  backend: docker
  docker_forward_env:
    - "GITHUB_TOKEN"
    - "NPM_TOKEN"
```

Hermes спочатку отримує кожну зазначену змінну з твоєї поточної оболонки, а потім, якщо вона була збережена за допомогою `hermes config set`, переходить до `~/.hermes/.env`.

:::warning
Все, що вказано в `docker_forward_env`, стає видимим для команд, що виконуються всередині контейнера. Пересилай лише ті облікові дані, які тобі комфортно відкривати у термінальній сесії.
:::
### Запуск контейнера від імені користувача хоста

За замовчуванням Docker‑контейнери працюють як `root` (UID 0). Файли, створені всередині `/workspace` або інших bind‑mount'ів, виявляються власністю root на хості, тому після сесії доводиться виконувати `sudo chown`, щоб мати можливість редагувати їх у редакторі хоста. Прапорець `terminal.docker_run_as_host_user` виправляє це:

```yaml
terminal:
  backend: docker
  docker_run_as_host_user: true   # default: false
```

Коли він увімкнений, Hermes додає `--user $(id -u):$(id -g)` до команди `docker run`, тож файли, записані у bind‑mounted каталоги (`/workspace`, `/root`, будь‑що в `docker_volumes`) належать твоєму користувачу хоста, а не root. Недолік: контейнер більше не зможе виконувати `apt install` або записувати у шляхи, що належать root, наприклад `/root/.npm` — використай базовий образ, у якому `HOME` належить не‑root користувачу (або додай потрібні інструменти під час збірки образу), якщо потрібні обидві можливості.

Залиш це `false` (за замовчуванням) для зворотної сумісності. Увімкни, коли твій робочий процес в основному полягає у «редагуванні змонтованих файлів хоста» і ти втомився від `sudo chown -R`.
### Опціонально: змонтувати каталог запуску у `/workspace`

Docker‑пісочниці за замовчуванням залишаються ізольованими. Hermes **не** передає поточний робочий каталог хоста у контейнер, якщо ти явно не погодишся.

Увімкни це в `config.yaml`:

```yaml
terminal:
  backend: docker
  docker_mount_cwd_to_workspace: true
```

**Коли увімкнено:**
- якщо ти запускаєш Hermes з `~/projects/my-app`, цей каталог хоста буде bind‑монтовано до `/workspace`;
- бекенд Docker стартує в `/workspace`;
- інструменти роботи з файлами та команди терміналу бачать один і той самий змонтований проєкт.

**Коли вимкнено:** `/workspace` залишається власністю пісочниці, якщо ти явно не змонтуєш щось через `docker_volumes`.

**Компроміс безпеки:**
- `false` зберігає межу пісочниці;
- `true` надає пісочниці прямий доступ до каталогу, з якого ти запустив Hermes.

Використовуй цей параметр лише тоді, коли свідомо хочеш, щоб контейнер працював з живими файлами хоста.
### Постійна оболонка

За замовчуванням кожна команда терміналу виконується у власному підпроцесі — робочий каталог, змінні середовища та змінні оболонки скидаються між командами. Коли **постійна оболонка** увімкнена, один довгоживучий процес `bash` зберігається між викликами `execute()`, тож стан зберігається між командами.

Це найбільш корисно для **SSH backend**, де також усуваються накладні витрати на підключення для кожної команди. Постійна оболонка **увімкнена за замовчуванням для SSH** і вимкнена для локального бекенду.

```yaml
terminal:
  persistent_shell: true   # default — enables persistent shell for SSH
```

Щоб вимкнути:

```bash
hermes config set terminal.persistent_shell false
```

**Що зберігається між командами:**
- Робочий каталог (`cd /tmp` залишається для наступної команди)
- Експортовані змінні середовища (`export FOO=bar`)
- Змінні оболонки (`MY_VAR=hello`)

**Пріоритетність:**

| Рівень | Змінна | За замовчуванням |
|-------|----------|-------------------|
| Config | `terminal.persistent_shell` | `true` |
| SSH override | `TERMINAL_SSH_PERSISTENT` | слідує конфігурації |
| Local override | `TERMINAL_LOCAL_PERSISTENT` | `false` |

Змінні середовища, задані per‑backend, мають найвищий пріоритет. Якщо ти хочеш постійну оболонку і на локальному бекенді:

```bash
export TERMINAL_LOCAL_PERSISTENT=true
```

:::note
Команди, які потребують `stdin_data` або `sudo`, автоматично переходять у режим одноразового виконання, оскільки stdin постійної оболонки вже зайнятий протоколом IPC.
:::

Дивись [Code Execution](features/code-execution.md) та [розділ Terminal у README](features/tools.md) для деталей про кожен бекенд.
## Налаштування навичок

Навички можуть оголошувати власні параметри конфігурації через frontmatter у файлі **SKILL.md**. Це не‑секретні значення (шляхи, уподобання, налаштування домену), які зберігаються в просторі імен `skills.config` у файлі `config.yaml`.

```yaml
skills:
  config:
    myplugin:
      path: ~/myplugin-data   # Example — each skill defines its own keys
```

**Як працюють налаштування навичок:**

- `hermes config migrate` сканує всі увімкнені навички, знаходить не налаштовані параметри та пропонує їх ввести
- `hermes config show` відображає всі налаштування навичок у розділі «Skill Settings» разом із навичкою, до якої вони належать
- Коли навичка завантажується, її розвʼязані значення конфігурації автоматично ін’єкціються в контекст навички

**Встановлення значень вручну:**

```bash
hermes config set skills.config.myplugin.path ~/myplugin-data
```

Для деталей щодо оголошення параметрів конфігурації у власних навичках дивись [Creating Skills — Config Settings](/developer-guide/creating-skills#config-settings-configyaml).

### Захист записів навичок, створених агентом

Коли агент використовує `skill_manage` для створення, редагування, патчування або видалення навички, Hermes може за бажанням сканувати новий/оновлений вміст на предмет небезпечних шаблонів ключових слів (збір облікових даних, очевидна ін’єкція підказок, інструкції з exfil). Сканер **вимкнено за замовчуванням** — реальні робочі процеси агентів, які легітимно працюють з `~/.ssh/` або згадують `$OPENAI_API_KEY`, занадто часто спрацьовували за гевристикою. Увімкни його знову, якщо хочеш, щоб сканер запитував підтвердження перед тим, як записи навичок агента будуть застосовані:

```yaml
skills:
  guard_agent_created: true   # default: false
```

Коли увімкнено, будь‑який позначений запис `skill_manage` з’являється у вигляді запиту на підтвердження з поясненням сканера. Прийняті записи застосовуються; відхилені записи повертають агенту пояснювальну помилку.
## Конфігурація пам'яті

```yaml
memory:
  memory_enabled: true
  user_profile_enabled: true
  memory_char_limit: 2200   # ~800 tokens
  user_char_limit: 1375     # ~500 tokens
```
## Безпека читання файлів

Керує тим, скільки вмісту може повернути один виклик `read_file`. Читання, що перевищують ліміт, відхиляються з помилкою, яка підказує агенту використати `offset` і `limit` для меншого діапазону. Це запобігає тому, щоб одне читання мінімізованого JS‑пакету або великого файлу даних не заповнило вікно контексту.

```yaml
file_read_max_chars: 100000  # default — ~25-35K tokens
```

Збільш його, якщо ти працюєш з моделлю з великим вікном контексту і часто читаєш великі файли. Зменш його для моделей з малим контекстом, щоб читання залишалися ефективними:

```yaml
# Large context model (200K+)
file_read_max_chars: 200000

# Small local model (16K context)
file_read_max_chars: 30000
```

Агент також автоматично дедуплікує читання файлів — якщо та сама область файлу читається двічі і файл не змінився, повертається легка заглушка замість повторного надсилання вмісту. Це скидається при стисненні контексту, тож агент може повторно читати файли після того, як їх вміст був підсумований.
## Обмеження Обрізання Виводу Інструменту

Три пов’язані ліміти контролюють, скільки необробленого виводу інструмент може повернути, перш ніж Hermes його обрізатиме:

```yaml
tool_output:
  max_bytes: 50000        # terminal output cap (chars)
  max_lines: 2000         # read_file pagination cap
  max_line_length: 2000   # per-line cap in read_file's line-numbered view
```

- **`max_bytes`** — Коли команда `terminal` генерує більше цієї кількості символів сумарного `stdout`/`stderr`, Hermes залишає перші 40 % і останні 60 % і вставляє повідомлення `[OUTPUT TRUNCATED]` між ними. За замовчуванням `50000` (≈12‑15 K токенів у типових токенізаторах).
- **`max_lines`** — Верхня межа параметра `limit` одного виклику `read_file`. Запити, що перевищують це значення, обмежуються, щоб одне читання не заповнювало вікно контексту. За замовчуванням `2000`.
- **`max_line_length`** — Ліміт довжини рядка, що застосовується, коли `read_file` виводить нумерований вигляд. Рядки, довші за це, обрізаються до вказаної кількості символів і додається `... [truncated]`. За замовчуванням `2000`.

Збільшуй ліміти для моделей з великим вікном контексту, які можуть дозволити більше необробленого виводу за виклик. Зменшуй їх для моделей з малим контекстом, щоб результати інструменту залишалися компактними:

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
## Глобальне вимкнення набору інструментів

Щоб вимкнути певні набори інструментів у всьому CLI та на кожній платформі шлюзу в одному місці, вкажи їхні назви у параметрі `agent.disabled_toolsets`:

```yaml
agent:
  disabled_toolsets:
    - memory       # hide memory tools + MEMORY_GUIDANCE injection
    - web          # no web_search / web_extract anywhere
```

Це застосовується **після** конфігурації інструментів для окремих платформ (`platform_toolsets`, створеної за допомогою `hermes tools`), тому набір інструментів, зазначений тут, завжди видаляється — навіть якщо збережена конфігурація платформи все ще його містить. Використовуй це, коли потрібен один перемикач для «вимкнути X скрізь», а не редагування 15+ рядків платформ у інтерфейсі `hermes tools`.

Якщо залишити список порожнім або не вказати ключ, нічого не відбудеться.
## Ізоляція worktree Git

Увімкни ізольовані git‑worktree’и для одночасного запуску кількох агентів у тому самому репозиторії:

```yaml
worktree: true    # Always create a worktree (same as hermes -w)
# worktree: false # Default — only when -w flag is passed
```

Коли ця опція увімкнена, кожна CLI‑сесія створює новий worktree у каталозі `.worktrees/` зі своєю гілкою. Агентам можна редагувати файли, робити commit, push та створювати PR без взаємного впливу. Чисті worktree’и видаляються при виході; dirty worktree’и залишаються для ручного відновлення.

Ти також можеш перелічити файли, проігноровані `.gitignore`, які треба скопіювати у worktree, за допомогою файлу `.worktreeinclude` у корені репозиторію:

```
# .worktreeinclude
.env
.venv/
node_modules/
```
## Стиснення контексту

Hermes автоматично стискає довгі розмови, щоб залишатися в межах вікна контексту твоєї моделі. Сумаризатор стискання — це окремий виклик LLM, ти можеш вказати будь‑якого провайдера або кінцеву точку.

Усі налаштування стискання зберігаються у `config.yaml` (без змінних середовища).

### Повна довідка

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

:::info Міграція застарілої конфігурації
Старі конфігурації з `compression.summary_model`, `compression.summary_provider` та `compression.summary_base_url` автоматично мігруються до `auxiliary.compression.*` при першому завантаженні (версія конфігурації 17). Додаткових дій не потрібно.
:::

`hygiene_hard_message_limit` — це **запобіжний клапан перед стисканням** лише для шлюзу. Сесії з тисячами повідомлень можуть вичерпати ліміт контексту моделі до того, як спрацює звичайний поріг у відсотках; коли кількість повідомлень перевищує цей ліміт, Hermes примусово стискає, незалежно від використання токенів. За замовчуванням `400` — збільшуй його для платформ, де дуже довгі сесії є нормою, зменшуй, щоб примусити більш агресивне стискання. Зміна цього значення в запущеному шлюзі набирає чинності з наступним повідомленням (див. нижче).

`protect_first_n` керує кількістю **не‑системних** початкових повідомлень, які закріплюються під час кожного стискання. За замовчуванням `3` — початкова взаємодія користувач‑асистент зберігається після кожного проходу сумаризатора, щоб початкова мета залишалася видимою. У довготривалих сесіях скользького стискання, коли початковий хід вже не актуальний, встанови `protect_first_n: 0`, щоб закріпити лише системний промпт + підсумок + кінець. Сам системний промпт завжди зберігається незалежно від цього налаштування.

:::tip Гаряче перезавантаження шлюзу для стискання та довжини контексту
Починаючи з останніх випусків, зміна `model.context_length` або будь‑якого ключа `compression.*` у `config.yaml` у запущеному шлюзі набирає чинності з наступним повідомленням — без перезапуску шлюзу, без `/reset`, без необхідності обертання сесії. Підпис кешованого агента включає ці ключі, тому шлюз прозоро перебудовує агента, коли бачить зміну. API‑ключі та конфігурація інструментів/навичок все ще вимагають звичних шляхів перезавантаження.
:::

### Типові налаштування

**За замовчуванням (авто‑виявлення) — конфігурація не потрібна:**
```yaml
compression:
  enabled: true
  threshold: 0.50
```
Використовує твого основного провайдера та основну модель. Перевизначай для окремих завдань (наприклад, `auxiliary.compression.provider: openrouter` + `model: google/gemini-2.5-flash`), якщо хочеш стискати на дешевшій моделі, ніж твоя основна чат‑модель.

**Примусово вказати конкретного провайдера** (на основі OAuth або API‑ключа):
```yaml
auxiliary:
  compression:
    provider: nous
    model: gemini-3-flash
```
Працює з будь‑яким провайдером: `nous`, `openrouter`, `codex`, `anthropic`, `main` тощо.

**Власна кінцева точка** (self‑hosted, Ollama, zai, DeepSeek тощо):
```yaml
auxiliary:
  compression:
    model: glm-4.7
    base_url: https://api.z.ai/api/coding/paas/v4
```
Вказує на власну сумісну з OpenAI кінцеву точку. Для автентифікації використовує `OPENAI_API_KEY`.

### Як взаємодіють три налаштування

| `auxiliary.compression.provider` | `auxiliary.compression.base_url` | Результат |
|----------------------------------|----------------------------------|-----------|
| `auto` (за замовчуванням)        | не встановлено                   | Авто‑виявлення найкращого доступного провайдера |
| `nous` / `openrouter` / тощо      | не встановлено                   | Примусово використати цей провайдер, його автентифікація |
| будь‑яке                         | встановлено                      | Використати вказану власну кінцеву точку (провайдер ігнорується) |

:::warning Вимога до довжини контексту моделі підсумку
Модель підсумку **повинна** мати вікно контексту принаймні таке ж, як у твоєї основної моделі агента. Компресор надсилає повну середню частину розмови до моделі підсумку — якщо вікно контексту цієї моделі менше, ніж у основної, виклик сумаризації завершиться помилкою через недостатню довжину контексту. У такому випадку середні ходи **будуть відкинуті без підсумку**, і контекст розмови буде втрачено без повідомлення. Якщо ти перевизначаєш модель, переконайся, що її довжина контексту відповідає або перевищує довжину контексту твоєї основної моделі.
:::
## Context Engine

Контекстний двигун керує тим, як ведуться розмови, коли наближаєшся до ліміту токенів моделі. Вбудований двигун `compressor` використовує втратне підсумовування (дивись [Context Compression](/developer-guide/context-compression-and-caching)). Двигуни‑плагіни можуть замінити його альтернативними стратегіями.

```yaml
context:
  engine: "compressor"    # default — built-in lossy summarization
```

Щоб використати двигун‑плагін (наприклад, LCM для без втрат управління контекстом):

```yaml
context:
  engine: "lcm"          # must match the plugin's name
```

Двигуни‑плагіни **ніколи не активуються автоматично** — ти маєш явно встановити `context.engine` на назву плагіна. Доступні двигуни можна переглянути та вибрати за допомогою `hermes plugins` → Provider Plugins → Context Engine.

Дивись [Memory Providers](/user-guide/features/memory-providers) для аналогічної системи одиночного вибору плагінів пам'яті.
## Тиск бюджету ітерацій

Коли агент працює над складним завданням із багатьма викликами інструментів, він може витратити свій бюджет ітерацій (за замовчуванням: 90 ходів), не помічаючи, що залишилось мало. Тиск бюджету автоматично попереджає модель, коли вона наближається до ліміту:

| Поріг | Рівень | Що бачить модель |
|-----------|-------|---------------------|
| **70%** | Увага | `[BUDGET: 63/90. 27 iterations left. Start consolidating.]` |
| **90%** | Попередження | `[BUDGET WARNING: 81/90. Only 9 left. Respond NOW.]` |

Попередження вставляються у JSON останнього результату інструмента (як поле `_budget_warning`), а не як окремі повідомлення — це зберігає кешування підказок і не порушує структуру розмови.

```yaml
agent:
  max_turns: 90                # Max iterations per conversation turn (default: 90)
  api_max_retries: 3           # Retries per provider before fallback engages (default: 3)
```

Тиск бюджету ввімкнено за замовчуванням. Агент бачить попередження природно як частину результатів інструментів, що спонукає його консолідувати роботу та надати відповідь до того, як вичерпає ітерації.

Коли бюджет ітерацій повністю вичерпується, CLI показує користувачеві сповіщення: `⚠ Iteration budget reached (90/90) — response may be incomplete`. Якщо бюджет закінчується під час активної роботи, агент генерує підсумок того, що було досягнуто, перед зупинкою.

`agent.api_max_retries` керує кількістю спроб Hermes повторити виклик API провайдера при тимчасових помилках (обмеження швидкості, втрати з’єднання, 5xx) **перед** перемиканням на fallback‑provider. За замовчуванням це `3` — всього чотири спроби. Якщо у вас налаштовані [fallback providers](/user-guide/features/fallback-providers) і ви хочете швидше переключатися, встановіть `0`, щоб перша тимчасова помилка на вашому основному провайдері одразу передавала управління fallback‑provider, а не витрачала спроби на нестабільний кінцевий пункт.

### Тайм‑аути API

Hermes має окремі рівні тайм‑аутів для потокової передачі, а також детектор «застою» для непотокових викликів. Детектори застою автоматично налаштовуються лише для локальних провайдерів, коли ви залишаєте їх у неявних значеннях за замовчуванням.

| Тайм‑аут | За замовчуванням | Локальні провайдери | Конфіг / env |
|---------|------------------|--------------------|--------------|
| Тайм‑аут читання сокету | 120 s | Авто‑збільшено до 1800 s | `HERMES_STREAM_READ_TIMEOUT` |
| Детекція застою потоку | 180 s | Авто‑вимкнено | `HERMES_STREAM_STALE_TIMEOUT` |
| Детекція застою без потоку | 300 s | Авто‑вимкнено, коли залишено неявно | `providers.<id>.stale_timeout_seconds` або `HERMES_API_CALL_STALE_TIMEOUT` |
| API‑виклик (не‑потоковий) | 1800 s | Без змін | `providers.<id>.request_timeout_seconds` / `timeout_seconds` або `HERMES_API_TIMEOUT` |

**Тайм‑аут читання сокету** визначає, як довго httpx чекає наступний фрагмент даних від провайдера. Локальні LLM можуть займати хвилини на попереднє заповнення великих контекстів перед виведенням першого токену, тому Hermes підвищує цей тайм‑аут до 30 хвилин, коли виявляє локальний кінцевий пункт. Якщо ви явно задаєте `HERMES_STREAM_READ_TIMEOUT`, це значення завжди використовується, незалежно від виявлення кінцевого пункту.

**Детекція застою потоку** розриває з’єднання, які отримують ping‑и SSE keep‑alive, але без реального вмісту. Це повністю вимкнено для локальних провайдерів, оскільки вони не надсилають keep‑alive ping‑и під час попереднього заповнення.

**Детекція застою без потоку** розриває непотокові виклики, які надто довго не повертають відповідь. За замовчуванням Hermes вимикає це для локальних кінцевих пунктів, щоб уникнути хибних спрацьовувань під час тривалих попередніх заповнень. Якщо ви явно задаєте `providers.<id>.stale_timeout_seconds`, `providers.<id>.models.<model>.stale_timeout_seconds` або `HERMES_API_CALL_STALE_TIMEOUT`, це значення буде дотримано навіть для локальних кінцевих пунктів.
## Попередження про тиск контексту

Окремо від тиску бюджету ітерації, тиск контексту відстежує, наскільки розмова наближається до **порогу ущільнення** — моменту, коли спрацьовує стиск контексту для підсумовування старих повідомлень. Це допомагає і тобі, і агенту розуміти, коли розмова стає довгою.

| Прогрес | Рівень | Що відбувається |
|----------|-------|-----------------|
| **≥ 60%** до порогу | Info | CLI показує блакитну смужку прогресу; gateway надсилає інформаційне сповіщення |
| **≥ 85%** до порогу | Warning | CLI показує жирну жовту смужку; gateway попереджає, що стиск незабаром відбудеться |

У CLI тиск контексту відображається як смужка прогресу у виводі інструменту:

```
  ◐ context ████████████░░░░░░░░ 62% to compaction  48k threshold (50%) · approaching compaction
```

На платформах обміну повідомленнями надсилається просте текстове сповіщення:

```
◐ Context: ████████████░░░░░░░░ 62% to compaction (threshold: 50% of window).
```

Якщо автоматичний стиск вимкнено, попередження повідомляє, що контекст може бути обрізаний замість стискання.

Тиск контексту працює автоматично — ніяких налаштувань не потрібно. Він спрацьовує лише як повідомлення для користувача і не змінює потік повідомлень і не впроваджує нічого в контекст моделі.
## Стратегії пулу облікових даних

Коли у тебе є кілька API‑ключів або OAuth‑токенів для одного провайдера, налаштуй стратегію ротації:

```yaml
credential_pool_strategies:
  openrouter: round_robin    # cycle through keys evenly
  anthropic: least_used      # always pick the least-used key
```

Опції: `fill_first` (за замовчуванням), `round_robin`, `least_used`, `random`. Дивись [Пули облікових даних](/user-guide/features/credential-pools) для повної документації.
## Кешування підказок

Hermes автоматично вмикає кешування підказок між сесіями, коли активний провайдер це підтримує — без налаштувань користувача.

Для Claude на **native Anthropic**, **OpenRouter** та **Nous Portal** Hermes додає контрольні точки `cache_control` з TTL = 1 година (`ttl: "1h"`) до системної підказки та блоків навичок. Перша відправка протягом нової години оплачується за повними тарифами вводу; подальші відправки в будь‑якій сесії протягом тієї ж години беруть дані з кешу за зниженою тарифою читання кешу. Це означає, що системна підказка, завантажений вміст навичок і початкова частина будь‑якого довгого контексту повторно використовуються в різних сесіях `hermes` та у форкованих підагентах протягом першої години.

У Qwen Cloud (Alibaba DashScope) верхня межа TTL кешу становить 5 хвилин, тому Hermes використовує TTL = 5 хвилин для контрольних точок там. Інші шляхи Claude через сторонні провайдери (AWS Bedrock, Azure Foundry) повертаються до власних налаштувань кешування провайдера. xAI Grok використовує окремий механізм розмови, прив’язаний до сесії — дивись [xAI prompt caching](/integrations/providers#xai-grok--responses-api--prompt-caching).

Жодного перемикача для вимкнення цього немає — кешування завжди ввімкнено і економить гроші навіть у одноразових діалогах, оскільки системна підказка сама по собі становить значну частину кількості вхідних токенів.
## Додаткові моделі

Hermes використовує «auxiliary» моделі для побічних завдань, таких як аналіз зображень, підсумовування веб‑сторінок, аналіз скріншотів браузера, генерація назви сесії та стиснення контексту. За замовчуванням (`auxiliary.*.provider: "auto"`), Hermes направляє кожне auxiliary‑завдання до твоєї **головної чат‑моделі** — того ж провайдера/моделі, яку ти вибрав у `hermes model`. Нічого налаштовувати не потрібно, щоб розпочати, але май на увазі, що на дорогих моделях розуміння (Opus, MiniMax M2.7 тощо) auxiliary‑завдання додають суттєві витрати. Якщо потрібні дешеві та швидкі побічні завдання незалежно від твоєї головної моделі, явно встанови `auxiliary.<task>.provider` та `auxiliary.<task>.model` (наприклад, Gemini Flash на OpenRouter для візуального та веб‑видобутку).

:::note Чому «auto» використовує твою головну модель
Раніші збірки розподіляли користувачів‑агрегаторів (OpenRouter, Nous Portal) на дешевий провайдер‑за‑замовчуванням. Це було несподівано — користувачі, які сплачували підписку на агрегатор, бачили іншу модель, що обробляла їхній auxiliary‑трафік. Тепер `auto` використовує головну модель для всіх, а переваги для окремих завдань у `config.yaml` залишаються (дивись [Full auxiliary config reference](#full-auxiliary-config-reference) нижче).
:::
### Налаштування допоміжних моделей інтерактивно

Замість ручного редагування YAML запусти `hermes model` і вибери **"Configure auxiliary models"** у меню. Ти отримаєш інтерактивний вибір для кожного завдання:

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

Вибери завдання, обери provider (OAuth‑flows відкривають браузер; provider‑и з API‑key запитують), вибери модель. Зміна зберігається у `auxiliary.<task>.*` у `config.yaml`. Та ж механіка, що й у виборі основної моделі — жодного додаткового синтаксису вчити не потрібно.
### Відео‑підручник

<div style={{position: 'relative', width: '100%', aspectRatio: '16 / 9', marginBottom: '1.5rem'}}>
  <iframe
    src="https://www.youtube.com/embed/NoF-YajElIM"
    title="Hermes Agent — Auxiliary Models Tutorial"
    style={{position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', border: 0}}
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
    allowFullScreen
  />
</div>
### Універсальний шаблон конфігурації

Кожен слот моделі в Hermes — допоміжні завдання, стиснення, запасний (варіант) — використовує ті ж самі три налаштування:

| Ключ | Що робить | За замовчуванням |
|-----|-----------|------------------|
| `provider` | Якого провайдера використовувати для автентифікації та маршрутизації | `"auto"` |
| `model` | Яку модель запитувати | типове значення провайдера |
| `base_url` | Кастомна кінцева точка, сумісна з OpenAI (перезаписує провайдера) | не встановлено |

Коли встановлено `base_url`, Hermes ігнорує провайдера і викликає цю кінцеву точку безпосередньо (використовуючи `api_key` або `OPENAI_API_KEY` для автентифікації). Коли встановлено лише `provider`, Hermes використовує вбудовану автентифікацію та базовий URL цього провайдера.

Доступні провайдери для допоміжних завдань: `auto`, `main`, а також будь‑який провайдер у [реєстрі провайдерів](/reference/environment-variables) — `openrouter`, `nous`, `openai-codex`, `copilot`, `copilot-acp`, `anthropic`, `gemini`, `google-gemini-cli`, `qwen-oauth`, `zai`, `kimi-coding`, `kimi-coding-cn`, `minimax`, `minimax-cn`, `minimax-oauth`, `deepseek`, `nvidia`, `xai`, `xai-oauth`, `ollama-cloud`, `alibaba`, `bedrock`, `huggingface`, `arcee`, `xiaomi`, `kilocode`, `opencode-zen`, `opencode-go`, `azure-foundry` — або будь‑який іменований кастомний провайдер зі списку `custom_providers` (наприклад `provider: "beans"`).

:::tip MiniMax OAuth
`minimax-oauth` виконує вхід через браузерний OAuth (не потрібен API‑ключ). Запусти `hermes model` і вибери **MiniMax (OAuth)** для автентифікації. Допоміжні завдання автоматично використовують `MiniMax-M2.7-highspeed`. Дивись [посібник MiniMax OAuth](../guides/minimax-oauth.md).
:::

:::tip xAI Grok OAuth
`xai-oauth` виконує вхід через браузерний OAuth для підписників SuperGrok та X Premium+ (не потрібен API‑ключ). Запусти `hermes model` і вибери **xAI Grok OAuth (SuperGrok / Premium+)** для автентифікації. Той самий OAuth‑токен використовується для всіх прямих до xAI сервісів (чат, допоміжні завдання, TTS, генерація зображень, відео, транскрипція). Дивись [посібник xAI Grok OAuth](../guides/xai-grok-oauth.md), а якщо Hermes працює на віддаленому хості — [OAuth через SSH / Віддалені хости](../guides/oauth-over-ssh.md).
:::

:::warning `"main"` використовується лише для допоміжних завдань
Опція провайдера `"main"` означає «використовувати той же провайдер, що й мій головний агент» — вона дійсна лише всередині конфігурацій `auxiliary:`, `compression:` та `fallback_model:`. Це **не** дійсне значення для вашого налаштування `model.provider` верхнього рівня. Якщо ви використовуєте кастомну кінцеву точку, сумісну з OpenAI, встановіть `provider: custom` у розділі `model:`. Дивись [AI Providers](/integrations/providers) для всіх варіантів провайдерів головних моделей.
:::
### Повний довідник допоміжних налаштувань

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
Кожне допоміжне завдання має налаштовуваний `timeout` (у секундах). За замовчуванням: vision 120 с, web_extract 360 с, approval 30 с, compression 120 с. Збільш ці значення, якщо використовуєш повільні локальні моделі для допоміжних завдань. У vision також є окремий `download_timeout` (за замовчуванням 30 с) для HTTP‑завантаження зображень — збільш його для повільних з’єднань або самохостинг‑серверів зображень.
:::

:::info
Компресія контексту має власний блок `compression:` для порогових значень і блок `auxiliary.compression:` для налаштувань модель/провайдер — дивись [Context Compression](#context-compression) вище. Запасний (варіант) модель використовує блок `fallback_model:` — дивись [Fallback Model](/integrations/providers#fallback-providers). Усі три слідують одному шаблону провайдер/модель/base_url.
:::
### Маршрутизація OpenRouter та Pareto Code для допоміжних завдань

Коли допоміжне завдання вирішується на OpenRouter (або явно, або через `provider: "main"` під час, коли твій основний агент працює на OpenRouter), налаштування `provider_routing` та `openrouter.min_coding_score` основного агента **не поширюються** — за задумом кожне допоміжне завдання є незалежним. Щоб задати переваги провайдера OpenRouter або використати [Pareto Code router](/integrations/providers#openrouter-pareto-code-router) для конкретного допоміжного завдання, встанови їх у межах завдання через `extra_body`:

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

Структура відповідає тому, що OpenRouter приймає у тілі запиту chat completions. Hermes передає весь `extra_body` дослівно, тому будь‑яке інше поле тіла запиту OpenRouter, задокументоване на [openrouter.ai/docs](https://openrouter.ai/docs), працює так само.
### Зміна моделі зору

Щоб використовувати GPT-4o замість Gemini Flash для аналізу зображень:

```yaml
auxiliary:
  vision:
    model: "openai/gpt-4o"
```

Або через змінну середовища (у `~/.hermes/.env`):

```bash
AUXILIARY_VISION_MODEL=openai/gpt-4o
```
### Параметри провайдера

Ці параметри застосовуються до **додаткових конфігурацій завдань** (`auxiliary:`, `compression:`, `fallback_model:`), а не до вашого основного налаштування `model.provider`.

| Провайдер | Опис | Вимоги |
|----------|------|--------|
| `"auto"` | Найкращий доступний (за замовчуванням). Vision пробує OpenRouter → Nous → Codex. | — |
| `"openrouter"` | Примусово OpenRouter — маршрутизує до будь‑якої моделі (Gemini, GPT‑4o, Claude тощо). | `OPENROUTER_API_KEY` |
| `"nous"` | Примусово Nous Portal. | `hermes auth` |
| `"codex"` | Примусово Codex OAuth (обліковий запис ChatGPT). Підтримує vision (gpt‑5.3‑codex). | `hermes model` → Codex |
| `"minimax-oauth"` | Примусово MiniMax OAuth (вхід у браузері, без API‑ключа). Використовує MiniMax‑M2.7‑highspeed для додаткових завдань. | `hermes model` → MiniMax (OAuth) |
| `"xai-oauth"` | Примусово xAI Grok OAuth (вхід у браузері для підписників SuperGrok або X Premium+, без API‑ключа). Один токен OAuth охоплює чат, TTS, зображення, відео та транскрипцію. | `hermes model` → xAI Grok OAuth (SuperGrok / Premium+) |
| `"main"` | Використовує ваш активний кастомний/головний endpoint. Може бути заданий через `OPENAI_BASE_URL` + `OPENAI_API_KEY` або через кастомний endpoint, збережений за допомогою `hermes model` / `config.yaml`. Працює з OpenAI, локальними моделями або будь‑яким сумісним з OpenAI API. **Тільки для додаткових завдань — не підходить для `model.provider`.** | Облікові дані кастомного endpoint + базовий URL |

Прямі провайдери API‑ключів з основного каталогу провайдерів також працюють тут, коли потрібно, щоб допоміжні завдання обходили ваш типовий роутер. `gmi` дійсний, коли налаштовано `GMI_API_KEY`:

```yaml
auxiliary:
  compression:
    provider: "gmi"
    model: "anthropic/claude-opus-4.6"
```

Для маршрутизації GMI auxiliary використовуйте точний ідентифікатор моделі, який повертає endpoint `/v1/models` сервісу GMI.
### Загальні налаштування

**Використання прямого кастомного endpoint** (зрозуміліше, ніж `provider: "main"` для локальних/самохостованих API):
```yaml
auxiliary:
  vision:
    base_url: "http://localhost:1234/v1"
    api_key: "local-key"
    model: "qwen2.5-vl"
```

`base_url` має пріоритет над `provider`, тому це найявніший спосіб направити допоміжне завдання до конкретного endpoint. При прямому перевизначенні endpoint Hermes використовує налаштований `api_key` або повертається до `OPENAI_API_KEY`; він не повторно використовує `OPENROUTER_API_KEY` для цього кастомного endpoint.

**Використання OpenAI API key для vision:**
```yaml
# In ~/.hermes/.env:
# OPENAI_BASE_URL=https://api.openai.com/v1
# OPENAI_API_KEY=sk-...

auxiliary:
  vision:
    provider: "main"
    model: "gpt-4o"       # or "gpt-4o-mini" for cheaper
```

**Використання OpenRouter для vision** (маршрутизація до будь‑якої моделі):
```yaml
auxiliary:
  vision:
    provider: "openrouter"
    model: "openai/gpt-4o"      # or "google/gemini-2.5-flash", etc.
```

**Використання Codex OAuth** (обліковий запис ChatGPT Pro/Plus — API key не потрібен):
```yaml
auxiliary:
  vision:
    provider: "codex"     # uses your ChatGPT OAuth token
    # model defaults to gpt-5.3-codex (supports vision)
```

**Використання MiniMax OAuth** (вхід через браузер, API key не потрібен):
```yaml
model:
  default: MiniMax-M2.7
  provider: minimax-oauth
  base_url: https://api.minimax.io/anthropic
```
Запусти `hermes model` і вибери **MiniMax (OAuth)**, щоб увійти та встановити це автоматично. Для регіону Китай базовий URL буде `https://api.minimaxi.com/anthropic`. Дивись [посібник MiniMax OAuth](../guides/minimax-oauth.md) для повного покрокового опису.

**Використання локальної/самохостованої моделі:**
```yaml
auxiliary:
  vision:
    provider: "main"      # uses your active custom endpoint
    model: "my-local-model"
```

`provider: "main"` використовує будь‑якого провайдера, який Hermes застосовує для звичайного чату — будь то іменований кастомний провайдер (наприклад, `beans`), вбудований провайдер типу `openrouter` або застарілий endpoint `OPENAI_BASE_URL`.

:::tip
Якщо ти використовуєш Codex OAuth як основного провайдера моделі, vision працює автоматично — додаткова конфігурація не потрібна. Codex включений у ланцюжок автодетекції для vision.
:::

:::warning
**Vision вимагає мультимодальної моделі.** Якщо ти встановив `provider: "main"`, переконайся, що твій endpoint підтримує мультимодальність/vision — інакше аналіз зображень завершиться помилкою.
:::
### Змінні середовища (застарілі)

Додаткові моделі також можна налаштувати за допомогою змінних середовища. Однак `config.yaml` — це переважний метод, оскільки його легше керувати і він підтримує усі параметри, включаючи `base_url` та `api_key`.

| Параметр | Змінна середовища |
|---------|---------------------|
| Vision provider | `AUXILIARY_VISION_PROVIDER` |
| Vision model | `AUXILIARY_VISION_MODEL` |
| Vision endpoint | `AUXILIARY_VISION_BASE_URL` |
| Vision API key | `AUXILIARY_VISION_API_KEY` |
| Web extract provider | `AUXILIARY_WEB_EXTRACT_PROVIDER` |
| Web extract model | `AUXILIARY_WEB_EXTRACT_MODEL` |
| Web extract endpoint | `AUXILIARY_WEB_EXTRACT_BASE_URL` |
| Web extract API key | `AUXILIARY_WEB_EXTRACT_API_KEY` |

Параметри стискання та запасного (варіант) моделі можна задати лише у `config.yaml`.

:::tip
Запусти `hermes config`, щоб побачити поточні налаштування додаткових моделей. Перевизначення відображаються лише тоді, коли вони відрізняються від значень за замовчуванням.
:::
## Зусилля розумової обробки

Керуйте тим, скільки «думання» модель виконує перед відповіддю:

```yaml
agent:
  reasoning_effort: ""   # empty = medium (default). Options: none, minimal, low, medium, high, xhigh (max)
```

Якщо параметр не встановлено (за замовчуванням), зусилля розумової обробки мають значення «середнє» — збалансований рівень, який добре підходить для більшості завдань. Встановлення значення перевизначає його — вищі зусилля розумової обробки дають кращі результати у складних завданнях, але вимагають більше токенів і збільшують затримку.

Ти також можеш змінити зусилля розумової обробки під час виконання за допомогою команди `/reasoning`:

```
/reasoning           # Show current effort level and display state
/reasoning high      # Set reasoning effort to high
/reasoning none      # Disable reasoning
/reasoning show      # Show model thinking above each response
/reasoning hide      # Hide model thinking
```
## Примусове використання інструментів

Деякі моделі іноді описують заплановані дії у вигляді тексту замість здійснення викликів інструментів («Я би запустив тести…» замість фактичного виклику терміналу). Примусове використання інструментів додає до системного промпту вказівки, які повертають модель до реального виклику інструментів.

```yaml
agent:
  tool_use_enforcement: "auto"   # "auto" | true | false | ["model-substring", ...]
```

| Value | Behavior |
|-------|----------|
| `"auto"` (default) | Увімкнено для моделей, що відповідають: `gpt`, `codex`, `gemini`, `gemma`, `grok`. Вимкнено для всіх інших (Claude, DeepSeek, Qwen тощо). |
| `true` | Завжди увімкнено, незалежно від моделі. Корисно, якщо ти помічаєш, що поточна модель описує дії замість їх виконання. |
| `false` | Завжди вимкнено, незалежно від моделі. |
| `["gpt", "codex", "qwen", "llama"]` | Увімкнено лише коли назва моделі містить один із зазначених підрядків (без урахування регістру). |

### Що саме додається

Коли увімкнено, до системного промпту можуть бути додані три рівні вказівок:

1. **Загальний примус використання інструментів** (усі підходящі моделі) — інструктує модель одразу робити виклики інструментів замість опису намірів, продовжувати роботу, доки завдання не буде завершено, і ніколи не завершувати хід обіцянкою майбутньої дії.

2. **Дисципліна виконання OpenAI** (лише моделі GPT та Codex) — додаткові вказівки, що стосуються специфічних проблем GPT: покидання роботи на часткових результатах, пропуск попередніх пошуків, галюцинації замість використання інструментів та оголошення «готово» без перевірки.

3. **Операційні вказівки Google** (лише моделі Gemini та Gemma) — стислисть, абсолютні шляхи, паралельні виклики інструментів та патерн «перевірити‑перед‑редагуванням».

Це прозоро для користувача і впливає лише на системний промпт. Моделі, які вже надійно використовують інструменти (наприклад Claude), не потребують цих вказівок, тому `"auto"` їх виключає.

### Коли вмикати

Якщо ти використовуєш модель, якої немає у списку за замовчуванням, і помічаєш, що вона часто описує, що *зробила б*, замість реального виконання, встанови `tool_use_enforcement: true` або додай підрядок моделі до списку:

```yaml
agent:
  tool_use_enforcement: ["gpt", "codex", "gemini", "grok", "my-custom-model"]
```
## Конфігурація TTS

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

Це керує як інструментом `text_to_speech`, так і озвученими відповідями у режимі голосу (`/voice tts` у CLI або messaging gateway).

**Ієрархія запасного (фолбек) швидкості:** швидкість, специфічна для провайдера (наприклад, `tts.edge.speed`) → глобальна `tts.speed` → типове значення `1.0`. Встанови глобальну `tts.speed`, щоб застосувати уніфіковану швидкість до всіх провайдерів, або перевизначай її для окремих провайдерів для тонкого налаштування.
## Налаштування відображення

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

### Перевірка зміни файлів

Коли `display.file_mutation_verifier` має значення `true` (за замовчуванням), Hermes додає однорядкове попередження до остаточної відповіді асистента, якщо під час ходу виклик `write_file` або `patch` завершився невдачею і ніколи не був замінений успішним записом у той самий шлях. Це ловить випадки типу «пакет паралельних патчів, половина тихо падає, модель підсумовує успіх» без потреби вручну запускати `git status` після кожного редагування.

Приклад нижнього колонтитула:

```
⚠️ File-mutation verifier: 3 file(s) were NOT modified this turn despite any wording above that may suggest otherwise. Run `git status` or `read_file` to confirm.
  • concepts/automatic-organization.md — [patch] Could not find match for old_string
  • concepts/lora.md — [patch] Could not find match for old_string
  • concepts/rag-pipeline.md — [patch] Could not find match for old_string
```

Встанови `file_mutation_verifier: false` (або `HERMES_FILE_MUTATION_VERIFIER=0`), щоб вимкнути цей нижній колонтитул. Перевірка спрацьовує лише коли реальні помилки залишаються наприкінці ходу — модель, яка повторно виконує невдалий патч і успішно завершує його в тому ж ході, не викличе його для цього файлу.

### Мова інтерфейсу для статичних повідомлень

Параметр `display.language` перекладає невеликий набір статичних повідомлень, орієнтованих на користувача — запит підтвердження в CLI, кілька відповідей шлюзу на слеш‑команди (наприклад, повідомлення про перезапуск‑дрен, «підтвердження прострочено», «мету очищено»). Він **не** перекладає відповіді агента, рядки журналу, вивід інструментів, трасування помилок або описи слеш‑команд — вони залишаються англійською. Якщо ти хочеш, щоб сам агент відповідав іншою мовою, просто вкажи це у своєму запиті або системному повідомленні.

Підтримувані значення: `en` (за замовчуванням), `zh` (спрощений китайський), `ja` (японська), `de` (німецька), `es` (іспанська), `fr` (французька), `tr` (турецька), `uk` (українська). Невідомі значення повертаються до англійської.

Також можна задати це для окремої сесії за допомогою змінної середовища `HERMES_LANGUAGE`, яка переважає над значенням у конфігурації.

```yaml
display:
  language: zh   # CLI approval prompts appear in Chinese
```

| Режим   | Що бачиш                                                                 |
|---------|--------------------------------------------------------------------------|
| `off`   | Тихо — лише остаточна відповідь                                            |
| `new`   | Показник інструмента лише коли інструмент змінюється                      |
| `all`   | Кожен виклик інструмента з коротким попереднім переглядом (за замовчуванням) |
| `verbose` | Повні аргументи, результати та журнали налагодження                     |

У CLI перемикай ці режими за допомогою `/verbose`. Щоб використовувати `/verbose` у платформах обміну повідомленнями (Telegram, Discord, Slack тощо), встанови `tool_progress_command: true` у розділі `display` вище. Команда тоді перемикатиме режим і зберігатиме його в конфігурації.

### Нижній колонтитул метаданих виконання (лише шлюз)

Коли `display.runtime_footer.enabled: true`, Hermes додає невеликий нижній колонтитул контексту виконання до **остаточного** повідомлення кожного ходу шлюзу — та сама інформація, яку CLI показує у статусному рядку (модель, % контексту, cwd, тривалість сесії, токени, вартість). За замовчуванням вимкнено; можна ввімкнути окремо для кожного шлюзу, якщо команда хоче, щоб кожна відповідь містила джерело.

```yaml
display:
  runtime_footer:
    enabled: true
    fields: ["model", "context_pct", "cwd"]   # any of: model, context_pct, cwd, duration, tokens, cost
```

Слеш‑команда `/footer` перемикає це під час виконання в будь‑якій сесії.

Приклад нижнього колонтитула, доданого до відповіді в Telegram/Discord/Slack:

```
— claude-opus-4.7 · 12 tool calls · 2m 14s · $0.042
```

Тільки **остаточне** повідомлення ходу отримує нижній колонтитул; проміжні оновлення залишаються чистими.

### Перевизначення прогресу для різних платформ

Різні платформи мають різні потреби у деталізації. Наприклад, Signal не може редагувати повідомлення, тому кожне оновлення прогресу стає окремим повідомленням — це шумно. Використовуй `display.platforms`, щоб задати режими для окремих платформ:

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

Платформи без перевизначення повертаються до глобального значення `tool_progress`. Дійсні ключі платформ: `telegram`, `discord`, `slack`, `signal`, `whatsapp`, `matrix`, `mattermost`, `email`, `sms`, `homeassistant`, `dingtalk`, `feishu`, `wecom`, `weixin`, `bluebubbles`, `qqbot`. Застарілий ключ `display.tool_progress_overrides` все ще завантажується для зворотної сумісності, але він застарів і при першому завантаженні переноситься у `display.platforms`.

`interim_assistant_messages` — лише для шлюзу. Коли ввімкнено, Hermes надсилає завершені проміжні оновлення асистента як окремі чат‑повідомлення. Це незалежно від `tool_progress` і не потребує потокової передачі шлюзу.
## Privacy

```yaml
privacy:
  redact_pii: false  # Strip PII from LLM context (gateway only)
```

Коли `redact_pii` має значення `true`, шлюз видаляє персонально ідентифіковану інформацію з системного запиту перед його передачею до LLM на підтримуваних платформах:

| Поле | Обробка |
|-------|-----------|
| Номери телефонів (user ID у WhatsApp/Signal) | Хешується до `user_<12-char-sha256>` |
| User IDs | Хешується до `user_<12-char-sha256>` |
| Chat IDs | Хешується лише числова частина, префікс платформи зберігається (`telegram:<hash>`) |
| Home channel IDs | Хешується лише числова частина |
| Імена користувачів / username | **Не змінюються** (вибрано користувачем, публічно видно) |

**Підтримка платформ:** редагування застосовується до WhatsApp, Signal та Telegram. Discord і Slack виключені, оскільки їх системи згадувань (`<@user_id>`) вимагають реального ID у контексті LLM.

Хеші детерміновані — один і той самий користувач завжди отримує один і той самий хеш, тому модель все ще може розрізняти користувачів у групових чатах. Маршрутизація та доставка використовують оригінальні значення внутрішньо.
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

Поведінка провайдера:

- `local` використовує `faster-whisper`, що працює на твоєму комп’ютері. Встанови його окремо за допомогою `pip install faster-whisper`.
- `groq` використовує сумісну з Whisper кінцеву точку Groq і читає `GROQ_API_KEY`.
- `openai` використовує speech API OpenAI і читає `VOICE_TOOLS_OPENAI_KEY`.

Якщо запитаний провайдер недоступний, Hermes автоматично переходить до запасного (варіанту) у такому порядку: `local` → `groq` → `openai`.

Перевизначення моделей Groq та OpenAI керуються змінними середовища:

```bash
STT_GROQ_MODEL=whisper-large-v3-turbo
STT_OPENAI_MODEL=whisper-1
GROQ_BASE_URL=https://api.groq.com/openai/v1
STT_OPENAI_BASE_URL=https://api.openai.com/v1
```
## Голосовий режим (CLI)

```yaml
voice:
  record_key: "ctrl+b"         # Push-to-talk key inside the CLI
  max_recording_seconds: 120    # Hard stop for long recordings
  auto_tts: false               # Enable spoken replies automatically when /voice on
  beep_enabled: true            # Play record start/stop beeps in CLI voice mode
  silence_threshold: 200        # RMS threshold for speech detection
  silence_duration: 3.0         # Seconds of silence before auto-stop
```

Використовуй `/voice on` у CLI, щоб увімкнути режим мікрофону, `record_key` — для старту/зупинки запису, і `/voice tts` — щоб перемкнути озвучення відповідей. Дивись [Voice Mode](/user-guide/features/voice-mode) для налаштування від початку до кінця та поведінки, специфічної для платформи.
## Streaming

Стрімити токени у термінал або платформи обміну повідомленнями одразу, коли вони надходять, замість очікування повної відповіді.

### CLI Streaming

```yaml
display:
  streaming: true         # Stream tokens to terminal in real-time
  show_reasoning: true    # Also stream reasoning/thinking tokens (optional)
```

Коли увімкнено, відповіді з’являються токен‑за‑токеном у вікні стрімінгу. Виклики інструментів все ще захоплюються тихо. Якщо провайдер не підтримує стрімінг, автоматично відбувається відкат до звичайного відображення.

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

Коли увімкнено, бот надсилає повідомлення на першому токені, а потім поступово редагує його, коли надходять інші токени. Платформи, які не підтримують редагування повідомлень (Signal, Email, Home Assistant), автоматично визначаються під час першої спроби — стрімінг для такої сесії ввічливо вимикається без флуду повідомлень.

Для окремих природних оновлень асистента посеред діалогу без прогресивного редагування токенів встанови `display.interim_assistant_messages: true`.

**Обробка переповнення:** Якщо стрімінговий текст перевищує ліміт довжини повідомлення платформи (~4096 символів), поточне повідомлення завершується, і автоматично починається нове.

**Свіжий фінал (Telegram):** `editMessageText` у Telegram зберігає початковий час повідомлення, тому довготривала стрімінгова відповідь залишатиме час першого токена навіть після завершення. Коли `fresh_final_after_seconds > 0` (за замовчуванням `60`), завершена відповідь надсилається як нове повідомлення (з найкращою спробою видалити застарілий попередній перегляд), щоб видимий час у Telegram відповідав часу завершення. Короткі попередні перегляди все ще завершуються на місці. Встанови `0`, щоб завжди редагувати на місці.

:::note
Стрімінг вимкнено за замовчуванням. Увімкни його у `~/.hermes/config.yaml`, щоб спробувати UX стрімінгу.
:::
## Ізоляція сесій групового чату

Керуй тим, чи спільні чати зберігають одну розмову на кімнату чи одну розмову на учасника:

```yaml
group_sessions_per_user: true  # true = per-user isolation in groups/channels, false = one shared session per chat
```

- `true` — типове та рекомендоване налаштування. У каналах Discord, групах Telegram, каналах Slack та подібних спільних контекстах кожен відправник отримує свою **сесію**, коли платформа надає ідентифікатор користувача.
- `false` повертає стару поведінку спільної кімнати. Це може бути корисно, якщо ти явно хочеш, щоб Hermes розглядав канал як одну спільну розмову, але це також означає, що користувачі діляться контекстом, витратами токенів та станом переривань.
- Direct messages не змінюються. Hermes і надалі ідентифікує DMs за ID чату/DM, як зазвичай.
- Threads залишаються ізольованими від їх батьківського каналу в будь‑якому випадку; при `true` кожен учасник також отримує свою **сесію** всередині thread.

Для деталей поведінки та прикладів дивись [Sessions](/user-guide/sessions) та [Discord guide](/user-guide/messaging/discord).
## Неавторизована поведінка DM

Керуй тим, що робить Hermes, коли невідомий користувач надсилає пряме повідомлення:

```yaml
unauthorized_dm_behavior: pair

whatsapp:
  unauthorized_dm_behavior: ignore
```

- `pair` — значення за замовчуванням. Hermes відмовляє в доступі, але відповідає одноразовим кодом парування у DM.
- `ignore` — тихо ігнорує неавторизовані DM.
- Розділи платформи переважають глобальне значення за замовчуванням, тому можна залишити парування ввімкненим загалом, а для окремої платформи вимкнути його.
## Швидкі команди

Визначай власні команди, які або виконують shell‑команди без залучення LLM, або створюють псевдонім однієї slash‑команди до іншої. `exec`‑швидкі команди не споживають токени і корисні з платформ обміну повідомленнями (Telegram, Discord тощо) для швидкої перевірки серверу чи утилітних скриптів.

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

Використання: введи `/status`, `/disk`, `/update`, `/gpu` або `/restart` у CLI або будь‑якій платформі обміну повідомленнями. `exec`‑команди виконуються локально на хості і повертають вивід безпосередньо — без виклику LLM, без спожитих токенів. `alias`‑команди переписують у налаштовану ціль slash‑команди.

- **30‑секундний тайм‑аут** — довготривалі команди завершуються з повідомленням про помилку
- **Пріоритет** — швидкі команди перевіряються перед командами skill, тому ти можеш перевизначити назви skill
- **Автодоповнення** — швидкі команди розв’язуються під час диспетчеризації і не відображаються у вбудованих таблицях автодоповнення slash‑команд
- **Тип** — підтримувані типи: `exec` і `alias`; інші типи викликають помилку
- **Працює скрізь** — CLI, Telegram, Discord, Slack, WhatsApp, Signal, Email, Home Assistant

Швидкі команди, що складаються лише зі строк‑підказок, не є дійсними. Для багаторазових робочих процесів підказок створюй skill або alias до існуючої slash‑команди.
## Людська затримка

Simulate human-like response pacing in messaging platforms:

```yaml
human_delay:
  mode: "off"                  # off | natural | custom
  min_ms: 800                  # Minimum delay (custom mode)
  max_ms: 2500                 # Maximum delay (custom mode)
```
## Виконання коду

Налаштуй інструмент `execute_code`:

```yaml
code_execution:
  mode: project                # project (default) | strict
  timeout: 300                 # Max execution time in seconds
  max_tool_calls: 50           # Max tool calls within code execution
```

**`mode`** керує робочим каталогом та інтерпретатором Python для скриптів:

- **`project`** (за замовчуванням) — скрипти виконуються в робочому каталозі сесії з активним віртуальним або conda‑середовищем Python. Залежності проєкту (`pandas`, `torch`, пакети проєкту) та відносні шляхи (`.env`, `./data.csv`) розв’язуються природно, так само, як бачить їх `terminal()`.
- **`strict`** — скрипти виконуються в тимчасовому стейджинг‑каталозі з `sys.executable` (власний Python Hermes). Максимальна відтворюваність, проте залежності проєкту та відносні шляхи не будуть розв’язуватись.

Очищення середовища (видаляє `*_API_KEY`, `*_TOKEN`, `*_SECRET`, `*_PASSWORD`, `*_CREDENTIAL`, `*_PASSWD`, `*_AUTH`) та білий список інструментів застосовуються однаково в обох режимах — переключення режиму не змінює рівень безпеки.
## Web Search Backends

Інструменти `web_search` та `web_extract` підтримують п’ять провайдерів бекенду. Налаштуй бекенд у `config.yaml` або за допомогою `hermes tools`:

```yaml
web:
  backend: firecrawl    # firecrawl | searxng | parallel | tavily | exa

  # Or use per-capability keys to mix providers (e.g. free search + paid extract):
  search_backend: "searxng"
  extract_backend: "firecrawl"
```

| Backend | Env Var | Search | Extract |
|---------|---------|--------|---------|
| **Firecrawl** (default) | `FIRECRAWL_API_KEY` | ✔ | ✔ |
| **SearXNG** | `SEARXNG_URL` | ✔ | — |
| **Parallel** | `PARALLEL_API_KEY` | ✔ | ✔ |
| **Tavily** | `TAVILY_API_KEY` | ✔ | ✔ |
| **Exa** | `EXA_API_KEY` | ✔ | ✔ |

**Backend selection:** Якщо `web.backend` не встановлено, бекенд визначається автоматично за наявними API‑ключами. Якщо встановлено лише `SEARXNG_URL`, використовується SearXNG. Якщо встановлено лише `EXA_API_KEY`, використовується Exa. Якщо встановлено лише `TAVILY_API_KEY`, використовується Tavily. Якщо встановлено лише `PARALLEL_API_KEY`, використовується Parallel. В іншому випадку за замовчуванням використовується Firecrawl.

**SearXNG** — безкоштовний, самохостинг, що поважає приватність, метапошуковий движок, який запитує понад 70 пошукових систем. Ключ API не потрібен — просто встанови `SEARXNG_URL` на свою інстанцію (наприклад, `http://localhost:8080`). SearXNG працює лише для пошуку; `web_extract` потребує окремого провайдера екстракції (встанови `web.extract_backend`). Дивись [Web Search setup guide](/user-guide/features/web-search) для інструкцій щодо налаштування Docker.

**Self-hosted Firecrawl:** Встанови `FIRECRAWL_API_URL`, щоб вказати свою інстанцію. Коли задається власний URL, ключ API стає необов’язковим (встанови `USE_DB_AUTHENTICATION=*** on the server to disable auth`).

**Parallel search modes:** Встанови `PARALLEL_SEARCH_MODE`, щоб керувати поведінкою пошуку — `fast`, `one-shot` або `agentic` (за замовчуванням: `agentic`).

**Exa:** Встанови `EXA_API_KEY` у `~/.hermes/.env`. Підтримує фільтрацію за `category` (`company`, `research paper`, `news`, `people`, `personal site`, `pdf`) та фільтри за доменом/датою.
## Browser

Налаштуй поведінку автоматизації браузера:

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

**Політики діалогових вікон:**

- `must_respond` (за замовчуванням) — захоплює діалог, відображає його в `browser_snapshot.pending_dialogs` і чекає, поки агент викличе `browser_dialog(action=…)`. Після `dialog_timeout_s` секунд без відповіді діалог автоматично закривається, щоб запобігти зависанню JS‑потоку сторінки назавжди.
- `auto_dismiss` — захоплює, одразу закриває. Агент все одно бачить запис діалогу в `browser_snapshot.recent_dialogs` з `closed_by="auto_policy"` після цього.
- `auto_accept` — захоплює, одразу приймає. Корисно для сторінок з агресивними підказками `beforeunload`.

Дивись [browser feature page](./features/browser.md#browser_dialog) для повного опису робочого процесу діалогів.

Набір інструментів браузера підтримує кілька провайдерів. Дивись [Browser feature page](/user-guide/features/browser) для деталей щодо Browserbase, Browser Use та локального налаштування CDP сімейства Chromium.
## Часовий пояс

Перевизначити часовий пояс сервера за допомогою рядка IANA. Впливає на мітки часу в журналах, плануванні cron та ін’єкції часу в системний підказник.

```yaml
timezone: "America/New_York"   # IANA timezone (default: "" = server-local time)
```

Підтримувані значення: будь‑який ідентифікатор IANA (наприклад `America/New_York`, `Europe/London`, `Asia/Kolkata`, `UTC`). Залишити порожнім або опустити для локального часу сервера.
## Discord

Налаштуй специфічну для Discord поведінку шлюзу обміну повідомленнями:

```yaml
discord:
  require_mention: true          # Require @mention to respond in server channels
  free_response_channels: ""     # Comma-separated channel IDs where bot responds without @mention
  auto_thread: true              # Auto-create threads on @mention in channels
```

- `require_mention` — коли `true` (за замовчуванням), бот відповідає в каналах сервера лише за згадкою `@BotName`. У приватних повідомленнях (DM) відповідь завжди працює без згадки.
- `free_response_channels` — список ідентифікаторів каналів, розділений комами, у яких бот відповідає на кожне повідомлення без вимоги згадки.
- `auto_thread` — коли `true` (за замовчуванням), згадки в каналах автоматично створюють тему (thread) для розмови, підтримуючи чистоту каналів (подібно до потоків у Slack).
## Security

Pre‑execution security scanning and secret redaction:

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

- `redact_secrets` — коли `true`, автоматично виявляє та затирає шаблони, схожі на API‑ключі, токени та паролі у виводі інструменту, перш ніж вони потраплять у контекст розмови та журнали. **Вимкнено за замовчуванням** — увімкни, якщо часто працюєш з реальними обліковими даними у виводі інструменту і потрібна додаткова безпека. Встанови `true` явно, щоб увімкнути.
- `tirith_enabled` — коли `true`, команди терміналу сканує [Tirith](https://github.com/sheeki03/tirith) перед виконанням для виявлення потенційно небезпечних операцій.
- `tirith_path` — шлях до бінарного файлу tirith. Вкажи його, якщо tirith встановлений у нестандартному місці.
- `tirith_timeout` — максимальна кількість секунд очікування сканування tirith. Команди продовжують виконання, якщо сканування перевищує час.
- `tirith_fail_open` — коли `true` (за замовчуванням), команди дозволяються виконувати, якщо tirith недоступний або зазнає збою. Встанови `false`, щоб блокувати команди, коли tirith не може їх перевірити.
## Блокування сайтів

Блокуй конкретні домени, щоб агент не міг отримати до них доступ за допомогою веб‑ та браузерних інструментів:

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

Коли увімкнено, будь‑яка URL‑адреса, що відповідає шаблону заблокованого домену, відхиляється ще до виконання інструменту `web_search`, `web_extract`, `browser_navigate` та будь‑якого іншого інструменту, що працює з URL‑адресами.

Підтримуються правила доменів:
- Точні домени: `admin.example.com`
- Шаблони піддоменів: `*.internal.company.com` (блокує всі піддомени)
- Шаблони TLD: `*.local`

У спільних файлах міститься одне правило домену на рядок (порожні рядки та коментарі `#` ігноруються). Якщо файл відсутній або його не вдається прочитати, записується попередження, але інші веб‑інструменти не вимикаються.

Політика кешується протягом 30 секунд, тому зміни конфігурації набувають сили швидко, без перезапуску.
## Розумні схвалення

Керуй тим, як Hermes обробляє потенційно небезпечні команди:

```yaml
approvals:
  mode: manual   # manual | smart | off
```

| Mode | Behavior |
|------|----------|
| `manual` (default) | Запитувати користувача перед виконанням будь‑якої позначеної команди. У CLI показується інтерактивний діалог схвалення. У обміні повідомленнями команда ставиться в чергу як запит на схвалення. |
| `smart` | Використовувати допоміжний LLM для оцінки, чи є позначена команда дійсно небезпечною. Команди з низьким ризиком автоматично схвалюються з збереженням на рівні сесії. Справді ризиковані команди передаються користувачеві. |
| `off` | Пропускати всі перевірки схвалення. Еквівалентно `HERMES_YOLO_MODE=true`. **Використовуй обережно.** |

Режим `smart` особливо корисний для зменшення втоми від схвалень — він дозволяє агенту працювати автономніше на безпечних операціях, залишаючись при цьому здатним виявляти справді руйнівні команди.

:::warning
Встановлення `approvals.mode: off` вимикає всі перевірки безпеки для команд терміналу. Використовуй це лише в довірених, ізольованих середовищах.
:::
## Контрольні точки

Автоматичні знімки файлової системи перед руйнівними операціями над файлами. Дивись [Контрольні точки та відкат](/user-guide/checkpoints-and-rollback) для деталей.

```yaml
checkpoints:
  enabled: false                 # Enable automatic checkpoints (also: hermes chat --checkpoints). Default: false (opt-in).
  max_snapshots: 20              # Max checkpoints to keep per directory (default: 20)
```
## Делегування

Налаштуй поведінку підагентів для інструмента **delegate**:

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

**Перевизначення provider:model підагента:** За замовчуванням підагенти успадковують provider і model батьківського агента. Встанови `delegation.provider` і `delegation.model`, щоб направити підагенти до іншої пари provider:model — напр., використати дешеву/швидку модель для вузькоспеціалізованих підзадач, поки основний агент працює з дорогою моделлю розуміння.

**Пряме перевизначення кінцевої точки:** Якщо потрібен власний шлях до кінцевої точки, встанови `delegation.base_url`, `delegation.api_key` і `delegation.model`. Це надсилатиме підагенти безпосередньо до вказаної сумісної з OpenAI кінцевої точки і матиме пріоритет над `delegation.provider`. Якщо `delegation.api_key` не вказано, Hermes повернеться до `OPENAI_API_KEY` лише.

**Протокол передачі (`api_mode`):** Hermes автоматично визначає протокол передачі з `delegation.base_url` (наприклад, шляхи, що закінчуються на `/anthropic` → `anthropic_messages`; хости Codex / native Anthropic / Kimi‑coding зберігають своє існуюче визначення). Для кінцевих точок, які алгоритм не може класифікувати — наприклад Azure AI Foundry, MiniMax, Zhipu GLM або проксі LiteLLM, що фронтують бекенд у стилі Anthropic — встанови `delegation.api_mode` явно в один із `chat_completions`, `codex_responses` або `anthropic_messages`. Залиш його порожнім (за замовчуванням), щоб залишити авто‑виявлення.

Провайдер делегування використовує ту ж схему розв’язання облікових даних, що і запуск CLI/gateway. Підтримуються всі налаштовані провайдери: `openrouter`, `nous`, `copilot`, `zai`, `kimi-coding`, `minimax`, `minimax-cn`. Коли провайдер встановлено, система автоматично визначає правильний базовий URL, API‑ключ і режим API — без необхідності ручного підключення облікових даних.

**Пріоритет:** `delegation.base_url` у конфігурації → `delegation.provider` у конфігурації → провайдер батька (успадковано). `delegation.model` у конфігурації → модель батька (успадковано). Встановлення лише `model` без `provider` змінює лише назву моделі, залишаючи облікові дані батька (корисно для переключення моделей в межах одного провайдера, наприклад OpenRouter).

**Ширина та глибина:** `max_concurrent_children` обмежує кількість підагентів, що працюють паралельно в одному батчі (за замовчуванням `3`, мінімум 1, без верхньої межі). Можна також задати через змінну середовища `DELEGATION_MAX_CONCURRENT_CHILDREN`. Коли модель надсилає масив `tasks`, довший за ліміт, `delegate_task` повертає **помилку інструмента**, пояснюючи обмеження, замість тихого скорочення. `max_spawn_depth` контролює глибину дерева делегування (обмежено 1‑3). При значенні за замовчуванням `1` делегування плоске: діти не можуть породжувати онуків, а передача `role="orchestrator"` тихо переходить у `leaf`. Підвищення до `2` дозволяє дітям‑оркестратором породжувати онуків‑leaf; `3` — трирівневі дерева. Агент активує оркестрацію per call через `role="orchestrator"`; `orchestrator_enabled: false` змушує кожного дитину залишатися `leaf` незалежно. Вартість масштабується мультиплікативно — при `max_spawn_depth: 3` і `max_concurrent_children: 3` дерево може досягти 3×3×3 = 27 одночасних `leaf`‑агентів. Дивись [Subagent Delegation → Depth Limit and Nested Orchestration](features/delegation.md#depth-limit-and-nested-orchestration) для прикладів використання.
## Уточнити

Налаштуй поведінку запиту уточнення:

```yaml
clarify:
  timeout: 120                 # Seconds to wait for user clarification response
```
## Файли контексту (SOUL.md, AGENTS.md)

Hermes використовує два різних контекстних **області**:

| Файл | Призначення | Область |
|------|-------------|----------|
| `SOUL.md` | **Основна ідентичність агента** — визначає, хто такий агент (слот #1 у системному підказці) | `~/.hermes/SOUL.md` або `$HERMES_HOME/SOUL.md` |
| `.hermes.md` / `HERMES.md` | Проєктно‑специфічні інструкції (найвищий пріоритет) | Шлях до кореня git |
| `AGENTS.md` | Проєктно‑специфічні інструкції, конвенції кодування | Рекурсивний обхід каталогів |
| `CLAUDE.md` | Файли контексту Claude Code (також виявляються) | Тільки робочий каталог |
| `.cursorrules` | Правила Cursor IDE (також виявляються) | Тільки робочий каталог |
| `.cursor/rules/*.mdc` | Файли правил Cursor (також виявляються) | Тільки робочий каталог |

- **SOUL.md** — це основна ідентичність агента. Вона займає слот #1 у системному підказці, повністю замінюючи вбудовану типову ідентичність. Відредагуй її, щоб повністю налаштувати, хто такий агент.
- Якщо SOUL.md відсутній, порожній або не може бути завантажений, Hermes переходить до запасного варіанту — вбудованої типової ідентичності.
- **Файли контексту проєкту використовують систему пріоритетів** — завантажується лише один тип (перший збіг виграє): `.hermes.md` → `AGENTS.md` → `CLAUDE.md` → `.cursorrules`. SOUL.md завжди завантажується незалежно.
- **AGENTS.md** ієрархічний: якщо підкаталоги також містять AGENTS.md, вони всі комбінуються.
- Hermes автоматично створює типову `SOUL.md`, якщо її ще не існує.
- Всі завантажені файли контексту обмежені 20 000 символами зі смарт‑обрізанням.

Дивись також:
- [Personality & SOUL.md](/user-guide/features/personality)
- [Context Files](/user-guide/features/context-files)
## Робочий каталог

| Контекст | За замовчуванням |
|----------|------------------|
| **CLI (`hermes`)** | Поточний каталог, у якому ти запускаєш команду |
| **шлюз обміну повідомленнями** | Домашній каталог `~` (можна перевизначити за допомогою `MESSAGING_CWD`) |
| **Docker / Singularity / Modal / SSH** | Домашній каталог користувача всередині контейнера або віддаленої машини |

Перевизначити робочий каталог:
```bash
# In ~/.hermes/.env or ~/.hermes/config.yaml:
MESSAGING_CWD=/home/myuser/projects    # Gateway sessions
TERMINAL_CWD=/workspace                # All terminal sessions
```