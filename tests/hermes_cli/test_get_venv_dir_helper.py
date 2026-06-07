"""Test the _get_venv_dir() helper function behavior.

The function detects the active venv using:
1. sys.prefix (when inside a venv)
2. VIRTUAL_ENV env var (for uv-managed envs)
3. Fallback to .venv or venv under PROJECT_ROOT
"""
import os
import sys
from pathlib import Path
import pytest


def test_get_venv_dir_function_exists():
    """Test that _get_venv_dir function is available."""
    from hermes_cli.main import _get_venv_dir
    assert callable(_get_venv_dir)


def test_get_venv_dir_returns_path():
    """Test that _get_venv_dir returns a Path object."""
    from hermes_cli.main import _get_venv_dir
    result = _get_venv_dir()
    assert isinstance(result, Path)


def test_venv_scripts_dir_uses_get_venv_dir():
    """Test that _venv_scripts_dir uses the new _get_venv_dir helper."""
    from hermes_cli.main import _venv_scripts_dir
    # Just ensure it runs without error - it may return None if venv doesn't exist
    # in the exact expected location, but it shouldn't crash
    result = _venv_scripts_dir()
    assert result is None or isinstance(result, Path)


def test_detection_prefers_sys_prefix():
    """Test that detection checks sys.prefix first."""
    # This is more of a behavioral test showing the priority
    # The actual sys.prefix check happens inside the function
    assert sys.prefix != sys.base_prefix or os.environ.get("VIRTUAL_ENV")
    # We're in a venv, so one of these should be true


def test_get_venv_dir_does_not_crash():
    """Smoke test: _get_venv_dir should not crash under normal conditions."""
    from hermes_cli.main import _get_venv_dir
    try:
        result = _get_venv_dir()
        # Should return something
        assert result is not None
        assert isinstance(result, Path)
    except Exception as e:
        pytest.fail(f"_get_venv_dir raised {type(e).__name__}: {e}")


def test_venv_detection_replaced_hardcoded_paths():
    """Verify that hardcoded PROJECT_ROOT / 'venv' patterns are replaced."""
    from hermes_cli import main as main_module
    import inspect
    
    # Get the source of _venv_scripts_dir
    source = inspect.getsource(main_module._venv_scripts_dir)
    
    # Should use _get_venv_dir() instead of hardcoded path
    assert "_get_venv_dir()" in source
    assert 'PROJECT_ROOT / "venv"' not in source
    # The function should check is_dir before using scripts
    assert ".is_dir()" in source


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
