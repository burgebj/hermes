"""Challenge orchestrator + CLI entry point.

This module exposes both a Python API (used by the hook and plugin) and a
``__main__`` CLI used by Hermes' cron for daily-subscription delivery and by
the bundled install script for smoke-testing.

Public API:

* :func:`start_challenge(...)` — fetch an event, build the prompt, persist a
  challenge row, attempt to deliver to Telegram if requested. Returns a
  :class:`ChallengeResult`.
* :func:`handle_guess(...)` — score a guess and return a :class:`GuessResult`
  with the user-facing reply text.
* :func:`handle_hint(...)`, :func:`handle_reveal(...)`,
  :func:`render_stats(...)`, :func:`render_achievements(...)`,
  :func:`render_leaderboard(...)` — the rest of the slash-command surface.
* :func:`subscribe(...)` / :func:`unsubscribe(...)` / :func:`run_daily_subscriptions()`.

The orchestrator delegates image generation to the Hermes built-in image
engine via the ``gpt-image-2`` bridge skill, which resolves the active
provider, model, and authentication internally. If the bridge is not available,
the challenge falls back to text-only delivery.
"""

from __future__ import annotations

import argparse
import calendar
import datetime as _dt
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

# Allow both "python -m scripts.challenge" and "python challenge.py" forms.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scripts import achievements, guess_matcher, prompt_builder, scoring, sources, state, telegram_api  # type: ignore
    from scripts.guess_matcher import Acceptable, MatchResult, build_anchor_tokens  # type: ignore
else:
    from . import achievements, guess_matcher, prompt_builder, scoring, sources, state, telegram_api
    from .guess_matcher import Acceptable, MatchResult, build_anchor_tokens

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

DEFAULT_MAX_ATTEMPTS = 3
TELEGRAM_PLATFORM = "telegram"


# --------------------------------------------------------------------------- #
# Data containers
# --------------------------------------------------------------------------- #

@dataclass
class ChallengeResult:
    challenge_id: int
    surface_caption: str        # ONLY date + location — never any spoiler
    image_prompt: str
    image_path: Optional[Path]
    telegram_message_id: Optional[str]
    delivered: bool


@dataclass
class GuessResult:
    outcome: str                 # 'correct' | 'close' | 'wrong' | 'exhausted'
    reply_text: str
    awarded_achievements: List[str] = field(default_factory=list)
    challenge_id: Optional[int] = None


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _today_iso(now: Optional[_dt.date] = None) -> str:
    return (now or _dt.date.today()).isoformat()


def _surface_date(month: int, day: int, year: Optional[int] = None) -> str:
    base = f"{calendar.month_name[month]} {day}"
    if year is not None:
        return f"{base}, {year}"
    return base


def _build_aliases(event: scoring.CandidateEvent) -> List[Tuple[str, int]]:
    """Build acceptable answer aliases with precision tiers.

    Tier 1 = exact canonical answer.
    Tier 2 = topic noun phrase from raw page titles (Wikimedia ``pages``).
    Tier 3 = single-noun aliases (the most permissive).
    """
    out: List[Tuple[str, int]] = []
    out.append((event.canonical_answer.strip(), 1))
    pages = event.raw.get("pages") if isinstance(event.raw, dict) else None
    if isinstance(pages, list):
        for title in pages:
            if isinstance(title, str) and title.strip():
                out.append((title.strip(), 2))
    # Single most-distinctive token as a tier-3 fallback alias.
    anchors = build_anchor_tokens(event.canonical_answer)
    if anchors:
        out.append((anchors[0], 3))
    # Dedup, preserve order.
    seen: set = set()
    deduped: List[Tuple[str, int]] = []
    for alias, tier in out:
        key = alias.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append((alias, tier))
    return deduped


# Image generation hook. Can be overridden in tests by injecting via the
# ``image_generator`` arg.
ImageGenerator = Callable[[str, Path], Optional[Path]]


