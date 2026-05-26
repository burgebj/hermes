"""Keystore: the wrapped Data Encryption Key and its key slots.

Design — envelope encryption with LUKS-style key slots:

* A single random 32-byte **Data Encryption Key (DEK)** encrypts every file
  and is the SQLCipher ``PRAGMA key``. It is generated once and never changes
  when a passphrase changes.
* The DEK is wrapped (AES-256-GCM) by a **Key Encryption Key (KEK)** and the
  wrapped copy is stored in ``~/.hermes/.encryption/keystore.json``.
* The keystore holds one or more **slots**, each an independent KEK-wrapped
  copy of the *same* DEK. A typical install has a ``primary`` slot plus an
  optional ``recovery`` slot. This makes changing a passphrase cheap (re-wrap,
  no data touched) and lets one install be unlocked by more than one method.

KEK sources:

* ``keyring``    — a random KEK held in the OS keyring (Windows Credential
  Manager / macOS Keychain / Linux Secret Service).
* ``passphrase`` — KEK derived from a user passphrase via Argon2id/scrypt.
* ``keyfile``    — a random KEK in ``~/.hermes/.encryption/keyfile`` (0600).
* ``recovery``   — KEK derived from a one-time base32 recovery code.

Every rekey (``replace_data_key``) and primary-slot rotation
(``rotate_primary``) generates a **fresh KEK** for ``keyfile`` and
``keyring`` slots — the old wrapping key must not survive either operation.

The decrypted DEK is cached in a module-level variable for the process
lifetime only — it is never written to disk in cleartext.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from hermes_constants import get_hermes_home

from . import audit, kdf
from .errors import DecryptionError, DependencyError, KeystoreError, LockedError
from .fileio import atomic_write_private, harden_dir

KEYSTORE_VERSION = 1
KEYRING_SERVICE = "hermes-agent-encryption"

VALID_KEY_SOURCES = ("keyring", "passphrase", "keyfile")

# Process-lifetime cache of the decrypted DEK. Never persisted.
_cached_dek: Optional[bytes] = None


# ─── Paths ────────────────────────────────────────────────────────────────────


def encryption_dir() -> Path:
    """Return ``<HERMES_HOME>/.encryption`` (the keystore/keyfile/backup dir)."""
    return get_hermes_home() / ".encryption"


def keystore_path() -> Path:
    return encryption_dir() / "keystore.json"


def keyfile_path() -> Path:
    return encryption_dir() / "keyfile"


def backup_dir() -> Path:
    return encryption_dir() / "backup"


def keystore_exists() -> bool:
    return keystore_path().exists()


# ─── DEK cache ────────────────────────────────────────────────────────────────


def cache_dek(dek: bytes) -> None:
    """Store the decrypted DEK in the process-lifetime cache."""
    global _cached_dek
    if len(dek) != 32:
        raise ValueError("DEK must be 32 bytes")
    _cached_dek = dek


def get_cached_dek() -> Optional[bytes]:
    return _cached_dek


def is_unlocked() -> bool:
    return _cached_dek is not None


def lock() -> None:
    """Drop the cached DEK from memory."""
    global _cached_dek
    _cached_dek = None


# ─── Keyring helpers ──────────────────────────────────────────────────────────


def _keyring_username() -> str:
    """A keyring entry name namespaced by HERMES_HOME so profiles don't collide."""
    home = str(get_hermes_home().resolve())
    digest = hashlib.sha256(home.encode("utf-8")).hexdigest()[:16]
    return f"kek:{digest}"


def _import_keyring():
    try:
        import keyring
    except ImportError as exc:
        raise DependencyError(
            "The 'keyring' package is required for keyring-backed encryption. "
            "Install it with:  pip install 'hermes-agent[encryption]'"
        ) from exc
    return keyring


