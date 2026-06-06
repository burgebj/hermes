---
title: "Интеграции"
sidebar_label: "Overview"
sidebar_position: 0
---

# Интеграции

Hermes Agent подключается к внешним системам для AI‑вычислений, серверов инструментов, рабочих процессов IDE, программного доступа и многого другого. Эти интеграции расширяют возможности Hermes и места, где он может работать.

:::tip Start here
Если у тебя есть время только на одну интеграцию, настрой [Nous Portal](/integrations/nous-portal) — один вход через OAuth покрывает более 300 моделей плюс четыре инструмента Tool Gateway (веб‑поиск, генерация изображений, TTS и автоматизация браузера).
:::

## AI‑провайдеры и маршрутизация

Hermes поддерживает несколько провайдеров AI‑вычислений «из коробки». Используй `hermes model` для интерактивной настройки или укажи их в `config.yaml`.

- **[AI Providers](/user-guide/features/provider-routing)** — OpenRouter, Anthropic, OpenAI, Google и любой совместимый с OpenAI эндпоинт. Hermes автоматически определяет возможности провайдера, такие как зрение, потоковая передача и использование инструментов.
- **[Provider Routing](/user-guide/features/provider-routing)** — Тонкая настройка того, какие провайдеры обрабатывают твои запросы к OpenRouter. Оптимизируй стоимость, скорость или качество с помощью сортировки, белых/чёрных списков и явного порядка приоритетов.
- **[Fallback Providers](/user-guide/features/fallback-providers)** — Автоматический переход к резервным LLM‑провайдерам, когда основная модель выдаёт ошибку. Включает откат основной модели и независимый откат вспомогательных задач для зрения, сжатия и веб‑извлечения.

## Серверы инструментов (MCP)

- **[MCP Servers](/user-guide/features/mcp)** — Подключай Hermes к внешним серверам инструментов через Model Context Protocol. Доступ к инструментам из GitHub, баз данных, файловых систем, стеков браузеров, внутренних API и прочего без написания собственных Hermes‑инструментов. Поддерживает транспорт stdio и SSE, фильтрацию инструментов per‑server и регистрацию ресурсов/промптов с учётом возможностей.

## Бэкенды веб‑поиска

Инструменты `web_search` и `web_extract` поддерживают четыре провайдера, настраиваемые через `config.yaml` или `hermes tools`:

| Бэкенд | Переменная окружения | Поиск | Извлечение | Сканирование |
|--------|----------------------|-------|------------|--------------|
| **Firecrawl** (по умолчанию) | `FIRECRAWL_API_KEY` | ✔ | ✔ | ✔ |
| **Parallel** | `PARALLEL_API_KEY` | ✔ | ✔ | — |
| **Tavily** | `TAVILY_API_KEY` | ✔ | ✔ | ✔ |
| **Exa** | `EXA_API_KEY` | ✔ | ✔ | — |

Пример быстрой настройки:

```yaml
web:
  backend: firecrawl    # firecrawl | parallel | tavily | exa
```

Если `web.backend` не задан, бэкенд определяется автоматически из доступного API‑ключа. Самостоятельно развернутый Firecrawl также поддерживается через `FIRECRAWL_API_URL`.

## Автоматизация браузера

Hermes включает полную автоматизацию браузера с несколькими вариантами бэкенда для навигации по сайтам, заполнения форм и извлечения информации:

- **Browserbase** — Управляемые облачные браузеры с анти‑бот‑инструментами, решением CAPTCHA и резидентными прокси.
- **Browser Use** — Альтернативный облачный провайдер браузеров.
- **Local Chromium‑family CDP** — Подключение к запущенному Chrome, Brave, Chromium или Edge через `/browser connect`.
- **Local Chromium** — Безголовый локальный браузер через CLI `agent-browser`.

Смотри [Browser Automation](/user-guide/features/browser) для настройки и использования.

## Провайдеры голоса и TTS

Текст‑в‑речь и речь‑в‑текст для всех платформ обмена сообщениями:

| Провайдер | Качество | Стоимость | API‑ключ |
|-----------|----------|-----------|----------|
| **Edge TTS** (по умолчанию) | Хорошее | Бесплатно | Не требуется |
| **ElevenLabs** | Отличное | Платно | `ELEVENLABS_API_KEY` |
| **OpenAI TTS** | Хорошее | Платно | `VOICE_TOOLS_OPENAI_KEY` |
| **MiniMax** | Хорошее | Платно | `MINIMAX_API_KEY` |
| **xAI TTS** | Хорошее | Платно | `XAI_API_KEY` |
| **NeuTTS** | Хорошее | Бесплатно | Не требуется |

