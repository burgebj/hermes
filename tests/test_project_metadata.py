"""Regression tests for packaging metadata in pyproject.toml."""

import json
from pathlib import Path
import re
import tomllib


def _load_optional_dependencies():
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with pyproject_path.open("rb") as handle:
        project = tomllib.load(handle)["project"]
    return project["optional-dependencies"]


def _load_setuptools_config():
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with pyproject_path.open("rb") as handle:
        tool = tomllib.load(handle)["tool"]
    return tool["setuptools"]


def _load_package_data():
    return _load_setuptools_config()["package-data"]


def test_mcp_registry_name_is_lowercase_and_matches_readme_marker():
    """Official MCP server names should stay canonical and lowercase."""
    root = Path(__file__).resolve().parents[1]
    server_json = json.loads((root / "server.json").read_text(encoding="utf-8"))
    readme = (root / "README.md").read_text(encoding="utf-8")

    assert server_json["name"] == "io.github.nousresearch/hermes-agent"
    assert server_json["name"] == server_json["name"].lower()
    assert re.search(r"<!--\s*mcp-name:\s*io\.github\.nousresearch/hermes-agent\s*-->", readme)


def test_matrix_extra_not_in_all():
    """The [matrix] extra pulls `mautrix[encryption]` -> `python-olm`,
    which has Linux-only wheels and no native build path on Windows or
    modern macOS (archived libolm, C++ errors with Clang 21+).

    With matrix in [all], `uv sync --locked` on Windows tried to build
    python-olm from sdist and failed on `make`. As of 2026-05-12 the
    [matrix] extra is excluded from [all] entirely and routed through
    `tools/lazy_deps.py` (LAZY_DEPS["platform.matrix"]) — installs at
    first use, where the user is expected to have a toolchain.
    """
    optional_dependencies = _load_optional_dependencies()

    assert "matrix" in optional_dependencies, "[matrix] extra must still exist for explicit `pip install hermes-agent[matrix]`"
    # Must NOT appear in [all] in any form — neither unconditional nor
    # platform-gated. Lazy-install handles it.
    matrix_in_all = [
        dep for dep in optional_dependencies["all"]
        if "matrix" in dep
    ]
    assert not matrix_in_all, (
        "matrix must not appear in [all] — it's lazy-installed via "
        "tools/lazy_deps.py LAZY_DEPS['platform.matrix']. Found: "
        f"{matrix_in_all}"
    )


def test_lazy_installable_extras_excluded_from_all():
    """Policy (2026-05-12): every extra that has a `LAZY_DEPS` entry
    in `tools/lazy_deps.py` must be excluded from [all].

    The lazy-install system exists so one quarantined PyPI release
    (e.g. mistralai 2.4.6) can't break every fresh install. Putting a
    backend in BOTH [all] and LAZY_DEPS defeats that — fresh installs
    eager-install it and inherit whatever's broken upstream.

    If you're tempted to add an opt-in backend to [all] for "convenience,"
    add it to `LAZY_DEPS` instead so it installs at first use.
    """
    optional_dependencies = _load_optional_dependencies()

    # Hard-coded mirror of the extras that are in LAZY_DEPS as of
    # 2026-05-12. This list intentionally duplicates rather than
    # imports tools/lazy_deps.py so the test stays a contract — if
    # someone adds a new lazy-install backend, they have to update
    # this list AND verify [all] doesn't contain it.
    lazy_covered_extras = {
        "anthropic", "bedrock",
        "exa", "firecrawl", "parallel-web",
        "fal",
        "edge-tts", "tts-premium",
        "voice",  # faster-whisper / sounddevice / numpy
        "modal", "daytona",
        "messaging", "slack", "matrix", "dingtalk", "feishu",
        "honcho", "hindsight",
        "mistral",  # mistralai — Voxtral STT/TTS, lazy-installed (stt.mistral / tts.mistral)
    }
    all_extra_specs = optional_dependencies["all"]
    for extra in lazy_covered_extras:
        offending = [
            spec for spec in all_extra_specs
            if f"hermes-agent[{extra}]" in spec
        ]
        assert not offending, (
            f"[{extra}] is in [all] but also in LAZY_DEPS. "
            f"Remove it from [all] in pyproject.toml — it lazy-installs "
            f"at first use. Found in [all]: {offending}"
        )


