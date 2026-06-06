---
sidebar_position: 5
title: "Каталог встроенных Skills"
description: "Каталог встроенных skills, поставляемых с Hermes Agent"
---

# Каталог встроенных skill

Hermes поставляется с большой встроенной библиотекой skill, копируемой в `~/.hermes/skills/` при установке. Каждый skill ниже ссылается на отдельную страницу с полным определением, настройкой и использованием.

Hermes также синхронизирует встроенные skill при выполнении `hermes update`, но манифест синхронизации учитывает локальные удаления и пользовательские правки. Если skill, указанный здесь, отсутствует в дереве `~/.hermes/skills/` вашего профиля, он всё равно поставляется с Hermes; восстанови его с помощью `hermes skills reset <name> --restore`.

Если skill отсутствует в этом списке, но присутствует в репозитории, каталог регенерируется скриптом `website/scripts/generate-skill-docs.py`.
## apple

| Skill | Описание | Путь |
|-------|----------|------|
| [`apple-notes`](/docs/user-guide/skills/bundled/apple/apple-apple-notes) | Управляй Apple Notes через memo CLI: создание, поиск, редактирование. | `apple/apple-notes` |
| [`apple-reminders`](/docs/user-guide/skills/bundled/apple/apple-apple-reminders) | Apple Reminders через remindctl: добавление, просмотр списка, завершение. | `apple/apple-reminders` |
| [`findmy`](/docs/user-guide/skills/bundled/apple/apple-findmy) | Отслеживание устройств Apple и AirTags через приложение FindMy.app в macOS. | `apple/findmy` |
| [`imessage`](/docs/user-guide/skills/bundled/apple/apple-imessage) | Отправка и получение iMessage/SMS через CLI‑утилиту imsg в macOS. | `apple/imessage` |
| [`macos-computer-use`](/docs/user-guide/skills/bundled/apple/apple-macos-computer-use) | Управляй рабочим столом macOS в фоновом режиме — скриншоты, мышь, клавиатура, прокрутка, перетаскивание — не захватывая курсор, фокус клавиатуры и Space пользователя. Работает с любой моделью, поддерживающей инструменты. Загружай этот навык, когда используется инструмент `computer_use`… | `apple/macos-computer-use` |
## автономные AI‑агенты

| Skill | Description | Path |
|-------|-------------|------|
| [`claude-code`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-claude-code) | Делегировать кодирование Claude Code CLI (фичи, PR‑ы). | `autonomous-ai-agents/claude-code` |
| [`codex`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-codex) | Делегировать кодирование OpenAI Codex CLI (фичи, PR‑ы). | `autonomous-ai-agents/codex` |
| [`hermes-agent`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-hermes-agent) | Настраивать, расширять или вносить вклад в Hermes Agent. | `autonomous-ai-agents/hermes-agent` |
| [`kanban-codex-lane`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-kanban-codex-lane) | Использовать, когда worker Hermes Kanban хочет запустить Codex CLI как изолированную lane реализации, при этом Hermes сохраняет владение жизненным циклом задачи, согласованием, тестированием и передачей. | `autonomous-ai-agents/kanban-codex-lane` |
| [`opencode`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-opencode) | Делегировать кодирование OpenCode CLI (фичи, обзор PR). | `autonomous-ai-agents/opencode` |
## креатив

