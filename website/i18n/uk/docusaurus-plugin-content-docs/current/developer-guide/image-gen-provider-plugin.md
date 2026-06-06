---
sidebar_position: 11
title: "Плагіни провайдерів генерації зображень"
description: "Як створити плагін бекенду генерації зображень для Hermes Agent"
---

# Створення плагіна провайдера генерації зображень

Плагіни провайдера image‑gen реєструють бекенд, який обслуговує кожен виклик інструмента `image_generate` — DALL·E, gpt-image, Grok, Flux, Imagen, Stable Diffusion, fal, Replicate, локальна установка ComfyUI, anything. Вбудовані провайдери (OpenAI, OpenAI‑Codex, xAI) постачаються як плагіни. Ти можеш додати новий або перевизначити вбудований, просто склавши каталог у `plugins/image_gen/<name>/`.

:::tip
Image‑gen — один із кількох **бекенд‑плагінів**, які підтримує Hermes. Інші (з більш спеціалізованими ABC) — це [Memory Provider Plugins](/developer-guide/memory-provider-plugin), [Context Engine Plugins](/developer-guide/context-engine-plugin) та [Model Provider Plugins](/developer-guide/model-provider-plugin). Плагіни інструментів/хукiв/CLI розташовані у [Build a Hermes Plugin](/guides/build-a-hermes-plugin).
:::

## Як працює виявлення

Hermes сканує бекенди image‑gen у трьох місцях:

1. **Bundled** — `<repo>/plugins/image_gen/<name>/` (автозавантажується з `kind: backend`, завжди доступний)
2. **User** — `~/.hermes/plugins/image_gen/<name>/` (вмикається через `plugins.enabled`)
3. **Pip** — пакети, що оголошують точку входу `hermes_agent.plugins`

У кожного плагіна функція `register(ctx)` викликає `ctx.register_image_gen_provider(...)` — це додає його до реєстру у `agent/image_gen_registry.py`. Активний провайдер обирається параметром `image_gen.provider` у `config.yaml`; `hermes tools` проводить користувача через вибір.

Обгортка інструмента `image_generate` запитує реєстр про активний провайдер і передає виклик туди. Якщо провайдер не зареєстрований, інструмент виводить зрозумілу помилку, що вказує на `hermes tools`.

## Структура каталогу

```
plugins/image_gen/my-backend/
├── __init__.py      # ImageGenProvider subclass + register()
└── plugin.yaml      # Manifest with kind: backend
```

Вбудований плагін завершений на цьому етапі. Користувацькі плагіни у `~/.hermes/plugins/image_gen/<name>/` потрібно додати до `plugins.enabled` у `config.yaml` (або виконати `hermes plugins enable <name>`).

## ABC ImageGenProvider

Наслідуй `agent.image_gen_provider.ImageGenProvider`. Єдиними обов’язковими членами є властивість `name` та метод `generate()` — все інше має розумні значення за замовчуванням:

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

`kind: backend` — це те, що направляє плагін у шлях реєстрації image‑gen. `requires_env` запитується під час `hermes plugins install`.

## Довідка по ABC

Повний контракт у `agent/image_gen_provider.py`. Методи, які зазвичай перевизначають:

| Member | Required | Default | Purpose |
|---|---|---|---|
| `name` | ✅ | — | Стабільний ідентифікатор, що використовується в конфігурації `image_gen.provider` |
| `display_name` | — | `name.title()` | Мітка, що показується у `hermes tools` |
| `is_available()` | — | `True` | Перевірка наявності облікових даних/залежностей |
| `list_models()` | — | `[]` | Каталог для вибору моделі у `hermes tools` |
| `default_model()` | — | перша з `list_models()` | Запасний (варіант), коли модель не налаштована |
| `get_setup_schema()` | — | minimal | Метадані вибору + підказки змінних оточення |
| `generate(prompt, aspect_ratio, **kwargs)` | ✅ | — | Виклик |

## Формат відповіді

`generate()` має повертати словник, створений за допомогою `success_response()` або `error_response()`. Обидві функції знаходяться у `agent/image_gen_provider.py`.

**Успіх:**
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

**Помилка:**
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

Обгортка інструмента серіалізує словник у JSON і передає його LLM. Помилки повертаються як результат інструмента; LLM вирішує, як їх пояснити користувачеві.

## Обробка виводу base64 vs URL

Деякі бекенди повертають URL‑адреси зображень (fal, Replicate); інші — payload у base64 (OpenAI gpt-image-2). Для випадку base64 використай `save_b64_image()` — вона записує файл у `$HERMES_HOME/cache/images/<prefix>_<timestamp>_<uuid>.<ext>` і повертає абсолютний `Path`. Передай цей шлях (як `str`) у параметр `image=` функції `success_response()`. Доставка шлюзом (Telegram photo bubble, Discord attachment) розпізнає і URL, і абсолютні шляхи.

## Перевизначення користувачем

Скинь користувацький плагін у `~/.hermes/plugins/image_gen/<name>/` з тією ж властивістю `name`, що й у вбудованого, і ввімкни його за допомогою `hermes plugins enable <name>` — реєстр працює за принципом «останній запис перемагає», тому твоя версія замінює вбудовану. Це корисно, наприклад, щоб направити плагін `openai` на приватний проксі або підмінити каталог моделей власним.

## Тестування

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

Або інтерактивно: `hermes tools` → «Image Generation» → вибери `my-backend` → введи API‑ключ, якщо буде запит.

## Приклади реалізацій

- **`plugins/image_gen/openai/__init__.py`** — gpt-image-2 у трьох рівнях (low/medium/high) як три віртуальні ідентифікатори моделей, що ділять один API‑модель з різними параметрами `quality`. Хороший приклад багаторівневих моделей в одному бекенді + ланцюжок пріоритету `config.yaml`.
- **`plugins/image_gen/xai/__init__.py`** — Grok Imagine через xAI. Інший формат (вивід URL, простіший каталог).
- **`plugins/image_gen/openai-codex/__init__.py`** — варіант Responses API у стилі Codex, що повторно використовує SDK OpenAI з іншим базовим URL маршруту.

## Поширення через pip

```toml
# pyproject.toml
[project.entry-points."hermes_agent.plugins"]
my-backend-imggen = "my_backend_imggen_package"
```

`my_backend_imggen_package` має експортувати функцію верхнього рівня `register`. Дивись розділ [Distribute via pip](/guides/build-a-hermes-plugin#distribute-via-pip) у загальному посібнику зі створення плагінів для повного налаштування.

## Пов’язані сторінки

- [Image Generation](/user-guide/features/image-generation) — документація функції для користувачів
- [Plugins overview](/user-guide/features/plugins) — огляд усіх типів плагінів
- [Build a Hermes Plugin](/guides/build-a-hermes-plugin) — загальний посібник щодо інструментів/хукiв/слеш‑команд