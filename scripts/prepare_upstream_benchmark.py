#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dvrecast.benchmark import prepare_benchmark  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an upstream benchmark workspace")
    parser.add_argument("--benchmark", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        payload = prepare_benchmark(ROOT, args.benchmark, dry_run=args.dry_run)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        payload = {"schema_version": 1, "state": "BLOCKED", "blockers": [str(exc)]}
    print(json.dumps(payload, indent=2))
    return 0 if payload["state"] == "NOT_RUN" or args.dry_run else 2


if __name__ == "__main__":
    raise SystemExit(main())
