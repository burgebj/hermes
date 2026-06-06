"""Pytest configuration: import path + per-test temporary database."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Make the skill scripts importable as ``scripts``.
ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "skill" / "on-this-day-art-trivia"
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture()
def tmp_db(tmp_path, monkeypatch):
    """Point state.get_db_path at a fresh per-test SQLite file."""
    from scripts import state  # type: ignore

    db_path = tmp_path / "trivia.db"
    state.set_db_path(db_path)
    state.migrate()
    yield db_path
    state.set_db_path(state._DEFAULT_DB_PATH)


@pytest.fixture()
def fixtures_dir():
    return FIXTURES_DIR


@pytest.fixture()
def britannica_fixture(fixtures_dir):
    return (fixtures_dir / "britannica_april28.html").read_text(encoding="utf-8")


@pytest.fixture()
def wikimedia_fixture(fixtures_dir):
    import json
    return json.loads((fixtures_dir / "wikimedia_april28.json").read_text(encoding="utf-8"))
