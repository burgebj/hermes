"""Tests for Discord clarify button rendering and resolution.

Mirrors test_telegram_clarify_buttons.py for the Discord ``send_clarify``
override and the ``ClarifyChoiceView`` callbacks. Discord uses ``discord.ui.View``
button callbacks (closures) rather than a string-prefixed callback_query
dispatcher like Telegram — the auth + resolution path is the same:

  · numeric choice → resolve_gateway_clarify(clarify_id, choice_text)
  · "Other" button → mark_awaiting_text(clarify_id) so the text-intercept
    captures the next user message in this session
  · already-resolved or unauthorized → ephemeral "this prompt..." reply
"""

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

# Repo root importable
_repo = str(Path(__file__).resolve().parents[2])
if _repo not in sys.path:
    sys.path.insert(0, _repo)

# Triggers the shared discord mock from tests/gateway/conftest.py before
# importing the production module.
from plugins.platforms.discord.adapter import (  # noqa: E402
    ClarifyChoiceView,
    DiscordAdapter,
)
from gateway.config import PlatformConfig  # noqa: E402


# The test-suite-wide conftest replaces the real ``discord`` module
# with a fake one whose UI classes are named ``_FakeSelect`` /
# ``_FakeButton`` / ``_FakeSelectOption`` instead of the real names.
# Real production uses ``discord.ui.Select`` etc. — both expose the
# same constructor signature. We import the names we need to detect
# them by class identity rather than by name.
import discord as _discord_for_test  # noqa: E402


def _is_select(child) -> bool:
    """True if the child is a Select menu (real or test-mocked)."""
    name = child.__class__.__name__
    if name in ("Select", "_FakeSelect"):
        return True
    # In case some other naming slips in, check by attribute shape.
    return hasattr(child, "options") and hasattr(child, "placeholder")


def _is_button(child) -> bool:
    """True if the child is a Button (real or test-mocked)."""
    name = child.__class__.__name__
    return name in ("Button", "_FakeButton")



# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_adapter(*, allowed_users=None, allowed_roles=None):
    config = PlatformConfig(enabled=True, token="test-token", extra={})
    adapter = DiscordAdapter(config)
    adapter._client = MagicMock()
    adapter._allowed_user_ids = set(allowed_users or [])
    adapter._allowed_role_ids = set(allowed_roles or [])
    return adapter


def _clear_clarify_state():
    from tools import clarify_gateway as cm
    with cm._lock:
        cm._entries.clear()
        cm._session_index.clear()
        cm._notify_cbs.clear()


def _make_interaction(*, user_id="42", display_name="Tester", roles=None,
                      include_message=True):
    """Build a mock discord.Interaction with response.edit_message /
    send_message / defer all coroutine-callable."""
    user = SimpleNamespace(
        id=user_id,
        display_name=display_name,
        roles=[SimpleNamespace(id=r) for r in (roles or [])],
    )
    response = SimpleNamespace(
        edit_message=AsyncMock(),
        send_message=AsyncMock(),
        defer=AsyncMock(),
    )
    if include_message:
        embed = MagicMock()
        embed.color = None
        embed.set_footer = MagicMock()
        message = SimpleNamespace(embeds=[embed])
    else:
        message = None
    return SimpleNamespace(user=user, response=response, message=message)


# ===========================================================================
# ClarifyChoiceView construction
# ===========================================================================

