"""Tests for image generator detection and invocation ordering.

These tests verify that ``challenge._default_image_generator`` discovers the
new ``gpt-image-2`` skill first and still falls back to legacy paths.
No real image credits are spent — generation is mocked.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest


def test_generate_py_has_no_openai_imports():
    """The generator script must not import openai or require OPENAI_API_KEY."""
    from scripts import challenge

    hermes_home = Path.home() / ".hermes"
    gen_script = (
        hermes_home
        / "skills"
        / "creative"
        / "gpt-image-2"
        / "scripts"
        / "generate.py"
    )
    assert gen_script.exists()
    src = gen_script.read_text(encoding="utf-8")
    assert "import openai" not in src, "generate.py imports openai directly — should use Hermes built-in tool"
    assert "OPENAI_API_KEY" not in src, "generate.py references OPENAI_API_KEY"
    assert "OpenAI(" not in src, "generate.py constructs an OpenAI client directly"


def test_generate_py_bootstraps_hermes_path():
    """The generator script must explicitly resolve and add the Hermes repo path to sys.path."""
    hermes_home = Path.home() / ".hermes"
    gen_script = hermes_home / "skills" / "creative" / "gpt-image-2" / "scripts" / "generate.py"
    assert gen_script.exists()
    src = gen_script.read_text(encoding="utf-8")
    assert "def _ensure_hermes_in_path()" in src, "generate.py missing _ensure_hermes_in_path() helper"
    assert "hermes_home = Path(os.environ.get(\"HERMES_HOME\"" in src, "generate.py does not resolve HERMES_HOME"
    assert "repo_path = hermes_home / \"hermes-agent\"" in src, "generate.py does not resolve hermes-agent repo path"
    assert "repo_path.exists()" in src, "generate.py does not guard on repo existence"
    assert "sys.path.insert(0, str(repo_path))" in src, "generate.py does not prepend repo to sys.path"
    assert "Hermes agent repo not found" in src, "generate.py has no clear missing-repo error"


def test_new_gpt_image_2_skill_detected_first(monkeypatch, tmp_path):
    """When gpt-image-2/scripts/generate.py exists, it is picked first."""
    from scripts import challenge

    home = tmp_path / ".hermes"
    new_skill = home / "skills" / "creative" / "gpt-image-2" / "scripts" / "generate.py"
    new_skill.parent.mkdir(parents=True, exist_ok=True)
    new_skill.write_text("# new", encoding="utf-8")

    legacy = home / "skills" / "creative" / "chatgpt-images-2-operator" / "run.py"
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_text("# old", encoding="utf-8")

    monkeypatch.setenv("HERMES_HOME", str(home))

    # Mock subprocess to avoid running real generators
    call_log = []

    def _fake_run(cmd, **kwargs):
        call_log.append(cmd)
        return subprocess.CompletedProcess(cmd, returncode=0, stdout=b"", stderr=b"")

    monkeypatch.setattr(subprocess, "run", _fake_run)
    # Also need the output file to "exist" after the mocked run
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    expected_out = out_dir / "scene.png"
    expected_out.write_text("fake image", encoding="utf-8")

    result = challenge._default_image_generator("test prompt", out_dir)
    assert result is not None
    assert len(call_log) == 1
    cmd = call_log[0]
    # cmd is like [sys.executable, str(new_skill), "--prompt", ..., "--output", ...]
    assert str(new_skill) in cmd
    assert "--prompt" in cmd
    assert "--output" in cmd


def test_legacy_fallback_used_when_new_missing(monkeypatch, tmp_path):
    """If gpt-image-2 is absent but legacy run.py exists, use the legacy path."""
    from scripts import challenge

    home = tmp_path / ".hermes"
    legacy = home / "skills" / "creative" / "chatgpt-images-2-operator" / "run.py"
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_text("# old", encoding="utf-8")

    monkeypatch.setenv("HERMES_HOME", str(home))

    call_log = []

    def _fake_run(cmd, **kwargs):
        call_log.append(cmd)
        return subprocess.CompletedProcess(cmd, returncode=0, stdout=b"", stderr=b"")

    monkeypatch.setattr(subprocess, "run", _fake_run)

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    expected_out = out_dir / "scene.png"
    expected_out.write_text("fake image", encoding="utf-8")

    result = challenge._default_image_generator("test prompt", out_dir)
    assert result is not None
    assert len(call_log) == 1
    assert str(legacy) in call_log[0]


def test_returns_none_when_no_generator_found(monkeypatch, tmp_path):
    """If neither new nor legacy generator exists, return None gracefully."""
    from scripts import challenge

    home = tmp_path / ".hermes"
    home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HERMES_HOME", str(home))

    out_dir = tmp_path / "out"
    out_dir.mkdir()

    result = challenge._default_image_generator("test prompt", out_dir)
    assert result is None


def test_invokes_with_prompt_and_output_flags(monkeypatch, tmp_path):
    """The subprocess command includes --prompt and --output in that order."""
    from scripts import challenge

    home = tmp_path / ".hermes"
    new_skill = home / "skills" / "creative" / "gpt-image-2" / "scripts" / "generate.py"
    new_skill.parent.mkdir(parents=True, exist_ok=True)
    new_skill.write_text("# new", encoding="utf-8")
    monkeypatch.setenv("HERMES_HOME", str(home))

    call_log = []

    def _fake_run(cmd, **kwargs):
        call_log.append(list(cmd))
        return subprocess.CompletedProcess(cmd, returncode=0, stdout=b"", stderr=b"")

    monkeypatch.setattr(subprocess, "run", _fake_run)

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    expected_out = out_dir / "scene.png"
    expected_out.write_text("fake", encoding="utf-8")

    challenge._default_image_generator("my prompt here", out_dir)

    assert len(call_log) == 1
    cmd = call_log[0]
    # Find indices
    prompt_idx = cmd.index("--prompt")
    output_idx = cmd.index("--output")
    assert cmd[prompt_idx + 1] == "my prompt here"
    assert cmd[output_idx + 1] == str(expected_out)


def test_skips_legacy_generate_py_when_run_py_exists(monkeypatch, tmp_path):
    """For legacy chatgpt-images-2-operator, prefer run.py over scripts/generate.py."""
    from scripts import challenge

    home = tmp_path / ".hermes"
    legacy_run = home / "skills" / "creative" / "chatgpt-images-2-operator" / "run.py"
    legacy_gen = home / "skills" / "creative" / "chatgpt-images-2-operator" / "scripts" / "generate.py"
    legacy_run.parent.mkdir(parents=True, exist_ok=True)
    legacy_gen.parent.mkdir(parents=True, exist_ok=True)
    legacy_run.write_text("# run", encoding="utf-8")
    legacy_gen.write_text("# gen", encoding="utf-8")

    monkeypatch.setenv("HERMES_HOME", str(home))

    call_log = []

    def _fake_run(cmd, **kwargs):
        call_log.append(cmd)
        return subprocess.CompletedProcess(cmd, returncode=0, stdout=b"", stderr=b"")

    monkeypatch.setattr(subprocess, "run", _fake_run)

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    expected_out = out_dir / "scene.png"
    expected_out.write_text("fake", encoding="utf-8")

    result = challenge._default_image_generator("test", out_dir)
    assert result is not None
    assert str(legacy_run) in call_log[0]
    assert str(legacy_gen) not in call_log[0]
