import os
from unittest.mock import patch


def _make_agent(session_db, *, platform: str, session_id: str):
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
        from run_agent import AIAgent

        return AIAgent(
            api_key="test-key",
            base_url="https://openrouter.ai/api/v1",
            model="test/model",
            quiet_mode=True,
            session_db=session_db,
            session_id=session_id,
            platform=platform,
            skip_context_files=True,
            skip_memory=True,
        )


def test_cli_session_source_env_overrides_cli_platform(tmp_path):
    from hermes_state import SessionDB

    db = SessionDB(db_path=tmp_path / "state.db")
    try:
        with patch.dict(os.environ, {"HERMES_SESSION_SOURCE": "flashbyte-dashboard"}):
            agent = _make_agent(db, platform="cli", session_id="cli-custom-source")
            agent._ensure_db_session()

        row = db.get_session("cli-custom-source")
        assert row is not None
        assert row["source"] == "flashbyte-dashboard"
    finally:
        db.close()


def test_gateway_platform_ignores_cli_source_env(tmp_path):
    from hermes_state import SessionDB

    db = SessionDB(db_path=tmp_path / "state.db")
    try:
        with patch.dict(os.environ, {"HERMES_SESSION_SOURCE": "flashbyte-dashboard"}):
            agent = _make_agent(db, platform="telegram", session_id="telegram-source")
            agent._ensure_db_session()

        row = db.get_session("telegram-source")
        assert row is not None
        assert row["source"] == "telegram"
    finally:
        db.close()
