"""Secret reference parsing.

A SecretRef is a locator only. It identifies where a secret should be
resolved from; it is not authorization to read that secret and must never
contain the raw secret value itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from urllib.parse import parse_qsl, quote, urlencode, urlparse

from .errors import SecretRefError

try:
    from agent.redact import redact_sensitive_text
except Exception:  # pragma: no cover - secret-ref parsing must stay import-safe
    redact_sensitive_text = None  # type: ignore[assignment]

_ENV_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.@-]+$")
_SAFE_QUERY_VALUE_RE = re.compile(r"^[A-Za-z0-9_.@-]{0,32}$")


def _validate_path_segments(parts: tuple[str, ...], *, raw: str) -> None:
    if not parts:
        raise SecretRefError("Secret reference has no item path")
    for part in parts:
        if not part or part in {".", ".."} or not _SAFE_SEGMENT_RE.match(part):
            raise SecretRefError("Secret reference contains invalid path segment")


def _is_secret_like_query_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    secret_markers = (
        "api_key",
        "access_token",
        "refresh_token",
        "auth_token",
        "authorization",
        "password",
        "passwd",
        "secret",
        "credential",
        "key",
        "jwt",
        "signature",
        "code",
        "token",
    )
    return any(marker in normalized for marker in secret_markers)


def _is_secret_like_query_value(value: str) -> bool:
    if not _SAFE_QUERY_VALUE_RE.fullmatch(value):
        return True
    if redact_sensitive_text is not None and redact_sensitive_text(value, force=True) != value:
        return True
    return False


def _normalize_path(parts: tuple[str, ...]) -> str:
    return "/".join(quote(part, safe="._@-") for part in parts)


def _provider_hint_from_name(name: str) -> str:
    normalized = name.lower()
    for suffix in ("_client_secret", "_access_token", "_refresh_token", "_api_key", "_token", "_secret"):
        if normalized.endswith(suffix):
            return normalized[: -len(suffix)].replace("_", "-")
    return ""


@dataclass(frozen=True)
class SecretRef:
    """Parsed secret locator.

    ``backend`` names the storage mechanism (for example ``env``, ``systemd``,
    or ``secret-service``). ``path`` identifies the item inside that backend.
    """

    scheme: str
    backend: str
    path: tuple[str, ...]
    original: str
    normalized: str
    display_safe: str
    _query_items: tuple[tuple[str, str], ...] = field(default_factory=tuple, repr=False)

    @property
    def query(self) -> dict[str, str]:
        """Public, non-secret query metadata as a defensive copy."""
        return dict(self._query_items)

    @property
    def name(self) -> str:
        """Leaf item name inside the backend."""
        return self.path[-1]

    @classmethod
    def parse(cls, raw: "str | SecretRef") -> "SecretRef":
        """Parse a supported secret reference string.

        Supported initial forms:
        - ``env:OPENROUTER_API_KEY``
        - ``systemd://openrouter_api_key``
        - ``secret://secret-service/hermes/openrouter/api_key``
        """
        if isinstance(raw, SecretRef):
            return raw
        if not isinstance(raw, str) or not raw.strip():
            raise SecretRefError("Secret reference must be a non-empty string")

        text = raw.strip()
        if text.startswith("env:"):
            return cls._parse_env(text)

        parsed = urlparse(text)
        if parsed.scheme == "systemd":
            return cls._parse_systemd(text, parsed)
        if parsed.scheme == "secret":
            return cls._parse_secret(text, parsed)

        raise SecretRefError("Unsupported or malformed secret reference")

    @classmethod
    def _parse_env(cls, text: str) -> "SecretRef":
        env_name = text[len("env:") :]
        if not _ENV_NAME_RE.match(env_name):
            raise SecretRefError("Invalid environment secret reference")
        return cls(
            scheme="env",
            backend="env",
            path=(env_name,),
            original=text,
            normalized=f"env:{env_name}",
            display_safe=f"env:{env_name}",
        )

    @classmethod
    def _parse_systemd(cls, text: str, parsed) -> "SecretRef":
        if parsed.params or parsed.query or parsed.fragment:
            raise SecretRefError("systemd secret references cannot include params/query/fragment")
        if parsed.path not in {"", "/"}:
            raise SecretRefError("systemd secret references must use systemd://<name>")
        name = parsed.netloc
        if not name or not _SAFE_SEGMENT_RE.match(name) or name in {".", ".."}:
            raise SecretRefError("Invalid systemd credential name")
        normalized = f"systemd://{quote(name, safe='._@-')}"
        return cls(
            scheme="systemd",
            backend="systemd",
            path=(name,),
            original=text,
            normalized=normalized,
            display_safe=normalized,
        )

    @classmethod
    def _parse_secret(cls, text: str, parsed) -> "SecretRef":
        backend = parsed.netloc
        if not backend or not _SAFE_SEGMENT_RE.match(backend):
            raise SecretRefError("Secret reference has invalid backend")
        if parsed.params or parsed.fragment:
            raise SecretRefError("Secret references cannot include params or fragments")

        parts = tuple(part for part in parsed.path.split("/") if part)
        # Reject doubled slash or trailing slash instead of silently normalizing.
        if parsed.path != "/" + "/".join(parts):
            raise SecretRefError("Secret reference contains an empty path segment")
        _validate_path_segments(parts, raw=text)

        query_items = tuple(parse_qsl(parsed.query, keep_blank_values=True))
        for key, value in query_items:
            if (
                _is_secret_like_query_key(key)
                or _is_secret_like_query_value(key)
                or _is_secret_like_query_value(value)
            ):
                raise SecretRefError("Secret reference query contains unsafe secret-like metadata")
        query = urlencode(query_items)
        normalized = f"secret://{backend}/{_normalize_path(parts)}"
        if query:
            normalized = f"{normalized}?{query}"
        return cls(
            scheme="secret",
            backend=backend,
            path=parts,
            original=text,
            normalized=normalized,
            display_safe=normalized,
            _query_items=query_items,
        )

    def to_public_dict(self) -> dict[str, object]:
        """Return locator-only metadata safe for logs/status output."""
        return {
            "scheme": self.scheme,
            "backend": self.backend,
            "path": list(self.path),
            "name": self.name,
            "query": self.query,
            "provider_hint": self.provider_hint,
            "ref": self.display_safe,
        }

    @property
    def provider_hint(self) -> str:
        """Best-effort provider hint encoded in the locator, if obvious."""
        if self.backend in {"env", "systemd"}:
            return _provider_hint_from_name(self.name)
        if self.scheme == "secret" and len(self.path) >= 2:
            leaf = self.path[-1].lower()
            if leaf in {
                "api_key",
                "apikey",
                "token",
                "access_token",
                "refresh_token",
                "client_secret",
            }:
                return self.path[-2].lower().replace("_", "-")
        return ""

    def __str__(self) -> str:
        return self.display_safe

    def __repr__(self) -> str:
        return f"SecretRef({self.display_safe!r})"
