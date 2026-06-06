---
sidebar_position: 3
title: "Обновление и удаление"
description: "Как обновить Hermes Agent до последней версии или удалить его"
---

# Обновление и удаление

## Обновление

### Установки через Git

Обнови до последней версии одной командой:

```bash
hermes update
```

Это вытягивает последний код из `main`, обновляет зависимости и предлагает настроить новые параметры, добавленные с момента последнего обновления.

### Установки через pip

Релизы на PyPI отслеживают **тегированные версии** (мажорные и минорные релизы), а не каждый коммит в `main`. Проверь наличие обновлений и обнови с помощью:

```bash
hermes update --check    # see if a newer release is on PyPI
hermes update            # runs pip install --upgrade hermes-agent
```

Или вручную:

```bash
pip install --upgrade hermes-agent    # or: uv pip install --upgrade hermes-agent
```

:::tip
`hermes update` автоматически обнаруживает новые параметры конфигурации и предлагает их добавить. Если ты пропустил этот запрос, можешь вручную выполнить `hermes config check`, чтобы увидеть недостающие параметры, а затем `hermes config migrate` для интерактивного добавления.
:::

### Что происходит во время обновления (установки через Git)

Когда ты запускаешь `hermes update`, выполняются следующие шаги:

1. **Снимок данных сопряжения** — сохраняется лёгкий предобновительный снимок состояния (охватывает `~/.hermes/pairing/`, правила комментариев Feishu и другие файлы состояния, изменяемые во время работы). Восстанавливается через процесс восстановления снимка, описанный в разделе [Snapshots and rollback](../user-guide/checkpoints-and-rollback.md), или путём извлечения последнего zip‑файла быстрого снимка, который Hermes записал рядом с каталогом `~/.hermes/`.
2. **Git pull** — вытягивает последний код из ветки `main` и обновляет подмодули.
3. **Проверка синтаксиса после pull + автооткат** — после вытягивания Hermes компилирует восемь критических файлов, которые импортируются при каждом запуске `hermes`. Если какой‑то файл не удаётся разобрать (например, оставшийся маркер конфликта слияния или случайно усечённый файл), Hermes выполняет `git reset --hard <pre-pull-sha>`, откатывая установку, чтобы твоя оболочка оставалась работоспособной. Затем запусти `hermes update` снова, когда исправление появится в upstream.
4. **Установка зависимостей** — запускает `uv pip install -e ".[all]"`, чтобы подобрать новые или изменённые зависимости.
5. **Миграция конфигурации** — обнаруживает новые параметры, добавленные с твоей версии, и предлагает их задать.
6. **Автоматический перезапуск шлюза** — работающие шлюзы обновляются после завершения обновления, чтобы новый код вступил в силу сразу. Шлюзы, управляемые сервисом (systemd в Linux, launchd в macOS), перезапускаются через менеджер сервисов. Ручные шлюзы перезапускаются автоматически, когда Hermes может сопоставить работающий PID с профилем.

### Обновление из ветки, отличной от основной: `--branch`

По умолчанию `hermes update` отслеживает `origin/main`. Передай `--branch <name>`, чтобы обновиться из другой ветки — удобно для QA‑каналов, веток функций или тестирования релиз‑кандидатов:

```bash
hermes update --branch release-candidate
hermes update --check --branch experimental   # preview behindness only
```

Если твой локальный checkout находится в другой ветке, Hermes автоматически сохраняет любые несохранённые изменения, переключает HEAD на целевую ветку и затем делает pull. Ветки, которых нет локально, автоматически отслеживаются из `origin/<name>` (`git checkout -B <name> origin/<name>`). Ветки, которые не существуют нигде, завершаются с ошибкой — твои сохранённые изменения восстанавливаются перед выходом, так что ты никогда не останешься в странном состоянии. Логика синхронизации только с `main` автоматически пропускается для веток, отличных от `main`.

### Только проверка: `hermes update --check`

Хочешь узнать, доступно ли обновление, прежде чем тянуть? Запусти `hermes update --check` — для установок через Git он получает и сравнивает коммиты с `origin/main`; для установок через pip он запрашивает PyPI последнюю версию. Файлы не меняются, шлюз не перезапускается. Полезно в скриптах и cron‑задачах, которые проверяют «есть ли обновление».

### Полный предобновительный бэкап: `--backup`

Для ценных профилей (продакшн‑шлюзы, совместные установки команд) можно включить полное пред‑pull резервное копирование `HERMES_HOME` (конфигурация, аутентификация, сессии, инструменты, сопряжение):

```bash
hermes update --backup
```

Или сделать его поведением по умолчанию для каждого запуска:

```yaml
# ~/.hermes/config.yaml
updates:
  pre_update_backup: true
```

`--backup` был включён по умолчанию в ранних сборках, но замедлял обновления больших домов, поэтому теперь он опционален. Лёгкий снимок данных сопряжения всё равно выполняется безусловно.

### Windows: запущен другой `hermes.exe`

В Windows `hermes update` откажется запускаться, если обнаружит другой процесс `hermes.exe`, удерживающий исполняемый файл виртуального окружения открытым — чаще всего это запущенный бекенд Hermes Desktop, открытый REPL `hermes` в другом терминале или работающий шлюз:

```
$ hermes update
✗ Another hermes.exe is running:
    PID 12345  hermes.exe

  Updating now would fail to overwrite ...\venv\Scripts\hermes.exe because
  Windows blocks REPLACE on a running executable.

  Close Hermes Desktop, exit any open `hermes` REPLs, and
  stop the gateway (`hermes gateway stop`) before retrying.
  Override with `hermes update --force` if you've already
  confirmed those processes will not write to the venv.
```

