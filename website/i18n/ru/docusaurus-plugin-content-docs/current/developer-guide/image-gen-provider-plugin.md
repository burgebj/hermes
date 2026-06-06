---
sidebar_position: 11
title: "Плагины provider генерации изображений"
description: "Как создать плагин бэкенда генерации изображений для Hermes Agent"
---

# Создание плагина провайдера генерации изображений

Плагины провайдера image‑gen регистрируют backend, который обслуживает каждый вызов инструмента `image_generate` — DALL·E, gpt‑image, Grok, Flux, Imagen, Stable Diffusion, fal, Replicate, локальная сборка ComfyUI и любые другие. Встроенные провайдеры (OpenAI, OpenAI‑Codex, xAI) поставляются в виде плагинов. Ты можешь добавить новый или переопределить встроенный, поместив каталог в `plugins/image_gen/<name>/`.

:::tip
Image‑gen — один из нескольких **backend‑плагинов**, поддерживаемых Hermes. Другие (с более специализированными ABC) — [Memory Provider Plugins](/developer-guide/memory-provider-plugin), [Context Engine Plugins](/developer-guide/context-engine-plugin) и [Model Provider Plugins](/developer-guide/model-provider-plugin). Общие плагины инструментов/хуков/CLI находятся в разделе [Build a Hermes Plugin](/guides/build-a-hermes-plugin).
:::

## Как работает обнаружение

Hermes ищет backend‑ы image‑gen в трёх местах:

1. **Bundled** — `<repo>/plugins/image_gen/<name>/` (автозагружается с `kind: backend`, всегда доступен)
2. **User** — `~/.hermes/plugins/image_gen/<name>/` (включается через `plugins.enabled`)
3. **Pip** — пакеты, объявляющие точку входа `hermes_agent.plugins`

Функция `register(ctx)` каждого плагина вызывает `ctx.register_image_gen_provider(...)` — это помещает его в реестр в `agent/image_gen_registry.py`. Активный провайдер выбирается параметром `image_gen.provider` в `config.yaml`; команда `hermes tools` проводит пользователя через выбор.

Обёртка инструмента `image_generate` запрашивает реестр о текущем провайдере и перенаправляет запрос туда. Если провайдер не зарегистрирован, инструмент выводит понятную ошибку, указывающую на `hermes tools`.

## Структура каталога

```
plugins/image_gen/my-backend/
├── __init__.py      # ImageGenProvider subclass + register()
└── plugin.yaml      # Manifest with kind: backend
```

На этом этапе встроенный плагин считается готовым. Пользовательские плагины в `~/.hermes/plugins/image_gen/<name>/` необходимо добавить в `plugins.enabled` в `config.yaml` (или выполнить `hermes plugins enable <name>`).

## ABC ImageGenProvider

Наследуй `agent.image_gen_provider.ImageGenProvider`. Обязательными являются только свойство `name` и метод `generate()` — всё остальное имеет разумные значения по умолчанию:

