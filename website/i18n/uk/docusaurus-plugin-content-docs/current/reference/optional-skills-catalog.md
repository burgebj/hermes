---
sidebar_position: 9
title: "Необов'язковий Skills Catalog"
description: "Офіційні додаткові навички, що постачаються з hermes-agent — встанови за допомогою `hermes skills install official/<category>/<skill>`"
---

# Каталог необов’язкових навичок

Необов’язкові навички постачаються разом з hermes-agent у каталозі `optional-skills/`, але **не активні за замовчуванням**. Встанови їх явно:

```bash
hermes skills install official/<category>/<skill>
```

Наприклад:

```bash
hermes skills install official/blockchain/solana
hermes skills install official/mlops/flash-attention
```

Кожна навичка нижче посилається на окрему сторінку з повним визначенням, налаштуванням та використанням.

Щоб видалити:

```bash
hermes skills uninstall <skill-name>
```
## автономні-агенти-ШІ

| Навичка | Опис |
|-------|-------------|
| [**antigravity-cli**](/docs/user-guide/skills/optional/autonomous-ai-agents/autonomous-ai-agents-antigravity-cli) | Керувати Antgravity CLI (agy): плагіни, автентифікація, пісочниця. |
| [**blackbox**](/docs/user-guide/skills/optional/autonomous-ai-agents/autonomous-ai-agents-blackbox) | Делегувати завдання кодування агенту Blackbox AI CLI. Багатомодельний агент зі вбудованим суддею, який виконує завдання через кілька LLM і обирає найкращий результат. Потрібен blackbox CLI та ключ API Blackbox AI. |
| [**grok**](/docs/user-guide/skills/optional/autonomous-ai-agents/autonomous-ai-agents-grok) | Делегувати кодування xAI Grok Build CLI (фічі, PR). |
| [**honcho**](/docs/user-guide/skills/optional/autonomous-ai-agents/autonomous-ai-agents-honcho) | Налаштувати та використовувати пам'ять Honcho з Hermes — крос‑сесійне моделювання користувачів, ізоляція багатьох профілів, конфігурація спостережень, діалектичне міркування, підсумки сесій та контроль бюджету контексту. Використовуй під час налаштування Honcho, усунення проблем тощо. |
| [**openhands**](/docs/user-guide/skills/optional/autonomous-ai-agents/autonomous-ai-agents-openhands) | Делегувати кодування OpenHands CLI (модель‑агностичний, LiteLLM). |
## blockchain

| Skill | Description |
|-------|-------------|
| [**evm**](/docs/user-guide/skills/optional/blockchain/blockchain-evm) | Клієнт EVM лише для читання: гаманці, токени, газ на 8 ланцюгах. |
| [**hyperliquid**](/docs/user-guide/skills/optional/blockchain/blockchain-hyperliquid) | Дані ринку Hyperliquid, історія облікового запису, перегляд торгів. |
| [**solana**](/docs/user-guide/skills/optional/blockchain/blockchain-solana) | Запит даних блокчейну Solana з цінами в USD — баланси гаманців, портфелі токенів з їх вартістю, деталі транзакцій, NFT, виявлення «китів» та живі статистики мережі. Використовує Solana RPC + CoinGecko. API‑ключ не потрібен. |
## communication

| Skill | Description |
|-------|-------------|
| [**one-three-one-rule**](/docs/user-guide/skills/optional/communication/communication-one-three-one-rule) | Структурована рамка прийняття рішень для технічних пропозицій та аналізу компромісів. Коли користувач стикається з вибором між кількома підходами (рішення архітектури, вибір інструменту, стратегії рефакторингу, шляхи міграції), ця навичка … |
## креатив

