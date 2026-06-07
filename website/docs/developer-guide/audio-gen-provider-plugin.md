---
sidebar_position: 13
title: "Audio Generation Provider Plugins"
description: "How to build an audio-generation backend plugin for Hermes Agent"
---

# Building an Audio Generation Provider Plugin

Audio-gen provider plugins register a backend that services every `audio_generate` tool call — composing music, soundscapes, or sound effects from a text prompt. The bundled OpenRouter backend (Google Lyria 3, GPT-Audio) ships as a plugin. Add a new one, or override a bundled one, by dropping a directory into `plugins/audio_gen/<name>/`.

:::tip
Audio-gen mirrors [Video Generation Provider Plugins](/developer-guide/video-gen-provider-plugin) almost line-for-line — same registry/ABC/picker shape. The difference is the payload: instead of resolutions and aspect ratios, audio backends advertise `kinds` (music / sfx), `formats`, a duration range, and lyric/negative-prompt flags via `capabilities()`.
:::

## Audio generation vs. text-to-speech

`audio_generate` is **not** TTS. They are separate tools:

- **`text_to_speech`** reads a fixed string aloud in a chosen voice — narration, voice messages. See [TTS Setup](/user-guide/features/tts).
- **`audio_generate`** composes *new* audio from a creative prompt — a song, a jingle, ambient rain, a retro game sound.

Keep the two distinct in your provider's prose so the agent reaches for the right one.

## How discovery works

Hermes scans for audio-gen backends in three places:

1. **Bundled** — `<repo>/plugins/audio_gen/<name>/` (auto-loaded with `kind: backend`)
2. **User** — `~/.hermes/plugins/audio_gen/<name>/` (opt-in via `plugins.enabled`)
3. **Pip** — packages declaring a `hermes_agent.plugins` entry point

Each plugin's `register(ctx)` function calls `ctx.register_audio_gen_provider(...)`. The active provider is picked by `audio_gen.provider` in `config.yaml`; `hermes tools` → Audio Generation walks users through selection. Like `video_generate`, there is no in-tree legacy backend — every provider is a plugin. The `audio_gen` toolset is **off by default**; users opt in.

## Directory structure

```
plugins/audio_gen/my-backend/
├── __init__.py      # AudioGenProvider subclass + register()
└── plugin.yaml      # Manifest with kind: backend
```

## The AudioGenProvider ABC

Subclass `agent.audio_gen_provider.AudioGenProvider`. Required: `name` property and `generate()` method.

```python
# plugins/audio_gen/my-backend/__init__.py
from typing import Any, Dict, List, Optional
import os

from agent.audio_gen_provider import (
    AudioGenProvider,
    error_response,
    success_response,
    save_b64_audio,
)


class MyAudioGenProvider(AudioGenProvider):
    @property
    def name(self) -> str:
        return "my-backend"

    @property
    def display_name(self) -> str:
        return "My Backend"

    def is_available(self) -> bool:
        return bool(os.environ.get("MY_API_KEY"))

    def list_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "song-v1",
                "display": "Song v1",
                "strengths": "Music with vocals",
                "kinds": ["music"],
            },
        ]

    def default_model(self) -> Optional[str]:
        return "song-v1"

    def capabilities(self) -> Dict[str, Any]:
        return {
            "kinds": ["music", "sfx"],
            "formats": ["mp3", "wav"],
            "min_duration": 1,
            "max_duration": 60,
            "supports_lyrics": True,
            "supports_negative_prompt": False,
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
        duration: Optional[int] = None,
        audio_format: str = "mp3",
        negative_prompt: Optional[str] = None,
        lyrics: Optional[str] = None,
        seed: Optional[int] = None,
        **kwargs: Any,  # always ignore unknown kwargs for forward-compat
    ) -> Dict[str, Any]:
        # ... call your API ...
        # If it returns base64, persist it under the audio-gen cache:
        path = save_b64_audio(b64_data, prefix="my-backend", extension=audio_format)

        return success_response(
            audio=str(path),
            model=model or "song-v1",
            prompt=prompt,
            duration=duration or 0,
            audio_format=audio_format,
            provider=self.name,
        )


def register(ctx) -> None:
    ctx.register_audio_gen_provider(MyAudioGenProvider())
```

## The plugin manifest

```yaml
# plugins/audio_gen/my-backend/plugin.yaml
name: my-backend
version: 1.0.0
description: "My audio generation backend"
author: Your Name
kind: backend
requires_env:
  - MY_API_KEY
```

## The `audio_generate` schema

The tool exposes one schema across every backend. Providers ignore parameters they don't support.

| Parameter | What it does |
|---|---|
| `prompt` | Text instruction describing the audio (required) |
| `duration` | Seconds — provider clamps |
| `audio_format` | `"mp3"` / `"wav"` / `"ogg"` / `"flac"` — provider clamps |
| `negative_prompt` | Content to avoid (provider-dependent) |
| `lyrics` | Lyrics for vocal/song models (ignored by instrumental/SFX backends) |
| `seed` | Reproducibility |
| `model` | Override the active model/family |

The provider's `capabilities()` advertises which of these are honored. The agent sees the active backend's capabilities in the tool description, dynamically rebuilt when the user changes backend via `hermes tools`.

## The OpenRouter pattern (streamed chat-completions audio output)

OpenRouter has **no** dedicated `/audio/generate` endpoint. Its music models (Lyria 3) are ordinary chat-completions models that declare `audio` in their output modalities. Verified against the live API, the call has two non-obvious requirements:

- `modalities` must be `["text", "audio"]` — audio-only is rejected.
- `stream: true` is **required** — a non-streaming request returns HTTP 400 (`"Audio output requires stream: true"`).

The base64 audio then arrives across streamed `delta.audio.data` chunks, which the backend concatenates before decoding with `save_b64_audio()`. The bundled `plugins/audio_gen/openrouter/` backend does exactly this and reuses the agent's `OPENROUTER_API_KEY` via the shared `resolve_openrouter_credentials()` helper, so it auto-works when Hermes runs on OpenRouter.

:::note
OpenAI's `gpt-audio` models also advertise audio output, but they additionally require an `audio.voice` parameter and behave like speech synthesis — so they belong to the [`text_to_speech`](/user-guide/features/tts) tool (OpenRouter is a built-in TTS provider), not audio generation. The OpenRouter audio-gen backend deliberately scopes its catalog to the Lyria music family.
:::

Use it as your reference implementation.

## Response shape

`success_response()` and `error_response()` produce the dict shape every backend returns. Use them — don't hand-roll the dict.

Success keys: `success`, `audio` (URL or absolute path), `model`, `prompt`, `duration`, `format`, `provider`, plus `extra`.

Error keys: `success`, `audio` (None), `error`, `error_type`, `model`, `prompt`, `provider`.

## Where to save artifacts

If your backend returns base64, use `save_b64_audio()` to write under `$HERMES_HOME/cache/audio_gen/`. For raw bytes from an HTTP download, use `save_bytes_audio()`. Otherwise return the upstream URL directly — the gateway resolves remote URLs on delivery.

## Testing

Drop a smoke test under `tests/plugins/audio_gen/test_<name>_plugin.py`. The OpenRouter test shows the pattern — stub the model-catalog fetch, register, verify catalog + capabilities, exercise `generate()` with a mocked HTTP response, and assert clean error responses on missing auth / no audio in the response.
