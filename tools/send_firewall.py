"""Messaging Firewall -- confirm-before-send gate for outbound messages.

Brings a "Human + LLM 2-of-2" security model to ``send_message``: the agent
may READ all incoming messages and COMPOSE replies freely, but DELIVERY to a
third party requires explicit human confirmation. Inspired by Vitalik
Buterin's open-source messaging-daemon (port 6000 read / port 7000 approval),
adapted to Hermes's in-process tool architecture.

The gate is evaluated inside ``send_message_tool._handle_send`` after the
target ``chat_id`` is fully resolved but before the platform API call. The
decision engine is pure and side-effect free (``evaluate_send_policy``); the
human-confirmation step (``request_approval``) blocks the agent thread.

Security boundary
-----------------
The firewall config is read from ``~/.hermes/config.yaml`` at evaluation time
(never cached in agent context). The agent cannot disable the firewall or add
trusted targets through its own tools because ``config.yaml`` is already a
protected write target in ``tools/approval.py`` (``_PROJECT_CONFIG_PATH`` /
``_HERMES_ENV_PATH``). "Always Allow" persistence here goes through
``hermes_cli.config.save_config``, which refuses to write in managed/Fly
deployments.

Scope (this module)
-------------------
* Decision engine: disabled -> self -> trusted -> auto-approve -> platform
  policy -> pending. Fully implemented and tested.
* Send-to-self detection: explicit ``self_targets`` + home-channel match.
* Cron exemption: cron-scheduled sends are never gated (no human present).
* CLI confirmation: interactive prompt with full message preview + persist.
* Audit logging: every allow/deny/timeout decision is logged.

Deferred (see MESSAGING_FIREWALL_DESIGN.md Phase 2/4)
----------------------------------------------------
* Gateway interactive button UI (Telegram/Discord/Slack ``send_approval_request``)
  and ``/approve``-style resolution. Until that lands, gateway-context sends
  that need confirmation FAIL CLOSED (denied) so the firewall is never a
  silent no-op when a human cannot be prompted.
* Hook-based ``tool:send_message`` architecture.
* Smart LLM-based auto-approval.
"""

from __future__ import annotations

import fnmatch
import logging
import os
import threading
from dataclasses import dataclass
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# Decision reason codes (stable strings used by callers/tests).
REASON_DISABLED = "disabled"
REASON_SELF = "self"
REASON_TRUSTED = "trusted"
REASON_AUTO_APPROVE = "auto_approve"
REASON_PLATFORM_ALLOW = "platform_allow"
REASON_CRON = "cron"
REASON_PENDING = "pending"
REASON_PLATFORM_DENY = "platform_deny"

# Length cap for message previews surfaced in prompts / audit logs.
_PREVIEW_MAX = 4000

# Session-scoped trusted targets added via "Always Allow" when config.yaml
# cannot be written (managed deployments). Keyed by normalized target.
_session_trusted: set[str] = set()
_session_lock = threading.RLock()


@dataclass
class FirewallDecision:
    """Outcome of evaluating the send policy for one outbound message."""

    allowed: bool
    reason: str
    platform: str
    chat_id: str
    target_label: str
    message_preview: str

    @property
    def needs_confirmation(self) -> bool:
        return (not self.allowed) and self.reason == REASON_PENDING


# =========================================================================
# Config access
# =========================================================================

def _load_firewall_config() -> dict:
    """Read the ``messaging_firewall`` section from config.yaml.

    Read fresh on every evaluation (never cached) so the gate cannot be
    pinned to a stale "enabled: false" snapshot, and so "Always Allow"
    additions take effect immediately. Returns ``{}`` on any failure
    (which means ``enabled`` defaults to False -> firewall off).
    """
    try:
        from hermes_cli.config import cfg_get, load_config

        cfg = load_config()
        section = cfg_get(cfg, "messaging_firewall", default={})
        return section if isinstance(section, dict) else {}
    except Exception:  # pragma: no cover - config import/parse failure
        logger.debug("messaging_firewall: failed to load config", exc_info=True)
        return {}


