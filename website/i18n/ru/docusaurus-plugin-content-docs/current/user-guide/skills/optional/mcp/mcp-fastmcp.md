---
title: "FastMCP — создавай, тестируй, проверяй, устанавливай и разворачивай серверы MCP с помощью FastMCP на Python"
sidebar_label: "Fastmcp"
description: "Собирай, тестируй, проверяй, устанавливай и развёртывай серверы MCP с FastMCP на Python"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# FastMCP

Создавай, тестируй, проверяй, устанавливай и развёртывай MCP‑серверы с помощью FastMCP на Python. Используй при создании нового MCP‑сервера, обёртывании API или базы данных в MCP‑инструменты, экспонировании ресурсов или подсказок, а также подготовке FastMCP‑сервера для Claude Code, Cursor или HTTP‑развёртывания.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/mcp/fastmcp` |
| Path | `optional-skills/mcp/fastmcp` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `MCP`, `FastMCP`, `Python`, `Tools`, `Resources`, `Prompts`, `Deployment` |
| Related skills | [`native-mcp`](/docs/user-guide/skills/bundled/mcp/mcp-native-mcp), [`mcporter`](/docs/user-guide/skills/optional/mcp/mcp-mcporter) |

## Reference: full SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции, когда навык включён.
:::

# FastMCP

Создавай MCP‑серверы на Python с помощью FastMCP, проверяй их локально, устанавливай в MCP‑клиенты и развёртывай как HTTP‑конечные точки.

## When to Use

Используй этот навык, когда задача состоит в:

- создании нового MCP‑сервера на Python
- обёртывании API, базы данных, CLI или файлового рабочего процесса в MCP‑инструменты
- экспонировании ресурсов или подсказок в дополнение к инструментам
- смоук‑тестировании сервера с помощью FastMCP CLI перед подключением к Hermes или другому клиенту
- установке сервера в Claude Code, Claude Desktop, Cursor или аналогичный MCP‑клиент
- подготовке репозитория FastMCP‑сервера для HTTP‑развёртывания

Используй `native-mcp`, когда сервер уже существует и нужно лишь подключить его к Hermes. Используй `mcporter`, когда цель — ad‑hoc CLI‑доступ к существующему MCP‑серверу вместо его создания.

## Prerequisites

Сначала установи FastMCP в рабочей среде:

```bash
pip install fastmcp
fastmcp version
```

Для шаблона API установи `httpx`, если он ещё не установлен:

```bash
pip install httpx
```

## Included Files

### Templates

- `templates/api_wrapper.py` — обёртка REST API с поддержкой заголовка авторизации
- `templates/database_server.py` — сервер запросов SQLite только для чтения
- `templates/file_processor.py` — сервер инспекции и поиска по текстовым файлам

### Scripts

- `scripts/scaffold_fastmcp.py` — копирует стартовый шаблон и заменяет плейсхолдер имени сервера

### References

- `references/fastmcp-cli.md` — рабочий процесс FastMCP CLI, цели установки и проверки развёртывания

## Workflow

### 1. Pick the Smallest Viable Server Shape

Сначала выбери самую узкую полезную поверхность:

- API wrapper: начни с 1‑3 ценных эндпоинтов, а не со всего API
- database server: открой только чтение и ограниченный путь запросов
- file processor: открой детерминированные операции с явными аргументами пути
- prompts/resources: добавляй только когда клиенту нужны переиспользуемые шаблоны подсказок или обнаруживаемые документы

Отдавай предпочтение тонкому серверу с хорошими именами, docstring‑ами и схемами вместо большого сервера с размытыми инструментами.

### 2. Scaffold from a Template

Скопируй шаблон напрямую или используй помощник scaffold:

```bash
python ~/.hermes/skills/mcp/fastmcp/scripts/scaffold_fastmcp.py \
  --template api_wrapper \
  --name "Acme API" \
  --output ./acme_server.py
