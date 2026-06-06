"""ECC ecc-perl -- Hermes plugin.

Provides 4 skills:
  - perl-patterns
  - perl-security
  - perl-testing
  - rules-perl
"""

from pathlib import Path

_PLUGIN_DIR = Path(__file__).parent
_SKILLS_DIR = _PLUGIN_DIR / "skills"

SKILLS = [
    "perl-patterns",
        "perl-security",
        "perl-testing",
        "rules-perl",
]


def register(ctx):
    """Register all ecc-perl skills and commands."""
    for skill in SKILLS:
        skill_path = _SKILLS_DIR / f"{skill}.md"
        if skill_path.exists():
            ctx.register_skill(
                name=skill,
                path=skill_path,
                description=f"ECC: {skill}",
            )

        pass  # No slash commands to register