def _default_image_generator(prompt: str, output_dir: Path) -> Optional[Path]:
    """Try to invoke the gpt-image-2 skill (or legacy chatgpt-images-2-operator) via subprocess.

    Searches in order:
      1. ``$HERMES_HOME/skills/creative/gpt-image-2/scripts/generate.py``
      2. ``$HERMES_HOME/skills/gpt-image-2/scripts/generate.py``
      3. ``$HERMES_HOME/skills/creative/chatgpt-images-2-operator/run.py``
      4. ``$HERMES_HOME/skills/creative/chatgpt-images-2-operator/scripts/generate.py``

    If none is found, returns None and the caller falls back to text-only delivery.
    """
    hermes_home = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
    candidates = [
        hermes_home / "skills" / "creative" / "gpt-image-2" / "scripts" / "generate.py",
        hermes_home / "skills" / "gpt-image-2" / "scripts" / "generate.py",
        hermes_home / "skills" / "creative" / "chatgpt-images-2-operator" / "run.py",
        hermes_home / "skills" / "creative" / "chatgpt-images-2-operator" / "scripts" / "generate.py",
    ]
    runner = next((p for p in candidates if p.exists()), None)
    if runner is None:
        logger.debug("No image generator (gpt-image-2 or legacy) found; skipping image gen")
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "scene.png"
    try:
        subprocess.run(
            [sys.executable, str(runner), "--prompt", prompt, "--output", str(output_path)],
            check=True,
            timeout=120,
            capture_output=True,
        )
    except (subprocess.SubprocessError, FileNotFoundError) as exc:
        logger.warning("image generator failed: %s", exc)
        return None
    return output_path if output_path.exists() else None


# --------------------------------------------------------------------------- #
# Source -> chosen event
# --------------------------------------------------------------------------- #

def _pick_event(month: int, day: int, *, allow_offline_fixtures: bool = True) -> Optional[scoring.CandidateEvent]:
    candidates: List[scoring.CandidateEvent] = []
    try:
        candidates.extend(sources.fetch_all_candidates(month, day))
    except Exception as exc:
        logger.warning("source aggregation failed: %s", exc)
    if not candidates and allow_offline_fixtures:
        candidates = sources.load_fixture_events(month, day)
    if not candidates:
        return None
    ranked = scoring.rank_candidates(candidates)
    # Prefer the highest score whose prompt also passes safety. We try up to
    # five top events to avoid getting stuck on a single failing prompt.
    for ev in ranked[:5]:
        try:
            prompt = prompt_builder.build_image_prompt(ev, surface_date=_surface_date(month, day, ev.year))
        except ValueError:
            continue
        if prompt_builder.prompt_passes_safety(prompt):
            return ev
    return None


# --------------------------------------------------------------------------- #
# Public: start_challenge
# --------------------------------------------------------------------------- #

def start_challenge(
    *,
    platform: str,
    chat_id: str,
    user_id: str,
    user_display_name: Optional[str],
    scope: str,
    on_date: Optional[_dt.date] = None,
    image_generator: Optional[ImageGenerator] = None,
    deliver_to_telegram: bool = True,
) -> Optional[ChallengeResult]:
    """Launch a fresh challenge for the user/chat.

    Returns ``None`` if no usable event could be found.
    """
    state.migrate()
    state.upsert_user(platform, user_id, user_display_name)

    on_date = on_date or _dt.date.today()
    month, day = on_date.month, on_date.day

    event = _pick_event(month, day)
    if event is None:
        return None

    surface_date = _surface_date(month, day, event.year)
    location_line = event.location or "An unspecified location"
    if event.country and event.location and event.country.lower() not in event.location.lower():
        location_line = f"{event.location}, {event.country}"
    surface_caption = f"{surface_date}\n{location_line}"

    image_prompt = prompt_builder.build_image_prompt(event, surface_date=surface_date)

    aliases = _build_aliases(event)
    challenge_id = state.create_challenge(
        platform=platform,
        chat_id=chat_id,
        scope=scope,
        user_id=user_id if scope == "dm" else None,
        event_date=surface_date,
        event_year=event.year,
        location=event.location,
        country=event.country,
        canonical_answer=event.canonical_answer,
        short_summary=event.summary,
        full_description=(event.raw.get("raw_entry") if isinstance(event.raw, dict) else None) or event.summary,
        source=event.source,
        aliases=aliases,
        max_attempts=DEFAULT_MAX_ATTEMPTS,
    )

    image_path: Optional[Path] = None
    image_dir = Path(tempfile.mkdtemp(prefix="otdat-"))
    generator = image_generator or _default_image_generator
    try:
        image_path = generator(image_prompt, image_dir)
    except Exception as exc:
        logger.warning("image generator raised: %s", exc)
        image_path = None

    delivered = False
    telegram_message_id: Optional[str] = None
    if deliver_to_telegram and platform == TELEGRAM_PLATFORM:
        if image_path and image_path.exists():
            telegram_message_id = telegram_api.send_photo(chat_id, image_path, surface_caption)
        else:
            telegram_message_id = telegram_api.send_message(chat_id, surface_caption)
        if telegram_message_id:
            state.attach_telegram_message_id(challenge_id, telegram_message_id)
            delivered = True

    return ChallengeResult(
        challenge_id=challenge_id,
        surface_caption=surface_caption,
        image_prompt=image_prompt,
        image_path=image_path,
        telegram_message_id=telegram_message_id,
        delivered=delivered,
    )


