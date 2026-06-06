"""CLI commands for the dgx plugin.

Wires ``hermes dgx <subcommand>``:
  setup     — interactive wizard: configure host, ports, default model/endpoint
  status    — GPU memory, running models, endpoint health
  models    — list models available on Ollama and vLLM
  use       — switch active model (updates config.yaml model.default)
  endpoint  — switch active endpoint (ollama / vllm / litellm)
  pull      — pull a model into Ollama on the DGX (streaming)
  rm        — remove a model from Ollama on the DGX
  ps        — show models currently loaded in GPU memory
  run       — run an arbitrary command on the DGX over SSH (streaming)
  push      — rsync local files to the DGX workspace
  doctor    — comprehensive health check: SSH, GPU, endpoints
  watch     — live nvidia-smi refresh until Ctrl+C
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from plugins.dgx._dgx_config import (
    DEFAULT_FORMATIONS,
    DEFAULTS,
    ENDPOINT_LABELS,
    NIM_CATALOG,
    apply_endpoint,
    list_nodes,
    litellm_base,
    load_dgx_config,
    ollama_base,
    save_dgx_config,
    vllm_base,
)


# ---------------------------------------------------------------------------
# argparse wiring
# ---------------------------------------------------------------------------

def register_cli(subparser: argparse.ArgumentParser) -> None:
    subs = subparser.add_subparsers(dest="dgx_command")

    subs.add_parser(
        "setup",
        help="Interactive wizard: configure DGX host, endpoints, default model",
    )

    subs.add_parser(
        "status",
        help="Show GPU memory usage, running models, and endpoint health",
    )

    models_p = subs.add_parser(
        "models",
        help="List and manage models (Ollama, vLLM, HF cache)",
    )
    models_p.add_argument(
        "models_subcommand", nargs="?",
        choices=["add", "rm"], default=None,
        help="add: pull to Ollama or serve HF model via vLLM; rm: remove or stop",
    )
    models_p.add_argument(
        "models_arg", nargs="?", default=None,
        help="Model name or HuggingFace org/name ID; use '--all' with rm to stop all vLLM",
    )
    models_p.add_argument("--port", type=int, default=None,
                          help="vLLM port for 'add' (auto-assigned if omitted)")
    models_p.add_argument("--gpu-mem", type=float, default=0.85, metavar="FRAC",
                          help="GPU memory utilization fraction for vLLM (default: 0.85)")
    models_p.add_argument("--force", "-f", action="store_true",
                          help="Skip confirmation for 'rm'")
    models_p.add_argument("--all", dest="models_all", action="store_true",
                          help="With 'rm': stop all vLLM servers and free GPU memory")

    use_p = subs.add_parser("use", help="Switch the active model")
    use_p.add_argument("model", nargs="?", default=None,
                       help="Model name (e.g. qwen2.5-coder:latest)")
    use_p.add_argument(
        "--endpoint",
        choices=["ollama", "vllm", "vllm-32b", "litellm"],
        default=None,
        help="Endpoint to use for this model (auto-detected if omitted)",
    )
    use_p.add_argument(
        "--for", dest="task", default=None, metavar="TASK",
        help="Describe a task and let the router pick the best model",
    )

    ep_p = subs.add_parser(
        "endpoint",
        help="Switch between ollama / vllm / litellm endpoints",
    )
    ep_p.add_argument(
        "name",
        choices=["ollama", "vllm", "vllm-32b", "litellm"],
        help="Endpoint to activate",
    )

    pull_p = subs.add_parser("pull", help="Pull a model into Ollama on the DGX")
    pull_p.add_argument("model", help="Model name (e.g. nemotron3:70b)")

    rm_p = subs.add_parser("rm", help="Remove a model from Ollama on the DGX")
    rm_p.add_argument("model", help="Model name to remove")
    rm_p.add_argument("--force", "-f", action="store_true", help="Skip confirmation prompt")

    subs.add_parser("ps", help="Show models currently loaded in GPU memory")

    run_p = subs.add_parser("run", help="Run a command on the DGX over SSH (streaming)")
    run_p.add_argument("cmd", nargs=argparse.REMAINDER, help="Command to run")

    push_p = subs.add_parser("push", help="rsync local files to the DGX workspace")
    push_p.add_argument("local", help="Local path to sync")
    push_p.add_argument("remote", nargs="?", default=None,
                        help="Remote destination (default: ~/workspace/)")

    subs.add_parser("doctor", help="Comprehensive health check: SSH, GPU, endpoints")

    watch_p = subs.add_parser("watch", help="Live nvidia-smi refresh until Ctrl+C")
    watch_p.add_argument("--interval", "-n", type=int, default=2,
                         help="Refresh interval in seconds (default: 2)")

    form_p = subs.add_parser("formation", help="Switch to a predefined model formation")
    form_p.add_argument("name", nargs="?", default=None,
                        help=f"Formation name: {', '.join(DEFAULT_FORMATIONS)}")
    form_p.add_argument("--list", "-l", action="store_true", help="List available formations")

    nim_p = subs.add_parser("nim", help="NVIDIA NIM model management for the DGX")
    nim_subs = nim_p.add_subparsers(dest="nim_command")
    nim_subs.add_parser("list", help="List NIM models that fit in 128 GB unified memory")
    nim_deploy_p = nim_subs.add_parser("deploy", help="Generate (and optionally apply) a NIM k8s manifest")
    nim_deploy_p.add_argument("model", help="NIM model ID (e.g. nvidia/nemotron-3-super-120b-a12b)")
    nim_deploy_p.add_argument("--port", type=int, default=8010, help="Host port for the NIM service (default: 8010)")
    nim_deploy_p.add_argument("--apply", action="store_true", help="Apply the manifest to the k3s cluster on nuc")

    route_p = subs.add_parser(
        "route",
        help="Recommend the best formation for a task (smart router)",
    )
    route_p.add_argument("task", help="Task description, e.g. 'implement OAuth2 login'")
    route_p.add_argument("--apply", "-a", action="store_true",
                         help="Apply the recommended formation immediately")
    route_p.add_argument("--check", "-c", action="store_true",
                         help="Probe endpoints before recommending (slower but accurate)")

    node_p = subs.add_parser("node", help="Manage multiple DGX nodes")
    node_subs = node_p.add_subparsers(dest="node_command")
    node_subs.add_parser("list", help="List configured DGX nodes")
    node_add_p = node_subs.add_parser("add", help="Add a new DGX node")
    node_add_p.add_argument("name", help="Node name (e.g. spark1)")
    node_add_p.add_argument("host", help="IP address or hostname")
    node_add_p.add_argument(
        "--ssh-user",
        default=None,
        help="SSH user (default: $HERMES_DGX_SSH_USER, then $USER)",
    )
    node_add_p.add_argument("--ollama-port", type=int, default=11434)
    node_add_p.add_argument("--vllm-port", type=int, default=30800)
    node_use_p = node_subs.add_parser("use", help="Switch the active DGX node")
    node_use_p.add_argument("name", help="Node name to activate")

    subparser.set_defaults(func=dgx_command)


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

def dgx_command(args: argparse.Namespace) -> int:
    sub = getattr(args, "dgx_command", None)
    if not sub:
        print("usage: hermes dgx {setup,status,models,use,endpoint,pull,rm,ps}")
        return 2
    if sub == "setup":
        return _cmd_setup()
    if sub == "status":
        return _cmd_status()
    if sub == "models":
        msub = getattr(args, "models_subcommand", None)
        marg = getattr(args, "models_arg", None)
        if msub == "add":
            return _cmd_models_add(model=marg, port=getattr(args, "port", None),
                                   gpu_mem=getattr(args, "gpu_mem", 0.85))
        if msub == "rm":
            return _cmd_models_rm(
                model=marg,
                force=getattr(args, "force", False),
                all_servers=getattr(args, "models_all", False),
            )
        return _cmd_models()
    if sub == "use":
        if getattr(args, "task", None) and not args.model:
            return _cmd_route(task=args.task, apply=True, check_endpoints=False)
        if not args.model:
            print("usage: hermes dgx use <model>  OR  hermes dgx use --for '<task>'")
            return 2
        return _cmd_use(model=args.model, endpoint=getattr(args, "endpoint", None))
    if sub == "route":
        return _cmd_route(
            task=args.task,
            apply=getattr(args, "apply", False),
            check_endpoints=getattr(args, "check", False),
        )
    if sub == "endpoint":
        return _cmd_endpoint(name=args.name)
    if sub == "pull":
        return _cmd_pull(model=args.model)
    if sub == "rm":
        return _cmd_rm(model=args.model, force=getattr(args, "force", False))
    if sub == "ps":
        return _cmd_ps()
    if sub == "run":
        cmd = " ".join(args.cmd) if args.cmd else ""
        if not cmd:
            print("usage: hermes dgx run <command>")
            return 2
        return _cmd_run(cmd)
    if sub == "push":
        return _cmd_push(local=args.local, remote=args.remote)
    if sub == "doctor":
        return _cmd_doctor()
    if sub == "watch":
        return _cmd_watch(interval=getattr(args, "interval", 2))
    if sub == "formation":
        if getattr(args, "list", False) or args.name is None:
            return _cmd_formation_list()
        return _cmd_formation(name=args.name)
    if sub == "nim":
        nim_sub = getattr(args, "nim_command", None)
        if nim_sub == "list":
            return _cmd_nim_list()
        if nim_sub == "deploy":
            return _cmd_nim_deploy(
                model=args.model,
                port=getattr(args, "port", 8010),
                apply=getattr(args, "apply", False),
            )
        print("usage: hermes dgx nim {list,deploy}")
        return 2
    if sub == "node":
        node_sub = getattr(args, "node_command", None)
        if node_sub == "list":
            return _cmd_node_list()
        if node_sub == "add":
            return _cmd_node_add(
                name=args.name, host=args.host,
                ssh_user=getattr(args, "ssh_user", None),
                ollama_port=getattr(args, "ollama_port", 11434),
                vllm_port=getattr(args, "vllm_port", 30800),
            )
        if node_sub == "use":
            return _cmd_node_use(name=args.name)
        print("usage: hermes dgx node {list,add,use}")
        return 2
    print(f"unknown subcommand: {sub}")
    return 2


# ---------------------------------------------------------------------------
# HTTP helpers (no extra deps — stdlib only)
# ---------------------------------------------------------------------------

def _get_json(url: str, timeout: int = 5) -> Tuple[Optional[Dict], Optional[str]]:
    """GET *url*, return (parsed_json, None) or (None, error_string)."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read()), None
    except urllib.error.URLError as e:
        return None, str(e.reason)
    except Exception as e:
        return None, str(e)


