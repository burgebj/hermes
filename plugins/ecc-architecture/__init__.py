"""ECC ecc-architecture -- Hermes plugin.

Provides 15 skills:
  - agent-a11y-architect
  - agent-architect
  - agent-code-architect
  - agent-database-reviewer
  - api-connector-builder
  - api-design
  - architecture-decision-records
  - backend-patterns
  - connections-optimizer
  - content-hash-cache-pattern
  - database-migrations
  - design-system
  - hexagonal-architecture
  - mcp-server-patterns
  - postgres-patterns
"""

from pathlib import Path

_PLUGIN_DIR = Path(__file__).parent
_SKILLS_DIR = _PLUGIN_DIR / "skills"

SKILLS = [
    "agent-a11y-architect",
        "agent-architect",
        "agent-code-architect",
        "agent-database-reviewer",
        "api-connector-builder",
        "api-design",
        "architecture-decision-records",
        "backend-patterns",
        "connections-optimizer",
        "content-hash-cache-pattern",
        "database-migrations",
        "design-system",
        "hexagonal-architecture",
        "mcp-server-patterns",
        "postgres-patterns",
]


def register(ctx):
    """Register all ecc-architecture skills and commands."""
    for skill in SKILLS:
        skill_path = _SKILLS_DIR / f"{skill}.md"
        if skill_path.exists():
            ctx.register_skill(
                name=skill,
                path=skill_path,
                description=f"ECC: {skill}",
            )

        pass  # No slash commands to register
