#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys

from agent.gbrain_minions_transport import post_completion_envelope


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        print(json.dumps({"error": "expected JSON completion envelope on stdin"}))
        return 1
    envelope = json.loads(raw)
    result = post_completion_envelope(
        envelope,
        url=os.getenv("HERMES_GBRAIN_COMPLETION_URL", ""),
        api_key=os.getenv("HERMES_GBRAIN_COMPLETION_KEY") or os.getenv("API_SERVER_KEY") or None,
        timeout=float(os.getenv("HERMES_GBRAIN_TIMEOUT", "30")),
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
