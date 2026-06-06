"""Auto-resume: resume interrupted sessions on gateway restart.

When the gateway restarts (crash, update, deploy), this hook scans for
sessions that were interrupted mid-turn (last message was a tool result
or a user message that never got a response) and triggers the agent to
pick up where it left off.
"""
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

EVENTS = ["gateway:startup"]
DESCRIPTION = "Auto-resume interrupted sessions on gateway startup"


async def handle(event_type: str, context: dict) -> None:
    if event_type != "gateway:startup":
        return

    logger.warning("Checking for interrupted sessions to auto-resume...")
    await asyncio.sleep(8)  # Wait for platform adapters to connect

    try:
        from hermes_cli.config import get_hermes_home
        from hermes_state import SessionDB
        from gateway.run import _gateway_runner_ref
        from gateway.platforms.base import Platform, MessageEvent, MessageType
        from gateway.session import SessionSource

        path = get_hermes_home() / "sessions" / "sessions.json"
        if not path.exists():
            logger.info("No sessions.json found — skipping auto-resume")
            return

        with open(path) as f:
            sessions = json.load(f)

        db = SessionDB()
        runner = _gateway_runner_ref()
        if not runner:
            logger.warning("No gateway runner available — skipping auto-resume")
            return

        resumed = 0
        for key, entry in sessions.items():
            if not isinstance(entry, dict) or entry.get("suspended"):
                continue

            sid = entry.get("session_id")
            if not sid:
                continue

            # Check if the session was interrupted mid-turn:
            #   role=tool → tool result was pending → agent should continue
            #   role=user → user message was unanswered → agent should reply
            try:
                msgs = db.get_messages(sid)
            except Exception:
                continue
            if not msgs:
                continue
            last_role = msgs[-1].get("role", "")
            if last_role not in ("tool", "user"):
                continue

            origin = entry.get("origin", {})
            pn = origin.get("platform", "")
            if not pn:
                continue
            try:
                plat = Platform(pn)
            except ValueError:
                continue
            plat_adapter = runner.adapters.get(plat)
            if plat_adapter is None:
                continue

            # Mark session for resume — the gateway injects a
            # "[System note: Your previous turn was interrupted...]"
            # prefix so the agent knows to continue rather than start fresh.
            runner.session_store.mark_resume_pending(key, reason="gateway_restart")

            source = SessionSource(
                platform=plat,
                chat_id=origin.get("chat_id", ""),
                chat_name=origin.get("chat_name", ""),
                chat_type=origin.get("chat_type", "dm"),
                user_id=origin.get("user_id", ""),
                user_name=origin.get("user_name", ""),
                thread_id=origin.get("thread_id"),
            )

            # Fire a synthetic internal event to trigger agent resume.
            # The text is "." — the gateway overrides it with the resume prefix.
            ev = MessageEvent(
                text=".",
                message_type=MessageType.TEXT,
                source=source,
                internal=True,
            )

            logger.warning("Auto-resuming session %s (%s)", key, plat.value)
            asyncio.create_task(plat_adapter.handle_message(ev))
            resumed += 1

        if resumed:
            logger.info("Auto-resumed %d interrupted session(s)", resumed)

    except Exception:
        logger.exception("auto-resume hook failed")
