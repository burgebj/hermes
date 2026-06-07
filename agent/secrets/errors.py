"""Exceptions for Hermes secret-provider resolution."""


class SecretError(RuntimeError):
    """Base class for secret-provider errors."""


class SecretRefError(ValueError, SecretError):
    """Raised when a secret reference string is malformed."""


class SecretResolutionError(SecretError):
    """Raised when a secret cannot be resolved safely."""


class SecretAccessDenied(SecretResolutionError):
    """Raised when caller context is not authorized to resolve a secret."""
