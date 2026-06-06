import asyncio

from tools import web_tools
from tools.registry import registry


def test_web_extract_schema_exposes_raw_mode_controls():
    props = web_tools.WEB_EXTRACT_SCHEMA["parameters"]["properties"]

    assert "urls" in props
    assert props["urls"]["maxItems"] == 5
    assert props["use_llm_processing"]["type"] == "boolean"
    assert props["use_llm_processing"]["default"] is True
    assert props["min_length"]["type"] == "integer"
    assert props["min_length"]["default"] == web_tools.DEFAULT_MIN_LENGTH_FOR_SUMMARIZATION


def test_web_extract_registry_handler_passes_raw_mode_controls(monkeypatch):
    calls = []

    async def fake_web_extract_tool(urls, format="markdown", use_llm_processing=True, model=None, min_length=0):
        calls.append(
            {
                "urls": urls,
                "format": format,
                "use_llm_processing": use_llm_processing,
                "model": model,
                "min_length": min_length,
            }
        )
        return '{"results": []}'

    monkeypatch.setattr(web_tools, "web_extract_tool", fake_web_extract_tool)
    entry = registry.get_entry("web_extract")
    assert entry is not None

    result = asyncio.run(entry.handler(
        {
            "urls": [
                "https://one.example",
                "https://two.example",
                "https://three.example",
                "https://four.example",
                "https://five.example",
                "https://six.example",
            ],
            "use_llm_processing": False,
            "min_length": 12345,
        }
    ))

    assert result == '{"results": []}'
    assert calls == [
        {
            "urls": [
                "https://one.example",
                "https://two.example",
                "https://three.example",
                "https://four.example",
                "https://five.example",
            ],
            "format": "markdown",
            "use_llm_processing": False,
            "model": None,
            "min_length": 12345,
        }
    ]


def test_web_extract_registry_handler_defaults_to_llm_processing(monkeypatch):
    calls = []

    async def fake_web_extract_tool(urls, format="markdown", use_llm_processing=True, model=None, min_length=0):
        calls.append((urls, format, use_llm_processing, min_length))
        return '{"results": []}'

    monkeypatch.setattr(web_tools, "web_extract_tool", fake_web_extract_tool)
    entry = registry.get_entry("web_extract")
    assert entry is not None

    asyncio.run(entry.handler({"urls": ["https://example.com"], "min_length": "not-an-int"}))
    asyncio.run(entry.handler({"urls": ["https://example.org"], "use_llm_processing": "definitely"}))

    assert calls == [
        (
            ["https://example.com"],
            "markdown",
            True,
            web_tools.DEFAULT_MIN_LENGTH_FOR_SUMMARIZATION,
        ),
        (
            ["https://example.org"],
            "markdown",
            True,
            web_tools.DEFAULT_MIN_LENGTH_FOR_SUMMARIZATION,
        ),
    ]
