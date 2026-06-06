"""Regression test for #21119 — gateway image routing must consult session
overrides, not just config.yaml.

When a user runs ``/model mimo-v2-pro`` (text-only Xiaomi MiMo) on a WeChat
session whose config.yaml default is the vision-capable ``mimo-v2.5``, the
gateway used to make its image-input routing decision against the config
default (vision-capable -> ``native``), then send the inline ``image_url``
content parts to the session-active text-only endpoint, which rejected
them with::

    400 unknown variant image_url, expected text

The fix routes the decision through the session's actual override-resolved
provider/model so non-vision sessions correctly fall back to ``text`` mode
(vision_analyze pre-analysis + prepended description).
"""

from __future__ import annotations

from unittest.mock import patch

from gateway.run import GatewayRunner


def _make_runner() -> GatewayRunner:
    runner = GatewayRunner.__new__(GatewayRunner)
    runner._session_model_overrides = {}
    return runner


def test_session_override_to_text_only_xiaomi_routes_text():
    """Session was switched to text-only Xiaomi MiMo — must route ``text``.

    Without the fix, ``_decide_image_input_mode`` reads provider/model from
    config.yaml (vision-capable mimo-v2.5) and returns ``native``, which
    then sends ``image_url`` parts that the actual session-active endpoint
    (mimo-v2-pro, text-only) rejects with HTTP 400.
    """
    runner = _make_runner()
    session_key = "weixin:user-42"
    runner._session_model_overrides[session_key] = {
        "provider": "xiaomi",
        "model": "mimo-v2-pro",  # text-only per models.dev modalities
    }

    # Stub config.yaml to assert the override path beats the config path:
    # config says vision-capable mimo-v2.5, override says text-only mimo-v2-pro.
    with patch("hermes_cli.config.load_config", return_value={
        "model": {"provider": "xiaomi", "default": "mimo-v2.5"},
    }):
        # Force a deterministic capability lookup: caps say mimo-v2-pro is
        # NOT vision-capable, mimo-v2.5 IS. The fix must consult the override
        # so the decision is "text", not "native".
        def fake_caps(provider: str, model: str):
            class _Caps:
                def __init__(self, supports_vision: bool) -> None:
                    self.supports_vision = supports_vision
            if model == "mimo-v2-pro":
                return _Caps(False)
            if model == "mimo-v2.5":
                return _Caps(True)
            return None

        with patch("agent.models_dev.get_model_capabilities", side_effect=fake_caps):
            mode = runner._decide_image_input_mode(session_key=session_key)

    assert mode == "text", (
        "Session override to text-only model must force text routing — "
        "otherwise inline image_url parts get rejected by the API (#21119)."
    )


def test_no_session_override_falls_back_to_config_yaml():
    """Without an override, config.yaml's main provider/model is used."""
    runner = _make_runner()
    # Empty overrides dict; pass session_key that is not present.
    session_key = "weixin:user-7"

    with patch("hermes_cli.config.load_config", return_value={
        "model": {"provider": "xiaomi", "default": "mimo-v2.5"},
    }):
        def fake_caps(provider: str, model: str):
            class _Caps:
                def __init__(self, supports_vision: bool) -> None:
                    self.supports_vision = supports_vision
            if model == "mimo-v2.5":
                return _Caps(True)
            return None

        with patch("agent.models_dev.get_model_capabilities", side_effect=fake_caps):
            mode = runner._decide_image_input_mode(session_key=session_key)

    assert mode == "native", (
        "Without a session override, config.yaml's vision-capable model "
        "should still route native."
    )


def test_no_session_key_argument_preserves_legacy_behavior():
    """Calling without session_key reads config.yaml — backward compatible."""
    runner = _make_runner()
    runner._session_model_overrides["weixin:user-1"] = {
        "provider": "xiaomi",
        "model": "mimo-v2-pro",
    }

    with patch("hermes_cli.config.load_config", return_value={
        "model": {"provider": "xiaomi", "default": "mimo-v2.5"},
    }):
        def fake_caps(provider: str, model: str):
            class _Caps:
                def __init__(self, supports_vision: bool) -> None:
                    self.supports_vision = supports_vision
            if model == "mimo-v2.5":
                return _Caps(True)
            if model == "mimo-v2-pro":
                return _Caps(False)
            return None

        with patch("agent.models_dev.get_model_capabilities", side_effect=fake_caps):
            mode = runner._decide_image_input_mode()  # no session_key

    assert mode == "native", (
        "Without session_key, the function must consult config.yaml only — "
        "this preserves call sites that pre-date the override-aware signature."
    )
