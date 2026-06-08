"""Regression tests for HermesIndexSource official skills fallback.

Issue #30482: skills index returns empty repo fields for all official skills,
causing HermesIndexSource.fetch() to return None. The fix adds a fallback
that constructs the GitHub path from NousResearch/hermes-agent/optional-skills/<path>
when the source is "official" and repo is empty.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from tools.skills_hub import HermesIndexSource


class TestHermesIndexSourceOfficialFallback:
    """Tests for HermesIndexSource.fetch() official skills fallback (#30482)."""

    def test_official_skill_fallback_with_empty_repo(self):
        """When repo is empty but source is 'official' and path is set,
        fetch should try NousResearch/hermes-agent/optional-skills/<path>."""
        source = HermesIndexSource(auth=MagicMock())

        # Mock the index to return an official skill with empty repo
        mock_index = {
            "skills": [
                {
                    "identifier": "official/finance/3-statement-model",
                    "source": "official",
                    "repo": "",
                    "path": "finance/3-statement-model",
                    "name": "3-statement-model",
                    "resolved_github_id": "",
                }
            ]
        }

        # Mock the GitHub source to avoid real API calls
        mock_github = MagicMock()
        mock_bundle = MagicMock()
        mock_bundle.source = None
        mock_bundle.identifier = None
        mock_github.fetch.return_value = mock_bundle

        with patch.object(HermesIndexSource, "_ensure_loaded", return_value=mock_index):
            with patch.object(HermesIndexSource, "_get_github", return_value=mock_github):
                result = source.fetch("official/finance/3-statement-model")

        # Verify the fallback path was tried
        mock_github.fetch.assert_any_call(
            "NousResearch/hermes-agent/optional-skills/finance/3-statement-model"
        )
        assert result is mock_bundle

    def test_official_skill_fallback_not_used_when_repo_present(self):
        """When repo is non-empty, the fallback should NOT be tried.
        The normal repo/path path should be used."""
        source = HermesIndexSource(auth=MagicMock())

        mock_index = {
            "skills": [
                {
                    "identifier": "official/some-skill",
                    "source": "official",
                    "repo": "someone/some-repo",
                    "path": "skills/some-skill",
                    "name": "some-skill",
                    "resolved_github_id": "",
                }
            ]
        }

        mock_github = MagicMock()
        mock_bundle = MagicMock()
        mock_github.fetch.return_value = mock_bundle

        with patch.object(HermesIndexSource, "_ensure_loaded", return_value=mock_index):
            with patch.object(HermesIndexSource, "_get_github", return_value=mock_github):
                result = source.fetch("official/some-skill")

        # Verify the normal repo/path was used, not the fallback
        mock_github.fetch.assert_any_call("someone/some-repo/skills/some-skill")
        # Should NOT have been called with the fallback path
        for call in mock_github.fetch.call_args_list:
            assert "NousResearch/hermes-agent/optional-skills" not in str(call)
        assert result is mock_bundle

    def test_official_skill_fallback_not_used_when_resolved_github_id_present(self):
        """When resolved_github_id is present (even with empty repo),
        it should be used directly without falling back to the official fallback."""
        source = HermesIndexSource(auth=MagicMock())

        mock_index = {
            "skills": [
                {
                    "identifier": "official/some-skill",
                    "source": "official",
                    "repo": "",
                    "path": "skills/some-skill",
                    "name": "some-skill",
                    "resolved_github_id": "someone/some-repo/skills/some-skill",
                }
            ]
        }

        mock_github = MagicMock()
        mock_bundle = MagicMock()
        mock_github.fetch.return_value = mock_bundle

        with patch.object(HermesIndexSource, "_ensure_loaded", return_value=mock_index):
            with patch.object(HermesIndexSource, "_get_github", return_value=mock_github):
                result = source.fetch("official/some-skill")

        # Verify resolved_github_id was used
        mock_github.fetch.assert_any_call("someone/some-repo/skills/some-skill")
        assert result is mock_bundle

    def test_official_skill_fallback_not_used_for_community_source(self):
        """When source is 'community' (not 'official'), the fallback should NOT be used."""
        source = HermesIndexSource(auth=MagicMock())

        mock_index = {
            "skills": [
                {
                    "identifier": "community/some-skill",
                    "source": "community",
                    "repo": "",
                    "path": "skills/some-skill",
                    "name": "some-skill",
                    "resolved_github_id": "",
                }
            ]
        }

        mock_github = MagicMock()

        with patch.object(HermesIndexSource, "_ensure_loaded", return_value=mock_index):
            with patch.object(HermesIndexSource, "_get_github", return_value=mock_github):
                result = source.fetch("community/some-skill")

        # Should NOT have tried the official fallback
        for call in mock_github.fetch.call_args_list:
            assert "NousResearch/hermes-agent/optional-skills" not in str(call)
        # And fetch should NOT have been called at all (no valid source)
        assert result is None

    def test_official_skill_fallback_not_used_when_no_path(self):
        """When both repo and path are empty, fetch should return None."""
        source = HermesIndexSource(auth=MagicMock())

        mock_index = {
            "skills": [
                {
                    "identifier": "official/broken-skill",
                    "source": "official",
                    "repo": "",
                    "path": "",
                    "name": "broken-skill",
                    "resolved_github_id": "",
                }
            ]
        }

        mock_github = MagicMock()

        with patch.object(HermesIndexSource, "_ensure_loaded", return_value=mock_index):
            with patch.object(HermesIndexSource, "_get_github", return_value=mock_github):
                result = source.fetch("official/broken-skill")

        mock_github.fetch.assert_not_called()
        assert result is None

    def test_source_field_preserved_on_fallback(self):
        """When fallback is used, the bundle.source should be set to the entry's source."""
        source = HermesIndexSource(auth=MagicMock())

        mock_index = {
            "skills": [
                {
                    "identifier": "official/org/skill-name",
                    "source": "official",
                    "repo": "",
                    "path": "org/skill-name",
                    "name": "skill-name",
                    "resolved_github_id": "",
                }
            ]
        }

        mock_github = MagicMock()
        mock_bundle = MagicMock()
        mock_bundle.source = None
        mock_bundle.identifier = None
        mock_github.fetch.return_value = mock_bundle

        with patch.object(HermesIndexSource, "_ensure_loaded", return_value=mock_index):
            with patch.object(HermesIndexSource, "_get_github", return_value=mock_github):
                source.fetch("official/org/skill-name")

        # After fetch, bundle.source should be "official"
        assert mock_bundle.source == "official"
        assert mock_bundle.identifier == "official/org/skill-name"
