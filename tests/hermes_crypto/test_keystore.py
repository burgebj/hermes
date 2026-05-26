"""Unit tests for the keystore: key slots, unlock, rotation, recovery."""

from __future__ import annotations

from pathlib import Path

import pytest

from hermes_crypto import audit, keystore
from hermes_crypto import kdf
from hermes_crypto.errors import DecryptionError, KeystoreError, LockedError

FAST_ARGON2 = {"time_cost": 1, "memory_cost_kib": 8, "parallelism": 1}


def test_passphrase_init_and_unlock():
    dek = keystore.init_keystore("passphrase", passphrase="hunter2", argon2_params=FAST_ARGON2)
    assert len(dek) == 32
    assert keystore.is_unlocked()

    keystore.lock()
    assert not keystore.is_unlocked()
    assert keystore.unlock(passphrase="hunter2") == dek


def test_wrong_passphrase_rejected():
    keystore.init_keystore("passphrase", passphrase="right", argon2_params=FAST_ARGON2)
    keystore.lock()
    with pytest.raises(DecryptionError):
        keystore.unlock(passphrase="wrong")


def test_keyring_init_and_unlock():
    # The in-memory fake keyring backend (see conftest) is treated as secure.
    assert keystore.keyring_is_secure()
    dek = keystore.init_keystore("keyring")
    keystore.lock()
    assert keystore.unlock() == dek


def test_keyfile_init_and_unlock():
    dek = keystore.init_keystore("keyfile")
    assert keystore.keyfile_path().exists()
    keystore.lock()
    assert keystore.unlock() == dek


def test_recovery_slot_unlocks_same_dek():
    dek = keystore.init_keystore("passphrase", passphrase="primary-pw", argon2_params=FAST_ARGON2)
    code = keystore.add_recovery_slot()
    assert keystore.has_recovery_slot()
    recovery = next(
        s for s in keystore.load_keystore()["slots"] if s.get("type") == "recovery"
    )
    assert recovery["kdf_params"] == kdf.RECOVERY_ARGON2_PARAMS

    keystore.lock()
    assert keystore.unlock(recovery_code=code) == dek
    # The recovery code is also accepted with lowercase / spacing noise.
    keystore.lock()
    assert keystore.unlock(recovery_code=code.lower().replace("-", " ")) == dek


def test_legacy_recovery_slot_with_stored_kdf_params_still_unlocks():
    """Slots created before the fast default persisted heavy params; unlock reads them."""
    dek = keystore.init_keystore("passphrase", passphrase="pw", argon2_params=FAST_ARGON2)
    legacy_params = {"time_cost": 2, "memory_cost_kib": 16, "parallelism": 1}
    code = keystore.add_recovery_slot(argon2_params=legacy_params)
    recovery = next(
        s for s in keystore.load_keystore()["slots"] if s.get("type") == "recovery"
    )
    assert recovery["kdf_params"] == legacy_params

    keystore.lock()
    assert keystore.unlock(recovery_code=code) == dek


def test_add_recovery_requires_unlock():
    keystore.init_keystore("passphrase", passphrase="pw", argon2_params=FAST_ARGON2)
    keystore.lock()
    with pytest.raises(LockedError):
        keystore.add_recovery_slot()


def test_replace_data_key_changes_cached_dek():
    dek = keystore.init_keystore("passphrase", passphrase="pw", argon2_params=FAST_ARGON2)
    new_dek = b"\x01" * 32
    dropped = keystore.replace_data_key(new_dek, passphrase="pw")
    assert dropped == 0
    assert keystore.get_cached_dek() == new_dek
    keystore.lock()
    assert keystore.unlock(passphrase="pw") == new_dek
    assert new_dek != dek


def test_replace_data_key_keyfile_rotates_kek():
    """Full re-key must generate a fresh keyfile KEK, not reuse the old one."""
    dek = keystore.init_keystore("keyfile")
    old_kek = keystore.keyfile_path().read_bytes()
    new_dek = b"\x02" * 32

    dropped = keystore.replace_data_key(new_dek)
    assert dropped == 0
    assert keystore.get_cached_dek() == new_dek
    assert new_dek != dek

    new_kek = keystore.keyfile_path().read_bytes()
    assert new_kek != old_kek

    keystore.lock()
    assert keystore.unlock() == new_dek

    keystore.lock()
    keystore.keyfile_path().write_bytes(old_kek)
    with pytest.raises(DecryptionError):
        keystore.unlock()


def test_replace_data_key_keyring_rotates_kek():
    """Full re-key must generate a fresh keyring KEK, not reuse the old one.

    Mirrors ``test_replace_data_key_keyfile_rotates_kek`` for the keyring slot,
    pinning the fresh-KEK-on-rekey invariant for the keyring backend ().
    """
    import base64
    import keyring as _keyring_mod

    dek = keystore.init_keystore("keyring")
    username = keystore._keyring_username()
    old_kek_b64 = _keyring_mod.get_password(keystore.KEYRING_SERVICE, username)
    assert old_kek_b64 is not None
    old_kek = base64.b64decode(old_kek_b64)
    assert len(old_kek) == 32

    new_dek = b"\x02" * 32
    dropped = keystore.replace_data_key(new_dek)
    assert dropped == 0
    assert keystore.get_cached_dek() == new_dek
    assert new_dek != dek

    new_kek_b64 = _keyring_mod.get_password(keystore.KEYRING_SERVICE, username)
    assert new_kek_b64 is not None
    new_kek = base64.b64decode(new_kek_b64)
    assert len(new_kek) == 32
    assert new_kek != old_kek

    keystore.lock()
    assert keystore.unlock() == new_dek

    # Restoring the old KEK in the keyring must no longer unlock the keystore:
    # the wrapped DEK in the slot was re-wrapped under the *new* KEK.
    keystore.lock()
    _keyring_mod.set_password(
        keystore.KEYRING_SERVICE, username, base64.b64encode(old_kek).decode("ascii")
    )
    with pytest.raises(DecryptionError):
        keystore.unlock()


