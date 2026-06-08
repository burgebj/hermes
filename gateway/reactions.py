"""Emoji-reaction reinforcement signals (issue #27438).

When users react to a Hermes message with 👍 / ❤️ / 👎 / 💩 / … on Telegram,
Discord, Slack, etc., those reactions are rich, low-friction feedback that
historically just disappeared.  This module is the foundation for using them
as a lightweight, in-process reinforcement signal:

* Each emoji maps to a :class:`ReactionSignal` with a polarity and weight.
* :class:`ReactionEvent` is the normalised event a platform adapter builds
  when an incoming reaction arrives.
* :class:`ReactionConfig` loads runtime config (enabled flag, weight
  overrides, minimum signal threshold, decay window) from env vars and
  ``config.yaml``.

The actual *consumers* of the signal (memory weighting, skill confidence
scoring, response-style tuning, preference extraction) are deliberately out
of scope here -- they will land in follow-up PRs and read events from the
:mod:`gateway.reaction_store`.  This module is pure, import-safe and has no
side effects.

See: https://github.com/NousResearch/hermes-agent/issues/27438
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Polarity + default weights
# ---------------------------------------------------------------------------


class ReactionPolarity(str, Enum):
    """Sign of a reaction signal.  Strings so they round-trip through SQLite."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class ReactionSignal:
    """Resolved meaning of a single emoji reaction."""

    emoji: str
    weight: float
    polarity: ReactionPolarity
    label: str

    def signed_weight(self) -> float:
        """Weight with the polarity sign applied.

        Built-in weights are stored as their natural sign in
        :data:`DEFAULT_REACTION_WEIGHTS`, but user overrides only need to
        specify a magnitude when the emoji is in the table -- this helper
        is the single source of truth for the final signed value.
        """
        if self.polarity is ReactionPolarity.NEGATIVE:
            return -abs(self.weight)
        if self.polarity is ReactionPolarity.NEUTRAL:
            return 0.0
        return abs(self.weight)


# Default emoji -> (weight, polarity, label).  Lifted straight from the
# table in #27438.  All weights stored as magnitudes -- sign comes from
# polarity via :meth:`ReactionSignal.signed_weight`.
DEFAULT_REACTION_WEIGHTS: Dict[str, ReactionSignal] = {
    "\u2764\ufe0f": ReactionSignal("\u2764\ufe0f", 2.0, ReactionPolarity.POSITIVE, "heart"),
    "\u2764": ReactionSignal("\u2764", 2.0, ReactionPolarity.POSITIVE, "heart"),
    "\U0001F44D": ReactionSignal("\U0001F44D", 1.0, ReactionPolarity.POSITIVE, "thumbs_up"),
    "\U0001F602": ReactionSignal("\U0001F602", 0.8, ReactionPolarity.POSITIVE, "laugh"),
    "\U0001F64C": ReactionSignal("\U0001F64C", 1.0, ReactionPolarity.POSITIVE, "raised_hands"),
    "\U0001F44E": ReactionSignal("\U0001F44E", 1.0, ReactionPolarity.NEGATIVE, "thumbs_down"),
    "\U0001F4A9": ReactionSignal("\U0001F4A9", 2.0, ReactionPolarity.NEGATIVE, "poo"),
    "\U0001F622": ReactionSignal("\U0001F622", 1.5, ReactionPolarity.NEGATIVE, "cry"),
    "\U0001F621": ReactionSignal("\U0001F621", 2.0, ReactionPolarity.NEGATIVE, "angry"),
}


# Reactions outside the default table get this when ``include_unknown=True``
# is configured -- we treat them as observed-but-undecided so we can still
# track engagement without polluting the signal.
NEUTRAL_UNKNOWN_WEIGHT = 0.0


# ---------------------------------------------------------------------------
# Emoji normalisation
# ---------------------------------------------------------------------------


def _strip_variation_selector(emoji: str) -> str:
    """Drop the trailing VS16 selector (``U+FE0F``).

    Telegram, Slack and Discord normalise emoji inconsistently: a heart can
    arrive as ``\u2764`` or ``\u2764\ufe0f`` depending on the client.  We
    look up both forms before falling back to "unknown emoji".
    """
    if emoji.endswith("\ufe0f"):
        return emoji[:-1]
    return emoji


