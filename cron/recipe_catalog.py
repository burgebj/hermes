"""Cron Recipes — parameterized automation templates with typed slots.

A *recipe* is a one-place definition of an automation that every surface
renders natively:

  * Dashboard / GUI app  -> a form (one field per slot)
  * CLI / TUI / messenger -> a pre-filled ``/cron-recipe`` slash command
  * Agent                 -> a seed prompt; it asks for any blank/ambiguous slot
  * Docs catalog          -> a copy-paste command + a ``hermes://`` deep-link

The single source of truth is the slot schema below. ``recipe_form_schema``
emits what a form renderer needs; ``recipe_slash_command`` emits the flattened
one-line command; ``fill_recipe`` validates user-supplied values and turns a
recipe into a ``cron.jobs.create_job`` kwargs dict (so there is no second job
engine). The form-where-there's-a-screen / agent-fills-where-there's-a-chat
split both consume this same module.

Design choice: users never type raw cron. A recipe carries a fixed recurrence
in ``schedule_template`` and parameterizes only the human-friendly parts
(time-of-day, weekday set). Recipes needing full flexibility expose a ``text``
slot named ``schedule`` that passes through verbatim.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

__all__ = [
    "RecipeSlot",
    "CronRecipe",
    "CATALOG",
    "get_recipe",
    "recipe_form_schema",
    "recipe_slash_command",
    "recipe_deeplink",
    "recipe_catalog_entry",
    "fill_recipe",
    "RecipeFillError",
    "WEEKDAY_PRESETS",
]


class RecipeFillError(ValueError):
    """Raised when supplied slot values fail validation."""


# Slot types the renderers understand.
_SLOT_TYPES = frozenset({"time", "enum", "text", "weekdays"})

# Named weekday recurrences -> cron day-of-week field.
WEEKDAY_PRESETS: Dict[str, str] = {
    "everyday": "*",
    "weekdays": "1-5",
    "weekends": "0,6",
}


@dataclass(frozen=True)
class RecipeSlot:
    """A single fillable field on a recipe."""

    name: str
    type: str
    label: str
    default: Any = None
    options: tuple = ()       # for type="enum": allowed values
    optional: bool = False
    help: str = ""

    def __post_init__(self) -> None:
        if self.type not in _SLOT_TYPES:
            raise ValueError(f"unknown slot type {self.type!r} (slot {self.name})")


@dataclass(frozen=True)
class CronRecipe:
    """A parameterized automation template."""

    key: str
    title: str
    description: str
    category: str
    # Cron expression with ``{slot}`` placeholders, e.g. "{minute} {hour} * * {dow}".
    # Placeholders are filled from resolved slot values (time -> minute/hour,
    # weekdays -> dow). A literal cron string with no placeholders = fixed schedule.
    schedule_template: str
    # Seed instruction for the agent / the cron job prompt; may contain {slot}s.
    prompt_template: str
    slots: List[RecipeSlot] = field(default_factory=list)
    deliver_default: str = "origin"
    skills: tuple = ()        # skills the job loads before running
    tags: tuple = ()


# ---------------------------------------------------------------------------
# Curated in-repo catalog
# ---------------------------------------------------------------------------

_TIME = lambda default="08:00": RecipeSlot(  # noqa: E731 - concise factory
    name="time", type="time", label="What time?", default=default,
    help="24h local time, e.g. 08:00",
)
_DELIVER = RecipeSlot(
    name="deliver", type="enum", label="Where to deliver?",
    default="origin", options=("origin", "local", "telegram", "discord", "email"),
    help="origin = the chat you set this up from; local = save only, no message",
)


CATALOG: List[CronRecipe] = [
    CronRecipe(
        key="morning-brief",
        title="Morning briefing",
        description="A short daily briefing: today's calendar, weather, and "
        "anything urgent waiting on you.",
        category="daily",
        schedule_template="{minute} {hour} * * *",
        prompt_template=(
            "Produce a concise morning briefing for the user: today's calendar "
            "events, the local weather, and any urgent items. Keep it short and "
            "scannable. If no data sources are connected, give a brief "
            "good-morning with the date and offer to connect calendar/email."
        ),
        slots=[_TIME("08:00"), _DELIVER],
        tags=("daily", "briefing"),
    ),
    CronRecipe(
        key="important-mail",
        title="Important-mail monitor",
        description="Check your inbox periodically and ping you ONLY about mail "
        "that actually needs attention.",
        category="email",
        schedule_template="*/{interval_min} * * * *",
        prompt_template=(
            "Check the user's inbox for new messages since the last run. Surface "
            "ONLY mail matching: {criteria}. Score candidates with the urgency "
            "classifier and deliver only what clears the bar; if nothing does, "
            "respond with [SILENT]. Requires a connected mail source; if none is "
            "configured, explain how to connect one and stop."
        ),
        slots=[
            RecipeSlot(
                name="interval_min", type="enum", label="How often?",
                default="30", options=("15", "30", "60"),
                help="minutes between checks",
            ),
            RecipeSlot(
                name="criteria", type="text",
                label="Only notify me if the mail…",
                default="needs a reply today, is from my manager or family, "
                "or mentions a deadline",
            ),
            _DELIVER,
        ],
        tags=("email", "monitor"),
    ),
    CronRecipe(
        key="weekly-review",
        title="Weekly review",
        description="A weekly recap: what got done, what's still open, and "
        "what's coming up.",
        category="weekly",
        schedule_template="{minute} {hour} * * {dow}",
        prompt_template=(
            "Produce a weekly review for the user: what was accomplished this "
            "week, still-open items, and next week's calendar. Pull from "
            "connected sources. Keep it tight."
        ),
        slots=[
            _TIME("18:00"),
            RecipeSlot(
                name="day", type="enum", label="Which day?",
                default="sunday",
                options=("sunday", "monday", "friday", "saturday"),
            ),
            _DELIVER,
        ],
        tags=("weekly", "review"),
    ),
    CronRecipe(
        key="workday-start",
        title="Workday start reminder",
        description="A weekday nudge with your agenda and top priorities.",
        category="daily",
        schedule_template="{minute} {hour} * * 1-5",
        prompt_template=(
            "Give the user a brief weekday start-of-day nudge: today's calendar "
            "and the 1-3 highest-priority things to focus on, inferred from "
            "recent context and any task tools. Encouraging, short, one message."
        ),
        slots=[_TIME("09:00"), _DELIVER],
        tags=("daily", "focus"),
    ),
    CronRecipe(
        key="custom-reminder",
        title="Custom reminder",
        description="A recurring reminder in your own words, on your schedule.",
        category="general",
        schedule_template="{minute} {hour} * * {dow}",
        prompt_template="Remind the user: {what}",
        slots=[
            RecipeSlot(name="what", type="text", label="Remind me to…",
                       default="take a break and stretch"),
            _TIME("14:00"),
            RecipeSlot(
                name="recurrence", type="weekdays", label="Repeat on",
                default="everyday",
                options=tuple(WEEKDAY_PRESETS.keys()),
            ),
            _DELIVER,
        ],
        tags=("reminder",),
    ),
]

_CATALOG_BY_KEY = {r.key: r for r in CATALOG}


def get_recipe(key: str) -> Optional[CronRecipe]:
    return _CATALOG_BY_KEY.get(key)


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------

def recipe_form_schema(recipe: CronRecipe) -> Dict[str, Any]:
    """Emit the JSON a form renderer (dashboard / GUI) needs for this recipe."""
    return {
        "key": recipe.key,
        "title": recipe.title,
        "description": recipe.description,
        "category": recipe.category,
        "tags": list(recipe.tags),
        "fields": [
            {
                "name": s.name,
                "type": s.type,
                "label": s.label,
                "default": s.default,
                "options": list(s.options),
                "optional": s.optional,
                "help": s.help,
            }
            for s in recipe.slots
        ],
    }


def recipe_slash_command(recipe: CronRecipe, values: Optional[Dict[str, Any]] = None) -> str:
    """Build the flattened ``/cron-recipe <key> slot=val …`` command string.

    Uses each slot's default when ``values`` is omitted, so the docs/dashboard
    can show a ready-to-paste command. Free-text slots are quoted.
    """
    values = values or {}
    parts = [f"/cron-recipe {recipe.key}"]
    for s in recipe.slots:
        val = values.get(s.name, s.default)
        if val is None or val == "":
            if s.optional:
                continue
            val = ""
        sval = str(val)
        if s.type == "text" or " " in sval:
            sval = '"' + sval.replace('"', '\\"') + '"'
        parts.append(f"{s.name}={sval}")
    return " ".join(parts)


def recipe_deeplink(recipe: CronRecipe, values: Optional[Dict[str, Any]] = None) -> str:
    """Build the ``hermes://cron-recipe/<key>?slot=val`` deep-link URL."""
    from urllib.parse import quote, urlencode

    values = values or {}
    query = {}
    for s in recipe.slots:
        val = values.get(s.name, s.default)
        if val not in (None, ""):
            query[s.name] = str(val)
    qs = ("?" + urlencode(query)) if query else ""
    return f"hermes://cron-recipe/{quote(recipe.key)}{qs}"


