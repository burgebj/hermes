"""Secret resolver registry and deny-by-default policy gate."""

from __future__ import annotations

from collections.abc import Iterable

from .context import CallerBoundary, SecretRequestContext
from .errors import SecretAccessDenied, SecretResolutionError
from .providers import SecretProvider, SecretProviderStatus, SecretValue
from .refs import SecretRef

_ALLOWED_CALLER_BOUNDARIES = frozenset({CallerBoundary.CORE})
_ALLOWED_PURPOSES = frozenset({
    "provider_api_key",
    "provider_access_token",
    "provider_refresh_token",
    "credential_pool_seed",
    "secret_status_check",
    "test",
})


def _normalize_provider(value: str) -> str:
    return value.strip().lower().replace("_", "-")


class SecretResolver:
    """Route allowed secret-resolution requests to registered providers."""

    def __init__(self, providers: Iterable[SecretProvider] | None = None) -> None:
        self._providers: dict[str, SecretProvider] = {}
        for provider in providers or ():
            self.register(provider)

    def register(self, provider: SecretProvider) -> None:
        backend = getattr(provider, "backend", "")
        if not isinstance(backend, str) or not backend.strip():
            raise SecretResolutionError("Secret provider must declare a non-empty backend")
        self._providers[backend.strip()] = provider

    def resolve(self, ref: str | SecretRef, context: SecretRequestContext) -> SecretValue:
        parsed = SecretRef.parse(ref)
        self._authorize(parsed, context)

        provider = self._providers.get(parsed.backend)
        if provider is None:
            raise SecretResolutionError(
                f"No secret provider registered for backend {parsed.backend!r}"
            )

        status = provider.status()
        if not isinstance(status, SecretProviderStatus):
            raise SecretResolutionError(
                f"Secret provider {parsed.backend!r} returned invalid status; failing closed"
            )
        if status != SecretProviderStatus.AVAILABLE:
            raise SecretResolutionError(
                f"Secret provider {parsed.backend!r} is {status.value}; failing closed"
            )

        value = provider.resolve(parsed, context)
        if not isinstance(value, SecretValue):
            raise SecretResolutionError(
                f"Secret provider {parsed.backend!r} returned an invalid value"
            )
        return value

    def _authorize(self, ref: SecretRef, context: SecretRequestContext) -> None:
        boundary_value = getattr(context.caller_boundary, "value", str(context.caller_boundary))
        if context.caller_boundary not in _ALLOWED_CALLER_BOUNDARIES:
            raise SecretAccessDenied(
                "Secret resolution denied for caller boundary "
                f"{boundary_value!r}; secret refs are locators, not authorization"
            )
        if not context.provider:
            raise SecretAccessDenied("Secret resolution requires a provider in request context")
        if not context.purpose:
            raise SecretAccessDenied("Secret resolution requires a purpose in request context")
        if context.purpose not in _ALLOWED_PURPOSES:
            raise SecretAccessDenied(
                f"Secret resolution denied for purpose {context.purpose!r}"
            )

        requested_provider = _normalize_provider(context.provider)
        ref_provider = _normalize_provider(ref.provider_hint)
        if ref_provider and requested_provider != ref_provider:
            raise SecretAccessDenied(
                "Secret resolution denied because request context provider "
                "does not match the secret reference provider hint"
            )
