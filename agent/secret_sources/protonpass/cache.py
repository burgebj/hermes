"""Two-layer cache for resolved Proton Pass secrets.

* In-process (:data:`_CACHE`): saves repeated fetches WITHIN one process
  (CLI startup, gateway hot-reload, test suites).
* Disk (``<hermes_home>/cache/protonpass_cache.json``, mode 0600 in a 0700
  dir): saves repeated fetches ACROSS processes (scripts, cron, the gateway
  forking new agents).

Both layers store ONLY the secret values plus a token FINGERPRINT (a SHA-256
prefix embedded in the cache key); the token itself is NEVER persisted.  A
``cache_ttl_seconds <= 0`` disables BOTH layers (read and write).
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

from .session import _token_fingerprint

# Cache key: (token_fingerprint, vault, refs_signature, home).  The token is
# represented only by its fingerprint, never stored.  ``home`` scopes the
# IN-PROCESS L1 cache so a single long-lived process serving multiple Hermes
# profiles can't return a stale L1 entry across profiles (the disk L2 is
# already scoped by living under each profile's home dir; only its serialized
# string is profile-agnostic, see :func:`_cache_key_str`).
_CacheKey = Tuple[str, str, str, str]
_CACHE: Dict[_CacheKey, "_CachedFetch"] = {}

_DISK_CACHE_BASENAME = "protonpass_cache.json"


@dataclass
class _CachedFetch:
    secrets: Dict[str, str]
    fetched_at: float

    def is_fresh(self, ttl_seconds: float) -> bool:
        if ttl_seconds <= 0:
            return False
        return (time.time() - self.fetched_at) < ttl_seconds


def _refs_signature(env_refs: Dict[str, str]) -> str:
    """Stable, value-free signature of the MODE B ref map for the cache key.

    Hashes the (sorted) env-var-name → ``pass://`` URI pairs.  The URIs are
    references (share/item/field ids), not secret values, but we hash them
    anyway so the cache key stays compact and uniform.
    """
    if not env_refs:
        return ""
    items = "\n".join(f"{k}={env_refs[k]}" for k in sorted(env_refs))
    return hashlib.sha256(items.encode("utf-8")).hexdigest()[:16]


def build_cache_key(
    service_token: str,
    vault: str,
    env_refs: Dict[str, str],
    home_path: Optional[Path] = None,
) -> _CacheKey:
    """Build the cache key for a fetch.  The token is reduced to a fingerprint.

    ``home_path`` is folded into the (in-process) key so a long-lived process
    that fetches for more than one Hermes profile keeps their L1 entries
    distinct.  When omitted we resolve the same home the disk layer uses so a
    direct caller and a ``home_path``-passing caller land on the same key.
    """
    return (
        _token_fingerprint(service_token),
        vault or "",
        _refs_signature(env_refs),
        str(_resolve_home(home_path)),
    )


def _resolve_home(home_path: Optional[Path] = None) -> Path:
    """Resolve the Hermes home dir for cache scoping.

    ``home_path`` is what ``load_hermes_dotenv()`` already resolved; when it is
    omitted we defer to ``get_hermes_home()`` (the single source of truth that
    honours the context-local profile override and ``$HERMES_HOME``) rather than
    re-reading the env var ourselves — see the repo AGENTS.md rule, which avoids
    import-order surprises and keeps every caller agreeing on the profile.
    """
    if home_path is not None:
        return home_path
    # Local import keeps this module import-safe (no top-level dependency on the
    # constants module, which several hot paths import at load time).
    from hermes_constants import get_hermes_home

    return get_hermes_home()


def _disk_cache_path(home_path: Optional[Path] = None) -> Path:
    """Return the disk cache path under hermes_home/cache/."""
    return _resolve_home(home_path) / "cache" / _DISK_CACHE_BASENAME


def _cache_key_str(cache_key: _CacheKey) -> str:
    """Serialize a cache key to a stable string for JSON storage.

    The leading element is the token *fingerprint*, never the token, so it is
    safe to persist.  The trailing ``home`` element is DELIBERATELY omitted: the
    disk file already lives under that home dir, so folding the path into the
    persisted string would be redundant (and would also churn the on-disk format
    for the N1 in-process-only fix).
    """
    token_fp, vault, refs_sig, _home = cache_key
    return f"{token_fp}|{vault}|{refs_sig}"


def _read_disk_cache(cache_key: _CacheKey, ttl_seconds: float,
                     home_path: Optional[Path] = None) -> Optional["_CachedFetch"]:
    """Return a cached entry from disk if fresh and the key matches, else None.

    The persisted ``key`` embeds the token fingerprint, so a changed token
    produces a different key and the stale entry is ignored (cache invalidation
    on token change).  Best-effort: any I/O or parse error returns None and we
    re-fetch.
    """
    if ttl_seconds <= 0:
        return None
    path = _disk_cache_path(home_path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    if payload.get("key") != _cache_key_str(cache_key):
        return None
    secrets = payload.get("secrets")
    fetched_at = payload.get("fetched_at")
    if not isinstance(secrets, dict) or not isinstance(fetched_at, (int, float)):
        return None
    # Coerce all values to strings — JSON allows numbers but env vars need strings.
    typed_secrets: Dict[str, str] = {
        k: v for k, v in secrets.items() if isinstance(k, str) and isinstance(v, str)
    }
    entry = _CachedFetch(secrets=typed_secrets, fetched_at=float(fetched_at))
    if not entry.is_fresh(ttl_seconds):
        return None
    return entry


def _write_disk_cache(cache_key: _CacheKey, entry: "_CachedFetch",
                      home_path: Optional[Path] = None) -> None:
    """Persist a cache entry to disk atomically with mode 0600.

    Stores only the values and the cache key (which embeds the token
    *fingerprint*, never the token).  Best-effort: any I/O error is swallowed
    (the next invocation will just re-fetch). We never want disk cache failures
    to break startup.
    """
    path = _disk_cache_path(home_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Lock the cache dir down so other local users can't enumerate it.
        try:
            os.chmod(path.parent, 0o700)
        except OSError:
            pass
        payload = {
            "key": _cache_key_str(cache_key),
            "secrets": entry.secrets,
            "fetched_at": entry.fetched_at,
        }
        # Write to a temp file in the same directory and atomic-rename.
        # tempfile honors os.umask, so we explicitly chmod 0600 before rename.
        fd, tmp = tempfile.mkstemp(
            prefix=".protonpass_cache_", suffix=".tmp", dir=str(path.parent)
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f)
            os.chmod(tmp, 0o600)
            os.replace(tmp, path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
    except OSError:
        pass  # best-effort — disk cache miss on next invocation is fine


def _reset_cache_for_tests(home_path: Optional[Path] = None) -> None:
    """Clear in-process AND disk caches.

    Tests can pass ``home_path`` to scope the disk cleanup to a tmpdir.
    Without it we fall back to the same default resolution as the cache writer
    itself.
    """
    _CACHE.clear()
    try:
        _disk_cache_path(home_path).unlink()
    except (FileNotFoundError, OSError):
        pass
