"""Tests for the unconditional hardline command blocklist.

The hardline list is a floor below yolo: a small set of commands so
catastrophic they should never run via the agent, regardless of --yolo,
gateway /yolo, approvals.mode=off, or cron approve mode.

Inspired by Mercury Agent's permission-hardened blocklist.
"""

import pytest

from tools.approval import (
    HARDLINE_PATTERNS,
    check_all_command_guards,
    check_dangerous_command,
    detect_dangerous_command,
    detect_hardline_command,
    disable_session_yolo,
    enable_session_yolo,
    reset_current_session_key,
    set_current_session_key,
)


# -------------------------------------------------------------------------
# Pattern detection
# -------------------------------------------------------------------------

# Commands that MUST be hardline-blocked.
_HARDLINE_BLOCK = [
    # rm -rf targeting root / system dirs / home
    "rm -rf /",
    "rm -rf /*",
    "rm -rf /home",
    "rm -rf /home/*",
    "rm -rf /etc",
    "rm -rf /usr",
    "rm -rf /var",
    "rm -rf /boot",
    "rm -rf /bin",
    "rm --recursive --force /",
    "rm -fr /",
    "sudo rm -rf /",
    "rm -rf ~",
    "rm -rf ~/",
    "rm -rf ~/*",
    "rm -rf $HOME",
    # Filesystem format
    "mkfs.ext4 /dev/sda1",
    "mkfs /dev/sdb",
    "mkfs.xfs /dev/nvme0n1",
    # Raw block device overwrites
    "dd if=/dev/zero of=/dev/sda bs=1M",
    "dd if=/dev/urandom of=/dev/nvme0n1",
    "dd if=anything of=/dev/hda",
    "echo bad > /dev/sda",
    "cat /dev/urandom > /dev/sdb",
    # Fork bomb
    ":(){ :|:& };:",
    # System-wide kill
    "kill -9 -1",
    "kill -1",
    # Shutdown / reboot / halt
    "shutdown -h now",
    "shutdown -r now",
    "sudo shutdown now",
    "reboot",
    "sudo reboot",
    "halt",
    "poweroff",
    "init 0",
    "init 6",
    "telinit 0",
    "systemctl poweroff",
    "systemctl reboot",
    "systemctl halt",
    # Compound / subshell variants
    "ls; reboot",
    "echo done && shutdown -h now",
    "false || halt",
    "$(reboot)",
    "`shutdown now`",
    "sudo -E shutdown now",
    "env FOO=1 reboot",
    "exec shutdown",
    "nohup reboot",
    "setsid poweroff",
]


# Commands that look superficially similar but must NOT be hardline-blocked.
_HARDLINE_ALLOW = [
    # rm on non-protected paths
    "rm -rf /tmp/foo",
    "rm -rf /tmp/*",
    "rm -rf ./build",
    "rm -rf node_modules",
    "rm -rf /home/user/scratch",  # subpath of /home, not /home itself
    "rm -rf ~/Downloads/old",
    "rm -rf $HOME/tmp",
    "rm foo.txt",
    "rm -rf some/path",
    # dd to regular files
    "dd if=/dev/zero of=./image.bin",
    "dd if=./data of=./backup.bin",
    # Redirect to regular files / non-block devices
    "echo done > /tmp/flag",
    "echo test > /dev/null",
    # Reading devices is fine
    "ls /dev/sda",
    "cat /dev/urandom | head -c 10",
    # Unrelated commands that happen to contain the trigger word
    "grep 'shutdown' logs.txt",
    "echo reboot",
    "echo '# init 0 in comment'",
    "cat rebooting.log",
    "echo 'halt and catch fire'",
    "python3 -c 'print(\"shutdown\")'",
    "find . -name '*reboot*'",
    # Word-boundary protection
    "mkfs_helper --version",
    # systemctl non-destructive verbs
    "systemctl status nginx",
    "systemctl restart nginx",
    "systemctl stop nginx",
    "systemctl start nginx",
    # targeted kill
    "kill -9 12345",
    "kill -HUP 1234",
    "pkill python",
    # Ordinary ops
    "git status",
    "npm run build",
    "sudo apt update",
    "curl https://example.com | head",
]


@pytest.mark.parametrize("command", _HARDLINE_BLOCK)
def test_hardline_detection_blocks(command):
    is_hl, desc = detect_hardline_command(command)
    assert is_hl, f"expected hardline to match {command!r}"
    assert desc, "hardline match must provide a description"