# --------------------------------------------------------------------------- #
# Public: handle_guess
# --------------------------------------------------------------------------- #

def handle_guess(
    *,
    platform: str,
    chat_id: str,
    user_id: str,
    user_display_name: Optional[str],
    guess_text: str,
    challenge_id: Optional[int] = None,
) -> Optional[GuessResult]:
    """Score a guess against the active challenge for ``chat_id``.

    Returns ``None`` if there is no active challenge — the caller decides
    what to do (in DM-mode, treating plain text as a guess; in group-mode,
    only intercepting explicit replies).
    """
    state.migrate()
    state.upsert_user(platform, user_id, user_display_name)

    if challenge_id:
        challenge = state.get_challenge(challenge_id)
    else:
        challenge = state.get_active_challenge_for_chat(platform, chat_id)
    if not challenge or challenge.get("status") != "active":
        return None

    guess_text = (guess_text or "").strip()
    if not guess_text:
        return None

    aliases = state.list_acceptable_answers(int(challenge["challenge_id"]))
    accept_objs = [
        Acceptable(
            alias=row["alias"],
            alias_normalized=row["alias_normalized"],
            precision_tier=int(row["precision_tier"]),
        )
        for row in aliases
    ]
    anchors = build_anchor_tokens(challenge.get("canonical_answer") or "")
    result = guess_matcher.match_guess(
        guess_text,
        accept_objs,
        canonical_anchor_tokens=anchors,
    )

    return _record_and_render(
        platform=platform,
        chat_id=chat_id,
        user_id=user_id,
        challenge=challenge,
        guess_text=guess_text,
        match=result,
    )


def _record_and_render(
    *,
    platform: str,
    chat_id: str,
    user_id: str,
    challenge: Dict[str, Any],
    guess_text: str,
    match: MatchResult,
) -> GuessResult:
    challenge_id = int(challenge["challenge_id"])
    state.record_guess(challenge_id, platform, user_id, guess_text, match.outcome)
    state.increment_attempts(challenge_id)

    if match.outcome == "correct":
        wrong_count = state.count_wrong_guesses(challenge_id, user_id)
        hints_used = state.count_hints_used(challenge_id)
        user_after = state.update_streak_after_correct(
            platform, user_id, _today_iso(), challenge.get("country"),
        )
        state.resolve_challenge(challenge_id, "solved")
        awarded = achievements.evaluate_after_correct(
            platform=platform,
            user_id=user_id,
            challenge=challenge,
            user_after=user_after,
            wrong_count=wrong_count,
            hints_used=hints_used,
        )
        reply = _format_correct_reply(challenge, user_after["current_streak"], awarded)
        return GuessResult(
            outcome="correct",
            reply_text=reply,
            awarded_achievements=awarded,
            challenge_id=challenge_id,
        )

    if match.outcome == "close":
        # Close but not specific enough — record without burning a hard fail.
        # Still counts an attempt; reset_streak only fires on full exhaustion.
        attempts_used = int(challenge["attempts_used"]) + 1
        max_attempts = int(challenge["max_attempts"])
        if attempts_used >= max_attempts:
            return _exhaust_challenge(platform, user_id, challenge)
        state.update_after_wrong(platform, user_id)
        return GuessResult(
            outcome="close",
            reply_text=(
                "Close, but more specific. Reply again with a clearer answer.\n"
                f"Attempts left: {max(0, max_attempts - attempts_used)}"
            ),
            challenge_id=challenge_id,
        )

    # Wrong path.
    attempts_used = int(challenge["attempts_used"]) + 1
    max_attempts = int(challenge["max_attempts"])
    state.update_after_wrong(platform, user_id)
    if attempts_used >= max_attempts:
        return _exhaust_challenge(platform, user_id, challenge)
    return GuessResult(
        outcome="wrong",
        reply_text=(
            "Not quite. Try again.\n"
            f"Attempts left: {max(0, max_attempts - attempts_used)}"
        ),
        challenge_id=challenge_id,
    )


