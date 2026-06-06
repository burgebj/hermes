"""Tests for Nextcloud Files Client."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx


def test_file_info_construction():
    from gateway.services.nextcloud_files_client import FileInfo
    fi = FileInfo(
        path="/Documents/test.pdf",
        etag='"abc123"',
        size=1024,
        mtime=1712800000.0,
        file_id=42,
        content_type="application/pdf",
        is_dir=False,
    )
    assert fi.path == "/Documents/test.pdf"
    assert fi.size == 1024
    assert fi.file_id == 42
    assert not fi.is_dir


PROPFIND_RESPONSE = """<?xml version="1.0"?>
<d:multistatus xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns" xmlns:nc="http://nextcloud.org/ns">
  <d:response>
    <d:href>/remote.php/dav/files/hermes/</d:href>
    <d:propstat>
      <d:prop>
        <d:resourcetype><d:collection/></d:resourcetype>
        <d:getetag>"root"</d:getetag>
        <oc:fileid>1</oc:fileid>
      </d:prop>
      <d:status>HTTP/1.1 200 OK</d:status>
    </d:propstat>
  </d:response>
  <d:response>
    <d:href>/remote.php/dav/files/hermes/test.pdf</d:href>
    <d:propstat>
      <d:prop>
        <d:getcontentlength>2048</d:getcontentlength>
        <d:getetag>"def456"</d:getetag>
        <d:getcontenttype>application/pdf</d:getcontenttype>
        <d:getlastmodified>Thu, 10 Apr 2026 12:00:00 GMT</d:getlastmodified>
        <oc:fileid>42</oc:fileid>
        <d:resourcetype/>
      </d:prop>
      <d:status>HTTP/1.1 200 OK</d:status>
    </d:propstat>
  </d:response>
