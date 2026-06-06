"""ECC ecc-swift -- Hermes plugin.

Provides 5 skills:
  - rules-swift
  - swift-actor-persistence
  - swift-concurrency-6-2
  - swift-protocol-di-testing
  - swiftui-patterns
"""

from pathlib import Path

_PLUGIN_DIR = Path(__file__).parent
_SKILLS_DIR = _PLUGIN_DIR / "skills"

SKILLS = [
    "rules-swift",
        "swift-actor-persistence",
        "swift-concurrency-6-2",
        "swift-protocol-di-testing",
        "swiftui-patterns",
]


def register(ctx):
    """Register all ecc-swift skills and commands."""
    for skill in SKILLS:
        skill_path = _SKILLS_DIR / f"{skill}.md"
        if skill_path.exists():
            ctx.register_skill(
                name=skill,
                path=skill_path,
                description=f"ECC: {skill}",
            )

        pass  # No slash commands to register
