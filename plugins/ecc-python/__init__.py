"""ECC ecc-python -- Hermes plugin.

Provides 11 skills:
  - agent-python-reviewer
  - agent-pytorch-build-resolver
  - cmd-python-review
  - django-patterns
  - django-security
  - django-tdd
  - django-verification
  - python-patterns
  - python-testing
  - pytorch-patterns
  - rules-python
"""

from pathlib import Path

_PLUGIN_DIR = Path(__file__).parent
_SKILLS_DIR = _PLUGIN_DIR / "skills"

SKILLS = [
    "agent-python-reviewer",
        "agent-pytorch-build-resolver",
        "cmd-python-review",
        "django-patterns",
        "django-security",
        "django-tdd",
        "django-verification",
        "python-patterns",
        "python-testing",
        "pytorch-patterns",
        "rules-python",
]


def register(ctx):
    """Register all ecc-python skills and commands."""
    for skill in SKILLS:
        skill_path = _SKILLS_DIR / f"{skill}.md"
        if skill_path.exists():
            ctx.register_skill(
                name=skill,
                path=skill_path,
                description=f"ECC: {skill}",
            )

        # Register /python-review slash command
    def _handle_python_review(raw_args: str) -> str:
        return '---\ndescription: Comprehensive Python code review for PEP 8 compliance, type hints, security, and Pythonic idioms. Invokes the python-reviewer agent.\n---\n\n# Python Code Review\n\nThis command invokes the **python-reviewer** agent for comprehensive Python-specific code review.\n\n## What This Command Does\n\n1. **Identify Python Changes**: Find modified `.py` files via `git diff`\n2. **Run Static Analysis**: Execute `ruff`, `mypy`, `pylint`, `black --check`\n3. **Security Scan**: Check for SQL injection, command injection, unsafe deserialization\n4. **Type Safety Review**: Analyze type hints and mypy errors\n5. **Pythonic Code Check**: Verify code follows PEP 8 and Python best practices\n6. **Generate Report**: Categorize issues by severity\n\n## When to Use\n\nUse `/python-review` when:\n- After writing or modifying Python code\n- Before committing Python changes\n- Reviewing pull requests with Python code\n- Onboarding to a new Python codebase\n- Learning Pythonic patterns and idioms\n\n## Review Categories\n\n### CRITICAL (Must Fix)\n- SQL/Command injection vulnerabilities\n- Unsafe eval/exec usage\n- Pickle unsafe deserialization\n- Hardcoded credentials\n- YAML unsafe load\n- Bare except clauses hiding errors\n\n### HIGH (Should Fix)\n- Missing type hints on public functions\n- Mutable default arguments\n- Swallowing exceptions silently\n- Not using context managers for resources\n- C-style looping instead of comprehensions\n- Using type() instead of isinstance()\n- Race conditions without locks\n\n### MEDIUM (Consider)\n- PEP 8 formatting violations\n- Missing docstrings on public functions\n- Print statements instead of logging\n- Inefficient string operations\n- Magic numbers without named constants\n- Not using f-strings for formatting\n- Unnecessary list creation\n\n## Automated Checks Run\n\n```bash\n# Type checking\nmypy .\n\n# Linting and formatting\nruff check .\nblack --check .\nisort --check-only .\n\n# Security scanning\nbandit -r .\n\n# Dependency audit\npip-audit\nsafety check\n\n# Testing\npytest --cov=app --cov-report=term-missing\n```\n\n## Example Usage\n\n```text\nUser: /python-review\n\nAgent:\n# Python Code Review Report\n\n## Files Reviewed\n- app/routes/user.py (modified)\n- app/services/auth.py (modified)\n\n## Static Analysis Results\n✓ ruff: No issues\n✓ mypy: No errors\nWARNING: black: 2 files need reformatting\n✓ bandit: No security issues\n\n## Issues Found\n\n[CRITICAL] SQL Injection vulnerability\nFile: app/routes/user.py:42\nIssue: User input directly interpolated into SQL query\n```python\nquery = f"SELECT * FROM users WHERE id = {user_id}"  # Bad\n```\nFix: Use parameterized query\n```python\nquery = "SELECT * FROM users WHERE id = %s"  # Good\ncursor.execute(query, (user_id,))\n```\n\n[HIGH] Mutable default argument\nFile: app/services/auth.py:18\nIssue: Mutable default argument causes shared state\n```python\ndef process_items(items=[]):  # Bad\n    items.append("new")\n    return items\n```\nFix: Use None as default\n```python\ndef process_items(items=None):  # Good\n    if items is None:\n        items = []\n    items.append("new")\n    return items\n```\n\n[MEDIUM] Missing type hints\nFile: app/services/auth.py:25\nIssue: Public function without type annotations\n```python\ndef get_user(user_id):  # Bad\n    return db.find(user_id)\n```\nFix: Add type hints\n```python\ndef get_user(user_id: str) -> Optional[User]:  # Good\n    return db.find(user_id)\n```\n\n[MEDIUM] Not using context manager\nFile: app/routes/user.py:55\nIssue: File not closed on exception\n```python\nf = open("config.json")  # Bad\ndata = f.read()\nf.close()\n```\nFix: Use context manager\n```python\nwith open("config.json") as f:  # Good\n    data = f.read()\n```\n\n## Summary\n- CRITICAL: 1\n- HIGH: 1\n- MEDIUM: 2\n\nRecommendation: FAIL: Block merge until CRITICAL issue is fixed\n\n## Formatting Required\nRun: `black app/routes/user.py app/services/auth.py`\n```\n\n## Approval Criteria\n\n| Status | Condition |\n|--------|-----------|\n| PASS: Approve | No CRITICAL or HIGH issues |\n| WARNING: Warning | Only MEDIUM issues (merge with caution) |\n| FAIL: Block | CRITICAL or HIGH issues found |\n\n## Integration with Other Commands\n\n- Use the `tdd-workflow` skill first to ensure tests pass\n- Use `/code-review` for non-Python specific concerns\n- Use `/python-review` before committing\n- Use `/build-fix` if static analysis tools fail\n\n## Framework-Specific Reviews\n\n### Django Projects\nThe reviewer checks for:\n- N+1 query issues (use `select_related` and `prefetch_related`)\n- Missing migrations for model changes\n- Raw SQL usage when ORM could work\n- Missing `transaction.atomic()` for multi-step operations\n\n### FastAPI Projects\nThe reviewer checks for:\n- CORS misconfiguration\n- Pydantic models for request validation\n- Response models correctness\n- Proper async/await usage\n- Dependency injection patterns\n\n### Flask Projects\nThe reviewer checks for:\n- Context management (app context, request context)\n- Proper error handling\n- Blueprint organization\n- Configuration management\n\n## Related\n\n- Agent: `agents/python-reviewer.md`\n- Skills: `skills/python-patterns/`, `skills/python-testing/`\n\n## Common Fixes\n\n### Add Type Hints\n```python\n# Before\ndef calculate(x, y):\n    return x + y\n\n# After\nfrom typing import Union\n\ndef calculate(x: Union[int, float], y: Union[int, float]) -> Union[int, float]:\n    return x + y\n```\n\n### Use Context Managers\n```python\n# Before\nf = open("file.txt")\ndata = f.read()\nf.close()\n\n# After\nwith open("file.txt") as f:\n    data = f.read()\n```\n\n### Use List Comprehensions\n```python\n# Before\nresult = []\nfor item in items:\n    if item.active:\n        result.append(item.name)\n\n# After\nresult = [item.name for item in items if item.active]\n```\n\n### Fix Mutable Defaults\n```python\n# Before\ndef append(value, items=[]):\n    items.append(value)\n    return items\n\n# After\ndef append(value, items=None):\n    if items is None:\n        items = []\n    items.append(value)\n    return items\n```\n\n### Use f-strings (Python 3.6+)\n```python\n# Before\nname = "Alice"\ngreeting = "Hello, " + name + "!"\ngreeting2 = "Hello, {}".format(name)\n\n# After\ngreeting = f"Hello, {name}!"\n```\n\n### Fix String Concatenation in Loops\n```python\n# Before\nresult = ""\nfor item in items:\n    result += str(item)\n\n# After\nresult = "".join(str(item) for item in items)\n```\n\n## Python Version Compatibility\n\nThe reviewer notes when code uses features from newer Python versions:\n\n| Feature | Minimum Python |\n|---------|----------------|\n| Type hints | 3.5+ |\n| f-strings | 3.6+ |\n| Walrus operator (`:=`) | 3.8+ |\n| Position-only parameters | 3.8+ |\n| Match statements | 3.10+ |\n| Type unions (&#96;x &#124; None&#96;) | 3.10+ |\n\nEnsure your project\'s `pyproject.toml` or `setup.py` specifies the correct minimum Python version.\n'
    ctx.register_command(
        name="python-review",
        handler=_handle_python_review,
        description="ECC /python-review command",
    )

