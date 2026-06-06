---
title: "Nous шлюз инструментов"
description: "Одна подписка, каждый инструмент. Веб‑поиск, генерация изображений, TTS и облачные браузеры — всё проходит через Nous Portal без дополнительных API‑ключей."
sidebar_label: "Tool Gateway"
sidebar_position: 2
---

# Nous Tool Gateway

**Одна подписка. Все инструменты включены.**

Tool Gateway включён в каждую платную подписку [Nous Portal](https://portal.nousresearch.com). Он направляет вызовы инструментов Hermes — веб‑поиск, генерацию изображений, преобразование текста в речь и автоматизацию облачного браузера — через инфраструктуру, которую уже управляет Nous, так что тебе не нужно регистрироваться в Firecrawl, FAL, OpenAI, Browser Use или где‑то ещё, лишь бы твой агент был полезен.

<div style={{display: 'flex', gap: '1rem', flexWrap: 'wrap', margin: '1.5rem 0'}}>
  <a href="https://portal.nousresearch.com/manage-subscription" style={{background: 'var(--ifm-color-primary)', color: 'white', padding: '0.75rem 1.5rem', borderRadius: '6px', textDecoration: 'none', fontWeight: 'bold'}}>Start or manage subscription →</a>
</div>

## Что включено

| | Инструмент | Что ты получаешь |
|---|---|---|
| 🔍 | **Web search & extract** | Веб‑поиск уровня агента и извлечение полной страницы через Firecrawl. Нет ограничений по частоте — шлюз инструментов сам масштабируется. |
| 🎨 | **Image generation** | Девять моделей через одну точку входа: **FLUX 2 Klein 9B**, **FLUX 2 Pro**, **Z-Image Turbo**, **Nano Banana Pro** (Gemini 3 Pro Image), **GPT Image 1.5**, **GPT Image 2**, **Ideogram V3**, **Recraft V4 Pro**, **Qwen Image**. Выбирай модель флагом при генерации или позволь Hermes использовать FLUX 2 Klein по умолчанию. |
| 🔊 | **Text-to-speech** | Голоса OpenAI TTS, встроенные в инструмент `text_to_speech`. Отправляй голосовые заметки в Telegram, генерируй аудио для пайплайнов, озвучивай всё, что нужно. |
| 🌐 | **Cloud browser automation** | Сессии безголового Chromium через Browser Use. `browser_navigate`, `browser_click`, `browser_type`, `browser_vision` — все primitives для агента, без необходимости аккаунта Browserbase. |

Все четыре инструмента оплачиваются по мере использования в рамках твоей подписки Nous. Используй любую комбинацию — запусти шлюз инструментов для веба и изображений, оставив свой ключ ElevenLabs для TTS, или направляй всё через Nous.

## Почему это нужно

Создать агента, который действительно *что‑то делает*, значит собрать более 5 подписок на API — каждая со своей регистрацией, ограничениями, биллингом и особенностями. Шлюз инструментов объединяет всё это в одну учётную запись:

- **Один счёт.** Платишь Nous; мы делаем всё остальное.
- **Одна регистрация.** Нет аккаунтов Firecrawl, FAL, Browser Use или OpenAI audio.
- **Один ключ.** Твой OAuth Nous Portal покрывает каждый инструмент.
- **То же качество.** Те же бекэнды, что и при прямом использовании ключей, только через наш фронтенд.

Можно подключать свои ключи в любой момент — по‑инструменту, когда захочешь. Шлюз — не привязка, а ускоритель.

## Как начать

Самый быстрый путь для новой установки:

```bash
hermes setup --portal     # Nous OAuth, set Nous as provider, and turn on the Tool Gateway in one go
```

Уже настроил Hermes? Просто переключи провайдера:

```bash
hermes model              # Pick Nous Portal — Hermes will offer to turn on the Tool Gateway
```

Когда выбираешь Nous Portal, Hermes предлагает включить Tool Gateway. Прими, и всё готово — каждый поддерживаемый инструмент будет доступен со следующего запуска.

Проверить, что активно, можно в любой момент:

```bash
hermes portal status      # Portal auth + Tool Gateway routing summary
hermes portal tools       # Gateway catalog with current routing per tool
hermes status             # Full system status (Tool Gateway is one section)
```

`hermes portal status` выводит раздел вроде:

```
◆ Nous Tool Gateway
  Nous Portal     ✓ managed tools available
  Web tools       ✓ active via Nous subscription
  Image gen       ✓ active via Nous subscription
  TTS             ✓ active via Nous subscription
  Browser         ○ active via Browser Use key
```

Инструменты, отмеченные «active via Nous subscription», идут через шлюз. Всё остальное использует твои собственные ключи.

## Требования

Tool Gateway — функция **платной подписки**. Бесплатные аккаунты Nous могут использовать Portal для инференса, но не включают управляемые инструменты — [обнови план](https://portal.nousresearch.com/manage-subscription), чтобы открыть шлюз.

## Сочетания

Шлюз привязывается к каждому инструменту. Включай его только для нужного:

- **Все инструменты через Nous** — самый простой вариант; одна подписка, всё готово.
- **Шлюз для веба + изображений, свой TTS** — оставляй голос ElevenLabs, а Nous берёт остальное.
- **Шлюз только для тех, у кого нет ключей** — «У меня уже есть Browserbase, но я не хочу аккаунт Firecrawl» работает без проблем.

Переключать любой инструмент можно в любой момент через:

```bash
hermes tools          # Interactive picker for each tool category
```

Выбери инструмент, укажи **Nous Subscription** как провайдера (или любой другой прямой провайдер). Правка конфигурации не требуется.

## Использование отдельных моделей изображений

Генерация изображений по умолчанию использует FLUX 2 Klein 9B для скорости. Переопределить модель можно, передав её ID в инструмент `image_generate`:

| Модель | ID | Лучшее применение |
|---|---|---|
| FLUX 2 Klein 9B | `fal-ai/flux-2/klein/9b` | Быстро, хороший вариант по умолчанию |
| FLUX 2 Pro | `fal-ai/flux-2/pro` | Более высокая точность FLUX |
| Z-Image Turbo | `fal-ai/z-image/turbo` | Стильный, быстрый |
| Nano Banana Pro | `fal-ai/gemini-3-pro-image` | Google Gemini 3 Pro Image |
| GPT Image 1.5 | `fal-ai/gpt-image-1/5` | Генерация изображений OpenAI, текст + изображение |
| GPT Image 2 | `fal-ai/gpt-image-2` | Последняя версия OpenAI |
| Ideogram V3 | `fal-ai/ideogram/v3` | Сильное соблюдение промптов + типографика |
| Recraft V4 Pro | `fal-ai/recraft/v4/pro` | Векторный стиль, графический дизайн |
| Qwen Image | `fal-ai/qwen-image` | Alibaba multimodal |

Набор меняется — `hermes tools` → Image Generation показывает текущий живой список.

---

## Справочник конфигурации

Большинству пользователей это не понадобится — `hermes model` и `hermes tools` покрывают все рабочие процессы интерактивно. Этот раздел предназначен для прямого редактирования `config.yaml` или скриптовой настройки.

### Флаг `use_gateway` для каждого инструмента

В блоке конфигурации каждого инструмента указывается булево `use_gateway`:

```yaml
web:
  backend: firecrawl
  use_gateway: true

image_gen:
  use_gateway: true

tts:
  provider: openai
  use_gateway: true

browser:
  cloud_provider: browser-use
  use_gateway: true
```

Приоритет: `use_gateway: true` направляет запросы через Nous независимо от наличия прямых ключей в `.env`. `use_gateway: false` (или отсутствие флага) использует прямые ключи, если они есть, и только при их отсутствии переходит к шлюзу.

### Отключение шлюза

```yaml
web:
  use_gateway: false   # Hermes now uses FIRECRAWL_API_KEY from .env
```

`hermes tools` автоматически сбрасывает флаг, когда ты выбираешь провайдера, не использующего шлюз, так что обычно это делается за тебя.

### Самостоятельно развернутый шлюз (продвинуто)

Запускаешь собственный совместимый с Nous шлюз? Переопредели конечные точки в `~/.hermes/.env`:

```bash
TOOL_GATEWAY_DOMAIN=your-domain.example.com
TOOL_GATEWAY_SCHEME=https
TOOL_GATEWAY_USER_TOKEN=your-token        # normally auto-populated from Portal login
FIRECRAWL_GATEWAY_URL=https://...         # override one endpoint specifically
```

Эти параметры нужны для кастомных инфраструктур (корпоративные развертывания, dev‑окружения). Обычным подписчикам их не требуется менять.

## FAQ

### Работает ли это с Telegram / Discord / другими мессенджерами?

Да. Tool Gateway работает на уровне выполнения инструмента, а не CLI. Любой интерфейс, который может вызвать инструмент — CLI, Telegram, Discord, Slack, IRC, Teams, API‑сервер и т.д. — получает выгоду прозрачно.

### Что произойдёт, если моя подписка истечёт?

Инструменты, маршрутизируемые через шлюз, перестанут работать, пока ты не продлишь подписку или не заменишь их прямыми API‑ключами через `hermes tools`. Hermes покажет чёткую ошибку, указывающую на портал.

### Можно ли увидеть использование или стоимость по каждому инструменту?

Да — панель [Nous Portal dashboard](https://portal.nousresearch.com) разбивает использование по инструментам, так что ты видишь, что именно формирует счёт.

### Входит ли Modal (серверлесс‑терминал) в комплект?

Modal доступен как **опциональное дополнение** через подписку Nous, но не входит в базовый набор Tool Gateway. Настраивай его через `hermes setup terminal` или напрямую в `config.yaml`, когда нужен удалённый песочничный терминал.

### Нужно ли удалять существующие API‑ключи, когда я включаю шлюз?

Нет — оставляй их в `.env`. При `use_gateway: true` Hermes игнорирует прямые ключи и использует шлюз. Сбрось флаг обратно в `false`, и твои ключи снова станут источником. Шлюз — не привязка.