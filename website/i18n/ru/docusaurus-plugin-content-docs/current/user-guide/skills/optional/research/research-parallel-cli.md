---
title: "Параллельный CLI"
sidebar_label: "Parallel Cli"
description: "Опциональный vendor skill для Parallel CLI — агентный веб-поиск, извлечение, глубокое исследование, обогащение, FindAll и мониторинг"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Parallel Cli

Опциональный навык поставщика для Parallel CLI — агентно‑нативный веб‑поиск, извлечение, глубокий анализ, обогащение, FindAll и мониторинг. Предпочитай вывод в формате JSON и неинтерактивные потоки.
## Метаданные навыка

| | |
|---|---|
| Источник | Опционально — установить с помощью `hermes skills install official/research/parallel-cli` |
| Путь | `optional-skills/research/parallel-cli` |
| Версия | `1.1.0` |
| Автор | Hermes Agent |
| Лицензия | MIT |
| Платформы | linux, macos, windows |
| Теги | `Research`, `Web`, `Search`, `Deep-Research`, `Enrichment`, `CLI` |
| Связанные навыки | [`duckduckgo-search`](/docs/user-guide/skills/optional/research/research-duckduckgo-search), [`mcporter`](/docs/user-guide/skills/optional/mcp/mcp-mcporter) |
:::info
Следующий текст — полное определение навыка, которое Hermes загружает при его срабатывании. Это то, что агент видит как инструкции, когда навык активен.
:::

# Parallel CLI

Используй `parallel-cli`, когда пользователь явно хочет Parallel, или когда терминальный‑нативный рабочий процесс получит выгоду от специфического стека Parallel для веб‑поиска, извлечения, глубоких исследований, обогащения, обнаружения сущностей или мониторинга.

Это необязательный сторонний рабочий процесс, а не базовая возможность Hermes.

Важные ожидания:
- Parallel — платный сервис с бесплатным уровнем, а не полностью бесплатный локальный инструмент.
- Он пересекается с нативными `web_search` / `web_extract` Hermes, поэтому не следует использовать его по умолчанию для обычных запросов.
- Предпочитай этот навык, когда пользователь упоминает Parallel конкретно или нуждается в возможностях, таких как обогащение Parallel, FindAll или рабочие процессы мониторинга.

`parallel-cli` разработан для агентов:
- Вывод JSON через `--json`
- Неинтерактивное выполнение команд
- Асинхронные длительные задачи с `--no-wait`, `status` и `poll`
- Цепочка контекста с помощью `--previous-interaction-id`
- Поиск, извлечение, исследование, обогащение, обнаружение сущностей и мониторинг в одном CLI
## Когда использовать

Рекомендуй этот **skill**, когда:

- Пользователь явно упоминает Parallel или `parallel-cli`
- Задача требует более сложных рабочих процессов, чем простой одноразовый поиск/извлечение
- Нужны асинхронные задачи глубоких исследований, которые можно запустить и позже опросить
- Требуется структурированное обогащение, обнаружение сущностей FindAll или мониторинг

Отдавай предпочтение нативному Hermes `web_search` / `web_extract` для быстрых одноразовых запросов, когда Parallel не запрашивается явно.
## Установка

Попробуй наименее навязчивый способ установки, доступный для твоей среды.

### Homebrew

```bash
brew install parallel-web/tap/parallel-cli
```

### npm

```bash
npm install -g parallel-web-cli
```

### Python package

```bash
pip install "parallel-web-tools[cli]"
```

### Standalone installer

```bash
curl -fsSL https://parallel.ai/install.sh | bash
```

Если ты хочешь изолированную установку Python, `pipx` тоже может подойти:

```bash
pipx install "parallel-web-tools[cli]"
pipx ensurepath
```
## Аутентификация

Interactive login:

```bash
parallel-cli login
```

Headless / SSH / CI:

```bash
parallel-cli login --device
```

API key environment variable:

```bash
export PARALLEL_API_KEY="***"
```

Verify current auth status:

```bash
parallel-cli auth
```

Если аутентификация требует взаимодействия с браузером, запусти с `pty=true`.
## Основной набор правил

1. Всегда предпочитай `--json`, когда нужен машинно‑читаемый вывод.
2. Предпочитай явные аргументы и неинтерактивные режимы.
3. Для длительных задач используй `--no-wait`, а затем `status` / `poll`.
4. Цитируй только URL‑адреса, возвращённые выводом CLI.
5. Сохраняй большие JSON‑выводы во временный файл, если ожидаются последующие вопросы.
6. Используй фоновые процессы только для действительно длительных рабочих процессов; иначе запускай их в переднем плане.
7. Предпочитай нативные инструменты Hermes, если только пользователь явно не запросил Parallel или не требуются рабочие процессы, доступные только в Parallel.
## Быстрая справка

