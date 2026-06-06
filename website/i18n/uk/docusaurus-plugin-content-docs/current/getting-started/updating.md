---
sidebar_position: 3
title: "Оновлення та видалення"
description: "Як оновити Hermes Agent до останньої версії або видалити його"
---

# Оновлення та видалення

## Оновлення

### Встановлення через Git

Онови до останньої версії однією командою:

```bash
hermes update
```

Це завантажує останній код з `main`, оновлює залежності та пропонує налаштувати нові параметри, які були додані після твого останнього оновлення.

### Встановлення через pip

Релізи на PyPI відстежують **теговані версії** (мажорні та мінорні випуски), а не кожен коміт у `main`. Перевір оновлення та онови за допомогою:

```bash
hermes update --check    # see if a newer release is on PyPI
hermes update            # runs pip install --upgrade hermes-agent
```

Або вручну:

```bash
pip install --upgrade hermes-agent    # or: uv pip install --upgrade hermes-agent
```

:::tip
`hermes update` автоматично виявляє нові параметри конфігурації та пропонує їх додати. Якщо ти пропустив це повідомлення, можеш вручну виконати `hermes config check`, щоб побачити відсутні параметри, а потім `hermes config migrate` для їх інтерактивного додавання.
:::

### Що відбувається під час оновлення (встановлення через Git)

Коли ти запускаєш `hermes update`, виконується наступна послідовність кроків:

1. **Знімок даних парування** — зберігається легковаговий знімок стану перед оновленням (охоплює `~/.hermes/pairing/`, правила коментарів Feishu та інші файли стану, які змінюються під час роботи). Відновити можна за допомогою процесу відновлення знімка, описаного у розділі [Snapshots and rollback](../user-guide/checkpoints-and-rollback.md), або витягнувши останній zip‑знімок, який Hermes записав поруч із твоїм каталогом `~/.hermes/`.
2. **Git pull** — завантажує останній код з гілки `main` та оновлює підмодулі.
3. **Перевірка синтаксису після pull + авто‑відкат** — після завантаження Hermes компілює вісім критичних файлів, які імпортуються при кожному виклику `hermes`. Якщо якийсь файл не вдається розпарсити (наприклад, залишився маркер конфлікту злиття або файл випадково обрізаний), Hermes виконує `git reset --hard <pre-pull-sha>`, щоб відкотити інсталяцію і залишити оболонку працездатною. Після виправлення в апстрімі запусти `hermes update` ще раз.
4. **Встановлення залежностей** — виконує `uv pip install -e ".[all]"`, щоб підхватити нові або змінені залежності.
5. **Міграція конфігурації** — виявляє нові параметри, додані після твоєї версії, і пропонує їх встановити.
6. **Авто‑перезапуск gateway** — працюючі gateway оновлюються після завершення оновлення, щоб новий код набув сили одразу. Gateway, керовані сервісом (systemd у Linux, launchd у macOS), перезапускаються через менеджер сервісів. Ручні gateway перезапускаються автоматично, коли Hermes зможе зіставити PID процесу з профілем.

### Оновлення з нестандартної гілки: `--branch`

За замовчуванням `hermes update` стежить за `origin/main`. Передай `--branch <name>`, щоб оновитися з іншої гілки — це корисно для QA‑каналів, функціональних гілок або тестування реліз‑кандидатів:

```bash
hermes update --branch release-candidate
hermes update --check --branch experimental   # preview behindness only
```

Якщо твоя локальна копія знаходиться в іншій гілці, Hermes автоматично збереже будь‑яку незакомічену роботу, переключить HEAD на цільову гілку та виконає pull. Гілки, яких немає локально, автоматично відстежуються з `origin/<name>` (`git checkout -B <name> origin/<name>`). Гілки, яких немає ніде, завершуються помилкою — твої збережені зміни відновлюються перед виходом, тому ти ніколи не залишишся у незвичному стані. Логіка синхронізації лише з `main` автоматично пропускається для гілок, відмінних від `main`.

### Перегляд без застосування змін: `hermes update --check`

Хочеш дізнатися, чи є оновлення, перш ніж завантажувати? Запусти `hermes update --check` — для встановлень через Git він отримує та порівнює коміти з `origin/main`; для встановлень через pip запитує PyPI про останній реліз. Жодні файли не змінюються, gateway не перезапускається. Корисно в скриптах та cron‑завданнях, які працюють лише за наявності оновлення.

### Повний резерв перед оновленням: `--backup`

Для важливих профілів (продакшн‑gateway, спільні інсталяції команди) можна ввімкнути повний резерв перед pull `HERMES_HOME` (конфіг, автентифікація, сесії, skills, парування):

```bash
hermes update --backup
```

Або зробити це поведінкою за замовчуванням для кожного запуску:

```yaml
# ~/.hermes/config.yaml
updates:
  pre_update_backup: true
```

`--backup` раніше був увімкнений за замовчуванням, але додавав кілька хвилин до кожного оновлення у великих домашніх каталогах, тому тепер це опція. Легковаговий знімок даних парування, описаний вище, все ще виконується без умов.

### Windows: інший процес `hermes.exe` вже працює

