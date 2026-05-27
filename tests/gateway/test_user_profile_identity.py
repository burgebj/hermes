from types import SimpleNamespace

from gateway.config import HomeChannel, Platform
from gateway.run import GatewayRunner
from gateway.session import SessionSource


def _runner(home_chat_id="5215514706713@s.whatsapp.net"):
    runner = object.__new__(GatewayRunner)
    home = HomeChannel(platform=Platform.WHATSAPP, chat_id=home_chat_id, name="Home")
    runner.config = SimpleNamespace(get_home_channel=lambda platform: home if platform == Platform.WHATSAPP else None)
    return runner


def test_gateway_skips_global_user_profile_for_non_owner_whatsapp_lid_dm():
    runner = _runner()
    source = SessionSource(
        platform=Platform.WHATSAPP,
        chat_id="230893885100129@lid",
        chat_type="dm",
        user_id="230893885100129@lid",
        user_name="Jorge",
    )

    assert runner._should_skip_user_profile_for_source(
        source=source,
        session_key="agent:main:whatsapp:dm:5215510253360",
        user_config={},
    ) is True


def test_gateway_keeps_global_user_profile_for_owner_whatsapp_dm_canonical_key():
    runner = _runner()
    source = SessionSource(
        platform=Platform.WHATSAPP,
        chat_id="96370627199010@lid",
        chat_type="dm",
        user_id="96370627199010@lid",
        user_name="Eliacim",
    )

    assert runner._should_skip_user_profile_for_source(
        source=source,
        session_key="agent:main:whatsapp:dm:5215514706713",
        user_config={},
    ) is False


def test_gateway_keeps_global_user_profile_for_owner_in_group_canonical_key():
    runner = _runner()
    source = SessionSource(
        platform=Platform.WHATSAPP,
        chat_id="5215520435780-1448604752@g.us",
        chat_type="group",
        user_id="96370627199010@lid",
        user_name="Eliacim",
    )

    assert runner._should_skip_user_profile_for_source(
        source=source,
        session_key="agent:main:whatsapp:group:5215520435780-1448604752@g.us:5215514706713",
        user_config={},
    ) is False


def test_gateway_skips_global_user_profile_when_no_home_match_even_if_user_name_known():
    runner = _runner()
    source = SessionSource(
        platform=Platform.WHATSAPP,
        chat_id="144492044791824@lid",
        chat_type="dm",
        user_id="144492044791824@lid",
        user_name="Jessica",
    )

    assert runner._should_skip_user_profile_for_source(
        source=source,
        session_key="agent:main:whatsapp:dm:5215540990699",
        user_config={},
    ) is True
