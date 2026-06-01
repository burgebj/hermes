"""Tests for optional-skills/blockchain/privy/scripts/privy_client.py."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest  # ty: ignore[unresolved-import]

SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "optional-skills"
    / "blockchain"
    / "privy"
    / "scripts"
    / "privy_client.py"
)
SKILL_PATH = SCRIPT_PATH.parents[1] / "SKILL.md"


@pytest.fixture(scope="module")
def privy_client():
    spec = importlib.util.spec_from_file_location("privy_client", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_skill_is_read_only_and_warns_against_signing():
    text = SKILL_PATH.read_text(encoding="utf-8")
    assert "read-only" in text.lower()
    assert "does not sign" in text.lower()
    assert "human-approved" in text.lower()
    assert "PRIVY_APP_ID" in text
    assert "PRIVY_APP_SECRET" in text


def test_build_basic_auth_header_uses_app_id_and_secret(privy_client):
    assert (
        privy_client.build_basic_auth_header("app_123", "secret_456")
        == "Basic YXBwXzEyMzpzZWNyZXRfNDU2"
    )


def test_load_credentials_requires_app_id_and_secret(privy_client, monkeypatch):
    monkeypatch.delenv("PRIVY_APP_ID", raising=False)
    monkeypatch.delenv("PRIVY_APP_SECRET", raising=False)

    with pytest.raises(SystemExit) as exc:
        privy_client.load_credentials()

    assert "PRIVY_APP_ID" in str(exc.value)
    assert "PRIVY_APP_SECRET" in str(exc.value)


def test_extract_wallets_returns_only_wallet_linked_accounts(privy_client):
    user = {
        "id": "did:privy:abc",
        "linked_accounts": [
            {"type": "email", "address": "alice@example.com"},
            {
                "type": "wallet",
                "address": "0x1234567890abcdef1234567890abcdef12345678",
                "chain_type": "ethereum",
                "wallet_client_type": "privy",
                "connector_type": "embedded",
                "verified_at": 1710000000,
            },
            {
                "type": "wallet",
                "address": "So11111111111111111111111111111111111111112",
                "chain_type": "solana",
            },
        ],
    }

    assert privy_client.extract_wallets(user) == [
        {
            "address": "0x1234567890abcdef1234567890abcdef12345678",
            "chain_type": "ethereum",
            "wallet_client_type": "privy",
            "connector_type": "embedded",
            "verified_at": 1710000000,
        },
        {
            "address": "So11111111111111111111111111111111111111112",
            "chain_type": "solana",
            "wallet_client_type": None,
            "connector_type": None,
            "verified_at": None,
        },
    ]


def test_summarize_user_redacts_pii_but_keeps_wallets(privy_client):
    user = {
        "id": "did:privy:abc",
        "created_at": 1710000000,
        "linked_accounts": [
            {"type": "email", "address": "alice@example.com"},
            {"type": "phone", "phoneNumber": "+15551234567"},
            {
                "type": "wallet",
                "address": "0x1234567890abcdef1234567890abcdef12345678",
                "chain_type": "ethereum",
            },
        ],
    }

    summary = privy_client.summarize_user(user)

    assert summary["id"] == "did:privy:abc"
    assert summary["created_at"] == 1710000000
    assert summary["linked_account_types"] == ["email", "phone", "wallet"]
    assert summary["wallets"] == [
        {
            "address": "0x1234567890abcdef1234567890abcdef12345678",
            "chain_type": "ethereum",
            "wallet_client_type": None,
            "connector_type": None,
            "verified_at": None,
        }
    ]
    assert "alice@example.com" not in json.dumps(summary)
    assert "+15551234567" not in json.dumps(summary)


def test_build_users_query_encodes_filters(privy_client):
    path = privy_client.build_users_query(limit=10, cursor="next cursor", email="a+b@example.com")
    assert path == "/v1/users?limit=10&cursor=next+cursor&email=a%2Bb%40example.com"