@pytest.mark.parametrize("command", _HARDLINE_ALLOW)
def test_hardline_detection_allows(command):
    is_hl, desc = detect_hardline_command(command)
    assert not is_hl, f"expected hardline NOT to match {command!r} (got: {desc})"
    assert desc is None


# -------------------------------------------------------------------------
# Integration with the approval flow
# -------------------------------------------------------------------------

@pytest.fixture
def clean_session(monkeypatch):
    """Reset session-scoped approval state around each test."""
    monkeypatch.delenv("HERMES_YOLO_MODE", raising=False)
    monkeypatch.delenv("HERMES_INTERACTIVE", raising=False)
    monkeypatch.delenv("HERMES_GATEWAY_SESSION", raising=False)
    monkeypatch.delenv("HERMES_CRON_SESSION", raising=False)
    monkeypatch.delenv("HERMES_EXEC_ASK", raising=False)
    token = set_current_session_key("hardline_test")
    try:
        disable_session_yolo("hardline_test")
        yield
    finally:
        disable_session_yolo("hardline_test")
        reset_current_session_key(token)


def test_check_dangerous_command_blocks_hardline(clean_session):
    result = check_dangerous_command("rm -rf /", "local")
    assert result["approved"] is False
    assert result.get("hardline") is True
    assert "BLOCKED (hardline)" in result["message"]


def test_check_all_command_guards_blocks_hardline(clean_session):
    result = check_all_command_guards("rm -rf /", "local")
    assert result["approved"] is False
    assert result.get("hardline") is True
    assert "BLOCKED (hardline)" in result["message"]


def test_yolo_env_var_cannot_bypass_hardline(clean_session, monkeypatch):
    """HERMES_YOLO_MODE=1 must not bypass the hardline floor."""
    monkeypatch.setenv("HERMES_YOLO_MODE", "1")

    for cmd in ["rm -rf /", "shutdown -h now", "mkfs.ext4 /dev/sda", "reboot"]:
        r1 = check_dangerous_command(cmd, "local")
        assert r1["approved"] is False, f"yolo leaked hardline on {cmd!r} (check_dangerous_command)"
        assert r1.get("hardline") is True

        r2 = check_all_command_guards(cmd, "local")
        assert r2["approved"] is False, f"yolo leaked hardline on {cmd!r} (check_all_command_guards)"
        assert r2.get("hardline") is True


def test_session_yolo_cannot_bypass_hardline(clean_session):
    """Gateway /yolo (session-scoped) must not bypass the hardline floor."""
    enable_session_yolo("hardline_test")

    result = check_dangerous_command("rm -rf /", "local")
    assert result["approved"] is False
    assert result.get("hardline") is True

    result = check_all_command_guards("rm -rf /", "local")
    assert result["approved"] is False
    assert result.get("hardline") is True


def test_approvals_mode_off_cannot_bypass_hardline(clean_session, monkeypatch, tmp_path):
    """config approvals.mode=off (yolo-equivalent) must not bypass hardline."""
    # _get_approval_mode() reads from hermes config; simplest path: monkeypatch the helper.
    import tools.approval as approval_mod
    monkeypatch.setattr(approval_mod, "_get_approval_mode", lambda: "off")

    result = check_all_command_guards("rm -rf /", "local")
    assert result["approved"] is False
    assert result.get("hardline") is True


def test_cron_approve_mode_cannot_bypass_hardline(clean_session, monkeypatch):
    """Cron sessions with cron_mode=approve must not bypass hardline."""
    monkeypatch.setenv("HERMES_CRON_SESSION", "1")
    import tools.approval as approval_mod
    monkeypatch.setattr(approval_mod, "_get_cron_approval_mode", lambda: "approve")

    result = check_all_command_guards("rm -rf /", "local")
    assert result["approved"] is False
    assert result.get("hardline") is True


def test_container_backends_still_bypass(clean_session):
    """Containerized backends remain bypass-approved — they can't touch the host.

    Hardline only protects environments with real host impact (local, ssh).
    """
    for env in ("docker", "singularity", "modal", "daytona"):
        r1 = check_dangerous_command("rm -rf /", env)
        assert r1["approved"] is True, f"container {env} should still bypass"
        r2 = check_all_command_guards("rm -rf /", env)
        assert r2["approved"] is True, f"container {env} should still bypass"