def is_enabled() -> bool:
    """True when the firewall is explicitly enabled in config.

    Opt-in by design: absent or falsy ``messaging_firewall.enabled`` means
    the gate is a no-op and ``send_message`` behaves exactly as before.
    """
    cfg = _load_firewall_config()
    return _as_bool(cfg.get("enabled"), default=False)


def _as_bool(value, default: bool) -> bool:
    """Coerce a YAML-ish value to bool. YAML 1.1 may parse ``off``->False."""
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"1", "true", "yes", "on", "enabled"}:
            return True
        if v in {"0", "false", "no", "off", "disabled", ""}:
            return False
    return bool(value)


def _str_list(cfg: dict, key: str) -> List[str]:
    """Return a list-of-strings config value, tolerating scalars/None."""
    raw = cfg.get(key)
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, (list, tuple)):
        return [str(x) for x in raw if x is not None]
    return []


# =========================================================================
# Target normalization + matching
# =========================================================================

def _normalize_target(platform: str, ref: str) -> str:
    """Build a canonical ``platform:ref`` label, lowercasing the platform.

    The ``ref`` (chat id / channel / phone / handle) is preserved verbatim
    except for surrounding whitespace and a leading ``#`` on channel names,
    which is stripped so ``discord:#bot-home`` and ``discord:bot-home``
    compare equal.
    """
    plat = (platform or "").strip().lower()
    r = (ref or "").strip()
    if r.startswith("#"):
        r = r[1:]
    return f"{plat}:{r}"


def _target_matches(candidate: str, pattern: str) -> bool:
    """Glob-match a normalized ``platform:ref`` candidate against a pattern.

    Patterns may use ``fnmatch`` wildcards (``*`` / ``?``). A bare platform
    pattern (``"telegram"`` with no colon) matches any target on that
    platform. Comparison is case-insensitive on the platform component and
    the ``#`` channel prefix is normalized on both sides.
    """
    if not pattern:
        return False
    pat = pattern.strip()
    # A pattern with no colon and no wildcard is a platform-only rule.
    if ":" not in pat and "*" not in pat and "?" not in pat:
        cand_platform = candidate.split(":", 1)[0]
        return cand_platform == pat.strip().lower()
    # Normalize a "platform:ref" pattern the same way as the candidate.
    if ":" in pat:
        p_plat, p_ref = pat.split(":", 1)
        pat_norm = _normalize_target(p_plat, p_ref)
    else:
        pat_norm = pat.lower()
    return fnmatch.fnmatchcase(candidate, pat_norm)


def _is_send_to_self(platform: str, chat_id: str, used_home_channel: bool,
                     cfg: dict) -> bool:
    """True when the target is the owner themselves (always allowed).

    Two signals:
      1. The message routed to the platform's configured home channel
         (the most common "send to self" pattern in Hermes).
      2. The target matches an explicit ``self_targets`` entry.
    """
    if used_home_channel:
        return True
    candidate = _normalize_target(platform, chat_id)
    for entry in _str_list(cfg, "self_targets"):
        if _target_matches(candidate, entry):
            return True
    return False


def _matches_auto_approve(platform: str, chat_id: str, message: str,
                          cfg: dict) -> bool:
    """True when (target, message) matches any ``auto_approve`` rule.

    Each rule is a dict with optional ``target_pattern`` (default ``*``) and
    ``message_pattern`` (default ``*``). ``message_pattern`` matches as a
    case-insensitive prefix OR an fnmatch glob, whichever succeeds -- so a
    plain ``"Scheduled:"`` prefix works without the user remembering to add
    a trailing ``*``.
    """
    rules = cfg.get("auto_approve")
    if not isinstance(rules, (list, tuple)):
        return False
    candidate = _normalize_target(platform, chat_id)
    msg = message or ""
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        target_pat = str(rule.get("target_pattern", "*") or "*")
        msg_pat = str(rule.get("message_pattern", "*") or "*")
        if target_pat != "*" and not _target_matches(candidate, target_pat):
            continue
        if msg_pat == "*":
            return True
        # Prefix match (literal) OR glob match.
        if msg.startswith(msg_pat):
            return True
        if fnmatch.fnmatch(msg, msg_pat):
            return True
    return False


