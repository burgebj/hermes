"""Optional Burn/Rust tool-router plugin for Hermes Agent.

This plugin shells out to a local ``hermes-burn-tool-router`` binary during the
``pre_llm_call`` hook and logs an advisory route prediction. It is intentionally
observe-first: enabling the plugin never changes the live tool surface or blocks
a turn. Missing binaries, slow sidecars, malformed JSON, and all other failures
fall back silently to normal Hermes behavior.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from dataclasses import dataclass, field
from typing import Any, Mapping

logger = logging.getLogger(__name__)

CATEGORY_TOOLSETS: dict[str, list[str]] = {
    "terminal": ["terminal", "code_execution"],
    "file": ["file"],
    "web": ["web"],
    "x_search": ["x_search"],
    "browser": ["browser"],
    "memory": ["memory", "session_search"],
    "skills": ["skills"],
    "delegation": ["delegation"],
    "media_generation": ["image_gen", "video_gen", "tts"],
    "media_analysis": ["vision", "video"],
    "messaging": ["messaging"],
    "cron": ["cronjob"],
    "hermes_cli": [],
    "todo": ["todo"],
    "smart_home": ["homeassistant"],
    "kanban": ["kanban"],
    "social_platforms": ["discord", "discord_admin", "yuanbao"],
    "productivity": ["feishu_doc", "feishu_drive", "spotify"],
    "computer_use": ["computer_use"],
}


@dataclass(frozen=True)
class BurnRouterConfig:
    """Runtime config for the optional Burn router sidecar."""

    enabled: bool = True
    mode: str = "observe"  # observe | hint | narrow
    binary: str | None = None
    model: str | None = None
    confidence_threshold: float = 0.72
    timeout_seconds: float = 0.25

    @classmethod
    def from_mapping(cls, config: Mapping[str, Any] | None) -> "BurnRouterConfig":
        """Build config from a plugin entry mapping plus env overrides."""

        cfg = config if isinstance(config, Mapping) else {}

        def env_bool(name: str, default: bool) -> bool:
            raw = os.getenv(name)
            if raw is None:
                return default
            return raw.strip().lower() in {"1", "true", "yes", "on"}

        def env_float(name: str, default: Any) -> float:
            raw = os.getenv(name)
            value = raw if raw is not None else default
            try:
                return float(value)
            except (TypeError, ValueError):
                return float(cls.__dataclass_fields__[  # type: ignore[attr-defined]
                    "confidence_threshold" if "CONFIDENCE" in name else "timeout_seconds"
                ].default)

        return cls(
            enabled=env_bool("HERMES_BURN_ROUTER_ENABLED", bool(cfg.get("enabled", True))),
            mode=str(os.getenv("HERMES_BURN_ROUTER_MODE", cfg.get("mode", "observe"))).lower(),
            binary=os.getenv("HERMES_BURN_ROUTER_BINARY", cfg.get("binary") or None),
            model=os.getenv("HERMES_BURN_ROUTER_MODEL", cfg.get("model") or None),
            confidence_threshold=env_float(
                "HERMES_BURN_ROUTER_CONFIDENCE",
                cfg.get("confidence_threshold", 0.72),
            ),
            timeout_seconds=env_float(
                "HERMES_BURN_ROUTER_TIMEOUT",
                cfg.get("timeout_seconds", 0.25),
            ),
        )

    @classmethod
    def load(cls) -> "BurnRouterConfig":
        """Load plugin config from Hermes config.yaml.

        Preferred location::

            plugins:
              enabled: [burn_router]
              entries:
                burn_router:
                  binary: /path/to/hermes-burn-tool-router
                  model: /path/to/router-model

        Env vars with the ``HERMES_BURN_ROUTER_*`` prefix override config.
        """

        try:
            from hermes_cli.config import cfg_get, load_config

            config = load_config() or {}
            plugin_cfg = cfg_get(config, "plugins", "entries", "burn_router", default={})
            if not isinstance(plugin_cfg, Mapping):
                plugin_cfg = {}
            return cls.from_mapping(plugin_cfg)
        except Exception as exc:  # pragma: no cover - defensive config path
            logger.debug("Burn router config load failed: %s", exc)
            return cls.from_mapping({})


@dataclass(frozen=True)
class BurnRouterResult:
    """Advisory route prediction returned by the Burn router."""

    category: str
    confidence: float
    time_us: float | None = None
    probabilities: dict[str, float] = field(default_factory=dict)
    enabled_toolsets: list[str] = field(default_factory=list)
    mode: str = "observe"
    raw: dict[str, Any] = field(default_factory=dict)

    def to_log_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "confidence": self.confidence,
            "time_us": self.time_us,
            "enabled_toolsets": self.enabled_toolsets,
            "mode": self.mode,
        }


def _mode_for_prediction(cfg: BurnRouterConfig, confidence: float) -> str:
    if cfg.mode == "observe":
        return "observe"
    if confidence >= cfg.confidence_threshold:
        return cfg.mode if cfg.mode in {"hint", "narrow"} else "hint"
    return "fallback_full_surface"


def get_burn_router_hint(message: str, config: BurnRouterConfig | Mapping[str, Any] | None = None) -> BurnRouterResult | None:
    """Return an advisory Burn router prediction, or ``None`` on disabled/failure."""

    cfg = config if isinstance(config, BurnRouterConfig) else BurnRouterConfig.from_mapping(config)
    if not cfg.enabled:
        return None
    if not cfg.binary or not cfg.model:
        logger.debug("Burn router plugin enabled but binary/model missing; skipping")
        return None

    try:
        completed = subprocess.run(
            [cfg.binary, "predict", message, cfg.model],
            check=False,
            capture_output=True,
            text=True,
            timeout=cfg.timeout_seconds,
        )
    except Exception as exc:
        logger.debug("Burn router invocation failed: %s", exc)
        return None

    if completed.returncode != 0:
        logger.debug("Burn router exited %s: %s", completed.returncode, completed.stderr.strip())
        return None

    try:
        payload = json.loads(completed.stdout)
        category = str(payload["category"])
        confidence = float(payload["confidence"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        logger.debug("Burn router returned malformed JSON: %s", exc)
        return None

    mode = _mode_for_prediction(cfg, confidence)
    enabled_toolsets = CATEGORY_TOOLSETS.get(category, []) if mode in {"hint", "narrow"} else []
    return BurnRouterResult(
        category=category,
        confidence=confidence,
        time_us=float(payload["time_us"]) if payload.get("time_us") is not None else None,
        probabilities=dict(payload.get("all") or {}),
        enabled_toolsets=list(enabled_toolsets),
        mode=mode,
        raw=payload,
    )


def observe_burn_router_turn(message: str, config: BurnRouterConfig | Mapping[str, Any] | None = None) -> BurnRouterResult | None:
    """Run the router once for telemetry and log the result."""

    result = get_burn_router_hint(message, config)
    if result is None:
        return None
    logger.info("burn_router prediction: %s", result.to_log_dict())
    return result


def _on_pre_llm_call(*, user_message: str = "", **_: Any) -> None:
    """Plugin hook: observe the next user turn before the model call.

    Return value intentionally stays ``None`` so the hook never injects prompt
    context or changes tool access. The current plugin surface is telemetry-only.
    """

    observe_burn_router_turn(user_message or "", BurnRouterConfig.load())
    return None


def register(ctx) -> None:
    """Register the observe-only pre-LLM hook."""

    ctx.register_hook("pre_llm_call", _on_pre_llm_call)