class TestClarifyChoiceViewConstruction:
    """The view should build numeric buttons plus an Other button."""

    def test_renders_n_choice_buttons_plus_other(self):
        # 2 choices → buttons (one per choice + 1 Other button = 3 children)
        view = ClarifyChoiceView(
            choices=["apple", "banana"],
            clarify_id="cidX",
            allowed_user_ids={"42"},
        )
        assert len(view.children) == 3
        labels = [b.label for b in view.children]
        assert labels[0].startswith("1. apple")
        assert labels[1].startswith("2. banana")
        assert "Other" in labels[2]
        # custom_ids encode clarify_id + index/other
        ids = [b.custom_id for b in view.children]
        assert ids[0] == "clarify:cidX:0"
        assert ids[1] == "clarify:cidX:1"
        assert ids[2] == "clarify:cidX:other"

    def test_renders_3_choices_as_select_menu(self):
        # 3 choices → Select menu (1 child with 4 options: 3 real + Other)
        view = ClarifyChoiceView(
            choices=["apple", "banana", "cherry"],
            clarify_id="cidX",
            allowed_user_ids={"42"},
        )
        assert len(view.children) == 1
        select = view.children[0]
        # Inside the select: 3 numbered choices + Other
        option_labels = [opt.label for opt in select.options]
        assert option_labels[0] == "apple"
        assert option_labels[1] == "banana"
        assert option_labels[2] == "cherry"
        assert "Other" in option_labels[3]
        # custom_id encodes the clarify_id
        assert select.custom_id == "clarify:cidX"

    def test_caps_at_24_choices_plus_other(self):
        # 2 choices stay as buttons; only the 25-cap test applies to
        # the Select path which has its own test. Here we verify that
        # a long list of button choices still gets capped at the
        # MAX_SELECT_OPTIONS - 1 (24) cap before rendering.
        choices = [f"choice-{i}" for i in range(50)]
        view = ClarifyChoiceView(
            choices=choices,
            clarify_id="cidY",
            allowed_user_ids=set(),
        )
        # Either path (buttons for 2, select for 3+) — at most 24 real
        # choices + 1 Other surface in the UI. The tool's MAX_CHOICES=4
        # already caps the input upstream, so the practical cap here
        # is much smaller, but the view's defence-in-depth cap must
        # still apply if a caller bypasses the tool.
        # For Select: at most 25 options (24 real + 1 Other)
        # For buttons: at most 25 buttons (24 real + 1 Other)
        if len(view.children) == 1 and _is_select(view.children[0]):
            assert len(view.children[0].options) <= 25
            assert "Other" in view.children[0].options[-1].label
        else:
            # Button path: 24 + 1 Other = 25 max
            assert len(view.children) <= 25
            assert "Other" in view.children[-1].label

    def test_truncates_long_choice_label(self):
        long_choice = "x" * 200
        view = ClarifyChoiceView(
            choices=[long_choice],
            clarify_id="cidZ",
            allowed_user_ids=set(),
        )
        # 75 chars + 3 ellipsis chars in the body, plus "1. " prefix
        first_label = view.children[0].label
        assert first_label.startswith("1. ")
        assert first_label.endswith("...")
        # Final label total <= 80 (Discord cap on button labels)
        assert len(first_label) <= 80

    def test_dict_choices_dont_leak_python_repr(self):
        """Regression: models sometimes pass dict choices like
        ``{'key': 'cc', 'value': 'Claude Code CLI (Anthropic) — recommended default'}``
        to the clarify tool. The view MUST render the human-readable
        ``value`` field, never the Python ``str(dict)`` repr — that
        corrupted form was making Discord buttons unreadable.
        """
        view = ClarifyChoiceView(
            choices=[
                {"key": "cc", "value": "Claude Code CLI (Anthropic) — recommended default"},
                {"key": "oc", "value": "OpenCode CLI — open-source, provider-agnostic"},
            ],
            clarify_id="cidD",
            allowed_user_ids=set(),
        )
        labels = [b.label for b in view.children]
        # Two real choices + Other button
        assert len(view.children) == 3
        # First two labels must contain the human-readable value, not the dict repr
        assert "Claude Code CLI" in labels[0]
        assert "{" not in labels[0], f"dict repr leaked into button: {labels[0]!r}"
        assert "key" not in labels[0], f"key field leaked: {labels[0]!r}"
        assert "OpenCode CLI" in labels[1]
        assert "{" not in labels[1], f"dict repr leaked: {labels[1]!r}"
        # Other button still present
        assert "Other" in labels[2]

    def test_dict_choices_fall_back_to_label(self):
        """If the dict has no 'value' field, fall back to 'label'."""
        view = ClarifyChoiceView(
            choices=[{"label": "Apple", "description": "red fruit"}],
            clarify_id="cidL",
            allowed_user_ids=set(),
        )
        labels = [b.label for b in view.children]
        assert "Apple" in labels[0]
        assert "{" not in labels[0]

    def test_three_choices_uses_select_menu(self):
        """>2 choices should use a Select menu (drop-up) instead of buttons,
        so descriptions don't get truncated at Discord's 80-char button cap.
        Each Select option gets label + description rows."""
        view = ClarifyChoiceView(
            choices=[
                {"value": "Install Claude Code", "description": "Recommended default, strongest reasoning"},
                {"value": "Install OpenCode", "description": "Provider-agnostic, BYO API keys"},
                {"value": "Install Codex", "description": "OpenAI, batch issue fixing"},
            ],
            clarify_id="cidM",
            allowed_user_ids=set(),
        )
        select_children = [c for c in view.children if _is_select(c)]
        button_children = [c for c in view.children if _is_button(c)]
        assert len(select_children) == 1, f"expected 1 Select, got {len(select_children)}"
        assert len(button_children) == 0, f"expected 0 Buttons, got {len(button_children)}"
        sel = select_children[0]
        labels = [opt.label for opt in sel.options]
        descs = [opt.description for opt in sel.options]
        assert "Install Claude Code" in labels
        assert "Recommended default, strongest reasoning" in descs
        assert "Other" in labels[-1]

    def test_two_choices_still_uses_buttons(self):
        """≤2 choices should stay as buttons (faster for yes/no)."""
        view = ClarifyChoiceView(
            choices=["Yes", "No"],
            clarify_id="cidYN",
            allowed_user_ids=set(),
        )
        select_children = [c for c in view.children if _is_select(c)]
        button_children = [c for c in view.children if _is_button(c)]
        assert len(select_children) == 0
        assert len(button_children) == 3  # 2 choices + 1 Other button

    def test_select_menu_truncates_long_descriptions(self):
        """Discord Select option.description caps at 100 chars; we truncate
        with an ellipsis to fit the platform constraint."""
        # We use 3 choices (the minimum that triggers the Select path)
        view = ClarifyChoiceView(
            choices=[
                {"value": "X", "description": "d" * 200},
                {"value": "Y", "description": "ok"},
                {"value": "Z", "description": "ok"},
            ],
            clarify_id="cidD",
            allowed_user_ids=set(),
        )
        select_children = [c for c in view.children if _is_select(c)]
        assert len(select_children) == 1
        sel = select_children[0]
        real_option = sel.options[0]
        assert len(real_option.description) <= 100
        assert real_option.description.endswith("...")

    def test_select_menu_other_row_appended(self):
        """A trailing "Other" row is appended to every Select menu so
        the user can still type a custom answer. Tool layer caps at
        4 real choices (MAX_CHOICES), so the Select has at most 5
        options (4 real + 1 Other). Discord's 25-option cap is never
        reached at the tool's max."""
        view = ClarifyChoiceView(
            choices=[{"value": f"choice-{i}"} for i in range(4)],
            clarify_id="cidMax",
            allowed_user_ids=set(),
        )
        select_children = [c for c in view.children if _is_select(c)]
        assert len(select_children) == 1
        sel = select_children[0]
        # 4 real + 1 Other = 5
        assert len(sel.options) == 5
        # First 4 are the real choices
        for i, opt in enumerate(sel.options[:4]):
            assert opt.label == f"choice-{i}"
        # Last is Other
        assert "Other" in sel.options[-1].label

    def test_choice_resolves_via_select_option(self):
        """When a Select option is chosen, it should resolve the clarify
        with the option's label, not just the index."""
        view = ClarifyChoiceView(
            choices=["apple", "banana", "cherry"],
            clarify_id="cidS",
            allowed_user_ids=set(),
        )
        select_children = [c for c in view.children if _is_select(c)]
        sel = select_children[0]
        # The custom_id encodes the clarify_id
        assert sel.custom_id == "clarify:cidS"
        # The option values are what gets sent to the interaction callback
        option_values = [opt.value for opt in sel.options[:3]]
        assert "0" in option_values
        assert "1" in option_values
        assert "2" in option_values
        # The labels carry the actual choice text (not the index)
        option_labels = [opt.label for opt in sel.options[:3]]
        assert option_labels == ["apple", "banana", "cherry"]


