---
sidebar_position: 3
title: "Создание Skills"
description: "Как создать skills для Hermes Agent — формат SKILL.md, рекомендации и публикация"
---

# Создание навыков

Навыки — предпочтительный способ добавить новые возможности в Hermes Agent. Их проще создавать, чем инструменты, они не требуют изменений кода агента и могут быть поделены с сообществом.
## Должно ли это быть Skill или Tool?

Отнеси к **Skill**, когда:
- Возможность может быть выражена инструкциями + shell‑командами + существующими инструментами
- Она оборачивает внешний CLI или API, который агент может вызвать через `terminal` или `web_extract`
- Не требуется пользовательская интеграция на Python или управление API‑ключами, встроенное в агент
- Примеры: поиск в arXiv, рабочие процессы git, управление Docker, обработка PDF, электронная почта через CLI‑инструменты

Отнеси к **Tool**, когда:
- Требуется сквозная интеграция с API‑ключами, процессами аутентификации или многокомпонентной конфигурацией
- Нужна пользовательская логика обработки, которая должна выполняться точно каждый раз
- Обрабатываются бинарные данные, потоковая передача или события в реальном времени
- Примеры: автоматизация браузера, TTS, анализ изображений
## Структура каталога навыков

Встроенные навыки находятся в `skills/`, организованные по категориям. Официальные необязательные навыки используют ту же структуру в `optional-skills/`:

```text
skills/
├── research/
│   └── arxiv/
│       ├── SKILL.md              # Required: main instructions
│       └── scripts/              # Optional: helper scripts
│           └── search_arxiv.py
├── productivity/
│   └── ocr-and-documents/
│       ├── SKILL.md
│       ├── scripts/
│       └── references/
└── ...
```
## Формат SKILL.md

```markdown
---
name: my-skill
description: Brief description (shown in skill search results)
version: 1.0.0
author: Your Name
license: MIT
platforms: [macos, linux]          # Optional — restrict to specific OS platforms
                                   #   Valid: macos, linux, windows
                                   #   Omit to load on all platforms (default)
metadata:
  hermes:
    tags: [Category, Subcategory, Keywords]
    related_skills: [other-skill-name]
    requires_toolsets: [web]            # Optional — only show when these toolsets are active
    requires_tools: [web_search]        # Optional — only show when these tools are available
    fallback_for_toolsets: [browser]    # Optional — hide when these toolsets are active
    fallback_for_tools: [browser_navigate]  # Optional — hide when these tools exist
    config:                              # Optional — config.yaml settings the skill needs
      - key: my.setting
        description: "What this setting controls"
        default: "sensible-default"
        prompt: "Display prompt for setup"
required_environment_variables:          # Optional — env vars the skill needs
  - name: MY_API_KEY
    prompt: "Enter your API key"
    help: "Get one at https://example.com"
    required_for: "API access"
---

# Skill Title

Brief intro.

## When to Use
Trigger conditions — when should the agent load this skill?

## Quick Reference
Table of common commands or API calls.

## Procedure
Step-by-step instructions the agent follows.

## Pitfalls
Known failure modes and how to handle them.

## Verification
How the agent confirms it worked.
```

### Платформенно‑специфичные skill’ы

Skill’ы могут ограничивать себя определёнными операционными системами с помощью поля `platforms`:

```yaml
platforms: [macos]            # macOS only (e.g., iMessage, Apple Reminders)
platforms: [macos, linux]     # macOS and Linux
platforms: [windows]          # Windows only
```

Если поле указано, skill автоматически скрывается из системной подсказки, `skills_list()` и slash‑команд на несовместимых платформах. Если поле опущено или пусто, skill загружается на всех платформах (обратная совместимость).

### Условная активация skill’а

Skill’ы могут объявлять зависимости от конкретных инструментов или наборов инструментов. Это контролирует, будет ли skill отображён в системной подсказке для данной сессии.

```yaml
metadata:
  hermes:
    requires_toolsets: [web]           # Hide if the web toolset is NOT active
    requires_tools: [web_search]       # Hide if web_search tool is NOT available
    fallback_for_toolsets: [browser]   # Hide if the browser toolset IS active
    fallback_for_tools: [browser_navigate]  # Hide if browser_navigate IS available
```

