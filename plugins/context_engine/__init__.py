"""Context engine plugin discovery.

Scans ``plugins/context_engine/<name>/`` directories for context engine
plugins.  Each subdirectory must contain ``__init__.py`` with a class
implementing the ContextEngine ABC.

Context engines are separate from the general plugin system — they live
in the repo and are always available without user installation.

Supported configurations:
- context.engine: lcm      — LCM for compression only
- context.engine: rlm      — RLM as standalone engine
- context.engine: lcm + context.rlm: true — LCM + RLM companion mode

The default engine is ``"compressor"`` (the built-in ContextCompressor).
"""

from __future__ import annotations

import importlib
import importlib.util
import inspect
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_CONTEXT_ENGINE_PLUGINS_DIR = Path(__file__).parent


def discover_context_engines() -> List[Tuple[str, str, bool]]:
    """Scan plugins/context_engine/ for available engines.

    Returns list of (name, description, is_available) tuples.
    Does NOT import the engines — just reads plugin.yaml for metadata
    and does a lightweight availability check.
    """
    results = []
    if not _CONTEXT_ENGINE_PLUGINS_DIR.is_dir():
        return results

    for child in sorted(_CONTEXT_ENGINE_PLUGINS_DIR.iterdir()):
        if not child.is_dir() or child.name.startswith(("_", ".")):
            continue
        init_file = child / "__init__.py"
        if not init_file.exists():
            continue

        # Read description from plugin.yaml if available
        desc = ""
        yaml_file = child / "plugin.yaml"
        if yaml_file.exists():
            try:
                import yaml
                with open(yaml_file, encoding="utf-8-sig") as f:
                    meta = yaml.safe_load(f) or {}
                desc = meta.get("description", "")
            except Exception:
                pass

        # Quick availability check — try loading and calling is_available()
        available = True
        try:
            engine = _load_engine_from_dir(child)
            if engine is None:
                available = False
            elif hasattr(engine, "is_available"):
                available = engine.is_available()
        except Exception:
            available = False

        results.append((child.name, desc, available))

    return results


def load_context_engine(name: str, **kwargs: Any) -> Optional["ContextEngine"]:
    """Load and return a ContextEngine instance by name.

    Args:
        name: Engine name (e.g. "lcm", "rlm", "compressor")
        **kwargs: Configuration passed to the engine constructor

    Returns None if the engine is not found or fails to load.
    """
    if name == "compressor":
        # Built-in engine — don't auto-load plugins
        return None

    engine_dir = _CONTEXT_ENGINE_PLUGINS_DIR / name
    if not engine_dir.is_dir():
        logger.debug("Context engine '%s' not found in %s", name, _CONTEXT_ENGINE_PLUGINS_DIR)
        return None

    try:
        engine = _load_engine_from_dir(engine_dir, **kwargs)
        if engine:
            return engine
        logger.warning("Context engine '%s' loaded but no engine instance found", name)
        return None
    except Exception as e:
        logger.warning("Failed to load context engine '%s': %s", name, e)
        return None


def load_composite_engine(
    compression_name: str = "lcm",
    rlm_enabled: bool = False,
    **kwargs: Any,
) -> Optional["ContextEngine"]:
    """Load a composite context engine combining LCM (compression) and RLM (tools).

    When rlm_enabled=True, creates a CompositeContextEngine that wraps both
    the compression engine and the RLM engine. When rlm_enabled=False,
    returns the compression engine directly.

    Args:
        compression_name: Name of the compression engine (default: "lcm")
        rlm_enabled: Whether to enable RLM companion mode
        **kwargs: Configuration passed to both engines

    Returns a ContextEngine instance (compressed engine or composite wrapper).
    """
    compression_engine = load_context_engine(compression_name, **kwargs)
    if compression_engine is None:
        return None

    if not rlm_enabled:
        return compression_engine

    # Load RLM companion engine
    try:
        from plugins.context_engine.rlm import RlmContextEngine
        rlm_engine = RlmContextEngine(**kwargs)
    except Exception as e:
        logger.debug("Failed to load RLM companion engine: %s", e)
        return compression_engine

    # Load the CompositeContextEngine
    try:
        from plugins.context_engine.rlm import CompositeContextEngine
        engine = CompositeContextEngine(compression_engine, rlm_engine, **kwargs)
        return engine
    except Exception as e:
        logger.warning("Failed to create composite engine: %s", e)
        return compression_engine