def test_dev_extra_excluded_from_all():
    """End-user installs should not pull test/lint/debug tooling."""
    optional_dependencies = _load_optional_dependencies()

    assert "dev" in optional_dependencies
    assert not any(
        spec == "hermes-agent[dev]"
        for spec in optional_dependencies["all"]
    )


def test_messaging_extra_includes_qrcode_for_weixin_setup():
    optional_dependencies = _load_optional_dependencies()

    messaging_extra = optional_dependencies["messaging"]
    assert any(dep.startswith("qrcode") for dep in messaging_extra)


def test_dingtalk_extra_includes_qrcode_for_qr_auth():
    """DingTalk's QR-code device-flow auth (hermes_cli/dingtalk_auth.py)
    needs the qrcode package."""
    optional_dependencies = _load_optional_dependencies()

    dingtalk_extra = optional_dependencies["dingtalk"]
    assert any(dep.startswith("qrcode") for dep in dingtalk_extra)


def test_feishu_extra_includes_qrcode_for_qr_login():
    """Feishu's QR login flow (gateway/platforms/feishu.py) needs the
    qrcode package."""
    optional_dependencies = _load_optional_dependencies()

    feishu_extra = optional_dependencies["feishu"]
    assert any(dep.startswith("qrcode") for dep in feishu_extra)


def test_nemo_relay_extra_uses_official_0_3_distribution():
    optional_dependencies = _load_optional_dependencies()

    assert optional_dependencies["nemo-relay"] == ["nemo-relay==0.3"]
    assert not any(
        spec == "hermes-agent[nemo-relay]"
        for spec in optional_dependencies["all"]
    )


def test_dashboard_plugin_manifests_and_assets_are_packaged():
    """Bundled dashboard plugins need their manifests and built assets in
    wheel installs so /api/dashboard/plugins can discover them outside a
    source checkout."""
    package_data = _load_package_data()
    plugin_data = package_data["plugins"]

    assert "*/dashboard/manifest.json" in plugin_data
    assert "*/dashboard/dist/*" in plugin_data
    assert "*/dashboard/dist/**/*" in plugin_data


def test_nested_bundled_plugin_metadata_is_packaged():
    """Nested opt-in plugins need manifests and READMEs in wheel installs."""
    package_data = _load_package_data()
    plugin_data = package_data["plugins"]

    assert "**/plugin.yaml" in plugin_data
    assert "**/plugin.yml" in plugin_data
    assert "**/README.md" in plugin_data


def test_mcp_serve_module_is_packaged_for_registry_launch():
    """The MCP registry entry launches `hermes mcp serve` from the PyPI wheel.

    `hermes_cli.main` imports the top-level `mcp_serve` module for that
    subcommand, so the module must be listed explicitly in setuptools'
    `py-modules` list.
    """
    py_modules = _load_setuptools_config()["py-modules"]

    assert "mcp_serve" in py_modules


def test_mcp_registry_package_launches_cli_with_mcp_extra():
    """Registry installs should include the MCP SDK and invoke `hermes mcp serve`.

    The package identifier includes the `[mcp]` extra so clients using a
    Python package runner (for example `uvx`) install the optional MCP SDK.
    The package runner commonly infers the executable from the package name,
    so the `hermes-agent` console script must dispatch through the main CLI
    instead of the legacy direct-agent entry point.
    """
    root = Path(__file__).resolve().parents[1]
    server_json = json.loads((root / "server.json").read_text(encoding="utf-8"))
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    package = server_json["packages"][0]
    project = pyproject["project"]

    assert server_json["version"] == project["version"]
    assert package["version"] == project["version"]
    assert package["registryType"] == "pypi"
    assert package["registryBaseUrl"] == "https://pypi.org"
    assert package["identifier"] == "hermes-agent[mcp]"
    assert package["runtimeHint"] == "uvx"
    assert [arg["value"] for arg in package["packageArguments"]] == ["mcp", "serve"]
    assert project["scripts"]["hermes-agent"] == "hermes_cli.main:main"


def test_mcp_server_docs_match_registry_identifier():
    root = Path(__file__).resolve().parents[1]
    server_json = json.loads((root / "server.json").read_text(encoding="utf-8"))
    docs = (root / "website/docs/guides/hermes-as-an-mcp-server.md").read_text(encoding="utf-8")

    assert f'`"identifier": "{server_json["packages"][0]["identifier"]}"`' in docs