```

Доступные шаблоны:

```bash
python ~/.hermes/skills/mcp/fastmcp/scripts/scaffold_fastmcp.py --list
```

Если копируешь вручную, замени `__SERVER_NAME__` на реальное имя сервера.

### 3. Implement Tools First

Сначала реализуй функции с `@mcp.tool`, а потом добавляй ресурсы или подсказки.

Правила проектирования инструмента:

- Давай каждому инструменту конкретное глагольное название
- Пиши docstring‑и как описания инструмента для пользователя
- Делай параметры явными и типизированными
- По возможности возвращай структурированные JSON‑безопасные данные
- Раннее валидируй небезопасные входные данные
- По умолчанию предпочитай только‑чтение в первых версиях

Хорошие примеры инструментов:

- `get_customer`
- `search_tickets`
- `describe_table`
- `summarize_text_file`

Слабые примеры инструментов:

- `run`
- `process`
- `do_thing`

### 4. Add Resources and Prompts Only When They Help

Добавляй `@mcp.resource`, когда клиенту выгодно получать стабильный только‑чтение контент, такой как схемы, документы политики или сгенерированные отчёты.

Добавляй `@mcp.prompt`, когда сервер должен предоставлять переиспользуемый шаблон подсказки для известного рабочего процесса.

Не превращай каждый документ в подсказку. Предпочитай:

- инструменты для действий
- ресурсы для получения данных/документов
- подсказки для переиспользуемых инструкций LLM

### 5. Test the Server Before Integrating It Anywhere

Используй FastMCP CLI для локальной проверки:

```bash
fastmcp inspect acme_server.py:mcp
fastmcp list acme_server.py --json
fastmcp call acme_server.py search_resources query=router limit=5 --json
```

Для быстрого итеративного отладки запусти сервер локально:

```bash
fastmcp run acme_server.py:mcp
```

Чтобы протестировать HTTP‑транспорт локально:

```bash
fastmcp run acme_server.py:mcp --transport http --host 127.0.0.1 --port 8000
fastmcp list http://127.0.0.1:8000/mcp --json
fastmcp call http://127.0.0.1:8000/mcp search_resources query=router --json
```

Всегда выполняй хотя бы один реальный `fastmcp call` для каждого нового инструмента, прежде чем заявлять, что сервер работает.

### 6. Install into a Client When Local Validation Passes

FastMCP может зарегистрировать сервер в поддерживаемых MCP‑клиентах:

```bash
fastmcp install claude-code acme_server.py
fastmcp install claude-desktop acme_server.py
fastmcp install cursor acme_server.py -e .
```

Используй `fastmcp discover` для просмотра именованных MCP‑серверов, уже сконфигурированных на машине.

Когда цель — интеграция с Hermes, либо:

- сконфигурировать сервер в `~/.hermes/config.yaml` с помощью навыка `native-mcp`, либо
- продолжать использовать команды FastMCP CLI во время разработки, пока интерфейс не стабилизируется

### 7. Deploy After the Local Contract Is Stable

Для управляемого хостинга путь FastMCP описан в Prefect Horizon. Перед развёртыванием:

```bash
fastmcp inspect acme_server.py:mcp
```

Убедись, что репозиторий содержит:

- Python‑файл с объектом FastMCP‑сервера
- `requirements.txt` или `pyproject.toml`
- любую документацию переменных окружения, необходимую для развёртывания

Для общего HTTP‑хостинга сначала проверь HTTP‑транспорт локально, затем развёртывай на любой Python‑совместимой платформе, способной открыть порт сервера.

## Common Patterns

### API Wrapper Pattern

Используй, когда нужно экспонировать REST или HTTP API как MCP‑инструменты.

Рекомендуемый первый срез:

- один путь чтения
- один путь списка/поиска
- опциональная проверка работоспособности

Замечания по реализации:

- хранить авторизацию в переменных окружения, а не в коде
- централизовать логику запросов в одном помощнике
- возвращать ошибки API с лаконичным контекстом
- нормализовать несогласованные входные данные перед возвратом

Начни с `templates/api_wrapper.py`.

### Database Pattern

Используй, когда нужно предоставить безопасные возможности запросов и инспекции.

Рекомендуованный первый срез:

- `list_tables`
- `describe_table`
- один ограниченный инструмент чтения запросов

Замечания по реализации:

- по умолчанию только‑чтение к БД
- отклонять не‑`SELECT` SQL в ранних версиях
- ограничивать количество строк
- возвращать строки вместе с названиями колонок

Начни с `templates/database_server.py`.

### File Processor Pattern

Используй, когда сервер должен инспектировать или трансформировать файлы по запросу.

Рекомендуемый первый срез:

- суммировать содержимое файла
- искать внутри файлов
- извлекать детерминированные метаданные

Замечания по реализации:

- принимать явные пути к файлам
- проверять отсутствие файлов и ошибки кодировки
- ограничивать превью и количество результатов
- избегать вызовов оболочки, если только не требуется конкретный внешний инструмент

Начни с `templates/file_processor.py`.

## Quality Bar

Перед передачей FastMCP‑сервера убедись, что выполнено всё ниже:

- сервер импортируется без ошибок
- `fastmcp inspect <file.py:mcp>` проходит успешно
- `fastmcp list <server spec> --json` проходит успешно
- каждый новый инструмент имеет хотя бы один реальный `fastmcp call`
- переменные окружения задокументированы
- поверхность инструмента достаточно мала, чтобы понять её без догадок

## Troubleshooting

### FastMCP command missing

Установи пакет в активной среде:

```bash
pip install fastmcp
fastmcp version
```

### `fastmcp inspect` fails

Проверь, что:

- файл импортируется без побочных эффектов, вызывающих падения
- экземпляр FastMCP назван правильно в `<file.py:object>`
- опциональные зависимости из шаблона установлены

### Tool works in Python but not through CLI

Выполни:

```bash
fastmcp list server.py --json
fastmcp call server.py your_tool_name --json
```

Обычно это выявляет несоответствия имён, отсутствие обязательных аргументов или не сериализуемые возвращаемые значения.

### Hermes cannot see the deployed server

Часть построения сервера может быть корректной, а конфигурация Hermes — нет. Загрузите навык `native-mcp` и сконфигурируйте сервер в `~/.hermes/config.yaml`, затем перезапустите Hermes.

## References

Для деталей CLI, целей установки и проверок развёртывания читай `references/fastmcp-cli.md`.