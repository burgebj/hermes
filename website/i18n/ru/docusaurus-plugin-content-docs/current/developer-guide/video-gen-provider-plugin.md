---
sidebar_position: 12
title: "Плагины поставщика генерации видео"
description: "Как создать плагин бэкенда видеогенерации для Hermes Agent"
---

# Создание плагина провайдера генерации видео

Плагины провайдера video-gen регистрируют бэкенд, который обслуживает каждый вызов инструмента `video_generate`. Встроенные провайдеры (xAI, FAL) поставляются как плагины. Добавь новый или переопредели встроенный, поместив каталог в `plugins/video_gen/<name>/`.

:::tip
Video-gen почти полностью повторяет [Image Generation Provider Plugins](/developer-guide/image-gen-provider-plugin) — если ты уже создавал бэкенд для генерации изображений, ты знаешь, как это выглядит. Основные отличия: метод `capabilities()` объявляет модальности/соотношения сторон/длительности и соглашение о маршрутизации (передай `image_url`, чтобы использовать image-to-video, опусти его — будет использовано text-to-video; провайдер выбирает правильный эндпоинт внутри).
:::

## Унифицированный интерфейс (один инструмент, две модальности)

Инструмент `video_generate` предоставляет две модальности через один параметр:

- **Text-to-video** — вызывай только с `prompt`. Провайдер направляет запрос к своему эндпоинту text-to-video.
- **Image-to-video** — вызывай с `prompt` + `image_url`. Провайдер направляет запрос к своему эндпоинту image-to-video.

Редактирование и расширение намеренно не поддерживаются. Большинство бэкендов их не поддерживают, а добавление несоответствий заставило бы писать отдельные описания для каждого бэкенда в описании инструмента агента.

## Как работает обнаружение

Hermes сканирует бэкенды video-gen в трёх местах:

1. **Bundled** — `<repo>/plugins/video_gen/<name>/` (автозагрузка с `kind: backend`)
2. **User** — `~/.hermes/plugins/video_gen/<name>/` (включается через `plugins.enabled`)
3. **Pip** — пакеты, объявляющие точку входа `hermes_agent.plugins`

Функция `register(ctx)` каждого плагина вызывает `ctx.register_video_gen_provider(...)`. Активный провайдер выбирается параметром `video_gen.provider` в `config.yaml`; `hermes tools` → Video Generation проводит пользователя через выбор. В отличие от `image_generate`, нет встроенного устаревшего бэкенда в дереве — каждый провайдер является плагином.

## Структура каталога

```
plugins/video_gen/my-backend/
├── __init__.py      # VideoGenProvider subclass + register()
└── plugin.yaml      # Manifest with kind: backend
```

## Абстрактный базовый класс VideoGenProvider

Наследуй `agent.video_gen_provider.VideoGenProvider`. Требуются: свойство `name` и метод `generate()`.

```python
# plugins/video_gen/my-backend/__init__.py
from typing import Any, Dict, List, Optional
import os

from agent.video_gen_provider import (
    VideoGenProvider,
    error_response,
    success_response,
)


class MyVideoGenProvider(VideoGenProvider):
    @property
    def name(self) -> str:
        return "my-backend"

    @property
    def display_name(self) -> str:
        return "My Backend"

    def is_available(self) -> bool:
        return bool(os.environ.get("MY_API_KEY"))

    def list_models(self) -> List[Dict[str, Any]]:
        # Each entry is a model FAMILY — a name the user picks once.
        # Your provider's generate() routes within the family based on
        # whether image_url was passed.
        return [
            {
                "id": "fast",
                "display": "Fast",
                "speed": "~30s",
                "strengths": "Cheapest tier",
                "price": "$0.05/s",
                "modalities": ["text", "image"],  # advisory
            },
        ]

    def default_model(self) -> Optional[str]:
        return "fast"

    def capabilities(self) -> Dict[str, Any]:
        return {
            "modalities": ["text", "image"],
            "aspect_ratios": ["16:9", "9:16"],
            "resolutions": ["720p", "1080p"],
            "min_duration": 1,
            "max_duration": 10,
            "supports_audio": False,
            "supports_negative_prompt": True,
            "max_reference_images": 0,
        }

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "My Backend",
            "badge": "paid",
            "tag": "Short description shown in `hermes tools`",
            "env_vars": [
                {
                    "key": "MY_API_KEY",
                    "prompt": "My Backend API key",
                    "url": "https://mybackend.example.com/keys",
                },
            ],
        }

    def generate(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        image_url: Optional[str] = None,
        reference_image_urls: Optional[List[str]] = None,
        duration: Optional[int] = None,
        aspect_ratio: str = "16:9",
        resolution: str = "720p",
        negative_prompt: Optional[str] = None,
        audio: Optional[bool] = None,
        seed: Optional[int] = None,
        **kwargs: Any,  # always ignore unknown kwargs for forward-compat
    ) -> Dict[str, Any]:
        # ROUTE: image_url presence picks the endpoint.
        if image_url:
            endpoint = "my-backend/image-to-video"
            modality_used = "image"
        else:
            endpoint = "my-backend/text-to-video"
            modality_used = "text"

        # ... call your API ...

        return success_response(
            video="https://your-cdn/output.mp4",
            model=model or "fast",
            prompt=prompt,
            modality=modality_used,
            aspect_ratio=aspect_ratio,
            duration=duration or 5,
            provider=self.name,
        )


def register(ctx) -> None:
    ctx.register_video_gen_provider(MyVideoGenProvider())
```

