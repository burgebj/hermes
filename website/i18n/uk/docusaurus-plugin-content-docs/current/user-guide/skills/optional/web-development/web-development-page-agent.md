---
title: "Сторінка Agent"
sidebar_label: "Page Agent"
description: "Вбудуй alibaba/page-agent у свою веб‑аплікацію — чистий JavaScript‑агент з графічним інтерфейсом у сторінці, який постачається як один тег <script> або npm‑пакет і дозволяє кінцевим…"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Page Agent

Вбудуй `alibaba/page-agent` у свою веб‑аплікацію — чистий JavaScript‑агент у вигляді GUI, який постачається як один `<script>`‑тег або npm‑пакет і дозволяє користувачам твого сайту керувати інтерфейсом за допомогою природної мови («клацни login, заповни username як John»). Без Python, без headless‑браузера, без розширень. Використовуй цей skill, коли користувач‑розробник хоче додати AI‑копілот у свій SaaS / admin‑панель / B2B інструмент, зробити застарілий веб‑додаток доступним через природну мову або оцінити page‑agent проти локального (Ollama) чи хмарного (Qwen / OpenAI / OpenRouter) LLM. **НЕ** для серверної автоматизації браузера — направляй таких користувачів до вбудованого інструменту браузера Hermes.
## Метадані навички

| | |
|---|---|
| Джерело | Необов’язково — встановити за допомогою `hermes skills install official/web-development/page-agent` |
| Шлях | `optional-skills/web-development/page-agent` |
| Версія | `1.0.0` |
| Автор | Hermes Agent |
| Ліцензія | MIT |
| Платформи | linux, macos, windows |
| Теги | `web`, `javascript`, `agent`, `browser`, `gui`, `alibaba`, `embed`, `copilot`, `saas` |
:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# page-agent

