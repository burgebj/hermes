"""Tests for credential exclusion during profile export.

Profile exports should NEVER include auth.json, .env, private keys, or the
timestamped config/env *backups* Hermes writes during normal operation
(``config.yaml.bak.<ts>``, ``config.yaml.bak-pre-migrate-xai-<ts>``,
``.env.bak-<...>``).  Users share exported profiles; leaking credentials or a
credential backup in the archive is a security issue.

Both the default-profile (``~/.hermes``) and named-profile export paths route
through :func:`_is_sensitive_export_name`, so these tests cover both.
"""

import tarfile

import pytest

from hermes_cli.profiles import (
    export_profile,
    _DEFAULT_EXPORT_EXCLUDE_ROOT,
    _is_sensitive_export_name,
)


class TestIsSensitiveExportName:
    """Unit coverage for the shared sensitive-name classifier."""

    @pytest.mark.parametrize(
        "name",
        [
            # Exact credential basenames
            ".env",
            "auth.json",
            "auth.lock",
            # dotenv variants (non-template)
            ".env.local",
            ".env.production",
            ".env.bak-kiro-20260529115545",
            ".env.bak-gemini-embedding-20260506_004415",
            # config backups (real-world shapes seen on disk)
            "config.yaml.bak.20260526_130938",
            "config.yaml.bak-pre-migrate-xai-20260410-040915",
            "config.yaml.bak-provider-key-cleanup-20260506_013334",
            "config.yml.bak.20260101_000000",
            "config.yaml.bak-kiro-context-20260529140131",
            # auth backups
            "auth.json.bak",
            "auth.json.20260101",
            # private keys / keystores
            "server.pem",
            "id_rsa.key",
            "store.p12",
            "cert.pfx",
            "release.keystore",
            "release.jks",
            # credential-/token-looking containers
            "credentials.json",
            "client_secret.json",
            "access_token.txt",
            "refresh-tokens.yaml",
            "api_key.txt",
            "api-keys.ini",
            "secrets.yaml",
            # no-extension credential names
            "credentials",
            "id_rsa",
        ],
    )
    def test_sensitive_names_flagged(self, name):
        assert _is_sensitive_export_name(name) is True

    @pytest.mark.parametrize(
        "name",
        [
            # Ordinary profile files
            "config.yaml",
            "config.yml",
            "SOUL.md",
            "MEMORY.md",
            "USER.md",
            "profile.yaml",
            "distribution.yaml",
            "README.md",
            # dotenv templates are safe to ship
            ".env.example",
            ".env.sample",
            ".env.template",
            ".env.dist",
            # token/secret substrings that are NOT credentials
            "tokenizer.json",
            "token_count.md",
            "secret-santa.md",
            "my-secrets-notes.md",  # .md is not a credential container
            "apikeys-guide.md",
            "backup-notes.md",
            # .bak that is not a config/auth/env backup
            "notes.txt.bak",
            "draft.md.bak",
        ],
    )
    def test_safe_names_not_flagged(self, name):
        assert _is_sensitive_export_name(name) is False

    def test_case_insensitive(self):
        assert _is_sensitive_export_name("Config.YAML.BAK.20260101_000000") is True
        assert _is_sensitive_export_name("AUTH.JSON") is True
        assert _is_sensitive_export_name(".ENV.LOCAL") is True


