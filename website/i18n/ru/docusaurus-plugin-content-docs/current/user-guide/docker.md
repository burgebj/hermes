---
sidebar_position: 7
title: "Docker"
description: "Запуск Hermes Agent в Docker и использование Docker в качестве терминального бэкенда"
---

# Hermes Agent — Docker

Существует два разных способа взаимодействия Docker с Hermes Agent:

1. **Running Hermes **IN Docker** — агент сам работает внутри контейнера (это основной фокус данной страницы)
2. **Docker как бекенд терминала** — агент работает на твоём хосте, но каждый командный вызов выполняется внутри единственного, постоянного контейнера‑песочницы Docker, который сохраняется между вызовами инструментов, `/new` и субагентами на протяжении всего процесса Hermes (см. [Configuration → Docker Backend](./configuration.md#docker-backend))

Эта страница описывает вариант 1. Контейнер хранит все пользовательские данные (config, API keys, sessions, skills, memories) в едином каталоге, смонтированном с хоста в `/opt/data`. Сам образ является безсостоянием и может быть обновлён путём загрузки новой версии без потери какой‑либо конфигурации.
## Быстрый старт

Если ты запускаешь Hermes Agent впервые, создай каталог данных на хосте и запусти контейнер в интерактивном режиме, чтобы пройти мастер настройки:

```sh
mkdir -p ~/.hermes
docker run -it --rm \
  -v ~/.hermes:/opt/data \
  nousresearch/hermes-agent setup
```

Это откроет мастер настройки, который запросит твои API‑ключи и запишет их в `~/.hermes/.env`. Делать это нужно только один раз. Настоятельно рекомендуется на этом этапе настроить систему чата, с которой будет работать gateway.

:::tip
Внутри контейнера выполни `hermes setup --portal` один раз — refresh‑токен сохраняется в смонтированном томе `~/.hermes`. См. [Nous Portal](/integrations/nous-portal).
:::
## Запуск в режиме шлюза

После настройки запусти контейнер в фоне как постоянный шлюз (Telegram, Discord, Slack, WhatsApp и т.д.):

```sh
docker run -d \
  --name hermes \
  --restart unless-stopped \
  -v ~/.hermes:/opt/data \
  -p 8642:8642 \
  nousresearch/hermes-agent gateway run
```

Порт 8642 открывает [OpenAI‑совместимый API‑сервер шлюза](./features/api-server.md) и эндпоинт состояния. Это необязательно, если ты используешь только чат‑платформы (Telegram, Discord и т.п.), но требуется, если нужен дашборд или внешние инструменты, которым нужно обращаться к шлюзу.

:::tip Шлюз работает под наблюдением
В официальном Docker‑образе `gateway run` **автоматически контролируется s6‑overlay**: если процесс шлюза падает, он перезапускается через пару секунд без потери контейнера, а дашборд (когда установлен `HERMES_DASHBOARD=1`) контролируется вместе с ним. Сам процесс `gateway run` в CMD представляет собой `sleep infinity`‑heartbeat, который держит контейнер живым, пока s6 управляет реальным процессом шлюза — поэтому `docker stop` всё равно корректно останавливает всё, а `docker logs` показывает вывод контролируемого шлюза.

Ты увидишь однострочное сообщение в `docker logs`, подтверждающее обновление. Чтобы отказаться от контроля — и получить историческое поведение «gateway — главный процесс контейнера, выход контейнера = выход шлюза» — передай `--no-supervise` или установи `HERMES_GATEWAY_NO_SUPERVISE=1`. Отказ полезен для CI‑тестов, где нужен выход контейнера с кодом статуса шлюза; для продакшн‑развёртываний контролируемый вариант по‑умолчанию однозначно лучше.

Это поведение относится только к образу на базе s6. Более ранние (на базе tini) образы всё ещё запускают `gateway run` как основной процесс в переднем плане.
:::

:::note Куда идут логи шлюза
Смотри раздел [Where the logs go](#where-the-logs-go) ниже для полной карты маршрутизации (шлюзы per‑profile, дашборд, reconciler при загрузке, `docker logs` контейнера в целом).
:::

Примечание: API‑сервер включён только при `API_SERVER_ENABLED=true`. Чтобы открыть его за пределами `127.0.0.1` внутри контейнера, также установи `API_SERVER_HOST=0.0.0.0` и `API_SERVER_KEY` (минимум 8 символов — сгенерируй его с помощью `openssl rand -hex 32`). Пример:

```sh
docker run -d \
  --name hermes \
  --restart unless-stopped \
  -v ~/.hermes:/opt/data \
  -p 8642:8642 \
  -e API_SERVER_ENABLED=true \
  -e API_SERVER_HOST=0.0.0.0 \
  -e API_SERVER_KEY="$(openssl rand -hex 32)" \
  -e API_SERVER_CORS_ORIGINS='*' \
  nousresearch/hermes-agent gateway run
```

Открытие любого порта на машине, доступной из интернета, представляет собой риск безопасности. Делать это следует только при полном понимании этих рисков.
## Запуск дашборда

Встроенный веб‑дашборд работает как контролируемый сервис s6‑rc рядом с gateway в том же контейнере. Установи `HERMES_DASHBOARD=1`, чтобы запустить его:

```sh
docker run -d \
  --name hermes \
  --restart unless-stopped \
  -v ~/.hermes:/opt/data \
  -p 8642:8642 \
  -p 9119:9119 \
  -e HERMES_DASHBOARD=1 \
  nousresearch/hermes-agent gateway run
```

Дашборд контролируется s6 — если он падает, `s6-supervise` автоматически перезапускает его после короткой паузы. stdout/stderr дашборда перенаправляются в `docker logs <container>` (без префикса; собственный вывод шлюза теперь записывается в отдельный s6‑log‑файл для каждого профиля — см. [Where the logs go](#where-the-logs-go) ниже — поэтому два потока не конфликтуют).

| Переменная окружения | Описание | По умолчанию |
|-----------------------|----------|--------------|
| `HERMES_DASHBOARD` | Установи `1` (или `true` / `yes`), чтобы включить контролируемый сервис дашборда | *(не задано — сервис зарегистрирован, но не запущен)* |
| `HERMES_DASHBOARD_HOST` | Адрес привязки HTTP‑сервера дашборда | `0.0.0.0` |
| `HERMES_DASHBOARD_PORT` | Порт HTTP‑сервера дашборда | `9119` |
| `HERMES_DASHBOARD_TUI` | Установи `1`, чтобы открыть вкладку **Chat** в браузере (встроенный `hermes --tui` через PTY/WebSocket) | *(не задано)* |
| `HERMES_DASHBOARD_INSECURE` | Установи `1` (или `true` / `yes`), чтобы привязываться без OAuth‑gate. Используй только в надёжных сетях за обратным прокси без OAuth‑контракта — дашборд раскрывает API‑ключи и данные сессии | *(не задано — gate включён, когда зарегистрирован `DashboardAuthProvider`)* |

Внутри контейнера дашборд по умолчанию привязывается к `0.0.0.0` — без этого опубликованный порт `-p 9119:9119` был бы недоступен с хоста. Чтобы ограничить привязку только loopback контейнера (для sidecar / reverse‑proxy‑конфигураций), задай `HERMES_DASHBOARD_HOST=127.0.0.1`.

OAuth‑gate дашборда включается автоматически, когда одновременно выполнены оба условия:

1. Хост привязки не является loopback (например, значение по умолчанию `0.0.0.0` внутри контейнера), **и**
2. Зарегистрирован плагин `DashboardAuthProvider`.

Встроенный провайдер `dashboard_auth/nous` активируется, когда задана переменная `HERMES_DASHBOARD_OAUTH_CLIENT_ID` (см. [Web Dashboard → Authentication](features/web-dashboard.md)). При включённом gate браузерные запросы перенаправляются на OAuth‑поток настроенного портала, прежде чем они смогут попасть на любой защищённый маршрут.

Если провайдер не зарегистрирован и привязка не является loopback, дашборд **завершается с ошибкой при старте**, указывая на отсутствие требуемой переменной окружения. Чтобы явно отключить gate — для развертывания в надёжной LAN‑сети за собственным обратным прокси без OAuth‑контракта — задай `HERMES_DASHBOARD_INSECURE=1`. Это **единственный** способ отключить gate; сам хост привязки никогда не подразумевает `--insecure` (ранее так было, но это предшествовало OAuth‑gate и молча отключало его для каждого дашборда в контейнере).

:::warning `HERMES_DASHBOARD_INSECURE=1` раскрывает API‑ключи
Отключение OAuth‑gate делает доступным API дашборда (включая ключи моделей и данные сессий) для любого, кто может достичь опубликованного порта. Включай его только если у тебя есть собственный слой аутентификации перед дашбордом, либо в надёжной LAN‑сети, которой ты полностью управляешь.
:::

Запуск дашборда в отдельном контейнере не поддерживается: его механизм обнаружения живости шлюза требует совместного PID‑пространства с процессом шлюза.
## Запуск в интерактивном режиме (CLI‑чат)

Чтобы открыть интерактивную чат‑сессию для запущенного каталога данных:

```sh
docker run -it --rm \
  -v ~/.hermes:/opt/data \
  nousresearch/hermes-agent
```

Или, если ты уже открыл терминал в работающем контейнере (например, через Docker Desktop), просто выполни:

```sh
/opt/hermes/.venv/bin/hermes
```
## Persistent volumes

Том `/opt/data` — единственный источник правды для всего состояния Hermes. Он отображается в каталог `~/.hermes/` твоего хоста и содержит:

| Path | Contents |
|------|----------|
| `.env` | API‑ключи и секреты |
| `config.yaml` | Вся конфигурация Hermes |
| `SOUL.md` | Личность/идентичность агента |
| `sessions/` | История разговоров |
| `memories/` | Хранилище постоянной памяти |
| `skills/` | Установленные skills |
| `home/` | HOME‑каталог для каждого профиля subprocess‑ов Hermes (`git`, `ssh`, `gh`, `npm` и CLI skills) |
| `cron/` | Определения запланированных задач |
| `hooks/` | Event hooks |
| `logs/` | Runtime logs |
| `skins/` | Пользовательские CLI‑скины |

CLI skills, которые сохраняют учётные данные в `~`, должны инициализироваться относительно HOME‑каталога subprocess‑а, а не только корня тома данных. Например, навык [xurl skill](./skills/bundled/social-media/social-media-xurl.md) сохраняет состояние OAuth в `~/.xurl`; в официальной Docker‑структуре вызовы инструментов Hermes читают его как `/opt/data/home/.xurl`, поэтому выполни ручную аутентификацию xurl с `HOME=/opt/data/home` и проверь статус с `HOME=/opt/data/home xurl auth status`.

:::warning
Никогда не запускай два контейнера Hermes **gateway** одновременно, используя один и тот же каталог данных — файлы сессий и хранилища памяти не предназначены для одновремённого доступа на запись.
:::
## Поддержка нескольких профилей

Hermes поддерживает [множество профилей](../reference/profile-commands.md) — отдельные подкаталоги `~/.hermes/`, позволяющие запускать независимые агенты (разные SOUL, навыки, память, сессии, учётные данные) из одной установки. **В официальном Docker‑образе дерево надзора s6 рассматривает каждый профиль как полноценный контролируемый сервис**, поэтому рекомендуется развертывать **один контейнер, содержащий все профили**.

Каждый профиль, созданный командой `hermes profile create <name>`, получает:

- Выделенный слот s6‑сервиса в `/run/service/gateway-<name>/`, регистрируемый динамически во время выполнения — пересборка контейнера не требуется.
- Автоматический перезапуск при падении, управление backoff осуществляется `s6-supervise`.
- Ротируемые логи профиля в `${HERMES_HOME}/logs/gateways/<name>/current` (10 архивов по 1 МБ каждый).
- Сохранение состояния при перезапуске контейнера: при загрузке reconciler читает `gateway_state.json` из каталога каждого профиля и поднимает слот только для тех профилей, у которых последнее записанное состояние было `running`. Остановленные профили остаются остановленными.

Команды жизненного цикла, которые ты запускаешь на хосте, работают так же изнутри контейнера:

```sh
# Create a profile — registers the gateway-<name> s6 slot.
docker exec hermes hermes profile create coder

# Start / stop / restart — dispatches s6-svc; the gateway lifecycle survives docker restart.
docker exec hermes hermes -p coder gateway start
docker exec hermes hermes -p coder gateway stop
docker exec hermes hermes -p coder gateway restart

# Status — reports `Manager: s6 (container supervisor)` inside the container.
docker exec hermes hermes -p coder gateway status

# Remove a profile — tears down the s6 slot too.
docker exec hermes hermes profile delete coder
```

Под капотом `hermes gateway start/stop/restart` внутри контейнера перехватывается и перенаправляется к `s6-svc` в нужный каталог сервиса; тебе не нужно напрямую изучать команды s6. Для получения сырого состояния супервизора используй `/command/s6-svstat /run/service/gateway-<name>` (обрати внимание, что `/command/` находится в PATH только для процессов, запущенных деревом надзора — при вызове из `docker exec` передай абсолютный путь).

### Почему один контейнер с множеством профилей, а не множество контейнеров

До миграции на s6 «один контейнер на профиль» был рекомендованным шаблоном, потому что внутри контейнера не было супервизора для управления несколькими шлюзами. С s6 в качестве PID 1 это больше не требуется, а одноконтейнерный подход проще почти во всех измерениях:

| | Один контейнер, многие профили | Один контейнер на профиль |
|---|---|---|
| Нагрузка на диск | Один образ, один объединённый venv, один кэш Playwright | N образов / N кэшей |
| Нагрузка на память | Общий кэш интерпретатора Python, общие `node_modules` | Дублирование в каждом контейнере |
| Создание профиля | `docker exec … hermes profile create <name>` (секунды) | Новый запуск `docker run` + выделение порта + конфигурация bind‑mount |
| Восстановление после падения профиля | Автоперезапуск `s6-supervise` | Docker `--restart unless-stopped` (медленнее, убивает соседние задачи) |
| Логи | Ротируемый файл профиля через `s6-log`, плюс аудит‑лог загрузки контейнера | `docker logs <name>` на контейнер — без встроённой ротации |
| Резервное копирование | Один каталог `~/.hermes` | N каталогов, требующих координации |

Профиль по умолчанию (`default`) всегда регистрируется при первой загрузке, поэтому свежий контейнер поставляется с одним контролируемым шлюзом «из коробки». Дополнительные профили — это чисто динамические добавления.

### Когда действительно нужен отдельный контейнер

Профиль‑в‑контейнере — это значение по умолчанию. Запускай отдельный контейнер на профиль только при наличии конкретной причины:

- **Изоляция ресурсов на задачу** — например, «выпадающая» сессия браузерного инструмента в профиле A не должна приводить к OOM в профиле B. Контейнеры позволяют задавать `--memory` / `--cpus` для каждого профиля.
- **Независимое закрепление образов** — разные теги upstream‑образов для разных задач.
- **Сегментация сети** — отдельные Docker‑сети для профилей (например, один клиентский, один внутренний).
- **Соответствие требованиям / ограничение зоны поражения** — разные учётные данные никогда не делят дерево процессов на уровне ОС.

В таких случаях объявляй один сервис на профиль с отдельными `container_name`, `volumes` и `ports`:

```yaml
services:
  hermes-work:
    image: nousresearch/hermes-agent:latest
    container_name: hermes-work
    restart: unless-stopped
    command: gateway run
    ports:
      - "8642:8642"
    volumes:
      - ~/.hermes-work:/opt/data

  hermes-personal:
    image: nousresearch/hermes-agent:latest
    container_name: hermes-personal
    restart: unless-stopped
    command: gateway run
    ports:
      - "8643:8642"
    volumes:
      - ~/.hermes-personal:/opt/data
```

Предупреждение из раздела [Persistent volumes](#persistent-volumes) остаётся в силе: никогда не указывай два контейнера одновременно на один и тот же каталог `~/.hermes`. Супервизор s6 внутри каждого контейнера управляет собственным набором профилей; совместное использование тома данных между контейнерами приводит к повреждению файлов сессий и хранилищ памяти.
## Куда идут логи

В контейнере s6 есть четыре отдельные поверхности логов, и вопрос «почему мой шлюз ничего не показывает в `docker logs`» часто вызывает удивление. Шпаргалка:

| Источник | Куда попадает | Как читать |
|---|---|---|
| **Шлюз per‑profile** (`hermes gateway run` и шлюзы per‑profile под s6) | Дублируется в два места: `docker logs <container>` (в реальном времени, без дополнительного префикса) **и** `${HERMES_HOME}/logs/gateways/<profile>/current` (ротация, метки времени ISO‑8601, 10 архивов × 1 МБ каждый) | `docker logs -f hermes` или `tail -F ~/.hermes/logs/gateways/default/current` на хосте |
| **Dashboard** (когда `HERMES_DASHBOARD=1`) | `docker logs <container>` (без префикса) | `docker logs -f hermes` — строки шлюза перемешаны с выводом дашборда |
| **Boot reconciler** (регистрирует, какие шлюзы профилей были восстановлены при каждом запуске контейнера) | `${HERMES_HOME}/logs/container-boot.log` (журнал аудита в режиме только добавления) | `tail -F ~/.hermes/logs/container-boot.log` |
| **Общие логи Hermes** (`agent.log`, `errors.log`) | `${HERMES_HOME}/logs/` (зависящий от профиля) | `docker exec hermes hermes logs --follow [--level WARNING] [--session <id>]` |

Две практические последствия, которые стоит знать:

- Копия файла в `logs/gateways/<profile>/current` сохраняется при перезапуске контейнера. `docker logs` хранит вывод только за время жизни текущего контейнера (и стирается при `docker rm`); ротационные файлы остаются на примонтированном томе.
- Формат строки аудита boot reconciler выглядит так: `<iso-timestamp> profile=<name> prior_state=<state> action=<registered|started>`, поэтому быстрый `grep profile=coder ~/.hermes/logs/container-boot.log` покажет, когда конкретный профиль был последний раз восстановлен и запустил ли его s6 автоматически.
## Перенаправление переменных окружения

API‑ключи читаются из `/opt/data/.env` внутри контейнера. Также можно передать переменные окружения напрямую:

```sh
docker run -it --rm \
  -v ~/.hermes:/opt/data \
  -e ANTHROPIC_API_KEY="sk-ant-..." \
  -e OPENAI_API_KEY="sk-..." \
  nousresearch/hermes-agent
```

Флаги `-e` переопределяют значения из `.env`. Это удобно для интеграций CI/CD или менеджеров секретов, когда не хочется хранить ключи на диске.

:::note Ищешь Docker в качестве **терминального бэкенда**?
Эта страница описывает запуск Hermes непосредственно внутри Docker. Если ты хочешь, чтобы Hermes выполнял вызовы `terminal` / `execute_code` агента внутри контейнера‑песочницы Docker (один длительно живущий контейнер, общий для процессов Hermes — см. issue #20561), это отдельный блок конфигурации — `terminal.backend: docker` плюс `terminal.docker_image`, `terminal.docker_volumes`, `terminal.docker_forward_env`, `terminal.docker_env`, `terminal.docker_run_as_host_user`, `terminal.docker_extra_args`, `terminal.docker_persist_across_processes` и `terminal.docker_orphan_reaper`. Смотри [Configuration → Docker Backend](configuration.md#docker-backend) для полного набора, включая правила жизненного цикла контейнера.
:::
## Пример Docker Compose

Для постоянного развертывания с одновременно шлюзом и панелью управления удобно использовать `docker-compose.yaml`:

```yaml
services:
  hermes:
    image: nousresearch/hermes-agent:latest
    container_name: hermes
    restart: unless-stopped
    command: gateway run
    ports:
      - "8642:8642"   # gateway API
      - "9119:9119"   # dashboard (only reached when HERMES_DASHBOARD=1)
    volumes:
      - ~/.hermes:/opt/data
    environment:
      - HERMES_DASHBOARD=1
      # Uncomment to forward specific env vars instead of using .env file:
      # - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      # - OPENAI_API_KEY=${OPENAI_API_KEY}
      # - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: "2.0"
```

Запусти `docker compose up -d` и просматривай логи с помощью `docker compose logs -f`. Стандартный вывод контролируемого шлюза также дублируется в `${HERMES_HOME}/logs/gateways/<profile>/current` на томе — смотри раздел [Where the logs go](#where-the-logs-go) для полной карты маршрутизации.
## Необязательно: аудио‑мост для Linux‑десктопа

Режим голосового ввода в Docker требует двух условий: Hermes должен иметь возможность опрашивать аудиоустройства внутри контейнера, и контейнер должен иметь доступ к аудиосерверу хоста. Ниже описана настройка, покрывающая аудиоподключение хоста для Linux‑десктопов, которые предоставляют совместимый с PulseAudio сокет, включая многие конфигурации PipeWire.

:::caution
Это обходное решение для Linux‑десктопа, а не общая функция Docker Desktop. Оно полезно, когда аудио на хосте уже работает и ты хочешь использовать режим голосового ввода CLI внутри контейнера Hermes. Если Hermes всё равно выводит `Running inside Docker container -- no audio devices`, используй сборку, включающую поддержку опроса аудио Docker для `PULSE_SERVER` / `PIPEWIRE_REMOTE`.
:::

Сначала создай конфигурацию ALSA рядом с файлом Compose:

```conf title="asound.conf"
pcm.!default {
    type pulse
    hint {
        show on
        description "Default ALSA Output (PulseAudio)"
    }
}

pcm.pulse {
    type pulse
}

ctl.!default {
    type pulse
}
```

Затем собери небольшой производный образ с установленным плагином ALSA PulseAudio:

```dockerfile title="Dockerfile.audio"
FROM nousresearch/hermes-agent:latest

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends libasound2-plugins \
    && rm -rf /var/lib/apt/lists/*
```

Используй этот образ в Compose и пробрось сокет PulseAudio пользователя хоста и cookie:

```yaml
services:
  hermes:
    build:
      context: .
      dockerfile: Dockerfile.audio
    image: hermes-agent-audio
    container_name: hermes
    restart: unless-stopped
    command: gateway run
    volumes:
      - ~/.hermes:/opt/data
      - /run/user/${HERMES_UID}/pulse:/run/user/${HERMES_UID}/pulse
      - ~/.config/pulse/cookie:/tmp/pulse-cookie:ro
      - ./asound.conf:/etc/asound.conf:ro
    environment:
      - HERMES_UID=${HERMES_UID}
      - HERMES_GID=${HERMES_GID}
      - XDG_RUNTIME_DIR=/run/user/${HERMES_UID}
      - PULSE_SERVER=unix:/run/user/${HERMES_UID}/pulse/native
      - PULSE_COOKIE=/tmp/pulse-cookie
```

Запусти его с UID/GID хоста, чтобы процесс в контейнере мог получить доступ к пользовательскому аудиосокету:

```sh
export HERMES_UID="$(id -u)"
export HERMES_GID="$(id -g)"
docker compose up -d --build
```

Чтобы проверить, что PortAudio видит внутри контейнера:

```sh
docker exec hermes /opt/hermes/.venv/bin/python -c "import sounddevice as sd; print(sd.query_devices())"
```
## Ограничения ресурсов

Контейнер Hermes требует умеренных ресурсов. Минимальные рекомендуемые параметры:

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| Memory | 1 GB | 2–4 GB |
| CPU | 1 core | 2 cores |
| Disk (data volume) | 500 MB | 2+ GB (растёт вместе с сессиями/skills) |

Автоматизация браузера (Playwright/Chromium) — самая требовательная к памяти функция. Если браузерные инструменты не нужны, достаточно 1 GB. При активных браузерных инструментах выделяй минимум 2 GB.

Установи ограничения в Docker:

```sh
docker run -d \
  --name hermes \
  --restart unless-stopped \
  --memory=4g --cpus=2 \
  -v ~/.hermes:/opt/data \
  nousresearch/hermes-agent gateway run
```
## Что делает Dockerfile

Официальный образ основан на `debian:13.4` и включает:

- Python 3 со всеми зависимостями Hermes (`uv pip install -e ".[all]"`)
- Node.js + npm (для автоматизации браузера и моста WhatsApp)
- Playwright с Chromium (`npx playwright install --with-deps chromium --only-shell`)
- ripgrep, ffmpeg, git и `xz-utils` как системные утилиты
- **`docker-cli`** — чтобы агенты, запущенные внутри контейнера, могли управлять Docker‑демоном хоста (привязка `/var/run/docker.sock` при желании) для `docker build`, `docker run`, инспекции контейнеров и т.д.
- **`openssh-client`** — позволяет использовать [SSH‑терминальный бекенд](/user-guide/configuration#ssh-backend) изнутри контейнера. SSH‑бекенд вызывает системный бинарник `ssh`; без этого он молча не работал в контейнерных установках.
- Мост WhatsApp (`scripts/whatsapp-bridge/`)
- **[`s6-overlay`](https://github.com/just-containers/s6-overlay) v3** в качестве PID 1 (заменяет старый `tini`) — контролирует дашборд и шлюзы per‑profile с авто‑перезапуском при падении, убирает зомби‑процессы и передаёт сигналы.

`ENTRYPOINT` контейнера — `/init` из s6‑overlay. При загрузке он:

1. Запускает `/etc/cont-init.d/01-hermes-setup` (= `docker/stage2-hook.sh`) от root: опциональное переопределение UID/GID, исправление прав томов, инициализация `.env` / `config.yaml` / `SOUL.md` при первом запуске, синхронизация встроенных навыков.
2. Запускает `/etc/cont-init.d/02-reconcile-profiles` (= `hermes_cli.container_boot`): проходит по `$HERMES_HOME/profiles/<name>/`, воссоздаёт слот службы шлюза s6 для каждого профиля в `/run/service/gateway-<profile>/` и автоматически стартует только те, у которых последнее зафиксированное состояние было `running` (см. [Supervision шлюза per‑profile](#per-profile-gateway-supervision)).
3. Запускает статические службы s6‑rc `main-hermes` и `dashboard`.
4. Выполняет CMD контейнера как основную программу (`/opt/hermes/docker/main-wrapper.sh`), который маршрутизирует аргументы, переданные пользователем в `docker run`:
   - без аргументов → `hermes` (по умолчанию)
   - первый аргумент — исполняемый файл в `PATH` (например, `sleep`, `bash`) → выполнить его напрямую
   - всё остальное → `hermes <args>` (проброс подкоманды)

Контейнер завершается, когда завершается эта основная программа, возвращая её код выхода.

:::warning Изменение поведения по сравнению с образами до s6
`ENTRYPOINT` теперь `/init` (s6‑overlay), а не `/usr/bin/tini`. Все пять задокументированных вариантов вызова `docker run` (без аргументов, `chat -q "…"`, `sleep infinity`, `bash`, `--tui`) работают так же, как и в образе на основе `tini`. Если у тебя есть обёртка, зависящая от специфического поведения сигналов `tini` или жёстко закодированного вызова `/usr/bin/tini --`, зафиксируй предыдущий тег образа.
:::

:::warning Модель привилегий
Не переопределяй `entrypoint` образа, если не оставляешь в цепочке команд `/init` (или, эквивалентно, наследуемый shim `docker/entrypoint.sh`, который переадресует к hook‑у stage2). `/init` из s6‑overlay запускается от root, чтобы изменить владельца тома при первом старте, затем переключается на пользователя `hermes` через `s6-setuidgid` для каждой контролируемой службы **и** для основной программы. Запуск `hermes gateway run` от root в официальном образе отклоняется по умолчанию, потому что это может оставить файлы, принадлежащие root, в `/opt/data` и сломать последующие запуски дашборда или шлюза. Устанавливай `HERMES_ALLOW_ROOT_GATEWAY=1` только если осознанно принимаешь этот риск.
:::

### `docker exec` автоматически переключается на пользователя `hermes`

`docker exec hermes <cmd>` по умолчанию запускается от root внутри контейнера, но образ поставляет лёгкий shim в `/opt/hermes/bin/hermes` (самый ранний в `PATH`), который обнаруживает вызовы от root и прозрачно переисполняет их через `s6-setuidgid hermes`. Поэтому `docker exec hermes login`, `docker exec hermes profile create …`, `docker exec hermes setup` и т.п. записывают файлы, принадлежащие UID 10000 — т.е. доступные контролируемому шлюзу — без необходимости указывать флаг `--user`. Не‑root вызовы (само контролируемые процессы, `docker exec --user hermes`, под‑агенты kanban внутри контейнера) попадают в короткий путь, который сразу исполняет бинарник виртуального окружения, так что накладные расходы на горячих путях отсутствуют.

Если нужен `docker exec`, сохраняющий привилегии root (диагностические сессии, инспекция состояния, доступ к файлам вне `/opt/data`, принадлежащим root), отключай переключение при каждом вызове:

```sh
docker exec -e HERMES_DOCKER_EXEC_AS_ROOT=1 hermes <cmd>
```

Shim принимает `1` / `true` / `yes` (без учёта регистра). Любое другое значение — включая опечатки вроде `=0` — приводит к обычному переключению, поэтому тихие отключения невозможны. Если `s6-setuidgid` недоступен (кастомные сборки без s6‑overlay), shim отказывается работать от root и выходит с кодом 126, явно сигнализируя о нарушенной модели привилегий, вместо того чтобы тихо возвращаться к старому «footgun», когда `docker exec hermes login` записывал `auth.json` как `root:root` и ломал аутентификацию шлюза на каждой платформе обмена сообщениями.

### Supervision шлюза per‑profile

Каждый профиль, созданный командой `hermes profile create <name>`, автоматически получает сервис шлюза, контролируемый s6, зарегистрированный в `/run/service/gateway-<name>/`, с сохранением состояния и авто‑перезапуском при перезапуске контейнера. См. [Поддержка нескольких профилей](#multi-profile-support) выше для пользовательского рабочего процесса и команд жизненного цикла.

**Преимущества supervision по сравнению с образами до s6:**

- При падении шлюза `s6-supervise` автоматически перезапускает его после ~1 секунды задержки.
- Дашборд, если включён через `HERMES_DASHBOARD=1`, находится в том же дереве supervision и получает такой же авто‑перезапуск.
- `docker restart` сохраняет работающие шлюзы: reconciler в `cont-init` читает `$HERMES_HOME/profiles/<name>/gateway_state.json` и восстанавливает слот, если последнее зафиксированное состояние было `running`. Остановленные шлюзы остаются остановленными.
- Логи шлюза per‑profile сохраняются в `$HERMES_HOME/logs/gateways/<profile>/current` (ротация через `s6-log`), а действия reconciler‑а добавляются в `$HERMES_HOME/logs/container-boot.log` при каждой загрузке. См. [Куда идут логи](#where-the-logs-go) для полной схемы маршрутизации.

`hermes status` внутри контейнера выводит `Manager: s6 (container supervisor)`. Используй `/command/s6-svstat /run/service/gateway-<name>` для просмотра сырых данных супервизора (заметь, `/command/` находится в `PATH` только для процессов supervision‑tree; при вызове из `docker exec` указывай абсолютный путь).
## Обновление

Загрузи последнюю версию образа и пересоздай контейнер. Твой каталог данных останется нетронутым.

```sh
docker pull nousresearch/hermes-agent:latest
docker rm -f hermes
docker run -d \
  --name hermes \
  --restart unless-stopped \
  -v ~/.hermes:/opt/data \
  nousresearch/hermes-agent gateway run
```

Или с Docker Compose:

```sh
docker compose pull
docker compose up -d
```
## Навыки и файлы учётных данных

При использовании Docker в качестве среды выполнения (не те методы, что выше, а когда агент выполняет команды внутри Docker‑песочницы — см. [Configuration → Docker Backend](./configuration.md#docker-backend)) Hermes переиспользует один долгоживущий контейнер для всех вызовов инструментов и автоматически bind‑монтирует каталог навыков (`~/.hermes/skills/`) и любые файлы учётных данных, объявленные навыками, в этот контейнер как тома только для чтения. Скрипты навыков, шаблоны и ссылки доступны внутри песочницы без ручной настройки, и поскольку контейнер сохраняется на протяжении всего процесса Hermes, любые установленные зависимости или созданные файлы остаются доступными для следующего вызова инструмента.

То же самое происходит для бекендов SSH и Modal — навыки и файлы учётных данных загружаются через rsync или API монтирования Modal перед каждой командой.
## Установка дополнительных инструментов в контейнере

Официальный образ поставляется с отобранным набором утилит (см. [What the Dockerfile does](#what-the-dockerfile-does)), но не каждый инструмент, который может понадобиться агенту, предустановлен. Существует пять рекомендуемых подходов, в порядке возрастания усилий и надёжности.

### npm или Python‑инструменты — используйте `npx` или `uvx`

Для любого инструмента, опубликованного в npm или PyPI, укажи Hermes запускать его через `npx` (npm) или `uvx` (Python) и запомнить эту команду в своей постоянной памяти. Если инструмент требует файл конфигурации или учётные данные, попроси его разместить их в `/opt/data` (например, `/opt/data/<tool>/config.yaml`).

Зависимости загружаются по запросу и кэшируются на время жизни контейнера. Конфигурация, записанная в `/opt/data`, сохраняется при перезапуске контейнера, поскольку находится в привязанном каталоге хоста. Сам кэш пакетов восстанавливается после `docker rm`, но `npx` и `uvx` автоматически повторно загружают его при следующем запуске инструмента.

### Другие инструменты (apt‑пакеты, бинарники) — установить и запомнить

Для всего, что находится вне npm или PyPI — пакеты `apt`, готовые бинарники, среды выполнения языков, не включённые в образ — укажи Hermes, как установить их (например, `apt-get update && apt-get install -y <package>`) и попроси запомнить команду установки. Инструмент будет сохраняться в течение всего срока жизни контейнера, а Hermes повторно выполнит команду установки после перезапуска контейнера, когда инструмент понадобится снова.

Это хороший вариант для инструментов, которые быстро устанавливаются и используются время от времени. Для постоянно используемых инструментов предпочтительнее следующий подход.

### Надёжные установки — собрать производный образ

Когда инструмент должен быть доступен сразу при каждом запуске контейнера без задержки переустановки, создай новый образ, наследующийся от `nousresearch/hermes-agent`, и установи инструмент в отдельном слое:

```dockerfile
FROM nousresearch/hermes-agent:latest

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends <your-package> \
    && rm -rf /var/lib/apt/lists/*
USER hermes
```

Собери его и используй вместо официального образа:

```sh
docker build -t my-hermes:latest .
docker run -d \
  --name hermes \
  --restart unless-stopped \
  -v ~/.hermes:/opt/data \
  -p 8642:8642 \
  my-hermes:latest gateway run
```

Скрипт `entrypoint` и семантика `/opt/data` наследуются без изменений, поэтому остальная часть этой страницы остаётся актуальной. Не забудь пересобрать образ при обновлении базового `nousresearch/hermes-agent`.

### Сложные инструменты или многосервисные стеки — запустить sidecar‑контейнер

Для инструментов, которые предоставляют собственный сервис (база данных, веб‑сервер, очередь, ферма безголовых браузеров) или слишком тяжёлые, чтобы жить внутри контейнера Hermes, запусти их в отдельном контейнере в общей Docker‑сети. Hermes обращается к sidecar‑контейнеру по имени контейнера, так же как к локальному серверу вывода (см. [Connecting to local inference servers](#connecting-to-local-inference-servers-vllm-ollama-etc)).

```yaml
services:
  hermes:
    image: nousresearch/hermes-agent:latest
    container_name: hermes
    restart: unless-stopped
    command: gateway run
    ports:
      - "8642:8642"
    volumes:
      - ~/.hermes:/opt/data
    networks:
      - hermes-net

  my-tool:
    image: example/my-tool:latest
    container_name: my-tool
    restart: unless-stopped
    networks:
      - hermes-net

networks:
  hermes-net:
    driver: bridge
```

Изнутри контейнера Hermes sidecar доступен по адресу `http://my-tool:<port>` (или по любому другому протоколу, который он обслуживает). Такой подход позволяет каждому сервису иметь независимый жизненный цикл, ограничения ресурсов и график обновлений, а также избегает раздувания образа Hermes зависимостями, нужными только одному инструменту.

### Широко полезные инструменты — открой issue или pull request

Если инструмент, вероятно, будет полезен большинству пользователей Hermes Agent, рассмотрите возможность внести его в основной репозиторий, а не поддерживать в частном производном образе. Открой issue или pull request в [hermes-agent repository](https://github.com/NousResearch/hermes-agent), описав инструмент и сценарий его использования. Инструменты, включённые в официальный образ, приносят пользу всем пользователям и избавляют от нагрузки по обслуживанию форка.
## Подключение к локальным inference‑серверам (vLLM, Ollama и др.)

Когда Hermes работает в Docker, а твой inference‑сервер (vLLM, Ollama, text‑generation‑inference и т.п.) также запущен на хосте или в другом контейнере, сетевые настройки требуют особого внимания.

### Docker Compose (рекомендовано)

Размести оба сервиса в одной Docker‑сети. Это самый надёжный подход:

```yaml
services:
  vllm:
    image: vllm/vllm-openai:latest
    container_name: vllm
    command: >
      --model Qwen/Qwen2.5-7B-Instruct
      --served-model-name my-model
      --host 0.0.0.0
      --port 8000
    ports:
      - "8000:8000"
    networks:
      - hermes-net
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]

  hermes:
    image: nousresearch/hermes-agent:latest
    container_name: hermes
    restart: unless-stopped
    command: gateway run
    ports:
      - "8642:8642"
    volumes:
      - ~/.hermes:/opt/data
    networks:
      - hermes-net

networks:
  hermes-net:
    driver: bridge
```

Затем в файле `~/.hermes/config.yaml` используй **имя контейнера** в качестве имени хоста:

```yaml
model:
  provider: custom
  model: my-model
  base_url: http://vllm:8000/v1
  api_key: "none"
```

:::tip Ключевые моменты
- Используй **имя контейнера** (`vllm`) в качестве имени хоста — не `localhost` и не `127.0.0.1`, которые указывают на сам контейнер Hermes.
- Значение `model` должно совпадать с `--served-model-name`, который ты передал vLLM.
- Установи `api_key` в любую непустую строку (vLLM требует заголовок, но по умолчанию не проверяет его).
- **Не** добавляй завершающий слеш в `base_url`.
:::

### Запуск Docker без Compose

Если inference‑сервер работает напрямую на хосте (не в Docker), используй `host.docker.internal` на macOS/Windows или `--network host` на Linux:

**macOS / Windows:**

```sh
docker run -d \
  --name hermes \
  -v ~/.hermes:/opt/data \
  -p 8642:8642 \
  nousresearch/hermes-agent gateway run
```

```yaml
# config.yaml
model:
  provider: custom
  model: my-model
  base_url: http://host.docker.internal:8000/v1
  api_key: "none"
```

**Linux (сетевой режим host):**

```sh
docker run -d \
  --name hermes \
  --network host \
  -v ~/.hermes:/opt/data \
  nousresearch/hermes-agent gateway run
```

```yaml
# config.yaml
model:
  provider: custom
  model: my-model
  base_url: http://127.0.0.1:8000/v1
  api_key: "none"
```

:::warning При использовании `--network host` флаг `-p` игнорируется — все порты контейнера напрямую открыты на хосте.
:::

### Проверка соединения

Изнутри контейнера Hermes убедись, что inference‑сервер доступен:

```sh
docker exec hermes curl -s http://vllm:8000/v1/models
```

Ты должен получить JSON‑ответ со списком твоих обслуживаемых моделей. Если это не удалось, проверь:

1. Оба контейнера находятся в одной Docker‑сети (`docker network inspect hermes-net`)
2. Инференс‑сервер слушает `0.0.0.0`, а не `127.0.0.1`
3. Номер порта совпадает

### Ollama

Ollama работает так же. Если Ollama запущена на хосте, используй `host.docker.internal:11434` (macOS/Windows) или `127.0.0.1:11434` (Linux с `--network host`). Если Ollama запущена в собственном контейнере в той же Docker‑сети:

```yaml
model:
  provider: custom
  model: llama3
  base_url: http://ollama:11434/v1
  api_key: "none"
```
## Устранение неполадок

### Контейнер сразу выходит

Проверьте логи: `docker logs hermes`. Распространённые причины:
- Отсутствует или неверный файл `.env` — запустите контейнер интерактивно, чтобы завершить настройку.
- Конфликты портов при запуске с проброшенными портами.

### Ошибки «Permission denied»

Хук stage2 контейнера понижает привилегии до непривилегированного пользователя `hermes` (UID 10000) через `s6-setuidgid` в каждом управляемом сервисе. Если ваш каталог `~/.hermes/` на хосте принадлежит другому UID, задайте `HERMES_UID`/`HERMES_GID` — или их псевдонимы `PUID`/`PGID`, как в образах LinuxServer.io и NAS — чтобы они совпадали с UID вашего пользователя, либо убедитесь, что каталог данных доступен для записи:

```sh
chmod -R 755 ~/.hermes
```

На NAS (UGOS, Synology, unRAID) каталог данных обычно представляет собой **bind mount**, принадлежащий UID хоста, который контейнер не может `chown`. Установите `PUID`/`PGID` (или `HERMES_UID`/`HERMES_GID`) в значение UID этого пользователя, чтобы процесс выполнения работал от имени владельца монтирования, а не UID 10000:

```sh
docker run -d \
  --name hermes \
  -e PUID=1000 -e PGID=10 \
  -v /volume1/docker/hermes:/opt/data \
  nousresearch/hermes-agent gateway run
```

`docker exec hermes <cmd>` также автоматически понижает привилегии до UID 10000 — см. [`docker exec` automatically drops to the `hermes` user`](#docker-exec-automatically-drops-to-the-hermes-user) для подробностей и возможности отключения при каждом вызове.

### Инструменты браузера не работают

Playwright требует совместно используемую память. Добавьте `--shm-size=1g` к вашей команде `docker run`:

```sh
docker run -d \
  --name hermes \
  --shm-size=1g \
  -v ~/.hermes:/opt/data \
  nousresearch/hermes-agent gateway run
```

### gateway не переподключается после проблем с сетью

Флаг `--restart unless-stopped` обрабатывает большинство временных сбоев. Если gateway «завис», перезапустите контейнер:

```sh
docker restart hermes
```

### Проверка состояния контейнера

```sh
docker logs --tail 50 hermes          # Recent logs
docker run -it --rm nousresearch/hermes-agent:latest version     # Verify version
docker stats hermes                    # Resource usage
```