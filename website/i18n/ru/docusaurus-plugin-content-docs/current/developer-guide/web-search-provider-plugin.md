---
sidebar_position: 12
title: "Веб‑поиск Provider плагины"
description: "Как построить бэкенд‑плагин для веб‑поиска/извлечения/сканирования для Hermes Agent"
---

# Создание плагина провайдера веб‑поиска

Плагины провайдеров веб‑поиска регистрируют бэкенд, обслуживающий `web_search`, `web_extract` и (опционально) вызовы инструмента deep‑crawl. Встроенные провайдеры — Firecrawl, SearXNG, Tavily, Exa, Parallel, Brave Search (бесплатный уровень), xAI и DDGS — все поставляются как плагины в `plugins/web/<name>/`. Ты можешь добавить новый или переопределить существующий, разместив каталог рядом с ними.

:::tip
Веб‑поиск — один из нескольких **backend‑плагинов**, поддерживаемых Hermes. Остальные (со своими ABC) — [Image Generation Provider Plugins](/developer-guide/image-gen-provider-plugin), [Video Generation Provider Plugins](/developer-guide/video-gen-provider-plugin), [Memory Provider Plugins](/developer-guide/memory-provider-plugin), [Context Engine Plugins](/developer-guide/context-engine-plugin) и [Model Provider Plugins](/developer-guide/model-provider-plugin). Общие плагины инструментов/хуков/CLI находятся в [Build a Hermes Plugin](/guides/build-a-hermes-plugin).
:::

## Как работает обнаружение

Hermes ищет бэкенды веб‑поиска в трёх местах:

1. **Bundled** — `<repo>/plugins/web/<name>/` (автозагружается с `kind: backend`, всегда доступен)
2. **User** — `~/.hermes/plugins/web/<name>/` (включается через `plugins.enabled` или `hermes plugins enable <name>`)
3. **Pip** — пакеты, объявляющие точку входа `hermes_agent.plugins`

Функция `register(ctx)` каждого плагина вызывает `ctx.register_web_search_provider(...)` — это помещает экземпляр в реестр в `agent/web_search_registry.py`. Активный провайдер для каждой возможности выбирается конфигурацией:

| Возможность | Ключ конфигурации | Запасной вариант |
|---|---|---|
| `web_search` | `web.search_backend` | `web.backend` |
| `web_extract` | `web.extract_backend` | `web.backend` |
| Режимы deep crawl внутри `web_extract` | `web.extract_backend` | `web.backend` |

Когда ни один из ключей не установлен, Hermes автоматически определяет бэкенд по наличию соответствующего API‑ключа/URL в окружении. `hermes tools` проводит пользователя через выбор.

## Структура каталога

```
plugins/web/my-backend/
├── __init__.py     # register() entry point
├── provider.py     # WebSearchProvider subclass
└── plugin.yaml     # Manifest with kind: backend and provides_web_providers
```

`brave_free/` и `ddgs/` — самые небольшие ссылки в дереве: `brave_free` — провайдер, работающий только по API‑ключу; `ddgs` — провайдер без ключа, который лениво устанавливает свой SDK.

## ABC `WebSearchProvider`

Наследуй `agent.web_search_provider.WebSearchProvider`. Обязательными членами являются `name`, `is_available()` и любой из `search()` / `extract()` / `crawl()`, которые ты реализуешь.

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

