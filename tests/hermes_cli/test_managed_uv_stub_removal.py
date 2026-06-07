"""Tests for issue #39706: hermes update crash with ValueError: too many values to unpack.

The issue occurred when:
1. The original code path tried to call rebuild_venv() which was a stub function
2. The stub function had just `True` as its body (not a return statement)
3. This caused unpacking errors when the function was imported during update

This test verifies that:
- rebuild_venv function does not exist (it was removed in fb853a178)
- The stub that was re-added in 4eca569bf has been removed
- Module imports without errors
"""
import pytest


def test_rebuild_venv_does_not_exist():
    """Verify the stub rebuild_venv function has been removed."""
    from hermes_cli import managed_uv
    
    # rebuild_venv should not exist in the module
    assert not hasattr(managed_uv, "rebuild_venv"), \
        "rebuild_venv stub function should be removed - it was never called and caused confusion"


def test_managed_uv_module_imports_cleanly():
    """Verify managed_uv imports without errors or incomplete functions."""
    from hermes_cli import managed_uv
    
    # All public functions should be callable
    assert callable(managed_uv.managed_uv_path)
    assert callable(managed_uv.resolve_uv)
    assert callable(managed_uv.ensure_uv)
    assert callable(managed_uv.update_managed_uv)


def test_ensure_uv_returns_single_value():
    """Verify ensure_uv returns a single value (not a tuple)."""
    from hermes_cli.managed_uv import ensure_uv
    
    # Should return a string or None, never a tuple
    result = ensure_uv()
    assert result is None or isinstance(result, str), \
        f"ensure_uv should return str or None, got {type(result)}"


def test_uvresult_handles_unpacking():
    """Verify _UvResult class handles unpacking for backward compatibility."""
    from hermes_cli.managed_uv import _UvResult
    import platform
    
    # Only test on non-Windows (see class docstring)
    if platform.system() != "Windows":
        # Should be unpackable as (path, fresh)
        result = _UvResult("/path/to/uv", fresh=True)
        
        # Single value usage
        assert str(result) == "/path/to/uv"
        
        # Tuple unpacking usage (for old code)
        path, fresh = result
        assert path == "/path/to/uv"
        assert fresh is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
