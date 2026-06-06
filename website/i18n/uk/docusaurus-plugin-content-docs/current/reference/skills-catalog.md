---
sidebar_position: 5
title: "Каталог вбудованих Skills"
description: "Каталог вбудованих навичок, що постачаються з Hermes Agent"
---

# Каталог вбудованих навичок

Hermes постачається з великою вбудованою бібліотекою навичок, яка копіюється у `~/.hermes/skills/` під час встановлення. Кожна навичка нижче посилається на окрему сторінку з повним визначенням, налаштуванням та використанням.

Hermes також синхронізує вбудовані навички за допомогою `hermes update`, причому маніфест синхронізації враховує локальні видалення та редагування користувачем. Якщо навичка, зазначена тут, відсутня у дереві `~/.hermes/skills/` вашого профілю, вона все одно постачається з Hermes; віднови її за допомогою `hermes skills reset <name> --restore`.

Якщо навичка відсутня у цьому списку, але присутня у репозиторії, каталог генерується заново скриптом `website/scripts/generate-skill-docs.py`.
## apple

| Навичка | Опис | Шлях |
|-------|-------------|------|
| [`apple-notes`](/docs/user-guide/skills/bundled/apple/apple-apple-notes) | Керуйте Apple Notes за допомогою memo CLI: створюйте, шукайте, редагуйте. | `apple/apple-notes` |
| [`apple-reminders`](/docs/user-guide/skills/bundled/apple/apple-apple-reminders) | Apple Reminders через remindctl: додавайте, переглядайте, позначайте виконаними. | `apple/apple-reminders` |
| [`findmy`](/docs/user-guide/skills/bundled/apple/apple-findmy) | Відстежуйте пристрої Apple/AirTags за допомогою FindMy.app на macOS. | `apple/findmy` |
| [`imessage`](/docs/user-guide/skills/bundled/apple/apple-imessage) | Надсилайте та отримуйте iMessages/SMS через CLI imsg на macOS. | `apple/imessage` |
| [`macos-computer-use`](/docs/user-guide/skills/bundled/apple/apple-macos-computer-use) | Керуйте робочим столом macOS у фоновому режимі — скріншоти, миша, клавіатура, прокручування, перетягування — без перехоплення курсору, фокусу клавіатури чи простору користувача. Працює з будь‑якою моделлю, що підтримує інструменти. Завантажуйте цю навичку, коли інструмент `computer_use`… | `apple/macos-computer-use` |
## автономні-ШІ-агенти

| Skill | Description | Path |
|-------|-------------|------|
| [`claude-code`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-claude-code) | Делегувати кодування Claude Code CLI (features, PRs). | `autonomous-ai-agents/claude-code` |
| [`codex`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-codex) | Делегувати кодування OpenAI Codex CLI (features, PRs). | `autonomous-ai-agents/codex` |
| [`hermes-agent`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-hermes-agent) | Налаштувати, розширити або внести свій внесок у Hermes Agent. | `autonomous-ai-agents/hermes-agent` |
| [`kanban-codex-lane`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-kanban-codex-lane) | Використовувати, коли Hermes Kanban worker хоче запустити Codex CLI як ізольовану lane‑реалізацію, залишаючи Hermes відповідальним за життєвий цикл завдання, узгодження, тестування та передачу. | `autonomous-ai-agents/kanban-codex-lane` |
| [`opencode`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-opencode) | Делегувати кодування OpenCode CLI (features, PR review). | `autonomous-ai-agents/opencode` |
## креативний

