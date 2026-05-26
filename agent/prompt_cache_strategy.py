"""Pluggable prompt-cache strategies.

Each provider expresses caching intent on the request differently:

    Anthropic        inline ``cache_control`` markers in messages
    Gemini explicit  POST /v1beta/cachedContents → resource ref
    OpenAI / others  fully automatic on the server side; no client work

This module factors that out into a ``PromptCacheStrategy`` protocol that
each ``ProviderProfile`` declares via ``cache_strategy_for(model)``. The
agent loop becomes a single call — no provider-specific branching.

Cache **stat extraction** (which response field carries the hit count)
is a separate concern owned by ``ProviderTransport.extract_usage()`` —
the wire format dictates the field names, independent of whether the
caller asked to cache.

This module ships in PR-1 alongside ``NoCacheStrategy`` and
``AnthropicInlineCacheStrategy``. ``GeminiResourceCacheStrategy`` (#29818)
lands in PR-2 against this same protocol.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


# ── Request-side data carriers ──────────────────────────────────────────


@dataclass
class PromptCacheIntent:
    """Provider-agnostic description of what the caller wants cached.

    Strategies may ignore fields they don't support (e.g. Anthropic
    clamps ``ttl`` to ``"5m"`` or ``"1h"``; everything else falls back
    to ``"5m"``).
    """

    ttl: str = "5m"               # "5m" | "1h" — Anthropic-specific tiers
    breakpoints: int = 4          # max marker count; Anthropic uses ≤4


@dataclass
class SessionCacheState:
    """Per-session state required by stateful strategies.

    Anthropic (inline markers) ignores this — every request is
    self-contained. Gemini explicit caching uses it to remember the
    ``cachedContents/<name>`` resource across turns in a session.
    Persisted in ``state.db.state_meta`` keyed by session_id.
    """

    session_id: str
    cache_name: Optional[str] = None     # "cachedContents/abc123…" for Gemini
    cache_key: Optional[str] = None      # hash of (system, tools) that the cache covers
    expires_at: Optional[float] = None   # unix ts when the cache TTL elapses


# ── Strategy protocol ───────────────────────────────────────────────────


@runtime_checkable
class PromptCacheStrategy(Protocol):
    """Adapter that applies a cache intent to a provider's request shape.

    Implementations live alongside their wire format:
      - ``AnthropicInlineCacheStrategy`` — this file
      - ``GeminiResourceCacheStrategy`` — to be added in PR-2
      - ``NoCacheStrategy`` — this file (universal default)

    ``apply()`` returns the messages list to send. A stateful strategy
    (Gemini) may both mutate ``session_ctx`` and return a TRIMMED message
    list with the cached prefix stripped — the cache_name reference does
    the rest. A stateless strategy (Anthropic) returns a copy with
    markers injected.
    """

    name: str

    def apply(
        self,
        messages: List[Dict[str, Any]],
        intent: PromptCacheIntent,
        session_ctx: Optional[SessionCacheState] = None,
    ) -> List[Dict[str, Any]]:
        ...


# ── No-op strategy (universal default) ──────────────────────────────────


@dataclass
class NoCacheStrategy:
    """Identity strategy used for providers without caching support
    (or where caching is server-side automatic — OpenAI / DeepSeek / xAI).

    These providers return cache stats in their response usage anyway —
    that's handled by the transport's ``extract_usage()``, not here.
    """

    name: str = "none"

    def apply(
        self,
        messages: List[Dict[str, Any]],
        intent: PromptCacheIntent,
        session_ctx: Optional[SessionCacheState] = None,
    ) -> List[Dict[str, Any]]:
        return messages


# ── Anthropic inline-marker strategy ────────────────────────────────────


_VALID_ANTHROPIC_LAYOUTS = frozenset({"native", "envelope"})


@dataclass
class AnthropicInlineCacheStrategy:
    """Inject ``cache_control`` markers into the message list.

    Two layouts exist on the wire:

      ``native``    — markers go on the inner content block (and on the
                      message envelope for ``role==tool`` / empty
                      content). Required by direct Anthropic API and any
                      gateway that speaks the native Anthropic protocol
                      (api.anthropic.com, api.minimax.io/anthropic, etc).

      ``envelope``  — markers go on the message envelope for
                      non-string content, but ``role==tool`` messages
                      are SKIPPED entirely. Used by OpenAI-wire proxies
                      that pass cache_control through to an underlying
                      Anthropic backend (OpenRouter, Nous Portal,
                      opencode-go for Qwen, etc).

    The actual marker placement logic lives in
    ``agent.prompt_caching.apply_anthropic_cache_control`` — this class
    is a thin wrapper that selects the layout via the boolean parameter
    the helper already accepts. Keeping the helper as the implementation
    means the 14 existing marker-placement unit tests in
    ``tests/agent/test_prompt_caching.py`` continue to cover this code
    without any rewrites.
    """

    layout: str = "native"
    name: str = "anthropic-inline"

    def __post_init__(self) -> None:
        if self.layout not in _VALID_ANTHROPIC_LAYOUTS:
            raise ValueError(
                f"AnthropicInlineCacheStrategy layout must be one of "
                f"{sorted(_VALID_ANTHROPIC_LAYOUTS)}, got {self.layout!r}"
            )

    def apply(
        self,
        messages: List[Dict[str, Any]],
        intent: PromptCacheIntent,
        session_ctx: Optional[SessionCacheState] = None,
    ) -> List[Dict[str, Any]]:
        # Late import: ``prompt_caching`` and ``prompt_cache_strategy``
        # live in the same package; importing at module top would create
        # a cycle once ``prompt_caching`` re-exports anything from here.
        from agent.prompt_caching import apply_anthropic_cache_control

        ttl = intent.ttl if intent.ttl in {"5m", "1h"} else "5m"
        return apply_anthropic_cache_control(
            messages,
            cache_ttl=ttl,
            native_anthropic=(self.layout == "native"),
        )


# ── Gemini server-side resource strategy ────────────────────────────────


@dataclass
class GeminiResourceCacheStrategy:
    """Marker strategy: use Gemini server-side context caching.

    Signal to conversation_loop.py that a ``cachedContents`` resource
    should be created (or reused) for the session's system instruction +
    tools. The actual HTTP call to ``POST /v1beta/cachedContents`` is made
    in the loop (which has access to the agent's credentials and state DB),
    not here.

    The resource name is threaded to ``GeminiNativeClient`` via
    ``extra_body["gemini_cached_content_name"]`` so ``build_gemini_request``
    can add ``cachedContent`` to the payload and omit ``systemInstruction``
    and ``tools`` (both are already encoded in the server-side resource).
    """

    name: str = "gemini-resource"

    def apply(
        self,
        messages: List[Dict[str, Any]],
        intent: PromptCacheIntent,
        session_ctx: Optional[SessionCacheState] = None,
    ) -> List[Dict[str, Any]]:
        return messages


# ── Public re-exports ───────────────────────────────────────────────────


__all__ = [
    "PromptCacheIntent",
    "SessionCacheState",
    "PromptCacheStrategy",
    "NoCacheStrategy",
    "AnthropicInlineCacheStrategy",
    "GeminiResourceCacheStrategy",
]
