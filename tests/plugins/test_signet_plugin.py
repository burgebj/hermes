"""Tests for the signet plugin.

Covers the bundled plugin at ``plugins/signet/``:

  * ``HashChainSigner``: append, verify, tamper detection, session-safe
    reopen continues the chain across restarts.
  * Plugin ``__init__``: ``post_tool_call`` hook writes signed receipts
    under ``$HERMES_HOME/signet/``; ``on_session_end`` hook runs verify.
  * ``/signet`` slash command: status, verify, tail, path, help.
  * Bundled-plugin discovery via ``PluginManager.discover_and_load``.

The Signet adapter (``signet_adapter.py``) is exercised only when the
optional ``signet-auth`` package is installed; otherwise its tests are
skipped.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _isolate_env(tmp_path, monkeypatch):
    """Isolate HERMES_HOME for each test."""
    hermes_home = tmp_path / ".hermes"
    hermes_home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    monkeypatch.delenv("HERMES_SIGNET_PROVIDER", raising=False)
    yield hermes_home


def _load_lib():
    """Import ``audit_signer`` directly (library, no plugin deps).

    The module is registered in ``sys.modules`` before ``exec_module`` so
    dataclass annotation resolution on Python 3.10 can look up
    ``cls.__module__`` — otherwise it raises ``AttributeError: 'NoneType'``.
    """
    repo_root = Path(__file__).resolve().parents[2]
    lib_path = repo_root / "plugins" / "signet" / "audit_signer.py"
    name = "signet_audit_signer_under_test"
    spec = importlib.util.spec_from_file_location(name, lib_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_plugin_init(monkeypatch=None):
    """Import the plugin's ``__init__.py`` with its relative import resolved."""
    repo_root = Path(__file__).resolve().parents[2]
    plugin_dir = repo_root / "plugins" / "signet"

    if "hermes_plugins" not in sys.modules:
        ns = types.ModuleType("hermes_plugins")
        ns.__path__ = []
        sys.modules["hermes_plugins"] = ns

    pkg_name = "hermes_plugins.signet"
    for mod_name in [pkg_name, f"{pkg_name}.audit_signer", f"{pkg_name}.signet_adapter"]:
        sys.modules.pop(mod_name, None)

    spec = importlib.util.spec_from_file_location(
        pkg_name,
        plugin_dir / "__init__.py",
        submodule_search_locations=[str(plugin_dir)],
    )
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = pkg_name
    mod.__path__ = [str(plugin_dir)]
    sys.modules[pkg_name] = mod
    spec.loader.exec_module(mod)

    mod._signer = None
    return mod


# ---------------------------------------------------------------------------
# HashChainSigner library
# ---------------------------------------------------------------------------

class TestHashChainSignerAppend:
    def test_first_event_uses_genesis_prev_hash(self, _isolate_env):
        lib = _load_lib()
        signer = lib.HashChainSigner(_isolate_env / "audit.jsonl")
        e = signer.append(
            tool_name="write_file",
            args={"path": "/tmp/x", "content": "abc"},
            result="OK",
            session_id="s1", task_id="t1", tool_call_id="c1",
        )
        assert e.sequence == 0
        assert e.prev_hash == lib.GENESIS_HASH
        assert len(e.hash) == 64
        assert e.args_digest != e.result_digest

    def test_second_event_chains_to_first(self, _isolate_env):
        lib = _load_lib()
        s = lib.HashChainSigner(_isolate_env / "audit.jsonl")
        a = s.append("t", {"x": 1}, "r1", "s", "", "")
        b = s.append("t", {"x": 2}, "r2", "s", "", "")
        assert b.sequence == 1
        assert b.prev_hash == a.hash

    def test_persists_across_reopen(self, _isolate_env):
        lib = _load_lib()
        p = _isolate_env / "audit.jsonl"
        s1 = lib.HashChainSigner(p)
        a = s1.append("t", {"a": 1}, "r", "s", "", "")
        # Reopen — second signer must pick up at sequence 1 chaining to a.hash
        s2 = lib.HashChainSigner(p)
        b = s2.append("t", {"a": 2}, "r", "s", "", "")
        assert b.sequence == 1
        assert b.prev_hash == a.hash

    def test_result_not_string_is_canonicalized(self, _isolate_env):
        lib = _load_lib()
        s = lib.HashChainSigner(_isolate_env / "audit.jsonl")
        e = s.append("t", {"a": 1}, {"b": [1, 2, 3]}, "s", "", "")
        assert len(e.result_digest) == 64