class TestCredentialExclusion:

    def test_auth_json_in_default_exclude_set(self):
        """auth.json must be in the default export exclusion set."""
        assert "auth.json" in _DEFAULT_EXPORT_EXCLUDE_ROOT

    def test_dotenv_in_default_exclude_set(self):
        """.env must be in the default export exclusion set."""
        assert ".env" in _DEFAULT_EXPORT_EXCLUDE_ROOT

    def test_named_profile_export_excludes_auth(self, tmp_path, monkeypatch):
        """Named profile export must not contain auth.json or .env."""
        profiles_root = tmp_path / "profiles"
        profile_dir = profiles_root / "testprofile"
        profile_dir.mkdir(parents=True)

        # Create a profile with credentials
        (profile_dir / "config.yaml").write_text("model: gpt-4\n")
        (profile_dir / "auth.json").write_text('{"tokens": {"access": "sk-secret"}}')
        (profile_dir / ".env").write_text("OPENROUTER_API_KEY=x\n")
        (profile_dir / "SOUL.md").write_text("I am helpful.\n")
        (profile_dir / "memories").mkdir()
        (profile_dir / "memories" / "MEMORY.md").write_text("# Memories\n")

        monkeypatch.setattr("hermes_cli.profiles._get_profiles_root", lambda: profiles_root)
        monkeypatch.setattr("hermes_cli.profiles.get_profile_dir", lambda n: profile_dir)
        monkeypatch.setattr("hermes_cli.profiles.validate_profile_name", lambda n: None)

        output = tmp_path / "export.tar.gz"
        result = export_profile("testprofile", str(output))

        # Check archive contents
        with tarfile.open(result, "r:gz") as tf:
            names = tf.getnames()

        assert any("config.yaml" in n for n in names), "config.yaml should be in export"
        assert any("SOUL.md" in n for n in names), "SOUL.md should be in export"
        assert not any("auth.json" in n for n in names), "auth.json must NOT be in export"
        assert not any(n.endswith("/.env") or n == ".env" for n in names), \
            ".env must NOT be in export"

    def test_named_profile_export_excludes_backups_and_secrets(self, tmp_path, monkeypatch):
        """Named profile export must drop config/env/auth backups and secrets,
        while keeping ordinary profile files (including .env.example)."""
        profiles_root = tmp_path / "profiles"
        profile_dir = profiles_root / "testprofile"
        profile_dir.mkdir(parents=True)

        # Files that MUST be excluded
        sensitive = [
            ".env",
            ".env.bak-kiro-20260529115545",
            ".env.local",
            "auth.json",
            "auth.lock",
            "auth.json.bak",
            "config.yaml.bak.20260526_130938",
            "config.yaml.bak-pre-migrate-xai-20260410-040915",
            "credentials.json",
            "client_secret.json",
            "server.pem",
        ]
        # Files that MUST survive
        kept = [
            "config.yaml",
            "SOUL.md",
            "profile.yaml",
            ".env.example",
            "README.md",
        ]
        for name in sensitive:
            (profile_dir / name).write_text("SENSITIVE\n")
        for name in kept:
            (profile_dir / name).write_text("ok\n")

        # A nested backup deep in a subdir must also be dropped.
        nested = profile_dir / "skins" / "old"
        nested.mkdir(parents=True)
        (nested / "config.yaml.bak.20260101_000000").write_text("SENSITIVE\n")
        (nested / "theme.json").write_text("{}\n")

        monkeypatch.setattr("hermes_cli.profiles._get_profiles_root", lambda: profiles_root)
        monkeypatch.setattr("hermes_cli.profiles.get_profile_dir", lambda n: profile_dir)
        monkeypatch.setattr("hermes_cli.profiles.validate_profile_name", lambda n: None)

        output = tmp_path / "export.tar.gz"
        result = export_profile("testprofile", str(output))

        with tarfile.open(result, "r:gz") as tf:
            basenames = {n.rsplit("/", 1)[-1] for n in tf.getnames()}

        for name in sensitive:
            assert name not in basenames, f"{name} must NOT be in export"
        for name in kept:
            assert name in basenames, f"{name} should be in export"
        # Nested backup excluded, nested ordinary file kept.
        assert "theme.json" in basenames
        # The only config.yaml.bak* we added are sensitive — none should survive.
        assert not any(b.startswith("config.yaml.bak") for b in basenames)

    def test_default_profile_export_excludes_backups_and_secrets(self, tmp_path, monkeypatch):
        """Default-profile (~/.hermes) export must drop credentials and the
        config/env backups Hermes writes, while keeping ordinary files."""
        # The default profile IS the hermes home directory itself.
        default_home = tmp_path / ".hermes"
        default_home.mkdir(parents=True)

        sensitive = [
            ".env",
            ".env.bak-kiro-20260529115545",
            "auth.json",
            "auth.lock",
            "config.yaml.bak.20260526_130938",
            "config.yaml.bak-pre-migrate-xai-20260410-040915",
            "private.pem",
        ]
        kept = [
            "config.yaml",
            "SOUL.md",
            ".env.example",
        ]
        for name in sensitive:
            (default_home / name).write_text("SENSITIVE\n")
        for name in kept:
            (default_home / name).write_text("ok\n")
        (default_home / "memories").mkdir()
        (default_home / "memories" / "MEMORY.md").write_text("# Memories\n")

        monkeypatch.setattr(
            "hermes_cli.profiles._get_default_hermes_home", lambda: default_home
        )
        monkeypatch.setattr("hermes_cli.profiles.get_profile_dir", lambda n: default_home)
        monkeypatch.setattr("hermes_cli.profiles.validate_profile_name", lambda n: None)

        output = tmp_path / "export.tar.gz"
        result = export_profile("default", str(output))

        with tarfile.open(result, "r:gz") as tf:
            names = tf.getnames()
            basenames = {n.rsplit("/", 1)[-1] for n in names}

        assert "config.yaml" in basenames
        assert "SOUL.md" in basenames
        assert "MEMORY.md" in basenames
        assert ".env.example" in basenames

        assert "auth.json" not in basenames
        assert "auth.lock" not in basenames
        assert ".env" not in basenames
        assert ".env.bak-kiro-20260529115545" not in basenames
        assert "private.pem" not in basenames
        assert not any(b.startswith("config.yaml.bak") for b in basenames)