# ===========================================================================
# Choice callback → resolve_gateway_clarify
# ===========================================================================

class TestClarifyChoiceResolve:
    """Clicking a numeric button should resolve the clarify entry."""

    def setup_method(self):
        _clear_clarify_state()

    @pytest.mark.asyncio
    async def test_choice_resolves_with_canonical_choice_text(self):
        from tools import clarify_gateway as cm
        cm.register("cidA", "sk-A", "Pick", ["red", "green", "blue"])

        view = ClarifyChoiceView(
            choices=["red", "green", "blue"],
            clarify_id="cidA",
            allowed_user_ids={"42"},
        )

        interaction = _make_interaction(user_id="42")
        await view._resolve_choice(interaction, index=1, choice="green")

        # Resolved through clarify primitive
        with cm._lock:
            entry = cm._entries.get("cidA")
        assert entry is not None
        assert entry.response == "green"
        assert entry.event.is_set()
        # Buttons disabled
        assert all(b.disabled for b in view.children)
        # Embed updated + edit_message called
        interaction.response.edit_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_choice_falls_back_to_label_text_when_entry_missing(self):
        """If the gateway entry vanished (race / stale view), the button's
        own choice text is used as the response."""
        # Note: no cm.register() — entry intentionally absent

        view = ClarifyChoiceView(
            choices=["alpha"],
            clarify_id="cidGone",
            allowed_user_ids={"42"},  # matches _make_interaction's user; empty = fail-closed
        )
        interaction = _make_interaction()
        # Doesn't raise; resolve_gateway_clarify returns False quietly
        await view._resolve_choice(interaction, index=0, choice="alpha")
        # Still marks the view resolved + disables buttons
        assert view.resolved is True
        assert all(b.disabled for b in view.children)

    @pytest.mark.asyncio
    async def test_already_resolved_sends_ephemeral_reply(self):
        view = ClarifyChoiceView(
            choices=["a", "b"],
            clarify_id="cidB",
            allowed_user_ids=set(),
        )
        view.resolved = True

        interaction = _make_interaction()
        await view._resolve_choice(interaction, index=0, choice="a")

        interaction.response.send_message.assert_called_once()
        kwargs = interaction.response.send_message.call_args.kwargs
        assert kwargs.get("ephemeral") is True
        # No resolve was called
        interaction.response.edit_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_unauthorized_user_rejected(self):
        from tools import clarify_gateway as cm
        cm.register("cidC", "sk-C", "Pick", ["x"])

        # Allowlist set, user not in it
        view = ClarifyChoiceView(
            choices=["x"],
            clarify_id="cidC",
            allowed_user_ids={"99999"},  # not 42
        )

        interaction = _make_interaction(user_id="42")
        await view._resolve_choice(interaction, index=0, choice="x")

        # Ephemeral rejection, no resolution, no edit
        interaction.response.send_message.assert_called_once()
        kwargs = interaction.response.send_message.call_args.kwargs
        assert kwargs.get("ephemeral") is True
        interaction.response.edit_message.assert_not_called()
        with cm._lock:
            entry = cm._entries.get("cidC")
        assert entry is not None
        assert not entry.event.is_set()


