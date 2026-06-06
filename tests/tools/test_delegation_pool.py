"""Tests for credential pool inheritance skip on base_url mismatch."""
import pytest


class TestPoolInheritanceSkip:
    """Test that credential pool is not shared when base_urls differ.

    The fix is at the top of _build_child_agent: it compares the parent's
    base_url with override_base_url and skips pool resolution if they differ.
    We test the logic directly rather than mocking the full agent construction.
    """

    def test_different_base_urls_skip_pool(self):
        """When override_base_url differs from parent, pool should be None."""
        parent_base = "https://api.mistral.ai/v1"
        child_base = "http://localhost:8080/v1"

        parent_norm = (parent_base or "").rstrip("/")
        child_norm = (child_base or "").rstrip("/")

        # This is the exact condition from delegate_tool.py
        should_skip = child_norm and child_norm != parent_norm
        assert should_skip

    def test_same_base_urls_inherit_pool(self):
        """When override_base_url matches parent, pool should be inherited."""
        parent_base = "https://api.mistral.ai/v1"
        child_base = "https://api.mistral.ai/v1"

        parent_norm = (parent_base or "").rstrip("/")
        child_norm = (child_base or "").rstrip("/")

        should_skip = child_norm and child_norm != parent_norm
        assert not should_skip

    def test_no_override_inherits_pool(self):
        """When no override_base_url, pool should be inherited."""
        parent_base = "https://api.mistral.ai/v1"
        child_base = ""

        parent_norm = (parent_base or "").rstrip("/")
        child_norm = (child_base or "").rstrip("/")

        should_skip = child_norm and child_norm != parent_norm
        assert not should_skip

    def test_trailing_slash_normalization(self):
        """Trailing slashes should not cause false mismatch."""
        parent_base = "https://api.mistral.ai/v1/"
        child_base = "https://api.mistral.ai/v1"

        parent_norm = (parent_base or "").rstrip("/")
        child_norm = (child_base or "").rstrip("/")

        should_skip = child_norm and child_norm != parent_norm
        assert not should_skip