def resolve_emoji_signal(
    emoji: str,
    weights: Optional[Dict[str, ReactionSignal]] = None,
    include_unknown: bool = False,
) -> Optional[ReactionSignal]:
    """Return the :class:`ReactionSignal` for ``emoji`` or ``None``.

    Lookup order: exact match -> stripped-VS16 match -> ``None``.  When
    ``include_unknown`` is true, unrecognised emoji return a polarity-neutral
    signal with :data:`NEUTRAL_UNKNOWN_WEIGHT` so the caller can still
    *record* the engagement without acting on the signal.
    """
    if not emoji:
        return None
    table = weights if weights is not None else DEFAULT_REACTION_WEIGHTS
    if emoji in table:
        return table[emoji]
    stripped = _strip_variation_selector(emoji)
    if stripped and stripped != emoji and stripped in table:
        return table[stripped]
    if include_unknown:
        return ReactionSignal(emoji, NEUTRAL_UNKNOWN_WEIGHT, ReactionPolarity.NEUTRAL, "unknown")
    return None


# ---------------------------------------------------------------------------
# ReactionEvent: the platform-normalised payload
# ---------------------------------------------------------------------------


@dataclass
class ReactionEvent:
    """A single reaction observation from a messaging platform.

    Built by platform adapters in their reaction handlers and dispatched to
    :meth:`gateway.platforms.base.BasePlatformAdapter.handle_reaction`.

    ``target_message_id`` identifies the message being reacted to (NOT the
    reaction itself).  ``actor_user_id`` is the user who tapped the emoji.
    ``platform_data`` is a small free-form dict for adapter-specific extras
    (e.g. Telegram's ``chat.type`` so a downstream consumer can decide
    whether a group reaction should bleed into the DM bias).
    """

    platform: str
    channel_id: str
    actor_user_id: str
    target_message_id: str
    emoji: str
    signal: ReactionSignal
    added: bool = True  # False when the user removed a reaction
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    platform_data: Dict[str, Any] = field(default_factory=dict)

    @property
    def weight(self) -> float:
        """Signed magnitude of this event's signal."""
        return self.signal.signed_weight()

    @property
    def polarity(self) -> ReactionPolarity:
        return self.signal.polarity


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except (TypeError, ValueError):
        logger.warning("Invalid float for %s=%r; using default %s", name, raw, default)
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        logger.warning("Invalid int for %s=%r; using default %s", name, raw, default)
        return default


@dataclass
class ReactionConfig:
    """Runtime config for emoji-reaction reinforcement.

    Loaded from env vars (highest precedence) and ``config.yaml``'s
    ``reaction_signals:`` block in :func:`from_env`.  Defaults preserve
    today's behaviour (no-op) so this feature is strictly opt-in.
    """

    enabled: bool = False
    min_signal_threshold: float = 0.5
    decay_days: int = 30
    include_unknown: bool = False
    weights: Dict[str, ReactionSignal] = field(default_factory=lambda: dict(DEFAULT_REACTION_WEIGHTS))

    @classmethod
    def from_env(
        cls,
        overrides: Optional[Dict[str, ReactionSignal]] = None,
    ) -> "ReactionConfig":
        """Build a :class:`ReactionConfig` from env vars + optional overrides."""
        weights = dict(DEFAULT_REACTION_WEIGHTS)
        if overrides:
            weights.update(overrides)
        return cls(
            enabled=_env_bool("HERMES_REACTION_SIGNALS_ENABLED", False),
            min_signal_threshold=_env_float("HERMES_REACTION_MIN_SIGNAL", 0.5),
            decay_days=_env_int("HERMES_REACTION_DECAY_DAYS", 30),
            include_unknown=_env_bool("HERMES_REACTION_INCLUDE_UNKNOWN", False),
            weights=weights,
        )

    def resolve(self, emoji: str) -> Optional[ReactionSignal]:
        """Convenience: resolve an emoji using this config's weights table."""
        return resolve_emoji_signal(emoji, self.weights, include_unknown=self.include_unknown)


# ---------------------------------------------------------------------------
# Convenience builder so adapters don't have to know polarity rules
# ---------------------------------------------------------------------------


def build_reaction_event(
    *,
    platform: str,
    channel_id: str,
    actor_user_id: str,
    target_message_id: str,
    emoji: str,
    added: bool = True,
    timestamp: Optional[datetime] = None,
    platform_data: Optional[Dict[str, Any]] = None,
    config: Optional[ReactionConfig] = None,
) -> Optional[ReactionEvent]:
    """Build a :class:`ReactionEvent` after resolving the emoji.

    Returns ``None`` when the emoji is unknown and ``config.include_unknown``
    is false -- saves the adapter from having to mirror that policy.
    """
    cfg = config or ReactionConfig.from_env()
    signal = cfg.resolve(emoji)
    if signal is None:
        return None
    return ReactionEvent(
        platform=platform,
        channel_id=str(channel_id),
        actor_user_id=str(actor_user_id),
        target_message_id=str(target_message_id),
        emoji=emoji,
        signal=signal,
        added=added,
        timestamp=timestamp or datetime.now(timezone.utc),
        platform_data=platform_data or {},
    )
