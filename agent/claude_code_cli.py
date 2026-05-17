"""Claude Code CLI runtime adapter for Hermes.

This backend executes the first-party ``claude`` CLI directly instead of
calling the Anthropic API. It is intended for local subscription-backed runs
where Hermes should use Claude Code OAuth / Max on the host.
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import threading
import uuid
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Dict, Iterable, List, Optional

from hermes_cli.config import get_hermes_home, load_config

_HERMES_HOME = get_hermes_home()
_SESSION_BINDINGS_LOCK = threading.RLock()

CLAUDE_CODE_CLEAR_ENV = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_API_KEY_OLD",
    "ANTHROPIC_API_TOKEN",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_CUSTOM_HEADERS",
    "ANTHROPIC_OAUTH_TOKEN",
    "ANTHROPIC_TOKEN",
    "ANTHROPIC_UNIX_SOCKET",
    "CLAUDE_CONFIG_DIR",
    "CLAUDE_CODE_API_KEY_FILE_DESCRIPTOR",
    "CLAUDE_CODE_ENTRYPOINT",
    "CLAUDE_CODE_OAUTH_REFRESH_TOKEN",
    "CLAUDE_CODE_OAUTH_SCOPES",
    "CLAUDE_CODE_OAUTH_TOKEN",
    "CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR",
    "CLAUDE_CODE_PLUGIN_CACHE_DIR",
    "CLAUDE_CODE_PLUGIN_SEED_DIR",
    "CLAUDE_CODE_REMOTE",
    "CLAUDE_CODE_USE_BEDROCK",
    "CLAUDE_CODE_USE_COWORK_PLUGINS",
    "CLAUDE_CODE_USE_FOUNDRY",
    "CLAUDE_CODE_USE_VERTEX",
    "OTEL_EXPORTER_OTLP_ENDPOINT",
    "OTEL_EXPORTER_OTLP_HEADERS",
    "OTEL_EXPORTER_OTLP_LOGS_ENDPOINT",
    "OTEL_EXPORTER_OTLP_LOGS_HEADERS",
    "OTEL_EXPORTER_OTLP_LOGS_PROTOCOL",
    "OTEL_EXPORTER_OTLP_METRICS_ENDPOINT",
    "OTEL_EXPORTER_OTLP_METRICS_HEADERS",
    "OTEL_EXPORTER_OTLP_METRICS_PROTOCOL",
    "OTEL_EXPORTER_OTLP_PROTOCOL",
    "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
    "OTEL_EXPORTER_OTLP_TRACES_HEADERS",
    "OTEL_EXPORTER_OTLP_TRACES_PROTOCOL",
    "OTEL_LOGS_EXPORTER",
    "OTEL_METRICS_EXPORTER",
    "OTEL_SDK_DISABLED",
    "OTEL_TRACES_EXPORTER",
)


class ClaudeCodeCliError(RuntimeError):
    """Raised when the Claude Code subprocess fails."""


def _runtime_cfg() -> Dict[str, Any]:
    try:
        cfg = load_config().get("claude_code_runtime", {})
    except Exception:
        return {}
    return cfg if isinstance(cfg, dict) else {}


def _session_bindings_path() -> Path:
    cfg = _runtime_cfg()
    configured = str(cfg.get("session_store") or "").strip()
    if configured:
        return Path(os.path.expanduser(configured))
    return _HERMES_HOME / "state" / "claude-code-sessions.json"


def _configured_resume_enabled() -> bool:
    cfg = _runtime_cfg()
    value = cfg.get("resume")
    if isinstance(value, bool):
        return value
    return True


def _configured_model_aliases() -> Dict[str, str]:
    cfg = _runtime_cfg()
    raw = cfg.get("model_aliases")
    if not isinstance(raw, dict):
        return {}
    aliases: Dict[str, str] = {}
    for key, value in raw.items():
        key_norm = str(key).strip().lower()
        value_norm = str(value).strip()
        if key_norm and value_norm:
            aliases[key_norm] = value_norm
    return aliases


def resolve_claude_code_model(model: str) -> str:
    aliases = _configured_model_aliases()
    normalized = str(model or "").strip()
    return aliases.get(normalized.lower(), normalized)


def resolve_claude_code_args(*, stream: bool) -> List[str]:
    cfg = _runtime_cfg()
    raw_args = os.getenv("HERMES_CLAUDE_CODE_ARGS", "").strip()
    if raw_args:
        args = shlex.split(raw_args)
    else:
        configured = cfg.get("args")
        if isinstance(configured, list) and configured:
            args = [str(item) for item in configured if str(item).strip()]
        else:
            args = [
                "-p",
                "--output-format",
                "stream-json",
                "--include-partial-messages",
                "--verbose",
                "--setting-sources",
                "user",
                "--permission-mode",
                "bypassPermissions",
            ]
    if stream and "--include-partial-messages" not in args:
        args.append("--include-partial-messages")
    return args


def resolve_claude_code_command() -> str:
    cfg = _runtime_cfg()
    configured = (
        os.getenv("HERMES_CLAUDE_CODE_COMMAND", "").strip()
        or os.getenv("CLAUDE_CLI_PATH", "").strip()
        or str(cfg.get("command") or "").strip()
    )
    if configured:
        if os.path.sep in configured:
            return os.path.expanduser(configured)
        found = shutil.which(configured)
        if found:
            return found
    found = shutil.which("claude")
    if found:
        return found
    fallback = Path.home() / ".local" / "bin" / "claude"
    if fallback.is_file() and os.access(fallback, os.X_OK):
        return str(fallback)
    raise ClaudeCodeCliError(
        "Claude Code CLI not found. Install it or set HERMES_CLAUDE_CODE_COMMAND."
    )


def _load_session_bindings() -> Dict[str, str]:
    with _SESSION_BINDINGS_LOCK:
        try:
            data = json.loads(_session_bindings_path().read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except Exception:
            return {}
        if not isinstance(data, dict):
            return {}
        return {
            str(key): str(value)
            for key, value in data.items()
            if str(key).strip() and str(value).strip()
        }


def _save_session_binding(binding_key: str, claude_session_id: str) -> None:
    if not binding_key or not claude_session_id:
        return
    with _SESSION_BINDINGS_LOCK:
        bindings = _load_session_bindings()
        bindings[str(binding_key)] = str(claude_session_id)
        session_path = _session_bindings_path()
        session_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = session_path.with_suffix(".tmp")
        tmp_path.write_text(
            json.dumps(bindings, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp_path.replace(session_path)


def _delete_session_binding(binding_key: Optional[str]) -> None:
    if not binding_key:
        return
    with _SESSION_BINDINGS_LOCK:
        bindings = _load_session_bindings()
        if str(binding_key) not in bindings:
            return
        bindings.pop(str(binding_key), None)
        session_path = _session_bindings_path()
        session_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = session_path.with_suffix(".tmp")
        tmp_path.write_text(
            json.dumps(bindings, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp_path.replace(session_path)


def get_bound_claude_session_id(binding_key: Optional[str]) -> Optional[str]:
    if not binding_key:
        return None
    return _load_session_bindings().get(str(binding_key))


def _build_cli_env() -> Dict[str, str]:
    env = dict(os.environ)
    cfg = _runtime_cfg()
    extra_scrub = cfg.get("scrub_env")
    scrub_keys = list(CLAUDE_CODE_CLEAR_ENV)
    if isinstance(extra_scrub, list):
        scrub_keys.extend(str(key) for key in extra_scrub if str(key).strip())
    for key in scrub_keys:
        env.pop(key, None)
    env_home = os.getenv("HERMES_CLAUDE_CODE_HOME", "").strip()
    configured_home = env_home or str(
        cfg.get("home") or cfg.get("claude_home") or ""
    ).strip()
    if configured_home:
        home = Path(os.path.expandvars(os.path.expanduser(configured_home)))
        home.mkdir(parents=True, exist_ok=True)
        try:
            home.chmod(0o700)
        except OSError:
            pass
        env["HOME"] = str(home)
    env_config_dir = os.getenv("HERMES_CLAUDE_CODE_CONFIG_DIR", "").strip()
    configured_config_dir = env_config_dir
    if not configured_home:
        configured_config_dir = configured_config_dir or str(
            cfg.get("config_dir") or cfg.get("claude_config_dir") or ""
        ).strip()
    if configured_config_dir:
        config_dir = Path(os.path.expandvars(os.path.expanduser(configured_config_dir)))
        config_dir.mkdir(parents=True, exist_ok=True)
        try:
            config_dir.chmod(0o700)
        except OSError:
            pass
        env["CLAUDE_CONFIG_DIR"] = str(config_dir)
    env.setdefault("PATH", os.environ.get("PATH", ""))
    env.setdefault("HOME", str(Path.home()))
    return env


def _coerce_text_content(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, dict):
                item_type = str(item.get("type") or "")
                if item_type in {"text", "input_text"}:
                    parts.append(str(item.get("text") or ""))
                    continue
                if item_type == "image_url":
                    image_url = item.get("image_url")
                    if isinstance(image_url, dict):
                        image_url = image_url.get("url")
                    if image_url:
                        parts.append(f"[Image: {image_url}]")
                    continue
                if item_type == "tool_result":
                    text = item.get("content")
                    if text:
                        parts.append(str(text))
                    continue
            else:
                parts.append(str(item))
        return "\n".join(part for part in parts if part).strip()
    if isinstance(content, dict):
        return _coerce_text_content(content.get("content") or content.get("text") or "")
    return str(content)


def _extract_latest_user_message(messages: Iterable[Dict[str, Any]]) -> str:
    for message in reversed(list(messages)):
        if str(message.get("role") or "") == "user":
            text = _coerce_text_content(message.get("content"))
            if text.strip():
                return text.strip()
    return ""


def _render_prompt(messages: List[Dict[str, Any]], *, use_resume: bool) -> str:
    latest_user = _extract_latest_user_message(messages)
    if use_resume and latest_user:
        return latest_user

    non_system = [m for m in messages if str(m.get("role") or "") != "system"]
    if len(non_system) <= 1 and latest_user:
        return latest_user

    rendered: List[str] = []
    for message in non_system:
        role = str(message.get("role") or "user").strip().lower() or "user"
        header = {"assistant": "Assistant", "tool": "Tool", "user": "User"}.get(role, role.title())
        content = _coerce_text_content(message.get("content"))
        if content:
            rendered.append(f"{header}:\n{content}")

    if not rendered:
        return latest_user

    return (
        "Continue the following conversation faithfully.\n\n"
        + "\n\n".join(rendered)
        + "\n"
    ).strip()


def _extract_system_prompt(messages: List[Dict[str, Any]]) -> str:
    for message in messages:
        if str(message.get("role") or "") == "system":
            text = _coerce_text_content(message.get("content"))
            if text.strip():
                return text.strip()
    return ""


def _build_usage_object(raw_usage: Dict[str, Any]) -> Optional[SimpleNamespace]:
    if not isinstance(raw_usage, dict) or not raw_usage:
        return None

    prompt_tokens = int(raw_usage.get("input_tokens") or 0)
    prompt_tokens += int(raw_usage.get("cache_read_input_tokens") or 0)
    prompt_tokens += int(raw_usage.get("cache_creation_input_tokens") or 0)
    completion_tokens = int(raw_usage.get("output_tokens") or 0)
    prompt_details = SimpleNamespace(
        cached_tokens=int(raw_usage.get("cache_read_input_tokens") or 0),
        cache_write_tokens=int(raw_usage.get("cache_creation_input_tokens") or 0),
    )
    return SimpleNamespace(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        prompt_tokens_details=prompt_details,
        input_tokens=int(raw_usage.get("input_tokens") or 0),
        output_tokens=completion_tokens,
        cache_read_input_tokens=int(raw_usage.get("cache_read_input_tokens") or 0),
        cache_creation_input_tokens=int(raw_usage.get("cache_creation_input_tokens") or 0),
    )


def _response_from_text(*, text: str, model: str, usage: Optional[SimpleNamespace]) -> SimpleNamespace:
    message = SimpleNamespace(role="assistant", content=text, tool_calls=None, reasoning_content=None)
    choice = SimpleNamespace(index=0, message=message, finish_reason="stop")
    return SimpleNamespace(
        id=f"claude-code-{uuid.uuid4()}",
        model=model,
        choices=[choice],
        usage=usage,
    )


def run_claude_code_cli(
    *,
    messages: List[Dict[str, Any]],
    model: str,
    binding_key: Optional[str],
    cwd: Optional[str] = None,
    stream: bool = False,
    on_text_delta: Optional[Callable[[str], None]] = None,
    interrupt_check: Optional[Callable[[], bool]] = None,
    allow_resume_retry: bool = True,
) -> SimpleNamespace:
    """Execute Claude Code and return a chat.completions-style response."""
    command = resolve_claude_code_command()
    requested_model = resolve_claude_code_model(model)
    bound_session_id = get_bound_claude_session_id(binding_key) if _configured_resume_enabled() else None
    use_resume = bool(bound_session_id)
    prompt = _render_prompt(messages, use_resume=use_resume)
    system_prompt = _extract_system_prompt(messages) if not use_resume else ""

    if not prompt.strip():
        raise ClaudeCodeCliError("Claude Code prompt is empty.")

    args = [command, *resolve_claude_code_args(stream=stream), "--model", requested_model]
    if use_resume and bound_session_id:
        args.extend(["--resume", bound_session_id])
    if system_prompt:
        args.extend(["--append-system-prompt", system_prompt])

    env = _build_cli_env()
    workdir = os.path.expanduser(cwd or os.environ.get("TERMINAL_CWD", "") or "~")

    proc = subprocess.Popen(
        args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        cwd=workdir,
        env=env,
        bufsize=1,
    )

    assert proc.stdin is not None
    proc.stdin.write(prompt)
    if not prompt.endswith("\n"):
        proc.stdin.write("\n")
    proc.stdin.close()

    final_text = ""
    assistant_text = ""
    session_id = bound_session_id
    usage: Optional[SimpleNamespace] = None
    error_text = ""

    assert proc.stdout is not None
    for raw_line in proc.stdout:
        if interrupt_check and interrupt_check():
            proc.terminate()
            raise InterruptedError("Claude Code CLI run interrupted")

        line = raw_line.strip()
        if not line:
            continue

        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        if not isinstance(event, dict):
            continue
        event_session = event.get("session_id")
        if isinstance(event_session, str) and event_session.strip():
            session_id = event_session.strip()

        if event.get("type") == "assistant":
            message = event.get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, list):
                    text_parts = [
                        str(part.get("text") or "")
                        for part in content
                        if isinstance(part, dict) and part.get("type") == "text"
                    ]
                    if text_parts:
                        assistant_text = "".join(text_parts)

        if event.get("type") == "stream_event":
            payload = event.get("event")
            if isinstance(payload, dict) and payload.get("type") == "content_block_delta":
                delta = payload.get("delta")
                if isinstance(delta, dict) and delta.get("type") == "text_delta":
                    delta_text = str(delta.get("text") or "")
                    if delta_text:
                        assistant_text += delta_text
                        if on_text_delta:
                            on_text_delta(delta_text)

        if event.get("type") == "result":
            if event.get("is_error"):
                error_text = str(event.get("result") or "Claude Code CLI error")
            else:
                final_text = str(event.get("result") or "").strip()
                usage = _build_usage_object(event.get("usage") or {})
                result_session = event.get("session_id")
                if isinstance(result_session, str) and result_session.strip():
                    session_id = result_session.strip()

    stderr_text = ""
    if proc.stderr is not None:
        stderr_text = proc.stderr.read().strip()
    return_code = proc.wait()

    if not final_text:
        final_text = assistant_text.strip()

    if session_id and binding_key:
        _save_session_binding(binding_key, session_id)

    if error_text and use_resume and allow_resume_retry:
        _delete_session_binding(binding_key)
        return run_claude_code_cli(
            messages=messages,
            model=model,
            binding_key=binding_key,
            cwd=cwd,
            stream=stream,
            on_text_delta=on_text_delta,
            interrupt_check=interrupt_check,
            allow_resume_retry=False,
        )
    if error_text:
        raise ClaudeCodeCliError(error_text)
    if return_code != 0:
        detail = stderr_text or final_text or f"Claude Code exited with status {return_code}"
        raise ClaudeCodeCliError(detail)
    if not final_text:
        raise ClaudeCodeCliError("Claude Code returned an empty response.")

    return _response_from_text(text=final_text, model=requested_model, usage=usage)


class _ClaudeCodeCompletions:
    def __init__(self, client: "ClaudeCodeClient") -> None:
        self._client = client

    def create(self, **kwargs: Any) -> SimpleNamespace:
        return run_claude_code_cli(
            messages=list(kwargs.get("messages") or []),
            model=str(kwargs.get("model") or self._client.model or ""),
            binding_key=self._client.binding_key,
            cwd=os.getenv("TERMINAL_CWD"),
            stream=bool(kwargs.get("stream")),
        )


class _ClaudeCodeChat:
    def __init__(self, client: "ClaudeCodeClient") -> None:
        self.completions = _ClaudeCodeCompletions(client)


class ClaudeCodeClient:
    """Minimal chat.completions-compatible client backed by Claude Code CLI."""

    def __init__(
        self,
        *,
        api_key: str = "claude-code",
        base_url: str = "claude://local",
        model: str = "",
        binding_key: Optional[str] = None,
        **_: Any,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.binding_key = binding_key
        self.chat = _ClaudeCodeChat(self)
