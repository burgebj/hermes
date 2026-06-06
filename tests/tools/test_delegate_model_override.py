#!/usr/bin/env python3
"""Tests for the per-task and top-level model override in delegate_task.

This patch adds the ability to spawn child agents on different models
than the parent — typical use case is cost-aware routing:

    delegate_task(
        tasks=[
            {"goal": "list files in /tmp", "model": "anthropic/claude-haiku-4"},
            {"goal": "refactor auth module", "model": "anthropic/claude-opus-4.7"},
        ],
    )

Precedence rules verified here:
    1. per-task t["model"]
    2. top-level model arg
    3. delegation.model config (creds["model"])
    4. parent_agent.model (resolved inside _build_child_agent)

Plus: when delegation.provider is configured, user model overrides are
ignored so credentials/model stay coherent.

Run with:  python -m pytest tests/tools/test_delegate_model_override.py -v
"""

import threading
import unittest
from unittest.mock import MagicMock, patch

from tools.delegate_tool import (
    DELEGATE_TASK_SCHEMA,
    _build_dynamic_schema_overrides,
    delegate_task,
)


def _make_mock_parent(depth=0, model="anthropic/claude-sonnet-4"):
    """Mock parent agent compatible with delegate_task's expectations."""
    parent = MagicMock()
    parent.base_url = "https://openrouter.ai/api/v1"
    parent.api_key = "test-key"
    parent.provider = "openrouter"
    parent.api_mode = "chat_completions"
    parent.model = model
    parent.platform = "cli"
    parent.providers_allowed = None
    parent.providers_ignored = None
    parent.providers_order = None
    parent.provider_sort = None
    parent._session_db = None
    parent._delegate_depth = depth
    parent._active_children = []
    parent._active_children_lock = threading.Lock()
    parent._print_fn = None
    parent.tool_progress_callback = None
    parent.thinking_callback = None
    return parent


class TestSchemaExposesModel(unittest.TestCase):
    """The new `model` fields must be visible in both static and dynamic schemas."""

    def test_top_level_model_in_static_schema(self):
        props = DELEGATE_TASK_SCHEMA["parameters"]["properties"]
        self.assertIn("model", props)
        self.assertEqual(props["model"]["type"], "string")

    def test_per_task_model_in_static_schema(self):
        task_props = DELEGATE_TASK_SCHEMA["parameters"]["properties"]["tasks"]["items"][
            "properties"
        ]
        self.assertIn("model", task_props)
        self.assertEqual(task_props["model"]["type"], "string")

    def test_dynamic_schema_preserves_model_fields(self):
        """`_build_dynamic_schema_overrides` re-emits the static schema with
        runtime-aware descriptions for `tasks` and `role`. Both `model`
        fields must survive that rewrite."""
        overrides = _build_dynamic_schema_overrides()
        props = overrides["parameters"]["properties"]
        self.assertIn("model", props)
        self.assertIn("model", props["tasks"]["items"]["properties"])

    def test_model_description_mentions_cost_routing(self):
        """The schema description must teach the LLM what this field is for —
        otherwise it won't think to use it. The description in both
        top-level and per-task slots should mention model routing."""
        props = DELEGATE_TASK_SCHEMA["parameters"]["properties"]
        self.assertIn("model", props["model"]["description"].lower())
        per_task = props["tasks"]["items"]["properties"]["model"]["description"]
        self.assertIn("haiku", per_task.lower())
        self.assertIn("opus", per_task.lower())


