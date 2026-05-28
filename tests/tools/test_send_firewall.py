"""Tests for the messaging firewall (tools/send_firewall.py) and its gate
in tools/send_message_tool.py.

The decision-engine tests are pure (they patch ``_load_firewall_config`` so
no config.yaml is touched). The integration tests reuse the established
send_message harness: patch ``gateway.config.load_gateway_config``,
``model_tools._run_async`` (run coroutines immediately), and
``tools.send_message_tool._send_to_platform``.
"""

import asyncio
import json
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

# python-telegram-bot is optional; the integration tests below send to
# telegram via the mocked _send_to_platform, but send_message_tool imports
# happen lazily. Skip the whole module if telegram isn't importable to match
# the sibling test_send_message_tool.py convention.
pytest.importorskip("telegram", reason="python-telegram-bot not installed")

from gateway.config import Platform  # noqa: E402
from tools import send_firewall  # noqa: E402
from tools.send_firewall import (  # noqa: E402
    FirewallDecision,
    evaluate_send_policy,
)
from tools.send_message_tool import send_message_tool  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_session_trusted():
    send_firewall._reset_session_trusted()
    yield
    send_firewall._reset_session_trusted()


def _cfg(**overrides):
    """Build a messaging_firewall config dict (enabled by default)."""
    base = {"enabled": True}
    base.update(overrides)
    return base


def _patch_cfg(cfg):
    return patch("tools.send_firewall._load_firewall_config", return_value=cfg)


def _patch_not_cron():
    return patch("tools.send_firewall._is_cron_session", return_value=False)


# =========================================================================
# Decision engine
# =========================================================================