<!-- ascii-guard-ignore -->
```text
parallel-cli
├── auth
├── login
├── logout
├── search
├── extract / fetch
├── research run|status|poll|processors
├── enrich run|status|poll|plan|suggest|deploy
├── findall run|ingest|status|poll|result|enrich|extend|schema|cancel
└── monitor create|list|get|update|delete|events|event-group|simulate
```
<!-- ascii-guard-ignore-end -->
## Общие флаги и шаблоны

Полезные флаги:
- `--json` — для структурированного вывода
- `--no-wait` — для асинхронных заданий
- `--previous-interaction-id <id>` — для последующих задач, использующих предыдущий контекст
- `--max-results <n>` — для указания количества результатов поиска
- `--mode one-shot|agentic` — для поведения поиска
- `--include-domains domain1.com,domain2.com`
- `--exclude-domains domain1.com,domain2.com`
- `--after-date YYYY-MM-DD`

Чтение из `stdin`, когда это удобно:

```bash
echo "What is the latest funding for Anthropic?" | parallel-cli search - --json
echo "Research question" | parallel-cli research run - --json
```
## Поиск

Используется для текущих веб‑запросов со структурированными результатами.

```bash
parallel-cli search "What is Anthropic's latest AI model?" --json
parallel-cli search "SEC filings for Apple" --include-domains sec.gov --json
parallel-cli search "bitcoin price" --after-date 2026-01-01 --max-results 10 --json
parallel-cli search "latest browser benchmarks" --mode one-shot --json
parallel-cli search "AI coding agent enterprise reviews" --mode agentic --json
```

Полезные параметры:
- `--include-domains` — для ограничения доверенных источников
- `--exclude-domains` — для удаления шумных доменов
- `--after-date` — для фильтрации по дате
- `--max-results` — когда требуется более широкое покрытие

Если ожидаются последующие вопросы, сохрани вывод:

```bash
parallel-cli search "latest React 19 changes" --json -o /tmp/react-19-search.json
```

При суммировании результатов:
- начинай с ответа
- указывай даты, имена и конкретные факты
- цитируй только полученные источники
- не выдумывай URL‑адреса или названия источников
## Извлечение

Используй для получения чистого содержимого или markdown из URL.

```bash
parallel-cli extract https://example.com --json
parallel-cli extract https://company.com --objective "Find pricing info" --json
parallel-cli extract https://example.com --full-content --json
parallel-cli fetch https://example.com --json
```

Используй `--objective`, когда страница обширна и нужен только один фрагмент информации.
## Глубокое исследование

Используется для более сложных многошаговых исследовательских задач, которые могут занять время.

Общие уровни процессоров:
- `lite` / `base` — для более быстрых, дешевых проходов
- `core` / `pro` — для более тщательного синтеза
- `ultra` — для самых тяжёлых исследовательских заданий

### Синхронный

```bash
parallel-cli research run \
  "Compare the leading AI coding agents by pricing, model support, and enterprise controls" \
  --processor core \
  --json
```

### Асинхронный запуск + опрос

```bash
parallel-cli research run \
  "Compare the leading AI coding agents by pricing, model support, and enterprise controls" \
  --processor ultra \
  --no-wait \
  --json

parallel-cli research status trun_xxx --json
parallel-cli research poll trun_xxx --json
parallel-cli research processors --json
```

### Цепочка контекста / последующие запросы

```bash
parallel-cli research run "What are the top AI coding agents?" --json
parallel-cli research run \
  "What enterprise controls does the top-ranked one offer?" \
  --previous-interaction-id trun_xxx \
  --json
```

Рекомендуемый рабочий процесс Hermes:
1. запусти с `--no-wait --json`
2. получи возвращённый идентификатор run/task
3. если пользователь хочет продолжить другую работу, продолжай работать
4. позже вызови `status` или `poll`
5. составь итоговый отчёт с цитатами из полученных источников
## Обогащение

Используется, когда у пользователя есть CSV/JSON/табличные входные данные и нужны дополнительные столбцы, полученные в результате веб‑поиска.

### Предложить столбцы

```bash
parallel-cli enrich suggest "Find the CEO and annual revenue" --json
```

### Запланировать конфигурацию

```bash
parallel-cli enrich plan -o config.yaml
```