class TestModelOverrideHonored(unittest.TestCase):
    """`delegate_task` should pass the resolved model into AIAgent(...)."""

    def test_per_task_model_passed_to_child(self):
        """A per-task `model` in `tasks=[{...}]` should reach AIAgent."""
        parent = _make_mock_parent()

        with patch("run_agent.AIAgent") as MockAgent:
            mock_child = MagicMock()
            mock_child.run_conversation.return_value = {
                "final_response": "ok", "completed": True, "api_calls": 1,
            }
            MockAgent.return_value = mock_child

            delegate_task(
                tasks=[{"goal": "trivial task",
                        "model": "anthropic/claude-haiku-4"}],
                parent_agent=parent,
            )

            _, kwargs = MockAgent.call_args
            self.assertEqual(kwargs["model"], "anthropic/claude-haiku-4")

    def test_top_level_model_passed_to_child(self):
        """A top-level `model` arg should reach AIAgent."""
        parent = _make_mock_parent()

        with patch("run_agent.AIAgent") as MockAgent:
            mock_child = MagicMock()
            mock_child.run_conversation.return_value = {
                "final_response": "ok", "completed": True, "api_calls": 1,
            }
            MockAgent.return_value = mock_child

            delegate_task(
                goal="some task",
                model="anthropic/claude-opus-4.7",
                parent_agent=parent,
            )

            _, kwargs = MockAgent.call_args
            self.assertEqual(kwargs["model"], "anthropic/claude-opus-4.7")

    def test_per_task_beats_top_level(self):
        """When both are set, the per-task value wins."""
        parent = _make_mock_parent()

        with patch("run_agent.AIAgent") as MockAgent:
            mock_child = MagicMock()
            mock_child.run_conversation.return_value = {
                "final_response": "ok", "completed": True, "api_calls": 1,
            }
            MockAgent.return_value = mock_child

            delegate_task(
                tasks=[{"goal": "task A",
                        "model": "anthropic/claude-haiku-4"}],
                model="anthropic/claude-opus-4.7",  # top-level fallback
                parent_agent=parent,
            )

            _, kwargs = MockAgent.call_args
            self.assertEqual(kwargs["model"], "anthropic/claude-haiku-4")

    def test_top_level_model_propagates_in_batch(self):
        """Top-level `model` should apply to every batch task that didn't set
        its own — mixed batch verifies the precedence cleanly."""
        parent = _make_mock_parent()

        captured_models = []

        def _capture(*args, **kwargs):
            captured_models.append(kwargs.get("model"))
            child = MagicMock()
            child.run_conversation.return_value = {
                "final_response": "ok", "completed": True, "api_calls": 1,
            }
            return child

        with patch("run_agent.AIAgent", side_effect=_capture):
            delegate_task(
                tasks=[
                    {"goal": "task A"},  # uses top-level
                    {"goal": "task B",
                     "model": "anthropic/claude-opus-4.7"},  # overrides
                    {"goal": "task C"},  # uses top-level
                ],
                model="anthropic/claude-haiku-4",
                parent_agent=parent,
            )

        self.assertEqual(captured_models, [
            "anthropic/claude-haiku-4",
            "anthropic/claude-opus-4.7",
            "anthropic/claude-haiku-4",
        ])

    def test_no_override_inherits_parent_model(self):
        """When no `model` override anywhere, child uses parent's model
        (because creds["model"] is None and _build_child_agent falls
        back to parent.model)."""
        parent = _make_mock_parent(model="anthropic/claude-sonnet-4")

        with patch("run_agent.AIAgent") as MockAgent:
            mock_child = MagicMock()
            mock_child.run_conversation.return_value = {
                "final_response": "ok", "completed": True, "api_calls": 1,
            }
            MockAgent.return_value = mock_child

            delegate_task(goal="task", parent_agent=parent)

            _, kwargs = MockAgent.call_args
            self.assertEqual(kwargs["model"], "anthropic/claude-sonnet-4")


class TestModelOverrideValidation(unittest.TestCase):
    """Edge cases around the model field type and falsy values."""

    def test_empty_string_model_falls_back(self):
        """An empty per-task `model: ""` should NOT override — falls back
        to top-level / creds / parent."""
        parent = _make_mock_parent(model="anthropic/claude-sonnet-4")

        with patch("run_agent.AIAgent") as MockAgent:
            mock_child = MagicMock()
            mock_child.run_conversation.return_value = {
                "final_response": "ok", "completed": True, "api_calls": 1,
            }
            MockAgent.return_value = mock_child

            delegate_task(
                tasks=[{"goal": "task", "model": ""}],
                parent_agent=parent,
            )

            _, kwargs = MockAgent.call_args
            self.assertEqual(kwargs["model"], "anthropic/claude-sonnet-4")

    def test_whitespace_only_model_falls_back(self):
        """`model: "   "` is treated as not-set."""
        parent = _make_mock_parent(model="anthropic/claude-sonnet-4")

        with patch("run_agent.AIAgent") as MockAgent:
            mock_child = MagicMock()
            mock_child.run_conversation.return_value = {
                "final_response": "ok", "completed": True, "api_calls": 1,
            }
            MockAgent.return_value = mock_child

            delegate_task(
                tasks=[{"goal": "task", "model": "   "}],
                parent_agent=parent,
            )

            _, kwargs = MockAgent.call_args
            self.assertEqual(kwargs["model"], "anthropic/claude-sonnet-4")

    def test_non_string_model_falls_back(self):
        """`model: 123` (wrong type) is silently ignored rather than crashing."""
        parent = _make_mock_parent(model="anthropic/claude-sonnet-4")

        with patch("run_agent.AIAgent") as MockAgent:
            mock_child = MagicMock()
            mock_child.run_conversation.return_value = {
                "final_response": "ok", "completed": True, "api_calls": 1,
            }
            MockAgent.return_value = mock_child

            delegate_task(
                tasks=[{"goal": "task", "model": 123}],
                parent_agent=parent,
            )

            _, kwargs = MockAgent.call_args
            self.assertEqual(kwargs["model"], "anthropic/claude-sonnet-4")

    def test_model_value_is_stripped(self):
        """Leading/trailing whitespace in model name is stripped."""
        parent = _make_mock_parent()

        with patch("run_agent.AIAgent") as MockAgent:
            mock_child = MagicMock()
            mock_child.run_conversation.return_value = {
                "final_response": "ok", "completed": True, "api_calls": 1,
            }
            MockAgent.return_value = mock_child

            delegate_task(
                tasks=[{"goal": "task",
                        "model": "  anthropic/claude-haiku-4  "}],
                parent_agent=parent,
            )

            _, kwargs = MockAgent.call_args
            self.assertEqual(kwargs["model"], "anthropic/claude-haiku-4")


