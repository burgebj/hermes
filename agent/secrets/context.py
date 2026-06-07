"""Secret request policy context."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CallerBoundary(str, Enum):
    """Boundary of the code asking to resolve a secret."""

    CORE = "core"
    TOOL = "tool"
    PLUGIN = "plugin"
    SUBPROCESS = "subprocess"


class RuntimeMode(str, Enum):
    """Runtime surface where the request is being made."""

    CLI = "cli"
    GATEWAY = "gateway"
    CRON = "cron"
    TEST = "test"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class SecretRequestContext:
    """Policy context for a secret-resolution request.

    This is an application policy guard, not a cryptographic boundary. The
    durable protection still comes from the backing secret provider.
    """

    provider: str
    purpose: str
    runtime_mode: RuntimeMode | str
    profile: str
    caller_boundary: CallerBoundary | str
    local_unlock_allowed: bool = False
    audit_label: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider", (self.provider or "").strip())
        object.__setattr__(self, "purpose", (self.purpose or "").strip())
        object.__setattr__(self, "profile", (self.profile or "").strip() or "default")
        object.__setattr__(
            self,
            "runtime_mode",
            self.runtime_mode if isinstance(self.runtime_mode, RuntimeMode) else RuntimeMode(str(self.runtime_mode)),
        )
        object.__setattr__(
            self,
            "caller_boundary",
            self.caller_boundary
            if isinstance(self.caller_boundary, CallerBoundary)
            else CallerBoundary(str(self.caller_boundary)),
        )