Распознавание речи поддерживает шесть провайдеров: локальный `faster‑whisper` (бесплатно, работает на устройстве), локальная обёртка‑команда, Groq, OpenAI Whisper API, Mistral и xAI. Транскрипция голосовых сообщений работает в Telegram, Discord, WhatsApp и других платформах. Смотри [Voice & TTS](/user-guide/features/tts) и [Voice Mode](/user-guide/features/voice-mode) для деталей.

## Интеграция с IDE и редакторами

- **[IDE Integration (ACP)](/user-guide/features/acp)** — Используй Hermes Agent внутри ACP‑совместимых редакторов, таких как VS Code, Zed и JetBrains. Hermes работает как ACP‑сервер, отображая сообщения чата, активность инструментов, диффы файлов и команды терминала внутри редактора.

## Программный доступ

- **[API Server](/user-guide/features/api-server)** — Выдавай Hermes как совместимый с OpenAI HTTP‑эндпоинт. Любой фронтенд, понимающий формат OpenAI — Open WebUI, LobeChat, LibreChat, NextChat, ChatBox — может подключиться и использовать Hermes как бекенд со всем набором инструментов.

## Память и персонализация

- **[Built-in Memory](/user-guide/features/memory)** — Постоянная, курируемая память через файлы `MEMORY.md` и `USER.md`. Агент поддерживает ограниченные хранилища личных заметок и данных профиля пользователя, сохраняющиеся между сессиями.
- **[Memory Providers](/user-guide/features/memory-providers)** — Подключай внешние бекенды памяти для более глубокой персонализации. Поддерживаются восемь провайдеров: Honcho (диалектическое рассуждение), OpenViking (иерархический поиск), Mem0 (облачное извлечение), Hindsight (графы знаний), Holographic (локальный SQLite), RetainDB (гибридный поиск), ByteRover (CLI‑based) и Supermemory.

## Платформы обмена сообщениями

Hermes работает как шлюз‑бот на более чем 27 платформах, все они настраиваются через одну подсистему `gateway`:

- **[Telegram](/user-guide/messaging/telegram)**, **[Discord](/user-guide/messaging/discord)**, **[Slack](/user-guide/messaging/slack)**, **[WhatsApp](/user-guide/messaging/whatsapp)**, **[Signal](/user-guide/messaging/signal)**, **[Matrix](/user-guide/messaging/matrix)**, **[Mattermost](/user-guide/messaging/mattermost)**, **[Email](/user-guide/messaging/email)**, **[SMS](/user-guide/messaging/sms)**, **[DingTalk](/user-guide/messaging/dingtalk)**, **[Feishu/Lark](/user-guide/messaging/feishu)**, **[WeCom](/user-guide/messaging/wecom)**, **[WeCom Callback](/user-guide/messaging/wecom-callback)**, **[Weixin](/user-guide/messaging/weixin)**, **[BlueBubbles](/user-guide/messaging/bluebubbles)**, **[QQ Bot](/user-guide/messaging/qqbot)**, **[Yuanbao](/user-guide/messaging/yuanbao)**, **[Home Assistant](/user-guide/messaging/homeassistant)**, **[Microsoft Teams](/user-guide/messaging/teams)**, **[Microsoft Teams Meetings](/user-guide/messaging/teams-meetings)**, **[Microsoft Graph Webhook](/user-guide/messaging/msgraph-webhook)**, **[Google Chat](/user-guide/messaging/google_chat)**, **[LINE](/user-guide/messaging/line)**, **[ntfy](/user-guide/messaging/ntfy)**, **[SimpleX](/user-guide/messaging/simplex)**, **[Open WebUI](/user-guide/messaging/open-webui)**, **[Webhooks](/user-guide/messaging/webhooks)**

См. [Messaging Gateway overview](/user-guide/messaging) для таблицы сравнения платформ и руководства по настройке.

## Умный дом

- **[Home Assistant](/user-guide/messaging/homeassistant)** — Управляй устройствами умного дома через четыре специализированных инструмента (`ha_list_entities`, `ha_get_state`, `ha_list_services`, `ha_call_service`). Набор инструментов Home Assistant активируется автоматически при наличии `HASS_TOKEN`.

## Плагины

- **[Plugin System](/user-guide/features/plugins)** — Расширяй Hermes пользовательскими инструментами, хуками жизненного цикла и командами CLI без изменения ядра. Плагины обнаруживаются в `~/.hermes/plugins/`, локальном проекте `.hermes/plugins/` и через pip‑установленные entry points.
- **[Build a Plugin](/guides/build-a-hermes-plugin)** — Пошаговое руководство по созданию плагинов Hermes с инструментами, хуками и командами CLI.

## Обучение и оценка

- **[Batch Processing](/user-guide/features/batch-processing)** — Запускай агента на сотнях запросов параллельно, генерируя структурированные данные траекторий в формате ShareGPT для создания обучающих наборов или оценки.