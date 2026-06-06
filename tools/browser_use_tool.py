#!/usr/bin/env python3
"""
Browser Use Tool Module

Proof-of-concept wrapper around the browser-use Python library for
LLM-driven autonomous browser automation. This complements Hermes's
existing low-level browser_tool.py (navigate/snapshot/click/type) by
providing a high-level "do this task for me" capability.

Where browser_tool.py gives the LLM fine-grained control (each click is
a separate tool call), browser_use_tool.py lets the LLM describe a task
in natural language and have browser-use autonomously execute the steps.

Usage:
    from tools.browser_use_tool import browser_use_run, browser_use_extract

    # Run an autonomous browser task
    result = browser_use_run(
        task="Find the top 3 stories on Hacker News and return their titles",
        max_steps=15,
    )

    # Extract structured data from a URL
    data = browser_use_extract(
        url="https://example.com/pricing",
        instruction="Extract all pricing tiers with their names, prices, and features",
    )

Integration notes:
- Requires: pip install browser-use
- Optional: BROWSER_USE_API_KEY for cloud mode (no local Playwright needed)
- Falls back to local Playwright Chromium when no API key is set
- Uses the same url_safety and website_policy checks as browser_tool.py
"""

import json
import logging
import os
import tempfile
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Security: URL validation (reuse existing modules)
# ---------------------------------------------------------------------------

try:
    from tools.url_safety import is_safe_url as _is_safe_url
except Exception:
    _is_safe_url = lambda url: False  # noqa: E731 — fail-closed

try:
    from tools.website_policy import check_website_access
except Exception:
    check_website_access = lambda url: None  # noqa: E731 — fail-open


def _validate_url(url: str) -> Optional[str]:
    """Validate a URL for safety and policy compliance.

    Returns None if OK, or an error message string if blocked.
    """
    if not url or not url.strip():
        return "URL cannot be empty"
    url = url.strip()
    if not _is_safe_url(url):
        return f"URL blocked by safety policy: {url}"
    try:
        check_website_access(url)
    except Exception as e:
        return f"URL blocked by website policy: {e}"
    return None


# ---------------------------------------------------------------------------
# Availability check
# ---------------------------------------------------------------------------

_browser_use_available: Optional[bool] = None


def _check_browser_use_available() -> bool:
    """Check if browser-use library is installed and usable."""
    global _browser_use_available
    if _browser_use_available is not None:
        return _browser_use_available
    try:
        import browser_use  # noqa: F401
        _browser_use_available = True
    except ImportError:
        _browser_use_available = False
    return _browser_use_available


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def browser_use_run(
    task: str,
    max_steps: int = 25,
    model: str = None,
    url: str = None,
    use_vision: bool = False,
) -> str:
    """Run an autonomous browser task using browser-use.

    Args:
        task: Natural language description of what to do in the browser.
        max_steps: Maximum number of autonomous steps before stopping.
        model: LLM model for browser-use's internal agent (default: from env).
        url: Optional starting URL. If provided, navigates there first.
        use_vision: Whether to use screenshots for visual context.

    Returns:
        JSON string with task result, final page content, and metadata.
    """
    if not _check_browser_use_available():
        return json.dumps({
            "error": "browser-use library not installed. "
                     "Install with: pip install browser-use && playwright install chromium"
        })

    # Validate URL if provided
    if url:
        err = _validate_url(url)
        if err:
            return json.dumps({"error": err})

    # Resolve model
    if not model:
        model = os.getenv("BROWSER_USE_MODEL", "").strip() or None

    try:
        import asyncio
        from browser_use import Agent, Browser, BrowserConfig
        from langchain_openai import ChatOpenAI
        from langchain_anthropic import ChatAnthropic

        return asyncio.run(
            _run_browser_use_agent(
                task=task,
                max_steps=max_steps,
                model=model,
                url=url,
                use_vision=use_vision,
            )
        )
    except ImportError as e:
        return json.dumps({
            "error": f"Missing dependency: {e}. "
                     "Install with: pip install browser-use langchain-openai langchain-anthropic"
        })
    except Exception as e:
        logger.exception("browser_use_run failed")
        return json.dumps({"error": f"Browser use failed: {type(e).__name__}: {e}"})


async def _run_browser_use_agent(
    task: str,
    max_steps: int,
    model: Optional[str],
    url: Optional[str],
    use_vision: bool,
) -> str:
    """Async implementation of browser_use_run."""
    from browser_use import Agent, Browser, BrowserConfig

    # Build LLM
    llm = _resolve_langchain_llm(model)
    if isinstance(llm, str):
        # Error message returned
        return llm

    # Configure browser
    browser_config = BrowserConfig(
        headless=True,
    )

    # Build the task string with optional starting URL
    full_task = task
    if url:
        full_task = f"Start by navigating to {url}. Then: {task}"

    # Create agent
    agent = Agent(
        task=full_task,
        llm=llm,
        browser=Browser(config=browser_config),
        use_vision=use_vision,
        max_actions_per_step=5,
    )

    # Run with step limit
    result = await agent.run(max_steps=max_steps)

    # Extract results
    final_url = ""
    final_content = ""
    steps_taken = 0

    if hasattr(result, "all_results") and result.all_results:
        steps_taken = len(result.all_results)
        last = result.all_results[-1]
        if hasattr(last, "extracted_content"):
            final_content = last.extracted_content or ""
        if hasattr(last, "url"):
            final_url = last.url or ""

    # Get the final content from the agent's history
    if hasattr(result, "final_result"):
        final_content = result.final_result or final_content

    return json.dumps({
        "success": True,
        "task": task,
        "result": final_content,
        "final_url": final_url,
        "steps_taken": steps_taken,
        "max_steps": max_steps,
    }, indent=2)


