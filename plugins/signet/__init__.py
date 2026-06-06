"""signet — cryptographic audit trail plugin for Hermes Agent.

Wires two behaviours, matching the pattern used by ``plugins/disk-cleanup``:

1. ``post_tool_call`` hook — every tool call produces a hash-chained,
   optionally signed audit receipt written to a JSONL under
   ``$HERMES_HOME/signet/``. Zero agent compliance required.

2. ``/signet`` slash command — ``status`` / ``verify`` / ``tail`` /
   ``path`` subcommands so operators can inspect the chain from the
   running agent.

Default signer is :class:`HashChainSigner` (stdlib-only SHA-256 chain,
answers the core of #487). Install ``signet-auth`` and set
``audit.provider: signet`` in config.yaml to upgrade to Ed25519-signed
receipts via :class:`SignetSigner`.

Addresses: https://github.com/NousResearch/hermes-agent/issues/487
"""

from __future__ import annotations

import logging
import os
import shlex
import threading
from pathlib import Path
from typing import Any, Dict, Optional

from .audit_signer import AuditSigner, HashChainSigner

logger = logging.getLogger(__name__)


# Module-level signer. Initialized lazily on first tool call so plugin
# load is cheap and purely declarative.
_signer: Optional[AuditSigner] = None
_signer_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def _hermes_home() -> Path:
    try:
        from hermes_constants import get_hermes_home
        return get_hermes_home()
    except Exception:
        return Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))


def _audit_dir() -> Path:
    d = _hermes_home() / "signet"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _provider_name() -> str:
    """Return ``"hashchain"`` (default) or ``"signet"`` from env / config.

    Read from ``HERMES_SIGNET_PROVIDER`` first (for tests / quick toggles),
    falling back to ``plugins.signet.provider`` if a config loader is
    available. Unknown values fall back to ``hashchain``.
    """
    env = os.environ.get("HERMES_SIGNET_PROVIDER", "").strip().lower()
    if env in {"hashchain", "signet"}:
        return env
    try:
        from hermes_cli.config import load_config  # type: ignore
        cfg = load_config() or {}
        prov = (
            cfg.get("plugins", {})
            .get("signet", {})
            .get("provider", "hashchain")
        )
        return prov if prov in {"hashchain", "signet"} else "hashchain"
    except Exception:
        return "hashchain"


def _get_signer() -> AuditSigner:
    global _signer
    if _signer is not None:
        return _signer
    with _signer_lock:
        if _signer is not None:
            return _signer
        provider = _provider_name()
        if provider == "signet":
            try:
                from .signet_adapter import SignetSigner
                _signer = SignetSigner(dir=_audit_dir() / "keys")
                logger.info("signet plugin: using SignetSigner (Ed25519)")
                return _signer
            except Exception as e:
                logger.warning(
                    "signet plugin: SignetSigner unavailable (%s) — "
                    "falling back to HashChainSigner",
                    e,
                )
        _signer = HashChainSigner(path=_audit_dir() / "audit.jsonl")
        logger.info("signet plugin: using HashChainSigner (SHA-256 only)")
        return _signer


# ---------------------------------------------------------------------------
# Hooks
# ---------------------------------------------------------------------------

def _on_post_tool_call(
    *,
    tool_name: str = "",
    args: Optional[Dict[str, Any]] = None,
    result: Any = None,
    task_id: str = "",
    session_id: str = "",
    tool_call_id: str = "",
    **_: Any,
) -> None:
    """Record the tool call. Never raises."""
    if not tool_name:
        return
    try:
        _get_signer().append(
            tool_name=tool_name,
            args=args or {},
            result=result,
            session_id=session_id,
            task_id=task_id,
            tool_call_id=tool_call_id,
        )
    except Exception as e:
        logger.debug("signet plugin: append failed for %s: %s", tool_name, e)


def _on_session_end(**_: Any) -> None:
    """Run a quick chain verification and log the result (best effort)."""
    try:
        signer = _get_signer()
        ok, count, err = signer.verify()
        if ok:
            logger.info("signet plugin: chain OK (%d entries)", count)
        else:
            logger.warning(
                "signet plugin: chain verification failed after %d entries: %s",
                count,
                err,
            )
    except Exception as e:
        logger.debug("signet plugin: session-end verify failed: %s", e)


# ---------------------------------------------------------------------------
# Slash command
# ---------------------------------------------------------------------------

_HELP = """\
Usage: /signet <subcommand>

Subcommands:
  status       Show provider, audit path, event count.
  verify       Walk the chain and report integrity.
  tail [N]     Print the last N events (default 5).
  path         Print the audit log path.
"""


def _fmt_event(e) -> str:
    return (
        f"#{e.sequence} {e.timestamp} tool={e.tool_name} "
        f"args={e.args_digest[:12]}… result={e.result_digest[:12]}… "
        f"hash={e.hash[:12]}…"
    )


def _handle_slash(raw_args: str) -> Optional[str]:
    try:
        argv = shlex.split(raw_args or "")
    except ValueError as e:
        return f"Parse error: {e}\n\n{_HELP}"
    if not argv or argv[0] in ("help", "-h", "--help"):
        return _HELP
    sub = argv[0].lower()
    signer = _get_signer()

    if sub == "status":
        provider = _provider_name()
        ok, count, err = signer.verify()
        lines = [
            f"Provider: {provider}",
            f"Audit dir: {_audit_dir()}",
            f"Events: {count}",
            f"Chain: {'OK' if ok else f'BROKEN ({err})'}",
        ]
        return "\n".join(lines)

    if sub == "verify":
        ok, count, err = signer.verify()
        if ok:
            return f"Chain OK: {count} event(s) verified."
        return f"Chain BROKEN after {count} event(s): {err}"

    if sub == "tail":
        try:
            n = int(argv[1]) if len(argv) > 1 else 5
        except ValueError:
            return "Usage: /signet tail [N]"
        events = list(signer.iter_events())
        tail = events[-n:] if n > 0 else []
        if not tail:
            return "(no events)"
        return "\n".join(_fmt_event(e) for e in tail)

    if sub == "path":
        return str(_audit_dir())

    return f"Unknown subcommand: {sub}\n\n{_HELP}"


# ---------------------------------------------------------------------------
# Plugin registration
# ---------------------------------------------------------------------------

def register(ctx) -> None:
    ctx.register_hook("post_tool_call", _on_post_tool_call)
    ctx.register_hook("on_session_end", _on_session_end)
    ctx.register_command(
        "signet",
        handler=_handle_slash,
        description="Inspect and verify the cryptographic audit trail.",
    )