| Skill | Description |
|-------|-------------|
| [**blender-mcp**](/docs/user-guide/skills/optional/creative/creative-blender-mcp) | Керуй Blender безпосередньо з Hermes через socket‑з’єднання з аддоном **blender-mcp**. Створюй 3D‑об’єкти, матеріали, анімації та виконуй довільний код Blender Python (bpy). Використовуй, коли користувач хоче створити або змінити будь‑що в Blender. |
| [**concept-diagrams**](/docs/user-guide/skills/optional/creative/creative-concept-diagrams) | Генеруй плоскі, мінімалістичні SVG‑діаграми, адаптовані до світлого/темного режиму, у вигляді окремих HTML‑файлів, використовуючи уніфіковану освітню візуальну мову з 9 семантичними кольоровими градієнтами, типографікою у реченні та автоматичним темним режимом. Найкраще підходить для освітніх та інших проєктів. |
| [**hyperframes**](/docs/user-guide/skills/optional/creative/creative-hyperframes) | Створюй HTML‑базовані відео‑композиції, анімовані титульні картки, соціальні оверлеї, відео з субтитрами та «говорячою головою», аудіо‑реактивну графіку та шейдерні переходи за допомогою **HyperFrames**. HTML є джерелом правди для відео. Використовуй, коли користувач хоче створити подібний контент. |
| [**kanban-video-orchestrator**](/docs/user-guide/skills/optional/creative/creative-kanban-video-orchestrator) | Плануй, налаштовуй та моніторь багатоканальний відео‑виробничий конвеєр, підтримуваний **Hermes Kanban**. Використовуй, коли користувач хоче створити будь‑яке відео — художній фільм, продуктове/маркетингове, музичне відео, пояснювальне, ASCII/термінальне мистецтво, абстрактне/генеративне тощо. |
| [**meme-generation**](/docs/user-guide/skills/optional/creative/creative-meme-generation) | Генеруй реальні мем‑зображення, вибираючи шаблон і накладаючи текст за допомогою **Pillow**. Створює фактичні .png‑файли мемів. |
## devops

| Skill | Опис |
|-------|------|
| [**inference-sh-cli**](/docs/user-guide/skills/optional/devops/devops-cli) | Run 150+ AI apps via inference.sh CLI (infsh) — генерація зображень, створення відео, LLMs, пошук, 3D, соціальна автоматизація. Використовує інструмент терміналу. Тригери: inference.sh, infsh, AI‑додатки, flux, veo, генерація зображень, генерація відео, seedrea… |
| [**docker-management**](/docs/user-guide/skills/optional/devops/devops-docker-management) | Керує Docker‑контейнерами, образами, томами, мережами та Compose‑стеками — операції життєвого циклу, налагодження, очищення та оптимізація Dockerfile. |
| [**pinggy-tunnel**](/docs/user-guide/skills/optional/devops/devops-pinggy-tunnel) | Тунелі localhost без встановлення через SSH за допомогою Pinggy. |
| [**watchers**](/docs/user-guide/skills/optional/devops/devops-watchers) | Опитування RSS, JSON‑API та GitHub з видаленням дублікатів за допомогою водяного знака. |
## dogfood

| Skill | Description |
|-------|-------------|
| [**adversarial-ux-test**](/docs/user-guide/skills/optional/dogfood/dogfood-adversarial-ux-test) | Рольова гра в ролі найскладнішого, технічно‑неприйнятливого користувача твого продукту. Переглядай додаток як ця персона, знаходь усі проблеми UX, а потім фільтруй скарги через шар прагматизму, щоб відокремити реальні проблеми від шуму. Створює практичні тикети… |
## email

| Skill | Description |
|-------|-------------|
| [**agentmail**](/docs/user-guide/skills/optional/email/email-agentmail) | Надати агенту власну виділену скриньку через AgentMail. Надсилати, отримувати та керувати електронною поштою автономно, використовуючи адреси електронної пошти, що належать агенту (наприклад hermes-agent@agentmail.to). |
## finance