def _humanize_schedule(recipe: CronRecipe) -> str:
    """A short human-readable description of when a recipe runs (defaults)."""
    sched = recipe.schedule_template
    if sched.startswith("*/"):
        iv = next((s for s in recipe.slots if s.name == "interval_min"), None)
        every = (iv.default if iv else None) or sched.split("/")[1].split()[0]
        return f"every {every} minutes"
    time_slot = next((s for s in recipe.slots if s.type == "time"), None)
    when = time_slot.default if time_slot else None
    if "* * 1-5" in sched:
        return f"weekdays at {when}" if when else "every weekday"
    if "{dow}" in sched:
        day_slot = next((s for s in recipe.slots if s.name in ("day", "recurrence")), None)
        scope = (day_slot.default if day_slot else "") or ""
        if scope and when:
            return f"{scope} at {when}"
        return f"at {when}" if when else "on a schedule"
    if when:
        return f"daily at {when}"
    return "on a schedule"


def recipe_catalog_entry(recipe: CronRecipe) -> Dict[str, Any]:
    """Unified serializable shape for a recipe — used by the docs generator
    and the dashboard API. Combines the form schema, the ready-to-paste slash
    command, the deep-link URL, and a human-readable schedule.
    """
    return {
        **recipe_form_schema(recipe),
        "schedule": recipe.schedule_template,
        "scheduleHuman": _humanize_schedule(recipe),
        "command": recipe_slash_command(recipe),
        "appUrl": recipe_deeplink(recipe),
    }


