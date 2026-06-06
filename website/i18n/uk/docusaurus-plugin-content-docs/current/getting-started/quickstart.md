---
sidebar_position: 1
title: "Швидкий старт"
description: "Твоя перша розмова з Hermes Agent — від встановлення до спілкування за менше ніж 5 хвилин"
---

# Швидкий старт

Цей посібник проведе тебе від нуля до працюючої інсталяції Hermes, яка витримує реальне використання. Встанови, обери провайдера, перевір працюючий чат і точно знайте, що робити, коли щось поламається.
## Віддаєш перевагу перегляду?

**Onchain AI Garage** зібрав майстер‑клас, у якому показано встановлення, налаштування та базові команди — хороший супровід до цієї сторінки, якщо ти хочеш слідувати за відео. Більше інформації — у повному плейлісті [Hermes Agent Tutorials & Use Cases](https://www.youtube.com/channel/UCqB1bhMwGsW-yefBxYwFCCg).

<div style={{position: 'relative', paddingBottom: '56.25%', height: 0, overflow: 'hidden', maxWidth: '100%', marginBottom: '1.5rem'}}>
  <iframe
    style={{position: 'absolute', top: 0, left: 0, width: '100%', height: '100%'}}
    src="https://www.youtube-nocookie.com/embed/R3YOGfTBcQg"
    title="Hermes Agent Masterclass: Installation, Setup, Basic Commands"
    frameBorder="0"
    allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
    allowFullScreen
  ></iframe>
</div>
## Для кого це

- Ти — абсолютний новачок і хочеш найкоротший шлях до робочого налаштування
- Перехід між провайдерами і не хочеш витрачати час на помилки конфігурації
- Налаштування Hermes для команди, бота або постійного робочого процесу
- Втомився від «встановив, а все одно нічого не робить»
## Найшвидший шлях

Вибери рядок, який відповідає твоїй меті:

| Мета | Спочатку зроби це | Потім зроби це |
|---|---|---|
| Я просто хочу, щоб Hermes працював на моєму комп’ютері | `hermes setup` | Запусти реальний чат і переконайся, що він відповідає |
| Я вже знаю свого провайдера | `hermes model` | Збережи конфігурацію, потім почни чат |
| Я хочу бота або постійно працююче налаштування | `hermes gateway setup` after CLI works | Підключи Telegram, Discord, Slack або іншу платформу |
| Я хочу локальну або самохостовану модель | `hermes model` → custom endpoint | Перевір endpoint, назву моделі та довжину контексту |
| Я хочу багатопровайдерський запасний (варіант) | `hermes model` first | Додай маршрутизацію та запасний (варіант) лише після того, як базовий чат працює |

**Загальне правило:** якщо Hermes не може завершити звичайний чат, не додавай нові функції. Спочатку забезпеч чисту розмову, а потім додавай шлюз, cron, навички, голос або маршрутизацію.
## 1. Встановити Hermes Agent

**Option A — pip (найпростіший):**

```bash
pip install hermes-agent
hermes postinstall     # optional: installs Node.js, browser, ripgrep, ffmpeg + runs setup
```

Релізи PyPI відстежують позначені версії (основні/мінорні випуски), а не кожен коміт у `main`. Для найновішого використай Option B.

**Option B — git installer (відстежує гілку main):**

```bash
# Linux / macOS / WSL2 / Android (Termux)
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

:::tip Android / Termux
Якщо встановлюєш на телефон, переглянь спеціальний [Termux guide](./termux.md) для перевіреного ручного шляху, підтримуваних extras та поточних обмежень для Android.
:::

:::tip Windows Users
Спочатку встанови [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install), потім виконай команду вище у терміналі WSL2.
:::

Після завершення перезавантаж свою оболонку:

```bash
source ~/.bashrc   # or source ~/.zshrc
```

Для докладних параметрів встановлення, передумов та усунення проблем дивись [посібник з встановлення](./installation.md).
## 2. Вибери провайдера

Найважливіший крок налаштування. Використай `hermes model`, щоб інтерактивно пройти вибір:

```bash
hermes model
```

:::tip Найпростіший шлях: Nous Portal
Одна підписка охоплює 300+ моделей плюс [Tool Gateway](../user-guide/features/tool-gateway.md) (веб‑пошук, генерація зображень, TTS, хмарний браузер). На чистій інсталяції:

```bash
hermes setup --portal
```

Це виконує вхід, встановлює Nous як твого провайдера та вмикає шлюз інструментів (Tool Gateway) однією командою.
:::

Хороші значення за замовчуванням:

| Провайдер | Що це | Як налаштувати |
|----------|-----------|---------------|
| **Nous Portal** | Підписка, zero‑config | OAuth‑логін через `hermes model` |
| **OpenAI Codex** | ChatGPT OAuth, використовує моделі Codex | Авторизація за кодом пристрою через `hermes model` |
| **Anthropic** | Моделі Claude безпосередньо — план Max + додаткові кредити (OAuth) або API‑ключ для pay‑per‑token | `hermes model` → OAuth‑логін (потрібен Max + кредити), або Anthropic API‑ключ |
| **OpenRouter** | Маршрутизація між багатьма провайдерами та моделями | Введи свій API‑ключ |
| **Z.AI** | Моделі GLM / Zhipu | Встанови `GLM_API_KEY` / `ZAI_API_KEY` (також приймає `Z_AI_API_KEY`) |
| **Kimi / Moonshot** | Моделі кодування та чатів, розміщені в Moonshot | Встанови `KIMI_API_KEY` (або специфічний для кодування `KIMI_CODING_API_KEY`) |
| **Kimi / Moonshot China** | Точка доступу Moonshot у Китаї | Встанови `KIMI_CN_API_KEY` |
| **Arcee AI** | Моделі Trinity | Встанови `ARCEEAI_API_KEY` |
| **GMI Cloud** | Прямий API до багатьох моделей | Встанови `GMI_API_KEY` |
| **MiniMax (OAuth)** | Модель MiniMax через браузерний OAuth — без API‑ключа (назва моделі в `hermes_cli/models.py` може змінюватись) | `hermes model` → MiniMax (OAuth) |
| **MiniMax** | Міжнародна точка доступу MiniMax | Встанови `MINIMAX_API_KEY` |
| **MiniMax China** | Точка доступу MiniMax у Китаї | Встанови `MINIMAX_CN_API_KEY` |
| **Alibaba Cloud** | Моделі Qwen через DashScope | Встанови `DASHSCOPE_API_KEY` (план Qwen Coding також приймає `ALIBABA_CODING_PLAN_API_KEY`) |
| **Hugging Face** | 20+ відкритих моделей через уніфікований роутер (Qwen, DeepSeek, Kimi тощо) | Встанови `HF_TOKEN` |
| **AWS Bedrock** | Claude, Nova, Llama, DeepSeek через нативний Converse API | IAM‑роль або `aws configure` ([путівник](../guides/aws-bedrock.md)) |
| **Azure Foundry** | Моделі, розміщені в Azure AI Foundry | Встанови `AZURE_FOUNDRY_API_KEY` + `AZURE_FOUNDRY_BASE_URL` |
| **Google AI Studio** | Моделі Gemini через прямий API | Встанови `GOOGLE_API_KEY` / `GEMINI_API_KEY` |
| **Google Gemini (OAuth)** | Gemini через OAuth‑потік `google-gemini-cli` — без ключа | `hermes model` → Google Gemini (OAuth) |
| **xAI** | Моделі Grok через прямий API | Встанови `XAI_API_KEY` |
| **xAI Grok OAuth** | Підписка SuperGrok / Premium+, без API‑ключа | `hermes model` → xAI Grok OAuth |
| **NovitaAI** | Шлюз API до багатьох моделей | Встанови `NOVITA_API_KEY` |
| **StepFun** | Моделі Step Plan | Встанови `STEPFUN_API_KEY` |
| **Xiaomi MiMo** | Моделі, розміщені в Xiaomi | Встанови `XIAOMI_API_KEY` |
| **Tencent TokenHub** | Моделі, розміщені в Tencent | Встанови `TOKENHUB_API_KEY` |
| **Ollama Cloud** | Керовані моделі Ollama | Встанови `OLLAMA_API_KEY` |
| **LM Studio** | Локальний десктоп‑додаток, що надає OpenAI‑сумісний API | Встанови `LM_API_KEY` (і `LM_BASE_URL`, якщо не за замовчуванням) |
| **Qwen OAuth** | Браузерний OAuth Qwen Portal — без API‑ключа | `hermes model` → Qwen OAuth |
| **Kilo Code** | Моделі, розміщені в KiloCode | Встанови `KILOCODE_API_KEY` |
| **OpenCode Zen** | Платний доступ до відібраних моделей | Встанови `OPENCODE_ZEN_API_KEY` |
| **OpenCode Go** | Підписка $10/міс для відкритих моделей | Встанови `OPENCODE_GO_API_KEY` |
| **DeepSeek** | Прямий доступ до API DeepSeek | Встанови `DEEPSEEK_API_KEY` |
| **NVIDIA NIM** | Моделі Nemotron через build.nvidia.com або локальний NIM | Встанови `NVIDIA_API_KEY` (за потреби `NVIDIA_BASE_URL`) |
| **GitHub Copilot** | Підписка GitHub Copilot (GPT‑5.x, Claude, Gemini тощо) | OAuth через `hermes model`, або `COPILOT_GITHUB_TOKEN` / `GH_TOKEN` |
| **GitHub Copilot ACP** | Backend агента Copilot ACP (запускає локальний CLI `copilot`) | `hermes model` (потрібен CLI `copilot` + `copilot login`) |
| **Custom Endpoint** | VLLM, SGLang, Ollama або будь‑який OpenAI‑сумісний API | Встанови базовий URL + API‑ключ |

Для більшості нових користувачів: обери провайдера, залиш стандартні значення, якщо тільки не знаєш, чому їх змінювати. Повний каталог провайдерів з змінними оточення та кроками налаштування знаходиться на сторінці [Providers](../integrations/providers.md).

:::caution Мінімальний контекст: 64 K токенів
Hermes Agent потребує модель з контекстом щонайменше **64 000 токенів**. Моделі з меншими вікнами не зможуть підтримувати достатню робочу пам'ять для багатокрокових робочих процесів виклику інструментів і будуть відхилені під час запуску. Більшість хостованих моделей (Claude, GPT, Gemini, Qwen, DeepSeek) легко задовольняють цю вимогу. Якщо ти запускаєш локальну модель, встанови її розмір контексту щонайменше 64 K (наприклад, `--ctx-size 65536` для llama.cpp або `-c 65536` для Ollama).
:::

:::tip
Ти можеш переключати провайдери у будь‑який момент за допомогою `hermes model` — без прив'язки. Для повного списку підтримуваних провайдерів та деталей налаштування дивись у [AI Providers](../integrations/providers.md).
:::

### Як зберігаються налаштування

Hermes розділяє секрети та звичайну конфігурацію:

- **Секрети та токени** → `~/.hermes/.env`
- **Несекретні налаштування** → `~/.hermes/config.yaml`

Найпростіший спосіб правильно задати значення — через CLI:

```bash
hermes config set model anthropic/claude-opus-4.6
hermes config set terminal.backend docker
hermes config set OPENROUTER_API_KEY sk-or-...
```

Правильне значення автоматично потрапляє у відповідний файл.
## 3. Запусти свій перший чат

```bash
hermes            # classic CLI
hermes --tui      # modern TUI (recommended)
```

Ти побачиш вітальний банер з твоєю моделлю, доступними інструментами та навичками. Використай запит, який є конкретним і легко перевірити:

:::tip Вибери інтерфейс
Hermes постачається з двома термінальними інтерфейсами: класичним `prompt_toolkit` CLI та новішим [TUI](../user-guide/tui.md) з модальними оверлеями, вибором мишею та неблокуючим вводом. Обидва використовують однакові сесії, слеш‑команди та конфігурацію — спробуй кожен за допомогою `hermes` та `hermes --tui`.
:::

```
Summarize this repo in 5 bullets and tell me what the main entrypoint is.
```

```
Check my current directory and tell me what looks like the main project file.
```

```
Help me set up a clean GitHub PR workflow for this codebase.
```

**Як виглядає успіх:**

- Банер показує обрану модель/провайдера
- Hermes відповідає без помилок
- За потреби може використати інструмент (термінал, читання файлу, веб‑пошук)
- Розмова продовжується без проблем більше ніж один хід

Якщо це працює, ти пройшов найскладнішу частину.
## 4. Перевірка роботи сесій

Перш ніж продовжувати, переконайся, що відновлення сесії працює:

```bash
hermes --continue    # Resume the most recent session
hermes -c            # Short form
```

Це має повернути тебе до сесії, яку ти лише що створив. Якщо цього не сталося, перевір, чи ти знаходишся в тому ж профілі та чи сесія дійсно була збережена. Це важливо пізніше, коли ти працюєш з кількома налаштуваннями або машинами.
## 5. Спробуй ключові функції

### Використання терміналу

```
❯ What's my disk usage? Show the top 5 largest directories.
```

Агент виконує команди терміналу від твого імені та показує результати.

### Команди зі слешем

Набери `/`, щоб побачити випадаюче автодоповнення всіх команд:

| Command | Що робить |
|---------|-----------|
| `/help` | Показати всі доступні команди |
| `/tools` | Перелік доступних інструментів |
| `/model` | Перемкнути моделі інтерактивно |
| `/personality pirate` | Спробувати веселу особистість |
| `/save` | Зберегти розмову |

### Багаторядковий ввід

Натисни `Alt+Enter`, `Ctrl+J` або `Shift+Enter`, щоб додати новий рядок. `Shift+Enter` потребує терміналу, який надсилає його як окрему послідовність (за замовчуванням Kitty / foot / WezTerm / Ghostty; iTerm2 / Alacritty / VS Code terminal після ввімкнення протоколу клавіатури Kitty). `Alt+Enter` і `Ctrl+J` працюють у будь‑якому терміналі.

### Переривання агента

Якщо агент працює надто довго, введи нове повідомлення і натисни Enter — це перериває поточне завдання і переходить до нових інструкцій. Працює також `Ctrl+C`.
## 6. Додати наступний шар

Лише після того, як базовий чат працює. Вибери, що тобі потрібно:

### Бот або спільний асистент

```bash
hermes gateway setup    # Interactive platform configuration
```

Підключи [Telegram](/user-guide/messaging/telegram), [Discord](/user-guide/messaging/discord), [Slack](/user-guide/messaging/slack), [WhatsApp](/user-guide/messaging/whatsapp), [Signal](/user-guide/messaging/signal), [Email](/user-guide/messaging/email), [Home Assistant](/user-guide/messaging/homeassistant) або [Microsoft Teams](/user-guide/messaging/teams).

### Автоматизація та інструменти

- `hermes tools` — налаштуй доступ до інструментів для кожної платформи
- `hermes skills` — переглядай і встановлюй повторно використовувані робочі процеси
- Cron — лише після того, як твій бот або CLI налаштовано стабільно

### Пісочний термінал

Для безпеки запускай агента в Docker‑контейнері або на віддаленому сервері:

```bash
hermes config set terminal.backend docker    # Docker isolation
hermes config set terminal.backend ssh       # Remote server
```

### Голосовий режим

```bash
# From the Hermes install directory (the curl installer placed it at
# ~/.hermes/hermes-agent on Linux/macOS or %LOCALAPPDATA%\hermes\hermes-agent on Windows):
cd ~/.hermes/hermes-agent
uv pip install -e ".[voice]"
# Includes faster-whisper for free local speech-to-text
```

Потім у CLI: `/voice on`. Натисни `Ctrl+B`, щоб записати. Дивись [Voice Mode](../user-guide/features/voice-mode.md).

### Навички

```bash
hermes skills search kubernetes
hermes skills install openai/skills/k8s
```

Або використай `/skills` всередині сесії чату.

### MCP‑сервери

```yaml
# Add to ~/.hermes/config.yaml
mcp_servers:
  github:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxx"
```

### Інтеграція редактора (ACP)

Підтримка ACP постачається зі стандартними `[all]` extras, тому інсталятор curl вже включає її. Просто виконай:

```bash
hermes acp
```

(Якщо ти встановив без `[all]`, спочатку виконай `cd ~/.hermes/hermes-agent && uv pip install -e ".[acp]"`.)

Дивись [ACP Editor Integration](../user-guide/features/acp.md).
## Типові режими відмов

Це проблеми, які забирають найбільше часу:

| Симптом | Ймовірна причина | Виправлення |
|---|---|---|
| Hermes відкривається, але повертає порожні або пошкоджені відповіді | Неправильна автентифікація провайдера або вибір моделі | Запусти `hermes model` ще раз і підтверди провайдера, модель та автентифікацію |
| Кастомний endpoint «працює», але повертає сміття | Помилковий базовий URL, назва моделі або несумісність з OpenAI | Спочатку перевір endpoint у окремому клієнті |
| Gateway стартує, але ніхто не може з ним спілкуватись | Токен бота, allowlist або налаштування платформи неповні | Запусти `hermes gateway setup` ще раз і перевір `hermes gateway status` |
| `hermes --continue` не знаходить стару сесію | Переключені профілі або сесія не була збережена | Перевір `hermes sessions list` і впевнись, що працюєш у правильному профілі |
| Модель недоступна або дивна поведінка запасного (фолбек) варіанту | Маршрутизація провайдера або налаштування фолбеку надто агресивні | Вимкни маршрутизацію, доки базовий провайдер не стабілізується |
| `hermes doctor` вказує на проблеми в конфігурації | Відсутні або застарілі значення конфігурації | Виправ конфіг, протестуй простий чат перед додаванням функцій |
## Набір інструментів відновлення

Коли відчуваєш, що щось не так, використай цей порядок:

1. `hermes doctor`
2. `hermes model`
3. `hermes setup`
4. `hermes sessions list`
5. `hermes --continue`
6. `hermes gateway status`

Ця послідовність швидко поверне тебе від «збоїв» до відомого стану.
## Коротка довідка

| Команда | Опис |
|---------|------|
| `hermes` | Почати спілкування |
| `hermes model` | Вибрати провайдера LLM та модель |
| `hermes tools` | Налаштувати, які інструменти ввімкнено на платформі |
| `hermes setup` | Повний майстер налаштувань (конфігурує все одразу) |
| `hermes doctor` | Діагностувати проблеми |
| `hermes update` | Оновити до останньої версії |
| `hermes gateway` | Запустити шлюз обміну повідомленнями |
| `hermes --continue` | Відновити останню сесію |
## Наступні кроки

- **[CLI Guide](../user-guide/cli.md)** — Опануй інтерфейс терміналу
- **[Configuration](../user-guide/configuration.md)** — Налаштуй свою конфігурацію
- **[Messaging Gateway](../user-guide/messaging/index.md)** — Підключи Telegram, Discord, Slack, WhatsApp, Signal, Email, Home Assistant, Teams та інші
- **[Tools & Toolsets](../user-guide/features/tools.md)** — Досліджуй доступні можливості
- **[AI Providers](../integrations/providers.md)** — Повний список провайдерів та деталі налаштування
- **[Skills System](../user-guide/features/skills.md)** — Система навичок: повторно використовувані робочі процеси та знання
- **[Tips & Best Practices](../guides/tips.md)** — Поради та кращі практики для досвідчених користувачів