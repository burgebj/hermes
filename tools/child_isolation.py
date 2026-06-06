#!/usr/bin/env python3
"""
Child Agent Isolation — Structured timeout, error handling, and parent isolation.

Wraps child agent execution to ensure:
- Child crash never crashes parent
- Hard timeout enforcement per delegation
- Structured error propagation with types
"""

import enum
import json
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional


class ChildErrorType(str, enum.Enum):
    TIMEOUT = "timeout"
    CRASH = "crash"
    INTERRUPTED = "interrupted"
    INTERNAL_ERROR = "internal_error"
    DEPTH_LIMIT = "depth_limit"
    PAUSED = "paused"


@dataclass
class ChildResult:
    """Structured result from a child agent execution."""

    success: bool
    task_index: int = 0
    status: str = "completed"
    summary: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    api_calls: int = 0
    duration_seconds: float = 0.0
    child_role: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


def wrap_child_execution(
    task_index: int,
    child_run_fn,
    child_timeout: float,
    child_role: Optional[str] = None,
) -> ChildResult:
    """Wrap child agent execution with timeout and crash isolation.

    Args:
        task_index: Index of the child task
        child_run_fn: Callable that runs the child (e.g., lambda: child.run_conversation(...))
        child_timeout: Hard timeout in seconds
        child_role: Role of the child ("leaf" or "orchestrator")

    Returns:
        ChildResult with success/error status
    """
    from concurrent.futures import ThreadPoolExecutor

    start = time.monotonic()
    executor = ThreadPoolExecutor(max_workers=1)

    try:
        future = executor.submit(child_run_fn)
        try:
            result = future.result(timeout=child_timeout)
            duration = time.monotonic() - start

            if isinstance(result, dict):
                return ChildResult(
                    success=True,
                    task_index=task_index,
                    status=result.get("status", "completed"),
                    summary=result.get("summary"),
                    api_calls=result.get("api_calls", 0),
                    duration_seconds=round(duration, 2),
                    child_role=child_role,
                    result=result,
                )
            return ChildResult(
                success=True,
                task_index=task_index,
                status="completed",
                duration_seconds=round(duration, 2),
                child_role=child_role,
            )

        except TimeoutError:
            duration = time.monotonic() - start
            return ChildResult(
                success=False,
                task_index=task_index,
                status="timeout",
                error=f"Child agent timed out after {child_timeout}s",
                error_type=ChildErrorType.TIMEOUT.value,
                api_calls=0,
                duration_seconds=round(duration, 2),
                child_role=child_role,
            )

    except Exception as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        duration = time.monotonic() - start
        return ChildResult(
            success=False,
            task_index=task_index,
            status="error",
            error=f"Child agent execution failed: {exc}",
            error_type=ChildErrorType.CRASH.value,
            api_calls=0,
            duration_seconds=round(duration, 2),
            child_role=child_role,
        )
    finally:
        executor.shutdown(wait=False)


def format_child_error(result: ChildResult) -> str:
    """Format a child error into a user-facing message.

    Args:
        result: ChildResult with error information

    Returns:
        Formatted error string
    """
    if result.success:
        return ""

    messages = {
        ChildErrorType.TIMEOUT.value: (
            f"Subagent timed out after {result.duration_seconds:.0f}s. "
            f"Increase delegation.child_timeout_seconds in config.yaml "
            f"(current: {result.duration_seconds:.0f}s) if tasks consistently need more time."
        ),
        ChildErrorType.CRASH.value: (
            f"Subagent crashed: {result.error or 'Unknown error'}. "
            f"The parent agent was not affected."
        ),
        ChildErrorType.INTERRUPTED.value: (
            f"Subagent was interrupted by parent."
        ),
        ChildErrorType.DEPTH_LIMIT.value: (
            f"Delegation depth limit reached. Increase delegation.max_spawn_depth in config.yaml."
        ),
    }

    return messages.get(result.error_type or "", result.error or "Unknown error")