class TestDecisionEngine:
    def test_disabled_allows_everything(self):
        with _patch_cfg({"enabled": False}):
            d = evaluate_send_policy("telegram", "999", "hi", "telegram:999")
        assert d.allowed is True
        assert d.reason == send_firewall.REASON_DISABLED
        assert d.needs_confirmation is False

    def test_absent_enabled_key_defaults_off(self):
        # No 'enabled' key at all -> firewall off (opt-in by design).
        with _patch_cfg({"self_targets": ["telegram:1"]}):
            d = evaluate_send_policy("telegram", "999", "hi", "telegram:999")
        assert d.allowed is True
        assert d.reason == send_firewall.REASON_DISABLED

    def test_yaml_off_string_treated_as_disabled(self):
        # YAML 1.1 'off' may arrive as the string "off" if quoted.
        with _patch_cfg({"enabled": "off"}):
            d = evaluate_send_policy("telegram", "999", "hi", "telegram:999")
        assert d.allowed is True
        assert d.reason == send_firewall.REASON_DISABLED

    def test_unknown_target_needs_confirmation(self):
        with _patch_cfg(_cfg()), _patch_not_cron():
            d = evaluate_send_policy("telegram", "999", "hi", "telegram:999")
        assert d.allowed is False
        assert d.reason == send_firewall.REASON_PENDING
        assert d.needs_confirmation is True

    def test_home_channel_is_self(self):
        with _patch_cfg(_cfg()), _patch_not_cron():
            d = evaluate_send_policy(
                "telegram", "111", "hi", "telegram", used_home_channel=True
            )
        assert d.allowed is True
        assert d.reason == send_firewall.REASON_SELF

    def test_explicit_self_target(self):
        cfg = _cfg(self_targets=["signal:+15554567"])
        with _patch_cfg(cfg), _patch_not_cron():
            d = evaluate_send_policy("signal", "+15554567", "note", "signal:+15554567")
        assert d.allowed is True
        assert d.reason == send_firewall.REASON_SELF

    def test_trusted_target_exact(self):
        cfg = _cfg(trusted_targets=["telegram:-1001234567890"])
        with _patch_cfg(cfg), _patch_not_cron():
            d = evaluate_send_policy(
                "telegram", "-1001234567890", "hi", "telegram:-1001234567890"
            )
        assert d.allowed is True
        assert d.reason == send_firewall.REASON_TRUSTED

    def test_trusted_target_channel_hash_normalized(self):
        # 'discord:#bot-home' in config should match a 'bot-home' chat_id.
        cfg = _cfg(trusted_targets=["discord:#bot-home"])
        with _patch_cfg(cfg), _patch_not_cron():
            d = evaluate_send_policy("discord", "bot-home", "hi", "discord:bot-home")
        assert d.allowed is True
        assert d.reason == send_firewall.REASON_TRUSTED

    def test_trusted_target_glob(self):
        cfg = _cfg(trusted_targets=["discord:*"])
        with _patch_cfg(cfg), _patch_not_cron():
            d = evaluate_send_policy("discord", "123456789", "hi", "discord:123456789")
        assert d.allowed is True
        assert d.reason == send_firewall.REASON_TRUSTED

    def test_auto_approve_message_prefix(self):
        cfg = _cfg(auto_approve=[{"target_pattern": "*", "message_pattern": "Scheduled:"}])
        with _patch_cfg(cfg), _patch_not_cron():
            d = evaluate_send_policy(
                "telegram", "999", "Scheduled: standup reminder", "telegram:999"
            )
        assert d.allowed is True
        assert d.reason == send_firewall.REASON_AUTO_APPROVE

    def test_auto_approve_does_not_match_other_messages(self):
        cfg = _cfg(auto_approve=[{"target_pattern": "*", "message_pattern": "Scheduled:"}])
        with _patch_cfg(cfg), _patch_not_cron():
            d = evaluate_send_policy("telegram", "999", "hello there", "telegram:999")
        assert d.allowed is False
        assert d.reason == send_firewall.REASON_PENDING

    def test_auto_approve_target_scoped(self):
        cfg = _cfg(auto_approve=[{"target_pattern": "discord:*", "message_pattern": "*"}])
        with _patch_cfg(cfg), _patch_not_cron():
            d_ok = evaluate_send_policy("discord", "1", "anything", "discord:1")
            d_no = evaluate_send_policy("telegram", "1", "anything", "telegram:1")
        assert d_ok.allowed is True and d_ok.reason == send_firewall.REASON_AUTO_APPROVE
        assert d_no.allowed is False and d_no.reason == send_firewall.REASON_PENDING

    def test_platform_policy_allow(self):
        cfg = _cfg(platform_policy={"discord": "allow"})
        with _patch_cfg(cfg), _patch_not_cron():
            d = evaluate_send_policy("discord", "123", "hi", "discord:123")
        assert d.allowed is True
        assert d.reason == send_firewall.REASON_PLATFORM_ALLOW

    def test_platform_policy_deny_blocks_without_prompt(self):
        cfg = _cfg(platform_policy={"telegram": "deny"})
        with _patch_cfg(cfg), _patch_not_cron():
            d = evaluate_send_policy("telegram", "999", "hi", "telegram:999")
        assert d.allowed is False
        assert d.reason == send_firewall.REASON_PLATFORM_DENY
        assert d.needs_confirmation is False  # hard deny, not a confirm-prompt

    def test_platform_policy_confirm_default(self):
        # No platform_policy section at all -> default 'confirm'.
        with _patch_cfg(_cfg()), _patch_not_cron():
            d = evaluate_send_policy("slack", "C123", "hi", "slack:C123")
        assert d.reason == send_firewall.REASON_PENDING

    def test_self_beats_deny_policy(self):
        # Send-to-self is checked before platform policy: a home-channel send
        # is allowed even if that platform's policy is 'deny'.
        cfg = _cfg(platform_policy={"telegram": "deny"})
        with _patch_cfg(cfg), _patch_not_cron():
            d = evaluate_send_policy(
                "telegram", "111", "note to self", "telegram", used_home_channel=True
            )
        assert d.allowed is True
        assert d.reason == send_firewall.REASON_SELF

    def test_cron_session_exempt(self):
        with _patch_cfg(_cfg()), patch(
            "tools.send_firewall._is_cron_session", return_value=True
        ):
            d = evaluate_send_policy("telegram", "999", "report", "telegram:999")
        assert d.allowed is True
        assert d.reason == send_firewall.REASON_CRON

    def test_cron_gated_when_gate_cron_set(self):
        cfg = _cfg(gate_cron=True)
        with _patch_cfg(cfg), patch(
            "tools.send_firewall._is_cron_session", return_value=True
        ):
            d = evaluate_send_policy("telegram", "999", "report", "telegram:999")
        assert d.allowed is False
        assert d.reason == send_firewall.REASON_PENDING

    def test_preview_truncated(self):
        long_msg = "x" * (send_firewall._PREVIEW_MAX + 500)
        with _patch_cfg(_cfg()), _patch_not_cron():
            d = evaluate_send_policy("telegram", "999", long_msg, "telegram:999")
        assert len(d.message_preview) == send_firewall._PREVIEW_MAX


