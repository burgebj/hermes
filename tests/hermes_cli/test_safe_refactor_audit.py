from hermes_cli.safe_refactor_audit import audit_tdb3_diff


def test_audit_rejects_uninstall_tty_guard_changes():
    diff = """
--- a/hermes_cli/main.py
+++ b/hermes_cli/main.py
@@
-    _require_tty(\"uninstall\")
+    if not sys.stdin.isatty():
+        return run_uninstall(args)
"""
    result = audit_tdb3_diff(diff)

    assert result.verdict == "REJECT_HARD"
    assert any(f.rule_id == "TTY_DOWNGRADE" for f in result.findings)


def test_audit_warns_on_non_whitelisted_and_shell_path_touches():
    diff = """
--- a/hermes_cli/profiles.py
+++ b/hermes_cli/profiles.py
@@
+export PATH=\"$HOME/.local/bin:$PATH\"
"""
    result = audit_tdb3_diff(diff)

    assert result.verdict == "WARN"
    assert any(f.rule_id == "FILE_SCOPE" for f in result.findings)
    assert any(f.rule_id == "SHELL_PATH_TOUCH" for f in result.findings)


def test_audit_warns_on_high_risk_io_and_contract_only_changes():
    diff = """
--- a/hermes_cli/main.py
+++ b/hermes_cli/main.py
@@
-    hermes uninstall           Uninstall Hermes Agent
+    hermes uninstall           Remove Hermes Agent from this machine
--- a/hermes_cli/uninstall.py
+++ b/hermes_cli/uninstall.py
@@
+    shutil.rmtree(project_root)
"""
    result = audit_tdb3_diff(diff)

    assert result.verdict == "WARN"
    assert any(f.rule_id == "HIGH_RISK_IO" for f in result.findings)
    assert any(f.rule_id == "CONTRACT_CONSISTENCY" for f in result.findings)


def test_audit_rejects_indirect_tty_policy_relaxation_via_defaults():
    diff = """
--- a/hermes_cli/uninstall.py
+++ b/hermes_cli/uninstall.py
@@
-DEFAULT_CONFIRM_REQUIRED = True
+DEFAULT_CONFIRM_REQUIRED = False
"""
    result = audit_tdb3_diff(diff)

    assert result.verdict == "REJECT_HARD"
    assert any(f.rule_id == "TTY_POLICY_INDIRECT_RELAXATION" for f in result.findings)


def test_audit_rejects_argument_alias_semantic_drift():
    diff = """
--- a/hermes_cli/main.py
+++ b/hermes_cli/main.py
@@
-    parser.add_argument("--yes", action="store_true", help="Confirm uninstall")
+    parser.add_argument("--approve", "--yes", action="store_true", help="Confirm uninstall")
"""
    result = audit_tdb3_diff(diff)

    assert result.verdict == "REJECT_HARD"
    assert any(f.rule_id == "ARG_ALIAS_SEMANTIC_DRIFT" for f in result.findings)


def test_audit_approves_minimal_test_only_change():
    diff = """
--- a/tests/hermes_cli/test_safe_refactor_audit.py
+++ b/tests/hermes_cli/test_safe_refactor_audit.py
@@
+def test_placeholder():
+    assert True
"""
    result = audit_tdb3_diff(diff)

    assert result.verdict == "APPROVE"
    assert result.changed_paths == ("tests/hermes_cli/test_safe_refactor_audit.py",)
    assert result.findings == ()
