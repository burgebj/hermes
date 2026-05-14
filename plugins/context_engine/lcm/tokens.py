"""Accurate token estimation for LCM context management.

Uses tiktoken for OpenAI models with fallbacks for other providers.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import tiktoken

logger = logging.getLogger(__name__)

# Character-to-token ratios for different model families
# Based on empirical measurements
CHAR_RATIOS = {
    "claude": 3.5,      # Claude tends to have fewer tokens per char
    "gpt": 4.0,         # OpenAI GPT models
    "llama": 4.0,       # LLaMA family
    "qwen": 4.0,        # Qwen models
    "gemini": 3.8,      # Google Gemini
    "mistral": 4.0,     # Mistral
    "default": 4.0,     # Default fallback
}

# Per-message overhead for role/metadata
MESSAGE_OVERHEAD_TOKENS = 4


@dataclass
class TokenEstimatorConfig:
    """Configuration for TokenEstimator."""
    model: str = ""
    provider: str = ""
    context_length: int = 128_000
    use_tiktoken: bool = True  # Can disable for testing


class TokenEstimator:
    """Accurate token estimation with model-specific handling.

    Uses tiktoken for OpenAI models, with character-ratio fallbacks
    for other providers.
    """

    def __init__(self, config: TokenEstimatorConfig):
        self.config = config
        self._encoding: Optional["tiktoken.Encoding"] = None
        self._initialized = False

    def _lazy_init(self):
        """Lazily initialize tiktoken encoding on first use."""
        if self._initialized:
            return

        self._initialized = True

        if not self.config.use_tiktoken:
            return

        # Try to use tiktoken for OpenAI models
        if self._should_use_tiktoken():
            self._encoding = self._get_tiktoken_encoding()

    def _should_use_tiktoken(self) -> bool:
        """Check if tiktoken should be used for this model."""
        model_lower = self.config.model.lower()
        provider_lower = self.config.provider.lower()

        # OpenAI models benefit from tiktoken
        if provider_lower == "openai" or "gpt" in model_lower:
            return True

        # Some OpenRouter models also use cl100k_base
        if provider_lower == "openrouter" and "gpt" in model_lower:
            return True

        return False

    def _get_tiktoken_encoding(self) -> Optional["tiktoken.Encoding"]:
        """Get tiktoken encoding for the model."""
        try:
            import tiktoken
        except ImportError:
            logger.debug("tiktoken not installed, using character-based estimation")
            return None

        model = self.config.model.lower()

        # Map model names to tiktoken encodings
        encoding_name = None

        # GPT-4 models
        if "gpt-4" in model or "gpt-4o" in model:
            encoding_name = "cl100k_base"
        # GPT-3.5-turbo
        elif "gpt-3.5" in model:
            encoding_name = "cl100k_base"
        # Default OpenAI encoding
        elif "gpt" in model:
            encoding_name = "cl100k_base"

        if encoding_name:
            try:
                return tiktoken.get_encoding(encoding_name)
            except Exception as e:
                logger.debug(f"Failed to get tiktoken encoding: {e}")

        # Try model-specific encoding
        try:
            return tiktoken.encoding_for_model(self.config.model)
        except Exception:
            pass

        # Fall back to cl100k_base for unknown OpenAI models
        try:
            return tiktoken.get_encoding("cl100k_base")
        except Exception:
            return None

    def estimate(self, messages: List[Dict[str, Any]]) -> int:
        """Estimate token count for a list of messages.

        This is the main entry point for token estimation.
        """
        self._lazy_init()

        if self._encoding:
            return self._estimate_with_tiktoken(messages)
        else:
            return self._estimate_with_char_ratio(messages)

    def estimate_single(self, content: str) -> int:
        """Estimate tokens for a single string."""
        self._lazy_init()

        if not content:
            return 0

        if self._encoding:
            return len(self._encoding.encode(content))
        else:
            return len(content) // self._get_char_ratio()

    def _estimate_with_tiktoken(self, messages: List[Dict[str, Any]]) -> int:
        """Accurate estimation using tiktoken."""
        total = 0

        for msg in messages:
            # Content — handle multimodal (list of parts) separately from plain strings
            content = msg.get("content") or ""
            if isinstance(content, list):
                # Multimodal: count text parts only; skip image/binary parts
                for part in content:
                    if isinstance(part, dict) and part.get("type") in ("text", "input_text"):
                        total += len(self._encoding.encode(str(part.get("text", ""))))
            else:
                total += len(self._encoding.encode(str(content)))

            # Tool calls
            for tc in msg.get("tool_calls") or []:
                if isinstance(tc, dict):
                    fn = tc.get("function", {})
                    args = fn.get("arguments", "")
                    if args:
                        total += len(self._encoding.encode(str(args)))
                else:
                    # Object-style tool call
                    fn = getattr(tc, "function", None)
                    if fn:
                        args = getattr(fn, "arguments", "")
                        if args:
                            total += len(self._encoding.encode(str(args)))

            # Message overhead
            total += MESSAGE_OVERHEAD_TOKENS

        return total

    def _estimate_with_char_ratio(self, messages: List[Dict[str, Any]]) -> int:
        """Fallback estimation using character ratio."""
        ratio = self._get_char_ratio()
        total = 0

        for msg in messages:
            # Content
            content = str(msg.get("content") or "")
            total += len(content) // ratio

            # Tool calls
            for tc in msg.get("tool_calls") or []:
                if isinstance(tc, dict):
                    args = tc.get("function", {}).get("arguments", "")
                    if args:
                        total += len(str(args)) // ratio
                else:
                    fn = getattr(tc, "function", None)
                    if fn:
                        args = getattr(fn, "arguments", "")
                        if args:
                            total += len(str(args)) // ratio

            # Message overhead
            total += MESSAGE_OVERHEAD_TOKENS

        return total

    def _get_char_ratio(self) -> int:
        """Get character-to-token ratio for the model."""
        model_lower = self.config.model.lower()
        provider_lower = self.config.provider.lower()

        # Check by provider first
        for key, ratio in CHAR_RATIOS.items():
            if key in provider_lower:
                return ratio

        # Check by model name  
        for key, ratio in CHAR_RATIOS.items():
            if key in model_lower:
                return ratio

        return CHAR_RATIOS["default"]

    @property
    def context_length(self) -> int:
        """Get the context length for this model."""
        return self.config.context_length

    @context_length.setter
    def context_length(self, value: int):
        """Set the context length."""
        self.config.context_length = value


def estimate_messages_tokens_rough(messages: List[Dict[str, Any]]) -> int:
    """Quick rough estimate without model-specific handling.

    Used for pre-flight checks where speed matters more than accuracy.
    """
    total = 0
    for msg in messages:
        content = str(msg.get("content") or "")
        total += len(content) // 4  # Rough estimate

        # Tool calls
        for tc in msg.get("tool_calls") or []:
            if isinstance(tc, dict):
                args = tc.get("function", {}).get("arguments", "")
                total += len(str(args)) // 4

        total += MESSAGE_OVERHEAD_TOKENS

    return total