# =========================================================================
# is_enabled
# =========================================================================

class TestIsEnabled:
    def test_enabled_true(self):
        with _patch_cfg({"enabled": True}):
            assert send_firewall.is_enabled() is True

    def test_enabled_missing_is_false(self):
        with _patch_cfg({}):
            assert send_firewall.is_enabled() is False


# =========================================================================
# Always-Allow persistence
# =========================================================================

class TestAddTrustedTarget:
    def test_persists_to_config_when_not_managed(self):
        saved = {}

        def _fake_save(cfg):
            saved["cfg"] = cfg

        with patch("hermes_cli.config.is_managed", return_value=False), \
             patch("hermes_cli.config.load_config", return_value={}), \
             patch("hermes_cli.config.save_config", side_effect=_fake_save):
            ok = send_firewall.add_trusted_target("telegram:999")

        assert ok is True
        assert "telegram:999" in saved["cfg"]["messaging_firewall"]["trusted_targets"]

    def test_managed_falls_back_to_session(self):
        with patch("hermes_cli.config.is_managed", return_value=True), \
             patch("hermes_cli.config.load_config", return_value={}), \
             patch("hermes_cli.config.save_config") as save_mock:
            ok = send_firewall.add_trusted_target("telegram:999")

        assert ok is False
        save_mock.assert_not_called()
        # Session allowlist now honors the target even though disk write was skipped.
        with _patch_cfg(_cfg()), _patch_not_cron():
            d = evaluate_send_policy("telegram", "999", "hi", "telegram:999")
        assert d.allowed is True
        assert d.reason == send_firewall.REASON_TRUSTED


# =========================================================================
# request_approval dispatch
# =========================================================================

class TestRequestApproval:
    def test_gateway_context_fails_closed(self):
        with patch("tools.send_firewall._is_gateway_context", return_value=True):
            approved, edited = send_firewall.request_approval(
                "telegram", "999", "hi", "telegram:999", "sess-1"
            )
        assert approved is False
        assert edited is None

    def test_cli_approve(self):
        with patch("tools.send_firewall._is_gateway_context", return_value=False), \
             patch("tools.send_firewall._request_approval_cli", return_value=(True, None)) as cli_mock:
            approved, edited = send_firewall.request_approval(
                "telegram", "999", "hi", "telegram:999", "sess-1"
            )
        assert approved is True
        assert edited is None
        cli_mock.assert_called_once()


# =========================================================================
# Integration: the gate inside send_message_tool._handle_send
# =========================================================================

def _run_async_immediately(coro):
    return asyncio.run(coro)


def _make_config(home=None):
    telegram_cfg = SimpleNamespace(enabled=True, token="***", extra={})
    return SimpleNamespace(
        platforms={Platform.TELEGRAM: telegram_cfg},
        get_home_channel=lambda _platform: home,
    ), telegram_cfg