def _load_engine_from_dir(
    engine_dir: Path, **kwargs: Any
) -> Optional["ContextEngine"]:
    """Import an engine module and extract the ContextEngine instance.

    The module must have either:
    - A register(ctx) function (plugin-style) — we simulate a ctx
    - A top-level class that extends ContextEngine — we instantiate it
    """
    name = engine_dir.name
    module_name = f"plugins.context_engine.{name}"
    init_file = engine_dir / "__init__.py"

    if not init_file.exists():
        return None

    # Check if already loaded
    if module_name in sys.modules:
        mod = sys.modules[module_name]
    else:
        # Handle relative imports within the plugin
        # First ensure the parent packages are registered
        for parent in ("plugins", "plugins.context_engine"):
            if parent not in sys.modules:
                parent_path = Path(__file__).parent
                if parent == "plugins":
                    parent_path = parent_path.parent
                parent_init = parent_path / "__init__.py"
                if parent_init.exists():
                    spec = importlib.util.spec_from_file_location(
                        parent, str(parent_init),
                        submodule_search_locations=[str(parent_path)]
                    )
                    if spec:
                        parent_mod = importlib.util.module_from_spec(spec)
                        sys.modules[parent] = parent_mod
                        try:
                            spec.loader.exec_module(parent_mod)
                        except Exception:
                            pass

        # Now load the engine module
        spec = importlib.util.spec_from_file_location(
            module_name, str(init_file),
            submodule_search_locations=[str(engine_dir)]
        )
        if not spec:
            return None

        mod = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = mod

        # Register submodules so relative imports work
        for sub_file in engine_dir.glob("*.py"):
            if sub_file.name == "__init__.py":
                continue
            sub_name = sub_file.stem
            full_sub_name = f"{module_name}.{sub_name}"
            if full_sub_name not in sys.modules:
                sub_spec = importlib.util.spec_from_file_location(
                    full_sub_name, str(sub_file)
                )
                if sub_spec:
                    sub_mod = importlib.util.module_from_spec(sub_spec)
                    sys.modules[full_sub_name] = sub_mod
                    try:
                        sub_spec.loader.exec_module(sub_mod)
                    except Exception as e:
                        logger.debug("Failed to load submodule %s: %s", full_sub_name, e)

        try:
            spec.loader.exec_module(mod)
        except Exception as e:
            logger.debug("Failed to exec_module %s: %s", module_name, e)
            sys.modules.pop(module_name, None)
            return None

    # Try register(ctx) pattern first (how plugins are written)
    if hasattr(mod, "register"):
        collector = _EngineCollector()
        try:
            reg_sig = inspect.signature(mod.register)
            filtered = _filter_kwargs(kwargs, reg_sig)
            mod.register(collector, **filtered)
            if collector.engine:
                return collector.engine
        except Exception as e:
            logger.debug("register() failed for %s: %s", name, e)

    # Fallback: find a ContextEngine subclass and instantiate it
    from agent.context_engine import ContextEngine
    for attr_name in dir(mod):
        attr = getattr(mod, attr_name, None)
        if (isinstance(attr, type) and issubclass(attr, ContextEngine)
                and attr is not ContextEngine):
            try:
                init_sig = inspect.signature(attr.__init__)
                filtered = _filter_kwargs(kwargs, init_sig)
                return attr(**filtered)
            except Exception:
                pass

    return None


def _filter_kwargs(kwargs: Dict[str, Any], sig: "inspect.Signature") -> Dict[str, Any]:
    """Return a filtered copy of kwargs accepted by the given signature.

    If the callable declares a **kwargs parameter (VAR_KEYWORD), all kwargs are
    passed through unchanged — the callee accepts arbitrary keyword arguments.
    Otherwise only the kwargs whose names appear as explicit parameters are kept.
    This prevents TypeError when a custom engine's register() does not declare
    parameters like ``rlm_config`` or ``lcm_config``.
    """
    params = sig.parameters
    # If there's a **kwargs catch-all, pass everything
    if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()):
        return dict(kwargs)
    # Otherwise filter to only declared parameter names (excluding 'self'/'ctx')
    accepted = set(params.keys()) - {"self", "ctx"}
    return {k: v for k, v in kwargs.items() if k in accepted}


class _EngineCollector:
    """Fake plugin context that captures register_context_engine calls."""

    def __init__(self):
        self.engine = None

    def register_context_engine(self, engine):
        self.engine = engine

    # No-op for other registration methods
    def register_tool(self, *args, **kwargs):
        pass

    def register_hook(self, *args, **kwargs):
        pass

    def register_cli_command(self, *args, **kwargs):
        pass

    def register_memory_provider(self, *args, **kwargs):
        pass

