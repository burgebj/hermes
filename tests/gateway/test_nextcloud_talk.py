"""Tests for the Nextcloud Talk gateway platform adapter (Phase 2: User-API)."""
import json
import os
import pytest


def _make_config(**overrides):
    """Factory for PlatformConfig with NC Talk User-API settings."""
    from gateway.config import PlatformConfig
    extra = {
        "nextcloud_url": "https://nc.example.com",
        "username": "hermes",
        "app_password_env": "NC_TALK_APP_PASSWORD_TEST",
        "conversations": [{"token": "test123", "alias": "testuser"}],
        "edit_ack_into_response": True,
        "show_status_updates": True,
        "poll_timeout": 30,
        "channel_aliases": {},
    }
    extra.update(overrides)
    return PlatformConfig(enabled=True, extra=extra)


def test_talk_user_client_constructs():
    from gateway.platforms.nextcloud_talk import TalkUserClient
    client = TalkUserClient(
        base_url="https://nc.example.com",
        username="hermes",
        password="testpass",
    )
    assert client._auth == ("hermes", "testpass")
    assert client._base_url == "https://nc.example.com"


def test_talk_user_client_strips_trailing_slash():
    from gateway.platforms.nextcloud_talk import TalkUserClient
    client = TalkUserClient(
        base_url="https://nc.example.com/",
        username="hermes",
        password="testpass",
    )
    assert client._base_url == "https://nc.example.com"


import pytest


@pytest.mark.anyio
async def test_client_send_message_success():
    from gateway.platforms.nextcloud_talk import TalkUserClient

    class FakeResponse:
        status_code = 201
        text = ""
        def json(self):
            return {"ocs": {"data": {"id": 42}}}

    class FakeClient:
        def __init__(self):
            self.last_url = None
            self.last_data = None

        async def post(self, url, **kwargs):
            self.last_url = url
            self.last_data = kwargs.get("data", {})
            return FakeResponse()

        async def aclose(self):
            pass

    fake = FakeClient()
    client = TalkUserClient(
        base_url="https://nc.example.com",
        username="hermes",
        password="testpass",
        http_client=fake,
    )
    ok, msg_id, err = await client.send_message("tok1", "Hello")
    assert ok is True
    assert msg_id == 42
    assert err is None
    assert fake.last_url.endswith("/chat/tok1")
    assert fake.last_data["message"] == "Hello"


@pytest.mark.anyio
async def test_client_send_message_with_reply():
    from gateway.platforms.nextcloud_talk import TalkUserClient

    class FakeResponse:
        status_code = 201
        text = ""
        def json(self):
            return {"ocs": {"data": {"id": 99}}}

    class FakeClient:
        def __init__(self):
            self.last_data = None

        async def post(self, url, **kwargs):
            self.last_data = kwargs.get("data", {})
            return FakeResponse()

        async def aclose(self):
            pass

    fake = FakeClient()
    client = TalkUserClient(
        base_url="https://nc.example.com",
        username="hermes",
        password="testpass",
        http_client=fake,
    )
    ok, msg_id, err = await client.send_message("tok1", "Reply!", reply_to=55)
    assert ok is True
    assert fake.last_data.get("replyTo") == 55


@pytest.mark.anyio
async def test_client_edit_message_success():
    from gateway.platforms.nextcloud_talk import TalkUserClient

    class FakeResponse:
        status_code = 200
        text = ""
        def json(self):
            return {}

    class FakeClient:
        def __init__(self):
            self.last_url = None
            self.last_data = None

        async def put(self, url, **kwargs):
            self.last_url = url
            self.last_data = kwargs.get("data", {})
            return FakeResponse()

        async def aclose(self):
            pass

    fake = FakeClient()
    client = TalkUserClient(
        base_url="https://nc.example.com",
        username="hermes",
        password="testpass",
        http_client=fake,
    )
    ok, err = await client.edit_message("tok1", 42, "New text")
    assert ok is True
    assert err is None
    assert fake.last_url.endswith("/chat/tok1/42")
    assert fake.last_data["message"] == "New text"


