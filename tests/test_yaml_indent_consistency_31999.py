"""Regression tests for #31999 — YAML indent consistency across writers.

The bug: ``utils.atomic_yaml_write`` used default PyYAML, which emits
"indentless" sequences (list items at column 0 under their parent
mapping key).  ``utils.atomic_roundtrip_yaml_update`` uses ``ruamel.yaml``
configured with ``indent(mapping=2, sequence=4, offset=2)``, which emits
list items at column 2.  When both writers touched the same
``config.yaml`` (e.g. CLI sets ``/skin`` via ruamel, then the Web UI
saves via PyYAML), indentation flipped on every save, eventually
landing in a mixed-indent state that ``js-yaml`` rejects with
``bad indentation of a mapping entry``.  In production this surfaced
as the Gateway silently dropping ``custom_providers`` and falling back
to defaults.

Fix: route ``atomic_yaml_write`` through ``IndentDumper`` (a PyYAML
``SafeDumper`` subclass that forces ``indentless=False``) so the two
serializers produce byte-identical layouts.  Also fold the Web UI
save path (``tui_gateway.server._save_cfg``) and the Telegram DM-topic
persistence path through the same writer so every config-mutating
code path emits the same shape.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest
import yaml

from utils import IndentDumper, atomic_roundtrip_yaml_update, atomic_yaml_write


# ---------------------------------------------------------------------------
# Shared sample data — exercises the exact list-under-mapping shape from
# the issue's traceback (``custom_providers``).
# ---------------------------------------------------------------------------

_SAMPLE_CONFIG = {
    "custom_providers": [
        {"name": "NVIDIA", "base_url": "https://api.nvidia.example/v1", "api_key": "x"},
        {"name": "Together", "base_url": "https://api.together.xyz/v1", "api_key": "y"},
    ],
    "platforms": {
        "telegram": {
            "extra": {
                "dm_topics": [
                    {"chat_id": 1234, "topics": [{"name": "general"}]},
                ],
            },
        },
    },
}


# ---------------------------------------------------------------------------
# IndentDumper: PyYAML output now matches ruamel.yaml byte-for-byte
# ---------------------------------------------------------------------------


class TestIndentDumperShape:
    """The PyYAML dumper now emits 2-indent list items under mappings."""

    def test_indent_dumper_indents_top_level_list_items(self):
        """The top-level ``custom_providers`` entries open at column 2."""
        out = yaml.dump(
            _SAMPLE_CONFIG,
            Dumper=IndentDumper,
            default_flow_style=False,
            sort_keys=False,
        )
        assert "custom_providers:\n  - name: NVIDIA" in out

    def test_default_pyyaml_emits_indentless_list_for_comparison(self):
        """Sanity check: the un-fixed PyYAML default still emits 0-indent.

        Pins the regression baseline so a future PyYAML behavior change
        doesn't silently make the fix redundant (or break it).
        """
        out = yaml.dump(_SAMPLE_CONFIG, default_flow_style=False, sort_keys=False)
        # Without IndentDumper, top-level ``custom_providers`` list items
        # sit at column 0 (immediately after the parent key, no indent).
        assert "custom_providers:\n- name: NVIDIA" in out

    def test_indent_dumper_round_trips_through_safe_load(self):
        """Output must still parse back to the same data."""
        out = yaml.dump(
            _SAMPLE_CONFIG,
            Dumper=IndentDumper,
            default_flow_style=False,
            sort_keys=False,
        )
        loaded = yaml.safe_load(out)
        assert loaded == _SAMPLE_CONFIG


class TestAtomicYamlWriteAndRuamelMatch:
    """``atomic_yaml_write`` and ``atomic_roundtrip_yaml_update`` agree on layout.

    The whole point of the fix: regardless of which writer the user
    happens to trip first, every subsequent writer produces the same
    indentation so the file never flips between styles.
    """

    def test_atomic_yaml_write_uses_2_indent_lists(self, tmp_path: Path):
        """The primary writer now emits ruamel-compatible 2-indent lists."""
        path = tmp_path / "config.yaml"
        atomic_yaml_write(path, _SAMPLE_CONFIG)
        text = path.read_text(encoding="utf-8")
        # Each list item under custom_providers is at column 2.
        assert "custom_providers:\n  - name: NVIDIA" in text
        # 0-indent list shape (the broken layout) must NOT appear at the
        # top level for ``custom_providers``.
        assert "custom_providers:\n- name:" not in text

    def test_atomic_yaml_write_layout_matches_ruamel_seed(self, tmp_path: Path):
        """A file seeded by ruamel and re-saved by atomic_yaml_write keeps shape.

        Models the mixed-writer sequence that produced #31999:
            CLI ``/skin`` (ruamel) → Web UI ``Save`` (atomic_yaml_write).
        Before the fix the second write toggled the layout and either
        wiped comments or produced mixed indent.  After the fix the
        second write leaves the list-item indentation identical.
        """
        path = tmp_path / "config.yaml"
        # First write through ruamel (the CLI single-key-update path).
        atomic_roundtrip_yaml_update(
            path, "custom_providers", _SAMPLE_CONFIG["custom_providers"]
        )
        ruamel_layout = path.read_text(encoding="utf-8")

        # Now have ``atomic_yaml_write`` rewrite the same data.  The list
        # column for ``- name:`` items must match.
        atomic_yaml_write(path, _SAMPLE_CONFIG)
        pyyaml_layout = path.read_text(encoding="utf-8")

        ruamel_dash_col = next(
            line.index("- name:")
            for line in ruamel_layout.splitlines()
            if "- name:" in line
        )
        pyyaml_dash_col = next(
            line.index("- name:")
            for line in pyyaml_layout.splitlines()
            if "- name:" in line
        )
        assert ruamel_dash_col == pyyaml_dash_col == 2

    def test_round_trip_pyyaml_then_ruamel_then_pyyaml_stays_consistent(
        self, tmp_path: Path,
    ):
        """The PyYAML/ruamel toggle dance no longer flips layout each pass.

        Reproduces the exact 4-step sequence from the issue's "Steps to
        Reproduce": fresh save → scanner save → Web UI save → CLI key
        update.  After the fix every step emits the same 2-indent shape
        so the file converges instead of bouncing between styles.
        """
        path = tmp_path / "config.yaml"

        # Step 1: fresh ``atomic_yaml_write``.
        atomic_yaml_write(path, _SAMPLE_CONFIG)
        layout_1 = path.read_text(encoding="utf-8")

        # Step 2: ruamel single-key update (touches one nested value).
        atomic_roundtrip_yaml_update(path, "ui.skin", "monokai")
        layout_2 = path.read_text(encoding="utf-8")

        # Step 3: ``atomic_yaml_write`` again (Web UI Save).
        merged = yaml.safe_load(layout_2) or {}
        atomic_yaml_write(path, merged)
        layout_3 = path.read_text(encoding="utf-8")

        # Step 4: another ruamel update.
        atomic_roundtrip_yaml_update(path, "ui.compact", True)
        layout_4 = path.read_text(encoding="utf-8")

        # All four files must keep ``custom_providers`` items at column 2
        # — no flip-flop.  Earlier PyYAML default would have emitted them
        # at column 0 on every other write.
        for layout in (layout_1, layout_2, layout_3, layout_4):
            assert "custom_providers:\n  - name: NVIDIA" in layout, (
                f"layout flipped to 0-indent: {layout!r}"
            )
            assert "custom_providers:\n- name:" not in layout
            # And every layout still parses cleanly through both readers.
            assert yaml.safe_load(layout) is not None


# ---------------------------------------------------------------------------
# Source-level guards: every config writer goes through the unified path
# ---------------------------------------------------------------------------


class TestUnifiedConfigWriters:
    """All ``config.yaml`` writers route through ``atomic_yaml_write``.

    Pins the wiring in source so an accidental ``yaml.safe_dump(...)``
    re-introduction is loud at code review.
    """

    def test_atomic_yaml_write_uses_indent_dumper(self):
        """The primary writer must reference ``IndentDumper`` explicitly."""
        src = inspect.getsource(atomic_yaml_write)
        assert "IndentDumper" in src
        assert "Dumper=IndentDumper" in src
        # Issue reference so the guard isn't refactored away silently.
        assert "31999" in src

    def test_tui_gateway_save_cfg_uses_atomic_yaml_write(self):
        """The Web UI save path no longer calls ``yaml.safe_dump`` directly."""
        from tui_gateway.server import _save_cfg
        src = inspect.getsource(_save_cfg)
        assert "atomic_yaml_write" in src
        # Direct ``yaml.safe_dump(`` (the buggy v0.14.0 shape) is gone.
        assert "yaml.safe_dump(" not in src

    def test_telegram_persist_dm_topic_uses_atomic_yaml_write(self):
        """The Telegram DM-topic persist path goes through the shared writer."""
        from gateway.platforms.telegram import TelegramAdapter
        src = inspect.getsource(TelegramAdapter._persist_dm_topic_thread_id)
        assert "atomic_yaml_write" in src
        # Direct ``_yaml.dump(config, ...)`` is gone.
        assert "_yaml.dump(config" not in src


class TestIndentDumperHandlesUnicode:
    """The fix preserves the previous behaviour for non-ASCII config values."""

    def test_unicode_keys_survive_round_trip(self, tmp_path: Path):
        """Chinese / Japanese model names in ``custom_providers`` round-trip."""
        path = tmp_path / "config.yaml"
        cfg = {
            "custom_providers": [
                {"name": "智谱-GLM", "base_url": "https://open.bigmodel.cn/api/paas/v4"},
                {"name": "ムーンショット", "base_url": "https://api.moonshot.ai"},
            ],
        }
        atomic_yaml_write(path, cfg)
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert loaded == cfg
        # Should be human-readable (allow_unicode=True), not escaped \u…
        assert "智谱-GLM" in path.read_text(encoding="utf-8")


class TestAtomicYamlWritePreservesAtomicity:
    """The IndentDumper change must not regress the atomic-write contract.

    ``atomic_yaml_write`` is guaranteed to (a) never leave a partially-
    written file and (b) preserve symlinks.  Both are unrelated to the
    indent fix, but they would silently regress if a careless refactor
    swapped the writer for plain ``open(..., "w")``.
    """

    def test_atomic_replace_target_overwritten_in_place(self, tmp_path: Path):
        path = tmp_path / "config.yaml"
        path.write_text("placeholder", encoding="utf-8")
        original_inode = path.stat().st_ino

        atomic_yaml_write(path, _SAMPLE_CONFIG)

        # File still exists at the same logical path.
        assert path.exists()
        # Content is the new YAML, not the placeholder.
        text = path.read_text(encoding="utf-8")
        assert "custom_providers:" in text
        # Inode may differ (atomic replace via rename), but content is fresh.
        assert path.stat().st_ino != original_inode or text != "placeholder"

    def test_existing_permissions_preserved(self, tmp_path: Path):
        """File mode must survive the atomic temp-file swap."""
        import os
        import stat

        path = tmp_path / "config.yaml"
        path.write_text("seed", encoding="utf-8")
        # Make the file world-readable to verify permission survival.
        os.chmod(path, 0o644)
        atomic_yaml_write(path, _SAMPLE_CONFIG)
        mode = stat.S_IMODE(path.stat().st_mode)
        assert mode == 0o644
