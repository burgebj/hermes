from hermes_cli.inventory import ConfigContext


def test_cli_model_picker_requests_uncapped_model_inventory(monkeypatch):
    """The CLI /model picker must load the full selectable model list.

    build_models_payload() may expose total_models larger than len(models), but
    the prompt-toolkit picker can only select entries present in models. Passing
    max_models=50 reproduces #35443 by making models past index 49 unreachable.
    """
    from cli import HermesCLI

    seen = {}
    ctx = ConfigContext(
        current_provider="nous",
        current_model="model-1",
        current_base_url="",
        user_providers={},
        custom_providers=[],
    )
    providers = [
        {
            "slug": "nous",
            "name": "Nous",
            "is_current": True,
            "is_user_defined": False,
            "models": [f"model-{i}" for i in range(75)],
            "total_models": 75,
            "source": "hermes",
        }
    ]

    def fake_build_models_payload(received_ctx, *, max_models=50, **kwargs):
        seen["ctx"] = received_ctx
        seen["max_models"] = max_models
        return {"providers": providers, "model": "model-1", "provider": "nous"}

    opened = {}

    def fake_open_model_picker(self, received_providers, current_model, current_provider, **kwargs):
        opened["providers"] = received_providers
        opened["current_model"] = current_model
        opened["current_provider"] = current_provider

    monkeypatch.setattr("hermes_cli.inventory.load_picker_context", lambda: ctx)
    monkeypatch.setattr("hermes_cli.inventory.build_models_payload", fake_build_models_payload)
    monkeypatch.setattr(HermesCLI, "_open_model_picker", fake_open_model_picker)

    cli = HermesCLI(compact=True, max_turns=1)
    cli.model = "model-1"
    cli.provider = "nous"

    cli._handle_model_switch("/model")

    assert seen["ctx"].current_provider == "nous"
    assert seen["ctx"].current_model == "model-1"
    assert seen["max_models"] is None
    assert opened["providers"][0]["models"][-1] == "model-74"
