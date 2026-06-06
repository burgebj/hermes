"""ECC ecc-testing -- Hermes plugin.

Provides 9 skills:
  - agent-e2e-runner
  - agent-eval
  - agent-performance-optimizer
  - ai-regression-testing
  - benchmark
  - browser-qa
  - cmd-test-coverage
  - e2e-testing
  - eval-harness
"""

from pathlib import Path

_PLUGIN_DIR = Path(__file__).parent
_SKILLS_DIR = _PLUGIN_DIR / "skills"

SKILLS = [
    "agent-e2e-runner",
        "agent-eval",
        "agent-performance-optimizer",
        "ai-regression-testing",
        "benchmark",
        "browser-qa",
        "cmd-test-coverage",
        "e2e-testing",
        "eval-harness",
]


def register(ctx):
    """Register all ecc-testing skills and commands."""
    for skill in SKILLS:
        skill_path = _SKILLS_DIR / f"{skill}.md"
        if skill_path.exists():
            ctx.register_skill(
                name=skill,
                path=skill_path,
                description=f"ECC: {skill}",
            )

        # Register /test-coverage slash command
    def _handle_test_coverage(raw_args: str) -> str:
        return '---\ndescription: Analyze coverage, identify gaps, and generate missing tests toward the target threshold.\n---\n\n# Test Coverage\n\nAnalyze test coverage, identify gaps, and generate missing tests to reach 80%+ coverage.\n\n## Step 1: Detect Test Framework\n\n| Indicator | Coverage Command |\n|-----------|-----------------|\n| `jest.config.*` or `package.json` jest | `npx jest --coverage --coverageReporters=json-summary` |\n| `vitest.config.*` | `npx vitest run --coverage` |\n| `pytest.ini` / `pyproject.toml` pytest | `pytest --cov=src --cov-report=json` |\n| `Cargo.toml` | `cargo llvm-cov --json` |\n| `pom.xml` with JaCoCo | `mvn test jacoco:report` |\n| `go.mod` | `go test -coverprofile=coverage.out ./...` |\n\n## Step 2: Analyze Coverage Report\n\n1. Run the coverage command\n2. Parse the output (JSON summary or terminal output)\n3. List files **below 80% coverage**, sorted worst-first\n4. For each under-covered file, identify:\n   - Untested functions or methods\n   - Missing branch coverage (if/else, switch, error paths)\n   - Dead code that inflates the denominator\n\n## Step 3: Generate Missing Tests\n\nFor each under-covered file, generate tests following this priority:\n\n1. **Happy path** — Core functionality with valid inputs\n2. **Error handling** — Invalid inputs, missing data, network failures\n3. **Edge cases** — Empty arrays, null/undefined, boundary values (0, -1, MAX_INT)\n4. **Branch coverage** — Each if/else, switch case, ternary\n\n### Test Generation Rules\n\n- Place tests adjacent to source: `foo.ts` → `foo.test.ts` (or project convention)\n- Use existing test patterns from the project (import style, assertion library, mocking approach)\n- Mock external dependencies (database, APIs, file system)\n- Each test should be independent — no shared mutable state between tests\n- Name tests descriptively: `test_create_user_with_duplicate_email_returns_409`\n\n## Step 4: Verify\n\n1. Run the full test suite — all tests must pass\n2. Re-run coverage — verify improvement\n3. If still below 80%, repeat Step 3 for remaining gaps\n\n## Step 5: Report\n\nShow before/after comparison:\n\n```\nCoverage Report\n──────────────────────────────\nFile                   Before  After\nsrc/services/auth.ts   45%     88%\nsrc/utils/validation.ts 32%    82%\n──────────────────────────────\nOverall:               67%     84%  PASS:\n```\n\n## Focus Areas\n\n- Functions with complex branching (high cyclomatic complexity)\n- Error handlers and catch blocks\n- Utility functions used across the codebase\n- API endpoint handlers (request → response flow)\n- Edge cases: null, undefined, empty string, empty array, zero, negative numbers\n'
    ctx.register_command(
        name="test-coverage",
        handler=_handle_test_coverage,
        description="ECC /test-coverage command",
    )