def _platform_policy(platform: str, cfg: dict) -> str:
    """Return the policy for a platform: 'allow' | 'confirm' | 'deny'.

    Default is 'confirm' (the secure default once the firewall is enabled).
    """
    policies = cfg.get("platform_policy")
    if isinstance(policies, dict):
        val = policies.get((platform or "").strip().lower())
        if isinstance(val, str):
            v = val.strip().lower()
            if v in {"allow", "confirm", "deny"}:
                return v
    return "confirm"


# =========================================================================
# Cron detection
# =========================================================================

def _is_cron_session() -> bool:
    """True when running inside a cron-scheduled send (no human present).

    Cron jobs are pre-configured by the user and run unattended, so gating
    them would block indefinitely. Mirrors the cron exemption in
    ``tools/approval.py``. Honors an explicit opt-in to gate cron anyway via
    ``messaging_firewall.gate_cron: true``.
    """
    try:
        from utils import env_var_enabled

        if env_var_enabled("HERMES_CRON_SESSION"):
            return True
    except Exception:  # pragma: no cover
        if os.getenv("HERMES_CRON_SESSION", "").strip().lower() in {"1", "true", "yes", "on"}:
            return True
    return False


# =========================================================================
# Decision engine
# =========================================================================

def evaluate_send_policy(
    platform: str,
    chat_id: str,
    message: str,
    target_label: str,
    *,
    used_home_channel: bool = False,
) -> FirewallDecision:
    """Decide whether an outbound message may be delivered without a human.

    Decision order (first match wins):
      a. Firewall disabled                -> allow (reason=disabled)
      b. Cron session (and not gate_cron) -> allow (reason=cron)
      c. Target is self / home channel    -> allow (reason=self)
      d. Target in trusted_targets        -> allow (reason=trusted)
      e. Message matches auto_approve rule -> allow (reason=auto_approve)
      f. Platform policy == 'allow'       -> allow (reason=platform_allow)
      g. Platform policy == 'deny'        -> deny  (reason=platform_deny)
      h. Otherwise                        -> needs confirmation (reason=pending)
    """
    preview = (message or "")[:_PREVIEW_MAX]
    cfg = _load_firewall_config()

    def _decide(allowed: bool, reason: str) -> FirewallDecision:
        return FirewallDecision(
            allowed=allowed,
            reason=reason,
            platform=platform,
            chat_id=chat_id,
            target_label=target_label,
            message_preview=preview,
        )

    # (a) disabled
    if not _as_bool(cfg.get("enabled"), default=False):
        return _decide(True, REASON_DISABLED)

    # (b) cron exemption (unless explicitly told to gate cron)
    if _is_cron_session() and not _as_bool(cfg.get("gate_cron"), default=False):
        return _decide(True, REASON_CRON)

    # (c) send to self / home channel
    if _is_send_to_self(platform, chat_id, used_home_channel, cfg):
        return _decide(True, REASON_SELF)

    # (d) trusted targets (config + session-scoped "Always Allow")
    candidate = _normalize_target(platform, chat_id)
    trusted = _str_list(cfg, "trusted_targets")
    with _session_lock:
        session_trusted = set(_session_trusted)
    for entry in list(trusted) + list(session_trusted):
        if _target_matches(candidate, entry):
            return _decide(True, REASON_TRUSTED)

    # (e) auto-approve patterns
    if _matches_auto_approve(platform, chat_id, message, cfg):
        return _decide(True, REASON_AUTO_APPROVE)

    # (f)/(g) platform-level policy
    policy = _platform_policy(platform, cfg)
    if policy == "allow":
        return _decide(True, REASON_PLATFORM_ALLOW)
    if policy == "deny":
        return _decide(False, REASON_PLATFORM_DENY)

    # (h) default -> confirm
    return _decide(False, REASON_PENDING)


# =========================================================================
# "Always Allow" persistence
# =========================================================================

