---
title: "Популярные веб‑дизайны — 54 реальных дизайн‑систем (Stripe, Linear, Vercel) в виде HTML/CSS"
sidebar_label: "Popular Web Designs"
description: "54 реальных дизайн‑систем (Stripe, Linear, Vercel) в виде HTML/CSS"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Популярные веб‑дизайны

54 реальных дизайн‑систем (Stripe, Linear, Vercel) в виде HTML/CSS.
## Метаданные навыка

| | |
|---|---|
| Источник | Встроенный (устанавливается по умолчанию) |
| Путь | `skills/creative/popular-web-designs` |
| Версия | `1.0.0` |
| Автор | Hermes Agent + Teknium (design systems sourced from VoltAgent/awesome-design-md) |
| Лицензия | MIT |
| Платформы | linux, macos, windows |
:::info
Следующее — полное определение **skill**, которое Hermes загружает, когда этот **skill** вызывается. Это то, что агент видит как инструкции, когда **skill** активен.
:::

# Популярные веб‑дизайны

54 реальных дизайн‑системы, готовые к использованию при генерации HTML/CSS. Каждый шаблон фиксирует полный визуальный язык сайта: цветовую палитру, иерархию типографики, стили компонентов, систему отступов, тени, адаптивное поведение и практические подсказки для агента с точными значениями CSS.
## Связанные навыки дизайна

- **`claude-design`** — использовать для *процесса и эстетики* дизайна (определение объёма задания, создание вариантов, проверка локального HTML‑артефакта, избегание низкокачественного AI‑дизайна). Сочетай этот навык с другим, когда пользователь хочет тщательно продуманную страницу в стиле известного бренда: `claude-design` управляет рабочим процессом, а этот навык предоставляет визуальный словарь.
- **`design-md`** — использовать, когда результатом является формальный файл спецификации токенов **DESIGN.md**, а не отрендеренный артефакт.
## Как использовать

1. Выбери дизайн из каталога ниже
2. Загрузите его: `skill_view(name="popular-web-designs", file_path="templates/<site>.md")`
3. Используй токены дизайна и спецификации компонентов при генерации HTML
4. Скомбинируй с навыком `generative-widgets`, чтобы обслужить результат через туннель cloudflared

Каждый шаблон содержит блок **Hermes Implementation Notes** вверху с:
- заменой шрифта CDN и тегом Google Fonts `<link>` (готово к вставке)
- стеками CSS `font-family` для основных и моноширинных шрифтов
- напоминаниями использовать `write_file` для создания HTML и `browser_vision` для проверки
## Шаблон генерации HTML

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Page Title</title>
  <!-- Paste the Google Fonts <link> from the template's Hermes notes -->
  <link href="https://fonts.googleapis.com/css2?family=..." rel="stylesheet">
  <style>
    /* Apply the template's color palette as CSS custom properties */
    :root {
      --color-bg: #ffffff;
      --color-text: #171717;
      --color-accent: #533afd;
      /* ... more from template Section 2 */
    }
    /* Apply typography from template Section 3 */
    body {
      font-family: 'Inter', system-ui, sans-serif;
      color: var(--color-text);
      background: var(--color-bg);
    }
    /* Apply component styles from template Section 4 */
    /* Apply layout from template Section 5 */
    /* Apply shadows from template Section 6 */
  </style>
</head>
<body>
  <!-- Build using component specs from the template -->
