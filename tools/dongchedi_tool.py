#!/usr/bin/env python3
"""
Hermes tool wrapper for dongchedi_l90_watch.py

Scrapes and monitors 乐道L90 EV listings on dongchedi.com.
Provides new/removed/changed listings compared to previous snapshot.

Usage (direct):
    python dongchedi_tool.py --list-url "https://..."

Usage (Hermes tool):
    dongchedi_watch(list_url="https://...", max_details=30, headless=False)
"""

import json
import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Absolute path to the scraper scripts (same directory)
SCRAPER_DIR = Path(__file__).parent.resolve()
DONGCHEDI_SCRIPT = SCRAPER_DIR / "dongchedi_l90_watch.py"
DEFAULT_DB = SCRAPER_DIR / "dongchedi_l90.sqlite"
DEFAULT_PROFILE = SCRAPER_DIR.parent.parent / ".crawl4ai" / "profiles" / "dongchedi_profile"


def dongchedi_watch(
    list_url: str,
    max_details: int = 30,
    headless: bool = False,
    db_path: str = None,
    include_raw_text: bool = False,
) -> str:
    """
    Scrape and monitor 乐道L90 (Leda L90) listings on 懂车帝 (dongchedi.com).

    Compares against the previous SQLite snapshot to report new listings,
    removed listings, and changed prices/mileage.

    Args:
        list_url: 懂车帝二手车列表页 URL (must be filtered to 乐道L90).
                  Get this by filtering on dongchedi.com and copying the URL.
        max_details: Maximum detail pages to scrape per run (default: 30).
        headless: If False (default), show browser window for manual verification
                  on captcha/login pages. If True, fail fast on verification pages.
        db_path: SQLite database path. Defaults to tools/dongchedi_l90.sqlite.
                 Set to "" to use in-memory (no persistence, no diff).
        include_raw_text: Include raw HTML text in JSON output (default: False).
                          Keep False to keep output compact.

    Returns:
        JSON string with run_at, counts, items, and delta (new/removed/changed).
    """
    import shutil

    # Resolve db_path
    if db_path is None:
        db = DEFAULT_DB
    elif str(db_path).strip() == "":
        db = SCRAPER_DIR / "data" / f"dongchedi_{Path(list_url).name[:20]}.sqlite"
    else:
        db = Path(db_path).expanduser().resolve()

    # Resolve profile dir
    profile_dir = DEFAULT_PROFILE.expanduser().resolve()
    profile_dir.mkdir(parents=True, exist_ok=True)
    db.parent.mkdir(parents=True, exist_ok=True)

    # Build command
    cmd = [
        sys.executable,
        str(DONGCHEDI_SCRIPT),
        "--list-url", list_url,
        "--db", str(db),
        "--max-details", str(max_details),
        "--profile-dir", str(profile_dir),
    ]

    if not headless:
        cmd.append("--headed")
    else:
        # Invert: script uses --headed flag (default=True), so omit it for headless
        pass

    if include_raw_text:
        cmd.append("--include-raw-text")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
            cwd=str(SCRAPER_DIR),
        )
    except subprocess.TimeoutExpired:
        return json.dumps({
            "success": False,
            "error": "Scrape timed out after 600 seconds. Try reducing --max-details.",
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to run scraper: {e}",
        }, ensure_ascii=False)

    if result.returncode != 0:
        # Check if it's a verification page error (recoverable hint)
        stderr_lower = result.stderr.lower()
        stdout_lower = result.stdout.lower()
        combined = stderr_lower + stdout_lower

        if "verify" in combined or "验证" in result.stdout or "captcha" in combined:
            hint = (
                "\nHint: 懂车帝 showed a verification/captcha page. "
                "Re-run with headless=False to complete verification manually."
            )
            try:
                # Try to extract partial JSON from stdout
                out_lines = result.stdout.strip().split("\n")
                for line in reversed(out_lines):
                    if line.strip().startswith("{"):
                        parsed = json.loads(line)
                        parsed["success"] = False
                        parsed["error"] = (parsed.get("error", "") + hint).strip()
                        return json.dumps(parsed, ensure_ascii=False)
            except Exception:
                pass
            return json.dumps({
                "success": False,
                "error": result.stderr or result.stdout or "Unknown error",
                "hint": hint.strip(),
            }, ensure_ascii=False)

        return json.dumps({
            "success": False,
            "error": result.stderr or result.stdout or f"Exit code {result.returncode}",
        }, ensure_ascii=False)

    # Parse JSON from stdout (multi-line pretty-printed JSON).
    # Strategy: find the first '{' and the last '}' in the output,
    # then trim trailing non-JSON lines char-by-char until we get valid JSON.
    output_text = result.stdout.strip()
    json_start = output_text.find("{")
    json_end = output_text.rfind("}")
    if json_start == -1 or json_end == -1 or json_end <= json_start:
        return json.dumps({
            "success": False,
            "error": "No JSON block found in output",
            "stdout": result.stdout[-1000:],
            "stderr": result.stderr[-1000:],
        }, ensure_ascii=False)

    # Start with the full JSON candidate
    json_candidate = output_text[json_start:json_end + 1]
    for _ in range(20):  # max 20 trailing lines to strip
        try:
            parsed = json.loads(json_candidate)
            parsed["success"] = True
            return json.dumps(parsed, ensure_ascii=False, indent=2)
        except json.JSONDecodeError:
            pass
        # Strip one trailing line
        json_candidate = json_candidate.rstrip()
        last_newline = json_candidate.rfind("\n")
        if last_newline == -1:
            break
        json_candidate = json_candidate[:last_newline]

    return json.dumps({
        "success": False,
        "error": "Could not parse JSON from output",
        "raw_output": result.stdout[:2000],
    }, ensure_ascii=False)


