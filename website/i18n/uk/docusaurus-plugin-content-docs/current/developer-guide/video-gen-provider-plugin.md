---
sidebar_position: 12
title: "Плагіни провайдера генерації відео"
description: "Як створити бекенд‑плагін для генерації відео для Hermes Agent"
---

# Створення плагіна провайдера генерації відео

Плагіни провайдера **video‑gen** реєструють бекенд, який обслуговує кожен виклик інструмента `video_generate`. Вбудовані провайдери (xAI, FAL) постачаються як плагіни. Додай новий або заміни вбудований, просто склавши каталог у `plugins/video_gen/<name>/`.

:::tip
Video‑gen відображає [Image Generation Provider Plugins](/developer-guide/image-gen-provider-plugin) майже рядок за рядком — якщо ти вже створив бекенд для генерації зображень, ти вже знаєш його структуру. Основні відмінності: метод `capabilities()`, який оголошує модальності, співвідношення сторін та тривалість, та конвенція маршрутизації (передай `image_url`, щоб використати image‑to‑video, опусти його, щоб використати text‑to‑video — провайдер сам обирає правильний кінцевий пункт).
:::

## Єдина поверхня (один інструмент, дві модальності)

Інструмент `video_generate` пропонує дві модальності через один параметр:

- **Text‑to‑video** — виклик лише з `prompt`. Провайдер перенаправляє на свій endpoint text‑to‑video.
- **Image‑to‑video** — виклик з `prompt` + `image_url`. Провайдер перенаправляє на свій endpoint image‑to‑video.

Редагування та розширення навмисно не входять у сферу. Більшість бекендів їх не підтримують, а несумісність змусила б додавати специфічний текст для кожного бекенду у опис інструмента агента.

## Як працює виявлення

Hermes сканує бекенди **video‑gen** у трьох місцях:

1. **Bundled** — `<repo>/plugins/video_gen/<name>/` (автозавантажується з `kind: backend`)
2. **User** — `~/.hermes/plugins/video_gen/<name>/` (вмикається через `plugins.enabled`)
3. **Pip** — пакети, що оголошують точку входу `hermes_agent.plugins`

У кожного плагіна функція `register(ctx)` викликає `ctx.register_video_gen_provider(...)`. Активний провайдер вибирається параметром `video_gen.provider` у `config.yaml`; `hermes tools` → **Video Generation** проводить користувача через вибір. На відміну від `image_generate`, немає вбудованого legacy‑бекенду — кожен провайдер є плагіном.

## Структура каталогу

```
plugins/video_gen/my-backend/
├── __init__.py      # VideoGenProvider subclass + register()
└── plugin.yaml      # Manifest with kind: backend
```

## ABC `VideoGenProvider`

Наслідуй `agent.video_gen_provider.VideoGenProvider`. Обов’язкові: властивість `name` та метод `generate()`.

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

## Маніфест плагіна

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

Інструмент пропонує одну схему для всіх бекендів. Провайдери ігнорують параметри, які не підтримують.

| Parameter | What it does |
|---|---|
| `prompt` | Текстова інструкція (обов’язково) |
| `image_url` | Якщо встановлено → image‑to‑video; якщо пропущено → text‑to‑video |
| `reference_image_urls` | Посилання на стиль/персонаж (залежить від провайдера) |
| `duration` | Секунди — провайдер обмежує |
| `aspect_ratio` | `"16:9"`, `"9:16"`, `"1:1"` … — провайдер обмежує |
| `resolution` | `"480p"` / `"540p"` / `"720p"` / `"1080p"` — провайдер обмежує |
| `negative_prompt` | Що уникати (лише Pixverse/Kling) |
| `audio` | Вбудований аудіо (тариф Veo3 / Pixverse) |
| `seed` | Відтворюваність |
| `model` | Перевизначення активної моделі/сімейства |

Метод `capabilities()` провайдера оголошує, які з цих параметрів підтримуються. Агент бачить можливості активного бекенду у описі інструмента, який динамічно оновлюється, коли користувач змінює бекенд через `hermes tools`.

## Сімейства моделей та маршрутизація endpoint‑ів (патерн FAL)

Коли у твоєму бекенді кілька endpoint‑ів на «модель» — як у FAL, де кожне сімейство (Veo 3.1, Pixverse v6, Kling O3) має і `/text-to-video`, і `/image-to-video` URL — представляй кожне **сімейство** як один запис у каталозі. Твій `generate()` обирає правильний endpoint залежно від того, чи був переданий `image_url`:

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

Користувач один раз вибирає `veo3.1` у `hermes tools`. Агент більше не думає про endpoint‑и — він просто передає (або не передає) `image_url`.

## Пріоритет вибору

Для налаштувань моделі на рівні інстанції (див. `plugins/video_gen/fal/__init__.py`):

1. Ключове слово `model=` у виклику інструмента
2. Змінна середовища `<PROVIDER>_VIDEO_MODEL`
3. `video_gen.<provider>.model` у `config.yaml`
4. `video_gen.model` у `config.yaml` (коли це один з твоїх ID)
5. `default_model()` провайдера

## Формат відповіді

`success_response()` та `error_response()` формують словник, який повертає кожен бекенд. Використовуй їх — не створюй словник вручну.

**Ключі успішної відповіді:** `success`, `video` (URL або абсолютний шлях), `model`, `prompt`, `modality` (`"text"` або `"image"`), `aspect_ratio`, `duration`, `provider`, плюс `extra`.

**Ключі помилкової відповіді:** `success`, `video` (None), `error`, `error_type`, `model`, `prompt`, `aspect_ratio`, `provider`.

## Куди зберігати артефакти

Якщо бекенд повертає base64, використай `save_b64_video()` для запису у `$HERMES_HOME/cache/videos/`. Для сирих байтів, отриманих після HTTP‑запиту, використай `save_bytes_video()`. Інакше поверни прямий upstream‑URL — шлюз інструментів розв’язує віддалені URL під час доставки.

## Тестування

Додай smoke‑тест у `tests/plugins/video_gen/test_<name>_plugin.py`. Тести xAI та FAL демонструють патерн — реєстрація, перевірка каталогу, тестування маршрутизації з `image_url` і без нього, а також перевірка чистих помилкових відповідей при відсутності автентифікації.