@pytest.mark.anyio
async def test_client_edit_message_forbidden():
    from gateway.platforms.nextcloud_talk import TalkUserClient

    class FakeResponse:
        status_code = 403
        text = "Forbidden"
        def json(self):
            return {}

    class FakeClient:
        async def put(self, url, **kwargs):
            return FakeResponse()

        async def aclose(self):
            pass

    fake = FakeClient()
    client = TalkUserClient(
        base_url="https://nc.example.com",
        username="hermes",
        password="testpass",
        http_client=fake,
    )
    ok, err = await client.edit_message("tok1", 42, "New text")
    assert ok is False
    assert "403" in err


@pytest.mark.anyio
async def test_client_get_messages_returns_new():
    from gateway.platforms.nextcloud_talk import TalkUserClient

    messages = [{"id": 101, "message": "hi"}, {"id": 102, "message": "there"}]

    class FakeResponse:
        status_code = 200
        def json(self):
            return {"ocs": {"data": messages}}

    class FakeClient:
        def __init__(self):
            self.last_url = None
            self.last_params = None

        async def get(self, url, **kwargs):
            self.last_url = url
            self.last_params = kwargs.get("params", {})
            return FakeResponse()

        async def aclose(self):
            pass

    fake = FakeClient()
    client = TalkUserClient(
        base_url="https://nc.example.com",
        username="hermes",
        password="testpass",
        http_client=fake,
    )
    status, msgs = await client.get_messages("tok1", last_known_id=100)
    assert status == 200
    assert msgs == messages
    assert fake.last_params["lastKnownMessageId"] == 100
    assert fake.last_params["lookIntoFuture"] == 1


@pytest.mark.anyio
async def test_client_get_messages_304_no_new():
    from gateway.platforms.nextcloud_talk import TalkUserClient

    class FakeResponse:
        status_code = 304
        def json(self):
            return {}

    class FakeClient:
        async def get(self, url, **kwargs):
            return FakeResponse()

        async def aclose(self):
            pass

    fake = FakeClient()
    client = TalkUserClient(
        base_url="https://nc.example.com",
        username="hermes",
        password="testpass",
        http_client=fake,
    )
    status, msgs = await client.get_messages("tok1", last_known_id=100)
    assert status == 304
    assert msgs == []


@pytest.mark.anyio
async def test_client_join_conversation():
    from gateway.platforms.nextcloud_talk import TalkUserClient

    class FakeResponse:
        status_code = 200
        text = ""
        def json(self):
            return {"ocs": {"data": {}}}

    class FakeClient:
        def __init__(self):
            self.last_url = None

        async def post(self, url, **kwargs):
            self.last_url = url
            return FakeResponse()

        async def aclose(self):
            pass

    fake = FakeClient()
    client = TalkUserClient(
        base_url="https://nc.example.com",
        username="hermes",
        password="testpass",
        http_client=fake,
    )
    ok, err = await client.join_conversation("tok1")
    assert ok is True
    assert err is None
    assert fake.last_url.endswith("/room/tok1/participants/active")


@pytest.mark.anyio
async def test_client_list_conversations():
    from gateway.platforms.nextcloud_talk import TalkUserClient

    convos = [{"token": "abc", "displayName": "Room 1"}, {"token": "def", "displayName": "Room 2"}]

    class FakeResponse:
        status_code = 200
        text = ""
        def json(self):
            return {"ocs": {"data": convos}}

    class FakeClient:
        def __init__(self):
            self.last_url = None

        async def get(self, url, **kwargs):
            self.last_url = url
            return FakeResponse()

        async def aclose(self):
            pass

    fake = FakeClient()
    client = TalkUserClient(
        base_url="https://nc.example.com",
        username="hermes",
        password="testpass",
        http_client=fake,
    )
    ok, rooms, err = await client.list_conversations()
    assert ok is True
    assert rooms == convos
    assert err is None
    assert fake.last_url.endswith("/room")


@pytest.mark.anyio
async def test_get_latest_message_id():
    from gateway.platforms.nextcloud_talk import TalkUserClient

    messages = [{"id": 200, "message": "last"}]

    class FakeResponse:
        status_code = 200
        def json(self):
            return {"ocs": {"data": messages}}

    class FakeClient:
        async def get(self, url, **kwargs):
            return FakeResponse()

        async def aclose(self):
            pass

    fake = FakeClient()
    client = TalkUserClient(
        base_url="https://nc.example.com",
        username="hermes",
        password="testpass",
        http_client=fake,
    )
    latest_id = await client.get_latest_message_id("tok1")
    assert latest_id == 200


