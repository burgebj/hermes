"""Tests for Nextcloud Files Service."""
import json
import os
import time
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


def test_file_sync_state_set_and_get(tmp_path):
    from gateway.services.nextcloud_files import FileSyncState

    state = FileSyncState(path=str(tmp_path / "state.json"))
    state.set("/test.pdf", etag='"abc"', size=1024, mtime=1712800000.0)

    entry = state.get("/test.pdf")
    assert entry is not None
    assert entry["etag"] == '"abc"'
    assert entry["size"] == 1024
    assert entry["mtime"] == 1712800000.0


def test_file_sync_state_persistence(tmp_path):
    from gateway.services.nextcloud_files import FileSyncState

    state_path = str(tmp_path / "state.json")
    state = FileSyncState(path=state_path)
    state.set("/test.pdf", etag='"abc"', size=1024, mtime=1712800000.0)

    state2 = FileSyncState(path=state_path)
    entry = state2.get("/test.pdf")
    assert entry is not None
    assert entry["etag"] == '"abc"'


def test_file_sync_state_remove(tmp_path):
    from gateway.services.nextcloud_files import FileSyncState

    state = FileSyncState(path=str(tmp_path / "state.json"))
    state.set("/test.pdf", etag='"abc"', size=1024, mtime=1712800000.0)
    state.remove("/test.pdf")
    assert state.get("/test.pdf") is None


def test_file_sync_state_get_all(tmp_path):
    from gateway.services.nextcloud_files import FileSyncState

    state = FileSyncState(path=str(tmp_path / "state.json"))
    state.set("/a.txt", etag='"1"', size=10, mtime=1.0)
    state.set("/b.txt", etag='"2"', size=20, mtime=2.0)
    all_entries = state.get_all()
    assert len(all_entries) == 2
    assert "/a.txt" in all_entries
    assert "/b.txt" in all_entries


def test_file_watcher_parse_event():
    from gateway.services.nextcloud_files import FileWatcher

    watcher = FileWatcher.__new__(FileWatcher)
    watcher._watch_path = Path("/home/testuser/.hermes/nextcloud")

    event = watcher._parse_inotify_line(
        "/home/testuser/.hermes/nextcloud/,CREATE,report.pdf"
    )
    assert event is not None
    path, event_type = event
    assert path == Path("/home/testuser/.hermes/nextcloud/report.pdf")
    assert event_type == "CREATE"


def test_file_watcher_parse_event_subdirectory():
    from gateway.services.nextcloud_files import FileWatcher

    watcher = FileWatcher.__new__(FileWatcher)
    watcher._watch_path = Path("/home/testuser/.hermes/nextcloud")

    event = watcher._parse_inotify_line(
        "/home/testuser/.hermes/nextcloud/docs/,MODIFY,notes.txt"
    )
    assert event is not None
    path, event_type = event
    assert path == Path("/home/testuser/.hermes/nextcloud/docs/notes.txt")
    assert event_type == "MODIFY"


def test_file_watcher_ignores_tmp_files():
    from gateway.services.nextcloud_files import FileWatcher

    watcher = FileWatcher.__new__(FileWatcher)
    watcher._watch_path = Path("/home/testuser/.hermes/nextcloud")

    event = watcher._parse_inotify_line(
        "/home/testuser/.hermes/nextcloud/,CREATE,report.pdf.tmp"
    )
    assert event is None


def test_file_watcher_parse_event_moved_to():
    from gateway.services.nextcloud_files import FileWatcher

    watcher = FileWatcher.__new__(FileWatcher)
    watcher._watch_path = Path("/home/testuser/.hermes/nextcloud")

    event = watcher._parse_inotify_line(
        "/home/testuser/.hermes/nextcloud/,MOVED_TO,renamed.txt"
    )
    assert event is not None
    _, event_type = event
    assert event_type == "MOVED_TO"


def test_notify_push_parse_event():
    from gateway.services.nextcloud_files import NotifyPushListener

    listener = NotifyPushListener.__new__(NotifyPushListener)

    file_ids = listener._parse_push_message("notify_file_id 42 99 123")
    assert file_ids == [42, 99, 123]


