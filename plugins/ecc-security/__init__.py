"""ECC ecc-security -- Hermes plugin.

Provides 10 skills:
  - agent-security-reviewer
  - defi-amm-security
  - gateguard
  - healthcare-phi-compliance
  - hipaa-compliance
  - llm-trading-agent-security
  - safety-guard
  - security-bounty-hunter
  - security-review
  - security-scan
"""

from pathlib import Path

_PLUGIN_DIR = Path(__file__).parent
_SKILLS_DIR = _PLUGIN_DIR / "skills"

SKILLS = [
    "agent-security-reviewer",
        "defi-amm-security",
        "gateguard",
        "healthcare-phi-compliance",
        "hipaa-compliance",
        "llm-trading-agent-security",
        "safety-guard",
        "security-bounty-hunter",
        "security-review",
        "security-scan",
]


def register(ctx):
    """Register all ecc-security skills and commands."""
    for skill in SKILLS:
        skill_path = _SKILLS_DIR / f"{skill}.md"
        if skill_path.exists():
            ctx.register_skill(
                name=skill,
                path=skill_path,
                description=f"ECC: {skill}",
            )

        pass  # No slash commands to register
