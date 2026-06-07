"""Secret provider contracts and redacted secret value wrapper."""

from __future__ import annotations

from contextlib import contextmanager
from enum import Enum
from typing import Any, Iterator, Mapping, Protocol, runtime_checkable

try:
    from agent.redact import redact_sensitive_text
except Exception:  # pragma: no cover - redaction import must never break secrets
    redact_sensitive_text = None  # type: ignore[assignment]


class SecretProviderStatus(str, Enum):
    """Coarse provider availability state."""

    AVAILABLE = "available"
    MISSING = "missing"
    LOCKED = "locked"
    UNAVAILABLE = "unavailable"


class SecretValue:
    """Runtime-only secret wrapper with redacted display behavior."""

    __slots__ = ("_value", "source", "metadata")

    def __init__(
        self,
        value: str,
        *,
        source: str = "",
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        self._value = str(value)
        self.source = source
        self.metadata = dict(metadata or {})

    def reveal(self) -> str:
        """Explicitly reveal the raw value to trusted provider-client code."""
        return self._value

    @contextmanager
    def reveal_temporarily(self) -> Iterator[str]:
        """Context-manager reveal helper for call sites that prefer scoped use."""
        yield self._value

    def to_public_dict(self) -> dict[str, Any]:
        """Return metadata safe for status/log output."""
        return {
            "redacted": True,
            "source": self._redact_public(self.source),
            "metadata": self._redact_public(self.metadata),
        }

    def _redact_public(self, value: Any) -> Any:
        if isinstance(value, str):
            return self._redact_public_text(value)
        if isinstance(value, Mapping):
            return {
                self._redact_public_text(str(key)): self._redact_public(item)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [self._redact_public(item) for item in value]
        if isinstance(value, tuple):
            return tuple(self._redact_public(item) for item in value)
        if isinstance(value, set):
            return sorted(self._redact_public(item) for item in value)
        return value

    def _redact_public_text(self, text: str) -> str:
        redacted = text
        if self._value and self._value in redacted:
            redacted = redacted.replace(self._value, "<redacted>")
        if redact_sensitive_text is not None:
            redacted = redact_sensitive_text(redacted, force=True)
        return redacted

    def __bool__(self) -> bool:
        return bool(self._value)

    def __repr__(self) -> str:
        source = f" source={self._redact_public_text(self.source)!r}" if self.source else ""
        return f"<SecretValue redacted{source}>"

    __str__ = __repr__


@runtime_checkable
class SecretProvider(Protocol):
    """Backend contract for resolving SecretRefs."""

    @property
    def backend(self) -> str:
        """Backend key this provider resolves, for example ``env``."""
        ...

    def status(self) -> SecretProviderStatus:
        """Return current provider availability."""
        ...

    def resolve(self, ref, context) -> SecretValue:
        """Resolve a SecretRef for an already-authorized request context."""
        ...