@pytest.mark.anyio
async def test_get_latest_message_id_empty_room():
    from gateway.platforms.nextcloud_talk import TalkUserClient

    class FakeResponse:
        status_code = 200
        def json(self):
            return {"ocs": {"data": []}}

    class FakeClient:
        async def get(self, url, **kwargs):
            return FakeResponse()

        async def aclose(self):
            pass

    fake = FakeClient()
    client = TalkUserClient(
        base_url="https://nc.example.com",
        username="hermes",
        password="testpass",
        http_client=fake,
    )
    latest_id = await client.get_latest_message_id("tok1")
    assert latest_id == 0


@pytest.mark.anyio
async def test_client_upload_file(tmp_path):
    from gateway.platforms.nextcloud_talk import TalkUserClient

    test_file = tmp_path / "test.txt"
    test_file.write_bytes(b"hello world")

    class FakeResponse:
        status_code = 201
        text = ""

    class FakeClient:
        def __init__(self):
            self.last_url = None
            self.last_content = None

        async def put(self, url, **kwargs):
            self.last_url = url
            self.last_content = kwargs.get("content")
            return FakeResponse()

        async def aclose(self):
            pass

    fake = FakeClient()
    client = TalkUserClient(
        base_url="https://nc.example.com",
        username="hermes",
        password="testpass",
        http_client=fake,
    )
    ok, err = await client.upload_file("uploads/test.txt", str(test_file))
    assert ok is True
    assert err is None
    assert "remote.php/dav/files/hermes/uploads/test.txt" in fake.last_url
    assert fake.last_content == b"hello world"


@pytest.mark.anyio
async def test_client_share_file_to_chat():
    from gateway.platforms.nextcloud_talk import TalkUserClient

    class FakeResponse:
        status_code = 200
        text = ""
        def json(self):
            return {"ocs": {"data": {"id": 77}}}

    class FakeClient:
        def __init__(self):
            self.last_url = None
            self.last_data = None

        async def post(self, url, **kwargs):
            self.last_url = url
            self.last_data = kwargs.get("data", {})
            return FakeResponse()

        async def aclose(self):
            pass

    fake = FakeClient()
    client = TalkUserClient(
        base_url="https://nc.example.com",
        username="hermes",
        password="testpass",
        http_client=fake,
    )
    ok, share_id, err = await client.share_file_to_chat("tok1", "/uploads/test.txt")
    assert ok is True
    assert share_id == 77
    assert err is None
    assert "files_sharing/api/v1/shares" in fake.last_url
    assert fake.last_data["shareType"] == "10"
    assert fake.last_data["shareWith"] == "tok1"


@pytest.mark.anyio
async def test_client_download_file(tmp_path):
    from gateway.platforms.nextcloud_talk import TalkUserClient

    class FakeResponse:
        status_code = 200
        content = b"file content here"
        text = ""

    class FakeClient:
        def __init__(self):
            self.last_url = None

        async def get(self, url, **kwargs):
            self.last_url = url
            return FakeResponse()

        async def aclose(self):
            pass

    fake = FakeClient()
    client = TalkUserClient(
        base_url="https://nc.example.com",
        username="hermes",
        password="testpass",
        http_client=fake,
    )
    local_path = str(tmp_path / "downloaded.txt")
    ok, saved_path, err = await client.download_file("remote/file.txt", local_path)
    assert ok is True
    assert saved_path == local_path
    assert err is None
    assert "remote.php/dav/files/hermes/remote/file.txt" in fake.last_url
    with open(local_path, "rb") as f:
        assert f.read() == b"file content here"

# ---------------------------------------------------------------------------
# Task 2.1 – _parse_user_message
# ---------------------------------------------------------------------------

SAMPLE_USER_MSG = {
    "id": 1773, "token": "svvac3ix",
    "actorType": "users", "actorId": "niko",
    "actorDisplayName": "Niko Syring",
    "message": "erkläre mir X",
    "messageParameters": {},
    "systemMessage": "", "timestamp": 1744178400,
}

