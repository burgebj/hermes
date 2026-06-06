---
title: "Страничный агент"
sidebar_label: "Page Agent"
description: "Встроить alibaba/page-agent в своё веб‑приложение — чистый JavaScript‑агент встраиваемого интерфейса, который поставляется в виде единственного тега <script> или npm‑пакета и позволяет конечным пользователям…"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Page Agent

Встраивай alibaba/page-agent в своё веб‑приложение — чистый JavaScript‑агент с графическим интерфейсом, который поставляется в виде единственного тега `<script>` или npm‑пакета и позволяет конечным пользователям твоего сайта управлять UI естественным языком («кликни вход, введи имя пользователя как John»). Не требуется Python, без безголового браузера, без расширений. Используй этот skill, когда пользователь — веб‑разработчик, желающий добавить AI‑копилот в свой SaaS / админ‑панель / B2B‑инструмент, сделать наследованное веб‑приложение доступным через естественный язык или оценить page‑agent с локальной (Ollama) или облачной (Qwen / OpenAI / OpenRouter) LLM. **НЕ** предназначен для серверной автоматизации браузера — направляй таких пользователей к встроенному в Hermes инструменту браузера.
## Метаданные навыка

| | |
|---|---|
| Источник | Опционально — установить с помощью `hermes skills install official/web-development/page-agent` |
| Путь | `optional-skills/web-development/page-agent` |
| Версия | `1.0.0` |
| Автор | Hermes Agent |
| Лицензия | MIT |
| Платформы | linux, macos, windows |
| Теги | `web`, `javascript`, `agent`, `browser`, `gui`, `alibaba`, `embed`, `copilot`, `saas` |
:::info
Следующее — полное определение **skill**, которое Hermes загружает, когда этот **skill** активируется. Это то, что агент видит как инструкции, когда **skill** включён.
:::

# page-agent

