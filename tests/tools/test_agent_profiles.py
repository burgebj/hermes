#!/usr/bin/env python3
"""
Tests for the agent profiles feature (issue #9459).

Covers:
  - _load_agent_profile: found, missing, bad config
  - _resolve_profile_system_prompt: inline / file / fallback priority
  - _build_child_agent: profile overrides (model, toolsets, max_iter, delegation creds)
  - build_delegate_task_schema: profile list injected into description
  - delegate_task: top-level profile + per-task profile in batch mode
  - _build_child_system_prompt_with_profiles: orchestrator prompt injection
"""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# ── install stubs before importing the module under test ──────────────────
import stub_missing  # noqa: F401

sys.path.insert(0, ".")

from tools.delegate_tool import (
    _load_agent_profile,
    _load_full_config,
    _resolve_profile_system_prompt,
    build_delegate_task_schema,
    DELEGATE_TASK_SCHEMA,
    _build_child_system_prompt,
    _build_child_system_prompt_with_profiles,
    _build_child_agent,
    delegate_task,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_mock_parent(depth=0):
    parent = MagicMock()
    parent.base_url = "https://openrouter.ai/api/v1"
    parent.api_key = "test-key"
    parent.provider = "openrouter"
    parent.api_mode = "chat_completions"
    parent.model = "gpt-4o"
    parent.max_tokens = None
    parent.reasoning_config = None
    parent.prefill_messages = None
    parent.platform = "cli"
    parent.acp_command = None
    parent.acp_args = []
    parent.providers_allowed = []
    parent.providers_ignored = []
    parent.providers_order = []
    parent.provider_sort = None
    parent._delegate_depth = depth
    parent._subagent_id = None
    parent.enabled_toolsets = ["terminal", "file", "web"]
    parent.valid_tool_names = []
    parent._active_children = []
    parent._active_children_lock = __import__("threading").Lock()
    parent._print_fn = None
    return parent


SAMPLE_PROFILES = {
    "explorer": {
        "model": "google/gemini-2.5-flash",
        "toolsets": ["file"],
        "max_iterations": 30,
        "description": "Fast read-only codebase explorer",
    },
    "oracle": {
        "model": "anthropic/claude-opus-4",
        "toolsets": ["file", "web"],
        "system_prompt": "You are a wise oracle.",
        "description": "Architecture decisions",
    },
    "fixer": {
        "model": "meta-llama/llama-4-maverick",
        "toolsets": ["terminal", "file"],
        "max_iterations": 20,
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# 1. _load_agent_profile
# ─────────────────────────────────────────────────────────────────────────────

class TestLoadAgentProfile(unittest.TestCase):

    def _patch_profiles(self, profiles):
        return patch(
            "tools.delegate_tool._load_full_config",
            return_value={"agent_profiles": profiles},
        )

    def test_returns_profile_when_found(self):
        with self._patch_profiles(SAMPLE_PROFILES):
            result = _load_agent_profile("explorer")
        self.assertIsNotNone(result)
        self.assertEqual(result["model"], "google/gemini-2.5-flash")

    def test_returns_none_for_empty_name(self):
        with self._patch_profiles(SAMPLE_PROFILES):
            self.assertIsNone(_load_agent_profile(""))
            self.assertIsNone(_load_agent_profile(None))

    def test_warns_and_returns_none_when_not_found(self):
        with self._patch_profiles(SAMPLE_PROFILES):
            with self.assertLogs("tools.delegate_tool", level="WARNING") as cm:
                result = _load_agent_profile("nonexistent")
        self.assertIsNone(result)
        self.assertTrue(any("nonexistent" in line for line in cm.output))

    def test_returns_none_when_no_profiles_configured(self):
        with patch("tools.delegate_tool._load_full_config", return_value={}):
            result = _load_agent_profile("explorer")
        self.assertIsNone(result)

    def test_handles_config_load_exception(self):
        with patch("tools.delegate_tool._load_full_config", side_effect=Exception("boom")):
            result = _load_agent_profile("explorer")
        self.assertIsNone(result)


# ─────────────────────────────────────────────────────────────────────────────
# 2. _resolve_profile_system_prompt
# ─────────────────────────────────────────────────────────────────────────────

class TestResolveProfileSystemPrompt(unittest.TestCase):

    def _base_kwargs(self, **overrides):
        kwargs = dict(
            workspace_path=None, role="leaf",
            max_spawn_depth=2, child_depth=1
        )
        kwargs.update(overrides)
        return kwargs

    def test_inline_system_prompt_takes_priority(self):
        profile = {"system_prompt": "You are a specialist.", "system_prompt_file": "/nonexistent"}
        result = _resolve_profile_system_prompt(
            profile, "Fix the bug", None, **self._base_kwargs()
        )
        self.assertIn("You are a specialist.", result)
        self.assertIn("Fix the bug", result)

    def test_inline_prompt_includes_goal_and_context(self):
        profile = {"system_prompt": "Expert agent."}
        result = _resolve_profile_system_prompt(
            profile, "Do X", "Context: Y", **self._base_kwargs()
        )
        self.assertIn("Expert agent.", result)
        self.assertIn("Do X", result)
        self.assertIn("Context: Y", result)

    def test_inline_prompt_includes_workspace_path(self):
        profile = {"system_prompt": "Agent."}
        result = _resolve_profile_system_prompt(
            profile, "Goal", None, workspace_path="/repo",
            role="leaf", max_spawn_depth=2, child_depth=1
        )
        self.assertIn("/repo", result)

    def test_system_prompt_file_used_when_no_inline(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("You are a file-based persona.")
            fname = f.name
        try:
            profile = {"system_prompt_file": fname}
            result = _resolve_profile_system_prompt(
                profile, "Goal", None, **self._base_kwargs()
            )
            self.assertIn("You are a file-based persona.", result)
            self.assertIn("Goal", result)
        finally:
            os.unlink(fname)

    def test_tilde_expanded_in_file_path(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md",
            dir=os.path.expanduser("~"), delete=False
        ) as f:
            f.write("Tilde persona.")
            fname = "~/" + os.path.basename(f.name)
        try:
            profile = {"system_prompt_file": fname}
            result = _resolve_profile_system_prompt(
                profile, "Goal", None, **self._base_kwargs()
            )
            self.assertIn("Tilde persona.", result)
        finally:
            os.unlink(os.path.expanduser(fname))

    def test_missing_file_falls_back_to_default(self):
        profile = {"system_prompt_file": "/absolutely/nonexistent/path.md"}
        result = _resolve_profile_system_prompt(
            profile, "Analyse code", None, **self._base_kwargs()
        )
        # Should fall back to standard subagent prompt
        self.assertIn("Analyse code", result)
        self.assertIn("focused subagent", result)

    def test_fallback_to_default_prompt_when_no_prompt_fields(self):
        profile = {"model": "gpt-4", "toolsets": ["file"]}
        result = _resolve_profile_system_prompt(
            profile, "Do something", "context here", **self._base_kwargs()
        )
        self.assertIn("Do something", result)
        self.assertIn("focused subagent", result)
        self.assertIn("context here", result)


# ─────────────────────────────────────────────────────────────────────────────
# 3. build_delegate_task_schema — dynamic profile injection
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildDelegateTaskSchema(unittest.TestCase):

    def test_profile_names_appear_in_description(self):
        schema = build_delegate_task_schema(SAMPLE_PROFILES)
        desc = schema["parameters"]["properties"]["profile"]["description"]
        for name in ("explorer", "oracle", "fixer"):
            self.assertIn(name, desc)

    def test_profile_model_appears_in_description(self):
        schema = build_delegate_task_schema(SAMPLE_PROFILES)
        desc = schema["parameters"]["properties"]["profile"]["description"]
        self.assertIn("google/gemini-2.5-flash", desc)

    def test_profile_description_field_appears(self):
        schema = build_delegate_task_schema(SAMPLE_PROFILES)
        desc = schema["parameters"]["properties"]["profile"]["description"]
        self.assertIn("Fast read-only codebase explorer", desc)

    def test_per_task_profile_also_updated(self):
        schema = build_delegate_task_schema(SAMPLE_PROFILES)
        task_props = schema["parameters"]["properties"]["tasks"]["items"]["properties"]
        task_desc = task_props["profile"]["description"]
        for name in ("explorer", "oracle", "fixer"):
            self.assertIn(name, task_desc)

    def test_does_not_mutate_original_schema(self):
        original_desc = DELEGATE_TASK_SCHEMA["parameters"]["properties"]["profile"]["description"]
        build_delegate_task_schema(SAMPLE_PROFILES)
        self.assertEqual(
            DELEGATE_TASK_SCHEMA["parameters"]["properties"]["profile"]["description"],
            original_desc,
        )

    def test_single_profile_no_crash(self):
        schema = build_delegate_task_schema({"solo": {"model": "gpt-4"}})
        desc = schema["parameters"]["properties"]["profile"]["description"]
        self.assertIn("solo", desc)


# ─────────────────────────────────────────────────────────────────────────────
# 4. _build_child_system_prompt_with_profiles
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildChildSystemPromptWithProfiles(unittest.TestCase):

    def test_leaf_role_no_profile_injection(self):
        result = _build_child_system_prompt_with_profiles(
            "Fix bug", None,
            workspace_path=None, role="leaf",
            max_spawn_depth=2, child_depth=1,
            available_profiles=SAMPLE_PROFILES,
        )
        self.assertNotIn("Available Agent Profiles", result)

    def test_orchestrator_gets_profile_list(self):
        result = _build_child_system_prompt_with_profiles(
            "Orchestrate", None,
            workspace_path=None, role="orchestrator",
            max_spawn_depth=2, child_depth=1,
            available_profiles=SAMPLE_PROFILES,
        )
        self.assertIn("Available Agent Profiles", result)
        for name in ("explorer", "oracle", "fixer"):
            self.assertIn(name, result)

    def test_orchestrator_no_profiles_no_injection(self):
        result = _build_child_system_prompt_with_profiles(
            "Orchestrate", None,
            workspace_path=None, role="orchestrator",
            max_spawn_depth=2, child_depth=1,
            available_profiles={},
        )
        self.assertNotIn("Available Agent Profiles", result)

    def test_orchestrator_profile_includes_model_info(self):
        result = _build_child_system_prompt_with_profiles(
            "Orchestrate", None,
            workspace_path=None, role="orchestrator",
            max_spawn_depth=2, child_depth=1,
            available_profiles=SAMPLE_PROFILES,
        )
        self.assertIn("google/gemini-2.5-flash", result)

    def test_none_profiles_arg_no_injection(self):
        result = _build_child_system_prompt_with_profiles(
            "Fix bug", None,
            workspace_path=None, role="orchestrator",
            max_spawn_depth=2, child_depth=1,
            available_profiles=None,
        )
        self.assertNotIn("Available Agent Profiles", result)


# ─────────────────────────────────────────────────────────────────────────────
# 5. _build_child_agent — profile field overrides
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildChildAgentProfileOverrides(unittest.TestCase):

    def _run_build(self, profile_cfg, parent_depth=0, **kwargs):
        parent = _make_mock_parent(depth=parent_depth)
        cfg_patch = patch(
            "tools.delegate_tool._load_config",
            return_value={"max_iterations": 50, "max_spawn_depth": 1,
                          "orchestrator_enabled": True, "inherit_mcp_toolsets": True},
        )
        full_cfg_patch = patch(
            "tools.delegate_tool._load_full_config",
            return_value={"agent_profiles": {}},
        )
        ai_agent_mock = MagicMock()
        ai_agent_patch = patch("run_agent.AIAgent", return_value=ai_agent_mock)
        with cfg_patch, full_cfg_patch, ai_agent_patch as mock_cls:
            child = _build_child_agent(
                task_index=0,
                goal="Do something",
                context=None,
                toolsets=None,
                model="gpt-4o",
                max_iterations=50,
                task_count=1,
                parent_agent=parent,
                profile_cfg=profile_cfg,
                **kwargs,
            )
            return mock_cls, child

    def test_profile_model_overrides_default(self):
        mock_cls, _ = self._run_build(
            profile_cfg={"model": "google/gemini-2.5-flash"}
        )
        call_kwargs = mock_cls.call_args[1]
        self.assertEqual(call_kwargs["model"], "google/gemini-2.5-flash")

    def test_profile_max_iterations_overrides_default(self):
        mock_cls, _ = self._run_build(
            profile_cfg={"max_iterations": 15}
        )
        call_kwargs = mock_cls.call_args[1]
        self.assertEqual(call_kwargs["max_iterations"], 15)

    def test_profile_toolsets_intersected_with_parent(self):
        """Profile asks for [file, terminal, web] but parent only has [file, terminal]."""
        parent = _make_mock_parent()
        parent.enabled_toolsets = ["file", "terminal"]

        cfg_patch = patch(
            "tools.delegate_tool._load_config",
            return_value={"max_iterations": 50, "max_spawn_depth": 1,
                          "orchestrator_enabled": True, "inherit_mcp_toolsets": False},
        )
        full_cfg_patch = patch(
            "tools.delegate_tool._load_full_config",
            return_value={"agent_profiles": {}},
        )
        ai_agent_mock = MagicMock()
        with cfg_patch, full_cfg_patch, patch("run_agent.AIAgent", return_value=ai_agent_mock) as mock_cls:
            _build_child_agent(
                task_index=0, goal="goal", context=None,
                toolsets=None, model="gpt-4o", max_iterations=50,
                task_count=1, parent_agent=parent,
                profile_cfg={"model": "x", "toolsets": ["file", "terminal", "web"]},
            )
        enabled = set(mock_cls.call_args[1]["enabled_toolsets"])
        self.assertIn("file", enabled)
        self.assertIn("terminal", enabled)
        self.assertNotIn("web", enabled)  # parent doesn't have it

    def test_no_profile_cfg_uses_passed_model(self):
        mock_cls, _ = self._run_build(profile_cfg=None)
        call_kwargs = mock_cls.call_args[1]
        self.assertEqual(call_kwargs["model"], "gpt-4o")

    def test_profile_delegation_provider_override(self):
        mock_cls, _ = self._run_build(
            profile_cfg={"delegation": {"provider": "openrouter", "api_key": "sk-abc"}}
        )
        # provider should not be None (it was set from profile)
        call_kwargs = mock_cls.call_args[1]
        # api_key set on child
        self.assertIsNotNone(call_kwargs.get("api_key") or call_kwargs.get("provider"))

    def test_profile_inline_prompt_used_as_system_prompt(self):
        ai_agent_mock = MagicMock()
        cfg_patch = patch(
            "tools.delegate_tool._load_config",
            return_value={"max_iterations": 50, "max_spawn_depth": 1,
                          "orchestrator_enabled": True, "inherit_mcp_toolsets": True},
        )
        full_cfg_patch = patch(
            "tools.delegate_tool._load_full_config",
            return_value={"agent_profiles": {}},
        )
        with cfg_patch, full_cfg_patch, patch("run_agent.AIAgent", return_value=ai_agent_mock) as mock_cls:
            parent = _make_mock_parent()
            _build_child_agent(
                task_index=0, goal="Do X", context=None,
                toolsets=None, model="gpt-4o", max_iterations=50,
                task_count=1, parent_agent=parent,
                profile_cfg={"system_prompt": "Custom persona here."},
            )
        prompt = mock_cls.call_args[1]["ephemeral_system_prompt"]
        self.assertIn("Custom persona here.", prompt)
        self.assertIn("Do X", prompt)


# ─────────────────────────────────────────────────────────────────────────────
# 6. delegate_task — end-to-end profile plumbing
# ─────────────────────────────────────────────────────────────────────────────

class TestDelegateTaskProfilePlumbing(unittest.TestCase):

    def _run_delegate(self, goal=None, tasks=None, profile=None, profiles_cfg=None):
        parent = _make_mock_parent()
        child_mock = MagicMock()
        child_mock.run = MagicMock(return_value=None)
        child_mock._subagent_goal = goal or (tasks[0]["goal"] if tasks else "g")
        child_mock._subagent_id = "sa-0-abc123"

        built_children = []

        def fake_build_child(**kwargs):
            built_children.append(kwargs)
            return child_mock

        creds = {"model": None, "provider": None, "base_url": None, "api_key": None, "api_mode": None}
        cfg_val = {"max_iterations": 50, "max_concurrent_children": 3}

        call_counter = {"n": 0}
        def fake_run_single(task_index, goal, child, parent_agent):
            i = task_index
            call_counter["n"] += 1
            return {"task_index": i, "goal": goal, "status": "completed",
                    "result": "ok", "summary": "done", "api_calls": 1,
                    "duration_seconds": 0.1, "_child_role": "leaf"}

        with patch("tools.delegate_tool._load_config", return_value=cfg_val), \
             patch("tools.delegate_tool._load_full_config",
                   return_value={"agent_profiles": profiles_cfg or {}}), \
             patch("tools.delegate_tool._resolve_delegation_credentials", return_value=creds), \
             patch("tools.delegate_tool._build_child_agent", side_effect=fake_build_child), \
             patch("tools.delegate_tool._run_single_child", side_effect=fake_run_single):
            result = delegate_task(
                goal=goal, tasks=tasks, profile=profile, parent_agent=parent
            )
        return json.loads(result), built_children

    def test_top_level_profile_passed_to_builder(self):
        profiles = {"explorer": {"model": "flash", "toolsets": ["file"]}}
        with patch("tools.delegate_tool._load_agent_profile",
                   return_value=profiles["explorer"]) as mock_load:
            result, children = self._run_delegate(
                goal="explore codebase", profile="explorer",
                profiles_cfg=profiles
            )
        self.assertEqual(len(children), 1)
        self.assertEqual(children[0]["profile_cfg"], profiles["explorer"])

    def test_no_profile_passes_none_to_builder(self):
        _, children = self._run_delegate(goal="simple task")
        self.assertEqual(len(children), 1)
        self.assertIsNone(children[0]["profile_cfg"])

    def test_per_task_profile_overrides_top_level(self):
        profiles = {
            "fast": {"model": "flash"},
            "slow": {"model": "opus"},
        }
        calls = []
        def mock_load(name):
            calls.append(name)
            return profiles.get(name)

        with patch("tools.delegate_tool._load_agent_profile", side_effect=mock_load):
            _, children = self._run_delegate(
                tasks=[
                    {"goal": "quick task", "profile": "fast"},
                    {"goal": "deep task", "profile": "slow"},
                ],
                profile="fast",  # top-level; per-task should beat it
                profiles_cfg=profiles,
            )
        # per-task profiles were used (load called with per-task names)
        self.assertIn("fast", calls)
        self.assertIn("slow", calls)
        self.assertEqual(children[0]["profile_cfg"], profiles["fast"])
        self.assertEqual(children[1]["profile_cfg"], profiles["slow"])

    def test_missing_profile_name_passes_none(self):
        with patch("tools.delegate_tool._load_agent_profile", return_value=None):
            _, children = self._run_delegate(
                goal="task", profile="nonexistent",
            )
        self.assertIsNone(children[0]["profile_cfg"])

    def test_backward_compat_no_profile_arg(self):
        """Calling delegate_task without profile= is unchanged."""
        result, children = self._run_delegate(goal="legacy task")
        self.assertIsNone(children[0]["profile_cfg"])
        result_data = result["results"][0]
        self.assertEqual(result_data["status"], "completed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