У Windows `hermes update` відмовиться запускатися, якщо виявить інший процес `hermes.exe`, який тримає виконуваний файл віртуального середовища відкритим — найчастіше це бекенд, запущений через Hermes Desktop, відкритий REPL `hermes` в іншому терміналі або працюючий gateway:

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

Закрий зазначені процеси та запусти команду знову. Якщо ти впевнений, що одночасний процес не завадить (рідко — зазвичай лише коли антивірусний шар помилково блокує файл), передай `--force`, щоб пропустити перевірку. У цьому випадку оновлювач все одно спробує перейменувати `.exe` з експоненціальним затриманням і, у випадку впертої блокування, запланує заміну під час наступного перезавантаження через `MoveFileEx(MOVEFILE_DELAY_UNTIL_REBOOT)`, щоб оновлення могло завершитися.

Очікуваний вивід виглядає так:

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

### Рекомендована перевірка після оновлення

`hermes update` виконує основний шлях оновлення, але швидка перевірка підтвердить, що все встановлено коректно:

1. `git status --short` — якщо дерево несподівано «брудне», перевір перед продовженням.
2. `hermes doctor` — перевіряє конфігурацію, залежності та стан сервісу.
3. `hermes --version` — підтверджує, що версія збільшилась, як очікувалося.
4. Якщо ти користуєшся gateway: `hermes gateway status`.
5. Якщо `doctor` повідомляє про проблеми npm audit: запусти `npm audit fix` у зазначеній директорії.

:::warning Брудне робоче дерево після оновлення
Якщо `git status --short` показує неочікувані зміни після `hermes update`, зупинись і перевір їх перед продовженням. Це зазвичай означає, що локальні модифікації були повторно застосовані поверх оновленого коду або крок залежності оновив lock‑файли.
:::

### Якщо термінал розірвався під час оновлення

`hermes update` захищає себе від випадкової втрати терміналу:

- Оновлення ігнорує `SIGHUP`, тому закриття SSH‑сесії або вікна терміналу більше не вбиває процес посеред інсталяції. Дочірні процеси `pip` і `git` успадковують цей захист, тому Python‑середовище не залишиться наполовину встановленим через розірвану з’єднання.
- Увесь вивід дублюється у `~/.hermes/logs/update.log` під час виконання оновлення. Якщо термінал зник, підключись знову та переглянь лог, щоб дізнатися, чи завершилось оновлення і чи успішно перезапустився gateway:

```bash
tail -f ~/.hermes/logs/update.log
```

- `Ctrl-C` (SIGINT) та завершення системи (SIGTERM) все ще обробляються — це навмисне скасування, а не випадковість.

Тепер не потрібно обгортати `hermes update` у `screen` або `tmux`, щоб пережити розрив терміналу.

### Перевірка поточної версії

```bash
hermes version
```

Порівняй її з останнім релізом на [сторінці випусків GitHub](https://github.com/NousResearch/hermes-agent/releases).

### Оновлення з платформ обміну повідомленнями

Ти можеш оновити безпосередньо з Telegram, Discord, Slack, WhatsApp або Teams, надіславши:

```
/update
```

Це завантажує останній код, оновлює залежності та перезапускає працюючі gateway. Бот на короткий час (зазвичай 5–15 секунд) буде недоступний під час перезапуску, а потім продовжить роботу.

### Ручне оновлення

Якщо ти встановив вручну (не через швидкий інсталятор):

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

### Інструкції щодо відкату

Якщо оновлення принесло проблему, можна відкотитися до попередньої версії:

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

Щоб відкотитися до конкретного тегу релізу (підстав свій попередній тег — наприклад, недавній реліз `v2026.5.16` або будь‑який старіший тег з `git tag --sort=-version:refname`):

```bash
git checkout vX.Y.Z
git submodule update --init --recursive
uv pip install -e ".[all]"
```

:::warning
Відкат може спричинити несумісність конфігурації, якщо після оновлення були додані нові параметри. Після відкату запусти `hermes config check` і видали будь‑які невідомі параметри з `config.yaml`, якщо виникнуть помилки.
:::

### Примітка для користувачів Nix

Якщо ти встановив через Nix flake, оновлення керуються менеджером пакетів Nix:

```bash
# Update the flake input
nix flake update hermes-agent

# Or rebuild with the latest
nix profile upgrade hermes-agent
```

Інсталяції Nix є незмінними — відкат здійснюється системою генерацій Nix:

```bash
nix profile rollback
```

Дивись [Nix Setup](./nix-setup.md) для докладніших відомостей.

---

## Видалення

### Встановлення через Git

```bash
hermes uninstall
```

Деінсталятор пропонує залишити файли конфігурації (`~/.hermes/`) для майбутньої повторної інсталяції.

### Встановлення через pip

```bash
pip uninstall hermes-agent
rm -rf ~/.hermes            # Optional — keep if you plan to reinstall
```

### Ручне видалення

```bash
rm -f ~/.local/bin/hermes
rm -rf /path/to/hermes-agent
rm -rf ~/.hermes            # Optional — keep if you plan to reinstall
```

:::info
Якщо ти встановив gateway як системний сервіс, спочатку зупини та вимкни його:
```bash
hermes gateway stop
# Linux: systemctl --user disable hermes-gateway
# macOS: launchctl remove ai.hermes.gateway
```
:::