| Навичка | Опис | Шлях |
|-------|------|------|
| [`architecture-diagram`](/docs/user-guide/skills/bundled/creative/creative-architecture-diagram) | SVG‑діаграми архітектури/хмари/інфраструктури у темному стилі, у вигляді HTML. | `creative/architecture-diagram` |
| [`ascii-art`](/docs/user-guide/skills/bundled/creative/creative-ascii-art) | ASCII‑арт: pyfiglet, cowsay, boxes, image-to-ascii. | `creative/ascii-art` |
| [`ascii-video`](/docs/user-guide/skills/bundled/creative/creative-ascii-video) | ASCII‑відео: конвертувати відео/аудіо в кольоровий ASCII MP4/GIF. | `creative/ascii-video` |
| [`baoyu-article-illustrator`](/docs/user-guide/skills/bundled/creative/creative-baoyu-article-illustrator) | Ілюстрації статей: тип × стиль × послідовність палітри. | `creative/baoyu-article-illustrator` |
| [`baoyu-comic`](/docs/user-guide/skills/bundled/creative/creative-baoyu-comic) | Комікси знань (知识漫画): освітні, біографічні, навчальні. | `creative/baoyu-comic` |
| [`baoyu-infographic`](/docs/user-guide/skills/bundled/creative/creative-baoyu-infographic) | Інфографіка: 21 макет × 21 стиль (信息图, 可视化). | `creative/baoyu-infographic` |
| [`claude-design`](/docs/user-guide/skills/bundled/creative/creative-claude-design) | Створення одноразових HTML‑артефактів (лендінг, презентація, прототип). | `creative/claude-design` |
| [`comfyui`](/docs/user-guide/skills/bundled/creative/creative-comfyui) | Генерувати зображення, відео та аудіо за допомогою ComfyUI — встановити, запустити, керувати вузлами/моделями, виконувати робочі процеси з ін’єкцією параметрів. Використовує офіційний comfy-cli для життєвого циклу та прямий REST/WebSocket API для виконання. | `creative/comfyui` |
| [`ideation`](/docs/user-guide/skills/bundled/creative/creative-creative-ideation) | Генерувати ідеї проєктів за допомогою креативних обмежень. | `creative/creative-ideation` |
| [`design-md`](/docs/user-guide/skills/bundled/creative/creative-design-md) | Створювати, перевіряти та експортувати файли специфікації токенів DESIGN.md від Google. | `creative/design-md` |
| [`excalidraw`](/docs/user-guide/skills/bundled/creative/creative-excalidraw) | Ручні Excalidraw JSON‑діаграми (арх, потік, послідовність). | `creative/excalidraw` |
| [`humanizer`](/docs/user-guide/skills/bundled/creative/creative-humanizer) | Гуманізувати текст: прибрати AI‑особливості та додати реальний голос. | `creative/humanizer` |
| [`manim-video`](/docs/user-guide/skills/bundled/creative/creative-manim-video) | Анімації Manim CE: відео з математики/алгоритмів від 3Blue1Brown. | `creative/manim-video` |
| [`p5js`](/docs/user-guide/skills/bundled/creative/creative-p5js) | Ескізи p5.js: генерування мистецтва, шейдери, інтерактивність, 3D. | `creative/p5js` |
| [`pixel-art`](/docs/user-guide/skills/bundled/creative/creative-pixel-art) | Піксельний арт з палітрами епох (NES, Game Boy, PICO‑8). | `creative/pixel-art` |
| [`popular-web-designs`](/docs/user-guide/skills/bundled/creative/creative-popular-web-designs) | 54 реальні системи дизайну (Stripe, Linear, Vercel) у вигляді HTML/CSS. | `creative/popular-web-designs` |
| [`pretext`](/docs/user-guide/skills/bundled/creative/creative-pretext) | Використовувати при створенні креативних браузерних демо з @chenglou/pretext — розмітка тексту без DOM для ASCII‑арту, типографічного потоку навколо перешкод, ігор «текст‑як‑геометрія», кінетичної типографії та генеративного мистецтва на основі тексту. Створює однорядковий HTML. | `creative/pretext` |
| [`sketch`](/docs/user-guide/skills/bundled/creative/creative-sketch) | Тимчасові HTML‑мокапи: 2‑3 варіанти дизайну для порівняння. | `creative/sketch` |
| [`songwriting-and-ai-music`](/docs/user-guide/skills/bundled/creative/creative-songwriting-and-ai-music) | Майстерність написання пісень та підказки для музики Suno AI. | `creative/songwriting-and-ai-music` |
| [`touchdesigner-mcp`](/docs/user-guide/skills/bundled/creative/creative-touchdesigner-mcp) | Керувати запущеним екземпляром TouchDesigner через twozero MCP — створювати оператори, задавати параметри, з’єднувати, виконувати Python, будувати візуали в реальному часі. 36 вбудованих інструментів. | `creative/touchdesigner-mcp` |
## наука про дані

