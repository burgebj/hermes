from __future__ import annotations

import io
import importlib.util
import tarfile
from pathlib import Path

from hermes_cli.main import _safe_extract_psutil_sdist as main_safe_extract


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "install_psutil_android.py"
)


def _load_install_script_module():
    spec = importlib.util.spec_from_file_location("install_psutil_android", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EXTRACTORS = (
    main_safe_extract,
    _load_install_script_module()._safe_extract_psutil_sdist,
)


def _tar_with_members(*members: tuple[str, bytes, str]) -> io.BytesIO:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, body, kind in members:
            info = tarfile.TarInfo(name)
            if kind == "dir":
                info.type = tarfile.DIRTYPE
                tar.addfile(info)
            elif kind == "symlink":
                info.type = tarfile.SYMTYPE
                info.linkname = "target"
                tar.addfile(info)
            elif kind == "hardlink":
                info.type = tarfile.LNKTYPE
                info.linkname = "target"
                tar.addfile(info)
            else:
                info.size = len(body)
                tar.addfile(info, io.BytesIO(body))
    buf.seek(0)
    return buf


def _run_extract(extractor, archive: io.BytesIO, dest: Path) -> None:
    with tarfile.open(fileobj=archive, mode="r:gz") as tar:
        extractor(tar, dest)


def _assert_extract_rejected(
    extractor, archive: io.BytesIO, dest: Path, match: str
) -> None:
    try:
        _run_extract(extractor, archive, dest)
    except RuntimeError as exc:
        assert match in str(exc)
    else:  # pragma: no cover - failure branch for clearer assertion output
        raise AssertionError("expected unsafe psutil sdist member to be rejected")


def test_psutil_sdist_safe_extract_allows_regular_files(tmp_path):
    for extractor in EXTRACTORS:
        dest = tmp_path / extractor.__module__.replace(".", "_")
        archive = _tar_with_members(
            ("psutil-7.2.2", b"", "dir"),
            (
                "psutil-7.2.2/psutil/_common.py",
                b'LINUX = sys.platform.startswith("linux")\n',
                "file",
            ),
        )

        _run_extract(extractor, archive, dest)

        extracted = dest / "psutil-7.2.2" / "psutil" / "_common.py"
        assert extracted.read_text() == 'LINUX = sys.platform.startswith("linux")\n'


def test_psutil_sdist_safe_extract_rejects_path_traversal(tmp_path):
    for extractor in EXTRACTORS:
        dest = tmp_path / extractor.__module__.replace(".", "_")
        outside = dest.parent / f"outside-owned-{dest.name}.txt"
        archive = _tar_with_members(("../outside-owned.txt", b"owned", "file"))

        _assert_extract_rejected(extractor, archive, dest, "outside temp dir")

        assert not outside.exists()


def test_psutil_sdist_safe_extract_rejects_absolute_paths(tmp_path):
    for extractor in EXTRACTORS:
        dest = tmp_path / extractor.__module__.replace(".", "_")
        outside = dest.parent / f"absolute-owned-{dest.name}.txt"
        archive = _tar_with_members((str(outside), b"owned", "file"))

        _assert_extract_rejected(extractor, archive, dest, "absolute path")

        assert not outside.exists()


def test_psutil_sdist_safe_extract_rejects_windows_absolute_paths(tmp_path):
    for extractor in EXTRACTORS:
        dest = tmp_path / extractor.__module__.replace(".", "_")
        archive = _tar_with_members(("C:/Users/attacker/owned.txt", b"owned", "file"))

        _assert_extract_rejected(extractor, archive, dest, "absolute path")

        assert not (dest / "C:" / "Users" / "attacker" / "owned.txt").exists()


def test_psutil_sdist_safe_extract_rejects_links(tmp_path):
    for extractor in EXTRACTORS:
        for kind in ("symlink", "hardlink"):
            dest = tmp_path / extractor.__module__.replace(".", "_") / kind
            archive = _tar_with_members(("psutil-7.2.2/link", b"", kind))

            _assert_extract_rejected(
                extractor,
                archive,
                dest,
                "unsupported psutil sdist member",
            )

            assert not (dest / "psutil-7.2.2" / "link").exists()