def _check_endpoint(url: str, timeout: int = 4) -> Tuple[bool, str]:
    """Return (reachable, status_string)."""
    _, err = _get_json(url, timeout=timeout)
    return (err is None), (err or "ok")


# ---------------------------------------------------------------------------
# SSH helpers
# ---------------------------------------------------------------------------

def _ssh_run(user: str, host: str, cmd: str, timeout: int = 10) -> Tuple[bool, str]:
    """Run *cmd* on host via SSH. Returns (ok, output_or_error)."""
    try:
        result = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=6", "-o", "BatchMode=yes",
             f"{user}@{host}", cmd],
            capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, (result.stderr.strip() or f"exit {result.returncode}")
    except subprocess.TimeoutExpired:
        return False, "ssh timed out"
    except FileNotFoundError:
        return False, "ssh not found"
    except Exception as e:
        return False, str(e)


def _ssh_stream(user: str, host: str, cmd: str, timeout: int = 300) -> int:
    """Run *cmd* on host via SSH, streaming stdout/stderr to the terminal.

    Returns the remote exit code. Used for long-running commands like
    ``ollama pull`` where real-time progress output matters.
    """
    try:
        result = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=6", "-o", "BatchMode=yes",
             f"{user}@{host}", cmd],
            timeout=timeout,
        )
        return result.returncode
    except subprocess.TimeoutExpired:
        print("(ssh timed out)")
        return 1
    except FileNotFoundError:
        print("ssh not found — is OpenSSH installed?")
        return 1
    except Exception as e:
        print(f"ssh error: {e}")
        return 1


# ---------------------------------------------------------------------------
# HuggingFace cache helpers
# ---------------------------------------------------------------------------

