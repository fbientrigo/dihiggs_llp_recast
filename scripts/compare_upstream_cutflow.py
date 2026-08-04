#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dvrecast.cutflow import compare_upstream_cutflows  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply the Gate B cutflow contract")
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--observed", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    try:
        reference = json.loads(args.reference.read_text(encoding="utf-8"))
        observed = json.loads(args.observed.read_text(encoding="utf-8"))
        payload = compare_upstream_cutflows(reference, observed)
    except (OSError, json.JSONDecodeError) as exc:
        payload = {"schema_version": 1, "status": "BLOCKED", "blockers": [str(exc)]}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"{payload['status']}: {args.out}")
    return 0 if payload["status"] in {"VALIDATED", "PROVISIONAL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
