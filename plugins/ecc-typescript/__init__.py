"""ECC ecc-typescript -- Hermes plugin.

Provides 11 skills:
  - agent-typescript-reviewer
  - bun-runtime
  - frontend-patterns
  - frontend-slides
  - nestjs-patterns
  - nextjs-turbopack
  - nodejs-keccak256
  - nuxt4-patterns
  - rules-typescript
  - rules-web
  - ui-demo
"""

from pathlib import Path

_PLUGIN_DIR = Path(__file__).parent
_SKILLS_DIR = _PLUGIN_DIR / "skills"

SKILLS = [
    "agent-typescript-reviewer",
        "bun-runtime",
        "frontend-patterns",
        "frontend-slides",
        "nestjs-patterns",
        "nextjs-turbopack",
        "nodejs-keccak256",
        "nuxt4-patterns",
        "rules-typescript",
        "rules-web",
        "ui-demo",
]


def register(ctx):
    """Register all ecc-typescript skills and commands."""
    for skill in SKILLS:
        skill_path = _SKILLS_DIR / f"{skill}.md"
        if skill_path.exists():
            ctx.register_skill(
                name=skill,
                path=skill_path,
                description=f"ECC: {skill}",
            )

        pass  # No slash commands to register