| Навичка | Опис | Шлях |
|-------|-------------|------|
| [`jupyter-live-kernel`](/docs/user-guide/skills/bundled/data-science/data-science-jupyter-live-kernel) | Ітеративний Python через живе ядро Jupyter (hamelnb). | `data-science/jupyter-live-kernel` |
## devops

| Інструмент | Опис | Path |
|------------|------|------|
| [`kanban-orchestrator`](/docs/user-guide/skills/bundled/devops/devops-kanban-orchestrator) | Плейбук декомпозиції + правила проти спокуси для профілю оркестратора, що маршрутизує роботу через Kanban. Правило «не роби роботу сам» та базовий життєвий цикл автоматично впроваджуються в системний підказник кожного kanban‑робітника; цей інструмент… | `devops/kanban-orchestrator` |
| [`kanban-worker`](/docs/user-guide/skills/bundled/devops/devops-kanban-worker) | Підводні камені, приклади та крайові випадки для Hermes Kanban workers. Сам життєвий цикл автоматично впроваджується в системний підказник кожного робітника як KANBAN_GUIDANCE (з agent/prompt_builder.py); цей інструмент завантажується, коли потрібен глибший детальний… | `devops/kanban-worker` |
| [`webhook-subscriptions`](/docs/user-guide/skills/bundled/devops/devops-webhook-subscriptions) | Підписки на вебхуки: запуск агента за подією. | `devops/webhook-subscriptions` |
## dogfood

| Навичка | Опис | Шлях |
|-------|-------------|------|
| [`dogfood`](/docs/user-guide/skills/bundled/dogfood/dogfood-dogfood) | Дослідницьке QA веб‑додатків: виявлення багів, збір доказів, створення звітів. | `dogfood` |
## електронна пошта

| Skill | Description | Path |
|-------|-------------|------|
| [`himalaya`](/docs/user-guide/skills/bundled/email/email-himalaya) | Himalaya CLI: електронна пошта IMAP/SMTP у терміналі. | `email/himalaya` |
## ігри

| Навичка | Опис | Шлях |
|-------|-------------|------|
| [`minecraft-modpack-server`](/docs/user-guide/skills/bundled/gaming/gaming-minecraft-modpack-server) | Хостити модифіковані сервери Minecraft (CurseForge, Modrinth). | `gaming/minecraft-modpack-server` |
| [`pokemon-player`](/docs/user-guide/skills/bundled/gaming/gaming-pokemon-player) | Грати в Pokémon через безголовий емулятор + читання RAM. | `gaming/pokemon-player` |
## github

| Skill | Опис | Path |
|-------|------|------|
| [`codebase-inspection`](/docs/user-guide/skills/bundled/github/github-codebase-inspection) | Перевірка кодової бази за допомогою pygount: LOC, мови, співвідношення. | `github/codebase-inspection` |
| [`github-auth`](/docs/user-guide/skills/bundled/github/github-github-auth) | Налаштування автентифікації GitHub: HTTPS‑токени, SSH‑ключі, вхід через gh CLI. | `github/github-auth` |
| [`github-code-review`](/docs/user-guide/skills/bundled/github/github-github-code-review) | Огляд PR: дифі, інлайн‑коментарі через gh або REST. | `github/github-code-review` |
| [`github-issues`](/docs/user-guide/skills/bundled/github/github-github-issues) | Створення, сортування, позначення мітками, призначення GitHub‑issues через gh або REST. | `github/github-issues` |
| [`github-pr-workflow`](/docs/user-guide/skills/bundled/github/github-github-pr-workflow) | Життєвий цикл GitHub PR: гілка, коміт, відкриття, CI, злиття. | `github/github-pr-workflow` |
| [`github-repo-management`](/docs/user-guide/skills/bundled/github/github-github-repo-management) | Клонування/створення/форк репозиторіїв; управління віддаленими репозиторіями, релізами. | `github/github-repo-management` |
## mcp