def _list_hf_models(user: str, host: str) -> List[str]:
    """Return HuggingFace model IDs cached in ~/.cache/huggingface/hub/ on the DGX."""
    ok, out = _ssh_run(
        user, host,
        "ls ~/.cache/huggingface/hub/ 2>/dev/null | grep '^models--'",
        timeout=8,
    )
    if not ok or not out:
        return []
    models: List[str] = []
    for line in out.splitlines():
        name = line.strip()
        if name.startswith("models--"):
            name = name[len("models--"):]
            if "--" in name:
                idx = name.index("--")
                models.append(name[:idx] + "/" + name[idx + 2:])
    return models


def _is_hf_model(model: str) -> bool:
    """True if model looks like a HuggingFace org/name ID."""
    return "/" in model


def _find_vllm_bin(user: str, host: str) -> Optional[str]:
    """Return the vllm binary path on the DGX, or None if not installed."""
    ok, out = _ssh_run(
        user, host,
        "command -v vllm 2>/dev/null || ls ~/.local/bin/vllm 2>/dev/null || echo ''",
        timeout=5,
    )
    path = out.strip() if ok else ""
    return path or None


def _next_vllm_port(dgx: Dict[str, Any]) -> int:
    """Return the next unassigned vLLM port.

    Starts at 8900 to avoid the k3s NodePort range (30000-32767) which may
    already have services mapped on the DGX. The configured vllm_port and
    vllm_32b_port are static endpoints; dynamically-served HF models get
    ports from 8900 upward.
    """
    used = {dgx.get("vllm_port", 0), dgx.get("vllm_32b_port", 0)}
    used.update(s.get("port", 0) for s in (dgx.get("vllm_servers") or []))
    port = 8900
    while port in used:
        port += 1
    return port


# ---------------------------------------------------------------------------
# hermes dgx pull
# ---------------------------------------------------------------------------

def _cmd_pull(model: str) -> int:
    dgx = load_dgx_config()
    print(f"Pulling {model} on dgx1 ({dgx['host']}) ...")
    rc = _ssh_stream(dgx["ssh_user"], dgx["host"], f"ollama pull {model}")
    if rc != 0:
        print(f"pull failed (exit {rc})")
    return rc


# ---------------------------------------------------------------------------
# hermes dgx rm
# ---------------------------------------------------------------------------

def _cmd_rm(model: str, force: bool = False) -> int:
    dgx = load_dgx_config()
    if not force:
        try:
            ans = input(f"Remove {model} from {dgx['host']}? [y/N] ").strip().lower()
        except EOFError:
            ans = ""
        if ans not in ("y", "yes"):
            print("aborted")
            return 0
    ok, out = _ssh_run(dgx["ssh_user"], dgx["host"], f"ollama rm {model}")
    if ok:
        print(f"removed {model}")
        return 0
    print(f"rm failed: {out}")
    return 1


# ---------------------------------------------------------------------------
# hermes dgx ps
# ---------------------------------------------------------------------------

def _cmd_ps() -> int:
    dgx = load_dgx_config()
    ok, out = _ssh_run(dgx["ssh_user"], dgx["host"], "ollama ps", timeout=10)
    if not ok:
        print(f"(SSH unavailable: {out})")
        return 1
    lines = out.strip().splitlines()
    # ollama ps prints a header even when empty; detect "nothing loaded" by
    # checking whether there are any data rows after the header.
    data_lines = [l for l in lines[1:] if l.strip()] if len(lines) > 1 else []
    if not data_lines:
        print("No models currently loaded in GPU memory.")
        return 0
    # Pass through ollama's own formatting — it already aligns columns nicely.
    for line in lines:
        print(f"  {line}")
    return 0


# ---------------------------------------------------------------------------
# hermes dgx run
# ---------------------------------------------------------------------------

def _cmd_run(cmd: str) -> int:
    dgx = load_dgx_config()
    rc = _ssh_stream(dgx["ssh_user"], dgx["host"], cmd)
    return rc


# ---------------------------------------------------------------------------
# hermes dgx push
# ---------------------------------------------------------------------------

def _cmd_push(local: str, remote: Optional[str]) -> int:
    dgx = load_dgx_config()
    remote_path = remote or "~/workspace/"
    dest = f"{dgx['ssh_user']}@{dgx['host']}:{remote_path}"
    print(f"Pushing {local}")
    print(f"     → {dest}")
    try:
        result = subprocess.run(
            ["rsync", "-avz", "--progress", local, dest],
            timeout=300,
        )
        return result.returncode
    except FileNotFoundError:
        print("rsync not found — install rsync to use this command")
        return 1
    except subprocess.TimeoutExpired:
        print("rsync timed out")
        return 1
    except Exception as e:
        print(f"push failed: {e}")
        return 1


# ---------------------------------------------------------------------------
# hermes dgx doctor
# ---------------------------------------------------------------------------

_CHECK_OK  = "✓"
_CHECK_FAIL = "✗"


def _cmd_doctor() -> int:
    dgx = load_dgx_config()
    host = dgx["host"]
    user = dgx["ssh_user"]

    print("hermes dgx doctor")
    print("─────────────────")

    failures: List[str] = []

    # --- SSH ---
    ok, out = _ssh_run(user, host, "echo ok", timeout=8)
    sym = _CHECK_OK if ok else _CHECK_FAIL
    print(f"  SSH         {user}@{host}  {sym}")
    if not ok:
        print(f"              ({out})")
        failures.append("ssh")

    # --- GPU ---
    gpu_ok, gpu_out = _ssh_run(
        user, host,
        "nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu "
        "--format=csv,noheader,nounits",
        timeout=10,
    )
    sym = _CHECK_OK if gpu_ok else _CHECK_FAIL
    print(f"  GPU         {sym}")
    if gpu_ok and gpu_out:
        for line in gpu_out.splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 4:
                idx, name, used, total = parts[0], parts[1], parts[2], parts[3]
                try:
                    free_gb = (int(total) - int(used)) / 1024
                    print(f"              GPU {idx}  {name}  {free_gb:.0f} GB free")
                except ValueError:
                    print(f"              GPU {idx}  {name}  {used}/{total} MiB")
    elif not gpu_ok:
        failures.append("gpu")

    # --- Ollama ---
    obase = ollama_base(dgx)
    data, err = _get_json(f"{obase}/api/tags", timeout=4)
    if data is not None:
        n = len(data.get("models", []))
        print(f"  Ollama      {obase}  {_CHECK_OK}  ({n} models)")
    else:
        print(f"  Ollama      {obase}  {_CHECK_FAIL}  ({err})")
        failures.append("ollama")

    # --- vLLM ---
    vbase = vllm_base(dgx)
    data, err = _get_json(f"{vbase}/v1/models", timeout=4)
    if data is not None:
        models = [m["id"] for m in data.get("data", [])]
        print(f"  vLLM        {vbase}  {_CHECK_OK}  ({', '.join(models) or 'no models'})")
    else:
        print(f"  vLLM        {vbase}  {_CHECK_FAIL}  ({err})")
        failures.append("vllm")

    # --- LiteLLM (advisory only — key required) ---
    lbase = litellm_base(dgx)
    lm_ok, lm_msg = _check_endpoint(f"{lbase}/health", timeout=4)
    sym = _CHECK_OK if lm_ok else _CHECK_FAIL
    note = "" if lm_ok else "  (key required — see ~/.hermes/.env)"
    print(f"  LiteLLM     {lbase}  {sym}{note}")

    print()
    # SSH failure is always fatal; all inference endpoints failing is fatal
    inference_ok = not ({"ollama", "vllm"} <= set(failures))
    critical_ok = "ssh" not in failures and inference_ok
    if critical_ok:
        print("All critical checks passed.")
    else:
        print("One or more critical checks FAILED — see above.")
    return 0 if critical_ok else 1


