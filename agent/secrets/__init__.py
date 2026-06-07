"""Native secret-provider core contracts.

This package defines the small shared vocabulary for future Hermes secret
storage backends. A SecretRef is only a locator; SecretRequestContext and
SecretResolver decide whether a caller may resolve it.
"""

from .backends import EnvSecretProvider
from .context import CallerBoundary, RuntimeMode, SecretRequestContext
from .errors import SecretAccessDenied, SecretError, SecretRefError, SecretResolutionError
from .providers import SecretProvider, SecretProviderStatus, SecretValue
from .refs import SecretRef
from .resolver import SecretResolver

__all__ = [
    "CallerBoundary",
    "EnvSecretProvider",
    "RuntimeMode",
    "SecretAccessDenied",
    "SecretError",
    "SecretProvider",
    "SecretProviderStatus",
    "SecretRef",
    "SecretRefError",
    "SecretRequestContext",
    "SecretResolutionError",
    "SecretResolver",
    "SecretValue",
]
