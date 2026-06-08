#!/usr/bin/env python3
"""
Clarify Tool Module - Interactive Clarifying Questions

Allows the agent to present structured multiple-choice questions or open-ended
prompts to the user. In CLI mode, choices are navigable with arrow keys. On
messaging platforms, choices are rendered as a numbered list.

The actual user-interaction logic lives in the platform layer (cli.py for CLI,
gateway/run.py for messaging). This module defines the schema, validation, and
a thin dispatcher that delegates to a platform-provided callback.
"""

import json
from typing import List, Optional, Callable, Sequence, Union


# Maximum number of predefined choices the agent can offer.
# A 5th "Other (type your answer)" option is always appended by the UI.
MAX_CHOICES = 4

# Choices can come in many shapes from the model:
#   - plain strings (the schema-promised shape)
#   - dicts like {"value": "Claude Code CLI", "key": "cc"}  ← real model output
#   - dicts like {"label": "Apple", "description": "red"}
#   - ints / floats (often serialised as numbers, e.g. enum indices)
# The model sometimes ignores the ``items: {type: string}`` schema
# constraint and emits the dict form because that mirrors the rendering
# metadata it was given in the prompt. Normalise defensively so the UI
# never sees a Python repr like ``"{'key': 'cc', 'value': '...'}"``.
ClarifyChoice = Union[str, dict, int, float]


def _normalize_clarify_choice(c: ClarifyChoice) -> Optional[str]:
    """Coerce a single model-supplied choice into a clean string.

    Returns None for empty / unparseable inputs so the caller can drop them.

    Precedence for dict inputs (matches what models actually emit today):
      1. ``value``     — most common, mirrors the answer the user will see
      2. ``label``     — fallback when ``value`` is absent
      3. ``text``      — another common model alias
      4. ``name``      — last-resort single field
    """
    if c is None:
        return None
    if isinstance(c, str):
        s = c.strip()
        return s or None
    if isinstance(c, dict):
        for key in ("value", "label", "text", "name"):
            v = c.get(key)
            if isinstance(v, str):
                s = v.strip()
                if s:
                    return s
        # If the dict has exactly one string value, use it. Otherwise
        # there's nothing we can render meaningfully.
        string_values = [v for v in c.values() if isinstance(v, str) and v.strip()]
        if len(string_values) == 1:
            return string_values[0].strip()
        return None
    if isinstance(c, bool):
        # bool is an int subclass; render explicitly so True != "True" surprises
        return "true" if c else "false"
    if isinstance(c, (int, float)):
        return str(c)
    # Last-ditch: anything stringifyable
    s = str(c).strip()
    return s or None


def _normalize_clarify_choices(choices) -> Optional[List[str]]:
    """Normalise a list of choices into clean strings. Returns None for
    empty / open-ended (the caller treats that as "no choices")."""
    if not choices:
        return None
    out: List[str] = []
    for c in choices:
        s = _normalize_clarify_choice(c)
        if s:
            out.append(s)
    if not out:
        return None
    return out[:MAX_CHOICES]


def _extract_clarify_description(c: ClarifyChoice) -> Optional[str]:
    """Pull an optional description string out of a choice. Used by
    adapters that render rich UI (Discord Select menus) so the user
    can see a full title + description row, not a truncated button."""
    if not isinstance(c, dict):
        return None
    for key in ("description", "desc", "hint", "subtitle"):
        v = c.get(key)
        if isinstance(v, str):
            s = v.strip()
            if s:
                return s
    return None


def _normalize_clarify_choices_rich(
    choices,
) -> Optional[List[dict]]:
    """Normalise a list of choices into ``[{"label": str, "description": str|None}]``.

    Returns None for empty / open-ended. The ``description`` field is
    optional — when the model didn't supply one (or passed a plain
    string), the result is ``{"label": "Apple", "description": None}``.

    Adapters that need rich rendering (Discord Select menus) use this.
    Adapters that only need strings should keep using
    ``_normalize_clarify_choices``.
    """
    if not choices:
        return None
    out: List[dict] = []
    for c in choices:
        label = _normalize_clarify_choice(c)
        if not label:
            continue
        desc = _extract_clarify_description(c)
        out.append({"label": label, "description": desc})
    if not out:
        return None
    return out[:MAX_CHOICES]


