"""ECC ecc-devops -- Hermes plugin.

Provides 15 skills:
  - agent-opensource-forker
  - agent-opensource-packager
  - agent-opensource-sanitizer
  - automation-audit-ops
  - canary-watch
  - cmd-auto-update
  - cmd-projects
  - deployment-patterns
  - dmux-workflows
  - docker-patterns
  - enterprise-agent-ops
  - github-ops
  - opensource-pipeline
  - project-flow-ops
  - terminal-ops
"""

from pathlib import Path

_PLUGIN_DIR = Path(__file__).parent
_SKILLS_DIR = _PLUGIN_DIR / "skills"

SKILLS = [
    "agent-opensource-forker",
        "agent-opensource-packager",
        "agent-opensource-sanitizer",
        "automation-audit-ops",
        "canary-watch",
        "cmd-auto-update",
        "cmd-projects",
        "deployment-patterns",
        "dmux-workflows",
        "docker-patterns",
        "enterprise-agent-ops",
        "github-ops",
        "opensource-pipeline",
        "project-flow-ops",
        "terminal-ops",
]


def register(ctx):
    """Register all ecc-devops skills and commands."""
    for skill in SKILLS:
        skill_path = _SKILLS_DIR / f"{skill}.md"
        if skill_path.exists():
            ctx.register_skill(
                name=skill,
                path=skill_path,
                description=f"ECC: {skill}",
            )

        # Register /auto-update slash command
    def _handle_auto_update(raw_args: str) -> str:
        return '---\ndescription: Pull the latest ECC repo changes and reinstall the current managed targets.\ndisable-model-invocation: true\n---\n\n# Auto Update\n\nUpdate ECC from its upstream repo and regenerate the current context\'s managed install using the original install-state request.\n\n## Usage\n\n```bash\n# Preview the update without mutating anything\nECC_ROOT="${CLAUDE_PLUGIN_ROOT:-$(node -e "var r=(()=>{var e=process.env.CLAUDE_PLUGIN_ROOT;if(e&&e.trim())return e.trim();var p=require(\'path\'),f=require(\'fs\'),h=require(\'os\').homedir(),d=p.join(h,\'.claude\'),q=p.join(\'scripts\',\'lib\',\'utils.js\');if(f.existsSync(p.join(d,q)))return d;for(var s of [[\'ecc\'],[\'ecc@ecc\'],[\'marketplace\',\'ecc\'],[\'everything-claude-code\'],[\'everything-claude-code@everything-claude-code\'],[\'marketplace\',\'everything-claude-code\']]){var l=p.join(d,\'plugins\',...s);if(f.existsSync(p.join(l,q)))return l}try{for(var g of [\'ecc\',\'everything-claude-code\']){var b=p.join(d,\'plugins\',\'cache\',g);for(var o of f.readdirSync(b,{withFileTypes:true})){if(!o.isDirectory())continue;for(var v of f.readdirSync(p.join(b,o.name),{withFileTypes:true})){if(!v.isDirectory())continue;var c=p.join(b,o.name,v.name);if(f.existsSync(p.join(c,q)))return c}}}}catch(x){}return d})();console.log(r)")}"\nnode "$ECC_ROOT/scripts/auto-update.js" --dry-run\n\n# Update only Cursor-managed files in the current project\nnode "$ECC_ROOT/scripts/auto-update.js" --target cursor\n\n# Override the ECC repo root explicitly\nnode "$ECC_ROOT/scripts/auto-update.js" --repo-root /path/to/everything-claude-code\n```\n\n## Notes\n\n- This command uses the recorded install-state request and reruns `install-apply.js` after pulling the latest repo changes.\n- Reinstall is intentional: it handles upstream renames and deletions that `repair.js` cannot safely reconstruct from stale operations alone.\n- Use `--dry-run` first if you want to see the reconstructed reinstall plan before mutating anything.\n'
    ctx.register_command(
        name="auto-update",
        handler=_handle_auto_update,
        description="ECC /auto-update command",
    )


    # Register /projects slash command
    def _handle_projects(raw_args: str) -> str:
        return '---\nname: projects\ndescription: List known projects and their instinct statistics\ncommand: true\n---\n\n# Projects Command\n\nList project registry entries and per-project instinct/observation counts for continuous-learning-v2.\n\n## Implementation\n\nRun the instinct CLI using the plugin root path:\n\n```bash\npython3 "${CLAUDE_PLUGIN_ROOT}/skills/continuous-learning-v2/scripts/instinct-cli.py" projects\n```\n\nOr if `CLAUDE_PLUGIN_ROOT` is not set (manual installation):\n\n```bash\npython3 ~/.claude/skills/continuous-learning-v2/scripts/instinct-cli.py projects\n```\n\n## Usage\n\n```bash\n/projects\n```\n\n## What to Do\n\n1. Read `~/.claude/homunculus/projects.json`\n2. For each project, display:\n   - Project name, id, root, remote\n   - Personal and inherited instinct counts\n   - Observation event count\n   - Last seen timestamp\n3. Also display global instinct totals\n'
    ctx.register_command(
        name="projects",
        handler=_handle_projects,
        description="ECC /projects command",
    )

