from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from hermes_cli.workflow.orchestrator import Subtask, WORKER_TYPES, _truncate


@dataclass
class LoadedWorkflowScript:
    path: Path
    subtasks: list[Subtask]
    max_concurrency: int | None = None


class WorkflowScriptBuilder:
    def __init__(self) -> None:
        self.subtasks: list[Subtask] = []
        self.max_concurrency: int | None = None

    def task(
        self,
        objective: str,
        worker: str = "researcher",
        context: str | dict[str, Any] | None = None,
        depends_on: list[str] | tuple[str, ...] | None = None,
        expected_output: str | None = None,
        acceptance_criteria: list[str] | tuple[str, ...] | None = None,
        risk_level: str = "medium",
    ) -> str:
        if worker not in WORKER_TYPES:
            worker = "researcher"
        task_id = f"script-{len(self.subtasks) + 1}"
        context_text = context if isinstance(context, str) else repr(context or {})
        subtask = Subtask(
            id=task_id,
            objective=objective.strip(),
            input_context=_truncate(context_text, 2400),
            expected_output=expected_output or "A focused worker output for this scripted task.",
            acceptance_criteria=list(
                acceptance_criteria
                or [
                    f"Addresses objective: {objective.strip()}",
                    "Calls out assumptions, risks, or blockers when relevant.",
                ]
            ),
            risk_level=risk_level if risk_level in {"low", "medium", "high"} else "medium",
            worker_type=worker,
            depends_on=[str(item) for item in depends_on or []],
            can_parallel=True,
        )
        self.subtasks.append(subtask)
        return task_id

    def parallel(
        self,
        items: list[str] | tuple[str, ...],
        max_concurrency: int | None = None,
    ) -> list[str]:
        ids = {str(item) for item in items}
        for subtask in self.subtasks:
            if subtask.id in ids:
                subtask.can_parallel = True
        if max_concurrency is not None:
            self.max_concurrency = max(1, int(max_concurrency))
        return list(items)

    def evaluate(self, output: str, criteria: list[str] | tuple[str, ...]) -> dict[str, Any]:
        lowered = output.lower()
        missing = [item for item in criteria if item.lower() not in lowered]
        return {"passed": not missing, "missing": missing}

    def revise(self, task_id: str, feedback: str) -> dict[str, str]:
        return {"task_id": task_id, "feedback": feedback}

    def synthesize(self, outputs: list[str] | tuple[str, ...]) -> str:
        return "\n\n".join(str(item) for item in outputs)


def load_script(path: str | Path) -> LoadedWorkflowScript:
    script_path = Path(path).expanduser().resolve()
    if not script_path.exists():
        raise FileNotFoundError(f"Workflow script not found: {script_path}")

    builder = WorkflowScriptBuilder()
    namespace = {
        "task": builder.task,
        "parallel": builder.parallel,
        "evaluate": builder.evaluate,
        "revise": builder.revise,
        "synthesize": builder.synthesize,
    }
    code = compile(script_path.read_text(encoding="utf-8"), str(script_path), "exec")
    exec(code, namespace, {})
    return LoadedWorkflowScript(
        path=script_path,
        subtasks=builder.subtasks,
        max_concurrency=builder.max_concurrency,
    )