# ---------------------------------------------------------------------------
# Fill + validate + translate to a create_job spec
# ---------------------------------------------------------------------------

_TIME_RE = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")
_DAY_TO_DOW = {
    "sunday": "0", "monday": "1", "tuesday": "2", "wednesday": "3",
    "thursday": "4", "friday": "5", "saturday": "6",
}


def _resolve_schedule(recipe: CronRecipe, values: Dict[str, Any]) -> str:
    """Fill the schedule_template placeholders from resolved slot values."""
    sched = recipe.schedule_template

    # A free-text `schedule` slot passes through verbatim (full flexibility).
    if "schedule" in values and values["schedule"]:
        return str(values["schedule"])

    repl: Dict[str, str] = {}

    # time -> minute/hour
    time_val = values.get("time")
    if "{minute}" in sched or "{hour}" in sched:
        if not time_val:
            raise RecipeFillError("a time is required")
        m = _TIME_RE.match(str(time_val).strip())
        if not m:
            raise RecipeFillError(f"invalid time {time_val!r} — use HH:MM (24h)")
        repl["hour"] = str(int(m.group(1)))
        repl["minute"] = str(int(m.group(2)))

    # weekday set -> dow
    if "{dow}" in sched:
        if "recurrence" in values:
            preset = str(values.get("recurrence", "everyday")).lower()
            if preset not in WEEKDAY_PRESETS:
                raise RecipeFillError(
                    f"unknown recurrence {preset!r} — one of {', '.join(WEEKDAY_PRESETS)}"
                )
            repl["dow"] = WEEKDAY_PRESETS[preset]
        elif "day" in values:
            day = str(values.get("day", "")).lower()
            if day not in _DAY_TO_DOW:
                raise RecipeFillError(f"unknown day {day!r}")
            repl["dow"] = _DAY_TO_DOW[day]
        else:
            repl["dow"] = "*"

    # interval (minutes) for */N schedules
    if "{interval_min}" in sched:
        iv = str(values.get("interval_min", "")).strip()
        if not iv.isdigit() or int(iv) <= 0:
            raise RecipeFillError(f"invalid interval {iv!r} — minutes as a positive integer")
        repl["interval_min"] = iv

    try:
        return sched.format(**repl)
    except KeyError as e:  # pragma: no cover - template/slot mismatch is a dev error
        raise RecipeFillError(f"schedule template missing value for {e}") from e


def fill_recipe(
    recipe: CronRecipe,
    values: Dict[str, Any],
    *,
    origin: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Validate ``values`` and return ``cron.jobs.create_job`` kwargs.

    Missing required (non-optional) slots raise RecipeFillError naming the
    slot, so a form can show field errors and the agent knows what to ask.
    Enum values are checked against their options. The result is passed
    straight to ``create_job`` — no second schema.
    """
    resolved: Dict[str, Any] = {}
    for s in recipe.slots:
        raw = values.get(s.name, s.default)
        if raw in (None, ""):
            if s.optional:
                continue
            raise RecipeFillError(f"missing required value: {s.name} ({s.label})")
        if s.type == "enum" and s.options and str(raw) not in {str(o) for o in s.options}:
            raise RecipeFillError(
                f"{s.name}={raw!r} not allowed — one of {', '.join(map(str, s.options))}"
            )
        resolved[s.name] = raw

    schedule = _resolve_schedule(recipe, resolved)

    # Render the prompt with whatever slots it references.
    try:
        prompt = recipe.prompt_template.format(**resolved)
    except KeyError as e:
        raise RecipeFillError(f"recipe prompt missing value for {e}") from e

    spec: Dict[str, Any] = {
        "prompt": prompt,
        "schedule": schedule,
        "name": recipe.title,
        "deliver": resolved.get("deliver", recipe.deliver_default),
    }
    if recipe.skills:
        spec["skills"] = list(recipe.skills)
    if origin is not None:
        spec["origin"] = origin
    return spec