SAMPLE_MSG_WITH_IMAGE = {
    **SAMPLE_USER_MSG, "id": 1774,
    "message": "{file}",
    "messageParameters": {
        "file": {
            "type": "file", "id": "199419", "name": "screenshot.png",
            "path": "screenshot.png", "link": "https://nc.example.com/s/abc",
            "mimetype": "image/png", "size": "292392",
            "width": "693", "height": "521",
        }
    },
}


def test_parse_user_message_text_only():
    from gateway.platforms.nextcloud_talk import _parse_user_message
    parsed = _parse_user_message(SAMPLE_USER_MSG, own_user_id="hermes")
    assert parsed is not None
    assert parsed["text"] == "erkläre mir X"
    assert parsed["message_id"] == 1773
    assert parsed["chat_id"] == "svvac3ix"
    assert parsed["user_id"] == "niko"
    assert parsed["user_name"] == "Niko Syring"
    assert parsed["attachment"] is None


def test_parse_user_message_with_image():
    from gateway.platforms.nextcloud_talk import _parse_user_message
    parsed = _parse_user_message(SAMPLE_MSG_WITH_IMAGE, own_user_id="hermes")
    assert parsed is not None
    assert parsed["attachment"]["mimetype"] == "image/png"
    assert parsed["attachment"]["name"] == "screenshot.png"
    assert parsed["attachment"]["id"] == "199419"


def test_parse_user_message_skips_own():
    from gateway.platforms.nextcloud_talk import _parse_user_message
    msg = {**SAMPLE_USER_MSG, "actorId": "hermes"}
    assert _parse_user_message(msg, own_user_id="hermes") is None


def test_parse_user_message_skips_system():
    from gateway.platforms.nextcloud_talk import _parse_user_message
    msg = {**SAMPLE_USER_MSG, "systemMessage": "user_added"}
    assert _parse_user_message(msg, own_user_id="hermes") is None


def test_parse_user_message_text_with_attachment():
    from gateway.platforms.nextcloud_talk import _parse_user_message
    msg = {**SAMPLE_MSG_WITH_IMAGE, "message": "was ist hier falsch? {file}"}
    parsed = _parse_user_message(msg, own_user_id="hermes")
    assert "was ist hier falsch?" in parsed["text"]
    assert "{file}" not in parsed["text"]
    assert parsed["attachment"] is not None


def test_parse_user_message_unicode():
    from gateway.platforms.nextcloud_talk import _parse_user_message
    msg = {**SAMPLE_USER_MSG, "message": "Grüße 🚀 日本語"}
    parsed = _parse_user_message(msg, own_user_id="hermes")
    assert parsed["text"] == "Grüße 🚀 日本語"
# ---------------------------------------------------------------------------
# Task 3.1 – NextcloudTalkPlatform __init__ (User API)
# ---------------------------------------------------------------------------


def test_adapter_init_user_api(monkeypatch):
    monkeypatch.setenv("NC_TALK_APP_PASSWORD_TEST", "testpass123")
    from gateway.platforms.nextcloud_talk import NextcloudTalkPlatform
    adapter = NextcloudTalkPlatform(_make_config())
    assert adapter._username == "hermes"
    assert adapter._password == "testpass123"
    assert adapter._nextcloud_url == "https://nc.example.com"
    assert adapter._conversations == [{"token": "test123", "alias": "testuser"}]
    assert adapter._edit_ack_into_response is True
    assert adapter._show_status_updates is True
    assert adapter._poll_timeout == 30


def test_adapter_init_raises_on_missing_password(monkeypatch):
    monkeypatch.delenv("NC_TALK_APP_PASSWORD_TEST", raising=False)
    from gateway.platforms.nextcloud_talk import NextcloudTalkPlatform
    with pytest.raises(ValueError, match="NC_TALK_APP_PASSWORD_TEST"):
        NextcloudTalkPlatform(_make_config())


def test_adapter_init_raises_on_empty_conversations(monkeypatch):
    monkeypatch.setenv("NC_TALK_APP_PASSWORD_TEST", "testpass123")
    from gateway.platforms.nextcloud_talk import NextcloudTalkPlatform
    with pytest.raises(ValueError, match="conversations"):
        NextcloudTalkPlatform(_make_config(conversations=[]))


