"""Test that docker_extra_args is bridged from terminal config to gateway env."""
from pathlib import Path


class TestDockerExtraArgsGatewayBridge:
    """Verify TERMINAL_DOCKER_EXTRA_ARGS mapping exists in the terminal env bridge."""

    def test_docker_extra_args_key_exists_in_source(self):
        """The docker_extra_args → TERMINAL_DOCKER_EXTRA_ARGS mapping must exist."""
        gateway_run = Path(__file__).resolve().parents[1] / "gateway" / "run.py"
        source = gateway_run.read_text()
        assert '"docker_extra_args": "TERMINAL_DOCKER_EXTRA_ARGS"' in source, (
            "docker_extra_args must be mapped to TERMINAL_DOCKER_EXTRA_ARGS "
            "in the terminal env bridge so gateway sessions inherit it from config"
        )
