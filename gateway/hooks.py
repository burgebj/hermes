"""
Event Hook System

A lightweight event-driven system that fires handlers at key lifecycle points.

There are two ways to register a handler:

1. **File-system discovery** — drop a directory into ``~/.hermes/hooks/``
   containing ``HOOK.yaml`` (metadata: name, description, events list) and
   ``handler.py`` (with ``def handle(event_type, context)``, sync or async).
   These are loaded by :meth:`HookRegistry.discover_and_load` at gateway
   startup.

2. **Programmatic registration** — call :meth:`HookRegistry.register` from
   inside the process. Useful for plugins that ship their own bundled hooks
   without expecting the user to maintain a ``~/.hermes/hooks/`` entry. Pairs
   with :func:`get_default_registry` so plugins don't have to hold a registry
   reference threaded through every call site.

Events fired today:

  - ``gateway:startup``    — Gateway process starts
  - ``session:start``      — New session created (first message of a new session)
  - ``session:end``        — Session ends (user ran /new or /reset)
  - ``session:reset``      — Session reset completed (new session entry created)
  - ``agent:start``        — Agent begins processing a message
  - ``agent:step``         — Each turn in the tool-calling loop
  - ``agent:end``          — Agent finishes processing
  - ``command:*``          — Any slash command executed (wildcard match)
  - ``tui:<sub-event>``    — Any TUI gateway dispatch event mirrored to the
                             bus (``tui:tool.start``, ``tui:message.delta``,
                             ``tui:reasoning.available``, etc.). Subscribe
                             with the full name for one event, or
                             ``tui:*`` for all of them.

Wildcards match one colon-separated namespace level: a handler registered for
``foo:*`` fires for every ``foo:<anything>`` event, but not for
``bar:something``.

Errors in hooks are caught and logged but never block the main pipeline.
"""

import asyncio
import importlib.util
import sys
from typing import Any, Callable, Dict, List, Optional

import yaml

from hermes_cli.config import get_hermes_home


HOOKS_DIR = get_hermes_home() / "hooks"


# Tracks handler functions we've already warned about for emit_sync's
# async-without-loop case, so each bad combination only logs once per
# process instead of flooding stderr on every event.
_ASYNC_NO_LOOP_WARNED: "set[int]" = set()