| Skill | Description | Path |
|-------|-------------|------|
| [`architecture-diagram`](/docs/user-guide/skills/bundled/creative/creative-architecture-diagram) | SVG‑диаграммы архитектуры, облака и инфраструктуры в тёмной теме, экспортируемые в HTML. | `creative/architecture-diagram` |
| [`ascii-art`](/docs/user-guide/skills/bundled/creative/creative-ascii-art) | ASCII‑арт: pyfiglet, cowsay, boxes, преобразование изображения в ASCII. | `creative/ascii-art` |
| [`ascii-video`](/docs/user-guide/skills/bundled/creative/creative-ascii-video) | ASCII‑видео: конвертация видео/аудио в цветное ASCII MP4/GIF. | `creative/ascii-video` |
| [`baoyu-article-illustrator`](/docs/user-guide/skills/bundled/creative/creative-baoyu-article-illustrator) | Иллюстрации к статьям: согласованность типа × стиля × палитры. | `creative/baoyu-article-illustrator` |
| [`baoyu-comic`](/docs/user-guide/skills/bundled/creative/creative-baoyu-comic) | Комиксы‑знания (知识漫画): обучающие, биографические, учебные. | `creative/baoyu-comic` |
| [`baoyu-infographic`](/docs/user-guide/skills/bundled/creative/creative-baoyu-infographic) | Инфографика: 21 макет × 21 стиль (信息图, 可视化). | `creative/baoyu-infographic` |
| [`claude-design`](/docs/user-guide/skills/bundled/creative/creative-claude-design) | Создание разовых HTML‑артефактов (лендинг, презентация, прототип). | `creative/claude-design` |
| [`comfyui`](/docs/user-guide/skills/bundled/creative/creative-comfyui) | Генерация изображений, видео и аудио с помощью ComfyUI — установка, запуск, управление узлами/моделями, выполнение рабочих процессов с внедрением параметров. Использует официальный comfy‑cli для жизненного цикла и прямой REST/WebSocket API для исполнения. | `creative/comfyui` |
| [`ideation`](/docs/user-guide/skills/bundled/creative/creative-creative-ideation) | Генерация идей проектов через творческие ограничения. | `creative/creative-ideation` |
| [`design-md`](/docs/user-guide/skills/bundled/creative/creative-design-md) | Создание, валидация и экспорт файлов спецификации токенов Google DESIGN.md. | `creative/design-md` |
| [`excalidraw`](/docs/user-guide/skills/bundled/creative/creative-excalidraw) | Рисованные от руки JSON‑диаграммы Excalidraw (архитектура, поток, последовательность). | `creative/excalidraw` |
| [`humanizer`](/docs/user-guide/skills/bundled/creative/creative-humanizer) | Оживление текста: удаление AI‑шаблонов и добавление реального голоса. | `creative/humanizer` |
| [`manim-video`](/docs/user-guide/skills/bundled/creative/creative-manim-video) | Анимации Manim CE: математические и алгоритмические видео в стиле 3Blue1Brown. | `creative/manim-video` |
| [`p5js`](/docs/user-guide/skills/bundled/creative/creative-p5js) | Скetch‑проекты p5.js: генеративное искусство, шейдеры, интерактивное 3D. | `creative/p5js` |
| [`pixel-art`](/docs/user-guide/skills/bundled/creative/creative-pixel-art) | Пиксель‑арт с палитрами эпох (NES, Game Boy, PICO‑8). | `creative/pixel-art` |
| [`popular-web-designs`](/docs/user-guide/skills/bundled/creative/creative-popular-web-designs) | 54 реальных дизайн‑системы (Stripe, Linear, Vercel) в виде HTML/CSS. | `creative/popular-web-designs` |
| [`pretext`](/docs/user-guide/skills/bundled/creative/creative-pretext) | Используется для создания креативных браузерных демо с @chenglou/pretext — разметка текста без DOM для ASCII‑арта, типографского потока вокруг препятствий, игр с текстом‑геометрией, кинетической типографии и генеративного искусства на основе текста. Генерирует однофайловый HTML… | `creative/pretext` |
| [`sketch`](/docs/user-guide/skills/bundled/creative/creative-sketch) | Быстрые HTML‑макеты: 2‑3 варианта дизайна для сравнения. | `creative/sketch` |
| [`songwriting-and-ai-music`](/docs/user-guide/skills/bundled/creative/creative-songwriting-and-ai-music) | Техника написания песен и подсказки для музыки Suno AI. | `creative/songwriting-and-ai-music` |
| [`touchdesigner-mcp`](/docs/user-guide/skills/bundled/creative/creative-touchdesigner-mcp) | Управление запущенным экземпляром TouchDesigner через twozero MCP — создание операторов, установка параметров, соединение узлов, выполнение Python, построение визуалов в реальном времени. 36 нативных инструментов. | `creative/touchdesigner-mcp` |
## data-science

