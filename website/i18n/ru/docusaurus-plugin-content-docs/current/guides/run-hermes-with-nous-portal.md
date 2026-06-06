---
sidebar_position: 1
title: "Запусти Hermes Agent с Nous Portal"
description: "Пошаговое руководство от начала до конца: подписка, настройка, переключение моделей, включение шлюза инструментов и проверка маршрутизации"
---

# Запуск Hermes Agent с Nous Portal

Это руководство проведёт тебя через процесс запуска Hermes Agent на подписке [Nous Portal](https://portal.nousresearch.com) от начала до конца — от регистрации до проверки корректной маршрутизации каждого инструмента. Если тебе нужен лишь обзор того, что такое Portal и что включено в подписку, смотри [страницу интеграции Nous Portal](/integrations/nous-portal). Эта страница — скрипт задачи.
## Предварительные требования

- Hermes Agent установлен ([Quickstart](/getting-started/quickstart))
- Веб‑браузер на машине, которую ты настраиваешь (или SSH‑перенаправление портов — см. [OAuth over SSH](/guides/oauth-over-ssh))
- Около 5 минут

Тебе **не** нужны: ключ OpenAI, ключ Anthropic, аккаунт Firecrawl, аккаунт FAL, аккаунт Browser Use или любые другие учётные данные от поставщиков. В этом и заключается суть.
## 1. Оформить подписку

Open [portal.nousresearch.com/manage-subscription](https://portal.nousresearch.com/manage-subscription), sign up, and pick a plan.

Уже подписан? Перейди к шагу 2.
## 2. Запуск одноразовой настройки

```bash
hermes setup --portal
```

Эта единственная команда делает пять вещей:

1. Открывает твой браузер на portal.nousresearch.com для входа через OAuth
2. Сохраняет токен обновления в `~/.hermes/auth.json`
3. Устанавливает `model.provider: nous` в `~/.hermes/config.yaml`
4. Выбирает агентную модель по умолчанию (`anthropic/claude-sonnet-4.6` или аналогичную)
5. Включает шлюз инструментов для веб‑поиска, генерации изображений, TTS и автоматизации браузера

Когда она завершится, ты вернёшься в терминал, готовый к общению.

### Что делать, если я подключён к серверу по SSH?

OAuth требует браузер, но loopback‑callback работает на машине, где запущен Hermes. Два варианта:

```bash
# Option A: SSH port forwarding (preferred)
ssh -N -L 8642:127.0.0.1:8642 user@remote-host    # in a local terminal
hermes setup --portal                              # on the remote, open the printed URL in your local browser

# Option B: manual paste (for Cloud Shell, Codespaces, EC2 Instance Connect)
hermes auth add nous --type oauth --manual-paste
# Then re-run `hermes setup --portal` to wire the provider + gateway
```

Смотри [OAuth over SSH / Remote Hosts](/guides/oauth-over-ssh) для полного руководства, включая цепочки ProxyJump, mosh/tmux и gotchas ControlMaster.
## 3. Убедись, что всё работает

```bash
hermes portal status
```

Ты должен увидеть:

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
```

Если какая‑либо строка показывает что‑то, отличное от «via Nous Portal», или строка аутентификации содержит «not logged in», перейди к разделу [Troubleshooting](#troubleshooting) ниже.
## 4. Запусти свой первый разговор

```bash
hermes chat
```

Попробуй что‑нибудь, что задействует и модель, и шлюз инструментов:

```
Hey, search the web for "Hermes Agent release notes" and summarize the top 3 hits.
```

Ты увидишь, как Hermes вызывает `web_search` (на базе Firecrawl, через шлюз инструментов) и отвечает сводкой. Если поиск выполнится и ответ будет осмысленным, всё готово — Portal подключён сквозным образом.
## 5. Выбери нужную модель

По умолчанию после `hermes setup --portal` используется разумная универсальная модель, но вся суть подписки — доступ к полному каталогу. Переключись с помощью `/model` в середине сессии:

```bash
/model anthropic/claude-sonnet-4.6     # best general-purpose agentic
/model openai/gpt-5.4                  # strong reasoning + tool calling
/model google/gemini-2.5-pro           # huge context window
/model deepseek/deepseek-v3.2          # cost-effective coder
/model anthropic/claude-opus-4.6       # heavyweight for hard problems
```

Или открой селектор для просмотра:

```bash
/model
```

Установи другую модель по умолчанию навсегда:

```bash
# in your terminal, outside any session
hermes config set model.default anthropic/claude-sonnet-4.6
```

### Не выбирай Hermes-4 для работы агента

Hermes-4-70B и Hermes-4-405B доступны на Портале со значительными скидками, но это **чат‑ и рассуждательные модели**, а не оптимизированные под вызов инструментов. Они будут с трудом справляться с многошаговыми циклами агента. Используй их через [Nous Chat](https://chat.nousresearch.com) для разговоров/исследований или через [прокси подписки](/user-guide/features/subscription-proxy) из неагентских инструментов. Для самого Hermes Agent используй перечисленные выше передовые агентные модели.

На собственной [информационной странице Портала](https://portal.nousresearch.com/info) также есть это предупреждение — это официальные рекомендации Nous, а не просто мнение со стороны Hermes.
## 6. (Опционально) Настройка маршрутизации шлюза инструментов

Шлюз инструментов включается отдельно для каждого инструмента, а не «всё или ничего». Если у тебя уже есть аккаунт Browserbase и ты хочешь продолжать его использовать, одновременно направляя веб‑поиск и генерацию изображений через Nous, это поддерживается:

```bash
hermes tools
# → Web search       → "Nous Subscription"     (recommended)
# → Image generation → "Nous Subscription"     (recommended)
# → Browser          → "Browserbase"           (your existing key)
# → TTS              → "Nous Subscription"     (recommended)
```

Проверь свою конфигурацию:

```bash
hermes portal tools
```

Ты увидишь маршрутизацию по каждому инструменту — `via Nous Portal` для тех, которые проходят через подписку, и название партнёра (`browserbase`, `firecrawl` и т.д.) для тех, которые используют твои собственные ключи.
## 7. (Optional) Включить голосовой режим

Поскольку шлюз инструментов включает OpenAI TTS, [голосовой режим](/user-guide/features/voice-mode) работает без отдельного ключа OpenAI:

```bash
hermes setup voice
# → pick "Nous Subscription" for TTS
# → pick a speech-to-text backend (local faster-whisper is free, no setup)
```

Затем в любой сессии платформы обмена сообщениями (Telegram, Discord, Signal и т.д.) отправь голосовое сообщение, и Hermes расшифрует его, ответит и отправит синтезированный голос — всё в рамках твоей подписки на Portal.
## 8. (Optional) Cron + always‑on workflows

Подписка в Portal работает для [cron jobs](/user-guide/features/cron) и [batch processing](/user-guide/features/batch-processing) так же, как и для интерактивного чата — OAuth refresh token автоматически переиспользуется. Никакой дополнительной настройки; просто планируй cron‑задачи, и они будут списываться с твоей подписки.

```bash
hermes cron create "every day at 9am" \
  "Search the web for top AI news and summarize the 5 most important stories" \
  --name "Daily AI news"
```

Cron‑задача запускается без вмешательства, вызывает модель + веб‑поиск + суммирование через твою подписку в Portal.
## Профили и многопользовательские настройки

Если ты используешь [Hermes profiles](/user-guide/profiles) (например, отдельный конфиг для каждого проекта), токен обновления Portal автоматически делится между всеми профилями через общий магазин токенов. Войди один раз в любом профиле — и остальные получат токен автоматически.

Для командных настроек, когда несколько человек используют одну машину, у каждого человека есть свой аккаунт Portal → в каждом домашнем каталоге хранится свой `~/.hermes/auth.json` → токены не делятся между пользователями. Это правильное разделение.
## Устранение неполадок

### `hermes portal status` показывает «not logged in» после `hermes setup --portal`

OAuth‑процесс не завершился. Запусти его снова:

```bash
hermes auth add nous --type oauth
```

Если браузер не открывается или обратный вызов не срабатывает, скорее всего ты находишься на удалённом/безголовом хосте — смотри [OAuth over SSH](/guides/oauth-over-ssh) для настройки проброса портов и ручных обходов.

### «Model: currently openrouter» (или другой провайдер) вместо «using Nous as inference provider»

Твоя локальная конфигурация отклонилась. OAuth прошёл, но `model.provider` всё ещё указывает на другой провайдер. Исправь:

```bash
hermes config set model.provider nous
```

Или интерактивно:

```bash
hermes model
# pick Nous Portal
```

Проверь снова с помощью `hermes portal status`.

### Инструменты шлюза инструментов показывают имена партнёров вместо «via Nous Portal»

Конфигурация отдельного инструмента переопределяет шлюз. Выполни:

```bash
hermes tools
# pick "Nous Subscription" for any tool you want gateway-routed
```

Некоторые пользователи намеренно смешивают — например, маршрутизируют веб через Nous, но используют свой ключ Browserbase для браузера. Если это сделано намеренно, оставь как есть. Если нет, эта команда исправит ситуацию.

### «Re-authentication required» в середине сессии

Токен обновления Portal был аннулирован (смена пароля, ручная отзыва, истечение срока сессии). Токен теперь изолирован локально, чтобы Hermes не пытался использовать его бесконечно. Просто войди снова:

```bash
hermes auth add nous
```

Изоляция автоматически снимается после успешного повторного входа.

### Модель, которую я хочу, отсутствует в выборе `/model`

Каталог Portal отражает список моделей OpenRouter (300+). Если модель отсутствует, попробуй ввести её slug в стиле OpenRouter напрямую:

```bash
/model anthropic/claude-opus-4.6
/model openai/o1-2025-12-17
```

Если модель действительно недоступна, [открой issue](https://github.com/NousResearch/hermes-agent/issues) — большинство пробелов связаны с конфигурацией маршрутизации, которую мы можем обновить.

### Платёжные данные не отображаются в моём аккаунте Portal

`hermes portal status` подскажет, действительно ли ты маршрутизируешь трафик через Portal или через другого провайдера. Частые причины:

- `model.provider` установлен в `openrouter`/`anthropic`/и т.д., а не в `nous`
- Ошибка обновления OAuth, приведшая к использованию запасного (варианта) провайдера
- Несколько профилей Hermes, и ты используешь неправильный (проверь `hermes profile current`)

### Хочу отозвать доступ и начать с нуля

```bash
hermes auth remove nous       # wipes the local refresh token
# Then re-run setup or remove the subscription from the Portal web UI
```
## Что ты получаешь, в цифрах

| Без Portal | С Portal |
|------------|----------|
| 1× OpenRouter / Anthropic / OpenAI key в `.env` | 1× OAuth refresh token, без ключей в `.env` |
| 1× Firecrawl key для веб‑поиска | Веб‑поиск проходит через шлюз |
| 1× FAL key для генерации изображений | Генерация изображений проходит через шлюз |
| 1× Browser Use / Browserbase key для браузера | Браузер проходит через шлюз |
| 1× OpenAI key для TTS / голосового режима | TTS проходит через шлюз |
| 5 отдельных дашбордов, пополнений, счетов | 1 подписка, 1 счёт |
| Межмашинное: копировать все 5 ключей | Межмашинное: повторный OAuth один раз |

Вот в чём суть. Если ты всё равно используешь более двух из этих бэкендов, подписка окупается сама.
## Смотрите также

- **[Nous Portal integration page](/integrations/nous-portal)** — Обзор того, что включено в подписку
- **[Tool Gateway](/user-guide/features/tool-gateway)** — Полные сведения о каждом инструменте, маршрутизируемом через шлюз
- **[Subscription proxy](/user-guide/features/subscription-proxy)** — Используй подписку Portal из инструментов, не являющихся Hermes
- **[Voice mode](/user-guide/features/voice-mode)** — Настрой голосовые беседы в подписке Portal
- **[OAuth over SSH](/guides/oauth-over-ssh)** — Схемы удалённого/безголового входа
- **[Profiles](/user-guide/profiles)** — Поделись одной учётной записью Portal между несколькими конфигурациями Hermes