def keyring_is_secure() -> bool:
    """Return True only when the active keyring backend is a real OS keyring.

    On headless hosts ``keyring`` silently falls back to a plaintext file
    backend (``keyrings.alt``) or a no-op ``fail`` backend — either defeats
    the purpose, so keyring mode must be refused there in favour of a
    passphrase.
    """
    try:
        keyring = _import_keyring()
        backend = keyring.get_keyring()
    except Exception:
        return False
    module = type(backend).__module__ or ""
    insecure_prefixes = ("keyrings.alt", "keyring.backends.fail", "keyring.backends.null")
    return not any(module.startswith(prefix) for prefix in insecure_prefixes)


def _keyring_set_kek(username: str, kek: bytes) -> None:
    keyring = _import_keyring()
    keyring.set_password(KEYRING_SERVICE, username, base64.b64encode(kek).decode("ascii"))


def _keyring_get_kek(username: str) -> bytes:
    keyring = _import_keyring()
    stored = keyring.get_password(KEYRING_SERVICE, username)
    if not stored:
        raise KeystoreError(
            "No encryption key found in the OS keyring for this install. "
            "The keyring entry may have been deleted, or this is a different "
            "machine. Unlock with a recovery code instead."
        )
    try:
        kek = base64.b64decode(stored)
    except ValueError as exc:
        raise KeystoreError("corrupt keyring entry") from exc
    if len(kek) != 32:
        raise KeystoreError("corrupt keyring entry (wrong length)")
    return kek


def _keyring_delete_kek(username: str) -> None:
    try:
        keyring = _import_keyring()
        keyring.delete_password(KEYRING_SERVICE, username)
    except Exception:
        pass


# ─── Recovery codes ───────────────────────────────────────────────────────────


def generate_recovery_code() -> str:
    """Return a fresh 160-bit recovery code as dash-grouped base32 text."""
    raw = secrets.token_bytes(20)
    body = base64.b32encode(raw).decode("ascii").rstrip("=")
    return "-".join(body[i : i + 5] for i in range(0, len(body), 5))


def normalize_recovery_code(code: str) -> bytes:
    """Canonicalise a user-typed recovery code back to its raw bytes."""
    cleaned = "".join(ch for ch in (code or "").upper() if ch.isalnum())
    if not cleaned:
        raise ValueError("empty recovery code")
    padding = "=" * (-len(cleaned) % 8)
    try:
        return base64.b32decode(cleaned + padding)
    except ValueError as exc:
        raise ValueError("invalid recovery code") from exc


# ─── Slot construction / resolution ───────────────────────────────────────────


def _wrap_dek(dek: bytes, kek: bytes) -> str:
    from . import envelope

    return base64.b64encode(envelope.encrypt(dek, kek)).decode("ascii")


def _unwrap_dek(wrapped_b64: str, kek: bytes) -> bytes:
    from . import envelope

    try:
        wrapped = base64.b64decode(wrapped_b64)
    except (TypeError, ValueError, binascii.Error) as exc:
        raise KeystoreError("keystore slot is malformed") from exc
    dek = envelope.decrypt(wrapped, kek)
    if len(dek) != 32:
        raise DecryptionError("unwrapped DEK has the wrong length")
    return dek


def _build_keyring_slot(slot_id: str, dek: bytes) -> Dict[str, Any]:
    if not keyring_is_secure():
        raise KeystoreError(
            "The OS keyring backend on this host is insecure or unavailable "
            "(no Secret Service / Credential Manager). Use 'passphrase' mode "
            "instead:  hermes encrypt enable --key-source passphrase"
        )
    username = _keyring_username()
    kek = secrets.token_bytes(32)
    _keyring_set_kek(username, kek)
    return {
        "id": slot_id,
        "type": "keyring",
        "keyring_id": username,
        "wrapped_dek": _wrap_dek(dek, kek),
    }