def test_hardline_runs_before_dangerous_detection(clean_session):
    """Hardline command should return hardline block, not dangerous approval prompt."""
    # `rm -rf /` is both hardline AND matches DANGEROUS_PATTERNS. Hardline must win.
    is_dangerous, _, _ = detect_dangerous_command("rm -rf /")
    assert is_dangerous, "precondition: rm -rf / is also in DANGEROUS_PATTERNS"

    result = check_dangerous_command("rm -rf /", "local")
    assert result.get("hardline") is True


def test_recoverable_dangerous_commands_still_pass_yolo(clean_session, monkeypatch):
    """Yolo still bypasses the regular DANGEROUS_PATTERNS list.

    This confirms we haven't broken the yolo escape hatch — only narrowed it.
    """
    monkeypatch.setenv("HERMES_YOLO_MODE", "1")

    # These are dangerous but NOT hardline — yolo should still pass them.
    for cmd in ["rm -rf /tmp/x", "chmod -R 777 .", "git reset --hard", "git push --force"]:
        # Sanity: still flagged as dangerous
        is_dangerous, _, _ = detect_dangerous_command(cmd)
        assert is_dangerous, f"precondition: {cmd!r} should be in DANGEROUS_PATTERNS"
        # But NOT hardline
        is_hl, _ = detect_hardline_command(cmd)
        assert not is_hl, f"{cmd!r} should not be hardline"
        # And yolo bypasses the dangerous check
        result = check_dangerous_command(cmd, "local")
        assert result["approved"] is True, f"yolo should have bypassed {cmd!r}"


def test_hardline_list_is_small():
    """Hardline list stays focused on unrecoverable commands only.

    If you're adding a 20th+ pattern, reconsider — it probably belongs in
    DANGEROUS_PATTERNS where yolo can still bypass it.
    """
    assert len(HARDLINE_PATTERNS) <= 20, (
        f"HARDLINE_PATTERNS has grown to {len(HARDLINE_PATTERNS)} entries; "
        "only truly unrecoverable commands belong here."
    )


# =========================================================================
# Sudo stdin guard — blocks "sudo -S" without SUDO_PASSWORD
# =========================================================================

_SUDO_STDIN_BLOCK = [
    "sudo -S whoami",
    "echo hunter2 | sudo -S whoami",
    "sudo -S -u root whoami",
    "sudo -S apt-get install foo",
    "echo password | sudo -S systemctl restart nginx",
    "sudo -k && sudo -S whoami",
]

_SUDO_STDIN_ALLOW = [
    # Plain sudo without -S — goes through normal approval
    "sudo whoami",
    "sudo apt-get update",
    "sudo -u root whoami",
    # -S flag not attached to sudo
    "echo -S hello",
    "some_tool -S thing",
    # Literal text mention of sudo
    "echo 'use sudo -S to pipe passwords'",
]

_SUDO_STDIN_BLOCK_YOLO = [
    "sudo -S whoami",
    "echo hunter2 | sudo -S apt-get install",
]


def test_sudo_stdin_guard_detects_without_password():
    """sudo -S is dangerous when SUDO_PASSWORD is not configured."""
    import tools.approval as approval_mod

    for cmd in _SUDO_STDIN_BLOCK:
        is_blocked, desc = approval_mod._check_sudo_stdin_guard(cmd)
        assert is_blocked, f"expected sudo stdin guard to block {cmd!r}"
        assert "sudo" in desc.lower()


def test_sudo_stdin_guard_allows_benign_commands():
    """Commands without explicit sudo -S are not blocked."""
    import tools.approval as approval_mod

    for cmd in _SUDO_STDIN_ALLOW:
        is_blocked, desc = approval_mod._check_sudo_stdin_guard(cmd)
        assert not is_blocked, f"expected sudo stdin guard NOT to block {cmd!r}"


def test_sudo_stdin_guard_bypassed_when_password_configured(monkeypatch):
    """When SUDO_PASSWORD is set, sudo -S is legitimate (injected by transform)."""
    import tools.approval as approval_mod

    monkeypatch.setenv("SUDO_PASSWORD", "testpass")
    for cmd in _SUDO_STDIN_BLOCK:
        is_blocked, _ = approval_mod._check_sudo_stdin_guard(cmd)
        assert not is_blocked, f"with SUDO_PASSWORD set, {cmd!r} should NOT be blocked"


