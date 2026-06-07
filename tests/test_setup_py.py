from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import types


SETUP_PATH = Path(__file__).resolve().parents[1] / "setup.py"


def _load_setup_module():
    spec = importlib.util.spec_from_file_location("hermes_setup_py_test", SETUP_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    setuptools_stub = types.ModuleType("setuptools")
    setuptools_stub.setup = lambda *args, **kwargs: None
    sys.modules["setuptools"] = setuptools_stub
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop("setuptools", None)
    return module


def test_data_file_tree_tolerates_missing_root(tmp_path):
    setup_mod = _load_setup_module()
    setup_mod.REPO_ROOT = tmp_path

    assert setup_mod._data_file_tree("optional-skills") == []