def _build_keyfile_slot(
    slot_id: str, dek: bytes, *, force_new_kek: bool = False
) -> Dict[str, Any]:
    """Build a keyfile slot wrapping *dek*.

    When *force_new_kek* is True the existing keyfile (if any) is overwritten
    in place with a freshly generated 32-byte KEK. ``atomic_write_private``
    handles the overwrite via os.replace, so this is race-free even when an
    AV/backup/concurrent-Hermes handle would block an unlink. Used by
    ``rotate_primary`` / ``replace_data_key`` to guarantee a new KEK on rekey
    even if a stale keyfile is still on disk.

    With the default ``force_new_kek=False`` an existing keyfile is honoured:
    callers like ``init_keystore`` must respect a pre-placed operator keyfile.
    """
    path = keyfile_path()
    if force_new_kek:
        kek = secrets.token_bytes(32)
        atomic_write_private(path, kek)
    elif path.exists():
        kek = path.read_bytes()
        if len(kek) != 32:
            raise KeystoreError("existing keyfile has the wrong length")
    else:
        kek = secrets.token_bytes(32)
        atomic_write_private(path, kek)
    return {
        "id": slot_id,
        "type": "keyfile",
        "wrapped_dek": _wrap_dek(dek, kek),
    }


def _build_secret_slot(
    slot_id: str,
    slot_type: str,
    dek: bytes,
    secret: bytes,
    argon2_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a passphrase- or recovery-derived slot."""
    salt = secrets.token_bytes(16)
    kdf_id = kdf.preferred_kdf_id()
    if slot_type == "recovery":
        # High-entropy random secret — see kdf.RECOVERY_ARGON2_PARAMS.
        base_params = kdf.RECOVERY_ARGON2_PARAMS
    else:
        base_params = kdf.DEFAULT_ARGON2_PARAMS
    params = {**base_params, **(argon2_params or {})}
    kek = kdf.derive_kek(secret, salt, kdf_id, params)
    return {
        "id": slot_id,
        "type": slot_type,
        "kdf_id": kdf_id,
        "kdf_params": params if kdf_id == kdf.KDF_ARGON2ID else {},
        "salt": base64.b64encode(salt).decode("ascii"),
        "wrapped_dek": _wrap_dek(dek, kek),
    }


def _kek_for_slot(
    slot: Dict[str, Any],
    *,
    passphrase: Optional[str] = None,
    recovery_code: Optional[str] = None,
) -> bytes:
    slot_type = slot.get("type")
    if slot_type == "keyring":
        return _keyring_get_kek(slot.get("keyring_id") or _keyring_username())
    if slot_type == "keyfile":
        path = keyfile_path()
        if not path.exists():
            raise KeystoreError(f"keyfile missing: {path}")
        kek = path.read_bytes()
        if len(kek) != 32:
            raise KeystoreError("keyfile has the wrong length")
        return kek
    if slot_type in ("passphrase", "recovery"):
        if slot_type == "passphrase":
            if passphrase is None:
                raise LockedError("a passphrase is required to unlock this keystore")
            secret = passphrase.encode("utf-8")
        else:
            if recovery_code is None:
                raise LockedError("a recovery code is required")
            secret = normalize_recovery_code(recovery_code)
        try:
            salt = base64.b64decode(slot["salt"])
            kdf_id = int(slot["kdf_id"])
        except (KeyError, TypeError, ValueError, binascii.Error) as exc:
            raise KeystoreError("keystore slot is malformed") from exc
        return kdf.derive_kek(
            secret, salt, kdf_id, slot.get("kdf_params") or None
        )
    raise KeystoreError(f"unknown slot type {slot_type!r}")


# ─── Keystore file I/O ────────────────────────────────────────────────────────


def load_keystore() -> Dict[str, Any]:
    path = keystore_path()
    if not path.exists():
        raise KeystoreError(
            "Encryption is enabled but no keystore exists. Run "
            "'hermes encrypt enable' to set one up."
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise KeystoreError(f"keystore is unreadable or corrupt: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("slots"), list):
        raise KeystoreError("keystore is malformed")
    try:
        version = int(data.get("version", 0))
    except (TypeError, ValueError) as exc:
        raise KeystoreError("keystore is malformed (invalid version)") from exc
    if version > KEYSTORE_VERSION:
        raise KeystoreError(
            f"keystore version {version} is newer than this Hermes "
            f"understands ({KEYSTORE_VERSION}); upgrade Hermes."
        )
    return data


def save_keystore(data: Dict[str, Any]) -> None:
    harden_dir(encryption_dir())
    payload = json.dumps(data, indent=2, sort_keys=False).encode("utf-8")
    atomic_write_private(keystore_path(), payload)


def _slots(keystore: Dict[str, Any]) -> List[Dict[str, Any]]:
    return list(keystore.get("slots") or [])


def primary_slot_type() -> Optional[str]:
    """Return the type of the non-recovery slot, or None when no keystore exists."""
    if not keystore_exists():
        return None
    try:
        keystore = load_keystore()
    except KeystoreError:
        return None
    for slot in _slots(keystore):
        if slot.get("type") != "recovery":
            return slot.get("type")
    return None


def has_recovery_slot() -> bool:
    if not keystore_exists():
        return False
    try:
        keystore = load_keystore()
    except KeystoreError:
        return False
    return any(slot.get("type") == "recovery" for slot in _slots(keystore))


# ─── Public operations ────────────────────────────────────────────────────────


def init_keystore(
    key_source: str,
    *,
    passphrase: Optional[str] = None,
    argon2_params: Optional[Dict[str, Any]] = None,
) -> bytes:
    """Create a brand-new keystore with one primary slot. Returns the DEK."""
    if key_source not in VALID_KEY_SOURCES:
        raise ValueError(f"key_source must be one of {VALID_KEY_SOURCES}")
    if keystore_exists():
        raise KeystoreError(
            "A keystore already exists. Use 'hermes encrypt rotate-key' to "
            "change keys, or 'hermes encrypt disable' first."
        )
    harden_dir(encryption_dir())
    dek = secrets.token_bytes(32)

    if key_source == "keyring":
        slot = _build_keyring_slot("primary", dek)
    elif key_source == "keyfile":
        slot = _build_keyfile_slot("primary", dek)
    else:  # passphrase
        if not passphrase:
            raise ValueError("passphrase mode requires a passphrase")
        slot = _build_secret_slot("primary", "passphrase", dek, passphrase.encode("utf-8"), argon2_params)

    keystore = {
        "version": KEYSTORE_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "key_source": key_source,
        "slots": [slot],
    }
    save_keystore(keystore)
    cache_dek(dek)
    audit.log_event(audit.KEYSTORE_CREATED, audit.SUCCESS, key_source=key_source)
    return dek


def unlock(
    *,
    passphrase: Optional[str] = None,
    recovery_code: Optional[str] = None,
) -> bytes:
    """Unwrap the DEK from the keystore, cache it, and return it.

    With no arguments only ``keyring``/``keyfile`` slots can be opened. Pass
    *passphrase* or *recovery_code* to open the matching slot.
    """
    keystore = load_keystore()
    slots = _slots(keystore)

    if recovery_code is not None:
        candidates = [s for s in slots if s.get("type") == "recovery"]
    elif passphrase is not None:
        candidates = [s for s in slots if s.get("type") == "passphrase"]
    else:
        candidates = [s for s in slots if s.get("type") in ("keyring", "keyfile")]

    if not candidates:
        raise KeystoreError(
            "No key slot matches the credentials provided. Available slot "
            f"types: {sorted({s.get('type') for s in slots})}."
        )

    last_error: Optional[Exception] = None
    for slot in candidates:
        try:
            kek = _kek_for_slot(slot, passphrase=passphrase, recovery_code=recovery_code)
            try:
                wrapped_dek = slot["wrapped_dek"]
            except KeyError as exc:
                raise KeystoreError("keystore slot is malformed") from exc
            dek = _unwrap_dek(wrapped_dek, kek)
        except (DecryptionError, KeystoreError, DependencyError, ValueError) as exc:
            last_error = exc
            continue
        cache_dek(dek)
        audit.log_event(audit.KEYSTORE_UNLOCKED, audit.SUCCESS, slot=slot.get("type"))
        return dek

    if isinstance(last_error, DependencyError):
        audit.log_event(
            audit.KEYSTORE_UNLOCK_FAILED, audit.FAILURE, reason="missing_dependency"
        )
        raise last_error
    if isinstance(last_error, KeystoreError) and "slot is malformed" in str(last_error):
        audit.log_event(
            audit.KEYSTORE_UNLOCK_FAILED, audit.FAILURE, reason="malformed_slot"
        )
        raise last_error
    audit.log_event(audit.KEYSTORE_UNLOCK_FAILED, audit.FAILURE, reason="wrong_key_or_corrupt")
    raise DecryptionError(
        "Could not unlock the keystore — wrong passphrase/recovery code, or "
        "the keystore is corrupt."
    )


def add_recovery_slot(argon2_params: Optional[Dict[str, Any]] = None) -> str:
    """Add a recovery slot wrapping the current DEK. Returns the recovery code.

    Requires the keystore to be unlocked (the DEK must be in memory).

    Recovery slots use :data:`kdf.RECOVERY_ARGON2_PARAMS` by default (fast KDF
    for a 160-bit random secret). *argon2_params* overrides that base only for
    tests or reading back legacy slots created before the fast default existed.
    """
    dek = get_cached_dek()
    if dek is None:
        raise LockedError("unlock the keystore before adding a recovery code")
    keystore = load_keystore()
    slots = _slots(keystore)
    slots = [s for s in slots if s.get("type") != "recovery"]
    code = generate_recovery_code()
    slots.append(
        _build_secret_slot(
            "recovery", "recovery", dek, normalize_recovery_code(code), argon2_params
        )
    )
    keystore["slots"] = slots
    save_keystore(keystore)
    audit.log_event(audit.RECOVERY_CODE_ADDED, audit.SUCCESS)
    return code


def rotate_primary(
    new_key_source: Optional[str] = None,
    *,
    new_passphrase: Optional[str] = None,
    argon2_params: Optional[Dict[str, Any]] = None,
) -> None:
    """Re-wrap the existing DEK under a fresh primary slot.

    This is the cheap rotation: the DEK (and therefore every encrypted file)
    is untouched — only the slot that wraps it changes. ``new_key_source`` may
    differ from the current one (e.g. move from keyring to passphrase).
    Requires the keystore to be unlocked.
    """
    dek = get_cached_dek()
    if dek is None:
        raise LockedError("unlock the keystore before rotating the key")
    keystore = load_keystore()
    source = new_key_source or keystore.get("key_source")
    if source not in VALID_KEY_SOURCES:
        raise ValueError(f"key_source must be one of {VALID_KEY_SOURCES}")

    if source == "keyring":
        new_slot = _build_keyring_slot("primary", dek)
    elif source == "keyfile":
        # Fresh KEK on every rekey. atomic_write_private overwrites the existing
        # keyfile in place via os.replace, so we don't need to unlink first —
        # that avoids a silent regression to the old KEK when an AV/backup/
        # concurrent-Hermes handle blocks the unlink on Windows.
        new_slot = _build_keyfile_slot("primary", dek, force_new_kek=True)
    else:
        if not new_passphrase:
            raise ValueError("passphrase rotation requires a new passphrase")
        new_slot = _build_secret_slot(
            "primary", "passphrase", dek, new_passphrase.encode("utf-8"), argon2_params
        )

    recovery = [s for s in _slots(keystore) if s.get("type") == "recovery"]
    keystore["key_source"] = source
    keystore["slots"] = [new_slot] + recovery
    keystore["rotated_at"] = datetime.now(timezone.utc).isoformat()
    save_keystore(keystore)
    audit.log_event(audit.KEYSTORE_ROTATED, audit.SUCCESS, key_source=source)


def replace_data_key(
    new_dek: bytes,
    *,
    passphrase: Optional[str] = None,
) -> int:
    """Replace the DEK with a fresh random key, re-wrapping the primary slot.

    Every envelope-encrypted artifact must already have been re-encrypted with
    *new_dek* before this is called. Recovery slots are dropped because they
    wrapped the old DEK and cannot be updated without each recovery code.

    Returns the number of recovery slots removed. Requires the keystore to be
    unlocked with the *old* DEK still cached.
    """
    if len(new_dek) != 32:
        raise ValueError("DEK must be 32 bytes")
    if get_cached_dek() is None:
        raise LockedError("unlock the keystore before replacing the data key")

    keystore = load_keystore()
    source = keystore.get("key_source")
    if source not in VALID_KEY_SOURCES:
        raise ValueError(f"key_source must be one of {VALID_KEY_SOURCES}")

    primary = next((s for s in _slots(keystore) if s.get("type") != "recovery"), None)
    if primary is None:
        raise KeystoreError("keystore has no primary slot")

    if source == "keyring":
        new_primary = _build_keyring_slot("primary", new_dek)
    elif source == "keyfile":
        # Fresh KEK on every rekey. atomic_write_private overwrites the existing
        # keyfile in place via os.replace, so we don't need to unlink first —
        # that avoids a silent regression to the old KEK when an AV/backup/
        # concurrent-Hermes handle blocks the unlink on Windows.
        new_primary = _build_keyfile_slot("primary", new_dek, force_new_kek=True)
    else:
        if not passphrase:
            raise ValueError("passphrase is required to re-wrap a passphrase slot")
        new_primary = _rewrap_secret_slot(primary, new_dek, passphrase.encode("utf-8"))

    recovery_count = sum(1 for s in _slots(keystore) if s.get("type") == "recovery")
    keystore["slots"] = [new_primary]
    keystore["rotated_at"] = datetime.now(timezone.utc).isoformat()
    save_keystore(keystore)
    cache_dek(new_dek)
    audit.log_event(
        audit.DATA_KEY_REKEYED,
        audit.SUCCESS,
        key_source=source,
        recovery_slots_dropped=recovery_count,
    )
    return recovery_count


def _rewrap_secret_slot(
    slot: Dict[str, Any],
    new_dek: bytes,
    secret: bytes,
) -> Dict[str, Any]:
    """Re-wrap *new_dek* under the same KDF parameters as an existing secret slot."""
    salt = base64.b64decode(slot["salt"])
    kek = kdf.derive_kek(
        secret, salt, int(slot["kdf_id"]), slot.get("kdf_params") or None
    )
    updated = dict(slot)
    updated["wrapped_dek"] = _wrap_dek(new_dek, kek)
    return updated


def destroy_keystore() -> None:
    """Remove the keystore, keyfile, and keyring entry. Used by ``disable``.

    The DEK must already be available to callers that still need to decrypt
    data — call this only after every file has been decrypted back to plaintext.
    """
    username = _keyring_username()
    keystore = None
    try:
        keystore = load_keystore()
    except KeystoreError:
        pass
    if keystore is not None:
        for slot in _slots(keystore):
            if slot.get("type") == "keyring":
                _keyring_delete_kek(slot.get("keyring_id") or username)
    remaining: list[tuple[Path, OSError]] = []
    for path in (keystore_path(), keyfile_path()):
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        except OSError as exc:
            remaining.append((path, exc))
    if remaining:
        audit.log_event(
            audit.KEYSTORE_DESTROYED,
            audit.FAILURE,
            paths=[str(p) for p, _ in remaining],
        )
        names = ", ".join(str(p) for p, _ in remaining)
        raise KeystoreError(
            f"could not remove keystore file(s): {names}. "
            "Retry 'hermes encrypt disable' once the file is unlocked."
        )
    lock()
    audit.log_event(audit.KEYSTORE_DESTROYED, audit.SUCCESS)