```python
# plugins/image_gen/my-backend/__init__.py
from typing import Any, Dict, List, Optional
import os

from agent.image_gen_provider import (
    DEFAULT_ASPECT_RATIO,
    ImageGenProvider,
    error_response,
    resolve_aspect_ratio,
    save_b64_image,
    success_response,
)


class MyBackendImageGenProvider(ImageGenProvider):
    @property
    def name(self) -> str:
        # Stable id used in image_gen.provider config. Lowercase, no spaces.
        return "my-backend"

    @property
    def display_name(self) -> str:
        # Human label shown in `hermes tools`. Defaults to name.title() if omitted.
        return "My Backend"

    def is_available(self) -> bool:
        # Return False if credentials or deps are missing.
        # The tool's availability gate calls this before dispatch.
        if not os.environ.get("MY_BACKEND_API_KEY"):
            return False
        try:
            import my_backend_sdk  # noqa: F401
        except ImportError:
            return False
        return True

    def list_models(self) -> List[Dict[str, Any]]:
        # Catalog shown in `hermes tools` model picker.
        return [
            {
                "id": "my-model-fast",
                "display": "My Model (Fast)",
                "speed": "~5s",
                "strengths": "Quick iteration",
                "price": "$0.01/image",
            },
            {
                "id": "my-model-hq",
                "display": "My Model (HQ)",
                "speed": "~30s",
                "strengths": "Highest fidelity",
                "price": "$0.04/image",
            },
        ]

    def default_model(self) -> Optional[str]:
        return "my-model-fast"

    def get_setup_schema(self) -> Dict[str, Any]:
        # Metadata for the `hermes tools` picker — keys to prompt for at setup.
        return {
            "name": "My Backend",
            "badge": "paid",        # optional; shown as a short tag in the picker
            "tag": "One-line description shown under the name",
            "env_vars": [
                {
                    "key": "MY_BACKEND_API_KEY",
                    "prompt": "My Backend API key",
                    "url": "https://my-backend.example.com/api-keys",
                },
            ],
        }

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        prompt = (prompt or "").strip()
        aspect_ratio = resolve_aspect_ratio(aspect_ratio)

        if not prompt:
            return error_response(
                error="Prompt is required",
                error_type="invalid_input",
                provider=self.name,
                prompt="",
                aspect_ratio=aspect_ratio,
            )

        # Model selection precedence: env var → config → default. The helper
        # _resolve_model() in the built-in openai plugin is a good reference.
        model_id = kwargs.get("model") or self.default_model() or "my-model-fast"

        try:
            import my_backend_sdk
            client = my_backend_sdk.Client(api_key=os.environ["MY_BACKEND_API_KEY"])
            result = client.generate(
                prompt=prompt,
                model=model_id,
                aspect_ratio=aspect_ratio,
            )

            # Two shapes supported:
            #   - URL string: return it as `image`
            #   - base64 data: save under $HERMES_HOME/cache/images/ via save_b64_image()
            if result.get("image_b64"):
                path = save_b64_image(
                    result["image_b64"],
                    prefix=self.name,
                    extension="png",
                )
                image = str(path)
            else:
                image = result["image_url"]

            return success_response(
                image=image,
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                provider=self.name,
            )
        except Exception as exc:
            return error_response(
                error=str(exc),
                error_type=type(exc).__name__,
                provider=self.name,
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
            )


def register(ctx) -> None:
    """Plugin entry point — called once at load time."""
    ctx.register_image_gen_provider(MyBackendImageGenProvider())
```

## plugin.yaml

```yaml
name: my-backend
version: 1.0.0
description: My image backend — text-to-image via My Backend SDK
author: Your Name
kind: backend
requires_env:
  - MY_BACKEND_API_KEY
```

`kind: backend` указывает, что плагин относится к пути регистрации image‑gen. `requires_env` запрашивается во время `hermes plugins install`.

## Справочник ABC

Полный контракт находится в `agent/image_gen_provider.py`. Методы, которые обычно переопределяют:

| Member | Required | Default | Purpose |
|---|---|---|---|
| `name` | ✅ | — | Stable id, используемый в конфиге `image_gen.provider` |
| `display_name` | — | `name.title()` | Метка, отображаемая в `hermes tools` |
| `is_available()` | — | `True` | Фильтр для отсутствующих учётных данных/зависимостей |
| `list_models()` | — | `[]` | Каталог для выбора модели в `hermes tools` |
| `default_model()` | — | первая из `list_models()` | Запасной вариант, когда модель не указана |
| `get_setup_schema()` | — | minimal | Метаданные пикера + запросы переменных окружения |
| `generate(prompt, aspect_ratio, **kwargs)` | ✅ | — | Сам вызов |

## Формат ответа

`generate()` должен возвращать словарь, созданный через `success_response()` или `error_response()`. Оба находятся в `agent/image_gen_provider.py`.

