"""Tests for Zoom Team Chat gateway setup integration."""

from __future__ import annotations

import os
from unittest.mock import MagicMock

from gateway.platform_registry import PlatformEntry, platform_registry


def _register_zoom_platform(**overrides):
    defaults = dict(
        name="zoom",
        label="Zoom Team Chat",
        adapter_factory=lambda cfg: None,
        check_fn=lambda: bool(os.getenv("ZOOM_ACCOUNT_ID", "") and os.getenv("ZOOM_CHAT_BOT_JID", "")),
        validate_config=lambda cfg: True,
        required_env=[
            "ZOOM_ACCOUNT_ID",
            "ZOOM_CLIENT_ID",
            "ZOOM_CLIENT_SECRET",
            "ZOOM_CHAT_BOT_JID",
            "ZOOM_WEBHOOK_SECRET_TOKEN",
        ],
        install_hint="pip install aiohttp requests",
        setup_fn=lambda: None,
        source="plugin",
        plugin_name="zoom-platform",
        allowed_users_env="ZOOM_ALLOWED_USERS",
        allow_all_env="ZOOM_ALLOW_ALL_USERS",
        max_message_length=4000,
        pii_safe=False,
        emoji="🎥",
        allow_update_command=True,
        platform_hint="You are chatting via Zoom Team Chat.",
    )
    defaults.update(overrides)
    entry = PlatformEntry(**defaults)
    platform_registry.register(entry)
    return {
        "key": entry.name,
        "label": entry.label,
        "emoji": entry.emoji,
        "token_var": entry.required_env[0] if entry.required_env else "",
        "install_hint": entry.install_hint,
        "_registry_entry": entry,
    }


def _unregister_zoom_platform():
    platform_registry.unregister("zoom")


class TestZoomFreshInstallDiscovery:
    def test_zoom_appears_in_all_platforms(self, monkeypatch):
        import hermes_cli.gateway as gateway_mod

        _register_zoom_platform()
        try:
            for key in (
                "ZOOM_ACCOUNT_ID",
                "ZOOM_CLIENT_ID",
                "ZOOM_CLIENT_SECRET",
                "ZOOM_CHAT_BOT_JID",
                "ZOOM_WEBHOOK_SECRET_TOKEN",
            ):
                monkeypatch.delenv(key, raising=False)

            platforms = gateway_mod._all_platforms()
            keys = {p["key"] for p in platforms}
            assert "zoom" in keys

            zoom_plat = next(p for p in platforms if p["key"] == "zoom")
            assert zoom_plat["label"] == "Zoom Team Chat"
            assert zoom_plat["emoji"] == "🎥"
        finally:
            _unregister_zoom_platform()

    def test_zoom_status_not_configured_when_fresh(self, monkeypatch):
        import hermes_cli.gateway as gateway_mod

        plat = _register_zoom_platform()
        try:
            for key in (
                "ZOOM_ACCOUNT_ID",
                "ZOOM_CLIENT_ID",
                "ZOOM_CLIENT_SECRET",
                "ZOOM_CHAT_BOT_JID",
                "ZOOM_WEBHOOK_SECRET_TOKEN",
            ):
                monkeypatch.delenv(key, raising=False)
            status = gateway_mod._platform_status(plat)
            assert status == "not configured"
        finally:
            _unregister_zoom_platform()

    def test_zoom_status_configured_when_env_set(self, monkeypatch):
        import hermes_cli.gateway as gateway_mod

        plat = _register_zoom_platform()
        try:
            monkeypatch.setenv("ZOOM_ACCOUNT_ID", "acct")
            monkeypatch.setenv("ZOOM_CLIENT_ID", "cid")
            monkeypatch.setenv("ZOOM_CLIENT_SECRET", "sec")
            monkeypatch.setenv("ZOOM_CHAT_BOT_JID", "bot-jid")
            monkeypatch.setenv("ZOOM_WEBHOOK_SECRET_TOKEN", "whsec")
            status = gateway_mod._platform_status(plat)
            assert status == "configured"
        finally:
            _unregister_zoom_platform()


class TestZoomInteractiveSetup:
    def test_configure_platform_dispatches_to_zoom_setup_fn(self, capsys):
        import hermes_cli.gateway as gateway_mod

        calls = []

        def fake_setup():
            calls.append("setup_called")
            print("Zoom setup complete!")

        plat = _register_zoom_platform(setup_fn=fake_setup)
        try:
            gateway_mod._configure_platform(plat)
        finally:
            _unregister_zoom_platform()

        assert "setup_called" in calls
        assert "Zoom setup complete!" in capsys.readouterr().out

    def test_interactive_setup_persists_credentials(self, tmp_path, monkeypatch):
        hermes_home = tmp_path / "hermes"
        monkeypatch.setenv("HERMES_HOME", str(hermes_home))

        import hermes_cli.cli_output as cli_output_mod
        import plugins.platforms.zoom.adapter as zoom_mod

        answers = iter(["acct", "cid", "sec", "bot-jid", "whsec"])
        monkeypatch.setattr(cli_output_mod, "prompt", lambda *_a, **_kw: next(answers))
        monkeypatch.setattr(cli_output_mod, "print_info", lambda *_a, **_kw: None)
        monkeypatch.setattr(cli_output_mod, "print_success", lambda *_a, **_kw: None)
        monkeypatch.setattr(cli_output_mod, "print_warning", lambda *_a, **_kw: None)

        zoom_mod.interactive_setup()

        env_text = (hermes_home / ".env").read_text(encoding="utf-8")
        assert "ZOOM_ACCOUNT_ID=acct" in env_text
        assert "ZOOM_CLIENT_ID=cid" in env_text
        assert "ZOOM_CLIENT_SECRET=sec" in env_text
        assert "ZOOM_CHAT_BOT_JID=bot-jid" in env_text
        assert "ZOOM_WEBHOOK_SECRET_TOKEN=whsec" in env_text
