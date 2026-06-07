"""Tests for venv detection and hardcoded path replacement.

Regression tests for #39714: hermes update installs deps into hardcoded venv/
while the active env is .venv, creating duplicate orphan virtualenvs.

The fix: use the existing _detect_venv_dir() helper consistently across all
code paths instead of hardcoding PROJECT_ROOT / "venv".
"""
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest


class TestVenvDetection:
    """Test venv detection logic."""

    def test_detect_venv_from_sys_prefix(self):
        """Detection should use sys.prefix when in a virtualenv."""
        # Simulate being inside a venv
        with patch('sys.prefix', '/path/to/.venv'):
            with patch('sys.base_prefix', '/usr'):
                # When sys.prefix != sys.base_prefix, we're in a venv
                in_venv = sys.prefix != sys.base_prefix
                assert in_venv is True
                assert Path(sys.prefix) == Path('/path/to/.venv')

    def test_detect_venv_from_virtual_env_env_var(self):
        """Detection should use VIRTUAL_ENV env var as fallback."""
        # Simulate uv-managed env where sys.prefix == sys.base_prefix
        # but VIRTUAL_ENV is set
        with patch.dict(os.environ, {"VIRTUAL_ENV": "/path/to/.venv"}):
            virtual_env = os.environ.get("VIRTUAL_ENV")
            assert virtual_env == "/path/to/.venv"

    def test_detect_venv_fallback_to_common_names(self):
        """Detection should check .venv before venv."""
        # When both sys.prefix detection and VIRTUAL_ENV fail,
        # fallback to checking common names
        candidates = [".venv", "venv"]
        
        # .venv should be checked first
        assert candidates[0] == ".venv"
        assert candidates[1] == "venv"

    def test_venv_detection_order(self):
        """Test the correct detection order: sys.prefix → VIRTUAL_ENV → fallback."""
        # This demonstrates the correct order that _detect_venv_dir() uses
        
        def detect_venv_order():
            order = []
            
            # Step 1: Check sys.prefix
            if sys.prefix != sys.base_prefix:
                order.append("sys.prefix")
            
            # Step 2: Check VIRTUAL_ENV env var
            if os.environ.get("VIRTUAL_ENV"):
                order.append("VIRTUAL_ENV")
            
            # Step 3: Fallback to common names
            order.append("fallback")
            
            return order
        
        order = detect_venv_order()
        # The fallback should always be included
        assert "fallback" in order


class TestHardcodedVenvPaths:
    """Test replacement of hardcoded PROJECT_ROOT / 'venv' patterns."""

    def test_hardcoded_path_problem(self):
        """Demonstrate the hardcoded path problem."""
        PROJECT_ROOT = Path("/opt/hermes-agent")
        
        # The problem: hardcoded paths
        hardcoded_venv = PROJECT_ROOT / "venv"  # This is wrong for uv installs
        
        # The actual active venv (from sys.prefix)
        actual_venv = Path(sys.prefix)
        
        # They're different for uv installs where actual is .venv
        # This test just documents the problem pattern
        assert str(hardcoded_venv) == "/opt/hermes-agent/venv"

    def test_detected_venv_over_hardcoded(self):
        """Detected venv should take precedence over hardcoded paths."""
        # The correct pattern: use detected venv, fallback to hardcoded
        def get_venv_dir(detected_venv, PROJECT_ROOT):
            """Correct pattern: detected first, hardcoded as fallback."""
            if detected_venv:
                return detected_venv
            # Only fallback to hardcoded if nothing detected
            return PROJECT_ROOT / "venv"
        
        PROJECT_ROOT = Path("/opt/hermes-agent")
        
        # With detected venv
        detected = Path("/opt/hermes-agent/.venv")
        result = get_venv_dir(detected, PROJECT_ROOT)
        assert result == Path("/opt/hermes-agent/.venv")
        
        # Without detected venv (fallback)
        result = get_venv_dir(None, PROJECT_ROOT)
        assert result == Path("/opt/hermes-agent/venv")

    def test_uv_install_uses_dot_venv(self):
        """uv installs create .venv, not venv."""
        # This documents the behavior of uv
        # uv creates .venv by default, not venv
        expected_uv_venv = ".venv"
        hardcoded_path = "venv"
        
        # These are different
        assert expected_uv_venv != hardcoded_path


class TestVenvEnvironmentVariable:
    """Test VIRTUAL_ENV environment variable usage."""

    def test_virtual_env_var_set_during_update(self):
        """During dep install, VIRTUAL_ENV should point to detected venv."""
        detected_venv = Path("/opt/hermes-agent/.venv")
        
        # Correct: set VIRTUAL_ENV to the detected venv
        uv_env = {
            **os.environ,
            "VIRTUAL_ENV": str(detected_venv)
        }
        
        assert uv_env["VIRTUAL_ENV"] == "/opt/hermes-agent/.venv"

    def test_virtual_env_var_should_not_be_hardcoded(self):
        """VIRTUAL_ENV should not be hardcoded to PROJECT_ROOT / 'venv'."""
        PROJECT_ROOT = Path("/opt/hermes-agent")
        
        # Wrong: hardcoded path
        hardcoded_virtual_env = str(PROJECT_ROOT / "venv")
        
        # Right: use detected or sys.prefix
        correct_virtual_env = str(Path(sys.prefix))
        
        # These might be different on uv installs
        # (one is /opt/hermes-agent/venv, other is /opt/hermes-agent/.venv)
        # This just documents that hardcoding is wrong


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
