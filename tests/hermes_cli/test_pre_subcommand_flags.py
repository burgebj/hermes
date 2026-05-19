"""Tests for top-level flags that appear BEFORE the ``chat`` subcommand.

Regression coverage for #28780 — ``hermes -t web chat`` silently
parsed identically to ``hermes chat`` because the ``chat`` subparser
redefined ``-t/--toolsets`` with ``default=None`` and clobbered the
value the top-level parser had already stashed in ``args.toolsets``.

The same bug affected ``-m/--model``, ``--provider``, ``--tui``, and
``--dev``. After the fix, all of these flags work in either position
(before or after ``chat``), and an explicit post-subcommand
occurrence still wins ("most specific override").
"""

from __future__ import annotations

import sys
from typing import Iterable

import pytest

from hermes_cli._parser import build_top_level_parser


def _parse(argv: Iterable[str]):
    """Parse ``argv`` through the real top-level parser.

    Returns the populated ``argparse.Namespace``.  We use
    ``parse_known_args`` (not ``parse_args``) so an unknown trailing
    chat-prompt token doesn't cause a SystemExit during the test —
    we're asserting on the parsed flag values, not on argv completeness.
    """
    parser, _subparsers, chat_parser = build_top_level_parser()
    # cmd_chat is only attached inside main.py; for these tests we just
    # need argparse to know that ``chat`` is a valid subcommand, which
    # ``build_top_level_parser`` already wires up.
    chat_parser.set_defaults(func=lambda _a: None)

    real_argv = sys.argv
    try:
        sys.argv = ["hermes", *argv]
        args, _unknown = parser.parse_known_args()
    finally:
        sys.argv = real_argv
    return args


class TestToolsetsFlagPosition:
    """``-t/--toolsets`` must work in either position (#28780)."""

    @pytest.mark.parametrize("toolset", ["web", "web,terminal", "*", "all"])
    def test_pre_subcommand_toolsets_survives_chat(self, toolset):
        # ``hermes -t web chat`` — the exact form from the bug report.
        args = _parse(["-t", toolset, "chat"])
        assert args.toolsets == toolset, (
            "Pre-subcommand -t was silently dropped by the chat subparser. "
            "This is the #28780 regression."
        )

    def test_post_subcommand_toolsets_still_works(self):
        # The working form from the bug report — must keep working.
        args = _parse(["chat", "-t", "web"])
        assert args.toolsets == "web"

    def test_post_subcommand_overrides_pre_subcommand(self):
        # If a user passes ``-t`` on both sides, the more-specific
        # (post-subcommand) value should win.  This matches argparse's
        # "subparser is more specific" convention and the way
        # ``hermes chat -t cli`` reads naturally.
        args = _parse(["-t", "web", "chat", "-t", "cli"])
        assert args.toolsets == "cli"

    def test_no_toolsets_yields_none(self):
        # Sanity: when neither position is used, the attribute is still
        # present (top-level default) and is None — many callers rely on
        # ``args.toolsets`` being addressable.
        args = _parse(["chat"])
        assert args.toolsets is None


class TestModelFlagPosition:
    """``-m/--model`` must also work in either position (same bug)."""

    def test_pre_subcommand_model_survives_chat(self):
        args = _parse(["-m", "gpt5", "chat"])
        assert args.model == "gpt5"

    def test_long_form_pre_subcommand(self):
        # Long-form spelling must travel the same path as the short form.
        args = _parse(["--model", "anthropic/claude-sonnet-4.6", "chat"])
        assert args.model == "anthropic/claude-sonnet-4.6"

    def test_post_subcommand_model_still_works(self):
        args = _parse(["chat", "-m", "gpt5"])
        assert args.model == "gpt5"

    def test_post_subcommand_model_overrides_pre(self):
        args = _parse(["-m", "gpt5", "chat", "-m", "claude"])
        assert args.model == "claude"


class TestProviderFlagPosition:
    """``--provider`` must also work in either position (same bug)."""

    def test_pre_subcommand_provider_survives_chat(self):
        args = _parse(["--provider", "openai", "chat"])
        assert getattr(args, "provider", None) == "openai"

    def test_post_subcommand_provider_still_works(self):
        args = _parse(["chat", "--provider", "openai"])
        assert getattr(args, "provider", None) == "openai"

    def test_post_subcommand_provider_overrides_pre(self):
        args = _parse(["--provider", "openai", "chat", "--provider", "anthropic"])
        assert getattr(args, "provider", None) == "anthropic"


