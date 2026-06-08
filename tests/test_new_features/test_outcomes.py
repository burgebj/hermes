"""Tests for Outcomes Engine."""
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock
from agent.outcomes import OutcomeEngine, Rubric, RubricCriterion, Outcome


@pytest.fixture
def rubric_dir(tmp_path):
    d = tmp_path / "rubrics"
    d.mkdir()
    # Write a sample rubric
    rubric_yaml = """name: code_quality
description: Evaluate code quality
pass_threshold: 0.7
criteria:
  - criterion: correctness
    weight: 0.4
    description: Does the code solve the problem?
  - criterion: readability
    weight: 0.3
    description: Is the code clean and readable?
  - criterion: completeness
    weight: 0.3
    description: Are edge cases handled?
"""
    (d / "code_quality.yaml").write_text(rubric_yaml)
    return d


@pytest.fixture
def engine(rubric_dir):
    return OutcomeEngine(rubric_dir)


def test_list_rubrics(engine):
    rubrics = engine.list_rubrics()
    assert "code_quality" in rubrics


def test_load_rubric(engine):
    rubric = engine.load_rubric("code_quality")
    assert rubric is not None
    assert rubric.name == "code_quality"
    assert rubric.pass_threshold == 0.7
    assert len(rubric.criteria) == 3


def test_load_rubric_not_found(engine):
    rubric = engine.load_rubric("nonexistent")
    assert rubric is None


def test_grade_returns_outcome(engine):
    rubric = engine.load_rubric("code_quality")
    outcome = engine.grade(rubric, "def hello(): print('hi')")
    assert isinstance(outcome, Outcome)
    assert outcome.rubric_name == "code_quality"
    assert 0.0 <= outcome.total_score <= 1.0


def test_outcome_serialization():
    outcome = Outcome(
        rubric_name="test",
        scores={"a": 0.8, "b": 0.6},
        total_score=0.7,
        passed=True,
        feedback="Good",
    )
    engine = OutcomeEngine(Path("/tmp"))
    data = engine.to_dict(outcome)
    assert data["rubric_name"] == "test"
    assert data["passed"] is True


def test_parse_simple_yaml(engine, rubric_dir):
    """Test the fallback YAML parser."""
    data = engine._parse_simple_yaml(rubric_dir / "code_quality.yaml")
    assert data["name"] == "code_quality"
    assert data["pass_threshold"] == 0.7
    assert len(data["criteria"]) == 3
