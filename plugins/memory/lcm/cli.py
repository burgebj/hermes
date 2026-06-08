"""CLI commands for LCM (Long-term Context Memory) plugin.

Handles: hermes memory lcm start | stop | status | logs | setup
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from hermes_constants import get_hermes_home

CONTAINER_NAME = "hermes-lcm"
VOLUME_NAME = "hermes-lcm-data"
SERVICE_PORT = "18732"
IMAGE_NAME = "ghcr.io/nousresearch/hermes-lcm:latest"


def _container_exists() -> bool:
    """Check if the LCM container exists (regardless of running state)."""
    result = subprocess.run(
        ["docker", "ps", "-a", "-q", "-f", f"name={CONTAINER_NAME}"],
        capture_output=True, text=True,
    )
    return bool(result.stdout.strip())


def _container_running() -> bool:
    """Check if the LCM container is currently running."""
    result = subprocess.run(
        ["docker", "ps", "-q", "-f", f"name={CONTAINER_NAME}"],
        capture_output=True, text=True,
    )
    return bool(result.stdout.strip())


def _service_url() -> str:
    """Return the LCM service URL."""
    return os.getenv("LCM_SERVICE_URL", f"http://localhost:{SERVICE_PORT}")


def _build_env_args(provider: str = "ollama") -> list[str]:
    """Build -e arguments for docker run based on embed provider."""
    args = [f"BUTTER_LCM_EMBED_PROVIDER={provider}"]

    if provider == "ollama":
        args.append(f"OLLAMA_BASE_URL={os.getenv('OLLAMA_BASE_URL', 'http://host.docker.internal:11434')}")
    elif provider == "openai":
        args.append(f"OPENAI_API_KEY={os.getenv('OPENAI_API_KEY', '')}")
        args.append(f"OPENAI_EMBED_MODEL={os.getenv('OPENAI_EMBED_MODEL', 'text-embedding-3-small')}")
    elif provider == "azure":
        args.append(f"AZURE_OPENAI_ENDPOINT={os.getenv('AZURE_OPENAI_ENDPOINT', '')}")
        args.append(f"AZURE_OPENAI_KEY={os.getenv('AZURE_OPENAI_KEY', '')}")
        args.append(f"AZURE_EMBED_MODEL={os.getenv('AZURE_EMBED_MODEL', '')}")
    elif provider == "bedrock":
        args.append(f"AWS_REGION={os.getenv('AWS_REGION', 'us-east-1')}")
        args.append(f"BEDROCK_EMBED_MODEL={os.getenv('BEDROCK_EMBED_MODEL', 'amazon.titan-embed-text-v1')}")

    return args


def lcm_command(args) -> None:
    """Handler for ``hermes memory lcm`` subcommands."""
    subcmd = getattr(args, "lcm_subcommand", None)

    if subcmd == "start":
        cmd_start(args)
    elif subcmd == "stop":
        cmd_stop(args)
    elif subcmd == "status":
        cmd_status(args)
    elif subcmd == "logs":
        cmd_logs(args)
    elif subcmd == "setup":
        cmd_setup(args)
    else:
        print("Usage: hermes memory lcm start|stop|status|logs|setup")
        sys.exit(1)


def cmd_start(args) -> None:
    """Start the LCM Docker container."""
    provider = getattr(args, "embed_provider", "ollama")

    if _container_running():
        print(f"LCM container '{CONTAINER_NAME}' is already running.")
        return

    env_args: list[str] = []
    for env_arg in _build_env_args(provider):
        env_args.extend(["-e", env_arg])

    # Add Ollama host mapping if using Ollama
    extra_hosts = []
    if provider == "ollama":
        extra_hosts = ["--add-host=host.docker.internal:host-gateway"]

    docker_cmd = [
        "docker", "run", "-d",
        "--name", CONTAINER_NAME,
        "-p", f"127.0.0.1:{SERVICE_PORT}:{SERVICE_PORT}",
        "-v", f"{VOLUME_NAME}:/app/data",
        *extra_hosts,
        *env_args,
        "--restart", "unless-stopped",
        IMAGE_NAME,
    ]

    if args.embed_provider == "local" and args.dockerfile:
        docker_cmd = [
            "docker", "run", "-d",
            "--name", CONTAINER_NAME,
            "-p", f"127.0.0.1:{SERVICE_PORT}:{SERVICE_PORT}",
            "-v", f"{VOLUME_NAME}:/app/data",
            "--add-host=host.docker.internal:host-gateway",
            "-e", f"BUTTER_LCM_EMBED_PROVIDER=ollama",
            "-e", "OLLAMA_BASE_URL=http://host.docker.internal:11434",
            "--restart", "unless-stopped",
            "-f", args.dockerfile,
            ".",
        ]

    try:
        subprocess.run(docker_cmd, check=True, capture_output=True, text=True)
        print(f"LCM container started on port {SERVICE_PORT}.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to start LCM container: {e.stderr.decode() if e.stderr else e}")
        sys.exit(1)


def cmd_stop(args) -> None:
    """Stop the LCM Docker container."""
    if not _container_exists():
        print(f"LCM container '{CONTAINER_NAME}' does not exist.")
        return

    try:
        subprocess.run(["docker", "stop", CONTAINER_NAME], check=True, capture_output=True, text=True)
        print(f"LCM container stopped.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to stop container: {e}")
        sys.exit(1)


def cmd_status(args) -> None:
    """Show LCM container status and service health."""
    exists = _container_exists()
    running = _container_running()

    if not exists:
        print(f"LCM container '{CONTAINER_NAME}' does not exist. Run: hermes memory lcm start")
        return

    print(f"Container: {'running' if running else 'stopped'}")

    if running:
        # Show container info
        result = subprocess.run(
            ["docker", "ps", "-f", f"name={CONTAINER_NAME}", "--format", "{{.Status}}"],
            capture_output=True, text=True,
        )
        if result.stdout.strip():
            print(f"Docker status: {result.stdout.strip()}")

        # Check service health
        import httpx
        try:
            resp = httpx.get(f"{_service_url()}/health", timeout=5)
            resp.raise_for_status()
            data = resp.json()
            print(f"Service health: {data}")
        except Exception as e:
            print(f"Service health check failed: {e}")

        # Show stats
        try:
            resp = httpx.get(f"{_service_url()}/stats", timeout=5)
            resp.raise_for_status()
            data = resp.json()
            print(f"Stats — total: {data.get('total')}, active: {data.get('active')}, vectors: {data.get('vectors')}")
        except Exception:
            pass
    else:
        print(f"Container exists but is not running. Start with: hermes memory lcm start")


def cmd_logs(args) -> None:
    """Tail LCM container logs."""
    if not _container_exists():
        print(f"LCM container '{CONTAINER_NAME}' does not exist.")
        sys.exit(1)

    tail_args = ["docker", "logs"]
    if args.tail:
        tail_args.extend(["--tail", str(args.tail)])
    if args.follow:
        tail_args.append("-f")
    tail_args.append(CONTAINER_NAME)

    try:
        subprocess.run(tail_args)
    except KeyboardInterrupt:
        pass


def cmd_setup(args) -> None:
    """Guided setup wizard for LCM."""
    print("=== LCM Memory Plugin Setup ===\n")

    # Check Docker
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True, text=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Docker is required but not found. Please install Docker first.")
        sys.exit(1)

    # Choose embed provider
    print("Select embedding provider:")
    print("  1) Ollama (local, free, default)")
    print("  2) OpenAI (requires API key)")
    print("  3) Azure OpenAI (requires endpoint + key)")
    print("  4) AWS Bedrock (requires AWS credentials)")

    choice = input("\nChoice [1]: ").strip() or "1"
    provider_map = {"1": "ollama", "2": "openai", "3": "azure", "4": "bedrock"}
    provider = provider_map.get(choice, "ollama")

    env_lines = [f"BUTTER_LCM_EMBED_PROVIDER={provider}"]

    if provider == "ollama":
        ollama_url = input("Ollama URL [http://host.docker.internal:11434]: ").strip()
        if ollama_url:
            env_lines.append(f"OLLAMA_BASE_URL={ollama_url}")
        else:
            env_lines.append("OLLAMA_BASE_URL=http://host.docker.internal:11434")

    elif provider == "openai":
        api_key = input("OpenAI API Key: ").strip()
        if api_key:
            env_lines.append(f"OPENAI_API_KEY={api_key}")
        model = input("Embedding model [text-embedding-3-small]: ").strip()
        if model:
            env_lines.append(f"OPENAI_EMBED_MODEL={model}")

    elif provider == "azure":
        endpoint = input("Azure OpenAI Endpoint: ").strip()
        if endpoint:
            env_lines.append(f"AZURE_OPENAI_ENDPOINT={endpoint}")
        key = input("Azure OpenAI API Key: ").strip()
        if key:
            env_lines.append(f"AZURE_OPENAI_KEY={key}")
        model = input("Deployment name: ").strip()
        if model:
            env_lines.append(f"AZURE_EMBED_MODEL={model}")

    elif provider == "bedrock":
        region = input("AWS Region [us-east-1]: ").strip() or "us-east-1"
        env_lines.append(f"AWS_REGION={region}")
        model = input("Bedrock model [amazon.titan-embed-text-v1]: ").strip() or "amazon.titan-embed-text-v1"
        env_lines.append(f"BEDROCK_EMBED_MODEL={model}")

    # Write to .env
    hermes_home = get_hermes_home()
    env_path = hermes_home / ".env"
    existing = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                existing[k.strip()] = v.strip()

    for line in env_lines:
        if "=" in line:
            k, v = line.split("=", 1)
            existing[k.strip()] = v.strip()

    with env_path.open("w") as f:
        for k, v in existing.items():
            f.write(f"{k}={v}\n")

    print(f"\nConfig saved to {env_path}")
    print("To enable LCM, add to ~/.hermes/config.yaml:")
    print("  memory:")
    print("    provider: lcm")
    print("\nThen run: hermes memory lcm start")


def register_cli(subparser) -> None:
    """Build the ``hermes memory lcm`` argparse subcommand tree.

    Called by the plugin CLI registration system during argparse setup.
    The *subparser* is the parser for ``hermes memory lcm``.
    """

    subs = subparser.add_subparsers(dest="lcm_subcommand")

    # start
    start_parser = subs.add_parser("start", help="Start the LCM Docker container")
    start_parser.add_argument(
        "--embed-provider", "-e",
        choices=["ollama", "openai", "azure", "bedrock", "local"],
        default="ollama",
        dest="embed_provider",
        help="Embedding provider (default: ollama)",
    )
    start_parser.add_argument(
        "--dockerfile", "-f",
        help="Path to local Dockerfile (for 'local' embed provider build)",
        dest="dockerfile",
    )

    # stop
    subs.add_parser("stop", help="Stop the LCM Docker container")

    # status
    subs.add_parser("status", help="Show LCM container status and service health")

    # logs
    logs_parser = subs.add_parser("logs", help="Tail LCM container logs")
    logs_parser.add_argument("--tail", "-n", type=int, default=100, help="Number of lines to show")
    logs_parser.add_argument("--follow", "-f", action="store_true", help="Follow log output")

    # setup
    subs.add_parser("setup", help="Guided LCM setup wizard")
