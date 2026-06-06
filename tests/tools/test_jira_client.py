"""Tests for plugins/jira/client.py — JiraClient, ADF helpers, auth utilities."""

import base64
import json
from unittest.mock import MagicMock, patch

import pytest

from plugins.jira.client import (
    JiraAPIError,
    JiraAuthRequiredError,
    JiraClient,
    adf_to_text,
    make_basic_token,
    text_to_adf,
)
from plugins.jira.tools import _issue_url


# ---------------------------------------------------------------------------
# make_basic_token
# ---------------------------------------------------------------------------

class TestMakeBasicToken:
    def test_encodes_email_and_token(self):
        token = make_basic_token("user@example.com", "mytoken")
        decoded = base64.b64decode(token).decode("utf-8")
        assert decoded == "user@example.com:mytoken"

    def test_output_is_ascii(self):
        token = make_basic_token("a@b.com", "t")
        assert token.isascii()


# ---------------------------------------------------------------------------
# _issue_url
# ---------------------------------------------------------------------------

class TestIssueUrl:
    def test_valid_self_link(self):
        issue = {
            "self": "https://myco.atlassian.net/rest/api/3/issue/10001",
            "key": "PROJ-1",
        }
        assert _issue_url(issue) == "https://myco.atlassian.net/browse/PROJ-1"

    def test_empty_self_returns_empty(self):
        assert _issue_url({"self": "", "key": "PROJ-1"}) == ""

    def test_missing_self_returns_empty(self):
        assert _issue_url({"key": "PROJ-1"}) == ""

    def test_missing_key_returns_empty(self):
        assert _issue_url({"self": "https://myco.atlassian.net/rest/api/3/issue/10001"}) == ""

    def test_malformed_self_returns_empty(self):
        # only one slash — split gives fewer than 3 parts
        assert _issue_url({"self": "broken", "key": "PROJ-1"}) == ""


# ---------------------------------------------------------------------------
# text_to_adf
# ---------------------------------------------------------------------------

class TestTextToAdf:
    def test_single_paragraph(self):
        adf = text_to_adf("Hello world")
        assert adf["type"] == "doc"
        assert adf["version"] == 1
        assert len(adf["content"]) == 1
        assert adf["content"][0]["type"] == "paragraph"
        assert adf["content"][0]["content"][0]["text"] == "Hello world"

    def test_double_newline_creates_two_paragraphs(self):
        adf = text_to_adf("First paragraph\n\nSecond paragraph")
        assert len(adf["content"]) == 2
        assert adf["content"][0]["content"][0]["text"] == "First paragraph"
        assert adf["content"][1]["content"][0]["text"] == "Second paragraph"

    def test_empty_string_returns_empty_paragraph(self):
        adf = text_to_adf("")
        assert adf["type"] == "doc"
        assert len(adf["content"]) == 1

    def test_code_block_detection(self):
        adf = text_to_adf("```python\nprint('hi')\n```")
        assert adf["content"][0]["type"] == "codeBlock"
        assert adf["content"][0]["attrs"]["language"] == "python"


# ---------------------------------------------------------------------------
# adf_to_text
# ---------------------------------------------------------------------------

class TestAdfToText:
    def test_simple_doc(self):
        adf = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Hello world"}],
                }
            ],
        }
        assert adf_to_text(adf) == "Hello world"

    def test_non_dict_returns_string(self):
        assert adf_to_text("plain text") == "plain text"
        assert adf_to_text(None) == ""
        assert adf_to_text(42) == "42"

    def test_nested_content(self):
        adf = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Line one"},
                    ],
                },
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Line two"},
                    ],
                },
            ],
        }
        result = adf_to_text(adf)
        assert "Line one" in result
        assert "Line two" in result


# ---------------------------------------------------------------------------
# JiraClient — auth error on missing credentials
# ---------------------------------------------------------------------------

class TestJiraClientAuthError:
    def test_raises_auth_required_when_not_authenticated(self, monkeypatch):
        from hermes_cli.auth import AuthError

        def _raise_auth_error():
            raise AuthError("not authenticated", provider="jira", code="jira_auth_missing")

        monkeypatch.setattr(
            "plugins.jira.client.resolve_jira_runtime_credentials",
            _raise_auth_error,
        )
        with pytest.raises(JiraAuthRequiredError):
            JiraClient()


# ---------------------------------------------------------------------------
# JiraClient.request — HTTP layer behaviour
# ---------------------------------------------------------------------------

def _make_client(domain="myco.atlassian.net", email="user@example.com", basic_token="tok") -> JiraClient:
    """Build a JiraClient with a fake runtime, bypassing auth."""
    client = object.__new__(JiraClient)
    client._runtime = {
        "domain": domain,
        "email": email,
        "basic_token": basic_token,
        "base_url": f"https://{domain}/rest/api/3",
    }
    return client