| Навык | Описание | Путь |
|-------|----------|------|
| [`jupyter-live-kernel`](/docs/user-guide/skills/bundled/data-science/data-science-jupyter-live-kernel) | Итеративный Python через живое ядро Jupyter (hamelnb). | `data-science/jupyter-live-kernel` |
## devops

| Навык | Описание | Путь |
|-------|-------------|------|
| [`kanban-orchestrator`](/docs/user-guide/skills/bundled/devops/devops-kanban-orchestrator) | Плейбук декомпозиции + правила против искушения для профиля оркестратора, направляющего работу через Kanban. Правило «не делай работу сам» и базовый жизненный цикл автоматически внедряются в system prompt каждого kanban‑worker; этот навык… | `devops/kanban-orchestrator` |
| [`kanban-worker`](/docs/user-guide/skills/bundled/devops/devops-kanban-worker) | Подводные камни, примеры и граничные случаи для Hermes Kanban workers. Сам жизненный цикл автоматически внедряется в system prompt каждого worker как KANBAN_GUIDANCE (из `agent/prompt_builder.py`); этот навык загружается, когда нужен более глубокий дет… | `devops/kanban-worker` |
| [`webhook-subscriptions`](/docs/user-guide/skills/bundled/devops/devops-webhook-subscriptions) | Подписки на вебхуки: запуск агента по событию. | `devops/webhook-subscriptions` |
## dogfood

| Навык | Описание | Путь |
|-------|----------|------|
| [`dogfood`](/docs/user-guide/skills/bundled/dogfood/dogfood-dogfood) | Исследовательское тестирование веб‑приложений: поиск багов, доказательств, отчётов. | `dogfood` |
## email

| Навык | Описание | Путь |
|-------|-------------|------|
| [`himalaya`](/docs/user-guide/skills/bundled/email/email-himalaya) | Himalaya CLI: работа с email по IMAP/SMTP из терминала. | `email/himalaya` |
## игры

| Навык | Описание | Путь |
|-------|----------|------|
| [`minecraft-modpack-server`](/docs/user-guide/skills/bundled/gaming/gaming-minecraft-modpack-server) | Размещение модифицированных серверов Minecraft (CurseForge, Modrinth). | `gaming/minecraft-modpack-server` |
| [`pokemon-player`](/docs/user-guide/skills/bundled/gaming/gaming-pokemon-player) | Играть в Pokemon через безголовый эмулятор и чтение оперативной памяти. | `gaming/pokemon-player` |
## github

| Skill | Description | Path |
|-------|-------------|------|
| [`codebase-inspection`](/docs/user-guide/skills/bundled/github/github-codebase-inspection) | Анализировать кодовые базы с помощью pygount: строки кода, языки, соотношения. | `github/codebase-inspection` |
| [`github-auth`](/docs/user-guide/skills/bundled/github/github-github-auth) | Настройка аутентификации GitHub: HTTPS‑токены, SSH‑ключи, вход через CLI `gh`. | `github/github-auth` |
| [`github-code-review`](/docs/user-guide/skills/bundled/github/github-github-code-review) | Обзор pull‑request‑ов: диффы, встроенные комментарии через `gh` или REST. | `github/github-code-review` |
| [`github-issues`](/docs/user-guide/skills/bundled/github/github-github-issues) | Создание, сортировка, маркировка, назначение GitHub‑issues через `gh` или REST. | `github/github-issues` |
| [`github-pr-workflow`](/docs/user-guide/skills/bundled/github/github-github-pr-workflow) | Жизненный цикл PR в GitHub: ветка, коммит, открытие, CI, слияние. | `github/github-pr-workflow` |
| [`github-repo-management`](/docs/user-guide/skills/bundled/github/github-github-repo-management) | Клонирование/создание/форк репозиториев; управление удалёнными, релизами. | `github/github-repo-management` |
## mcp

