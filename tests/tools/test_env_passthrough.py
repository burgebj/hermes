"""Tests for tools.env_passthrough — skill and config env var passthrough."""

import os
import pytest
import yaml

import tools.env_passthrough as _ep_mod
from tools.env_passthrough import (
    clear_env_passthrough,
    get_all_passthrough,
    is_env_passthrough,
    register_env_passthrough,
)


@pytest.fixture(autouse=True)
def _clean_passthrough():
    """Ensure a clean passthrough state for every test."""
    clear_env_passthrough()
    _ep_mod._config_passthrough = None
    yield
    clear_env_passthrough()
    _ep_mod._config_passthrough = None


class TestSkillScopedPassthrough:
    def test_register_and_check(self):
        assert not is_env_passthrough("TENOR_API_KEY")
        register_env_passthrough(["TENOR_API_KEY"])
        assert is_env_passthrough("TENOR_API_KEY")

    def test_register_multiple(self):
        register_env_passthrough(["FOO_TOKEN", "BAR_SECRET"])
        assert is_env_passthrough("FOO_TOKEN")
        assert is_env_passthrough("BAR_SECRET")
        assert not is_env_passthrough("OTHER_KEY")

    def test_clear(self):
        register_env_passthrough(["TENOR_API_KEY"])
        assert is_env_passthrough("TENOR_API_KEY")
        clear_env_passthrough()
        assert not is_env_passthrough("TENOR_API_KEY")

    def test_get_all(self):
        register_env_passthrough(["A_KEY", "B_TOKEN"])
        result = get_all_passthrough()
        assert "A_KEY" in result
        assert "B_TOKEN" in result

    def test_strips_whitespace(self):
        register_env_passthrough(["  SPACED_KEY  "])
        assert is_env_passthrough("SPACED_KEY")

    def test_skips_empty(self):
        register_env_passthrough(["", "  ", "VALID_KEY"])
        assert is_env_passthrough("VALID_KEY")
        assert not is_env_passthrough("")


class TestConfigPassthrough:
    def test_reads_from_config(self, tmp_path, monkeypatch):
        config = {"terminal": {"env_passthrough": ["MY_CUSTOM_KEY", "ANOTHER_TOKEN"]}}
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(config))
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        _ep_mod._config_passthrough = None

        assert is_env_passthrough("MY_CUSTOM_KEY")
        assert is_env_passthrough("ANOTHER_TOKEN")
        assert not is_env_passthrough("UNRELATED_VAR")

    def test_empty_config(self, tmp_path, monkeypatch):
        config = {"terminal": {"env_passthrough": []}}
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(config))
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        _ep_mod._config_passthrough = None

        assert not is_env_passthrough("ANYTHING")

    def test_missing_config_key(self, tmp_path, monkeypatch):
        config = {"terminal": {"backend": "local"}}
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(config))
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        _ep_mod._config_passthrough = None

        assert not is_env_passthrough("ANYTHING")

    def test_no_config_file(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        _ep_mod._config_passthrough = None

        assert not is_env_passthrough("ANYTHING")

    def test_union_of_skill_and_config(self, tmp_path, monkeypatch):
        config = {"terminal": {"env_passthrough": ["CONFIG_KEY"]}}
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(config))
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        _ep_mod._config_passthrough = None

        register_env_passthrough(["SKILL_KEY"])
        all_pt = get_all_passthrough()
        assert "CONFIG_KEY" in all_pt
        assert "SKILL_KEY" in all_pt


class TestExecuteCodeIntegration:
    """Verify that the passthrough is checked in execute_code's env filtering."""

    def test_secret_substring_blocked_by_default(self):
        """TENOR_API_KEY should be blocked without passthrough."""
        _SAFE_ENV_PREFIXES = ("PATH", "HOME", "USER", "LANG", "LC_", "TERM",
                              "TMPDIR", "TMP", "TEMP", "SHELL", "LOGNAME",
                              "XDG_", "PYTHONPATH", "VIRTUAL_ENV", "CONDA")
        _SECRET_SUBSTRINGS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL",
                              "PASSWD", "AUTH")

        test_env = {"PATH": "/usr/bin", "TENOR_API_KEY": "test123", "HOME": "/home/user"}
        child_env = {}
        for k, v in test_env.items():
            if is_env_passthrough(k):
                child_env[k] = v
                continue
            if any(s in k.upper() for s in _SECRET_SUBSTRINGS):
                continue
            if any(k.startswith(p) for p in _SAFE_ENV_PREFIXES):
                child_env[k] = v

        assert "PATH" in child_env
        assert "HOME" in child_env
        assert "TENOR_API_KEY" not in child_env

    def test_passthrough_allows_secret_through(self):
        """TENOR_API_KEY should pass through when registered."""
        _SAFE_ENV_PREFIXES = ("PATH", "HOME", "USER", "LANG", "LC_", "TERM",
                              "TMPDIR", "TMP", "TEMP", "SHELL", "LOGNAME",
                              "XDG_", "PYTHONPATH", "VIRTUAL_ENV", "CONDA")
        _SECRET_SUBSTRINGS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL",
                              "PASSWD", "AUTH")

        register_env_passthrough(["TENOR_API_KEY"])

        test_env = {"PATH": "/usr/bin", "TENOR_API_KEY": "test123", "HOME": "/home/user"}
        child_env = {}
        for k, v in test_env.items():
            if is_env_passthrough(k):
                child_env[k] = v
                continue
            if any(s in k.upper() for s in _SECRET_SUBSTRINGS):
                continue
            if any(k.startswith(p) for p in _SAFE_ENV_PREFIXES):
                child_env[k] = v

        assert "PATH" in child_env
        assert "HOME" in child_env
        assert "TENOR_API_KEY" in child_env
        assert child_env["TENOR_API_KEY"] == "test123"