class TestFirewallIntegration:
    def _send(self, *, target, message="hello"):
        return json.loads(
            send_message_tool({"action": "send", "target": target, "message": message})
        )

    def test_firewall_off_sends_normally(self):
        config, _cfg_obj = _make_config()
        with patch("gateway.config.load_gateway_config", return_value=config), \
             patch("tools.interrupt.is_interrupted", return_value=False), \
             patch("model_tools._run_async", side_effect=_run_async_immediately), \
             patch("tools.send_message_tool._send_to_platform",
                   new=AsyncMock(return_value={"success": True})) as send_mock, \
             patch("gateway.mirror.mirror_to_session", return_value=True), \
             patch("tools.send_firewall.is_enabled", return_value=False):
            result = self._send(target="telegram:999")
        assert result["success"] is True
        send_mock.assert_awaited_once()

    def test_denied_send_is_blocked(self):
        config, _cfg_obj = _make_config()
        with patch("gateway.config.load_gateway_config", return_value=config), \
             patch("tools.interrupt.is_interrupted", return_value=False), \
             patch("model_tools._run_async", side_effect=_run_async_immediately), \
             patch("tools.send_message_tool._send_to_platform",
                   new=AsyncMock(return_value={"success": True})) as send_mock, \
             patch("gateway.mirror.mirror_to_session", return_value=True), \
             patch("tools.send_firewall.is_enabled", return_value=True), \
             patch("tools.send_firewall.evaluate_send_policy",
                   return_value=FirewallDecision(False, send_firewall.REASON_PENDING,
                                                 "telegram", "999", "telegram:999", "hello")), \
             patch("tools.send_firewall.request_approval", return_value=(False, None)) as approve_mock:
            result = self._send(target="telegram:999")
        assert result.get("firewall") == "denied"
        assert "blocked by the messaging firewall" in result["error"]
        send_mock.assert_not_awaited()
        approve_mock.assert_called_once()

    def test_approved_send_proceeds(self):
        config, telegram_cfg = _make_config()
        with patch("gateway.config.load_gateway_config", return_value=config), \
             patch("tools.interrupt.is_interrupted", return_value=False), \
             patch("model_tools._run_async", side_effect=_run_async_immediately), \
             patch("tools.send_message_tool._send_to_platform",
                   new=AsyncMock(return_value={"success": True})) as send_mock, \
             patch("gateway.mirror.mirror_to_session", return_value=True), \
             patch("tools.send_firewall.is_enabled", return_value=True), \
             patch("tools.send_firewall.evaluate_send_policy",
                   return_value=FirewallDecision(False, send_firewall.REASON_PENDING,
                                                 "telegram", "999", "telegram:999", "hello")), \
             patch("tools.send_firewall.request_approval", return_value=(True, None)):
            result = self._send(target="telegram:999")
        assert result["success"] is True
        send_mock.assert_awaited_once()
        # Sent with the original message.
        assert send_mock.await_args.args[3] == "hello"

    def test_approved_edit_changes_delivered_message(self):
        config, telegram_cfg = _make_config()
        with patch("gateway.config.load_gateway_config", return_value=config), \
             patch("tools.interrupt.is_interrupted", return_value=False), \
             patch("model_tools._run_async", side_effect=_run_async_immediately), \
             patch("tools.send_message_tool._send_to_platform",
                   new=AsyncMock(return_value={"success": True})) as send_mock, \
             patch("gateway.mirror.mirror_to_session", return_value=True), \
             patch("tools.send_firewall.is_enabled", return_value=True), \
             patch("tools.send_firewall.evaluate_send_policy",
                   return_value=FirewallDecision(False, send_firewall.REASON_PENDING,
                                                 "telegram", "999", "telegram:999", "hello")), \
             patch("tools.send_firewall.request_approval", return_value=(True, "edited text")):
            result = self._send(target="telegram:999", message="hello")
        assert result["success"] is True
        send_mock.assert_awaited_once()
        assert send_mock.await_args.args[3] == "edited text"

    def test_allowed_decision_skips_approval(self):
        # evaluate_send_policy returns allowed -> request_approval never called.
        config, _cfg_obj = _make_config()
        with patch("gateway.config.load_gateway_config", return_value=config), \
             patch("tools.interrupt.is_interrupted", return_value=False), \
             patch("model_tools._run_async", side_effect=_run_async_immediately), \
             patch("tools.send_message_tool._send_to_platform",
                   new=AsyncMock(return_value={"success": True})) as send_mock, \
             patch("gateway.mirror.mirror_to_session", return_value=True), \
             patch("tools.send_firewall.is_enabled", return_value=True), \
             patch("tools.send_firewall.evaluate_send_policy",
                   return_value=FirewallDecision(True, send_firewall.REASON_TRUSTED,
                                                 "telegram", "999", "telegram:999", "hello")), \
             patch("tools.send_firewall.request_approval") as approve_mock:
            result = self._send(target="telegram:999")
        assert result["success"] is True
        send_mock.assert_awaited_once()
        approve_mock.assert_not_called()

    def test_policy_deny_hard_blocks(self):
        config, _cfg_obj = _make_config()
        with patch("gateway.config.load_gateway_config", return_value=config), \
             patch("tools.interrupt.is_interrupted", return_value=False), \
             patch("model_tools._run_async", side_effect=_run_async_immediately), \
             patch("tools.send_message_tool._send_to_platform",
                   new=AsyncMock(return_value={"success": True})) as send_mock, \
             patch("gateway.mirror.mirror_to_session", return_value=True), \
             patch("tools.send_firewall.is_enabled", return_value=True), \
             patch("tools.send_firewall.evaluate_send_policy",
                   return_value=FirewallDecision(False, send_firewall.REASON_PLATFORM_DENY,
                                                 "telegram", "999", "telegram:999", "hello")), \
             patch("tools.send_firewall.request_approval") as approve_mock:
            result = self._send(target="telegram:999")
        assert result.get("firewall") == "policy_denied"
        send_mock.assert_not_awaited()
        approve_mock.assert_not_called()
