---
sidebar_position: 12
title: "Плагіни провайдерів веб‑пошуку"
description: "Як створити бекенд‑плагін для веб‑пошуку/видобутку/сканування для Hermes Agent"
---

# Створення плагіна провайдера веб‑пошуку

Плагіни провайдерів веб‑пошуку реєструють бекенд, який обслуговує `web_search`, `web_extract` та (за бажанням) виклики інструменту deep‑crawl. Вбудовані провайдери — Firecrawl, SearXNG, Tavily, Exa, Parallel, Brave Search (безкоштовний рівень), xAI та DDGS — всі постачаються як плагіни у `plugins/web/<name>/`. Ти можеш додати новий або перевизначити вбудований, розмістивши каталог поруч із ними.

:::tip
Веб‑пошук — один із кількох **backend‑плагінів**, які підтримує Hermes. Інші (з їхніми власними ABC) — [Image Generation Provider Plugins](/developer-guide/image-gen-provider-plugin), [Video Generation Provider Plugins](/developer-guide/video-gen-provider-plugin), [Memory Provider Plugins](/developer-guide/memory-provider-plugin), [Context Engine Plugins](/developer-guide/context-engine-plugin) та [Model Provider Plugins](/developer-guide/model-provider-plugin). Загальні плагіни інструментів/хукiв/CLI знаходяться у [Build a Hermes Plugin](/guides/build-a-hermes-plugin).
:::

## Як працює виявлення

Hermes сканує бекенди веб‑пошуку у трьох місцях:

1. **Bundled** — `<repo>/plugins/web/<name>/` (автозавантажується з `kind: backend`, завжди доступний)
2. **User** — `~/.hermes/plugins/web/<name>/` (опціонально через `plugins.enabled` або `hermes plugins enable <name>`)
3. **Pip** — пакети, що оголошують точку входу `hermes_agent.plugins`

У функції `register(ctx)` кожного плагіна викликається `ctx.register_web_search_provider(...)` — це додає інстанс у реєстр у `agent/web_search_registry.py`. Активний провайдер для кожної можливості вибирається за конфігурацією:

| Можливість | Ключ конфігурації | Повертається до |
|---|---|---|
| `web_search` | `web.search_backend` | `web.backend` |
| `web_extract` | `web.extract_backend` | `web.backend` |
| Режими deep crawl у `web_extract` | `web.extract_backend` | `web.backend` |

Якщо жоден з ключів не встановлений, Hermes автоматично визначає бекенд за наявністю API‑ключа/URL у середовищі. `hermes tools` проводить користувачів через вибір.

## Структура каталогу

```
plugins/web/my-backend/
├── __init__.py     # register() entry point
├── provider.py     # WebSearchProvider subclass
└── plugin.yaml     # Manifest with kind: backend and provides_web_providers
```

`brave_free/` та `ddgs/` — найменші приклади у дереві: `brave_free` — провайдер лише пошуку з API‑ключем, `ddgs` — провайдер без ключа, який ліниво встановлює свій SDK.

## ABC провайдера WebSearchProvider

Наслідуй `agent.web_search_provider.WebSearchProvider`. Єдині обов’язкові члени — `name`, `is_available()` та будь‑яка з `search()` / `extract()` / `crawl()`, яку ти реалізуєш.

```python
# plugins/web/my-backend/provider.py
from __future__ import annotations

import os
from typing import Any, Dict, List

from agent.web_search_provider import WebSearchProvider


class MyBackendWebSearchProvider(WebSearchProvider):
    """Minimal search-only provider against the My Backend HTTP API."""

    @property
    def name(self) -> str:
        # Stable id used in web.search_backend / web.extract_backend / web.backend
        # config keys. Lowercase, no spaces; hyphens permitted.
        return "my-backend"

    @property
    def display_name(self) -> str:
        # Human label shown in `hermes tools`. Defaults to `name`.
        return "My Backend"

    def is_available(self) -> bool:
        # Cheap check — env var present, optional dep importable, etc.
        # MUST NOT make network calls (runs on every `hermes tools` paint).
        return bool(os.getenv("MY_BACKEND_API_KEY", "").strip())

    def supports_search(self) -> bool:
        return True

    def supports_extract(self) -> bool:
        return False

    def search(self, query: str, limit: int = 5) -> Dict[str, Any]:
        import httpx

        api_key = os.environ["MY_BACKEND_API_KEY"]
        try:
            resp = httpx.get(
                "https://api.example.com/search",
                params={"q": query, "count": max(1, min(int(limit), 20))},
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as exc:
            return {"success": False, "error": str(exc)}

        # Response shape is fixed — see "Response shape" below.
        return {
            "success": True,
            "data": {
                "web": [
                    {
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "description": item.get("snippet", ""),
                        "position": idx + 1,
                    }
                    for idx, item in enumerate(data.get("results", []))
                ],
            },
        }
```

