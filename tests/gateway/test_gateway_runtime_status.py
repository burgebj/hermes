import json

from gateway import status


def test_write_runtime_status_drops_platforms_from_previous_gateway_run(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    state_path = tmp_path / "gateway_state.json"
    state_path.write_text(
        json.dumps(
            {
                "kind": "hermes-gateway",
                "pid": 999999,
                "start_time": 123,
                "gateway_state": "running",
                "platforms": {
                    "feishu": {
                        "state": "connected",
                        "updated_at": "2026-05-15T00:00:00+00:00",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    status.write_runtime_status(gateway_state="running")

    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert payload["gateway_state"] == "running"
    assert payload["platforms"] == {}


def test_write_runtime_status_preserves_platforms_for_same_gateway_run(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))

    status.write_runtime_status(platform="telegram", platform_state="connected")
    status.write_runtime_status(gateway_state="running")

    payload = json.loads((tmp_path / "gateway_state.json").read_text(encoding="utf-8"))
    assert payload["gateway_state"] == "running"
    assert payload["platforms"]["telegram"]["state"] == "connected"
