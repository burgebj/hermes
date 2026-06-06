---
title: "Інтеграції"
sidebar_label: "Overview"
sidebar_position: 0
---

# Інтеграції

Hermes Agent підключається до зовнішніх систем для AI‑inference, серверів інструментів, робочих процесів IDE, програмного доступу та багато іншого. Ці інтеграції розширюють можливості Hermes і місця, де його можна запускати.

:::tip Start here
Якщо ти маєш час налаштувати лише одну інтеграцію, налаштуй [Nous Portal](/integrations/nous-portal) — один OAuth‑вхід охоплює 300+ моделей плюс чотири інструменти Tool Gateway (веб‑пошук, генерація зображень, TTS та автоматизація браузера).
:::

## AI‑провайдери та маршрутизація

Hermes підтримує кілька AI‑inference провайдерів «з коробки». Використовуй `hermes model` для інтерактивного налаштування або вкажи їх у `config.yaml`.

- **[AI Providers](/user-guide/features/provider-routing)** — OpenRouter, Anthropic, OpenAI, Google та будь‑яка сумісна з OpenAI кінцева точка. Hermes автоматично визначає можливості, такі як бачення, потокове передавання та використання інструментів, для кожного провайдера.
- **[Provider Routing](/user-guide/features/provider-routing)** — Тонке керування тим, які саме провайдери оброблятимуть твої запити OpenRouter. Оптимізуй за вартістю, швидкістю або якістю за допомогою сортування, білих/чорних списків та явного пріоритетного порядку.
- **[Fallback Providers](/user-guide/features/fallback-providers)** — Автоматичний відкат до запасних LLM‑провайдерів, коли основна модель стикається з помилками. Включає відкат основної моделі та незалежний відкат допоміжних завдань для бачення, стиснення та веб‑видобутку.

## Сервери інструментів (MCP)

- **[MCP Servers](/user-guide/features/mcp)** — Підключай Hermes до зовнішніх серверів інструментів через Model Context Protocol. Доступ до інструментів з GitHub, баз даних, файлових систем, стеків браузерів, внутрішніх API та інше без написання власних інструментів Hermes. Підтримує транспорт stdio та SSE, фільтрацію інструментів per‑server та реєстрацію ресурсів/промптів з урахуванням можливостей.

## Бекенди веб‑пошуку

Інструменти `web_search` та `web_extract` підтримують чотири бекенд‑провайдери, які налаштовуються через `config.yaml` або `hermes tools`:

| Бекенд | Env Var | Пошук | Видобуток | Краул |
|--------|---------|------|-----------|-------|
| **Firecrawl** (за замовчуванням) | `FIRECRAWL_API_KEY` | ✔ | ✔ | ✔ |
| **Parallel** | `PARALLEL_API_KEY` | ✔ | ✔ | — |
| **Tavily** | `TAVILY_API_KEY` | ✔ | ✔ | ✔ |
| **Exa** | `EXA_API_KEY` | ✔ | ✔ | — |

Швидкий приклад налаштування:

```yaml
web:
  backend: firecrawl    # firecrawl | parallel | tavily | exa
```

Якщо `web.backend` не вказано, бекенд автоматично визначається за наявністю відповідного API‑ключа. Самостійно розгорнутий Firecrawl також підтримується через `FIRECRAWL_API_URL`.

## Автоматизація браузера

Hermes включає повну автоматизацію браузера з кількома варіантами бекендів для навігації сайтами, заповнення форм та видобутку інформації:

- **Browserbase** — Керовані хмарні браузери з інструментами проти ботів, розв’язанням CAPTCHA та резидентними проксі
- **Browser Use** — Альтернативний провайдер хмарних браузерів
- **Local Chromium‑family CDP** — Підключення до запущеного Chrome, Brave, Chromium або Edge через `/browser connect`
- **Local Chromium** — Безголовий локальний браузер через CLI `agent-browser`

Дивись [Browser Automation](/user-guide/features/browser) для налаштування та використання.

## Провайдери голосу та TTS

Текст‑у‑мову та мовлення‑у‑текст для всіх платформ обміну повідомленнями:

| Провайдер | Якість | Вартість | API‑ключ |
|-----------|--------|----------|----------|
| **Edge TTS** (за замовчуванням) | Good | Free | None needed |
| **ElevenLabs** | Excellent | Paid | `ELEVENLABS_API_KEY` |
| **OpenAI TTS** | Good | Paid | `VOICE_TOOLS_OPENAI_KEY` |
| **MiniMax** | Good | Paid | `MINIMAX_API_KEY` |
| **xAI TTS** | Good | Paid | `XAI_API_KEY` |
| **NeuTTS** | Good | Free | None needed |

