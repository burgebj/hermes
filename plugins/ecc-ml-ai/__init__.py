"""ECC ecc-ml-ai -- Hermes plugin.

Provides 31 skills:
  - agent-gan-evaluator
  - agent-gan-generator
  - agent-gan-planner
  - agent-harness-construction
  - agent-harness-optimizer
  - agent-introspection-debugging
  - agent-loop-operator
  - agentic-engineering
  - autonomous-agent-harness
  - autonomous-loops
  - ck
  - cmd-gan-build
  - cmd-gan-design
  - cmd-loop-start
  - cmd-loop-status
  - cmd-model-route
  - cmd-santa-loop
  - context-budget
  - continuous-agent-loop
  - cost-aware-llm-pipeline
  - exa-search
  - fal-ai-media
  - foundation-models-on-device
  - gan-style-harness
  - manim-video
  - prompt-optimizer
  - regex-vs-llm-structured-text
  - remotion-video-creation
  - token-budget-advisor
  - video-editing
  - videodb
"""

from pathlib import Path

_PLUGIN_DIR = Path(__file__).parent
_SKILLS_DIR = _PLUGIN_DIR / "skills"

SKILLS = [
    "agent-gan-evaluator",
        "agent-gan-generator",
        "agent-gan-planner",
        "agent-harness-construction",
        "agent-harness-optimizer",
        "agent-introspection-debugging",
        "agent-loop-operator",
        "agentic-engineering",
        "autonomous-agent-harness",
        "autonomous-loops",
        "ck",
        "cmd-gan-build",
        "cmd-gan-design",
        "cmd-loop-start",
        "cmd-loop-status",
        "cmd-model-route",
        "cmd-santa-loop",
        "context-budget",
        "continuous-agent-loop",
        "cost-aware-llm-pipeline",
        "exa-search",
        "fal-ai-media",
        "foundation-models-on-device",
        "gan-style-harness",
        "manim-video",
        "prompt-optimizer",
        "regex-vs-llm-structured-text",
        "remotion-video-creation",
        "token-budget-advisor",
        "video-editing",
        "videodb",
]


