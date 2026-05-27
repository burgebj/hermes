"""Abstract base for provider transports.

A transport owns the data path for one api_mode:
  convert_messages → convert_tools → build_kwargs → normalize_response

It also owns canonical token-usage extraction via ``extract_usage()``,
which knows the wire format's field names and quirks (e.g. Codex/OpenAI
include cached tokens in their prompt_tokens total — the transport
subtracts them out; Anthropic's input_tokens is already net).

It does NOT own: client construction, streaming, credential refresh,
prompt caching strategy, interrupt handling, or retry logic. Those stay
on AIAgent.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from agent.transports.types import NormalizedResponse, Usage


class ProviderTransport(ABC):
    """Base class for provider-specific format conversion and normalization."""

    @property
    @abstractmethod
    def api_mode(self) -> str:
        """The api_mode string this transport handles (e.g. 'anthropic_messages')."""
        ...

    @abstractmethod
    def convert_messages(self, messages: List[Dict[str, Any]], **kwargs) -> Any:
        """Convert OpenAI-format messages to provider-native format.

        Returns provider-specific structure (e.g. (system, messages) for Anthropic,
        or the messages list unchanged for chat_completions).
        """
        ...

    @abstractmethod
    def convert_tools(self, tools: List[Dict[str, Any]]) -> Any:
        """Convert OpenAI-format tool definitions to provider-native format.

        Returns provider-specific tool list (e.g. Anthropic input_schema format).
        """
        ...

    @abstractmethod
    def build_kwargs(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **params,
    ) -> Dict[str, Any]:
        """Build the complete API call kwargs dict.

        This is the primary entry point — it typically calls convert_messages()
        and convert_tools() internally, then adds model-specific config.

        Returns a dict ready to be passed to the provider's SDK client.
        """
        ...

    @abstractmethod
    def normalize_response(self, response: Any, **kwargs) -> NormalizedResponse:
        """Normalize a raw provider response to the shared NormalizedResponse type.

        This is the only method that returns a transport-layer type.
        """
        ...

    def validate_response(self, response: Any) -> bool:
        """Optional: check if the raw response is structurally valid.

        Returns True if valid, False if the response should be treated as invalid.
        Default implementation always returns True.
        """
        return True

    def extract_usage(self, response_usage: Any) -> Usage:
        """Extract canonical token usage from a raw response.usage object.

        Each transport reads the wire-format-specific fields and returns
        a populated ``Usage``. The Codex/OpenAI variants also subtract
        cached tokens from ``prompt_tokens`` so the value is net (the
        Anthropic variant's ``input_tokens`` is already net, no subtraction).

        Default returns a zeroed ``Usage`` for transports without an
        override. Callers should pass the inner ``response.usage`` object
        — extraction never reaches into ``response`` itself.
        """
        return Usage()

    def map_finish_reason(self, raw_reason: str) -> str:
        """Optional: map provider-specific stop reason to OpenAI equivalent.

        Default returns the raw reason unchanged.  Override for providers
        with different stop reason vocabularies.
        """
        return raw_reason
