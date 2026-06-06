"""DGX config helpers — read/write the ``dgx:`` block in config.yaml
and the ``model:`` block that points at DGX endpoints.

Multi-node design: the ``dgx.nodes`` dict holds named DGX instances;
``dgx.active_node`` selects which one is currently active.  Single-node
configs (flat ``dgx.host`` etc.) are transparently migrated on first read.

Defaults are intentionally unset (None) for host-specific values so that
nothing accidentally talks to a stranger's network. The user supplies the
host either by running ``hermes dgx setup`` (interactive) or by exporting
``HERMES_DGX_HOST`` / ``HERMES_DGX_SSH_USER`` / ``HERMES_DGX_LITELLM_HOST``.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

def _env(name: str) -> Optional[str]:
    """Read an env var, returning None for empty/unset."""
    v = os.environ.get(name)
    return v or None


# SSH user falls back to the local $USER so the same machine can be both
# the controller and the GPU host without configuring anything.
_DEFAULT_SSH_USER = _env("HERMES_DGX_SSH_USER") or os.environ.get("USER") or "dgx"

NODE_DEFAULTS: Dict[str, Any] = {
    "host": _env("HERMES_DGX_HOST"),
    "ssh_user": _DEFAULT_SSH_USER,
    "ollama_port": int(_env("HERMES_DGX_OLLAMA_PORT") or "11434"),
    "vllm_port": int(_env("HERMES_DGX_VLLM_PORT") or "30800"),
    "name": "DGX Spark",
}

DEFAULTS: Dict[str, Any] = {
    # flat keys kept for backwards compat and single-node convenience
    "host": _env("HERMES_DGX_HOST"),
    "ssh_user": _DEFAULT_SSH_USER,
    "ollama_port": int(_env("HERMES_DGX_OLLAMA_PORT") or "11434"),
    "vllm_port": int(_env("HERMES_DGX_VLLM_PORT") or "30800"),
    "vllm_32b_port": int(_env("HERMES_DGX_VLLM_32B_PORT") or "30881"),
    "litellm_host": _env("HERMES_DGX_LITELLM_HOST"),
    "litellm_port": int(_env("HERMES_DGX_LITELLM_PORT") or "4000"),
    "active_endpoint": "ollama",
    "default_model": "qwen2.5-coder:latest",
    # vLLM servers started via "hermes dgx models add <hf-model>"
    "vllm_servers": [],
    # multi-node
    "active_node": "default",
    "nodes": {},
}

ENDPOINT_LABELS = {
    "ollama":    "Ollama (direct, no auth)",
    "vllm":      "vLLM 3B (port 30800, always ready)",
    "vllm-32b":  "vLLM 32B (port 30881, qwen2.5-coder-32b)",
    "litellm":   "LiteLLM proxy (HA pool, requires API key)",
}

# Predefined model formations: name → {model, endpoint}
DEFAULT_FORMATIONS: Dict[str, Dict[str, str]] = {
    "coding":      {"model": "qwen3-coder:30b",               "endpoint": "ollama"},
    "reasoning":   {"model": "deepseek-r1:70b",               "endpoint": "ollama"},
    "fast":        {"model": "nemotron-mini:4b",               "endpoint": "ollama"},
    "flagship":    {"model": "qwen3.6:35b",                   "endpoint": "ollama"},
    "vllm-fast":   {"model": "qwen2.5-coder-3b",              "endpoint": "vllm"},
    "vllm-coding": {"model": "qwen2.5-coder-32b",             "endpoint": "vllm-32b"},
}

# NIM models verified to fit in 128 GB unified memory (DGX Spark GB10)
NIM_CATALOG: list[Dict[str, Any]] = [
    {"id": "nvidia/nemotron-3-super-120b-a12b",    "params": "120B/12B-active", "tier": "flagship",  "fits": True},
    {"id": "nvidia/nemotron-3-nano-30b-a3b",        "params": "30B/3B-active",   "tier": "fast",      "fits": True},
    {"id": "nvidia/nemotron-nano-9b-v2",            "params": "9B",              "tier": "mini",      "fits": True},
    {"id": "nvidia/llama-3.1-nemotron-70b-instruct","params": "70B",             "tier": "reasoning", "fits": True},
    {"id": "nvidia/mistral-nemo-12b-instruct",      "params": "12B",             "tier": "fast",      "fits": True},
    {"id": "nvidia/deepseek-r1-distill-llama-70b",  "params": "70B",             "tier": "reasoning", "fits": True},
    {"id": "nvidia/llama-nemotron-embed-1b-v2",     "params": "1B",              "tier": "embed",     "fits": True},
]


# ---------------------------------------------------------------------------
# Config accessors
# ---------------------------------------------------------------------------

def load_dgx_config() -> Dict[str, Any]:
    from hermes_cli.config import load_config
    cfg = load_config()
    dgx = dict(DEFAULTS)
    dgx.update(cfg.get("dgx") or {})
    # Inject _active_node for tools that want the currently selected node
    dgx["_active_node"] = _resolve_active_node(dgx)
    return dgx


def _resolve_active_node(dgx: Dict[str, Any]) -> Dict[str, Any]:
    """Return the active node dict (host, ssh_user, ports).

    Falls back to the flat dgx keys for single-node configs.
    """
    nodes = dgx.get("nodes") or {}
    active_name = dgx.get("active_node", "default")
    if active_name in nodes:
        node = dict(NODE_DEFAULTS)
        node.update(nodes[active_name])
        return node
    # single-node / legacy: synthesise a node from flat keys
    return {
        "host":        dgx["host"],
        "ssh_user":    dgx["ssh_user"],
        "ollama_port": dgx["ollama_port"],
        "vllm_port":   dgx["vllm_port"],
        "name":        dgx.get("name", "DGX Spark"),
    }


def list_nodes(dgx: Dict[str, Any]) -> list[Dict[str, Any]]:
    """Return all configured nodes as a list, including the legacy single node."""
    nodes = dgx.get("nodes") or {}
    if nodes:
        result = []
        for name, nd in nodes.items():
            entry = dict(NODE_DEFAULTS)
            entry.update(nd)
            entry["_key"] = name
            result.append(entry)
        return result
    # single-node
    return [{**_resolve_active_node(dgx), "_key": "default"}]


def save_dgx_config(dgx: Dict[str, Any]) -> None:
    from hermes_cli.config import load_config, save_config
    cfg = load_config()
    # Don't persist the injected _active_node helper key
    to_save = {k: v for k, v in dgx.items() if not k.startswith("_")}
    cfg["dgx"] = to_save
    save_config(cfg)


def apply_endpoint(dgx: Dict[str, Any], endpoint: Optional[str] = None,
                   port_override: Optional[int] = None) -> None:
    """Write model.provider + model.base_url to point at the given endpoint.

    port_override: if set, replaces the vllm/vllm-32b port (used when a
    specific model's vLLM server runs on a non-default port).
    """
    from hermes_cli.config import load_config, save_config

    ep = endpoint or dgx.get("active_endpoint", "ollama")
    node = dgx.get("_active_node") or _resolve_active_node(dgx)
    host = node["host"]

    if ep == "ollama":
        base_url = f"http://{host}:{node['ollama_port']}/v1"
        provider = "ollama"
    elif ep == "vllm":
        port = port_override or node["vllm_port"]
        base_url = f"http://{host}:{port}/v1"
        provider = "custom"
    elif ep == "vllm-32b":
        port = dgx.get("vllm_32b_port", 30881)
        base_url = f"http://{host}:{port}/v1"
        provider = "custom"
    elif ep == "litellm":
        lh = dgx.get("litellm_host") or _env("HERMES_DGX_LITELLM_HOST")
        lp = dgx.get("litellm_port", 4000)
        if not lh:
            raise ValueError(
                "litellm endpoint requires dgx.litellm_host (run `hermes dgx "
                "setup` or set HERMES_DGX_LITELLM_HOST)"
            )
        base_url = f"http://{lh}:{lp}/v1"
        provider = "custom"
    else:
        raise ValueError(f"Unknown endpoint: {ep!r}")

    dgx["active_endpoint"] = ep

    cfg = load_config()
    if not isinstance(cfg.get("model"), dict):
        cfg["model"] = {}
    cfg["model"]["provider"] = provider
    cfg["model"]["base_url"] = base_url
    to_save = {k: v for k, v in dgx.items() if not k.startswith("_")}
    cfg["dgx"] = to_save
    save_config(cfg)


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------

class DGXNotConfigured(RuntimeError):
    """Raised when a DGX host has not been configured yet."""


def _require_host(node: Dict[str, Any]) -> str:
    host = node.get("host")
    if not host:
        raise DGXNotConfigured(
            "DGX host is not configured. Run `hermes dgx setup` or export "
            "HERMES_DGX_HOST=<ip-or-hostname>."
        )
    return host


def ollama_base(dgx: Dict[str, Any]) -> str:
    node = dgx.get("_active_node") or _resolve_active_node(dgx)
    return f"http://{_require_host(node)}:{node['ollama_port']}"


def vllm_base(dgx: Dict[str, Any]) -> str:
    node = dgx.get("_active_node") or _resolve_active_node(dgx)
    return f"http://{_require_host(node)}:{node['vllm_port']}"


def litellm_base(dgx: Dict[str, Any]) -> Optional[str]:
    """Return the LiteLLM base URL, or None if not configured."""
    lh = dgx.get("litellm_host") or _env("HERMES_DGX_LITELLM_HOST")
    if not lh:
        return None
    lp = dgx.get("litellm_port", 4000)
    return f"http://{lh}:{lp}"
