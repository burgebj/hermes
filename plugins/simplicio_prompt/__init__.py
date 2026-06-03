"""SIMPLICIO_PROMPT plugin.

Adds an opt-in pre-LLM prompt overlay for users who want every Hermes turn to
follow the SIMPLICIO_PROMPT V2 tuple-space execution policy automatically.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

from utils import env_var_enabled, is_truthy_value


PLUGIN_NAME = "SIMPLICIO_PROMPT"
PLUGIN_DIR = Path(__file__).resolve().parent
VENDORED_ROOT = PLUGIN_DIR / "vendor" / "simplicio_prompt"
VENDORED_PROMPT_PATH = VENDORED_ROOT / "prompts" / "agent-runtime-execution-prompt.md"
VENDORED_SOURCE_COMMIT = "c1df48534a6e23cacee94c8894cc4ca382aa3459"

FALLBACK_RUNTIME_POLICY = """You are a Tuple-Space + Yool Architecture execution engine.
Treat any prompt, chat message, question, command, code snippet, or user input
as task X. Decompose X into a Hilbert-indexed tuple graph, create a root tuple,
use batch_spawn(depth, branching, compression_threshold) for 1,000,000+
subagents without enumeration, execute active work with spawn_agent, route by
out_tuple/in_tuple/rd_tuple/route_packet/scan_index, apply hookwall,
compress_token, prune_idle, LaneWorkerPool, receipt/input cache, adaptive lanes,
jittered backoff, provider circuit breakers, small-task batching,
prompt/context compression, local deterministic routing, and idempotent-only
speculation. Respect provider limits and terms.

Return exactly:
[Tuple Space Snapshot]
[Active Agents/Subagents]
[Total Agents/Subagents]
[Proximo Yool a executar]
[Resultado parcial]"""


def _extract_prompt_section(markdown: str) -> str:
    lines = markdown.splitlines()
    try:
        start_idx = next(
            i for i, line in enumerate(lines) if line.strip() == "## Prompt"
        )
    except StopIteration:
        return markdown.strip()

    body = lines[start_idx + 1 :]
    for idx, line in enumerate(body):
        if line.startswith("## "):
            body = body[:idx]
            break
    return "\n".join(body).strip()


@lru_cache(maxsize=1)
def _load_vendored_prompt_section() -> str:
    try:
        prompt = VENDORED_PROMPT_PATH.read_text(encoding="utf-8")
    except OSError:
        return FALLBACK_RUNTIME_POLICY

    section = _extract_prompt_section(prompt)
    if not section:
        return FALLBACK_RUNTIME_POLICY
    return section


@lru_cache(maxsize=1)
def _build_context_text() -> str:
    vendored_prompt = _load_vendored_prompt_section()
    return f"""[SIMPLICIO_PROMPT]
Bundled local snapshot: plugins/simplicio_prompt/vendor/simplicio_prompt.
Vendored source commit: {VENDORED_SOURCE_COMMIT}.
Apply to every enabled main-agent turn before the model call. Treat every
prompt/message as eligible for SIMPLICIO_PROMPT, including questions, commands,
code snippets, single words, layout edits, refactors, debugging, docs, and
normal chat. Do not require any trigger word such as "Implement", "Fix", or
"Build".

Do not fetch or consult an external GitHub repository to execute this policy.
The local bundle includes the prompt, spec, reference kernel, guardrails,
examples, benchmarks, receipts, and build scripts needed by SIMPLICIO_PROMPT V2.
When file access is available, read local bundled files before editing:
- plugins/simplicio_prompt/vendor/simplicio_prompt/YOOL_TUPLE_HAMT.md
- plugins/simplicio_prompt/vendor/simplicio_prompt/kernel/yool_tuple_kernel.py
- plugins/simplicio_prompt/vendor/simplicio_prompt/kernel/README.md
- plugins/simplicio_prompt/vendor/simplicio_prompt/guardrails/cpu_throttle.py
- plugins/simplicio_prompt/vendor/simplicio_prompt/guardrails/disk_gc.py
- plugins/simplicio_prompt/vendor/simplicio_prompt/examples/python/minimal_bus.py
- plugins/simplicio_prompt/vendor/simplicio_prompt/examples/python/receipts.py
- plugins/simplicio_prompt/vendor/simplicio_prompt/scripts/build_hamt.py
- plugins/simplicio_prompt/vendor/simplicio_prompt/prompts/agent-runtime-execution-prompt.md

Vendored SIMPLICIO_PROMPT V2 policy:
{vendored_prompt}
[/SIMPLICIO_PROMPT]"""


SIMPLICIO_PROMPT_CONTEXT = _build_context_text()


def _load_config() -> Dict[str, Any]:
    try:
        from hermes_cli.config import load_config

        config = load_config()
    except Exception:
        return {}
    return config if isinstance(config, dict) else {}


def _config_flag_enabled(config: Dict[str, Any]) -> bool:
    try:
        from hermes_cli.config import cfg_get

        explicit = cfg_get(config, "simplicio_prompt", "enabled", default=False)
    except Exception:
        explicit = False
    if is_truthy_value(explicit):
        return True

    plugins_cfg = config.get("plugins")
    enabled = plugins_cfg.get("enabled") if isinstance(plugins_cfg, dict) else None
    if isinstance(enabled, list):
        normalized = {str(item).strip().lower() for item in enabled}
        return PLUGIN_NAME.lower() in normalized or "simplicio_prompt" in normalized
    return False


def _config_flag_disabled(config: Dict[str, Any]) -> bool:
    plugins_cfg = config.get("plugins")
    disabled = plugins_cfg.get("disabled") if isinstance(plugins_cfg, dict) else None
    if not isinstance(disabled, list):
        return False

    normalized = {str(item).strip().lower() for item in disabled}
    return PLUGIN_NAME.lower() in normalized or "simplicio_prompt" in normalized


def is_enabled(config: Optional[Dict[str, Any]] = None) -> bool:
    """Return True when SIMPLICIO_PROMPT should inject its overlay."""
    resolved_config = config if config is not None else _load_config()
    if _config_flag_disabled(resolved_config):
        return False

    if env_var_enabled("SIMPLICIO_PROMPT") or env_var_enabled(
        "HERMES_SIMPLICIO_PROMPT"
    ):
        return True
    return _config_flag_enabled(resolved_config)


def build_context(config: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, str]]:
    """Build a pre_llm_call hook return payload, or None when disabled."""
    if not is_enabled(config):
        return None
    return {"context": SIMPLICIO_PROMPT_CONTEXT}


def _pre_llm_call(**_: Any) -> Optional[Dict[str, str]]:
    """Inject for every enabled turn; message content is intentionally ignored."""
    return build_context()


def register(ctx) -> None:
    """Register the pre_llm_call hook."""
    ctx.register_hook("pre_llm_call", _pre_llm_call)
