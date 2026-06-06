"""Cua-driver backend (macOS only).

Speaks MCP over stdio to `cua-driver`. The Python `mcp` SDK is async, so we
run a dedicated asyncio event loop on a background thread and marshal sync
calls through it.

Install: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/trycua/cua/main/libs/cua-driver/scripts/install.sh)"`

After install, `cua-driver` is on $PATH and supports `cua-driver mcp` (stdio
transport) which is what we invoke.

The private SkyLight SPIs cua-driver uses (SLEventPostToPid, SLPSPostEvent-
RecordTo, _AXObserverAddNotificationAndCheckRemote) are not Apple-public and
can break on OS updates. Pin the installed version via `HERMES_CUA_DRIVER_
VERSION` if you want reproducibility across an OS bump.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import re
import shutil
import sys
import threading
from typing import Any, Dict, List, Optional, Tuple

from tools.computer_use.backend import (
    ActionResult,
    CaptureResult,
    ComputerUseBackend,
    UIElement,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Version pinning
# ---------------------------------------------------------------------------

PINNED_CUA_DRIVER_VERSION = os.environ.get("HERMES_CUA_DRIVER_VERSION", "0.5.0")

_CUA_DRIVER_CMD = os.environ.get("HERMES_CUA_DRIVER_CMD", "cua-driver")
_CUA_DRIVER_ARGS = ["mcp"]  # stdio MCP transport

# Regex to parse list_windows text output lines:
#   "- AppName (pid 12345) "Title" [window_id: 67890]"
_WINDOW_LINE_RE = re.compile(
    r'^-\s+(.+?)\s+\(pid\s+(\d+)\)\s+.*\[window_id:\s+(\d+)\]',
    re.MULTILINE,
)

# Regex to parse element lines from get_window_state AX tree markdown.
#
# Handles two output formats from different cua-driver versions:
#   Classic:  "  - [N] AXRole \"label\""
#   New:       "[N] AXRole (order) id=Label"
#
# Group 1: element index
# Group 2: AX role
# Group 3: quoted label (classic format)
# Group 4: id= label (new format)
_ELEMENT_LINE_RE = re.compile(
    r'^\s*(?:-\s+)?\[(\d+)\]\s+(\w+)(?:\s+"([^"]*)"|(?:\s+\(\d+\))?\s+id=([^\s\[\]]*))?' ,
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_macos() -> bool:
    return sys.platform == "darwin"


def cua_driver_binary_available() -> bool:
    """True if `cua-driver` is on $PATH or HERMES_CUA_DRIVER_CMD resolves."""
    return bool(shutil.which(_CUA_DRIVER_CMD))


def cua_driver_install_hint() -> str:
    return (
        "cua-driver is not installed. Install with one of:\n"
        "  hermes computer-use install\n"
        "Or run the upstream installer directly:\n"
        '  /bin/bash -c "$(curl -fsSL '
        'https://raw.githubusercontent.com/trycua/cua/main/libs/cua-driver/scripts/install.sh)"\n'
        "Or run `hermes tools` and enable the Computer Use toolset to install it automatically."
    )


def _parse_windows_from_text(text: str) -> List[Dict[str, Any]]:
    """Parse window records from list_windows text output."""
    windows = []
    for m in _WINDOW_LINE_RE.finditer(text):
        windows.append({
            "app_name": m.group(1).strip(),
            "pid": int(m.group(2)),
            "window_id": int(m.group(3)),
            "off_screen": "[off-screen]" in m.group(0),
            "title": "",
            "bundle_id": "",
            "z_index": 0,
        })
    return windows


def _normalize_match_text(value: Any) -> str:
    """Normalize app/window identifiers for conservative matching."""
    text = str(value or "").strip().lower()
    # Some apps surface names with leading UI decoration, e.g. "- Browser".
    # Treat leading decoration as noise without changing meaningful bundle IDs
    # or names.
    text = re.sub(r"^[\s\-–—_:•]+", "", text).strip()
    return re.sub(r"\s+", " ", text)


def _prefix_word_match(query: str, candidate: str) -> bool:
    """Return True for prefix matches that stop on a word boundary.

    This keeps "Code" from matching "Codex", while still allowing app/window
    names like "Code - project" or "Browser Settings".
    """
    if not candidate.startswith(query):
        return False
    if len(candidate) == len(query):
        return True
    return not candidate[len(query)].isalnum()


def _contains_word_match(query: str, candidate: str) -> bool:
    """Return True when query appears inside candidate on word boundaries."""
    start = candidate.find(query)
    while start != -1:
        end = start + len(query)
        before_ok = start == 0 or not candidate[start - 1].isalnum()
        after_ok = end == len(candidate) or not candidate[end].isalnum()
        if before_ok and after_ok:
            return True
        start = candidate.find(query, start + 1)
    return False


def _looks_like_bundle_id(query: str) -> bool:
    """Return True for plausible macOS bundle identifiers like com.apple.Safari."""
    return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*(?:\.[A-Za-z0-9][A-Za-z0-9_-]*)+", query.strip()))


def _parse_elements_from_tree(markdown: str) -> List[UIElement]:
    """Parse UIElement list from get_window_state AX tree markdown.

    Handles both the classic ``"label"``-quoted format and the newer
    ``id=Label`` format introduced in cua-driver v0.1.6.
    """
    elements = []
    for m in _ELEMENT_LINE_RE.finditer(markdown):
        # group(3) = quoted label (classic); group(4) = id= label (new)
        label = m.group(3) or m.group(4) or ""
        elements.append(UIElement(
            index=int(m.group(1)),
            role=m.group(2),
            label=label,
            bounds=(0, 0, 0, 0),
        ))
    return elements


def _split_tree_text(full_text: str) -> Tuple[str, str]:
    """Split get_window_state text into (summary_line, tree_markdown)."""
    lines = full_text.split("\n", 1)
    summary = lines[0]
    tree = lines[1] if len(lines) > 1 else ""
    return summary, tree


def _parse_key_combo(keys: str) -> Tuple[Optional[str], List[str]]:
    """Parse a key string like 'cmd+s' into (key, modifiers).

    Returns (key, modifiers) where key is the non-modifier key and modifiers
    is a list of modifier names (cmd, shift, option, ctrl).
    """
    MODIFIER_NAMES = {"cmd", "command", "shift", "option", "alt", "ctrl", "control", "fn"}
    KEY_ALIASES = {"command": "cmd", "alt": "option", "control": "ctrl"}

    parts = [p.strip().lower() for p in re.split(r'[+\-]', keys) if p.strip()]
    modifiers = []
    key = None
    for part in parts:
        normalized = KEY_ALIASES.get(part, part)
        if normalized in MODIFIER_NAMES:
            modifiers.append(normalized)
        else:
            key = part  # last non-modifier wins
    return key, modifiers


# ---------------------------------------------------------------------------
# Asyncio bridge — one long-lived loop on a background thread
# ---------------------------------------------------------------------------

class _AsyncBridge:
    """Runs one asyncio loop on a daemon thread; marshals coroutines from the caller."""

    def __init__(self) -> None:
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._ready = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._ready.clear()

        def _run() -> None:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._ready.set()
            try:
                self._loop.run_forever()
            finally:
                try:
                    self._loop.close()
                except Exception:
                    pass

        self._thread = threading.Thread(target=_run, daemon=True, name="cua-driver-loop")
        self._thread.start()
        if not self._ready.wait(timeout=5.0):
            raise RuntimeError("cua-driver asyncio bridge failed to start")

    def run(self, coro, timeout: Optional[float] = 30.0) -> Any:
        from agent.async_utils import safe_schedule_threadsafe
        if not self._loop or not self._thread or not self._thread.is_alive():
            if asyncio.iscoroutine(coro):
                coro.close()
            raise RuntimeError("cua-driver bridge not started")
        fut = safe_schedule_threadsafe(coro, self._loop)
        if fut is None:
            raise RuntimeError("cua-driver bridge not started")
        return fut.result(timeout=timeout)

    def stop(self) -> None:
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=2.0)
        self._thread = None
        self._loop = None


# ---------------------------------------------------------------------------
# MCP session (lazy, shared across tool calls)
# ---------------------------------------------------------------------------

class _CuaDriverSession:
    """Holds the mcp ClientSession. Spawned lazily; re-entered on drop."""

    def __init__(self, bridge: _AsyncBridge) -> None:
        self._bridge = bridge
        self._session = None
        self._exit_stack = None
        self._lock = threading.Lock()
        self._started = False

    def _require_started(self) -> None:
        if not self._started:
            raise RuntimeError("cua-driver session not started")

    async def _aenter(self) -> None:
        from contextlib import AsyncExitStack
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        if not cua_driver_binary_available():
            raise RuntimeError(cua_driver_install_hint())

        params = StdioServerParameters(
            command=_CUA_DRIVER_CMD,
            args=_CUA_DRIVER_ARGS,
            env={**os.environ},
        )
        stack = AsyncExitStack()
        read, write = await stack.enter_async_context(stdio_client(params))
        session = await stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        self._exit_stack = stack
        self._session = session

    async def _aexit(self) -> None:
        if self._exit_stack is not None:
            try:
                await self._exit_stack.aclose()
            except Exception as e:
                logger.warning("cua-driver shutdown error: %s", e)
        self._exit_stack = None
        self._session = None

    def start(self) -> None:
        with self._lock:
            if self._started:
                return
            self._bridge.start()
            self._bridge.run(self._aenter(), timeout=15.0)
            self._started = True

    def stop(self) -> None:
        with self._lock:
            if not self._started:
                return
            try:
                self._bridge.run(self._aexit(), timeout=5.0)
            finally:
                self._started = False

    async def _call_tool_async(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        result = await self._session.call_tool(name, args)
        return _extract_tool_result(result)

    def call_tool(self, name: str, args: Dict[str, Any], timeout: float = 30.0) -> Dict[str, Any]:
        self._require_started()
        return self._bridge.run(self._call_tool_async(name, args), timeout=timeout)


def _extract_tool_result(mcp_result: Any) -> Dict[str, Any]:
    """Convert an mcp CallToolResult into a plain dict.

    cua-driver returns a mix of text parts, image parts, and structuredContent.
    We flatten into:
      {
        "data": <text or parsed json>,
        "images": [b64, ...],
        "structuredContent": <dict|None>,
        "isError": bool,
      }
    structuredContent is populated from the MCP result's structuredContent field
    (MCP spec §2024-11-05+) and takes precedence for structured data like
    list_windows window arrays.
    """
    data: Any = None
    images: List[str] = []
    is_error = bool(getattr(mcp_result, "isError", False))
    structured: Optional[Dict] = getattr(mcp_result, "structuredContent", None) or None
    text_chunks: List[str] = []
    for part in getattr(mcp_result, "content", []) or []:
        ptype = getattr(part, "type", None)
        if ptype == "text":
            text_chunks.append(getattr(part, "text", "") or "")
        elif ptype == "image":
            b64 = getattr(part, "data", None)
            if b64:
                images.append(b64)
    if text_chunks:
        joined = "\n".join(t for t in text_chunks if t)
        try:
            data = json.loads(joined) if joined.strip().startswith(("{", "[")) else joined
        except json.JSONDecodeError:
            data = joined
    return {"data": data, "images": images, "structuredContent": structured, "isError": is_error}


# ---------------------------------------------------------------------------
# The backend itself
# ---------------------------------------------------------------------------

class CuaDriverBackend(ComputerUseBackend):
    """Default computer-use backend. macOS-only via cua-driver MCP."""

    def __init__(self) -> None:
        self._bridge = _AsyncBridge()
        self._session = _CuaDriverSession(self._bridge)
        # Sticky context — updated by capture(), used by action tools.
        self._active_pid: Optional[int] = None
        self._active_window_id: Optional[int] = None
        self._last_app: Optional[str] = None  # last app name targeted via capture/focus_app

    # ── Lifecycle ──────────────────────────────────────────────────
    def start(self) -> None:
        self._session.start()

    def stop(self) -> None:
        try:
            self._session.stop()
        finally:
            self._bridge.stop()

    def is_available(self) -> bool:
        if not _is_macos():
            return False
        return cua_driver_binary_available()

    def _list_windows(self, on_screen_only: bool) -> List[Dict[str, Any]]:
        """Return normalized cua-driver window records sorted frontmost first."""
        lw_out = self._session.call_tool("list_windows", {"on_screen_only": on_screen_only})

        sc = lw_out.get("structuredContent") or {}
        raw_windows = sc.get("windows") if sc else None
        if raw_windows:
            windows = [
                {
                    "app_name": w.get("app_name", ""),
                    "pid": int(w["pid"]),
                    "window_id": int(w["window_id"]),
                    "off_screen": not w.get("is_on_screen", True),
                    "title": w.get("title", ""),
                    "bundle_id": (
                        w.get("bundle_id")
                        or w.get("bundle_identifier")
                        or w.get("bundleIdentifier")
                        or ""
                    ),
                    "z_index": w.get("z_index", 0),
                }
                for w in raw_windows
            ]
            # cua-driver reports lower z_index as closer to the front on macOS.
            windows.sort(key=lambda w: w.get("z_index", 0))
        else:
            raw_text = lw_out["data"] if isinstance(lw_out["data"], str) else ""
            windows = _parse_windows_from_text(raw_text)

        return windows

    def _augment_windows_from_apps(self, windows: List[Dict[str, Any]]) -> None:
        """Merge list_apps metadata into windows by PID.

        Some cua-driver window records expose surprising app names, while
        list_apps can still have the canonical app name and bundle ID. Merge
        that metadata by PID so matching can use whichever identifier the
        platform exposes most reliably.
        """
        try:
            apps = self.list_apps()
        except Exception:
            return
        by_pid: Dict[int, Dict[str, Any]] = {}
        for app in apps:
            try:
                pid = int(app.get("pid"))
            except (TypeError, ValueError):
                continue
            by_pid[pid] = app

        for window in windows:
            app = by_pid.get(window.get("pid"))
            if not app:
                continue
            window.setdefault("bundle_id", "")
            window["bundle_id"] = (
                window.get("bundle_id")
                or app.get("bundle_id")
                or app.get("bundle_identifier")
                or app.get("bundleIdentifier")
                or ""
            )
            window["list_app_name"] = app.get("name", "")

    def _system_pids_for_bundle_id(self, bundle_id: str) -> List[int]:
        """Return running macOS process IDs for a bundle ID when cua-driver omits it.

        cua-driver/list_apps versions differ: some expose only app names and
        pids, not bundle identifiers. Only use the slower System Events lookup
        as a fallback for explicit bundle-ID queries; normal name matching must
        stay fast and not depend on Automation permissions.
        """
        if not _is_macos() or not shutil.which("osascript") or not _looks_like_bundle_id(bundle_id):
            return []
        script = (
            'tell application "System Events" to get unix id of every process '
            f'whose bundle identifier is "{bundle_id}"'
        )
        try:
            out = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=2.0,
                check=False,
            )
        except Exception as e:
            logger.debug("bundle id lookup failed for %s: %s", bundle_id, e)
            return []
        if out.returncode != 0:
            return []
        return [int(m.group(0)) for m in re.finditer(r"\d+", out.stdout)]

    def _augment_windows_for_bundle_id(self, windows: List[Dict[str, Any]], bundle_id: str) -> None:
        pids = set(self._system_pids_for_bundle_id(bundle_id))
        if not pids:
            return
        for window in windows:
            try:
                pid = int(window.get("pid", 0))
            except (TypeError, ValueError):
                continue
            if pid in pids and not window.get("bundle_id"):
                window["bundle_id"] = bundle_id

    def _window_match_score(self, query: str, window: Dict[str, Any]) -> int:
        q_raw = str(query or "").strip().lower()
        q = _normalize_match_text(query)
        if not q:
            return 0

        pid = str(window.get("pid", ""))
        if q_raw and q_raw == pid:
            return 400

        identity_fields = [
            window.get("bundle_id", ""),
            window.get("app_name", ""),
            window.get("list_app_name", ""),
        ]
        identity = [_normalize_match_text(f) for f in identity_fields if f]

        # Only app identity, bundle ID, list_apps name, or PID can create a
        # match for an explicit app target. Window titles remain useful for
        # tie-breaking/preference, but must not turn a localized app-name
        # mismatch into a silent target selection.
        if q in identity:
            return 320
        for candidate in identity:
            if _prefix_word_match(q, candidate):
                return 300
        if len(q) >= 4:
            for candidate in identity:
                if _contains_word_match(q, candidate):
                    return 240
        return 0

    def _window_preference_score(self, window: Dict[str, Any]) -> int:
        """Prefer normal content windows over transient titleless utility windows.

        Some apps expose several same-process windows with the same app name.
        The frontmost entry can be a hover card, About box, or titleless
        auxiliary surface. When the app query matches several windows equally,
        prefer windows that look like real browsing/document content.
        """
        score = 0
        title = str(window.get("title") or "").strip()
        if not window.get("off_screen"):
            score += 40
        if title:
            score += 20
        return score

    def _score_matching_windows(
        self,
        app: str,
        windows_by_key: Dict[Tuple[int, int], Dict[str, Any]],
        order_by_key: Dict[Tuple[int, int], int],
    ) -> List[Tuple[int, int, int, Dict[str, Any]]]:
        scored = []
        for key, window in windows_by_key.items():
            match = self._window_match_score(app, window)
            if match > 0:
                scored.append((match, self._window_preference_score(window), order_by_key[key], window))
        return scored

    def _select_window(self, app: str) -> Optional[Dict[str, Any]]:
        """Select the best window for an explicit app query, or None.

        Explicit app targeting must never silently fall back to the first
        unrelated window. Prefer strong on-screen app-identity matches, but
        consult all windows when needed so off-screen app matches are still
        available.
        """
        windows_by_key: Dict[Tuple[int, int], Dict[str, Any]] = {}
        order_by_key: Dict[Tuple[int, int], int] = {}
        order = 0

        def add_windows(windows: List[Dict[str, Any]]) -> None:
            nonlocal order
            for window in windows:
                key = (int(window.get("pid", 0)), int(window.get("window_id", 0)))
                if key not in windows_by_key:
                    windows_by_key[key] = window
                    order_by_key[key] = order
                    order += 1
                else:
                    # Keep useful metadata from later passes, but do not let
                    # them downgrade an already observed on-screen window.
                    existing = windows_by_key[key]
                    for field, value in window.items():
                        if field != "off_screen" and value not in (None, ""):
                            existing[field] = value
                    if not window.get("off_screen"):
                        existing["off_screen"] = False

        add_windows(self._list_windows(on_screen_only=True))
        needs_app_metadata = _looks_like_bundle_id(app)
        scored = self._score_matching_windows(app, windows_by_key, order_by_key)
        if (not scored or needs_app_metadata) and windows_by_key:
            self._augment_windows_from_apps(list(windows_by_key.values()))
            scored = self._score_matching_windows(app, windows_by_key, order_by_key)

        # Exact on-screen identity/PID matches are strong enough to avoid a
        # second list_windows call. We still do the all-windows pass for weak or
        # missing matches so off-screen exact app/bundle matches can beat them.
        best_score = max((item[0] for item in scored), default=0)
        if best_score < 320:
            add_windows(self._list_windows(on_screen_only=False))
            scored = self._score_matching_windows(app, windows_by_key, order_by_key)
            if (not scored or needs_app_metadata) and windows_by_key:
                self._augment_windows_from_apps(list(windows_by_key.values()))
                scored = self._score_matching_windows(app, windows_by_key, order_by_key)

        if not scored and needs_app_metadata:
            self._augment_windows_for_bundle_id(list(windows_by_key.values()), app.strip())
            scored = self._score_matching_windows(app, windows_by_key, order_by_key)
        if not scored:
            return None

        # Highest match score wins; for ties prefer likely content windows,
        # then preserve frontmost order.
        scored.sort(key=lambda item: (-item[0], -item[1], item[2]))
        return scored[0][3]

    def _default_window(self) -> Optional[Dict[str, Any]]:
        """Return the frontmost window for captures without an explicit app."""
        for on_screen_only in (True, False):
            windows = self._list_windows(on_screen_only=on_screen_only)
            if windows:
                return next((w for w in windows if not w.get("off_screen")), windows[0])
        return None

    def _empty_capture(self, mode: str, message: str = "") -> CaptureResult:
        return CaptureResult(mode=mode, width=0, height=0, png_b64=None,
                             elements=[], app="", window_title=message,
                             png_bytes_len=0)

    def _no_window_message(self, app: str) -> str:
        base = f"No window found for app '{app}'."
        q = _normalize_match_text(app)
        try:
            windows = self._list_windows(on_screen_only=True)
        except Exception:
            return base
        for window in windows:
            title = _normalize_match_text(window.get("title", ""))
            if title and (q == title or _prefix_word_match(q, title) or _contains_word_match(q, title)):
                return (
                    f"No window found for app '{app}'. A window title matched, but "
                    "explicit app targeting only matches app names, bundle IDs, "
                    "or PIDs; call list_apps to see available app names "
                    "(macOS may report localized names, e.g. '計算機' instead of 'Calculator')."
                )
        return base

    # ── Capture ────────────────────────────────────────────────────
    def capture(self, mode: str = "som", app: Optional[str] = None) -> CaptureResult:
        """Capture the frontmost on-screen window (optionally filtered by app name).

        Maps hermes `capture(mode, app)` → cua-driver `list_windows` +
        `get_window_state` (ax/som) or `screenshot` (vision).
        """
        if app:
            target = self._select_window(app)
            if target is None:
                self._active_pid = None
                self._active_window_id = None
                return self._empty_capture(mode, self._no_window_message(app))
        else:
            target = self._default_window()
            if target is None:
                return self._empty_capture(mode)

        cap = self._capture_window(mode, target)
        if app:
            self._last_app = cap.app or app
        return cap

    def capture_active(self, mode: str = "som") -> CaptureResult:
        """Capture the sticky active window after an action.

        `capture_after` should not re-run generic frontmost-window selection,
        because that can lose the target selected by capture/focus_app and land
        on an unrelated app. Preserve the stored pid/window_id whenever we can.
        """
        if self._active_pid is None or self._active_window_id is None:
            return self.capture(mode=mode)
        target = None
        try:
            for window in self._list_windows(on_screen_only=False):
                if (window.get("pid") == self._active_pid
                        and window.get("window_id") == self._active_window_id):
                    target = window
                    break
        except Exception:
            target = None
        if target is None:
            target = {
                "pid": self._active_pid,
                "window_id": self._active_window_id,
                "app_name": "",
                "title": "",
            }
        return self._capture_window(mode, target)

    def _capture_window(self, mode: str, target: Dict[str, Any]) -> CaptureResult:
        self._active_pid = int(target["pid"])
        self._active_window_id = int(target["window_id"])
        app_name = target.get("app_name") or target.get("list_app_name", "")
        if app_name and not self._last_app:
            self._last_app = app_name

        png_b64: Optional[str] = None
        elements: List[UIElement] = []
        width = height = 0
        window_title = str(target.get("title", "") or "")

        if mode == "vision":
            # screenshot tool: just the PNG, no AX walk.
            sc_out = self._session.call_tool(
                "screenshot",
                {"window_id": self._active_window_id, "format": "jpeg", "quality": 85},
            )
            if sc_out["images"]:
                png_b64 = sc_out["images"][0]
        else:
            # get_window_state: AX tree + optional screenshot.
            gws_out = self._session.call_tool(
                "get_window_state",
                {"pid": self._active_pid, "window_id": self._active_window_id},
            )
            text = gws_out["data"] if isinstance(gws_out["data"], str) else ""
            summary, tree = _split_tree_text(text)

            # Parse element count from summary e.g. "✅ AppName — 42 elements, turn 3..."
            m = re.search(r'(\d+)\s+elements?', summary)
            if tree and not gws_out["images"]:
                # ax mode — no screenshot
                elements = _parse_elements_from_tree(tree)
            elif gws_out["images"]:
                png_b64 = gws_out["images"][0]
                elements = _parse_elements_from_tree(tree)

            # Extract window title from the AX tree first AXWindow line.
            wt = re.search(r'AXWindow\s+"([^"]+)"', tree)
            if wt:
                window_title = wt.group(1)

        png_bytes_len = 0
        if png_b64:
            try:
                png_bytes_len = len(base64.b64decode(png_b64, validate=False))
            except Exception:
                png_bytes_len = len(png_b64) * 3 // 4

        return CaptureResult(
            mode=mode,
            width=width,
            height=height,
            png_b64=png_b64,
            elements=elements,
            app=app_name,
            window_title=window_title,
            png_bytes_len=png_bytes_len,
        )

    # ── Pointer ────────────────────────────────────────────────────
    def click(
        self,
        *,
        element: Optional[int] = None,
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: str = "left",
        click_count: int = 1,
        modifiers: Optional[List[str]] = None,
    ) -> ActionResult:
        pid = self._active_pid
        if pid is None:
            return ActionResult(ok=False, action="click",
                                message="No active window — call capture() first.")

        # Choose tool based on button and click_count.
        if button == "right":
            tool = "right_click"
        elif click_count == 2:
            tool = "double_click"
        else:
            tool = "click"

        args: Dict[str, Any] = {"pid": pid}
        if element is not None:
            if self._active_window_id is None:
                return ActionResult(ok=False, action=tool,
                                    message="No active window_id for element_index click.")
            args["element_index"] = element
            args["window_id"] = self._active_window_id
        elif x is not None and y is not None:
            args["x"] = x
            args["y"] = y
        else:
            return ActionResult(ok=False, action=tool,
                                message="click requires element= or x/y.")
        if modifiers:
            args["modifier"] = modifiers

        return self._action(tool, args)

    def drag(
        self,
        *,
        from_element: Optional[int] = None,
        to_element: Optional[int] = None,
        from_xy: Optional[Tuple[int, int]] = None,
        to_xy: Optional[Tuple[int, int]] = None,
        button: str = "left",
        modifiers: Optional[List[str]] = None,
    ) -> ActionResult:
        pid = self._active_pid
        if pid is None:
            return ActionResult(ok=False, action="drag",
                                message="No active window — call capture() first.")
        args: Dict[str, Any] = {"pid": pid}
        if from_element is not None and to_element is not None:
            if self._active_window_id is None:
                return ActionResult(ok=False, action="drag",
                                    message="No active window_id for element-based drag.")
            args["from_element"] = from_element
            args["to_element"] = to_element
            args["window_id"] = self._active_window_id
        elif from_xy is not None and to_xy is not None:
            args["from_x"], args["from_y"] = int(from_xy[0]), int(from_xy[1])
            args["to_x"], args["to_y"] = int(to_xy[0]), int(to_xy[1])
        else:
            return ActionResult(ok=False, action="drag",
                                message="drag requires from_element/to_element or from_coordinate/to_coordinate.")
        return self._action("drag", args)

    def scroll(
        self,
        *,
        direction: str,
        amount: int = 3,
        element: Optional[int] = None,
        x: Optional[int] = None,
        y: Optional[int] = None,
        modifiers: Optional[List[str]] = None,
    ) -> ActionResult:
        pid = self._active_pid
        if pid is None:
            return ActionResult(ok=False, action="scroll",
                                message="No active window — call capture() first.")
        args: Dict[str, Any] = {
            "pid": pid,
            "direction": direction,
            "amount": max(1, min(50, amount)),
        }
        if element is not None and self._active_window_id is not None:
            args["element_index"] = element
            args["window_id"] = self._active_window_id
        elif x is not None and y is not None:
            args["x"] = x
            args["y"] = y
        return self._action("scroll", args)

    # ── Keyboard ───────────────────────────────────────────────────
    def type_text(self, text: str) -> ActionResult:
        pid = self._active_pid
        if pid is None:
            return ActionResult(ok=False, action="type_text",
                                message="No active window — call capture() first.")
        return self._action("type_text", {"pid": pid, "text": text})

    def key(self, keys: str) -> ActionResult:
        pid = self._active_pid
        if pid is None:
            return ActionResult(ok=False, action="key",
                                message="No active window — call capture() first.")

        key_name, modifiers = _parse_key_combo(keys)
        if not key_name:
            return ActionResult(ok=False, action="key",
                                message=f"Could not parse key from '{keys}'.")

        if modifiers:
            # hotkey requires at least one modifier + one key.
            return self._action("hotkey", {"pid": pid, "keys": modifiers + [key_name]})
        else:
            return self._action("press_key", {"pid": pid, "key": key_name})

    # ── Value setter ────────────────────────────────────────────────
    def set_value(self, value: str, element: Optional[int] = None) -> ActionResult:
        """Set a value on an element. Handles AXPopUpButton selects natively."""
        pid = self._active_pid
        window_id = self._active_window_id
        if pid is None or window_id is None:
            return ActionResult(ok=False, action="set_value",
                                message="No active window — call capture() first.")
        if element is None:
            return ActionResult(ok=False, action="set_value",
                                message="set_value requires element= (element index).")
        args: Dict[str, Any] = {
            "pid": pid,
            "window_id": window_id,
            "element_index": element,
            "value": value,
        }
        return self._action("set_value", args)

    # ── Introspection ──────────────────────────────────────────────
    def list_apps(self) -> List[Dict[str, Any]]:
        out = self._session.call_tool("list_apps", {})
        sc = out.get("structuredContent") or {}
        if isinstance(sc, dict) and isinstance(sc.get("apps"), list):
            return sc["apps"]
        data = out["data"]
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("apps", [])
        # list_apps returns plain text — parse app lines.
        if isinstance(data, str):
            apps = []
            for line in data.splitlines():
                m = re.search(r'(.+?)\s+\(pid\s+(\d+)\)', line)
                if m:
                    apps.append({"name": m.group(1).strip(), "pid": int(m.group(2))})
            return apps
        return []

    def focus_app(self, app: str, raise_window: bool = False) -> ActionResult:
        """Target an app for subsequent actions without stealing system focus.

        cua-driver background-automation never needs to bring a window to the
        front: capture(app=...) already selects the right window via
        list_windows. We implement focus_app as a pure window-selector. An
        explicit app target must not silently fall back to a random first
        window, because that routes later keys/clicks to the wrong app.

        raise_window=True is intentionally ignored: stealing the user's focus
        is exactly what this backend is designed to avoid.
        """
        target = self._select_window(app)
        if not target:
            self._active_pid = None
            self._active_window_id = None
            return ActionResult(ok=False, action="focus_app",
                                message=self._no_window_message(app))

        self._active_pid = int(target["pid"])
        self._active_window_id = int(target["window_id"])
        app_name = target.get("app_name") or target.get("list_app_name", "")
        self._last_app = app_name or app
        return ActionResult(
            ok=True, action="focus_app",
            message=f"Targeted {app_name} (pid {self._active_pid}, "
                    f"window {self._active_window_id}) without raising window.",
        )

    # ── Internal ───────────────────────────────────────────────────
    def _action(self, name: str, args: Dict[str, Any]) -> ActionResult:
        try:
            out = self._session.call_tool(name, args)
        except Exception as e:
            logger.exception("cua-driver %s call failed", name)
            return ActionResult(ok=False, action=name, message=f"cua-driver error: {e}")
        ok = not out["isError"]
        message = ""
        data = out["data"]
        if isinstance(data, dict):
            message = str(data.get("message", ""))
        elif isinstance(data, str):
            message = data
        return ActionResult(ok=ok, action=name, message=message,
                            meta=data if isinstance(data, dict) else {})
