#!/usr/bin/env python3
"""Wrapper: patches crawl4ai antibot detector → run dongchedi_l90_watch.py"""
import sys, os, site

# ── Patch crawl4ai antibot structural_check BEFORE importing crawl4ai ─────────
site_packages = site.getsitepackages()[0]
antibot_path = os.path.join(site_packages, "crawl4ai", "antibot_detector.py")

ORIGINAL_FUNC = '''def structural_check(html: str) -> Tuple[bool, str]:
    """Tier 3 structural integrity check for pages that pass pattern detection.
    Returns (is_blocked, reason).
    """
    html_len = len(html)

    if html_len < 500:
        return True, f"Structural: no <body> tag ({html_len} bytes)"

    signals = []

    # Signal 1: Missing <body> tag in a page larger than 500 bytes
    if not re.search(r"<body\\b", html, re.IGNORECASE):
        signals.append("no_body_tag")

    # Signal 2: Minimal visible text after stripping scripts/styles/tags
    body_match = re.search(r"<body\\b[^>]*>([\\s\\S]*)</body>", html, re.IGNORECASE)
    body_content = body_match.group(1) if body_match else html
    stripped = _SCRIPT_BLOCK_RE.sub('', body_content)
    stripped = _STYLE_TAG_RE.sub('', stripped)
    visible_text = _TAG_RE.sub('', stripped).strip()
    visible_len = len(visible_text)
    if visible_len < 50:
        signals.append("minimal_text")

    # Signal 3: No content elements (semantic HTML)
    content_elements = len(_CONTENT_ELEMENTS_RE.findall(html))
    if content_elements == 0:
        signals.append("no_content_elements")

    # Signal 4: Script-heavy shell — scripts present but no content
    script_count = len(_SCRIPT_TAG_RE.findall(html))
    if script_count > 0 and content_elements == 0 and visible_len < 100:
        signals.append("script_heavy_shell")

    # Scoring
    signal_count = len(signals)
    if signal_count >= 2:
        return True, f"Structural: {', '.join(signals)} ({html_len} bytes, {visible_len} chars visible)"

    if signal_count == 1 and html_len < 5000:
        return True, f"Structural: {signals[0]} on small page ({html_len} bytes, {visible_len} chars visible)"

    return False, ""
'''

PATCHED_FUNC = '''def structural_check(html: str) -> Tuple[bool, str]:
    """Tier 3 structural integrity check — DISABLED for dongchedi compatibility.
    Dongchedi challenge pages are valid browser-render targets; we allow manual
    verification in headed mode without antibot blocking.
    """
    return False, ""
'''

with open(antibot_path) as f:
    src = f.read()

if "DISABLED for dongchedi" not in src:
    patched = src.replace(ORIGINAL_FUNC.strip(), PATCHED_FUNC.strip())
    if patched == src:
        import sys as _sys
        print("[WARN] Could not find structural_check to patch", file=_sys.stderr)
    else:
        with open(antibot_path, "w") as f:
            f.write(patched)
        print("[PATCH] Disabled structural_check in antibot_detector.py")
else:
    print("[OK] structural_check already patched")

# ── Run the real dongchedi_l90_watch.py ─────────────────────────────────────
tool_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.dirname(tool_dir) or ".")
sys.argv = ["dongchedi_l90_watch.py"] + sys.argv[1:]
exec(open(os.path.join(tool_dir, "dongchedi_l90_watch.py")).read(), {"__name__": "__main__", "__file__": os.path.join(tool_dir, "dongchedi_l90_watch.py")})