| Поле | Поведение |
|-------|----------|
| `requires_toolsets` | Skill **скрывается**, если **любой** из перечисленных наборов инструментов **не** доступен |
| `requires_tools` | Skill **скрывается**, если **любой** из перечисленных инструментов **не** доступен |
| `fallback_for_toolsets` | Skill **скрывается**, если **любой** из перечисленных наборов инструментов **доступен** |
| `fallback_for_tools` | Skill **скрывается**, если **любой** из перечисленных инструментов **доступен** |

**Сценарий использования `fallback_for_*`:** Создай skill, который служит обходным решением, когда основной инструмент недоступен. Например, skill `duckduckgo-search` с `fallback_for_tools: [web_search]` будет показываться только тогда, когда инструмент веб‑поиска (требующий API‑ключ) не настроен.

**Сценарий использования `requires_*`:** Создай skill, который имеет смысл только при наличии определённых инструментов. Например, skill рабочего процесса веб‑скрейпинга с `requires_toolsets: [web]` не будет загромождать подсказку, когда веб‑инструменты отключены.

### Требования к переменным окружения

Skill’ы могут объявлять переменные окружения, которые им нужны. Когда skill загружается через `skill_view`, его обязательные переменные автоматически регистрируются для проброса в изолированные среды выполнения (терминал, `execute_code`).

```yaml
required_environment_variables:
  - name: TENOR_API_KEY
    prompt: "Tenor API key"               # Shown when prompting user
    help: "Get your key at https://tenor.com"  # Help text or URL
    required_for: "GIF search functionality"   # What needs this var
```

Каждая запись поддерживает:
- `name` (обязательно) — имя переменной окружения
- `prompt` (необязательно) — текст подсказки при запросе значения у пользователя
- `help` (необязательно) — справочный текст или URL для получения значения
- `required_for` (необязательно) — описывает, какая функция требует эту переменную

Пользователи также могут вручную настроить пробрасываемые переменные в `config.yaml`:

```yaml
terminal:
  env_passthrough:
    - MY_CUSTOM_VAR
    - ANOTHER_VAR
```

См. `skills/apple/` для примеров skill’ов, доступных только на macOS.
## Безопасная настройка при загрузке

Используй `required_environment_variables`, когда навыку нужен API‑ключ или токен. Отсутствующие значения **не** скрывают навык из списка доступных. Вместо этого Hermes запрашивает их безопасным способом, когда навык загружается в локальном CLI.

```yaml
required_environment_variables:
  - name: TENOR_API_KEY
    prompt: Tenor API key
    help: Get a key from https://developers.google.com/tenor
    required_for: full functionality
```

Пользователь может пропустить настройку и продолжить загрузку навыка. Hermes никогда не раскрывает модели сырое значение секрета. Сеансы gateway и messaging показывают локальные подсказки по настройке вместо передачи секретов в потоке.

