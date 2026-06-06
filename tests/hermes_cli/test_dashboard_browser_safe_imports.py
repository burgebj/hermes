"""Static dashboard tests for browser-safe @nous-research/ui imports."""
from pathlib import Path


WEB_SRC = Path(__file__).resolve().parents[2] / "web" / "src"


def test_dashboard_does_not_import_nous_ui_root_barrel():
    offenders = []
    for ext in ("*.tsx", "*.ts"):
        for path in WEB_SRC.rglob(ext):
            content = path.read_text(encoding="utf-8")
            if 'from "@nous-research/ui"' in content or "from '@nous-research/ui'" in content:
                offenders.append(str(path.relative_to(WEB_SRC)))

    assert offenders == []


def test_dashboard_api_client_injects_session_token_header():
    source = (WEB_SRC / "lib" / "api.ts").read_text(encoding="utf-8")

    required_snippets = [
        'const SESSION_HEADER = "X-Hermes-Session-Token";',
        "const headers = new Headers(init?.headers);",
        "const token = window.__HERMES_SESSION_TOKEN__;",
        "setSessionHeader(headers, token);",
        "fetch(`${BASE}${url}`, { ...init, headers })",
        "fetchJSON<AnalyticsResponse>(`/api/analytics/usage?days=${days}`)",
        "fetchJSON<ModelsAnalyticsResponse>(`/api/analytics/models?days=${days}`)",
    ]

    missing = [snippet for snippet in required_snippets if snippet not in source]
    assert missing == []
