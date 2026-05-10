"""Streaming card state machine for Feishu/Lark.

Manages the full lifecycle of a streaming card reply:

    idle → creating → streaming → completed / aborted / terminated

Four independent accumulator blocks:
    - text      : main answer text
    - reasoning : think/reasoning text (shown while generating)
    - toolUse   : active tool-call tracking
    - cardKit   : card identity / sequence counter (mirrors JS cardKit block)

The controller accepts LLM token chunks via ``add_text_chunk`` /
``add_reasoning_chunk`` / ``start_tool_use`` / ``complete_tool_use`` and
pushes updates to Feishu via CardKit ``cardElement.content`` when a
``card_id`` is available. It falls back to throttled ``im.v1.message.update``
with TENANT token for deployments without CardKit permission/support.

Port of openclaw-lark ``src/card/streaming-card-controller.js`` (~1045 lines).
The primary path mirrors its CardKit v2 streaming APIs
(``streamCardContent``, ``setCardStreamingMode``, ``updateCardKitCard``);
the IM-patch path remains as fallback when CardKit is unavailable.  The
6-phase state machine and 4-block accumulator logic are equivalent.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Dict, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Phase definitions
# ---------------------------------------------------------------------------

class Phase(str, Enum):
    """Explicit state machine phases (mirrors JS PHASE_TRANSITIONS)."""

    IDLE = "idle"
    CREATING = "creating"
    STREAMING = "streaming"
    COMPLETED = "completed"
    ABORTED = "aborted"
    TERMINATED = "terminated"


# Valid forward transitions (same logic as JS PHASE_TRANSITIONS map).
_ALLOWED_TRANSITIONS: Dict[Phase, frozenset] = {
    Phase.IDLE: frozenset({Phase.CREATING, Phase.ABORTED, Phase.TERMINATED}),
    Phase.CREATING: frozenset({Phase.STREAMING, Phase.ABORTED, Phase.TERMINATED}),
    Phase.STREAMING: frozenset({Phase.COMPLETED, Phase.ABORTED, Phase.TERMINATED}),
    Phase.COMPLETED: frozenset(),
    Phase.ABORTED: frozenset(),
    Phase.TERMINATED: frozenset(),
}

TERMINAL_PHASES: frozenset = frozenset({Phase.COMPLETED, Phase.ABORTED, Phase.TERMINATED})

# Element ID used by CardKit's native typewriter stream.
STREAMING_ELEMENT_ID = "streaming_content"

# Throttle: CardKit is designed for frequent streaming; IM patch is the slower
# compatibility path.
_CARDKIT_FLUSH_THROTTLE_MS: int = 100
_IM_PATCH_FLUSH_THROTTLE_MS: int = 500
_FINAL_FLUSH_MAX_ATTEMPTS: int = 3
_FINAL_FLUSH_RETRY_SECONDS: float = 0.1


# ---------------------------------------------------------------------------
# Accumulator dataclasses (mirrors JS structured state blocks)
# ---------------------------------------------------------------------------

@dataclass
class _TextBlock:
    """Accumulates answer text across streaming tokens."""

    accumulated_text: str = ""
    completed_text: str = ""
    last_flushed_text: str = ""


@dataclass
class _ReasoningBlock:
    """Accumulates reasoning / think-tag text."""

    accumulated_reasoning_text: str = ""
    reasoning_start_time: Optional[float] = None   # epoch seconds
    reasoning_elapsed_ms: float = 0.0
    is_reasoning_phase: bool = False


@dataclass
class _StatusBlock:
    """Ephemeral in-progress status that is not kept in the final card."""

    visible_text: str = ""


@dataclass
class _ToolUseBlock:
    """Tracks the currently active tool call."""

    tool_name: Optional[str] = None
    tool_args: Optional[Any] = None
    tool_result: Optional[Any] = None
    started_at: Optional[float] = None             # epoch seconds
    elapsed_ms: float = 0.0
    is_active: bool = False
    steps: list = field(default_factory=list)       # completed steps


@dataclass
class _CardKitBlock:
    """Feishu card / message identity."""

    card_message_id: Optional[str] = None
    card_id: Optional[str] = None
    original_card_id: Optional[str] = None
    card_kit_sequence: int = 0


# ---------------------------------------------------------------------------
# Card JSON helpers
# ---------------------------------------------------------------------------

def _build_status_footer(content: str) -> Dict[str, Any]:
    """Return a schema 2.0-compatible footer/status element."""
    return {
        "tag": "markdown",
        "content": f"<font color='grey'>{content}</font>",
        "text_size": "notation",
    }


_MARKDOWN_IMAGE_OR_LINK_RE = re.compile(r"(!?)\[([^\]]*)\]\((https?://[^)\s]+)\)")
_RAW_URL_RE = re.compile(r"(?<!\]\()https?://[^\s<>)]+")
_IMAGE_EXTENSION_RE = re.compile(r"\.(?:png|jpe?g|gif|webp|bmp|svg)(?:$|[?#])", re.IGNORECASE)


def _is_card_unsafe_image_url(url: str) -> bool:
    """Return True for image URLs that Feishu CardKit may validate as img_key."""
    try:
        parsed = urlparse(url)
    except Exception:
        return False

    host = parsed.netloc.lower()
    path = parsed.path.lower()
    query = parsed.query.lower()
    if "feishucdn.com" in host and (
        "/static-resource/" in path
        or "image_size=" in query
        or "sticker_format=" in query
    ):
        return True
    return bool(_IMAGE_EXTENSION_RE.search(url))


def _sanitize_card_markdown(content: str) -> str:
    """Remove image link targets that make CardKit reject streaming cards.

    CardKit accepts normal links, but direct image resources, especially Feishu
    avatar URLs, can be interpreted as image keys and fail validation. Keep the
    human label while dropping only the unsafe image target.
    """
    if not content:
        return content

    def replace_markdown_link(match: re.Match[str]) -> str:
        bang, label, url = match.groups()
        if bang or _is_card_unsafe_image_url(url):
            return label.strip() or "图片"
        return match.group(0)

    sanitized = _MARKDOWN_IMAGE_OR_LINK_RE.sub(replace_markdown_link, content)

    def replace_raw_url(match: re.Match[str]) -> str:
        url = match.group(0)
        if _is_card_unsafe_image_url(url):
            return "图片链接"
        return url

    return _RAW_URL_RE.sub(replace_raw_url, sanitized)


def build_streaming_cardkit_initial_card() -> Dict[str, Any]:
    """Return the initial CardKit 2.0 card used for native typewriter output."""
    return {
        "schema": "2.0",
        "config": {
            "streaming_mode": True,
            "wide_screen_mode": True,
            "summary": {"content": "Processing..."},
        },
        "body": {
            "elements": [
                {
                    "tag": "markdown",
                    "content": "",
                    "text_align": "left",
                    "text_size": "normal_v2",
                    "element_id": STREAMING_ELEMENT_ID,
                },
                _build_status_footer("Generating..."),
            ],
        },
    }


def _build_streaming_card(
    text: str = "",
    reasoning_text: Optional[str] = None,
    tool_steps: Optional[list] = None,
    is_streaming: bool = True,
) -> Dict[str, Any]:
    """Return a Feishu interactive card payload dict.

    Produces a minimal card with:
    - Optional reasoning section (collapsed details block)
    - Optional tool-use steps list
    - Optional reasoning section
    - Main text body (markdown)
    - Footer tag indicating streaming / complete state

    Args:
        text: Main answer text (markdown).
        reasoning_text: Think/reasoning content; omitted if None.
        tool_steps: List of ``{"name": str, "elapsed_ms": float}`` dicts.
        is_streaming: True while reply is in progress; False for final card.

    Returns:
        Card JSON-serialisable dict compatible with Feishu ``interactive`` type.
    """
    elements: list = []
    display_text = _sanitize_card_markdown(text)
    safe_reasoning_text = _sanitize_card_markdown(reasoning_text or "")

    # Tool-use steps (active tools show a running indicator)
    if tool_steps:
        step_lines = []
        for s in tool_steps:
            if s.get("_active"):
                step_lines.append(f"- {s.get('name', 'tool')} ⏳ running...")
            else:
                step_lines.append(f"- {s.get('name', 'tool')} ({s.get('elapsed_ms', 0):.0f} ms)")
        steps_md = "\n".join(step_lines)
        elements.append({
            "tag": "markdown",
            "content": f"**Tool calls:**\n{steps_md}",
        })
        elements.append({"tag": "hr"})

    # Reasoning section
    if safe_reasoning_text:
        elements.append({
            "tag": "markdown",
            "content": f"**Thinking...**\n\n{safe_reasoning_text}",
            "text_align": "left",
        })
        elements.append({"tag": "hr"})

    # Main text. Keeping this after diagnostics gives the CardKit typewriter a
    # stable lower section to grow in instead of reordering completed metadata.
    if is_streaming:
        elements.append({
            "tag": "markdown",
            "content": display_text + "▌",
        })
    elif display_text:
        elements.append({
            "tag": "markdown",
            "content": display_text,
        })

    # Footer status. Feishu schema 2.0 rejects the legacy "note" tag, so use
    # notation-sized markdown instead.
    status_label = "Generating..." if is_streaming else "Done"
    elements.append(_build_status_footer(status_label))

    return {
        "schema": "2.0",
        "body": {"elements": elements},
    }


def _build_final_card(
    text: str,
    reasoning_text: Optional[str] = None,
    reasoning_elapsed_ms: float = 0.0,
    tool_steps: Optional[list] = None,
    elapsed_ms: float = 0.0,
    is_aborted: bool = False,
    is_error: bool = False,
) -> Dict[str, Any]:
    """Return a completed (non-streaming) card payload.

    Args:
        text: Final answer text (markdown).
        reasoning_text: Accumulated reasoning content; omitted if None/empty.
        reasoning_elapsed_ms: Duration the model spent reasoning (ms).
        tool_steps: Completed tool-call steps list.
        elapsed_ms: Total reply elapsed time (ms).
        is_aborted: True if the reply was cancelled by the user.
        is_error: True if the reply ended with an error.

    Returns:
        Card JSON-serialisable dict.
    """
    elements: list = []
    safe_reasoning_text = _sanitize_card_markdown(reasoning_text or "")

    # Reasoning section (collapsed)
    if safe_reasoning_text:
        elapsed_s = reasoning_elapsed_ms / 1000
        elements.append({
            "tag": "collapsible_panel",
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"Reasoning ({elapsed_s:.1f}s)",
                },
            },
            "elements": [{"tag": "markdown", "content": safe_reasoning_text}],
        })

    # Tool-use steps
    if tool_steps:
        steps_md = "\n".join(
            f"- {s.get('name', 'tool')} ({s.get('elapsed_ms', 0):.0f} ms)"
            for s in tool_steps
        )
        elements.append({
            "tag": "markdown",
            "content": f"**Tool calls:**\n{steps_md}",
        })

    # Main answer
    display_text = text or ("Aborted." if is_aborted else "An error occurred." if is_error else "")
    display_text = _sanitize_card_markdown(display_text)
    elements.append({"tag": "markdown", "content": display_text})

    # Footer
    total_s = elapsed_ms / 1000
    if is_aborted:
        status = f"Aborted ({total_s:.1f}s)"
    elif is_error:
        status = f"Error ({total_s:.1f}s)"
    else:
        status = f"Done ({total_s:.1f}s)"

    elements.append(_build_status_footer(status))

    return {
        "schema": "2.0",
        "body": {"elements": elements},
    }


# ---------------------------------------------------------------------------
# StreamingCardController
# ---------------------------------------------------------------------------

class StreamingCardController:
    """Streaming card state machine for Feishu/Lark IM replies.

    Manages the full lifecycle of one reply from ``idle`` through
    ``streaming`` to a terminal phase (``completed`` / ``aborted`` /
    ``terminated``).

    The controller is **not** thread-safe; use it from a single asyncio task
    or protect external access with a lock.

    Args:
        message_id: The Feishu message ID to update (``om_xxx``).  Used as
            the target for ``im.v1.message.update`` (PATCH).  If None the
            controller operates in "accumulate-only" mode and ``flush()``
            is a no-op.
        client: A ``lark_oapi.Client`` instance initialised with
            ``TENANT`` token type.  Required for the ``flush()`` call.
            May be None for unit-testing without network access.

    Example::

        ctrl = StreamingCardController(message_id="om_xxx", client=lark_client)
        await ctrl.add_text_chunk("Hello ")
        await ctrl.add_text_chunk("world!")
        await ctrl.flush()
        await ctrl.mark_completed()
    """

    def __init__(
        self,
        message_id: Optional[str],
        client: Any,
        *,
        card_id: Optional[str] = None,
    ) -> None:
        self._message_id = message_id
        self._client = client

        # ---- State machine ----
        self._phase: Phase = Phase.IDLE
        self._terminal_reason: Optional[str] = None

        # ---- Accumulator blocks ----
        self.text = _TextBlock()
        self.reasoning = _ReasoningBlock()
        self.status = _StatusBlock()
        self.tool_use = _ToolUseBlock()
        self.card_kit = _CardKitBlock(
            card_message_id=message_id,
            card_id=card_id,
            original_card_id=card_id,
            card_kit_sequence=1 if card_id else 0,
        )

        # ---- Lifecycle ----
        self._dispatch_start_time: float = time.time()
        self._last_flush_time: float = 0.0
        self._flush_lock: asyncio.Lock = asyncio.Lock()
        self._pending_flush: bool = False
        self._pending_flush_task: Optional[asyncio.Task] = None

    # ------------------------------------------------------------------
    # Public accessors
    # ------------------------------------------------------------------

    @property
    def phase(self) -> Phase:
        """Current state machine phase."""
        return self._phase

    @property
    def is_terminal_phase(self) -> bool:
        """True if the controller has reached a terminal phase."""
        return self._phase in TERMINAL_PHASES

    @property
    def is_aborted(self) -> bool:
        """True if the reply was explicitly aborted."""
        return self._phase == Phase.ABORTED

    @property
    def terminal_reason(self) -> Optional[str]:
        """Human-readable reason for entering a terminal phase, or None."""
        return self._terminal_reason

    def elapsed_ms(self) -> float:
        """Elapsed milliseconds since the controller was created."""
        return (time.time() - self._dispatch_start_time) * 1000

    # ------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------

    def _transition(self, to: Phase, source: str, reason: Optional[str] = None) -> bool:
        """Attempt a phase transition.

        Args:
            to: Target phase.
            source: Caller label used for log messages.
            reason: Optional human-readable reason recorded in
                ``terminal_reason`` when entering a terminal phase.

        Returns:
            True if the transition was accepted; False if rejected.
        """
        from_phase = self._phase
        if from_phase == to:
            return False
        allowed = _ALLOWED_TRANSITIONS.get(from_phase, frozenset())
        if to not in allowed:
            logger.warning(
                "streaming_card: phase transition rejected from=%s to=%s source=%s",
                from_phase.value, to.value, source,
            )
            return False
        self._phase = to
        logger.info(
            "streaming_card: phase transition from=%s to=%s source=%s reason=%s",
            from_phase.value, to.value, source, reason,
        )
        if to in TERMINAL_PHASES:
            self._terminal_reason = reason
            self._on_enter_terminal_phase()
        return True

    def _on_enter_terminal_phase(self) -> None:
        """Hook called immediately upon entering any terminal phase."""
        self._pending_flush = False

    # ------------------------------------------------------------------
    # Tool-use helpers
    # ------------------------------------------------------------------

    def _mark_tool_use_activity(self, *, reset_timer: bool = False) -> None:
        if reset_timer or not self.tool_use.started_at:
            self.tool_use.started_at = time.time()
        self.tool_use.elapsed_ms = (time.time() - self.tool_use.started_at) * 1000
        self.tool_use.is_active = True

    def _capture_tool_use_elapsed(self) -> None:
        if not self.tool_use.started_at:
            return
        # Round to int to avoid float trailing-zero false-negative dedup.
        self.tool_use.elapsed_ms = int(round((time.time() - self.tool_use.started_at) * 1000))
        self.tool_use.is_active = False

    # ------------------------------------------------------------------
    # Public API: chunk ingestion
    # ------------------------------------------------------------------

    # Max characters to accumulate before truncating (Feishu card content limit ~30k).
    _MAX_ACCUMULATED_TEXT: int = 28_000
    _TRUNCATION_SUFFIX: str = "...[truncated]"

    async def add_text_chunk(self, chunk: str) -> None:
        """Append a text token to the answer accumulator.

        Transitions from ``idle`` to ``creating`` → ``streaming`` on first
        call if the controller has not yet started.  Schedules a throttled
        flush after accumulating.

        Empty string or None chunks are silently ignored (noop) — this is
        intentional to handle LLM stream events that emit empty deltas.

        Args:
            chunk: Raw text token from the LLM stream.
        """
        if not chunk:
            return
        if self.is_terminal_phase:
            return

        self._capture_tool_use_elapsed()
        self.status.visible_text = ""

        # Exit reasoning phase if we were in it
        if self.reasoning.is_reasoning_phase:
            self.reasoning.is_reasoning_phase = False
            if self.reasoning.reasoning_start_time:
                self.reasoning.reasoning_elapsed_ms = (
                    (time.time() - self.reasoning.reasoning_start_time) * 1000
                )

        self.text.accumulated_text += chunk

        # Enforce Feishu card content limit (~30k chars). Truncate with warning.
        if len(self.text.accumulated_text) > self._MAX_ACCUMULATED_TEXT:
            self.text.accumulated_text = (
                self.text.accumulated_text[:27_000] + self._TRUNCATION_SUFFIX
            )
            logger.warning(
                "streaming_card: accumulated_text truncated at 27000 chars "
                "message_id=%s",
                self.card_kit.card_message_id,
            )

        await self._ensure_streaming()
        if not self.is_terminal_phase:
            await self._schedule_flush()

    async def add_reasoning_chunk(self, chunk: str) -> None:
        """Append a reasoning/think token to the reasoning accumulator.

        Args:
            chunk: Reasoning text token (e.g. content inside ``<think>`` tags).
        """
        if not chunk:
            return
        if self.is_terminal_phase:
            return

        if not self.reasoning.reasoning_start_time:
            self.reasoning.reasoning_start_time = time.time()

        self.status.visible_text = ""
        self.reasoning.is_reasoning_phase = True
        self.reasoning.accumulated_reasoning_text += chunk

        await self._ensure_streaming()
        if not self.is_terminal_phase:
            await self._schedule_flush()

    def start_tool_use(self, tool_name: str, args: Any = None) -> None:
        """Record the start of a tool call.

        Args:
            tool_name: Name of the tool being invoked.
            args: Tool input arguments (arbitrary JSON-serialisable value).
        """
        if self.is_terminal_phase:
            return
        self.tool_use.tool_name = tool_name
        self.tool_use.tool_args = args
        self.tool_use.tool_result = None
        self.status.visible_text = ""
        self._mark_tool_use_activity(reset_timer=True)
        logger.debug("streaming_card: tool_use started name=%s", tool_name)

    async def set_status(self, content: str) -> None:
        """Show an ephemeral streaming status without retaining it as reasoning."""
        if not content:
            return
        if self.is_terminal_phase:
            return
        self.status.visible_text = content
        await self._ensure_streaming()
        if not self.is_terminal_phase:
            await self._schedule_flush()

    def complete_tool_use(self, result: Any = None) -> None:
        """Record the completion of the current tool call.

        Appends a step to the completed steps list and resets the active
        tool-use block.

        Args:
            result: Tool output (arbitrary JSON-serialisable value).
        """
        self._capture_tool_use_elapsed()
        step = {
            "name": self.tool_use.tool_name or "tool",
            "args": self.tool_use.tool_args,
            "result": result,
            "elapsed_ms": self.tool_use.elapsed_ms,
        }
        self.tool_use.steps.append(step)
        self.tool_use.tool_name = None
        self.tool_use.tool_args = None
        self.tool_use.tool_result = None
        self.tool_use.started_at = None
        self.tool_use.elapsed_ms = 0.0
        self.tool_use.is_active = False
        logger.debug("streaming_card: tool_use completed step=%s", step.get("name"))

    async def mark_tool_started(self, tool_name: str, args: Any = None) -> None:
        """Show an active tool-use row and flush the card."""
        if self.is_terminal_phase:
            return
        self.start_tool_use(tool_name, args=args)
        await self._ensure_streaming()
        if not self.is_terminal_phase:
            await self._schedule_flush()

    async def mark_tool_completed(self, result: Any = None) -> None:
        """Record a completed tool-use row and flush the card."""
        if self.is_terminal_phase:
            return
        self.complete_tool_use(result=result)
        await self._ensure_streaming()
        if not self.is_terminal_phase:
            await self._schedule_flush()

    # ------------------------------------------------------------------
    # Public API: lifecycle control
    # ------------------------------------------------------------------

    async def mark_completed(self) -> None:
        """Finalize the reply with a completed-state card.

        Waits for any in-flight scheduled flush to complete, then transitions
        to ``completed`` and sends a final non-streaming card update to Feishu.
        """
        if self.is_terminal_phase:
            return
        # Wait for any in-flight scheduled flush before taking the terminal path.
        if self._pending_flush_task and not self._pending_flush_task.done():
            try:
                await self._pending_flush_task
            except Exception:
                pass
        self._capture_tool_use_elapsed()
        self.text.completed_text = self.text.accumulated_text
        self._transition(Phase.COMPLETED, "mark_completed", "normal")
        await self._flush_final(is_aborted=False, is_error=False)

    async def abort(self) -> None:
        """Abort the reply and send a terminal aborted card.

        Safe to call even if the controller is already in a terminal phase
        (becomes a no-op).
        """
        if self.is_terminal_phase:
            return
        self._capture_tool_use_elapsed()
        if not self._transition(Phase.ABORTED, "abort", "abort"):
            return
        await self._flush_final(is_aborted=True, is_error=False)

    async def terminate(self, reason: str = "unavailable") -> None:
        """Terminate the pipeline (e.g. message was deleted/recalled).

        Args:
            reason: Human-readable termination reason.
        """
        self._transition(Phase.TERMINATED, "terminate", reason)

    # ------------------------------------------------------------------
    # Public API: card JSON snapshot
    # ------------------------------------------------------------------

    def to_card_json(self) -> Dict[str, Any]:
        """Return the current card state as a Feishu card payload dict.

        Generates either a streaming in-progress card or a final completed
        card depending on the current phase.

        Returns:
            JSON-serialisable dict ready to pass as the ``content`` field of
            a Feishu ``interactive`` message.
        """
        in_terminal = self.is_terminal_phase

        if in_terminal:
            return _build_final_card(
                text=self.text.completed_text or self.text.accumulated_text,
                reasoning_text=self.reasoning.accumulated_reasoning_text or None,
                reasoning_elapsed_ms=self.reasoning.reasoning_elapsed_ms,
                tool_steps=self.tool_use.steps or None,
                elapsed_ms=self.elapsed_ms(),
                is_aborted=self.is_aborted,
                is_error=False,
            )

        # Build visible tool steps: completed steps + active tool placeholder.
        visible_steps = list(self.tool_use.steps)
        if self.tool_use.is_active and self.tool_use.tool_name:
            visible_steps.append({
                "name": self.tool_use.tool_name,
                "elapsed_ms": self.tool_use.elapsed_ms,
                "_active": True,
            })

        return _build_streaming_card(
            text=self.text.accumulated_text,
            reasoning_text=(
                self.reasoning.accumulated_reasoning_text
                if self.reasoning.is_reasoning_phase
                else None
            ),
            tool_steps=visible_steps or None,
            is_streaming=True,
        )

    # ------------------------------------------------------------------
    # Public API: explicit flush
    # ------------------------------------------------------------------

    async def flush(self) -> None:
        """Immediately push the current card state to Feishu.

        Calls ``im.v1.message.update`` (PATCH) with TENANT token.
        Safe to call at any time; becomes a no-op if no message ID or
        client is configured.
        """
        await self._perform_flush()

    # ------------------------------------------------------------------
    # Internal: streaming lifecycle
    # ------------------------------------------------------------------

    async def _ensure_streaming(self) -> None:
        """Transition from idle → creating → streaming if not already there."""
        if self._phase == Phase.STREAMING:
            return
        if self._phase == Phase.IDLE:
            self._transition(Phase.CREATING, "_ensure_streaming")
        if self._phase == Phase.CREATING:
            self._transition(Phase.STREAMING, "_ensure_streaming")

    # ------------------------------------------------------------------
    # Internal: throttled flush scheduling
    # ------------------------------------------------------------------

    async def _schedule_flush(self) -> None:
        """Schedule a flush respecting the throttle window.

        If a flush was performed recently, waits for the remainder of the
        throttle window before flushing.  Concurrent calls are coalesced —
        only one pending flush runs at a time.

        Saves the task reference to ``_pending_flush_task`` so that
        ``mark_completed`` can await it before entering the terminal path.
        """
        if self.is_terminal_phase:
            return
        if self._pending_flush:
            return  # already scheduled

        now_ms = time.time() * 1000
        elapsed_since_flush = now_ms - self._last_flush_time
        throttle_ms = (
            _CARDKIT_FLUSH_THROTTLE_MS
            if self.card_kit.card_id
            else _IM_PATCH_FLUSH_THROTTLE_MS
        )
        delay_ms = max(0.0, throttle_ms - elapsed_since_flush)

        self._pending_flush = True

        async def _do_flush_after_delay() -> None:
            if delay_ms > 0:
                await asyncio.sleep(delay_ms / 1000)
            self._pending_flush = False
            if not self.is_terminal_phase:
                await self._perform_flush()

        task = asyncio.ensure_future(_do_flush_after_delay())
        self._pending_flush_task = task

    # ------------------------------------------------------------------
    # Internal: actual Feishu PATCH call
    # ------------------------------------------------------------------

    async def _perform_flush(self) -> None:
        """Push current card content to Feishu.

        Uses CardKit ``cardElement.content`` for native typewriter streaming
        when ``card_id`` is available. Otherwise falls back to
        ``im.v1.message.update``. Skips silently if target identity or client
        is not set.
        """
        if not self.card_kit.card_message_id or not self._client:
            return
        if self.is_terminal_phase:
            return

        if self.card_kit.card_id:
            content = self._build_cardkit_stream_content()
            if not content or content == self.text.last_flushed_text:
                return
            async with self._flush_lock:
                try:
                    await self._stream_cardkit_content(content)
                    self.text.last_flushed_text = content
                    self._last_flush_time = time.time() * 1000
                    logger.debug(
                        "streaming_card: cardkit flushed message_id=%s card_id=%s phase=%s",
                        self.card_kit.card_message_id,
                        self.card_kit.card_id,
                        self._phase.value,
                    )
                except Exception as exc:
                    logger.warning(
                        "streaming_card: cardkit flush failed message_id=%s card_id=%s error=%s",
                        self.card_kit.card_message_id,
                        self.card_kit.card_id,
                        exc,
                    )
                    self.card_kit.card_id = None
            return

        if self.card_kit.original_card_id:
            logger.debug(
                "streaming_card: skipping IM patch for CardKit card message_id=%s "
                "original_card_id=%s",
                self.card_kit.card_message_id,
                self.card_kit.original_card_id,
            )
            return

        card_payload = self.to_card_json()
        card_json = json.dumps(card_payload, ensure_ascii=False)
        # Skip if nothing changed since last flush
        if card_json == self.text.last_flushed_text:
            return

        async with self._flush_lock:
            try:
                await self._patch_message(card_json)
                self.text.last_flushed_text = card_json
                self._last_flush_time = time.time() * 1000
                logger.debug(
                    "streaming_card: flushed message_id=%s phase=%s",
                    self.card_kit.card_message_id, self._phase.value,
                )
            except Exception as exc:
                logger.warning(
                    "streaming_card: flush failed message_id=%s error=%s",
                    self.card_kit.card_message_id, exc,
                )

    async def _flush_final(
        self, is_aborted: bool = False, is_error: bool = False
    ) -> None:
        """Push the final terminal card to Feishu.

        Acquires ``_flush_lock`` to prevent a concurrent in-progress
        ``_perform_flush`` (running in ThreadPoolExecutor) from racing with
        this final PATCH.

        Args:
            is_aborted: Pass True when the reply was cancelled.
            is_error: Pass True when the reply ended with an error.
        """
        if not self.card_kit.card_message_id or not self._client:
            return

        card_payload = _build_final_card(
            text=self.text.completed_text or self.text.accumulated_text,
            reasoning_text=self.reasoning.accumulated_reasoning_text or None,
            reasoning_elapsed_ms=self.reasoning.reasoning_elapsed_ms,
            tool_steps=self.tool_use.steps or None,
            elapsed_ms=self.elapsed_ms(),
            is_aborted=is_aborted,
            is_error=is_error,
        )
        card_json = json.dumps(card_payload, ensure_ascii=False)

        async with self._flush_lock:
            last_error: Optional[Exception] = None
            for attempt in range(1, _FINAL_FLUSH_MAX_ATTEMPTS + 1):
                effective_card_id = self._effective_cardkit_card_id()
                try:
                    if effective_card_id:
                        await self._close_cardkit_streaming_mode()
                        await self._update_cardkit_card(card_json)
                    else:
                        await self._patch_message(card_json)
                    logger.info(
                        "streaming_card: final card sent message_id=%s card_id=%s "
                        "aborted=%s error=%s attempt=%s",
                        self.card_kit.card_message_id,
                        effective_card_id,
                        is_aborted,
                        is_error,
                        attempt,
                    )
                    return
                except Exception as exc:
                    last_error = exc
                    logger.warning(
                        "streaming_card: final flush failed message_id=%s "
                        "card_id=%s attempt=%s/%s error=%s",
                        self.card_kit.card_message_id,
                        effective_card_id,
                        attempt,
                        _FINAL_FLUSH_MAX_ATTEMPTS,
                        exc,
                    )
                    if attempt < _FINAL_FLUSH_MAX_ATTEMPTS:
                        await asyncio.sleep(_FINAL_FLUSH_RETRY_SECONDS * attempt)
            if last_error is not None:
                raise last_error

    def _effective_cardkit_card_id(self) -> Optional[str]:
        """Return the CardKit id needed for terminal close/update."""
        return self.card_kit.card_id or self.card_kit.original_card_id

    def _build_cardkit_stream_content(self) -> str:
        """Build the cumulative markdown sent to CardKit's streaming element."""
        sections: list[str] = []
        visible_steps = list(self.tool_use.steps)
        if self.tool_use.is_active and self.tool_use.tool_name:
            visible_steps.append({
                "name": self.tool_use.tool_name,
                "elapsed_ms": self.tool_use.elapsed_ms,
                "_active": True,
            })
        if visible_steps:
            lines = []
            for step in visible_steps:
                name = step.get("name") or "tool"
                if step.get("_active"):
                    lines.append(f"- {name} running...")
                else:
                    lines.append(f"- {name} ({step.get('elapsed_ms', 0):.0f} ms)")
            sections.append("**Tool calls:**\n" + "\n".join(lines))
        if self.reasoning.accumulated_reasoning_text:
            sections.append("**Reasoning...**")
        elif self.status.visible_text and not self.text.accumulated_text:
            sections.append(self.status.visible_text)
        if self.text.accumulated_text:
            sections.append(self.text.accumulated_text)
        return _sanitize_card_markdown("\n\n".join(section for section in sections if section))

    async def _stream_cardkit_content(self, content: str) -> None:
        """Call CardKit ``cardElement.content`` with cumulative markdown."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._sync_stream_cardkit_content, content)

    def _sync_stream_cardkit_content(self, content: str) -> None:
        try:
            from lark_oapi.api.cardkit.v1 import (
                ContentCardElementRequest,
                ContentCardElementRequestBody,
            )
        except ImportError as exc:
            logger.error("streaming_card: lark_oapi cardkit not available: %s", exc)
            return

        card_id = self.card_kit.card_id
        if not card_id:
            return

        self.card_kit.card_kit_sequence += 1
        sequence = self.card_kit.card_kit_sequence
        body = (
            ContentCardElementRequestBody.builder()
            .content(content)
            .sequence(sequence)
            .build()
        )
        request = (
            ContentCardElementRequest.builder()
            .card_id(card_id)
            .element_id(STREAMING_ELEMENT_ID)
            .request_body(body)
            .build()
        )
        response = self._client.cardkit.v1.card_element.content(request)
        code = getattr(response, "code", None)
        msg = getattr(response, "msg", "")
        logger.info(
            "streaming_card: cardElement.content message_id=%s card_id=%s seq=%s content_len=%s",
            self.card_kit.card_message_id,
            card_id,
            sequence,
            len(content),
        )
        if code not in (None, 0):
            raise RuntimeError(f"cardElement.content failed code={code} msg={msg}")

    async def _close_cardkit_streaming_mode(self) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._sync_close_cardkit_streaming_mode)

    def _sync_close_cardkit_streaming_mode(self) -> None:
        try:
            from lark_oapi.api.cardkit.v1 import (
                SettingsCardRequest,
                SettingsCardRequestBody,
            )
        except ImportError as exc:
            logger.error("streaming_card: lark_oapi cardkit not available: %s", exc)
            return

        card_id = self._effective_cardkit_card_id()
        if not card_id:
            return

        self.card_kit.card_kit_sequence += 1
        sequence = self.card_kit.card_kit_sequence
        body = (
            SettingsCardRequestBody.builder()
            .settings(json.dumps({"streaming_mode": False}, ensure_ascii=False))
            .sequence(sequence)
            .build()
        )
        request = (
            SettingsCardRequest.builder()
            .card_id(card_id)
            .request_body(body)
            .build()
        )
        response = self._client.cardkit.v1.card.settings(request)
        code = getattr(response, "code", None)
        msg = getattr(response, "msg", "")
        logger.info(
            "streaming_card: card.settings message_id=%s card_id=%s seq=%s streaming_mode=false",
            self.card_kit.card_message_id,
            card_id,
            sequence,
        )
        if code not in (None, 0):
            raise RuntimeError(f"card.settings failed code={code} msg={msg}")

    async def _update_cardkit_card(self, card_json: str) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._sync_update_cardkit_card, card_json)

    def _sync_update_cardkit_card(self, card_json: str) -> None:
        try:
            from lark_oapi.api.cardkit.v1 import (
                Card as CardKitCard,
                UpdateCardRequest,
                UpdateCardRequestBody,
            )
        except ImportError as exc:
            logger.error("streaming_card: lark_oapi cardkit not available: %s", exc)
            return

        card_id = self._effective_cardkit_card_id()
        if not card_id:
            return

        self.card_kit.card_kit_sequence += 1
        sequence = self.card_kit.card_kit_sequence
        card = CardKitCard.builder().type("card_json").data(card_json).build()
        body = (
            UpdateCardRequestBody.builder()
            .card(card)
            .sequence(sequence)
            .build()
        )
        request = (
            UpdateCardRequest.builder()
            .card_id(card_id)
            .request_body(body)
            .build()
        )
        response = self._client.cardkit.v1.card.update(request)
        code = getattr(response, "code", None)
        msg = getattr(response, "msg", "")
        logger.info(
            "streaming_card: card.update message_id=%s card_id=%s seq=%s",
            self.card_kit.card_message_id,
            card_id,
            sequence,
        )
        if code not in (None, 0):
            raise RuntimeError(f"card.update failed code={code} msg={msg}")

    async def _patch_message(self, card_json: str) -> None:
        """Call Feishu ``im.v1.message.update`` (PATCH) with TENANT token.

        Wraps the synchronous lark_oapi SDK call in a thread executor so it
        does not block the asyncio event loop.

        Args:
            card_json: JSON string of the card payload.
        """
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._sync_patch_message, card_json)

    def _sync_patch_message(self, card_json: str) -> None:
        """Synchronous Feishu message patch via lark_oapi BaseRequest.

        Uses AccessTokenType.TENANT (TENANT-only API requirement for
        ``im.v1.message.update``).

        Args:
            card_json: JSON string of the card payload.
        """
        try:
            from lark_oapi import AccessTokenType
            from lark_oapi.core.enum import HttpMethod
            from lark_oapi.core.model.base_request import BaseRequest
        except ImportError as exc:
            logger.error("streaming_card: lark_oapi not available: %s", exc)
            return

        message_id = self.card_kit.card_message_id
        uri = f"/open-apis/im/v1/messages/{message_id}"

        body = {
            "msg_type": "interactive",
            "content": card_json,
        }

        request = (
            BaseRequest.builder()
            .http_method(HttpMethod.PATCH)
            .uri(uri)
            .token_types({AccessTokenType.TENANT})
            .body(body)
            .build()
        )

        response = self._client.request(request)
        code = getattr(response, "code", None)
        msg = getattr(response, "msg", "")

        if code not in (None, 0):
            logger.warning(
                "streaming_card: PATCH failed code=%s msg=%s message_id=%s",
                code, msg, message_id,
            )

    # ------------------------------------------------------------------
    # Async iterator integration
    # ------------------------------------------------------------------

    async def consume_stream(
        self,
        stream: AsyncIterator[str],
        *,
        flush_on_complete: bool = True,
    ) -> None:
        """Consume an async LLM token stream and accumulate to text block.

        Convenience method for feeding a raw text stream directly into the
        controller.  Each yielded string is passed to ``add_text_chunk``.

        Args:
            stream: Async iterator yielding raw text tokens.
            flush_on_complete: If True, calls ``mark_completed()`` after the
                stream is exhausted.  Set to False when you want to manage
                the lifecycle manually (e.g. to send a final card with
                additional metadata before completing).

        Example::

            async def my_llm_stream():
                yield "Hello "
                yield "world!"

            await ctrl.consume_stream(my_llm_stream())
        """
        async for chunk in stream:
            if self.is_terminal_phase:
                break
            await self.add_text_chunk(chunk)

        if flush_on_complete and not self.is_terminal_phase:
            await self.mark_completed()

    def __repr__(self) -> str:
        return (
            f"StreamingCardController("
            f"message_id={self.card_kit.card_message_id!r}, "
            f"phase={self._phase.value!r}, "
            f"text_len={len(self.text.accumulated_text)}, "
            f"reasoning_len={len(self.reasoning.accumulated_reasoning_text)}"
            f")"
        )