| Навичка | Опис |
|-------|------|
| [**3-statement-model**](/docs/user-guide/skills/optional/finance/finance-3-statement-model) | Створюй повністю інтегровані 3‑заявкові моделі (IS, BS, CF) в Excel з графіками оборотного капіталу, розрахунками D&A, графіком боргу та підключеннями, які забезпечують узгодженість готівки та нерозподіленого прибутку. Працює в парі з **excel-author**. |
| [**comps-analysis**](/docs/user-guide/skills/optional/finance/finance-comps-analysis) | Створюй аналіз порівнянних компаній в Excel — операційні метрики, мультиплікатори оцінки, статистичне порівняння з групами аналогів. Працює в парі з **excel-author**. Використовуй для оцінки публічних компаній, ціноутворення IPO, галузевого бенчмаркінгу або виявлення аномалій. |
| [**dcf-model**](/docs/user-guide/skills/optional/finance/finance-dcf-model) | Створюй інституційної якості DCF‑моделі оцінки в Excel — прогнози доходів, побудова FCF, WACC, остаточна вартість, сценарії Bear/Base/Bull, таблиці чутливості 5×5. Працює в парі з **excel-author**. Використовуй для аналізу внутрішньої вартості акцій. |
| [**excel-author**](/docs/user-guide/skills/optional/finance/finance-excel-author) | Створюй аудиторські Excel‑книги без інтерфейсу за допомогою **openpyxl** — конвенції кольорів клітинок (blue/black/green), формули замість жорстких значень, іменовані діапазони, перевірки балансу, таблиці чутливості. Використовуй для фінансових моделей, аудиторських виводів, звірок. |
| [**lbo-model**](/docs/user-guide/skills/optional/finance/finance-lbo-model) | Створюй моделі викупу з використанням кредитного плеча в Excel — джерела та використання, графік боргу, погашення готівки, вихідний мультиплікатор, чутливість IRR/MOIC. Працює в парі з **excel-author**. Використовуй для скринінгу PE, оцінки спонсорських кейсів або ілюстративного LBO у презентації. |
| [**merger-model**](/docs/user-guide/skills/optional/finance/finance-merger-model) | Створюй моделі акреції/дилюції (злиття) в Excel — про‑формальний P&L, синергії, мікс фінансування, вплив на EPS. Працює в парі з **excel-author**. Використовуй для M&A‑презентацій, матеріалів правління або оцінки угод. |
| [**pptx-author**](/docs/user-guide/skills/optional/finance/finance-pptx-author) | Створюй PowerPoint‑презентації без інтерфейсу за допомогою **python-pptx**. Працює в парі з **excel-author** для презентацій, підкріплених моделями, де кожне число прив’язане до клітини книги. Використовуй для презентацій, меморандумів IC, нотаток про прибутки. |
| [**stocks**](/docs/user-guide/skills/optional/finance/finance-stocks) | Котирування акцій, історія, пошук, порівняння, криптовалюти через Yahoo. |
## health

| Skill | Description |
|-------|-------------|
| [**fitness-nutrition**](/docs/user-guide/skills/optional/health/health-fitness-nutrition) | Планувальник тренувань у спортзалі та трекер харчування. Пошук понад 690 вправ за м’язами, обладнанням або категорією через wger. Перегляд макронутрієнтів і калорій для понад 380 000 продуктів через USDA FoodData Central. Обчислення ІМТ, загальної добової енерговитрати (TDEE), максимуму однієї повторення, розподілу макросів та інших параметрів тіла… |
| [**neuroskill-bci**](/docs/user-guide/skills/optional/health/health-neuroskill-bci) | Підключення до запущеного інстансу NeuroSkill та включення в реальному часі когнітивного та емоційного стану користувача (фокус, розслаблення, настрій, когнітивне навантаження, сонливість, частота серцебиття, HRV, стадії сну та 40+ отриманих EXG‑балів) у відповіді… |
## mcp