| Навык | Описание | Путь |
|-------|----------|------|
| [`native-mcp`](/docs/user-guide/skills/bundled/mcp/mcp-native-mcp) | MCP‑клиент: подключать к серверам, регистрировать инструменты (stdio/HTTP). | `mcp/native-mcp` |
## Media

| Skill | Description | Path |
|-------|-------------|------|
| [`gif-search`](/docs/user-guide/skills/bundled/media/media-gif-search) | Поиск/скачивание GIF‑изображений из Tenor с помощью `curl` + `jq`. | `media/gif-search` |
| [`heartmula`](/docs/user-guide/skills/bundled/media/media-heartmula) | HeartMuLa: генерация песен в стиле Suno из текста и тегов. | `media/heartmula` |
| [`songsee`](/docs/user-guide/skills/bundled/media/media-songsee) | Спектрограммы и признаки аудио (mel, chroma, MFCC) через CLI. | `media/songsee` |
| [`spotify`](/docs/user-guide/skills/bundled/media/media-spotify) | Spotify: воспроизведение, поиск, очередь, управление плейлистами и устройствами. | `media/spotify` |
| [`youtube-content`](/docs/user-guide/skills/bundled/media/media-youtube-content) | Транскрипты YouTube в резюме, ветки, блоги. | `media/youtube-content` |
## mlops

| Навык | Описание | Путь |
|-------|----------|------|
| [`audiocraft-audio-generation`](/docs/user-guide/skills/bundled/mlops/mlops-models-audiocraft) | AudioCraft: MusicGen — преобразование текста в музыку, AudioGen — преобразование текста в звук. | `mlops/models/audiocraft` |
| [`dspy`](/docs/user-guide/skills/bundled/mlops/mlops-research-dspy) | DSPy: декларативные программы LM, автоматическая оптимизация подсказок, RAG. | `mlops/research/dspy` |
| [`huggingface-hub`](/docs/user-guide/skills/bundled/mlops/mlops-huggingface-hub) | HuggingFace hf CLI: поиск/загрузка/отправка моделей, наборов данных. | `mlops/huggingface-hub` |
| [`llama-cpp`](/docs/user-guide/skills/bundled/mlops/mlops-inference-llama-cpp) | llama.cpp — локальная инференция GGUF + обнаружение моделей в HF Hub. | `mlops/inference/llama-cpp` |
| [`evaluating-llms-harness`](/docs/user-guide/skills/bundled/mlops/mlops-evaluation-lm-evaluation-harness) | lm-eval-harness: бенчмарк LLM (MMLU, GSM8K и др.). | `mlops/evaluation/lm-evaluation-harness` |
| [`obliteratus`](/docs/user-guide/skills/bundled/mlops/mlops-inference-obliteratus) | OBLITERATUS: обезвреживание отказов LLM (diff-in-means). | `mlops/inference/obliteratus` |
| [`segment-anything-model`](/docs/user-guide/skills/bundled/mlops/mlops-models-segment-anything) | SAM: сегментация изображений без обучения с помощью точек, рамок, масок. | `mlops/models/segment-anything` |
| [`serving-llms-vllm`](/docs/user-guide/skills/bundled/mlops/mlops-inference-vllm) | vLLM: высокопроизводительное обслуживание LLM, OpenAI API, квантизация. | `mlops/inference/vllm` |
| [`weights-and-biases`](/docs/user-guide/skills/bundled/mlops/mlops-evaluation-weights-and-biases) | W&B: журналирование ML‑экспериментов, sweeps, реестр моделей, дашборды. | `mlops/evaluation/weights-and-biases` |
## заметки

