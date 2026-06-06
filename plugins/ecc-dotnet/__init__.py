"""ECC ecc-dotnet -- Hermes plugin.

Provides 4 skills:
  - agent-csharp-reviewer
  - csharp-testing
  - dotnet-patterns
  - rules-csharp
"""

from pathlib import Path

_PLUGIN_DIR = Path(__file__).parent
_SKILLS_DIR = _PLUGIN_DIR / "skills"

SKILLS = [
    "agent-csharp-reviewer",
        "csharp-testing",
        "dotnet-patterns",
        "rules-csharp",
]


def register(ctx):
    """Register all ecc-dotnet skills and commands."""
    for skill in SKILLS:
        skill_path = _SKILLS_DIR / f"{skill}.md"
        if skill_path.exists():
            ctx.register_skill(
                name=skill,
                path=skill_path,
                description=f"ECC: {skill}",
            )

        pass  # No slash commands to register