| Skill | Description |
|-------|-------------|
| [**fastmcp**](/docs/user-guide/skills/optional/mcp/mcp-fastmcp) | Будуй, тестуй, перевіряй, встановлюй та розгортай сервери MCP за допомогою FastMCP на Python. Використовуй, коли створюєш новий сервер MCP, обгортаєш API або базу даних як інструменти MCP, відкриваєш ресурси чи підказки, або готуєш сервер FastMCP для Claude Code, Cur… |
| [**mcporter**](/docs/user-guide/skills/optional/mcp/mcp-mcporter) | Використовуй CLI `mcporter` для переліку, налаштування, автентифікації та виклику серверів/інструментів MCP безпосередньо (HTTP або stdio), включаючи ad‑hoc сервери, редагування конфігурації та генерацію CLI/типів. |
## міграція

| Skill | Опис |
|-------|------|
| [**openclaw-migration**](/docs/user-guide/skills/optional/migration/migration-openclaw-migration) | Мігрирує налаштування користувача OpenClaw у Hermes Agent. Імпортує сумісні з Hermes пам’яті, `SOUL.md`, білий список дозволених команд, навички користувача та вибрані ресурси робочого простору з `~/.openclaw`, після чого звітує про те, що не вдалося мігрувати… |
## mlops
| Skill | Опис |
|-------|------|
| [**huggingface-accelerate**](/docs/user-guide/skills/optional/mlops/mlops-accelerate) | Найпростіший API розподіленого навчання. 4 рядки коду, щоб додати розподілену підтримку до будь‑якого скрипту PyTorch. Уніфікований API для DeepSpeed/FSDP/Megatron/DDP. Автоматичне розміщення на пристрої, змішана точність (FP16/BF16/FP8). Інтерактивна конфігурація, один запуск команди. |
| [**axolotl**](/docs/user-guide/skills/optional/mlops/mlops-training-axolotl) | Axolotl: YAML‑настройка LLM (LoRA, DPO, GRPO). |
| [**chroma**](/docs/user-guide/skills/optional/mlops/mlops-chroma) | Відкритий embedding‑база даних для AI‑застосунків. Зберігає embeddings та метадані, виконує векторний і повнотекстовий пошук, фільтрацію за метаданими. Простий 4‑функціональний API. Масштабується від ноутбуків до виробничих кластерів. Використовується для семантичного пошуку, RAG тощо. |
| [**clip**](/docs/user-guide/skills/optional/mlops/mlops-clip) | Модель OpenAI, що поєднує зір і мову. Дозволяє zero‑shot класифікацію зображень, зіставлення зображення‑тексту та крос‑модальний пошук. Навчена на 400 млн пар зображення‑текст. Використовується для пошуку зображень, модерації контенту або завдань «зір‑мова». |
| [**faiss**](/docs/user-guide/skills/optional/mlops/mlops-faiss) | Бібліотека Facebook для ефективного пошуку схожості та кластеризації густих векторів. Підтримує мільярди векторів, прискорення на GPU та різні типи індексів (Flat, IVF, HNSW). Використовується для швидкого k‑NN пошуку, масштабного векторного отримання тощо. |
| [**optimizing-attention-flash**](/docs/user-guide/skills/optional/mlops/mlops-flash-attention) | Оптимізує увагу трансформерів за допомогою Flash Attention для 2‑4× прискорення та 10‑20× зменшення використання пам’яті. Використовується під час навчання/запуску трансформерів з довгими послідовностями (>512 токенів), при проблемах пам’яті GPU або коли потрібна швидша обробка. |
| [**guidance**](/docs/user-guide/skills/optional/mlops/mlops-guidance) | Керує виводом LLM за допомогою regex та граматик, гарантує коректний JSON/XML/код, забезпечує структуровані формати та створює багатокрокові робочі процеси за допомогою Guidance — фреймворку обмеженого генерування від Microsoft Research. |
| [**huggingface-tokenizers**](/docs/user-guide/skills/optional/mlops/mlops-huggingface-tokenizers) | Швидкі токенізатори, оптимізовані для досліджень та продакшну. Реалізація на Rust токенізує 1 GB за <20 секунд. Підтримує алгоритми BPE, WordPiece та Unigram. Навчайте власні словники, відстежуйте вирівнювання, працюйте з паддінгом/триманням. Інтегрується з 🤗 Transformers. |
| [**instructor**](/docs/user-guide/skills/optional/mlops/mlops-instructor) | Витягує структуровані дані з відповідей LLM з валідацією Pydantic, автоматично повторює невдалі витяги, парсить складний JSON з типобезпекою та транслює часткові результати за допомогою Instructor — випробуваної бібліотеки структурованого виводу. |
| [**lambda-labs-gpu-cloud**](/docs/user-guide/skills/optional/mlops/mlops-lambda-labs) | Резервовані та on‑demand GPU‑хмари для навчання та інференсу ML. Використовується, коли потрібні виділені GPU‑інстанси з простим SSH‑доступом, постійними файловими системами або високопродуктивними мульти‑нодовими кластерами для масштабного навчання. |
| [**llava**](/docs/user-guide/skills/optional/mlops/mlops-llava) | Великий мовний та візуальний асистент. Дозволяє візуальне інструкційне налаштування та розмови на основі зображень. Поєднує CLIP‑візуальний енкодер з мовними моделями Vicuna/LLaMA. Підтримує багатокроковий чат з зображеннями, візуальне питання‑відповідь та інструкційні діалоги. |
| [**modal-serverless-gpu**](/docs/user-guide/skills/optional/mlops/mlops-modal) | Безсерверна GPU‑хмара для запуску ML‑навантажень. Використовується, коли потрібен on‑demand GPU‑доступ без управління інфраструктурою, розгортання ML‑моделей як API або запуск пакетних завдань з автоматичним масштабуванням. |
| [**nemo-curator**](/docs/user-guide/skills/optional/mlops/mlops-nemo-curator) | GPU‑прискорене формування даних для навчання LLM. Підтримує текст, зображення, відео, аудіо. Функції: нечітке дедуплікування (16× швидше), фільтрація якості (30+ евристик), семантичне дедуплікування, редагування PII, виявлення NSFW. Масштабується на кілька GPU. |
| [**outlines**](/docs/user-guide/skills/optional/mlops/mlops-inference-outlines) | Outlines: структурована генерація LLM у форматах JSON, regex, Pydantic. |
| [**peft-fine-tuning**](/docs/user-guide/skills/optional/mlops/mlops-peft) | Параметр‑ефективне донастроювання LLM за допомогою LoRA, QLoRA та 25+ методів. Використовується, коли треба донастроювати великі моделі (7B‑70B) з обмеженою пам’яттю GPU, коли потрібно навчити <1 % параметрів з мінімальною втратою точності або для мульти‑адаптерних сценаріїв. |
| [**pinecone**](/docs/user-guide/skills/optional/mlops/mlops-pinecone) | Керована векторна база даних для продакшн AI‑застосунків. Повністю керована, авто‑масштабування, гібридний пошук (густий + розріджений), фільтрація метаданих, простори імен. Низька затримка (<100 ms p95). Використовується для продакшн RAG, рекомендаційних систем тощо. |
| [**pytorch-fsdp**](/docs/user-guide/skills/optional/mlops/mlops-pytorch-fsdp) | Експертна підтримка Fully Sharded Data Parallel навчання з PyTorch FSDP — шардинг параметрів, змішана точність, відвантаження на CPU, FSDP2. |
| [**pytorch-lightning**](/docs/user-guide/skills/optional/mlops/mlops-pytorch-lightning) | Високорівневий фреймворк PyTorch з класом Trainer, автоматичним розподіленим навчанням (DDP/FSDP/DeepSpeed), системою callbacks та мінімальним шаблоном коду. Масштабується від ноутбука до суперкомп’ютера без зміни коду. Використовується, коли потрібні чисті цикли навчання. |
| [**qdrant-vector-search**](/docs/user-guide/skills/optional/mlops/mlops-qdrant) | Високопродуктивний движок векторного пошуку схожості для RAG та семантичного пошуку. Використовується при створенні продакшн RAG‑систем, що потребують швидкого пошуку найближчих сусідів, гібридного пошуку з фільтрацією або масштабованого зберігання векторів на Rust‑базі. |
| [**sparse-autoencoder-training**](/docs/user-guide/skills/optional/mlops/mlops-saelens) | Надає рекомендації щодо навчання та аналізу Sparse Autoencoders (SAE) за допомогою SAELens для розкладання активацій нейронних мереж на інтерпретовані ознаки. Використовується при виявленні інтерпретованих ознак, аналізі суперпозиції або дослідженні внутрішньої структури моделей. |
| [**simpo-training**](/docs/user-guide/skills/optional/mlops/mlops-simpo) | Simple Preference Optimization для вирівнювання LLM. Альтернатива DPO без референсної моделі з кращою продуктивністю (+6.4 балів на AlpacaEval 2.0). Ефективніше за DPO. Використовується для вирівнювання за уподобаннями, коли потрібен простий підхід. |
| [**slime-rl-training**](/docs/user-guide/skills/optional/mlops/mlops-slime) | Надає рекомендації щодо пост‑тренування LLM за допомогою RL у slime — фреймворку Megatron+SGLang. Використовується при навчанні моделей GLM, створенні кастомних воркфлоу генерації даних або коли потрібна тісна інтеграція Megatron‑LM для масштабування RL. |
| [**stable-diffusion-image-generation**](/docs/user-guide/skills/optional/mlops/mlops-stable-diffusion) | Сучасна генерація текст‑у‑зображення за допомогою моделей Stable Diffusion через HuggingFace Diffusers. Використовується для створення зображень за текстовими підказками, трансляції зображення‑у‑зображення, інпейнтингу або побудови кастомних дифузійних пайплайнів. |
| [**tensorrt-llm**](/docs/user-guide/skills/optional/mlops/mlops-tensorrt-llm) | Оптимізує інференс LLM за допомогою NVIDIA TensorRT для максимальної пропускної здатності та мінімальної затримки. Використовується для продакшн розгортання на GPU NVIDIA (A100/H100), коли потрібен 10‑100× швидший інференс, ніж у PyTorch, або для сервісу моделей з квантизацією. |
| [**distributed-llm-pretraining-torchtitan**](/docs/user-guide/skills/optional/mlops/mlops-torchtitan) | Забезпечує розподілене предтренування LLM у PyTorch за допомогою torchtitan з 4‑D паралелізмом (FSDP2, TP, PP, CP). Використовується при предтренуванні Llama 3.1, DeepSeek V3 або кастомних моделей у масштабі від 8 до 512+ GPU з Float8, torch.compile та розподіленим навчанням. |
| [**fine-tuning-with-trl**](/docs/user-guide/skills/optional/mlops/mlops-training-trl-fine-tuning) | TRL: SFT, DPO, PPO, GRPO, reward modeling для RLHF LLM. |
| [**unsloth**](/docs/user-guide/skills/optional/mlops/mlops-training-unsloth) | Unsloth: 2‑5× швидше донастроювання LoRA/QLoRA, менше VRAM. |
|
| [**whisper**](/docs/user-guide/skills/optional/mlops/mlops-whisper) | Загальна модель розпізнавання мови від OpenAI. Підтримує 99 мов, транскрипцію, переклад на англійську та ідентифікацію мови. Шість розмірів моделі — від **tiny** (39 М параметрів) до **large** (1550 М параметрів). Використовуй для перетворення мови в текст, подкастів тощо. |
## продуктивність