| Навык | Описание | Путь |
|-------|----------|------|
| [`obsidian`](/docs/user-guide/skills/bundled/note-taking/note-taking-obsidian) | Чтение, поиск, создание и редактирование заметок в хранилище Obsidian. | `note-taking/obsidian` |
## продуктивность

| Skill | Description | Path |
|-------|-------------|------|
| [`airtable`](/docs/user-guide/skills/bundled/productivity/productivity-airtable) | REST API Airtable через curl. Операции CRUD с записями, фильтры, upsert. | `productivity/airtable` |
| [`google-workspace`](/docs/user-guide/skills/bundled/productivity/productivity-google-workspace) | Gmail, Calendar, Drive, Docs, Sheets через gws CLI или Python. | `productivity/google-workspace` |
| [`linear`](/docs/user-guide/skills/bundled/productivity/productivity-linear) | Linear: управление задачами, проектами, командами через GraphQL + curl. | `productivity/linear` |
| [`maps`](/docs/user-guide/skills/bundled/productivity/productivity-maps) | Геокодирование, POI, маршруты, часовые пояса через OpenStreetMap/OSRM. | `productivity/maps` |
| [`nano-pdf`](/docs/user-guide/skills/bundled/productivity/productivity-nano-pdf) | Редактирование текста, опечаток, заголовков PDF через nano-pdf CLI (NL‑подсказки). | `productivity/nano-pdf` |
| [`notion`](/docs/user-guide/skills/bundled/productivity/productivity-notion) | API Notion + ntn CLI: страницы, базы данных, markdown, Workers. | `productivity/notion` |
| [`ocr-and-documents`](/docs/user-guide/skills/bundled/productivity/productivity-ocr-and-documents) | Извлечение текста из PDF/сканов (pymupdf, marker-pdf). | `productivity/ocr-and-documents` |
| [`powerpoint`](/docs/user-guide/skills/bundled/productivity/productivity-powerpoint) | Создание, чтение, редактирование .pptx‑презентаций, слайдов, заметок, шаблонов. | `productivity/powerpoint` |
| [`teams-meeting-pipeline`](/docs/user-guide/skills/bundled/productivity/productivity-teams-meeting-pipeline) | Работа с pipeline резюме встреч Teams через Hermes CLI — резюмировать встречи, проверять статус pipeline, перезапускать задачи, управлять подписками Microsoft Graph. | `productivity/teams-meeting-pipeline` |
## red-teaming

| Навык | Описание | Путь |
|-------|----------|------|
| [`godmode`](/docs/user-guide/skills/bundled/red-teaming/red-teaming-godmode) | Обход ограничений LLM: Parseltongue, GODMODE, ULTRAPLINIAN. | `red-teaming/godmode` |
## исследования

| Навык | Описание | Путь |
|-------|----------|------|
| [`arxiv`](/docs/user-guide/skills/bundled/research/research-arxiv) | Поиск статей arXiv по ключевому слову, автору, категории или ID. | `research/arxiv` |
| [`blogwatcher`](/docs/user-guide/skills/bundled/research/research-blogwatcher) | Мониторинг блогов и RSS/Atom‑лент с помощью инструмента **blogwatcher‑cli**. | `research/blogwatcher` |
| [`llm-wiki`](/docs/user-guide/skills/bundled/research/research-llm-wiki) | LLM Wiki Карпати: построение/запрос взаимосвязанной базы знаний в markdown. | `research/llm-wiki` |
| [`polymarket`](/docs/user-guide/skills/bundled/research/research-polymarket) | Запрос к Polymarket: рынки, цены, ордербуки, история. | `research/polymarket` |
| [`research-paper-writing`](/docs/user-guide/skills/bundled/research/research-research-paper-writing) | Написание статей по машинному обучению для NeurIPS/ICML/ICLR: от разработки до подачи. | `research/research-paper-writing` |
## умный дом

