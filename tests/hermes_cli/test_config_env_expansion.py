"""Tests for runtime reference substitution in config.yaml values."""

import base64
import os

import pytest
import yaml
from hermes_cli.config import _expand_env_vars, load_config, save_config


class TestExpandEnvVars:
    def test_simple_substitution(self):
        with pytest.MonkeyPatch().context() as mp:
            mp.setenv("MY_KEY", "secret123")
            assert _expand_env_vars("${MY_KEY}") == "secret123"

    def test_missing_var_kept_verbatim(self):
        with pytest.MonkeyPatch().context() as mp:
            mp.delenv("UNDEFINED_VAR_XYZ", raising=False)
            assert _expand_env_vars("${UNDEFINED_VAR_XYZ}") == "${UNDEFINED_VAR_XYZ}"

    def test_no_placeholder_unchanged(self):
        assert _expand_env_vars("plain-value") == "plain-value"

    def test_dict_recursive(self):
        with pytest.MonkeyPatch().context() as mp:
            mp.setenv("TOKEN", "tok-abc")
            result = _expand_env_vars({"key": "${TOKEN}", "other": "literal"})
            assert result == {"key": "tok-abc", "other": "literal"}

    def test_nested_dict(self):
        with pytest.MonkeyPatch().context() as mp:
            mp.setenv("API_KEY", "sk-xyz")
            result = _expand_env_vars({"model": {"api_key": "${API_KEY}"}})
            assert result["model"]["api_key"] == "sk-xyz"

    def test_list_items(self):
        with pytest.MonkeyPatch().context() as mp:
            mp.setenv("VAL", "hello")
            result = _expand_env_vars(["${VAL}", "literal", 42])
            assert result == ["hello", "literal", 42]

    def test_non_string_values_untouched(self):
        assert _expand_env_vars(42) == 42
        assert _expand_env_vars(3.14) == 3.14
        assert _expand_env_vars(True) is True
        assert _expand_env_vars(None) is None

    def test_multiple_placeholders_in_one_string(self):
        with pytest.MonkeyPatch().context() as mp:
            mp.setenv("HOST", "localhost")
            mp.setenv("PORT", "5432")
            assert _expand_env_vars("${HOST}:${PORT}") == "localhost:5432"

    def test_dict_keys_not_expanded(self):
        with pytest.MonkeyPatch().context() as mp:
            mp.setenv("KEY", "value")
            result = _expand_env_vars({"${KEY}": "no-expand-key"})
            assert "${KEY}" in result


class TestLoadConfigExpansion:
    def test_load_config_expands_env_vars(self, tmp_path, monkeypatch):
        config_yaml = (
            "model:\n"
            "  api_key: ${GOOGLE_API_KEY}\n"
            "platforms:\n"
            "  telegram:\n"
            "    token: ${TELEGRAM_BOT_TOKEN}\n"
            "plain: no-substitution\n"
        )
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_yaml)

        monkeypatch.setenv("GOOGLE_API_KEY", "gsk-test-key")
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "1234567:ABC-token")
        # Patch the imported function's own globals. Other tests may reload
        # hermes_cli.config, making string-target monkeypatches hit a different
        # module object than this collection-time imported load_config().
        monkeypatch.setitem(load_config.__globals__, "get_config_path", lambda: config_file)

        config = load_config()

        assert config["model"]["api_key"] == "gsk-test-key"
        assert config["platforms"]["telegram"]["token"] == "1234567:ABC-token"
        assert config["plain"] == "no-substitution"

    def test_load_config_unresolved_kept_verbatim(self, tmp_path, monkeypatch):
        config_yaml = "model:\n  api_key: ${NOT_SET_XYZ_123}\n"
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_yaml)

        monkeypatch.delenv("NOT_SET_XYZ_123", raising=False)
        monkeypatch.setitem(load_config.__globals__, "get_config_path", lambda: config_file)

        config = load_config()

        assert config["model"]["api_key"] == "${NOT_SET_XYZ_123}"