| Skill | Description |
|-------|-------------|
| [**canvas**](/docs/user-guide/skills/optional/productivity/productivity-canvas) | Інтеграція Canvas LMS — отримання курсів та завдань, на які записано, за допомогою автентифікації токеном API. |
| [**here.now**](/docs/user-guide/skills/optional/productivity/productivity-here-now) | Публікація статичних сайтів на \{slug\}.here.now та зберігання приватних файлів у хмарних дисках для передачі між агентами. |
| [**memento-flashcards**](/docs/user-guide/skills/optional/productivity/productivity-memento-flashcards) | Система карток з інтервальним повторенням. Створюй картки з фактів або тексту, спілкуйся з картками, використовуючи вільний текст, оцінюваний агентом, генеруй вікторини з транскриптів YouTube, переглядай прострочені картки з адаптивним плануванням та експортуй/імпортуй… |
| [**shop-app**](/docs/user-guide/skills/optional/productivity/productivity-shop-app) | Shop.app: пошук продуктів, відстеження замовлень, повернення, повторне замовлення. |
| [**shopify**](/docs/user-guide/skills/optional/productivity/productivity-shopify) | GraphQL API Shopify Admin та Storefront через curl. Продукти, замовлення, клієнти, інвентар, метаполя. |
| [**siyuan**](/docs/user-guide/skills/optional/productivity/productivity-siyuan) | API SiYuan Note для пошуку, читання, створення та керування блоками і документами у самохостованій базі знань через curl. |
| [**telephony**](/docs/user-guide/skills/optional/productivity/productivity-telephony) | Надай Hermes можливості телефонії без змін у базових інструментах. Забезпеч номер Twilio та збережи його, надсилай і отримуй SMS/MMS, здійснюй прямі дзвінки та роби вихідні дзвінки, керовані ШІ, через Bland.ai або Vapi. |
## дослідження