class HookRegistry:
    """
    Discovers, loads, and fires event hooks.

    Usage:
        registry = HookRegistry()
        registry.discover_and_load()
        await registry.emit("agent:start", {"platform": "telegram", ...})
    """

    def __init__(self):
        # event_type -> [handler_fn, ...]
        self._handlers: Dict[str, List[Callable]] = {}
        self._loaded_hooks: List[dict] = []  # metadata for listing

    @property
    def loaded_hooks(self) -> List[dict]:
        """Return metadata about all loaded hooks."""
        return list(self._loaded_hooks)

    def register(
        self,
        event_type: str,
        handler: Callable,
        *,
        name: Optional[str] = None,
    ) -> Callable[[], None]:
        """Programmatically register a handler for ``event_type``.

        Intended for in-process plugins, tests, and built-in hooks. Pairs with
        the file-system discovery path (HOOK.yaml + handler.py) — both share
        the same dispatch and wildcard rules.

        The handler signature matches discovered hooks: ``handle(event_type,
        context)`` where ``handler`` may be sync or async.

        Returns a callable that, when invoked, removes this specific handler
        registration from the registry. Other handlers for the same event are
        unaffected.

        Args:
            event_type: Event identifier such as ``agent:start`` or
                ``tui:tool.start``. May also be a wildcard like ``command:*``.
            handler:    Function or coroutine function to invoke when the
                event fires.
            name:       Optional friendly name recorded alongside the
                registration metadata for listing/debugging. Defaults to the
                handler's ``__name__``.

        Returns:
            A no-arg callable that unregisters this handler when called.
        """
        self._handlers.setdefault(event_type, []).append(handler)

        meta = {
            "name": name or getattr(handler, "__name__", "<anonymous>"),
            "description": "(registered programmatically)",
            "events": [event_type],
            "path": "<programmatic>",
        }
        self._loaded_hooks.append(meta)

        def _unregister() -> None:
            try:
                self._handlers.get(event_type, []).remove(handler)
            except ValueError:
                pass
            try:
                self._loaded_hooks.remove(meta)
            except ValueError:
                pass

        return _unregister

    def _register_builtin_hooks(self) -> None:
        """Register built-in hooks that are always active.

        Currently empty — no shipped built-in hooks. Kept as the extension
        point for future always-on gateway hooks so they drop in without
        re-plumbing discover_and_load().
        """
        return

    def discover_and_load(self) -> None:
        """
        Scan the hooks directory for hook directories and load their handlers.

        Also registers built-in hooks that are always active.

        Each hook directory must contain:
          - HOOK.yaml with at least 'name' and 'events' keys
          - handler.py with a top-level 'handle' function (sync or async)
        """
        self._register_builtin_hooks()

        if not HOOKS_DIR.exists():
            return

        for hook_dir in sorted(HOOKS_DIR.iterdir()):
            if not hook_dir.is_dir():
                continue

            manifest_path = hook_dir / "HOOK.yaml"
            handler_path = hook_dir / "handler.py"

            if not manifest_path.exists() or not handler_path.exists():
                continue

            try:
                manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
                if not manifest or not isinstance(manifest, dict):
                    print(f"[hooks] Skipping {hook_dir.name}: invalid HOOK.yaml", flush=True)
                    continue

                hook_name = manifest.get("name", hook_dir.name)
                events = manifest.get("events", [])
                if not events:
                    print(f"[hooks] Skipping {hook_name}: no events declared", flush=True)
                    continue

                # Dynamically load the handler module.
                # Register in sys.modules BEFORE exec_module so Pydantic /
                # dataclasses / typing introspection can resolve forward
                # references (triggered by `from __future__ import annotations`
                # in the handler). Without this, a handler that declares a
                # Pydantic BaseModel for webhook/event payloads fails at first
                # dispatch with "TypeAdapter ... is not fully defined".
                module_name = f"hermes_hook_{hook_name}"
                spec = importlib.util.spec_from_file_location(
                    module_name, handler_path
                )
                if spec is None or spec.loader is None:
                    print(f"[hooks] Skipping {hook_name}: could not load handler.py", flush=True)
                    continue

                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                try:
                    spec.loader.exec_module(module)
                except Exception:
                    sys.modules.pop(module_name, None)
                    raise

                handle_fn = getattr(module, "handle", None)
                if handle_fn is None:
                    print(f"[hooks] Skipping {hook_name}: no 'handle' function found", flush=True)
                    continue

                # Register the handler for each declared event
                for event in events:
                    self._handlers.setdefault(event, []).append(handle_fn)

                self._loaded_hooks.append({
                    "name": hook_name,
                    "description": manifest.get("description", ""),
                    "events": events,
                    "path": str(hook_dir),
                })

                print(f"[hooks] Loaded hook '{hook_name}' for events: {events}", flush=True)

            except Exception as e:
                print(f"[hooks] Error loading hook {hook_dir.name}: {e}", flush=True)

    def _resolve_handlers(self, event_type: str) -> List[Callable]:
        """Return all handlers that should fire for ``event_type``.

        Exact matches fire first, followed by wildcard matches (e.g.
        ``command:*`` matches ``command:reset``).
        """
        handlers = list(self._handlers.get(event_type, []))
        if ":" in event_type:
            base = event_type.split(":")[0]
            wildcard_key = f"{base}:*"
            handlers.extend(self._handlers.get(wildcard_key, []))
        return handlers

    async def emit(self, event_type: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Fire all handlers registered for an event, discarding return values.

        Supports wildcard matching: handlers registered for "command:*" will
        fire for any "command:..." event. Handlers registered for a base type
        like "agent" won't fire for "agent:start" -- only exact matches and
        explicit wildcards.

        Args:
            event_type: The event identifier (e.g. "agent:start").
            context:    Optional dict with event-specific data.
        """
        if context is None:
            context = {}

        for fn in self._resolve_handlers(event_type):
            try:
                result = fn(event_type, context)
                # Support both sync and async handlers
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                print(f"[hooks] Error in handler for '{event_type}': {e}", flush=True)

    async def emit_collect(
        self,
        event_type: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Any]:
        """Fire handlers and return their non-None return values in order.

        Like :meth:`emit` but captures each handler's return value. Used for
        decision-style hooks (e.g. ``command:<name>`` policies that want to
        allow/deny/rewrite the command before normal dispatch).

        Exceptions from individual handlers are logged but do not abort the
        remaining handlers.
        """
        if context is None:
            context = {}

        results: List[Any] = []
        for fn in self._resolve_handlers(event_type):
            try:
                result = fn(event_type, context)
                if asyncio.iscoroutine(result):
                    result = await result
                if result is not None:
                    results.append(result)
            except Exception as e:
                print(f"[hooks] Error in handler for '{event_type}': {e}", flush=True)
        return results

    def emit_sync(
        self,
        event_type: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Fire handlers from a synchronous caller.

        Companion to :meth:`emit` for hot-path callers that cannot await — most
        notably ``tui_gateway/server.py:_emit``, which serves both async dispatch
        paths and sync callback paths and must remain ``def`` (not ``async
        def``).

        Behavior:

        - Sync handlers run immediately, in registration order. Exceptions are
          caught and logged so a buggy handler can't break the host pipeline.
        - Async handlers (coroutine functions) are scheduled via
          ``asyncio.ensure_future`` if a running event loop is available in the
          current thread. If no loop is running, the handler is **skipped** and
          a one-time warning is logged per handler — async handlers in a
          purely sync process don't have a way to make forward progress.

        Like :meth:`emit`, never raises and never blocks waiting on async
        handlers — fire-and-forget for the async case.

        Args:
            event_type: The event identifier (e.g. ``tui:tool.start``).
            context:    Optional dict with event-specific data.
        """
        if context is None:
            context = {}

        for fn in self._resolve_handlers(event_type):
            try:
                result = fn(event_type, context)
            except Exception as e:
                print(f"[hooks] Error in handler for '{event_type}': {e}", flush=True)
                continue

            if not asyncio.iscoroutine(result):
                continue

            # Coroutine returned — needs a loop to make progress.
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # No running loop in this thread.
                handler_id = id(fn)
                if handler_id not in _ASYNC_NO_LOOP_WARNED:
                    _ASYNC_NO_LOOP_WARNED.add(handler_id)
                    handler_name = getattr(fn, "__name__", "<anonymous>")
                    print(
                        f"[hooks] Skipping async handler {handler_name!r} for "
                        f"'{event_type}' — emit_sync called with no running "
                        f"event loop. Subsequent skips for this handler are "
                        f"silent.",
                        flush=True,
                    )
                # Close the coroutine to suppress "coroutine was never
                # awaited" RuntimeWarning noise.
                try:
                    result.close()
                except Exception:
                    pass
                continue

            try:
                # ensure_future schedules the coroutine on the loop and
                # returns immediately. Exceptions inside the coroutine
                # surface via the task's done callback (or asyncio's
                # default exception handler) — we don't await here.
                task = asyncio.ensure_future(result, loop=loop)
                task.add_done_callback(_log_task_exception)
            except Exception as e:
                print(
                    f"[hooks] Failed to schedule async handler for "
                    f"'{event_type}': {e}",
                    flush=True,
                )


def _log_task_exception(task: "asyncio.Task[Any]") -> None:
    """Surface exceptions from scheduled async hook handlers.

    Without this callback, an exception inside a fire-and-forget handler
    coroutine becomes "Task exception was never retrieved" noise from
    asyncio's default exception handler at GC time. Logging it explicitly
    keeps the failure mode visible and consistent with the sync path.
    """
    if task.cancelled():
        return
    exc = task.exception()
    if exc is not None:
        print(f"[hooks] Async handler raised: {exc}", flush=True)


# ── Module-level default registry ──────────────────────────────────
#
# Plugins and in-process callers (TUI gateway's ``_emit`` etc.) need a
# stable place to find "the" registry without threading a reference
# through every API. The gateway process installs its own
# ``self.hooks`` instance as the default during startup so file-system
# discovery and built-in hooks share state with programmatic
# registrations. Other processes (TUI) lazily get their own default on
# first access and run ``discover_and_load()`` themselves.

_default_registry: Optional["HookRegistry"] = None


def get_default_registry() -> "HookRegistry":
    """Return the process-wide default :class:`HookRegistry`.

    Lazily creates one (without auto-running discovery) on first call. Callers
    that need file-system hook discovery should invoke
    :meth:`HookRegistry.discover_and_load` themselves after first access — the
    gateway already does this for the registry it installs as the default.
    """
    global _default_registry
    if _default_registry is None:
        _default_registry = HookRegistry()
    return _default_registry


def install_as_default(registry: "HookRegistry") -> None:
    """Install ``registry`` as the process-wide default.

    Intended for the gateway and other long-lived hosts that want their own
    :class:`HookRegistry` instance to be visible to in-process plugins through
    :func:`get_default_registry`. Idempotent — installing the same registry
    twice is a no-op; installing a different registry replaces the previous
    default.
    """
    global _default_registry
    _default_registry = registry


def _reset_default_registry_for_tests() -> None:
    """Test helper — clears the cached default so each test starts fresh."""
    global _default_registry
    _default_registry = None
    _ASYNC_NO_LOOP_WARNED.clear()