class TestJiraClientRequest:
    def _mock_response(self, status_code: int, body: dict | None = None):
        resp = MagicMock()
        resp.status_code = status_code
        resp.content = b"ok" if body is not None else b""
        resp.headers = {"content-type": "application/json"}
        resp.json.return_value = body or {}
        resp.text = json.dumps(body) if body else ""
        return resp

    def test_get_returns_json(self):
        client = _make_client()
        resp = self._mock_response(200, {"id": "1", "key": "PROJ-1"})
        with patch("plugins.jira.client.httpx.request", return_value=resp):
            result = client.request("GET", "/issue/PROJ-1")
        assert result["key"] == "PROJ-1"

    def test_204_returns_success(self):
        client = _make_client()
        resp = MagicMock()
        resp.status_code = 204
        resp.content = b""
        with patch("plugins.jira.client.httpx.request", return_value=resp):
            result = client.request("PUT", "/issue/PROJ-1")
        assert result["success"] is True

    def test_401_raises_auth_required(self):
        client = _make_client()
        resp = self._mock_response(401, {"errorMessages": ["Unauthorized"]})
        with patch("plugins.jira.client.httpx.request", return_value=resp):
            with pytest.raises(JiraAuthRequiredError):
                client.request("GET", "/issue/PROJ-1")

    def test_400_raises_api_error_with_status(self):
        client = _make_client()
        resp = self._mock_response(400, {"errorMessages": ["Field 'foo' is required"]})
        with patch("plugins.jira.client.httpx.request", return_value=resp):
            with pytest.raises(JiraAPIError) as exc_info:
                client.request("POST", "/issue")
        assert exc_info.value.status_code == 400

    def test_404_raises_api_error(self):
        client = _make_client()
        resp = self._mock_response(404, {"errorMessages": ["Issue does not exist"]})
        with patch("plugins.jira.client.httpx.request", return_value=resp):
            with pytest.raises(JiraAPIError):
                client.request("GET", "/issue/BAD-999")


# ---------------------------------------------------------------------------
# JiraClient convenience methods
# ---------------------------------------------------------------------------

class TestJiraClientMethods:
    def _mock_response(self, body: dict):
        resp = MagicMock()
        resp.status_code = 200
        resp.content = b"ok"
        resp.headers = {"content-type": "application/json"}
        resp.json.return_value = body
        return resp

    def test_create_issue_builds_correct_payload(self):
        client = _make_client()
        captured = {}

        def fake_request(method, url, **kwargs):
            captured["json"] = kwargs.get("json")
            resp = MagicMock()
            resp.status_code = 201
            resp.content = b'{"key":"PROJ-1","id":"10001","self":"http://x"}'
            resp.headers = {"content-type": "application/json"}
            resp.json.return_value = {"key": "PROJ-1", "id": "10001", "self": "http://x"}
            return resp

        with patch("plugins.jira.client.httpx.request", side_effect=fake_request):
            result = client.create_issue("PROJ", "Bug", "Something is broken", description="Details here")

        fields = captured["json"]["fields"]
        assert fields["project"]["key"] == "PROJ"
        assert fields["issuetype"]["name"] == "Bug"
        assert fields["summary"] == "Something is broken"
        # Description must be ADF
        assert fields["description"]["type"] == "doc"
        assert result["key"] == "PROJ-1"

    def test_search_passes_jql(self):
        client = _make_client()
        captured_params = {}

        def fake_request(method, url, **kwargs):
            captured_params.update(kwargs.get("params") or {})
            resp = MagicMock()
            resp.status_code = 200
            resp.content = b'{"issues":[],"total":0}'
            resp.headers = {"content-type": "application/json"}
            resp.json.return_value = {"issues": [], "total": 0}
            return resp

        with patch("plugins.jira.client.httpx.request", side_effect=fake_request):
            client.search("project=PROJ AND status=Open", max_results=10)

        assert captured_params["jql"] == "project=PROJ AND status=Open"
        assert captured_params["maxResults"] == 10

    def test_add_comment_converts_to_adf(self):
        client = _make_client()
        captured = {}

        def fake_request(method, url, **kwargs):
            captured["json"] = kwargs.get("json")
            resp = MagicMock()
            resp.status_code = 201
            resp.content = b'{"id":"10001","created":"2026-01-01"}'
            resp.headers = {"content-type": "application/json"}
            resp.json.return_value = {"id": "10001", "created": "2026-01-01"}
            return resp

        with patch("plugins.jira.client.httpx.request", side_effect=fake_request):
            client.add_comment("PROJ-1", "This is my comment")

        assert captured["json"]["body"]["type"] == "doc"
        assert captured["json"]["body"]["content"][0]["content"][0]["text"] == "This is my comment"
