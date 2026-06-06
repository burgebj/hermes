---
sidebar_position: 3
---

# Профільні розподіли: поділитися цілим агентом

**Профільний розподіл** упакує повного Hermes‑агента — особистість, інструменти, cron‑завдання, MCP‑з’єднання, конфігурацію — у вигляді git‑репозиторію. Будь‑хто, хто має доступ до репозиторію, може встановити весь агент однією командою, оновити його на місці та залишити свої власні пам'яті, сесії та API‑ключі недоторканими.

Якщо [профіль](./profiles.md) — це локальний агент, розподіл — це цей агент, зроблений придатним для спільного використання.
## Що це означає

До дистрибутивів передача Hermes‑агента означала надсилання комусь:

1. Ваш `SOUL.md`
2. Список інструментів для встановлення
3. Ваш `config.yaml`, без секретів
4. Опис, які сервери MCP ви підключили
5. Будь‑які заплановані `cron`‑завдання
6. Інструкції, які змінні середовища треба задати

… і сподівання, що вони правильно все зберуть. Кожне підвищення версії чи виправлення помилки вимагало повторення передачі.

З дистрибутивами усе це живе в одному git‑репозиторії:

```
my-research-agent/
├── distribution.yaml    # manifest: name, version, env-var requirements
├── SOUL.md              # the agent's personality / system prompt
├── config.yaml          # model, temperature, reasoning, tool defaults
├── skills/              # bundled skills that come with the agent
├── cron/                # scheduled tasks the agent runs
└── mcp.json             # MCP servers the agent connects to
```

Одержувачі виконують:

```bash
hermes profile install github.com/you/my-research-agent --alias
```

… і тепер мають весь агент. Вони заповнюють свої власні API‑ключі (`.env.EXAMPLE` → `.env`), і можуть запускати `my-research-agent chat` або звертатися до нього через Telegram / Discord / Slack / будь‑яку платформу шлюзу. Коли ти пушиш нову версію, вони виконують `hermes profile update my-research-agent` і отримують твої зміни — їх пам’ять і сесії залишаються на місці.
## Чому git?

Ми розглядали tarballs, HTTP‑архіви, власний формат. Жоден з них не зрівнявся з git:

- **Нульовий крок збірки для авторів.** Пушиш у GitHub; споживачі встановлюють. Немає циклу «запакувати це, завантажити те, оновити індекс».
- **Теги, гілки та коміти вже є системою версіонування.** Пуш тегу робить для нас те, що «запакувати + завантажити реліз» робить у інших інструментах.
- **Оновлення — це fetch.** Не потрібно повторно завантажувати весь архів.
- **Прозоро.** Користувачі можуть переглядати репозиторій, читати дифи між версіями, відкривати issue, форкати його для кастомізації.
- **Приватні репо працюють безкоштовно.** SSH‑ключі, `git credential`‑хелпери, збережені облікові дані GitHub CLI — будь‑яка автентифікація, яку вже налаштовано у твоєму терміналі, застосовується прозоро.
- **Відтворюваність — це SHA коміту.** Те саме, що записують pip і npm.

Компроміс: отримувачі повинні мати встановлений git. На будь‑якій машині, де працює Hermes у 2026 р., це вже так.
## Коли слід використовувати дистрибутив?

Підходять випадки:

- **Ти ділишся спеціалізованим агентом** — монітором відповідності, рев’юером коду, помічником дослідника, ботом підтримки клієнтів — з командою або спільнотою.
- **Ти розгортаєш один і той самий агент на кількох машинах** і не хочеш копіювати файли вручну щоразу.
- **Ти вносиш зміни в агент** і хочеш, щоб отримувачі підхоплювали нові версії однією командою.
- **Ти створюєш агент як продукт** — упереджені за замовчуванням налаштування, підготовлені навички, налаштовані підказки — які інші люди мають використовувати як стартову точку.

Не підходить:

