---
sidebar_position: 1
title: "Довідник команд CLI"
description: "Авторитетне посилання на команди терміналу Hermes та сімейства команд"
---

# Довідник команд CLI

Ця сторінка охоплює **термінальні команди**, які ти запускаєш у своєму шеллі.

Для команд зі слешем у чаті дивись [Довідник команд зі слешем](./slash-commands.md).
## Глобальна точка входу

```bash
hermes [global-options] <command> [subcommand/options]
```

### Глобальні параметри

| Опція | Опис |
|--------|-------------|
| `--version`, `-V` | Показати версію та вийти. |
| `--profile <name>`, `-p <name>` | Вибрати, який профіль Hermes використовувати для цього виклику. Перезаписує постійний типовий профіль, встановлений командою `hermes profile use`. |
| `--resume <session>`, `-r <session>` | Відновити попередню сесію за ID або назвою. |
| `--continue [name]`, `-c [name]` | Відновити останню сесію або останню сесію, що відповідає назві. |
| `--worktree`, `-w` | Запуститися в ізольованому git worktree для паралельних робочих процесів агентів. |
| `--yolo` | Обійти запити підтвердження небезпечних команд. |
| `--pass-session-id` | Включити ID сесії у системний запит агента. |
| `--ignore-user-config` | Ігнорувати `~/.hermes/config.yaml` і повернутись до вбудованих типових налаштувань. Облікові дані у `.env` все ще завантажуються. |
| `--ignore-rules` | Пропустити автоматичне впровадження `AGENTS.md`, `SOUL.md`, `.cursorrules`, пам’яті та попередньо завантажених інструментів. |
| `--tui` | Запустити [TUI](../user-guide/tui.md) замість класичного CLI. Еквівалентно `HERMES_TUI=1`. |
| `--dev` | З `--tui`: запускати TypeScript‑джерела безпосередньо через `tsx` замість попередньо зібраного пакету (для учасників розробки TUI). |
## Команди верхнього рівня