</body>
</html>
```

Создай файл с помощью `write_file`, разверни его через workflow `generative-widgets` (cloudflared tunnel) и проверь результат с помощью `browser_vision`, чтобы подтвердить визуальную точность.
## Справочник по замене шрифтов

Большинство сайтов используют проприетарные шрифты, недоступные через CDN. Каждый шаблон сопоставлен с заменой из Google Fonts, сохраняющей характер дизайна. Распространённые сопоставления:

| Проприетарный шрифт | CDN‑замена | Характеристика |
|---|---|---|
| Geist / Geist Sans | Geist (on Google Fonts) | Геометрический, сжатый трекинг |
| Geist Mono | Geist Mono (on Google Fonts) | Чистый моноширинный, лигатуры |
| sohne‑var (Stripe) | Source Sans 3 | Элегантность лёгкого веса |
| Berkeley Mono | JetBrains Mono | Технический моноширинный |
| Airbnb Cereal VF | DM Sans | Округлый, дружелюбный, геометрический |
| Circular (Spotify) | DM Sans | Геометрический, тёплый |
| figmaSans | Inter | Чистый гуманистический |
| Pin Sans (Pinterest) | DM Sans | Дружелюбный, округлый |
| NVIDIA‑EMEA | Inter (or Arial system) | Промышленный, чистый |
| CoinbaseDisplay/Sans | DM Sans | Геометрический, надёжный |
| UberMove | DM Sans | Смелый, плотный |
| HashiCorp Sans | Inter | Корпоративный, нейтральный |
| waldenburgNormal (Sanity) | Space Grotesk | Геометрический, слегка сжатый |
| IBM Plex Sans/Mono | IBM Plex Sans/Mono | Доступен в Google Fonts |
| Rubik (Sentry) | Rubik | Доступен в Google Fonts |

Если CDN‑шрифт шаблона совпадает с оригиналом (Inter, IBM Plex, Rubik, Geist), потери от замены не происходит. Когда используется замена (DM Sans для Circular, Source Sans 3 для sohne‑var), следует точно соблюдать значения веса, размера и межбуквенного интервала шаблона — они несут большую визуальную идентичность, чем конкретный шрифт.
## Каталог дизайна

### AI & Machine Learning

| Template | Site | Style |
|---|---|---|
| `claude.md` | Anthropic Claude | Тёплый терракотовый акцент, чистый редакционный макет |
| `cohere.md` | Cohere | Яркие градиенты, эстетика информационно‑насыщённой панели |
| `elevenlabs.md` | ElevenLabs | Тёмный кинематографический UI, эстетика аудио‑волн |
| `minimax.md` | Minimax | Смелый тёмный интерфейс с неоновыми акцентами |
| `mistral.ai.md` | Mistral AI | Французский минимализм, пурпурные тона |
| `ollama.md` | Ollama | Терминал‑центричный, монохромная простота |
| `opencode.ai.md` | OpenCode AI | Тёмная тема, ориентированная на разработчиков, полностью моноширинный |
| `replicate.md` | Replicate | Чистый белый холст, код‑ориентированный |
| `runwayml.md` | RunwayML | Кинематографический тёмный UI, медиа‑насыщенный макет |
| `together.ai.md` | Together AI | Технический, дизайн в стиле чертежа |
| `voltagent.md` | VoltAgent | Чёрный как пустота холст, изумрудный акцент, терминал‑нативный |
| `x.ai.md` | xAI | Жёсткий монохром, футуристический минимализм, полностью моноширинный |

### Developer Tools & Platforms

| Template | Site | Style |
|---|---|---|
| `cursor.md` | Cursor | Гладкий тёмный интерфейс, градиентные акценты |
| `expo.md` | Expo | Тёмная тема, плотное межбуквенное расстояние, код‑центричный |
| `linear.app.md` | Linear | Ультра‑минимализм в тёмном режиме, точный, пурпурный акцент |
| `lovable.md` | Lovable | Игристые градиенты, дружелюбная эстетика для разработчиков |
| `mintlify.md` | Mintlify | Чистый, с зелёными акцентами, оптимизированный для чтения |
| `posthog.md` | PostHog | Игристый брендинг, тёмный UI, удобный для разработчиков |
| `raycast.md` | Raycast | Гладкий тёмный хром, яркие градиентные акценты |
| `resend.md` | Resend | Минималистичная тёмная тема, моноширинные акценты |
| `sentry.md` | Sentry | Тёмная панель, информационно‑насыщённая, розово‑пурпурный акцент |
| `supabase.md` | Supabase | Тёмная изумрудная тема, инструмент для разработчиков, ориентированный на код |
| `superhuman.md` | Superhuman | Премиальный тёмный UI, клавиатурный подход, пурпурное свечение |
| `vercel.md` | Vercel | Чёрно‑белая точность, система шрифтов Geist |
| `warp.md` | Warp | Тёмный интерфейс, похожий на IDE, блочно‑командный UI |
| `zapier.md` | Zapier | Тёплый оранжевый, дружелюбный, иллюстрации в центре внимания |

### Infrastructure & Cloud

| Template | Site | Style |
|---|---|---|
| `clickhouse.md` | ClickHouse | Жёлтый акцент, стиль технической документации |
| `composio.md` | Composio | Современный тёмный дизайн с яркими иконками интеграций |
| `hashicorp.md` | HashiCorp | Корпоративный чистый стиль, чёрно‑белый |
| `mongodb.md` | MongoDB | Брендинг с зелёным листом, фокус на документацию для разработчиков |
| `sanity.md` | Sanity | Красный акцент, контент‑ориентированный редакционный макет |
| `stripe.md` | Stripe | Фирменные пурпурные градиенты, элегантность с весом 300 |

### Design & Productivity

| Template | Site | Style |
|---|---|---|
| `airtable.md` | Airtable | Красочный, дружелюбный, эстетика структурированных данных |
| `cal.md` | Cal.com | Чистый нейтральный UI, простота, ориентированная на разработчиков |
| `clay.md` | Clay | Органические формы, мягкие градиенты, художественно‑направленный макет |
| `figma.md` | Figma | Яркие многокрасочные, игриво‑профессиональный |
| `framer.md` | Framer | Смелый чёрный и синий, движение в центре, дизайн‑ориентированный |
| `intercom.md` | Intercom | Дружелюбная синяя палитра, паттерны разговорного UI |
| `miro.md` | Miro | Яркий жёлтый акцент, бесконечный холст |
| `notion.md` | Notion | Тёплый минимализм, заголовки с засечками, мягкие поверхности |
| `pinterest.md` | Pinterest | Красный акцент, сетка «кирпич», макет, ориентированный на изображения |
| `webflow.md` | Webflow | Синий акцент, полированный маркетинговый сайт |

### Fintech & Crypto

| Template | Site | Style |
|---|---|---|
| `coinbase.md` | Coinbase | Чистый синий фирменный стиль, доверие, институциональный вид |
| `kraken.md` | Kraken | Пурпурный акцент, тёмный UI, информационно‑насыщённые панели |
| `revolut.md` | Revolut | Гладкий тёмный интерфейс, градиентные карточки, точность финтеха |
| `wise.md` | Wise | Яркий зелёный акцент, дружелюбный и понятный |

### Enterprise & Consumer

| Template | Site | Style |
|---|---|---|
| `airbnb.md` | Airbnb | Тёплый коралловый акцент, фотографии в центре, скруглённый UI |
| `apple.md` | Apple | Премиум‑пространство, SF Pro, кинематографические изображения |
| `bmw.md` | BMW | Тёмные премиальные поверхности, точный инженерный эстетический вид |
| `ibm.md` | IBM | Система дизайна Carbon, структурированная синяя палитра |
| `nvidia.md` | NVIDIA | Зелёно‑чёрная энергия, технический мощный эстетический вид |
| `spacex.md` | SpaceX | Жёсткий чёрно‑белый, изображения на весь экран, футуристический |
| `spotify.md` | Spotify | Ярко‑зелёный на тёмном фоне, жирный шрифт, ориентация на обложки альбомов |
| `uber.md` | Uber | Жёсткий чёрно‑белый, плотный шрифт, городская энергия |
## Выбор дизайна

Подбери дизайн под контент:

- **Инструменты разработчика / панели:** Linear, Vercel, Supabase, Raycast, Sentry
- **Документация / контент‑сайты:** Mintlify, Notion, Sanity, MongoDB
- **Маркетинг / посадочные страницы:** Stripe, Framer, Apple, SpaceX
- **Темный режим UI:** Linear, Cursor, ElevenLabs, Warp, Superhuman
- **Светлый / чистый UI:** Vercel, Stripe, Notion, Cal.com, Replicate
- **Игривый / дружелюбный:** PostHog, Figma, Lovable, Zapier, Miro
- **Премиум / люксовый:** Apple, BMW, Stripe, Superhuman, Revolut
- **UI с большим объёмом данных / панели:** Sentry, Kraken, Cohere, ClickHouse
- **Моноширинный / терминальный стиль:** Ollama, OpenCode, x.ai, VoltAgent