"""Telegram multi-agent workspace router.

Dispatches @mention commands to actual agent processes (codex, bm, glm)
or Hermes background tasks.  Acknowledgements are returned immediately;
results are delivered to the correct Telegram thread via the Bot API.

No secrets are hard-coded; the bot token must be passed in by the caller
(obtained from the platform adapter config).
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
from typing import Optional

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Constants — Eternal workspace thread IDs
# --------------------------------------------------------------------------

HERMES_CHAT_ID = "-1003932124823"
MULTI_AGENT_ROOM_THREAD = "903"
AGENT_WORKBENCH_THREAD = "708"
BLAZEMIND_THREAD = "823"

# --------------------------------------------------------------------------
# Telegram delivery helper
# --------------------------------------------------------------------------


async def _tg_send(
    token: str,
    chat_id: str,
    text: str,
    thread_id: Optional[str] = None,
) -> None:
    """Send a plain-text Telegram message directly via the Bot REST API.

    Uses aiohttp when available; falls back to urllib if not.  Never raises —
    failures are logged as warnings so background delivery never crashes the
    caller.
    """
    if not token:
        logger.warning("workspace_router: no bot token — cannot deliver result")
        return

    payload: dict = {
        "chat_id": chat_id,
        "text": text[:4000],
    }
    if thread_id:
        try:
            payload["message_thread_id"] = int(thread_id)
        except (ValueError, TypeError):
            pass

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        import aiohttp  # type: ignore[import-not-found]

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, json=payload, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if not resp.ok:
                    body = await resp.text()
                    logger.warning(
                        "workspace_router: Telegram send failed %d: %.200s",
                        resp.status,
                        body,
                    )
    except ImportError:
        # aiohttp not available — fall back to sync urllib in executor
        import json
        import urllib.request

        def _sync_post() -> None:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status not in (200, 201):
                    logger.warning(
                        "workspace_router: Telegram send status %d", resp.status
                    )

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _sync_post)
        except Exception as exc:
            logger.warning("workspace_router: urllib fallback failed: %s", exc)
    except Exception as exc:
        logger.warning("workspace_router: _tg_send failed: %s", exc)


# --------------------------------------------------------------------------
# Command resolution
# --------------------------------------------------------------------------


def _resolve_command(alias: str) -> Optional[list[str]]:
    """Return the CLI command list for *alias*, or None if unavailable.

    The lookup is done at dispatch time so PATH changes after startup are
    respected (e.g., installing a new CLI tool during a session).
    """
    if alias in ("codex",):
        codex_bin = shutil.which("codex")
        if codex_bin:
            # codex --no-interactive -p "<task>" runs non-interactively
            return [codex_bin, "--no-interactive", "-p"]
        # Fallback: hermes codex -- <task>
        hermes_bin = shutil.which("hermes")
        if hermes_bin:
            return [hermes_bin, "codex", "--"]
        return None

    if alias in ("glm",):
        glm_bin = shutil.which("glm")
        return [glm_bin] if glm_bin else None

    if alias in ("blazemind", "bm"):
        bm_bin = shutil.which("bm")
        return [bm_bin, "quick"] if bm_bin else None

    if alias in ("hermes",):
        # Hermes IS the current process; we don't recurse.
        return None

    return None


# --------------------------------------------------------------------------
# Subprocess runner
# --------------------------------------------------------------------------


async def _run_subprocess(cmd: list[str], task: str, timeout: int = 120) -> tuple[bool, str]:
    """Run *cmd + [task]* and return (success, stdout_or_stderr)."""
    full = cmd + [task]
    try:
        proc = await asyncio.create_subprocess_exec(
            *full,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ},
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            return False, f"⏱ Agent timed out after {timeout}s."
        out = (stdout or b"").decode(errors="replace").strip()
        if not out:
            out = (stderr or b"").decode(errors="replace").strip()
        return (proc.returncode == 0), (out[:2000] or "(no output)")
    except Exception as exc:
        return False, f"❌ Subprocess error: {exc}"


# --------------------------------------------------------------------------
# Public dispatch functions
# --------------------------------------------------------------------------


async def dispatch_single_agent(
    alias: str,
    task: str,
    bot_token: str,
    result_chat_id: str,
    result_thread_id: Optional[str],
    *,
    config=None,
) -> str:
    """Dispatch *task* to agent *alias*.

    Returns an acknowledgement string immediately.  Spawns a background
    asyncio task that runs the agent process and delivers the result to
    ``result_chat_id / result_thread_id`` via the Bot API.
    """
    from gateway.agent_registry import lookup_agent

    entry = lookup_agent(alias, config or {})
    if entry is None:
        return f"⚠️ Unknown agent `@{alias}`."
    if not entry.enabled:
        return f"⏸ Agent `@{alias}` ({entry.display_name}) is disabled."

    cmd = _resolve_command(alias)

    if cmd is None:
        if alias == "hermes":
            return (
                f"✅ Task queued for **@hermes** (current session).\n"
                f"Task: `{task[:200]}`\n"
                f"↳ Continue this conversation to proceed."
            )
        return (
            f"⚠️ **@{alias}** (`{entry.display_name}`) CLI not available on this host.\n"
            f"Task: `{task[:150]}`\n"
            f"To run manually: `{alias} \"{task[:80]}\"`"
        )

    lane = entry.topic_lane or "agent-workbench"
    ack = (
        f"⚡ **@{alias}** dispatched.\n"
        f"Task: `{task[:100]}`\n"
        f"Result → #{lane}"
    )

    async def _deliver() -> None:
        success, output = await _run_subprocess(cmd, task)
        icon = "✅" if success else "❌"
        msg = (
            f"{icon} **@{alias}** completed task:\n`{task[:100]}`\n\n"
            f"```\n{output[:1800]}\n```"
        )
        await _tg_send(bot_token, result_chat_id, msg, result_thread_id)

    asyncio.create_task(_deliver())
    return ack


async def dispatch_fanout(
    aliases: list[str],
    task: str,
    bot_token: str,
    fanout_chat_id: str,
    fanout_thread_id: Optional[str],
    *,
    config=None,
) -> str:
    """Dispatch *task* to multiple agents concurrently.

    Returns a combined acknowledgement string.  Each agent delivers its own
    result to ``fanout_chat_id / fanout_thread_id``.
    """
    if not aliases:
        return "No agents specified."

    ack_lines: list[str] = [
        f"🌐 **Multi-agent fanout** — {len(aliases)} agent(s)",
        f"Task: `{task[:100]}`",
        "",
    ]
    for alias in aliases:
        a_ack = await dispatch_single_agent(
            alias=alias,
            task=task,
            bot_token=bot_token,
            result_chat_id=fanout_chat_id,
            result_thread_id=fanout_thread_id,
            config=config,
        )
        first_line = a_ack.split("\n", 1)[0]
        ack_lines.append(f"• @{alias}: {first_line}")

    ack_lines.append(f"\nResults → #multi-agent-room (thread {fanout_thread_id or 'default'})")
    return "\n".join(ack_lines)
