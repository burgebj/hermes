r"""Regression tests for the Windows one-line installer's parse invariants.

``scripts/install.ps1`` MUST be saved as pure ASCII (or UTF-8 *without* BOM)
AND must keep a single contiguous ``param(...)`` block as the first
non-comment statement.  See #28141 (dup of #27397) for context.

Why:

* ``irm`` (Invoke-RestMethod) decodes the response body into a .NET string.
  A leading UTF-8 BOM is preserved as U+FEFF at position 0 of that string.
* ``iex`` (Invoke-Expression) parses via ``[scriptblock]::Create($string)``,
  whose expression-context parser does NOT strip a leading U+FEFF the way
  PowerShell's *script file* loader does.
* With a stray U+FEFF -- or any executable statement / split ``param(...)``
  block -- in front of ``param(``, PowerShell stops recognising ``param``
  as a keyword.  Each parameter declaration then parses as a bare
  assignment (e.g. ``[string]$Branch = "main"`` becomes a cast-on-LHS =
  literal-on-RHS expression, which is invalid), yielding the exact error
  reported in #28141::

      The assignment expression is not valid. The input to an assignment
      operator must be an object that is able to accept assignments, such
      as a variable or a property.

Direct ``.\install.ps1`` invocation tolerates the BOM (PowerShell's file
host strips it), so the failure only surfaces via the canonical one-liner --
the path the README points new users at.

These tests pin the on-disk byte invariants so a future editor save (or a
script that uses ``Set-Content`` with a default encoding on Windows) cannot
silently reintroduce the BOM or otherwise mangle the param() block.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALL_PS1 = REPO_ROOT / "scripts" / "install.ps1"

UTF8_BOM = b"\xef\xbb\xbf"


@pytest.fixture(scope="module")
def install_ps1_bytes() -> bytes:
    assert INSTALL_PS1.is_file(), f"missing {INSTALL_PS1}"
    return INSTALL_PS1.read_bytes()


def test_no_utf8_bom(install_ps1_bytes: bytes) -> None:
    """A leading UTF-8 BOM breaks `irm | iex` (#28141, #27397)."""
    assert not install_ps1_bytes.startswith(UTF8_BOM), (
        "scripts/install.ps1 starts with a UTF-8 BOM (EF BB BF). "
        "This breaks the canonical Windows one-line installer "
        "`irm <url> | iex` with 'The assignment expression is not valid' "
        "errors on the param() block.  Re-save the file as ASCII / UTF-8 "
        "WITHOUT BOM."
    )


def test_is_ascii(install_ps1_bytes: bytes) -> None:
    """The file should decode cleanly as ASCII -- no stray high bytes."""
    try:
        install_ps1_bytes.decode("ascii")
    except UnicodeDecodeError as exc:  # pragma: no cover - diagnostic only
        pytest.fail(
            f"scripts/install.ps1 contains non-ASCII bytes at offset "
            f"{exc.start}: {install_ps1_bytes[exc.start:exc.start+4]!r}. "
            "Keep this file pure ASCII so the irm | iex parser cannot "
            "misinterpret it."
        )


def test_single_top_level_param_block(install_ps1_bytes: bytes) -> None:
    """Exactly one top-level (column 0) `param(` must exist, and it must
    appear before any executable statement.  A duplicate `param(` token or
    a misplaced `)` that splits the parameter list is the failure mode
    described in #28141.
    """
    text = install_ps1_bytes.decode("ascii")
    lines = text.splitlines()

    top_level_param_lines = [
        i for i, line in enumerate(lines) if line.startswith("param(")
    ]
    assert len(top_level_param_lines) == 1, (
        f"expected exactly one top-level `param(` in install.ps1, found "
        f"{len(top_level_param_lines)} at lines "
        f"{[i + 1 for i in top_level_param_lines]}"
    )

    param_line = top_level_param_lines[0]

    # Everything before the param() block must be blank or a comment line.
    for i, line in enumerate(lines[:param_line]):
        stripped = line.lstrip()
        if stripped == "" or stripped.startswith("#"):
            continue
        pytest.fail(
            f"line {i + 1} ({line!r}) precedes the param() block with a "
            "non-comment statement; PowerShell only recognises `param` as "
            "a keyword when it is the first executable construct."
        )

    # The param() block must close with a top-level `)` before the next
    # top-level statement -- i.e. a single contiguous block.
    close_idx = None
    for i in range(param_line + 1, len(lines)):
        if lines[i].startswith(")"):
            close_idx = i
            break
        if lines[i].startswith("param("):
            pytest.fail(
                f"duplicate top-level `param(` token at line {i + 1}; the "
                "param() block must be a single contiguous declaration."
            )
    assert close_idx is not None, "top-level param() block is never closed"
