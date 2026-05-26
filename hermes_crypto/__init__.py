"""hermes_crypto — opt-in encryption-at-rest for Hermes Agent.

This package keeps the sensitive files under ``HERMES_HOME`` encrypted on
disk (credentials, OAuth tokens, conversation history) so a stolen laptop,
a leaked backup, or a decommissioned VPS disk does not expose them. Data is
decrypted into process memory at runtime — the agent still needs cleartext
to run.

**Import-safety contract:** this ``__init__`` module imports only the
standard library plus the dependency-free :mod:`hermes_crypto.detect`. The
heavy submodules (``envelope`` → ``cryptography``, ``keystore`` → ``keyring``)
are imported lazily inside functions. Credential loaders import this module
very early — before the agent loop and before plugins — so it must never
fail to import just because the optional ``encryption`` extra is absent.

Public API used by the rest of the codebase:

* :func:`is_encrypted`            — cheap, dependency-free envelope detection.
* :func:`is_encryption_enabled`   — reads ``security.encryption.enabled``.
* :func:`decrypt_if_encrypted`    — decrypt a credential blob iff it is an envelope.
* :func:`encrypt_if_enabled`      — encrypt a credential blob iff encryption is on.
* :func:`get_data_key`            — the 32-byte DEK, used as the SQLCipher key.

Submodules with their own public API (import directly, not re-exported here):

* :mod:`hermes_crypto.log_handler`     — :func:`build_rotating_handler`, ``read_log_text``.
* :mod:`hermes_crypto.session_writer`  — :func:`build_session_writer`, ``read_session_text``.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict

from .detect import ENV_MARKER, MAGIC, is_encrypted, is_encrypted_env
from .errors import (
    DecryptionError,
    DependencyError,
    HermesCryptoError,
    KeystoreError,
    LockedError,
)

__all__ = [
    "MAGIC",
    "ENV_MARKER",
    "is_encrypted",
    "is_encrypted_env",
    "is_encryption_enabled",
    "encryption_settings",
    "credentials_encryption_active",
    "database_encryption_active",
    "logs_encryption_active",
    "running_under_openshell",
    "decrypt_if_encrypted",
    "encrypt_if_enabled",
    "get_data_key",
    "unlock_keystore",
    "HermesCryptoError",
    "DependencyError",
    "DecryptionError",
    "KeystoreError",
    "LockedError",
]

PASSPHRASE_ENV_VAR = "HERMES_ENCRYPTION_PASSPHRASE"


# ─── Config gating ────────────────────────────────────────────────────────────


def encryption_settings() -> Dict[str, Any]:
    """Return the ``security.encryption`` config block, or ``{}`` on any error.

    Deliberately swallows every exception: this runs during very early
    credential loading where a missing/broken config must degrade to
    "encryption off" rather than crash the process.
    """
    try:
        from hermes_cli.config import cfg_get, load_config

        config = load_config()
        block = cfg_get(config, "security", "encryption", default=None)
        return dict(block) if isinstance(block, dict) else {}
    except Exception:
        return {}


def is_encryption_enabled() -> bool:
    """Return True when ``security.encryption.enabled`` is set."""
    from utils import is_truthy_value

    return is_truthy_value(encryption_settings().get("enabled", False))


def credentials_encryption_active() -> bool:
    """True when credential files (.env, auth.json, OAuth) should be encrypted."""
    from utils import is_truthy_value

    settings = encryption_settings()
    if not is_truthy_value(settings.get("enabled", False)):
        return False
    return is_truthy_value(settings.get("encrypt_credentials", True))


def database_encryption_active() -> bool:
    """True when SQLite databases (state.db, kanban.db) should be encrypted."""
    from utils import is_truthy_value

    settings = encryption_settings()
    if not is_truthy_value(settings.get("enabled", False)):
        return False
    return is_truthy_value(settings.get("encrypt_databases", False))


def logs_encryption_active() -> bool:
    """True when rotated log segments under ``~/.hermes/logs/`` should be encrypted."""
    from utils import is_truthy_value

    settings = encryption_settings()
    if not is_truthy_value(settings.get("enabled", False)):
        return False
    return is_truthy_value(settings.get("encrypt_logs", False))


def running_under_openshell() -> bool:
    """True when Hermes is running inside an NVIDIA OpenShell sandbox.

    OpenShell's supervisor injects these variables into the sandboxed
    process. Encryption-at-rest protects data on a cold disk; OpenShell is
    the complementary layer that confines the *running* process — when both
    are present, the agent's security posture covers both halves.
    """
    return bool(
        os.environ.get("OPENSHELL_SANDBOX_ID") or os.environ.get("OPENSHELL_ENDPOINT")
    )


# ─── Key access ───────────────────────────────────────────────────────────────


def get_data_key() -> bytes:
    """Return the 32-byte Data Encryption Key, unlocking the keystore if needed.

    Unlock strategy by primary slot type:

    * ``keyring`` / ``keyfile`` — silent, no prompt.
    * ``passphrase`` — uses ``HERMES_ENCRYPTION_PASSPHRASE`` (consumed and
      removed from the environment) when set, otherwise prompts on a TTY,
      otherwise raises :class:`LockedError`.

    Raises :class:`DependencyError` when the ``encryption`` extra is missing.
    """
    from . import audit, keystore

    cached = keystore.get_cached_dek()
    if cached is not None:
        return cached

    source = keystore.primary_slot_type()
    if source in ("keyring", "keyfile"):
        return keystore.unlock()

    if source == "passphrase":
        # Layer 1 (parent process): pop after unlock so the passphrase does not
        # linger in os.environ for later in-process reads. Layer 2 (upstream
        # subprocess scrub in tools/environments/local.py and
        # tools/code_execution_tool.py): strip HERMES_ENCRYPTION_PASSPHRASE
        # unconditionally from every spawned shell/code-exec env — belt-and-
        # suspenders if the var is re-set or this pop did not run. Both layers
        # are intentional; do not remove either.
        #
        # read first, pop only on successful unlock so a
        # wrong-passphrase failure surfaces cleanly (caller can retry) instead
        # of consuming the env var and falling through to the TTY / LockedError
        # path on the next call. Layer 2 still strips it from every spawned
        # subprocess regardless.
        passphrase = os.environ.get(PASSPHRASE_ENV_VAR)
        if passphrase:
            dek = keystore.unlock(passphrase=passphrase)  # may raise; var stays
            os.environ.pop(PASSPHRASE_ENV_VAR, None)
            return dek
        if sys.stdin is not None and sys.stdin.isatty():
            import getpass

            entered = getpass.getpass("Hermes encryption passphrase: ")
            return keystore.unlock(passphrase=entered)
        audit.log_event(audit.DATA_KEY_UNAVAILABLE, audit.FAILURE, reason="no_passphrase")
        raise LockedError(
            "Encryption is enabled in passphrase mode but no passphrase is "
            f"available. Set the {PASSPHRASE_ENV_VAR} environment variable, or "
            "run in an interactive terminal."
        )

    audit.log_event(audit.DATA_KEY_UNAVAILABLE, audit.FAILURE, reason="no_keystore")
    raise KeystoreError(
        "Encryption is enabled but the keystore is missing or unreadable. "
        "Run 'hermes encrypt status' to diagnose."
    )


def unlock_keystore(*, passphrase: str | None = None, recovery_code: str | None = None) -> bytes:
    """Explicitly unlock and cache the DEK (used by the ``hermes encrypt`` CLI)."""
    from . import keystore

    return keystore.unlock(passphrase=passphrase, recovery_code=recovery_code)


# ─── Transparent credential I/O ───────────────────────────────────────────────


def decrypt_if_encrypted(data: bytes) -> bytes:
    """Return cleartext: decrypt *data* when it is an envelope, else return it.

    Decryption is driven by the envelope itself, not the config flag — an
    encrypted file is always decrypted so a half-finished migration or a
    stale flag never makes credentials silently unreadable.
    """
    if not is_encrypted(data):
        return data
    from . import envelope

    dek = get_data_key()
    raw = bytes(data)
    if is_encrypted_env(raw):
        return envelope.decrypt_env(raw, dek)
    return envelope.decrypt(raw, dek)


def encrypt_if_enabled(data: bytes, *, env: bool = False) -> bytes:
    """Return *data* encrypted when credential encryption is active, else as-is.

    Set ``env=True`` for the ``.env`` file so the text-framed (marker + base64)
    form is produced instead of the raw binary envelope.
    """
    if not credentials_encryption_active():
        return data
    from . import envelope

    dek = get_data_key()
    return envelope.encrypt_env(bytes(data), dek) if env else envelope.encrypt(bytes(data), dek)