def test_notify_push_parse_event_ignores_other():
    from gateway.services.nextcloud_files import NotifyPushListener

    listener = NotifyPushListener.__new__(NotifyPushListener)

    file_ids = listener._parse_push_message("notify_activity")
    assert file_ids == []

    file_ids = listener._parse_push_message("authenticated")
    assert file_ids == []


@pytest.mark.asyncio
async def test_notify_push_discover_endpoint():
    from gateway.services.nextcloud_files import NotifyPushListener

    listener = NotifyPushListener(
        base_url="https://nc.example.com",
        username="hermes",
        password="pass",
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json = MagicMock(return_value={
        "ocs": {
            "data": {
                "capabilities": {
                    "notify_push": {
                        "endpoints": {
                            "websocket": "wss://nc.example.com/push/ws"
                        }
                    }
                }
            }
        }
    })

    mock_http = AsyncMock()
    mock_http.get = AsyncMock(return_value=mock_resp)

    ws_url = await listener._discover_ws_endpoint(mock_http)
    assert ws_url == "wss://nc.example.com/push/ws"

    await listener.close()


def test_service_construction():
    from gateway.services.nextcloud_files import NextcloudFilesService

    config = {
        "nextcloud_url": "https://nc.example.com",
        "username": "hermes",
        "app_password_env": "NC_APP_PW",
        "local_path": "/tmp/test_nc_files",
        "deliver": "nextcloud_talk:svvac3ix",
        "auto_share_with": "alice",
        "max_file_size_mb": 500,
        "chunk_size_mb": 5,
        "initial_sync": True,
    }

    with patch.dict(os.environ, {"NC_APP_PW": "test_password"}):
        svc = NextcloudFilesService(config)

    assert svc.name == "nextcloud_files"
    assert svc._deliver_platform == "nextcloud_talk"
    assert svc._deliver_chat_id == "svvac3ix"
    assert svc._auto_share_with == "alice"
    assert svc._max_file_size == 500 * 1024 * 1024
    assert svc._chunk_size == 5 * 1024 * 1024


def test_path_conversion():
    from gateway.services.nextcloud_files import NextcloudFilesService

    config = {
        "nextcloud_url": "https://nc.example.com",
        "local_path": "/tmp/test_nc",
        "deliver": "nextcloud_talk:abc",
    }
    with patch.dict(os.environ, {"NEXTCLOUD_TALK_APP_PASSWORD": "pw"}):
        svc = NextcloudFilesService(config)

    assert svc._to_remote_path(Path("/tmp/test_nc/docs/file.txt")) == "/docs/file.txt"
    assert svc._to_local_path("/docs/file.txt") == Path("/tmp/test_nc/docs/file.txt")


def test_is_own_operation_active():
    from gateway.services.nextcloud_files import NextcloudFilesService

    config = {
        "nextcloud_url": "https://nc.example.com",
        "local_path": "/tmp/test_nc",
        "deliver": "nextcloud_talk:abc",
    }
    with patch.dict(os.environ, {"NEXTCLOUD_TALK_APP_PASSWORD": "pw"}):
        svc = NextcloudFilesService(config)

    p = Path("/tmp/test_nc/file.txt")
    svc._downloading.add(p)
    assert svc._is_own_operation(p) is True
    svc._downloading.discard(p)
    assert svc._is_own_operation(p) is False


def test_is_own_operation_recent():
    from gateway.services.nextcloud_files import NextcloudFilesService

    config = {
        "nextcloud_url": "https://nc.example.com",
        "local_path": "/tmp/test_nc",
        "deliver": "nextcloud_talk:abc",
    }
    with patch.dict(os.environ, {"NEXTCLOUD_TALK_APP_PASSWORD": "pw"}):
        svc = NextcloudFilesService(config)

    p = Path("/tmp/test_nc/file.txt")
    svc._recently_downloaded[p] = time.monotonic()
    assert svc._is_own_operation(p) is True


def test_is_own_operation_expired():
    from gateway.services.nextcloud_files import NextcloudFilesService

    config = {
        "nextcloud_url": "https://nc.example.com",
        "local_path": "/tmp/test_nc",
        "deliver": "nextcloud_talk:abc",
    }
    with patch.dict(os.environ, {"NEXTCLOUD_TALK_APP_PASSWORD": "pw"}):
        svc = NextcloudFilesService(config)

    p = Path("/tmp/test_nc/file.txt")
    svc._recently_downloaded[p] = time.monotonic() - 10
    assert svc._is_own_operation(p) is False
    assert p not in svc._recently_downloaded


@pytest.mark.asyncio
async def test_download_file_skips_large(tmp_path):
    from gateway.services.nextcloud_files import NextcloudFilesService
    from gateway.services.nextcloud_files_client import FileInfo

    config = {
        "nextcloud_url": "https://nc.example.com",
        "local_path": str(tmp_path),
        "deliver": "nextcloud_talk:abc",
        "max_file_size_mb": 1,
    }
    with patch.dict(os.environ, {"NEXTCLOUD_TALK_APP_PASSWORD": "pw"}):
        svc = NextcloudFilesService(config)

    fi = FileInfo(
        path="/huge.bin", etag='"x"', size=50_000_000,
        mtime=0, file_id=1,
    )
    result = await svc._download_file("/huge.bin", fi)
    assert result is False


@pytest.mark.asyncio
async def test_download_file_tracks_attribution(tmp_path):
    from gateway.services.nextcloud_files import NextcloudFilesService
    from gateway.services.nextcloud_files_client import FileInfo

    config = {
        "nextcloud_url": "https://nc.example.com",
        "local_path": str(tmp_path),
        "deliver": "nextcloud_talk:abc",
        "store_path": str(tmp_path / "state.json"),
    }
    with patch.dict(os.environ, {"NEXTCLOUD_TALK_APP_PASSWORD": "pw"}):
        svc = NextcloudFilesService(config)

    svc._client = AsyncMock()
    svc._client.download = AsyncMock(return_value=True)

    fi = FileInfo(
        path="/test.pdf", etag='"abc"', size=1024,
        mtime=1712800000.0, file_id=42,
    )

    local_path = tmp_path / "test.pdf"

    result = await svc._download_file("/test.pdf", fi)
    assert result is True

    assert local_path not in svc._downloading
    assert local_path in svc._recently_downloaded

    entry = svc._sync_state.get("/test.pdf")
    assert entry is not None
    assert entry["etag"] == '"abc"'


@pytest.mark.asyncio
async def test_notify_agent(tmp_path):
    from gateway.services.nextcloud_files import NextcloudFilesService
    from gateway.services.nextcloud_files_client import FileInfo

    config = {
        "nextcloud_url": "https://nc.example.com",
        "local_path": str(tmp_path),
        "deliver": "nextcloud_talk:svvac3ix",
    }
    with patch.dict(os.environ, {"NEXTCLOUD_TALK_APP_PASSWORD": "pw"}):
        svc = NextcloudFilesService(config)

    mock_adapter = MagicMock()
    mock_adapter._classify_chat = MagicMock(return_value="group")
    mock_adapter.build_source = MagicMock(return_value=MagicMock())
    mock_adapter.handle_message = AsyncMock()

    mock_runner = MagicMock()

    with patch("gateway.config.Platform") as mock_platform_cls:
        mock_platform = MagicMock()
        mock_platform_cls.return_value = mock_platform
        mock_runner.adapters = {mock_platform: mock_adapter}
        svc.gateway_runner = mock_runner

        fi = FileInfo(path="/test.pdf", etag='"x"', size=100, mtime=0, file_id=42)
        await svc._notify_agent(fi)

    mock_adapter.handle_message.assert_called_once()
    msg_event = mock_adapter.handle_message.call_args[0][0]
    assert "/test.pdf" in msg_event.text


def test_file_watcher_ignores_dot_files():
    from gateway.services.nextcloud_files import FileWatcher

    watcher = FileWatcher.__new__(FileWatcher)
    watcher._watch_path = Path('/home/testuser/.hermes/nextcloud')

    # NC internal temp files like .~596c1172
    event = watcher._parse_inotify_line(
        '/home/testuser/.hermes/nextcloud/Deck/,CREATE,.Nextcloud sample image.jpg.~596c1172'
    )
    assert event is None

    # NC sync db files
    event = watcher._parse_inotify_line(
        '/home/testuser/.hermes/nextcloud/,MODIFY,.sync_21ed9a1a428c.db'
    )
    assert event is None

    # Normal files should still work
    event = watcher._parse_inotify_line(
        '/home/testuser/.hermes/nextcloud/,CREATE,report.pdf'
    )
    assert event is not None