def test_adapter_init_merges_conversation_aliases(monkeypatch):
    monkeypatch.setenv("NC_TALK_APP_PASSWORD_TEST", "testpass123")
    from gateway.platforms.nextcloud_talk import NextcloudTalkPlatform
    adapter = NextcloudTalkPlatform(_make_config(
        conversations=[
            {"token": "abc", "alias": "alice"},
            {"token": "def", "alias": "bob"},
        ],
        channel_aliases={"manual": "xyz"},
    ))
    assert adapter._resolve_chat_identifier("alice") == "abc"
    assert adapter._resolve_chat_identifier("bob") == "def"
    assert adapter._resolve_chat_identifier("manual") == "xyz"


# ---------------------------------------------------------------------------
# Task 3.2 – connect / disconnect / _poll_loop
# ---------------------------------------------------------------------------

import asyncio


@pytest.mark.asyncio
async def test_connect_creates_client_and_tasks(monkeypatch):
    monkeypatch.setenv("NC_TALK_APP_PASSWORD_TEST", "testpass123")
    from gateway.platforms.nextcloud_talk import NextcloudTalkPlatform
    adapter = NextcloudTalkPlatform(_make_config(
        conversations=[{"token": "room1", "alias": "r1"}],
    ))

    class FakeClient:
        joined = []

        async def list_conversations(self):
            return True, [{"token": "room1"}], None

        async def join_conversation(self, token):
            self.joined.append(token)
            return True, None

        async def get_latest_message_id(self, token):
            return 100

        async def get_messages(self, *a, **kw):
            await asyncio.sleep(999)  # block forever
            return 304, []

        async def close(self):
            pass

    fake_client = FakeClient()
    adapter._client = fake_client

    result = await adapter.connect()
    assert result is True
    assert len(adapter._poll_tasks) == 1
    await adapter.disconnect()
    assert adapter._poll_tasks == []


# ---------------------------------------------------------------------------
# Task 3.3 – send() + edit_message()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_adapter_send_text(monkeypatch):
    monkeypatch.setenv("NC_TALK_APP_PASSWORD_TEST", "testpass123")
    from gateway.platforms.nextcloud_talk import NextcloudTalkPlatform
    adapter = NextcloudTalkPlatform(_make_config())
    sent = []

    class FakeClient:
        async def send_message(self, token, message, reply_to=None):
            sent.append((token, message))
            return True, 42, None

        async def close(self):
            pass

    adapter._client = FakeClient()
    result = await adapter.send("room1", "hello")
    assert result.success is True
    assert result.message_id == "42"
    assert sent == [("room1", "hello")]


@pytest.mark.asyncio
async def test_adapter_edit_message(monkeypatch):
    monkeypatch.setenv("NC_TALK_APP_PASSWORD_TEST", "testpass123")
    from gateway.platforms.nextcloud_talk import NextcloudTalkPlatform
    adapter = NextcloudTalkPlatform(_make_config())

    class FakeClient:
        async def edit_message(self, token, msg_id, text):
            self.edited = (token, msg_id, text)
            return True, None

        async def close(self):
            pass

    fc = FakeClient()
    adapter._client = fc
    result = await adapter.edit_message("room1", "42", "updated")
    assert result.success is True
    assert fc.edited == ("room1", 42, "updated")


# ---------------------------------------------------------------------------
# Task 3.4 – _on_poll_message
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_on_poll_message_text_with_ack(monkeypatch):
    monkeypatch.setenv("NC_TALK_APP_PASSWORD_TEST", "testpass123")
    from gateway.platforms.nextcloud_talk import NextcloudTalkPlatform
    adapter = NextcloudTalkPlatform(_make_config(
        show_status_updates=True,
        conversations=[{"token": "room1", "alias": "test"}],
    ))
    timeline = []

    class FakeClient:
        async def send_message(self, token, message, reply_to=None):
            timeline.append(("send", message))
            return True, 100, None

        async def close(self):
            pass

    adapter._client = FakeClient()

    async def fake_handle(event):
        timeline.append(("runtime", event.text))

    monkeypatch.setattr(adapter, "handle_message", fake_handle)
    msg = {
        "id": 50, "token": "room1", "actorType": "users",
        "actorId": "niko", "actorDisplayName": "Niko",
        "message": "hi", "messageParameters": {}, "systemMessage": "",
    }
    await adapter._on_poll_message(msg, "room1")
    assert timeline[0] == ("send", "\u23f3 denke nach...")
    assert timeline[1] == ("runtime", "hi")


