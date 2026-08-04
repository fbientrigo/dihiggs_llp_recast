#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dvrecast.cutflow import parse_upstream_cutflow  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse an upstream DV+jets cutflow log")
    parser.add_argument("source", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--csv", type=Path)
    args = parser.parse_args()

    payload = parse_upstream_cutflow(args.source)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with args.csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=("branch", "step", "percent", "count", "count_source")
            )
            writer.writeheader()
            for branch, metrics in payload["branches"].items():
                for step, metric in metrics.items():
                    writer.writerow({"branch": branch, "step": step, **metric})
    print(f"PARSED: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