alibaba/page-agent (https://github.com/alibaba/page-agent, 17k+ stars, MIT) — це GUI‑агент, який працює в межах сторінки, написаний на TypeScript. Він живе всередині веб‑сторінки, читає DOM як текст (без скріншотів, без мульти‑модального LLM) і виконує інструкції природною мовою типу «click the login button, then fill username as John» щодо поточної сторінки. Чисто клієнт‑сайд — хост‑сайт лише підключає скрипт і передає сумісну з OpenAI кінцеву точку LLM.
## Коли використовувати цю навичку

Завантаж цю навичку, коли користувач хоче:

- **Вбудувати AI‑копілот у власний веб‑додаток** (SaaS, admin‑панель, B2B‑інструмент, ERP, CRM) — «користувачі на моїй панелі повинні мати можливість ввести `create invoice for Acme Corp and email it` замість того, щоб клікати через п’ять екранів»
- **Модернізувати застарілий веб‑додаток** без переписування фронтенду — page‑agent накладається поверх існуючого DOM
- **Додати доступність за допомогою природної мови** — користувачі голосу/скрін‑рідера керують UI, описуючи, чого вони хочуть
- **Продемонструвати або оцінити page‑agent** проти локального (Ollama) або хостованого (Qwen, OpenAI, OpenRouter) LLM
- **Створити інтерактивне навчання/демонстрації продукту** — дозволити AI крок за кроком вести користувача через «як подати звіт про витрати» у реальному інтерфейсі
## Коли НЕ слід використовувати цей skill

- Користувач хоче, щоб **Hermes сам керував браузером** → використай вбудований інструмент браузера Hermes (Browserbase / Camofox). page‑agent — це *протилежний* напрямок.
- Користувач хоче **автоматизацію між вкладками без вбудовування** → використай Playwright, browser‑use або розширення Chrome page‑agent.
- Користувач потребує **візуального підкріплення / скріншотів** → page‑agent працює лише з текстовим DOM; замість нього використай мультимодальний браузерний агент.
## Передумови

- Node 22.13+ або 24+, npm 10+ (у документації зазначено 11+, але 10.9 працює добре)
- Кінцева точка LLM, сумісна з OpenAI: Qwen (DashScope), OpenAI, Ollama, OpenRouter або будь‑яка, що підтримує `/v1/chat/completions`
- Браузер з інструментами розробника (для налагодження)
## Path 1 — 30‑second demo via CDN (no install)

Найшвидший спосіб побачити, як це працює. Використовує безкоштовний тестовий проксі LLM від Alibaba — **лише для оцінки**, згідно з їхніми умовами.

Додай до будь‑якої HTML‑сторінки (або встав у консоль devtools як bookmarklet):

```html
<script src="https://cdn.jsdelivr.net/npm/page-agent@1.8.0/dist/iife/page-agent.demo.js" crossorigin="true"></script>
```

З’явиться панель. Введи інструкцію. Готово.

Форма bookmarklet (перетягни у панель закладок, клікни на будь‑якій сторінці):

```javascript
javascript:(function(){var s=document.createElement('script');s.src='https://cdn.jsdelivr.net/npm/page-agent@1.8.0/dist/iife/page-agent.demo.js';document.head.appendChild(s);})();
```
## Шлях 2 — npm install у твоєму веб‑додатку (використання у продакшн)

У існуючому веб‑проєкті (React / Vue / Svelte / без фреймворку):

```bash
npm install page-agent
```

Підключи свій власний LLM‑endpoint — **ніколи не розповсюджуй демо‑CDN реальним користувачам**:

```javascript
import { PageAgent } from 'page-agent'

const agent = new PageAgent({
    model: 'qwen3.5-plus',
    baseURL: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    apiKey: process.env.LLM_API_KEY,   // never hardcode
    language: 'en-US',
})

// Show the panel for end users:
agent.panel.show()

// Or drive it programmatically:
await agent.execute('Click submit button, then fill username as John')
```

Provider examples (any OpenAI‑compatible endpoint works):

| Provider | `baseURL` | `model` |
|----------|-----------|---------|
| Qwen / DashScope | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen3.5-plus` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| Ollama (local) | `http://localhost:11434/v1` | `qwen3:14b` |
| OpenRouter | `https://openrouter.ai/api/v1` | `anthropic/claude-sonnet-4.6` |

**Ключові поля конфігурації** (передаються в `new PageAgent({...})`):

- `model`, `baseURL`, `apiKey` — з’єднання з LLM
- `language` — мова інтерфейсу (`en-US`, `zh-CN` тощо)
- Існують allowlist та hooks маскування даних для обмеження того, до чого агент має доступ — дивись https://alibaba.github.io/page-agent/ для повного списку опцій

**Безпека.** Не розміщуй свій `apiKey` у коді на боці клієнта у реальному розгортанні — проксіруй виклики LLM через бекенд і вкажи `baseURL` на свій проксі. Демонстраційний CDN існує, бо alibaba запускає цей проксі для оцінки.
## Path 3 — клонувати репозиторій з вихідним кодом (contributing, або hacking on it)

Використовуй це, коли користувач хоче змінити page-agent, протестувати його проти довільних сайтів за допомогою локального IIFE‑bundle або розробляти розширення браузера.

```bash
git clone https://github.com/alibaba/page-agent.git
cd page-agent
npm ci              # exact lockfile install (or `npm i` to allow updates)
```

Створи `.env` у корені репозиторію з кінцевою точкою LLM. Приклад:

```
LLM_MODEL_NAME=gpt-4o-mini
LLM_API_KEY=sk-...
LLM_BASE_URL=https://api.openai.com/v1
```

Ollama flavor:

```
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=NA
LLM_MODEL_NAME=qwen3:14b
```

Загальні команди:

```bash
npm start           # docs/website dev server
npm run build       # build every package
npm run dev:demo    # serve IIFE bundle at http://localhost:5174/page-agent.demo.js
npm run dev:ext     # develop the browser extension (WXT + React)
npm run build:ext   # build the extension
```

**Тестуй на будь‑якому веб‑сайті** за допомогою локального IIFE‑bundle. Додай цей bookmarklet:

```javascript
javascript:(function(){var s=document.createElement('script');s.src=`http://localhost:5174/page-agent.demo.js?t=${Math.random()}`;s.onload=()=>console.log('PageAgent ready!');document.head.appendChild(s);})();
```

Потім: `npm run dev:demo`, клікни bookmarklet на будь‑якій сторінці, і локальна збірка буде інжектована. Автоматично перебудовується при збереженні.

**Warning:** твій `.env` `LLM_API_KEY` вбудовується у IIFE‑bundle під час dev‑збірок. Не поширюй bundle. Не коміти його. Не вставляй URL у Slack. (Перевірено: пошук у публічному dev‑bundle повертає буквальні значення з `.env`.)
## Структура репозиторію (шлях 3)

Monorepo з npm workspaces. Ключові пакети:

| Пакет | Шлях | Призначення |
|---------|------|---------|
| `page-agent` | `packages/page-agent/` | Головна точка входу з UI‑панеллю |
| `@page-agent/core` | `packages/core/` | Логіка ядра агента, без UI |
| `@page-agent/mcp` | `packages/mcp/` | MCP‑сервер (бета) |
| — | `packages/llms/` | LLM‑клієнт |
| — | `packages/page-controller/` | Операції DOM + візуальний фідбек |
| — | `packages/ui/` | Панель + i18n |
| — | `packages/extension/` | Розширення Chrome/Firefox |
| — | `packages/website/` | Документація + цільовий сайт |
## Перевірка роботи

Після Path 1 або Path 2:
1. Відкрий сторінку в браузері з відкритими devtools.
2. Ти маєш побачити плаваючу панель. Якщо ні — перевір консоль на помилки (найчастіше: CORS на LLM‑endpoint, неправильний `baseURL` або неправильний API‑ключ).
3. Введи просту інструкцію, що відповідає чомусь видимому на сторінці («click the Login link»).
4. Переглянь вкладку **Network** — ти маєш побачити запит до твого `baseURL`.

Після Path 3:
1. `npm run dev:demo` виводить `Accepting connections at http://localhost:5174`.
2. `curl -I http://localhost:5174/page-agent.demo.js` повертає `HTTP/1.1 200 OK` з `Content-Type: application/javascript`.
3. Клацни bookmarklet на будь‑якому сайті; панель з’явиться.
## Pitfalls

- **Demo CDN in production** — не роби. Це обмежено за швидкістю, використовує безкоштовний проксі alibaba, і їхні умови забороняють використання у продакшені.
- **API key exposure** — будь‑який ключ, переданий у `new PageAgent({apiKey: ...})`, потрапляє у твій JS‑bundle. Завжди проксуй через власний бекенд для реальних розгортань.
- **Non-OpenAI-compatible endpoints** — silently fail або повертають незрозумілі помилки. Якщо твій провайдер потребує нативного форматування Anthropic/Gemini, використай проксі сумісності з OpenAI (LiteLLM, OpenRouter) перед ним.
- **CSP blocks** — сайти зі строгим Content‑Security‑Policy можуть відмовитися завантажувати скрипт CDN або заборонити inline eval. У такому випадку розмісти скрипт самостійно зі свого походження.
- **Restart dev server** після редагування `.env` у Path 3 — Vite читає змінні лише під час запуску.
- **Node version** — репозиторій оголошує `^22.13.0 || >=24`. Node 20 завершить `npm ci` з помилками engine.
- **npm 10 vs 11** — в документації зазначено npm 11+, проте npm 10.9 працює без проблем.
## Посилання

- Репозиторій: https://github.com/alibaba/page-agent
- Документація: https://alibaba.github.io/page-agent/
- Ліцензія: MIT (засновано на внутрішніх механізмах обробки DOM бібліотеки **browser-use**, © 2024 Gregor Zunic)