@pytest.mark.asyncio
async def test_on_poll_message_skips_own(monkeypatch):
    monkeypatch.setenv("NC_TALK_APP_PASSWORD_TEST", "testpass123")
    from gateway.platforms.nextcloud_talk import NextcloudTalkPlatform
    adapter = NextcloudTalkPlatform(_make_config(
        conversations=[{"token": "room1", "alias": "test"}],
    ))
    forwarded = []

    async def fake_handle(event):
        forwarded.append(event)

    monkeypatch.setattr(adapter, "handle_message", fake_handle)
    adapter._client = type("C", (), {"close": lambda s: None})()
    msg = {
        "id": 50, "token": "room1", "actorType": "users",
        "actorId": "hermes", "actorDisplayName": "Hermes",
        "message": "own msg", "messageParameters": {}, "systemMessage": "",
    }
    await adapter._on_poll_message(msg, "room1")
    assert forwarded == []


@pytest.mark.asyncio
async def test_on_poll_message_command(monkeypatch):
    monkeypatch.setenv("NC_TALK_APP_PASSWORD_TEST", "testpass123")
    from gateway.platforms.nextcloud_talk import NextcloudTalkPlatform
    adapter = NextcloudTalkPlatform(_make_config(
        conversations=[{"token": "room1", "alias": "test"}],
        show_status_updates=False,
    ))
    sent = []

    class FakeClient:
        async def send_message(self, token, message, reply_to=None):
            sent.append(message)
            return True, 1, None

        async def close(self):
            pass

    adapter._client = FakeClient()

    class FakeStore:
        def reset_session(self, key):
            pass

    adapter._session_store = FakeStore()
    forwarded = []

    async def fake_handle(event):
        forwarded.append(event)

    monkeypatch.setattr(adapter, "handle_message", fake_handle)
    msg = {
        "id": 60, "token": "room1", "actorType": "users",
        "actorId": "niko", "actorDisplayName": "Niko",
        "message": "/reset", "messageParameters": {}, "systemMessage": "",
    }
    await adapter._on_poll_message(msg, "room1")
    assert forwarded == []
    assert any("zurückgesetzt" in s.lower() for s in sent)


# ---------------------------------------------------------------------------
# Task 3.5 – Ack-edit integration in send()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_edits_pending_ack(monkeypatch):
    monkeypatch.setenv("NC_TALK_APP_PASSWORD_TEST", "testpass123")
    from gateway.platforms.nextcloud_talk import NextcloudTalkPlatform
    adapter = NextcloudTalkPlatform(_make_config())
    actions = []

    class FakeClient:
        async def send_message(self, token, message, reply_to=None):
            actions.append(("send", message))
            return True, 200, None

        async def edit_message(self, token, msg_id, text):
            actions.append(("edit", msg_id, text))
            return True, None

        async def close(self):
            pass

    adapter._client = FakeClient()
    adapter._pending_ack = {"chat_id": "room1", "message_id": 100}
    result = await adapter.send("room1", "final response")
    assert result.success is True
    assert actions == [("edit", 100, "final response")]
    assert adapter._pending_ack is None


@pytest.mark.asyncio
async def test_send_falls_back_on_edit_failure(monkeypatch):
    monkeypatch.setenv("NC_TALK_APP_PASSWORD_TEST", "testpass123")
    from gateway.platforms.nextcloud_talk import NextcloudTalkPlatform
    adapter = NextcloudTalkPlatform(_make_config())
    actions = []

    class FakeClient:
        async def send_message(self, token, message, reply_to=None):
            actions.append(("send", message))
            return True, 201, None

        async def edit_message(self, token, msg_id, text):
            actions.append(("edit_fail", msg_id))
            return False, "HTTP 403"

        async def close(self):
            pass

    adapter._client = FakeClient()
    adapter._pending_ack = {"chat_id": "room1", "message_id": 100}
    result = await adapter.send("room1", "fallback")
    assert result.success is True
    assert ("edit_fail", 100) in actions
    assert ("send", "fallback") in actions
    assert adapter._pending_ack is None


