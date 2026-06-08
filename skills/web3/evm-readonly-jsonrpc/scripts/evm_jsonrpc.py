#!/usr/bin/env python3
"""CLI wrapper: Pydantic validation + whitelist JSON-RPC (see `_evm_transport`)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from _evm_transport import _Envelope as _TransportEnvelope

from _evm_transport import rpc_call as _transport_rpc


def _dedupe_https_urls(raws: list[str]) -> list[str]:
    urls: list[str] = []

    seen: set[str] = set()

    for raw in raws:

        u = raw.strip()

        if not u or not u.startswith("https://"):
            raise ValueError("rpc_urls entries must be non-empty HTTPS URLs")

        if u in seen:
            continue

        seen.add(u)
        urls.append(u)

    if not urls:

        raise ValueError("rpc_urls must contain at least one URL")

    return urls


class EvmRpcCliPayload(BaseModel):
    """stdin JSON for `--stdin` automation."""

    model_config = ConfigDict(extra="forbid")

    method: str = Field(min_length=1)
    params: list[Any] = Field(default_factory=list)
    rpc_urls: list[str] | None = None

    @field_validator("method")
    @classmethod
    def _strip_method(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("method must be non-empty")
        return stripped

    @field_validator("rpc_urls")
    @classmethod
    def _normalize_urls(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return None
        return _dedupe_https_urls(v)


def _load_rpc_urls(cli_urls: list[str] | None) -> list[str]:

    if cli_urls:

        return _dedupe_https_urls(cli_urls)

    bundled = os.getenv("HERMES_SKILL_EVM_RPC_URLS") or ""

    if bundled.strip():

        return _dedupe_https_urls([p for p in bundled.split(",") if p.strip()])

    one = os.getenv("HERMES_SKILL_EVM_RPC_URL")

    if not one or not one.strip().startswith("https://"):
        raise ValueError(
            "Missing HTTPS RPC. Set HERMES_SKILL_EVM_RPC_URL(S) or pass rpc_urls in the JSON payload.",
        )

    return [one.strip()]


def _parse_cmd(argv: list[str]) -> argparse.Namespace:

    p = argparse.ArgumentParser(description="EVM HTTPS JSON-RPC (read-only whitelist).")

    sub = p.add_subparsers(dest="cmd", required=True)

    rp = sub.add_parser("rpc", help="Perform a whitelist JSON-RPC call.")

    grp = rp.add_mutually_exclusive_group(required=True)

    grp.add_argument("--stdin", action="store_true", help="Read UTF-8 JSON EvmRpcCliPayload from stdin")

    grp.add_argument("--method", help="Explicit JSON-RPC method name")

    rp.add_argument("--params-json", default="[]", help='JSON list for params when using --method (default [])')

    rp.add_argument("--rpc-url", action="append", default=None, help="HTTPS RPC (repeat for fallback)")

    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:

    args = _parse_cmd(argv or sys.argv[1:])

    if args.cmd != "rpc":
        return 2

    rpc_urls_override: list[str] | None = None

    if args.stdin:

        try:
            payload_model = EvmRpcCliPayload.model_validate_json(sys.stdin.read())
        except Exception as exc:  # noqa: BLE001
            print(json.dumps({"success": False, "error": f"stdin_parse:{exc}", "stdin": True}))

            return 1

        rpc_urls_override = payload_model.rpc_urls

        envelope = _TransportEnvelope(method=payload_model.method, params=payload_model.params)

    else:

        if args.method is None:

            print(json.dumps({"success": False, "error": "missing --method"}))

            return 1

        try:
            parsed = json.loads(args.params_json)
        except json.JSONDecodeError as exc:

            print(json.dumps({"success": False, "error": f"invalid params-json:{exc}", "stdin": False}))

            return 1

        if not isinstance(parsed, list):
            print(json.dumps({"success": False, "error": "--params-json must decode to JSON array"}))

            return 1

        envelope = _TransportEnvelope(method=args.method.strip(), params=parsed)

        if args.rpc_url:

            try:
                rpc_urls_override = _dedupe_https_urls(args.rpc_url)
            except ValueError as exc:

                print(json.dumps({"success": False, "error": f"rpc_url:{exc}", "stdin": False}))

                return 1

    try:

        urls = _load_rpc_urls(rpc_urls_override)

    except ValueError as exc:

        print(json.dumps({"success": False, "error": str(exc), "stdin": bool(args.stdin)}))

        return 1

    out = _transport_rpc(envelope, urls)

    print(json.dumps(out, ensure_ascii=False))

    return 0 if out.get("success") else 3


if __name__ == "__main__":
    sys.exit(main())