class TestTerminalIntegration:
    """Verify that the passthrough is checked in terminal's env sanitizers."""

    def test_blocklisted_var_blocked_by_default(self):
        from tools.environments.local import _sanitize_subprocess_env, _HERMES_PROVIDER_ENV_BLOCKLIST

        # Pick a var we know is in the blocklist
        blocked_var = next(iter(_HERMES_PROVIDER_ENV_BLOCKLIST))
        env = {blocked_var: "secret_value", "PATH": "/usr/bin"}
        result = _sanitize_subprocess_env(env)
        assert blocked_var not in result
        assert "PATH" in result

    def test_passthrough_cannot_override_provider_blocklist(self):
        """GHSA-rhgp-j443-p4rf: register_env_passthrough must NOT accept
        Hermes provider credentials — that was the bypass where a skill
        could declare ANTHROPIC_TOKEN / OPENAI_API_KEY as passthrough and
        defeat the execute_code sandbox scrubbing."""
        from tools.environments.local import (
            _sanitize_subprocess_env,
            _HERMES_PROVIDER_ENV_BLOCKLIST,
        )

        blocked_var = next(iter(_HERMES_PROVIDER_ENV_BLOCKLIST))
        # Attempt to register — must be silently refused (logged warning).
        register_env_passthrough([blocked_var])

        # is_env_passthrough must NOT report it as allowed
        assert not is_env_passthrough(blocked_var)

        # Sanitizer still strips the var from subprocess env
        env = {blocked_var: "secret_value", "PATH": "/usr/bin"}
        result = _sanitize_subprocess_env(env)
        assert blocked_var not in result
        assert "PATH" in result

    def test_make_run_env_blocklist_override_rejected(self):
        """_make_run_env must NOT expose a blocklisted var to subprocess env
        even after a skill attempts to register it via passthrough."""
        from tools.environments.local import (
            _make_run_env,
            _HERMES_PROVIDER_ENV_BLOCKLIST,
        )

        blocked_var = next(iter(_HERMES_PROVIDER_ENV_BLOCKLIST))
        os.environ[blocked_var] = "secret_value"
        try:
            # Without passthrough — blocked
            result_before = _make_run_env({})
            assert blocked_var not in result_before

            # Skill tries to register it — must be refused, so still blocked
            register_env_passthrough([blocked_var])
            result_after = _make_run_env({})
            assert blocked_var not in result_after
        finally:
            os.environ.pop(blocked_var, None)

    def test_non_hermes_api_key_still_registerable(self):
        """Third-party API keys (TENOR_API_KEY, NOTION_TOKEN, etc.) are NOT
        Hermes provider credentials and must still pass through — skills
        that legitimately wrap third-party APIs must keep working."""
        # TENOR_API_KEY is a real example — used by the gif-search skill
        register_env_passthrough(["TENOR_API_KEY"])
        assert is_env_passthrough("TENOR_API_KEY")

        # Arbitrary skill-specific var
        register_env_passthrough(["MY_SKILL_CUSTOM_CONFIG"])
        assert is_env_passthrough("MY_SKILL_CUSTOM_CONFIG")