| Навык | Описание | Путь |
|-------|----------|------|
| [`openhue`](/docs/user-guide/skills/bundled/smart-home/smart-home-openhue) | Управление светильниками Philips Hue, сценами и комнатами через OpenHue CLI. | `smart-home/openhue` |
## social-media

| Навык | Описание | Путь |
|-------|----------|------|
| [`xurl`](/docs/user-guide/skills/bundled/social-media/social-media-xurl) | X/Twitter через CLI xurl: публикация, поиск, прямые сообщения (DM), медиа, API v2. | `social-media/xurl` |
## разработка программного обеспечения

| Skill | Description | Path |
|-------|-------------|------|
| [`debugging-hermes-tui-commands`](/docs/user-guide/skills/bundled/software-development/software-development-debugging-hermes-tui-commands) | Отладка слеш‑команд Hermes TUI: Python, gateway, Ink UI. | `software-development/debugging-hermes-tui-commands` |
| [`hermes-agent-skill-authoring`](/docs/user-guide/skills/bundled/software-development/software-development-hermes-agent-skill-authoring) | Создание SKILL.md в репозитории: frontmatter, validator, структура. | `software-development/hermes-agent-skill-authoring` |
| [`hermes-s6-container-supervision`](/docs/user-guide/skills/bundled/software-development/software-development-hermes-s6-container-supervision) | Изменить, отладить или расширить дерево надзора s6‑overlay внутри Docker‑образа Hermes Agent — добавить новые сервисы, отладить шлюзы профилей, понять шаблон основной программы Architecture B. | `software-development/hermes-s6-container-supervision` |
| [`node-inspect-debugger`](/docs/user-guide/skills/bundled/software-development/software-development-node-inspect-debugger) | Отладка Node.js через `--inspect` + CLI протокола Chrome DevTools. | `software-development/node-inspect-debugger` |
| [`plan`](/docs/user-guide/skills/bundled/software-development/software-development-plan) | Режим планирования: написать markdown‑план в `.hermes/plans/`, без выполнения. | `software-development/plan` |
| [`python-debugpy`](/docs/user-guide/skills/bundled/software-development/software-development-python-debugpy) | Отладка Python: pdb REPL + remote debugpy (DAP). | `software-development/python-debugpy` |
| [`requesting-code-review`](/docs/user-guide/skills/bundled/software-development/software-development-requesting-code-review) | Предкоммитный ревью: сканирование безопасности, контроль качества, авто‑исправление. | `software-development/requesting-code-review` |
| [`spike`](/docs/user-guide/skills/bundled/software-development/software-development-spike) | Одноразовые эксперименты для проверки идеи перед разработкой. | `software-development/spike` |
| [`subagent-driven-development`](/docs/user-guide/skills/bundled/software-development/software-development-subagent-driven-development) | Выполнение планов через subagents `delegate_task` (двухэтапный ревью). | `software-development/subagent-driven-development` |
| [`systematic-debugging`](/docs/user-guide/skills/bundled/software-development/software-development-systematic-debugging) | 4‑фазовая отладка корневой причины: понять баги перед исправлением. | `software-development/systematic-debugging` |
| [`test-driven-development`](/docs/user-guide/skills/bundled/software-development/software-development-test-driven-development) | TDD: применять RED‑GREEN‑REFACTOR, тесты — до кода. | `software-development/test-driven-development` |
| [`writing-plans`](/docs/user-guide/skills/bundled/software-development/software-development-writing-plans) | Создание планов реализации: небольшие задачи, пути, код. | `software-development/writing-plans` |
## yuanbao

| Навык | Описание | Путь |
|-------|----------|------|
| [`yuanbao`](/docs/user-guide/skills/bundled/yuanbao/yuanbao-yuanbao) | Yuanbao (元宝) группы: упоминание @пользователей, запрос информации/участников. | `yuanbao` |