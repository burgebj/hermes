from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_windows_sandbox_launcher_maps_repo_readonly_and_results_writable():
    source = (ROOT / "scripts" / "windows-sandbox-validate.ps1").read_text(encoding="utf-8")

    assert "<ReadOnly>true</ReadOnly>" in source
    assert "<ReadOnly>false</ReadOnly>" in source
    assert "windows-sandbox-smoke.ps1" in source
    assert "WindowsSandbox.exe" in source


def test_windows_sandbox_smoke_uses_skip_setup_and_skip_gateway():
    source = (ROOT / "scripts" / "windows-sandbox-smoke.ps1").read_text(encoding="utf-8")

    assert "-SkipSetup" in source
    assert "-SkipGateway" in source
    assert "hermes gateway status" in source
    assert "HERMES_GIT_BASH_PATH" in source
    assert "Start-Transcript" in source
    assert "Save-Summary" in source
    assert "InstallerTimeoutMinutes" in source
    assert "last_heartbeat" in source


def test_windows_sandbox_smoke_does_not_delete_host_checkout():
    source = (ROOT / "scripts" / "windows-sandbox-smoke.ps1").read_text(encoding="utf-8")

    assert "Remove-Item $RepoRoot" not in source
    assert "robocopy $RepoRoot $installRoot" in source