def clarify_tool(
    question: str,
    choices: Optional[Sequence[ClarifyChoice]] = None,
    callback: Optional[Callable] = None,
) -> str:
    """
    Ask the user a question, optionally with multiple-choice options.

    Args:
        question: The question text to present.
        choices:  Up to 4 predefined answer choices. Each may be a plain
                  string, a dict (``{"value": "..."}`` or
                  ``{"label": "..."}``), or a number. Dict shapes come
                  from the model ignoring the string-typed schema. The
                  tool normalises them to readable strings.
        callback: Platform-provided function that handles the actual UI
                  interaction. Signature: callback(question, choices) -> str.
                  Injected by the agent runner (cli.py / gateway).

    Returns:
        JSON string with the user's response.
    """
    if not question or not question.strip():
        return tool_error("Question text is required.")

    question = question.strip()

    # Validate and normalise choices. We accept any list (the model
    # sometimes sends dicts) but reject non-list inputs as a hard error.
    if choices is not None:
        if not isinstance(choices, list):
            return tool_error("choices must be a list of strings.")
        normalised = _normalize_clarify_choices(choices)
        if normalised is not None and not normalised:
            return tool_error(
                "choices list contained no readable values "
                "(expected strings or dicts with a 'value'/'label' field)."
            )
        choices = normalised  # may be None (open-ended) after normalisation

    if callback is None:
        return json.dumps(
            {"error": "Clarify tool is not available in this execution context."},
            ensure_ascii=False,
        )

    try:
        user_response = callback(question, choices)
    except Exception as exc:
        return json.dumps(
            {"error": f"Failed to get user input: {exc}"},
            ensure_ascii=False,
        )

    return json.dumps({
        "question": question,
        "choices_offered": choices,
        "user_response": str(user_response).strip(),
    }, ensure_ascii=False)


def check_clarify_requirements() -> bool:
    """Clarify tool has no external requirements -- always available."""
    return True


# =============================================================================
# OpenAI Function-Calling Schema
# =============================================================================

CLARIFY_SCHEMA = {
    "name": "clarify",
    "description": (
        "Ask the user a question when you need clarification, feedback, or a "
        "decision before proceeding. Supports two modes:\n\n"
        "1. **Multiple choice** — provide up to 4 choices. The user picks one "
        "or types their own answer via a 5th 'Other' option.\n"
        "2. **Open-ended** — omit choices entirely. The user types a free-form "
        "response.\n\n"
        "Use this tool when:\n"
        "- The task is ambiguous and you need the user to choose an approach\n"
        "- You want post-task feedback ('How did that work out?')\n"
        "- You want to offer to save a skill or update memory\n"
        "- A decision has meaningful trade-offs the user should weigh in on\n\n"
        "Do NOT use this tool for simple yes/no confirmation of dangerous "
        "commands (the terminal tool handles that). Prefer making a reasonable "
        "default choice yourself when the decision is low-stakes."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question to present to the user.",
            },
            "choices": {
                "type": "array",
                "items": {
                    "oneOf": [
                        {"type": "string"},
                        {
                            "type": "object",
                            "properties": {
                                "label": {"type": "string"},
                                "value": {"type": "string"},
                                "description": {
                                    "type": "string",
                                    "description": (
                                        "Optional secondary line shown "
                                        "beneath the choice in rich UIs "
                                        "(Discord Select menu)."
                                    ),
                                },
                                "key": {"type": "string"},
                            },
                            "required": [],
                        },
                    ],
                },
                "maxItems": MAX_CHOICES,
                "description": (
                    "Up to 4 answer choices. Each may be a plain string, "
                    "or a dict like "
                    '``{"label": "Apple", "description": "red fruit"}``. '
                    "When a ``description`` is supplied, rich UIs (Discord "
                    "Select menus) show it as a second line under the "
                    "label; plain UIs ignore it. Omit this parameter "
                    "entirely to ask an open-ended question. When "
                    "provided, the UI automatically appends an "
                    "'Other (type your answer)' option."
                ),
            },
        },
        "required": ["question"],
    },
}


# --- Registry ---
from tools.registry import registry, tool_error

registry.register(
    name="clarify",
    toolset="clarify",
    schema=CLARIFY_SCHEMA,
    handler=lambda args, **kw: clarify_tool(
        question=args.get("question", ""),
        choices=args.get("choices"),
        callback=kw.get("callback")),
    check_fn=check_clarify_requirements,
    emoji="❓",
)
