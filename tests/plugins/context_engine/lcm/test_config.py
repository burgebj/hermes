from plugins.context_engine.lcm.config import LcmConfig


def test_lcm_package_exports():
    """All public types should be importable from plugins.context_engine.lcm."""
    from plugins.context_engine.lcm import (
        LcmConfig,
        LcmEngine,
        CompactionAction,
        ContextEntry,
        SummaryDag,
        SummaryNode,
        MessageId,
        ImmutableStore,
    )
    assert LcmConfig is not None
    assert LcmEngine is not None
    assert CompactionAction is not None
    assert ContextEntry is not None
    assert SummaryDag is not None
    assert SummaryNode is not None
    assert MessageId is not None
    assert ImmutableStore is not None


def test_defaults():
    cfg = LcmConfig()
    assert cfg.enabled is True
    assert cfg.tau_soft == 0.50
    assert cfg.tau_hard == 0.85
    assert cfg.deterministic_target == 512
    assert cfg.protect_last_n == 4
    assert cfg.summary_model == ""


def test_from_dict():
    d = {
        "enabled": "true",
        "tau_soft": "0.6",
        "tau_hard": "0.9",
        "deterministic_target": "1024",
        "protect_last_n": "8",
        "summary_model": "claude-haiku-3",
    }
    cfg = LcmConfig.from_dict(d)
    assert cfg.enabled is True
    assert cfg.tau_soft == 0.6
    assert cfg.tau_hard == 0.9
    assert cfg.deterministic_target == 1024
    assert cfg.protect_last_n == 8
    assert cfg.summary_model == "claude-haiku-3"


def test_from_dict_partial_overrides():
    d = {"enabled": "1", "tau_soft": "0.75"}
    cfg = LcmConfig.from_dict(d)
    assert cfg.enabled is True
    assert cfg.tau_soft == 0.75
    # unspecified keys keep defaults
    assert cfg.tau_hard == 0.85
    assert cfg.deterministic_target == 512
    assert cfg.protect_last_n == 4
    assert cfg.summary_model == ""
