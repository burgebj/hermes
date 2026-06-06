---
sidebar_position: 1
title: "Nous Portal"
description: "Один підпис, понад 300 передових моделей, шлюз інструментів (Tool Gateway) і Nous Chat — рекомендований спосіб запуску Hermes Agent"
---

# Nous Portal

[Nous Portal](https://portal.nousresearch.com) — це уніфікований шлюз підписки Nous Research і **рекомендований спосіб запуску Hermes Agent**. Один вхід OAuth замінює клопіт з окремими обліковими записами, API‑ключами та платіжними взаємовідносинами для кожної лабораторії моделей, пошукового API, генератора зображень і провайдера браузера, які інакше доведеться налаштовувати вручну.

Якщо у тебе є час лише на одне налаштування, налаштуй саме це. Найшвидший шлях:

```bash
hermes setup --portal
```

Ця єдина команда запускає OAuth у Portal, встановлює Nous як твого провайдера інференсу у `config.yaml` і вмикає шлюз інструментів. Ти готовий одразу виконати `hermes chat`.

Ще немає підписки? [portal.nousresearch.com/manage-subscription](https://portal.nousresearch.com/manage-subscription) — зареєструйся, потім повернись і виконай команду вище.
## Що входить у підписку

### 300+ передових моделей, один рахунок

Портал проксіює відібраний каталог агентних моделей з усієї екосистеми — оплачується за твоєю підпискою Nous замість окремого кредитного балансу для кожної лабораторії.

| Family | Models |
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
| **Hermes** | Hermes-4-70B, Hermes-4-405B (chat, see [note below](#a-note-on-hermes-4)) |
| **+ everything else** | 280+ додаткових моделей — повний агентний фронтир |

Маршрутизація відбувається через OpenRouter під капотом, тому доступність моделей і поведінка відмови відповідає тому, що ти отримав би з ключем OpenRouter — лише оплачується за твоєю підпискою Nous. Перемикайся між Claude Sonnet 4.6 для коду та Gemini 3 Pro для довгого контексту за допомогою `/model` під час сесії — без нових облікових даних, без поповнень, без несподіваних помилок нульового балансу.

### Шлюз інструментів Nous

Така ж підписка розблоковує [Шлюз інструментів](/user-guide/features/tool-gateway), який маршрутизує виклики інструментів Hermes Agent через інфраструктуру, керовану Nous. П’ять бекендів, один вхід:

| Tool | Partner | What it does |
|------|---------|--------------|
| **Web search & extract** | Firecrawl | Пошук агентського рівня та повна екстракція сторінок. Без API‑ключа Firecrawl, без обмежень швидкості. |
| **Image generation** | FAL | Дев’ять моделей в одному кінцевому пункті: FLUX 2 Klein 9B, FLUX 2 Pro, Z-Image Turbo, Nano Banana Pro (Gemini 3 Pro Image), GPT Image 1.5, GPT Image 2, Ideogram V3, Recraft V4 Pro, Qwen Image. |
| **Text-to-speech** | OpenAI TTS | Якісний TTS без окремого ключа OpenAI. Дозволяє [режим голосу](/user-guide/features/voice-mode) у різних платформах обміну повідомленнями. |
| **Cloud browser automation** | Browser Use | Безголові Chromium‑сесії для `browser_navigate`, `browser_click`, `browser_type`, `browser_vision`. Не потрібен обліковий запис Browserbase. |
| **Cloud terminal sandbox** | Modal | Безсерверні термінальні пісочниці для виконання коду (опційний додаток). |

Без шлюзу підключення кожного з цих інструментів означає обліковий запис Firecrawl, обліковий запис FAL, обліковий запис Browser Use, ключ OpenAI та обліковий запис Modal — п’ять окремих реєстрацій, п’ять окремих панелей, п’ять окремих потоків поповнення. З шлюзом усе це маршрутизується через одну підписку.

Ти також можеш увімкнути лише конкретні інструменти шлюзу (наприклад, веб‑пошук, але без генерації зображень) — дивись [Mixing the gateway with your own backends](#mixing-the-gateway-with-your-own-backends) нижче.

### Nous Chat

Твій обліковий запис Порталу також охоплює [chat.nousresearch.com](https://chat.nousresearch.com) — веб‑чат інтерфейс Nous Research з тим же каталогом моделей. Корисно, коли ти не біля терміналу або для роботи без агентних розмов.

### Без облікових даних у dotfiles

Оскільки все маршрутизується через одну OAuth‑автентифіковану сесію Порталу, ти не накопичуєш файл `.env` з десятком довгоживучих API‑ключів. Токен оновлення у `~/.hermes/auth.json` — єдина облікова дані на диску, а Hermes створює короткоживучі JWT‑токени з нього для кожного запиту — дивись [Token handling](#token-handling) нижче.

### Крос‑платформна паритетність

[Native Windows](/user-guide/windows-native) ще в ранній бета‑стадії, і налаштування API‑ключів для інструментів — його «грубий» момент: встановлення облікового запису Firecrawl, облікового запису FAL, облікового запису Browser Use, ключа OpenAI у Windows — найскладніша частина отримання корисного агента. Підписка Порталу спрощує це: один OAuth покриває модель і кожен інструмент шлюзу, тому користувачі Windows отримують той самий досвід, що й macOS/Linux, без ручного налаштування чотирьох бекендів.
## Примітка щодо Hermes 4

Сімейство **Hermes 4** від Nous Research (Hermes-4-70B, Hermes-4-405B) доступне в Порталі за значно зниженими цінами. Це **фронтірні гібридно‑розумові чат‑моделі** — сильні в математиці, науці, дотриманні інструкцій, слідуванні схемам, рольовій грі та довгих текстах.

Вони **не рекомендовані для використання всередині Hermes Agent**, проте Hermes 4 налаштований на чат і розуміння, а не на швидкісний цикл виклику інструментів, на якому базується агент. Використовуй їх у [Nous Chat](https://chat.nousresearch.com), у дослідницьких робочих процесах або через [проксі підписки](/user-guide/features/subscription-proxy) з інших інструментів — але для роботи агента обери фронтірну агентну модель з каталогу:

```bash
/model anthropic/claude-sonnet-4.6     # best general-purpose agentic model
/model openai/gpt-5.5-pro              # strong reasoning + tool calling
/model google/gemini-3-pro-preview     # huge context window
/model deepseek/deepseek-v4-pro        # cost-effective coder
```

Сторінка [інформації про модель](https://portal.nousresearch.com/info) у Порталі містить те ж саме попередження, тому це не думка Hermes — це офіційна рекомендація від Nous Research.
## Налаштування

### Свіжа інсталяція — одна команда

```bash
hermes setup --portal
```

Це виконує повне налаштування одним кроком:

1. Відкриває твій браузер на portal.nousresearch.com для OAuth‑входу
2. Зберігає токен оновлення у `~/.hermes/auth.json`
3. Встановлює Nous як твого провайдера інференції у `~/.hermes/config.yaml`
4. Вмикає шлюз інструментів (веб, зображення, TTS, маршрутизація браузера)
5. Повертає тебе до терміналу, готового до `hermes chat`

Якщо у тебе ще немає підписки, спочатку зареєструйся на [portal.nousresearch.com/manage-subscription](https://portal.nousresearch.com/manage-subscription).

### Існуюча інсталяція — додати Portal поряд з іншими провайдерами

Якщо ти вже налаштував Hermes з OpenRouter, Anthropic або будь‑яким іншим провайдером і хочеш додати Portal поряд з ними:

```bash
hermes model
# pick "Nous Portal" from the provider list
# browser opens, sign in, done
```

Твої існуючі провайдери залишаються налаштованими. Ти можеш перемикатися між ними за допомогою `/model` під час сесії або `hermes model` між сесіями — Portal стає одним із доступних провайдерів, а не єдиним.

### Безголовий / SSH / віддалений налаштування

OAuth потребує браузера, але зворотний виклик loopback працює на машині, де запущений Hermes. Для віддалених хостів дивись [OAuth over SSH / Remote Hosts](/guides/oauth-over-ssh) — ті ж шаблони працюють для Portal, що й для будь‑якого іншого OAuth‑базованого провайдера (`ssh -L` переадресація портів, `--manual-paste` для середовищ лише з браузером, таких як Cloud Shell / Codespaces).

### Налаштування профілю

Якщо ти використовуєш [Hermes profiles](/user‑guide/profiles), токен оновлення Portal автоматично ділиться між усіма профілями через спільне сховище токенів. Увійди один раз у будь‑якому профілі, і інші підхоплять його автоматично — не потрібно повторювати OAuth‑процес для кожного профілю.
## Використання Порталу щодня

### Перевірка підключень

```bash
hermes portal status     # login status, subscription info, model + gateway routing
hermes portal tools      # detailed Tool Gateway catalog with per-tool routing
hermes portal open       # open the subscription management page in your browser
```

`hermes portal status` (або просто `hermes portal`) показує тобі огляд високого рівня:

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

### Перемикання моделей

Всередині сесії:

```bash
/model anthropic/claude-sonnet-4.6
/model openai/gpt-5.5-pro
/model google/gemini-3-pro-preview
```

Або відкрий список вибору:

```bash
/model
# arrow keys, enter to select
```

Позапосесійно (повний майстер налаштувань, корисний при додаванні нового provider):

```bash
hermes model
```

### Поєднання шлюзу з власними бекендами

Якщо у тебе вже є, наприклад, обліковий запис Browserbase і ти хочеш продовжувати його використання, одночасно маршрутизуючи веб‑пошук та генерацію зображень через Nous, це підтримується. Використовуй `hermes tools`, щоб вибрати бекенди для кожного інструменту:

```bash
hermes tools
# → Web search       → "Nous Subscription"
# → Image generation → "Nous Subscription"
# → Browser          → "Browserbase"  (your existing key)
# → TTS              → "Nous Subscription"
```

Шлюз інструментів (Tool Gateway) активується окремо для кожного інструменту, а не як «все або нічого». Дивись [документацію Tool Gateway](/user-guide/features/tool-gateway) для повної матриці конфігурації по інструментах.

### Керування підпискою

Керуй своїм планом, переглядай використання або оновлюй/скасуй підписку в будь‑який час:

- **Web:** [portal.nousresearch.com/manage-subscription](https://portal.nousresearch.com/manage-subscription)
- **CLI shortcut:** `hermes portal open` (відкриває ту ж сторінку у твоєму браузері за замовчуванням)
## Довідник конфігурації

Після `hermes setup --portal` файл `~/.hermes/config.yaml` виглядатиме так:

```yaml
model:
  provider: nous
  default: anthropic/claude-sonnet-4.6     # or whatever model you picked
  base_url: https://inference-api.nousresearch.com/v1
```

Налаштування **шлюзу інструментів (Tool Gateway)** розташовані у відповідних розділах інструментів:

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

Токен оновлення OAuth зберігається окремо у `~/.hermes/auth.json` (не в `config.yaml` — облікові дані та конфігурація розділені навмисно).
## Обробка токенів

Hermes створює короткоживучий JWT зі збереженого refresh‑токену Portal під час кожного виклику інференсу, замість повторного використання довгоживучого API‑ключа. Життєвий цикл токену повністю автоматичний — оновлення, створення, повторна спроба при тимчасовій 401 — і ти його ніколи не бачиш.

Якщо Portal анулює refresh‑токен (зміна пароля, ручне відкликання, закінчення сесії), недійсний refresh‑токен **карантиновано локально**, і Hermes припиняє його повторне використання, і ти не бачиш потік однакових 401. Наступний виклик повертає чітке повідомлення «потрібна повторна автентифікація». Запусти `hermes auth add nous`, щоб увійти знову; карантин знімається після наступного успішного входу.
## Усунення проблем

### `hermes portal status` показує «not logged in»

Ти не завершив процес OAuth, або твій refresh‑токен був видалений. Запусти:

```bash
hermes auth add nous --type oauth
```

або використай `hermes model` і знову вибери Nous Portal.

### Появилось повідомлення «re-authentication required» під час сесії

Твій refresh‑токен Portal був анульований (зміна пароля, ручне відкликання або закінчення терміну дії сесії). Запусти `hermes auth add nous`, і наступний запит використає нові облікові дані. Будь‑який карантин старого токену буде автоматично знятий після успішного повторного входу.

### Хочеш використати конкретну модель провайдера, яку Portal не показує

Portal проксірує запити через OpenRouter, тому будь‑яка модель, яку підтримує OpenRouter, зазвичай доступна. Якщо певна модель не з’являється у `/model`, спробуй вказати slug у стилі OpenRouter безпосередньо:

```bash
/model anthropic/claude-opus-4.6
```

Якщо модель дійсно відсутня, [відкрий issue](https://github.com/NousResearch/hermes-agent/issues) — ми відображаємо каталог Portal у Hermes, і прогалини зазвичай означають, що треба оновити конфігурацію маршрутизації.

### Рахунки не відображаються в моєму обліковому записі Portal

Спочатку перевір `hermes portal status` — якщо він показує, що ти використовуєш іншого провайдера (`Model: currently openrouter` замість `using Nous as inference provider`), твоя локальна конфігурація відхилилася. Запусти `hermes model`, вибери Nous Portal, і наступний запит буде виконуватись через твою підписку.
## Дивись також

- **[Шлюз інструментів](/user-guide/features/tool-gateway)** — Повний опис кожного інструменту шлюзу, конфігурація per‑tool та ціноутворення
- **[Проксі підписки](/user-guide/features/subscription-proxy)** — Використовуй підписку Порталу з інструментів, які не є Hermes (інші агенти, скрипти, сторонні клієнти)
- **[Голосовий режим](/user-guide/features/voice-mode)** — Голосові розмови за допомогою OpenAI TTS Порталу
- **[Провайдери ШІ](/integrations/providers)** — Повний каталог провайдерів, якщо хочеш порівняти альтернативи
- **[OAuth через SSH](/guides/oauth-over-ssh)** — Вхід з віддалених хостів або лише браузерних середовищ
- **[Профілі](/user-guide/profiles)** — Кілька конфігурацій Hermes, що ділять один вхід у Портал