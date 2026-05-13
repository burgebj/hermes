#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hermes_cli.office_superpowers import watchdog_cli

if __name__ == "__main__":
    raise SystemExit(watchdog_cli())
