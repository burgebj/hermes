from gateway.platforms.base import split_gateway_response_text
from gateway.run import _channel_worker_options


def test_channel_routes_resolve_fresh_worker_options():
    cfg = {
        "channel_routes": {
            "discord": {
                "123": {
                    "mode": "fresh_per_message",
                    "enabled_toolsets": ["file", "web", "browser"],
                    "skip_memory": True,
                    "skip_context_files": True,
                }
            }
        }
    }

    opts = _channel_worker_options(cfg, "discord", "123")

    assert opts["fresh_per_message"] is True
    assert opts["enabled_toolsets"] == ["browser", "file", "web"]
    assert opts["skip_memory"] is True
    assert opts["skip_context_files"] is True


def test_channel_routes_override_legacy_channel_options():
    cfg = {
        "channel_session_modes": {"discord": {"123": "fresh_per_message"}},
        "channel_agent_options": {
            "discord": {
                "123": {
                    "enabled_toolsets": ["terminal"],
                    "skip_memory": False,
                    "skip_context_files": False,
                }
            }
        },
        "channel_routes": {
            "discord": {
                "123": {
                    "mode": "default",
                    "enabled_toolsets": "web,file",
                    "skip_memory": True,
                }
            }
        },
    }

    opts = _channel_worker_options(cfg, "discord", "123")

    assert opts["fresh_per_message"] is False
    assert opts["enabled_toolsets"] == ["file", "web"]
    assert opts["skip_memory"] is True
    assert opts["skip_context_files"] is False


def test_gateway_nested_channel_routes_are_supported():
    cfg = {
        "gateway": {
            "channel_routes": {
                "discord": {
                    "123": {"fresh_per_message": True, "enabled_toolsets": ["web"]}
                }
            }
        }
    }

    opts = _channel_worker_options(cfg, "discord", "123")

    assert opts["fresh_per_message"] is True
    assert opts["enabled_toolsets"] == ["web"]


def test_response_splitter_sends_tail_as_copy_ready_message():
    cfg = {
        "response_splitters": {
            "discord": {
                "123": {
                    "marker_regex": r"(?im)^\s*(Comment draft:|Draft reply:)\s*$",
                    "keep_marker_with_head": True,
                    "strip_marker_from_tail": True,
                }
            }
        }
    }
    text = "Analysis paragraph.\n\nComment draft:\n\nCopy this comment only."

    parts = split_gateway_response_text(text, platform="discord", chat_id="123", config=cfg)

    assert parts == ["Analysis paragraph.\n\nComment draft:", "Copy this comment only."]


def test_response_splitter_leaves_unconfigured_channels_unchanged():
    cfg = {
        "response_splitters": {
            "discord": {
                "123": {"marker_regex": r"(?im)^Comment draft:$"}
            }
        }
    }
    text = "Analysis\n\nComment draft:\n\nCopy"

    assert split_gateway_response_text(text, platform="discord", chat_id="999", config=cfg) == [text]