# ===========================================================================
# "Other" button → mark_awaiting_text
# ===========================================================================

class TestClarifyOtherButton:
    """Clicking Other should flip the entry into text-capture mode."""

    def setup_method(self):
        _clear_clarify_state()

    @pytest.mark.asyncio
    async def test_other_flips_entry_to_awaiting_text(self):
        from tools import clarify_gateway as cm
        cm.register("cidD", "sk-D", "Pick", ["x", "y"])

        view = ClarifyChoiceView(
            choices=["x", "y"],
            clarify_id="cidD",
            allowed_user_ids={"42"},  # matches _make_interaction's user; empty = fail-closed
        )

        interaction = _make_interaction()
        await view._on_other(interaction)

        # Entry awaiting_text now
        pending = cm.get_pending_for_session("sk-D")
        assert pending is not None
        assert pending.clarify_id == "cidD"
        assert pending.awaiting_text is True
        # Entry still pending (not resolved)
        with cm._lock:
            entry = cm._entries.get("cidD")
        assert entry is not None
        assert not entry.event.is_set()
        # View locked + buttons disabled
        assert view.resolved is True
        assert all(b.disabled for b in view.children)
        interaction.response.edit_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_other_unauthorized_user_rejected(self):
        from tools import clarify_gateway as cm
        cm.register("cidE", "sk-E", "Pick", ["x"])

        view = ClarifyChoiceView(
            choices=["x"],
            clarify_id="cidE",
            allowed_user_ids={"99999"},
        )

        interaction = _make_interaction(user_id="42")
        await view._on_other(interaction)

        # Rejected; entry NOT awaiting text
        interaction.response.send_message.assert_called_once()
        pending = cm.get_pending_for_session("sk-E")
        assert pending is None or pending.awaiting_text is False


