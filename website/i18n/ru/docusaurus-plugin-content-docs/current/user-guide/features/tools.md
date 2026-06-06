---
sidebar_position: 1
title: "Инструменты & Инструменты"
description: "Обзор инструментов Hermes Agent — что доступно, как работают наборы инструментов и терминальные бэкенды"
---

# Инструменты и наборы инструментов

Инструменты — это функции, расширяющие возможности агента. Они организованы в логические **наборы инструментов**, которые можно включать или отключать для каждой платформы.

## Доступные инструменты

Hermes поставляется с широким встроенным реестром инструментов, охватывающим веб‑поиск, автоматизацию браузера, выполнение команд в терминале, редактирование файлов, память, делегирование, обучение с подкреплением, доставку сообщений, Home Assistant и многое другое.

:::note
**Honcho cross‑session memory** доступна как плагин провайдера памяти (`plugins/memory/honcho/`), а не как встроенный набор инструментов. См. раздел [Plugins](./plugins.md) для установки.
:::

Высокоуровневые категории:

| Категория | Примеры | Описание |
|----------|----------|----------|
| **Web** | `web_search`, `web_extract` | Поиск в интернете и извлечение содержимого страниц. |
| **X Search** | `x_search` | Поиск постов и веток в X (Twitter) через встроенный инструмент `x_search` от xAI — требует учётных данных xAI (SuperGrok OAuth или `XAI_API_KEY`); отключён по умолчанию, включается через `hermes tools` → 🐦 X (Twitter) Search. |
| **Terminal & Files** | `terminal`, `process`, `read_file`, `patch` | Выполнение команд и работа с файлами. |
| **Browser** | `browser_navigate`, `browser_snapshot`, `browser_vision` | Интерактивная автоматизация браузера с поддержкой текста и зрения. |
| **Media** | `vision_analyze`, `image_generate`, `video_generate`, `video_analyze`, `text_to_speech` | Мультимодальный анализ и генерация. `video_generate` и `video_analyze` включаются по желанию (добавьте наборы `video_gen` / `video` через `hermes tools` или `--toolsets`). |
| **Agent orchestration** | `todo`, `clarify`, `execute_code`, `delegate_task` | Планирование, уточнение, выполнение кода и делегирование субагентам. |
| **Memory & recall** | `memory`, `session_search` | Постоянная память и поиск по сессии. |
| **Automation & delivery** | `cronjob`, `send_message` | Планирование задач с действиями create / list / update / pause / resume / run / remove, а также отправка сообщений. |
| **Integrations** | `ha_*`, MCP server tools, `rl_*` | Home Assistant, MCP, обучение с подкреплением и другие интеграции. |

Для официального реестра, полученного из кода, см. [Built-in Tools Reference](/reference/tools-reference) и [Toolsets Reference](/reference/toolsets-reference).

:::tip Nous Tool Gateway
Платные подписчики [Nous Portal](https://portal.nousresearch.com) могут использовать веб‑поиск, генерацию изображений, TTS и автоматизацию браузера через **[Tool Gateway](tool-gateway.md)** — без отдельных API‑ключей. Запусти `hermes model`, чтобы включить его, или настрой отдельные инструменты с помощью `hermes tools`.
:::

## Использование наборов инструментов

```bash
# Use specific toolsets
hermes chat --toolsets "web,terminal"

# See all available tools
hermes tools

# Configure tools per platform (interactive)
hermes tools
```

Распространённые наборы инструментов включают `web`, `search`, `terminal`, `file`, `browser`, `vision`, `image_gen`, `moa`, `skills`, `tts`, `todo`, `memory`, `session_search`, `cronjob`, `code_execution`, `delegation`, `clarify`, `homeassistant`, `messaging`, `spotify`, `discord`, `discord_admin`, `debugging`, `safe` и `rl`.

Смотрите [Toolsets Reference](/reference/toolsets-reference) для полного списка, включая предустановки платформ, такие как `hermes-cli`, `hermes-telegram`, и динамические наборы MCP, например `mcp-<server>`.

## Терминальные бекэнды

Инструмент терминала может выполнять команды в разных окружениях:

| Бекенд | Описание | Сценарий использования |
|--------|----------|------------------------|
| `local` | Запуск на твоём компьютере (по умолчанию) | Разработка, доверенные задачи |
| `docker` | Изолированные контейнеры | Безопасность, воспроизводимость |
| `ssh` | Удалённый сервер | Песочница, защита кода агента |
| `singularity` | HPC‑контейнеры | Кластерные вычисления, без root‑прав |
| `modal` | Облачное выполнение | Serverless, масштабирование |
| `daytona` | Облачное рабочее пространство | Постоянные удалённые среды разработки |

### Конфигурация

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

**Один постоянный контейнер, общий для всего процесса.** Hermes запускает один длительно живущий контейнер при первом использовании (`docker run -d ... sleep 2h`) и направляет каждый вызов терминала, файлов и `execute_code` через `docker exec` в тот же контейнер. Изменения рабочей директории, установленные пакеты, настройки окружения и файлы в `/workspace` сохраняются между вызовами инструмента, включая `/new`, `/reset` и субагенты `delegate_task`, на протяжении жизни процесса Hermes. При завершении процесс останавливает и удаляет контейнер.

Это значит, что бекенд Docker работает как постоянная изолированная VM, а не как новый контейнер для каждой команды. Если выполнить `pip install foo` один раз, пакет будет доступен до конца сессии. Если выполнить `cd /workspace/project`, последующие вызовы `ls` увидят эту директорию. См. [Configuration → Docker Backend](../configuration.md#docker-backend) для полного описания жизненного цикла и флага `container_persistent`, контролирующего сохранение `/workspace` и `/root` между перезапусками Hermes.

### SSH Backend

Рекомендуется для безопасности — агент не может изменять свой собственный код:

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

### Ресурсы контейнера

Настройка CPU, памяти, диска и постоянства для всех контейнерных бекэндов:

```yaml
terminal:
  backend: docker  # or singularity, modal, daytona
  container_cpu: 1              # CPU cores (default: 1)
  container_memory: 5120        # Memory in MB (default: 5GB)
  container_disk: 51200         # Disk in MB (default: 50GB)
  container_persistent: true    # Persist filesystem across sessions (default: true)
```

Когда `container_persistent: true`, установленные пакеты, файлы и конфигурации сохраняются между сессиями.

### Безопасность контейнера

Все контейнерные бекэнды работают с усиленной безопасностью:

- Файловая система корня только для чтения (Docker)
- Отключены все Linux‑capabilities
- Запрещено повышение привилегий
- Ограничения PID (256 процессов)
- Полная изоляция пространств имён
- Постоянное рабочее пространство через тома, а не через записываемый слой корня

Docker может получать явный список разрешённых переменных окружения через `terminal.docker_forward_env`, но переданные переменные видны внутри контейнера и считаются раскрытыми для этой сессии.

## Управление фоновыми процессами

Запуск фоновых процессов и их управление:

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

Режим PTY (`pty=true`) включает интерактивные CLI‑инструменты, такие как Codex и Claude Code.

## Поддержка sudo

Если команда требует sudo, будет запрошен пароль (кешируется на время сессии). Либо задайте `SUDO_PASSWORD` в `~/.hermes/.env`.

:::warning
На платформах обмена сообщениями, если sudo не удаётся, вывод содержит подсказку добавить `SUDO_PASSWORD` в `~/.hermes/.env`.
:::