class TestFailClosedOnImportError:
    """Regression tests for issue #37950.

    _is_hermes_provider_credential() must fail CLOSED when
    tools.environments.local cannot be imported.  The original
    ``except Exception: return False`` made every name appear to be a
    non-credential, letting a skill register ANTHROPIC_TOKEN / OPENAI_API_KEY
    as passthrough and receive the key inside execute_code.

    Why: verifies the hardcoded fallback blocklist (_FALLBACK_PROVIDER_ENV_BLOCKLIST)
    correctly protects well-known provider credentials even when the dynamic
    blocklist is unavailable.
    Test approach: inject a MetaPathFinder that raises ImportError for
    tools.environments.local, then exercise the full registration/passthrough
    path to confirm fail-closed behavior is maintained end-to-end.
    """

    def test_is_hermes_provider_credential_fails_closed_on_import_error(
        self, monkeypatch
    ):
        """_is_hermes_provider_credential must return True for well-known
        Hermes credentials even when tools.environments.local cannot be
        imported — proving fail-closed behavior (fixes #37950).

        Why: the old ``except Exception: return False`` was fail-open.
        What: blocks import of tools.environments.local, then asserts the
        function still recognizes ANTHROPIC_TOKEN and OPENAI_API_KEY as
        provider credentials.
        Test: monkeypatch sys.modules to simulate import failure, call
        _is_hermes_provider_credential, assert return value is True.
        """
        import importlib.abc
        import sys

        import tools.env_passthrough as ep_module

        class _BlockLocalFinder(importlib.abc.MetaPathFinder):
            """Raise ImportError for tools.environments.local to simulate failure."""

            def find_spec(self, fullname, path, target=None):
                if fullname == "tools.environments.local":
                    raise ImportError(
                        "Simulated import failure for tools.environments.local"
                    )
                return None

        import importlib as _il

        finder = _BlockLocalFinder()
        sys.meta_path.insert(0, finder)
        # Remove the already-imported module so the next import triggers the finder.
        monkeypatch.delitem(sys.modules, "tools.environments.local", raising=False)

        try:
            # Reload the module under test so the import inside
            # _is_hermes_provider_credential runs fresh against the blocker.
            _il.reload(ep_module)

            # Well-known Hermes provider credentials must be recognized even
            # without the full dynamic blocklist.
            assert ep_module._is_hermes_provider_credential(
                "ANTHROPIC_TOKEN"
            ), "ANTHROPIC_TOKEN must be recognized as a provider credential even on import failure"
            assert ep_module._is_hermes_provider_credential(
                "OPENAI_API_KEY"
            ), "OPENAI_API_KEY must be recognized as a provider credential even on import failure"

            # Third-party keys are NOT in the fallback blocklist and must still
            # be registerable (skills wrapping third-party APIs must keep working).
            assert not ep_module._is_hermes_provider_credential(
                "TENOR_API_KEY"
            ), "TENOR_API_KEY must NOT be blocked — it is a third-party key, not a Hermes credential"

        finally:
            sys.meta_path.remove(finder)
            # Restore the real module so other tests see clean state.
            _il.reload(ep_module)

    def test_register_env_passthrough_refuses_credential_on_import_error(
        self, monkeypatch
    ):
        """register_env_passthrough must refuse a Hermes provider credential
        even when tools.environments.local cannot be imported (fail-closed).

        Why: if _is_hermes_provider_credential fails open, a skill can call
        register_env_passthrough(["ANTHROPIC_TOKEN"]) and the key ends up in
        the sandbox allowlist, bypassing the execute_code scrub.
        Test: simulate broken import, attempt registration, assert the var is
        not in the allowlist and does not appear in a sanitized subprocess env.
        """
        import importlib.abc
        import sys

        import tools.env_passthrough as ep_module

        class _BlockLocalFinder(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path, target=None):
                if fullname == "tools.environments.local":
                    raise ImportError(
                        "Simulated import failure for tools.environments.local"
                    )
                return None

        import importlib as _il

        finder = _BlockLocalFinder()
        sys.meta_path.insert(0, finder)
        monkeypatch.delitem(sys.modules, "tools.environments.local", raising=False)

        try:
            _il.reload(ep_module)
            ep_module.clear_env_passthrough()
            ep_module._config_passthrough = None

            # Attempt to register a Hermes provider credential.
            ep_module.register_env_passthrough(["ANTHROPIC_TOKEN", "TENOR_API_KEY"])

            # ANTHROPIC_TOKEN must have been silently refused.
            assert not ep_module.is_env_passthrough(
                "ANTHROPIC_TOKEN"
            ), "ANTHROPIC_TOKEN must not be in the allowlist even when local.py import fails"

            # TENOR_API_KEY (third-party) must still be allowed through.
            assert ep_module.is_env_passthrough(
                "TENOR_API_KEY"
            ), "TENOR_API_KEY (non-Hermes credential) must still be registerable"

        finally:
            sys.meta_path.remove(finder)
            ep_module.clear_env_passthrough()
            ep_module._config_passthrough = None
            _il.reload(ep_module)