</d:multistatus>"""


def test_parse_propfind_response():
    from gateway.services.nextcloud_files_client import NextcloudFilesClient
    client = NextcloudFilesClient.__new__(NextcloudFilesClient)
    client._dav_base = "/remote.php/dav/files/hermes"
    results = client._parse_propfind(PROPFIND_RESPONSE)
    assert len(results) == 1
    fi = results[0]
    assert fi.path == "/test.pdf"
    assert fi.etag == '"def456"'
    assert fi.size == 2048
    assert fi.file_id == 42
    assert fi.content_type == "application/pdf"
    assert not fi.is_dir


@pytest.mark.asyncio
async def test_propfind():
    from gateway.services.nextcloud_files_client import NextcloudFilesClient

    mock_response = MagicMock()
    mock_response.status_code = 207
    mock_response.text = PROPFIND_RESPONSE
    mock_response.raise_for_status = MagicMock()

    client = NextcloudFilesClient("https://nc.example.com", "hermes", "pass")
    client._http = AsyncMock()
    client._http.request = AsyncMock(return_value=mock_response)

    results = await client.propfind("/")
    assert len(results) == 1
    assert results[0].path == "/test.pdf"

    call_args = client._http.request.call_args
    assert call_args[1]["method"] == "PROPFIND"
    assert "/remote.php/dav/files/hermes/" in call_args[1]["url"]

    await client.close()


@pytest.mark.asyncio
async def test_download(tmp_path):
    from gateway.services.nextcloud_files_client import NextcloudFilesClient

    client = NextcloudFilesClient("https://nc.example.com", "hermes", "pass")

    mock_stream = AsyncMock()
    mock_stream.status_code = 200
    mock_stream.raise_for_status = MagicMock()

    async def fake_aiter_bytes(chunk_size=None):
        yield b"Hello "
        yield b"World"

    mock_stream.aiter_bytes = fake_aiter_bytes
    mock_stream.aclose = AsyncMock()
    mock_stream.__aenter__ = AsyncMock(return_value=mock_stream)
    mock_stream.__aexit__ = AsyncMock(return_value=False)

    client._http = AsyncMock()
    client._http.stream = MagicMock(return_value=mock_stream)

    local_path = tmp_path / "test.pdf"
    result = await client.download("/test.pdf", local_path)
    assert result is True
    assert local_path.read_bytes() == b"Hello World"
    assert not (tmp_path / "test.pdf.tmp").exists()

    await client.close()


@pytest.mark.asyncio
async def test_download_creates_parent_dirs(tmp_path):
    from gateway.services.nextcloud_files_client import NextcloudFilesClient

    client = NextcloudFilesClient("https://nc.example.com", "hermes", "pass")

    mock_stream = AsyncMock()
    mock_stream.status_code = 200
    mock_stream.raise_for_status = MagicMock()

    async def fake_aiter_bytes(chunk_size=None):
        yield b"content"

    mock_stream.aiter_bytes = fake_aiter_bytes
    mock_stream.aclose = AsyncMock()
    mock_stream.__aenter__ = AsyncMock(return_value=mock_stream)
    mock_stream.__aexit__ = AsyncMock(return_value=False)

    client._http = AsyncMock()
    client._http.stream = MagicMock(return_value=mock_stream)

    local_path = tmp_path / "sub" / "dir" / "file.txt"
    result = await client.download("/sub/dir/file.txt", local_path)
    assert result is True
    assert local_path.read_bytes() == b"content"

    await client.close()


@pytest.mark.asyncio
async def test_upload(tmp_path):
    from gateway.services.nextcloud_files_client import NextcloudFilesClient

    client = NextcloudFilesClient("https://nc.example.com", "hermes", "pass")

    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.raise_for_status = MagicMock()
    mock_response.headers = {"ETag": '"new_etag"', "OC-FileId": "99"}

    client._http = AsyncMock()
    client._http.put = AsyncMock(return_value=mock_response)

    local_file = tmp_path / "upload.txt"
    local_file.write_text("upload content")

    etag = await client.upload(local_file, "/upload.txt")
    assert etag == '"new_etag"'

    client._http.put.assert_called_once()
    call_args = client._http.put.call_args
    assert "/remote.php/dav/files/hermes/upload.txt" in call_args[0][0]

    await client.close()


@pytest.mark.asyncio
async def test_upload_chunked(tmp_path):
    from gateway.services.nextcloud_files_client import NextcloudFilesClient

    client = NextcloudFilesClient("https://nc.example.com", "hermes", "pass")

    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.raise_for_status = MagicMock()
    mock_response.headers = {"ETag": '"chunked_etag"', "OC-FileId": "100"}

    client._http = AsyncMock()
    client._http.request = AsyncMock(return_value=mock_response)
    client._http.put = AsyncMock(return_value=mock_response)

    local_file = tmp_path / "large.bin"
    local_file.write_bytes(b"x" * 150)

    etag = await client.upload_chunked(local_file, "/large.bin", chunk_size=64)
    assert etag == '"chunked_etag"'
    assert client._http.put.call_count == 3

    await client.close()


@pytest.mark.asyncio
async def test_mkdir():
    from gateway.services.nextcloud_files_client import NextcloudFilesClient

    client = NextcloudFilesClient("https://nc.example.com", "hermes", "pass")
    mock_resp = MagicMock(status_code=201)
    mock_resp.raise_for_status = MagicMock()
    client._http = AsyncMock()
    client._http.request = AsyncMock(return_value=mock_resp)

    result = await client.mkdir("/new_dir")
    assert result is True
    call_args = client._http.request.call_args
    assert call_args[1]["method"] == "MKCOL"

    await client.close()


@pytest.mark.asyncio
async def test_delete():
    from gateway.services.nextcloud_files_client import NextcloudFilesClient

    client = NextcloudFilesClient("https://nc.example.com", "hermes", "pass")
    mock_resp = MagicMock(status_code=204)
    mock_resp.raise_for_status = MagicMock()
    client._http = AsyncMock()
    client._http.delete = AsyncMock(return_value=mock_resp)

    result = await client.delete("/old.txt")
    assert result is True

    await client.close()


@pytest.mark.asyncio
async def test_move():
    from gateway.services.nextcloud_files_client import NextcloudFilesClient

    client = NextcloudFilesClient("https://nc.example.com", "hermes", "pass")
    mock_resp = MagicMock(status_code=201)
    mock_resp.raise_for_status = MagicMock()
    client._http = AsyncMock()
    client._http.request = AsyncMock(return_value=mock_resp)

    result = await client.move("/old.txt", "/new.txt")
    assert result is True
    call_args = client._http.request.call_args
    assert call_args[1]["method"] == "MOVE"

    await client.close()


@pytest.mark.asyncio
async def test_resolve_file_ids():
    from gateway.services.nextcloud_files_client import NextcloudFilesClient, FileInfo

    client = NextcloudFilesClient("https://nc.example.com", "hermes", "pass")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json = MagicMock(return_value={
        "ocs": {
            "data": {
                "id": 42,
                "name": "test.pdf",
                "path": "/Documents",
                "size": 2048,
                "etag": "abc123",
                "mimetype": "application/pdf",
                "mtime": 1712800000,
            }
        }
    })

    client._ocs_http = AsyncMock()
    client._ocs_http.get = AsyncMock(return_value=mock_resp)

    results = await client.resolve_file_ids([42])
    assert len(results) == 1
    fi = results[0]
    assert fi.path == "/Documents/test.pdf"
    assert fi.file_id == 42
    assert fi.size == 2048

    await client.close()


@pytest.mark.asyncio
async def test_share():
    from gateway.services.nextcloud_files_client import NextcloudFilesClient, PERM_ALL

    client = NextcloudFilesClient("https://nc.example.com", "hermes", "pass")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json = MagicMock(return_value={
        "ocs": {"data": {"id": 55, "path": "/test.pdf"}}
    })

    client._ocs_http = AsyncMock()
    client._ocs_http.post = AsyncMock(return_value=mock_resp)

    result = await client.share("/test.pdf", "alice", permissions=PERM_ALL)
    assert result["id"] == 55

    call_args = client._ocs_http.post.call_args
    post_data = call_args[1]["data"]
    assert post_data["shareWith"] == "alice"
    assert post_data["shareType"] == 0
    assert post_data["permissions"] == PERM_ALL

    await client.close()


@pytest.mark.asyncio
async def test_resolve_file_ids_skips_errors():
    from gateway.services.nextcloud_files_client import NextcloudFilesClient

    client = NextcloudFilesClient("https://nc.example.com", "hermes", "pass")

    client._ocs_http = AsyncMock()
    client._ocs_http.get = AsyncMock(side_effect=httpx.HTTPStatusError(
        "Not Found", request=MagicMock(), response=MagicMock(status_code=404),
    ))

    results = await client.resolve_file_ids([999])
    assert results == []

    await client.close()


@pytest.mark.asyncio
async def test_unshare():
    from gateway.services.nextcloud_files_client import NextcloudFilesClient

    client = NextcloudFilesClient("https://nc.example.com", "hermes", "pass")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()

    client._ocs_http = AsyncMock()
    client._ocs_http.delete = AsyncMock(return_value=mock_resp)

    result = await client.unshare(55)
    assert result is True
    call_url = client._ocs_http.delete.call_args[0][0]
    assert "/shares/55" in call_url

    await client.close()


@pytest.mark.asyncio
async def test_get_shares():
    from gateway.services.nextcloud_files_client import NextcloudFilesClient

    client = NextcloudFilesClient("https://nc.example.com", "hermes", "pass")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json = MagicMock(return_value={
        "ocs": {"data": [{"id": 55, "path": "/test.pdf"}]}
    })

    client._ocs_http = AsyncMock()
    client._ocs_http.get = AsyncMock(return_value=mock_resp)

    shares = await client.get_shares(path="/test.pdf")
    assert len(shares) == 1
    assert shares[0]["id"] == 55

    await client.close()