Мовлення‑у‑текст підтримує шість провайдерів: локальний faster‑whisper (безкоштовний, працює на пристрої), локальний обгортковий командний інструмент, Groq, OpenAI Whisper API, Mistral та xAI. Транскрипція голосових повідомлень працює в Telegram, Discord, WhatsApp та інших платформах. Дивись [Voice & TTS](/user-guide/features/tts) та [Voice Mode](/user-guide/features/voice-mode) для деталей.

## Інтеграція IDE та редакторів

- **[IDE Integration (ACP)](/user-guide/features/acp)** — Використовуй Hermes Agent всередині редакторів, сумісних з ACP, таких як VS Code, Zed та JetBrains. Hermes працює як сервер ACP, відображаючи чат‑повідомлення, активність інструментів, дифи файлів та команди терміналу безпосередньо у твоєму редакторі.

## Програмний доступ

- **[API Server](/user-guide/features/api-server)** — Експонуй Hermes як HTTP‑кінцеву точку, сумісну з OpenAI. Будь‑який фронтенд, що розуміє формат OpenAI — Open WebUI, LobeChat, LibreChat, NextChat, ChatBox — може підключитися та використовувати Hermes як бекенд зі всім набором інструментів.

## Пам’ять та персоналізація

- **[Built-in Memory](/user-guide/features/memory)** — Постійна, курована пам’ять через файли `MEMORY.md` та `USER.md`. Агент підтримує обмежені сховища особистих нотаток і даних профілю користувача, які зберігаються між сесіями.
- **[Memory Providers](/user-guide/features/memory-providers)** — Підключай зовнішні бекенди пам’яті для глибшої персоналізації. Підтримуються вісім провайдерів: Honcho (діалектичне міркування), OpenViking (багаторівневий пошук), Mem0 (хмарний видобуток), Hindsight (графи знань), Holographic (локальний SQLite), RetainDB (гібридний пошук), ByteRover (CLI‑базований) та Supermemory.

## Платформи обміну повідомленнями

Hermes працює як шлюз‑бот на більш ніж 27 платформах, всі налаштовуються через підсистему `gateway`:

- **[Telegram](/user-guide/messaging/telegram)**, **[Discord](/user-guide/messaging/discord)**, **[Slack](/user-guide/messaging/slack)**, **[WhatsApp](/user-guide/messaging/whatsapp)**, **[Signal](/user-guide/messaging/signal)**, **[Matrix](/user-guide/messaging/matrix)**, **[Mattermost](/user-guide/messaging/mattermost)**, **[Email](/user-guide/messaging/email)**, **[SMS](/user-guide/messaging/sms)**, **[DingTalk](/user-guide/messaging/dingtalk)**, **[Feishu/Lark](/user-guide/messaging/feishu)**, **[WeCom](/user-guide/messaging/wecom)**, **[WeCom Callback](/user-guide/messaging/wecom-callback)**, **[Weixin](/user-guide/messaging/weixin)**, **[BlueBubbles](/user-guide/messaging/bluebubbles)**, **[QQ Bot](/user-guide/messaging/qqbot)**, **[Yuanbao](/user-guide/messaging/yuanbao)**, **[Home Assistant](/user-guide/messaging/homeassistant)**, **[Microsoft Teams](/user-guide/messaging/teams)**, **[Microsoft Teams Meetings](/user-guide/messaging/teams-meetings)**, **[Microsoft Graph Webhook](/user-guide/messaging/msgraph-webhook)**, **[Google Chat](/user-guide/messaging/google_chat)**, **[LINE](/user-guide/messaging/line)**, **[ntfy](/user-guide/messaging/ntfy)**, **[SimpleX](/user-guide/messaging/simplex)**, **[Open WebUI](/user-guide/messaging/open-webui)**, **[Webhooks](/user-guide/messaging/webhooks)**

Дивись [Messaging Gateway overview](/user-guide/messaging) для таблиці порівняння платформ та інструкції з налаштування.

## Домашня автоматизація

- **[Home Assistant](/user-guide/messaging/homeassistant)** — Керуйте розумними пристроями через чотири спеціалізовані інструменти (`ha_list_entities`, `ha_get_state`, `ha_list_services`, `ha_call_service`). Набір інструментів Home Assistant активується автоматично, коли налаштовано `HASS_TOKEN`.

## Плагіни

- **[Plugin System](/user-guide/features/plugins)** — Розширюй Hermes власними інструментами, хуками життєвого циклу та командами CLI без зміни ядра. Плагіни виявляються у `~/.hermes/plugins/`, у проектних `.hermes/plugins/` та у встановлених pip‑точках входу.
- **[Build a Plugin](/guides/build-a-hermes-plugin)** — Покрокова інструкція зі створення плагінів Hermes з інструментами, хуками та командами CLI.

## Тренування та оцінка

- **[Batch Processing](/user-guide/features/batch-processing)** — Запускай агента на сотнях запитів паралельно, генеруючи структуровані дані траєкторій у форматі ShareGPT для створення навчальних даних або оцінки.