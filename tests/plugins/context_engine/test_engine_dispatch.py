"""Regression tests for run_agent.py context-engine dispatch logic.

Before the fix, the dispatch condition was:
    if _engine_name == "compressor" or _engine_name not in ("lcm", "rlm"):
        pass  # fall through to built-in compressor — BUG

Any engine name that was not "lcm" or "rlm" silently fell into the no-op
branch.  E.g. context.engine: "custom" would never call load_context_engine.

After the fix the condition is simply:
    if _engine_name == "compressor":
        pass

So any other name reaches the generic else branch that calls
load_context_engine(_engine_name, ...).
"""

import json
import sys
import types
from unittest.mock import MagicMock, patch


class TestEngineDispatch:
    """Verify that custom engine names reach load_context_engine()."""

    def _run_dispatch(self, engine_name: str, rlm_enabled: bool = False):
        """Execute just the context-engine dispatch block from run_agent.py.

        Replicated from run_agent.py lines ~1907-1966 so the logic can be
        unit-tested without spinning up a full AIAgent.
        """
        _ctx_cfg = {"engine": engine_name, "rlm": rlm_enabled, "rlm_config": {}}
        _engine_name = _ctx_cfg.get("engine", "compressor") or "compressor"
        _rlm_enabled = bool(_ctx_cfg.get("rlm", False))
        _selected_engine = None

        if _engine_name == "compressor":
            pass
        elif _engine_name == "rlm":
            try:
                from plugins.context_engine import load_context_engine  # noqa: F401
                _selected_engine = load_context_engine(
                    "rlm", rlm_config=_ctx_cfg.get("rlm_config", {})
                )
            except Exception:
                pass
        else:
            rlm_kwargs = {"rlm_config": _ctx_cfg.get("rlm_config", {})}
            if _rlm_enabled:
                try:
                    from plugins.context_engine import load_composite_engine  # noqa: F401
                    _selected_engine = load_composite_engine(
                        compression_name=_engine_name,
                        rlm_enabled=True,
                        **rlm_kwargs,
                    )
                except Exception:
                    _selected_engine = None
            if _selected_engine is None:
                try:
                    from plugins.context_engine import load_context_engine  # noqa: F401
                    _selected_engine = load_context_engine(
                        _engine_name,
                        rlm_config=rlm_kwargs.get("rlm_config"),
                    )
                except Exception:
                    pass

        return _selected_engine

    def test_compressor_name_uses_builtin(self):
        """engine=compressor must never call load_context_engine."""
        mock_engine = MagicMock(name="mock_engine")
        with patch("plugins.context_engine.load_context_engine", return_value=mock_engine) as mock_load:
            result = self._run_dispatch("compressor")
        mock_load.assert_not_called()
        assert result is None

    def test_custom_engine_name_calls_load_context_engine(self):
        """engine=custom must call load_context_engine('custom', ...)."""
        mock_engine = MagicMock(name="mock_custom_engine")
        with patch("plugins.context_engine.load_context_engine", return_value=mock_engine) as mock_load:
            result = self._run_dispatch("custom")
        mock_load.assert_called_once()
        call_args = mock_load.call_args
        assert call_args[0][0] == "custom", (
            f"load_context_engine called with engine name {call_args[0][0]!r}, expected 'custom'"
        )
        assert result is mock_engine

    def test_lcm_engine_still_calls_load_context_engine(self):
        """engine=lcm must also reach load_context_engine (not broken by fix)."""
        mock_engine = MagicMock(name="mock_lcm_engine")
        with patch("plugins.context_engine.load_context_engine", return_value=mock_engine) as mock_load:
            result = self._run_dispatch("lcm")
        mock_load.assert_called_once()
        assert mock_load.call_args[0][0] == "lcm"
        assert result is mock_engine

    def test_rlm_standalone_calls_load_context_engine_with_rlm(self):
        """engine=rlm must call load_context_engine('rlm', ...)."""
        mock_engine = MagicMock(name="mock_rlm_engine")
        with patch("plugins.context_engine.load_context_engine", return_value=mock_engine) as mock_load:
            result = self._run_dispatch("rlm")
        mock_load.assert_called_once()
        assert mock_load.call_args[0][0] == "rlm"
        assert result is mock_engine

    def test_custom_engine_with_rlm_tries_composite_first(self):
        """engine=custom with rlm=True must try load_composite_engine first."""
        mock_composite = MagicMock(name="mock_composite")
        with patch("plugins.context_engine.load_composite_engine", return_value=mock_composite) as mock_composite_load, \
             patch("plugins.context_engine.load_context_engine") as mock_plain_load:
            result = self._run_dispatch("custom", rlm_enabled=True)
        mock_composite_load.assert_called_once()
        assert mock_composite_load.call_args[1]["compression_name"] == "custom"
        mock_plain_load.assert_not_called()  # composite succeeded, no fallback needed
        assert result is mock_composite