class TestSecretFileRefs:
    def test_expand_config_refs_reads_raw_secret_file(self, tmp_path):
        from hermes_cli.config import _expand_config_refs

        secret_file = tmp_path / "api-key"
        secret_file.write_text("sk-secret\n", encoding="utf-8")

        result = _expand_config_refs({"api_key": {"__secret_file": str(secret_file)}})

        assert result == {"api_key": "sk-secret"}

    def test_expand_config_refs_reads_secret_path_with_env_var(self, tmp_path, monkeypatch):
        from hermes_cli.config import _expand_config_refs

        secret_dir = tmp_path / "secrets"
        secret_dir.mkdir()
        secret_file = secret_dir / "token"
        secret_file.write_text("tok-secret", encoding="utf-8")
        monkeypatch.setenv("SECRET_DIR_FOR_TEST", str(secret_dir))

        result = _expand_config_refs(
            {"token": {"__secret_file": "${SECRET_DIR_FOR_TEST}/token"}}
        )

        assert result["token"] == "tok-secret"

    def test_expand_config_refs_base64_encodes_secret_file_bytes(self, tmp_path):
        from hermes_cli.config import _expand_config_refs

        secret_file = tmp_path / "binary-secret"
        secret_bytes = b"not utf8: \xff\x00"
        secret_file.write_bytes(secret_bytes)

        result = _expand_config_refs(
            {
                "basic_auth": {
                    "__secret_file": str(secret_file),
                    "__secret_encoding": "base64",
                }
            }
        )

        assert result["basic_auth"] == base64.b64encode(secret_bytes).decode("ascii")

    def test_expand_config_refs_base64_strips_trailing_newlines(self, tmp_path):
        from hermes_cli.config import _expand_config_refs

        secret_file = tmp_path / "basic-auth"
        secret_file.write_bytes(b"user:pass\r\n")

        result = _expand_config_refs(
            {
                "basic_auth": {
                    "__secret_file": str(secret_file),
                    "__secret_encoding": "base64",
                }
            }
        )

        assert result["basic_auth"] == base64.b64encode(b"user:pass").decode("ascii")

    def test_expand_config_refs_missing_secret_file_fails_loudly(self, tmp_path):
        from hermes_cli.config import _expand_config_refs

        missing = tmp_path / "missing-secret"

        with pytest.raises(FileNotFoundError):
            _expand_config_refs({"api_key": {"__secret_file": str(missing)}})

    def test_expand_config_refs_unknown_secret_encoding_fails_loudly(self, tmp_path):
        from hermes_cli.config import _expand_config_refs

        secret_file = tmp_path / "api-key"
        secret_file.write_text("sk-secret", encoding="utf-8")

        with pytest.raises(ValueError, match="Unsupported __secret_encoding"):
            _expand_config_refs(
                {
                    "api_key": {
                        "__secret_file": str(secret_file),
                        "__secret_encoding": "rot13",
                    }
                }
            )

    def test_load_config_resolves_secret_file_refs(self, tmp_path, monkeypatch):
        secret_file = tmp_path / "api-key"
        secret_file.write_text("sk-secret\n", encoding="utf-8")
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "model:\n"
            "  api_key:\n"
            f"    __secret_file: {secret_file}\n"
        )

        monkeypatch.setitem(load_config.__globals__, "get_config_path", lambda: config_file)

        config = load_config()

        assert config["model"]["api_key"] == "sk-secret"

    def test_load_config_cache_invalidates_when_secret_file_changes(self, tmp_path, monkeypatch):
        secret_file = tmp_path / "api-key"
        secret_file.write_text("first-secret", encoding="utf-8")
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "model:\n"
            "  api_key:\n"
            f"    __secret_file: {secret_file}\n"
        )
        monkeypatch.setitem(load_config.__globals__, "get_config_path", lambda: config_file)

        first = load_config()
        secret_file.write_text("second-secret", encoding="utf-8")
        os.utime(secret_file, None)
        second = load_config()

        assert first["model"]["api_key"] == "first-secret"
        assert second["model"]["api_key"] == "second-secret"

    def test_save_config_preserves_secret_file_ref_instead_of_writing_plaintext(
        self,
        tmp_path,
        monkeypatch,
    ):
        secret_file = tmp_path / "api-key"
        secret_file.write_text("sk-secret", encoding="utf-8")
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "model:\n"
            "  api_key:\n"
            f"    __secret_file: {secret_file}\n"
            "plain: old\n"
        )
        monkeypatch.setitem(load_config.__globals__, "get_config_path", lambda: config_file)

        config = load_config()
        assert config["model"]["api_key"] == "sk-secret"
        config["plain"] = "new"
        save_config(config)

        saved_text = config_file.read_text(encoding="utf-8")
        saved = yaml.safe_load(saved_text)
        assert saved["model"]["api_key"] == {"__secret_file": str(secret_file)}
        assert "sk-secret" not in saved_text
        assert saved["plain"] == "new"


class TestLoadCliConfigExpansion:
    """Verify that load_cli_config() also expands ${VAR} references."""

    def test_cli_config_expands_auxiliary_api_key(self, tmp_path, monkeypatch):
        config_yaml = (
            "auxiliary:\n"
            "  vision:\n"
            "    api_key: ${TEST_VISION_KEY_XYZ}\n"
        )
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_yaml)

        monkeypatch.setenv("TEST_VISION_KEY_XYZ", "vis-key-123")
        # Patch the hermes home so load_cli_config finds our test config
        monkeypatch.setattr("cli._hermes_home", tmp_path)

        from cli import load_cli_config
        config = load_cli_config()

        assert config["auxiliary"]["vision"]["api_key"] == "vis-key-123"

    def test_cli_config_unresolved_kept_verbatim(self, tmp_path, monkeypatch):
        config_yaml = (
            "auxiliary:\n"
            "  vision:\n"
            "    api_key: ${UNSET_CLI_VAR_ABC}\n"
        )
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_yaml)

        monkeypatch.delenv("UNSET_CLI_VAR_ABC", raising=False)
        monkeypatch.setattr("cli._hermes_home", tmp_path)

        from cli import load_cli_config
        config = load_cli_config()

        assert config["auxiliary"]["vision"]["api_key"] == "${UNSET_CLI_VAR_ABC}"