# ---------------------------------------------------------------------------
# hermes dgx watch
# ---------------------------------------------------------------------------

_NVIDIA_SMI_QUERY = (
    "nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu "
    "--format=csv,noheader,nounits"
)


def _print_gpu_lines(out: str) -> None:
    """Render nvidia-smi csv output as formatted GPU rows."""
    for line in out.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 5:
            idx, name, used, total, util = parts[0], parts[1], parts[2], parts[3], parts[4]
            try:
                bar_pct = int(used) / max(int(total), 1)
                bar = "█" * int(bar_pct * 20) + "░" * (20 - int(bar_pct * 20))
                print(f"  GPU {idx}  {name}")
                print(f"  [{bar}] {used}/{total} MiB  ({util}% util)")
            except ValueError:
                print(f"  GPU {idx}  {name}  mem={used}/{total} MiB  util={util}%")


def _cmd_watch(interval: int = 2) -> int:
    """Live-refresh nvidia-smi every *interval* seconds until Ctrl+C."""
    import time

    dgx = load_dgx_config()
    host = dgx["host"]
    user = dgx["ssh_user"]

    try:
        while True:
            ok, out = _ssh_run(user, host, _NVIDIA_SMI_QUERY, timeout=10)
            print("\033[2J\033[H", end="")  # clear screen, move cursor home
            print(f"DGX Spark GPU  {host}  —  Ctrl+C to stop\n")
            if ok and out:
                _print_gpu_lines(out)
            else:
                print(f"  (SSH unavailable: {out})")
            time.sleep(interval)
    except KeyboardInterrupt:
        print()
        return 0


# ---------------------------------------------------------------------------
# hermes dgx status
# ---------------------------------------------------------------------------

def _cmd_status() -> int:
    dgx = load_dgx_config()
    host = dgx["host"]
    user = dgx["ssh_user"]
    active = dgx.get("active_endpoint", "ollama")

    print(f"DGX Spark  {host}  (active endpoint: {active})")
    print()

    # --- GPU via nvidia-smi over SSH ---
    print("GPU memory")
    ok, out = _ssh_run(
        user, host,
        "nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu "
        "--format=csv,noheader,nounits",
    )
    if ok and out:
        _print_gpu_lines(out)
    else:
        print(f"  (SSH unavailable: {out})")
    print()

    # --- Ollama ---
    obase = ollama_base(dgx)
    data, err = _get_json(f"{obase}/api/tags")
    if data is not None:
        models = [m["name"] for m in data.get("models", [])]
        print(f"Ollama  {obase}  ✓  ({len(models)} models loaded)")
        for m in models:
            marker = " ◀ active" if (active == "ollama" and m.startswith(
                dgx.get("default_model", "").split(":")[0])) else ""
            print(f"  {m}{marker}")
    else:
        print(f"Ollama  {obase}  ✗  ({err})")
    print()

    # --- vLLM ---
    vbase = vllm_base(dgx)
    data, err = _get_json(f"{vbase}/v1/models")
    if data is not None:
        models = [m["id"] for m in data.get("data", [])]
        print(f"vLLM    {vbase}  ✓  ({len(models)} models loaded)")
        for m in models:
            marker = " ◀ active" if active == "vllm" else ""
            print(f"  {m}{marker}")
    else:
        print(f"vLLM    {vbase}  ✗  ({err})")
    print()

    # --- LiteLLM ---
    lbase = litellm_base(dgx)
    ok, msg = _check_endpoint(f"{lbase}/health")
    sym = "✓" if ok else "✗"
    marker = " ◀ active" if active == "litellm" else ""
    print(f"LiteLLM {lbase}  {sym}  ({msg}){marker}")

    return 0


# ---------------------------------------------------------------------------
# hermes dgx models / models add / models rm
# ---------------------------------------------------------------------------

def _cmd_models() -> int:
    dgx = load_dgx_config()
    found_any = False

    # --- Ollama ---
    obase = ollama_base(dgx)
    data, err = _get_json(f"{obase}/api/tags")
    if data is not None:
        models = data.get("models", [])
        print(f"Ollama  {obase}")
        for m in models:
            size_gb = m.get("size", 0) / 1e9
            print(f"  {m['name']:<42} {size_gb:.1f} GB")
        if not models:
            print("  (no models — use: hermes dgx pull <name>)")
        found_any = True
    else:
        print(f"Ollama  {obase}  (unreachable: {err})")
    print()

    # --- vLLM servers tracked in config ---
    servers: List[Dict[str, Any]] = dgx.get("vllm_servers") or []
    if servers:
        print("vLLM (tracked servers)")
        for s in servers:
            port = s.get("port", "?")
            model = s.get("model", "?")
            probe, _ = _get_json(f"http://{dgx['host']}:{port}/v1/models", timeout=3)
            status = "✓ running" if probe is not None else "✗ stopped"
            print(f"  {model:<50} :{port}  {status}")
        print()
        print("  hermes dgx models add <hf-id>          — start serving")
        print("  hermes dgx models rm  <hf-id>          — stop + free GPU memory")
        print("  hermes dgx models rm  --all            — stop all vLLM servers")
    else:
        print("vLLM (no tracked servers)")
        print("  hermes dgx models add <org/model-id>  — serve an HF model via vLLM")
    print()

    # --- HuggingFace cache ---
    hf_models = _list_hf_models(dgx["ssh_user"], dgx["host"])
    served_ids = {s.get("model", "") for s in servers}
    if hf_models:
        print(f"HuggingFace cache  (~/.cache/huggingface/hub)  [{len(hf_models)} model(s)]")
        for m in hf_models:
            marker = "  ← serving via vLLM" if m in served_ids else ""
            print(f"  {m}{marker}")
        found_any = True
    else:
        print("HuggingFace cache  (empty)")
        print("  Download: hermes dgx run \"hf download <org/model-id>\"")
    print()

    return 0 if found_any else 1


