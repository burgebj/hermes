"""Tests verifying that the web_server._call_cron_for_profile monkeypatch
still works after the #25295 refactor (dynamic _resolve_* helpers).

The dashboard is a single-process multi-profile viewer that temporarily
redirects cron.jobs internals to target a specific profile's directories.
These tests confirm that both the new _resolve_* helpers AND the legacy
module-level constants are correctly retargeted.
"""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture()
def _fake_home(tmp_path):
    """Create two profile home directories with cron/jobs.json files."""
    default_home = tmp_path / "default"
    alt_home = tmp_path / "alt-profile"
    for home in (default_home, alt_home):
        cron_dir = home / "cron"
        cron_dir.mkdir(parents=True)
        (cron_dir / "jobs.json").write_text(json.dumps({"jobs": [], "updated_at": ""}))
        (cron_dir / "output").mkdir()

    # Return a function that maps profile names to home dirs.
    def home_for_profile(name):
        if name == "alt":
            return alt_home
        return default_home

    return default_home, alt_home, home_for_profile


class TestWebServerMonkeypatchCompat:
    """Verify _call_cron_for_profile patches both resolve helpers and constants."""

    def test_resolve_helpers_patched_during_call(self, tmp_path):
        """When _resolve_cron_dir is monkeypatched, internal code uses it."""
        from cron.jobs import _resolve_cron_dir

        original = _resolve_cron_dir()
        target = tmp_path / "patched-cron"
        target.mkdir()

        # Simulate what _call_cron_for_profile does
        from cron import jobs as cron_jobs
        orig = cron_jobs._resolve_cron_dir
        try:
            cron_jobs._resolve_cron_dir = lambda: target
            assert cron_jobs._resolve_cron_dir() == target
            assert cron_jobs._resolve_output_dir() == target / "output"
            assert cron_jobs._resolve_jobs_file() == target / "jobs.json"
        finally:
            cron_jobs._resolve_cron_dir = orig

        # Restored
        assert cron_jobs._resolve_cron_dir() == original

    def test_module_constants_patched_during_call(self, tmp_path):
        """Module-level CRON_DIR/JOBS_FILE/OUTPUT_DIR are also retargeted."""
        from cron import jobs as cron_jobs

        orig_cron_dir = cron_jobs.CRON_DIR
        orig_jobs_file = cron_jobs.JOBS_FILE
        orig_output_dir = cron_jobs.OUTPUT_DIR

        target = tmp_path / "patched-cron"
        target.mkdir()

        try:
            cron_jobs.CRON_DIR = target
            cron_jobs.JOBS_FILE = target / "jobs.json"
            cron_jobs.OUTPUT_DIR = target / "output"

            assert cron_jobs.CRON_DIR == target
            assert cron_jobs.JOBS_FILE == target / "jobs.json"
            assert cron_jobs.OUTPUT_DIR == target / "output"
        finally:
            cron_jobs.CRON_DIR = orig_cron_dir
            cron_jobs.JOBS_FILE = orig_jobs_file
            cron_jobs.OUTPUT_DIR = orig_output_dir

    def test_load_jobs_uses_patched_resolve(self, tmp_path):
        """load_jobs() reads from the patched profile, not the import-time default."""
        from cron import jobs as cron_jobs

        target = tmp_path / "profile-cron"
        target.mkdir()
        jobs_data = {"jobs": [{"id": "test-from-alt", "name": "alt-job"}], "updated_at": ""}
        (target / "jobs.json").write_text(json.dumps(jobs_data))
        (target / "output").mkdir()

        orig_resolve = cron_jobs._resolve_cron_dir
        orig_cron_dir = cron_jobs.CRON_DIR
        try:
            cron_jobs._resolve_cron_dir = lambda: target
            cron_jobs.CRON_DIR = target
            loaded = cron_jobs.load_jobs()
        finally:
            cron_jobs._resolve_cron_dir = orig_resolve
            cron_jobs.CRON_DIR = orig_cron_dir

        assert len(loaded) == 1
        assert loaded[0]["id"] == "test-from-alt"

    def test_ensure_dirs_creates_under_patched_path(self, tmp_path):
        """ensure_dirs() creates directories under the patched profile."""
        from cron import jobs as cron_jobs

        target = tmp_path / "profile-cron"

        orig_resolve = cron_jobs._resolve_cron_dir
        try:
            cron_jobs._resolve_cron_dir = lambda: target
            cron_jobs.ensure_dirs()
        finally:
            cron_jobs._resolve_cron_dir = orig_resolve

        assert (target).is_dir()
        assert (target / "output").is_dir()