class TestTuiFlagPosition:
    """``--tui`` must also work in either position (same bug)."""

    def test_pre_subcommand_tui_survives_chat(self):
        args = _parse(["--tui", "chat"])
        assert getattr(args, "tui", False) is True

    def test_post_subcommand_tui_still_works(self):
        args = _parse(["chat", "--tui"])
        assert getattr(args, "tui", False) is True

    def test_no_tui_anywhere_defaults_false(self):
        args = _parse(["chat"])
        assert getattr(args, "tui", False) is False


class TestMixedPreSubcommandFlags:
    """All five inherited flags should compose freely (#28780)."""

    def test_all_five_inherited_flags_pre_subcommand(self):
        # Smoke: every fixed flag stacked in the pre-subcommand position.
        args = _parse([
            "-t", "web,terminal",
            "-m", "gpt5",
            "--provider", "openai",
            "--tui",
            "chat",
        ])
        assert args.toolsets == "web,terminal"
        assert args.model == "gpt5"
        assert getattr(args, "provider", None) == "openai"
        assert getattr(args, "tui", False) is True

    def test_mixed_pre_and_post_subcommand_positions(self):
        # Realistic usage where the user has half their flags before
        # ``chat`` (from a shell alias, perhaps) and adds more
        # interactively after.
        args = _parse([
            "-t", "web",
            "chat",
            "-m", "gpt5",
        ])
        assert args.toolsets == "web"
        assert args.model == "gpt5"


class TestPreviouslyWorkingFlagsStillWork:
    """Sanity: the flags that *weren't* broken (they already used
    ``argparse.SUPPRESS``) must stay unaffected by the fix.  Lock
    them down so a future refactor doesn't quietly regress them."""

    def test_pre_subcommand_continue_with_name(self):
        # Note: ``-c`` is ``nargs='?'`` (optional value).  With a bare
        # ``hermes -c chat`` argparse greedily consumes ``chat`` as
        # the optional value instead of the subcommand — a known
        # argparse limitation acknowledged in main.py's
        # ``_TOP_LEVEL_VALUE_FLAGS``.  The supported form is therefore
        # ``-c <name> chat`` (this test) or ``-c`` alone with no
        # following positional.  Neither path is affected by the
        # #28780 fix; this test exists so future cleanup of ``-c``
        # parsing doesn't accidentally re-break the supported form.
        args = _parse(["-c", "my-session", "chat"])
        assert args.continue_last == "my-session"

    def test_pre_subcommand_resume_flag(self):
        args = _parse(["-r", "abc123", "chat"])
        assert args.resume == "abc123"

    def test_pre_subcommand_worktree_flag(self):
        args = _parse(["-w", "chat"])
        assert args.worktree is True

    def test_pre_subcommand_skills_flag(self):
        args = _parse(["-s", "git-auth,hermes-agent-dev", "chat"])
        assert args.skills == ["git-auth,hermes-agent-dev"]

    def test_pre_subcommand_yolo_flag(self):
        args = _parse(["--yolo", "chat"])
        assert args.yolo is True

    def test_pre_subcommand_ignore_user_config(self):
        args = _parse(["--ignore-user-config", "chat"])
        assert args.ignore_user_config is True


class TestParserContract:
    """Lock down the parser shape that the fix relies on.  If these
    invariants drift, the runtime tests above might still pass
    accidentally — the explicit contract makes intent clear and
    surfaces regressions at the structural level."""

    def test_chat_subparser_uses_suppress_for_inherited_flags(self):
        """The five formerly-broken flags must use ``argparse.SUPPRESS``
        on the chat subparser, otherwise an absent post-subcommand
        occurrence will silently re-overwrite the top-level value."""
        import argparse

        _parser, _subs, chat = build_top_level_parser()
        inherited = {"--model", "--toolsets", "--provider", "--tui", "--dev"}

        for action in chat._actions:
            if not action.option_strings:
                continue
            if any(opt in inherited for opt in action.option_strings):
                assert action.default is argparse.SUPPRESS, (
                    f"chat subparser action {action.option_strings!r} must "
                    f"use argparse.SUPPRESS so pre-subcommand values "
                    f"survive, got default={action.default!r} (#28780)."
                )

    def test_top_level_parser_still_defines_these_flags(self):
        """The fix relies on the top-level parser providing real defaults
        for these flags so ``args.toolsets`` etc. always exist on the
        Namespace.  If someone removes a top-level definition, every
        ``args.toolsets`` site in main.py would AttributeError."""
        parser, _subs, _chat = build_top_level_parser()
        top_level_option_strings: set[str] = set()
        for action in parser._actions:
            top_level_option_strings.update(action.option_strings)

        for required in ("--toolsets", "--model", "--provider", "--tui"):
            assert required in top_level_option_strings, (
                f"Top-level parser must define {required!r} — the chat "
                f"subparser uses argparse.SUPPRESS and relies on the "
                f"top-level default to populate args."
            )