# ===========================================================================
# DiscordAdapter.send_clarify integration
# ===========================================================================

class TestDiscordSendClarify:
    """Verify send_clarify renders an embed and (optionally) attaches the view."""

    def setup_method(self):
        _clear_clarify_state()

    @pytest.mark.asyncio
    async def test_multi_choice_attaches_view(self):
        adapter = _make_adapter(allowed_users={"42"})
        channel = MagicMock()
        sent_msg = MagicMock()
        sent_msg.id = 123456
        channel.send = AsyncMock(return_value=sent_msg)
        adapter._client.get_channel = MagicMock(return_value=channel)

        result = await adapter.send_clarify(
            chat_id="9001",
            question="Pick a color",
            choices=["red", "green", "blue"],
            clarify_id="cidM",
            session_key="sk-M",
        )

        assert result.success is True
        assert result.message_id == "123456"
        # Verify channel.send was called with embed + view kwargs
        channel.send.assert_called_once()
        kwargs = channel.send.call_args.kwargs
        assert "embed" in kwargs
        assert "view" in kwargs
        assert isinstance(kwargs["view"], ClarifyChoiceView)
        # 3 choices → Select menu (1 child with 4 options: 3 real + Other)
        view = kwargs["view"]
        assert len(view.children) == 1
        select = view.children[0]
        assert len(select.options) == 4
        assert "Other" in select.options[-1].label
        # The view should also carry the question for the Select placeholder
        assert view.question == "Pick a color"

    @pytest.mark.asyncio
    async def test_open_ended_omits_view(self):
        adapter = _make_adapter()
        channel = MagicMock()
        sent_msg = MagicMock()
        sent_msg.id = 222
        channel.send = AsyncMock(return_value=sent_msg)
        adapter._client.get_channel = MagicMock(return_value=channel)

        result = await adapter.send_clarify(
            chat_id="9001",
            question="What is your name?",
            choices=None,
            clarify_id="cidOE",
            session_key="sk-OE",
        )

        assert result.success is True
        channel.send.assert_called_once()
        kwargs = channel.send.call_args.kwargs
        # Open-ended path renders embed but no view (text-capture handles reply)
        assert "embed" in kwargs
        assert "view" not in kwargs

    @pytest.mark.asyncio
    async def test_routes_to_thread_when_metadata_thread_id_set(self):
        adapter = _make_adapter()
        channel = MagicMock()
        sent_msg = MagicMock()
        sent_msg.id = 333
        channel.send = AsyncMock(return_value=sent_msg)
        adapter._client.get_channel = MagicMock(return_value=channel)

        await adapter.send_clarify(
            chat_id="9001",
            question="?",
            choices=["a"],
            clarify_id="cidT",
            session_key="sk-T",
            metadata={"thread_id": "7777"},
        )

        # Channel lookup should resolve to thread id, not chat_id
        adapter._client.get_channel.assert_called_once_with(7777)

    @pytest.mark.asyncio
    async def test_not_connected_returns_failure(self):
        adapter = _make_adapter()
        adapter._client = None
        result = await adapter.send_clarify(
            chat_id="9001",
            question="?",
            choices=["a"],
            clarify_id="cidNC",
            session_key="sk-NC",
        )
        assert result.success is False
        assert "Not connected" in (result.error or "")

    @pytest.mark.asyncio
    async def test_filters_empty_and_whitespace_choices(self):
        adapter = _make_adapter()
        channel = MagicMock()
        sent_msg = MagicMock()
        sent_msg.id = 444
        channel.send = AsyncMock(return_value=sent_msg)
        adapter._client.get_channel = MagicMock(return_value=channel)

        await adapter.send_clarify(
            chat_id="9001",
            question="?",
            choices=["", "  ", "real-choice", None],
            clarify_id="cidF",
            session_key="sk-F",
        )
        kwargs = channel.send.call_args.kwargs
        view = kwargs["view"]
        # Only 1 real choice → falls into button path (≤2): 1 button + 1 Other
        assert len(view.children) == 2
        assert "real-choice" in view.children[0].label

    @pytest.mark.asyncio
    async def test_select_option_click_resolves_clarify(self):
        """End-to-end: simulate a user clicking a Select option and verify
        the gateway clarify entry resolves with the option's label."""
        from tools import clarify_gateway as cm

        adapter = _make_adapter(allowed_users={"42"})
        channel = MagicMock()
        sent_msg = MagicMock()
        sent_msg.id = 555
        channel.send = AsyncMock(return_value=sent_msg)
        adapter._client.get_channel = MagicMock(return_value=channel)

        # 3 choices → Select menu
        await adapter.send_clarify(
            chat_id="9001",
            question="Pick one",
            choices=[
                {"value": "alpha", "description": "first"},
                {"value": "beta", "description": "second"},
                {"value": "gamma", "description": "third"},
            ],
            clarify_id="cidSel",
            session_key="sk-Sel",
        )
        view = channel.send.call_args.kwargs["view"]
        # Get the Select
        select = next(c for c in view.children if _is_select(c))

        # Register a pending clarify entry so the resolve path can find it
        with cm._lock:
            cm._entries["cidSel"] = cm._ClarifyEntry(
                clarify_id="cidSel",
                session_key="sk-Sel",
                question="Pick one",
                choices=["alpha", "beta", "gamma"],
            )
        try:
            # Simulate the user picking the second option ("beta")
            interaction = _make_interaction(user_id="42", display_name="Tester")
            interaction.data = {"values": ["1"]}  # "1" = index of "beta"
            await view._on_select(interaction)

            # The clarify entry should be resolved with "beta"
            entry = cm._entries.get("cidSel")
            assert entry is not None
            assert entry.response == "beta"
            # The interaction should have responded
            interaction.response.edit_message.assert_called_once()
        finally:
            _clear_clarify_state()

    @pytest.mark.asyncio
    async def test_select_other_option_routes_to_text_capture(self):
        """Selecting the 'Other' row in the Select should flip the clarify
        entry into text-capture mode (same as the Other button)."""
        from tools import clarify_gateway as cm

        adapter = _make_adapter(allowed_users={"42"})
        channel = MagicMock()
        sent_msg = MagicMock()
        sent_msg.id = 666
        channel.send = AsyncMock(return_value=sent_msg)
        adapter._client.get_channel = MagicMock(return_value=channel)

        await adapter.send_clarify(
            chat_id="9001",
            question="Pick one",
            choices=["alpha", "beta", "gamma"],
            clarify_id="cidOther",
            session_key="sk-Other",
        )
        view = channel.send.call_args.kwargs["view"]
        select = next(c for c in view.children if _is_select(c))

        with cm._lock:
            cm._entries["cidOther"] = cm._ClarifyEntry(
                clarify_id="cidOther",
                session_key="sk-Other",
                question="Pick one",
                choices=["alpha", "beta", "gamma"],
            )
        try:
            interaction = _make_interaction(user_id="42", display_name="Tester")
            interaction.data = {"values": ["other"]}
            await view._on_select(interaction)

            # The entry should be marked as awaiting text, not resolved
            entry = cm._entries.get("cidOther")
            assert entry is not None
            assert entry.awaiting_text is True
            assert entry.response is None
        finally:
            _clear_clarify_state()
