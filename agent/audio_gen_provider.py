"""
Audio Generation Provider ABC
=============================

Defines the pluggable-backend interface for **audio generation** — music,
sound effects, and other non-speech audio synthesized from a text prompt.
Providers register instances via
``PluginContext.register_audio_gen_provider()``; the active one (selected
via ``audio_gen.provider`` in ``config.yaml``) services every
``audio_generate`` tool call.

This is the audio analogue of ``agent/video_gen_provider.py`` — the two
surfaces are intentionally near-identical so they stay learnable together.
It is distinct from TTS (``tools/tts_tool.py``): TTS reads a fixed string
aloud in a chosen voice, whereas audio generation composes new audio
(a song, an ambience, a sound effect) from a creative prompt.

Providers live in ``<repo>/plugins/audio_gen/<name>/`` (built-in, auto-
loaded as ``kind: backend``) or ``~/.hermes/plugins/audio_gen/<name>/``
(user, opt-in via ``plugins.enabled``).

Response shape
--------------
All providers return a dict built by :func:`success_response` /
:func:`error_response`. Keys:

    success         bool
    audio           str | None      URL or absolute file path
    model           str             provider-specific model identifier
    prompt          str             echoed prompt
    duration        int             seconds (0 if not applicable)
    format          str             container/codec, e.g. "mp3", "wav"
    provider        str             provider name (for diagnostics)
    error           str             only when success=False
    error_type      str             only when success=False
"""

from __future__ import annotations

import abc
import base64
import datetime
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# Common output formats across audio-gen backends. The tool schema advertises
# this set as a hint; providers may accept a narrower/wider set and are
# responsible for clamping.
COMMON_AUDIO_FORMATS: Tuple[str, ...] = ("mp3", "wav", "ogg", "flac")
DEFAULT_AUDIO_FORMAT = "mp3"


# ---------------------------------------------------------------------------
# ABC
# ---------------------------------------------------------------------------


class AudioGenProvider(abc.ABC):
    """Abstract base class for an audio generation backend.

    Subclasses must implement :meth:`generate`. Everything else has sane
    defaults — override only what your provider needs.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Stable short identifier used in ``audio_gen.provider`` config.

        Lowercase, no spaces. Examples: ``openrouter``, ``fal``, ``elevenlabs``.
        """

    @property
    def display_name(self) -> str:
        """Human-readable label shown in ``hermes tools``. Defaults to ``name.title()``."""
        return self.name.title()

    def is_available(self) -> bool:
        """Return True when this provider can service calls.

        Typically checks for a required API key and optional-dependency
        import. Default: True.
        """
        return True

    def list_models(self) -> List[Dict[str, Any]]:
        """Return catalog entries for the ``hermes tools`` model picker.

        Each entry::

            {
                "id": "google/lyria-3-pro-preview",   # required
                "display": "Lyria 3 Pro",             # optional; defaults to id
                "strengths": "...",                   # optional
                "kinds": ["music"],                   # optional, advisory
            }

        Default: empty list (provider has no user-selectable models).
        """
        return []

    def get_setup_schema(self) -> Dict[str, Any]:
        """Return provider metadata for the ``hermes tools`` picker."""
        return {
            "name": self.display_name,
            "badge": "",
            "tag": "",
            "env_vars": [],
        }

    def default_model(self) -> Optional[str]:
        """Return the default model id, or None if not applicable."""
        models = self.list_models()
        if models:
            return models[0].get("id")
        return None

    def capabilities(self) -> Dict[str, Any]:
        """Return what this provider supports.

        Returned dict (all keys optional)::

            {
                "kinds": ["music", "sfx"],   # what kind of audio it makes
                "formats": ["mp3", "wav"],
                "max_duration": 30,           # seconds
                "min_duration": 1,
                "supports_lyrics": True,
                "supports_negative_prompt": False,
            }

        Used by the tool layer for soft validation and by ``hermes tools``
        for the picker. Default: music-only.
        """
        return {
            "kinds": ["music"],
            "formats": list(COMMON_AUDIO_FORMATS),
            "max_duration": 30,
            "min_duration": 1,
            "supports_lyrics": False,
            "supports_negative_prompt": False,
        }

    @abc.abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        duration: Optional[int] = None,
        audio_format: str = DEFAULT_AUDIO_FORMAT,
        negative_prompt: Optional[str] = None,
        lyrics: Optional[str] = None,
        seed: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate audio from a text prompt.

        Implementations should return the dict from :func:`success_response`
        or :func:`error_response`. ``kwargs`` may contain forward-compat
        parameters future versions of the schema will expose — implementations
        MUST ignore unknown keys (no TypeError).
        """


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _audio_cache_dir() -> Path:
    """Return ``$HERMES_HOME/cache/audio_gen/``, creating parents as needed."""
    from hermes_constants import get_hermes_home

    path = get_hermes_home() / "cache" / "audio_gen"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_b64_audio(
    b64_data: str,
    *,
    prefix: str = "audio",
    extension: str = "mp3",
) -> Path:
    """Decode base64 audio data and write under ``$HERMES_HOME/cache/audio_gen/``.

    Returns the absolute :class:`Path` to the saved file.

    Filename format: ``<prefix>_<YYYYMMDD_HHMMSS>_<short-uuid>.<ext>``.
    """
    raw = base64.b64decode(b64_data)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    short = uuid.uuid4().hex[:8]
    path = _audio_cache_dir() / f"{prefix}_{ts}_{short}.{extension}"
    path.write_bytes(raw)
    return path


def save_bytes_audio(
    raw: bytes,
    *,
    prefix: str = "audio",
    extension: str = "mp3",
) -> Path:
    """Write raw audio bytes (e.g. an HTTP download body) to the cache."""
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    short = uuid.uuid4().hex[:8]
    path = _audio_cache_dir() / f"{prefix}_{ts}_{short}.{extension}"
    path.write_bytes(raw)
    return path


def success_response(
    *,
    audio: str,
    model: str,
    prompt: str,
    duration: int = 0,
    audio_format: str = "",
    provider: str,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a uniform success response dict.

    ``audio`` may be an HTTP URL or an absolute filesystem path.
    """
    payload: Dict[str, Any] = {
        "success": True,
        "audio": audio,
        "model": model,
        "prompt": prompt,
        "duration": int(duration) if duration else 0,
        "format": audio_format,
        "provider": provider,
    }
    if extra:
        for k, v in extra.items():
            payload.setdefault(k, v)
    return payload


def error_response(
    *,
    error: str,
    error_type: str = "provider_error",
    provider: str = "",
    model: str = "",
    prompt: str = "",
) -> Dict[str, Any]:
    """Build a uniform error response dict."""
    return {
        "success": False,
        "audio": None,
        "error": error,
        "error_type": error_type,
        "model": model,
        "prompt": prompt,
        "provider": provider,
    }