def browser_use_extract(
    url: str,
    instruction: str = "Extract all meaningful content from this page",
    max_steps: int = 15,
    model: str = None,
) -> str:
    """Navigate to a URL and extract structured data using browser-use.

    This is a convenience wrapper that combines navigation + extraction
    into a single tool call.

    Args:
        url: The URL to extract data from.
        instruction: What to extract (e.g., "Extract all pricing tiers").
        max_steps: Maximum browser steps.
        model: LLM model for browser-use agent.

    Returns:
        JSON string with extracted data.
    """
    err = _validate_url(url)
    if err:
        return json.dumps({"error": err})

    task = (
        f"Navigate to {url}. {instruction}. "
        f"Return the extracted data in a structured format. "
        f"When done, use the 'done' action to finish."
    )

    return browser_use_run(
        task=task,
        max_steps=max_steps,
        model=model,
        url=url,
    )


def browser_use_compare(
    urls: list,
    instruction: str = "Compare the content on these pages",
    max_steps: int = 25,
    model: str = None,
) -> str:
    """Visit multiple URLs and compare their content.

    Args:
        urls: List of URLs to visit and compare.
        instruction: What to compare (e.g., "Compare pricing plans").
        max_steps: Maximum browser steps.
        model: LLM model for browser-use agent.

    Returns:
        JSON string with comparison results.
    """
    if not urls or not isinstance(urls, list):
        return json.dumps({"error": "urls must be a non-empty list"})

    # Validate all URLs
    for u in urls:
        err = _validate_url(u)
        if err:
            return json.dumps({"error": f"URL validation failed for {u}: {err}"})

    url_list = "\n".join(f"  {i+1}. {u}" for i, u in enumerate(urls))
    task = (
        f"Visit each of these URLs and compare them:\n{url_list}\n\n"
        f"Comparison task: {instruction}\n\n"
        f"Visit each URL one by one, extract relevant information, "
        f"then provide a structured comparison. Use the 'done' action when finished."
    )

    return browser_use_run(
        task=task,
        max_steps=max_steps,
        model=model,
        url=urls[0],
    )


# ---------------------------------------------------------------------------
# LLM resolution helpers
# ---------------------------------------------------------------------------

def _resolve_langchain_llm(model: Optional[str]):
    """Build a LangChain LLM from a model string or environment.

    Supports OpenAI and Anthropic models. Returns the LLM instance or
    an error message string on failure.
    """
    if not model:
        # Auto-detect from available API keys
        if os.getenv("ANTHROPIC_API_KEY"):
            model = "claude-sonnet-4-20250514"
        elif os.getenv("OPENAI_API_KEY"):
            model = "gpt-4o"
        else:
            return json.dumps({
                "error": "No LLM model configured for browser-use. "
                         "Set BROWSER_USE_MODEL, ANTHROPIC_API_KEY, or OPENAI_API_KEY."
            })

    model_lower = model.lower()

    if "claude" in model_lower or "anthropic" in model_lower:
        try:
            from langchain_anthropic import ChatAnthropic
            api_key = os.getenv("ANTHROPIC_API_KEY", "")
            if not api_key:
                return json.dumps({"error": "ANTHROPIC_API_KEY not set"})
            return ChatAnthropic(
                model=model,
                api_key=api_key,
                timeout=60,
                stop=None,
            )
        except ImportError:
            return json.dumps({
                "error": "langchain-anthropic not installed. "
                         "Install: pip install langchain-anthropic"
            })

    # Default to OpenAI-compatible
    try:
        from langchain_openai import ChatOpenAI
        api_key = os.getenv("OPENAI_API_KEY", "")
        base_url = os.getenv("OPENAI_BASE_URL", None)
        if not api_key:
            return json.dumps({"error": "OPENAI_API_KEY not set"})
        kwargs = {
            "model": model,
            "api_key": api_key,
            "timeout": 60,
        }
        if base_url:
            kwargs["base_url"] = base_url
        return ChatOpenAI(**kwargs)
    except ImportError:
        return json.dumps({
            "error": "langchain-openai not installed. "
                     "Install: pip install langchain-openai"
        })


# ---------------------------------------------------------------------------
# Schema definitions
# ---------------------------------------------------------------------------

