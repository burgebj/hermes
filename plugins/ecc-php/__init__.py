"""ECC ecc-php -- Hermes plugin.

Provides 6 skills:
  - laravel-patterns
  - laravel-plugin-discovery
  - laravel-security
  - laravel-tdd
  - laravel-verification
  - rules-php
"""

from pathlib import Path

_PLUGIN_DIR = Path(__file__).parent
_SKILLS_DIR = _PLUGIN_DIR / "skills"

SKILLS = [
    "laravel-patterns",
        "laravel-plugin-discovery",
        "laravel-security",
        "laravel-tdd",
        "laravel-verification",
        "rules-php",
]


def register(ctx):
    """Register all ecc-php skills and commands."""
    for skill in SKILLS:
        skill_path = _SKILLS_DIR / f"{skill}.md"
        if skill_path.exists():
            ctx.register_skill(
                name=skill,
                path=skill_path,
                description=f"ECC: {skill}",
            )

        pass  # No slash commands to register
