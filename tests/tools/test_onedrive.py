"""Tests for the read-only Microsoft OneDrive tools."""

import builtins


ONEDRIVE_TOOL_NAMES = {
    "list_onedrive_root",
    "list_onedrive_folder",
    "read_onedrive_text_file",
    "download_onedrive_file",
}


def test_check_onedrive_false_without_client_id(monkeypatch):
    from tools.onedrive import _check_onedrive

    monkeypatch.delenv("MICROSOFT_CLIENT_ID", raising=False)

    assert _check_onedrive() is False


def test_check_onedrive_false_when_msal_missing(monkeypatch):
    from tools.onedrive import _check_onedrive

    monkeypatch.setenv("MICROSOFT_CLIENT_ID", "test-client-id")
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "msal":
            raise ImportError("No module named 'msal'")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    assert _check_onedrive() is False


def test_onedrive_schemas_have_expected_json_schema_shape():
    from tools import onedrive

    schemas = {
        "list_onedrive_root": onedrive.LIST_ONEDRIVE_ROOT_SCHEMA,
        "list_onedrive_folder": onedrive.LIST_ONEDRIVE_FOLDER_SCHEMA,
        "read_onedrive_text_file": onedrive.READ_ONEDRIVE_TEXT_FILE_SCHEMA,
        "download_onedrive_file": onedrive.DOWNLOAD_ONEDRIVE_FILE_SCHEMA,
    }

    for name, schema in schemas.items():
        assert schema["name"] == name
        assert schema["parameters"]["type"] == "object"
        assert "properties" in schema["parameters"]

    assert "required" not in schemas["list_onedrive_root"]["parameters"]
    assert schemas["list_onedrive_folder"]["parameters"]["required"] == ["path"]
    assert schemas["read_onedrive_text_file"]["parameters"]["required"] == ["path"]
    assert schemas["download_onedrive_file"]["parameters"]["required"] == [
        "path",
        "target_path",
    ]


def test_onedrive_tools_registered_in_registry():
    import tools.onedrive  # noqa: F401
    from tools.registry import registry

    names = set(registry.get_all_tool_names())
    assert ONEDRIVE_TOOL_NAMES <= names

    toolset_map = registry.get_tool_to_toolset_map()
    for tool_name in ONEDRIVE_TOOL_NAMES:
        assert toolset_map[tool_name] == "onedrive"


def test_validate_endpoint_allows_graph_drive_paths_and_rejects_traversal():
    from tools.onedrive import _validate_endpoint

    assert _validate_endpoint("/me")
    assert _validate_endpoint("/me/drive/root/children")
    assert _validate_endpoint("/me/drive/root:/Documents:/children")
    assert _validate_endpoint("/me/drive/root:/Documents/report.txt:/content")

    assert not _validate_endpoint("/me/drive/root:/../secret.txt:/content")
    assert not _validate_endpoint("/me/drive/root:/Documents/../secret.txt:/content")
    assert not _validate_endpoint("/me/drive/items/some-id/content")