- **Ти просто хочеш створити резервну копію профілю на своїй машині.** Використовуй [`hermes profile export` / `import`](../reference/profile-commands.md#hermes-profile-export) — саме для цього вони призначені.
- **Ти хочеш ділитися API‑ключами разом з агентом.** `auth.json` і `.env` навмисно виключені з дистрибутивів. Кожен інсталятор приносить свої облікові дані.
- **Ти хочеш ділитися пам’яттю / сесіями / історією розмов.** Це дані користувача, а не вміст дистрибутиву. Ніколи не постачаються.
## Життєвий цикл: від автора до інсталятора та оновлення

Нижче наведено повний сквозний процес. Вибери ту частину, яка тебе цікавить.

---
## Для авторів: публікація дистрибутиву

### Крок 1 — Почати з робочого профілю

Створюй та вдосконалюй агента, як будь‑який інший профіль:

```bash
hermes profile create research-bot
research-bot setup                    # configure model, API keys
# Edit ~/.hermes/profiles/research-bot/SOUL.md
# Install skills, wire up MCP servers, schedule cron jobs, etc.
research-bot chat                     # dogfood until it feels right
```

### Крок 2 — Додати `distribution.yaml`

Створи `~/.hermes/profiles/research-bot/distribution.yaml`:

```yaml
name: research-bot
version: 1.0.0
description: "Autonomous research assistant with arXiv and web tools"
hermes_requires: ">=0.12.0"
author: "Your Name"
license: "MIT"

# Tell installers which env vars the agent needs. These are checked against
# the installer's shell and existing .env file so they don't get nagged
# about keys they already have configured.
env_requires:
  - name: OPENAI_API_KEY
    description: "OpenAI API key (for model access)"
    required: true
  - name: SERPAPI_KEY
    description: "SerpAPI key for web search"
    required: false
    default: ""
```

Це весь маніфест. Усі поля, крім `name`, мають розумні значення за замовчуванням.

### Крок 3 — Запушити в git‑репозиторій

```bash
cd ~/.hermes/profiles/research-bot
git init
git add .
git commit -m "v1.0.0"
git remote add origin git@github.com:you/research-bot.git
git tag v1.0.0
git push -u origin main --tags
```

Тепер репозиторій — це дистрибутив. Будь‑хто з доступом може його встановити.

:::note
Git‑репозиторій містить **все в каталозі профілю, крім того, що вже виключено з дистрибутивів**: `auth.json`, `.env`, `memories/`, `sessions/`, `state.db*`, `logs/`, `workspace/`, `*_cache/`, `local/`. Це залишається на твоїй машині. За потреби можеш додати `.gitignore`, щоб виключити додаткові шляхи.
:::

### Крок 4 — Тегувати версійні релізи

Кожного разу, коли агент досягає стабільної точки, збільшуй версію та став тег:

```bash
# Edit distribution.yaml: version: 1.1.0
git add distribution.yaml SOUL.md skills/
git commit -m "v1.1.0: tighter research SOUL, add arxiv skill"
git tag v1.1.0
git push --tags
```

Отримувачі, які запускають `hermes profile update research-bot`, отримають останню версію.

### Як виглядає репозиторій

Повний створений дистрибутив:

```
research-bot/
├── distribution.yaml            # required
├── SOUL.md                      # strongly recommended
├── config.yaml                  # model, provider, tool defaults
├── mcp.json                     # MCP server connections
├── skills/
│   ├── arxiv-search/SKILL.md
│   ├── paper-summarization/SKILL.md
│   └── citation-lookup/SKILL.md
├── cron/
│   └── weekly-digest.json       # scheduled tasks
└── README.md                    # human-facing description (optional)
```

### Distribution-owned vs user-owned

Коли інсталятор оновлює до нової версії, деякі файли замінюються (домени автора), а деякі залишаються (домени інсталятора). За замовчуванням:

| Категорія | Шляхи | При оновленні |
|---|---|---|
| **Distribution-owned** | `SOUL.md`, `config.yaml`, `mcp.json`, `skills/`, `cron/`, `distribution.yaml` | Замінюються новим клонуванням |
| **Config override** | `config.yaml` | Насправді зберігається за замовчуванням — інсталятор може налаштувати модель або провайдера. Додай `--force-config` під час оновлення, щоб скинути. |
| **User-owned** | `memories/`, `sessions/`, `state.db*`, `auth.json`, `.env`, `logs/`, `workspace/`, `plans/`, `home/`, `*_cache/`, `local/` | Ніколи не змінюються |

Список distribution-owned можна перевизначити в маніфесті:

```yaml
distribution_owned:
  - SOUL.md
  - skills/research/            # only my research skills; other installed skills stay
  - cron/digest.json
```

Якщо його не вказано, застосовуються наведені вище значення за замовчуванням — саме те, чого хочуть більшість дистрибутивів.
## Для інсталяторів: використання дистрибутиву

### Встановлення

```bash
hermes profile install github.com/you/research-bot --alias
```

Що відбувається:

1. Клонує репозиторій у тимчасову директорію.
2. Читає `distribution.yaml`, показує тобі маніфест (назва, версія, опис, автор, необхідні змінні оточення).
3. Перевіряє кожну необхідну змінну оточення проти твого shell‑оточення та існуючого `.env` у цільовому профілі. Позначає кожну як `✓ set` або `needs setting`, щоб ти точно знав, що налаштовувати.
4. Запитує підтвердження. Передай `-y` / `--yes`, щоб пропустити.
5. Копіює файли, що належать дистрибутиву, у `~/.hermes/profiles/research-bot/` (або куди вказує `name` у маніфесті).
6. Створює `.env.EXAMPLE` з закоментованими необхідними ключами — скопіюй його у `.env` і заповни.
7. За допомогою `--alias` створює обгортку, щоб ти міг запускати `research-bot chat` безпосередньо.

### Типи джерел

Будь‑яка git‑URL працює:

```bash
# GitHub shorthand
hermes profile install github.com/you/research-bot

# Full HTTPS
hermes profile install https://github.com/you/research-bot.git

# SSH
hermes profile install git@github.com:you/research-bot.git

# Self-hosted, GitLab, Gitea, Forgejo — any Git host
hermes profile install https://git.example.com/team/research-bot.git

# Private repo using your configured git auth
hermes profile install git@github.com:your-org/internal-bot.git

# Local directory during development (no git push needed)
hermes profile install ~/my-profile-in-progress/
```

### Перевизначення назви профілю

Двоє користувачів хочуть один і той самий дистрибутив під різними назвами профілів:

```bash
# Alice
hermes profile install github.com/acme/support-bot --name support-us --alias
# Bob (same distribution, different local name)
hermes profile install github.com/acme/support-bot --name support-eu --alias
```

### Заповнення змінних оточення

Після встановлення профіль агента містить `.env.EXAMPLE`:

```
# Environment variables required by this Hermes distribution.
# Copy to `.env` and fill in your own values before running.

# OpenAI API key (for model access)
# (required)
OPENAI_API_KEY=

# SerpAPI key for web search
# (optional)
# SERPAPI_KEY=
```

Скопіюй його:

```bash
cp ~/.hermes/profiles/research-bot/.env.EXAMPLE ~/.hermes/profiles/research-bot/.env
# Edit .env, paste your real keys
```

Необхідні ключі, які вже були у твоєму shell‑оточенні (наприклад, `OPENAI_API_KEY`, експортований у твоєму `~/.zshrc`), позначені `✓ set` під час встановлення — їх не потрібно дублювати у `.env`.

### Перевірка встановленого

```bash
hermes profile info research-bot
```

Показує:

```
Distribution: research-bot
Version:      1.0.0
Description:  Autonomous research assistant with arXiv and web tools
Author:       Your Name
Requires:     Hermes >=0.12.0
Source:       https://github.com/you/research-bot
Installed:    2026-05-08T17:04:32+00:00

Environment variables:
  OPENAI_API_KEY (required) — OpenAI API key (for model access)
  SERPAPI_KEY (optional) — SerpAPI key for web search
```

`hermes profile list` також показує колонку `Distribution`, тож одразу видно, які профілі походять з репозиторіїв, а які ти створив вручну:

```
 Profile          Model                        Gateway      Alias        Distribution
 ───────────────    ───────────────────────────    ───────────    ───────────    ────────────────────
 ◆default         claude-sonnet-4              stopped      —            —
  coder           gpt-5                        stopped      coder        —
  research-bot    claude-opus-4                stopped      research-bot research-bot@1.0.0
  telemetry       claude-sonnet-4              running      telemetry    telemetry@2.3.1
```

### Оновлення

```bash
hermes profile update research-bot
```

Що відбувається:

1. Повторно клонує репозиторій за записаною URL‑адресою джерела.
2. Замінює файли, що належать дистрибутиву (SOUL, skills, cron, mcp.json).
3. **Зберігає** твій `config.yaml` — ти міг налаштувати модель, температуру чи інші параметри. Передай `--force-config`, щоб перезаписати.
4. **Ніколи не торкається** даних користувача: пам’яті, сесії, автентифікації, `.env`, логи, стан.

Без повторного завантаження всього архіву. Без перезапису твоїх локальних змін у конфігурації. Без видалення історії розмов.

### Видалення

```bash
hermes profile delete research-bot
```

Запит на видалення спочатку показує інформацію про дистрибутив, перш ніж попросити підтвердження:

```
Profile: research-bot
Path:    ~/.hermes/profiles/research-bot
Model:   claude-opus-4 (anthropic)
Skills:  12
Distribution: research-bot@1.0.0
Installed from: https://github.com/you/research-bot

This will permanently delete:
  • All config, API keys, memories, sessions, skills, cron jobs
  • Command alias (~/.local/bin/research-bot)

Type 'research-bot' to confirm:
```

Тож ти ніколи випадково не видалиш агента, не знаючи, звідки він походить, або не зможеш його повторно встановити.
## Use cases and patterns

### Personal: sync one agent across machines

Ти створив дослідницького асистента на своєму ноутбуці. Ти хочеш той самий агент на своїй робочій станції.

```bash
# Laptop
cd ~/.hermes/profiles/research-bot
git init && git add . && git commit -m "initial"
git remote add origin git@github.com:you/research-bot.git
git push -u origin main

# Workstation
hermes profile install github.com/you/research-bot --alias
# Fill in .env. Done.
```

Будь‑яка ітерація на ноутбуці (`git commit && push`) потягнеться на робочу станцію за допомогою `hermes profile update research-bot`. Пам’ять залишається на кожному пристрої — ноутбук пам’ятає свої розмови, робоча станція — свої, вони не конфліктують.

### Team: ship a reviewed internal agent

Твоя інженерна команда хоче спільного бота для рев’ю PR з певним SOUL, конкретними інструментами та cron‑ом, який запускає його для кожного PR.

```bash
# Engineering lead
cd ~/.hermes/profiles/pr-reviewer
# ... build and tune ...
git init && git add . && git commit -m "v1.0 PR reviewer"
git tag v1.0.0
git push -u origin main --tags    # push to your company's internal Git host

# Each engineer
hermes profile install git@github.com:your-org/pr-reviewer.git --alias
# Fill in .env with their own API key (billed to them), .env.EXAMPLE points at what's required
pr-reviewer chat
```

Коли лідер випускає v1.1 (кращий SOUL, новий інструмент), інженери виконують `hermes profile update pr-reviewer`, і всі отримують нову версію за кілька хвилин.

### Community: publish a public agent

Ти створив щось нове — можливо, «Polymarket trader», «academic paper summarizer» або «Minecraft server ops assistant». Ти хочеш поділитися цим.

```bash
# You
cd ~/.hermes/profiles/polymarket-trader
# Write a solid README.md at the repo root — GitHub shows it on the repo page
git init && git add . && git commit -m "v1.0"
git tag v1.0.0
# Publish to a public GitHub repo
git remote add origin https://github.com/you/hermes-polymarket-trader.git
git push -u origin main --tags

# Anyone
hermes profile install github.com/you/hermes-polymarket-trader --alias
```

Твітни команду встановлення. Люди, які її спробують, надсилають тобі issues та PR‑и. Якщо хтось хоче налаштувати, він форкає — той самий git‑workflow, який вже знає кожен.

### Product: ship an opinionated agent

Ти створив Hermes‑on‑top — можливо, harness для моніторингу відповідності, стек підтримки клієнтів або доменно‑специфічну дослідницьку платформу. Ти хочеш розповсюдити це як продукт.

```yaml
# distribution.yaml
name: telemetry-harness
version: 2.3.1
description: "Compliance telemetry harness — monitors and reviews regulated workflows"
hermes_requires: ">=0.13.0"
author: "Acme Compliance Inc."
license: "Commercial"

env_requires:
  - name: ACME_API_KEY
    description: "Your Acme Compliance license key (email support@acme.com)"
    required: true
  - name: OPENAI_API_KEY
    description: "OpenAI API key for model access"
    required: true
  - name: GRAPHITI_MCP_URL
    description: "URL for your Graphiti knowledge graph instance"
    required: false
    default: "http://127.0.0.1:8000/sse"
```

Твої клієнти встановлюють його однією командою; попередній перегляд інсталяції підказує, які ключі потрібно підготувати; оновлення розгортаються одразу після тегу нового релізу; їхні дані відповідності (`memories/`, `sessions/`) ніколи не залишають їхнього пристрою.

### Ephemeral: one‑off scripts on shared infra

Ти — лідер ops. Ти хочеш тимчасовий агент, який діагностує інцидент у продакшн — готовий SOUL з потрібними інструментами та MCP‑з’єднаннями — і працює на трьох ноутбуках інженерів‑дежурних протягом наступного тижня.

```bash
# You
# Build the profile, commit, push a private repo
git push -u origin main

# Each on-call
hermes profile install git@github.com:your-org/incident-2026-q2.git --alias

# Incident resolved — tear it down
hermes profile delete incident-2026-q2
```

Цикл встановлення‑видалення настільки дешевий, що його можна вважати одноразовим.
## Рецепти

### Закріпити конкретну версію

:::note
Закріплення Git‑рефу (`#v1.2.0`) заплановано, але воно не входить у початковий реліз — наразі встановлення слідує за гілкою за замовчуванням. Перевіряй встановлену версію за допомогою `hermes profile info <name>` і відкладай оновлення, доки не будеш готовий.
:::

### Перевірити, яку версію ти маєш порівняно з останньою

```bash
# Your installed version
hermes profile info research-bot | grep Version

# Latest upstream (without installing)
git ls-remote --tags https://github.com/you/research-bot | tail -5
```

### Зберігати локальні налаштування під час оновлень

Типова поведінка оновлення вже це робить: `config.yaml` зберігається. Щоб бути впевненим, запиши свої локальні правки у файл, яким не керує дистрибуція:

```yaml
# ~/.hermes/profiles/research-bot/local/my-overrides.yaml
# (distribution never touches local/)
```

…і посилайся на нього з `config.yaml` або зі свого SOUL за потреби.

### Примусово виконати чисту переустановку

```bash
# Nuke and re-install from scratch (loses memories/sessions too)
hermes profile delete research-bot --yes
hermes profile install github.com/you/research-bot --alias

# Update to current main but reset config.yaml to the distribution's default
hermes profile update research-bot --force-config --yes
```

### Форкнути та налаштувати

Стандартний git‑робочий процес — дистрибуції це просто репозиторії:

```bash
# Fork the repo on GitHub, then install your fork
hermes profile install github.com/yourname/forked-research-bot --alias

# Iterate locally in ~/.hermes/profiles/forked-research-bot/
# Edit SOUL.md, commit, push to your fork
# Upstream changes: pull them into your fork the usual way
```

### Протестувати дистрибуцію перед відправленням

З машини автора:

```bash
# Install from a local directory (no git push needed)
hermes profile install ~/.hermes/profiles/research-bot --name research-bot-test --alias

# Tweak, delete, re-install until it's right
hermes profile delete research-bot-test --yes
hermes profile install ~/.hermes/profiles/research-bot --name research-bot-test
```

---
## Що НЕ входить до дистрибутива (ніколи)

Інсталятор жорстко виключає ці шляхи, навіть якщо автор випадково їх включив. Жодна опція конфігурації не дозволяє це обійти — захисний механізм є регресійно протестованою інваріантою:

- `auth.json` — OAuth‑токени, облікові дані платформи
- `.env` — API‑ключі, секрети
- `memories/` — пам’ять розмов
- `sessions/` — історія розмов
- `state.db`, `state.db‑shm`, `state.db‑wal` — метадані сесії
- `logs/` — логи агента та помилок
- `workspace/` — згенеровані робочі файли
- `plans/` — чернеткові плани
- `home/` — домашня точка монтування користувача в бекендах Docker
- `*_cache/` — кеші зображень / аудіо / документів
- `local/` — простір імен користувацької кастомізації

Коли ти клонюєш дистрибутив, цих файлів просто немає. Коли оновлюєш, вони залишаються на місці. Якщо ти встановив один і той же дистрибутив на п’яти машинах, у тебе буде п’ять ізольованих наборів цих даних — по одному на кожну машину.
## Безпека та довіра

Розподіли профілів за замовчуванням не підписані. Ти довіряєш:

- **Git‑хосту** (GitHub / GitLab / будь‑де), що подає байти, які автор завантажив.
- **Автору**, що не надішле шкідливий SOUL, skills або cron‑завдання.

Cron‑завдання з розподілу **не плануються автоматично** — інсталятор виводить `hermes -p <name> cron list`, і ти вмикаєш їх явно. SOUL.md і skills АКТИВНІ одразу після того, як ти починаєш спілкуватися з профілем, тому прочитай їх перед першим запуском, якщо встановлюєш їх від когось, кого не знаєш.

Приблизна аналогія: встановлення розподілу схоже на встановлення розширення браузера або розширення VS Code. Низький бар’єр входу, велика потужність, довіряй джерелу. Для внутрішніх розподілів компанії використай приватний репозиторій і звичайну git‑автентифікацію — нічого нового не потрібно налаштовувати.

Майбутні версії можуть додати підписування, lock‑файл (`.distribution-lock.yaml`) з конкретним SHA коміту та прапорець `--dry-run`, який виводить різницю перед застосуванням оновлення. Жоден із цих механізмів ще не постачається.
## Під капотом

Для деталей реалізації, точного поводження CLI та всіх прапорців дивись [довідник команд профілю](../reference/profile-commands.md#distribution-commands).

Коротка версія:

- `install`, `update`, `info` живуть всередині `hermes profile` — це не паралельне дерево команд.
- Формат маніфесту — YAML з мінімальною обов’язковою схемою (`name` лише).
- Інсталятор використовує твою локальну бінарну `git` для клонування, тому будь‑яка автентифікація, яку вже обробляє твоя оболонка (SSH‑ключі, помічники облікових даних), працює прозоро.
- Після клонування `.git/` видаляється — встановлений профіль сам не є git‑checkout, уникаючи пасток типу «ой, я випадково закомітив свій `.env` у історію git дистрибутива».
- Зарезервовані імена профілів (`hermes`, `test`, `tmp`, `root`, `sudo`) відхиляються під час встановлення, щоб уникнути конфліктів із поширеними бінарними файлами.
## Дивись також

- [Профілі: запуск кількох агентів](./profiles.md) — базова концепція
- [Довідник команд профілю](../reference/profile-commands.md) — кожен прапорець, кожен параметр
- [`hermes profile export` / `import`](../reference/profile-commands.md#hermes-profile-export) — локальне резервне копіювання/відновлення (не розповсюдження)
- [Використання SOUL з Hermes](../guides/use-soul-with-hermes.md) — створення персональностей
- [Персональність & SOUL](./features/personality.md) — як SOUL вписується в агента
- [Каталог навичок](../reference/skills-catalog.md) — навички, які можна об’єднати