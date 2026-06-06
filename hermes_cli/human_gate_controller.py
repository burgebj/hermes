from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from hermes_cli.review_orchestrator import AutomatedReviewResult

_APPROVAL_TOKENS: set[str] = {"y", "confirm"}


@dataclass(frozen=True)
class HumanGateDecision:
    approved: bool
    response: str
    prompt_text: str


class HumanGateController:
    def __init__(
        self,
        *,
        input_fn: Callable[[str], str] = input,
        output_fn: Callable[[str], None] = print,
    ) -> None:
        self._input_fn = input_fn
        self._output_fn = output_fn

    def require_explicit_approval(self, review_result: AutomatedReviewResult) -> HumanGateDecision:
        prompt_text = build_approval_request(review_result)
        self._output_fn(prompt_text)
        response = self._input_fn("北冥是否批准进入下一步？[Y/Confirm]: ").strip()
        approved = response.lower() in _APPROVAL_TOKENS
        return HumanGateDecision(approved=approved, response=response, prompt_text=prompt_text)


def build_approval_request(review_result: AutomatedReviewResult) -> str:
    first_reason = review_result.reasons[0] if review_result.reasons else "无"
    return (
        "《北冥裁决请示书》\n"
        f"- 当前裁决: {review_result.verdict}\n"
        f"- M3 审计: {review_result.audit_result.verdict}\n"
        f"- pytest: exit={review_result.pytest.exit_code}\n"
        f"- 主结论: {first_reason}\n"
        "- 请求: 若认可，请输入 Y 或 Confirm；否则保持停机。"
    )
