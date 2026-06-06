---
sidebar_position: 7
title: "Docker"
description: "Запуск Hermes Agent у Docker та використання Docker як термінальний бекенд"
---

# Hermes Agent — Docker

Існує два різних способи взаємодії Docker з Hermes Agent:

1. **Running Hermes IN Docker** — агент сам запускається всередині контейнера (основна тема цієї сторінки)
2. **Docker as a terminal backend** — агент працює на твоєму хості, але виконує кожну команду всередині одного, постійного Docker‑sandbox контейнера, який зберігається між викликами інструментів, `/new` та субагентами протягом усього життя процесу Hermes (дивись [Configuration → Docker Backend](./configuration.md#docker-backend))

Ця сторінка охоплює варіант 1. Контейнер зберігає всі дані користувача (конфігурація, API‑ключі, сесії, skills, пам'ять) в одному каталозі, змонтованому з хоста за шляхом `/opt/data`. Сам образ є безстанним і може бути оновлений шляхом завантаження нової версії без втрати будь‑якої конфігурації.
## Швидкий старт

Якщо ти вперше запускаєш Hermes Agent, створи каталог даних на хості та запусти контейнер у інтерактивному режимі, щоб пройти майстер налаштування:

```sh
mkdir -p ~/.hermes
docker run -it --rm \
  -v ~/.hermes:/opt/data \
  nousresearch/hermes-agent setup
```

Це відкриє майстер налаштування, який запитає твої API‑ключі та збереже їх у `~/.hermes/.env`. Це потрібно зробити лише один раз. Настійно рекомендуємо налаштувати чат‑систему, з якою працюватиме шлюз, на цьому етапі.

:::tip
У контейнері запусти `hermes setup --portal` один раз — токен оновлення зберігається у змонтованому томі `~/.hermes`. Дивись [Nous Portal](/integrations/nous-portal).
:::
## Запуск у режимі шлюзу

Після налаштування запусти контейнер у фоні як постійний шлюз (Telegram, Discord, Slack, WhatsApp тощо):

```sh
docker run -d \
  --name hermes \
  --restart unless-stopped \
  -v ~/.hermes:/opt/data \
  -p 8642:8642 \
  nousresearch/hermes-agent gateway run
```

Порт 8642 відкриває [сервер API, сумісний з OpenAI](./features/api-server.md) шлюзу та endpoint стану здоров’я. Це необов’язково, якщо ти використовуєш лише чат‑платформи (Telegram, Discord тощо), але потрібно, якщо ти хочеш, щоб панель управління або зовнішні інструменти мали доступ до шлюзу.

:::tip Шлюз працює під наглядом
У офіційному образі Docker команда `gateway run` **автоматично контролюється s6‑overlay**: якщо процес шлюзу падає, його перезапускають через кілька секунд без втрати контейнера, а панель (коли встановлено `HERMES_DASHBOARD=1`) контролюється разом із ним. Сам процес `gateway run` у CMD — це `sleep infinity`‑серце, яке тримає контейнер живим, поки s6 керує реальним процесом шлюзу — тому `docker stop` все одно чисто зупиняє все, а `docker logs` показує вивід під наглядом шлюзу.

Ти побачиш однорядкову **хлібну крихту** у `docker logs`, що підтверджує оновлення. Щоб відмовитися — і отримати історичну семантику «шлюз є головним процесом контейнера, вихід контейнера = вихід шлюзу» — передай `--no-supervise` або встанови `HERMES_GATEWAY_NO_SUPERVISE=1`. Відмова корисна для CI‑тестів, які хочуть, щоб контейнер завершувався зі статус‑кодом шлюзу; для продакшн‑розгортань під наглядом за замовчуванням однозначно кращий варіант.

Ця поведінка стосується лише образу на базі s6. Попередні (на базі tini) образи все ще запускають `gateway run` як процес у передньому плані.
:::

:::note Куди потрапляють логи шлюзу
Дивись розділ [Куди потрапляють логи](#where-the-logs-go) нижче для повної карти маршрутизації (шлюзи per‑profile, панель, boot reconciler, `docker logs` контейнера).
:::

Примітка: сервер API активується лише за умови `API_SERVER_ENABLED=true`. Щоб відкрити його за межами `127.0.0.1` всередині контейнера, також встанови `API_SERVER_HOST=0.0.0.0` і `API_SERVER_KEY` (мінімум 8 символів — згенеруй його за допомогою `openssl rand -hex 32`). Приклад:

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

Відкриття будь‑якого порту на машині, доступній в інтернеті, є ризиком безпеки. Не роби цього, якщо не розумієш ризиків.
## Запуск дашборду

Вбудований веб‑дашборд працює як супервізований s6‑rc сервіс поряд із шлюзом в тому ж контейнері. Встанови `HERMES_DASHBOARD=1`, щоб його підняти:

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

Дашборд супервізується s6 — якщо він падає, `s6-supervise` автоматично перезапускає його після короткої затримки. stdout/stderr дашборду пересилаються до `docker logs <container>` (без префікса; власний вивід шлюзу тепер записується у файл s6‑log для кожного профілю — дивись [Where the logs go](#where-the-logs-go) нижче — тому два потоки не конфліктують).

| Environment variable | Description | Default |
|---------------------|-------------|---------|
| `HERMES_DASHBOARD` | Встанови `1` (або `true` / `yes`), щоб увімкнути супервізований сервіс дашборду | *(unset — сервіс зареєстровано, але він не запущений)* |
| `HERMES_DASHBOARD_HOST` | Адреса прив’язки HTTP‑сервера дашборду | `0.0.0.0` |
| `HERMES_DASHBOARD_PORT` | Порт HTTP‑сервера дашборду | `9119` |
| `HERMES_DASHBOARD_TUI` | Встанови `1`, щоб відкрити в‑браузері вкладку Chat (вбудований `hermes --tui` через PTY/WebSocket) | *(unset)* |
| `HERMES_DASHBOARD_INSECURE` | Встанови `1` (або `true` / `yes`), щоб прив’язатися без OAuth‑gate. Використовуй лише у довірених мережах за зворотним проксі без OAuth‑контракту — дашборд відкриває API‑ключі та дані сесії | *(unset — gate застосовується, коли зареєстровано `DashboardAuthProvider`)* |

Дашборд у контейнері за замовчуванням прив’язується до `0.0.0.0` — без цього опублікований порт `-p 9119:9119` був би недоступний з хоста. Щоб обмежити прив’язку лише до loopback контейнера (для sidecar / reverse‑proxy налаштувань), встанови `HERMES_DASHBOARD_HOST=127.0.0.1`.

OAuth‑gate дашборду активується автоматично, коли виконуються обидві умови:

1. Хост прив’язки не є loopback (наприклад, за замовчуванням `0.0.0.0` у контейнері), **і**
2. Зареєстровано плагін `DashboardAuthProvider`.

Вбудований провайдер `dashboard_auth/nous` активується, коли встановлено `HERMES_DASHBOARD_OAUTH_CLIENT_ID` (дивись [Web Dashboard → Authentication](features/web-dashboard.md)). При активному gate браузерні клієнти перенаправляються до OAuth‑потоку налаштованого порталу, перш ніж отримати доступ до будь‑якого захищеного маршруту.

Якщо провайдер не зареєстровано і хост прив’язки не loopback, дашборд **завершується з помилкою під час старту**, вказуючи на відсутню змінну оточення. Щоб явно вимкнути gate — для розгортання у довіреній LAN‑мережі за власним reverse‑proxy без OAuth‑контракту — встанови `HERMES_DASHBOARD_INSECURE=1`. Це **єдиний** шлях, який вимикає gate; сам хост прив’язки ніколи не передбачає `--insecure` (раніше так було, але це передувало OAuth‑gate і тихо його вимикало у кожному дашборді, розгорнутому в контейнері).

:::warning `HERMES_DASHBOARD_INSECURE=1` відкриває API‑ключі
Вимкнення OAuth‑gate робить API‑поверхню дашборду (включаючи ключі моделей та дані сесії) доступною будь‑кому, хто може досягти опублікованого порту. Увімкни його лише тоді, коли перед дашбордом є власний шар автентифікації, або у довіреній LAN‑мережі, яку ти повністю контролюєш.
:::

Запуск дашборду в окремому контейнері не підтримується: його детекція живості шлюзу вимагає спільного PID‑простору з процесом шлюзу.
## Запуск у інтерактивному режимі (CLI чат)

Щоб відкрити інтерактивну чат‑сесію для запущеного каталогу даних:

```sh
docker run -it --rm \
  -v ~/.hermes:/opt/data \
  nousresearch/hermes-agent
```

А якщо ти вже відкрив термінал у запущеному контейнері (наприклад, через Docker Desktop), просто виконай:

```sh
/opt/hermes/.venv/bin/hermes
```
## Постійні томи

Том `/opt/data` є єдиним джерелом істини для всього стану Hermes. Він відображається у вашому каталозі `~/.hermes/` на хості і містить:

| Шлях | Вміст |
|------|----------|
| `.env` | API‑ключі та секрети |
| `config.yaml` | Уся конфігурація Hermes |
| `SOUL.md` | Особистість/ідентичність агента |
| `sessions/` | Історія розмов |
| `memories/` | Постійне сховище пам’яті |
| `skills/` | Встановлені skills |
| `home/` | HOME‑каталог для кожного профілю підпроцесів інструментів Hermes (`git`, `ssh`, `gh`, `npm` та CLI skills) |
| `cron/` | Визначення запланованих завдань |
| `hooks/` | Хуки подій |
| `logs/` | Журнали виконання |
| `skins/` | Користувацькі CLI‑шкурки |

CLI skills, які зберігають облікові дані у `~`, мають ініціалізуватись щодо HOME підпроцесу, а не лише кореня тома даних. Наприклад, [xurl skill](./skills/bundled/social-media/social-media-xurl.md) зберігає стан OAuth у `~/.xurl`; в офіційному Docker‑розташуванні Hermes інструмент читає це як `/opt/data/home/.xurl`, тому запусти ручну автентифікацію xurl з `HOME=/opt/data/home` і перевір її за допомогою `HOME=/opt/data/home xurl auth status`.

:::warning
Ніколи не запускай два контейнері Hermes **gateway** одночасно проти одного і того ж каталогу даних — файли сесій та сховища пам’яті не призначені для одночасного запису.
:::
## Підтримка кількох профілів

Hermes підтримує [кілька профілів](../reference/profile-commands.md) — окремі підкаталоги `~/.hermes/`, які дозволяють запускати незалежні агенти (різні SOUL, навички, пам’ять, сесії, облікові дані) з однієї інсталяції. **У офіційному Docker‑образі дерево нагляду s6 розглядає кожен профіль як першокласний підконтрольний сервіс**, тому рекомендоване розгортання — **один контейнер, що містить усі профілі**.

Кожен профіль, створений за допомогою `hermes profile create <name>`, отримує:

- Виділений слот s6‑служби за адресою `/run/service/gateway-<name>/`, зареєстрований динамічно під час виконання — без потреби перебудови контейнера.
- Авто‑перезапуск при збоях, керування затримкою здійснює `s6-supervise`.
- Ротовані журнали профілю за шляхом `${HERMES_HOME}/logs/gateways/<name>/current` (10 архівів по 1 МБ кожен).
- Збереження стану між перезапусками контейнера: під час завантаження реконсилятор читає `gateway_state.json` у каталозі кожного профілю і піднімає слот лише для профілів, у яких останній записаний стан був `running`. Зупинені профілі залишаються зупиненими.

Команди життєвого циклу, які ти виконуєш на хості, працюють так само й усередині контейнера:

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

Під капотом `hermes gateway start/stop/restart` всередині контейнера перехоплюється і перенаправляється до `s6-svc` у відповідний каталог служби; тобі не потрібно безпосередньо вивчати команди s6. Для отримання стану супервізора використай `/command/s6-svstat /run/service/gateway-<name>` (зауваж, `/command/` доступний у PATH лише для процесів, запущених деревом нагляду — при виклику з `docker exec` передай абсолютний шлях).

### Чому один контейнер з багатьма профілями, а не багато контейнерів

До переходу на s6 «один контейнер на профіль» був рекомендованим шаблоном, бо не існувало внутрішнього супервізора для керування кількома шлюзами. Тепер, коли s6 працює як PID 1, це вже не потрібно, і розташування в одному контейнері простіше майже у всіх вимірах:

| | Один контейнер, багато профілів | Один контейнер на профіль |
|---|---|---|
| Навантаження на диск | Один образ, один bundled venv, один кеш Playwright | N образів / N кешів |
| Навантаження на пам’ять | Спільний кеш інтерпретатора Python, спільні `node_modules` | Дубльований у кожному контейнері |
| Створення профілю | `docker exec ... hermes profile create <name>` (секунди) | Новий виклик `docker run` + розподіл порту + конфігурація `bind‑mount` |
| Відновлення після збою профілю | `s6-supervise` авто‑перезапуск | Docker `--restart unless-stopped` (повільніше, вбиває роботу сусідів) |
| Журнали | Ротовані файли журналу профілю через `s6-log`, плюс аудит‑лог завантаження контейнера | `docker logs <name>` на контейнер — без вбудованої ротації |
| Резервне копіювання | Один каталог `~/.hermes` | N каталогів, які треба координувати |

Профіль за замовчуванням (`default`) завжди реєструється під час першого запуску, тому новий контейнер постачається з одним підконтрольним шлюзом «з коробки». Додаткові профілі — це лише динамічні додатки.

### Коли ТИ хочеш окремий контейнер

Профіль у контейнері — це налаштування за замовчуванням. Окремий контейнер на профіль варто запускати лише за наявності конкретної причини:

- **Ізоляція ресурсів на робоче навантаження** — напр., сесія інструменту браузера у профілі A не повинна вичерпувати пам’ять у профілі B. Контейнери дозволяють задати `--memory` / `--cpus` для кожного профілю.
- **Незалежне закріплення образу** — різні теги upstream‑образу для різних навантажень.
- **Сегментація мережі** — окремі Docker‑мережі для кожного профілю (наприклад, один для клієнтів, інший — внутрішній).
- **Відповідність / радіус ураження** — різні облікові дані ніколи не ділять процесне дерево ОС.

У таких випадках оголоси один сервіс на профіль з унікальними `container_name`, `volumes` та `ports`:

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

Попередження з розділу [Persistent volumes](#persistent-volumes) залишається в силі: ніколи не вказуй два контейнери одночасно на той самий каталог `~/.hermes`. s6‑супервізор у кожному контейнері керує власним набором профілів; спільне використання тому даних між контейнерами пошкоджує файли сесій та сховища пам’яті.
## Куди потрапляють логи

У s6‑контейнері є чотири окремі поверхні логів, і питання «чому мій gateway нічого не показує у `docker logs`» часто викликає здивування. Шпаргалка:

| Джерело | Куди потрапляє | Як читати |
|---|---|---|
| **Per‑profile gateway** (`hermes gateway run` та per‑profile gateways під s6) | Дублюється в два місця: `docker logs <container>` (реальний час, без додаткового префікса) **і** `${HERMES_HOME}/logs/gateways/<profile>/current` (ротація, мітка часу ISO‑8601, 10 архівів × 1 МБ кожен) | `docker logs -f hermes` або `tail -F ~/.hermes/logs/gateways/default/current` на хості |
| **Dashboard** (коли `HERMES_DASHBOARD=1`) | `docker logs <container>` (без префікса) | `docker logs -f hermes` — перемішано з рядками gateway |
| **Boot reconciler** (реєструє, які gateway профілів були відновлені при кожному запуску контейнера) | `${HERMES_HOME}/logs/container-boot.log` (лог аудиту лише для додавання) | `tail -F ~/.hermes/logs/container-boot.log` |
| **Generic Hermes logs** (`agent.log`, `errors.log`) | `${HERMES_HOME}/logs/` (profile‑aware) | `docker exec hermes hermes logs --follow [--level WARNING] [--session <id>]` |

Два практичні наслідки, які варто знати:

- Копія файлу в `logs/gateways/<profile>/current` — це те, що зберігається після перезапуску контейнера. `docker logs` зберігає лише вивід протягом поточного життєвого циклу контейнера (і стирається при `docker rm`); ротаційні файли залишаються у змонтованому томі.
- Формат рядка аудиту boot reconciler виглядає так: `<iso-timestamp> profile=<name> prior_state=<state> action=<registered|started>`, тому швидкий `grep profile=coder ~/.hermes/logs/container-boot.log` покаже, коли даний профіль був останній раз відновлений і чи auto‑start s6 його запустив.
## Перенаправлення змінних середовища

API‑ключі читаються з `/opt/data/.env` всередині контейнера. Ти також можеш передавати змінні середовища безпосередньо:

```sh
docker run -it --rm \
  -v ~/.hermes:/opt/data \
  -e ANTHROPIC_API_KEY="sk-ant-..." \
  -e OPENAI_API_KEY="sk-..." \
  nousresearch/hermes-agent
```

Прямі прапорці `-e` перезаписують значення з `.env`. Це корисно для інтеграцій CI/CD або менеджерів секретів, коли не хочеш зберігати ключі на диску.

:::note Шукаєш Docker як **термінальний бекенд**?
Ця сторінка охоплює запуск Hermes безпосередньо в Docker. Якщо ти хочеш, щоб Hermes виконував виклики `terminal` / `execute_code` агента всередині контейнера‑пісочниці Docker (один довгоживучий контейнер, спільний для процесів Hermes — див. issue #20561), це окремий блок конфігурації — `terminal.backend: docker` плюс `terminal.docker_image`, `terminal.docker_volumes`, `terminal.docker_forward_env`, `terminal.docker_env`, `terminal.docker_run_as_host_user`, `terminal.docker_extra_args`, `terminal.docker_persist_across_processes` та `terminal.docker_orphan_reaper`. Дивись [Configuration → Docker Backend](configuration.md#docker-backend) для повного набору, включаючи правила життєвого циклу контейнера.
:::
## Приклад Docker Compose

Для постійного розгортання з одночасним запуском шлюзу та dashboard зручний `docker-compose.yaml`:

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

Запусти `docker compose up -d` і переглядай логи за допомогою `docker compose logs -f`. Стандартний вивід (stdout) керованого шлюзу також дублюється у `${HERMES_HOME}/logs/gateways/<profile>/current` на томі — дивись [Where the logs go](#where-the-logs-go) для повної карти маршрутизації.
## Додатково: аудіоміст для Linux‑десктопу

Режим голосу в Docker потребує двох окремих умов: Hermes має мати дозвіл на запит аудіопристроїв всередині контейнера, і контейнер повинен мати можливість підключитися до аудіосервера хоста. Нижче наведено налаштування, яке забезпечує підключення аудіо хоста для Linux‑десктопів, що експортують сокет, сумісний з PulseAudio, включаючи багато налаштувань PipeWire.

:::caution
Це обхідний метод для Linux‑десктопу, а не загальна функція Docker Desktop. Він корисний, коли у тебе вже працює аудіо хоста і ти хочеш використовувати режим голосу в CLI всередині контейнера Hermes. Якщо Hermes все ще виводить `Running inside Docker container -- no audio devices`, використай збірку, яка включає підтримку запиту аудіо Docker для `PULSE_SERVER` / `PIPEWIRE_REMOTE`.
:::

Спочатку створіть конфігурацію ALSA поруч із файлом Compose:

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

Потім зберіть невеликий похідний образ з встановленим плагіном ALSA PulseAudio:

```dockerfile title="Dockerfile.audio"
FROM nousresearch/hermes-agent:latest

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends libasound2-plugins \
    && rm -rf /var/lib/apt/lists/*
```

Використай цей образ у Compose і передай сокет PulseAudio користувача хоста та cookie:

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

Запусти його з UID/GID твого хоста, щоб процес у контейнері міг отримати доступ до користувацького аудіо‑сокету:

```sh
export HERMES_UID="$(id -u)"
export HERMES_GID="$(id -g)"
docker compose up -d --build
```

Щоб перевірити, що PortAudio бачить всередині контейнера:

```sh
docker exec hermes /opt/hermes/.venv/bin/python -c "import sounddevice as sd; print(sd.query_devices())"
```
## Обмеження ресурсів

Контейнер Hermes потребує помірних ресурсів. Рекомендовані мінімальні значення:

| Ресурс | Мінімум | Рекомендовано |
|----------|---------|---------------|
| Пам'ять | 1 ГБ | 2–4 ГБ |
| CPU | 1 ядро | 2 ядра |
| Диск (том даних) | 500 МБ | 2+ ГБ (зростає разом із сесіями/інструментами) |

Автоматизація браузера (Playwright/Chromium) — це найбільш пам'яттєємна функція. Якщо тобі не потрібні інструменти браузера, 1 ГБ достатньо. При активних інструментах браузера виділи принаймні 2 ГБ.

Встанови обмеження у Docker:

```sh
docker run -d \
  --name hermes \
  --restart unless-stopped \
  --memory=4g --cpus=2 \
  -v ~/.hermes:/opt/data \
  nousresearch/hermes-agent gateway run
```
## Що робить Dockerfile

Офіційний образ базується на `debian:13.4` і включає:

- Python 3 зі всіма залежностями Hermes (`uv pip install -e ".[all]"`)
- Node.js + npm (для автоматизації браузера та мосту WhatsApp)
- Playwright з Chromium (`npx playwright install --with-deps chromium --only-shell`)
- ripgrep, ffmpeg, git та `xz-utils` як системні утиліти
- **`docker-cli`** — щоб агенти, що працюють у контейнері, могли керувати Docker‑демоном хоста (bind‑mount `/var/run/docker.sock` для підключення) для `docker build`, `docker run`, інспекції контейнерів тощо.
- **`openssh-client`** — дозволяє використовувати [SSH terminal backend](/user-guide/configuration#ssh-backend) всередині контейнера. SSH‑бекенд викликає системний бінарний файл `ssh`; без цього він тихо падав у контейнеризованих інсталяціях.
- Міст WhatsApp (`scripts/whatsapp-bridge/`)
- **[`s6-overlay`](https://github.com/just-containers/s6-overlay) v3** як PID 1 (замінює старий `tini`) — контролює dashboard та шлюзи per‑profile з автоматичним перезапуском при збоях, прибирає зомбі‑процеси та передає сигнали.

`ENTRYPOINT` контейнера — це `/init` від s6‑overlay. При запуску він:

1. Виконує `/etc/cont-init.d/01-hermes-setup` (= `docker/stage2-hook.sh`) від root: необов’язкове переназначення UID/GID, виправлення прав власності томів, ініціалізація `.env` / `config.yaml` / `SOUL.md` під час першого запуску, синхронізація вбудованих інструментів.
2. Виконує `/etc/cont-init.d/02-reconcile-profiles` (= `hermes_cli.container_boot`): обходить `$HERMES_HOME/profiles/<name>/`, відтворює слот сервісу шлюзу per‑profile у `/run/service/gateway-<profile>/` і автоматично запускає лише ті, у яких останній записаний стан був `running` (див. [Per-profile gateway supervision](#per-profile-gateway-supervision)).
3. Запускає статичні s6‑rc сервіси `main-hermes` та `dashboard`.
4. Виконує CMD контейнера як головну програму (`/opt/hermes/docker/main-wrapper.sh`), яка маршрутизує аргументи, передані користувачем у `docker run`:
   - без аргументів → `hermes` (за замовчуванням)
   - перший аргумент — виконуваний файл у PATH (наприклад `sleep`, `bash`) → виконати його безпосередньо
   - будь‑що інше → `hermes <args>` (проброс підкоманди)

Контейнер завершується, коли ця головна програма завершується, повертаючи її код виходу.

:::warning Змінений підхід порівняно з образами до s6
Тепер `ENTRYPOINT` контейнера — це `/init` (s6‑overlay), а не `/usr/bin/tini`. Усі п’ять задокументованих варіантів виклику `docker run` (без аргументів, `chat -q "…"`, `sleep infinity`, `bash`, `--tui`) працюють ідентично образу на базі tini. Якщо у вас є обгортка, що залежить від поведінки сигналів tini або ж жорстко закодованого виклику `/usr/bin/tini --`, закріпіть попередній тег образу.
:::

:::warning Модель привілеїв
Не перевизначайте entrypoint образу, якщо не залишаєте `/init` (або, еквівалентно, legacy‑скрипт `docker/entrypoint.sh`, який передає управління stage2‑hook) у ланцюжку команд. `/init` від s6‑overlay запускається від root, щоб змінити власника тому під час першого запуску, а потім переходить до користувача `hermes` через `s6-setuidgid` для кожного контрольованого сервісу ТА для головної програми. Запуск `hermes gateway run` від root в офіційному образі за замовчуванням заборонений, бо може залишити файли, що належать root, у `/opt/data` і зламати подальші запуски dashboard або шлюзів. Встановлюй `HERMES_ALLOW_ROOT_GATEWAY=1` лише коли свідомо приймаєш цей ризик.
:::

### `docker exec` автоматично переходить до користувача `hermes`

`docker exec hermes <cmd>` за замовчуванням виконується від root у контейнері, проте образ постачає тонкий shim у `/opt/hermes/bin/hermes` (найраніше у PATH), який виявляє виклики від root і прозоро пере‑виконує їх через `s6-setuidgid hermes`. Тому `docker exec hermes login`, `docker exec hermes profile create …`, `docker exec hermes setup` тощо записують файли, що належать UID 10000 — тобто доступні контрольованому шлюзу — без додаткового прапорця `--user`. Виклики від не‑root (самі контрольовані процеси, `docker exec --user hermes`, підагенти kanban у контейнері) швидко переходять до виконання бінарника venv без накладних витрат.

Якщо потрібен `docker exec`, який зберігає root‑семантику (діагностичні сесії, інспекція стану лише для root, файли поза `/opt/data`, що належать root), відмовся від автоматичного переходу під час виклику:

```sh
docker exec -e HERMES_DOCKER_EXEC_AS_ROOT=1 hermes <cmd>
```

Shim приймає `1` / `true` / `yes` (без урахування регістру). Будь‑що інше — включаючи помилки типу `=0` — проходить до переходу, тому тихих відмов немає. Якщо `s6-setuidgid` недоступний (кастомні збірки без s6‑overlay), shim відмовляє запуску від root і виходить з кодом 126, явно повідомляючи про порушену модель привілеїв, а не дозволяючи історичну помилку, коли `docker exec hermes login` записував `auth.json` як `root:root` і зламав аутентифікацію шлюзу.

### Контроль шлюзу per‑profile

Кожен профіль, створений командою `hermes profile create <name>`, автоматично отримує s6‑контрольований сервіс шлюзу, зареєстрований у `/run/service/gateway-<name>/`, з автоперезапуском, що зберігає стан між перезапусками контейнера. Дивись [Multi-profile support](#multi-profile-support) вище для користувацького процесу та команд життєвого циклу.

**Переваги контролю над образом до s6:**

- Збої шлюзу автоматично перезапускаються `s6-supervise` після ~1 секунди затримки.
- Dashboard, коли ввімкнено `HERMES_DASHBOARD=1`, контролюється в тому ж дереві і отримує таке ж автоматичне перезапускання.
- `docker restart` зберігає запущені шлюзи: cont‑init реконциліатор читає `$HERMES_HOME/profiles/<name>/gateway_state.json` і піднімає слот, якщо останній записаний стан був `running`. Зупинені шлюзи залишаються зупиненими.
- Логи шлюзів per‑profile зберігаються у `$HERMES_HOME/logs/gateways/<profile>/current` (ротація через `s6-log`), а дії реконциліатора додаються до `$HERMES_HOME/logs/container-boot.log` при кожному запуску. Дивись [Where the logs go](#where-the-logs-go) для повної карти маршрутизації.

`hermes status` у контейнері показує `Manager: s6 (container supervisor)`. Використовуй `/command/s6-svstat /run/service/gateway-<name>` для перегляду сирого стану контролера (зауваж, `/command/` знаходиться у PATH лише для процесів контрольного дерева; передавай абсолютний шлях, коли викликаєш з `docker exec`).
## Оновлення

Отримай останній образ і створити контейнер заново. Твій каталог даних залишиться незмінним.

```sh
docker pull nousresearch/hermes-agent:latest
docker rm -f hermes
docker run -d \
  --name hermes \
  --restart unless-stopped \
  -v ~/.hermes:/opt/data \
  nousresearch/hermes-agent gateway run
```

Or with Docker Compose:

```sh
docker compose pull
docker compose up -d
```
## Skills та credential files

Коли використовується Docker як середовище виконання (не методи, описані вище, а коли агент виконує команди всередині Docker‑пісочниці — див. [Configuration → Docker Backend](./configuration.md#docker-backend)), Hermes повторно використовує один довгоживучий контейнер для всіх викликів інструментів і автоматично bind‑mount’ить каталог skills (`~/.hermes/skills/`) та будь‑які credential files, оголошені skills, у цей контейнер як томи лише для читання. Скрипти skills, шаблони та посилання доступні всередині пісочниці без ручної конфігурації, і оскільки контейнер зберігається протягом усього життєвого циклу процесу Hermes, будь‑які залежності, які ти встановиш, або файли, які ти створиш, залишаються доступними для наступного виклику інструменту.

Те саме синхронізується для бекендів SSH та Modal — skills та credential files завантажуються за допомогою rsync або Modal mount API перед кожною командою.
## Встановлення додаткових інструментів у контейнері

Офіційний образ постачається з підготовленим набором утиліт (див. [What the Dockerfile does](#what-the-dockerfile-does)), але не кожен інструмент, який може знадобитися агенту, попередньо встановлений. Є п’ять рекомендованих підходів у порядку збільшення зусиль та довговічності.

### npm або Python інструменти — використай `npx` або `uvx`

Для будь‑якого інструменту, опублікованого в npm або PyPI, дай Hermes запустити його через `npx` (npm) або `uvx` (Python) і запам’ятати цю команду у його постійній пам’яті. Якщо інструмент потребує конфігураційного файлу або облікових даних, дай йому розмістити їх у `/opt/data` (наприклад, `/opt/data/<tool>/config.yaml`).

Залежності завантажуються за потребою та кешуються протягом життя контейнера. Конфігурація, записана у `/opt/data`, зберігається після перезапуску контейнера, оскільки розташована у змонтованій директорії хоста. Сам кеш пакетів відновлюється після `docker rm`, але `npx` і `uvx` повторно завантажують його прозоро під час наступного запуску інструменту.

### Інші інструменти (apt‑пакети, бінарники) — встановити і запам’ятати

Для всього, що не входить до npm або PyPI — `apt`‑пакети, готові бінарники, середовища виконання мов, яких немає в образі — дай Hermes інструкції, як їх встановити (наприклад, `apt-get update && apt-get install -y <package>`) і попроси його запам’ятати команду встановлення. Інструмент залишиться доступним протягом усього часу життя контейнера, і Hermes повторно виконає команду встановлення після перезапуску контейнера, коли інструмент знову знадобиться.

Це підходить для інструментів, які швидко встановлюються і використовуються час від часу. Для інструментів, що використовуються постійно, краще обрати наступний підхід.

### Довговічні встановлення — створити похідний образ

Коли інструмент має бути доступний одразу при кожному запуску контейнера без затримки на повторне встановлення, створіть новий образ, який успадковує `nousresearch/hermes-agent` і встановлює інструмент у окремому шарі:

```dockerfile
FROM nousresearch/hermes-agent:latest

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends <your-package> \
    && rm -rf /var/lib/apt/lists/*
USER hermes
```

Збудуйте його і використайте замість офіційного образу:

```sh
docker build -t my-hermes:latest .
docker run -d \
  --name hermes \
  --restart unless-stopped \
  -v ~/.hermes:/opt/data \
  -p 8642:8642 \
  my-hermes:latest gateway run
```

Скрипт `entrypoint` та семантика `/opt/data` успадковуються без змін, тому решта цієї сторінки залишається актуальною. Не забудьте перебудувати образ при оновленні базового `nousresearch/hermes-agent`.

### Складні інструменти або багатосервісні стеки — запустити sidecar‑контейнер

Для інструментів, які постачають власний сервіс (база даних, веб‑сервер, черга, ферма безголових браузерів) або занадто важкі, щоб працювати всередині контейнера Hermes, запустіть їх у окремому контейнері в спільній Docker‑мережі. Hermes підключається до sidecar за ім’ям контейнера, так само, як підключається до локального inference‑серверу (див. [Connecting to local inference servers](#connecting-to-local-inference-servers-vllm-ollama-etc)).

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

Зсередини контейнера Hermes sidecar доступний за адресою `http://my-tool:<port>` (або іншим протоколом, яким він обслуговується). Такий підхід дозволяє кожному сервісу мати власний життєвий цикл, обмеження ресурсів та графік оновлень, а також запобігає роздуванню образу Hermes залежностями, потрібними лише одному інструменту.

### Широко корисні інструменти — відкрий issue або pull request

Якщо інструмент може бути корисним більшості користувачів Hermes Agent, розглянь можливість внести його в upstream, а не тримати в приватному похідному образі. Відкрий issue або pull request у [hermes-agent repository](https://github.com/NousResearch/hermes-agent), описавши інструмент і його випадок використання. Інструменти, які потрапляють до офіційного образу, приносять користь усім користувачам і зменшують навантаження на підтримку downstream‑форку.
## Підключення до локальних серверів інференції (vLLM, Ollama тощо)

Коли Hermes запускається в Docker, а твій сервер інференції (vLLM, Ollama, text-generation-inference тощо) також працює на хості або в іншому контейнері, мережеві налаштування потребують додаткової уваги.

### Docker Compose (рекомендовано)

Розмісти обидві служби в одній Docker‑мережі. Це найнадійніший підхід:

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

Потім у файлі `~/.hermes/config.yaml` використай **назву контейнера** як ім’я хоста:

```yaml
model:
  provider: custom
  model: my-model
  base_url: http://vllm:8000/v1
  api_key: "none"
```

:::tip Ключові моменти
- Використовуй **назву контейнера** (`vllm`) як ім’я хоста — а не `localhost` чи `127.0.0.1`, які вказують на сам контейнер Hermes.
- Значення `model` має збігатися з `--served-model-name`, який ти передав vLLM.
- Встанови `api_key` у будь‑який непорожній рядок (vLLM вимагає заголовок, але за замовчуванням його не перевіряє).
- **Не** додавай кінцевий слеш у `base_url`.
:::

### Окремий запуск Docker (без Compose)

Якщо сервер інференції працює безпосередньо на хості (не в Docker), використай `host.docker.internal` на macOS/Windows або `--network host` на Linux:

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

**Linux (host networking):**

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

:::warning При використанні `--network host` прапорець `-p` ігнорується — усі порти контейнера відкриваються безпосередньо на хості.
:::

### Перевірка з’єднання

Зсередини контейнера Hermes переконайся, що сервер інференції доступний:

```sh
docker exec hermes curl -s http://vllm:8000/v1/models
```

Ти маєш отримати JSON‑відповідь зі списком твоєї серверованої моделі. Якщо це не вдається, перевір:

1. Обидва контейнери знаходяться в одній Docker‑мережі (`docker network inspect hermes-net`)
2. Сервер інференції слухає на `0.0.0.0`, а не на `127.0.0.1`
3. Номер порту збігається

### Ollama

Ollama працює так само. Якщо Ollama запущена на хості, використай `host.docker.internal:11434` (macOS/Windows) або `127.0.0.1:11434` (Linux з `--network host`). Якщо Ollama працює в окремому контейнері в тій самій Docker‑мережі:

```yaml
model:
  provider: custom
  model: llama3
  base_url: http://ollama:11434/v1
  api_key: "none"
```
## Усунення проблем

### Контейнер завершує роботу одразу

Перевір журнали: `docker logs hermes`. Типові причини:
- Відсутній або неправильний файл `.env` — спочатку запусти інтерактивно, щоб завершити налаштування
- Конфлікти портів, якщо запускаєш з відкритими портами

### Помилки «Permission denied»

Хук stage2 контейнера знижує привілеї до користувача без прав root `hermes` (UID 10000) за допомогою `s6-setuidgid` у кожному підконтрольному сервісі. Якщо у твоєму домашньому каталозі `~/.hermes/` власником є інший UID, встанови `HERMES_UID`/`HERMES_GID` — або їхні псевдоніми `PUID`/`PGID`, як у образах LinuxServer.io та NAS — щоб вони відповідали користувачеві хоста, або переконайся, що каталог даних доступний для запису:

```sh
chmod -R 755 ~/.hermes
```

На NAS (UGOS, Synology, unRAID) каталог даних зазвичай є **bind mount**‑ом, власником якого є UID хоста, який контейнер не може `chown`. Встанови `PUID`/`PGID` (або `HERMES_UID`/`HERMES_GID`) на цього користувача хоста, щоб під час виконання процес працював від імені власника монту, а не UID 10000:

```sh
docker run -d \
  --name hermes \
  -e PUID=1000 -e PGID=10 \
  -v /volume1/docker/hermes:/opt/data \
  nousresearch/hermes-agent gateway run
```

`docker exec hermes <cmd>` також автоматично переходить на UID 10000 — дивись [`docker exec` automatically drops to the `hermes` user](#docker-exec-automatically-drops-to-the-hermes-user) для деталей та можливості вимкнути це для окремого виклику.

### Інструменти браузера не працюють

Playwright потребує спільної пам’яті. Додай `--shm-size=1g` до команди запуску Docker:

```sh
docker run -d \
  --name hermes \
  --shm-size=1g \
  -v ~/.hermes:/opt/data \
  nousresearch/hermes-agent gateway run
```

### Шлюз не перепідключається після проблем з мережею

Параметр `--restart unless-stopped` обробляє більшість тимчасових збоїв. Якщо шлюз завис, перезапусти контейнер:

```sh
docker restart hermes
```

### Перевірка стану контейнера

```sh
docker logs --tail 50 hermes          # Recent logs
docker run -it --rm nousresearch/hermes-agent:latest version     # Verify version
docker stats hermes                    # Resource usage
```