| Ключ | Назначение |
|---|---|
| `kind: backend` | Маршрутизирует плагин через путь загрузки бэкенда |
| `provides_web_providers` | Список `name` провайдеров, которые регистрирует этот плагин — используется загрузчиком для отображения плагина в `hermes tools` ещё до выполнения `register()` |
| `requires_env` | Интерактивный запрос учётных данных во время `hermes plugins install` (см. [Build a Hermes Plugin](/guides/build-a-hermes-plugin#gate-on-environment-variables) для полного формата) |

## Ссылка на ABC

Полный контракт в `agent/web_search_provider.py`. Методы, которые можно переопределить:

| Член | Обязательно | По умолчанию | Назначение |
|---|---|---|---|
| `name` | ✅ | — | Стабильный идентификатор, используемый в конфигурации `web.*_backend` |
| `display_name` | — | `name` | Метка, отображаемая в `hermes tools` |
| `is_available()` | ✅ | — | Дешёвый шлюз доступности — переменные окружения, необязательные зависимости |
| `supports_search()` | — | `True` | Флаг возможности для маршрутизации `web_search` |
| `supports_extract()` | — | `False` | Флаг возможности для маршрутизации `web_extract` |
| `search(query, limit)` | условно | бросает | Требуется, когда `supports_search()` возвращает `True` |
| `extract(urls, **kwargs)` | условно | бросает | Требуется, когда `supports_extract()` возвращает `True` |

Провайдеры могут объявлять несколько возможностей в одном классе — Firecrawl, Tavily, Exa и Parallel реализуют и поиск, и извлечение. Brave Search и DDGS только поиск; SearXNG только поиск с документированным рабочим процессом «подключи меня к провайдеру извлечения».

## Формат ответа

Обёртка инструмента ожидает фиксированный конверт, чтобы не переводить данные между бэкендами.

**Успешный поиск:**

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

**Успешное извлечение:**

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

**Любая возможность при ошибке:**

```python
{"success": False, "error": "human-readable message"}
```

Как `search()`, так и `extract()` могут быть `async def` — диспетчер определяет корутины через `inspect.iscoroutinefunction` и ожидает их при необходимости. Синхронные реализации, выполняющие блокирующий I/O (HTTP, вызовы SDK), подходят для небольших бэкендов; диспетчер обрабатывает их в отдельном потоке.

## Флаги возможностей

Hermes направляет вызовы к нужному провайдеру на основе флагов `supports_*`. Пример типичной конфигурации с несколькими провайдерами:

```yaml
# ~/.hermes/config.yaml
web:
  search_backend: "brave-free"     # search-only, fast, free 2k/mo
  extract_backend: "firecrawl"     # extract + crawl, paid quota
```

Когда `web.search_backend` или `web.extract_backend` не заданы, оба переходят к `web.backend`. Если и он не установлен, Hermes выбирает первый доступный провайдер, поддерживающий требуемую возможность, основываясь на наличии переменных окружения.

Если твой провайдер поддерживает только одну возможность, оставь остальные флаги со значением по умолчанию (`False`), и реестр пропустит его для этого инструмента — пользователи не увидят вводящие в заблуждение сообщения «провайдер X не удалось», когда они используют X только для поиска и просят агент выполнить извлечение.

## Как Hermes подключает это к инструментам

Инструменты `web_search` и `web_extract` находятся в `tools/web_tools.py`. При вызове они:

1. Считывают соответствующий ключ конфигурации (`web.search_backend` для `web_search`, `web.extract_backend` для `web_extract`);
2. Запрашивают реестр провайдера с этим `name`;
3. Проверяют `is_available()` и соответствующий флаг `supports_*()`;
4. Диспатчатся к `search()` / `extract()` / `crawl()`, ожидая, если метод является корутиной;
5. Сериализуют ответ в JSON и возвращают его LLM.

Ошибки попадают в результат инструмента; LLM решает, как их объяснить. Если провайдер не зарегистрирован (или каждый доступный провайдер не проходит проверку возможности), инструмент возвращает полезную ошибку с указанием `hermes tools`.

## Ленивое установление необязательных зависимостей

Если твой провайдер оборачивает сторонний SDK (как DDGS оборачивает пакет `ddgs`), не импортируй его на уровне модуля. Используй `tools.lazy_deps.ensure(...)` внутри `is_available()` или `search()` — Hermes установит пакет при первом использовании, если включена опция `security.allow_lazy_installs`. См. [Build a Hermes Plugin → Lazy-install](/guides/build-a-hermes-plugin#lazy-install-optional-python-dependencies) для модели безопасности.

## Реализации‑пример

- **`plugins/web/brave_free/`** — небольшой провайдер, работающий только по API‑ключу, только поиск. Хороший шаблон для начала.
- **`plugins/web/ddgs/`** — провайдер без ключа, который лениво устанавливает свой SDK. Полезный шаблон для бэкендов, оборачивающих Python‑пакет.
- **`plugins/web/firecrawl/`** — полноценный провайдер с несколькими возможностями (поиск + извлечение + crawl) и различными режимами формата.
- **`plugins/web/searxng/`** — самохостинг, конфигурируемый URL‑ом бэкенд без аутентификации.
- **`plugins/web/xai/`** — поиск, поддерживаемый LLM через серверный инструмент `web_search` от Grok. Показано, как переиспользовать существующий OAuth/переменную окружения (`tools/xai_http.py`) без добавления новых переменных и как написать дешёвый `is_available()`, соблюдающий контракт «без сети».

## Распространение через pip

```toml
# pyproject.toml
[project.entry-points."hermes_agent.plugins"]
my-backend-web = "my_backend_web_package"
```

`my_backend_web_package` должен экспортировать функцию верхнего уровня `register`. См. [Distribute via pip](/guides/build-a-hermes-plugin#distribute-via-pip) в общем руководстве по плагинам для полной настройки.

## Связанные страницы

- [Web Search](/user-guide/features/web-search) — документация пользовательской функции и конфигурация per‑backend
- [Plugins overview](/user-guide/features/plugins) — обзор всех типов плагинов
- [Build a Hermes Plugin](/guides/build-a-hermes-plugin) — общее руководство по инструментам/хукам/слеш‑командам