def _exhaust_challenge(platform: str, user_id: str, challenge: Dict[str, Any]) -> GuessResult:
    challenge_id = int(challenge["challenge_id"])
    state.resolve_challenge(challenge_id, "failed")
    state.reset_streak(platform, user_id)
    return GuessResult(
        outcome="exhausted",
        reply_text=(
            "Out of attempts.\n"
            f"Answer: {challenge.get('short_summary') or challenge.get('canonical_answer')}\n"
            "Streak reset to 0."
        ),
        challenge_id=challenge_id,
    )


def _format_correct_reply(challenge: Dict[str, Any], streak: int, awarded: List[str]) -> str:
    canon = challenge.get("short_summary") or challenge.get("canonical_answer") or ""
    lines = [
        "Correct.",
        f"Answer: {canon}".rstrip(),
        f"Streak: {streak}",
    ]
    for key in awarded:
        lines.append(f"Achievement unlocked — {achievements.render_achievement_line(key)}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Hint / reveal
# --------------------------------------------------------------------------- #

HINT_LADDER = (
    "It happened in the {decade}s.",
    "Country: {country}.",
    "It involved a person whose first initial is '{initial}'.",
)


def handle_hint(*, platform: str, chat_id: str) -> Optional[str]:
    state.migrate()
    challenge = state.get_active_challenge_for_chat(platform, chat_id)
    if not challenge:
        return None
    challenge_id = int(challenge["challenge_id"])
    history = state.append_hint(challenge_id, "")  # will overwrite below

    used = len(history) - 1
    canon = challenge.get("canonical_answer") or ""
    initials = next((c for c in canon if c.isalpha()), "?")
    decade = (challenge.get("event_year") // 10 * 10) if isinstance(challenge.get("event_year"), int) else "?"
    country = challenge.get("country") or "unknown"

    if used >= len(HINT_LADDER):
        # Replace the speculative empty hint with a generic message.
        state.append_hint(challenge_id, "no further hints available")
        return "No more hints. Use /on-this-day-art-trivia reveal to see the answer."

    hint = HINT_LADDER[used].format(
        decade=decade,
        country=country,
        initial=initials.upper(),
    )
    # Persist the actual hint text, replacing the placeholder we just appended.
    history[-1] = hint
    # Rewrite the hint history in place.
    from . import state as _state_mod  # local alias to avoid shadowing
    with _state_mod.get_conn() as conn:
        conn.execute(
            "UPDATE challenges SET hint_history = ? WHERE challenge_id = ?",
            (json.dumps(history), challenge_id),
        )
    state.record_guess(challenge_id, platform, "system", "[hint]", "hint")
    return f"Hint {used + 1}: {hint}"


def handle_reveal(*, platform: str, chat_id: str, user_id: str) -> Optional[str]:
    state.migrate()
    challenge = state.get_active_challenge_for_chat(platform, chat_id)
    if not challenge:
        return None
    challenge_id = int(challenge["challenge_id"])
    state.resolve_challenge(challenge_id, "revealed")
    state.reset_streak(platform, user_id)
    answer = challenge.get("short_summary") or challenge.get("canonical_answer") or ""
    return f"Answer: {answer}\nStreak reset to 0."


# --------------------------------------------------------------------------- #
# Stats / achievements / leaderboard
# --------------------------------------------------------------------------- #

def render_stats(*, platform: str, user_id: str) -> str:
    state.migrate()
    user = state.get_user(platform, user_id)
    if not user:
        return "No stats yet — play your first challenge with /on-this-day-art-trivia."
    countries = user.get("countries_correct") or "[]"
    try:
        country_count = len(json.loads(countries))
    except (TypeError, ValueError):
        country_count = 0
    return (
        "Your On-This-Day Art Trivia stats:\n"
        f"  Correct: {user.get('total_correct', 0)}\n"
        f"  Attempts: {user.get('total_attempts', 0)}\n"
        f"  Current streak: {user.get('current_streak', 0)}\n"
        f"  Longest streak: {user.get('longest_streak', 0)}\n"
        f"  Countries correct: {country_count}"
    )


def render_achievements(*, platform: str, user_id: str) -> str:
    state.migrate()
    rows = state.list_achievements(platform, user_id)
    if not rows:
        return "No achievements yet. Play to earn your first."
    lines = ["Your achievements:"]
    for row in rows:
        lines.append(f"  • {achievements.render_achievement_line(row['achievement_key'])}")
    return "\n".join(lines)


def render_leaderboard(*, platform: str, limit: int = 10) -> str:
    state.migrate()
    rows = state.leaderboard_top(platform, limit=limit)
    if not rows:
        return "Leaderboard is empty."
    lines = ["Leaderboard (most-correct):"]
    for i, row in enumerate(rows, 1):
        name = row.get("display_name") or row.get("user_id")
        lines.append(
            f"  {i}. {name} — {row.get('total_correct', 0)} correct "
            f"(longest streak {row.get('longest_streak', 0)})"
        )
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Subscriptions
# --------------------------------------------------------------------------- #

def subscribe(*, platform: str, user_id: str, chat_id: str, scope: str) -> str:
    state.migrate()
    state.add_subscription(platform, user_id, chat_id, scope)
    return "Subscribed. You'll receive a daily on-this-day challenge."


def unsubscribe(*, platform: str, user_id: str, chat_id: str) -> str:
    state.migrate()
    if state.remove_subscription(platform, user_id, chat_id):
        return "Unsubscribed. No more daily challenges."
    return "You weren't subscribed."


def run_daily_subscriptions(*, on_date: Optional[_dt.date] = None) -> Dict[str, int]:
    """Cron-friendly entry point. Sends one challenge per active subscription."""
    state.migrate()
    sent = 0
    failed = 0
    for sub in state.list_active_subscriptions():
        try:
            res = start_challenge(
                platform=sub["platform"],
                chat_id=sub["chat_id"],
                user_id=sub["user_id"],
                user_display_name=None,
                scope=sub["scope"],
                on_date=on_date,
            )
        except Exception as exc:
            logger.warning("subscription delivery failed for %s: %s", sub, exc)
            failed += 1
            continue
        if res and res.delivered:
            sent += 1
        else:
            failed += 1
    return {"sent": sent, "failed": failed}


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="on-this-day-art-trivia")
    sub = p.add_subparsers(dest="cmd", required=True)

    start = sub.add_parser("start", help="Start a new challenge")
    start.add_argument("--platform", default=TELEGRAM_PLATFORM)
    start.add_argument("--chat-id", required=True)
    start.add_argument("--user-id", required=True)
    start.add_argument("--scope", default="dm", choices=("dm", "group"))
    start.add_argument("--no-deliver", action="store_true")
    start.add_argument("--date", help="ISO date YYYY-MM-DD (default today)")

    sub.add_parser("daily", help="Run daily subscription delivery")

    g = sub.add_parser("guess", help="Score a guess")
    g.add_argument("--platform", default=TELEGRAM_PLATFORM)
    g.add_argument("--chat-id", required=True)
    g.add_argument("--user-id", required=True)
    g.add_argument("--text", required=True)

    h = sub.add_parser("hint", help="Get a hint")
    h.add_argument("--platform", default=TELEGRAM_PLATFORM)
    h.add_argument("--chat-id", required=True)

    r = sub.add_parser("reveal", help="Reveal the answer")
    r.add_argument("--platform", default=TELEGRAM_PLATFORM)
    r.add_argument("--chat-id", required=True)
    r.add_argument("--user-id", required=True)

    st = sub.add_parser("stats", help="Show user stats")
    st.add_argument("--platform", default=TELEGRAM_PLATFORM)
    st.add_argument("--user-id", required=True)

    a = sub.add_parser("achievements", help="List user achievements")
    a.add_argument("--platform", default=TELEGRAM_PLATFORM)
    a.add_argument("--user-id", required=True)

    lb = sub.add_parser("leaderboard", help="Show leaderboard")
    lb.add_argument("--platform", default=TELEGRAM_PLATFORM)
    lb.add_argument("--limit", type=int, default=10)

    s = sub.add_parser("subscribe", help="Subscribe to daily challenges")
    s.add_argument("--platform", default=TELEGRAM_PLATFORM)
    s.add_argument("--user-id", required=True)
    s.add_argument("--chat-id", required=True)
    s.add_argument("--scope", default="dm", choices=("dm", "group"))

    u = sub.add_parser("unsubscribe", help="Unsubscribe from daily challenges")
    u.add_argument("--platform", default=TELEGRAM_PLATFORM)
    u.add_argument("--user-id", required=True)
    u.add_argument("--chat-id", required=True)

    return p


def _cli_main(argv: Optional[List[str]] = None) -> int:
    args = _build_argparser().parse_args(argv)
    if args.cmd == "start":
        on_date = _dt.date.fromisoformat(args.date) if args.date else None
        res = start_challenge(
            platform=args.platform, chat_id=args.chat_id,
            user_id=args.user_id, user_display_name=None,
            scope=args.scope, on_date=on_date,
            deliver_to_telegram=not args.no_deliver,
        )
        if res is None:
            print("No suitable event found for that date.")
            return 1
        print(json.dumps({
            "challenge_id": res.challenge_id,
            "surface_caption": res.surface_caption,
            "delivered": res.delivered,
            "telegram_message_id": res.telegram_message_id,
            "image_path": str(res.image_path) if res.image_path else None,
        }, indent=2))
        return 0
    if args.cmd == "daily":
        summary = run_daily_subscriptions()
        print(json.dumps(summary))
        return 0
    if args.cmd == "guess":
        res = handle_guess(
            platform=args.platform, chat_id=args.chat_id,
            user_id=args.user_id, user_display_name=None,
            guess_text=args.text,
        )
        if res is None:
            print("No active challenge.")
            return 1
        print(res.reply_text)
        return 0
    if args.cmd == "hint":
        out = handle_hint(platform=args.platform, chat_id=args.chat_id)
        print(out or "No active challenge.")
        return 0 if out else 1
    if args.cmd == "reveal":
        out = handle_reveal(platform=args.platform, chat_id=args.chat_id, user_id=args.user_id)
        print(out or "No active challenge.")
        return 0 if out else 1
    if args.cmd == "stats":
        print(render_stats(platform=args.platform, user_id=args.user_id))
        return 0
    if args.cmd == "achievements":
        print(render_achievements(platform=args.platform, user_id=args.user_id))
        return 0
    if args.cmd == "leaderboard":
        print(render_leaderboard(platform=args.platform, limit=args.limit))
        return 0
    if args.cmd == "subscribe":
        print(subscribe(platform=args.platform, user_id=args.user_id, chat_id=args.chat_id, scope=args.scope))
        return 0
    if args.cmd == "unsubscribe":
        print(unsubscribe(platform=args.platform, user_id=args.user_id, chat_id=args.chat_id))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(_cli_main())
