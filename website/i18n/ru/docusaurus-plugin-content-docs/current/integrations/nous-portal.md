---
sidebar_position: 1
title: "Nous Portal"
description: "Одна подписка, более 300 передовых моделей, шлюз инструментов (Tool Gateway) и Nous Chat — рекомендуемый способ запуска Hermes Agent"
---

# Nous Portal

[Nous Portal](https://portal.nousresearch.com) — единый **subscription gateway** Nous Research и **рекомендованный способ запуска Hermes Agent**. Один вход через OAuth заменяет необходимость управлять отдельными учётными записями, API‑ключами и платёжными отношениями для каждой лаборатории моделей, поискового API, генератора изображений и провайдера браузера, которые иначе пришлось бы настраивать вручную.

Если у тебя есть время только на одну настройку, настрой её. Самый быстрый путь:

```bash
hermes setup --portal
```

Эта единственная команда запускает OAuth **gateway**, задаёт Nous в качестве **inference provider** в `config.yaml` и включает **Tool Gateway**. Ты сразу готов к `hermes chat`.

Ещё нет подписки? [portal.nousresearch.com/manage-subscription](https://portal.nousresearch.com/manage-subscription) — зарегистрируйся, затем вернись и выполни команду выше.
## Что входит в подписку

### 300+ передовых моделей, один счёт

Портал проксирует отобранный каталог агентных моделей из разных частей экосистемы — оплата происходит по твоей подписке Nous, а не по отдельному кредитному балансу за каждый лабораторный доступ.

| Семейство | Модели |
|--------|--------|
| **Anthropic Claude** | Opus 4.7, Opus 4.6, Sonnet 4.6, Haiku 4.5 |
| **OpenAI** | GPT-5.5, GPT-5.5 Pro, GPT-5.4 Mini, GPT-5.4 Nano, GPT-5.3 Codex |
| **Google Gemini** | Gemini 3 Pro Preview, Gemini 3 Flash Preview, Gemini 3.1 Pro Preview, Gemini 3.1 Flash Lite Preview |
| **DeepSeek** | DeepSeek V4 Pro |
| **Qwen** | Qwen3.7-Max, Qwen3.6-35B-A3B |
| **Kimi / Moonshot** | Kimi K2.6 |
| **GLM / Zhipu** | GLM-5.1 |
| **MiniMax** | MiniMax M2.7 |
| **xAI** | Grok 4.3 |
| **NVIDIA** | Nemotron-3 Super 120B-A12B |
| **Tencent** | Hunyuan 3 Preview |
| **Xiaomi** | MiMo V2.5 Pro |
| **StepFun** | Step 3.5 Flash |
| **Hermes** | Hermes-4-70B, Hermes-4-405B (чат, см. [note below](#a-note-on-hermes-4)) |
| **+ всё остальное** | 280+ дополнительных моделей — полный набор агентных передовых моделей |

Маршрутизация происходит через OpenRouter, поэтому доступность моделей и поведение при отказе соответствуют тому, что ты получаешь с ключом OpenRouter — просто оплата идёт по твоей подписке Nous. Переключайся между `Claude Sonnet 4.6` для кода и `Gemini 3 Pro` для длинного контекста с помощью `/model` в середине сессии — без новых учётных данных, без пополнений, без неожиданного нулевого баланса.

### Шлюз инструментов Nous

Та же подписка открывает доступ к [Tool Gateway](/user-guide/features/tool-gateway), который маршрутизирует вызовы инструментов Hermes Agent через инфраструктуру, управляемую Nous. Пять бекендов, один вход:

| Инструмент | Партнёр | Что делает |
|------|---------|--------------|
| **Веб‑поиск & извлечение** | Firecrawl | Поиск уровня агента и извлечение полной страницы. Без ключа Firecrawl API, без ограничения скорости. |
| **Генерация изображений** | FAL | Девять моделей через одну точку доступа: FLUX 2 Klein 9B, FLUX 2 Pro, Z-Image Turbo, Nano Banana Pro (Gemini 3 Pro Image), GPT Image 1.5, GPT Image 2, Ideogram V3, Recraft V4 Pro, Qwen Image. |
| **Текст‑в‑речь** | OpenAI TTS | Высококачественный TTS без отдельного ключа OpenAI. Включает [voice mode](/user-guide/features/voice-mode) во всех платформах обмена сообщениями. |
| **Автоматизация облачного браузера** | Browser Use | Безголовые сессии Chromium для `browser_navigate`, `browser_click`, `browser_type`, `browser_vision`. Учётная запись Browserbase не требуется. |
| **Облачная терминальная песочница** | Modal | Бессерверные терминальные песочницы для выполнения кода (опциональное дополнение). |

Без шлюза подключение каждого из этих сервисов требует учётную запись Firecrawl, учётную запись FAL, учётную запись Browser Use, ключ OpenAI и учётную запись Modal — пять отдельных регистраций, пять отдельных панелей, пять отдельных потоков пополнения. С шлюзом всё маршрутизируется через одну подписку.

Можно включить только отдельные инструменты шлюза (например, веб‑поиск без генерации изображений) — см. [Mixing the gateway with your own backends](#mixing-the-gateway-with-your-own-backends) ниже.

### Nous Chat

Твой аккаунт Портала также покрывает [chat.nousresearch.com](https://chat.nousresearch.com) — веб‑интерфейс чата Nous Research с тем же каталогом моделей. Удобно, когда ты не у терминала или когда нужен обычный диалог без агента.

### Нет учётных данных в dot‑файлах

Поскольку всё проходит через одну OAuth‑аутентифицированную сессию Портала, ты не копишь файл `.env` с десятком долгоживущих API‑ключей. Токен обновления в `~/.hermes/auth.json` — единственная учётная запись на диске, а Hermes генерирует короткоживущие JWT из него для каждого запроса — см. [Token handling](#token-handling) ниже.

### Кроссплатформенная согласованность

[Native Windows](/user-guide/windows-native) всё ещё в раннем бета‑тесте, и настройка API‑ключей для каждого инструмента — самый «острый» момент — установка учётных записей Firecrawl, FAL, Browser Use и ключа OpenAI в Windows является самым трудоёмким шагом для получения полезного агента. Подписка Портала упрощает это: один OAuth покрывает модель и каждый инструмент шлюза, так что пользователи Windows получают тот же опыт, что и macOS/Linux, без ручной настройки четырёх бекендов.
## Заметка о Hermes 4

Семейство **Hermes 4** от Nous Research (Hermes-4-70B, Hermes-4-405B) доступно через Portal по сильно сниженным ценам. Это **передовые гибридные модели диалогового рассуждения** — сильные в математике, науке, выполнении инструкций, соблюдении схем, ролевой игре и написании длинных текстов.

Однако их **не рекомендуется использовать внутри Hermes Agent**. Hermes 4 настроен для диалога и рассуждения, а не для быстрого цикла вызова инструментов, на котором опирается агент. Используй их в [Nous Chat](https://chat.nousresearch.com), для исследовательских рабочих процессов или через [прокси подписки](/user-guide/features/subscription-proxy) из других инструментов — но для работы агента выбирай передовую агентную модель из каталога:

```bash
/model anthropic/claude-sonnet-4.6     # best general-purpose agentic model
/model openai/gpt-5.5-pro              # strong reasoning + tool calling
/model google/gemini-3-pro-preview     # huge context window
/model deepseek/deepseek-v4-pro        # cost-effective coder
```

Страница [информация о модели](https://portal.nousresearch.com/info) на Portal содержит то же предупреждение, так что это не мнение со стороны Hermes — это официальное руководство от Nous Research.
## Установка

### Новая установка — одной командой

```bash
hermes setup --portal
```

Это выполнит полную настройку за один раз:

1. Откроет твой браузер на `portal.nousresearch.com` для входа через OAuth
2. Сохранит refresh token в `~/.hermes/auth.json`
3. Установит Nous в качестве провайдера вывода в `~/.hermes/config.yaml`
4. Включит шлюз инструментов (web, image, TTS, маршрутизация браузера)
5. Вернёт тебя в терминал, готовый к `hermes chat`

Если у тебя ещё нет подписки, сначала зарегистрируйся на [portal.nousresearch.com/manage-subscription](https://portal.nousresearch.com/manage-subscription).

### Существующая установка — добавить Portal рядом с другими провайдерами

Если у тебя уже настроен Hermes с OpenRouter, Anthropic или любым другим провайдером и ты хочешь добавить Portal рядом с ними:

```bash
hermes model
# pick "Nous Portal" from the provider list
# browser opens, sign in, done
```

Твои текущие провайдеры останутся настроенными. Ты можешь переключаться между ними с помощью `/model` в середине сессии или `hermes model` между сессиями — Portal станет одним из доступных провайдеров, а не единственным.

### Безголовый / SSH / удалённая настройка

OAuth требует браузер, но обратный вызов loopback работает на машине, где запущен Hermes. Для удалённых хостов смотри [OAuth over SSH / Remote Hosts](/guides/oauth-over-ssh) — те же шаблоны работают для Portal, как и для любого другого провайдера на основе OAuth (`ssh -L` переадресация портов, `--manual-paste` для окружений только с браузером, таких как Cloud Shell / Codespaces).

### Настройка профиля

Если ты используешь [Hermes profiles](/user-guide/profiles), refresh token Portal автоматически делится между всеми профилями через общий пул учётных данных. Войди один раз в любом профиле, и остальные автоматически получат токен — нет необходимости повторять процесс OAuth для каждого профиля.
## Использование Портала в повседневной работе

### Проверка подключений

```bash
hermes portal status     # login status, subscription info, model + gateway routing
hermes portal tools      # detailed Tool Gateway catalog with per-tool routing
hermes portal open       # open the subscription management page in your browser
```

`hermes portal status` (или просто `hermes portal`) показывает обзор высокого уровня:

```
  Nous Portal
  ───────────
  Auth:    ✓ logged in
  Portal:  https://portal.nousresearch.com
  Model:   ✓ using Nous as inference provider

  Tool Gateway
  ────────────
  Web search & extract  via Nous Portal
  Image generation      via Nous Portal
  Text-to-speech        via Nous Portal
  Browser automation    via Nous Portal
  Cloud terminal        not configured
```

### Переключение моделей

Внутри сессии:

```bash
/model anthropic/claude-sonnet-4.6
/model openai/gpt-5.5-pro
/model google/gemini-3-pro-preview
```

Или открыть выборщик:

```bash
/model
# arrow keys, enter to select
```

Вне сессии (полный мастер настройки, полезен при добавлении нового провайдера):

```bash
hermes model
```

### Сочетание шлюза инструментов со своими бэкендами

Если у тебя уже, например, есть аккаунт Browserbase и ты хочешь продолжать его использовать, одновременно направляя веб‑поиск и генерацию изображений через Nous, это поддерживается. Используй `hermes tools`, чтобы выбирать бэкенды для каждого инструмента:

```bash
hermes tools
# → Web search       → "Nous Subscription"
# → Image generation → "Nous Subscription"
# → Browser          → "Browserbase"  (your existing key)
# → TTS              → "Nous Subscription"
```

Шлюз инструментов (Tool Gateway) включается отдельно для каждого инструмента, а не «всё или ничего». См. [документацию Шлюза инструментов](/user-guide/features/tool-gateway) для полной матрицы конфигураций по инструментам.

### Управление подпиской

Управляй своим планом, просматривай использование или меняй/отменяй подписку в любое время:

- **Web:** [portal.nousresearch.com/manage-subscription](https://portal.nousresearch.com/manage-subscription)
- **CLI‑ярлык:** `hermes portal open` (открывает ту же страницу в твоём браузере по умолчанию)
## Справочник конфигурации

После выполнения `hermes setup --portal` файл `~/.hermes/config.yaml` будет выглядеть так:

```yaml
model:
  provider: nous
  default: anthropic/claude-sonnet-4.6     # or whatever model you picked
  base_url: https://inference-api.nousresearch.com/v1
```

Настройки шлюза инструментов находятся в соответствующих разделах инструментов:

```yaml
web:
  backend: nous       # web search/extract routes through Tool Gateway

image_gen:
  provider: nous

tts:
  provider: nous

browser:
  backend: nous
```

OAuth‑токен обновления хранится отдельно в `~/.hermes/auth.json` (не в `config.yaml` — учётные данные и конфигурация намеренно разделены).
## Обработка токенов

Hermes создаёт короткоживущий JWT из сохранённого refresh‑токена Portal при каждом вызове инференса, вместо повторного использования долгоживущего API‑ключа. Жизненный цикл токена полностью автоматизирован — обновление, создание, повторная попытка при временных 401 — и ты никогда его не видишь.

Если Portal аннулирует refresh‑токен (смена пароля, ручной отзыв, истечение сессии), недействительный refresh‑токен **помещается в карантин локально**, поэтому Hermes перестаёт его использовать, и ты не получаешь поток одинаковых 401. При следующем вызове появляется чёткое сообщение «требуется повторная аутентификация». Выполни `hermes auth add nous`, чтобы войти снова; карантин будет снят после следующего успешного входа.
## Устранение неполадок

### `hermes portal status` показывает «not logged in»

Ты не завершил процесс OAuth, либо твой токен обновления был удалён. Выполни:

```bash
hermes auth add nous --type oauth
```

или используй `hermes model` и заново выбери Nous Portal.

### Появилось сообщение «re-authentication required» в середине сессии

Токен обновления Portal был аннулирован (смена пароля, ручная отзыва или истечение срока действия сессии). Выполни `hermes auth add nous`, и следующий запрос будет использовать новые учётные данные. Любой карантин старого токена будет автоматически снят после успешного повторного входа.

### Хочешь использовать конкретную модель провайдера, которую Portal не показывает

Portal проксирует запросы через OpenRouter, поэтому любая модель, поддерживаемая OpenRouter, обычно доступна. Если конкретная модель не появляется в `/model`, попробуй указать её slug в стиле OpenRouter напрямую:

```bash
/model anthropic/claude-opus-4.6
```

Если модель действительно отсутствует, [создай issue](https://github.com/NousResearch/hermes-agent/issues) — мы отображаем каталог Portal в Hermes, а пробелы обычно означают проблему с конфигурацией маршрутизации, которую можно обновить.

### Счета не отображаются в моём аккаунте Portal

Сначала проверь `hermes portal status` — если он показывает, что ты используешь другого провайдера (`Model: currently openrouter` вместо `using Nous as inference provider`), значит локальная конфигурация отклонилась. Выполни `hermes model`, выбери Nous Portal, и следующий запрос будет маршрутизирован через твою подписку.
## См. также

- **[Tool Gateway](/user-guide/features/tool-gateway)** — Полная информация о каждом инструменте шлюза, конфигурации для каждого инструмента и ценообразовании
- **[Subscription proxy](/user-guide/features/subscription-proxy)** — Используй свою подписку Portal из не‑Hermes инструментов (другие агенты, скрипты, сторонние клиенты)
- **[Voice mode](/user-guide/features/voice-mode)** — Голосовые беседы с использованием OpenAI TTS от Portal
- **[AI Providers](/integrations/providers)** — Полный каталог провайдеров, если хочешь сравнить альтернативы
- **[OAuth over SSH](/guides/oauth-over-ssh)** — Вход с удалённых хостов или в средах, где доступен только браузер
- **[Profiles](/user-guide/profiles)** — Несколько конфигураций Hermes, использующих один профиль Portal