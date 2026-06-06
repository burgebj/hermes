"""Tests for display.reasoning_format config option (#25574).

Validates that reasoning_format=code|quote|none controls how reasoning
content is rendered in gateway responses.
"""

import pytest

from gateway.display_config import (
    _GLOBAL_DEFAULTS,
    _normalise,
    resolve_display_setting,
)


class TestReasoningFormatDefaults:
    """Default value is 'code' (backward-compatible)."""

    def test_global_default_is_code(self):
        assert _GLOBAL_DEFAULTS["reasoning_format"] == "code"

    def test_resolve_default_returns_code(self):
        """No config set anywhere → returns 'code' from global defaults."""
        result = resolve_display_setting(
            {},  # user_config
            "telegram",  # platform_key
            "reasoning_format",
            "code",
        )
        assert result == "code"


class TestReasoningFormatNormalise:
    """_normalise() validation of reasoning_format values."""

    def test_code_is_accepted(self):
        assert _normalise("reasoning_format", "code") == "code"

    def test_quote_is_accepted(self):
        assert _normalise("reasoning_format", "quote") == "quote"

    def test_none_is_accepted(self):
        assert _normalise("reasoning_format", "none") == "none"

    def test_case_insensitive(self):
        assert _normalise("reasoning_format", "CODE") == "code"
        assert _normalise("reasoning_format", "Quote") == "quote"
        assert _normalise("reasoning_format", "NONE") == "none"

    def test_invalid_value_falls_back_to_code(self):
        assert _normalise("reasoning_format", "invalid") == "code"
        assert _normalise("reasoning_format", "markdown") == "code"
        assert _normalise("reasoning_format", "") == "code"

    def test_boolean_falls_back_to_code(self):
        assert _normalise("reasoning_format", True) == "code"
        assert _normalise("reasoning_format", False) == "code"


class TestReasoningFormatPerPlatform:
    """Per-platform overrides work for reasoning_format."""

    def test_platform_override_wins_over_global(self):
        """display.platforms.telegram.reasoning_format overrides display.reasoning_format."""
        config = {
            "display": {
                "reasoning_format": "code",
                "platforms": {
                    "telegram": {"reasoning_format": "quote"},
                },
            },
        }
        result = resolve_display_setting(config, "telegram", "reasoning_format", "code")
        assert result == "quote"

    def test_global_setting_works(self):
        """display.reasoning_format is read when no per-platform override."""
        config = {
            "display": {
                "reasoning_format": "quote",
            },
        }
        result = resolve_display_setting(config, "telegram", "reasoning_format", "code")
        assert result == "quote"

    def test_invalid_platform_value_falls_back(self):
        """Invalid value in per-platform override falls back to code."""
        config = {
            "display": {
                "platforms": {
                    "telegram": {"reasoning_format": "invalid_option"},
                },
            },
        }
        result = resolve_display_setting(config, "telegram", "reasoning_format", "code")
        assert result == "code"


class TestReasoningFormatInConfig:
    """Integration-style: reasoning_format key is present in defaults dicts."""

    def test_key_in_global_defaults(self):
        assert "reasoning_format" in _GLOBAL_DEFAULTS

    def test_key_in_overrideable_keys(self):
        from gateway.display_config import OVERRIDEABLE_KEYS
        assert "reasoning_format" in OVERRIDEABLE_KEYS