def _cmd_models_add(model: Optional[str], port: Optional[int] = None,
                    gpu_mem: float = 0.85) -> int:
    """Pull to Ollama (short names) or start vLLM server (HF org/model IDs)."""
    if not model:
        print("usage: hermes dgx models add <model>")
        print("  Ollama : hermes dgx models add deepseek-r1:32b")
        print("  HF/vLLM: hermes dgx models add nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16")
        return 2

    dgx = load_dgx_config()

    if not _is_hf_model(model):
        return _cmd_pull(model)

    # HuggingFace model → serve via vLLM
    vllm_bin = _find_vllm_bin(dgx["ssh_user"], dgx["host"])
    if not vllm_bin:
        print("vllm not found on DGX — install with:")
        print("  hermes dgx run \"pip install --break-system-packages vllm\"")
        return 1

    use_port = port or _next_vllm_port(dgx)
    log_file = f"/tmp/vllm-{use_port}.log"

    # If already tracked, restart it
    servers: List[Dict[str, Any]] = list(dgx.get("vllm_servers") or [])
    existing = next((s for s in servers if s.get("model") == model), None)
    if existing:
        old_port = existing["port"]
        print(f"Restarting vLLM for {model} (was port {old_port}) ...")
        _ssh_run(dgx["ssh_user"], dgx["host"],
                 f"fuser -k {old_port}/tcp 2>/dev/null; pkill -f 'vllm serve {model}' 2>/dev/null; true",
                 timeout=8)
        use_port = old_port  # keep same port on restart
        log_file = f"/tmp/vllm-{use_port}.log"
    else:
        print(f"Starting vLLM for {model} on port {use_port} ...")

    cmd = (
        f"nohup {vllm_bin} serve {model} --host 0.0.0.0 --port {use_port} "
        f"--trust-remote-code --gpu-memory-utilization {gpu_mem:.2f} "
        f"> {log_file} 2>&1 & echo $!"
    )
    ok, pid = _ssh_run(dgx["ssh_user"], dgx["host"], cmd, timeout=12)
    if not ok or not (pid or "").strip().isdigit():
        print(f"Failed to start vLLM: {pid}")
        return 1

    # Persist to config
    servers = [s for s in servers if s.get("model") != model]
    servers.append({"model": model, "port": use_port})
    dgx["vllm_servers"] = servers
    save_dgx_config(dgx)

    print(f"  PID    : {pid.strip()}")
    print(f"  Port   : {use_port}")
    print(f"  Log    : {log_file}")
    print()
    print(f"  Watch  : hermes dgx run \"tail -f {log_file}\"")
    print(f"  Use it : hermes dgx use {model} --endpoint vllm")
    print(f"  (Model loading typically takes 30-120 s)")
    return 0


def _cmd_models_rm(model: Optional[str], force: bool = False,
                   all_servers: bool = False) -> int:
    """Stop a vLLM server (freeing GPU memory) or remove an Ollama model."""
    dgx = load_dgx_config()
    servers: List[Dict[str, Any]] = list(dgx.get("vllm_servers") or [])

    # --all: stop every tracked vLLM server
    if all_servers:
        if not servers:
            print("No tracked vLLM servers to stop.")
            return 0
        if not force:
            try:
                ans = input(f"Stop all {len(servers)} vLLM server(s) and free GPU memory? [y/N] ").strip().lower()
            except EOFError:
                ans = ""
            if ans not in ("y", "yes"):
                print("aborted")
                return 0
        _ssh_run(dgx["ssh_user"], dgx["host"],
                 "pkill -f 'vllm serve' 2>/dev/null; echo done", timeout=10)
        dgx["vllm_servers"] = []
        save_dgx_config(dgx)
        print(f"Stopped all vLLM servers. GPU memory freed.")
        return 0

    if not model:
        print("usage: hermes dgx models rm <model>  OR  hermes dgx models rm --all")
        return 2

    if _is_hf_model(model):
        entry = next((s for s in servers if s.get("model") == model), None)
        if not entry:
            print(f"No tracked vLLM server for {model}.")
            print(f"Try: hermes dgx run \"pkill -f 'vllm serve {model}'\"")
            return 1
        port = entry["port"]
        if not force:
            try:
                ans = input(f"Stop vLLM for {model} (port {port}) and free GPU memory? [y/N] ").strip().lower()
            except EOFError:
                ans = ""
            if ans not in ("y", "yes"):
                print("aborted")
                return 0
        _ssh_run(dgx["ssh_user"], dgx["host"],
                 f"fuser -k {port}/tcp 2>/dev/null; pkill -f 'vllm serve {model}' 2>/dev/null; true",
                 timeout=10)
        dgx["vllm_servers"] = [s for s in servers if s.get("model") != model]
        save_dgx_config(dgx)
        print(f"Stopped vLLM for {model} (port {port}). GPU memory freed.")
        return 0

    return _cmd_rm(model=model, force=force)


# ---------------------------------------------------------------------------
# hermes dgx use <model>
# ---------------------------------------------------------------------------

