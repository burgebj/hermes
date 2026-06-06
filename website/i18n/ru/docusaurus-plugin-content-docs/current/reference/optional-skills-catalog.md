---
sidebar_position: 9
title: "Опциональный каталог Skills"
description: "Официальные необязательные навыки, поставляемые с Hermes Agent — установи их командой `hermes skills install official/<category>/<skill>`"
---

# Каталог необязательных skill

Необязательные skill поставляются с hermes-agent в `optional-skills/`, но **не активны по умолчанию**. Установи их явно:

```bash
hermes skills install official/<category>/<skill>
```

Например:

```bash
hermes skills install official/blockchain/solana
hermes skills install official/mlops/flash-attention
```

Каждый skill ниже ссылается на отдельную страницу с полным определением, настройкой и использованием.

Чтобы удалить:

```bash
hermes skills uninstall <skill-name>
```
## автономные AI‑агенты

| Навык | Описание |
|-------|----------|
| [**antigravity-cli**](/docs/user-guide/skills/optional/autonomous-ai-agents/autonomous-ai-agents-antigravity-cli) | Управляй Antigravity CLI (agy): плагины, аутентификация, песочница. |
| [**blackbox**](/docs/user-guide/skills/optional/autonomous-ai-agents/autonomous-ai-agents-blackbox) | Делегируй задачи программирования агенту Blackbox AI CLI. Мульти‑модельный агент со встроенным судейством, который запускает задачи через несколько LLM и выбирает лучший результат. Требуется CLI blackbox и API‑ключ Blackbox AI. |
| [**grok**](/docs/user-guide/skills/optional/autonomous-ai-agents/autonomous-ai-agents-grok) | Делегируй программирование в xAI Grok Build CLI (функции, pull‑request'ы). |
| [**honcho**](/docs/user-guide/skills/optional/autonomous-ai-agents/autonomous-ai-agents-honcho) | Настраивай и используй память Honcho с Hermes — кросс‑сессионное моделирование пользователей, изоляция нескольких профилей, конфигурация наблюдений, диалектическое рассуждение, резюме сессий и контроль бюджета контекста. Используй при настройке Honcho и устранении проблем. |
| [**openhands**](/docs/user-guide/skills/optional/autonomous-ai-agents/autonomous-ai-agents-openhands) | Делегируй программирование в OpenHands CLI (модель‑агностичный, LiteLLM). |
## блокчейн

| Skill | Description |
|-------|-------------|
| [**evm**](/docs/user-guide/skills/optional/blockchain/blockchain-evm) | Только клиент EVM для чтения: кошельки, токены, gas на 8 цепочках. |
| [**hyperliquid**](/docs/user-guide/skills/optional/blockchain/blockchain-hyperliquid) | Данные рынка Hyperliquid, история аккаунта, обзор сделок. |
| [**solana**](/docs/user-guide/skills/optional/blockchain/blockchain-solana) | Запрос данных блокчейна Solana с ценами в USD — балансы кошельков, портфели токенов со стоимостью, детали транзакций, NFT, обнаружение крупных держателей и живая статистика сети. Использует Solana RPC + CoinGecko. API‑ключ не требуется. |
## коммуникация

| Навык | Описание |
|-------|-----------|
| [**one-three-one-rule**](/docs/user-guide/skills/optional/communication/communication-one-three-one-rule) | Структурированная методика принятия решений для технических предложений и анализа компромиссов. Когда пользователь сталкивается с выбором между несколькими подходами (архитектурные решения, выбор инструментов, стратегии рефакторинга, пути миграции), этот навык помогает разбить процесс на три этапа: один — определить цель, три — оценить варианты, один — принять решение. |
## creative

| Skill | Description |
|-------|-------------|
| [**blender-mcp**](/docs/user-guide/skills/optional/creative/creative-blender-mcp) | Управляй Blender напрямую из Hermes через socket‑соединение с аддоном **blender-mcp**. Создавай 3D‑объекты, материалы, анимации и выполняй произвольный код Blender Python (bpy). Используется, когда пользователь хочет создать или изменить что‑либо в Blender. |
| [**concept-diagrams**](/docs/user-guide/skills/optional/creative/creative-concept-diagrams) | Генерируй плоские минималистичные SVG‑диаграммы, учитывающие светлую/тёмную темы, в виде автономных HTML‑файлов, используя единый образовательный визуальный язык с 9 семантическими цветовыми градациями, типографикой sentence‑case и автоматическим тёмным режимом. Наилучшим образом подходит для образовательных и подобных задач. |
| [**hyperframes**](/docs/user-guide/skills/optional/creative/creative-hyperframes) | Создавай видеокомпозиции на основе HTML, анимированные титульные карточки, социальные оверлеи, видео с субтитрами и говорящими ведущими, аудио‑реактивные визуалы и переходы‑шейдеры с помощью **HyperFrames**. HTML является единственным источником правды для видео. Используется, когда пользователь хочет создать такие видеоматериалы. |
| [**kanban-video-orchestrator**](/docs/user-guide/skills/optional/creative/creative-kanban-video-orchestrator) | Планируй, настраивай и контролируй многопоточный видеопроизводственный конвейер, поддерживаемый **Hermes Kanban**. Используется, когда пользователь хочет создать ЛЮБОЕ видео — художественный фильм, рекламный/продуктовый ролик, музыкальное видео, объяснительное, ASCII/терминальное искусство, абстрактное/генеративное и т.д. |
| [**meme-generation**](/docs/user-guide/skills/optional/creative/creative-meme-generation) | Генерируй настоящие мем‑изображения, выбирая шаблон и накладывая текст с помощью **Pillow**. Создаёт реальные файлы мемов в формате **.png**. |
## devops

| Skill | Description |
|-------|-------------|
| [**inference-sh-cli**](/docs/user-guide/skills/optional/devops/devops-cli) | Запусти более 150 AI‑приложений через CLI `inference.sh` (infsh) — генерация изображений, создание видео, LLM, поиск, 3D, автоматизация соцсетей. Использует терминальный инструмент. Триггеры: `inference.sh`, `infsh`, AI‑приложения, `flux`, `veo`, генерация изображений, генерация видео, `seedrea`… |
| [**docker-management**](/docs/user-guide/skills/optional/devops/devops-docker-management) | Управляй контейнерами Docker, образами, томами, сетями и стеками Compose — операции жизненного цикла, отладка, очистка и оптимизация Dockerfile. |
| [**pinggy-tunnel**](/docs/user-guide/skills/optional/devops/devops-pinggy-tunnel) | Туннели localhost без установки через SSH с помощью Pinggy. |
| [**watchers**](/docs/user-guide/skills/optional/devops/devops-watchers) | Опрос RSS, JSON‑API и GitHub с дедупликацией по водянному знаку. |
## dogfood

| Навык | Описание |
|-------|----------|
| [**adversarial-ux-test**](/docs/user-guide/skills/optional/dogfood/dogfood-adversarial-ux-test) | Разыгрывай роль самого сложного, технологически неподготовленного пользователя твоего продукта. Просматривай приложение от лица этой персоны, находи каждую проблему UX, а затем отфильтруй жалобы через слой прагматизма, чтобы отделить реальные проблемы от шума. Создаёт практические тикеты… |
## email

| Skill | Описание |
|-------|----------|
| [**agentmail**](/docs/user-guide/skills/optional/email/email-agentmail) | Предоставить агенту собственный выделенный почтовый ящик через AgentMail. Отправлять, получать и управлять электронной почтой автономно, используя принадлежащие агенту адреса (например, hermes-agent@agentmail.to). |
## финансы

| Skill | Description |
|-------|-------------|
| [**3-statement-model**](/docs/user-guide/skills/optional/finance/finance-3-statement-model) | Создавай полностью интегрированные модели трёх финансовых отчётов (IS, BS, CF) в Excel с графиками оборотного капитала, расчётами амортизации, графиком долга и связями, обеспечивающими согласованность наличных и нераспределённой прибыли. Сочетается с **excel-author**. |
| [**comps-analysis**](/docs/user-guide/skills/optional/finance/finance-comps-analysis) | Выполняй анализ сопоставимых компаний в Excel — операционные метрики, мультипликаторы оценки, статистическое сравнение с группой аналогов. Сочетается с **excel-author**. Используется для оценки публичных компаний, ценообразования IPO, отраслевого бенчмаркинга или выявления аномалий. |
| [**dcf-model**](/docs/user-guide/skills/optional/finance/finance-dcf-model) | Создавай институциональные модели DCF‑оценки в Excel — прогнозы выручки, построение FCF, WACC, терминальная стоимость, сценарии Bear/Base/Bull, таблицы чувствительности 5×5. Сочетается с **excel-author**. Применяется для анализа внутренней стоимости акций. |
| [**excel-author**](/docs/user-guide/skills/optional/finance/finance-excel-author) | Создавай проверяемые рабочие книги Excel без интерфейса с помощью **openpyxl** — конвенции цветов ячеек (синий/чёрный/зелёный), формулы вместо жёстких значений, именованные диапазоны, проверки баланса, таблицы чувствительности. Используется для финансовых моделей, аудита выводов, сверок. |
| [**lbo-model**](/docs/user-guide/skills/optional/finance/finance-lbo-model) | Создавай модели выкупа с привлечением заемных средств в Excel — источники и использования, график долга, погашение наличных, выходной мультипликатор, чувствительность IRR/MOIC. Сочетается с **excel-author**. Применяется для отбора PE‑проекта, оценки спонсорского кейса или иллюстративного LBO в презентации. |
| [**merger-model**](/docs/user-guide/skills/optional/finance/finance-merger-model) | Создавай модели аккреции/разводнения (слияния) в Excel — про‑форму P&L, синергии, структуру финансирования, влияние на EPS. Сочетается с **excel-author**. Применяется для M&A‑презентаций, материалов для совета директоров или оценки сделки. |
| [**pptx-author**](/docs/user-guide/skills/optional/finance/finance-pptx-author) | Создавай презентации PowerPoint без интерфейса с помощью **python-pptx**. Сочетается с **excel-author** для деков, где каждый показатель прослеживается к ячейке рабочей книги. Используется для питч‑деков, меморандумов IC, примечаний к отчётности. |
| [**stocks**](/docs/user-guide/skills/optional/finance/finance-stocks) | Котировки акций, история, поиск, сравнение, криптовалюты через Yahoo. |
## health

| Skill | Description |
|-------|-------------|
| [**fitness-nutrition**](/docs/user-guide/skills/optional/health/health-fitness-nutrition) | Планировщик тренировок в зале и трекер питания. Поиск более 690 упражнений по группе мышц, оборудованию или категории через wger. Просмотр макронутриентов и калорий более 380 000 продуктов через USDA FoodData Central. Вычисление ИМТ, TDEE, максимального одноповторного веса, распределения макронутриентов и … |
| [**neuroskill-bci**](/docs/user-guide/skills/optional/health/health-neuroskill-bci) | Подключение к запущенному экземпляру NeuroSkill и включение в ответы текущего когнитивного и эмоционального состояния пользователя (фокус, расслабление, настроение, когнитивная нагрузка, сонливость, частота сердечных сокращений, HRV, стадии сна и более 40 полученных EXG‑оценок) … |
## mcp

| Skill | Description |
|-------|-------------|
| [**fastmcp**](/docs/user-guide/skills/optional/mcp/mcp-fastmcp) | Создавай, тестируй, проверяй, устанавливай и развёртывай серверы MCP с помощью FastMCP на Python. Используй при создании нового сервера MCP, обёртывании API или базы данных в инструменты MCP, публикации ресурсов или подсказок, а также при подготовке сервера FastMCP для Claude Code, Cur… |
| [**mcporter**](/docs/user-guide/skills/optional/mcp/mcp-mcporter) | Используй CLI `mcporter` для перечисления, настройки, аутентификации и вызова серверов/инструментов MCP напрямую (по HTTP или stdio), включая ad‑hoc‑серверы, правки конфигурации и генерацию CLI/типов. |
## миграция

| Skill | Описание |
|-------|----------|
| [**openclaw-migration**](/docs/user-guide/skills/optional/migration/migration-openclaw-migration) | Переносит пользовательские настройки OpenClaw в Hermes Agent. Импортирует совместимые с Hermes `memories`, `SOUL.md`, списки разрешённых команд, пользовательские навыки и выбранные ресурсы рабочего пространства из `~/.openclaw`, затем точно сообщает, что не удалось мигрировать… |
## mlops

| Skill | Description |
|-------|-------------|
| [**huggingface-accelerate**](/docs/user-guide/skills/optional/mlops/mlops-accelerate) | Самый простой API распределённого обучения. 4 строки кода, чтобы добавить поддержку распределённого режима в любой скрипт PyTorch. Унифицированный API для DeepSpeed, FSDP, Megatron и DDP. Автоматическое размещение устройств, смешанная точность (FP16/BF16/FP8). Интерактивная конфигурация, единый запуск команд. |
| [**axolotl**](/docs/user-guide/skills/optional/mlops/mlops-training-axolotl) | Axolotl: настройка LLM через YAML (LoRA, DPO, GRPO). |
| [**chroma**](/docs/user-guide/skills/optional/mlops/mlops-chroma) | Открытая база эмбеддингов для AI‑приложений. Хранит эмбеддинги и метаданные, выполняет векторный и полнотекстовый поиск, фильтрацию по метаданным. Простой API из 4 функций. Масштабируется от ноутбуков до производственных кластеров. Используется для семантического поиска, RAG и пр. |
| [**clip**](/docs/user-guide/skills/optional/mlops/mlops-clip) | Модель OpenAI, соединяющая зрение и язык. Позволяет выполнять классификацию изображений в ноль‑выстрелов, сопоставление изображение‑текст и кросс‑модальный поиск. Обучена на 400 млн пар изображение‑текст. Применяется для поиска изображений, модерации контента и задач vision‑language. |
| [**faiss**](/docs/user-guide/skills/optional/mlops/mlops-faiss) | Библиотека Facebook для эффективного поиска похожих векторов и кластеризации плотных векторов. Поддерживает миллиарды векторов, ускорение на GPU и различные типы индексов (Flat, IVF, HNSW). Используется для быстрого k‑NN‑поиска, масштабного векторного извлечения и т.п. |
| [**optimizing-attention-flash**](/docs/user-guide/skills/optional/mlops/mlops-flash-attention) | Оптимизирует внимание трансформеров с помощью Flash Attention, обеспечивая ускорение 2‑4× и сокращение потребления памяти 10‑20×. Применяется при обучении/инференсе трансформеров с длинными последовательностями (>512 токенов), при проблемах с памятью GPU из‑за внимания или когда требуется более быстрая обработка. |
| [**guidance**](/docs/user-guide/skills/optional/mlops/mlops-guidance) | Управляй выводом LLM с помощью regex и грамматик, гарантируй корректную генерацию JSON/XML/кода, принуждай к структурированным форматам и создавай многошаговые рабочие процессы с Guidance — фреймворком ограниченной генерации от Microsoft Research. |
| [**huggingface-tokenizers**](/docs/user-guide/skills/optional/mlops/mlops-huggingface-tokenizers) | Быстрые токенизаторы, оптимизированные для исследований и продакшна. Реализация на Rust токенизирует 1 GB за <20 секунд. Поддерживает алгоритмы BPE, WordPiece и Unigram. Позволяют обучать пользовательские словари, отслеживать выравнивание, обрабатывать паддинг и усечение. Полностью интегрируются в экосистему HuggingFace. |
| [**instructor**](/docs/user-guide/skills/optional/mlops/mlops-instructor) | Извлекай структурированные данные из ответов LLM с валидацией Pydantic, автоматически повторяй неудачные извлечения, парси сложный JSON с типобезопасностью и получай частичные результаты потоково с Instructor — проверенной библиотекой для структурированного вывода. |
| [**lambda-labs-gpu-cloud**](/docs/user-guide/skills/optional/mlops/mlops-lambda-labs) | Зарезервированные и по‑запросу GPU‑облачные инстансы для обучения и инференса ML. Подходит, когда нужны выделенные GPU‑инстансы с простым SSH‑доступом, постоянными файловыми системами или высокопроизводительные многонодные кластеры для масштабного обучения. |
| [**llava**](/docs/user-guide/skills/optional/mlops/mlops-llava) | Большой языковой и визуальный помощник. Позволяет выполнять визуальное инструктивное дообучение и вести диалоги на основе изображений. Комбинирует визуальный энкодер CLIP с языковыми моделями Vicuna/LLaMA. Поддерживает многовопросные чат‑сессии с изображениями, визуальные вопросы‑ответы и инструктивные задачи. |
| [**modal-serverless-gpu**](/docs/user-guide/skills/optional/mlops/mlops-modal) | Серверлесс‑GPU облачная платформа для запуска ML‑нагрузок. Подходит, когда нужен доступ к GPU по запросу без управления инфраструктурой, развертывание ML‑моделей как API или запуск пакетных задач с автоматическим масштабированием. |
| [**nemo-curator**](/docs/user-guide/skills/optional/mlops/mlops-nemo-curator) | GPU‑ускоренная подготовка данных для обучения LLM. Поддерживает текст, изображения, видео и аудио. Функции: нечёткое дедуплицирование (16× быстрее), фильтрация качества (30+ эвристик), семантическое дедуплицирование, редактирование PII, обнаружение NSFW. Масштабируется на несколько GPU. |
| [**outlines**](/docs/user-guide/skills/optional/mlops/mlops-inference-outlines) | Outlines: структурированная генерация LLM в формате JSON, regex и Pydantic. |
| [**peft-fine-tuning**](/docs/user-guide/skills/optional/mlops/mlops-peft) | Параметр‑эффективное дообучение LLM с использованием LoRA, QLoRA и более 25 методов. Применяется, когда нужно дообучать большие модели (7 B‑70 B) при ограниченной памяти GPU, обучать < 1 % параметров с минимальной потерей точности или использовать несколько адаптеров. |
| [**pinecone**](/docs/user-guide/skills/optional/mlops/mlops-pinecone) | Управляемая векторная база данных для продакшн‑AI‑приложений. Полностью управляемая, авто‑масштабируемая, с гибридным поиском (плотный + разреженный), фильтрацией по метаданным и пространствами имён. Низкая задержка (<100 ms p95). Используется для продакшн‑RAG, рекомендаций и пр. |
| [**pytorch-fsdp**](/docs/user-guide/skills/optional/mlops/mlops-pytorch-fsdp) | Экспертные рекомендации по обучению Fully Sharded Data Parallel в PyTorch FSDP — шардинг параметров, смешанная точность, выгрузка на CPU, FSDP2. |
| [**pytorch-lightning**](/docs/user-guide/skills/optional/mlops/mlops-pytorch-lightning) | Высокоуровневый фреймворк PyTorch с классом Trainer, автоматическим распределённым обучением (DDP/FSDP/DeepSpeed), системой callbacks и минимальным шаблонным кодом. Масштабируется от ноутбука до суперкомпьютера без изменения кода. Подходит, когда нужен чистый цикл обучения. |
| [**qdrant-vector-search**](/docs/user-guide/skills/optional/mlops/mlops-qdrant) | Высокопроизводительный движок векторного поиска для RAG и семантического поиска. Применяется при построении продакшн‑RAG‑систем, требующих быстрого поиска ближайших соседей, гибридного поиска с фильтрацией или масштабируемого векторного хранилища на базе Rust. |
| [**sparse-autoencoder-training**](/docs/user-guide/skills/optional/mlops/mlops-saelens) | Руководство по обучению и анализу Sparse Autoencoders (SAE) с помощью SAELens для разложения активаций нейронных сетей на интерпретируемые признаки. Полезно при поиске интерпретируемых признаков, анализе суперпозиции или изучении внутренних представлений моделей. |
| [**simpo-training**](/docs/user-guide/skills/optional/mlops/mlops-simpo) | Simple Preference Optimization для выравнивания LLM. Альтернатива DPO без референсной модели с лучшей производительностью (+6.4 пт на AlpacaEval 2.0). Более эффективна, чем DPO. Применяется для выравнивания по предпочтениям, когда нужен упрощённый подход. |
| [**slime-rl-training**](/docs/user-guide/skills/optional/mlops/mlops-slime) | Руководство по пост‑обучению LLM с помощью RL в рамках slime — фреймворка Megatron + SGLang. Подходит для обучения моделей GLM, реализации пользовательских пайплайнов генерации данных или тесной интеграции Megatron‑LM для масштабирования RL. |
| [**stable-diffusion-image-generation**](/docs/user-guide/skills/optional/mlops/mlops-stable-diffusion) | Современная генерация изображений из текста с моделями Stable Diffusion через HuggingFace Diffusers. Используется для создания изображений по текстовым подсказкам, трансформации изображений, inpainting и построения кастомных диффузионных пайплайнов. |
| [**tensorrt-llm**](/docs/user-guide/skills/optional/mlops/mlops-tensorrt-llm) | Оптимизирует инференс LLM с помощью NVIDIA TensorRT для максимальной пропускной способности и минимальной задержки. Применяется в продакшн‑развёртывании на GPU NVIDIA (A100/H100), когда требуется ускорение инференса в 10‑100× по сравнению с PyTorch, или при обслуживании моделей с квантизацией. |
| [**distributed-llm-pretraining-torchtitan**](/docs/user-guide/skills/optional/mlops/mlops-torchtitan) | Нативное распределённое предобучение LLM в PyTorch с использованием torchtitan и 4‑мерного параллелизма (FSDP2, TP, PP, CP). Подходит для предобучения Llama 3.1, DeepSeek V3 или кастомных моделей в масштабе от 8 до 512+ GPU с Float8, torch.compile и распределённым обучением. |
| [**fine-tuning-with-trl**](/docs/user-guide/skills/optional/mlops/mlops-training-trl-fine-tuning) | TRL: SFT, DPO, PPO, GRPO, моделирование наград для RLHF LLM. |
| [**unsloth**](/docs/user-guide/skills/optional/mlops/mlops-training-unsloth) | Unsloth: 2‑5× быстрее LoRA/QLoRA‑дообучения, требует меньше VRAM. |
| [**whisper**](/docs/user-guide/skills/optional/mlops/mlops-whisper) | Универсальная модель распознавания речи от OpenAI. Поддерживает 99 языков, транскрипцию, перевод на английский и определение языка. Шесть размеров модели от tiny (39 M параметров) до large (1550 M параметров). Применяется для speech‑to‑text, подкастов и пр. |
## продуктивность

| Skill | Описание |
|-------|----------|
| [**canvas**](/docs/user-guide/skills/optional/productivity/productivity-canvas) | Интеграция с Canvas LMS — получение зачисленных курсов и заданий с использованием аутентификации токеном API. |
| [**here.now**](/docs/user-guide/skills/optional/productivity/productivity-here-now) | Публикация статических сайтов на &#123;slug&#125;.here.now и хранение приватных файлов в облачных дисках для передачи от агента к агенту. |
| [**memento-flashcards**](/docs/user-guide/skills/optional/productivity/productivity-memento-flashcards) | Система флешкарт с интервальным повторением. Создание карточек из фактов или текста, общение с флешкартами с помощью ответов свободного текста, которые оценивает агент, генерация викторин из транскриптов YouTube, просмотр карточек, срок которых наступил, с адаптивным расписанием, и экспорт/импорт… |
| [**shop-app**](/docs/user-guide/skills/optional/productivity/productivity-shop-app) | Shop.app: поиск товаров, отслеживание заказов, возвраты, повторный заказ. |
| [**shopify**](/docs/user-guide/skills/optional/productivity/productivity-shopify) | GraphQL‑API Shopify Admin и Storefront через curl. Товары, заказы, покупатели, инвентарь, метаполя. |
| [**siyuan**](/docs/user-guide/skills/optional/productivity/productivity-siyuan) | API SiYuan Note для поиска, чтения, создания и управления блоками и документами в саморазмещённой базе знаний через curl. |
| [**telephony**](/docs/user-guide/skills/optional/productivity/productivity-telephony) | Предоставление Hermes телефонных возможностей без изменения ядра инструмента. Выделение и сохранение номера Twilio, отправка и получение SMS/MMS, прямые звонки и исходящие AI‑звонки через Bland.ai или Vapi. |
## research

| Skill | Description |
|-------|-------------|
| [**bioinformatics**](/docs/user-guide/skills/optional/research/research-bioinformatics) | Шлюз к более чем 400 биоинформатическим навыкам от bioSkills и ClawBio. Охватывает геномику, транскриптомику, одноклеточные исследования, определение вариантов, фармакогеномику, метагеномику, структурную биологию и многое другое. Получает специализированные справочные материалы по домену… |
| [**darwinian-evolver**](/docs/user-guide/skills/optional/research/research-darwinian-evolver) | Эволюция подсказок/regex/SQL/кода с помощью цикла эволюции Imbue. |
| [**domain-intel**](/docs/user-guide/skills/optional/research/research-domain-intel) | Пассивная разведка домена с использованием стандартной библиотеки Python. Поиск поддоменов, проверка SSL‑сертификатов, WHOIS‑запросы, DNS‑записи, проверка доступности домена и массовый анализ нескольких доменов. Не требуются API‑ключи. |
| [**drug-discovery**](/docs/user-guide/skills/optional/research/research-drug-discovery) | Помощник в фармацевтических исследованиях для рабочих процессов открытого поиска лекарств. Поиск биоактивных соединений в ChEMBL, расчёт «лекарственной пригодности» (Lipinski Ro5, QED, TPSA, синтетическая доступность), поиск взаимодействий лекарств через OpenFDA, интерпретация ADMET… |
| [**duckduckgo-search**](/docs/user-guide/skills/optional/research/research-duckduckgo-search) | Бесплатный веб‑поиск через DuckDuckGo — текст, новости, изображения, видео. Не нужен API‑ключ. Предпочитай CLI `ddgs`, если он установлен; используй библиотеку Python DDGS только после проверки доступности `ddgs` в текущем окружении. |
| [**gitnexus-explorer**](/docs/user-guide/skills/optional/research/research-gitnexus-explorer) | Индексация кодовой базы с помощью GitNexus и предоставление интерактивного графа знаний через веб‑интерфейс + туннель Cloudflare. |
| [**osint-investigation**](/docs/user-guide/skills/optional/research/research-osint-investigation) | Фреймворк OSINT‑расследований публичных записей — SEC EDGAR, контракты USAspending, лоббирование в Сенате, санкции OFAC, утечки ICIJ, записи о недвижимости NYC (ACRIS), реестры OpenCorporates, судебные записи CourtListener, Wayback… |
| [**parallel-cli**](/docs/user-guide/skills/optional/research/research-parallel-cli) | Опциональный навык поставщика для Parallel CLI — агентно‑нативный веб‑поиск, извлечение, глубокие исследования, обогащение, FindAll и мониторинг. Предпочитай вывод в JSON и безинтерактивные потоки. |
| [**qmd**](/docs/user-guide/skills/optional/research/research-qmd) | Поиск по личным базам знаний, заметкам, документам и стенограммам встреч локально с помощью qmd — гибридного движка поиска с BM25, векторным поиском и пере‑ранжированием LLM. Поддерживает CLI и интеграцию с MCP. |
| [**scrapling**](/docs/user-guide/skills/optional/research/research-scrapling) | Веб‑скрейпинг с Scrapling — HTTP‑запросы, скрытая автоматизация браузера, обход Cloudflare и паукообразный обход через CLI и Python. |
| [**searxng-search**](/docs/user-guide/skills/optional/research/research-searxng-search) | Бесплатный мета‑поиск через SearXNG — агрегирует результаты более чем 70 поисковых систем. Самостоятельно размещаемый или публичный экземпляр. Не нужен API‑ключ. Автоматически переходит к запасному варианту, когда набор инструментов веб‑поиска недоступен. |
## security

| Skill | Description |
|-------|-------------|
| [**1password**](/docs/user-guide/skills/optional/security/security-1password) | Настройка и использование 1Password CLI (`op`). Применяется при установке CLI, включении интеграции с настольным приложением, входе в систему и чтении/внедрении секретов для команд. |
| [**oss-forensics**](/docs/user-guide/skills/optional/security/security-oss-forensics) | Исследование цепочки поставок, восстановление доказательств и форензика репозиториев GitHub. Включает восстановление удалённых коммитов, обнаружение принудительных push‑ей, извлечение IOC, сбор доказательств из нескольких источников, формирование и валидацию гипотез и … |
| [**sherlock**](/docs/user-guide/skills/optional/security/security-sherlock) | OSINT‑поиск имён пользователей более чем в 400 социальных сетях. Поиск учётных записей в соцсетях по имени пользователя. |
| [**web-pentest**](/docs/user-guide/skills/optional/security/security-web-pentest) | Авторизованное тестирование на проникновение веб‑приложений — разведка, анализ уязвимостей, доказательная эксплуатация и профессиональная отчётность. Применяет методологию Шеннона «No Exploit, No Report» с жёсткими ограничениями по области, авторизации … |
## разработка программного обеспечения

| Навык | Описание |
|-------|----------|
| [**code-wiki**](/docs/user-guide/skills/optional/software-development/software-development-code-wiki) | Генерируй wiki‑документацию + диаграммы Mermaid для любой кодовой базы. |
| [**rest-graphql-debug**](/docs/user-guide/skills/optional/software-development/software-development-rest-graphql-debug) | Отлаживай REST/GraphQL API: коды статусов, аутентификацию, схемы, воспроизведение запросов. |
## веб-разработка

| Навык | Описание |
|-------|----------|
| [**page-agent**](/docs/user-guide/skills/optional/web-development/web-development-page-agent) | Встраивает alibaba/page-agent в твоё веб‑приложение — чистый JavaScript‑агент с GUI, который поставляется в виде единственного тега `<script>` или npm‑пакета и позволяет пользователям твоего сайта управлять UI с помощью естественного языка («кликни вход, заполни имя пользователя…») |
## Добавление необязательных навыков

Чтобы добавить новый необязательный навык в репозиторий:

1. Создай директорию `optional-skills/<category>/<skill-name>/`
2. Добавь файл `SKILL.md` со стандартным frontmatter (name, description, version, author)
3. Помести любые вспомогательные файлы в подкаталоги `references/`, `templates/` или `scripts/`
4. Отправь pull‑request — навык появится в этом каталоге и получит собственную страницу документации после слияния