| Навичка | Опис | Шлях |
|-------|-------------|------|
| [`native-mcp`](/docs/user-guide/skills/bundled/mcp/mcp-native-mcp) | MCP‑клієнт: підключення до серверів, реєстрація інструментів (stdio/HTTP). | `mcp/native-mcp` |
## media

| Skill | Опис | Path |
|-------|------|------|
| [`gif-search`](/docs/user-guide/skills/bundled/media/media-gif-search) | Пошук/завантаження GIF‑файлів з Tenor за допомогою `curl` + `jq`. | `media/gif-search` |
| [`heartmula`](/docs/user-guide/skills/bundled/media/media-heartmula) | HeartMuLa: генерація пісень у стилі Suno за текстом та тегами. | `media/heartmula` |
| [`songsee`](/docs/user-guide/skills/bundled/media/media-songsee) | Аудіо‑спектрограми/особливості (mel, chroma, MFCC) через CLI. | `media/songsee` |
| [`spotify`](/docs/user-guide/skills/bundled/media/media-spotify) | Spotify: відтворення, пошук, черга, керування плейлистами та пристроями. | `media/spotify` |
| [`youtube-content`](/docs/user-guide/skills/bundled/media/media-youtube-content) | Транскрипції YouTube, перетворені на резюме, теми та блоги. | `media/youtube-content` |
## mlops

| Skill | Description | Path |
|-------|-------------|------|
| [`audiocraft-audio-generation`](/docs/user-guide/skills/bundled/mlops/mlops-models-audiocraft) | AudioCraft: MusicGen текст‑у‑музику, AudioGen текст‑у‑звук. | `mlops/models/audiocraft` |
| [`dspy`](/docs/user-guide/skills/bundled/mlops/mlops-research-dspy) | DSPy: декларативні програми LM, автоматичне оптимізування підказок, RAG. | `mlops/research/dspy` |
| [`huggingface-hub`](/docs/user-guide/skills/bundled/mlops/mlops-huggingface-hub) | HuggingFace hf CLI: пошук/завантаження/вивантаження моделей, наборів даних. | `mlops/huggingface-hub` |
| [`llama-cpp`](/docs/user-guide/skills/bundled/mlops/mlops-inference-llama-cpp) | llama.cpp локальне інференсування GGUF + виявлення моделей у HF Hub. | `mlops/inference/llama-cpp` |
| [`evaluating-llms-harness`](/docs/user-guide/skills/bundled/mlops/mlops-evaluation-lm-evaluation-harness) | lm-eval-harness: бенчмарк LLM (MMLU, GSM8K тощо). | `mlops/evaluation/lm-evaluation-harness` |
| [`obliteratus`](/docs/user-guide/skills/bundled/mlops/mlops-inference-obliteratus) | OBLITERATUS: усунення відмов LLM (diff‑in‑means). | `mlops/inference/obliteratus` |
| [`segment-anything-model`](/docs/user-guide/skills/bundled/mlops/mlops-models-segment-anything) | SAM: zero‑shot сегментація зображень за допомогою точок, прямокутників, масок. | `mlops/models/segment-anything` |
| [`serving-llms-vllm`](/docs/user-guide/skills/bundled/mlops/mlops-inference-vllm) | vLLM: високопродуктивне обслуговування LLM, OpenAI API, квантування. | `mlops/inference/vllm` |
| [`weights-and-biases`](/docs/user-guide/skills/bundled/mlops/mlops-evaluation-weights-and-biases) | W&B: журналювання ML‑експериментів, sweep‑ів, реєстр моделей, панелі. | `mlops/evaluation/weights-and-biases` |
## нотатки