BROWSER_USE_RUN_SCHEMA = {
    "name": "browser_use_run",
    "description": (
        "Run an autonomous browser task using AI-driven browser automation. "
        "Describe what you want to accomplish in natural language, and browser-use "
        "will autonomously navigate, click, type, and extract data to complete it. "
        "Best for multi-step tasks like 'find X on website Y' or 'fill out this form'. "
        "For simple single-page extraction, prefer web_extract (faster). "
        "For fine-grained step-by-step control, use browser_navigate/snapshot/click/type."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "description": "Natural language description of the browser task to perform"
            },
            "max_steps": {
                "type": "integer",
                "description": "Maximum number of autonomous steps (default: 25)",
                "default": 25,
            },
            "model": {
                "type": "string",
                "description": "LLM model for the browser-use agent (default: auto-detect from available API keys)",
            },
            "url": {
                "type": "string",
                "description": "Optional starting URL to navigate to before beginning the task",
            },
            "use_vision": {
                "type": "boolean",
                "description": "Use screenshots for visual context (more token-heavy, default: false)",
                "default": False,
            },
        },
        "required": ["task"],
    },
}

BROWSER_USE_EXTRACT_SCHEMA = {
    "name": "browser_use_extract",
    "description": (
        "Navigate to a URL and extract structured data using autonomous browser automation. "
        "Specify what to extract in natural language. This is a convenience wrapper that "
        "combines navigation + extraction into a single call."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to navigate to and extract data from"
            },
            "instruction": {
                "type": "string",
                "description": "What to extract (e.g., 'Extract all pricing tiers with prices and features')",
                "default": "Extract all meaningful content from this page",
            },
            "max_steps": {
                "type": "integer",
                "description": "Maximum number of browser steps (default: 15)",
                "default": 15,
            },
            "model": {
                "type": "string",
                "description": "LLM model for the browser-use agent",
            },
        },
        "required": ["url"],
    },
}

BROWSER_USE_COMPARE_SCHEMA = {
    "name": "browser_use_compare",
    "description": (
        "Visit multiple URLs and compare their content using autonomous browser automation. "
        "Specify what to compare in natural language. The agent will visit each URL, "
        "extract relevant data, and produce a structured comparison."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "urls": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of URLs to visit and compare"
            },
            "instruction": {
                "type": "string",
                "description": "What to compare (e.g., 'Compare pricing plans and features')",
                "default": "Compare the content on these pages",
            },
            "max_steps": {
                "type": "integer",
                "description": "Maximum number of browser steps (default: 25)",
                "default": 25,
            },
            "model": {
                "type": "string",
                "description": "LLM model for the browser-use agent",
            },
        },
        "required": ["urls"],
    },
}


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

def _handle_browser_use_run(args: dict, **kw) -> str:
    return browser_use_run(
        task=args.get("task", ""),
        max_steps=args.get("max_steps", 25),
        model=args.get("model"),
        url=args.get("url"),
        use_vision=args.get("use_vision", False),
    )


def _handle_browser_use_extract(args: dict, **kw) -> str:
    return browser_use_extract(
        url=args.get("url", ""),
        instruction=args.get("instruction", "Extract all meaningful content from this page"),
        max_steps=args.get("max_steps", 15),
        model=args.get("model"),
    )


def _handle_browser_use_compare(args: dict, **kw) -> str:
    return browser_use_compare(
        urls=args.get("urls", []),
        instruction=args.get("instruction", "Compare the content on these pages"),
        max_steps=args.get("max_steps", 25),
        model=args.get("model"),
    )


# ---------------------------------------------------------------------------
# Module test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Browser Use Tool Module")
    print("=" * 40)

    if _check_browser_use_available():
        print("browser-use library: installed")
    else:
        print("browser-use library: NOT installed")
        print("  Install: pip install browser-use && playwright install chromium")

    # Check API keys
    if os.getenv("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY: set")
    elif os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY: set")
    else:
        print("No LLM API keys found (need ANTHROPIC_API_KEY or OPENAI_API_KEY)")

    if os.getenv("BROWSER_USE_API_KEY"):
        print("BROWSER_USE_API_KEY: set (cloud mode available)")
    else:
        print("BROWSER_USE_API_KEY: not set (local Playwright mode)")


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

from tools.registry import registry

registry.register(
    name="browser_use_run",
    toolset="browser_use",
    schema=BROWSER_USE_RUN_SCHEMA,
    handler=_handle_browser_use_run,
    check_fn=_check_browser_use_available,
    emoji="🤖",
)

registry.register(
    name="browser_use_extract",
    toolset="browser_use",
    schema=BROWSER_USE_EXTRACT_SCHEMA,
    handler=_handle_browser_use_extract,
    check_fn=_check_browser_use_available,
    emoji="🔍",
)

registry.register(
    name="browser_use_compare",
    toolset="browser_use",
    schema=BROWSER_USE_COMPARE_SCHEMA,
    handler=_handle_browser_use_compare,
    check_fn=_check_browser_use_available,
    emoji="⚖️",
)