**Успех:**
```python
success_response(
    image=<url-or-absolute-path>,
    model=<model-id>,
    prompt=<echoed-prompt>,
    aspect_ratio="landscape" | "square" | "portrait",
    provider=<your-provider-name>,
    extra={...},  # optional backend-specific fields
)
```

**Ошибка:**
```python
error_response(
    error="human-readable message",
    error_type="provider_error" | "invalid_input" | "<exception class name>",
    provider=<your-provider-name>,
    model=<model-id>,
    prompt=<prompt>,
    aspect_ratio=<resolved aspect>,
)
```

Обёртка инструмента сериализует словарь в JSON и передаёт его LLM. Ошибки выводятся как результат инструмента; LLM решает, как объяснить их пользователю.

## Обработка вывода base64 vs URL

Некоторые backend‑ы возвращают URL изображений (fal, Replicate); другие — payload в base64 (OpenAI gpt‑image‑2). Для случая base64 используй `save_b64_image()` — он сохраняет файл в `$HERMES_HOME/cache/images/<prefix>_<timestamp>_<uuid>.<ext>` и возвращает абсолютный `Path`. Передай этот путь (как `str`) в параметр `image=` функции `success_response()`. Доставка через шлюз (Telegram‑bubble, Discord‑attachment) распознаёт как URL, так и абсолютные пути.

## Переопределения пользователем

Помести пользовательский плагин в `~/.hermes/plugins/image_gen/<name>/` с тем же свойством `name`, что и у встроенного, и включи его через `hermes plugins enable <name>` — реестр использует правило «последний записавший выигрывает», поэтому твоя версия заменит встроенную. Это удобно, например, чтобы направить плагин `openai` на приватный прокси или подменить каталог моделей своим.

## Тестирование

```bash
export HERMES_HOME=/tmp/hermes-imggen-test
mkdir -p $HERMES_HOME/plugins/image_gen/my-backend
# …copy __init__.py + plugin.yaml into that dir…

export MY_BACKEND_API_KEY=your-test-key
hermes plugins enable my-backend

# Pick it as the active provider
echo "image_gen:" >> $HERMES_HOME/config.yaml
echo "  provider: my-backend" >> $HERMES_HOME/config.yaml

# Exercise it
hermes -z "Generate an image of a corgi in a spacesuit"
```

Или интерактивно: `hermes tools` → «Image Generation» → выбери `my-backend` → введи API‑ключ, если будет запрос.

## Реализации‑примеры

- **`plugins/image_gen/openai/__init__.py`** — gpt‑image‑2 в уровнях low/medium/high как три виртуальных идентификатора модели, использующие одну API‑модель с разными параметрами `quality`. Хороший пример уровневых моделей в одном backend + цепочка приоритетов в `config.yaml`.
- **`plugins/image_gen/xai/__init__.py`** — Grok Imagine через xAI. Другой формат (URL‑вывод, упрощённый каталог).
- **`plugins/image_gen/openai-codex/__init__.py`** — вариант Responses API в стиле Codex, переиспользующий SDK OpenAI с другим базовым URL маршрутизации.

## Распространение через pip

```toml
# pyproject.toml
[project.entry-points."hermes_agent.plugins"]
my-backend-imggen = "my_backend_imggen_package"
```

Пакет `my_backend_imggen_package` должен экспортировать функцию верхнего уровня `register`. См. раздел [Distribute via pip](/guides/build-a-hermes-plugin#distribute-via-pip) в общем руководстве по плагинам для полной настройки.

## Связанные страницы

- [Image Generation](/user-guide/features/image-generation) — документация пользовательской функции
- [Plugins overview](/user-guide/features/plugins) — обзор всех типов плагинов
- [Build a Hermes Plugin](/guides/build-a-hermes-plugin) — руководство по общим инструментам/хукам/слеш‑командам