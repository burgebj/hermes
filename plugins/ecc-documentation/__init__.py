"""ECC ecc-documentation -- Hermes plugin.

Provides 14 skills:
  - agent-doc-updater
  - agent-docs-lookup
  - article-writing
  - cmd-learn
  - cmd-learn-eval
  - cmd-update-codemaps
  - cmd-update-docs
  - codebase-onboarding
  - deep-research
  - documentation-lookup
  - iterative-retrieval
  - knowledge-ops
  - research-ops
  - search-first
"""

from pathlib import Path

_PLUGIN_DIR = Path(__file__).parent
_SKILLS_DIR = _PLUGIN_DIR / "skills"

SKILLS = [
    "agent-doc-updater",
        "agent-docs-lookup",
        "article-writing",
        "cmd-learn",
        "cmd-learn-eval",
        "cmd-update-codemaps",
        "cmd-update-docs",
        "codebase-onboarding",
        "deep-research",
        "documentation-lookup",
        "iterative-retrieval",
        "knowledge-ops",
        "research-ops",
        "search-first",
]


def register(ctx):
    """Register all ecc-documentation skills and commands."""
    for skill in SKILLS:
        skill_path = _SKILLS_DIR / f"{skill}.md"
        if skill_path.exists():
            ctx.register_skill(
                name=skill,
                path=skill_path,
                description=f"ECC: {skill}",
            )

        # Register /update-docs slash command
    def _handle_update_docs(raw_args: str) -> str:
        return "---\ndescription: Sync documentation from source-of-truth files such as scripts, schemas, routes, and exports.\n---\n\n# Update Documentation\n\nSync documentation with the codebase, generating from source-of-truth files.\n\n## Step 1: Identify Sources of Truth\n\n| Source | Generates |\n|--------|-----------|\n| `package.json` scripts | Available commands reference |\n| `.env.example` | Environment variable documentation |\n| `openapi.yaml` / route files | API endpoint reference |\n| Source code exports | Public API documentation |\n| `Dockerfile` / `docker-compose.yml` | Infrastructure setup docs |\n\n## Step 2: Generate Script Reference\n\n1. Read `package.json` (or `Makefile`, `Cargo.toml`, `pyproject.toml`)\n2. Extract all scripts/commands with their descriptions\n3. Generate a reference table:\n\n```markdown\n| Command | Description |\n|---------|-------------|\n| `npm run dev` | Start development server with hot reload |\n| `npm run build` | Production build with type checking |\n| `npm test` | Run test suite with coverage |\n```\n\n## Step 3: Generate Environment Documentation\n\n1. Read `.env.example` (or `.env.template`, `.env.sample`)\n2. Extract all variables with their purposes\n3. Categorize as required vs optional\n4. Document expected format and valid values\n\n```markdown\n| Variable | Required | Description | Example |\n|----------|----------|-------------|---------|\n| `DATABASE_URL` | Yes | PostgreSQL connection string | `postgres://user:pass@host:5432/db` |\n| `LOG_LEVEL` | No | Logging verbosity (default: info) | `debug`, `info`, `warn`, `error` |\n```\n\n## Step 4: Update Contributing Guide\n\nGenerate or update `docs/CONTRIBUTING.md` with:\n- Development environment setup (prerequisites, install steps)\n- Available scripts and their purposes\n- Testing procedures (how to run, how to write new tests)\n- Code style enforcement (linter, formatter, pre-commit hooks)\n- PR submission checklist\n\n## Step 5: Update Runbook\n\nGenerate or update `docs/RUNBOOK.md` with:\n- Deployment procedures (step-by-step)\n- Health check endpoints and monitoring\n- Common issues and their fixes\n- Rollback procedures\n- Alerting and escalation paths\n\n## Step 6: Staleness Check\n\n1. Find documentation files not modified in 90+ days\n2. Cross-reference with recent source code changes\n3. Flag potentially outdated docs for manual review\n\n## Step 7: Show Summary\n\n```\nDocumentation Update\n──────────────────────────────\nUpdated:  docs/CONTRIBUTING.md (scripts table)\nUpdated:  docs/ENV.md (3 new variables)\nFlagged:  docs/DEPLOY.md (142 days stale)\nSkipped:  docs/API.md (no changes detected)\n──────────────────────────────\n```\n\n## Rules\n\n- **Single source of truth**: Always generate from code, never manually edit generated sections\n- **Preserve manual sections**: Only update generated sections; leave hand-written prose intact\n- **Mark generated content**: Use `<!-- AUTO-GENERATED -->` markers around generated sections\n- **Don't create docs unprompted**: Only create new doc files if the command explicitly requests it\n"
    ctx.register_command(
        name="update-docs",
        handler=_handle_update_docs,
        description="ECC /update-docs command",
    )


    # Register /update-codemaps slash command
    def _handle_update_codemaps(raw_args: str) -> str:
        return '---\ndescription: Scan project structure and generate token-lean architecture codemaps.\n---\n\n# Update Codemaps\n\nAnalyze the codebase structure and generate token-lean architecture documentation.\n\n## Step 1: Scan Project Structure\n\n1. Identify the project type (monorepo, single app, library, microservice)\n2. Find all source directories (src/, lib/, app/, packages/)\n3. Map entry points (main.ts, index.ts, app.py, main.go, etc.)\n\n## Step 2: Generate Codemaps\n\nCreate or update codemaps in `docs/CODEMAPS/` (or `.reports/codemaps/`):\n\n| File | Contents |\n|------|----------|\n| `architecture.md` | High-level system diagram, service boundaries, data flow |\n| `backend.md` | API routes, middleware chain, service → repository mapping |\n| `frontend.md` | Page tree, component hierarchy, state management flow |\n| `data.md` | Database tables, relationships, migration history |\n| `dependencies.md` | External services, third-party integrations, shared libraries |\n\n### Codemap Format\n\nEach codemap should be token-lean — optimized for AI context consumption:\n\n```markdown\n# Backend Architecture\n\n## Routes\nPOST /api/users → UserController.create → UserService.create → UserRepo.insert\nGET  /api/users/:id → UserController.get → UserService.findById → UserRepo.findById\n\n## Key Files\nsrc/services/user.ts (business logic, 120 lines)\nsrc/repos/user.ts (database access, 80 lines)\n\n## Dependencies\n- PostgreSQL (primary data store)\n- Redis (session cache, rate limiting)\n- Stripe (payment processing)\n```\n\n## Step 3: Diff Detection\n\n1. If previous codemaps exist, calculate the diff percentage\n2. If changes > 30%, show the diff and request user approval before overwriting\n3. If changes <= 30%, update in place\n\n## Step 4: Add Metadata\n\nAdd a freshness header to each codemap:\n\n```markdown\n<!-- Generated: 2026-02-11 | Files scanned: 142 | Token estimate: ~800 -->\n```\n\n## Step 5: Save Analysis Report\n\nWrite a summary to `.reports/codemap-diff.txt`:\n- Files added/removed/modified since last scan\n- New dependencies detected\n- Architecture changes (new routes, new services, etc.)\n- Staleness warnings for docs not updated in 90+ days\n\n## Tips\n\n- Focus on **high-level structure**, not implementation details\n- Prefer **file paths and function signatures** over full code blocks\n- Keep each codemap under **1000 tokens** for efficient context loading\n- Use ASCII diagrams for data flow instead of verbose descriptions\n- Run after major feature additions or refactoring sessions\n'
    ctx.register_command(
        name="update-codemaps",
        handler=_handle_update_codemaps,
        description="ECC /update-codemaps command",
    )


    # Register /learn slash command
    def _handle_learn(raw_args: str) -> str:
        return "---\ndescription: Extract reusable patterns from the current session and save them as candidate skills or guidance.\n---\n\n# /learn - Extract Reusable Patterns\n\nAnalyze the current session and extract any patterns worth saving as skills.\n\n## Trigger\n\nRun `/learn` at any point during a session when you've solved a non-trivial problem.\n\n## What to Extract\n\nLook for:\n\n1. **Error Resolution Patterns**\n   - What error occurred?\n   - What was the root cause?\n   - What fixed it?\n   - Is this reusable for similar errors?\n\n2. **Debugging Techniques**\n   - Non-obvious debugging steps\n   - Tool combinations that worked\n   - Diagnostic patterns\n\n3. **Workarounds**\n   - Library quirks\n   - API limitations\n   - Version-specific fixes\n\n4. **Project-Specific Patterns**\n   - Codebase conventions discovered\n   - Architecture decisions made\n   - Integration patterns\n\n## Output Format\n\nCreate a skill file at `~/.claude/skills/learned/[pattern-name].md`:\n\n```markdown\n# [Descriptive Pattern Name]\n\n**Extracted:** [Date]\n**Context:** [Brief description of when this applies]\n\n## Problem\n[What problem this solves - be specific]\n\n## Solution\n[The pattern/technique/workaround]\n\n## Example\n[Code example if applicable]\n\n## When to Use\n[Trigger conditions - what should activate this skill]\n```\n\n## Process\n\n1. Review the session for extractable patterns\n2. Identify the most valuable/reusable insight\n3. Draft the skill file\n4. Ask user to confirm before saving\n5. Save to `~/.claude/skills/learned/`\n\n## Notes\n\n- Don't extract trivial fixes (typos, simple syntax errors)\n- Don't extract one-time issues (specific API outages, etc.)\n- Focus on patterns that will save time in future sessions\n- Keep skills focused - one pattern per skill\n"
    ctx.register_command(
        name="learn",
        handler=_handle_learn,
        description="ECC /learn command",
    )


    # Register /learn-eval slash command
    def _handle_learn_eval(raw_args: str) -> str:
        return '---\ndescription: "Extract reusable patterns from the session, self-evaluate quality before saving, and determine the right save location (Global vs Project)."\n---\n\n# /learn-eval - Extract, Evaluate, then Save\n\nExtends `/learn` with a quality gate, save-location decision, and knowledge-placement awareness before writing any skill file.\n\n## What to Extract\n\nLook for:\n\n1. **Error Resolution Patterns** — root cause + fix + reusability\n2. **Debugging Techniques** — non-obvious steps, tool combinations\n3. **Workarounds** — library quirks, API limitations, version-specific fixes\n4. **Project-Specific Patterns** — conventions, architecture decisions, integration patterns\n\n## Process\n\n1. Review the session for extractable patterns\n2. Identify the most valuable/reusable insight\n\n3. **Determine save location:**\n   - Ask: "Would this pattern be useful in a different project?"\n   - **Global** (`~/.claude/skills/learned/`): Generic patterns usable across 2+ projects (bash compatibility, LLM API behavior, debugging techniques, etc.)\n   - **Project** (`.claude/skills/learned/` in current project): Project-specific knowledge (quirks of a particular config file, project-specific architecture decisions, etc.)\n   - When in doubt, choose Global (moving Global → Project is easier than the reverse)\n\n4. Draft the skill file using this format:\n\n```markdown\n---\nname: pattern-name\ndescription: "Under 130 characters"\nuser-invocable: false\norigin: auto-extracted\n---\n\n# [Descriptive Pattern Name]\n\n**Extracted:** [Date]\n**Context:** [Brief description of when this applies]\n\n## Problem\n[What problem this solves - be specific]\n\n## Solution\n[The pattern/technique/workaround - with code examples]\n\n## When to Use\n[Trigger conditions]\n```\n\n5. **Quality gate — Checklist + Holistic verdict**\n\n   ### 5a. Required checklist (verify by actually reading files)\n\n   Execute **all** of the following before evaluating the draft:\n\n   - [ ] Grep `~/.claude/skills/` and relevant project `.claude/skills/` files by keyword to check for content overlap\n   - [ ] Check MEMORY.md (both project and global) for overlap\n   - [ ] Consider whether appending to an existing skill would suffice\n   - [ ] Confirm this is a reusable pattern, not a one-off fix\n\n   ### 5b. Holistic verdict\n\n   Synthesize the checklist results and draft quality, then choose **one** of the following:\n\n   | Verdict | Meaning | Next Action |\n   |---------|---------|-------------|\n   | **Save** | Unique, specific, well-scoped | Proceed to Step 6 |\n   | **Improve then Save** | Valuable but needs refinement | List improvements → revise → re-evaluate (once) |\n   | **Absorb into [X]** | Should be appended to an existing skill | Show target skill and additions → Step 6 |\n   | **Drop** | Trivial, redundant, or too abstract | Explain reasoning and stop |\n\n**Guideline dimensions** (informing the verdict, not scored):\n\n- **Specificity & Actionability**: Contains code examples or commands that are immediately usable\n- **Scope Fit**: Name, trigger conditions, and content are aligned and focused on a single pattern\n- **Uniqueness**: Provides value not covered by existing skills (informed by checklist results)\n- **Reusability**: Realistic trigger scenarios exist in future sessions\n\n6. **Verdict-specific confirmation flow**\n\n- **Improve then Save**: Present the required improvements + revised draft + updated checklist/verdict after one re-evaluation; if the revised verdict is **Save**, save after user confirmation, otherwise follow the new verdict\n- **Save**: Present save path + checklist results + 1-line verdict rationale + full draft → save after user confirmation\n- **Absorb into [X]**: Present target path + additions (diff format) + checklist results + verdict rationale → append after user confirmation\n- **Drop**: Show checklist results + reasoning only (no confirmation needed)\n\n7. Save / Absorb to the determined location\n\n## Output Format for Step 5\n\n```\n### Checklist\n- [x] skills/ grep: no overlap (or: overlap found → details)\n- [x] MEMORY.md: no overlap (or: overlap found → details)\n- [x] Existing skill append: new file appropriate (or: should append to [X])\n- [x] Reusability: confirmed (or: one-off → Drop)\n\n### Verdict: Save / Improve then Save / Absorb into [X] / Drop\n\n**Rationale:** (1-2 sentences explaining the verdict)\n```\n\n## Design Rationale\n\nThis version replaces the previous 5-dimension numeric scoring rubric (Specificity, Actionability, Scope Fit, Non-redundancy, Coverage scored 1-5) with a checklist-based holistic verdict system. Modern frontier models (Opus 4.6+) have strong contextual judgment — forcing rich qualitative signals into numeric scores loses nuance and can produce misleading totals. The holistic approach lets the model weigh all factors naturally, producing more accurate save/drop decisions while the explicit checklist ensures no critical check is skipped.\n\n## Notes\n\n- Don\'t extract trivial fixes (typos, simple syntax errors)\n- Don\'t extract one-time issues (specific API outages, etc.)\n- Focus on patterns that will save time in future sessions\n- Keep skills focused — one pattern per skill\n- When the verdict is Absorb, append to the existing skill rather than creating a new file\n'
    ctx.register_command(
        name="learn-eval",
        handler=_handle_learn_eval,
        description="ECC /learn-eval command",
    )