:::tip Sandbox Passthrough
Когда твой навык загружается, любые объявленные `required_environment_variables`, которые заданы, **автоматически передаются** в песочницы `execute_code` и `terminal` — включая удалённые бекенды вроде Docker и Modal. Скрипты твоего навыка могут обращаться к `$TENOR_API_KEY` (или `os.environ["TENOR_API_KEY"]` в Python), не требуя от пользователя дополнительной конфигурации. Подробнее см. [Environment Variable Passthrough](/user-guide/security#environment-variable-passthrough).
:::

Устаревший `prerequisites.env_vars` остаётся поддерживаемым как совместимый алиас.

### Параметры конфигурации (config.yaml)

Навыки могут объявлять несекретные настройки, которые хранятся в `config.yaml` в пространстве имён `skills.config`. В отличие от переменных окружения (секретов, хранящихся в `.env`), параметры конфигурации предназначены для путей, предпочтений и других нечувствительных значений.

```yaml
metadata:
  hermes:
    config:
      - key: myplugin.path
        description: Path to the plugin data directory
        default: "~/myplugin-data"
        prompt: Plugin data directory path
      - key: myplugin.domain
        description: Domain the plugin operates on
        default: ""
        prompt: Plugin domain (e.g., AI/ML research)
```

Каждая запись поддерживает:
- `key` (обязательно) — путь‑точка для настройки (например, `myplugin.path`)
- `description` (обязательно) — объясняет, что контролирует настройка
- `default` (необязательно) — значение по умолчанию, если пользователь его не задаёт
- `prompt` (необязательно) — текст подсказки, показываемый во время `hermes config migrate`; используется `description`, если не задан

**Как это работает:**

1. **Хранение:** Значения записываются в `config.yaml` под `skills.config.<key>`:
   ```yaml
   skills:
     config:
       myplugin:
         path: ~/my-data
   ```

2. **Обнаружение:** `hermes config migrate` сканирует все включённые навыки, ищет незаданные параметры и запрашивает их у пользователя. Параметры также отображаются в `hermes config show` в разделе «Skill Settings».

3. **Внедрение во время выполнения:** При загрузке навыка его конфигурационные значения разрешаются и добавляются к сообщению навыка:
   ```
   [Skill config (from ~/.hermes/config.yaml):
     myplugin.path = /home/user/my-data
   ]
   ```
   Агент видит настроенные значения без необходимости самостоятельно читать `config.yaml`.

4. **Ручная настройка:** Пользователи могут также задавать значения напрямую:
   ```bash
   hermes config set skills.config.myplugin.path ~/my-data
   ```

:::tip Когда использовать что
Используй `required_environment_variables` для API‑ключей, токенов и других **секретов** (хранятся в `~/.hermes/.env`, никогда не показываются модели). Используй `config` для **путей, предпочтений и нечувствительных настроек** (хранятся в `config.yaml`, видимы в `config show`).
:::

### Требования к файлам учётных данных (OAuth‑токены и пр.)

Навыки, использующие OAuth или учётные данные в виде файлов, могут объявлять файлы, которые необходимо монтировать в удалённые песочницы. Это относится к учётным данным, хранящимся **в файлах** (а не в переменных окружения) — обычно OAuth‑токены, создаваемые скриптом настройки.

```yaml
required_credential_files:
  - path: google_token.json
    description: Google OAuth2 token (created by setup script)
  - path: google_client_secret.json
    description: Google OAuth2 client credentials
```

Каждая запись поддерживает:
- `path` (обязательно) — путь к файлу относительно `~/.hermes/`
- `description` (необязательно) — объясняет, что это за файл и как он создаётся

При загрузке Hermes проверяет наличие этих файлов. Отсутствующие файлы вызывают `setup_needed`. Существующие файлы автоматически:
- **Монтируются в контейнеры Docker** как bind‑mount только для чтения
- **Синхронизируются в песочницы Modal** (при создании и перед каждой командой, чтобы OAuth работал в середине сессии)
- Доступны на **локальном** бекенде без какой‑либо специальной обработки

:::tip Когда использовать что
Используй `required_environment_variables` для простых API‑ключей и токенов (строки, хранящиеся в `~/.hermes/.env`). Используй `required_credential_files` для OAuth‑токенов, клиентских секретов, JSON‑файлов сервисных аккаунтов, сертификатов или любых учётных данных, представленных файлом на диске.
:::

См. `skills/productivity/google-workspace/SKILL.md` для полного примера, использующего оба подхода.
## Руководство по навыкам

### Без внешних зависимостей

Отдавай предпочтение стандартной библиотеке Python, `curl` и уже существующим инструментам Hermes (`web_extract`, `terminal`, `read_file`). Если всё‑равно нужна зависимость, задокументируй шаги её установки в навыке.

### Прогрессивное раскрытие

Сначала размещай самый распространённый рабочий процесс. Крайние случаи и продвинутые сценарии помещай в конец. Это снижает расход токенов для типовых задач.

### Включай вспомогательные скрипты

Для парсинга XML/JSON или сложной логики размещай вспомогательные скрипты в `scripts/` — не рассчитывай, что LLM будет писать парсеры «на лету» каждый раз.

### Доставляй медиа как документы (`[[as_document]]`)

Если твой навык генерирует скриншот высокого разрешения, график или любое изображение, где сжатие с потерями ухудшит качество, вставь буквальную директиву `[[as_document]]` где‑нибудь в ответе (обычно в последней строке). Шлюз удалит директиву и доставит каждый извлечённый путь к медиа в этом ответе как вложенный файл‑аттачмент вместо встроенного изображения. См. [Вывод навыка и доставка медиа](../user‑guide/features/skills.md#skill-output-and-media-delivery) для полного описания семантики.

#### Ссылка на включённые скрипты из SKILL.md

При загрузке навыка в сообщении активации указывается абсолютный путь к каталогу навыка как `[Skill directory: /abs/path]` и также подставляются два шаблонных токена в любом месте тела SKILL.md:

| Токен | Заменяется на |
|---|---|
| `${HERMES_SKILL_DIR}` | Абсолютный путь к каталогу навыка |
| `${HERMES_SESSION_ID}` | Идентификатор активной сессии (оставляется без замены, если сессии нет) |

Таким образом, SKILL.md может указать агенту выполнить включённый скрипт напрямую:

```markdown
To analyse the input, run:

    node ${HERMES_SKILL_DIR}/scripts/analyse.js <input>
```

Агент видит подставленный абсолютный путь и вызывает инструмент `terminal` с готовой к запуску командой — без вычисления путей, без дополнительного раунда `skill_view`. Отключить подстановку глобально можно параметром `skills.template_vars: false` в `config.yaml`.

#### Встроенные фрагменты оболочки (по желанию)

Навыки могут также включать встроенные фрагменты оболочки, записанные как ``!`cmd` `` в теле SKILL.md. При включении вывод `stdout` каждого фрагмента инлайн‑вставляется в сообщение перед тем, как агент его прочитает, позволяя навыкам добавлять динамический контекст:

```markdown
Current date: !`date -u +%Y-%m-%d`
Git branch: !`git -C ${HERMES_SKILL_DIR} rev-parse --abbrev-ref HEAD`
```

Это **выключено по умолчанию** — любой фрагмент в SKILL.md выполняется на хосте без подтверждения, поэтому включай его только для надёжных источников навыков:

```yaml
# config.yaml
skills:
  inline_shell: true
  inline_shell_timeout: 10   # seconds per snippet
```

Фрагменты запускаются с каталогом навыка в качестве рабочей директории, а вывод ограничен 4000 символами. Ошибки (тайм‑ауты, ненулевые коды возврата) отображаются как короткий маркер `[inline-shell error: ...]` вместо поломки всего навыка.

### Протестировать

Запусти навык и убедись, что агент правильно следует инструкциям:

```bash
hermes chat --toolsets skills -q "Use the X skill to do Y"
```
## Где должен находиться skill?

Встроенные skill’ы (в `skills/`) поставляются со всеми установками Hermes. Они должны быть **полезны широкому кругу пользователей**:

- Обработка документов, веб‑поиск, типовые рабочие процессы разработки, администрирование систем
- Регулярно используются большим числом людей

Если твой skill официальен и полезен, но не нужен всем (например, интеграция платного сервиса, тяжёлая зависимость), размести его в **`optional-skills/`** — он включён в репозиторий, доступен через `hermes skills browse` (отмечен как «official») и устанавливается с встроенным уровнем доверия.

Если твой skill специализированный, созданный сообществом или нишевый, лучше разместить его в **Skills Hub** — загрузить в реестр и поделиться им через `hermes skills install`.
## Публикация навыков

### В Skills Hub

```bash
hermes skills publish skills/my-skill --to github --repo owner/repo
```

### В пользовательский репозиторий

Add your repo as a tap:

```bash
hermes skills tap add owner/repo
```

Пользователи смогут выполнять поиск и устанавливать пакеты из твоего репозитория.
## Сканирование безопасности

Все навыки, установленные через хаб, проходят проверку сканером безопасности, который ищет:

- шаблоны утечки данных
- попытки внедрения подсказок
- разрушительные команды
- инъекция оболочки

Уровни доверия:
- `builtin` — поставляется с Hermes (всегда доверенный)
- `official` — из `optional-skills/` в репозитории (встроенный уровень доверия, без предупреждения о сторонних источниках)
- `trusted` — из openai/skills, anthropics/skills, huggingface/skills
- `community` — неопасные находки могут быть переопределены с помощью `--force`; вердикты `dangerous` остаются заблокированными

Hermes теперь может потреблять сторонние навыки из нескольких внешних моделей обнаружения:
- прямые идентификаторы GitHub (например `openai/skills/k8s`)
- идентификаторы `skills.sh` (например `skills-sh/vercel-labs/json-render/json-render-react`)
- известные эндпоинты, обслуживаемые из `/.well-known/skills/index.json`

Если ты хочешь, чтобы твои навыки были обнаруживаемыми без установщика, специфичного для GitHub, размести их на известном эндпоинте в дополнение к публикации в репозитории или маркетплейсе.