```python
# plugins/web/my-backend/__init__.py
from plugins.web.my_backend.provider import MyBackendWebSearchProvider


def register(ctx) -> None:
    """Plugin entry point — called once at load time."""
    ctx.register_web_search_provider(MyBackendWebSearchProvider())
```

## plugin.yaml

```yaml
name: web-my-backend
version: 1.0.0
description: "My Backend web search — Bearer-auth REST API"
author: Your Name
kind: backend
provides_web_providers:
  - my-backend
requires_env:
  - MY_BACKEND_API_KEY
```

| Ключ | Призначення |
|---|---|
| `kind: backend` | Маршрутизує плагін через шлях завантаження бекенду |
| `provides_web_providers` | Список `name` провайдерів, які реєструє цей плагін — використовується завантажувачем для реклами плагіна у `hermes tools` ще до виконання `register()` |
| `requires_env` | Інтерактивний запит облікових даних під час `hermes plugins install` (див. [Build a Hermes Plugin](/guides/build-a-hermes-plugin#gate-on-environment-variables) для розширеного формату) |

## Довідка по ABC

Повний контракт у `agent/web_search_provider.py`. Методи, які можна перевизначити:

| Член | Обов’язковий | За замовчуванням | Призначення |
|---|---|---|---|
| `name` | ✅ | — | Стабільний ідентифікатор, що використовується у конфігурації `web.*_backend` |
| `display_name` | — | `name` | Мітка, що показується у `hermes tools` |
| `is_available()` | ✅ | — | Дешеві ворота доступності — змінні середовища, необов’язкові залежності |
| `supports_search()` | — | `True` | Прапорець можливості для маршрутизації `web_search` |
| `supports_extract()` | — | `False` | Прапорець можливості для маршрутизації `web_extract` |
| `search(query, limit)` | умовний | піднімає виключення | Потрібен, коли `supports_search()` повертає `True` |
| `extract(urls, **kwargs)` | умовний | піднімає виключення | Потрібен, коли `supports_extract()` повертає `True` |

Провайдери можуть рекламувати кілька можливостей в одному класі — Firecrawl, Tavily, Exa та Parallel реалізують і пошук, і екстракцію. Brave Search і DDGS — лише пошук; SearXNG — лише пошук з документованим робочим процесом «підключити до провайдера екстракції».

## Формат відповіді

Обгортка інструменту очікує фіксовану структуру, щоб не доводилося перекладати між бекендами.

**Успішний пошук:**

```python
{
    "success": True,
    "data": {
        "web": [
            {"title": str, "url": str, "description": str, "position": int},
            ...
        ],
    },
}
```

**Успішна екстракція:**

```python
{
    "success": True,
    "data": [
        {
            "url": str,
            "title": str,
            "content": str,
            "raw_content": str,
            "metadata": dict,    # optional
            "error": str,        # optional, only on per-URL failure
        },
        ...
    ],
}
```

**Будь‑яка можливість, у разі помилки:**

```python
{"success": False, "error": "human-readable message"}
```

Як `search()`, так і `extract()` можуть бути `async def` — диспетчер виявляє корутинові функції через `inspect.iscoroutinefunction` і чекає їх виконання. Синхронні реалізації, що виконують блокуючі I/O (HTTP, виклики SDK), підходять для малих бекендів; диспетчер обробляє їх у окремих потоках.

## Прапорці можливостей

Hermes маршрутує виклики до правильного провайдера на основі прапорців `supports_*`. Приклад багатопровайдерної конфігурації:

```yaml
# ~/.hermes/config.yaml
web:
  search_backend: "brave-free"     # search-only, fast, free 2k/mo
  extract_backend: "firecrawl"     # extract + crawl, paid quota
```

Коли `web.search_backend` або `web.extract_backend` не встановлені, обидва параметри спадають до `web.backend`. Якщо і його немає, Hermes вибирає перший доступний провайдер, який підтримує потрібну можливість, виходячи з наявності змінних середовища.

Якщо твій провайдер підтримує лише одну можливість, залиш інші прапорці за їхнім значенням за замовчуванням (`False`), і реєстр пропустить його для цього інструменту — користувачі не побачать помилкових повідомлень типу «провайдер X не вдалося», коли вони використовують X лише для пошуку і просять агента виконати екстракцію.

## Як Hermes підключає це до інструментів

Інструменти `web_search` та `web_extract` розташовані у `tools/web_tools.py`. Під час виклику вони:

1. Читають відповідний ключ конфігурації (`web.search_backend` для `web_search`, `web.extract_backend` для `web_extract`)
2. Запитують реєстр про провайдера з цим `name`
3. Перевіряють `is_available()` та відповідний прапорець `supports_*()`
4. Диспетчеризують до `search()` / `extract()` / `crawl()`, чекаючи, якщо метод є корутиновим
5. JSON‑серіалізують обгортку відповіді і повертають її LLM

Помилки повертаються як результат інструменту; LLM вирішує, як їх пояснити. Якщо жоден провайдер не зареєстрований (або всі доступні не проходять ворота можливості), інструмент повертає зрозумілу помилку з посиланням на `hermes tools`.

## Ліниве встановлення необов’язкових залежностей

Якщо твій провайдер обгортає сторонній SDK (наприклад, DDGS — пакет `ddgs`), не імпортуй його на рівні модуля. Використовуй `tools.lazy_deps.ensure(...)` всередині `is_available()` або `search()` — Hermes встановить пакет при першому використанні, за умови, що `security.allow_lazy_installs` дозволено. Дивись [Build a Hermes Plugin → Lazy-install](/guides/build-a-hermes-plugin#lazy-install-optional-python-dependencies) для моделі безпеки.

## Приклади реалізацій

- **`plugins/web/brave_free/`** — невеликий провайдер лише пошуку з API‑ключем. Хороший стартовий шаблон.
- **`plugins/web/ddgs/`** — провайдер без ключа, який ліниво встановлює свій SDK. Корисний шаблон для бекендів, що обгортають Python‑пакет.
- **`plugins/web/firecrawl/`** — повноцінний провайдер з кількома можливостями (search + extract + crawl) та різними режимами форматування.
- **`plugins/web/searxng/`** — самохостинг, бекенд, налаштований URL‑ом, без автентифікації.
- **`plugins/web/xai/`** — пошук, підкріплений LLM через серверний інструмент `web_search` від Grok. Показує, як повторно використати існуючу OAuth/змінну середовища (`tools/xai_http.py`) без додавання нових змінних, і як написати дешевий `is_available()`, що дотримується контракту без мережі.

## Поширення через pip

```toml
# pyproject.toml
[project.entry-points."hermes_agent.plugins"]
my-backend-web = "my_backend_web_package"
```

`my_backend_web_package` має експортувати функцію верхнього рівня `register`. Дивись [Distribute via pip](/guides/build-a-hermes-plugin#distribute-via-pip) у загальному посібнику щодо плагінів для повного налаштування.

## Пов’язані сторінки

- [Web Search](/user-guide/features/web-search) — документація функції для користувачів та налаштування бекендів
- [Plugins overview](/user-guide/features/plugins) — огляд усіх типів плагінів
- [Build a Hermes Plugin](/guides/build-a-hermes-plugin) — загальний посібник щодо інструментів/хукiв/слеш‑команд