alibaba/page-agent (https://github.com/alibaba/page-agent, 17k+ stars, MIT) — это GUI‑агент, работающий внутри страницы, написанный на TypeScript. Он живёт внутри веб‑страницы, читает DOM как текст (без скриншотов, без мультимодального LLM) и исполняет инструкции на естественном языке типа «кликни кнопку входа, затем введи имя пользователя John» относительно текущей страницы. Полностью клиентская — хост‑сайт просто подключает скрипт и передаёт совместимый с OpenAI LLM endpoint.
## Когда использовать этот навык

Загрузи этот навык, когда пользователь хочет:

- **Встроить AI‑копилот в своё веб‑приложение** (SaaS, админ‑панель, B2B‑инструмент, ERP, CRM) — «пользователи на моей панели должны иметь возможность написать `create invoice for Acme Corp and email it` вместо того, чтобы кликать по пяти экранам»
- **Модернизировать устаревшее веб‑приложение** без переписывания фронтенда — page‑agent накладывается поверх существующего DOM
- **Добавить доступность через естественный язык** — пользователи голосового ввода и скрин‑ридеров управляют UI, описывая, что им нужно
- **Продемонстрировать или оценить page‑agent** с локальной (Ollama) или размещённой (Qwen, OpenAI, OpenRouter) LLM
- **Создать интерактивные обучающие материалы и демонстрации продукта** — позволить AI проводить пользователя через процесс «как отправить отчёт о расходах» в реальном UI.
## Когда НЕ следует использовать этот инструмент

- Пользователь хочет, чтобы **Hermes сам управлял браузером** → используй встроенный в Hermes инструмент браузера (Browserbase / Camofox). page‑agent работает в *противоположном* направлении.
- Пользователь хочет **автоматизацию между вкладками без встраивания** → используй Playwright, browser‑use или расширение Chrome page‑agent.
- Пользователю нужны **визуальная привязка / скриншоты** → page‑agent работает только с текстовым DOM; вместо него используй мультимодальный браузерный агент.
## Требования

- Node 22.13+ или 24+, npm 10+ (в документации указано 11+, но 10.9 работает отлично)
- LLM‑endpoint, совместимый с OpenAI: Qwen (DashScope), OpenAI, Ollama, OpenRouter или любой другой, поддерживающий `/v1/chat/completions`
- Браузер с devtools (для отладки)
## Path 1 — 30‑секундная демонстрация через CDN (без установки)

Самый быстрый способ увидеть, как это работает. Использует бесплатный тестовый LLM‑прокси от **Alibaba** — **только для оценки**, в соответствии с их условиями.

Добавь в любую HTML‑страницу (или вставь в консоль DevTools как bookmarklet):

```html
<script src="https://cdn.jsdelivr.net/npm/page-agent@1.8.0/dist/iife/page-agent.demo.js" crossorigin="true"></script>
```

Появится панель. Введи инструкцию. Всё.

Форма bookmarklet (перетащи в панель закладок, кликни на любой странице):

```javascript
javascript:(function(){var s=document.createElement('script');s.src='https://cdn.jsdelivr.net/npm/page-agent@1.8.0/dist/iife/page-agent.demo.js';document.head.appendChild(s);})();
```
## Path 2 — npm install в своё веб‑приложение (использование в продакшене)

Внутри существующего веб‑проекта (React / Vue / Svelte / plain):

```bash
npm install page-agent
```

Подключи свой собственный LLM‑endpoint — **никогда не отправляй демо‑CDN реальным пользователям**:

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

Примеры провайдеров (подойдёт любой совместимый с OpenAI endpoint):

| Provider | `baseURL` | `model` |
|----------|-----------|---------|
| Qwen / DashScope | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen3.5-plus` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| Ollama (local) | `http://localhost:11434/v1` | `qwen3:14b` |
| OpenRouter | `https://openrouter.ai/api/v1` | `anthropic/claude-sonnet-4.6` |

**Ключевые поля конфигурации** (передаются в `new PageAgent({...})`):

- `model`, `baseURL`, `apiKey` — подключение к LLM
- `language` — язык интерфейса (`en-US`, `zh-CN` и т.д.)
- Существуют хуки **allowlist** и **data‑masking** для ограничения того, к чему агент имеет доступ — см. https://alibaba.github.io/page-agent/ для полного списка опций

**Безопасность.** Не размещай свой `apiKey` в клиентском коде при реальном развертывании — прокси‑запросы к LLM делай через свой бекенд и указывай `baseURL` на свой прокси. Демонстрационный CDN существует потому, что alibaba предоставляет этот прокси для оценки.
## Path 3 — клонирование репозитория исходного кода (contributing, or hacking on it)

Используй этот способ, когда нужно изменить **page-agent**, протестировать его на произвольных сайтах с помощью локального IIFE‑бандла или разрабатывать расширение для браузера.

```bash
git clone https://github.com/alibaba/page-agent.git
cd page-agent
npm ci              # exact lockfile install (or `npm i` to allow updates)
```

Создай файл `.env` в корне репозитория с указанием LLM‑endpoint. Пример:

```
LLM_MODEL_NAME=gpt-4o-mini
LLM_API_KEY=sk-...
LLM_BASE_URL=https://api.openai.com/v1
```

Вариант для Ollama:

```
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=NA
LLM_MODEL_NAME=qwen3:14b
```

Распространённые команды:

```bash
npm start           # docs/website dev server
npm run build       # build every package
npm run dev:demo    # serve IIFE bundle at http://localhost:5174/page-agent.demo.js
npm run dev:ext     # develop the browser extension (WXT + React)
npm run build:ext   # build the extension
```

**Тестирование на любом сайте** с помощью локального IIFE‑бандла. Добавь эту bookmarklet‑закладку:

```javascript
javascript:(function(){var s=document.createElement('script');s.src=`http://localhost:5174/page-agent.demo.js?t=${Math.random()}`;s.onload=()=>console.log('PageAgent ready!');document.head.appendChild(s);})();
```

Затем запусти `npm run dev:demo`, кликни по закладке на любой странице — локальная сборка будет внедрена. При сохранении файлов происходит автоматическая пересборка.

**Warning:** значение `LLM_API_KEY` из твоего файла `.env` встраивается в IIFE‑бандл при разработческих сборках. Не распространяй бандл, не коммить его и не вставляй URL в Slack. (Проверено: поиск по публичному dev‑бандлу возвращает буквальные значения из `.env`.)
## Структура репозитория (Путь 3)

Monorepo с npm‑рабочими пространствами. Ключевые пакеты:

| Пакет | Путь | Назначение |
|---------|------|------------|
| `page-agent` | `packages/page-agent/` | Основная точка входа с UI‑панелью |
| `@page-agent/core` | `packages/core/` | Логика ядра агента, без UI |
| `@page-agent/mcp` | `packages/mcp/` | MCP‑сервер (бета) |
| — | `packages/llms/` | Клиент LLM |
| — | `packages/page-controller/` | Операции с DOM и визуальная обратная связь |
| — | `packages/ui/` | Панель + i18n |
| — | `packages/extension/` | Расширение Chrome/Firefox |
| — | `packages/website/` | Документация + посадочная страница |
## Проверка работы

После Path 1 или Path 2:
1. Открой страницу в браузере с открытыми **devtools**.
2. Ты должен увидеть плавающую панель. Если её нет, проверь консоль на наличие ошибок (самая частая — CORS на конечной точке LLM, неверный `baseURL` или плохой API‑ключ).
3. Введи простую инструкцию, соответствующую чему‑то видимому на странице (например, «click the Login link»).
4. Посмотри на вкладку **Network** — ты должен увидеть запрос к твоему `baseURL`.

После Path 3:
1. `npm run dev:demo` выводит `Accepting connections at http://localhost:5174`.
2. `curl -I http://localhost:5174/page-agent.demo.js` возвращает `HTTP/1.1 200 OK` с `Content-Type: application/javascript`.
3. Кликни на **bookmarklet** на любом сайте — панель появится.
## Подводные камни

- **Demo CDN в продакшене** — не делай. Он ограничен по частоте запросов, использует бесплатный прокси alibaba, а их условия запрещают использование в продакшене.
- **Экспозиция API‑ключа** — любой ключ, переданный в `new PageAgent({apiKey: ...})`, попадает в твой JS‑бандл. Всегда проксируй запросы через собственный бекенд для реальных развертываний.
- **Эндпоинты, несовместимые с OpenAI**, молча терпят неудачу или выдают непонятные ошибки. Если твой провайдер требует нативного формата Anthropic/Gemini, используй прокси совместимости с OpenAI (LiteLLM, OpenRouter) перед ним.
- **Блокировки CSP** — сайты со строгой Content‑Security‑Policy могут отказать в загрузке скрипта CDN или запретить inline‑eval. В таком случае размещай скрипт самостоятельно на своём сервере.
- **Перезапусти dev‑сервер** после изменения `.env` в Path 3 — Vite читает переменные окружения только при старте.
- **Версия Node** — репозиторий объявляет `^22.13.0 || >=24`. Node 20 не пройдет `npm ci` из‑за ошибок engine.
- **npm 10 vs 11** — в документации указано npm 11+, но npm 10.9 тоже работает без проблем.
## Ссылки

- Репозиторий: https://github.com/alibaba/page-agent
- Документация: https://alibaba.github.io/page-agent/
- Лицензия: MIT (built on browser-use's DOM processing internals, Copyright 2024 Gregor Zunic)