| Skill | Опис |
|-------|------|
| [**bioinformatics**](/docs/user-guide/skills/optional/research/research-bioinformatics) | Шлюз до 400+ навичок біоінформатики від bioSkills та ClawBio. Охоплює геноміку, транскриптоміку, одноклітинний аналіз, виявлення варіантів, фармакогеноміку, метагеноміку, структурну біологію та інше. Отримує доменно‑специфічний референсний матеріал… |
| [**darwinian-evolver**](/docs/user-guide/skills/optional/research/research-darwinian-evolver) | Еволюція підказок/regex/SQL/коду за допомогою циклу еволюції Imbue. |
| [**domain-intel**](/docs/user-guide/skills/optional/research/research-domain-intel) | Пасивна розвідка домену за допомогою Python stdlib. Виявлення піддоменів, інспекція SSL‑сертифікатів, WHOIS‑запити, DNS‑записи, перевірка доступності домену та масовий аналіз кількох доменів. Не потребує API‑ключів. |
| [**drug-discovery**](/docs/user-guide/skills/optional/research/research-drug-discovery) | Асистент фармацевтичних досліджень для процесів відкриття препаратів. Пошук біоактивних сполук у ChEMBL, розрахунок drug‑likeness (Lipinski Ro5, QED, TPSA, synthetic accessibility), пошук взаємодій препарат‑препарат через OpenFDA, інтерпретація ADMET… |
| [**duckduckgo-search**](/docs/user-guide/skills/optional/research/research-duckduckgo-search) | Безкоштовний веб‑пошук через DuckDuckGo — текст, новини, зображення, відео. Не потрібен API‑ключ. Користуйся CLI `ddds`, якщо він встановлений; використовуйте бібліотеку Python DDGS лише після перевірки доступності `ddgs` у поточному середовищі. |
| [**gitnexus-explorer**](/docs/user-guide/skills/optional/research/research-gitnexus-explorer) | Індексує кодову базу за допомогою GitNexus та надає інтерактивний граф знань через веб‑інтерфейс + тунель Cloudflare. |
| [**osint-investigation**](/docs/user-guide/skills/optional/research/research-osint-investigation) | Фреймворк OSINT‑розслідувань за публічними записами — SEC EDGAR, контракти USAspending, лобіювання Сенату, санкції OFAC, витоки ICIJ, записи про нерухомість NYC (ACRIS), реєстри OpenCorporates, судові записи CourtListener, Wayback… |
| [**parallel-cli**](/docs/user-guide/skills/optional/research/research-parallel-cli) | Додаткова навичка від постачальника для Parallel CLI — агентно‑нативний веб‑пошук, екстракція, глибоке дослідження, збагачення, FindAll та моніторинг. Перевага надається JSON‑виводу та не‑інтерактивним потокам. |
| [**qmd**](/docs/user-guide/skills/optional/research/research-qmd) | Пошук у особистих базах знань, нотатках, документах та транскриптах зустрічей локально за допомогою qmd — гібридного рушія пошуку з BM25, векторним пошуком та переранжируванням LLM. Підтримує CLI та інтеграцію з MCP. |
| [**scrapling**](/docs/user-guide/skills/optional/research/research-scrapling) | Веб‑скрапінг за допомогою Scrapling — HTTP‑запити, автоматизація stealth‑браузера, обходи Cloudflare та павукове сканування через CLI та Python. |
| [**searxng-search**](/docs/user-guide/skills/optional/research/research-searxng-search) | Безкоштовний мета‑пошук через SearXNG — агрегує результати з 70+ пошукових систем. Самостійно розгорнуто або використовуйте публічний інстанс. Не потрібен API‑ключ. Автоматично переходить у запасний (варіант), коли інструмент веб‑пошуку недоступний. |
## безпека

