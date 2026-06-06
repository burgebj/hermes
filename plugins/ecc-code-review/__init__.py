"""ECC ecc-code-review -- Hermes plugin.

Provides 14 skills:
  - agent-comment-analyzer
  - agent-conversation-analyzer
  - agent-pr-test-analyzer
  - agent-silent-failure-hunter
  - agent-type-design-analyzer
  - cmd-code-review
  - cmd-quality-gate
  - cmd-refactor-clean
  - cmd-review-pr
  - cmd-test-coverage
  - code-tour
  - plankton-code-quality
  - repo-scan
  - rules-distill
"""

from pathlib import Path

_PLUGIN_DIR = Path(__file__).parent
_SKILLS_DIR = _PLUGIN_DIR / "skills"

SKILLS = [
    "agent-comment-analyzer",
        "agent-conversation-analyzer",
        "agent-pr-test-analyzer",
        "agent-silent-failure-hunter",
        "agent-type-design-analyzer",
        "cmd-code-review",
        "cmd-quality-gate",
        "cmd-refactor-clean",
        "cmd-review-pr",
        "cmd-test-coverage",
        "code-tour",
        "plankton-code-quality",
        "repo-scan",
        "rules-distill",
]


def register(ctx):
    """Register all ecc-code-review skills and commands."""
    for skill in SKILLS:
        skill_path = _SKILLS_DIR / f"{skill}.md"
        if skill_path.exists():
            ctx.register_skill(
                name=skill,
                path=skill_path,
                description=f"ECC: {skill}",
            )

        # Register /code-review slash command
    def _handle_code_review(raw_args: str) -> str:
        return '---\ndescription: Code review — local uncommitted changes or GitHub PR (pass PR number/URL for PR mode)\nargument-hint: [pr-number | pr-url | blank for local review]\n---\n\n# Code Review\n\n> PR review mode adapted from PRPs-agentic-eng by Wirasm. Part of the PRP workflow series.\n\n**Input**: $ARGUMENTS\n\n---\n\n## Mode Selection\n\nIf `$ARGUMENTS` contains a PR number, PR URL, or `--pr`:\n→ Jump to **PR Review Mode** below.\n\nOtherwise:\n→ Use **Local Review Mode**.\n\n---\n\n## Local Review Mode\n\nComprehensive security and quality review of uncommitted changes.\n\n### Phase 1 — GATHER\n\n```bash\ngit diff --name-only HEAD\n```\n\nIf no changed files, stop: "Nothing to review."\n\n### Phase 2 — REVIEW\n\nRead each changed file in full. Check for:\n\n**Security Issues (CRITICAL):**\n- Hardcoded credentials, API keys, tokens\n- SQL injection vulnerabilities\n- XSS vulnerabilities\n- Missing input validation\n- Insecure dependencies\n- Path traversal risks\n\n**Code Quality (HIGH):**\n- Functions > 50 lines\n- Files > 800 lines\n- Nesting depth > 4 levels\n- Missing error handling\n- console.log statements\n- TODO/FIXME comments\n- Missing JSDoc for public APIs\n\n**Best Practices (MEDIUM):**\n- Mutation patterns (use immutable instead)\n- Emoji usage in code/comments\n- Missing tests for new code\n- Accessibility issues (a11y)\n\n### Phase 3 — REPORT\n\nGenerate report with:\n- Severity: CRITICAL, HIGH, MEDIUM, LOW\n- File location and line numbers\n- Issue description\n- Suggested fix\n\nBlock commit if CRITICAL or HIGH issues found.\nNever approve code with security vulnerabilities.\n\n---\n\n## PR Review Mode\n\nComprehensive GitHub PR review — fetches diff, reads full files, runs validation, posts review.\n\n### Phase 1 — FETCH\n\nParse input to determine PR:\n\n| Input | Action |\n|---|---|\n| Number (e.g. `42`) | Use as PR number |\n| URL (`github.com/.../pull/42`) | Extract PR number |\n| Branch name | Find PR via `gh pr list --head <branch>` |\n\n```bash\ngh pr view <NUMBER> --json number,title,body,author,baseRefName,headRefName,changedFiles,additions,deletions\ngh pr diff <NUMBER>\n```\n\nIf PR not found, stop with error. Store PR metadata for later phases.\n\n### Phase 2 — CONTEXT\n\nBuild review context:\n\n1. **Project rules** — Read `CLAUDE.md`, `.claude/docs/`, and any contributing guidelines\n2. **PRP artifacts** — Check `.claude/PRPs/reports/` and `.claude/PRPs/plans/` for implementation context related to this PR\n3. **PR intent** — Parse PR description for goals, linked issues, test plans\n4. **Changed files** — List all modified files and categorize by type (source, test, config, docs)\n\n### Phase 3 — REVIEW\n\nRead each changed file **in full** (not just the diff hunks — you need surrounding context).\n\nFor PR reviews, fetch the full file contents at the PR head revision:\n```bash\ngh pr diff <NUMBER> --name-only | while IFS= read -r file; do\n  gh api "repos/{owner}/{repo}/contents/$file?ref=<head-branch>" --jq \'.content\' | base64 -d\ndone\n```\n\nApply the review checklist across 7 categories:\n\n| Category | What to Check |\n|---|---|\n| **Correctness** | Logic errors, off-by-ones, null handling, edge cases, race conditions |\n| **Type Safety** | Type mismatches, unsafe casts, `any` usage, missing generics |\n| **Pattern Compliance** | Matches project conventions (naming, file structure, error handling, imports) |\n| **Security** | Injection, auth gaps, secret exposure, SSRF, path traversal, XSS |\n| **Performance** | N+1 queries, missing indexes, unbounded loops, memory leaks, large payloads |\n| **Completeness** | Missing tests, missing error handling, incomplete migrations, missing docs |\n| **Maintainability** | Dead code, magic numbers, deep nesting, unclear naming, missing types |\n\nAssign severity to each finding:\n\n| Severity | Meaning | Action |\n|---|---|---|\n| **CRITICAL** | Security vulnerability or data loss risk | Must fix before merge |\n| **HIGH** | Bug or logic error likely to cause issues | Should fix before merge |\n| **MEDIUM** | Code quality issue or missing best practice | Fix recommended |\n| **LOW** | Style nit or minor suggestion | Optional |\n\n### Phase 4 — VALIDATE\n\nRun available validation commands:\n\nDetect the project type from config files (`package.json`, `Cargo.toml`, `go.mod`, `pyproject.toml`, etc.), then run the appropriate commands:\n\n**Node.js / TypeScript** (has `package.json`):\n```bash\nnpm run typecheck 2>/dev/null || npx tsc --noEmit 2>/dev/null  # Type check\nnpm run lint                                                    # Lint\nnpm test                                                        # Tests\nnpm run build                                                   # Build\n```\n\n**Rust** (has `Cargo.toml`):\n```bash\ncargo clippy -- -D warnings  # Lint\ncargo test                   # Tests\ncargo build                  # Build\n```\n\n**Go** (has `go.mod`):\n```bash\ngo vet ./...    # Lint\ngo test ./...   # Tests\ngo build ./...  # Build\n```\n\n**Python** (has `pyproject.toml` / `setup.py`):\n```bash\npytest  # Tests\n```\n\nRun only the commands that apply to the detected project type. Record pass/fail for each.\n\n### Phase 5 — DECIDE\n\nForm recommendation based on findings:\n\n| Condition | Decision |\n|---|---|\n| Zero CRITICAL/HIGH issues, validation passes | **APPROVE** |\n| Only MEDIUM/LOW issues, validation passes | **APPROVE** with comments |\n| Any HIGH issues or validation failures | **REQUEST CHANGES** |\n| Any CRITICAL issues | **BLOCK** — must fix before merge |\n\nSpecial cases:\n- Draft PR → Always use **COMMENT** (not approve/block)\n- Only docs/config changes → Lighter review, focus on correctness\n- Explicit `--approve` or `--request-changes` flag → Override decision (but still report all findings)\n\n### Phase 6 — REPORT\n\nCreate review artifact at `.claude/PRPs/reviews/pr-<NUMBER>-review.md`:\n\n```markdown\n# PR Review: #<NUMBER> — <TITLE>\n\n**Reviewed**: <date>\n**Author**: <author>\n**Branch**: <head> → <base>\n**Decision**: APPROVE | REQUEST CHANGES | BLOCK\n\n## Summary\n<1-2 sentence overall assessment>\n\n## Findings\n\n### CRITICAL\n<findings or "None">\n\n### HIGH\n<findings or "None">\n\n### MEDIUM\n<findings or "None">\n\n### LOW\n<findings or "None">\n\n## Validation Results\n\n| Check | Result |\n|---|---|\n| Type check | Pass / Fail / Skipped |\n| Lint | Pass / Fail / Skipped |\n| Tests | Pass / Fail / Skipped |\n| Build | Pass / Fail / Skipped |\n\n## Files Reviewed\n<list of files with change type: Added/Modified/Deleted>\n```\n\n### Phase 7 — PUBLISH\n\nPost the review to GitHub:\n\n```bash\n# If APPROVE\ngh pr review <NUMBER> --approve --body "<summary of review>"\n\n# If REQUEST CHANGES\ngh pr review <NUMBER> --request-changes --body "<summary with required fixes>"\n\n# If COMMENT only (draft PR or informational)\ngh pr review <NUMBER> --comment --body "<summary>"\n```\n\nFor inline comments on specific lines, use the GitHub review comments API:\n```bash\ngh api "repos/{owner}/{repo}/pulls/<NUMBER>/comments" \\\n  -f body="<comment>" \\\n  -f path="<file>" \\\n  -F line=<line-number> \\\n  -f side="RIGHT" \\\n  -f commit_id="$(gh pr view <NUMBER> --json headRefOid --jq .headRefOid)"\n```\n\nAlternatively, post a single review with multiple inline comments at once:\n```bash\ngh api "repos/{owner}/{repo}/pulls/<NUMBER>/reviews" \\\n  -f event="COMMENT" \\\n  -f body="<overall summary>" \\\n  --input comments.json  # [{"path": "file", "line": N, "body": "comment"}, ...]\n```\n\n### Phase 8 — OUTPUT\n\nReport to user:\n\n```\nPR #<NUMBER>: <TITLE>\nDecision: <APPROVE|REQUEST_CHANGES|BLOCK>\n\nIssues: <critical_count> critical, <high_count> high, <medium_count> medium, <low_count> low\nValidation: <pass_count>/<total_count> checks passed\n\nArtifacts:\n  Review: .claude/PRPs/reviews/pr-<NUMBER>-review.md\n  GitHub: <PR URL>\n\nNext steps:\n  - <contextual suggestions based on decision>\n```\n\n---\n\n## Edge Cases\n\n- **No `gh` CLI**: Fall back to local-only review (read the diff, skip GitHub publish). Warn user.\n- **Diverged branches**: Suggest `git fetch origin && git rebase origin/<base>` before review.\n- **Large PRs (>50 files)**: Warn about review scope. Focus on source changes first, then tests, then config/docs.\n'
    ctx.register_command(
        name="code-review",
        handler=_handle_code_review,
        description="ECC /code-review command",
    )


    # Register /review-pr slash command
    def _handle_review_pr(raw_args: str) -> str:
        return "---\ndescription: Comprehensive PR review using specialized agents\n---\n\nRun a comprehensive multi-perspective review of a pull request.\n\n## Usage\n\n`/review-pr [PR-number-or-URL] [--focus=comments|tests|errors|types|code|simplify]`\n\nIf no PR is specified, review the current branch's PR. If no focus is specified, run the full review stack.\n\n## Steps\n\n1. Identify the PR:\n   - use `gh pr view` to get PR details, changed files, and diff\n2. Find project guidance:\n   - look for `CLAUDE.md`, lint config, TypeScript config, repo conventions\n3. Run specialized review agents:\n   - `code-reviewer`\n   - `comment-analyzer`\n   - `pr-test-analyzer`\n   - `silent-failure-hunter`\n   - `type-design-analyzer`\n   - `code-simplifier`\n4. Aggregate results:\n   - dedupe overlapping findings\n   - rank by severity\n5. Report findings grouped by severity\n\n## Confidence Rule\n\nOnly report issues with confidence >= 80:\n\n- Critical: bugs, security, data loss\n- Important: missing tests, quality problems, style violations\n- Advisory: suggestions only when explicitly requested\n"
    ctx.register_command(
        name="review-pr",
        handler=_handle_review_pr,
        description="ECC /review-pr command",
    )


    # Register /quality-gate slash command
    def _handle_quality_gate(raw_args: str) -> str:
        return '---\ndescription: Run the ECC quality pipeline for a file or project scope and report remediation steps.\n---\n\n# Quality Gate Command\n\nRun the ECC quality pipeline on demand for a file or project scope.\n\n## Usage\n\n`/quality-gate [path|.] [--fix] [--strict]`\n\n- default target: current directory (`.`)\n- `--fix`: allow auto-format/fix where configured\n- `--strict`: fail on warnings where supported\n\n## Pipeline\n\n1. Detect language/tooling for target.\n2. Run formatter checks.\n3. Run lint/type checks when available.\n4. Produce a concise remediation list.\n\n## Notes\n\nThis command mirrors hook behavior but is operator-invoked.\n\n## Arguments\n\n$ARGUMENTS:\n- `[path|.]` optional target path\n- `--fix` optional\n- `--strict` optional\n'
    ctx.register_command(
        name="quality-gate",
        handler=_handle_quality_gate,
        description="ECC /quality-gate command",
    )


    # Register /refactor-clean slash command
    def _handle_refactor_clean(raw_args: str) -> str:
        return "---\ndescription: Safely identify and remove dead code with verification after each change.\n---\n\n# Refactor Clean\n\nSafely identify and remove dead code with test verification at every step.\n\n## Step 1: Detect Dead Code\n\nRun analysis tools based on project type:\n\n| Tool | What It Finds | Command |\n|------|--------------|---------|\n| knip | Unused exports, files, dependencies | `npx knip` |\n| depcheck | Unused npm dependencies | `npx depcheck` |\n| ts-prune | Unused TypeScript exports | `npx ts-prune` |\n| vulture | Unused Python code | `vulture src/` |\n| deadcode | Unused Go code | `deadcode ./...` |\n| cargo-udeps | Unused Rust dependencies | `cargo +nightly udeps` |\n\nIf no tool is available, use Grep to find exports with zero imports:\n```\n# Find exports, then check if they're imported anywhere\n```\n\n## Step 2: Categorize Findings\n\nSort findings into safety tiers:\n\n| Tier | Examples | Action |\n|------|----------|--------|\n| **SAFE** | Unused utilities, test helpers, internal functions | Delete with confidence |\n| **CAUTION** | Components, API routes, middleware | Verify no dynamic imports or external consumers |\n| **DANGER** | Config files, entry points, type definitions | Investigate before touching |\n\n## Step 3: Safe Deletion Loop\n\nFor each SAFE item:\n\n1. **Run full test suite** — Establish baseline (all green)\n2. **Delete the dead code** — Use Edit tool for surgical removal\n3. **Re-run test suite** — Verify nothing broke\n4. **If tests fail** — Immediately revert with `git checkout -- <file>` and skip this item\n5. **If tests pass** — Move to next item\n\n## Step 4: Handle CAUTION Items\n\nBefore deleting CAUTION items:\n- Search for dynamic imports: `import()`, `require()`, `__import__`\n- Search for string references: route names, component names in configs\n- Check if exported from a public package API\n- Verify no external consumers (check dependents if published)\n\n## Step 5: Consolidate Duplicates\n\nAfter removing dead code, look for:\n- Near-duplicate functions (>80% similar) — merge into one\n- Redundant type definitions — consolidate\n- Wrapper functions that add no value — inline them\n- Re-exports that serve no purpose — remove indirection\n\n## Step 6: Summary\n\nReport results:\n\n```\nDead Code Cleanup\n──────────────────────────────\nDeleted:   12 unused functions\n           3 unused files\n           5 unused dependencies\nSkipped:   2 items (tests failed)\nSaved:     ~450 lines removed\n──────────────────────────────\nAll tests passing PASS:\n```\n\n## Rules\n\n- **Never delete without running tests first**\n- **One deletion at a time** — Atomic changes make rollback easy\n- **Skip if uncertain** — Better to keep dead code than break production\n- **Don't refactor while cleaning** — Separate concerns (clean first, refactor later)\n"
    ctx.register_command(
        name="refactor-clean",
        handler=_handle_refactor_clean,
        description="ECC /refactor-clean command",
    )


    # Register /test-coverage slash command
    def _handle_test_coverage(raw_args: str) -> str:
        return '---\ndescription: Analyze coverage, identify gaps, and generate missing tests toward the target threshold.\n---\n\n# Test Coverage\n\nAnalyze test coverage, identify gaps, and generate missing tests to reach 80%+ coverage.\n\n## Step 1: Detect Test Framework\n\n| Indicator | Coverage Command |\n|-----------|-----------------|\n| `jest.config.*` or `package.json` jest | `npx jest --coverage --coverageReporters=json-summary` |\n| `vitest.config.*` | `npx vitest run --coverage` |\n| `pytest.ini` / `pyproject.toml` pytest | `pytest --cov=src --cov-report=json` |\n| `Cargo.toml` | `cargo llvm-cov --json` |\n| `pom.xml` with JaCoCo | `mvn test jacoco:report` |\n| `go.mod` | `go test -coverprofile=coverage.out ./...` |\n\n## Step 2: Analyze Coverage Report\n\n1. Run the coverage command\n2. Parse the output (JSON summary or terminal output)\n3. List files **below 80% coverage**, sorted worst-first\n4. For each under-covered file, identify:\n   - Untested functions or methods\n   - Missing branch coverage (if/else, switch, error paths)\n   - Dead code that inflates the denominator\n\n## Step 3: Generate Missing Tests\n\nFor each under-covered file, generate tests following this priority:\n\n1. **Happy path** — Core functionality with valid inputs\n2. **Error handling** — Invalid inputs, missing data, network failures\n3. **Edge cases** — Empty arrays, null/undefined, boundary values (0, -1, MAX_INT)\n4. **Branch coverage** — Each if/else, switch case, ternary\n\n### Test Generation Rules\n\n- Place tests adjacent to source: `foo.ts` → `foo.test.ts` (or project convention)\n- Use existing test patterns from the project (import style, assertion library, mocking approach)\n- Mock external dependencies (database, APIs, file system)\n- Each test should be independent — no shared mutable state between tests\n- Name tests descriptively: `test_create_user_with_duplicate_email_returns_409`\n\n## Step 4: Verify\n\n1. Run the full test suite — all tests must pass\n2. Re-run coverage — verify improvement\n3. If still below 80%, repeat Step 3 for remaining gaps\n\n## Step 5: Report\n\nShow before/after comparison:\n\n```\nCoverage Report\n──────────────────────────────\nFile                   Before  After\nsrc/services/auth.ts   45%     88%\nsrc/utils/validation.ts 32%    82%\n──────────────────────────────\nOverall:               67%     84%  PASS:\n```\n\n## Focus Areas\n\n- Functions with complex branching (high cyclomatic complexity)\n- Error handlers and catch blocks\n- Utility functions used across the codebase\n- API endpoint handlers (request → response flow)\n- Edge cases: null, undefined, empty string, empty array, zero, negative numbers\n'
    ctx.register_command(
        name="test-coverage",
        handler=_handle_test_coverage,
        description="ECC /test-coverage command",
    )