| Навичка | Опис | Шлях |
|-------|-------------|------|
| [`obsidian`](/docs/user-guide/skills/bundled/note-taking/note-taking-obsidian) | Читати, шукати, створювати та редагувати нотатки у сховищі Obsidian. | `note-taking/obsidian` |
## продуктивність

| Навичка | Опис | Шлях |
|-------|-------------|------|
| [`airtable`](/docs/user-guide/skills/bundled/productivity/productivity-airtable) | Airtable REST API через curl. Операції CRUD над записами, фільтри, upsert. | `productivity/airtable` |
| [`google-workspace`](/docs/user-guide/skills/bundled/productivity/productivity-google-workspace) | Gmail, Calendar, Drive, Docs, Sheets через gws CLI або Python. | `productivity/google-workspace` |
| [`linear`](/docs/user-guide/skills/bundled/productivity/productivity-linear) | Linear: керування задачами, проектами, командами через GraphQL + curl. | `productivity/linear` |
| [`maps`](/docs/user-guide/skills/bundled/productivity/productivity-maps) | Геокодування, POI, маршрути, часові пояси через OpenStreetMap/OSRM. | `productivity/maps` |
| [`nano-pdf`](/docs/user-guide/skills/bundled/productivity/productivity-nano-pdf) | Редагування тексту, помилок, заголовків PDF через nano-pdf CLI (NL prompts). | `productivity/nano-pdf` |
| [`notion`](/docs/user-guide/skills/bundled/productivity/productivity-notion) | Notion API + ntn CLI: сторінки, бази даних, markdown, Workers. | `productivity/notion` |
| [`ocr-and-documents`](/docs/user-guide/skills/bundled/productivity/productivity-ocr-and-documents) | Витягнення тексту з PDF/сканів (pymupdf, marker-pdf). | `productivity/ocr-and-documents` |
| [`powerpoint`](/docs/user-guide/skills/bundled/productivity/productivity-powerpoint) | Створення, читання, редагування .pptx презентацій, слайдів, нотаток, шаблонів. | `productivity/powerpoint` |
| [`teams-meeting-pipeline`](/docs/user-guide/skills/bundled/productivity/productivity-teams-meeting-pipeline) | Керування конвеєром підсумків зустрічей Teams через Hermes CLI — підсумовування зустрічей, перевірка статусу конвеєра, повторне виконання завдань, управління підписками Microsoft Graph. | `productivity/teams-meeting-pipeline` |
## red-teaming

| Навичка | Опис | Шлях |
|-------|-------------|------|
| [`godmode`](/docs/user-guide/skills/bundled/red-teaming/red-teaming-godmode) | Обхід захисту LLM: Parseltongue, GODMODE, ULTRAPLINIAN. | `red-teaming/godmode` |
## дослідження

| Навичка | Опис | Шлях |
|-------|-------------|------|
| [`arxiv`](/docs/user-guide/skills/bundled/research/research-arxiv) | Пошук статей arXiv за ключовим словом, автором, категорією або ID. | `research/arxiv` |
| [`blogwatcher`](/docs/user-guide/skills/bundled/research/research-blogwatcher) | Моніторинг блогів та RSS/Atom‑стрічок за допомогою інструменту **blogwatcher‑cli**. | `research/blogwatcher` |
| [`llm-wiki`](/docs/user-guide/skills/bundled/research/research-llm-wiki) | **LLM Wiki** Карпарті: створення/запит взаємопов’язаної markdown‑бази знань. | `research/llm-wiki` |
| [`polymarket`](/docs/user-guide/skills/bundled/research/research-polymarket) | Запит Polymarket: ринки, ціни, ордербуки, історія. | `research/polymarket` |
| [`research-paper-writing`](/docs/user-guide/skills/bundled/research/research-research-paper-writing) | Написання ML‑статей для NeurIPS/ICML/ICLR: від дизайну → подачі. | `research/research-paper-writing` |
## розумний дім