| Навичка | Опис |
|-------|------|
| [**1password**](/docs/user-guide/skills/optional/security/security-1password) | Налаштуй та використай 1Password CLI (`op`). Використовуй під час встановлення CLI, підключення десктоп‑додатку, входу в систему та читання/вставки секретів для команд. |
| [**oss-forensics**](/docs/user-guide/skills/optional/security/security-oss-forensics) | Дослідження ланцюжка постачання, відновлення доказів та судово‑експертний аналіз репозиторіїв GitHub. Охоплює відновлення видалених комітів, виявлення примусових пушів, вилучення IOC, збір доказів з кількох джерел, формування/перевірку гіпотез та інше. |
| [**sherlock**](/docs/user-guide/skills/optional/security/security-sherlock) | OSINT‑пошук імен користувачів у більш ніж 400 соціальних мережах. Відшукай облікові записи в соцмережах за іменем користувача. |
| [**web-pentest**](/docs/user-guide/skills/optional/security/security-web-pentest) | Авторизоване тестування веб‑додатків — розвідка, аналіз вразливостей, експлуатація на основі доказів та професійна звітність. Адаптує методологію Шеннона «No Exploit, No Report» з жорсткими обмеженнями щодо сфери, авторизації та інше. |
## software-development

| Skill | Description |
|-------|-------------|
| [**code-wiki**](/docs/user-guide/skills/optional/software-development/software-development-code-wiki) | Генерувати wiki‑документи + діаграми Mermaid для будь‑якої кодової бази. |
| [**rest-graphql-debug**](/docs/user-guide/skills/optional/software-development/software-development-rest-graphql-debug) | Налагоджувати REST/GraphQL API: коди статусу, автентифікація, схеми, відтворення. |
## web-development

| Skill | Опис |
|-------|------|
| [**page-agent**](/docs/user-guide/skills/optional/web-development/web-development-page-agent) | Вбудуй alibaba/page-agent у свою веб‑аплікацію — чистий JavaScript‑агент з графічним інтерфейсом, що працює в межах сторінки, постачається як один тег <script> або npm‑пакет і дозволяє користувачам твого сайту керувати інтерфейсом за допомогою природної мови («клікни вхід, заповни ім’я користувача…») |
## Contributing Optional Skills

Щоб додати новий необов’язковий **skill** до репозиторію:

1. Створи каталог `optional-skills/<category>/<skill-name>/`
2. Додай `SKILL.md` зі стандартним frontmatter (name, description, version, author)
3. Додай будь‑які допоміжні файли у підкаталоги `references/`, `templates/` або `scripts/`
4. Надішли pull request — skill з’явиться в цьому каталозі та отримає власну сторінку документації після злиття.