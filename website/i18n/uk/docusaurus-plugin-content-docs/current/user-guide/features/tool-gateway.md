---
title: "Nous шлюз інструментів"
description: "Один підпис, кожен інструмент. Веб‑пошук, генерація зображень, TTS і хмарні браузери — все маршрутизовано через Nous Portal без додаткових API‑ключів."
sidebar_label: "Tool Gateway"
sidebar_position: 2
---

# Nous Tool Gateway

**Одна підписка. Кожен інструмент включений.**

Tool Gateway включений у кожну платну підписку [Nous Portal](https://portal.nousresearch.com). Він маршрутизує виклики інструментів Hermes — веб‑пошук, генерація зображень, text‑to‑speech та автоматизація хмарного браузера — через інфраструктуру, яку вже підтримує Nous, тому тобі не потрібно реєструватися у Firecrawl, FAL, OpenAI, Browser Use чи будь‑якому іншому сервісі, лише щоб зробити агента корисним.

<div style={{display: 'flex', gap: '1rem', flexWrap: 'wrap', margin: '1.5rem 0'}}>
  <a href="https://portal.nousresearch.com/manage-subscription" style={{background: 'var(--ifm-color-primary)', color: 'white', padding: '0.75rem 1.5rem', borderRadius: '6px', textDecoration: 'none', fontWeight: 'bold'}}>Start or manage subscription →</a>
</div>

## Що включено

| | Інструмент | Що ти отримуєш |
|---|---|---|
| 🔍 | **Web search & extract** | Веб‑пошук рівня агента та повна екстракція сторінок через Firecrawl. Немає обмежень швидкості — шлюз сам масштабує. |
| 🎨 | **Image generation** | Дев’ять моделей в одному ендпоінті: **FLUX 2 Klein 9B**, **FLUX 2 Pro**, **Z-Image Turbo**, **Nano Banana Pro** (Gemini 3 Pro Image), **GPT Image 1.5**, **GPT Image 2**, **Ideogram V3**, **Recraft V4 Pro**, **Qwen Image**. Вибирай модель прапорцем під час генерації або залишай Hermes вибирати FLUX 2 Klein за замовчуванням. |
| 🔊 | **Text-to-speech** | Голоси OpenAI TTS, підключені до інструмента `text_to_speech`. Надсилай голосові нотатки в Telegram, генеруй аудіо для пайплайнів, озвучуй будь‑що. |
| 🌐 | **Cloud browser automation** | Сесії headless Chromium через Browser Use. `browser_navigate`, `browser_click`, `browser_type`, `browser_vision` — всі примітиви для агента, без потреби в обліковому записі Browserbase. |

Усі чотири інструменти оплачуються за використання у рамках твоєї підписки Nous. Використовуй будь‑яку комбінацію — запускай шлюз для веб‑пошуку та зображень, залишаючи власний ключ ElevenLabs для TTS, або маршрутизуй усе через Nous.

## Чому це потрібно

Створення агента, який справді *щось робить*, вимагає підключення 5+ API‑підписок — кожна зі своїм процесом реєстрації, обмеженнями, білінгом та нюансами. Шлюз об’єднує це в один обліковий запис:

- **Один рахунок.** Платиш Nous; ми діємо далі.
- **Одна реєстрація.** Не потрібно реєструвати Firecrawl, FAL, Browser Use чи OpenAI audio.
- **Один ключ.** Твій OAuth у Nous Portal покриває кожен інструмент.
- **Така ж якість.** Ті ж бекенди, що й при прямому використанні ключа, лише через наш шлюз.

Можеш підключати власні ключі в будь‑який момент — по‑інструменту, коли захочеш. Шлюз не є блокуванням, а скороченням шляху.

## Перші кроки

Найшвидший шлях для нової інсталяції:

```bash
hermes setup --portal     # Nous OAuth, set Nous as provider, and turn on the Tool Gateway in one go
```

Вже налаштований Hermes? Просто переключи провайдера:

```bash
hermes model              # Pick Nous Portal — Hermes will offer to turn on the Tool Gateway
```

Коли обираєш Nous Portal, Hermes пропонує увімкнути Tool Gateway. Підтверди — і все готово: кожен підтримуваний інструмент активний вже під час наступного запуску.

Перевірити, що активовано, можна в будь‑який момент:

```bash
hermes portal status      # Portal auth + Tool Gateway routing summary
hermes portal tools       # Gateway catalog with current routing per tool
hermes status             # Full system status (Tool Gateway is one section)
```

`hermes portal status` показує розділ типу:

```
◆ Nous Tool Gateway
  Nous Portal     ✓ managed tools available
  Web tools       ✓ active via Nous subscription
  Image gen       ✓ active via Nous subscription
  TTS             ✓ active via Nous subscription
  Browser         ○ active via Browser Use key
```

Інструменти, позначені «active via Nous subscription», проходять через шлюз. Все інше використовує твої власні ключі.

## Право на використання

Tool Gateway — це функція **платної підписки**. Безкоштовні акаунти Nous можуть користуватись Portal для інференсу, але не отримують керованих інструментів — [онови план](https://portal.nousresearch.com/manage-subscription), щоб розблокувати шлюз.

## Комбінуйте як хочете

Шлюз працює по‑інструменту. Увімкни його лише для потрібного:

- **Всі інструменти через Nous** — найпростіше; одна підписка, готово.
- **Шлюз для вебу + зображень, власний TTS** — залишай свій ElevenLabs голос, а Nous бере решту.
- **Шлюз лише для тих, у кого немає ключів** — «У мене вже є Browserbase, а Firecrawl не потрібен» працює без проблем.

Перемкнути будь‑який інструмент у будь‑який момент можна через:

```bash
hermes tools          # Interactive picker for each tool category
```

Обери інструмент, вибери **Nous Subscription** як провайдера (або будь‑якого прямого провайдера). Ніякого редагування конфігурації не потрібно.

## Використання окремих моделей зображень

За замовчуванням генерація зображень використовує FLUX 2 Klein 9B за швидкістю. Перевизначити модель можна, передавши її ID інструменту `image_generate`:

| Модель | ID | Найкраще для |
|---|---|---|
| FLUX 2 Klein 9B | `fal-ai/flux-2/klein/9b` | Швидко, хороший базовий варіант |
| FLUX 2 Pro | `fal-ai/flux-2/pro` | Вища якість FLUX |
| Z-Image Turbo | `fal-ai/z-image/turbo` | Стилізовано, швидко |
| Nano Banana Pro | `fal-ai/gemini-3-pro-image` | Google Gemini 3 Pro Image |
| GPT Image 1.5 | `fal-ai/gpt-image-1/5` | OpenAI генерація, текст+зображення |
| GPT Image 2 | `fal-ai/gpt-image-2` | Остання модель OpenAI |
| Ideogram V3 | `fal-ai/ideogram/v3` | Сильна відповідність підказкам + типографіка |
| Recraft V4 Pro | `fal-ai/recraft/v4/pro` | Векторний стиль, графічний дизайн |
| Qwen Image | `fal-ai/qwen-image` | Alibaba мультимодальна |

Набір оновлюється — `hermes tools` → Image Generation показує актуальний список.

---

## Довідка з конфігурації

Більшість користувачів ніколи не торкаються цього — `hermes model` і `hermes tools` охоплюють усі робочі процеси інтерактивно. Цей розділ призначений для прямого редагування `config.yaml` або скриптів.

### Прапорець `use_gateway` для інструмента

У кожному блоці конфігурації інструмента є булевий параметр `use_gateway`:

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

Пріоритет: `use_gateway: true` маршрутує через Nous незалежно від будь‑яких прямих ключів у `.env`. `use_gateway: false` (або відсутність) використовує прямі ключі, якщо вони є, і лише при їх відсутності переходить до шлюзу.

### Вимкнення шлюзу

```yaml
web:
  use_gateway: false   # Hermes now uses FIRECRAWL_API_KEY from .env
```

`hermes tools` автоматично скидає прапорець, коли ти обираєш провайдера без шлюзу, тому це зазвичай відбувається самостійно.

### Самостійно розгорнутий шлюз (просунутий)

Запускаєш власний сумісний з Nous шлюз? Перевизначи ендпоінти у `~/.hermes/.env`:

```bash
TOOL_GATEWAY_DOMAIN=your-domain.example.com
TOOL_GATEWAY_SCHEME=https
TOOL_GATEWAY_USER_TOKEN=your-token        # normally auto-populated from Portal login
FIRECRAWL_GATEWAY_URL=https://...         # override one endpoint specifically
```

Ці налаштування потрібні для кастомної інфраструктури (корпоративні розгортання, dev‑середовища). Звичайні підписники їх не використовують.

## FAQ

### Чи працює це з Telegram / Discord / іншими шлюзами обміну повідомленнями?

Так. Tool Gateway працює на рівні виконання інструмента, а не CLI. Будь‑який інтерфейс, який може викликати інструмент — CLI, Telegram, Discord, Slack, IRC, Teams, API‑сервер, будь‑що — користується ним прозоро.

### Що станеться, якщо моя підписка закінчиться?

Інструменти, що проходять через шлюз, перестануть працювати, доки ти не оновиш підписку або не підставиш прямі API‑ключі через `hermes tools`. Hermes виведе чітку помилку з посиланням на портал.

### Чи можна побачити використання чи витрати по інструменту?

Так — [дашборд Nous Portal](https://portal.nousresearch.com) розбиває використання за інструментами, щоб ти бачив, що саме формує рахунок.

### Чи включений Modal (безсерверний термінал)?

Modal доступний як **додаткова опція** у підписці Nous, не входить у базовий пакет Tool Gateway. Налаштуй його через `hermes setup terminal` або безпосередньо у `config.yaml`, коли потрібен віддалений пісочний простір для виконання команд.

### Чи треба видаляти існуючі API‑ключі, коли я вмикаю шлюз?

Ні — залишай їх у `.env`. Коли `use_gateway: true`, Hermes ігнорує прямі ключі і користується шлюзом. Поверни прапорець у `false`, і твої ключі знову стануть джерелом. Шлюз не є блокуванням.