def _cmd_use(model: str, endpoint: Optional[str] = None) -> int:
    from hermes_cli.config import load_config, save_config

    dgx = load_dgx_config()

    # Auto-detect endpoint from which service has the model, if not specified
    if endpoint is None:
        endpoint = dgx.get("active_endpoint", "ollama")
        obase = ollama_base(dgx)
        data, _ = _get_json(f"{obase}/api/tags")
        if data is not None:
            ollama_models = [m["name"] for m in data.get("models", [])]
            model_root = model.split(":")[0]
            if any(m.startswith(model_root) for m in ollama_models):
                endpoint = "ollama"

    # If the model has a specific vLLM server, route to its port
    port_override: Optional[int] = None
    if _is_hf_model(model):
        servers = dgx.get("vllm_servers") or []
        entry = next((s for s in servers if s.get("model") == model), None)
        if entry:
            port_override = entry["port"]
            if endpoint not in ("vllm", "vllm-32b", "litellm"):
                endpoint = "vllm"

    dgx["default_model"] = model
    apply_endpoint(dgx, endpoint, port_override=port_override)

    # Also update model.default
    cfg = load_config()
    if not isinstance(cfg.get("model"), dict):
        cfg["model"] = {}
    cfg["model"]["default"] = model
    save_config(cfg)

    port_note = f" (port {port_override})" if port_override else ""
    print(f"Active model : {model}")
    print(f"Endpoint     : {endpoint}  ({ENDPOINT_LABELS.get(endpoint, endpoint)}){port_note}")
    return 0


# ---------------------------------------------------------------------------
# hermes dgx endpoint <name>
# ---------------------------------------------------------------------------

def _cmd_endpoint(name: str) -> int:
    dgx = load_dgx_config()
    apply_endpoint(dgx, name)
    label = ENDPOINT_LABELS.get(name, name)
    print(f"Switched to {name}  ({label})")
    _print_model_summary(dgx, name)
    return 0


def _print_model_summary(dgx: Dict[str, Any], endpoint: str) -> None:
    from hermes_cli.config import load_config
    cfg = load_config()
    model = cfg.get("model", {})
    print(f"  base_url : {model.get('base_url', '(not set)')}")
    print(f"  provider : {model.get('provider', '(not set)')}")
    print(f"  model    : {model.get('default', '(not set)')}")


# ---------------------------------------------------------------------------
# hermes dgx route
# ---------------------------------------------------------------------------

_TIER_LABELS = {
    "fast":     "fast     (simple/short task)",
    "standard": "standard (single-concern task)",
    "complex":  "complex  (multi-step or cross-cutting)",
    "review":   "review   (audit / bug hunt / code quality)",
}


def _cmd_route(task: str, apply: bool = False, check_endpoints: bool = False) -> int:
    from plugins.dgx.router import Tier, classify, recommend

    result = recommend(task, check_endpoints=check_endpoints)
    tier_label = _TIER_LABELS.get(result.tier, result.tier)

    print()
    print("Task analysis")
    print("─────────────")
    print(f"  Input      : {task}")
    print(f"  Complexity : {tier_label}")
    print()
    print(f"  Formation  : {result.formation}")
    print(f"  Model      : {result.model}")
    print(f"  Endpoint   : {result.endpoint}  ({ENDPOINT_LABELS.get(result.endpoint, result.endpoint)})")
    if result.fallback:
        dgx = load_dgx_config()
        all_formations = dict(DEFAULTS)
        from plugins.dgx._dgx_config import DEFAULT_FORMATIONS
        all_formations = dict(DEFAULT_FORMATIONS)
        all_formations.update(dgx.get("formations") or {})
        fb_spec = all_formations.get(result.fallback, {})
        print(f"  Fallback   : {result.fallback} ({fb_spec.get('model', '?')} via {fb_spec.get('endpoint', '?')})")
    print()
    print(f"  Why        : {result.reason}")
    print()

    if apply:
        return _cmd_formation(result.formation)

    print(f"  Apply now  : hermes dgx formation {result.formation}")
    print(f"  Or         : hermes dgx route '{task}' --apply")
    return 0


# ---------------------------------------------------------------------------
# hermes dgx setup
# ---------------------------------------------------------------------------

def _prompt(label: str, default: Any) -> str:
    val = input(f"  {label} [{default}]: ").strip()
    return val if val else str(default)


def _probe_ollama(host: str, port: int) -> Tuple[bool, List[str]]:
    url = f"http://{host}:{port}/api/tags"
    data, err = _get_json(url, timeout=4)
    if data is None:
        return False, []
    models = [m["name"] for m in data.get("models", [])]
    return True, models


def _probe_vllm(host: str, port: int) -> Tuple[bool, List[str]]:
    url = f"http://{host}:{port}/v1/models"
    data, err = _get_json(url, timeout=4)
    if data is None:
        return False, []
    models = [m["id"] for m in data.get("data", [])]
    return True, models


def _probe_litellm(host: str, port: int) -> bool:
    url = f"http://{host}:{port}/health"
    ok, _ = _check_endpoint(url, timeout=4)
    return ok


