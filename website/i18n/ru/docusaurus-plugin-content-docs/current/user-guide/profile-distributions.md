---
sidebar_position: 3
---

# Распределения профилей: Делимся целым агентом

**Распределение профиля** упаковывает полностью готового Hermes‑агента — личность, инструменты, задачи cron, подключения MCP, конфигурацию — в виде git‑репозитория. Любой, у кого есть доступ к репозиторию, может установить весь агент одной командой, обновить его на месте и при этом сохранить свою память, сессии и API‑ключи нетронутыми.

Если [профиль](./profiles.md) — это локальный агент, то распределение — это сделанный доступным для совместного использования агент.
## Что это значит

До появления дистрибутивов, чтобы поделиться агентом Hermes, приходилось отправлять кому‑то:

1. Ваш `SOUL.md`
2. Список **skill** для установки
3. Ваш `config.yaml`, без секретов
4. Описание того, какие MCP‑серверы вы подключили
5. Любые запланированные `cron`‑задачи
6. Инструкции, какие переменные окружения установить

…и надеяться, что они соберут всё правильно. Каждое повышение версии или исправление ошибки означали повторять передачу.

С дистрибутивами всё это живёт в одном git‑репозитории:

```
my-research-agent/
├── distribution.yaml    # manifest: name, version, env-var requirements
├── SOUL.md              # the agent's personality / system prompt
├── config.yaml          # model, temperature, reasoning, tool defaults
├── skills/              # bundled skills that come with the agent
├── cron/                # scheduled tasks the agent runs
└── mcp.json             # MCP servers the agent connects to
```

Получатели запускают:

```bash
hermes profile install github.com/you/my-research-agent --alias
```

…и теперь у них есть весь агент. Они заполняют свои собственные API‑ключи (`.env.EXAMPLE` → `.env`), и могут запускать `my-research-agent chat` или обращаться к нему через Telegram / Discord / Slack / любую платформу **gateway**. Когда ты публикуешь новую версию, они запускают `hermes profile update my-research-agent` и получают твои изменения — их **память** и **сессии** остаются на месте.
## Почему git?

Мы рассматривали tar‑архивы, HTTP‑архивы, собственный формат. Ни один из них не превзошёл git:

- **Нулевой шаг сборки для авторов.** Пушишь в GitHub — потребители устанавливают. Нет цикла «упаковать это, загрузить то, обновить индекс».
- **Теги, ветки и коммиты уже являются системой версионирования.** Пуш тега делает для нас то, что «упаковать + загрузить релиз» делает в других инструментах.
- **Обновления — это fetch.** Не требуется повторно скачивать весь архив.
- **Прозрачность.** Пользователи могут просматривать репозиторий, читать диффы между версиями, открывать issue, форкать его для кастомизации.
- **Приватные репозитории работают бесплатно.** SSH‑ключи, `git credential`‑хелперы, сохранённые учётные данные GitHub CLI — любая аутентификация, уже настроенная в твоём терминале, применяется прозрачно.
- **Воспроизводимость — это SHA коммита.** То же самое фиксируют pip и npm.

**Компромисс:** получателям нужен установленный git. На любой машине, где работает Hermes в 2026 году, это уже так.
## Когда следует использовать дистрибутив?

Подходящие случаи:

- **Ты делишься специализированным агентом** — монитором соответствия, ревьюером кода, помощником исследователя, ботом поддержки клиентов — с командой или сообществом.
- **Ты развёртываешь один и тот же агент на нескольких машинах** и не хочешь каждый раз копировать файлы вручную.
- **Ты итеративно разрабатываешь агент** и хочешь, чтобы получатели получали новые версии одной командой.
- **Ты создаёшь агент как продукт** — предустановленные настройки, отобранные инструменты, настроенные подсказки — который другие люди могут использовать в качестве отправной точки.

Не подходит:

