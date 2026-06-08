"""Tests for bundled `evm-readonly-jsonrpc` skill (whitelist HTTPS JSON-RPC)."""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_DIR = _REPO_ROOT / "skills/web3/evm-readonly-jsonrpc/scripts"

if str(_SCRIPT_DIR) not in sys.path:

    sys.path.insert(0, str(_SCRIPT_DIR))


def _transport():

    spec = importlib.util.spec_from_file_location(
        "_evm_transport_under_test",
        _SCRIPT_DIR / "_evm_transport.py",
    )

    mod = importlib.util.module_from_spec(spec)

    assert spec.loader is not None

    spec.loader.exec_module(mod)

    return mod


def _cli():

    spec = importlib.util.spec_from_file_location(
        "evm_jsonrpc_under_test",
        _SCRIPT_DIR / "evm_jsonrpc.py",
    )

    mod = importlib.util.module_from_spec(spec)

    assert spec.loader is not None

    spec.loader.exec_module(mod)

    return mod


def test_disallows_send_raw():

    _ev = _transport()

    envelope = _ev._Envelope(method="eth_sendRawTransaction", params=[])

    out = _ev.rpc_call(envelope, ["https://example.invalid/rpc"])

    assert out["success"] is False
    assert out.get("disallowed") is True


def test_eth_chain_id_success(monkeypatch: pytest.MonkeyPatch):

    _ev = _transport()

    class _Fake:

        def __enter__(self):
            return self

        def __exit__(self, *a):

            return False

        def read(self):

            return b'{"jsonrpc":"2.0","id":1,"result":"0x539"}'


    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=_ev._RPC_TIMEOUT_SEC: _Fake())

    envelope = _ev._Envelope(method="eth_chainId", params=[])

    out = _ev.rpc_call(envelope, ["https://example.good/rpc"])

    assert out["success"] is True

    assert out["result"] == "0x539"

    assert "endpoint" in out


def test_eth_call_rejects_non_object_first():

    _ev = _transport()

    envelope = _ev._Envelope(method="eth_call", params=["bad", "latest"])

    out = _ev.rpc_call(envelope, ["https://example.invalid/rpc"])

    assert out["success"] is False
    assert "eth_call requires" in (out.get("error") or "")


def test_eth_call_oversized_data():

    _ev = _transport()

    huge = "0x" + "ab" * (20_481)

    envelope = _ev._Envelope(
        method="eth_call",
        params=[{"to": "0x0000000000000000000000000000000000000000", "data": huge}, "latest"],
    )

    out = _ev.rpc_call(envelope, ["https://example.invalid/rpc"])

    assert out["success"] is False

    assert "exceeds configured maximum" in (out.get("error") or "")


def test_main_requires_rpc_env():

    monkeypatch = pytest.MonkeyPatch()

    monkeypatch.delenv("HERMES_SKILL_EVM_RPC_URL", raising=False)

    monkeypatch.delenv("HERMES_SKILL_EVM_RPC_URLS", raising=False)

    try:

        cli_mod = _cli()

        rc = cli_mod.main(["rpc", "--method", "eth_chainId"])

        assert rc == 1

    finally:

        monkeypatch.undo()


def test_fallback_second_endpoint(monkeypatch: pytest.MonkeyPatch):

    _ev = _transport()

    state = {"n": 0}

    class _Body:

        def __enter__(self):
            return self

        def __exit__(self, *a):

            return False

        def read(self):

            return b'{"jsonrpc":"2.0","id":1,"result":"0xaa"}'


    def fake_urlopen(req, *, timeout=_ev._RPC_TIMEOUT_SEC):

        state["n"] += 1

        if req.full_url.endswith("rpc-a"):

            fp = io.BytesIO(b"{}")

            fp.seek(0)

            raise urllib.error.HTTPError("", 503, "Unavailable", msg=None, hdrs={}, fp=fp)

        assert req.full_url.endswith("rpc-b")

        return _Body()


    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    envelope = _ev._Envelope(method="eth_gasPrice", params=[])

    out = _ev.rpc_call(
        envelope,
        ["https://example.invalid/rpc-a", "https://example.invalid/rpc-b"],

    )

    assert state["n"] >= 2

    assert out["success"] is True

    assert out["endpoint"].endswith("rpc-b")


def test_cli_stdout(monkeypatch: pytest.MonkeyPatch, capsys):

    cli_mod = _cli()

    class _Ok:

        def __enter__(self):
            return self

        def __exit__(self, *a):

            return False

        def read(self):

            return b'{"jsonrpc":"2.0","id":1,"result":"0xbeef"}'


    monkeypatch.setattr(urllib.request, "urlopen", lambda req, *, timeout=None: _Ok())


    rc = cli_mod.main(["rpc", "--method", "eth_blockNumber", "--rpc-url", "https://x.example/rpc"])

    assert rc == 0

    stdout = capsys.readouterr().out.strip()


    line = json.loads(stdout)


    assert line["success"] is True

    assert line["endpoint"] == "https://x.example/rpc"