DONGCHEDI_WATCH_SCHEMA = {
    "name": "dongchedi_watch",
    "description": (
        "Scrape and monitor 乐道L90 EV listings on 懂车帝 (dongchedi.com). "
        "Compares against the previous run to report new listings, removed listings, "
        "and changed prices/mileage. Stores results in SQLite for historical tracking.\n\n"
        "First run: use headless=False to complete any verification/captcha in the browser. "
        "Subsequent runs: headless=True works with saved browser profile.\n\n"
        "Args:\n"
        "  list_url (required): 懂车帝二手车列表页 URL. Filter on dongchedi.com first.\n"
        "  max_details (default 30): Max detail pages per run.\n"
        "  headless (default False): If True, fail on verification pages instead of pausing.\n"
        "  db_path (optional): Custom SQLite path. Defaults to car_scraper/dongchedi_l90.sqlite.\n"
        "  include_raw_text (default False): Include raw HTML text in output.\n\n"
        "Returns: JSON with matched_count, new_count, removed_count, changed_count, "
        "items list, and delta (new/removed/changed listings)."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "list_url": {
                "type": "string",
                "description": "懂车帝二手车列表页 URL (must be filtered to 乐道L90). Get by filtering on dongchedi.com and copying the URL.",
            },
            "max_details": {
                "type": "integer",
                "description": "Maximum detail pages to scrape per run (default: 30).",
                "default": 30,
            },
            "headless": {
                "type": "boolean",
                "description": "If False (default), pause for manual verification on captcha pages. If True, fail fast.",
                "default": False,
            },
            "db_path": {
                "type": "string",
                "description": "Custom SQLite database path. Defaults to tools/car_scraper/dongchedi_l90.sqlite.",
            },
            "include_raw_text": {
                "type": "boolean",
                "description": "Include raw HTML text in output JSON (default: False, keeps output compact).",
                "default": False,
            },
        },
        "required": ["list_url"],
    },
}


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

def _check_requirements() -> bool:
    """Check if crawl4ai and aiosqlite are available."""
    try:
        import crawl4ai  # noqa: F401
        import aiosqlite  # noqa: F401
        return True
    except ImportError:
        return False


from tools.registry import registry, tool_error

registry.register(
    name="dongchedi_watch",
    toolset="car_scraper",
    schema=DONGCHEDI_WATCH_SCHEMA,
    handler=lambda args, **kw: dongchedi_watch(
        list_url=args.get("list_url", ""),
        max_details=args.get("max_details", 30),
        headless=args.get("headless", False),
        db_path=args.get("db_path"),
        include_raw_text=args.get("include_raw_text", False),
    ),
    check_fn=_check_requirements,
    requires_env=[],
    emoji="🚗",
)