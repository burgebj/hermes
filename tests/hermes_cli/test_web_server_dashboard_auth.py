from __future__ import annotations

import sys
from pathlib import Path

_repo = str(Path(__file__).resolve().parents[1])
if _repo not in sys.path:
    sys.path.insert(0, _repo)


def test_dashboard_auth_disabled_by_default():
    from fastapi.testclient import TestClient
    from hermes_cli import web_server

    web_server._DASHBOARD_AUTH_PASSWORD = None
    client = TestClient(web_server.app)

    resp = client.get("/api/status")

    assert resp.status_code != 401


def test_dashboard_auth_redirects_page_requests_to_login():
    from fastapi.testclient import TestClient
    from hermes_cli import web_server

    web_server._DASHBOARD_AUTH_PASSWORD = "123456"
    try:
        client = TestClient(web_server.app, follow_redirects=False)
        resp = client.get("/")

        assert resp.status_code == 303
        assert resp.headers["location"] == "/login"
    finally:
        web_server._DASHBOARD_AUTH_PASSWORD = None


def test_dashboard_auth_returns_401_for_api_requests():
    from fastapi.testclient import TestClient
    from hermes_cli import web_server

    web_server._DASHBOARD_AUTH_PASSWORD = "123456"
    try:
        client = TestClient(web_server.app)
        resp = client.get("/api/status")

        assert resp.status_code == 401
        assert resp.json() == {"detail": "Dashboard locked"}
    finally:
        web_server._DASHBOARD_AUTH_PASSWORD = None


def test_dashboard_login_page_matches_hermes_shell():
    from fastapi.testclient import TestClient
    from hermes_cli import web_server

    web_server._DASHBOARD_AUTH_PASSWORD = "123456"
    try:
        client = TestClient(web_server.app)
        resp = client.get("/login")

        assert resp.status_code == 200
        assert "Hermes Agent" in resp.text
        assert "Dashboard locked" in resp.text
        assert "#041c1c" in resp.text
        assert "#ffe6cb" in resp.text
    finally:
        web_server._DASHBOARD_AUTH_PASSWORD = None


def test_dashboard_login_rejects_wrong_password():
    from fastapi.testclient import TestClient
    from hermes_cli import web_server

    web_server._DASHBOARD_AUTH_PASSWORD = "123456"
    try:
        client = TestClient(web_server.app, follow_redirects=False)
        resp = client.post("/login", data={"password": "wrong"})

        assert resp.status_code == 303
        assert resp.headers["location"] == "/login?error=1"
        assert "set-cookie" not in resp.headers
    finally:
        web_server._DASHBOARD_AUTH_PASSWORD = None


def test_dashboard_login_accepts_valid_password_and_sets_cookie():
    from fastapi.testclient import TestClient
    from hermes_cli import web_server

    web_server._DASHBOARD_AUTH_PASSWORD = "123456"
    try:
        client = TestClient(web_server.app, follow_redirects=False)
        resp = client.post("/login", data={"password": "123456"})

        assert resp.status_code == 303
        assert resp.headers["location"] == "/"
        assert "hermes_dashboard_auth" in resp.headers["set-cookie"]
        assert "HttpOnly" in resp.headers["set-cookie"]
    finally:
        web_server._DASHBOARD_AUTH_PASSWORD = None


def test_dashboard_auth_allows_request_with_session_cookie():
    from fastapi.testclient import TestClient
    from hermes_cli import web_server

    web_server._DASHBOARD_AUTH_PASSWORD = "123456"
    try:
        client = TestClient(web_server.app)
        client.post("/login", data={"password": "123456"})
        resp = client.get("/api/status")

        assert resp.status_code != 401
    finally:
        web_server._DASHBOARD_AUTH_PASSWORD = None