class TestHashChainSignerVerify:
    def test_empty_log_verifies(self, _isolate_env):
        lib = _load_lib()
        s = lib.HashChainSigner(_isolate_env / "audit.jsonl")
        ok, n, err = s.verify()
        assert ok and n == 0 and err is None

    def test_clean_chain_verifies(self, _isolate_env):
        lib = _load_lib()
        s = lib.HashChainSigner(_isolate_env / "audit.jsonl")
        for i in range(5):
            s.append("t", {"i": i}, f"r{i}", "s", "", "")
        ok, n, err = s.verify()
        assert ok and n == 5 and err is None

    def test_tampered_entry_is_detected(self, _isolate_env):
        lib = _load_lib()
        p = _isolate_env / "audit.jsonl"
        s = lib.HashChainSigner(p)
        for i in range(3):
            s.append("t", {"i": i}, "r", "s", "", "")
        # Tamper: flip the tool_name of entry 1 in place
        lines = p.read_text().splitlines()
        entry = json.loads(lines[1])
        entry["tool_name"] = "pwned"
        lines[1] = json.dumps(entry, separators=(",", ":"))
        p.write_text("\n".join(lines) + "\n")

        s2 = lib.HashChainSigner(p)  # re-open to drop cached state
        ok, n, err = s2.verify()
        assert not ok
        assert "hash mismatch" in (err or "") or "sequence" in (err or "")

    def test_truncation_from_middle_is_detected(self, _isolate_env):
        lib = _load_lib()
        p = _isolate_env / "audit.jsonl"
        s = lib.HashChainSigner(p)
        for i in range(4):
            s.append("t", {"i": i}, "r", "s", "", "")
        lines = p.read_text().splitlines()
        # Delete entry at index 2 (keep 0, 1, 3) → sequence gap
        p.write_text("\n".join([lines[0], lines[1], lines[3]]) + "\n")
        ok, _, err = lib.HashChainSigner(p).verify()
        assert not ok
        assert "sequence" in (err or "") or "prev_hash" in (err or "")


class TestIterEvents:
    def test_roundtrip(self, _isolate_env):
        lib = _load_lib()
        s = lib.HashChainSigner(_isolate_env / "audit.jsonl")
        for i in range(3):
            s.append(f"tool{i}", {"i": i}, "r", "s", "", "")
        events = list(s.iter_events())
        assert len(events) == 3
        assert [e.sequence for e in events] == [0, 1, 2]
        assert [e.tool_name for e in events] == ["tool0", "tool1", "tool2"]


# ---------------------------------------------------------------------------
# Plugin hook tests
# ---------------------------------------------------------------------------