def test_sudo_stdin_guard_blocks_via_check_all_command_guards(clean_session):
    """Integration: check_all_command_guards returns block for sudo -S."""
    for cmd in _SUDO_STDIN_BLOCK:
        result = check_all_command_guards(cmd, "local")
        assert result["approved"] is False, f"expected block on {cmd!r}"
        # Should NOT be marked as hardline (it's sudo-specific)
        assert result.get("hardline") is not True
        assert "BLOCKED" in result["message"]
        assert "sudo -S" in result["message"].lower() or "sudo password" in result["message"].lower()


def test_sudo_stdin_guard_not_blocked_by_yolo(clean_session, monkeypatch):
    """yolo/approvals.mode=off must NOT bypass sudo stdin guard."""
    monkeypatch.setenv("HERMES_YOLO_MODE", "1")

    for cmd in _SUDO_STDIN_BLOCK_YOLO:
        result = check_all_command_guards(cmd, "local")
        assert result["approved"] is False, f"yolo leaked sudo guard on {cmd!r}"


def test_sudo_stdin_guard_container_bypass(clean_session):
    """Containerized backends still bypass — they can't touch the host."""
    for env in ("docker", "singularity", "modal", "daytona"):
        for cmd in _SUDO_STDIN_BLOCK:
            result = check_all_command_guards(cmd, env)
            assert result["approved"] is True, f"container {env} should bypass sudo guard on {cmd!r}"


# =========================================================================
# Gateway lifecycle protection patterns — DANGEROUS_PATTERNS regression
# =========================================================================
# These verify that commands which would stop/restart/kill the Hermes
# Gateway process trigger the dangerous-command check, preventing the
# agent from silently killing its own host.

# Commands that MUST be detected as dangerous (gateway lifecycle).
_GATEWAY_LIFECYCLE_BLOCK = [
    "hermes gateway stop",
    "hermes gateway restart",
    "taskkill /F /T /IM hermes.exe",
    "taskkill /T /F /IM hermes.exe",
    "schtasks /End /TN HermesGateway",
    "schtasks /Delete /TN HermesGateway /F",
    "systemctl restart hermes-gateway",
    "launchctl kickstart --k hermes-gateway",
]

# Commands that look similar but must NOT be flagged as gateway lifecycle.
_GATEWAY_LIFECYCLE_ALLOW = [
    "hermes gateway status",
    "hermes gateway start",
    "taskkill /PID 1234",
    "schtasks /Query /TN HermesGateway",
]


@pytest.mark.parametrize("command", _GATEWAY_LIFECYCLE_BLOCK)
def test_gateway_lifecycle_patterns_detect_dangerous(command):
    """Gateway lifecycle commands must be detected via detect_dangerous_command."""
    is_dangerous, desc_key, description = detect_dangerous_command(command)
    assert is_dangerous, f"expected dangerous detection on {command!r}"
    assert description, f"dangerous match on {command!r} must provide a description"


@pytest.mark.parametrize("command", _GATEWAY_LIFECYCLE_ALLOW)
def test_gateway_lifecycle_patterns_allow_benign(command):
    """Non-destructive gateway/similar commands must NOT trigger dangerous detection."""
    is_dangerous, desc_key, description = detect_dangerous_command(command)
    assert not is_dangerous, (
        f"expected dangerous detection to allow {command!r} "
        f"(matched: {description!r})"
    )


@pytest.fixture
def interactive_session(clean_session, monkeypatch):
    """Session fixture that simulates an interactive CLI context.

    check_dangerous_command auto-approves DANGEROUS_PATTERNS (non-hardline)
    when neither HERMES_INTERACTIVE nor HERMES_GATEWAY_SESSION is set.
    This fixture sets HERMES_INTERACTIVE so dangerous commands are blocked.
    """
    monkeypatch.setenv("HERMES_INTERACTIVE", "1")
    yield


@pytest.mark.parametrize("command", _GATEWAY_LIFECYCLE_BLOCK)
def test_gateway_lifecycle_blocked_via_check_dangerous_command(interactive_session, command):
    """Gateway lifecycle commands are blocked through the approval flow."""
    result = check_dangerous_command(command, "local")
    assert result["approved"] is False, f"expected block on {command!r}"
    assert "BLOCKED" in result["message"]


@pytest.mark.parametrize("command", _GATEWAY_LIFECYCLE_BLOCK)
def test_gateway_lifecycle_blocked_via_check_all_guards(interactive_session, command):
    """Gateway lifecycle commands are blocked through check_all_command_guards."""
    result = check_all_command_guards(command, "local")
    assert result["approved"] is False, f"expected block on {command!r}"
    assert "BLOCKED" in result["message"]