def _cmd_setup() -> int:
    current = load_dgx_config()

    print()
    print("hermes dgx setup")
    print("────────────────")
    print("Configure your DGX Spark inference endpoints.")
    print("Press Enter to accept the current value shown in brackets.")
    print()

    # --- Host / SSH ---
    print("DGX Spark host")
    host = _prompt("IP address", current.get("host", DEFAULTS["host"]))
    ssh_user = _prompt("SSH user", current.get("ssh_user", DEFAULTS["ssh_user"]))
    print()

    # --- Ports ---
    print("Endpoint ports")
    ollama_port = int(_prompt("Ollama port", current.get("ollama_port", DEFAULTS["ollama_port"])))
    vllm_port = int(_prompt("vLLM port", current.get("vllm_port", DEFAULTS["vllm_port"])))
    print()

    # --- Probe endpoints ---
    print("Probing endpoints...")
    ollama_ok, ollama_models = _probe_ollama(host, ollama_port)
    vllm_ok, vllm_models = _probe_vllm(host, vllm_port)

    if ollama_ok:
        summary = f"({len(ollama_models)} models: {', '.join(ollama_models[:3])}{'...' if len(ollama_models) > 3 else ''})"
        print(f"  Ollama  http://{host}:{ollama_port}  ✓  {summary}")
    else:
        print(f"  Ollama  http://{host}:{ollama_port}  ✗  (unreachable — check host/port or VPN)")

    if vllm_ok:
        print(f"  vLLM    http://{host}:{vllm_port}  ✓  ({', '.join(vllm_models)})")
    else:
        print(f"  vLLM    http://{host}:{vllm_port}  ✗  (unreachable)")
    print()

    # --- LiteLLM (optional) ---
    print("LiteLLM proxy (optional — HA pool across all GPU nodes)")
    litellm_host = _prompt("LiteLLM host", current.get("litellm_host", DEFAULTS["litellm_host"]))
    litellm_port = int(_prompt("LiteLLM port", current.get("litellm_port", DEFAULTS["litellm_port"])))
    litellm_ok = _probe_litellm(litellm_host, litellm_port)
    if litellm_ok:
        print(f"  LiteLLM http://{litellm_host}:{litellm_port}  ✓")
    else:
        print(f"  LiteLLM http://{litellm_host}:{litellm_port}  ✗  (unreachable — key required; set OPENAI_API_KEY in ~/.hermes/.env)")
    print()

    # --- Probe vLLM 32B (port 30881) ---
    vllm_32b_port = int(_prompt("vLLM 32B port", current.get("vllm_32b_port", DEFAULTS["vllm_32b_port"])))
    vllm_32b_ok, vllm_32b_models = _probe_vllm(host, vllm_32b_port)
    if vllm_32b_ok:
        print(f"  vLLM 32B http://{host}:{vllm_32b_port}  ✓  ({', '.join(vllm_32b_models)})")
    else:
        print(f"  vLLM 32B http://{host}:{vllm_32b_port}  ✗  (not ready yet — model may still be downloading)")
    print()

    # --- Scan HuggingFace cache ---
    print("HuggingFace cache (scanning...)", end="", flush=True)
    hf_models = _list_hf_models(ssh_user, host)
    if hf_models:
        shown = [m.split("/")[-1] for m in hf_models[:3]]
        extra = len(hf_models) - len(shown)
        summary = ", ".join(shown) + (f" +{extra} more" if extra else "")
        print(f"\r  HF cache: {len(hf_models)} model(s) — {summary}            ")
    else:
        print(f"\r  HF cache: empty — download with: hermes dgx run \"hf download <org/model>\"")
    print()

    # --- Choose default endpoint ---
    available = []
    if ollama_ok:
        available.append("ollama")
    if vllm_ok:
        available.append("vllm")
    if vllm_32b_ok:
        available.append("vllm-32b")
    if litellm_ok:
        available.append("litellm")

    current_ep = current.get("active_endpoint", "ollama")
    if not available:
        print("WARNING: no endpoints are reachable. Saving config anyway.")
        print("         Check your VPN (WireGuard) or DGX host/port settings.")
        chosen_ep = current_ep
    else:
        print("Default endpoint")
        for i, ep in enumerate(available, 1):
            marker = " (current)" if ep == current_ep else ""
            print(f"  {i}) {ep:<8} — {ENDPOINT_LABELS[ep]}{marker}")
        while True:
            raw = input(f"  Choice [{'1' if available else '?'}]: ").strip()
            if not raw and available:
                chosen_ep = available[0]
                break
            try:
                chosen_ep = available[int(raw) - 1]
                break
            except (ValueError, IndexError):
                print("  Enter a number from the list above.")
    print()

    # --- Choose default model ---
    endpoint_models: List[str] = []
    if chosen_ep == "ollama":
        endpoint_models = ollama_models
    elif chosen_ep in ("vllm", "vllm-32b"):
        endpoint_models = vllm_models

    # Combine endpoint models + HF cached models (labelled)
    all_choices: List[Tuple[str, str]] = (
        [(m, "") for m in endpoint_models]
        + [(m, "  ← HF cache (serve with: hermes dgx models add <id>)") for m in hf_models]
    )

    current_model = current.get("default_model", DEFAULTS["default_model"])
    if all_choices:
        print("Default model")
        for i, (m, note) in enumerate(all_choices, 1):
            marker = " (current)" if m == current_model else ""
            print(f"  {i}) {m}{marker}{note}")
        print(f"  Or type a model name directly.")
        raw = input(f"  Choice [{current_model}]: ").strip()
        if not raw:
            chosen_model = current_model
        elif raw.isdigit() and 1 <= int(raw) <= len(all_choices):
            chosen_model = all_choices[int(raw) - 1][0]
        else:
            chosen_model = raw
    else:
        chosen_model = _prompt("Default model", current_model)
    print()

    # --- Save ---
    dgx = {
        "host": host,
        "ssh_user": ssh_user,
        "ollama_port": ollama_port,
        "vllm_port": vllm_port,
        "litellm_host": litellm_host,
        "litellm_port": litellm_port,
        "active_endpoint": chosen_ep,
        "default_model": chosen_model,
    }
    save_dgx_config(dgx)
    apply_endpoint(dgx, chosen_ep)

    # Update model.default too
    from hermes_cli.config import load_config, save_config
    cfg = load_config()
    if not isinstance(cfg.get("model"), dict):
        cfg["model"] = {}
    cfg["model"]["default"] = chosen_model
    save_config(cfg)

    print("Configuration saved.")
    print()
    print(f"  DGX host  : {host}")
    print(f"  Endpoint  : {chosen_ep}  ({ENDPOINT_LABELS.get(chosen_ep, chosen_ep)})")
    print(f"  Model     : {chosen_model}")
    print()
    print("Next steps:")
    print("  hermes dgx status    — verify GPU and endpoint health")
    print("  hermes dgx models    — browse available models")
    print("  hermes               — start chatting")
    return 0


# ---------------------------------------------------------------------------
# hermes dgx formation
# ---------------------------------------------------------------------------

def _cmd_formation_list() -> int:
    dgx = load_dgx_config()
    all_formations = dict(DEFAULT_FORMATIONS)
    all_formations.update(dgx.get("formations") or {})
    active_model = dgx.get("default_model", "")
    print("Available formations:")
    for name, spec in all_formations.items():
        marker = " ◀ active" if spec["model"] == active_model else ""
        print(f"  {name:<14} {spec['model']:<35} via {spec['endpoint']}{marker}")
    return 0


def _cmd_formation(name: str) -> int:
    dgx = load_dgx_config()
    all_formations = dict(DEFAULT_FORMATIONS)
    all_formations.update(dgx.get("formations") or {})

    if name not in all_formations:
        available = ", ".join(all_formations)
        print(f"Unknown formation {name!r}. Available: {available}")
        return 1

    spec = all_formations[name]
    model = spec["model"]
    endpoint = spec["endpoint"]

    apply_endpoint(dgx, endpoint)

    from hermes_cli.config import load_config, save_config
    cfg = load_config()
    if not isinstance(cfg.get("model"), dict):
        cfg["model"] = {}
    cfg["model"]["default"] = model
    dgx["default_model"] = model
    dgx["active_endpoint"] = endpoint
    to_save = {k: v for k, v in dgx.items() if not k.startswith("_")}
    cfg["dgx"] = to_save
    save_config(cfg)

    print(f"Formation : {name}")
    print(f"Model     : {model}")
    print(f"Endpoint  : {endpoint}  ({ENDPOINT_LABELS.get(endpoint, endpoint)})")
    return 0