# ---------------------------------------------------------------------------
# Chunk 4.1: _classify_attachment + _download_attachment
# ---------------------------------------------------------------------------

MEDIA_TEMP_DIR_KEY = "gateway.platforms.nextcloud_talk.MEDIA_TEMP_DIR"


def test_classify_attachment_mimetype():
    from gateway.platforms.nextcloud_talk import _classify_attachment
    assert _classify_attachment("image/png") == "image"
    assert _classify_attachment("image/jpeg") == "image"
    assert _classify_attachment("audio/ogg") == "audio"
    assert _classify_attachment("audio/mpeg") == "audio"
    assert _classify_attachment("video/mp4") == "audio"
    assert _classify_attachment("application/pdf") == "document"
    assert _classify_attachment("text/plain") == "document"
    assert _classify_attachment("application/zip") == "other"


@pytest.mark.asyncio
async def test_download_attachment_via_client(monkeypatch, tmp_path):
    monkeypatch.setenv("NC_TALK_APP_PASSWORD_TEST", "testpass123")
    from gateway.platforms.nextcloud_talk import NextcloudTalkPlatform
    import gateway.platforms.nextcloud_talk as ntm
    monkeypatch.setattr(ntm, "MEDIA_TEMP_DIR", str(tmp_path))

    adapter = NextcloudTalkPlatform(_make_config())
    class FakeClient:
        async def download_file(self, remote_path, local_path):
            with open(local_path, "wb") as f:
                f.write(b"fake image bytes")
            return True, local_path, None
        async def close(self): pass
    adapter._client = FakeClient()

    attachment = {
        "type": "file", "id": "123", "name": "test.png",
        "path": "test.png", "mimetype": "image/png",
        "link": "https://nc.example.com/s/abc123", "size": "1000",
    }
    path = await adapter._download_attachment(attachment)
    assert path is not None
    assert os.path.exists(path)
    assert path.endswith(".png")
    assert open(path, "rb").read() == b"fake image bytes"


# ---------------------------------------------------------------------------
# Chunk 4.2: Wire attachments into _on_poll_message
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_on_poll_message_with_image(monkeypatch, tmp_path):
    monkeypatch.setenv("NC_TALK_APP_PASSWORD_TEST", "testpass123")
    import gateway.platforms.nextcloud_talk as ntm
    monkeypatch.setattr(ntm, "MEDIA_TEMP_DIR", str(tmp_path))
    from gateway.platforms.nextcloud_talk import NextcloudTalkPlatform

    adapter = NextcloudTalkPlatform(_make_config(
        conversations=[{"token": "room1", "alias": "test"}],
        show_status_updates=False,
    ))
    class FakeClient:
        async def download_file(self, remote, local):
            with open(local, "wb") as f:
                f.write(b"PNG fake")
            return True, local, None
        async def send_message(self, *a, **kw):
            return True, 1, None
        async def close(self): pass
    adapter._client = FakeClient()

    events = []
    async def fake_handle(event):
        events.append(event)
    monkeypatch.setattr(adapter, "handle_message", fake_handle)

    msg = {
        "id": 70, "token": "room1", "actorType": "users",
        "actorId": "niko", "actorDisplayName": "Niko",
        "message": "{file}",
        "messageParameters": {
            "file": {
                "type": "file", "id": "100", "name": "screenshot.png",
                "path": "screenshot.png", "link": "",
                "mimetype": "image/png", "size": "5000",
            }
        },
        "systemMessage": "",
    }
    await adapter._on_poll_message(msg, "room1")
    assert len(events) == 1
    assert events[0].message_type.value == "photo"
    assert len(events[0].media_urls) == 1


