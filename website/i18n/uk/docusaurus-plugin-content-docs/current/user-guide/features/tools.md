---
sidebar_position: 1
title: "Інструменти & набори інструментів"
description: "Огляд інструментів Hermes Agent — що доступно, як працюють набори інструментів та термінальні бекенди"
---

# Інструменти та набори інструментів

Інструменти — це функції, які розширюють можливості агента. Вони організовані в логічні **набори інструментів**, які можна вмикати або вимикати для кожної платформи.

## Доступні інструменти

Hermes постачається з широким вбудованим реєстром інструментів, що охоплює веб‑пошук, автоматизацію браузера, виконання команд у терміналі, редагування файлів, пам'ять, делегування, RL‑тренування, доставку повідомлень, Home Assistant та інше.

:::note
**Honcho cross‑session memory** доступна як плагін провайдера пам'яті (`plugins/memory/honcho/`), а не як вбудований набір інструментів. Дивись [Plugins](./plugins.md) для встановлення.
:::

Високорівневі категорії:

| Категорія | Приклади | Опис |
|----------|----------|------|
| **Web** | `web_search`, `web_extract` | Пошук в інтернеті та витяг вмісту сторінок. |
| **X Search** | `x_search` | Пошук постів і тем у X (Twitter) через вбудований інструмент `x_search` Responses від xAI — доступний лише за наявності облікових даних xAI (SuperGrok OAuth або `XAI_API_KEY`); вимкнено за замовчуванням, увімкнути можна через `hermes tools` → 🐦 X (Twitter) Search. |
| **Terminal & Files** | `terminal`, `process`, `read_file`, `patch` | Виконання команд і маніпуляція файлами. |
| **Browser** | `browser_navigate`, `browser_snapshot`, `browser_vision` | Інтерактивна автоматизація браузера з підтримкою тексту та зору. |
| **Media** | `vision_analyze`, `image_generate`, `video_generate`, `video_analyze`, `text_to_speech` | Багатомодальний аналіз та генерація. `video_generate` і `video_analyze` доступні за підключення (додай набори `video_gen` / `video` через `hermes tools` або `--toolsets`). |
| **Agent orchestration** | `todo`, `clarify`, `execute_code`, `delegate_task` | Планування, уточнення, виконання коду та делегування підагентам. |
| **Memory & recall** | `memory`, `session_search` | Постійна пам'ять та пошук у сесіях. |
| **Automation & delivery** | `cronjob`, `send_message` | Заплановані завдання з діями створення/перегляду/оновлення/паузи/відновлення/запуску/видалення, а також зовнішня доставка повідомлень. |
| **Integrations** | `ha_*`, MCP server tools, `rl_*` | Home Assistant, MCP, RL‑тренування та інші інтеграції. |

Для авторитетного реєстру, згенерованого з коду, дивись [Built-in Tools Reference](/reference/tools-reference) та [Toolsets Reference](/reference/toolsets-reference).

