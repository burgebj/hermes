---
sidebar_position: 1
title: "Запусти Hermes Agent з Nous Portal"
description: "Повний покроковий посібник: підписатися, налаштувати, переключити моделі, увімкнути gateway інструменти та перевірити маршрутизацію"
---

# Запуск Hermes Agent з Nous Portal

Цей посібник крок за кроком проводить тебе через запуск Hermes Agent на підписці [Nous Portal](https://portal.nousresearch.com) — від реєстрації до перевірки правильності маршрутизації кожного інструмента. Якщо тобі потрібен лише огляд того, що таке Portal і що входить до підписки, переглянь [сторінку інтеграції Nous Portal](/integrations/nous-portal). Ця сторінка є скриптом завдання.
## Передумови

- Hermes Agent встановлений ([Quickstart](/getting-started/quickstart))
- Веб‑браузер на машині, яку ти налаштовуєш (або SSH‑перенаправлення портів — дивись [OAuth over SSH](/guides/oauth-over-ssh))
- Приблизно 5 хвилин

Ти **не** потребуєш: ключа OpenAI, ключа Anthropic, облікового запису Firecrawl, облікового запису FAL, облікового запису Browser Use або будь‑яких інших постачальників облікових даних. У цьому і полягає вся суть.
## 1. Отримати підписку

Open [portal.nousresearch.com/manage-subscription](https://portal.nousresearch.com/manage-subscription), **sign up**, and **pick a plan**.

Вже маєш підписку? Перейди до кроку 2.
## 2. Запусти одноразове налаштування

```bash
hermes setup --portal
```

Ця одна команда виконує п’ять дій:

1. Відкриває твій браузер на portal.nousresearch.com для входу через OAuth
2. Зберігає токен оновлення у `~/.hermes/auth.json`
3. Встановлює `model.provider: nous` у `~/.hermes/config.yaml`
4. Вибирає модель‑агент за замовчуванням (`anthropic/claude-sonnet-4.6` або подібну)
5. Вмикає шлюз інструментів для веб‑пошуку, генерації зображень, TTS та автоматизації браузера

Коли вона завершиться, ти повернешся до терміналу, готовий до спілкування.

### Що робити, якщо я підключений через SSH до сервера?

OAuth потребує браузера, але зворотний виклик loopback працює на машині, де запущений Hermes. Два варіанти:

```bash
# Option A: SSH port forwarding (preferred)
ssh -N -L 8642:127.0.0.1:8642 user@remote-host    # in a local terminal
hermes setup --portal                              # on the remote, open the printed URL in your local browser

# Option B: manual paste (for Cloud Shell, Codespaces, EC2 Instance Connect)
hermes auth add nous --type oauth --manual-paste
# Then re-run `hermes setup --portal` to wire the provider + gateway
```

Дивись [OAuth over SSH / Remote Hosts](/guides/oauth-over-ssh) для повного покрокового посібника, включаючи ланцюжки ProxyJump, mosh/tmux та нюанси ControlMaster.
## 3. Перевір, чи працює

```bash
hermes portal status
```

Ти маєш бачити:

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

Якщо будь‑який рядок показує щось інше, ніж «via Nous Portal», або рядок автентифікації говорить «not logged in», переходь до розділу [Troubleshooting](#troubleshooting) нижче.
## 4. Запусти свою першу розмову

```bash
hermes chat
```

Спробуй щось, що залучає і модель, і **шлюз інструментів (Tool Gateway)**:

```
Hey, search the web for "Hermes Agent release notes" and summarize the top 3 hits.
```

Ти маєш побачити, як Hermes викликає `web_search` (на базі Firecrawl, через шлюз) і відповідає з підсумком. Якщо пошук виконується і відповідь має сенс, ти готовий — Portal підключений від початку до кінця.
## 5. Вибери модель, яку дійсно хочеш

Типова модель після `hermes setup --portal` – це розумна універсальна модель, але вся суть підписки — доступ до повного каталогу. Перемкнись за допомогою `/model` під час сесії:

```bash
/model anthropic/claude-sonnet-4.6     # best general-purpose agentic
/model openai/gpt-5.4                  # strong reasoning + tool calling
/model google/gemini-2.5-pro           # huge context window
/model deepseek/deepseek-v3.2          # cost-effective coder
/model anthropic/claude-opus-4.6       # heavyweight for hard problems
```

Або відкрий вибірник, щоб переглянути:

```bash
/model
```

Вибери інший варіант за замовчуванням назавжди:

```bash
# in your terminal, outside any session
hermes config set model.default anthropic/claude-sonnet-4.6
```

### Не обирай Hermes-4 для роботи агента

Hermes-4-70B та Hermes-4-405B доступні в Порталі за глибокими знижками, але це **моделі чат/розуміння**, а не налаштовані на виклик інструментів. Вони будуть мати труднощі з багатокроковими агентськими циклами. Використовуй їх через [Nous Chat](https://chat.nousresearch.com) для розмов/дослідницької роботи або через [проксі підписки](/user-guide/features/subscription-proxy) з не‑агентських інструментів. Для самого Hermes Agent використовуйте передові агентські моделі, зазначені вище.

Власна [інформаційна сторінка Порталу](https://portal.nousresearch.com/info) також містить це попередження — це офіційне керівництво Nous, а не лише думка Hermes.
## 6. (Optional) Налаштування маршрутизації шлюзу інструментів

Шлюз працює за принципом opt‑in для кожного інструменту, а не «все або нічого». Якщо у тебе вже є обліковий запис Browserbase і ти хочеш і надалі користуватися ним, одночасно маршрутизуючи веб‑пошук та генерацію зображень через Nous, це підтримується:

```bash
hermes tools
# → Web search       → "Nous Subscription"     (recommended)
# → Image generation → "Nous Subscription"     (recommended)
# → Browser          → "Browserbase"           (your existing key)
# → TTS              → "Nous Subscription"     (recommended)
```

Перевір свою конфігурацію за допомогою:

```bash
hermes portal tools
```

Ти побачиш маршрутизацію для кожного інструменту — `via Nous Portal` для тих, що проходять через підписку, і назву партнера (`browserbase`, `firecrawl` тощо) для інструментів, які використовують твої власні ключі.
## 7. (Optional) Увімкнути голосовий режим

Оскільки шлюз інструментів включає OpenAI TTS, [голосовий режим](/user-guide/features/voice-mode) працює без окремого ключа OpenAI:

```bash
hermes setup voice
# → pick "Nous Subscription" for TTS
# → pick a speech-to-text backend (local faster-whisper is free, no setup)
```

Потім у будь‑якій сесії платформи обміну повідомленнями (Telegram, Discord, Signal тощо) надішли голосове повідомлення, і Hermes його транскрибуватиме, відповість і відтворить синтезований голос — все це на твоїй підписці в Portal.
## 8. (Optional) Cron + always‑on workflows

Підписка на Portal працює для [cron jobs](/user‑guide/features/cron) та [batch processing](/user‑guide/features/batch-processing) так само, як і для інтерактивного чату — OAuth‑refresh‑токен використовується автоматично. Ніяких додаткових налаштувань; просто заплануй cron‑завдання, і вони будуть списані з твоєї підписки.

```bash
hermes cron create "every day at 9am" \
  "Search the web for top AI news and summarize the 5 most important stories" \
  --name "Daily AI news"
```

Cron‑завдання виконується без нагляду, викликає модель + веб‑пошук + підсумовування через твою підписку на Portal.
## Профілі та багатокористувацькі налаштування

Якщо ти використовуєш [Hermes profiles](/user-guide/profiles) (наприклад, окремий конфіг для кожного проєкту), токен оновлення Portal автоматично спільний для всіх профілів через спільне сховище токенів. Увійди один раз у будь‑якому профілі, і решта підхопить його автоматично.

Для командних налаштувань, коли кілька людей користуються однією машиною, кожна людина має свій власний обліковий запис Portal → у кожному домашньому каталозі зберігається свій `~/.hermes/auth.json` → без спільного використання токенів між користувачами. Це правильна межа.
## Усунення проблем

### `hermes portal status` показує «not logged in» після `hermes setup --portal`

OAuth‑потік не завершився. Запусти його ще раз:

```bash
hermes auth add nous --type oauth
```

Якщо браузер не відкривається або зворотний виклик не вдається, ти, ймовірно, працюєш на віддаленому/безголовому хості — дивись [OAuth over SSH](/guides/oauth-over-ssh) для налаштування переадресації портів та ручних обхідних рішень.

### «Model: currently openrouter» (або інший провайдер) замість «using Nous as inference provider»

Твоя локальна конфігурація відхилилася. OAuth спрацював, але `model.provider` все ще вказує на інший провайдер. Виправ:

```bash
hermes config set model.provider nous
```

Або інтерактивно:

```bash
hermes model
# pick Nous Portal
```

Перевір ще раз за допомогою `hermes portal status`.

### Інструменти шлюзу інструментів (Tool Gateway) показують імена партнерів замість «via Nous Portal»

Конфігурація окремих інструментів переважає над шлюзом. Виконай:

```bash
hermes tools
# pick "Nous Subscription" for any tool you want gateway-routed
```

Деякі користувачі навмисно комбінують — напр., маршрутизують веб‑трафік через Nous, але використовують власний ключ Browserbase для браузера. Якщо це навмисно, залиш це як є. Якщо ні, ця команда виправить ситуацію.

### «Re-authentication required» під час сесії

Токен оновлення Portal був анульований (зміна пароля, ручне відкликання, закінчення сесії). Токен тепер локально ізольований, щоб Hermes не повторював його безкінечно. Просто ввійди знову:

```bash
hermes auth add nous
```

Ізоляція автоматично зникає після успішного повторного входу.

### Модель, яку я хочу, відсутня у вибірці `/model`

Каталог Portal відображає список моделей OpenRouter (300+). Якщо модель відсутня, спробуй ввести slug у стилі OpenRouter безпосередньо:

```bash
/model anthropic/claude-opus-4.6
/model openai/o1-2025-12-17
```

Якщо модель дійсно недоступна, [відкрий issue](https://github.com/NousResearch/hermes-agent/issues) — більшість прогалин пов’язані з конфігурацією маршрутизації, яку ми можемо оновити.

### Платіжна інформація не відображається у моєму обліковому записі Portal

`hermes portal status` підкаже, чи ти дійсно маршрутизуєш через Portal, чи через інший провайдер. Поширені причини:

- `model.provider` встановлено на `openrouter`/`anthropic`/тощо замість `nous`
- Помилка оновлення OAuth, яка переключилася на інший налаштований провайдер
- Кілька профілів Hermes, і ти використовуєш неправильний (перевір `hermes profile current`)

### Хочу відкликати доступ і почати з чистого листа

```bash
hermes auth remove nous       # wipes the local refresh token
# Then re-run setup or remove the subscription from the Portal web UI
```
## Що це дає, у простих цифрах

| Без Portal | З Portal |
|----------------|-------------|
| 1× OpenRouter / Anthropic / OpenAI key у `.env` | 1× OAuth refresh token, без `.env` key |
| 1× Firecrawl key для веб‑пошуку | Веб‑трафік маршрутизовано через gateway |
| 1× FAL key для генерації зображень | Генерація зображень маршрутизована через gateway |
| 1× Browser Use / Browserbase key для браузера | Браузер маршрутизовано через gateway |
| 1× OpenAI key для TTS / voice mode | TTS маршрутизовано через gateway |
| 5 окремих дашбордів, поповнень, рахунків | 1 підписка, 1 рахунок |
| Крос‑машинне: реплікація всіх 5 key | Крос‑машинне: повторний OAuth один раз |

Ось і все. Якщо ти використовуєш більше двох цих бекенд‑сервісів, підписка окупається сама.
## Дивись також

- **[Сторінка інтеграції Nous Portal](/integrations/nous-portal)** — Огляд того, що включено в підписку
- **[Шлюз інструментів](/user-guide/features/tool-gateway)** — Повні деталі щодо кожного інструменту, маршрутизованого через шлюз
- **[Проксі підписки](/user-guide/features/subscription-proxy)** — Використовуй підписку Portal з інструментів, які не пов'язані з Hermes
- **[Режим голосу](/user-guide/features/voice-mode)** — Налаштуй голосові розмови в підписці Portal
- **[OAuth через SSH](/guides/oauth-over-ssh)** — Шаблони віддаленого / безголового входу
- **[Профілі](/user-guide/profiles)** — Поділись одним входом у Portal між кількома конфігураціями Hermes