def register(ctx):
    """Register all ecc-ml-ai skills and commands."""
    for skill in SKILLS:
        skill_path = _SKILLS_DIR / f"{skill}.md"
        if skill_path.exists():
            ctx.register_skill(
                name=skill,
                path=skill_path,
                description=f"ECC: {skill}",
            )

        # Register /loop-start slash command
    def _handle_loop_start(raw_args: str) -> str:
        return '---\ndescription: Start a managed autonomous loop pattern with safety defaults and explicit stop conditions.\n---\n\n# Loop Start Command\n\nStart a managed autonomous loop pattern with safety defaults.\n\n## Usage\n\n`/loop-start [pattern] [--mode safe|fast]`\n\n- `pattern`: `sequential`, `continuous-pr`, `rfc-dag`, `infinite`\n- `--mode`:\n  - `safe` (default): strict quality gates and checkpoints\n  - `fast`: reduced gates for speed\n\n## Flow\n\n1. Confirm repository state and branch strategy.\n2. Select loop pattern and model tier strategy.\n3. Enable required hooks/profile for the chosen mode.\n4. Create loop plan and write runbook under `.claude/plans/`.\n5. Print commands to start and monitor the loop.\n\n## Required Safety Checks\n\n- Verify tests pass before first loop iteration.\n- Ensure `ECC_HOOK_PROFILE` is not disabled globally.\n- Ensure loop has explicit stop condition.\n\n## Arguments\n\n$ARGUMENTS:\n- `<pattern>` optional (`sequential|continuous-pr|rfc-dag|infinite`)\n- `--mode safe|fast` optional\n'
    ctx.register_command(
        name="loop-start",
        handler=_handle_loop_start,
        description="ECC /loop-start command",
    )


    # Register /loop-status slash command
    def _handle_loop_status(raw_args: str) -> str:
        return '---\ndescription: Inspect active loop state, progress, failure signals, and recommended intervention.\n---\n\n# Loop Status Command\n\nInspect active loop state, progress, and failure signals.\n\nThis slash command can only run after the current session dequeues it. If you\nneed to inspect a wedged or sibling session, run the packaged CLI from another\nterminal:\n\n```bash\nnpx --package ecc-universal ecc loop-status --json\n```\n\nThe CLI scans local Claude transcript JSONL files under\n`~/.claude/projects/**` and reports stale `ScheduleWakeup` calls or `Bash`\ntool calls that have no matching `tool_result`.\n\n## Usage\n\n`/loop-status [--watch]`\n\n## What to Report\n\n- active loop pattern\n- current phase and last successful checkpoint\n- failing checks (if any)\n- estimated time/cost drift\n- recommended intervention (continue/pause/stop)\n\n## Cross-Session CLI\n\n- `ecc loop-status --json` emits machine-readable status for recent local\n  Claude transcripts.\n- `ecc loop-status --home <dir>` scans a different home directory when\n  inspecting another local profile or mounted workspace.\n- `ecc loop-status --transcript <session.jsonl>` inspects one transcript\n  directly.\n- `ecc loop-status --bash-timeout-seconds 1800` adjusts the stale Bash\n  threshold.\n- `ecc loop-status --exit-code` exits `2` when stale loop or tool signals are\n  found, or `1` when transcripts cannot be scanned.\n- `--exit-code` with `--watch` requires `--watch-count` so watchdog scripts do\n  not wait forever for a process exit.\n- `ecc loop-status --watch` refreshes status until interrupted.\n- `ecc loop-status --watch --watch-count 3 --exit-code` refreshes a bounded\n  number of times, then exits with the highest status seen.\n- `ecc loop-status --watch --watch-count 3` emits a bounded watch stream for\n  scripts and handoffs.\n- `ecc loop-status --watch --write-dir ~/.claude/loops` maintains\n  `index.json` and per-session JSON snapshots for sibling terminals or\n  watchdog scripts.\n\n## Watch Mode\n\nWhen `--watch` is present, refresh status periodically. With `--json`, each\nrefresh is emitted as one JSON object per line so another terminal or script can\nconsume the stream.\n\n## Snapshot Files\n\nUse `--write-dir <dir>` when a separate process needs to inspect loop state\nwithout waiting for the current Claude session to dequeue `/loop-status`. The\nCLI writes:\n\n- `index.json` with one row per inspected session.\n- `<session-id>.json` with the full status payload for that session.\n\nThese files are snapshots of local transcript analysis. They do not control or\ntimeout Claude Code runtime tool calls.\n\n## Arguments\n\n$ARGUMENTS:\n- `--watch` optional\n'
    ctx.register_command(
        name="loop-status",
        handler=_handle_loop_status,
        description="ECC /loop-status command",
    )


    # Register /santa-loop slash command
    def _handle_santa_loop(raw_args: str) -> str:
        return '---\ndescription: Adversarial dual-review convergence loop — two independent model reviewers must both approve before code ships.\n---\n\n# Santa Loop\n\nAdversarial dual-review convergence loop using the santa-method skill. Two independent reviewers — different models, no shared context — must both return NICE before code ships.\n\n## Purpose\n\nRun two independent reviewers (Claude Opus + an external model) against the current task output. Both must return NICE before the code is pushed. If either returns NAUGHTY, fix all flagged issues, commit, and re-run fresh reviewers — up to 3 rounds.\n\n## Usage\n\n```\n/santa-loop [file-or-glob | description]\n```\n\n## Workflow\n\n### Step 1: Identify What to Review\n\nDetermine the scope from `$ARGUMENTS` or fall back to uncommitted changes:\n\n```bash\ngit diff --name-only HEAD\n```\n\nRead all changed files to build the full review context. If `$ARGUMENTS` specifies a path, file, or description, use that as the scope instead.\n\n### Step 2: Build the Rubric\n\nConstruct a rubric appropriate to the file types under review. Every criterion must have an objective PASS/FAIL condition. Include at minimum:\n\n| Criterion | Pass Condition |\n|-----------|---------------|\n| Correctness | Logic is sound, no bugs, handles edge cases |\n| Security | No secrets, injection, XSS, or OWASP Top 10 issues |\n| Error handling | Errors handled explicitly, no silent swallowing |\n| Completeness | All requirements addressed, no missing cases |\n| Internal consistency | No contradictions between files or sections |\n| No regressions | Changes don\'t break existing behavior |\n\nAdd domain-specific criteria based on file types (e.g., type safety for TS, memory safety for Rust, migration safety for SQL).\n\n### Step 3: Dual Independent Review\n\nLaunch two reviewers **in parallel** using the Agent tool (both in a single message for concurrent execution). Both must complete before proceeding to the verdict gate.\n\nEach reviewer evaluates every rubric criterion as PASS or FAIL, then returns structured JSON:\n\n```json\n{\n  "verdict": "PASS" | "FAIL",\n  "checks": [\n    {"criterion": "...", "result": "PASS|FAIL", "detail": "..."}\n  ],\n  "critical_issues": ["..."],\n  "suggestions": ["..."]\n}\n```\n\nThe verdict gate (Step 4) maps these to NICE/NAUGHTY: both PASS → NICE, either FAIL → NAUGHTY.\n\n#### Reviewer A: Claude Agent (always runs)\n\nLaunch an Agent (subagent_type: `code-reviewer`, model: `opus`) with the full rubric + all files under review. The prompt must include:\n- The complete rubric\n- All file contents under review\n- "You are an independent quality reviewer. You have NOT seen any other review. Your job is to find problems, not to approve."\n- Return the structured JSON verdict above\n\n#### Reviewer B: External Model (Claude fallback only if no external CLI installed)\n\nFirst, detect which CLIs are available:\n```bash\ncommand -v codex >/dev/null 2>&1 && echo "codex" || true\ncommand -v gemini >/dev/null 2>&1 && echo "gemini" || true\n```\n\nBuild the reviewer prompt (identical rubric + instructions as Reviewer A) and write it to a unique temp file:\n```bash\nPROMPT_FILE=$(mktemp /tmp/santa-reviewer-b-XXXXXX.txt)\ncat > "$PROMPT_FILE" << \'EOF\'\n... full rubric + file contents + reviewer instructions ...\nEOF\n```\n\nUse the first available CLI:\n\n**Codex CLI** (if installed)\n```bash\ncodex exec --sandbox read-only -m gpt-5.4 -C "$(pwd)" - < "$PROMPT_FILE"\nrm -f "$PROMPT_FILE"\n```\n\n**Gemini CLI** (if installed and codex is not)\n```bash\ngemini -p "$(cat "$PROMPT_FILE")" -m gemini-2.5-pro\nrm -f "$PROMPT_FILE"\n```\n\n**Claude Agent fallback** (only if neither `codex` nor `gemini` is installed)\nLaunch a second Claude Agent (subagent_type: `code-reviewer`, model: `opus`). Log a warning that both reviewers share the same model family — true model diversity was not achieved but context isolation is still enforced.\n\nIn all cases, the reviewer must return the same structured JSON verdict as Reviewer A.\n\n### Step 4: Verdict Gate\n\n- **Both PASS** → **NICE** — proceed to Step 6 (push)\n- **Either FAIL** → **NAUGHTY** — merge all critical issues from both reviewers, deduplicate, proceed to Step 5\n\n### Step 5: Fix Cycle (NAUGHTY path)\n\n1. Display all critical issues from both reviewers\n2. Fix every flagged issue — change only what was flagged, no drive-by refactors\n3. Commit all fixes in a single commit:\n   ```\n   fix: address santa-loop review findings (round N)\n   ```\n4. Re-run Step 3 with **fresh reviewers** (no memory of previous rounds)\n5. Repeat until both return PASS\n\n**Maximum 3 iterations.** If still NAUGHTY after 3 rounds, stop and present remaining issues:\n\n```\nSANTA LOOP ESCALATION (exceeded 3 iterations)\n\nRemaining issues after 3 rounds:\n- [list all unresolved critical issues from both reviewers]\n\nManual review required before proceeding.\n```\n\nDo NOT push.\n\n### Step 6: Push (NICE path)\n\nWhen both reviewers return PASS:\n\n```bash\ngit push -u origin HEAD\n```\n\n### Step 7: Final Report\n\nPrint the output report (see Output section below).\n\n## Output\n\n```\nSANTA VERDICT: [NICE / NAUGHTY (escalated)]\n\nReviewer A (Claude Opus):   [PASS/FAIL]\nReviewer B ([model used]):  [PASS/FAIL]\n\nAgreement:\n  Both flagged:      [issues caught by both]\n  Reviewer A only:   [issues only A caught]\n  Reviewer B only:   [issues only B caught]\n\nIterations: [N]/3\nResult:     [PUSHED / ESCALATED TO USER]\n```\n\n## Notes\n\n- Reviewer A (Claude Opus) always runs — guarantees at least one strong reviewer regardless of tooling.\n- Model diversity is the goal for Reviewer B. GPT-5.4 or Gemini 2.5 Pro gives true independence — different training data, different biases, different blind spots. The Claude-only fallback still provides value via context isolation but loses model diversity.\n- Strongest available models are used: Opus for Reviewer A, GPT-5.4 or Gemini 2.5 Pro for Reviewer B.\n- External reviewers run with `--sandbox read-only` (Codex) to prevent repo mutation during review.\n- Fresh reviewers each round prevents anchoring bias from prior findings.\n- The rubric is the most important input. Tighten it if reviewers rubber-stamp or flag subjective style issues.\n- Commits happen on NAUGHTY rounds so fixes are preserved even if the loop is interrupted.\n- Push only happens after NICE — never mid-loop.\n'
    ctx.register_command(
        name="santa-loop",
        handler=_handle_santa_loop,
        description="ECC /santa-loop command",
    )


    # Register /model-route slash command
    def _handle_model_route(raw_args: str) -> str:
        return '---\ndescription: Recommend the best model tier for the current task based on complexity, risk, and budget.\n---\n\n# Model Route Command\n\nRecommend the best model tier for the current task by complexity and budget.\n\n## Usage\n\n`/model-route [task-description] [--budget low|med|high]`\n\n## Routing Heuristic\n\n- `haiku`: deterministic, low-risk mechanical changes\n- `sonnet`: default for implementation and refactors\n- `opus`: architecture, deep review, ambiguous requirements\n\n## Required Output\n\n- recommended model\n- confidence level\n- why this model fits\n- fallback model if first attempt fails\n\n## Arguments\n\n$ARGUMENTS:\n- `[task-description]` optional free-text\n- `--budget low|med|high` optional\n'
    ctx.register_command(
        name="model-route",
        handler=_handle_model_route,
        description="ECC /model-route command",
    )


    # Register /gan-build slash command
    def _handle_gan_build(raw_args: str) -> str:
        return '---\ndescription: Run a generator/evaluator build loop for implementation tasks with bounded iterations and scoring.\n---\n\nParse the following from $ARGUMENTS:\n1. `brief` — the user\'s one-line description of what to build\n2. `--max-iterations N` — (optional, default 15) maximum generator-evaluator cycles\n3. `--pass-threshold N` — (optional, default 7.0) weighted score to pass\n4. `--skip-planner` — (optional) skip planner, assume spec.md already exists\n5. `--eval-mode MODE` — (optional, default "playwright") one of: playwright, screenshot, code-only\n\n## GAN-Style Harness Build\n\nThis command orchestrates a three-agent build loop inspired by Anthropic\'s March 2026 harness design paper.\n\n### Phase 0: Setup\n1. Create `gan-harness/` directory in project root\n2. Create subdirectories: `gan-harness/feedback/`, `gan-harness/screenshots/`\n3. Initialize git if not already initialized\n4. Log start time and configuration\n\n### Phase 1: Planning (Planner Agent)\nUnless `--skip-planner` is set:\n1. Launch the `gan-planner` agent via Task tool with the user\'s brief\n2. Wait for it to produce `gan-harness/spec.md` and `gan-harness/eval-rubric.md`\n3. Display the spec summary to the user\n4. Proceed to Phase 2\n\n### Phase 2: Generator-Evaluator Loop\n```\niteration = 1\nwhile iteration <= max_iterations:\n\n    # GENERATE\n    Launch gan-generator agent via Task tool:\n    - Read spec.md\n    - If iteration > 1: read feedback/feedback-{iteration-1}.md\n    - Build/improve the application\n    - Ensure dev server is running\n    - Commit changes\n\n    # Wait for generator to finish\n\n    # EVALUATE\n    Launch gan-evaluator agent via Task tool:\n    - Read eval-rubric.md and spec.md\n    - Test the live application (mode: playwright/screenshot/code-only)\n    - Score against rubric\n    - Write feedback to feedback/feedback-{iteration}.md\n\n    # Wait for evaluator to finish\n\n    # CHECK SCORE\n    Read feedback/feedback-{iteration}.md\n    Extract weighted total score\n\n    if score >= pass_threshold:\n        Log "PASSED at iteration {iteration} with score {score}"\n        Break\n\n    if iteration >= 3 and score has not improved in last 2 iterations:\n        Log "PLATEAU detected — stopping early"\n        Break\n\n    iteration += 1\n```\n\n### Phase 3: Summary\n1. Read all feedback files\n2. Display final scores and iteration history\n3. Show score progression: `iteration 1: 4.2 → iteration 2: 5.8 → ... → iteration N: 7.5`\n4. List any remaining issues from the final evaluation\n5. Report total time and estimated cost\n\n### Output\n\n```markdown\n## GAN Harness Build Report\n\n**Brief:** [original prompt]\n**Result:** PASS/FAIL\n**Iterations:** N / max\n**Final Score:** X.X / 10\n\n### Score Progression\n| Iter | Design | Originality | Craft | Functionality | Total |\n|------|--------|-------------|-------|---------------|-------|\n| 1 | ... | ... | ... | ... | X.X |\n| 2 | ... | ... | ... | ... | X.X |\n| N | ... | ... | ... | ... | X.X |\n\n### Remaining Issues\n- [Any issues from final evaluation]\n\n### Files Created\n- gan-harness/spec.md\n- gan-harness/eval-rubric.md\n- gan-harness/feedback/feedback-001.md through feedback-NNN.md\n- gan-harness/generator-state.md\n- gan-harness/build-report.md\n```\n\nWrite the full report to `gan-harness/build-report.md`.\n'
    ctx.register_command(
        name="gan-build",
        handler=_handle_gan_build,
        description="ECC /gan-build command",
    )


    # Register /gan-design slash command
    def _handle_gan_design(raw_args: str) -> str:
        return '---\ndescription: Run a generator/evaluator design loop for frontend or visual work with bounded iterations and scoring.\n---\n\nParse the following from $ARGUMENTS:\n1. `brief` — the user\'s description of the design to create\n2. `--max-iterations N` — (optional, default 10) maximum design-evaluate cycles\n3. `--pass-threshold N` — (optional, default 7.5) weighted score to pass (higher default for design)\n\n## GAN-Style Design Harness\n\nA two-agent loop (Generator + Evaluator) focused on frontend design quality. No planner — the brief IS the spec.\n\nThis is the same mode Anthropic used for their frontend design experiments, where they saw creative breakthroughs like the 3D Dutch art museum with CSS perspective and doorway navigation.\n\n### Setup\n1. Create `gan-harness/` directory\n2. Write the brief directly as `gan-harness/spec.md`\n3. Write a design-focused `gan-harness/eval-rubric.md` with extra weight on Design Quality and Originality\n\n### Design-Specific Eval Rubric\n```markdown\n### Design Quality (weight: 0.35)\n### Originality (weight: 0.30)\n### Craft (weight: 0.25)\n### Functionality (weight: 0.10)\n```\n\nNote: Originality weight is higher (0.30 vs 0.20) to push for creative breakthroughs. Functionality weight is lower since design mode focuses on visual quality.\n\n### Loop\nSame as `/project:gan-build` Phase 2, but:\n- Skip the planner\n- Use the design-focused rubric\n- Generator prompt emphasizes visual quality over feature completeness\n- Evaluator prompt emphasizes "would this win a design award?" over "do all features work?"\n\n### Key Difference from gan-build\nThe Generator is told: "Your PRIMARY goal is visual excellence. A stunning half-finished app beats a functional ugly one. Push for creative leaps — unusual layouts, custom animations, distinctive color work."\n'
    ctx.register_command(
        name="gan-design",
        handler=_handle_gan_design,
        description="ECC /gan-design command",
    )

