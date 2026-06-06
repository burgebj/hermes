---
sidebar_position: 2
title: "Skills система"
description: "Документы знаний по запросу — прогрессивное раскрытие, управляемые агентом skills и Skills Hub"
---

# Система навыков

Навыки — это документы знаний по запросу, которые агент может загрузить при необходимости. Они используют шаблон **прогрессивного раскрытия** для минимизации использования токенов и совместимы с открытым стандартом [agentskills.io](https://agentskills.io/specification).

Все навыки находятся в **`~/.hermes/skills/`** — основном каталоге и источнике правды. При свежей установке встроенные навыки копируются из репозитория. Навыки, установленные через Hub, и созданные агентом, также помещаются сюда. Агент может изменять или удалять любой навык.

Ты также можешь указать Hermes внешние каталоги навыков — дополнительные папки, сканируемые вместе с локальной. См. [Внешние каталоги навыков](#external-skill-directories).

См. также:

- [Каталог встроенных навыков](/reference/skills-catalog)
- [Официальный каталог дополнительных навыков](/reference/optional-skills-catalog)
## Использование навыков

Каждый установленный навык автоматически доступен как слеш‑команда:

```bash
# In the CLI or any messaging platform:
/gif-search funny cats
/axolotl help me fine-tune Llama 3 on my dataset
/github-pr-workflow create a PR for the auth refactor
/plan design a rollout for migrating our auth provider

# Just the skill name loads it and lets the agent ask what you need:
/excalidraw
```

Встроенный навык `plan` — хороший пример. Выполнение `/plan [request]` загружает инструкции навыка, заставляя Hermes при необходимости проанализировать контекст, написать план реализации в markdown вместо выполнения задачи и сохранить результат в `.hermes/plans/` относительно активного рабочего каталога/бэкенда.

Ты также можешь взаимодействовать с навыками через естественный диалог:

```bash
hermes chat --toolsets skills -q "What skills do you have?"
hermes chat --toolsets skills -q "Show me the axolotl skill"
```
## Прогрессивное раскрытие

Навыки используют токен‑экономичный шаблон загрузки:

```
Level 0: skills_list()           → [{name, description, category}, ...]   (~3k tokens)
Level 1: skill_view(name)        → Full content + metadata       (varies)
Level 2: skill_view(name, path)  → Specific reference file       (varies)
```

Агент загружает полное содержание навыка только тогда, когда это действительно требуется.
## Формат SKILL.md

```markdown
---
name: my-skill
description: Brief description of what this skill does
version: 1.0.0
platforms: [macos, linux]     # Optional — restrict to specific OS platforms
metadata:
  hermes:
    tags: [python, automation]
    category: devops
    fallback_for_toolsets: [web]    # Optional — conditional activation (see below)
    requires_toolsets: [terminal]   # Optional — conditional activation (see below)
    config:                          # Optional — config.yaml settings
      - key: my.setting
        description: "What this controls"
        default: "value"
        prompt: "Prompt for setup"
---

# Skill Title

## When to Use
Trigger conditions for this skill.

## Procedure
1. Step one
2. Step two

## Pitfalls
- Known failure modes and fixes

## Verification
How to confirm it worked.
```

### Платформенно‑специфичные навыки

Навыки могут ограничивать себя конкретными операционными системами с помощью поля `platforms`:

| Значение | Соответствия |
|----------|--------------|
| `macos`   | macOS (Darwin) |
| `linux`   | Linux |
| `windows` | Windows |

```yaml
platforms: [macos]            # macOS only (e.g., iMessage, Apple Reminders, FindMy)
platforms: [macos, linux]     # macOS and Linux
```

Если параметр установлен, навык автоматически скрывается из системной подсказки, `skills_list()` и слеш‑команд на несовместимых платформах. Если параметр опущен, навык загружается на всех платформах.
## Вывод навыка и доставка медиа

Когда ответ навыка (или любой ответ агента) содержит «голый» абсолютный путь к медиа‑файлу — например `/home/user/screenshots/diagram.png` — шлюз автоматически обнаруживает его, удаляет из видимого текста и доставляет файл нативно в чат пользователя (фото в Telegram, вложение в Discord и т.д.), вместо того чтобы оставлять в сообщении сырой путь.

Для аудио директива `[[audio_as_voice]]` преобразует аудио‑файлы в нативные голосовые сообщения на платформах, которые их поддерживают (Telegram, WhatsApp).

### Принудительная доставка в виде документа: `[[as_document]]`

Иногда нужен **противоположный** эффект от встроенного превью: файл должен быть доставлен как загружаемое вложение, а не как пере‑сжатый пузырёк‑изображение. Классический пример — скриншот или график высокого разрешения: `sendPhoto` в Telegram перекодирует его до ~200 KB при 1280 px, разрушая читаемость. PNG размером 1‑2 MB, отправленный через `sendDocument`, сохраняет оригинальные байты.

Если ответ (или любой текст внутри него — обычно последняя строка) содержит буквальную директиву `[[as_document]]`, каждый путь к медиа, извлечённый из этого ответа, будет доставлен как документ/вложение, а не как пузырёк‑изображение:

```
Here is your rendered chart:

/home/user/.hermes/cache/chart-q4-2025.png

[[as_document]]
```

Директива удаляется перед доставкой, поэтому пользователи её не видят. Гранулярность намеренно «всё или ничего» для каждого ответа: указываешь `[[as_document]]` один раз, и все пути к изображениям в том же ответе доставляются как документы. Это аналогично области действия `[[audio_as_voice]]`.

Используй её в навыке, когда:

- Ты генерируешь скриншоты или графики, которые пользователю нужны как файлы (для редактирования в другом инструменте, архивирования, передачи без потерь).
- Стандартное сжатое превью скрывает детали (маленький текст, пиксельно‑точные схемы, цветочувствительные рендеры).

Платформы без отдельного пути для документов (например SMS) используют любой доступный механизм вложений.

### Условная активация (запасные навыки)

Навыки могут автоматически показываться или скрываться в зависимости от того, какие инструменты доступны в текущей сессии. Это особенно полезно для **запасных навыков** — бесплатных или локальных альтернатив, которые должны появляться только тогда, когда премиум‑инструмент недоступен.

```yaml
metadata:
  hermes:
    fallback_for_toolsets: [web]      # Show ONLY when these toolsets are unavailable
    requires_toolsets: [terminal]     # Show ONLY when these toolsets are available
    fallback_for_tools: [web_search]  # Show ONLY when these specific tools are unavailable
    requires_tools: [terminal]        # Show ONLY when these specific tools are available
```

| Поле | Поведение |
|------|-----------|
| `fallback_for_toolsets` | Навык **скрывается**, когда указанные наборы инструментов доступны. Появляется, когда их нет. |
| `fallback_for_tools` | То же, но проверяются отдельные инструменты вместо наборов. |
| `requires_toolsets` | Навык **скрывается**, когда указанные наборы инструментов недоступны. Появляется, когда они присутствуют. |
| `requires_tools` | То же, но проверяются отдельные инструменты. |

**Пример:** встроенный навык `duckduckgo-search` использует `fallback_for_toolsets: [web]`. Когда у тебя установлен `FIRECRAWL_API_KEY`, набор инструментов `web` доступен, и агент использует `web_search` — навык DuckDuckGo остаётся скрытым. Если ключ API отсутствует, набор `web` недоступен, и навык DuckDuckGo автоматически появляется как запасной.

Навыки без каких‑либо условных полей ведут себя как раньше — они всегда показываются.
## Безопасная настройка при загрузке

Навыки могут объявлять необходимые переменные окружения, не исчезая из списка обнаружения:

```yaml
required_environment_variables:
  - name: TENOR_API_KEY
    prompt: Tenor API key
    help: Get a key from https://developers.google.com/tenor
    required_for: full functionality
```

Когда встречается отсутствие значения, Hermes запрашивает его безопасно только в тот момент, когда навык действительно загружается в локальном CLI. Можно пропустить настройку и продолжать использовать навык. В интерфейсах обмена сообщениями запросов секретов в чате не происходит — вместо этого они советуют использовать `hermes setup` или `~/.hermes/.env` локально.

После установки объявленные переменные окружения **автоматически передаются** в песочницы `execute_code` и `terminal` — скрипты навыка могут обращаться к `$TENOR_API_KEY` напрямую. Для переменных окружения, не относящихся к навыкам, используйте опцию конфигурации `terminal.env_passthrough`. См. [Environment Variable Passthrough](/user-guide/security#environment-variable-passthrough) для подробностей.

### Параметры конфигурации навыка

Навыки также могут объявлять неконфиденциальные параметры конфигурации (пути, предпочтения), хранящиеся в `config.yaml`:

```yaml
metadata:
  hermes:
    config:
      - key: myplugin.path
        description: Path to the plugin data directory
        default: "~/myplugin-data"
        prompt: Plugin data directory path
```

Параметры сохраняются под `skills.config` в вашем `config.yaml`. Команда `hermes config migrate` запрашивает значения для неустановленных параметров, а `hermes config show` выводит их. При загрузке навыка его разрешённые значения конфигурации внедряются в контекст, чтобы агент автоматически знал настроенные значения.

См. [Skill Settings](/user-guide/configuration#skill-settings) и [Creating Skills — Config Settings](/developer-guide/creating-skills#config-settings-configyaml) для подробностей.
## Структура каталога навыков

```text
~/.hermes/skills/                  # Single source of truth
├── mlops/                         # Category directory
│   ├── axolotl/
│   │   ├── SKILL.md               # Main instructions (required)
│   │   ├── references/            # Additional docs
│   │   ├── templates/             # Output formats
│   │   ├── scripts/               # Helper scripts callable from the skill
│   │   └── assets/                # Supplementary files
│   └── vllm/
│       └── SKILL.md
├── devops/
│   └── deploy-k8s/                # Agent-created skill
│       ├── SKILL.md
│       └── references/
├── .hub/                          # Skills Hub state
│   ├── lock.json
│   ├── quarantine/
│   └── audit.log
└── .bundled_manifest              # Tracks seeded bundled skills
```
## Внешние каталоги навыков

Если ты хранишь навыки вне Hermes — например, в общем каталоге `~/.agents/skills/`, используемом несколькими AI‑инструментами — ты можешь указать Hermes сканировать и эти каталоги.

Добавь `external_dirs` в раздел `skills` в файле `~/.hermes/config.yaml`:

```yaml
skills:
  external_dirs:
    - ~/.agents/skills
    - /home/shared/team-skills
    - ${SKILLS_REPO}/skills
```

Пути поддерживают расширение `~` и подстановку переменных окружения `${VAR}`.

### Как это работает

- **Создавай локально, обновляй на месте**: новые навыки, создаваемые агентом, записываются в `~/.hermes/skills/`. Существующие навыки изменяются там, где они находятся, включая навыки из `external_dirs`, когда агент использует действия `skill_manage`, такие как `patch`, `edit`, `write_file`, `remove_file` или `delete`.
- **Внешние каталоги не являются границей защиты от записи**: если внешний каталог навыков доступен для записи процессу Hermes, обновления навыков, управляемые агентом, могут менять файлы в этом каталоге. Используй разрешения файловой системы или отдельную настройку профиля/наборов инструментов, если общие внешние навыки должны оставаться только для чтения.
- **Локальный приоритет**: если один и тот же навык присутствует и в локальном каталоге, и во внешнем, приоритет имеет локальная версия.
- **Полная интеграция**: внешние навыки появляются в индексе системных подсказок, `skills_list`, `skill_view` и как слеш‑команды `/skill-name` — ничем не отличаются от локальных навыков.
- **Несуществующие пути пропускаются без сообщений**: если указанный каталог не существует, Hermes игнорирует его без ошибок. Это удобно для опциональных общих каталогов, которые могут отсутствовать на некоторых машинах.

### Пример

```text
~/.hermes/skills/               # Local (primary, read-write)
├── devops/deploy-k8s/
│   └── SKILL.md
└── mlops/axolotl/
    └── SKILL.md

~/.agents/skills/               # External (shared, mutable if writable)
├── my-custom-workflow/
│   └── SKILL.md
└── team-conventions/
    └── SKILL.md
```

Все четыре навыка появляются в твоём индексе навыков. Если ты создашь новый навык `my-custom-workflow` локально, он будет перекрывать внешнюю версию.
## Пакеты навыков

Пакеты навыков — это небольшие YAML‑файлы, которые группируют несколько навыков под одной slash‑командой. Когда ты вызываешь `/<bundle-name>`, все навыки, перечисленные в пакете, загружаются сразу — удобно, когда конкретная задача всегда выигрывает от одинакового набора навыков вместе.

### Быстрый пример

```bash
# Create a bundle for backend feature work
hermes bundles create backend-dev \
  --skill github-code-review \
  --skill test-driven-development \
  --skill github-pr-workflow \
  -d "Backend feature work — review, test, PR workflow"
```

Затем в CLI или любой платформе шлюза:

```
/backend-dev refactor the auth middleware
```

Агент получает все три навыка, загруженные в одно пользовательское сообщение, а любой текст после slash‑команды прикрепляется как инструкция пользователя.

### Схема YAML

Пакеты находятся в **`~/.hermes/skill-bundles/<slug>.yaml`** и выглядят так:

```yaml
name: backend-dev
description: Backend feature work — review, test, PR workflow.
skills:
  - github-code-review
  - test-driven-development
  - github-pr-workflow
instruction: |
  Always start by writing failing tests, then implement.
  Open the PR through the standard workflow with co-author tags.
```

**Поля**
- `name` (необязательно — по умолчанию берётся имя файла) — отображаемое название пакета. Нормализуется в slug с дефисом для slash‑команды (`Backend Dev` → `/backend-dev`).
- `description` (необязательно) — короткий текст, показываемый в `/bundles` и `hermes bundles list`.
- `skills` (обязательно, непустой список) — имена навыков или пути, относительные к твоему каталогу навыков. Используй тот же идентификатор, который передаёшь в `/<skill-name>`.
- `instruction` (необязательно) — дополнительное руководство, добавляемое перед загруженным содержимым навыка. Полезно для фиксирования «как мы всегда используем их вместе».

### Управление пакетами

```bash
# List all installed bundles
hermes bundles list

# Inspect one bundle
hermes bundles show backend-dev

# Create a bundle interactively (omit --skill flags to enter them one per line)
hermes bundles create research

# Overwrite an existing bundle
hermes bundles create backend-dev --skill ... --force

# Delete a bundle
hermes bundles delete backend-dev

# Re-scan ~/.hermes/skill-bundles/ and report changes
hermes bundles reload
```

Изнутри чат‑сессии команда `/bundles` выводит список всех установленных пакетов и их навыков.

### Поведение

- **Пакеты имеют приоритет над отдельными навыками**, когда их slug совпадают. Если ты назовёшь пакет `research`, а также у тебя есть навык `research`, команда `/research` вызовет пакет. Это задумано — ты выбираешь пакет, задав ему такое имя.
- **Отсутствующие навыки пропускаются, а не вызывают ошибку.** Если в пакете указан `skill-foo`, но он не установлен, пакет всё равно загрузит те навыки, которые найдёт, а агент получит заметку со списком пропущенных.
- **Пакеты работают на любой поверхности** — интерактивный CLI, TUI, чат‑дашборд и любые платформы шлюза (Telegram, Discord, Slack, …) — потому что диспетчеризация централизована в том же месте, что и отдельные команды навыков.
- **Пакеты не инвалидируют кеш подсказок.** Они генерируют новое пользовательское сообщение в момент вызова, так же как делает `/<skill-name>` — без изменения системной подсказки.

### Когда пакеты лучше, чем устанавливать каждый навык вручную

Используй пакет, когда:
- Ты всегда комбинируешь одни и те же навыки для повторяющейся задачи (`/backend-dev`, `/release-prep`, `/incident-response`).
- Хочешь иметь более короткую ментальную модель, чем набор нескольких вызовов `/skill` подряд.
- Хочешь распространить «профиль задачи» на всю команду, разместив YAML пакета в общем репозитории dotfiles и создав символическую ссылку в `~/.hermes/skill-bundles/`.

Пакет — это просто YAML‑алиас; он не устанавливает навыки за тебя. Сами навыки должны уже присутствовать (в `~/.hermes/skills/` или внешнем каталоге навыков). В противном случае вызов пакета просто пропустит отсутствующие.
## Навыки, управляемые агентом (инструмент `skill_manage`)

Агент может создавать, обновлять и удалять свои собственные навыки с помощью инструмента `skill_manage`. Это **процедурная память** агента — когда он разрабатывает нетривиальный рабочий процесс, он сохраняет подход как навык для будущего повторного использования.

### Когда агент создаёт навыки

- После успешного завершения сложной задачи (5 + вызовов инструмента)
- Когда он столкнулся с ошибками или тупиками и нашёл рабочий путь
- Когда пользователь исправил его подход
- Когда он обнаружил нетривиальный рабочий процесс

### Действия

| Действие | Назначение | Ключевые параметры |
|----------|------------|--------------------|
| `create` | Новый навык с нуля | `name`, `content` (полный `SKILL.md`), опционально `category` |
| `patch` | Целевые исправления (предпочтительно) | `name`, `old_string`, `new_string` |
| `edit` | Крупные структурные переписывания | `name`, `content` (полная замена `SKILL.md`) |
| `delete` | Полное удаление навыка | `name` |
| `write_file` | Добавление/обновление вспомогательных файлов | `name`, `file_path`, `file_content` |
| `remove_file` | Удаление вспомогательного файла | `name`, `file_path` |

:::tip
Действие `patch` предпочтительно для обновлений — оно более экономично по токенам, чем `edit`, поскольку в вызове инструмента появляется только изменённый текст.
:::
## Центр навыков

Просматривай, ищи, устанавливай и управляй навыками из онлайн‑реестров, `skills.sh`, прямых известных конечных точек навыков и официальных дополнительных навыков.

### Распространённые команды

```bash
hermes skills browse                              # Browse all hub skills (official first)
hermes skills browse --source official            # Browse only official optional skills
hermes skills search kubernetes                   # Search all sources
hermes skills search react --source skills-sh     # Search the skills.sh directory
hermes skills search https://mintlify.com/docs --source well-known
hermes skills inspect openai/skills/k8s           # Preview before installing
hermes skills install openai/skills/k8s           # Install with security scan
hermes skills install official/security/1password
hermes skills install skills-sh/vercel-labs/json-render/json-render-react --force
hermes skills install well-known:https://mintlify.com/docs/.well-known/skills/mintlify
hermes skills install https://sharethis.chat/SKILL.md              # Direct URL (single-file SKILL.md)
hermes skills install https://example.com/SKILL.md --name my-skill # Override name when frontmatter has none
hermes skills list --source hub                   # List hub-installed skills
hermes skills check                               # Check installed hub skills for upstream updates
hermes skills update                              # Reinstall hub skills with upstream changes when needed
hermes skills audit                               # Re-scan all hub skills for security
hermes skills uninstall k8s                       # Remove a hub skill
hermes skills reset google-workspace              # Un-stick a bundled skill from "user-modified" (see below)
hermes skills reset google-workspace --restore    # Also restore the bundled version, deleting your local edits
hermes skills publish skills/my-skill --to github --repo owner/repo
hermes skills snapshot export setup.json          # Export skill config
hermes skills tap add myorg/skills-repo           # Add a custom GitHub source
```

### Поддерживаемые источники центра

| Источник | Пример | Примечания |
|--------|---------|-------|
| `official` | `official/security/1password` | Дополнительные навыки, поставляемые с Hermes. |
| `skills-sh` | `skills-sh/vercel-labs/agent-skills/vercel-react-best-practices` | Доступно через `hermes skills search <query> --source skills-sh`. Hermes разрешает псевдонимы навыков, когда slug в skills.sh отличается от папки репозитория. |
| `well-known` | `well-known:https://mintlify.com/docs/.well-known/skills/mintlify` | Навыки, обслуживаемые напрямую из `/.well-known/skills/index.json` на сайте. Поиск по URL сайта или документации. |
| `url` | `https://sharethis.chat/SKILL.md` | Прямая HTTP(S)‑ссылка на одиночный файл `SKILL.md`. Разрешение имени: frontmatter → slug URL → интерактивный запрос → флаг `--name`. |
| `github` | `openai/skills/k8s` | Прямая установка из репозитория GitHub и пользовательские tap‑ы. |
| `clawhub`, `lobehub`, `browse-sh` | Идентификаторы, специфичные для источника | Интеграции сообщества или маркетплейса. |

### Интегрированные центры и реестры

Hermes в настоящее время интегрирует следующие экосистемы навыков и источники их обнаружения:

#### 1. Официальные дополнительные навыки (`official`)

Поддерживаются непосредственно в репозитории Hermes и устанавливаются с встроенным доверием.

- Каталог: [Official Optional Skills Catalog](../../reference/optional-skills-catalog)
- Путь в репозитории: `optional-skills/`
- Пример:

```bash
hermes skills browse --source official
hermes skills install official/security/1password
```

#### 2. skills.sh (`skills-sh`)

Публичный каталог навыков от Vercel. Hermes может искать его напрямую, просматривать страницы деталей навыков, разрешать псевдонимы slug и устанавливать из исходного репозитория.

- Каталог: [skills.sh](https://skills.sh/)
- Репозиторий CLI/инструментов: [vercel-labs/skills](https://github.com/vercel-labs/skills)
- Официальный репозиторий навыков Vercel: [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills)
- Пример:

```bash
hermes skills search react --source skills-sh
hermes skills inspect skills-sh/vercel-labs/json-render/json-render-react
hermes skills install skills-sh/vercel-labs/json-render/json-render-react --force
```

#### 3. Конечные точки известных навыков (`well-known`)

Обнаружение по URL с сайтов, публикующих `/.well-known/skills/index.json`. Это не единый централизованный центр — это веб‑конвенция обнаружения.

- Пример живой конечной точки: [Индекс навыков документации Mintlify](https://mintlify.com/docs/.well-known/skills/index.json)
- Реализация референс‑сервера: [vercel-labs/skills-handler](https://github.com/vercel-labs/skills-handler)
- Пример:

```bash
hermes skills search https://mintlify.com/docs --source well-known
hermes skills inspect well-known:https://mintlify.com/docs/.well-known/skills/mintlify
hermes skills install well-known:https://mintlify.com/docs/.well-known/skills/mintlify
```

#### 4. Прямые навыки GitHub (`github`)

Hermes может устанавливать напрямую из репозиториев GitHub и tap‑ов на их основе. Это удобно, когда известен репозиторий/путь или требуется добавить собственный кастомный репозиторий.

Стандартные tap‑ы (доступные без дополнительной настройки):
- [openai/skills](https://github.com/openai/skills)
- [anthropics/skills](https://github.com/anthropics/skills)
- [huggingface/skills](https://github.com/huggingface/skills)
- [garrytan/gstack](https://github.com/garrytan/gstack)

- Пример:

```bash
hermes skills install openai/skills/k8s
hermes skills tap add myorg/skills-repo
```

#### 5. ClawHub (`clawhub`)

Маркетплейс навыков от сторонних разработчиков, интегрированный как источник сообщества.

- Сайт: [clawhub.ai](https://clawhub.ai/)
- Идентификатор источника Hermes: `clawhub`

#### 6. Репозитории в стиле маркетплейса Claude (`claude-marketplace`)

Hermes поддерживает репозитории‑маркетплейсы, публикующие совместимые с Claude манифесты плагинов/маркетплейса.

Известные интегрированные источники:
- [anthropics/skills](https://github.com/anthropics/skills)
- [aiskillstore/marketplace](https://github.com/aiskillstore/marketplace)

Идентификатор источника Hermes: `claude-marketplace`

#### 7. LobeHub (`lobehub`)

Hermes может искать и конвертировать записи агентов из публичного каталога LobeHub в устанавливаемые навыки Hermes.

- Сайт: [LobeHub](https://lobehub.com/)
- Публичный индекс агентов: [chat-agents.lobehub.com](https://chat-agents.lobehub.com/)
- Репозиторий‑источник: [lobehub/lobe-chat-agents](https://github.com/lobehub/lobe-chat-agents)
- Идентификатор источника Hermes: `lobehub`

#### 8. browse.sh (`browse-sh`)

Hermes интегрируется с [browse.sh](https://browse.sh), каталогом Browserbase из более чем 200 файлов `SKILL.md` для конкретных сайтов (Airbnb, Amazon, arXiv, 12306.cn, Etsy, Xero и многие другие). Каждый навык описывает, как полностью управлять сайтом, и подходит для использования с браузерными инструментами Hermes и другими установленными навыками автоматизации браузера.

- Сайт: [browse.sh](https://browse.sh/)
- API каталога: `https://browse.sh/api/skills`
- Идентификатор источника Hermes: `browse-sh`
- Уровень доверия: `community`

```bash
hermes skills search airbnb --source browse-sh
hermes skills inspect browse-sh/airbnb.com/search-listings-ddgioa
hermes skills install browse-sh/airbnb.com/search-listings-ddgioa
```

Идентификаторы имеют форму `browse-sh/<hostname>/<task-id>` и соответствуют slug, опубликованному в каталоге browse.sh. Содержимое разрешается через эндпоинт детали навыка (`/api/skills/<slug>` → `skillMdUrl`), а не через `sourceUrl` репозитория GitHub.

#### 9. Прямая URL‑ссылка (`url`)

Устанавливай одиночный файл `SKILL.md` напрямую из любой HTTP(S)‑ссылки — удобно, когда автор размещает навык на своём сайте (без листинга в центре, без пути GitHub). Hermes скачивает URL, парсит YAML‑frontmatter, сканирует безопасность и устанавливает.

- Идентификатор источника Hermes: `url`
- Идентификатор: сама URL (префикс не нужен)
- Область применения: **только одиночный файл `SKILL.md`**. Навыки из нескольких файлов с `references/` или `scripts/` требуют манифеста и должны публиковаться через один из других источников.

```bash
hermes skills install https://sharethis.chat/SKILL.md
hermes skills install https://example.com/my-skill/SKILL.md --category productivity
```

Разрешение имени, по порядку:
1. Поле `name:` в YAML‑frontmatter `SKILL.md` (рекомендовано — каждый корректный навык имеет его).
2. Имя родительской директории из пути URL (например, `.../my-skill/SKILL.md` → `my-skill`, или `.../my-skill.md` → `my-skill`), если оно соответствует шаблону идентификатора (`^[a-z][a-z0-9_-]*$`).
3. Интерактивный запрос в терминале с TTY.
4. На неинтерактивных поверхностях (слеш‑команда `/skills install` в TUI, платформы gateway, скрипты) — чистая ошибка с указанием переопределения через флаг `--name`.

```bash
# Frontmatter has no name and the URL slug is unhelpful — supply one:
hermes skills install https://example.com/SKILL.md --name sharethis-chat

# Or inside a chat session:
/skills install https://example.com/SKILL.md --name sharethis-chat
```

Уровень доверия всегда `community` — тот же скан безопасности, что и для всех остальных источников. URL сохраняется как идентификатор установки, поэтому `hermes skills update` автоматически повторно получает его при обновлении.

### Сканирование безопасности и `--force`

Все навыки, установленные через центр, проходят **сканер безопасности**, проверяющий утечки данных, инъекции подсказок, разрушительные команды, сигналы цепочки поставок и другие угрозы.

`hermes skills inspect ...` теперь также выводит метаданные upstream, если они доступны:
- URL репозитория
- URL страницы детали в skills.sh
- Команда установки
- Еженедельные установки
- Статусы аудита безопасности upstream
- URL‑ы индексов/конечных точек well-known

Используй `--force`, когда ты проверил сторонний навык и хочешь переопределить блокировку по неопасному обнаружению:

```bash
hermes skills install skills-sh/anthropics/skills/pdf --force
```

Важные детали поведения:
- `--force` может переопределять блокировки по предупреждениям/стилю `warn`.
- `--force` **не** переопределяет verdict `dangerous`.
- Официальные дополнительные навыки (`official/...`) считаются встроенно надёжными и не показывают панель предупреждения о сторонних источниках.

### Уровни доверия

| Уровень | Источник | Политика |
|-------|--------|--------|
| `builtin` | Поставляется с Hermes | Всегда доверенный |
| `official` | `optional-skills/` в репозитории | Встроенное доверие, без предупреждения о сторонних источниках |
| `trusted` | Надёжные реестры/репозитории, такие как `openai/skills`, `anthropics/skills`, `huggingface/skills` | Более мягкая политика, чем у community‑источников |
| `community` | Всё остальное (`skills.sh`, well-known эндпоинты, кастомные репозитории GitHub, большинство маркетплейсов) | Неопасные находки можно переопределить через `--force`; verdict `dangerous` остаётся заблокированным |

### Жизненный цикл обновления

Центр теперь отслеживает достаточную провенанс‑информацию, чтобы повторно проверять upstream‑копии установленных навыков:

```bash
hermes skills check          # Report which installed hub skills changed upstream
hermes skills update         # Reinstall only the skills with updates available
hermes skills update react   # Update one specific installed hub skill
```

Это использует сохранённый идентификатор источника плюс текущий хеш содержимого upstream‑пакета для обнаружения отклонений.

:::tip GitHub rate limits
Операции центра навыков используют GitHub API, у которого лимит — 60 запросов в час для неавторизованных пользователей. Если ты получаешь ошибки ограничения лимита при установке или поиске, задай `GITHUB_TOKEN` в файле `.env`, чтобы увеличить лимит до 5 000 запросов в час. Сообщение об ошибке содержит подсказку, как действовать.
:::

### Публикация собственного tap‑а навыков

Если хочешь поделиться набором отобранных навыков — для команды, организации или публично — можешь опубликовать их как **tap**: репозиторий GitHub, который другие пользователи Hermes добавляют через `hermes skills tap add <owner/repo>`. Никакого сервера, реестра или пайплайна релизов не требуется. Просто каталог файлов `SKILL.md`.

#### Структура репозитория

Tap — это любой репозиторий GitHub (публичный или приватный — для приватных нужен `GITHUB_TOKEN`), оформленный так:

```
owner/repo
├── skills/                       # default path; configurable per-tap
│   ├── my-workflow/
│   │   ├── SKILL.md              # required
│   │   ├── references/           # optional supporting files
│   │   ├── templates/
│   │   └── scripts/
│   ├── another-skill/
│   │   └── SKILL.md
│   └── third-skill/
│       └── SKILL.md
└── README.md                     # optional but helpful
```

Правила:
- Каждый навык находится в отдельной директории в корне tap‑а (по умолчанию `skills/`).
- Имя директории становится slug‑ом установки навыка.
- В каждой директории должен быть `SKILL.md` со стандартным [frontmatter SKILL.md](#skillmd-format) (`name`, `description`, плюс опциональные `metadata.hermes.tags`, `version`, `author`, `platforms`, `metadata.hermes.config`).
- Поддиректории вроде `references/`, `templates/`, `scripts/`, `assets/` скачиваются вместе с `SKILL.md` во время установки.
- Навыки, чьи имена директорий начинаются с `.` или `_`, игнорируются.

Hermes обнаруживает навыки, перечисляя все поддиректории пути tap‑а и проверяя наличие в каждой `SKILL.md`.

#### Минимальный пример tap‑а

```
my-org/hermes-skills
└── skills/
    └── deploy-runbook/
        └── SKILL.md
```

`skills/deploy-runbook/SKILL.md`:

```markdown
---
name: deploy-runbook
description: Our deployment runbook — services, rollback, Slack channels
version: 1.0.0
author: My Org Platform Team
metadata:
  hermes:
    tags: [deployment, runbook, internal]
---

# Deploy Runbook

Step 1: ...
```

После пуша в GitHub любой пользователь Hermes может подписаться и установить:

```bash
hermes skills tap add my-org/hermes-skills
hermes skills search deploy
hermes skills install my-org/hermes-skills/deploy-runbook
```

#### Нестандартные пути

Если навыки находятся не в `skills/` (часто так бывает, когда добавляешь поддерево `skills/` в существующий проект), отредактируй запись tap‑а в `~/.hermes/.hub/taps.json`:

```json
{
  "taps": [
    {"repo": "my-org/platform-docs", "path": "internal/skills/"}
  ]
}
```

CLI `hermes skills tap add` по умолчанию задаёт новым tap‑ам `path: "skills/"`; при необходимости измени файл вручную. `hermes skills tap list` показывает фактический путь для каждого tap‑а.

#### Установка отдельных навыков напрямую (без добавления tap)

Пользователи могут также установить один навык из любого публичного репозитория GitHub без добавления всего репозитория как tap:

```bash
hermes skills install owner/repo/skills/my-workflow
```

Это удобно, когда нужно поделиться одним навыком, не заставляя пользователя подписываться на весь ваш реестр.

#### Уровни доверия для tap‑ов

Новые tap‑ы получают уровень доверия `community` по умолчанию. Навыки, установленные из них, проходят стандартный скан безопасности и показывают панель предупреждения о стороннем источнике при первой установке. Если ваша организация или широко‑доверенный источник должны иметь более высокий уровень доверия, добавьте их репозиторий в `TRUSTED_REPOS` в `tools/skills_hub.py` (требуется PR в ядро Hermes).

#### Управление tap‑ами

```bash
hermes skills tap list                                # show all configured taps
hermes skills tap add myorg/skills-repo               # add (default path: skills/)
hermes skills tap remove myorg/skills-repo            # remove
```

Внутри запущенной сессии:

```
/skills tap list
/skills tap add myorg/skills-repo
/skills tap remove myorg/skills-repo
```

Tap‑ы хранятся в `~/.hermes/.hub/taps.json` (создаётся по требованию).
## Обновления встроенных навыков (`hermes skills reset`)

Hermes поставляется с набором встроенных навыков в `skills/` внутри репозитория. При установке и при каждом `hermes update` выполняется синхронизация, которая копирует их в `~/.hermes/skills/` и записывает манифест в `~/.hermes/skills/.bundled_manifest`, сопоставляющий имя каждого навыка с хешем содержимого на момент синхронизации ( **origin hash**).

При каждой синхронизации Hermes пересчитывает хеш твоей локальной копии и сравнивает его с origin hash:

- **Unchanged** → безопасно подтянуть изменения из upstream, скопировать новую встроенную версию, записать новый origin hash.
- **Changed** → считается **user-modified** и навсегда пропускается, поэтому твои правки никогда не будут перезаписаны.

Защита хороша, но у неё есть один острый край. Если ты отредактировал встроенный навык, а затем захочешь отказаться от изменений и вернуться к встроенной версии, просто скопировав её из `~/.hermes/hermes-agent/skills/`, манифест всё равно хранит *старый* origin hash от последней успешной синхронизации. Содержимое твоего свежего копипаста (текущий хеш встроенного навыка) не совпадёт со старым origin hash, и синхронизация продолжит помечать его как пользовательский.

`hermes skills reset` — это способ выйти из ситуации:

```bash
# Safe: clears the manifest entry for this skill. Your current copy is preserved,
# but the next sync re-baselines against it so future updates work normally.
hermes skills reset google-workspace

# Full restore: also deletes your local copy and re-copies the current bundled
# version. Use this when you want the pristine upstream skill back.
hermes skills reset google-workspace --restore

# Non-interactive (e.g. in scripts or TUI mode) — skip the --restore confirmation.
hermes skills reset google-workspace --restore --yes
```

Ту же команду можно вызвать в чате как slash‑команду:

```text
/skills reset google-workspace
/skills reset google-workspace --restore
```

:::note Profiles
Каждый профиль имеет свой собственный `.bundled_manifest` в своём `HERMES_HOME`, поэтому `hermes -p coder skills reset <name>` затрагивает только этот профиль.
:::

### Slash‑команды (внутри чата)

Все те же команды работают с `/skills`:

```text
/skills browse
/skills search react --source skills-sh
/skills search https://mintlify.com/docs --source well-known
/skills inspect skills-sh/vercel-labs/json-render/json-render-react
/skills install openai/skills/skill-creator --force
/skills check
/skills update
/skills reset google-workspace
/skills list
```

Официальные необязательные навыки по‑прежнему используют идентификаторы вроде `official/security/1password` и `official/migration/openclaw-migration`.