# ---------------------------------------------------------------------------
# hermes dgx nim
# ---------------------------------------------------------------------------

def _cmd_nim_list() -> int:
    print(f"{'MODEL ID':<50} {'PARAMS':<14} {'TIER'}")
    print("─" * 80)
    for m in NIM_CATALOG:
        print(f"  {m['id']:<48} {m['params']:<14} {m['tier']}")
    print()
    print("Deploy: hermes dgx nim deploy <model-id>")
    print("Needs:  NVIDIA_API_KEY in ~/.hermes/.env or NGC_API_KEY secret in k3s")
    return 0


def _cmd_nim_deploy(model: str, port: int = 8010, apply: bool = False) -> int:
    import re

    slug = re.sub(r"[^a-z0-9]", "-", model.lower()).strip("-")
    cfg = load_dgx_config()
    k8s_host = cfg.get("litellm_host") or os.environ.get("HERMES_DGX_K8S_HOST")
    k8s_user = cfg.get("ssh_user") or os.environ.get("HERMES_DGX_SSH_USER") or os.environ.get("USER")
    dgx_host = cfg.get("host")
    if apply and not (k8s_host and k8s_user):
        print(
            "nim deploy --apply needs a host to ssh into for `kubectl apply`. "
            "Set dgx.litellm_host (or HERMES_DGX_K8S_HOST) and dgx.ssh_user."
        )
        return 1
    if not dgx_host:
        print(
            "DGX host is not configured. Run `hermes dgx setup` or export "
            "HERMES_DGX_HOST=<ip-or-hostname>."
        )
        return 1

    manifest = f"""\
apiVersion: v1
kind: Service
metadata:
  name: nim-{slug}
  namespace: inference
spec:
  selector:
    app: nim-{slug}
  ports:
    - port: 8000
      nodePort: {port}
  type: NodePort
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nim-{slug}
  namespace: inference
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nim-{slug}
  template:
    metadata:
      labels:
        app: nim-{slug}
    spec:
      nodeSelector:
        kubernetes.io/hostname: dgx1
      tolerations:
        - key: gpu
          operator: Exists
          effect: NoSchedule
      runtimeClassName: nvidia
      containers:
        - name: nim
          image: nvcr.io/nim/{model}:latest
          env:
            - name: NVIDIA_VISIBLE_DEVICES
              value: all
            - name: NGC_API_KEY
              valueFrom:
                secretKeyRef:
                  name: ngc-api-key
                  key: key
          ports:
            - containerPort: 8000
          resources:
            limits:
              nvidia.com/gpu: 1
"""
    print(manifest)

    if apply:
        tmp = f"/tmp/nim-{slug}.yaml"
        ok, out = _ssh_run(k8s_user, k8s_host,
                           f"cat > {tmp} << 'YAML'\n{manifest}\nYAML\nkubectl apply -f {tmp}",
                           timeout=30)
        if ok:
            print(out)
            print(f"\nNIM endpoint will be at http://{dgx_host}:{port}/v1")
            return 0
        print(f"Apply failed: {out}")
        return 1
    else:
        print(f"# To apply: hermes dgx nim deploy {model} --apply")
        if k8s_user and k8s_host:
            print(f"# Or:       ssh {k8s_user}@{k8s_host} kubectl apply -f <above-manifest>")
        else:
            print("# Or:       kubectl apply -f <above-manifest>  (from the k8s control host)")
    return 0


# ---------------------------------------------------------------------------
# hermes dgx node
# ---------------------------------------------------------------------------

def _cmd_node_list() -> int:
    dgx = load_dgx_config()
    nodes = list_nodes(dgx)
    active = dgx.get("active_node", "default")
    print(f"{'NAME':<12} {'HOST':<18} {'SSH USER':<12} OLLAMA  vLLM")
    print("─" * 60)
    for nd in nodes:
        marker = " ◀" if nd["_key"] == active else ""
        print(f"  {nd['_key']:<10} {nd['host']:<18} {nd['ssh_user']:<12} "
              f"{nd['ollama_port']:<7} {nd['vllm_port']}{marker}")
    return 0


def _cmd_node_add(name: str, host: str, ssh_user: Optional[str] = None,
                  ollama_port: int = 11434, vllm_port: int = 30800) -> int:
    dgx = load_dgx_config()
    resolved_user = (
        ssh_user
        or os.environ.get("HERMES_DGX_SSH_USER")
        or os.environ.get("USER")
        or "dgx"
    )
    nodes = dict(dgx.get("nodes") or {})
    nodes[name] = {
        "host": host,
        "ssh_user": resolved_user,
        "ollama_port": ollama_port,
        "vllm_port": vllm_port,
        "name": f"DGX Spark ({name})",
    }
    dgx["nodes"] = nodes
    save_dgx_config(dgx)
    print(f"Added node {name!r} → {host}")
    return 0


def _cmd_node_use(name: str) -> int:
    dgx = load_dgx_config()
    nodes = dgx.get("nodes") or {}
    if name != "default" and name not in nodes:
        available = list(nodes) or ["default"]
        print(f"Unknown node {name!r}. Available: {', '.join(available)}")
        return 1
    dgx["active_node"] = name
    # Also update the flat host/ports for backwards compat
    if name in nodes:
        nd = nodes[name]
        dgx["host"] = nd["host"]
        dgx["ssh_user"] = (
            nd.get("ssh_user")
            or os.environ.get("HERMES_DGX_SSH_USER")
            or os.environ.get("USER")
            or "dgx"
        )
        dgx["ollama_port"] = nd.get("ollama_port", 11434)
        dgx["vllm_port"] = nd.get("vllm_port", 30800)
        apply_endpoint(dgx, dgx.get("active_endpoint", "ollama"))
    save_dgx_config(dgx)
    print(f"Active node → {name}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser(prog="hermes dgx")
    register_cli(parser)
    ns = parser.parse_args()
    sys.exit(dgx_command(ns))
