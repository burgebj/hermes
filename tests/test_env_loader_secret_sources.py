"""Tests for the secret-source tracking in ``hermes_cli.env_loader``.

These cover the small public surface that lets `hermes model` / `hermes setup`
label detected credentials with their origin ("from Bitwarden") so users
don't see an unexplained "credentials ✓" line when their .env is empty.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hermes_cli import env_loader  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_sources():
    """Each test starts with a clean source map and applied-home guard."""
    env_loader._SECRET_SOURCES.clear()
    env_loader.reset_secret_source_cache()
    yield
    env_loader._SECRET_SOURCES.clear()
    env_loader.reset_secret_source_cache()


def test_get_secret_source_returns_none_for_untracked_var():
    assert env_loader.get_secret_source("ANTHROPIC_API_KEY") is None


def test_get_secret_source_returns_label_for_tracked_var():
    env_loader._SECRET_SOURCES["ANTHROPIC_API_KEY"] = "bitwarden"
    assert env_loader.get_secret_source("ANTHROPIC_API_KEY") == "bitwarden"


def test_format_secret_source_suffix_empty_for_untracked():
    # Credentials from .env or the shell shouldn't add noise — the
    # implicit case stays unlabeled.
    assert env_loader.format_secret_source_suffix("ANTHROPIC_API_KEY") == ""


def test_format_secret_source_suffix_bitwarden_uses_proper_name():
    env_loader._SECRET_SOURCES["ANTHROPIC_API_KEY"] = "bitwarden"
    assert (
        env_loader.format_secret_source_suffix("ANTHROPIC_API_KEY")
        == " (from Bitwarden)"
    )


def test_format_secret_source_suffix_generic_label_for_future_sources():
    # Future-proofing: a new secret source (e.g. "vault") should still
    # produce a sensible label without needing to edit every call site.
    env_loader._SECRET_SOURCES["OPENAI_API_KEY"] = "vault"
    assert (
        env_loader.format_secret_source_suffix("OPENAI_API_KEY")
        == " (from vault)"
    )


def test_format_secret_source_suffix_protonpass_uses_proper_name():
    env_loader._SECRET_SOURCES["ANTHROPIC_API_KEY"] = "protonpass"
    assert (
        env_loader.format_secret_source_suffix("ANTHROPIC_API_KEY")
        == " (from Proton Pass)"
    )


def test_apply_external_secret_sources_records_bitwarden_origin(tmp_path, monkeypatch):
    """End-to-end: when ``apply_bitwarden_secrets`` returns applied keys,
    they end up in ``_SECRET_SOURCES`` so the UI can label them."""

    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "secrets:\n"
        "  bitwarden:\n"
        "    enabled: true\n"
        "    project_id: test-project\n"
        "    access_token_env: BWS_ACCESS_TOKEN\n",
        encoding="utf-8",
    )

    # Stub apply_bitwarden_secrets to return a synthetic FetchResult.
    from agent.secret_sources.bitwarden import FetchResult

    fake_result = FetchResult(
        secrets={"ANTHROPIC_API_KEY": "sk-ant-test"},
        applied=["ANTHROPIC_API_KEY"],
    )

    def _fake_apply(**_kwargs):
        return fake_result

    # The import inside _apply_external_secret_sources is lazy, so we
    # patch the *module attribute* it will pull in.
    import agent.secret_sources.bitwarden as bw_module

    monkeypatch.setattr(bw_module, "apply_bitwarden_secrets", _fake_apply)

    env_loader._apply_external_secret_sources(tmp_path)

    assert env_loader.get_secret_source("ANTHROPIC_API_KEY") == "bitwarden"
    assert (
        env_loader.format_secret_source_suffix("ANTHROPIC_API_KEY")
        == " (from Bitwarden)"
    )


def test_apply_external_secret_sources_records_protonpass_origin(tmp_path, monkeypatch):
    """When ``apply_protonpass_secrets`` returns applied keys they end up in
    ``_SECRET_SOURCES`` tagged ``protonpass`` so the UI can label them."""

    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "secrets:\n"
        "  protonpass:\n"
        "    enabled: true\n"
        "    service_token_env: PROTON_PASS_PERSONAL_ACCESS_TOKEN\n"
        "    env:\n"
        "      ANTHROPIC_API_KEY: 'pass://SHARE/ITEM/api_key'\n",
        encoding="utf-8",
    )

    from agent.secret_sources.protonpass import FetchResult

    captured = {}

    def _fake_apply(**kwargs):
        captured.update(kwargs)
        return FetchResult(
            secrets={"ANTHROPIC_API_KEY": "sk-ant-test"},
            applied=["ANTHROPIC_API_KEY"],
        )

    import agent.secret_sources.protonpass as pp_module

    monkeypatch.setattr(pp_module, "apply_protonpass_secrets", _fake_apply)

    env_loader._apply_external_secret_sources(tmp_path)

    # B6: env_loader now threads a parsed ProtonPassConfig via ``config=``
    # instead of re-splatting the seven fields, so the `env` config key arrives
    # as ``config.env_refs`` (not a bare ``env_refs`` kwarg).
    assert captured["enabled"] is True
    assert captured["config"].env_refs == {
        "ANTHROPIC_API_KEY": "pass://SHARE/ITEM/api_key"
    }
    assert env_loader.get_secret_source("ANTHROPIC_API_KEY") == "protonpass"
    assert (
        env_loader.format_secret_source_suffix("ANTHROPIC_API_KEY")
        == " (from Proton Pass)"
    )


def test_apply_external_secret_sources_protonpass_noop_when_disabled(tmp_path, monkeypatch):
    """Disabled Proton Pass config must not call the backend or touch the map."""

    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "secrets:\n"
        "  protonpass:\n"
        "    enabled: false\n"
        "    env:\n"
        "      ANTHROPIC_API_KEY: 'pass://SHARE/ITEM/api_key'\n",
        encoding="utf-8",
    )

    called = {"n": 0}

    def _fake_apply(**_kwargs):  # pragma: no cover - must not be called
        called["n"] += 1
        from agent.secret_sources.protonpass import FetchResult
        return FetchResult()

    import agent.secret_sources.protonpass as pp_module
    monkeypatch.setattr(pp_module, "apply_protonpass_secrets", _fake_apply)

    env_loader._apply_external_secret_sources(tmp_path)

    assert called["n"] == 0
    assert env_loader.get_secret_source("ANTHROPIC_API_KEY") is None


def test_apply_external_secret_sources_noop_when_disabled(tmp_path, monkeypatch):
    """Disabled Bitwarden config must not touch the source map."""

    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "secrets:\n"
        "  bitwarden:\n"
        "    enabled: false\n",
        encoding="utf-8",
    )

    env_loader._apply_external_secret_sources(tmp_path)

    assert env_loader.get_secret_source("ANTHROPIC_API_KEY") is None


def test_apply_external_secret_sources_dedupes_within_process(tmp_path, monkeypatch):
    """``load_hermes_dotenv()`` is called at module-import time from several
    hot modules (cli.py, hermes_cli/main.py, run_agent.py, ...).  The
    Bitwarden status line previously printed once per call — 3-5x per
    startup.  The applied-home guard must short-circuit subsequent calls
    so the heavy work (config re-parse, Bitwarden lookup, status print)
    runs exactly once per HERMES_HOME per process.
    """

    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "secrets:\n"
        "  bitwarden:\n"
        "    enabled: true\n"
        "    project_id: test-project\n"
        "    access_token_env: BWS_ACCESS_TOKEN\n",
        encoding="utf-8",
    )

    from agent.secret_sources.bitwarden import FetchResult

    call_count = {"n": 0}

    def _fake_apply(**_kwargs):
        call_count["n"] += 1
        return FetchResult(
            secrets={"ANTHROPIC_API_KEY": "sk-ant-test"},
            applied=["ANTHROPIC_API_KEY"],
        )

    import agent.secret_sources.bitwarden as bw_module
    monkeypatch.setattr(bw_module, "apply_bitwarden_secrets", _fake_apply)

    # Five calls in a row, simulating module-import-time invocations from
    # cli.py, hermes_cli/main.py, run_agent.py, trajectory_compressor.py,
    # gateway/run.py.  Only the first should actually call the backend.
    for _ in range(5):
        env_loader._apply_external_secret_sources(tmp_path)

    assert call_count["n"] == 1, (
        "Bitwarden backend was called {} time(s); expected exactly 1 — "
        "the applied-home guard is broken.".format(call_count["n"])
    )

    # Source tracking still works after dedup.
    assert env_loader.get_secret_source("ANTHROPIC_API_KEY") == "bitwarden"

    # reset_secret_source_cache() forces a fresh pull on the next call.
    env_loader.reset_secret_source_cache()
    env_loader._apply_external_secret_sources(tmp_path)
    assert call_count["n"] == 2


def test_apply_external_secret_sources_fail_open_on_malformed_config(
    tmp_path, monkeypatch, capsys
):
    """[O] A malformed provider config (e.g. cache_ttl_seconds: abc) must NOT
    crash startup.  The bad coercion happens inside the registry loop's guarded
    iteration, so we log one warning and continue — load proceeds."""

    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    config_path = tmp_path / "config.yaml"
    # cache_ttl_seconds is non-numeric → float(...) would raise during coerce.
    config_path.write_text(
        "secrets:\n"
        "  bitwarden:\n"
        "    enabled: true\n"
        "    project_id: test-project\n"
        "    cache_ttl_seconds: not-a-number\n",
        encoding="utf-8",
    )

    from agent.secret_sources.bitwarden import FetchResult

    called = {"n": 0}

    def _fake_apply(**kwargs):
        called["n"] += 1
        # The coercion float("not-a-number") happens BEFORE this is reached.
        return FetchResult()

    import agent.secret_sources.bitwarden as bw_module
    monkeypatch.setattr(bw_module, "apply_bitwarden_secrets", _fake_apply)

    # Must not raise.
    env_loader._apply_external_secret_sources(tmp_path)

    # The applicator should NOT have produced a result (coercion failed first),
    # and a single warning should have been printed to stderr.
    captured = capsys.readouterr()
    assert "Bitwarden Secrets Manager" in captured.err
    assert "skipped" in captured.err
    assert called["n"] == 0


def test_apply_external_secret_sources_fail_open_continues_to_next_source(
    tmp_path, monkeypatch, capsys
):
    """[O]+[P] A failure in one source must not prevent the next source in the
    registry from being applied."""

    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "secrets:\n"
        "  bitwarden:\n"
        "    enabled: true\n"
        "    cache_ttl_seconds: not-a-number\n"
        "  protonpass:\n"
        "    enabled: true\n"
        "    env:\n"
        "      ANTHROPIC_API_KEY: 'pass://SHARE/ITEM/api_key'\n",
        encoding="utf-8",
    )

    from agent.secret_sources.protonpass import FetchResult as PPResult

    pp_called = {"n": 0}

    def _fake_pp(**kwargs):
        pp_called["n"] += 1
        return PPResult(
            secrets={"ANTHROPIC_API_KEY": "sk-ant"},
            applied=["ANTHROPIC_API_KEY"],
        )

    import agent.secret_sources.protonpass as pp_module
    monkeypatch.setattr(pp_module, "apply_protonpass_secrets", _fake_pp)

    env_loader._apply_external_secret_sources(tmp_path)

    # Bitwarden blew up on coercion, but Proton Pass still ran and recorded.
    assert pp_called["n"] == 1
    assert env_loader.get_secret_source("ANTHROPIC_API_KEY") == "protonpass"


def test_apply_external_secret_sources_import_error_warns(tmp_path, monkeypatch, capsys):
    """[Q] An ENABLED source whose module fails to import emits a one-line
    stderr warning instead of being silently swallowed."""

    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "secrets:\n"
        "  protonpass:\n"
        "    enabled: true\n"
        "    env:\n"
        "      ANTHROPIC_API_KEY: 'pass://SHARE/ITEM/api_key'\n",
        encoding="utf-8",
    )

    def _raise_import(cfg, home_path):
        raise ImportError("module gone")

    # Patch the registry applicator for protonpass to raise ImportError.
    new_registry = [
        (key, src, name, (_raise_import if key == "protonpass" else app))
        for (key, src, name, app) in env_loader._SECRET_SOURCE_REGISTRY
    ]
    monkeypatch.setattr(env_loader, "_SECRET_SOURCE_REGISTRY", new_registry)

    env_loader._apply_external_secret_sources(tmp_path)

    captured = capsys.readouterr()
    assert "Proton Pass" in captured.err
    assert "could not be imported" in captured.err


def test_apply_external_secret_sources_does_not_crash_on_protonpass_true(
    tmp_path, monkeypatch, capsys
):
    """`protonpass: true` (a bool, not a mapping) must NOT crash startup.

    The per-source config read + coerce now happens INSIDE the guarded boundary,
    so a non-mapping value is treated as "not enabled" rather than raising an
    AttributeError on ``True.get(...)``.
    """
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "secrets:\n"
        "  protonpass: true\n",
        encoding="utf-8",
    )

    called = {"n": 0}

    def _fake_pp(**_kwargs):  # pragma: no cover - must not be called
        called["n"] += 1
        from agent.secret_sources.protonpass import FetchResult
        return FetchResult()

    import agent.secret_sources.protonpass as pp_module
    monkeypatch.setattr(pp_module, "apply_protonpass_secrets", _fake_pp)

    # Must not raise.
    env_loader._apply_external_secret_sources(tmp_path)

    # A non-mapping protonpass config is treated as disabled — backend untouched.
    assert called["n"] == 0
    assert env_loader.get_secret_source("ANTHROPIC_API_KEY") is None


def test_apply_external_secret_sources_scalar_secrets_no_per_source_warnings(
    tmp_path, monkeypatch, capsys
):
    """C5: a non-Mapping top-level ``secrets: true`` must be normalized to ``{}``
    ONCE at the config boundary so the provider loop simply finds nothing to do.
    Previously the bool reached the loop, every ``secrets.get(cfg_key)`` raised
    ``'bool' object has no attribute 'get'``, and a per-source "skipped" warning
    printed ONCE PER SOURCE (two warnings).  Now: ZERO per-source warnings."""
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "secrets: true\n",
        encoding="utf-8",
    )

    bw_called = {"n": 0}
    pp_called = {"n": 0}

    def _fake_bw(**_kwargs):  # pragma: no cover - must not be called
        bw_called["n"] += 1
        from agent.secret_sources.bitwarden import FetchResult
        return FetchResult()

    def _fake_pp(**_kwargs):  # pragma: no cover - must not be called
        pp_called["n"] += 1
        from agent.secret_sources.protonpass import FetchResult
        return FetchResult()

    import agent.secret_sources.bitwarden as bw_module
    import agent.secret_sources.protonpass as pp_module
    monkeypatch.setattr(bw_module, "apply_bitwarden_secrets", _fake_bw)
    monkeypatch.setattr(pp_module, "apply_protonpass_secrets", _fake_pp)

    # Must not raise.
    env_loader._apply_external_secret_sources(tmp_path)

    # Both sources are simply disabled (nothing to read), backends untouched.
    assert bw_called["n"] == 0
    assert pp_called["n"] == 0
    captured = capsys.readouterr()
    # No per-source "skipped" warning for either source.
    assert "skipped" not in captured.err
    assert "Bitwarden Secrets Manager" not in captured.err
    assert "Proton Pass" not in captured.err


def test_protonpass_setup_never_accepts_token_via_argv():
    """[R] The setup subcommand must NOT expose a token flag on argv.

    A token on the command line leaks via shell history, ps, /proc/*/cmdline,
    and CI logs.  Assert the old `--service-token` flag is gone and no option
    named like a token is registered."""
    import argparse

    from hermes_cli import protonpass_secrets_cli

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    pp_parser = sub.add_parser("protonpass")
    protonpass_secrets_cli.register_protonpass_cli(pp_parser)

    # The flag must be rejected (no longer a known option).
    with pytest.raises(SystemExit):
        parser.parse_args(["protonpass", "setup", "--service-token", "pst_secret"])

    # And no registered option string should look like a raw-token flag.
    def _walk_options(p):
        opts = []
        for action in p._actions:
            opts.extend(action.option_strings)
            if isinstance(action, argparse._SubParsersAction):
                for choice in action.choices.values():
                    opts.extend(_walk_options(choice))
        return opts

    all_opts = _walk_options(parser)
    assert "--service-token" not in all_opts
    assert not any("token" in o and o != "--token-env" for o in all_opts)