def test_rotate_primary_keyfile_overwrites_when_unlink_fails(monkeypatch):
    """rotate_primary must still install a fresh KEK if unlink() of the keyfile fails.

    Regression test for previously the call site swallowed OSError from
    ``keyfile_path().unlink()`` and ``_build_keyfile_slot`` then read the
    old bytes back, silently reusing the same KEK.
    """
    keystore.init_keystore("keyfile")
    old_kek = keystore.keyfile_path().read_bytes()
    assert len(old_kek) == 32

    real_unlink = Path.unlink
    keyfile = keystore.keyfile_path()

    def fail_keyfile_unlink(self, *args, **kwargs):
        if self == keyfile:
            raise OSError(13, "Permission denied (handle held)")
        return real_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_keyfile_unlink)

    # Sanity: unlink really is blocked for the keyfile under the monkeypatch.
    with pytest.raises(OSError):
        keyfile.unlink()
    assert keyfile.exists()

    keystore.rotate_primary("keyfile")

    new_kek = keystore.keyfile_path().read_bytes()
    assert len(new_kek) == 32
    # The fix: the KEK on disk changed despite unlink being blocked.
    assert new_kek != old_kek

    # And the keystore unlocks cleanly with the new KEK in place.
    keystore.lock()
    assert len(keystore.unlock()) == 32


def test_rotate_passphrase_keeps_dek_and_invalidates_old():
    dek = keystore.init_keystore("passphrase", passphrase="old-pw", argon2_params=FAST_ARGON2)
    keystore.rotate_primary("passphrase", new_passphrase="new-pw", argon2_params=FAST_ARGON2)

    keystore.lock()
    assert keystore.unlock(passphrase="new-pw") == dek  # same DEK, new wrapping

    keystore.lock()
    with pytest.raises(DecryptionError):
        keystore.unlock(passphrase="old-pw")


def test_rotate_can_switch_key_source():
    dek = keystore.init_keystore("passphrase", passphrase="pw", argon2_params=FAST_ARGON2)
    keystore.rotate_primary("keyring")
    assert keystore.primary_slot_type() == "keyring"
    keystore.lock()
    assert keystore.unlock() == dek


def test_rotate_preserves_recovery_slot():
    keystore.init_keystore("passphrase", passphrase="pw", argon2_params=FAST_ARGON2)
    code = keystore.add_recovery_slot()
    keystore.rotate_primary("passphrase", new_passphrase="pw2", argon2_params=FAST_ARGON2)
    keystore.lock()
    # Recovery code still opens the keystore after a primary rotation.
    assert len(keystore.unlock(recovery_code=code)) == 32


def test_destroy_keystore_removes_everything():
    keystore.init_keystore("keyfile")
    assert keystore.keystore_exists()
    keystore.destroy_keystore()
    assert not keystore.keystore_exists()
    assert not keystore.keyfile_path().exists()
    assert not keystore.is_unlocked()


def test_destroy_keystore_raises_when_unlink_fails(monkeypatch):
    keystore.init_keystore("keyfile")
    real_unlink = Path.unlink

    def fail_keystore_unlink(self, *args, **kwargs):
        if self == keystore.keystore_path():
            raise OSError(13, "Permission denied")
        return real_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_keystore_unlink)
    with pytest.raises(KeystoreError, match="could not remove keystore"):
        keystore.destroy_keystore()
    assert keystore.keystore_exists()
    record = audit.read_recent(1)[0]
    assert record["activity"] == audit.KEYSTORE_DESTROYED
    assert record["outcome"] == audit.FAILURE
    assert str(keystore.keystore_path()) in record["detail"]["paths"]


def test_init_refuses_when_keystore_exists():
    keystore.init_keystore("keyfile")
    with pytest.raises(KeystoreError):
        keystore.init_keystore("keyfile")


def test_load_keystore_rejects_newer_version():
    keystore.init_keystore("keyfile")
    data = keystore.load_keystore()
    data["version"] = keystore.KEYSTORE_VERSION + 1
    keystore.save_keystore(data)
    keystore.lock()
    with pytest.raises(KeystoreError, match="newer than this Hermes"):
        keystore.load_keystore()


def test_load_keystore_rejects_malformed_version():
    keystore.init_keystore("keyfile")
    data = keystore.load_keystore()
    data["version"] = "not-an-int"
    keystore.save_keystore(data)
    keystore.lock()
    with pytest.raises(KeystoreError, match="invalid version"):
        keystore.load_keystore()


def test_unlock_maps_malformed_slot_to_keystore_error():
    keystore.init_keystore("passphrase", passphrase="pw", argon2_params=FAST_ARGON2)
    data = keystore.load_keystore()
    data["slots"][0].pop("salt")
    keystore.save_keystore(data)
    keystore.lock()
    with pytest.raises(KeystoreError, match="slot is malformed"):
        keystore.unlock(passphrase="pw")


def test_recovery_code_normalization_round_trip():
    code = keystore.generate_recovery_code()
    raw = keystore.normalize_recovery_code(code)
    assert keystore.normalize_recovery_code(code.lower()) == raw
    assert keystore.normalize_recovery_code(code.replace("-", "  ")) == raw
