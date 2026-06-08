"""Outbound payload routing for the Feishu adapter.

Feishu 'post' / 'lark_md' elements do not render GFM markdown tables (the
message arrives blank), so table content used to be downgraded to plain text.
The interactive-card 'markdown' component (card schema 2.0) renders tables, so
``_build_outbound_payload`` now routes table content to a card. Non-table
content is unchanged: markdown -> post, plain -> text.
"""
import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

_repo = str(Path(__file__).resolve().parents[2])
if _repo not in sys.path:
    sys.path.insert(0, _repo)


def _ensure_feishu_mocks():
    if importlib.util.find_spec("lark_oapi") is None and "lark_oapi" not in sys.modules:
        mod = MagicMock()
        for name in ("lark_oapi", "lark_oapi.api.im.v1",
                     "lark_oapi.event", "lark_oapi.event.callback_type"):
            sys.modules.setdefault(name, mod)
    if importlib.util.find_spec("aiohttp") is None and "aiohttp" not in sys.modules:
        aio = MagicMock()
        sys.modules.setdefault("aiohttp", aio)
        sys.modules.setdefault("aiohttp.web", aio.web)


_ensure_feishu_mocks()

from gateway.platforms.feishu import FeishuAdapter

_TABLE = (
    "## GPU usage\n\n"
    "| host | util | mem |\n"
    "|---|---|---|\n"
    "| mx005 | 7.9% | 95.6% |\n"
    "| mx006 | 11.4% | 96.6% |\n"
)


def _route(content):
    # _build_outbound_payload does not touch self; call it unbound.
    return FeishuAdapter._build_outbound_payload(None, content)


def test_table_content_routes_to_interactive_card():
    msg_type, payload = _route(_TABLE)
    assert msg_type == "interactive"
    card = json.loads(payload)
    assert card["schema"] == "2.0"
    element = card["body"]["elements"][0]
    assert element["tag"] == "markdown"
    # The full markdown (table included) is preserved verbatim in the card.
    assert element["content"] == _TABLE
    assert "| host |" in element["content"]


def test_table_embedded_in_prose_still_routes_to_card():
    content = "Here is the report:\n\n" + _TABLE + "\nDone."
    msg_type, payload = _route(content)
    assert msg_type == "interactive"
    assert json.loads(payload)["body"]["elements"][0]["content"] == content


def test_non_table_markdown_still_routes_to_post():
    msg_type, _ = _route("**bold** and a list:\n- one\n- two")
    assert msg_type == "post"


def test_plain_text_stays_text():
    msg_type, payload = _route("just a plain sentence")
    assert msg_type == "text"
    assert json.loads(payload) == {"text": "just a plain sentence"}