Закрой перечисленные процессы и запусти снова. Если ты уверен, что параллельный процесс не помешает (редко — обычно только когда антивирус ошибочно блокирует файл), передай `--force`, чтобы пропустить проверку. В этом случае обновлятор всё равно будет пытаться переименовать `.exe` с экспоненциальным бэкофом и, при упорных блокировках, запланирует замену на следующую перезагрузку через `MoveFileEx(MOVEFILE_DELAY_UNTIL_REBOOT)`, чтобы обновление завершилось.

Ожидаемый вывод выглядит так:

```
$ hermes update
Updating Hermes Agent...
📥 Pulling latest code...
Already up to date.  (or: Updating abc1234..def5678)
📦 Updating dependencies...
✅ Dependencies updated
🔍 Checking for new config options...
✅ Config is up to date  (or: Found 2 new options — running migration...)
🔄 Restarting gateways...
✅ Gateway restarted
✅ Hermes Agent updated successfully!
```

### Рекомендованная проверка после обновления

`hermes update` обрабатывает основной путь обновления, но быстрая проверка подтверждает, что всё установилось корректно:

1. `git status --short` — если дерево неожиданно грязное, проверь изменения перед продолжением.
2. `hermes doctor` — проверяет конфигурацию, зависимости и состояние сервисов.
3. `hermes --version` — убедись, что версия увеличилась как ожидалось.
4. Если ты используешь шлюз: `hermes gateway status`.
5. Если `doctor` сообщает о проблемах `npm audit`: запусти `npm audit fix` в указанном каталоге.

:::warning Dirty working tree after update
Если `git status --short` показывает неожиданные изменения после `hermes update`, остановись и изучи их перед продолжением. Обычно это значит, что локальные модификации были повторно применены поверх обновлённого кода, или шаг зависимости обновил lock‑файлы.
:::

### Если терминал отключился во время обновления

`hermes update` защищает себя от случайной потери терминала:

- Обновление игнорирует `SIGHUP`, поэтому закрытие SSH‑сессии или окна терминала больше не прерывает его посередине. Дочерние процессы `pip` и `git` наследуют эту защиту, так что Python‑окружение не останется полупоставленным из‑за разорванного соединения.
- Весь вывод дублируется в `~/.hermes/logs/update.log` во время выполнения обновления. Если твой терминал исчез, подключись снова и проверь лог, чтобы увидеть, завершилось ли обновление и прошёл ли перезапуск шлюза:

```bash
tail -f ~/.hermes/logs/update.log
```

- `Ctrl‑C` (SIGINT) и выключение системы (SIGTERM) всё ещё обрабатываются — это намеренные отмены, а не случайные.

Тебе больше не нужно оборачивать `hermes update` в `screen` или `tmux`, чтобы пережить падение терминала.

### Проверка текущей версии

```bash
hermes version
```

Сравни её с последним релизом на странице [GitHub releases page](https://github.com/NousResearch/hermes-agent/releases).

### Обновление из мессенджеров

Можно также обновить напрямую из Telegram, Discord, Slack, WhatsApp или Teams, отправив:

```
/update
```

Это вытягивает последний код, обновляет зависимости и перезапускает работающие шлюзы. Бот будет недоступен на короткое время во время перезапуска (обычно 5–15 секунд), а затем продолжит работу.

### Ручное обновление

Если ты установил вручную (не через быстрый установщик):

```bash
cd /path/to/hermes-agent
export VIRTUAL_ENV="$(pwd)/venv"

# Pull latest code
git pull origin main

# Reinstall (picks up new dependencies)
uv pip install -e ".[all]"

# Check for new config options
hermes config check
hermes config migrate   # Interactively add any missing options
```

### Инструкции по откату

Если обновление принесло проблему, можешь откатиться к предыдущей версии:

```bash
cd /path/to/hermes-agent

# List recent versions
git log --oneline -10

# Roll back to a specific commit
git checkout <commit-hash>
git submodule update --init --recursive
uv pip install -e ".[all]"

# Restart the gateway if running
hermes gateway restart
```

Чтобы откатиться к конкретному тегу релиза (подставь свой предыдущий тег — например, недавний релиз `v2026.5.16` или любой более ранний тег из `git tag --sort=-version:refname`):

```bash
git checkout vX.Y.Z
git submodule update --init --recursive
uv pip install -e ".[all]"
```

:::warning
Откат может вызвать несовместимости конфигурации, если были добавлены новые параметры. После отката запусти `hermes config check` и удали любые неизвестные параметры из `config.yaml`, если возникнут ошибки.
:::

### Примечание для пользователей Nix

Если ты установил через Nix flake, обновления управляются менеджером пакетов Nix:

```bash
# Update the flake input
nix flake update hermes-agent

# Or rebuild with the latest
nix profile upgrade hermes-agent
```

Установки Nix неизменяемы — откат осуществляется системой генераций Nix:

```bash
nix profile rollback
```

Смотри [Nix Setup](./nix-setup.md) для подробностей.

---

## Удаление

### Установки через Git

```bash
hermes uninstall
```

Деинсталлятор предлагает сохранить файлы конфигурации (`~/.hermes/`) для будущей переустановки.

### Установки через pip

```bash
pip uninstall hermes-agent
rm -rf ~/.hermes            # Optional — keep if you plan to reinstall
```

### Ручное удаление

```bash
rm -f ~/.local/bin/hermes
rm -rf /path/to/hermes-agent
rm -rf ~/.hermes            # Optional — keep if you plan to reinstall
```

:::info
Если ты установил шлюз как системный сервис, сначала останови и отключи его:
```bash
hermes gateway stop
# Linux: systemctl --user disable hermes-gateway
# macOS: launchctl remove ai.hermes.gateway
```
:::