## Манифест плагина

```yaml
# plugins/video_gen/my-backend/plugin.yaml
name: my-backend
version: 1.0.0
description: "My video generation backend"
author: Your Name
kind: backend
requires_env:
  - MY_API_KEY
```

## Схема `video_generate`

Инструмент предоставляет одну схему для всех бэкендов. Провайдеры игнорируют параметры, которые они не поддерживают.

| Parameter | What it does |
|---|---|
| `prompt` | Текстовая инструкция (обязательно) |
| `image_url` | Если указано — image-to-video; если опущено — text-to-video |
| `reference_image_urls` | Ссылки на стили/персонажей (зависит от провайдера) |
| `duration` | Секунды — провайдер ограничивает значение |
| `aspect_ratio` | `"16:9"`, `"9:16"`, `"1:1"`, … — провайдер ограничивает значение |
| `resolution` | `"480p"` / `"540p"` / `"720p"` / `"1080p"` — провайдер ограничивает значение |
| `negative_prompt` | Содержание, которое следует избегать (только Pixverse/Kling) |
| `audio` | Встроенный аудио (тарифный план Veo3 / Pixverse) |
| `seed` | Воспроизводимость |
| `model` | Переопределить активную модель/семейство |

Метод `capabilities()` провайдера объявляет, какие из этих параметров учитываются. Агент видит возможности активного бэкенда в описании инструмента, которое динамически пересобирается при смене бэкенда через `hermes tools`.

## Семейства моделей и маршрутизация эндпоинтов (шаблон FAL)

Если у твоего бэкенда несколько эндпоинтов на «модель» — как у FAL, где каждое семейство (Veo 3.1, Pixverse v6, Kling O3) имеет как `/text-to-video`, так и `/image-to-video` URL — представляй каждое **семейство** как одну запись в каталоге. Твой `generate()` выбирает правильный эндпоинт в зависимости от того, был ли передан `image_url`:

```python
FAMILIES = {
    "veo3.1": {
        "text_endpoint": "fal-ai/veo3.1",
        "image_endpoint": "fal-ai/veo3.1/image-to-video",
        # ... family-specific capability flags ...
    },
}

def generate(self, prompt, *, image_url=None, model=None, **kwargs):
    family_id, family = _resolve_family(model)
    endpoint = family["image_endpoint"] if image_url else family["text_endpoint"]
    # ... build payload from family's declared capability flags, call endpoint ...
```

Пользователь один раз выбирает `veo3.1` в `hermes tools`. Агент никогда не думает об эндпоинтах — он просто передаёт (или не передаёт) `image_url`.

## Приоритет выбора

Для параметров модели на уровне экземпляра (см. `plugins/video_gen/fal/__init__.py`):

1. Ключевое слово `model=` из вызова инструмента
2. Переменная окружения `<PROVIDER>_VIDEO_MODEL`
3. `video_gen.<provider>.model` в `config.yaml`
4. `video_gen.model` в `config.yaml` (если это один из твоих ID)
5. `default_model()` провайдера

## Формат ответа

`success_response()` и `error_response()` формируют словарь, который возвращает каждый бэкенд. Используй их — не создавай словарь вручную.

Ключи успешного ответа: `success`, `video` (URL или абсолютный путь), `model`, `prompt`, `modality` (`"text"` или `"image"`), `aspect_ratio`, `duration`, `provider`, плюс `extra`.

Ключи ошибки: `success`, `video` (None), `error`, `error_type`, `model`, `prompt`, `aspect_ratio`, `provider`.

## Где сохранять артефакты

Если бэкенд возвращает base64, используй `save_b64_video()` для записи в `$HERMES_HOME/cache/videos/`. Для сырых байтов, полученных через последующий HTTP‑запрос, используй `save_bytes_video()`. В остальных случаях возвращай прямой URL‑адрес upstream — шлюз разрешит удалённые URL при доставке.

## Тестирование

Помести smoke‑тест в `tests/plugins/video_gen/test_<name>_plugin.py`. Тесты xAI и FAL показывают шаблон — регистрировать, проверять каталог, проверять маршрутизацию с `image_url` и без него, а также убеждаться в корректных ошибочных ответах при отсутствии авторизации.