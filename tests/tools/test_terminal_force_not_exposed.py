"""Tests that the 'force' parameter is NOT exposed in the terminal tool's LLM schema.

The ``force`` parameter on ``terminal_tool()`` bypasses ALL security checks
(dangerous-command approval, tirith guards, etc.).  It exists for internal
programmatic use only (e.g. after the user has already approved a command
through the interactive approval flow).

If ``force`` were included in the tool schema sent to the LLM, a model could
trivially bypass every safety check by setting ``force=True``.  These tests
ensure that:

1. ``force`` never appears in the schema properties.
2. The handler that bridges LLM args -> ``terminal_tool()`` never forwards
   ``force`` from the args dict.
3. ``force`` still works when called directly in Python (internal use).
"""

import json
import logging

import tools.terminal_tool as tt
from tools.terminal_tool import TERMINAL_SCHEMA, _handle_terminal


# ── Schema tests ──────────────────────────────────────────────────────────


def test_force_not_in_schema_properties():
    """'force' must not appear in TERMINAL_SCHEMA properties."""
    props = TERMINAL_SCHEMA["parameters"]["properties"]
    assert "force" not in props, (
        "SECURITY: 'force' parameter found in TERMINAL_SCHEMA — "
        "this would let the LLM bypass all security checks"
    )


def test_force_not_in_schema_required():
    """'force' must not be listed as a required parameter."""
    required = TERMINAL_SCHEMA["parameters"].get("required", [])
    assert "force" not in required, (
        "SECURITY: 'force' listed in required parameters"
    )


def test_schema_has_no_force_anywhere():
    """Deep check: 'force' must not appear anywhere in the serialised schema."""
    schema_str = json.dumps(TERMINAL_SCHEMA)
    # Check for the key name in JSON form — catches nested or future additions
    assert '"force"' not in schema_str, (
        "SECURITY: 'force' found somewhere in the serialised TERMINAL_SCHEMA"
    )


# ── Registry tests ────────────────────────────────────────────────────────


def test_force_not_in_registered_schema():
    """The schema stored in the tool registry must not include 'force'."""
    from tools.registry import registry

    schema = registry.get_schema("terminal")
    assert schema is not None, "terminal tool not found in registry"
    props = schema["parameters"]["properties"]
    assert "force" not in props, (
        "SECURITY: 'force' found in registered terminal schema properties"
    )


def test_force_not_in_openai_format_definitions():
    """get_definitions() output (sent to the LLM) must not contain 'force'."""
    from tools.registry import registry

    defs = registry.get_definitions({"terminal"}, quiet=True)
    assert len(defs) >= 1, "terminal tool not returned by get_definitions"

    for defn in defs:
        fn = defn.get("function", {})
        props = fn.get("parameters", {}).get("properties", {})
        assert "force" not in props, (
            "SECURITY: 'force' present in OpenAI-format tool definition"
        )
        # Also check serialised form for nested occurrences
        assert '"force"' not in json.dumps(fn.get("parameters", {})), (
            "SECURITY: 'force' found in serialised parameters of tool definition"
        )


# ── Handler guard tests ──────────────────────────────────────────────────


def test_handle_terminal_ignores_force_from_args(monkeypatch, caplog):
    """_handle_terminal must never forward 'force' from LLM-supplied args."""
    calls = []

    def fake_terminal_tool(**kwargs):
        calls.append(kwargs)
        return json.dumps({"output": "", "exit_code": 0, "error": None})

    monkeypatch.setattr(tt, "terminal_tool", fake_terminal_tool)

    with caplog.at_level(logging.WARNING):
        _handle_terminal({"command": "echo hi", "force": True})

    assert len(calls) == 1
    assert "force" not in calls[0], (
        "SECURITY: _handle_terminal forwarded 'force' from args to terminal_tool()"
    )
    # Should log a warning about the blocked attempt
    assert any("force" in rec.message.lower() for rec in caplog.records), (
        "_handle_terminal should log a warning when LLM tries to set force=True"
    )


def test_handle_terminal_works_without_force(monkeypatch):
    """Normal invocation (no force) should work fine."""
    calls = []

    def fake_terminal_tool(**kwargs):
        calls.append(kwargs)
        return json.dumps({"output": "ok", "exit_code": 0, "error": None})

    monkeypatch.setattr(tt, "terminal_tool", fake_terminal_tool)

    result = _handle_terminal({"command": "ls"})
    assert len(calls) == 1
    assert calls[0]["command"] == "ls"
    assert "force" not in calls[0]


# ── Programmatic (internal) force still works ─────────────────────────────


def test_force_bypasses_guards_when_called_directly(monkeypatch):
    """Calling terminal_tool(force=True) directly should skip security checks.

    This confirms 'force' is still functional for internal/programmatic use,
    just not exposed to the LLM.
    """
    guard_called = []

    original_check = tt._check_all_guards

    def tracking_guard(command, env_type):
        guard_called.append(command)
        return original_check(command, env_type)

    monkeypatch.setattr(tt, "_check_all_guards", tracking_guard)

    # Also stub out environment creation so we don't need real infra
    class FakeEnv:
        def execute(self, command, **kwargs):
            return {"output": "done", "returncode": 0}

    monkeypatch.setattr(tt, "_active_environments", {"default": FakeEnv()})
    monkeypatch.setattr(tt, "_last_activity", {"default": 0})
    monkeypatch.setenv("TERMINAL_ENV", "local")

    # With force=True, _check_all_guards should NOT be called
    result = tt.terminal_tool(command="echo test", force=True)
    parsed = json.loads(result)
    assert parsed.get("exit_code") == 0
    assert len(guard_called) == 0, (
        "force=True should skip _check_all_guards entirely"
    )
