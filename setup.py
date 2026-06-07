from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from setuptools import setup


REPO_ROOT = Path(__file__).parent.resolve()


def _data_file_tree(root_name: str) -> list[tuple[str, list[str]]]:
    root = REPO_ROOT / root_name
    grouped: defaultdict[str, list[str]] = defaultdict(list)
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel_path = path.relative_to(REPO_ROOT)
        grouped[str(rel_path.parent)].append(str(rel_path))
    return sorted(grouped.items())


def _plugin_dashboard_data_files() -> list[tuple[str, list[str]]]:
    """Collect non-Python dashboard plugin assets for wheel inclusion.

    Discovers any ``plugins/<name>/dashboard/`` directory with non-Python
    assets (``manifest.json``, ``dist/`` bundles, etc.) — no need to
    enumerate plugin names manually.  ``.py`` files are excluded because
    setuptools package discovery handles them.
    """
    grouped: defaultdict[str, list[str]] = defaultdict(list)
    for dashboard_dir in sorted(REPO_ROOT.glob("plugins/*/dashboard")):
        if not dashboard_dir.is_dir():
            continue
        for path in sorted(dashboard_dir.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix == ".py":
                continue
            rel_path = path.relative_to(REPO_ROOT)
            grouped[str(rel_path.parent)].append(str(rel_path))
    return sorted(grouped.items())


setup(
    data_files=[
        *_data_file_tree("skills"),
        *_data_file_tree("optional-skills"),
        *_plugin_dashboard_data_files(),
    ]
)
