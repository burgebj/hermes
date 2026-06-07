"""Regression tests for memory provider submodule loading safety (#38674)."""

from __future__ import annotations

import sys
from pathlib import Path


_PROVIDER_INIT = '''\
class {cls_name}:
    name = "{name}"
    is_available = staticmethod(lambda: True)
    def initialize(self, session_id, **kwargs): pass
    def get_tool_schemas(self): return []
    def shutdown(self): pass

def register(ctx):
    ctx.register_memory_provider({cls_name}())
'''


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _strip_sys_modules(prefix: str) -> None:
    for key in list(sys.modules):
        if key == prefix or key.startswith(prefix + "."):
            sys.modules.pop(key, None)


def _make_provider_dir(tmp_path: Path, name: str, cls_name: str) -> Path:
    provider_dir = tmp_path / name
    provider_dir.mkdir()
    _write_file(provider_dir / "__init__.py", _PROVIDER_INIT.format(cls_name=cls_name, name=name))
    _strip_sys_modules(f"plugins.memory.{name}")
    return provider_dir


def _load_provider_from_dir(tmp_path: Path, provider_dir: Path):
    from plugins import memory as mem_init

    orig_plugins_dir = mem_init._MEMORY_PLUGINS_DIR
    try:
        mem_init._MEMORY_PLUGINS_DIR = tmp_path
        return mem_init._load_provider_from_dir(provider_dir)
    finally:
        mem_init._MEMORY_PLUGINS_DIR = orig_plugins_dir


def test_systemexit_in_legitimate_subfile_does_not_crash_loader(tmp_path):
    provider_dir = _make_provider_dir(tmp_path, "echomind", "EchoMindProvider")
    _write_file(provider_dir / "store.py", "import sys\nsys.exit(1)\n")

    provider = _load_provider_from_dir(tmp_path, provider_dir)

    assert provider is not None
    assert provider.name == "echomind"
    _strip_sys_modules("plugins.memory.echomind")


def test_non_module_py_files_are_not_executed(tmp_path):
    provider_dir = _make_provider_dir(tmp_path, "skipmem", "SkipMemProvider")
    marker = tmp_path / "side_effect.txt"
    side_effect = f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n"
    _write_file(provider_dir / "setup.py", side_effect)
    _write_file(provider_dir / "conftest.py", side_effect)
    _write_file(provider_dir / "test_helpers.py", side_effect)
    _write_file(provider_dir / "helpers_test.py", side_effect)
    _write_file(provider_dir / "store.py", "VALUE = 42\n")

    provider = _load_provider_from_dir(tmp_path, provider_dir)

    assert provider is not None
    assert provider.name == "skipmem"
    assert not marker.exists()
    assert "plugins.memory.skipmem.store" in sys.modules
    assert "plugins.memory.skipmem.setup" not in sys.modules
    assert "plugins.memory.skipmem.conftest" not in sys.modules
    assert "plugins.memory.skipmem.test_helpers" not in sys.modules
    assert "plugins.memory.skipmem.helpers_test" not in sys.modules
    _strip_sys_modules("plugins.memory.skipmem")


def test_legitimate_submodule_still_loads(tmp_path):
    provider_dir = _make_provider_dir(tmp_path, "fullmem", "FullMemProvider")
    _write_file(provider_dir / "store.py", "VALUE = 42\n")

    provider = _load_provider_from_dir(tmp_path, provider_dir)

    assert provider is not None
    assert provider.name == "fullmem"
    store_mod = sys.modules["plugins.memory.fullmem.store"]
    assert store_mod.VALUE == 42
    _strip_sys_modules("plugins.memory.fullmem")