def add_trusted_target(target_label: str) -> bool:
    """Persist an "Always Allow" decision to config.yaml.

    Appends ``target_label`` to ``messaging_firewall.trusted_targets`` and
    saves. In managed/Fly deployments (where ``save_config`` is a no-op) the
    target is added to a session-scoped allowlist instead so the current
    session still honors the choice. Returns True if persisted to disk.
    """
    label = (target_label or "").strip()
    if not label:
        return False
    # Always honor for the rest of this session, regardless of persistence.
    with _session_lock:
        _session_trusted.add(_normalize_target(*_split_target(label)))

    try:
        from hermes_cli.config import is_managed, load_config, save_config

        if is_managed():
            logger.info(
                "messaging_firewall: managed deployment -- 'Always Allow' for %s "
                "applied to this session only (config.yaml is read-only).",
                label,
            )
            return False

        cfg = load_config() or {}
        section = cfg.get("messaging_firewall")
        if not isinstance(section, dict):
            section = {}
            cfg["messaging_firewall"] = section
        existing = section.get("trusted_targets")
        if not isinstance(existing, list):
            existing = []
        if label not in existing:
            existing.append(label)
        section["trusted_targets"] = existing
        save_config(cfg)
        logger.info("messaging_firewall: added trusted target %s", label)
        return True
    except Exception:
        logger.warning(
            "messaging_firewall: failed to persist trusted target %s (kept for session)",
            label,
            exc_info=True,
        )
        return False


def _split_target(label: str) -> Tuple[str, str]:
    """Split a ``platform:ref`` label into (platform, ref)."""
    if ":" in label:
        plat, ref = label.split(":", 1)
        return plat, ref
    return label, ""


def _reset_session_trusted() -> None:
    """Drop session-scoped trusted targets (test/session-boundary helper)."""
    with _session_lock:
        _session_trusted.clear()


# =========================================================================
# Audit logging
# =========================================================================

def _audit(decision_reason: str, target_label: str, message_preview: str,
           outcome: str) -> None:
    """Log a firewall decision for the audit trail (agent.log)."""
    snippet = message_preview.replace("\n", " ")
    if len(snippet) > 200:
        snippet = snippet[:200] + "..."
    logger.info(
        "messaging_firewall decision: outcome=%s reason=%s target=%s preview=%r",
        outcome, decision_reason, target_label, snippet,
    )


# =========================================================================
# Human confirmation
# =========================================================================

def request_approval(
    platform: str,
    chat_id: str,
    message: str,
    target_label: str,
    session_key: str,
) -> Tuple[bool, Optional[str]]:
    """Ask the human to approve delivery. Blocks the agent thread.

    Returns ``(approved, edited_message)``. ``edited_message`` is None unless
    the human supplied a revised message (CLI edit flow).

    Dispatch:
      * Gateway context -> currently FAIL CLOSED (deny). Interactive gateway
        approval buttons are Phase 2 (see module docstring). Failing closed
        keeps the firewall honest: an enabled firewall must never silently
        pass an unconfirmed send just because the prompt surface is missing.
      * CLI / non-gateway context -> interactive ``input()`` prompt with full
        message preview and [approve / edit / deny / always] choices.
    """
    preview = (message or "")[:_PREVIEW_MAX]

    if _is_gateway_context():
        logger.warning(
            "messaging_firewall: send to %s needs confirmation but interactive "
            "gateway approval is not yet implemented (Phase 2); denying. Add the "
            "target to messaging_firewall.trusted_targets or set the platform "
            "policy to 'allow' to permit it.",
            target_label,
        )
        _audit(REASON_PENDING, target_label, preview, "denied_gateway_unsupported")
        return False, None

    return _request_approval_cli(platform, chat_id, preview, target_label)


def _is_gateway_context() -> bool:
    """True when running inside a gateway/API session (no local stdin)."""
    try:
        from tools.approval import _is_gateway_approval_context

        return bool(_is_gateway_approval_context())
    except Exception:  # pragma: no cover
        return bool(os.getenv("HERMES_GATEWAY_SESSION"))