- **Ты просто хочешь создать резервную копию профиля на своей машине.** Используй [`hermes profile export` / `import`](../reference/profile-commands.md#hermes-profile-export) — для этого они и предназначены.
- **Ты хочешь поделиться API‑ключами вместе с агентом.** `auth.json` и `.env` намеренно исключены из дистрибутивов. Каждый установщик использует свои учётные данные.
- **Ты хочешь поделиться памятью / сессиями / историей разговоров.** Это пользовательские данные, а не содержимое дистрибутива. Никогда не поставляются.
## Жизненный цикл: от автора к установщику к обновлению

Ниже показан полный сквозной процесс. Выбери сторону, которая тебя интересует.

---
## Для авторов: публикация дистрибутива

### Шаг 1 — Начни с рабочего профиля

Собирай и дорабатывай агента, как любой другой профиль:

```bash
hermes profile create research-bot
research-bot setup                    # configure model, API keys
# Edit ~/.hermes/profiles/research-bot/SOUL.md
# Install skills, wire up MCP servers, schedule cron jobs, etc.
research-bot chat                     # dogfood until it feels right
```

### Шаг 2 — Добавь `distribution.yaml`

Создай `~/.hermes/profiles/research-bot/distribution.yaml`:

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

Это весь манифест. Все поля, кроме `name`, имеют разумные значения по умолчанию.

### Шаг 3 — Запушь в git‑репозиторий

```bash
cd ~/.hermes/profiles/research-bot
git init
git add .
git commit -m "v1.0.0"
git remote add origin git@github.com:you/research-bot.git
git tag v1.0.0
git push -u origin main --tags
```

Теперь репозиторий является дистрибутивом. Любой, у кого есть доступ, может установить его.

:::note
Git‑репозиторий содержит **всё в каталоге профиля, кроме того, что уже исключено из дистрибутивов**: `auth.json`, `.env`, `memories/`, `sessions/`, `state.db*`, `logs/`, `workspace/`, `*_cache/`, `local/`. Эти файлы остаются на твоей машине. При желании можно добавить `.gitignore`, чтобы исключить дополнительные пути.
:::

### Шаг 4 — Тегировать версии релизов

Каждый раз, когда агент достигает стабильного состояния, увеличивай версию и ставь тег:

```bash
# Edit distribution.yaml: version: 1.1.0
git add distribution.yaml SOUL.md skills/
git commit -m "v1.1.0: tighter research SOUL, add arxiv skill"
git tag v1.1.0
git push --tags
```

Получатели, которые выполняют `hermes profile update research-bot`, получат последние изменения.

### Как выглядит репозиторий

Полный созданный дистрибутив:

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

### Что принадлежит дистрибутиву, а что пользователю

При обновлении установщиком до новой версии некоторые файлы заменяются (домены автора), а некоторые остаются нетронутыми (домены установщика). Значения по умолчанию:

| Категория | Пути | При обновлении |
|---|---|---|
| **Distribution-owned** | `SOUL.md`, `config.yaml`, `mcp.json`, `skills/`, `cron/`, `distribution.yaml` | Заменяются из нового клона |
| **Config override** | `config.yaml` | На самом деле сохраняется по умолчанию — установщик мог настроить модель или провайдера. Передай `--force-config` при обновлении, чтобы сбросить. |
| **User-owned** | `memories/`, `sessions/`, `state.db*`, `auth.json`, `.env`, `logs/`, `workspace/`, `plans/`, `home/`, `*_cache/`, `local/` | Никогда не трогаются |

Список файлов, принадлежащих дистрибутиву, можно переопределить в манифесте:

```yaml
distribution_owned:
  - SOUL.md
  - skills/research/            # only my research skills; other installed skills stay
  - cron/digest.json
```

Если не указано, применяются значения по умолчанию, указанные выше — что подходит большинству дистрибутивов.
## Для установщиков: использование дистрибутива

### Установка

```bash
hermes profile install github.com/you/research-bot --alias
```

Что происходит:

1. Клонирует репозиторий во временный каталог.
2. Читает `distribution.yaml`, показывает манифест (имя, версия, описание, автор, требуемые переменные окружения).
3. Проверяет каждую требуемую переменную окружения в твоей оболочке и в существующем `.env` целевого профиля. Отмечает каждую как `✓ set` или `needs setting` — `needs setting` заменяется на «нужна настройка», чтобы ты точно знал, что нужно сконфигурировать.
4. Запрашивает подтверждение. Передай `-y` / `--yes`, чтобы пропустить.
5. Копирует файлы, принадлежащие дистрибутиву, в `~/.hermes/profiles/research-bot/` (или туда, куда указывает `name` в манифесте).
6. Записывает `.env.EXAMPLE` с требуемыми ключами, закомментированными — скопируй в `.env` и заполни.
7. С `--alias` создаёт обёртку, чтобы ты мог запускать `research-bot chat` напрямую.

### Типы источников

Любой git‑URL подходит:

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

### Переопределение имени профиля

Два пользователя хотят один и тот же дистрибутив под разными именами профилей:

```bash
# Alice
hermes profile install github.com/acme/support-bot --name support-us --alias
# Bob (same distribution, different local name)
hermes profile install github.com/acme/support-bot --name support-eu --alias
```

### Заполнение переменных окружения

После установки в профиле агента появляется файл `.env.EXAMPLE`:

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

Скопируй его:

```bash
cp ~/.hermes/profiles/research-bot/.env.EXAMPLE ~/.hermes/profiles/research-bot/.env
# Edit .env, paste your real keys
```

Требуемые ключи, которые уже присутствовали в твоей оболочке (например, `OPENAI_API_KEY`, экспортированный в `~/.zshrc`), отмечены `✓ set` во время установки — их не нужно дублировать в `.env`.

### Проверка установленного

```bash
hermes profile info research-bot
```

Показывает:

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

Команда `hermes profile list` также выводит столбец `Distribution`, так что сразу видно, какие профили пришли из репозиториев, а какие ты создал вручную:

```
 Profile          Model                        Gateway      Alias        Distribution
 ───────────────    ───────────────────────────    ───────────    ───────────    ────────────────────
 ◆default         claude-sonnet-4              stopped      —            —
  coder           gpt-5                        stopped      coder        —
  research-bot    claude-opus-4                stopped      research-bot research-bot@1.0.0
  telemetry       claude-sonnet-4              running      telemetry    telemetry@2.3.1
```

### Обновление

```bash
hermes profile update research-bot
```

Что происходит:

1. Повторно клонирует репозиторий из записанного URL‑источника.
2. Заменяет файлы, принадлежащие дистрибутиву (SOUL, skills, cron, mcp.json).
3. **Сохраняет** твой `config.yaml` — ты мог настроить модель, температуру или другие параметры. Передай `--force-config`, чтобы перезаписать.
4. **Никогда не трогает** пользовательские данные: память, сессии, аутентификацию, `.env`, логи, состояние.

Без повторного скачивания всего архива. Без перезаписи твоих локальных изменений конфигурации. Без удаления истории разговоров.

### Удаление

```bash
hermes profile delete research-bot
```

Запрос на удаление сначала показывает информацию о дистрибутиве, а затем просит подтверждения:

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

Таким образом, ты никогда не удалишь агент случайно, не зная его происхождения или не имея возможности переустановить его.
## Сценарии использования и шаблоны

### Персональный: синхронизация одного агента между машинами

Ты создал исследовательского помощника на ноутбуке. Хочешь тот же агент на рабочей станции.

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

Любая итерация на ноутбуке (`git commit && push`) подтягивается на рабочую станцию командой `hermes profile update research-bot`. Память хранится отдельно на каждой машине — ноутбук сохраняет свои разговоры, рабочая станция — свои, они не конфликтуют.

### Командный: развернуть проверенного внутреннего агента

Твоя инженерная команда хочет общий бот для ревью PR с определённым SOUL, набором навыков и cron, который будет запускать его для каждого PR.

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

Когда лидер выпускает v1.1 (лучший SOUL, новый навык), инженеры выполняют `hermes profile update pr-reviewer`, и у всех новая версия уже через несколько минут.

### Сообщество: публикация публичного агента

Ты создал что‑то новое — например, «трейдер Polymarket», «резюмер академических статей» или «ассистент операторов сервера Minecraft». Хочешь поделиться этим.

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

Твитни команду установки. Люди, которые её используют, отправляют тебе баги и PR. Если кто‑то хочет кастомизировать, он форкает — тот же git‑workflow, который уже знаком всем.

### Продукт: выпуск opinionated‑агента

Ты построил Hermes‑on‑top — возможно, систему мониторинга соответствия, стек поддержки клиентов или доменно‑специфичную исследовательскую платформу. Хочешь распространять её как продукт.

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

Твои клиенты устанавливают её одной командой; превью установки показывает, какие ключи нужно подготовить; обновления выкатываются сразу после создания нового релиза; их данные соответствия (`memories/`, `sessions/`) никогда не покидают их машину.

### Эфемерный: одноразовые скрипты в общей инфраструктуре

Ты — лидер ops. Нужно временный агент, который диагностирует инцидент в продакшене — готовый SOUL с нужными инструментами и подключениями MCP — и работает на ноутбуках трёх дежурных инженеров в течение недели.

```bash
# You
# Build the profile, commit, push a private repo
git push -u origin main

# Each on-call
hermes profile install git@github.com:your-org/incident-2026-q2.git --alias

# Incident resolved — tear it down
hermes profile delete incident-2026-q2
```

Цикл «установить‑удалить» достаточно дешёвый, чтобы быть одноразовым.

---
## Рецепты

### Закрепление на конкретной версии

:::note
Закрепление Git‑рефа (`#v1.2.0`) запланировано, но не будет в начальном выпуске — сейчас `install` отслеживает ветку по умолчанию. Отслеживай установленную версию через `hermes profile info <name>` и откладывай обновления, пока не будешь готов.
:::

### Проверка текущей версии относительно последней

```bash
# Your installed version
hermes profile info research-bot | grep Version

# Latest upstream (without installing)
git ls-remote --tags https://github.com/you/research-bot | tail -5
```

### Сохранение локальных настроек при обновлениях

Поведение обновления по умолчанию уже делает это: `config.yaml` сохраняется. Чтобы быть уверенным, запиши свои локальные правки в файл, которым не управляет дистрибутив:

```yaml
# ~/.hermes/profiles/research-bot/local/my-overrides.yaml
# (distribution never touches local/)
```

…и подключи его из `config.yaml` или своего SOUL по необходимости.

### Принудительная чистая переустановка

```bash
# Nuke and re-install from scratch (loses memories/sessions too)
hermes profile delete research-bot --yes
hermes profile install github.com/you/research-bot --alias

# Update to current main but reset config.yaml to the distribution's default
hermes profile update research-bot --force-config --yes
```

### Форк и кастомизация

Стандартный git‑workflow — дистрибутивы это просто репозитории:

```bash
# Fork the repo on GitHub, then install your fork
hermes profile install github.com/yourname/forked-research-bot --alias

# Iterate locally in ~/.hermes/profiles/forked-research-bot/
# Edit SOUL.md, commit, push to your fork
# Upstream changes: pull them into your fork the usual way
```

### Тестирование дистрибутива перед публикацией

С машины автора:

```bash
# Install from a local directory (no git push needed)
hermes profile install ~/.hermes/profiles/research-bot --name research-bot-test --alias

# Tweak, delete, re-install until it's right
hermes profile delete research-bot-test --yes
hermes profile install ~/.hermes/profiles/research-bot --name research-bot-test
```

---
## Что НЕ входит в дистрибутив (никогда)

Установщик жёстко исключает эти пути, даже если автор случайно их добавит. Ни одна опция конфигурации не позволяет переопределить это — защита является проверенным регрессионным инвариантом:

- `auth.json` — OAuth‑токены, учётные данные платформы
- `.env` — API‑ключи, секреты
- `memories/` — память диалогов
- `sessions/` — история диалогов
- `state.db`, `state.db-shm`, `state.db-wal` — метаданные сессии
- `logs/` — журналы агента и ошибки
- `workspace/` — сгенерированные рабочие файлы
- `plans/` — черновые планы
- `home/` — домашний монтируемый каталог пользователя в Docker‑бэкендах
- `*_cache/` — кеши изображений/аудио/документов
- `local/` — пользовательское пространство настройки

Когда ты клонируешь дистрибутив, этих элементов просто нет. При обновлении они остаются на месте. Если ты установил один и тот же дистрибутив на пяти машинах, у тебя будет пять изолированных наборов этих данных — по одному на каждую машину.
## Безопасность и доверие

Распределения профилей по умолчанию не подписаны. Ты доверяешь:

- **Git‑хосту** (GitHub / GitLab / где‑угодно), который отдаёт байты, загруженные автором.
- **Автору**, который не добавит вредоносный SOUL, skills или cron‑задачи.

Cron‑задачи из распределения **не планируются автоматически** — установщик выводит `hermes -p <name> cron list`, и ты включаешь их явно. SOUL.md и skills активируются сразу после начала общения с профилем, поэтому прочитай их перед первым запуском, если устанавливаешь от кого‑то, кого не знаешь.

Грубая аналогия: установка распределения похожа на установку расширения браузера или расширения VS Code. Низкое трение, высокая мощность, доверяй источнику. Для внутренних распределений компании используй приватный репозиторий и обычную аутентификацию Git — ничего нового настраивать не нужно.

В будущих версиях может появиться подпись, lock‑файл (`.distribution-lock.yaml`) с зафиксированным SHA коммита и флаг `--dry-run`, который выводит различия перед применением обновления. Пока ни один из этих механизмов не поставляется.
## Под капотом

Для деталей реализации, точного поведения CLI и всех флагов смотри [Справочник команд профиля](../reference/profile-commands.md#distribution-commands).

Кратко:

- `install`, `update`, `info` находятся внутри `hermes profile` — это не отдельное дерево команд.
- Формат манифеста — YAML с небольшой обязательной схемой (`name` только).
- Установщик использует твой локальный бинарный `git` для клонирования, поэтому любая аутентификация, которую уже обрабатывает твой шелл (SSH‑ключи, помощники учётных данных), работает прозрачно.
- После клонирования каталог `.git/` удаляется — установленный профиль сам по себе не является git‑checkout, что избавляет от ловушек типа «ой, я случайно закоммитил свой `.env` в историю git дистрибутива».
- Зарезервированные имена профилей (`hermes`, `test`, `tmp`, `root`, `sudo`) отклоняются во время установки, чтобы избежать конфликтов с распространёнными бинарными файлами.
## См. также

- [Профили: запуск нескольких агентов](./profiles.md) — базовая концепция
- [Справочник команд профиля](../reference/profile-commands.md) — каждый флаг, каждая опция
- [`hermes profile export` / `import`](../reference/profile-commands.md#hermes-profile-export) — локальное резервное копирование/восстановление (не для распространения)
- [Использование SOUL с Hermes](../guides/use-soul-with-hermes.md) — создание персональностей
- [Личность и SOUL](./features/personality.md) — как SOUL вписывается в агента
- [Каталог навыков](../reference/skills-catalog.md) — навыки, которые можно собрать в пакет