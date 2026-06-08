"""Outcome Tool — Grade agent outputs against rubrics.

Provides rubric-based evaluation of agent outputs with configurable criteria.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

from tools.registry import registry

log = logging.getLogger(__name__)

OUTCOME_SCHEMA = {
    "type": "function",
    "function": {
        "name": "outcomes",
        "description": (
            "Evaluate agent outputs against configurable rubrics. "
            "Supports grading, review loops, listing rubrics, and viewing past outcomes."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["grade", "review", "list_rubrics", "view_outcomes"],
                    "description": "Action to perform.",
                },
                "rubric_name": {
                    "type": "string",
                    "description": "Name of the rubric to use (for grade/review).",
                },
                "output": {
                    "type": "string",
                    "description": "The output to grade (for grade action).",
                },
                "task": {
                    "type": "string",
                    "description": "Task description for review loop (for review action).",
                },
                "max_retries": {
                    "type": "integer",
                    "description": "Maximum retries for review loop (default: 2).",
                    "default": 2,
                },
                "limit": {
                    "type": "integer",
                    "description": "Max outcomes to return (for view_outcomes).",
                    "default": 20,
                },
            },
            "required": ["action"],
        },
    },
}


def _handle_outcome(args: Dict[str, Any]) -> str:
    """Handle outcome tool calls."""
    action = args.get("action", "list_rubrics")

    try:
        from hermes_constants import get_hermes_home
        from agent.outcomes import OutcomeEngine

        hermes_home = get_hermes_home()
        rubrics_dir = hermes_home / "rubrics"
        rubrics_dir.mkdir(exist_ok=True)

        engine = OutcomeEngine(rubrics_dir)

        if action == "list_rubrics":
            rubrics = engine.list_rubrics()
            return json.dumps({"status": "ok", "rubrics": rubrics})

        if action == "view_outcomes":
            limit = args.get("limit", 20)
            outcomes = engine.get_outcomes(limit=limit)
            return json.dumps({"status": "ok", "outcomes": outcomes})

        rubric_name = args.get("rubric_name")
        if not rubric_name:
            return json.dumps({"status": "error", "message": "rubric_name is required"})

        rubric = engine.load_rubric(rubric_name)
        if not rubric:
            available = engine.list_rubrics()
            return json.dumps({
                "status": "error",
                "message": f"Rubric '{rubric_name}' not found.",
                "available": available,
            })

        if action == "grade":
            output = args.get("output", "")
            if not output:
                return json.dumps({"status": "error", "message": "output is required for grading"})
            outcome = engine.grade(rubric, output)
            return json.dumps({"status": "ok", "outcome": engine.to_dict(outcome)}, indent=2)

        if action == "review":
            task = args.get("task", "")
            if not task:
                return json.dumps({"status": "error", "message": "task is required for review"})
            max_retries = args.get("max_retries", 2)
            # For tool usage, return the review plan
            return json.dumps({
                "status": "ok",
                "message": f"Review loop configured: rubric='{rubric_name}', "
                           f"max_retries={max_retries}, task='{task[:100]}...'",
                "rubric": {
                    "name": rubric.name,
                    "threshold": rubric.pass_threshold,
                    "criteria_count": len(rubric.criteria),
                },
            }, indent=2)

        return json.dumps({"status": "error", "message": f"Unknown action: {action}"})

    except Exception as e:
        log.error("Outcome tool error: %s", e)
        return json.dumps({"status": "error", "message": str(e)})


# Register the tool
registry.register("outcomes", "sloop", OUTCOME_SCHEMA, _handle_outcome)
