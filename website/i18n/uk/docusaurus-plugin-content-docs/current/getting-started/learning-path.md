---
sidebar_position: 3
title: 'Шлях навчання'
description: 'Вибери свій шлях навчання через документацію Hermes Agent, орієнтуючись на рівень досвіду та цілі.'
---

# Шлях навчання

Hermes Agent може робити багато — CLI‑асистент, бот у Telegram/Discord, автоматизація завдань, RL‑тренування та інше. Ця сторінка допоможе тобі визначити, з чого почати і що читати, залежно від твого рівня досвіду та цілей.

:::tip Почни тут
Якщо ти ще не встановив Hermes Agent, розпочни з [Посібника з інсталяції](/getting-started/installation) і потім пройди [Швидкий старт](/getting-started/quickstart). Усе нижче передбачає, що у тебе вже є працююча інсталяція.
:::

:::tip Налаштування провайдера вперше
Користувачі, які вперше працюють з системою, майже завжди хочуть `hermes setup --portal` — один OAuth охоплює модель і чотири інструменти шлюзу інструментів (search/image/TTS/browser). Дивись [Nous Portal](/integrations/nous-portal).
:::
## Як користуватися цією сторінкою

- **Знаєш свій рівень?** Перейди до [таблиці за рівнем досвіду](#by-experience-level) і слідуй порядку читання для свого **рівня**.
- **Маєш конкретну мету?** Перейди до розділу [За випадком використання](#by-use-case) і знайди сценарій, який підходить.
- **Просто переглядаєш?** Переглянь таблицю [Ключові функції](#key-features-at-a-glance) для швидкого огляду всього, що може Hermes Agent.
## За рівнем досвіду

| Рівень | Мета | Рекомендоване читання | Оцінка часу |
|---|---|---|---|
| **Початківець** | Запуститися, вести базові розмови, користуватися вбудованими інструментами | [Встановлення](/getting-started/installation) → [Швидкий старт](/getting-started/quickstart) → [Використання CLI](/user-guide/cli) → [Налаштування](/user-guide/configuration) | ~1 година |
| **Середній** | Налаштувати ботів для обміну повідомленнями, використовувати розширені функції, такі як пам'ять, cron‑завдання та навички | [Сесії](/user-guide/sessions) → [Обмін повідомленнями](/user-guide/messaging) → [Інструменти](/user-guide/features/tools) → [Навички](/user-guide/features/skills) → [Пам'ять](/user-guide/features/memory) → [Cron](/user-guide/features/cron) | ~2–3 години |
| **Просунутий** | Створювати власні інструменти, розробляти навички, навчати моделі за допомогою RL, робити внесок у проєкт | [Архітектура](/developer-guide/architecture) → [Додавання інструментів](/developer-guide/adding-tools) → [Створення навичок](/developer-guide/creating-skills) → [Внесок](/developer-guide/contributing) | ~4–6 годин |
## За випадком використання

Вибери сценарій, який відповідає тому, що ти хочеш зробити. Кожен з них посилає тебе на відповідну документацію у потрібному порядку.

### «Я хочу CLI‑асистента для кодування»

Використовуй Hermes Agent як інтерактивного термінального асистента для написання, перегляду та запуску коду.

1. [Installation](/getting-started/installation)
2. [Quickstart](/getting-started/quickstart)
3. [CLI Usage](/user-guide/cli)
4. [Code Execution](/user-guide/features/code-execution)
5. [Context Files](/user-guide/features/context-files)
6. [Tips & Tricks](/guides/tips)

:::tip
Передавай файли безпосередньо у свою розмову за допомогою **контекстних файлів**. Hermes Agent може читати, редагувати та запускати код у твоїх проектах.
:::

### «Я хочу Telegram/Discord‑бота»

Розгорни Hermes Agent як бота на улюбленій платформі обміну повідомленнями.

1. [Installation](/getting-started/installation)
2. [Configuration](/user-guide/configuration)
3. [Messaging Overview](/user-guide/messaging)
4. [Telegram Setup](/user-guide/messaging/telegram)
5. [Discord Setup](/user-guide/messaging/discord)
6. [Voice Mode](/user-guide/features/voice-mode)
7. [Use Voice Mode with Hermes](/guides/use-voice-mode-with-hermes)
8. [Security](/user-guide/security)

Для повних прикладів проєктів дивись:
- [Daily Briefing Bot](/guides/daily-briefing-bot)
- [Team Telegram Assistant](/guides/team-telegram-assistant)

### «Я хочу автоматизувати завдання»

Плануй повторювані завдання, запускай пакетні роботи або ланцюжки дій агента.

1. [Quickstart](/getting-started/quickstart)
2. [Cron Scheduling](/user-guide/features/cron)
3. [Batch Processing](/user-guide/features/batch-processing)
4. [Delegation](/user-guide/features/delegation)
5. [Hooks](/user-guide/features/hooks)

:::tip
Cron‑завдання дозволяють Hermes Agent виконувати задачі за розкладом — щоденні підсумки, періодичні перевірки, автоматичні звіти — без твоєї присутності.
:::

### «Я хочу створювати власні інструменти/навички»

Розширюй Hermes Agent своїми **інструментами** та повторно використовуваними пакетами **навичок**.

1. [Plugins](/user-guide/features/plugins)
2. [Build a Hermes Plugin](/guides/build-a-hermes-plugin)
3. [Tools Overview](/user-guide/features/tools)
4. [Skills Overview](/user-guide/features/skills)
5. [MCP (Model Context Protocol)](/user-guide/features/mcp)
6. [Architecture](/developer-guide/architecture)
7. [Adding Tools](/developer-guide/adding-tools)
8. [Creating Skills](/developer-guide/creating-skills)

:::tip
Для більшості створення власних інструментів починай з **plugins**. Сторінка [Adding Tools](/developer-guide/adding-tools) призначена для розробки вбудованого ядра Hermes, а не для звичайного користувацького/custom‑tool шляху.
:::

### «Я хочу навчати моделі»

Використовуй підкріплювальне навчання для тонкого налаштування поведінки моделі за допомогою RL‑тренувального конвеєра Hermes Agent (на базі [Atropos](https://github.com/NousResearch/atropos)).

1. [Quickstart](/getting-started/quickstart)
2. [Configuration](/user-guide/configuration)
3. [Atropos RL Environments](https://github.com/NousResearch/atropos) (external)
4. [Provider Routing](/user-guide/features/provider-routing)
5. [Architecture](/developer-guide/architecture)

:::tip
RL‑тренування працює найкраще, коли ти вже розумієш основи того, як Hermes Agent обробляє розмови та виклики інструментів. Спочатку пройди шлях **Beginner**, якщо ти новачок.
:::

### «Я хочу використовувати його як бібліотеку Python»

Інтегруй Hermes Agent у свої власні Python‑додатки програмно.

1. [Installation](/getting-started/installation)
2. [Quickstart](/getting-started/quickstart)
3. [Python Library Guide](/guides/python-library)
4. [Architecture](/developer-guide/architecture)
5. [Tools](/user-guide/features/tools)
6. [Sessions](/user-guide/sessions)
## Ключові можливості в огляді

Не впевнений, що доступно? Ось швидкий огляд основних функцій:

| Feature | What It Does | Link |
|---|---|---|
| **Tools** | Built‑in tools the agent can call (file I/O, search, shell, etc.) | [Tools](/user-guide/features/tools) |
| **Skills** | Installable plugin packages that add new capabilities | [Skills](/user-guide/features/skills) |
| **Memory** | Persistent memory across sessions | [Memory](/user-guide/features/memory) |
| **Context Files** | Feed files and directories into conversations | [Context Files](/user-guide/features/context-files) |
| **MCP** | Connect to external tool servers via Model Context Protocol | [MCP](/user-guide/features/mcp) |
| **Cron** | Schedule recurring agent tasks | [Cron](/user-guide/features/cron) |
| **Delegation** | Spawn sub‑agents for parallel work | [Delegation](/user-guide/features/delegation) |
| **Code Execution** | Run Python scripts that call Hermes tools programmatically | [Code Execution](/user-guide/features/code-execution) |
| **Browser** | Web browsing and scraping | [Browser](/user-guide/features/browser) |
| **Hooks** | Event‑driven callbacks and middleware | [Hooks](/user-guide/features/hooks) |
| **Batch Processing** | Process multiple inputs in bulk | [Batch Processing](/user-guide/features/batch-processing) |
| **Provider Routing** | Route requests across multiple LLM providers | [Provider Routing](/user-guide/features/provider-routing) |
## Що читати далі

Виходячи з того, де ти зараз:

- **Тільки-но встановив?** → Перейди до [Quickstart](/getting-started/quickstart), щоб запустити свою першу розмову.
- **Завершив Quickstart?** → Прочитай [CLI Usage](/user-guide/cli) та [Configuration](/user-guide/configuration), щоб налаштувати свою інсталяцію.
- **Впевнений у основах?** → Досліджуй [Tools](/user-guide/features/tools), [Skills](/user-guide/features/skills) та [Memory](/user-guide/features/memory), щоб розкрити повну потужність агента.
- **Налаштовуєш для команди?** → Прочитай [Security](/user-guide/security) та [Sessions](/user-guide/sessions), щоб зрозуміти контроль доступу та управління розмовами.
- **Готовий будувати?** → Переходь до [Developer Guide](/developer-guide/architecture), щоб зрозуміти внутрішню структуру та почати робити внесок.
- **Хочеш практичні приклади?** → Переглянь розділ [Guides](/guides/tips) для реальних проєктів та порад.

:::tip
Тобі не потрібно читати все. Обери шлях, який відповідає твоїй меті, слідуй за посиланнями у порядку, і ти швидко станеш продуктивним. Завжди можеш повернутися на цю сторінку, щоб знайти наступний крок.
:::