:::tip Nous Tool Gateway
Платні підписники [Nous Portal](https://portal.nousresearch.com) можуть користуватися веб‑пошуком, генерацією зображень, TTS та автоматизацією браузера через **[Tool Gateway](tool-gateway.md)** — без окремих API‑ключів. Запусти `hermes model`, щоб його ввімкнути, або налаштуй окремі інструменти за допомогою `hermes tools`.
:::

## Використання наборів інструментів

```bash
# Use specific toolsets
hermes chat --toolsets "web,terminal"

# See all available tools
hermes tools

# Configure tools per platform (interactive)
hermes tools
```

Типові набори інструментів включають `web`, `search`, `terminal`, `file`, `browser`, `vision`, `image_gen`, `moa`, `skills`, `tts`, `todo`, `memory`, `session_search`, `cronjob`, `code_execution`, `delegation`, `clarify`, `homeassistant`, `messaging`, `spotify`, `discord`, `discord_admin`, `debugging`, `safe` та `rl`.

Дивись [Toolsets Reference](/reference/toolsets-reference) для повного переліку, включаючи пресети платформ, такі як `hermes-cli`, `hermes-telegram`, і динамічні набори MCP, наприклад `mcp-<server>`.

## Термінальні бекенди

Інструмент `terminal` може виконувати команди у різних середовищах:

| Бекенд | Опис | Випадок використання |
|--------|------|-----------------------|
| `local` | Запуск на твоїй машині (за замовчуванням) | Розробка, довірені завдання |
| `docker` | Ізольовані контейнери | Безпека, відтворюваність |
| `ssh` | Віддалений сервер | Пісочниця, тримати агента подалі від його коду |
| `singularity` | HPC‑контейнери | Кластерні обчислення, без root‑прав |
| `modal` | Хмарне виконання | Serverless, масштабування |
| `daytona` | Хмарне робоче середовище | Постійні віддалені середовища розробки |

### Конфігурація

```yaml
# In ~/.hermes/config.yaml
terminal:
  backend: local    # or: docker, ssh, singularity, modal, daytona
  cwd: "."          # Working directory
  timeout: 180      # Command timeout in seconds
```

### Docker Backend

```yaml
terminal:
  backend: docker
  docker_image: python:3.11-slim
```

**Один постійний контейнер, спільний для всього процесу.** Hermes запускає один довгоживучий контейнер при першому використанні (`docker run -d … sleep 2h`) і направляє кожний виклик `terminal`, `file` та `execute_code` через `docker exec` у той самий контейнер. Зміни робочого каталогу, встановлені пакети, налаштування середовища та файли, записані у `/workspace`, зберігаються між викликами інструментів, між `/new`, `/reset` та підагентами `delegate_task` протягом усього часу роботи процесу Hermes. Контейнер зупиняється і видаляється при завершенні роботи.

Тобто бекенд Docker поводиться як постійна пісочниця‑VM, а не як новий контейнер для кожної команди. Якщо ти один раз виконаєш `pip install foo`, пакет залишиться на весь залишок сесії. Якщо ти перейдеш у `cd /workspace/project`, наступні виклики `ls` побачать цей каталог. Дивись [Configuration → Docker Backend](../configuration.md#docker-backend) для повного опису життєвого циклу та прапорця `container_persistent`, який керує тим, чи зберігаються `/workspace` і `/root` між перезапусками Hermes.

### SSH Backend

Рекомендовано для безпеки — агент не може змінювати власний код:

```yaml
terminal:
  backend: ssh
```
```bash
# Set credentials in ~/.hermes/.env
TERMINAL_SSH_HOST=my-server.example.com
TERMINAL_SSH_USER=myuser
TERMINAL_SSH_KEY=~/.ssh/id_rsa
```

### Singularity/Apptainer

```bash
# Pre-build SIF for parallel workers
apptainer build ~/python.sif docker://python:3.11-slim

# Configure
hermes config set terminal.backend singularity
hermes config set terminal.singularity_image ~/python.sif
```

### Modal (Serverless Cloud)

```bash
uv pip install modal
modal setup
hermes config set terminal.backend modal
```

### Ресурси контейнера

Налаштуй CPU, пам'ять, диск та стійкість для всіх контейнерних бекендів:

```yaml
terminal:
  backend: docker  # or singularity, modal, daytona
  container_cpu: 1              # CPU cores (default: 1)
  container_memory: 5120        # Memory in MB (default: 5GB)
  container_disk: 51200         # Disk in MB (default: 50GB)
  container_persistent: true    # Persist filesystem across sessions (default: true)
```

Коли `container_persistent: true`, встановлені пакети, файли та конфігурації зберігаються між сесіями.

### Безпека контейнера

Усі контейнерні бекенди працюють з жорстким посиленням безпеки:

- Файлова система кореня лише для читання (Docker)
- Всі Linux‑можливості вимкнено
- Без підвищення привілеїв
- Обмеження PID (256 процесів)
- Повна ізоляція простору імен
- Постійна робоча область через томи, а не записувальний кореневий шар

Docker може отримати явний список дозволених змінних середовища через `terminal.docker_forward_env`, проте передані змінні видимі всередині контейнера і повинні розглядатися як відкриті для цієї сесії.

## Управління фоновими процесами

Запуск фонових процесів та їх керування:

```python
terminal(command="pytest -v tests/", background=true)
# Returns: {"session_id": "proc_abc123", "pid": 12345}

# Then manage with the process tool:
process(action="list")       # Show all running processes
process(action="poll", session_id="proc_abc123")   # Check status
process(action="wait", session_id="proc_abc123")   # Block until done
process(action="log", session_id="proc_abc123")    # Full output
process(action="kill", session_id="proc_abc123")   # Terminate
process(action="write", session_id="proc_abc123", data="y")  # Send input
```

Режим PTY (`pty=true`) вмикає інтерактивні CLI‑інструменти, такі як Codex та Claude Code.

## Підтримка sudo

Якщо команда потребує sudo, тебе буде запитано пароль (кешується на час сесії). Або встанови `SUDO_PASSWORD` у `~/.hermes/.env`.

:::warning
На платформах обміну повідомленнями, якщо sudo не вдається, у виводі є підказка додати `SUDO_PASSWORD` у `~/.hermes/.env`.
:::