### Встроенные данные

```bash
parallel-cli enrich run \
  --data '[{"company": "Anthropic"}, {"company": "Mistral"}]' \
  --intent "Find headquarters and employee count" \
  --json
```

### Запуск из файла в неинтерактивном режиме

```bash
parallel-cli enrich run \
  --source-type csv \
  --source companies.csv \
  --target enriched.csv \
  --source-columns '[{"name": "company", "description": "Company name"}]' \
  --intent "Find the CEO and annual revenue"
```

### Запуск с YAML‑конфигурацией

```bash
parallel-cli enrich run config.yaml
```

### Статус / опрос

```bash
parallel-cli enrich status <task_group_id> --json
parallel-cli enrich poll <task_group_id> --json
```

Используй явные JSON‑массивы для определения столбцов при работе в неинтерактивном режиме.
Проверь выходной файл перед тем, как сообщать об успешном завершении.
## FindAll

Используется для веб‑масштабного обнаружения сущностей, когда пользователь хочет получить обнаруженный набор данных, а не короткий ответ.

```bash
parallel-cli findall run "Find AI coding agent startups with enterprise offerings" --json
parallel-cli findall run "AI startups in healthcare" -n 25 --json
parallel-cli findall status <run_id> --json
parallel-cli findall poll <run_id> --json
parallel-cli findall result <run_id> --json
parallel-cli findall schema <run_id> --json
```

Это более подходящий вариант, чем обычный поиск, когда пользователь хочет получить набор обнаруженных сущностей, который позже можно просматривать, фильтровать или обогащать.
## Монитор

Используй для непрерывного обнаружения изменений во времени.

```bash
parallel-cli monitor list --json
parallel-cli monitor get <monitor_id> --json
parallel-cli monitor events <monitor_id> --json
parallel-cli monitor delete <monitor_id> --json
```

Создание обычно является чувствительной частью, потому что частота и доставка имеют значение:

```bash
parallel-cli monitor create --help
```

Используй это, когда пользователь хочет периодическое отслеживание страницы или источника, а не однократное получение.
## Рекомендованные шаблоны использования Hermes

### Быстрый ответ с цитатами
1. Выполни `parallel-cli search … --json`
2. Разбери заголовки, URL, даты, выдержки
3. Сформируй сводку с встроенными цитатами только из возвращённых URL

### Исследование URL
1. Выполни `parallel-cli extract URL --json`
2. При необходимости запусти снова с `--objective` или `--full-content`
3. Цитируй или резюмируй извлечённый markdown

### Длинный исследовательский процесс
1. Выполни `parallel-cli research run … --no-wait --json`
2. Сохрани полученный ID
3. Продолжай другую работу или периодически проверяй статус
4. Сформируй итоговый отчёт с цитатами

### Структурированный процесс обогащения
1. Проверь входной файл и его столбцы
2. Используй `enrich suggest` или явно укажи обогащённые столбцы
3. Выполни `enrich run`
4. При необходимости опроси статус завершения
5. Проверь выходной файл перед сообщением об успехе
## Обработка ошибок и коды выхода

CLI описывает следующие коды выхода:
- `0` — успех
- `2` — неверный ввод
- `3` — ошибка аутентификации
- `4` — ошибка API
- `5` — тайм‑аут

Если ты сталкиваешься с ошибками аутентификации:
1. проверь `parallel-cli auth`
2. убедись, что задан `PARALLEL_API_KEY`, либо запусти `parallel-cli login` / `parallel-cli login --device`
3. проверь, что `parallel-cli` находится в `PATH`
## Обслуживание

Проверь текущий статус аутентификации/установки:

```bash
parallel-cli auth
parallel-cli --help
```

Команды обновления:

```bash
parallel-cli update
pip install --upgrade parallel-web-tools
parallel-cli config auto-update-check off
```
## Подводные камни

- Не опускай `--json`, если пользователь явно не запросил вывод в человекочитаемом формате.
- Не цитируй источники, которых нет в выводе CLI.
- `login` может требовать взаимодействия PTY/браузера.
- Предпочитай выполнение в переднем плане для коротких задач; не злоупотребляй фоновыми процессами.
- Для больших наборов результатов сохраняй JSON в `/tmp/*.json`, вместо того чтобы помещать всё в контекст.
- Не выбирай автоматически режим Parallel, если нативных инструментов Hermes уже достаточно.
- Помни, что это рабочий процесс поставщика, который обычно требует аутентификации учётной записи и платного использования сверх бесплатного уровня.