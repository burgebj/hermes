"""Compatibility environment-variable secret provider.

This backend is useful for tests and migration paths. It is not a native
secret-storage backend; it simply adapts ``env:NAME`` references into the
common SecretProvider contract.
"""

from __future__ import annotations

import os

from ..context import SecretRequestContext
from ..errors import SecretResolutionError
from ..providers import SecretProviderStatus, SecretValue
from ..refs import SecretRef


class EnvSecretProvider:
    """Resolve ``env:VARIABLE`` references from ``os.environ``."""

    backend = "env"

    def status(self) -> SecretProviderStatus:
        return SecretProviderStatus.AVAILABLE

    def resolve(self, ref: SecretRef, context: SecretRequestContext) -> SecretValue:
        parsed = SecretRef.parse(ref)
        if parsed.backend != self.backend:
            raise SecretResolutionError(
                f"EnvSecretProvider cannot resolve backend {parsed.backend!r}"
            )

        raw = os.environ.get(parsed.name, "")
        if not raw:
            raise SecretResolutionError(
                f"Environment secret {parsed.name!r} is not set; failing closed"
            )
        return SecretValue(raw, source=parsed.display_safe)