def _approval_timeout() -> int:
    """Read ``messaging_firewall.approval_timeout`` (seconds). Default 300."""
    cfg = _load_firewall_config()
    try:
        return int(cfg.get("approval_timeout", 300))
    except (TypeError, ValueError):
        return 300


def _request_approval_cli(
    platform: str,
    chat_id: str,
    preview: str,
    target_label: str,
) -> Tuple[bool, Optional[str]]:
    """Interactive CLI approval with full message preview.

    Choices:
      y / approve  -> deliver as-is
      e / edit     -> retype the message; delivered with the new text
      a / always   -> deliver AND persist target to trusted_targets
      n / deny     -> block (default on empty input / EOF / timeout)

    Guards against the prompt_toolkit stdin-deadlock (issue #15216): if a
    TUI owns the terminal, deny fast rather than spawning an input() thread
    whose Enter never arrives.
    """
    timeout = _approval_timeout()

    # Fail-closed guard mirrored from tools/approval.py: a live prompt_toolkit
    # app means input() can never see Enter -> would hang. Deny instead.
    try:
        from prompt_toolkit.application.current import get_app_or_none

        if get_app_or_none() is not None:
            logger.warning(
                "messaging_firewall: approval requested while prompt_toolkit is "
                "active and no interactive prompt is wired; denying send to %s.",
                target_label,
            )
            _audit(REASON_PENDING, target_label, preview, "denied_tui_no_prompt")
            return False, None
    except Exception:
        pass  # prompt_toolkit not installed -> safe to use input()

    os.environ["HERMES_SPINNER_PAUSE"] = "1"
    try:
        print()
        print("  \U0001f6e1️  Messaging firewall: confirm send")
        print(f"      To:   {target_label}")
        print("      Message:")
        for line in preview.splitlines() or [""]:
            print(f"        | {line}")
        print()
        print("      [y] approve   [e] edit   [a] always allow this target   [n] deny")
        print()
        import sys
        sys.stdout.flush()

        result = {"choice": ""}

        def _get_input():
            try:
                result["choice"] = input("  Approve send? [y/e/a/N]: ").strip().lower()
            except (EOFError, OSError):
                result["choice"] = ""

        thread = threading.Thread(target=_get_input, daemon=True)
        thread.start()
        thread.join(timeout=timeout)

        if thread.is_alive():
            print("\n  Messaging firewall: no response -- send denied (timeout).")
            _audit(REASON_PENDING, target_label, preview, "timeout")
            return False, None

        choice = result["choice"]
        if choice in {"y", "yes", "approve"}:
            _audit(REASON_PENDING, target_label, preview, "approved")
            return True, None
        if choice in {"a", "always"}:
            add_trusted_target(target_label)
            _audit(REASON_PENDING, target_label, preview, "approved_always")
            return True, None
        if choice in {"e", "edit"}:
            edited = {"text": ""}

            def _get_edit():
                try:
                    print("      Enter the revised message (single line):")
                    edited["text"] = input("      > ")
                except (EOFError, OSError):
                    edited["text"] = ""

            ethread = threading.Thread(target=_get_edit, daemon=True)
            ethread.start()
            ethread.join(timeout=timeout)
            if ethread.is_alive() or not edited["text"].strip():
                print("\n  Messaging firewall: no edit provided -- send denied.")
                _audit(REASON_PENDING, target_label, preview, "denied_empty_edit")
                return False, None
            _audit(REASON_PENDING, target_label, edited["text"], "approved_edited")
            return True, edited["text"]

        print("  Messaging firewall: send denied.")
        _audit(REASON_PENDING, target_label, preview, "denied")
        return False, None
    except (EOFError, KeyboardInterrupt):
        print("\n  Messaging firewall: cancelled -- send denied.")
        _audit(REASON_PENDING, target_label, preview, "denied_cancelled")
        return False, None
    finally:
        os.environ.pop("HERMES_SPINNER_PAUSE", None)
        try:
            import sys
            sys.stdout.flush()
        except Exception:
            pass
