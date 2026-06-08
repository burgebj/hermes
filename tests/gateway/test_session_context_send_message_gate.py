"""Tests for send_message tool gating in build_session_context_prompt.

Regression test for #38101: the session prompt should not promise
messaging capabilities (Home Channels, delivery targets, Yuanbao DM
instructions) when the ``messaging`` toolset is not enabled for the
current platform.
"""

from unittest.mock import patch

from gateway.session import (
    SessionContext,
    SessionSource,
    build_session_context_prompt,
    _send_message_loaded,
)
from gateway.config import Platform, HomeChannel


def _make_context(
    platform=Platform.TELEGRAM,
    chat_id="telegram:99999",
    home_channels=None,
):
    source = SessionSource(
        platform=platform,
        chat_id=chat_id,
        chat_type="dm",
        user_id="user-123",
    )
    return SessionContext(
        source=source,
        connected_platforms=[platform],
        home_channels=home_channels or {},
    )


# ---------------------------------------------------------------------------
# _send_message_loaded helper
# ---------------------------------------------------------------------------

class TestSendMessageLoaded:
    def test_returns_false_on_exception(self):
        """Safe default when config/tools_config is unavailable."""
        with patch("hermes_cli.config.load_config", side_effect=RuntimeError):
            assert _send_message_loaded(Platform.TELEGRAM) is False

    def test_returns_true_when_messaging_toolset_enabled(self):
        with patch("hermes_cli.config.load_config", return_value={}), \
             patch("hermes_cli.tools_config._get_platform_tools",
                    return_value={"messaging", "terminal", "file"}):
            assert _send_message_loaded(Platform.TELEGRAM) is True

    def test_returns_false_when_messaging_toolset_absent(self):
        with patch("hermes_cli.config.load_config", return_value={}), \
             patch("hermes_cli.tools_config._get_platform_tools",
                    return_value={"terminal", "file", "vision", "cronjob"}):
            assert _send_message_loaded(Platform.TELEGRAM) is False


# ---------------------------------------------------------------------------
# Home Channels gating
# ---------------------------------------------------------------------------

class TestHomeChannelsGating:
    HC = {Platform.TELEGRAM: HomeChannel(
        name="General", chat_id="telegram:12345", platform=Platform.TELEGRAM,
    )}

    def test_home_channels_absent_when_send_message_disabled(self):
        ctx = _make_context(home_channels=self.HC)
        with patch("gateway.session._send_message_loaded", return_value=False):
            prompt = build_session_context_prompt(ctx)
        assert "Home Channels" not in prompt
        assert "telegram:12345" not in prompt

    def test_home_channels_present_when_send_message_enabled(self):
        ctx = _make_context(home_channels=self.HC)
        with patch("gateway.session._send_message_loaded", return_value=True):
            prompt = build_session_context_prompt(ctx)
        assert "Home Channels" in prompt
        assert "General" in prompt


# ---------------------------------------------------------------------------
# Delivery options gating
# ---------------------------------------------------------------------------

class TestDeliveryOptionsGating:
    HC = {Platform.TELEGRAM: HomeChannel(
        name="General", chat_id="telegram:12345", platform=Platform.TELEGRAM,
    )}

    def test_platform_delivery_targets_absent_when_disabled(self):
        ctx = _make_context(home_channels=self.HC)
        with patch("gateway.session._send_message_loaded", return_value=False):
            prompt = build_session_context_prompt(ctx)
        # Platform-specific home channel delivery line should be absent
        assert "Home channel" not in prompt
        # Explicit targeting note should be absent
        assert "explicit targeting" not in prompt.lower()

    def test_platform_delivery_targets_present_when_enabled(self):
        ctx = _make_context(home_channels=self.HC)
        with patch("gateway.session._send_message_loaded", return_value=True):
            prompt = build_session_context_prompt(ctx)
        assert "Home channel" in prompt
        assert "explicit targeting" in prompt.lower()


# ---------------------------------------------------------------------------
# Yuanbao platform notes gating
# ---------------------------------------------------------------------------

class TestYuanbaoPlatformNotes:
    def test_yuanbao_disclaimer_when_send_message_disabled(self):
        ctx = _make_context(platform=Platform.YUANBAO, chat_id="yuanbao:123")
        with patch("gateway.session._send_message_loaded", return_value=False):
            prompt = build_session_context_prompt(ctx)
        assert "do NOT have access" in prompt
        assert "send_message" not in prompt

    def test_yuanbao_messaging_instructions_when_enabled(self):
        ctx = _make_context(platform=Platform.YUANBAO, chat_id="yuanbao:123")
        with patch("gateway.session._send_message_loaded", return_value=True):
            prompt = build_session_context_prompt(ctx)
        assert "send_message tool" in prompt
        assert "yuanbao:direct:" in prompt


# ---------------------------------------------------------------------------
# Connected Platforms always shown (informational)
# ---------------------------------------------------------------------------

class TestConnectedPlatformsAlwaysShown:
    def test_connected_platforms_present_regardless(self):
        ctx = _make_context(platform=Platform.TELEGRAM)
        with patch("gateway.session._send_message_loaded", return_value=False):
            prompt = build_session_context_prompt(ctx)
        assert "Connected Platforms" in prompt
        assert "telegram: Connected" in prompt