| Команда | Призначення |
|---------|-------------|
| `hermes chat` | Інтерактивний або одноразовий чат з агентом. |
| `hermes model` | Інтерактивний вибір провайдера та моделі за замовчуванням. |
| `hermes fallback` | Керування запасними (варіант) провайдерами, які пробуються при помилці основної моделі. |
| `hermes gateway` | Запуск або керування сервісом шлюзу обміну повідомленнями. |
| `hermes proxy` | Локальний проксі, сумісний з OpenAI, який підключає облікові дані провайдера OAuth. Дивись [Subscription Proxy](../user-guide/features/subscription-proxy.md). |
| `hermes lsp` | Керування інтеграцією Language Server Protocol (семантична діагностика для `write_file`/`patch`). |
| `hermes setup` | Інтерактивний майстер налаштувань для всієї конфігурації або її частини. |
| `hermes whatsapp` | Налаштування та парування мосту WhatsApp. |
| `hermes slack` | Допоміжні інструменти Slack (наразі: генерація маніфесту додатку з кожною командою як нативним slash). |
| `hermes auth` | Керування обліковими даними — додати, перелічити, видалити, скинути, встановити стратегію. Обробляє OAuth‑потоки для Codex/Nous/Anthropic. |
| `hermes login` / `logout` | **Застаріло** — використовуйте `hermes auth` замість цього. |
| `hermes send` | Надіслати одноразове повідомлення на налаштовану платформу обміну (Telegram, Discord, Slack, Signal, SMS, …). Корисно в скриптах оболонки, cron‑завданнях, CI‑хуках та моніторингових демонах — без циклу агента, без LLM. |
| `hermes secrets` | Керування зовнішніми джерелами секретів (наразі Bitwarden Secrets Manager) для отримання API‑ключів під час запуску процесу замість `~/.hermes/.env`. |
| `hermes migrate` | Діагностика та (за потреби) переписування `config.yaml` для заміни посилань на вилучені моделі або застарілі налаштування (наприклад, `migrate xai`). |
| `hermes status` | Показати стан агента, автентифікації та платформи. |
| `hermes cron` | Перегляд та запуск планувальника cron. |
| `hermes kanban` | Дошка співпраці з кількома профілями (завдання, посилання, диспетчер). |
| `hermes webhook` | Керування динамічними підписками webhook для активації за подіями. |
| `hermes hooks` | Перегляд, схвалення або видалення скриптових хуків, оголошених у `config.yaml`. |
| `hermes doctor` | Діагностика проблем конфігурації та залежностей. |
| `hermes security audit` | За запитом аудит ланцюжка постачання (OSV.dev) для venv, вимог плагінів та зафіксованих серверів MCP. |
| `hermes dump` | Підсумок налаштувань, готовий до копіювання/вставки, для підтримки/налагодження. |
| `hermes debug` | Інструменти налагодження — завантаження журналів та інформації про систему для підтримки. |
| `hermes backup` | Резервне копіювання домашнього каталогу Hermes у zip‑файл. |
| `hermes checkpoints` | Перегляд / очищення / видалення `~/.hermes/checkpoints/` (тіньового сховища, що використовується `/rollback`). Запуск без аргументів — огляд стану. |
| `hermes import` | Відновлення резервної копії Hermes з zip‑файлу. |
| `hermes logs` | Перегляд, стеження та фільтрація журналів агента/шлюзу/помилок. |
| `hermes config` | Показ, редагування, міграція та запит конфігураційних файлів. |
| `hermes pairing` | Схвалення або відкликання кодів парування повідомлень. |
| `hermes skills` | Перегляд, встановлення, публікація, аудит та налаштування навичок. |
| `hermes bundles` | Групування кількох навичок під однією slash‑командою `/<name>`. Дивись [Skill Bundles](../user-guide/features/skills.md#skill-bundles). |
| `hermes curator` | Фонове обслуговування навичок — стан, запуск, пауза, закріплення. Дивись [Curator](../user-guide/features/curator.md). |
| `hermes memory` | Налаштування зовнішнього провайдера пам'яті. Підкоманди, специфічні для плагінів (наприклад, `hermes honcho`), реєструються автоматично, коли їх провайдер активний. |
| `hermes acp` | Запуск Hermes як ACP‑сервера для інтеграції з редактором. |
| `hermes mcp` | Керування конфігураціями сервера MCP та запуск Hermes як MCP‑сервера. |
| `hermes plugins` | Керування плагінами Hermes Agent (встановлення, увімкнення, вимкнення, видалення). |
| `hermes portal` | Статус Nous Portal, посилання на підписку та маршрутизація шлюзу інструментів (Tool Gateway). Дивись [Tool Gateway](../user-guide/features/tool-gateway.md). |
| `hermes tools` | Налаштування увімкнених інструментів для кожної платформи. |
| `hermes computer-use` | Встановлення або перевірка бекенду cua-driver (macOS Computer Use). |
| `hermes sessions` | Перегляд, експорт, очищення, перейменування та видалення сесій. |
| `hermes insights` | Показ аналітики токенів/витрат/активності. |
| `hermes claw` | Допоміжні інструменти міграції OpenClaw. |
| `hermes dashboard` | Запуск веб‑дашборду для керування конфігурацією, API‑ключами та сесіями. |
| `hermes profile` | Керування профілями — кілька ізольованих екземплярів Hermes. |
| `hermes completion` | Виведення скриптів автодоповнення для оболонки (bash/zsh/fish). |
| `hermes version` | Показ інформації про версію. |
| `hermes update` | Завантаження останнього коду та переустановка залежностей (git‑встановлення) або перевірка PyPI та `pip install --upgrade` (pip‑встановлення). `--check` попередньо переглядає без встановлення; `--backup` створює знімок `HERMES_HOME` перед завантаженням. |
| `hermes uninstall` | Видалення Hermes з системи. |
## `hermes chat`

```bash
hermes chat [options]
```

Загальні параметри:

| Параметр | Опис |
|--------|------|
| `-q`, `--query "..."` | Одноразовий, неінтерактивний запит. |
| `-m`, `--model <model>` | Перевизначити модель для цього запуску. |
| `-t`, `--toolsets <csv>` | Увімкнути набір інструментів, розділений комами. |
| `--provider <provider>` | Примусово задати провайдера: `auto`, `openrouter`, `nous`, `openai-codex`, `copilot-acp`, `copilot`, `anthropic`, `gemini`, `google-gemini-cli`, `huggingface`, `novita`, `zai`, `kimi-coding`, `kimi-coding-cn`, `minimax`, `minimax-cn`, `minimax-oauth`, `kilocode`, `xiaomi`, `arcee`, `gmi`, `alibaba`, `alibaba-coding-plan` (alias `alibaba_coding`), `deepseek`, `nvidia`, `ollama-cloud`, `xai` (alias `grok`), `xai-oauth` (alias `grok-oauth`), `qwen-oauth`, `bedrock`, `opencode-zen`, `opencode-go`, `azure-foundry`, `lmstudio`, `stepfun`, `tencent-tokenhub` (alias `tencent`, `tokenhub`). |
| `-s`, `--skills <name>` | Попередньо завантажити один або кілька навичок для сесії (можна вказати кілька разів або через кому). |
| `-v`, `--verbose` | Детальний вивід. |
| `-Q`, `--quiet` | Програмний режим: приховати банер, індикатор, попередній перегляд інструментів. |
| `--image <path>` | Додати локальне зображення до окремого запиту. |
| `--resume <session>` / `--continue [name]` | Відновити сесію безпосередньо з `chat`. |
| `--worktree` | Створити ізольований git‑worktree для цього запуску. |
| `--checkpoints` | Увімкнути контрольні точки файлової системи перед руйнівними змінами файлів. |
| `--yolo` | Пропустити запити підтвердження. |
| `--pass-session-id` | Передати ідентифікатор сесії у системний запит. |
| `--ignore-user-config` | Ігнорувати `~/.hermes/config.yaml` і використовувати вбудовані значення за замовчуванням. Облікові дані з `.env` все ще завантажуються. Корисно для ізольованих CI‑запусків, відтворюваних звітів про помилки та сторонніх інтеграцій. |
| `--ignore-rules` | Пропустити автоматичне підключення `AGENTS.md`, `SOUL.md`, `.cursorrules`, постійної пам’яті та попередньо завантажених навичок. Поєднуй з `--ignore-user-config` для повністю ізольованого запуску. |
| `--source <tag>` | Тег джерела сесії для фільтрації (за замовчуванням: `cli`). Використовуй `tool` для сторонніх інтеграцій, які не повинні з’являтися у списках користувацьких сесій. |
| `--max-turns <N>` | Максимальна кількість ітерацій виклику інструментів за один хід розмови (за замовчуванням: 90 або `agent.max_turns` у конфігурації). |

Приклади:

```bash
hermes
hermes chat -q "Summarize the latest PRs"
hermes chat --provider openrouter --model anthropic/claude-sonnet-4.6
hermes chat --toolsets web,terminal,skills
hermes chat --quiet -q "Return only JSON"
hermes chat --worktree -q "Review this repo and open a PR"
hermes chat --ignore-user-config --ignore-rules -q "Repro without my personal setup"
```

### `hermes -z <prompt>` — скриптовий одноразовий запуск

Для програмних викликів (shell‑скрипти, CI, cron, батьківські процеси, що передають запит) `hermes -z` — найчистіший одноразовий вхід: **один запит на вхід, фінальний текст відповіді на вихід, нічого більше у stdout чи stderr.** Без банеру, без індикатора, без попереднього перегляду інструментів, без рядка `Session:` — лише остаточна відповідь агента у вигляді простого тексту.

```bash
hermes -z "What's the capital of France?"
# → Paris.

# Parent scripts can cleanly capture the response:
answer=$(hermes -z "summarize this" < /path/to/file.txt)
```

Перезапис параметрів під час запуску (без зміни `~/.hermes/config.yaml`):

| Прапорець | Еквівалентна змінна середовища | Призначення |
|---|---|---|
| `-m` / `--model <model>` | `HERMES_INFERENCE_MODEL` | Перевизначити модель для цього запуску |
| `--provider <provider>` | _(none)_ | Перевизначити провайдера для цього запуску |

```bash
hermes -z "…" --provider openrouter --model openai/gpt-5.5
# or:
HERMES_INFERENCE_MODEL=anthropic/claude-sonnet-4.6 hermes -z "…"
```

Той самий агент, ті ж інструменти, ті ж навички — просто видаляє всі інтерактивні та косметичні шари. Якщо потрібен вивід інструментів у транскрипті, використай `hermes chat -q`; `-z` призначений виключно для випадку «хочу лише фінальну відповідь».
## `hermes model`

Інтерактивний провайдер і селектор моделей. **Це команда для додавання нових провайдерів, налаштування API‑ключів та запуску OAuth‑процесів.** Запускай її у терміналі — не всередині активної сесії Hermes.

```bash
hermes model
```

Використовуй, коли потрібно:
- **додати нового провайдера** (OpenRouter, Anthropic, Copilot, DeepSeek, custom тощо)
- увійти в провайдери, що підтримують OAuth (Anthropic, Copilot, Codex, Nous Portal)
- ввести або оновити API‑ключі
- вибрати зі списку моделей конкретного провайдера
- налаштувати власну/самохостовану кінцеву точку
- зберегти новий провайдер за замовчуванням у конфігурації

:::warning hermes model vs /model — know the difference
**`hermes model`** (запускається у терміналі, поза будь‑якою сесією Hermes) — це **повний майстер налаштування провайдера**. Він може додавати нових провайдерів, запускати OAuth‑процеси, запитувати API‑ключі та налаштовувати кінцеві точки.

**`/model`** (вводиться всередині активної сесії Hermes) може лише **перемикати між вже налаштованими провайдерами та моделями**. Він не може додавати нових провайдерів, запускати OAuth чи запитувати API‑ключі.

**Якщо потрібно додати нового провайдера:** спочатку вийди з сесії Hermes (`Ctrl+C` або `/quit`), потім запусти `hermes model` у терміналі.
:::

### `/model` slash command (mid-session)

Перемикай між вже налаштованими моделями, не залишаючи сесію:

```
/model                              # Show current model and available options
/model claude-sonnet-4              # Switch model (auto-detects provider)
/model zai:glm-5                    # Switch provider and model
/model custom:qwen-2.5              # Use model on your custom endpoint
/model custom                       # Auto-detect model from custom endpoint
/model custom:local:qwen-2.5        # Use a named custom provider
/model openrouter:anthropic/claude-sonnet-4  # Switch back to cloud
```

За замовчуванням зміни `/model` застосовуються **лише до поточної сесії**. Додай `--global`, щоб зберегти зміни у `config.yaml`:

```
/model claude-sonnet-4 --global     # Switch and save as new default
```

:::info What if I only see OpenRouter models?
Якщо ти налаштував лише OpenRouter, `/model` покаже лише моделі OpenRouter. Щоб додати інший провайдер (Anthropic, DeepSeek, Copilot тощо), вийди з сесії та запусти `hermes model` у терміналі.
:::

Зміни провайдера та базової URL‑адреси автоматично зберігаються у `config.yaml`. При переході від власної кінцевої точки застаріла базова URL‑адреса очищується, щоб не потрапляти до інших провайдерів.
## `hermes gateway`

```bash
hermes gateway <subcommand>
```

Підкоманди:

| Підкоманда | Опис |
|------------|------|
| `run` | Запустити шлюз у передньому плані. Рекомендовано для WSL, Docker та Termux. |
| `start` | Запустити встановлену службу systemd/launchd у фоні. |
| `stop` | Зупинити службу (або процес у передньому плані). |
| `restart` | Перезапустити службу. |
| `status` | Показати стан служби. |
| `list` | Перелічити **всі профілі** і чи запущений шлюз кожного профілю (з PID, якщо доступний). Зручно, коли ти працюєш з кількома профілями одночасно і потрібен один огляд. |
| `install` | Встановити як службу systemd (Linux) або launchd (macOS) у фоні. |
| `uninstall` | Видалити встановлену службу. |
| `setup` | Інтерактивне налаштування платформи обміну повідомленнями. |

Опції:

| Опція | Опис |
|-------|------|
| `--all` | При `start` / `restart` / `stop`: діяти на **кожному профілі** шлюзу, а не лише на активному `HERMES_HOME`. Корисно, якщо ти запускаєш кілька профілів одночасно і хочеш перезапустити їх усі після `hermes update`. |
| `--no-supervise` | При `run`: у Docker‑образі s6-overlay відмовитися від автоматичного нагляду та використовувати семантику переднього плану без s6 — шлюз працює як головний процес контейнера без автоперезапуску. Не має ефекту поза s6‑образом. Еквівалентно встановленню `HERMES_GATEWAY_NO_SUPERVISE=1`. |

:::tip Користувачі WSL
Використовуй `hermes gateway run` замість `hermes gateway start` — підтримка systemd у WSL ненадійна. Обгорни його у tmux для збереження процесу: `tmux new -s hermes 'hermes gateway run'`. Дивись [WSL FAQ](/reference/faq#wsl-gateway-keeps-disconnecting-or-hermes-gateway-start-fails) для деталей.
:::
## `hermes lsp`

```bash
hermes lsp <subcommand>
```

Керує інтеграцією Language Server Protocol. LSP запускає реальні
мовні сервери (pyright, gopls, rust-analyzer, …) у
фоні та передає їх діагностику у перевірку після запису,
яку використовують `write_file` та `patch`. Активується лише при виявленні git‑робочого простору — LSP працює лише коли cwd або відредагований файл знаходиться у git‑worktree.

Підкоманди:

| Підкоманда | Опис |
|------------|------|
| `status` | Показати стан сервісу, налаштовані сервери, статус встановлення. |
| `list` | Вивести реєстр підтримуваних серверів. Передай `--installed-only`, щоб пропустити відсутні. |
| `install <id>` | Активно встановити бінарний файл одного сервера. |
| `install-all` | Встановити всі сервери, для яких відома автоматична інсталяція. |
| `restart` | Зупинити запущені клієнти, щоб при наступному редагуванні вони перезапустились. |
| `which <id>` | Вивести розв’язаний шлях до бінарного файлу одного сервера. |

Дивись [LSP — Semantic Diagnostics](/user-guide/features/lsp) для
повного посібника, підтримуваних мов та параметрів налаштування.
## `hermes setup`

```bash
hermes setup [model|tts|terminal|gateway|tools|agent] [--non-interactive] [--reset] [--quick] [--reconfigure] [--portal]
```

**Найпростіший шлях:** `hermes setup --portal` — OAuth у Nous Portal і одночасно підключити [Tool Gateway](../user-guide/features/tool-gateway.md).

**Перший запуск:** запускає майстер налаштування для першого використання.

**Повернений користувач (вже налаштовано):** переходить одразу до майстра повторного налаштування — у кожному запиті показане ваше поточне значення як значення за замовчуванням, натисніть **Enter**, щоб залишити його, або введіть нове. Без меню.

Перейти до окремого розділу замість всього майстра:

| Section | Description |
|---------|-------------|
| `model` | Налаштування провайдера та моделі. |
| `terminal` | Налаштування бекенду терміналу та пісочниці. |
| `gateway` | Налаштування платформи обміну повідомленнями. |
| `tools` | Увімкнення/вимкнення інструментів для кожної платформи. |
| `agent` | Параметри поведінки самонавчального агента. |

Опції:

| Option | Description |
|--------|-------------|
| `--quick` | При повторному вході: запитує лише ті елементи, які відсутні або не встановлені. Пропускає вже налаштовані. |
| `--non-interactive` | Використовувати значення за замовчуванням / змінні середовища без запитів. |
| `--reset` | Скинути конфігурацію до значень за замовчуванням перед налаштуванням. |
| `--reconfigure` | Сумісний псевдонім — тепер простий `hermes setup` у вже встановленій системі робить це за замовчуванням. |
| `--portal` | Одноразове налаштування Nous Portal: вхід через OAuth, встановлення Nous як провайдера інференції та підключення до [Tool Gateway](../user-guide/features/tool-gateway.md). Пропускає решту майстра. |
## `hermes portal`

```bash
hermes portal [status|open|tools]
```

Перевір аутентифікацію Nous Portal, маршрутизацію Tool Gateway та перейди на сторінку підписки. Виклик без підкоманди виконує `status`.

| Subcommand | Description |
|------------|-------------|
| `status` (default) | Стан аутентифікації порталу + підсумок маршрутизації Tool Gateway для кожного інструмента. Показується також, коли не вказано підкоманду. |
| `open` | Відкрити `portal.nousresearch.com/manage-subscription` у твоєму типово́му браузері. |
| `tools` | Перелічити всіх партнерів Tool Gateway (Firecrawl, FAL, OpenAI TTS, Browser Use, Modal) і вказати, які маршрутизуються через Nous. |

Для налаштування самого шлюзу дивись [Tool Gateway](../user-guide/features/tool-gateway.md). Для одноразового шляху налаштування дивись `hermes setup --portal` вище.
## `hermes whatsapp`

```bash
hermes whatsapp
```

Запускає процес підключення та налаштування WhatsApp, включаючи вибір режиму та підключення за допомогою QR‑коду.
## `hermes slack`

```bash
hermes slack manifest              # print manifest to stdout
hermes slack manifest --write      # write to ~/.hermes/slack-manifest.json
hermes slack manifest --slashes-only  # just the features.slash_commands array
```

Генерує маніфест Slack‑додатку, який реєструє кожну команду шлюзу в
`COMMAND_REGISTRY` (`/btw`, `/stop`, `/model`, …) як повноцінну
slash‑команду Slack — забезпечуючи паритет з Discord та Telegram. Скопіюй
вивід у конфігурацію свого Slack‑додатку за адресою
[https://api.slack.com/apps](https://api.slack.com/apps) → твій додаток →
**Features → App Manifest → Edit**, потім **Save**. Slack запропонує
перевстановити, якщо змінилися області доступу або slash‑команди.

| Flag | Default | Purpose |
|------|---------|---------|
| `--write [PATH]` | stdout | Записати у файл замість stdout. Само `--write` записує `$HERMES_HOME/slack-manifest.json`. |
| `--name NAME` | `Hermes` | Відображуване ім'я бота у Slack. |
| `--description DESC` | default blurb | Опис бота, який показується в каталозі Slack‑додатків. |
| `--slashes-only` | off | Виводити лише `features.slash_commands` для злиття у вручну підтримуваний маніфест. |

Запусти `hermes slack manifest --write` ще раз після `hermes update`, щоб
підхопити нові команди.
## `hermes send`

```bash
hermes send --to <target> "message text"
hermes send --to <target> --file <path>
echo "message" | hermes send --to <target>
hermes send --list [platform]
```

Надсилає одноразове повідомлення на налаштовану платформу обміну без запуску агента чи циклу шлюзу. Використовує вже налаштовані облікові дані шлюзу (`~/.hermes/.env` + `~/.hermes/config.yaml`), тому скрипти операцій, cron‑завдання, CI‑хуки та демони моніторингу можуть публікувати оновлення статусу без повторної реалізації REST‑клієнта кожної платформи.

Для платформ з токеном бота (Telegram, Discord, Slack, Signal, SMS, WhatsApp‑CloudAPI) не потрібен запущений шлюз — `hermes send` спілкується безпосередньо з REST‑кінцевою точкою платформи. Платформи‑плагіни, яким потрібен постійний адаптер, все ще вимагають живий шлюз.

| Option | Description |
|--------|-------------|
| `-t`, `--to <TARGET>` | Ціль доставки. Формати: `platform` (використовує домашній канал), `platform:chat_id`, `platform:chat_id:thread_id` або `platform:#channel-name`. Приклади: `telegram`, `telegram:-1001234567890`, `discord:#ops`, `slack:C0123ABCD`, `signal:+15551234567`. |
| `-f`, `--file <PATH>` | Прочитати тіло повідомлення з `PATH`. Передай `-`, щоб примусово читати зі stdin. |
| `-s`, `--subject <LINE>` | Додати рядок теми/заголовка перед тілом повідомлення. |
| `-l`, `--list [platform]` | Перелічити налаштовані цілі на всіх платформах (або лише на вказаній платформі). |
| `-q`, `--quiet` | Придушити вивід у stdout при успішному виконанні — корисно в скриптах (спиратись лише на код виходу). |
| `--json` | Вивести сирий JSON‑результат замість людсько‑читабельного виводу. |

Якщо не вказано позиційний аргумент `message` і не використано `--file`, `hermes send` читає зі stdin, коли stdin не є TTY. Коди виходу: `0` — успіх, `1` — помилка доставки/бекенду, `2` — помилки використання.

Examples:

```bash
hermes send --to telegram "deploy finished"
echo "RAM 92%" | hermes send --to telegram:-1001234567890
hermes send --to discord:#ops --file /tmp/report.md
hermes send --to slack:#eng --subject "[CI]" --file build.log
hermes send --list                  # all platforms
hermes send --list telegram         # filter by platform
```
## `hermes secrets`

```bash
hermes secrets bitwarden <subcommand>
hermes secrets bw <subcommand>          # short alias
```

Отримуй API‑ключі з зовнішнього менеджера секретів при запуску процесу замість зберігання їх у `~/.hermes/.env`. Наразі підтримується **Bitwarden Secrets Manager**. Дивись повний посібник: [Bitwarden integration](../user-guide/secrets/bitwarden.md).

Підкоманди `bitwarden` (alias `bw`):

| Subcommand | Description |
|------------|-------------|
| `setup` | Інтерактивний майстер: встановити закріплений бінарник `bws`, зберегти токен доступу та вибрати проєкт. Приймає `--project-id`, `--access-token` та `--server-url` для неінтерактивного використання. |
| `status` | Показати поточну конфігурацію, шлях/версію бінарника та інформацію про останнє отримання. |
| `sync` | Отримати секрети зараз і повідомити, що змінилося. Додай `--apply`, щоб фактично експортувати секрети у середовище поточної оболонки (за замовчуванням — сухий запуск). |
| `install` | Завантажити та перевірити закріплений бінарник `bws`. `--force` перезавантажує, навіть якщо керована копія вже існує. |
| `disable` | Вимкнути інтеграцію з Bitwarden. |
## `hermes migrate`

```bash
hermes migrate <type>
```

Діагностувати та (за потреби) переписати активний `config.yaml`, замінюючи посилання на вилучені моделі або застарілі налаштування. Перед будь‑яким переписуванням створюється резервна копія оригінального `config.yaml` з міткою часу (можна пропустити за допомогою `--no-backup`).

| Subcommand | Description |
|------------|-------------|
| `xai` | Сканувати `config.yaml` на предмет посилань на моделі xAI, заплановані до вилучення 15 травня 2026 р., і (з `--apply`) переписати їх на місці на офіційні замінники згідно з посібником міграції xAI. За замовчуванням — пробний запуск без змін. |

Загальні прапорці для підкоманд міграції:

| Flag | Description |
|------|-------------|
| `--apply` | Переписати `config.yaml` на місці (за замовчуванням: пробний запуск, без запису). |
| `--no-backup` | Пропустити створення резервної копії `config.yaml` з міткою часу під час застосування. |

> Не плутати з `hermes claw migrate` (одноразовий імпорт конфігурації OpenClaw у Hermes) — `hermes migrate` є командою верхнього рівня для переписування конфігурації.
## `hermes proxy`

```bash
hermes proxy <subcommand>
```

Запусти локальний HTTP‑сервер, сумісний з OpenAI, який пересилає запити до upstream‑provider, автентифікованого через OAuth (наприклад, Nous Portal, xAI). Зовнішні додатки можуть звертатися до проксі з будь‑яким bearer‑токеном; проксі додає твої реальні OAuth‑облікові дані під час виходу. Дивись [Subscription Proxy](../user-guide/features/subscription-proxy.md) для повного посібника.

| Subcommand | Description |
|------------|-------------|
| `start` | Запусти проксі у передньому плані. Прапорці: `--provider <nous\|xai>` (за замовчуванням `nous`), `--host <addr>` (за замовчуванням `127.0.0.1`; використай `0.0.0.0`, щоб відкрити в LAN), `--port <int>` (за замовчуванням `8645`). |
| `status` | Показати, які upstream‑proxy готові (облікові дані присутні, OAuth дійсний). |
| `providers` | Перелічити доступних провайдерів upstream‑proxy. |
## `hermes security`

```bash
hermes security <subcommand>
```

Сканування вразливостей за запитом проти [OSV.dev](https://osv.dev). Охоплює venv Hermes (встановлені дистрибутиви PyPI), залежності Python, оголошені плагінами у `~/.hermes/plugins/`, та закріплені сервери `npx`/`uvx` MCP у `config.yaml`. НЕ сканує глобально встановлені пакети або розширення редактора/браузера.

| Subcommand | Description |
|------------|-------------|
| `audit` | Запустити одноразовий аудит ланцюга постачання. |

`audit` flags:

| Flag | Default | Description |
|------|---------|-------------|
| `--json` | off | Вивести машинозчитуваний JSON замість людськочитабельного тексту. |
| `--fail-on <level>` | `critical` | Завершити з ненульовим кодом, коли будь‑яке знаходження має зазначену серйозність (`low`, `moderate`, `high`, `critical`). |
| `--skip-venv` | off | Пропустити сканування Python‑venv Hermes. |
| `--skip-plugins` | off | Пропустити сканування файлів вимог плагінів. |
| `--skip-mcp` | off | Пропустити сканування закріплених серверів MCP у `config.yaml`. |
## `hermes login` / `hermes logout` *(Застарілий)*

:::caution
`hermes login` було видалено. Використовуй `hermes auth` для керування OAuth‑обліковими даними, `hermes model` для вибору провайдера або `hermes setup` для повного інтерактивного налаштування.
:::
## `hermes auth`

Керуйте пулами облікових даних для ротації ключів одного провайдера. Дивіться [Пули облікових даних](/user-guide/features/credential-pools) для повної документації.

```bash
hermes auth                                              # Interactive wizard
hermes auth list                                         # Show all pools
hermes auth list openrouter                              # Show specific provider
hermes auth add openrouter --api-key sk-or-v1-xxx        # Add API key
hermes auth add anthropic --type oauth                   # Add OAuth credential
hermes auth remove openrouter 2                          # Remove by index
hermes auth reset openrouter                             # Clear cooldowns
hermes auth status anthropic                             # Show auth status for a provider
hermes auth logout anthropic                             # Log out and clear stored auth state
hermes auth spotify                                      # Authenticate Hermes with Spotify via PKCE
```

Підкоманди: `add`, `list`, `remove`, `reset`, `status`, `logout`, `spotify`. Якщо викликано без підкоманди, запускає інтерактивний майстер управління.
## `hermes status`

```bash
hermes status [--all] [--deep]
```

| Опція | Опис |
|--------|-------------|
| `--all` | Показати всі деталі у форматі, придатному для спільного використання, з редагуванням. |
| `--deep` | Виконати глибші перевірки, які можуть зайняти більше часу. |
## `hermes cron`

```bash
hermes cron <list|create|edit|pause|resume|run|remove|status|tick>
```

| Subcommand | Description |
|------------|-------------|
| `list` | Показати заплановані завдання. |
| `create` / `add` | Створити заплановане завдання за запитом, за потреби додаючи одну або кілька **skill** за допомогою повторюваного `--skill`. |
| `edit` | Оновити розклад завдання, запит, назву, delivery, кількість повторень або приєднані **skill**. Підтримує `--clear-skills`, `--add-skill` та `--remove-skill`. |
| `pause` | Призупинити завдання без його видалення. |
| `resume` | Відновити призупинене завдання та обчислити його наступний запуск. |
| `run` | Запустити завдання на наступному тикі планувальника. |
| `remove` | Видалити заплановане завдання. |
| `status` | Перевірити, чи працює планувальник **cron**. |
| `tick` | Виконати належні завдання один раз і завершити роботу. |
## `hermes kanban`

```bash
hermes kanban [--board <slug>] <action> [options]
```

Багатопрофільна, багатопроектна дошка співпраці. Кожна інсталяція може містити багато дошок (по одній на проєкт, репозиторій або домен); кожна дошка — це окрема черга зі своєю SQLite‑базою даних і областю диспетчера. Нові інсталяції стартують з однієї дошки під назвою `default`, чия БД розташована у `~/.hermes/kanban.db` для зворотної сумісності; додаткові дошки зберігаються у `~/.hermes/kanban/boards/<slug>/kanban.db`. Вбудований у шлюз диспетчер обробляє кожну дошку на кожному тикі.

**Глобальні прапорці (застосовуються до всіх дій нижче):**

| Прапорець | Призначення |
|------|---------|
| `--board <slug>` | Працювати з конкретною дошкою. За замовчуванням — поточна дошка (встановлена через `hermes kanban boards switch`, змінну середовища `HERMES_KANBAN_BOARD` або `default`). |

**Це інтерфейс для людей / скриптів.** Робочі процеси‑агенти, створені диспетчером, керують дошкою через спеціальний `kanban_*` [toolset](/user-guide/features/kanban#how-workers-interact-with-the-board) (`kanban_show`, `kanban_complete`, `kanban_block`, `kanban_create`, `kanban_link`, `kanban_comment`, `kanban_heartbeat`; профілі‑оркестратори також отримують `kanban_list` і `kanban_unblock`) замість виклику `hermes kanban`. У робочих процесів змінна `HERMES_KANBAN_BOARD` зафіксована в їхньому середовищі, тому вони фізично не бачать інші дошки.

| Дія | Призначення |
|--------|---------|
| `init` | Створити `kanban.db`, якщо її немає. Ідемпотентно. |
| `boards list` / `boards ls` | Перелік усіх дошок з кількістю задач. `--json`, `--all` (включно з архівованими). |
| `boards create <slug>` | Створити нову дошку. Прапорці: `--name`, `--description`, `--icon`, `--color`, `--switch` (зробити активною). `slug` у kebab‑case, автоматично нижнього регістру. |
| `boards switch <slug>` / `boards use` | Записати `<slug>` як активну дошку (у файл `~/.hermes/kanban/current`). |
| `boards show` / `boards current` | Вивести назву поточної активної дошки, шлях до БД та кількість задач. |
| `boards rename <slug> "<name>"` | Змінити відображувану назву дошки. `slug` незмінний. |
| `boards rm <slug>` | Архівувати (за замовчуванням) або жорстко видалити дошку. `--delete` пропускає крок архівації. Архівовані дошки переміщуються до `boards/_archived/<slug>-<ts>/`. Заборонено для `default`. |
| `create "<title>"` | Створити нову задачу на активній дошці. Прапорці: `--body`, `--assignee`, `--parent` (повторюваний), `--workspace scratch\|worktree\|dir:<path>`, `--tenant`, `--priority`, `--triage`, `--idempotency-key`, `--max-runtime`, `--max-retries`, `--skill` (повторюваний). |
| `list` / `ls` | Перелік задач на активній дошці. Фільтри: `--mine`, `--assignee`, `--status`, `--tenant`, `--archived`, `--json`. |
| `show <id>` | Показати задачу разом з коментарями та подіями. `--json` — машинний вивід. |
| `assign <id> <profile>` | Призначити або переназначити. Використай `none` для зняття призначення. Заборонено, доки задача виконується. |
| `link <parent> <child>` | Додати залежність. Виявляє цикли. Обидві задачі мають бути на одній дошці. |
| `unlink <parent> <child>` | Видалити залежність. |
| `claim <id>` | Атомарно захопити готову задачу. Виводить розв’язаний шлях робочого простору. |
| `comment <id> "<text>"` | Додати коментар. Наступний робочий процес, який захопить задачу, прочитає його у відповіді `kanban_show()`. |
| `complete <id>` | Позначити задачу виконаною. Прапорці: `--result`, `--summary`, `--metadata`. |
| `block <id> "<reason>"` | Позначити задачу заблокованою для людського вводу. Також додає причину як коментар. |
| `schedule <id> "<reason>"` | Перемістити задачу у `scheduled` для відкладеної роботи, щоб вона не відображалась як блокування людини. |
| `unblock <id>` | Повернути заблоковану або заплановану задачу у стан готовності (або `todo`, якщо залишаються відкриті залежності). |
| `archive <id>` | Приховати з типового списку. `gc` видалить тимчасові робочі простори. |
| `tail <id>` | Слідкувати за потоком подій задачі. |
| `dispatch` | Один прохід диспетчера по активній дошці. Прапорці: `--dry-run`, `--max N`, `--failure-limit N`, `--json`. |
| `context <id>` | Вивести повний контекст, який бачить робочий процес (заголовок + тіло + результати батьків + коментарі). |
| `specify <id>` / `specify --all` | Перетворити задачу у колонці triage у конкретну специфікацію (заголовок + тіло з метою, підходом, критеріями прийняття) за допомогою допоміжного LLM, потім підвищити її до `todo`. Прапорці: `--tenant` (обмежує `--all` одним тенантом), `--author`, `--json`. Налаштуй модель у `auxiliary.triage_specifier` у `config.yaml`. |
| `decompose <id>` / `decompose --all` | Розбити задачу у колонці triage на граф дочірніх задач, розподілених між спеціалістами‑профілями за описом (шлях, керований оркестратором). При відсутності вигоди від розгалуження повертається до однозадачної промоції у стилі `specify`. Ті ж прапорці, що й у `specify`. Налаштуй модель у `auxiliary.kanban_decomposer` у `config.yaml`. Також виконується автоматично кожного тика диспетчера, коли `kanban.auto_decompose: true` (за замовчуванням). Дивись [Auto vs Manual orchestration](/user-guide/features/kanban#auto-vs-manual-orchestration). |
| `gc` | Видалити тимчасові робочі простори для архівованих задач. |

Приклади:

```bash
# Create a second board and put a task on it without switching away.
hermes kanban boards create atm10-server --name "ATM10 Server" --icon 🎮
hermes kanban --board atm10-server create "Restart server" --assignee ops

# Switch the active board for subsequent calls.
hermes kanban boards switch atm10-server
hermes kanban list                  # shows atm10-server tasks

# Archive a board (recoverable) or hard-delete it.
hermes kanban boards rm atm10-server
hermes kanban boards rm atm10-server --delete
```

Порядок визначення дошки (спочатку найвищий пріоритет): прапорець `--board <slug>` → змінна середовища `HERMES_KANBAN_BOARD` → файл `~/.hermes/kanban/current` → `default`.

Усі дії також доступні як slash‑команда у шлюзі (`/kanban …`) з тим самим набором аргументів — включно з підкомандами `boards` та прапорцем `--board`.

Для повного опису — порівняння з Cline Kanban / Paperclip / NanoClaw / Gemini Enterprise, вісім патернів співпраці, чотири історії користувачів, доказ коректності конкурентності — дивись `docs/hermes-kanban-v1-spec.pdf` у репозиторії або [Kanban user guide](/user-guide/features/kanban).
## `hermes webhook`

```bash
hermes webhook <subscribe|list|remove|test>
```

Керує динамічними підписками на webhook для активації агента за подіями. Потрібно, щоб платформа webhook була ввімкнена в конфігурації — якщо не налаштовано, виводить інструкції зі встановлення.

| Subcommand | Description |
|------------|-------------|
| `subscribe` / `add` | Створити маршрут webhook. Повертає URL та HMAC‑секрет для налаштування у вашому сервісі. |
| `list` / `ls` | Показати всі підписки, створені агентом. |
| `remove` / `rm` | Видалити динамічну підписку. Статичні маршрути з `config.yaml` не зачіпаються. |
| `test` | Надіслати тестовий POST, щоб перевірити, чи працює підписка. |

### `hermes webhook subscribe`

```bash
hermes webhook subscribe <name> [options]
```

| Option | Description |
|--------|-------------|
| `--prompt` | Шаблон запиту з посиланнями на дані `{dot.notation}`. |
| `--events` | Список типів подій через кому, які приймаються (наприклад `issues,pull_request`). Порожньо = всі. |
| `--description` | Людсько‑читабельний опис. |
| `--skills` | Список назв навичок через кому, які завантажуються для запуску агента. |
| `--deliver` | Ціль доставки: `log` (за замовчуванням), `telegram`, `discord`, `slack`, `github_comment`. |
| `--deliver-chat-id` | Ідентифікатор чату/каналу для крос‑платформенної доставки. |
| `--secret` | Користувацький HMAC‑секрет. Автоматично генерується, якщо не вказано. |
| `--deliver-only` | Пропустити агента — доставити відрендерений `--prompt` як буквальне повідомлення. Нульова вартість LLM, доставка за субсекунду. Потрібно, щоб `--deliver` був реальним призначенням (не `log`). |

Підписки зберігаються у `~/.hermes/webhook_subscriptions.json` і автоматично перезавантажуються адаптером webhook без перезапуску **gateway**.
## `hermes doctor`

```bash
hermes doctor [--fix]
```

| Option | Опис |
|--------|------|
| `--fix` | Спробувати автоматично виправити, якщо це можливо. |
## `hermes dump`

```bash
hermes dump [--show-keys]
```

Виводить компактний, простий текстовий підсумок усієї твоєї конфігурації Hermes. Призначений для копіювання у Discord, GitHub issues або Telegram під час запиту підтримки — без ANSI‑кольорів, без спеціального форматування, лише дані.

| Опція | Опис |
|--------|-------------|
| `--show-keys` | Показати засекречені префікси API‑ключів (перші та останні 4 символи) замість просто `set`/`not set`. |

### Що включає

| Розділ | Деталі |
|---------|---------|
| **Header** | Версія Hermes, дата випуску, хеш git‑коміту |
| **Environment** | ОС, версія Python, версія OpenAI SDK |
| **Identity** | Назва активного профілю, шлях HERMES_HOME |
| **Model** | Налаштована модель за замовчуванням та провайдер |
| **Terminal** | Тип бекенду (local, docker, ssh тощо) |
| **API keys** | Перевірка наявності всіх 22 API‑ключів провайдерів/інструментів |
| **Features** | Увімкнені інструменти, кількість серверів MCP, провайдер пам'яті |
| **Services** | Стан шлюзу, налаштовані платформи обміну повідомленнями |
| **Workload** | Кількість cron‑завдань, кількість встановлених skill |
| **Config overrides** | Будь‑які значення конфігурації, що відрізняються від значень за замовчуванням |

### Приклад виводу

```
--- hermes dump ---
version:          0.8.0 (2026.4.8) [af4abd2f]
os:               Linux 6.14.0-37-generic x86_64
python:           3.11.14
openai_sdk:       2.24.0
profile:          default
hermes_home:      ~/.hermes
model:            anthropic/claude-opus-4.6
provider:         openrouter
terminal:         local

api_keys:
  openrouter           set
  openai               not set
  anthropic            set
  nous                 not set
  firecrawl            set
  ...

features:
  toolsets:           all
  mcp_servers:        0
  memory_provider:    built-in
  gateway:            running (systemd)
  platforms:          telegram, discord
  cron_jobs:          3 active / 5 total
  skills:             42

config_overrides:
  agent.max_turns: 250
  compression.threshold: 0.85
  display.streaming: True
--- end dump ---
```

### Коли використовувати

- При повідомленні про помилку на GitHub — встав дамп у свій issue
- Коли просиш допомоги в Discord — поділись ним у кодовому блоці
- Порівнюєш свою конфігурацію з конфігурацією іншого користувача
- Швидка перевірка, коли щось не працює

:::tip
`hermes dump` спеціально створений для поширення. Для інтерактивної діагностики використай `hermes doctor`. Для візуального огляду — `hermes status`.
:::
## `hermes debug`

```bash
hermes debug share [options]
```

Завантажити звіт налагодження (інформація про систему + останні логи) у paste‑service і отримати URL для спільного доступу. Корисно для швидких запитів підтримки — містить усе, що потрібне помічнику для діагностики твоєї проблеми.

| Option | Description |
|--------|-------------|
| `--lines <N>` | Кількість рядків журналу, які включати з кожного файлу логу (за замовчуванням: 200). |
| `--expire <days>` | Термін дії paste в днях (за замовчуванням: 7). |
| `--local` | Вивести звіт локально замість завантаження. |

Звіт включає інформацію про систему (OS, версія Python, Hermes), останні логи агента та gateway (ліміт 512 KB на файл) та статус прихованих API‑ключів. Ключі завжди приховуються — жодних секретів не завантажується.

Paste‑service, які пробуються у порядку: paste.rs, dpaste.com.

### Приклади

```bash
hermes debug share              # Upload debug report, print URL
hermes debug share --lines 500  # Include more log lines
hermes debug share --expire 30  # Keep paste for 30 days
hermes debug share --local      # Print report to terminal (no upload)
```
## `hermes backup`

```bash
hermes backup [options]
```

Створи zip‑архів твоєї конфігурації Hermes, навичок, сесій та даних. Резервна копія не включає сам код `hermes-agent`.

| Option | Description |
|--------|-------------|
| `-o`, `--output <path>` | Шлях виведення для zip‑файлу (за замовчуванням: `~/hermes-backup-<timestamp>.zip`). |
| `-q`, `--quick` | Швидкий знімок: лише критичні файли стану (`config.yaml`, `state.db`, `.env`, `auth`, cron jobs). Значно швидше, ніж повна резервна копія. |
| `-l`, `--label <name>` | Мітка для знімка (використовується лише з `--quick`). |

Резервна копія використовує API `backup()` SQLite для безпечного копіювання, тому працює коректно навіть коли Hermes запущений (безпечний режим WAL).

**Що виключено з zip‑архіву:**

- `*.db-wal`, `*.db-shm`, `*.db-journal` — допоміжні файли WAL / shared‑memory / journal SQLite. Файл `*.db` вже отримав послідовний знімок через `sqlite3.backup()`; включення живих допоміжних файлів дозволило б відновленню побачити частково зафіксований стан.
- `checkpoints/` — кеші траєкторій per‑session. Хеш‑ключовані та регенеруються для кожної сесії; їх не вдасться чисто перенести в іншу інсталяцію.
- Сам код `hermes-agent` (це резервна копія даних користувача, а не знімок репозиторію).

### Приклади

```bash
hermes backup                           # Full backup to ~/hermes-backup-*.zip
hermes backup -o /tmp/hermes.zip        # Full backup to specific path
hermes backup --quick                   # Quick state-only snapshot
hermes backup --quick --label "pre-upgrade"  # Quick snapshot with label
```
## `hermes checkpoints`

```bash
hermes checkpoints [COMMAND]
```

Переглядай та керуй тіньовим git‑сховищем у `~/.hermes/checkpoints/` — шаром зберігання, що стоїть за командою сесії `/rollback`. Безпечно запускати в будь‑який час; не потребує запущеного агента.

| Subcommand | Description |
|------------|-------------|
| `status` (default) | Показати загальний розмір, кількість проєктів та розподіл по проєктах. Саме `hermes checkpoints` еквівалентно. |
| `list` | Псевдонім для `status`. |
| `prune` | Примусово виконати очистку — видалити осиротілі та застарілі проєкти, провести GC сховища, застосувати обмеження розміру. Ігнорує 24‑годинний маркер ідемпотентності. |
| `clear` | Видалити всю базу контрольних точок. Незворотньо; запитує підтвердження, якщо не вказано `-f`. |
| `clear-legacy` | Видалити лише архіви `legacy-<timestamp>/`, створені під час міграції v1→v2. |

### Options

| Option | Subcommand | Description |
|--------|------------|-------------|
| `--limit N` | `status`, `list` | Максимальна кількість проєктів у виводі (за замовчуванням 20). |
| `--retention-days N` | `prune` | Видалити проєкти, у яких `last_touch` старіший за N днів (за замовчуванням 7). |
| `--max-size-mb N` | `prune` | Після проходу осиротілих/застарілих, видаляти найстаріші коміти в кожному проєкті, доки загальний розмір сховища не стане ≤ N MB (за замовчуванням 500). |
| `--keep-orphans` | `prune` | Не видаляти проєкти, чиї робочі каталоги більше не існують. |
| `-f`, `--force` | `clear`, `clear-legacy` | Пропустити запит підтвердження. |

### Examples

```bash
hermes checkpoints                                  # status overview
hermes checkpoints prune --retention-days 3         # aggressive cleanup
hermes checkpoints prune --max-size-mb 200          # tighten size cap once
hermes checkpoints clear-legacy -f                  # drop v1 archive dirs
hermes checkpoints clear -f                         # wipe everything
```

Дивись [Checkpoints and `/rollback`](../user-guide/checkpoints-and-rollback.md) для повної архітектури та команд сесії.
## `hermes import`

```bash
hermes import <zipfile> [options]
```

Відновити раніше створену резервну копію Hermes у твоєму домашньому каталозі Hermes. Усі файли в архіві перезаписують існуючі файли в твоєму домашньому каталозі Hermes; `--force` лише пропускає запит підтвердження, який з’являється, коли ціль вже має встановлену Hermes.

| Option | Description |
|--------|-------------|
| `-f`, `--force` | Пропустити запит підтвердження існуючої інсталяції. |

:::warning
Зупини **gateway** перед імпортом, щоб уникнути конфліктів із запущеними процесами.
:::

### Приклади
```bash
hermes import ~/hermes-backup-20260423.zip           # Prompts before overwriting existing config
hermes import ~/hermes-backup-20260423.zip --force   # Overwrite without prompting
```
## `hermes logs`

```bash
hermes logs [log_name] [options]
```

Переглядай, стеж за та фільтруй файли журналу Hermes. Усі журнали зберігаються в `~/.hermes/logs/` (або `<profile>/logs/` для профілів, відмінних від типового).

### Файли журналу

| Name | File | What it captures |
|------|------|-----------------|
| `agent` (default) | `agent.log` | Уся активність агента — виклики API, розподіл інструментів, життєвий цикл сесії (INFO та вище) |
| `errors` | `errors.log` | Тільки попередження та помилки — відфільтрована підмножина `agent.log` |
| `gateway` | `gateway.log` | Активність шлюзу обміну повідомленнями — підключення платформ, розсилання повідомлень, події вебхуків |

### Параметри

| Option | Description |
|--------|-------------|
| `log_name` | Який журнал переглядати: `agent` (за замовчуванням), `errors`, `gateway` або `list` — показати доступні файли з розмірами. |
| `-n`, `--lines <N>` | Кількість рядків для показу (за замовчуванням: 50). |
| `-f`, `--follow` | Слідкувати за журналом у реальному часі, як `tail -f`. Натисни Ctrl+C, щоб зупинити. |
| `--level <LEVEL>` | Мінімальний рівень журналу для показу: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. |
| `--session <ID>` | Фільтрувати рядки, що містять підрядок ідентифікатора сесії. |
| `--since <TIME>` | Показати рядки за відносний проміжок часу: `30m`, `1h`, `2d` тощо. Підтримуються `s` (секунди), `m` (хвилини), `h` (години), `d` (дні). |
| `--component <NAME>` | Фільтрувати за компонентом: `gateway`, `agent`, `tools`, `cli`, `cron`. |

### Приклади

```bash
# View the last 50 lines of agent.log (default)
hermes logs

# Follow agent.log in real time
hermes logs -f

# View the last 100 lines of gateway.log
hermes logs gateway -n 100

# Show only warnings and errors from the last hour
hermes logs --level WARNING --since 1h

# Filter by a specific session
hermes logs --session abc123

# Follow errors.log, starting from 30 minutes ago
hermes logs errors --since 30m -f

# List all log files with their sizes
hermes logs list
```

### Фільтрація

Фільтри можна комбінувати. Коли активні кілька фільтрів, рядок журналу має задовольнити **усі** з них, щоб бути показаним:

```bash
# WARNING+ lines from the last 2 hours containing session "tg-12345"
hermes logs --level WARNING --since 2h --session tg-12345
```

Рядки без розбірливої часової мітки включаються, коли активний `--since` (вони можуть бути продовженням багаторядкового запису журналу). Рядки без визначеного рівня включаються, коли активний `--level`.

### Ротація журналу

Hermes використовує `RotatingFileHandler` з Python. Старі журнали автоматично ротуються — шукай `agent.log.1`, `agent.log.2` тощо. Підкоманда `hermes logs list` показує всі файли журналу, включаючи ротовані.
## `hermes config`

```bash
hermes config <subcommand>
```

Підкоманди:

| Підкоманда | Опис |
|------------|------|
| `show` | Показати поточні значення конфігурації. |
| `edit` | Відкрити `config.yaml` у твоєму редакторі. |
| `set <key> <value>` | Встановити значення конфігурації. |
| `path` | Вивести шлях до файлу конфігурації. |
| `env-path` | Вивести шлях до файлу `.env`. |
| `check` | Перевірити відсутні або застарілі параметри конфігурації. |
| `migrate` | Додати нові параметри конфігурації інтерактивно. |
## `hermes pairing`

```bash
hermes pairing <list|approve|revoke|clear-pending>
```

| Підкоманда | Опис |
|------------|------|
| `list` | Показати користувачів, які очікують схвалення, та вже схвалених. |
| `approve <platform> <code>` | Схвалити код парування. |
| `revoke <platform> <user-id>` | Відкликати доступ користувача. |
| `clear-pending` | Очистити список очікуваних кодів парування. |
## `hermes skills`

```bash
hermes skills <subcommand>
```

Підкоманди:

| Підкоманда | Опис |
|------------|------|
| `browse` | Пагінований браузер для реєстрів **skill**‑ів. |
| `search` | Пошук у реєстрах **skill**‑ів. |
| `install` | Встановити **skill**. |
| `inspect` | Переглянути **skill** без встановлення. |
| `list` | Перелік встановлених **skill**‑ів. |
| `check` | Перевірити встановлені **skill**‑и gateway на оновлення в апстрімі. |
| `update` | Перевстановити **skill**‑и gateway з урахуванням змін в апстрімі, коли вони доступні. |
| `audit` | Пересканувати встановлені **skill**‑и gateway. |
| `uninstall` | Видалити **skill**, встановлений через gateway. |
| `reset` | Зняти прив’язку вбудованого **skill**, позначеного як `user_modified`, очистивши його запис у маніфесті. За допомогою `--restore` також замінює копію користувача на вбудовану версію. |
| `publish` | Опублікувати **skill** у реєстрі. |
| `snapshot` | Експортувати/імпортувати конфігурації **skill**‑ів. |
| `tap` | Керувати власними джерелами **skill**‑ів. |
| `config` | Інтерактивне вмикання/вимикання налаштувань **skill**‑ів за платформою. |

Загальні приклади:

```bash
hermes skills browse
hermes skills browse --source official
hermes skills search react --source skills-sh
hermes skills search https://mintlify.com/docs --source well-known
hermes skills inspect official/security/1password
hermes skills inspect skills-sh/vercel-labs/json-render/json-render-react
hermes skills install official/migration/openclaw-migration
hermes skills install skills-sh/anthropics/skills/pdf --force
hermes skills install https://sharethis.chat/SKILL.md                     # Direct URL (single-file SKILL.md)
hermes skills install https://example.com/SKILL.md --name my-skill        # Override name when frontmatter has none
hermes skills check
hermes skills update
hermes skills config
hermes skills reset google-workspace
hermes skills reset google-workspace --restore --yes
```

Примітки:
- `--force` може обійти **не** небезпечні блоки політики для **skill**‑ів третіх сторін/спільноти.
- `--force` не переважає вердикт сканування `dangerous`.
- `--source skills-sh` шукає у публічному каталозі `skills.sh`.
- `--source well-known` дозволяє вказати Hermes сайт, що розкриває `/.well-known/skills/index.json`.
- `--source browse-sh` шукає в каталозі [browse.sh](https://browse.sh) понад 200 сайт‑специфічних **skill**‑ів автоматизації браузера. Ідентифікатори виглядають як `browse-sh/airbnb.com/search-listings-ddgioa`.
- Передача URL `http(s)://…/*.md` встановлює одиночний файл SKILL.md безпосередньо. Якщо у frontmatter немає `name:` і slug URL не є дійсним ідентифікатором, інтерактивний термінал запитує назву; у неінтерактивних середовищах (`/skills install` у TUI, платформи gateway) потрібно вказати `--name <x>`.
## `hermes bundles`

```bash
hermes bundles <subcommand>
```

Skill bundles групують кілька навичок під однією slash‑командою `/<bundle-name>`. Виклик пакету завантажує всі зазначені навички в одне об’єднане повідомлення користувача. Сховище: `~/.hermes/skill-bundles/<slug>.yaml`. Дивись [Skill Bundles](../user-guide/features/skills.md#skill-bundles) для схеми YAML та поведінки.

Підкоманди:

| Підкоманда | Опис |
|------------|------|
| `list` | Перелік встановлених пакетів (за замовчуванням, коли підкоманда не вказана) |
| `show <name>` | Показати назву, опис, навички та шлях до файлу конкретного пакету |
| `create <name>` | Створити новий пакет. Додай `--skill <id>` (можна кілька разів) або пропусти для інтерактивного вводу. Доступні `--description`, `--instruction`, `--force`. |
| `delete <name>` | Видалити файл пакету |
| `reload` | Пересканувати `~/.hermes/skill-bundles/` та повідомити про додані/видалені пакети |

Приклади:

```bash
hermes bundles create backend-dev \
  --skill github-code-review \
  --skill test-driven-development \
  --skill github-pr-workflow \
  -d "Backend feature work"

hermes bundles list
hermes bundles show backend-dev
hermes bundles delete backend-dev
```

У чат‑сесії `/bundles` виводить список встановлених пакетів, а `/<bundle-name>` завантажує один.
## `hermes curator`

```bash
hermes curator <subcommand>
```

Curator — це допоміжна модель фонового завдання, яке періодично переглядає створені агентом **skills**, видаляє застарілі, консолідує дублікати та архівує застарілі **skills**. **Bundled** та **hub‑installed** **skills** ніколи не змінюються. Архіви можна відновити; автоматичне видалення не відбувається.

| Subcommand | Description |
|------------|-------------|
| `status` | Показати стан curator та статистику **skills** |
| `run` | Запустити перегляд curator зараз (блокує, доки не завершиться прохід LLM) |
| `run --background` | Запустити прохід LLM у фоні та повернутись одразу |
| `run --dry-run` | Тільки попередній перегляд — створити звіт без змін |
| `backup` | Створити ручний tar.gz‑знімок `~/.hermes/skills/` (curator також автоматично робить знімок перед кожним реальним запуском) |
| `rollback` | Відновити `~/.hermes/skills/` зі знімка (за замовчуванням найновішого) |
| `rollback --list` | Перерахувати доступні знімки |
| `rollback --id <ts>` | Відновити конкретний знімок за ідентифікатором |
| `rollback -y` | Пропустити запит підтвердження |
| `pause` | Призупинити curator до його відновлення |
| `resume` | Відновити призупинений curator |
| `pin <skill>` | Закріпити **skill**, щоб curator ніколи не переміщував його автоматично |
| `unpin <skill>` | Відкріпити **skill** |
| `restore <skill>` | Відновити архівований **skill** |
| `archive <skill>` | Архівувати **skill** вручну |
| `prune` | Ручне видалення **skills**, які curator зазвичай очищає |
| `list-archived` | Перерахувати архівовані **skills** (можна відновити за допомогою `restore`) |

При новій інсталяції перший запланований прохід відкладений на повний `interval_hours` (за замовчуванням 7 днів) — шлюз не буде виконувати curator одразу після першого тіку після `hermes update`. Використай `hermes curator run --dry-run`, щоб переглянути результат перед цим.

Дивись [Curator](../user-guide/features/curator.md) для опису поведінки та налаштувань.
## `hermes fallback`

```bash
hermes fallback <subcommand>
```

Керує ланцюжком запасних (варіант) провайдерів. Запасні (варіант) провайдери перебираються у порядку, коли основна модель не працює через обмеження швидкості, перевантаження або помилки з’єднання.

| Subcommand | Description |
|------------|-------------|
| `list` (alias: `ls`) | Показати поточний ланцюжок запасних (варіант) провайдерів (за замовчуванням, коли не вказано підкоманду) |
| `add` | Вибрати провайдера + модель (те ж діалогове вікно, що і `hermes model`) і додати в кінець ланцюжка |
| `remove` (alias: `rm`) | Вибрати запис для видалення з ланцюжка |
| `clear` | Видалити всі записи запасних (варіант) провайдерів |

See [Постачальники запасного (варіант) провайдера](../user-guide/features/fallback-providers.md).
## `hermes hooks`

```bash
hermes hooks <subcommand>
```

Переглядай shell‑script hooks, оголошені у `~/.hermes/config.yaml`, тестуй їх на синтетичних payload‑ах і керуй allowlist‑ом першого використання у `~/.hermes/shell-hooks-allowlist.json`.

| Subcommand | Description |
|------------|-------------|
| `list` (alias: `ls`) | Показати налаштовані hooks разом із matcher, timeout та статусом згода |
| `test <event>` | Запустити кожен hook, що відповідає `<event>`, на синтетичному payload |
| `revoke` (aliases: `remove`, `rm`) | Видалити записи allowlist для команди (вступає в силу після наступного перезапуску) |
| `doctor` | Перевірити кожен налаштований hook: біт exec, allowlist, зсув mtime, валідність JSON та час синтетичного запуску |

Дивись [Hooks](../user-guide/features/hooks.md) для підписів подій та форм payload‑ів.
## `hermes memory`

```bash
hermes memory <subcommand>
```

Налаштуй та керуй плагінами зовнішніх провайдерів пам’яті. Доступні провайдери: honcho, openviking, mem0, hindsight, holographic, retaindb, byterover, supermemory. Одночасно може бути активний лише один зовнішній провайдер. Вбудована пам’ять (MEMORY.md/USER.md) завжди активна.

Підкоманди:

| Підкоманда | Опис |
|------------|------|
| `setup` | Інтерактивний вибір провайдера та його налаштування. |
| `status` | Показати поточну конфігурацію провайдера пам’яті. |
| `off` | Вимкнути зовнішнього провайдера (залишити лише вбудовану). |

:::info Provider-specific subcommands
Коли зовнішній провайдер пам’яті активний, він може зареєструвати свою власну команду верхнього рівня `hermes <provider>` для управління, специфічне для провайдера (наприклад, `hermes honcho`, коли активний Honcho). Неактивні провайдери не надають свої підкоманди. Запусти `hermes --help`, щоб побачити, що наразі підключено.
:::
## `hermes acp`

```bash
hermes acp
```

Запускає Hermes як сервер stdio ACP (Agent Client Protocol) для інтеграції в редактор.

Пов’язані точки входу:

```bash
hermes-acp
python -m acp_adapter
```

Спочатку встанови підтримку:

```bash
pip install -e '.[acp]'
```

Дивись [Інтеграція редактора ACP](../user-guide/features/acp.md) та [Внутрішня структура ACP](../developer-guide/acp-internals.md).
## `hermes mcp`

```bash
hermes mcp <subcommand>
```

Керує конфігураціями сервера MCP (Model Context Protocol) та запускає Hermes у режимі сервера MCP.

| Subcommand | Description |
|------------|-------------|
| *(none)* or `picker` | Інтерактивний вибір каталогу — переглянути схвалені Nous MCP та встановити/увімкнути/вимкнути. |
| `catalog` | Перелік схвалених Nous MCP (простий текст, скриптований). |
| `install <name>` | Встановити запис каталогу (наприклад `hermes mcp install n8n`). |
| `serve [-v\|--verbose]` | Запустити Hermes як сервер MCP — надати доступ до розмов іншим агентам. |
| `add <name> [--url URL] [--command CMD] [--args ...] [--auth oauth\|header]` | Додати власний сервер MCP з автоматичним виявленням інструментів. |
| `remove <name>` (alias: `rm`) | Видалити сервер MCP з конфігурації. |
| `list` (alias: `ls`) | Перелік налаштованих серверів MCP. |
| `test <name>` | Перевірити з’єднання з сервером MCP. |
| `configure <name>` (alias: `config`) | Перемкнути вибір інструментів для сервера. |
| `login <name>` | Примусово переавтентифікуватися для серверу MCP на базі OAuth. |

Дивись [MCP Config Reference](./mcp-config-reference.md), [Use MCP with Hermes](../guides/use-mcp-with-hermes.md) та [MCP Server Mode](../user-guide/features/mcp.md#running-hermes-as-an-mcp-server).
## `hermes plugins`

```bash
hermes plugins [subcommand]
```

Уніфіковане керування плагінами — загальні плагіни, провайдери пам’яті та контекстні движки в одному місці. Запуск `hermes plugins` без підкоманди відкриває композитний інтерактивний інтерфейс з двома секціями:

- **General Plugins** — багатовибіркові чекбокси для вмикання/вимикання встановлених плагінів
- **Provider Plugins** — одиночний вибір конфігурації для Memory Provider та Context Engine. Натисни **ENTER** на категорії, щоб відкрити радіо‑вибір.

| Subcommand | Description |
|------------|-------------|
| *(none)* | Composite interactive UI — general plugin toggles + provider plugin configuration. |
| `install <identifier> [--force]` | Install a plugin from a Git URL or `owner/repo`. |
| `update <name>` | Pull latest changes for an installed plugin. |
| `remove <name>` (aliases: `rm`, `uninstall`) | Remove an installed plugin. |
| `enable <name>` | Enable a disabled plugin. |
| `disable <name>` | Disable a plugin without removing it. |
| `list` (alias: `ls`) | List installed plugins with enabled/disabled status. |

Вибори провайдерних плагінів зберігаються у `config.yaml`:
- `memory.provider` — активний провайдер пам’яті (порожньо = лише вбудований)
- `context.engine` — активний контекстний движок (`"compressor"` = вбудований за замовчуванням)

Список вимкнених загальних плагінів зберігається у `config.yaml` під `plugins.disabled`.

Дивись [Plugins](../user-guide/features/plugins.md) та [Build a Hermes Plugin](../guides/build-a-hermes-plugin.md).
## `hermes tools`

```bash
hermes tools [--summary]
```

| Option | Опис |
|--------|------|
| `--summary` | Вивести поточний підсумок увімкнених інструментів і завершити роботу. |

Без `--summary` це запускає інтерактивний інтерфейс налаштування інструментів для кожної платформи.
## `hermes computer-use`

```bash
hermes computer-use <subcommand>
```

Підкоманди:

| Підкоманда | Опис |
|------------|------|
| `install` | Запустити інсталятор **cua-driver** (лише macOS). |
| `install --upgrade` | Перезапустити інсталятор, навіть якщо `cua-driver` вже є в `$PATH`. Скрипт upstream завжди завантажує останній реліз, тому це виконує оновлення на місці. |
| `status` | Вивести, чи `cua-driver` знаходиться в `$PATH` і яку версію встановлено. |

`hermes computer-use install` — стабільна точка входу для встановлення бінарника [cua-driver](https://github.com/trycua/cua), який використовується інструментальним набором `computer_use`. Він запускає той самий інсталятор upstream, який викликає `hermes tools` під час першого ввімкнення Computer Use, тому його безпечно використовувати для повторного запуску встановлення, якщо перемикач інструментального набору не спрацював (наприклад, у налаштуваннях повернених користувачів).

`hermes update` автоматично повторно запускає інсталятор upstream у кінці оновлення, якщо `cua-driver` є в `$PATH`, тому більшості користувачів не потрібно вручну викликати `--upgrade`. Використовуй його, коли upstream випускає виправлення, яке потрібне одразу, без очікування наступного оновлення Hermes.
## `hermes sessions`

```bash
hermes sessions <subcommand>
```

Subcommands:

| Subcommand | Description |
|------------|-------------|
| `list` | Переглянути недавні сесії. |
| `browse` | Інтерактивний вибір сесії з пошуком та відновленням. |
| `export <output> [--session-id ID]` | Експортувати сесії у формат JSONL. |
| `delete <session-id>` | Видалити одну сесію. |
| `prune` | Видалити старі сесії. |
| `stats` | Показати статистику сховища сесій. |
| `rename <session-id> <title>` | Встановити або змінити назву сесії. |
## `hermes insights`

```bash
hermes insights [--days N] [--source platform]
```

| Опція | Опис |
|--------|-------------|
| `--days <n>` | Проаналізувати останні `n` днів (за замовчуванням: 30). |
| `--source <platform>` | Фільтрувати за джерелом, наприклад `cli`, `telegram` або `discord`. |
## `hermes claw`

```bash
hermes claw migrate [options]
```

Перенеси свою конфігурацію OpenClaw до Hermes. Читає з `~/.openclaw` (або кастомного шляху) і записує в `~/.hermes`. Автоматично виявляє застарілі назви каталогів (`~/.clawdbot`, `~/.moltbot`) та імена файлів конфігурації (`clawdbot.json`, `moltbot.json`).

| Option | Description |
|--------|-------------|
| `--dry-run` | Попередній перегляд того, що буде перенесено, без запису. |
| `--preset <name>` | Пресет міграції: `full` (всі сумісні налаштування) або `user-data` (виключає конфігурацію інфраструктури). Жоден пресет не імпортує секрети — передай `--migrate-secrets` явно. |
| `--overwrite` | Перезаписати існуючі файли Hermes у разі конфліктів (за замовчуванням: відмовитися застосовувати, коли план має конфлікти). |
| `--migrate-secrets` | Включити API‑ключі у міграцію. Потрібно навіть при `--preset full`. |
| `--no-backup` | Пропустити створення zip‑знімка `~/.hermes/` перед міграцією (за замовчуванням перед застосуванням створюється архів restore‑point у `~/.hermes/backups/pre-migration-*.zip`; його можна відновити за допомогою `hermes import`). |
| `--source <path>` | Кастомний каталог OpenClaw (за замовчуванням: `~/.openclaw`). |
| `--workspace-target <path>` | Цільовий каталог для інструкцій робочого простору (AGENTS.md). |
| `--skill-conflict <mode>` | Обробка колізій імен навичок: `skip` (за замовчуванням), `overwrite` або `rename`. |
| `--yes` | Пропустити запит підтвердження. |

### What gets migrated

Міграція охоплює 30+ категорій, включаючи персона, пам'ять, навички, провайдери моделей, платформи обміну повідомленнями, поведінку агентів, політики сесій, сервери MCP, TTS та інше. Елементи або **безпосередньо імпортовані** у еквіваленти Hermes, або **заархівовані** для ручного перегляду.

**Безпосередньо імпортовані:** SOUL.md, MEMORY.md, USER.md, AGENTS.md, навички (4 вихідних каталоги), модель за замовчуванням, кастомні провайдери, сервери MCP, токени та allowlist платформ обміну повідомленнями (Telegram, Discord, Slack, WhatsApp, Signal, Matrix, Mattermost), налаштування за замовчуванням агентів (зусилля розуміння, компресія, затримка людини, часовий пояс, sandbox), політики скидання сесій, правила схвалення, конфігурація TTS, налаштування браузера, налаштування інструментів, таймаут виконання, allowlist команд, конфігурація шлюзу інструментів та API‑ключі з 3 джерел.

**Заархівовані для ручного перегляду:** Cron‑завдання, плагіни, хуки/webhooks, бекенд пам'яті (QMD), конфігурація реєстру навичок, UI/ідентичність, логування, багатагентна установка, прив'язки каналів, IDENTITY.md, TOOLS.md, HEARTBEAT.md, BOOTSTRAP.md.

**Визначення API‑ключа** перевіряє три джерела у пріоритетному порядку: значення конфігурації → `~/.openclaw/.env` → `auth-profiles.json`. Усі поля токенів підтримують прості рядки, шаблони env (`${VAR}`) та об’єкти SecretRef.

Для повного мапінгу ключів конфігурації, деталей обробки SecretRef та чек‑ліста після міграції дивись **[full migration guide](../guides/migrate-from-openclaw.md)**.

### Examples

```bash
# Preview what would be migrated
hermes claw migrate --dry-run

# Full migration (all compatible settings, no secrets)
hermes claw migrate --preset full

# Full migration including API keys
hermes claw migrate --preset full --migrate-secrets

# Migrate user data only (no secrets), overwrite conflicts
hermes claw migrate --preset user-data --overwrite

# Migrate from a custom OpenClaw path
hermes claw migrate --source /home/user/old-openclaw
```
## `hermes dashboard`

```bash
hermes dashboard [options]
```

Запусти веб‑дашборд — інтерфейс у браузері для керування конфігурацією, API‑ключами та моніторингу сесій. Потрібно `pip install hermes-agent[web]` (FastAPI + Uvicorn). Вбудована вкладка **Chat** у браузері потребує `--tui` та додатковий `pty`. Дивись [Web Dashboard](/user-guide/features/web-dashboard) для повної документації.

| Option | Default | Description |
|--------|---------|-------------|
| `--port` | `9119` | Порт, на якому запускати веб‑сервер |
| `--host` | `127.0.0.1` | Адреса прив’язки |
| `--no-open` | — | Не відкривати браузер автоматично |
| `--tui` | off | Увімкнути вкладку **Chat** у браузері, запустивши `hermes --tui` через PTY/WebSocket‑мост. Потрібно `pip install 'hermes-agent[web,pty]'` і POSIX‑PTY‑середовище, наприклад Linux, macOS або WSL2. |
| `--insecure` | off | Дозволити прив’язку до хостів, відмінних від `localhost`. Відкриває облікові дані дашборда в мережі; використовуйте лише за надійних мережевих контролів. |
| `--stop` | — | Зупинити процеси `hermes dashboard` і вийти. |
| `--status` | — | Показати запущені процеси `hermes dashboard` і вийти. |

```bash
# Default — opens browser to http://127.0.0.1:9119
hermes dashboard

# Custom port, no browser
hermes dashboard --port 8080 --no-open

# Enable the browser Chat tab
hermes dashboard --tui
```
## `hermes profile`

```bash
hermes profile <subcommand>
```

Керування профілями — кілька ізольованих екземплярів Hermes, кожен зі своїми конфігураціями, сесіями, навичками та домашнім каталогом.

| Subcommand | Description |
|------------|-------------|
| `list` | Показати всі профілі. |
| `use <name>` | Встановити «липкий» профіль за замовчуванням. |
| `create <name> [--clone] [--clone-all] [--clone-from <source>] [--no-alias]` | Створити новий профіль. `--clone` копіює конфігурацію, `.env` і `SOUL.md` з активного профілю. `--clone-all` копіює весь стан. `--clone-from` вказує профіль‑джерело. |
| `delete <name> [-y]` | Видалити профіль. |
| `show <name>` | Показати деталі профілю (домашній каталог, конфігурація тощо). |
| `alias <name> [--remove] [--name NAME]` | Керувати скриптами‑обгортками для швидкого доступу до профілю. |
| `rename <old> <new>` | Перейменувати профіль. |
| `export <name> [-o FILE]` | Експортувати профіль у архів `.tar.gz` (локальна резервна копія). |
| `import <archive> [--name NAME]` | Імпортувати профіль з архіву `.tar.gz` (локальне відновлення). |
| `install <source> [--name N] [--alias] [--force] [-y]` | Встановити дистрибутив профілю з git‑URL або локального каталогу. |
| `update <name> [--force-config] [-y]` | Перевантажити дистрибутив; зберігає дані користувача (пам’ять, сесії, автентифікація). |
| `info <name>` | Показати маніфест дистрибутиву профілю (версія, вимоги, джерело). |

Examples:

```bash
hermes profile list
hermes profile create work --clone
hermes profile use work
hermes profile alias work --name h-work
hermes profile export work -o work-backup.tar.gz
hermes profile import work-backup.tar.gz --name restored
hermes profile install github.com/user/my-distro --alias
hermes profile update work
hermes -p work chat -q "Hello from work profile"
```
## `hermes completion`

```bash
hermes completion [bash|zsh|fish]
```

Виводить скрипт автодоповнення оболонки у `stdout`. Підключи (застосуй) цей вивід у свій профіль оболонки, щоб отримати автодоповнення команд Hermes, підкоманд та імен профілів.

Приклади:

```bash
# Bash
hermes completion bash >> ~/.bashrc

# Zsh
hermes completion zsh >> ~/.zshrc

# Fish
hermes completion fish > ~/.config/fish/completions/hermes.fish
```
## `hermes update`

```bash
hermes update [--check] [--backup] [--restart-gateway]
```

Отримує останній код `hermes-agent` і переустановлює залежності у твоєму venv, потім повторно запускає post‑install хуки (MCP‑сервери, синхронізація skills, встановлення автодоповнень). Безпечно запускати на живій інсталяції.

**pip installs:** `hermes update` автоматично визначає pip‑based інсталяції — він запитує PyPI про останній реліз і виконує `pip install --upgrade hermes-agent` замість `git pull`. Релізи PyPI відстежують позначені версії (major/minor), а не кожен коміт у `main`. Використай `--check`, щоб дізнатися, чи доступний новіший PyPI‑реліз без встановлення.

| Option | Description |
|--------|-------------|
| `--check` | Виводить поточний коміт і останній коміт `origin/main` поруч і завершується кодом 0, якщо вони синхронізовані, або 1, якщо відстаєш. Не виконує pull, install чи перезапуск. |
| `--backup` | Створює позначений знімок `HERMES_HOME` (конфіг, auth, sessions, skills, pairing data) перед pull‑ом. За замовчуванням **вимкнено** — попередня поведінка «завжди backup» додавала хвилини до кожного оновлення на великих home. Увімкни назавжди через `update.backup: true` у `config.yaml`. |
| `--restart-gateway` | Після успішного оновлення перезапускає запущений сервіс шлюзу. Має семантику `--all`, якщо встановлено кілька профілів. |

Додаткова поведінка:

- **Знімок даних парингу.** Навіть коли `--backup` вимкнено, `hermes update` робить легкий знімок `~/.hermes/pairing/` та правил коментарів Feishu перед `git pull`. Ти можеш відкотити його за допомогою `hermes backup restore --state pre-update`, якщо pull переписав файл, який ти редагував.
- **Попередження про застарілий `hermes.service`.** Якщо Hermes виявляє стару systemd‑одиницю `hermes.service` (замість поточної `hermes-gateway.service`), виводить одноразову підказку про міграцію, щоб уникнути проблем з flap‑loop.
- **Коди виходу.** `0` — успіх, `1` — помилки pull/install/post‑install, `2` — неочікувані зміни у робочому дереві, які блокують `git pull`.
## Команди обслуговування

| Command | Description |
|---------|-------------|
| `hermes version` | Вивести інформацію про версію. |
| `hermes update` | Отримати останні зміни та перевстановити залежності. |
| `hermes postinstall` | Внутрішнє ініціалізування. Виконується один раз після `pip install hermes-agent` (або `hermes update` при встановленні через pip) для встановлення не‑Python‑залежностей, які pip не може надати — середовище Node.js, безголовий браузер, ripgrep, ffmpeg — а потім запускає `hermes setup`, якщо профіль ще не налаштовано. Безпечно повторно запускати ідемпотентно. |
| `hermes uninstall [--full] [--yes]` | Видалити Hermes, за потреби видаливши всю конфігурацію/дані. |
## Дивись також

- [Довідка щодо Slash‑команд](./slash-commands.md)
- [Інтерфейс CLI](../user-guide/cli.md)
- [Сесії](../user-guide/sessions.md)
- [Система skill](../user-guide/features/skills.md)
- [Скіни та теми](../user-guide/features/skins.md)