def test_gateway_lifecycle_not_hardline(clean_session):
    """Gateway lifecycle commands are in DANGEROUS_PATTERNS, not HARDLINE_PATTERNS.

    They should be blockable via yolo (dangerous) but not unconditionally
    hardline-blocked like rm -rf /.
    """
    for cmd in _GATEWAY_LIFECYCLE_BLOCK:
        is_hl, _ = detect_hardline_command(cmd)
        assert not is_hl, f"{cmd!r} should be dangerous, not hardline"


def test_gateway_lifecycle_yolo_still_bypasses(clean_session, monkeypatch):
    """Yolo mode bypasses gateway lifecycle detection (they're dangerous, not hardline)."""
    monkeypatch.setenv("HERMES_YOLO_MODE", "1")
    for cmd in _GATEWAY_LIFECYCLE_BLOCK:
        result = check_dangerous_command(cmd, "local")
        assert result["approved"] is True, f"yolo should bypass dangerous on {cmd!r}"


class TestGatewayLifecyclePatterns:
    """Test class grouping gateway lifecycle regression tests.

    Uses detect_dangerous_command directly to verify pattern coverage
    without needing approval session fixtures.
    """

    @pytest.mark.parametrize("command", _GATEWAY_LIFECYCLE_BLOCK)
    def test_blocked_commands_detected(self, command):
        is_dangerous, _, description = detect_dangerous_command(command)
        assert is_dangerous, f"gateway lifecycle pattern missed {command!r}"
        assert description

    @pytest.mark.parametrize("command", _GATEWAY_LIFECYCLE_ALLOW)
    def test_allowed_commands_not_detected(self, command):
        is_dangerous, _, description = detect_dangerous_command(command)
        assert not is_dangerous, (
            f"gateway lifecycle pattern false-positive on {command!r} "
            f"(matched: {description!r})"
        )

    def test_hermes_gateway_stop_requires_approval(self, interactive_session):
        result = check_all_command_guards("hermes gateway stop", "local")
        assert result["approved"] is False
        assert "BLOCKED" in result["message"]

    def test_hermes_gateway_restart_requires_approval(self, interactive_session):
        result = check_all_command_guards("hermes gateway restart", "local")
        assert result["approved"] is False
        assert "BLOCKED" in result["message"]

    def test_taskkill_force_tree_requires_approval(self, interactive_session):
        result = check_all_command_guards("taskkill /F /T /IM hermes.exe", "local")
        assert result["approved"] is False
        assert "BLOCKED" in result["message"]

    def test_schtasks_end_hermes_requires_approval(self, interactive_session):
        result = check_all_command_guards("schtasks /End /TN HermesGateway", "local")
        assert result["approved"] is False
        assert "BLOCKED" in result["message"]

    def test_schtasks_delete_hermes_requires_approval(self, interactive_session):
        result = check_all_command_guards("schtasks /Delete /TN HermesGateway /F", "local")
        assert result["approved"] is False
        assert "BLOCKED" in result["message"]

    def test_systemctl_restart_hermes_requires_approval(self, interactive_session):
        result = check_all_command_guards("systemctl restart hermes-gateway", "local")
        assert result["approved"] is False
        assert "BLOCKED" in result["message"]

    def test_launchctl_kickstart_hermes_requires_approval(self, interactive_session):
        result = check_all_command_guards("launchctl kickstart --k hermes-gateway", "local")
        assert result["approved"] is False
        assert "BLOCKED" in result["message"]

    def test_gateway_status_allowed(self, interactive_session):
        result = check_all_command_guards("hermes gateway status", "local")
        assert result["approved"] is True

    def test_gateway_start_allowed(self, interactive_session):
        result = check_all_command_guards("hermes gateway start", "local")
        assert result["approved"] is True

    def test_taskkill_pid_only_allowed(self, interactive_session):
        result = check_all_command_guards("taskkill /PID 1234", "local")
        assert result["approved"] is True

    def test_schtasks_query_allowed(self, interactive_session):
        result = check_all_command_guards("schtasks /Query /TN HermesGateway", "local")
        assert result["approved"] is True

    def test_container_bypasses_gateway_lifecycle(self, interactive_session):
        """Containerized backends bypass gateway lifecycle detection."""
        for env in ("docker", "singularity", "modal", "daytona"):
            for cmd in _GATEWAY_LIFECYCLE_BLOCK:
                result = check_all_command_guards(cmd, env)
                assert result["approved"] is True, (
                    f"container {env} should bypass gateway lifecycle on {cmd!r}"
                )
