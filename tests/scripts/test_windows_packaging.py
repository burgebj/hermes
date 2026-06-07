import hashlib
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = ROOT / "packaging" / "windows" / "build-windows-package.ps1"


def test_windows_packaging_templates_have_no_placeholders():
    templates = sorted((ROOT / "packaging" / "windows" / "winget").glob("*.yaml.in"))
    assert templates
    for template in templates:
        text = template.read_text(encoding="utf-8")
        assert "{{VERSION}}" in text
        if template.name.endswith(".installer.yaml.in"):
            assert "{{INSTALLER_URL}}" in text
            assert "{{INSTALLER_SHA256}}" in text


def test_windows_packaging_script_inputs_exist():
    script = BUILD_SCRIPT.read_text(encoding="utf-8")
    required = re.search(r"\$requiredFiles\s*=\s*@\((.*?)\)", script, re.S)
    assert required, "build script should declare required package inputs"
    paths = re.findall(r'"([^"]+)"', required.group(1))
    assert paths
    for relative in paths:
        assert (ROOT / relative).exists(), f"missing packaging input: {relative}"


@pytest.mark.skipif(sys.platform != "win32", reason="PowerShell packaging smoke is Windows-only")
def test_build_windows_package_smoke(tmp_path):
    output_dir = tmp_path / "windows-dist"
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(BUILD_SCRIPT),
            "-Version",
            "9.8.7",
            "-ReleaseTag",
            "v9.8.7-test",
            "-OutputDir",
            str(output_dir),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr + result.stdout

    zip_path = output_dir / "hermes-agent-windows-9.8.7.zip"
    sha_path = output_dir / "hermes-agent-windows-9.8.7.zip.sha256"
    assert zip_path.exists()
    assert sha_path.exists()
    assert hashlib.sha256(zip_path.read_bytes()).hexdigest() in sha_path.read_text(encoding="ascii")

    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
    assert "scripts/install.ps1" in names
    assert "scripts/install.cmd" in names
    assert "WINDOWS-PACKAGE.md" in names

    winget_dir = output_dir / "winget"
    rendered = sorted(winget_dir.glob("*.yaml"))
    assert len(rendered) == 3
    for manifest in rendered:
        text = manifest.read_text(encoding="utf-8")
        assert "{{" not in text
        assert "9.8.7" in text
        yaml.safe_load(text)

    installer = (winget_dir / "NousResearch.HermesAgent.installer.yaml").read_text(encoding="utf-8")
    assert "https://github.com/NousResearch/hermes-agent/releases/download/v9.8.7-test/hermes-agent-windows-9.8.7.zip" in installer
