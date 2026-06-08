"""Unit tests for gateway.reactions (issue #27438).

These are pure-Python tests: no SQLite, no platform adapters.  They pin
the public API of :mod:`gateway.reactions` so refactors of the storage
or wiring layers don't accidentally change emoji-signal semantics.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from gateway.reactions import (
    DEFAULT_REACTION_WEIGHTS,
    NEUTRAL_UNKNOWN_WEIGHT,
    ReactionConfig,
    ReactionEvent,
    ReactionPolarity,
    ReactionSignal,
    build_reaction_event,
    resolve_emoji_signal,
)


# ---------------------------------------------------------------------------
# DEFAULT_REACTION_WEIGHTS table
# ---------------------------------------------------------------------------


class TestDefaultReactionWeights:
    """Pin the canonical emoji table from the issue."""

    def test_heart_is_positive_two(self):
        assert "\u2764\ufe0f" in DEFAULT_REACTION_WEIGHTS
        sig = DEFAULT_REACTION_WEIGHTS["\u2764\ufe0f"]
        assert sig.weight == 2.0
        assert sig.polarity is ReactionPolarity.POSITIVE
        assert sig.label == "heart"

    def test_thumbs_up_is_positive_one(self):
        sig = DEFAULT_REACTION_WEIGHTS["\U0001F44D"]
        assert sig.weight == 1.0
        assert sig.polarity is ReactionPolarity.POSITIVE
        assert sig.label == "thumbs_up"

    def test_thumbs_down_is_negative_one(self):
        sig = DEFAULT_REACTION_WEIGHTS["\U0001F44E"]
        assert sig.weight == 1.0
        assert sig.polarity is ReactionPolarity.NEGATIVE
        assert sig.signed_weight() == -1.0

    def test_poo_is_strongly_negative(self):
        sig = DEFAULT_REACTION_WEIGHTS["\U0001F4A9"]
        assert sig.weight == 2.0
        assert sig.polarity is ReactionPolarity.NEGATIVE
        assert sig.signed_weight() == -2.0

    def test_laugh_is_positive_zero_point_eight(self):
        sig = DEFAULT_REACTION_WEIGHTS["\U0001F602"]
        assert sig.signed_weight() == pytest.approx(0.8)

    def test_cry_is_negative_one_point_five(self):
        sig = DEFAULT_REACTION_WEIGHTS["\U0001F622"]
        assert sig.signed_weight() == pytest.approx(-1.5)

    def test_angry_is_negative_two(self):
        sig = DEFAULT_REACTION_WEIGHTS["\U0001F621"]
        assert sig.signed_weight() == -2.0

    def test_raised_hands_is_positive_one(self):
        sig = DEFAULT_REACTION_WEIGHTS["\U0001F64C"]
        assert sig.signed_weight() == 1.0

    def test_table_only_holds_documented_emoji(self):
        # If somebody adds an emoji here without updating the issue
        # table, the test will catch it.  The bare '\u2764' alias is
        # an intentional client-normalisation shim.
        expected = {
            "\u2764\ufe0f", "\u2764",
            "\U0001F44D", "\U0001F602", "\U0001F64C",
            "\U0001F44E", "\U0001F4A9", "\U0001F622", "\U0001F621",
        }
        assert set(DEFAULT_REACTION_WEIGHTS.keys()) == expected


# ---------------------------------------------------------------------------
# resolve_emoji_signal
# ---------------------------------------------------------------------------


class TestResolveEmojiSignal:
    def test_known_emoji_returns_default_signal(self):
        sig = resolve_emoji_signal("\U0001F44D")
        assert sig is not None
        assert sig.label == "thumbs_up"

    def test_unknown_emoji_returns_none_by_default(self):
        assert resolve_emoji_signal("\U0001F914") is None  # 🤔

    def test_unknown_emoji_with_include_unknown_is_neutral(self):
        sig = resolve_emoji_signal("\U0001F914", include_unknown=True)
        assert sig is not None
        assert sig.polarity is ReactionPolarity.NEUTRAL
        assert sig.weight == NEUTRAL_UNKNOWN_WEIGHT
        assert sig.signed_weight() == 0.0
        assert sig.label == "unknown"

    def test_variation_selector_normalisation(self):
        # ❤️ (U+2764 U+FE0F) and ❤ (U+2764) both resolve to "heart".
        with_vs = resolve_emoji_signal("\u2764\ufe0f")
        without_vs = resolve_emoji_signal("\u2764")
        assert with_vs is not None and without_vs is not None
        assert with_vs.label == without_vs.label == "heart"

    def test_empty_string_returns_none(self):
        assert resolve_emoji_signal("") is None

    def test_custom_weights_override(self):
        custom = {
            "\U0001F44D": ReactionSignal(
                "\U0001F44D", 5.0, ReactionPolarity.POSITIVE, "thumbs_up_boosted"
            )
        }
        sig = resolve_emoji_signal("\U0001F44D", weights=custom)
        assert sig is not None
        assert sig.label == "thumbs_up_boosted"
        assert sig.signed_weight() == 5.0

    def test_custom_weights_table_falls_through_to_unknown(self):
        custom = {
            "\U0001F44D": ReactionSignal(
                "\U0001F44D", 5.0, ReactionPolarity.POSITIVE, "thumbs_up"
            )
        }
        # Heart isn't in the custom table, so without include_unknown -> None.
        assert resolve_emoji_signal("\u2764\ufe0f", weights=custom) is None


# ---------------------------------------------------------------------------
# ReactionSignal.signed_weight semantics
# ---------------------------------------------------------------------------


class TestSignedWeight:
    def test_negative_polarity_inverts_weight(self):
        sig = ReactionSignal("x", 3.0, ReactionPolarity.NEGATIVE, "x")
        assert sig.signed_weight() == -3.0

    def test_negative_polarity_with_already_negative_weight_still_negative(self):
        # signed_weight() must use magnitude so callers can't double-sign.
        sig = ReactionSignal("x", -3.0, ReactionPolarity.NEGATIVE, "x")
        assert sig.signed_weight() == -3.0

    def test_neutral_polarity_zeroes_out(self):
        sig = ReactionSignal("x", 99.0, ReactionPolarity.NEUTRAL, "x")
        assert sig.signed_weight() == 0.0

    def test_positive_polarity_with_negative_weight_recovers_magnitude(self):
        sig = ReactionSignal("x", -3.0, ReactionPolarity.POSITIVE, "x")
        assert sig.signed_weight() == 3.0


# ---------------------------------------------------------------------------
# ReactionConfig
# ---------------------------------------------------------------------------


class TestReactionConfigFromEnv:
    def test_defaults_are_opt_out(self, monkeypatch):
        for var in (
            "HERMES_REACTION_SIGNALS_ENABLED",
            "HERMES_REACTION_MIN_SIGNAL",
            "HERMES_REACTION_DECAY_DAYS",
            "HERMES_REACTION_INCLUDE_UNKNOWN",
        ):
            monkeypatch.delenv(var, raising=False)
        cfg = ReactionConfig.from_env()
        assert cfg.enabled is False
        assert cfg.min_signal_threshold == 0.5
        assert cfg.decay_days == 30
        assert cfg.include_unknown is False
        # Default weight table is copied, not shared, so mutating cfg
        # doesn't leak into the module-level default.
        cfg.weights.clear()
        assert DEFAULT_REACTION_WEIGHTS  # untouched

    def test_enabled_true_via_env(self, monkeypatch):
        monkeypatch.setenv("HERMES_REACTION_SIGNALS_ENABLED", "true")
        assert ReactionConfig.from_env().enabled is True

    @pytest.mark.parametrize("raw", ["1", "True", "YES", "on", "  yes  "])
    def test_enabled_accepts_common_truthy_values(self, monkeypatch, raw):
        monkeypatch.setenv("HERMES_REACTION_SIGNALS_ENABLED", raw)
        assert ReactionConfig.from_env().enabled is True

    @pytest.mark.parametrize("raw", ["0", "false", "no", "off", ""])
    def test_enabled_rejects_non_truthy(self, monkeypatch, raw):
        monkeypatch.setenv("HERMES_REACTION_SIGNALS_ENABLED", raw)
        assert ReactionConfig.from_env().enabled is False

    def test_min_signal_threshold_parsed_as_float(self, monkeypatch):
        monkeypatch.setenv("HERMES_REACTION_MIN_SIGNAL", "1.25")
        assert ReactionConfig.from_env().min_signal_threshold == 1.25

    def test_min_signal_threshold_invalid_falls_back_to_default(self, monkeypatch):
        monkeypatch.setenv("HERMES_REACTION_MIN_SIGNAL", "not-a-number")
        assert ReactionConfig.from_env().min_signal_threshold == 0.5

    def test_decay_days_parsed_as_int(self, monkeypatch):
        monkeypatch.setenv("HERMES_REACTION_DECAY_DAYS", "7")
        assert ReactionConfig.from_env().decay_days == 7

    def test_decay_days_invalid_falls_back_to_default(self, monkeypatch):
        monkeypatch.setenv("HERMES_REACTION_DECAY_DAYS", "??")
        assert ReactionConfig.from_env().decay_days == 30

    def test_include_unknown_toggle(self, monkeypatch):
        monkeypatch.setenv("HERMES_REACTION_INCLUDE_UNKNOWN", "yes")
        assert ReactionConfig.from_env().include_unknown is True

    def test_overrides_merge_on_top_of_defaults(self, monkeypatch):
        for var in ("HERMES_REACTION_SIGNALS_ENABLED",):
            monkeypatch.delenv(var, raising=False)
        custom = {
            "\U0001F44D": ReactionSignal(
                "\U0001F44D", 10.0, ReactionPolarity.POSITIVE, "thumbs_up_boosted"
            )
        }
        cfg = ReactionConfig.from_env(overrides=custom)
        sig = cfg.resolve("\U0001F44D")
        assert sig is not None
        assert sig.signed_weight() == 10.0
        # Heart still resolves from defaults.
        assert cfg.resolve("\u2764\ufe0f") is not None

    def test_resolve_honours_include_unknown(self, monkeypatch):
        monkeypatch.setenv("HERMES_REACTION_INCLUDE_UNKNOWN", "true")
        cfg = ReactionConfig.from_env()
        sig = cfg.resolve("\U0001F914")  # 🤔 not in table
        assert sig is not None
        assert sig.polarity is ReactionPolarity.NEUTRAL


# ---------------------------------------------------------------------------
# ReactionEvent dataclass
# ---------------------------------------------------------------------------


class TestReactionEventProperties:
    def _event(self, sig: ReactionSignal, added: bool = True) -> ReactionEvent:
        return ReactionEvent(
            platform="telegram",
            channel_id="42",
            actor_user_id="user-1",
            target_message_id="m-1",
            emoji=sig.emoji,
            signal=sig,
            added=added,
        )

    def test_weight_uses_signed_value(self):
        sig = DEFAULT_REACTION_WEIGHTS["\U0001F44E"]  # thumbs_down
        e = self._event(sig)
        assert e.weight == -1.0
        assert e.polarity is ReactionPolarity.NEGATIVE

    def test_default_timestamp_is_utc(self):
        sig = DEFAULT_REACTION_WEIGHTS["\u2764\ufe0f"]
        e = self._event(sig)
        assert e.timestamp.tzinfo == timezone.utc

    def test_platform_data_defaults_to_empty_dict(self):
        sig = DEFAULT_REACTION_WEIGHTS["\u2764\ufe0f"]
        e = self._event(sig)
        assert e.platform_data == {}

    def test_added_false_marks_removal(self):
        sig = DEFAULT_REACTION_WEIGHTS["\u2764\ufe0f"]
        e = self._event(sig, added=False)
        assert e.added is False
        # weight unchanged -- ReactionStore subtracts it explicitly.
        assert e.weight == 2.0


# ---------------------------------------------------------------------------
# build_reaction_event
# ---------------------------------------------------------------------------


class TestBuildReactionEvent:
    def _config(self, monkeypatch, *, enabled=True, include_unknown=False):
        monkeypatch.setenv(
            "HERMES_REACTION_SIGNALS_ENABLED", "true" if enabled else "false"
        )
        monkeypatch.setenv(
            "HERMES_REACTION_INCLUDE_UNKNOWN", "true" if include_unknown else "false"
        )
        return ReactionConfig.from_env()

    def test_returns_event_for_known_emoji(self, monkeypatch):
        cfg = self._config(monkeypatch)
        e = build_reaction_event(
            platform="telegram",
            channel_id=42,
            actor_user_id=100,
            target_message_id=7,
            emoji="\U0001F44D",
            config=cfg,
        )
        assert e is not None
        assert e.platform == "telegram"
        # Numeric inputs are stringified at the boundary so storage stays
        # uniform across adapters that emit ints (Telegram) vs strings (Slack).
        assert e.channel_id == "42"
        assert e.actor_user_id == "100"
        assert e.target_message_id == "7"

    def test_returns_none_for_unknown_emoji_by_default(self, monkeypatch):
        cfg = self._config(monkeypatch)
        e = build_reaction_event(
            platform="telegram",
            channel_id=1,
            actor_user_id=1,
            target_message_id=1,
            emoji="\U0001F914",  # 🤔
            config=cfg,
        )
        assert e is None

    def test_returns_neutral_event_when_include_unknown_enabled(self, monkeypatch):
        cfg = self._config(monkeypatch, include_unknown=True)
        e = build_reaction_event(
            platform="telegram",
            channel_id=1,
            actor_user_id=1,
            target_message_id=1,
            emoji="\U0001F914",
            config=cfg,
        )
        assert e is not None
        assert e.signal.polarity is ReactionPolarity.NEUTRAL
        assert e.weight == 0.0

    def test_added_false_is_propagated(self, monkeypatch):
        cfg = self._config(monkeypatch)
        e = build_reaction_event(
            platform="telegram",
            channel_id=1,
            actor_user_id=1,
            target_message_id=1,
            emoji="\u2764\ufe0f",
            added=False,
            config=cfg,
        )
        assert e is not None
        assert e.added is False

    def test_custom_timestamp_preserved(self, monkeypatch):
        cfg = self._config(monkeypatch)
        ts = datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc)
        e = build_reaction_event(
            platform="telegram",
            channel_id=1,
            actor_user_id=1,
            target_message_id=1,
            emoji="\u2764\ufe0f",
            timestamp=ts,
            config=cfg,
        )
        assert e is not None
        assert e.timestamp == ts

    def test_platform_data_is_carried_through(self, monkeypatch):
        cfg = self._config(monkeypatch)
        e = build_reaction_event(
            platform="telegram",
            channel_id=1,
            actor_user_id=1,
            target_message_id=1,
            emoji="\U0001F44D",
            platform_data={"chat_type": "group"},
            config=cfg,
        )
        assert e is not None
        assert e.platform_data == {"chat_type": "group"}

    def test_falls_back_to_env_when_config_omitted(self, monkeypatch):
        # If no config arg is passed, build_reaction_event reads env.
        # Even with the master flag *disabled*, build_reaction_event itself
        # must still produce an event for known emoji -- the master flag is
        # an enforcement point on the adapter / handle_reaction path, not
        # on the pure builder.  This keeps the builder usable from tests
        # and tools that just want the signal.
        for var in (
            "HERMES_REACTION_SIGNALS_ENABLED",
            "HERMES_REACTION_INCLUDE_UNKNOWN",
        ):
            monkeypatch.delenv(var, raising=False)
        e = build_reaction_event(
            platform="telegram",
            channel_id=1,
            actor_user_id=1,
            target_message_id=1,
            emoji="\U0001F44D",
        )
        assert e is not None
        assert e.weight == 1.0