class TestFallbackBlocklistDriftGuard:
    """Regression guard: _FALLBACK_PROVIDER_ENV_BLOCKLIST must be a superset
    of every hardcoded credential name in _build_provider_env_blocklist().

    Why: the fallback is the last line of defence when tools.environments.local
    cannot be imported.  If _build_provider_env_blocklist gains a new hardcoded
    entry and _FALLBACK_PROVIDER_ENV_BLOCKLIST is not updated, the credential
    leaks the next time the dynamic import fails — exactly the class of defect
    fixed in #37950 and hardened here.

    Approach: parse the AST of tools/environments/local.py and extract every
    string constant from the ``blocked.update({...})`` call in
    ``_build_provider_env_blocklist``.  That set is the authoritative hardcoded
    subset.  The test asserts that _FALLBACK_PROVIDER_ENV_BLOCKLIST contains
    all of them.  Adding a new string to the blocked.update() call in local.py
    without updating the fallback will cause this test to fail.

    Test: import both modules, extract the hardcoded names via AST, assert
    _FALLBACK_PROVIDER_ENV_BLOCKLIST is a superset.
    """

    def _extract_hardcoded_blocklist_names(self) -> frozenset[str]:
        """Parse local.py AST and return every string literal in the
        ``blocked.update({...})`` call inside ``_build_provider_env_blocklist``.

        Why: AST parsing is the only way to reliably extract the static set
        without executing the function (which performs dynamic imports that may
        add extra names).
        What: walks the function body, finds the blocked.update(set_literal)
        call, and collects all Constant string nodes from it.
        Test: returns the set and the caller asserts subset membership.
        """
        import ast
        import pathlib

        local_py = (
            pathlib.Path(__file__).parent.parent.parent
            / "tools" / "environments" / "local.py"
        )
        tree = ast.parse(local_py.read_text())

        hardcoded: set[str] = set()
        for node in ast.walk(tree):
            # Find the function definition
            if not (isinstance(node, ast.FunctionDef) and node.name == "_build_provider_env_blocklist"):
                continue
            # Walk statements inside the function for blocked.update({...}) calls
            for stmt in ast.walk(node):
                if not isinstance(stmt, ast.Expr):
                    continue
                call = stmt.value
                if not (
                    isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Attribute)
                    and call.func.attr == "update"
                    and isinstance(call.func.value, ast.Name)
                    and call.func.value.id == "blocked"
                ):
                    continue
                # The argument to blocked.update() should be a set literal
                if not call.args:
                    continue
                arg = call.args[0]
                if not isinstance(arg, ast.Set):
                    continue
                for elt in arg.elts:
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                        hardcoded.add(elt.value)
        return frozenset(hardcoded)

    def test_fallback_contains_all_hardcoded_names(self):
        """_FALLBACK_PROVIDER_ENV_BLOCKLIST must be a superset of the hardcoded
        string literals in _build_provider_env_blocklist()'s blocked.update() call.

        Failure here means a new credential was added to local.py's static block
        but the fallback was not updated — re-opening the leak fixed in #37950.
        """
        from tools.env_passthrough import _FALLBACK_PROVIDER_ENV_BLOCKLIST

        hardcoded = self._extract_hardcoded_blocklist_names()
        assert hardcoded, (
            "AST extraction returned empty set — the parser may be broken or "
            "_build_provider_env_blocklist no longer has a blocked.update({...}) call"
        )

        missing = hardcoded - _FALLBACK_PROVIDER_ENV_BLOCKLIST
        assert not missing, (
            f"_FALLBACK_PROVIDER_ENV_BLOCKLIST is missing {len(missing)} name(s) "
            f"that are in _build_provider_env_blocklist()'s hardcoded block:\n"
            + "\n".join(f"  {name!r}" for name in sorted(missing))
            + "\n\nAdd them to _FALLBACK_PROVIDER_ENV_BLOCKLIST in tools/env_passthrough.py."
        )

    def test_fallback_contains_review_specified_credentials(self):
        """Explicitly assert the credentials named in the adversarial review
        are present in _FALLBACK_PROVIDER_ENV_BLOCKLIST.

        Why: belt-and-suspenders check so the specific CVE-class credentials
        are ALWAYS covered even if the AST extraction approach ever misses them.
        Test: direct membership assertions for each named credential.
        """
        from tools.env_passthrough import _FALLBACK_PROVIDER_ENV_BLOCKLIST

        # These are the specific names called out as missing by the review.
        required = {
            "ANTHROPIC_API_KEY",
            "TELEGRAM_BOT_TOKEN",
            "DISCORD_BOT_TOKEN",
            "SLACK_BOT_TOKEN",
            "GITHUB_TOKEN",
            "SUDO_PASSWORD",
            # Already present before, but assert for regression safety
            "ANTHROPIC_TOKEN",
            "OPENAI_API_KEY",
            "GH_TOKEN",
            "HERMES_DASHBOARD_SESSION_TOKEN",
        }
        missing = required - _FALLBACK_PROVIDER_ENV_BLOCKLIST
        assert not missing, (
            f"Critical credentials missing from _FALLBACK_PROVIDER_ENV_BLOCKLIST: "
            f"{sorted(missing)}"
        )