| Навичка | Опис | Шлях |
|-------|-------------|------|
| [`openhue`](/docs/user-guide/skills/bundled/smart-home/smart-home-openhue) | Керуйте лампами Philips Hue, сценами, кімнатами за допомогою OpenHue CLI. | `smart-home/openhue` |
## social-media

| Skill | Description | Path |
|-------|-------------|------|
| [`xurl`](/docs/user-guide/skills/bundled/social-media/social-media-xurl) | X/Twitter за допомогою CLI xurl: публікація, пошук, DM, медіа, API v2. | `social-media/xurl` |
## розробка ПЗ

| Навичка | Опис | Шлях |
|-------|-------------|------|
| [`debugging-hermes-tui-commands`](/docs/user-guide/skills/bundled/software-development/software-development-debugging-hermes-tui-commands) | Налагоджуй slash‑команди Hermes TUI: Python, gateway, Ink UI. | `software-development/debugging-hermes-tui-commands` |
| [`hermes-agent-skill-authoring`](/docs/user-guide/skills/bundled/software-development/software-development-hermes-agent-skill-authoring) | Створи у репозиторії файл **SKILL.md**: frontmatter, validator, структура. | `software-development/hermes-agent-skill-authoring` |
| [`hermes-s6-container-supervision`](/docs/user-guide/skills/bundled/software-development/software-development-hermes-s6-container-supervision) | Змінюй, налагоджуй або розширюй дерево супервізії s6‑overlay у Docker‑образі Hermes Agent — додавай нові сервіси, налагоджуй gateway профілів, розумій шаблон головної програми Architecture B. | `software-development/hermes-s6-container-supervision` |
| [`node-inspect-debugger`](/docs/user-guide/skills/bundled/software-development/software-development-node-inspect-debugger) | Налагоджуй Node.js через `--inspect` + CLI протоколу Chrome DevTools. | `software-development/node-inspect-debugger` |
| [`plan`](/docs/user-guide/skills/bundled/software-development/software-development-plan) | Режим плану: записуй markdown‑план у `.hermes/plans/`, без виконання. | `software-development/plan` |
| [`python-debugpy`](/docs/user-guide/skills/bundled/software-development/software-development-python-debugpy) | Налагоджуй Python: pdb REPL + remote debugpy (DAP). | `software-development/python-debugpy` |
| [`requesting-code-review`](/docs/user-guide/skills/bundled/software-development/software-development-requesting-code-review) | Перевірка перед комітом: сканування безпеки, контроль якості, автоматичне виправлення. | `software-development/requesting-code-review` |
| [`spike`](/docs/user-guide/skills/bundled/software-development/software-development-spike) | Тимчасові експерименти для підтвердження ідеї перед розробкою. | `software-development/spike` |
| [`subagent-driven-development`](/docs/user-guide/skills/bundled/software-development/software-development-subagent-driven-development) | Виконуй плани через підагенти `delegate_task` (2‑етапний перегляд). | `software-development/subagent-driven-development` |
| [`systematic-debugging`](/docs/user-guide/skills/bundled/software-development/software-development-systematic-debugging) | 4‑фазове налагодження причин: розумій помилки перед виправленням. | `software-development/systematic-debugging` |
| [`test-driven-development`](/docs/user-guide/skills/bundled/software-development/software-development-test-driven-development) | TDD: застосовуй RED‑GREEN‑REFACTOR, тести перед кодом. | `software-development/test-driven-development` |
| [`writing-plans`](/docs/user-guide/skills/bundled/software-development/software-development-writing-plans) | Пиши плани реалізації: маленькі завдання, шляхи, код. | `software-development/writing-plans` |
## yuanbao

| Навичка | Опис | Шлях |
|-------|-------------|------|
| [`yuanbao`](/docs/user-guide/skills/bundled/yuanbao/yuanbao-yuanbao) | Yuanbao (元宝) групи: @mention користувачів, запит інформації/учасників. | `yuanbao` |