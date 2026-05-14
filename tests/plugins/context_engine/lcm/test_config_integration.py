"""Test that LCM config integrates with hermes config system."""


def test_lcm_defaults_in_config():
    """LCM section should exist in DEFAULT_CONFIG with correct defaults."""
    from hermes_cli.config import DEFAULT_CONFIG
    assert "lcm" in DEFAULT_CONFIG
    lcm = DEFAULT_CONFIG["lcm"]
    assert lcm["enabled"] is True
    assert lcm["tau_soft"] == 0.50
    assert lcm["tau_hard"] == 0.85
    assert lcm["deterministic_target"] == 512
    assert lcm["protect_last_n"] == 4


def test_lcm_config_from_hermes_config():
    """LcmConfig.from_dict should work with hermes config format."""
    from plugins.context_engine.lcm.config import LcmConfig
    from hermes_cli.config import DEFAULT_CONFIG
    lcm_dict = DEFAULT_CONFIG.get("lcm", {})
    config = LcmConfig.from_dict(lcm_dict)
    assert config.enabled is True
    assert config.tau_soft == 0.50
