"""
smart_router.py — core classifier, features, and tier definitions
for the Hermes SmartRouter plugin.

Self-contained module with zero external dependencies (pure Python stdlib).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════
# Tier definitions
# ═══════════════════════════════════════════════════════════════════

class TierLevel(IntEnum):
    T0 = 0  # Simple chat, greetings
    T1 = 1  # Information retrieval, analysis
    T2 = 2  # Code generation, debugging, reasoning
    T3 = 3  # Complex architecture, security, refactoring


@dataclass
class TierConfig:
    level: TierLevel
    model: str
    provider: str = ""
    reasoning_effort: str = ""
    description: str = ""


DEFAULT_TIERS: Dict[TierLevel, TierConfig] = {
    TierLevel.T0: TierConfig(
        level=TierLevel.T0,
        model="deepseek-v4-flash",
        provider="deepseek",
        description="Simple chat, greetings — cheap & fast",
    ),
    TierLevel.T1: TierConfig(
        level=TierLevel.T1,
        model="qwen3.7-max",
        provider="ali-token-plan",
        description="Info retrieval, analysis — balanced",
    ),
    TierLevel.T2: TierConfig(
        level=TierLevel.T2,
        model="qwen3.7-max",
        provider="ali-token-plan",
        reasoning_effort="high",
        description="Code, debugging — capable with reasoning",
    ),
    TierLevel.T3: TierConfig(
        level=TierLevel.T3,
        model="claude-sonnet-4-20250514",
        provider="ali-token-plan",
        reasoning_effort="high",
        description="Architecture, security — top capability",
    ),
}


# ═══════════════════════════════════════════════════════════════════
# Feature extraction
# ═══════════════════════════════════════════════════════════════════

_CODE_BLOCK_OPEN = re.compile(r"(?:^|\n)```(\w*)")
_SHELL_PATTERN = re.compile(
    r"\b(?:bash|sh|zsh|powershell|cmd|terminal|console)\b", re.IGNORECASE
)
_FILE_PATH_PATTERN = re.compile(
    r"(?:~/|/|[a-zA-Z]:[/\\]|\.\.?/)[\w.\-/\\]+\.[a-z]{1,4}(?::\d+)?", re.IGNORECASE
)
_KEYWORD_PATTERN = re.compile(
    r"(?:"
    r"重构|优化|审计|安全|迁移|部署|设计|架构|"
    r"分析|计算|查询|搜索|统计|生成|对比|评估|"
    r"refactor|optimize|audit|security|migrate|deploy|design|architecture|"
    r"analyze|analysis|search|query|generate|compare|evaluate|"
    r"并发|竞态|deadlock|race|thread|"
    r"concurrent|deadlock|race\s*condition|thread|"
    r"加密|auth|oauth|jwt|token|certificate|"
    r"encrypt|auth|oauth|jwt|token|cert|"
    r"数据库|sql|query|schema|migration|"
    r"database|sql|query|schema|migration"
    r")",
    re.IGNORECASE,
)
_HIGH_COMPLEXITY_KEYWORDS = re.compile(
    r"(?:"
    r"security|audit|审计|安全|penetration|渗透|"
    r"architecture|架构|distributed|分布式|"
    r"refactor|重构|migration|迁移|rollback|回滚|"
    r"crypto|cryptography|加密|encrypt|decrypt|"
    r"thread(?:\s*safe)?|并发|竞态|deadlock|"
    r"zero\s*trust|零信任|auth[0-9]|oauth|jwt|"
    r"kubernetes|k8s|docker|container|容器|"
    r"performance|性能|optimization|优化|瓶颈|bottleneck"
    r")",
    re.IGNORECASE,
)
_SIMPLE_GREETINGS = re.compile(
    r"^(?:"
    r"你好|嗨|hello|hi|hey|早安|午安|晚安|"
    r"谢谢|thank|thanks|好的|ok|好的|继续|"
    r"嗯|是|对|好|行|可以|再?见|bye"
    r")\s*[.。!！?？]?\s*$",
    re.IGNORECASE,
)


@dataclass
class TaskFeatures:
    text: str = ""
    length: int = 0
    has_code_block: bool = False
    code_block_count: int = 0
    code_languages: List[str] = field(default_factory=list)
    code_ratio: float = 0.0
    has_shell_commands: bool = False
    has_file_paths: bool = False
    keyword_count: int = 0
    high_complexity_count: int = 0
    is_simple_greeting: bool = False
    has_questions: bool = False
    question_count: int = 0
    is_multi_line: bool = False
    line_count: int = 0
    contains_url: bool = False
    contains_json: bool = False


def extract_features(message: str) -> TaskFeatures:
    features = TaskFeatures(text=message[:200], length=len(message))

    blocks = _CODE_BLOCK_OPEN.findall(message)
    opening_blocks = [b for b in blocks if b]
    features.has_code_block = len(blocks) > 0
    features.code_block_count = len(opening_blocks) if opening_blocks else (1 if blocks else 0)
    features.code_languages = [b for b in blocks if b]

    code_lines = 0
    total_lines = message.count("\n") + 1
    in_code = False
    for line in message.split("\n"):
        if line.strip().startswith("```"):
            in_code = not in_code
        elif in_code:
            code_lines += 1
    features.code_ratio = code_lines / max(total_lines, 1)

    features.has_shell_commands = bool(_SHELL_PATTERN.search(message))
    features.has_file_paths = bool(_FILE_PATH_PATTERN.search(message))
    features.keyword_count = len(_KEYWORD_PATTERN.findall(message))
    features.high_complexity_count = len(_HIGH_COMPLEXITY_KEYWORDS.findall(message))
    features.is_simple_greeting = bool(_SIMPLE_GREETINGS.match(message.strip()))
    features.question_count = message.count("?") + message.count("？")
    features.has_questions = features.question_count > 0
    features.is_multi_line = "\n" in message.strip()
    features.line_count = total_lines
    features.contains_url = bool(re.search(r"https?://[^\s,，。；;'\"<>()（）]+", message))
    features.contains_json = bool(re.search(r'\{[\s\S]*"[^"]+"\s*:', message))

    return features


# ═══════════════════════════════════════════════════════════════════
# Classifier
# ═══════════════════════════════════════════════════════════════════

@dataclass
class ClassificationResult:
    tier: TierLevel
    config: TierConfig
    features: TaskFeatures = field(default_factory=lambda: TaskFeatures())
    reason: str = ""
    score: float = 0.0


class Classifier:
    """Rule-based task complexity classifier.

    Classifier is stateless — one instance is shared across all sessions.
    """

    def __init__(
        self,
        tiers: Optional[Dict[TierLevel, TierConfig]] = None,
        default_tier: TierLevel = TierLevel.T1,
    ):
        self.tiers = tiers or dict(DEFAULT_TIERS)
        self.default_tier = default_tier

    def classify(self, message: str) -> ClassificationResult:
        features = extract_features(message)
        tier, score, reason = self._predict(features)
        return ClassificationResult(
            tier=tier,
            config=self.tiers.get(tier, self.tiers[self.default_tier]),
            features=features,
            reason=reason,
            score=score,
        )

    def _predict(self, features: TaskFeatures) -> Tuple[TierLevel, float, str]:
        # Priority 1: Simple greetings → T0
        if features.is_simple_greeting:
            return (TierLevel.T0, 0.95, "Detected simple greeting/acknowledgment")

        # Priority 2: High-complexity keywords → T3
        if features.high_complexity_count >= 3:
            return (
                TierLevel.T3, 0.85,
                f"Found {features.high_complexity_count} high-complexity keywords "
                f"(security/architecture/refactor)"
            )

        # Priority 3: Multiple code blocks → T2
        if features.has_code_block and features.code_block_count >= 2:
            return (TierLevel.T2, 0.80,
                    f"Multiple code blocks ({features.code_block_count}) detected")

        # Priority 4: Single code block
        if features.has_code_block:
            if features.high_complexity_count >= 1:
                return (TierLevel.T2, 0.75,
                        "Code block + high-complexity keywords suggest non-trivial task")
            return (TierLevel.T1, 0.65, "Single code block — moderate complexity")

        # Priority 5: High code ratio (inline code)
        if features.code_ratio > 0.3 and features.length > 500:
            return (TierLevel.T2, 0.70,
                    f"High code ratio ({features.code_ratio:.0%}) in long message")

        # Priority 6: File paths + keywords
        if features.has_file_paths and features.keyword_count >= 2:
            if features.high_complexity_count >= 1:
                return (TierLevel.T3, 0.75,
                        "File paths + complex keywords indicate system-level work")
            return (TierLevel.T2, 0.65,
                    "File paths with task keywords suggest development work")

        # Priority 7: Very long messages
        if features.length > 2000:
            if features.keyword_count >= 3:
                return (TierLevel.T3, 0.70,
                        f"Long message ({features.length} chars) with {features.keyword_count} "
                        f"task keywords — likely complex analysis")
            return (TierLevel.T2, 0.60,
                    f"Long message ({features.length} chars) — allocate capable model")

        # Priority 8: Medium length with keywords
        if features.length <= 2000 and features.keyword_count >= 2:
            return (TierLevel.T1, 0.70,
                    f"Moderate length with {features.keyword_count} keywords — "
                    f"info retrieval or analysis")

        # Priority 9: Short with keywords (e.g. "分析一下趋势")
        if features.length <= 200 and features.keyword_count >= 1:
            return (TierLevel.T1, 0.65,
                    f"Short message ({features.length} chars) with task keyword — "
                    f"likely an actionable request")

        # Priority 10: Short no-signal messages → T0
        if features.length <= 200:
            return (TierLevel.T0, 0.80,
                    f"Short message ({features.length} chars, minimal signals) — "
                    f"use cheapest tier")

        return (self.default_tier, 0.50,
                f"No strong signals — using default tier ({self.default_tier.name})")


# ═══════════════════════════════════════════════════════════════════
# Cost estimation (approximate)
# ═══════════════════════════════════════════════════════════════════

_COST_PER_1K = {
    "deepseek-v4-flash": 0.00015,
    "qwen3.7-max": 0.0015,
    "claude-sonnet-4-20250514": 0.003,
}


def estimate_cost(message: str, classifier: Classifier) -> dict:
    result = classifier.classify(message)
    input_tokens = int(len(message) * 0.35)
    output_tokens = 500
    total_tokens = input_tokens + output_tokens

    model_name = result.config.model
    base_cost = _COST_PER_1K.get(model_name, 0.001)
    cost = (total_tokens / 1000) * base_cost

    alternatives = {}
    for tl in TierLevel:
        if tl == result.tier:
            continue
        cfg = classifier.tiers.get(tl)
        if not cfg:
            continue
        alt_cost = _COST_PER_1K.get(cfg.model, 0.001)
        alternatives[tl.name] = round((total_tokens / 1000) * alt_cost, 6)

    return {
        "recommended_tier": result.tier.name,
        "recommended_model": model_name,
        "reason": result.reason,
        "estimated_cost_usd": round(cost, 6),
        "input_tokens_est": input_tokens,
        "output_tokens_est": output_tokens,
        "savings_vs_t3": round((1 - cost / alternatives.get("T3", cost)) * 100, 1) if "T3" in alternatives else 0,
    }