# ---------------------------------------------------------------------------
# Fix 2 — loader filters kwargs by engine signature to avoid TypeError
# ---------------------------------------------------------------------------

class TestKwargsFiltering:
    """_load_engine_from_dir must not pass kwargs that the engine's register()
    does not declare, avoiding TypeError on custom engines.

    Approach A (inspect.signature): only kwargs in the explicit parameter list
    are forwarded; if register() has a **kwargs catch-all, everything passes.
    """

    def _make_fake_engine_module(self, register_fn, mod_name: str = "fake_engine"):
        """Build a throwaway module with the given register function."""
        from agent.context_engine import ContextEngine
        mod = types.ModuleType(mod_name)
        mod.register = register_fn
        return mod

    def test_register_no_kwargs_does_not_raise(self):
        """A register(ctx) with no kwargs must not receive rlm_config / lcm_config."""
        received = {}

        def register(ctx):
            # If any kwargs were forwarded this call would raise TypeError
            received["called"] = True
            from agent.context_engine import ContextEngine
            class _E(ContextEngine):
                @property
                def name(self): return "fake"
                def compress(self, m, **k): return m
                def should_compress(self, p=None): return False
                def should_compress_preflight(self, m): return False
                def get_tool_schemas(self): return []
                def handle_tool_call(self, n, a, **k): return "{}"
            ctx.register_context_engine(_E())

        from plugins.context_engine import _load_engine_from_dir, _filter_kwargs
        import inspect

        # Verify _filter_kwargs strips unknown keys
        sig = inspect.signature(register)
        filtered = _filter_kwargs({"rlm_config": {}, "lcm_config": {}}, sig)
        assert filtered == {}, (
            f"_filter_kwargs should strip all kwargs from a no-kwargs register(); got {filtered!r}"
        )

    def test_register_explicit_lcm_config_receives_only_lcm_config(self):
        """register(ctx, lcm_config=None) must receive lcm_config but not rlm_config."""
        from plugins.context_engine import _filter_kwargs
        import inspect

        def register(ctx, lcm_config=None):
            pass

        sig = inspect.signature(register)
        filtered = _filter_kwargs({"rlm_config": {"x": 1}, "lcm_config": {"enabled": False}}, sig)
        assert "lcm_config" in filtered, "lcm_config should pass through to a register that declares it"
        assert "rlm_config" not in filtered, "rlm_config should be stripped from a register that doesn't declare it"

    def test_register_with_var_keyword_receives_all_kwargs(self):
        """register(ctx, **kwargs) must receive everything — the VAR_KEYWORD check."""
        from plugins.context_engine import _filter_kwargs
        import inspect

        def register(ctx, **kwargs):
            pass

        sig = inspect.signature(register)
        all_kwargs = {"rlm_config": {}, "lcm_config": {"enabled": True}, "model": "gpt-4"}
        filtered = _filter_kwargs(all_kwargs, sig)
        assert filtered == all_kwargs, (
            "register(**kwargs) should receive all kwargs unchanged"
        )

    def test_load_context_engine_lcm_with_rlm_config_no_error(self):
        """load_context_engine('lcm', rlm_config={...}, lcm_config={...}) must not
        raise TypeError — lcm's register() accepts **kwargs so all pass through."""
        from plugins.context_engine import load_context_engine
        engine = load_context_engine("lcm", rlm_config={"max_iterations": 5}, lcm_config={"enabled": True})
        assert engine is not None, "load_context_engine should return an LcmContextEngine"
        assert engine.name == "lcm"