# ---------------------------------------------------------------------------
# Chunk 4.3: Outgoing file upload + share
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_adapter_send_voice(monkeypatch, tmp_path):
    monkeypatch.setenv("NC_TALK_APP_PASSWORD_TEST", "testpass123")
    from gateway.platforms.nextcloud_talk import NextcloudTalkPlatform

    adapter = NextcloudTalkPlatform(_make_config())
    actions = []
    class FakeClient:
        async def upload_file(self, remote, local):
            actions.append(("upload", remote))
            return True, None
        async def share_file_to_chat(self, token, path, talk_meta=None):
            actions.append(("share", token, path))
            return True, 999, None
        async def send_message(self, *a, **kw): return True, 1, None
        async def close(self): pass
    adapter._client = FakeClient()

    test_file = tmp_path / "voice.mp3"
    test_file.write_bytes(b"fake audio")
    result = await adapter.send_voice("room1", str(test_file))
    assert result.success is True
    assert any("upload" in str(a) for a in actions)
    assert any("share" in str(a) for a in actions)

# ---------------------------------------------------------------------------
# Chunk 5.1: PlaceholderSTT + LlamaCppSTT classes
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_stt_placeholder_returns_none():
    from gateway.platforms.nextcloud_talk import PlaceholderSTT
    stt = PlaceholderSTT()
    result = await stt.transcribe("/tmp/fake.ogg")
    assert result is None


def test_stt_llamacpp_constructs():
    from gateway.platforms.nextcloud_talk import LlamaCppSTT
    stt = LlamaCppSTT(base_url="http://unreachable:9999")
    assert stt._base_url == "http://unreachable:9999"

# ---------------------------------------------------------------------------
# Chunk 5.2: STT wired into voice memo handling
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_voice_memo_with_stt(monkeypatch, tmp_path):
    monkeypatch.setenv("NC_TALK_APP_PASSWORD_TEST", "testpass123")
    import gateway.platforms.nextcloud_talk as ntm
    monkeypatch.setattr(ntm, "MEDIA_TEMP_DIR", str(tmp_path))
    from gateway.platforms.nextcloud_talk import NextcloudTalkPlatform

    adapter = NextcloudTalkPlatform(_make_config(
        conversations=[{"token": "room1", "alias": "test"}],
        show_status_updates=False,
    ))
    class FakeSTT:
        async def transcribe(self, path):
            return "transcribed text from voice"
    adapter._stt = FakeSTT()

    class FakeClient:
        async def download_file(self, remote, local):
            with open(local, "wb") as f:
                f.write(b"fake audio")
            return True, local, None
        async def send_message(self, *a, **kw):
            return True, 1, None
        async def close(self): pass
    adapter._client = FakeClient()

    events = []
    async def fake_handle(event):
        events.append(event)
    monkeypatch.setattr(adapter, "handle_message", fake_handle)

    msg = {
        "id": 70, "token": "room1", "actorType": "users",
        "actorId": "niko", "actorDisplayName": "Niko",
        "message": "{file}",
        "messageParameters": {
            "file": {
                "type": "file", "id": "100", "name": "voice.ogg",
                "path": "voice.ogg", "link": "",
                "mimetype": "audio/ogg", "size": "5000",
            }
        },
        "systemMessage": "",
    }
    await adapter._on_poll_message(msg, "room1")
    assert len(events) == 1
    assert "transcribed text from voice" in events[0].text


def test_send_message_tool_uses_user_client():
    """_send_nextcloud_talk imports TalkUserClient (not TalkRestClient)."""
    import inspect
    import tools.send_message_tool as smt
    source = inspect.getsource(smt._send_nextcloud_talk)
    assert "TalkUserClient" in source
    assert "TalkRestClient" not in source
    assert "bot_secret" not in source.lower()


def test_channel_directory_reads_conversations_aliases(tmp_path, monkeypatch):
    import yaml
    cfg = {
        "platforms": {
            "nextcloud_talk": {
                "enabled": True,
                "extra": {
                    "nextcloud_url": "https://test.example.com",
                    "app_password_env": "NC_TEST",
                    "conversations": [
                        {"token": "abc", "alias": "alice"},
                        {"token": "def", "alias": "bob"},
                    ],
                    "channel_aliases": {"manual": "xyz"},
                },
            },
        },
    }
    (tmp_path / "config.yaml").write_text(yaml.safe_dump(cfg))
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    from gateway.channel_directory import _build_nextcloud_talk_aliases
    entries = _build_nextcloud_talk_aliases()
    names = {e["name"] for e in entries}
    ids = {e["id"] for e in entries}
    assert "alice" in names
    assert "bob" in names
    assert "manual" in names
    assert "abc" in ids
    assert "def" in ids
    assert "xyz" in ids
