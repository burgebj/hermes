---
sidebar_position: 3
title: 'Путь обучения'
description: 'Выбери свой путь обучения через документацию Hermes Agent в зависимости от уровня опыта и целей.'
---

# Путь обучения

Hermes Agent может многое — CLI‑ассистент, бот для Telegram/Discord, автоматизация задач, RL‑тренировка и многое другое. Эта страница поможет тебе понять, с чего начать и что читать в зависимости от уровня опыта и целей.

:::tip Начни здесь
Если ты ещё не установил Hermes Agent, начни с [Руководства по установке](/getting-started/installation), а затем пройди [Быстрый старт](/getting-started/quickstart). Всё ниже предполагает, что у тебя уже есть рабочая установка.
:::

:::tip Настройка провайдера при первом запуске
Пользователи, запускающие Hermes Agent впервые, почти всегда используют `hermes setup --portal` — один OAuth покрывает модель плюс четыре инструмента шлюза инструментов (search/image/TTS/browser). Смотри [Nous Portal](/integrations/nous-portal).
:::
## Как использовать эту страницу

- **Знаешь свой уровень?** Перейди к [таблице уровней опыта](#by-experience-level) и следуй порядку чтения для своего уровня.
- **Есть конкретная цель?** Перейди к разделу [По случаю использования](#by-use-case) и найди подходящий сценарий.
- **Просто просматриваешь?** Посмотри таблицу [Ключевые возможности](#key-features-at-a-glance) для быстрого обзора того, что может Hermes Agent.
## По уровню опыта

| Уровень | Цель | Рекомендуемое чтение | Оценка времени |
|---|---|---|---|
| **Начинающий** | Запустить и начать работу, вести базовые диалоги, использовать встроенные инструменты | [Installation](/getting-started/installation) → [Quickstart](/getting-started/quickstart) → [CLI Usage](/user-guide/cli) → [Configuration](/user-guide/configuration) | ~1 ч |
| **Средний** | Настроить ботов для обмена сообщениями, использовать продвинутые функции, такие как память, cron‑задачи и навыки | [Sessions](/user-guide/sessions) → [Messaging](/user-guide/messaging) → [Tools](/user-guide/features/tools) → [Skills](/user-guide/features/skills) → [Memory](/user-guide/features/memory) → [Cron](/user-guide/features/cron) | ~2–3 ч |
| **Продвинутый** | Создавать пользовательские инструменты, создавать навыки, обучать модели с помощью RL, вносить вклад в проект | [Architecture](/developer-guide/architecture) → [Adding Tools](/developer-guide/adding-tools) → [Creating Skills](/developer-guide/creating-skills) → [Contributing](/developer-guide/contributing) | ~4–6 ч |
## По сценариям использования

Выбери сценарий, соответствующий тому, что ты хочешь сделать. Каждый из них ведёт к нужной документации в порядке, в котором её следует читать.

### «Я хочу CLI‑помощника по коду»

Используй Hermes Agent как интерактивного терминального помощника для написания, проверки и запуска кода.

1. [Installation](/getting-started/installation)
2. [Quickstart](/getting-started/quickstart)
3. [CLI Usage](/user-guide/cli)
4. [Code Execution](/user-guide/features/code-execution)
5. [Context Files](/user-guide/features/context-files)
6. [Tips & Tricks](/guides/tips)

:::tip
Передавай файлы напрямую в разговор с помощью **context files**. Hermes Agent может читать, редактировать и запускать код в твоих проектах.
:::

### «Я хочу бот для Telegram/Discord»

Разверни Hermes Agent как бота на любимой платформе обмена сообщениями.

1. [Installation](/getting-started/installation)
2. [Configuration](/user-guide/configuration)
3. [Messaging Overview](/user-guide/messaging)
4. [Telegram Setup](/user-guide/messaging/telegram)
5. [Discord Setup](/user-guide/messaging/discord)
6. [Voice Mode](/user-guide/features/voice-mode)
7. [Use Voice Mode with Hermes](/guides/use-voice-mode-with-hermes)
8. [Security](/user-guide/security)

Для полных примеров проектов смотри:
- [Daily Briefing Bot](/guides/daily-briefing-bot)
- [Team Telegram Assistant](/guides/team-telegram-assistant)

### «Я хочу автоматизировать задачи»

Планируй периодические задачи, запускай пакетные задания или связывай действия агента в цепочки.

1. [Quickstart](/getting-started/quickstart)
2. [Cron Scheduling](/user-guide/features/cron)
3. [Batch Processing](/user-guide/features/batch-processing)
4. [Delegation](/user-guide/features/delegation)
5. [Hooks](/user-guide/features/hooks)

:::tip
Cron‑задачи позволяют Hermes Agent выполнять задачи по расписанию — ежедневные сводки, периодические проверки, автоматические отчёты — без твоего присутствия.
:::

### «Я хочу создавать собственные инструменты/skills»

Расширяй Hermes Agent своими инструментами и переиспользуемыми пакетами **skills**.

1. [Plugins](/user-guide/features/plugins)
2. [Build a Hermes Plugin](/guides/build-a-hermes-plugin)
3. [Tools Overview](/user-guide/features/tools)
4. [Skills Overview](/user-guide/features/skills)
5. [MCP (Model Context Protocol)](/user-guide/features/mcp)
6. [Architecture](/developer-guide/architecture)
7. [Adding Tools](/developer-guide/adding-tools)
8. [Creating Skills](/developer-guide/creating-skills)

:::tip
Для большинства пользовательских инструментов начни с **plugins**. Страница [Adding Tools](/developer-guide/adding-tools) предназначена для разработки встроенного ядра Hermes, а не для обычного пути пользователь / кастомный‑инструмент.
:::

### «Я хочу обучать модели»

Используй обучение с подкреплением для тонкой настройки поведения модели через RL‑pipeline Hermes Agent (на базе [Atropos](https://github.com/NousResearch/atropos)).

1. [Quickstart](/getting-started/quickstart)
2. [Configuration](/user-guide/configuration)
3. [Atropos RL Environments](https://github.com/NousResearch/atropos) (external)
4. [Provider Routing](/user-guide/features/provider-routing)
5. [Architecture](/developer-guide/architecture)

:::tip
RL‑обучение работает лучше всего, если ты уже понимаешь основы того, как Hermes Agent обрабатывает разговоры и вызовы инструментов. Сначала пройди путь **Beginner**, если ты новичок.
:::

### «Я хочу использовать его как библиотеку Python»

Интегрируй Hermes Agent в свои собственные Python‑приложения программно.

1. [Installation](/getting-started/installation)
2. [Quickstart](/getting-started/quickstart)
3. [Python Library Guide](/guides/python-library)
4. [Architecture](/developer-guide/architecture)
5. [Tools](/user-guide/features/tools)
6. [Sessions](/user-guide/sessions)
## Ключевые возможности в обзоре

Не уверен, что доступно? Вот быстрый каталог основных возможностей:

| Функция | Что делает | Ссылка |
|---|---|---|
| **Tools** | Встроенные инструменты, которые агент может вызывать (работа с файлами, поиск, оболочка и т.д.) | [Tools](/user-guide/features/tools) |
| **Skills** | Устанавливаемые пакеты‑плагины, добавляющие новые возможности | [Skills](/user-guide/features/skills) |
| **Memory** | Постоянная память между сессиями | [Memory](/user-guide/features/memory) |
| **Context Files** | Передача файлов и каталогов в диалог | [Context Files](/user-guide/features/context-files) |
| **MCP** | Подключение к внешним серверам инструментов через Model Context Protocol | [MCP](/user-guide/features/mcp) |
| **Cron** | Планирование повторяющихся задач агента | [Cron](/user-guide/features/cron) |
| **Delegation** | Создание под‑агентов для параллельной работы | [Delegation](/user-guide/features/delegation) |
| **Code Execution** | Выполнение Python‑скриптов, программно вызывающих инструменты Hermes | [Code Execution](/user-guide/features/code-execution) |
| **Browser** | Веб‑просмотр и скрейпинг | [Browser](/user-guide/features/browser) |
| **Hooks** | Обратные вызовы и промежуточное ПО, основанные на событиях | [Hooks](/user-guide/features/hooks) |
| **Batch Processing** | Пакетная обработка множества входных данных | [Batch Processing](/user-guide/features/batch-processing) |
| **Provider Routing** | Маршрутизация запросов между несколькими LLM‑провайдерами | [Provider Routing](/user-guide/features/provider-routing) |
## Что читать дальше

Исходя из того, где ты сейчас находишься:

- **Только что установил?** → Перейди к [Quickstart](/getting-started/quickstart), чтобы запустить свой первый разговор.
- **Завершил Quickstart?** → Прочитай [CLI Usage](/user-guide/cli) и [Configuration](/user-guide/configuration), чтобы настроить свою систему.
- **Уверенно владеешь основами?** → Исследуй [Tools](/user-guide/features/tools), [Skills](/user-guide/features/skills) и [Memory](/user-guide/features/memory), чтобы раскрыть полную мощь агента.
- **Настраиваешь работу в команде?** → Прочитай [Security](/user-guide/security) и [Sessions](/user-guide/sessions), чтобы понять контроль доступа и управление диалогами.
- **Готов к разработке?** → Переходи к [Developer Guide](/developer-guide/architecture), чтобы разобраться во внутреннем устройстве и начать вносить свой вклад.
- **Хочешь практические примеры?** → Загляни в раздел [Guides](/guides/tips) для реальных проектов и советов.

:::tip
Тебе не нужно читать всё. Выбери путь, соответствующий твоей цели, следуй ссылкам последовательно, и ты быстро станешь продуктивным. Ты всегда можешь вернуться на эту страницу, чтобы найти следующий шаг.
:::