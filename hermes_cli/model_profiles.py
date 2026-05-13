"""Shared helpers for Hermes model routing profiles.

The routing policy uses two named slots:
- main: ordinary/cheap/default work
- escalate: senior/review/implementation work

The helpers here deliberately stay config-driven so the CLI, gateway, and
quota commands can all resolve the same routing state without re-implementing
slot parsing in multiple places.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


_PROFILE_LABELS = {
    "main": "main/default",
    "escalate": "senior/escalate",
}


@dataclass(frozen=True)
class ModelProfile:
    profile: str
    provider: str
    model: str
    base_url: str = ""
    api_key: str = ""
    api_mode: str = ""
    source: str = ""

    @property
    def configured(self) -> bool:
        return bool(self.provider and self.model)

    @property
    def label(self) -> str:
        return _PROFILE_LABELS.get(self.profile, self.profile)

    def as_dict(self) -> dict[str, str]:
        return {
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "api_mode": self.api_mode,
        }

    def short_target(self) -> str:
        provider = self.provider or "unknown"
        model = self.model or "unknown"
        return f"{provider}/{model}"


def normalize_profile_name(name: str) -> str:
    return (name or "").strip().lower().replace("_", "-")


def profile_title(name: str) -> str:
    normalized = normalize_profile_name(name)
    return _PROFILE_LABELS.get(normalized, normalized or "model")


def _stringify(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _extract_profile_entry(entry: Any) -> tuple[str, str, str, str, str]:
    provider = ""
    model = ""
    base_url = ""
    api_key = ""
    api_mode = ""
    if isinstance(entry, dict):
        provider = _stringify(entry.get("provider"))
        model = _stringify(entry.get("model") or entry.get("default_model"))
        base_url = _stringify(entry.get("base_url") or entry.get("url"))
        api_key = _stringify(entry.get("api_key"))
        api_mode = _stringify(entry.get("api_mode") or entry.get("transport"))
    elif isinstance(entry, str):
        model = entry.strip()
    return provider, model, base_url, api_key, api_mode


def load_model_profile(config: Optional[dict[str, Any]], profile: str) -> Optional[ModelProfile]:
    """Resolve a named routing profile from Hermes config.

    The main profile falls back to the legacy root model settings so existing
    installs keep working even before they migrate to the explicit slot.
    The escalate profile is only returned when it is explicitly configured.
    """

    normalized = normalize_profile_name(profile)
    if normalized not in {"main", "escalate"}:
        return None

    model_cfg: dict[str, Any] = {}
    if isinstance(config, dict):
        maybe_model = config.get("model", {})
        if isinstance(maybe_model, dict):
            model_cfg = maybe_model

    slot = model_cfg.get(normalized)
    provider, model, base_url, api_key, api_mode = _extract_profile_entry(slot)
    source = f"model.{normalized}"

    if normalized == "main" and not (provider and model):
        provider = _stringify(model_cfg.get("provider"))
        model = _stringify(model_cfg.get("default"))
        base_url = _stringify(model_cfg.get("base_url"))
        api_key = _stringify(model_cfg.get("api_key"))
        api_mode = _stringify(model_cfg.get("api_mode"))
        source = "model.default/provider"

    if not (provider and model):
        return None

    return ModelProfile(
        profile=normalized,
        provider=provider,
        model=model,
        base_url=base_url,
        api_key=api_key,
        api_mode=api_mode,
        source=source,
    )


def current_runtime_profile(
    provider: Optional[str],
    model: Optional[str],
    base_url: Optional[str] = "",
    api_key: Optional[str] = "",
    api_mode: Optional[str] = "",
    profile: str = "main",
) -> ModelProfile:
    return ModelProfile(
        profile=normalize_profile_name(profile) or "main",
        provider=_stringify(provider),
        model=_stringify(model),
        base_url=_stringify(base_url),
        api_key=_stringify(api_key),
        api_mode=_stringify(api_mode),
        source="runtime",
    )


def profile_missing_message(profile: str) -> str:
    normalized = normalize_profile_name(profile)
    if normalized == "escalate":
        return (
            "The senior/escalate profile is not configured yet. "
            "Set it with `/model escalate <provider/model>` first."
        )
    if normalized == "main":
        return (
            "The main profile is not configured yet. Set it with `/model main <provider/model>`."
        )
    return f"The {normalized or 'model'} profile is not configured yet."


def detect_openrouter_free_model(model: str) -> bool:
    value = (model or "").strip().lower()
    return bool(value) and (
        value.endswith(":free")
        or value.endswith("/free")
        or ":free" in value
        or "/free" in value
    )