class TestDelegationProviderTrumpsOverride(unittest.TestCase):
    """When `delegation.provider` is configured, the user-supplied model
    override is silently ignored so the provider-pinned credential
    bundle stays coherent (credentials + model from one source).
    """

    def test_provider_override_ignores_per_task_model(self):
        """If `_resolve_delegation_credentials` returns provider=set, the
        per-task model override is dropped in favour of creds["model"].
        """
        parent = _make_mock_parent()

        # Make _resolve_delegation_credentials return a "provider configured"
        # bundle so the precedence rule triggers.
        fake_creds = {
            "model": "z-ai/glm-4.6",  # delegation.model from config
            "provider": "z-ai",
            "base_url": "https://api.z.ai/v1",
            "api_key": "secret",
            "api_mode": "chat_completions",
        }

        with patch(
            "tools.delegate_tool._resolve_delegation_credentials",
            return_value=fake_creds,
        ), patch("run_agent.AIAgent") as MockAgent:
            mock_child = MagicMock()
            mock_child.run_conversation.return_value = {
                "final_response": "ok", "completed": True, "api_calls": 1,
            }
            MockAgent.return_value = mock_child

            delegate_task(
                tasks=[{"goal": "task",
                        "model": "anthropic/claude-haiku-4"}],
                parent_agent=parent,
            )

            _, kwargs = MockAgent.call_args
            # delegation.model wins; user override ignored.
            self.assertEqual(kwargs["model"], "z-ai/glm-4.6")
            self.assertEqual(kwargs["provider"], "z-ai")

    def test_provider_override_ignores_top_level_model(self):
        """Same rule applies to the top-level `model` arg."""
        parent = _make_mock_parent()
        fake_creds = {
            "model": "z-ai/glm-4.6",
            "provider": "z-ai",
            "base_url": "https://api.z.ai/v1",
            "api_key": "secret",
            "api_mode": "chat_completions",
        }

        with patch(
            "tools.delegate_tool._resolve_delegation_credentials",
            return_value=fake_creds,
        ), patch("run_agent.AIAgent") as MockAgent:
            mock_child = MagicMock()
            mock_child.run_conversation.return_value = {
                "final_response": "ok", "completed": True, "api_calls": 1,
            }
            MockAgent.return_value = mock_child

            delegate_task(
                goal="task",
                model="anthropic/claude-opus-4.7",
                parent_agent=parent,
            )

            _, kwargs = MockAgent.call_args
            self.assertEqual(kwargs["model"], "z-ai/glm-4.6")


class TestRegistryHandlerPlumbsModel(unittest.TestCase):
    """The registry handler must forward `args["model"]` into delegate_task."""

    def test_registry_handler_forwards_model(self):
        """The auto-generated lambda in registry.register must include
        model=args.get("model"). We verify by invoking the registry
        handler directly."""
        from tools.registry import registry

        entry = registry.get_entry("delegate_task")
        self.assertIsNotNone(entry, "delegate_task must be registered")

        parent = _make_mock_parent()
        with patch("run_agent.AIAgent") as MockAgent:
            mock_child = MagicMock()
            mock_child.run_conversation.return_value = {
                "final_response": "ok", "completed": True, "api_calls": 1,
            }
            MockAgent.return_value = mock_child

            entry.handler(
                {
                    "goal": "test",
                    "model": "anthropic/claude-haiku-4",
                },
                parent_agent=parent,
            )

            _, kwargs = MockAgent.call_args
            self.assertEqual(kwargs["model"], "anthropic/claude-haiku-4")


if __name__ == "__main__":
    unittest.main()