class TestPostToolCallHook:
    def test_hook_appends_one_entry(self, _isolate_env):
        pi = _load_plugin_init()
        pi._on_post_tool_call(
            tool_name="terminal",
            args={"command": "ls"},
            result="bin/\nusr/\n",
            task_id="t", session_id="s", tool_call_id="c1",
        )
        audit = _isolate_env / "signet" / "audit.jsonl"
        assert audit.exists()
        entries = [json.loads(line) for line in audit.read_text().splitlines() if line]
        assert len(entries) == 1
        assert entries[0]["tool_name"] == "terminal"
        assert entries[0]["sequence"] == 0

    def test_missing_tool_name_is_noop(self, _isolate_env):
        pi = _load_plugin_init()
        pi._on_post_tool_call(tool_name="", args={}, result="", task_id="", session_id="")
        assert not (_isolate_env / "signet" / "audit.jsonl").exists()

    def test_hook_is_exception_safe(self, _isolate_env, monkeypatch):
        pi = _load_plugin_init()
        # Force _get_signer to blow up — the hook must swallow the error.
        monkeypatch.setattr(pi, "_get_signer", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
        pi._on_post_tool_call(tool_name="terminal", args={}, result="x",
                              task_id="", session_id="", tool_call_id="")

    def test_two_calls_chain(self, _isolate_env):
        pi = _load_plugin_init()
        pi._on_post_tool_call(tool_name="a", args={}, result="1",
                              task_id="", session_id="", tool_call_id="")
        pi._on_post_tool_call(tool_name="b", args={}, result="2",
                              task_id="", session_id="", tool_call_id="")
        audit = _isolate_env / "signet" / "audit.jsonl"
        entries = [json.loads(line) for line in audit.read_text().splitlines() if line]
        assert [e["sequence"] for e in entries] == [0, 1]
        assert entries[1]["prev_hash"] == entries[0]["hash"]


class TestOnSessionEnd:
    def test_verify_on_session_end_noop_for_clean_chain(self, _isolate_env, caplog):
        pi = _load_plugin_init()
        pi._on_post_tool_call(tool_name="a", args={}, result="1",
                              task_id="", session_id="", tool_call_id="")
        pi._on_session_end()
        # Should not raise; chain is clean.


class TestProviderSelection:
    def test_default_is_hashchain(self, _isolate_env):
        pi = _load_plugin_init()
        assert pi._provider_name() == "hashchain"

    def test_env_override_to_signet_requested(self, _isolate_env, monkeypatch):
        monkeypatch.setenv("HERMES_SIGNET_PROVIDER", "signet")
        pi = _load_plugin_init()
        assert pi._provider_name() == "signet"

    def test_env_bogus_value_falls_back(self, _isolate_env, monkeypatch):
        monkeypatch.setenv("HERMES_SIGNET_PROVIDER", "nonsense")
        pi = _load_plugin_init()
        assert pi._provider_name() == "hashchain"

    def test_signet_provider_falls_back_when_missing(self, _isolate_env, monkeypatch):
        # Even if provider=signet, missing signet-auth must not crash the plugin —
        # it should fall back to HashChainSigner so the hook still produces events.
        monkeypatch.setenv("HERMES_SIGNET_PROVIDER", "signet")
        pi = _load_plugin_init()
        pi._on_post_tool_call(tool_name="x", args={}, result="r",
                              task_id="", session_id="", tool_call_id="")
        # Either provider writes entries; for HashChainSigner fallback it's
        # at $HERMES_HOME/signet/audit.jsonl.
        audit = _isolate_env / "signet" / "audit.jsonl"
        if not audit.exists():
            pytest.skip("signet-auth is installed — SignetSigner took over")
        data = [json.loads(line) for line in audit.read_text().splitlines() if line]
        assert data and data[0]["tool_name"] == "x"


# ---------------------------------------------------------------------------
# Slash command
# ---------------------------------------------------------------------------

class TestSlashCommand:
    def test_help_on_empty(self, _isolate_env):
        pi = _load_plugin_init()
        out = pi._handle_slash("")
        assert out and "signet" in out.lower()

    def test_path_prints_audit_dir(self, _isolate_env):
        pi = _load_plugin_init()
        out = pi._handle_slash("path")
        assert str(_isolate_env / "signet") in (out or "")

    def test_status_reports_clean_chain(self, _isolate_env):
        pi = _load_plugin_init()
        pi._on_post_tool_call(tool_name="a", args={}, result="1",
                              task_id="", session_id="", tool_call_id="")
        out = pi._handle_slash("status")
        assert "Provider:" in (out or "")
        assert "Events: 1" in (out or "")
        assert "Chain: OK" in (out or "")

    def test_verify_reports_ok(self, _isolate_env):
        pi = _load_plugin_init()
        pi._on_post_tool_call(tool_name="a", args={}, result="1",
                              task_id="", session_id="", tool_call_id="")
        out = pi._handle_slash("verify")
        assert "OK" in (out or "")

    def test_tail_prints_last_n(self, _isolate_env):
        pi = _load_plugin_init()
        for i in range(3):
            pi._on_post_tool_call(tool_name=f"t{i}", args={}, result=str(i),
                                  task_id="", session_id="", tool_call_id="")
        out = pi._handle_slash("tail 2")
        assert out and "t1" in out and "t2" in out
        assert "t0" not in out

    def test_unknown_subcommand(self, _isolate_env):
        pi = _load_plugin_init()
        out = pi._handle_slash("nonsense")
        assert "Unknown subcommand" in (out or "")


# ---------------------------------------------------------------------------
# Plugin discovery
# ---------------------------------------------------------------------------

class TestBundledDiscovery:
    def test_signet_is_discoverable(self, _isolate_env):
        from hermes_cli.plugins import PluginManager
        mgr = PluginManager()
        mgr.discover_and_load()
        # Bundled plugins are discovered but only loaded when enabled.
        # We just confirm the manifest was parsed without error.
        names = {p.manifest.name for p in mgr._plugins.values()}
        assert "signet" in names


# ---------------------------------------------------------------------------
# SignetSigner adapter (optional)
# ---------------------------------------------------------------------------

signet_auth = pytest.importorskip("signet_auth", reason="signet-auth not installed")


class TestSignetSigner:
    def test_append_and_verify_via_plugin(self, _isolate_env, monkeypatch):
        """Exercise SignetSigner through the plugin's own loader.

        Using the plugin's ``_get_signer`` keeps relative imports
        (``from .audit_signer import ...``) working without manual
        sys.modules gymnastics.
        """
        monkeypatch.setenv("HERMES_SIGNET_PROVIDER", "signet")
        pi = _load_plugin_init()
        pi._on_post_tool_call(
            tool_name="tool", args={"a": 1}, result="ok",
            task_id="t", session_id="s", tool_call_id="c",
        )
        signer = pi._get_signer()
        # The adapter lives under hermes_plugins.signet.signet_adapter when
        # loaded through the plugin's package hack — its type name is enough.
        assert type(signer).__name__ == "SignetSigner"
        ok, n, err = signer.verify()
        assert ok
        assert n >= 1
