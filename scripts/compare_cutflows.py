#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dvrecast.cutflow import (  # noqa: E402
    compare_cutflows,
    comparison_as_dict,
    read_cutflow_csv,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare two cutflow CSV files")
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--observed", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--relative-tolerance", type=float, default=0.20)
    parser.add_argument("--low-count-threshold", type=float, default=10.0)
    parser.add_argument("--low-count-absolute-tolerance", type=float, default=3.0)
    args = parser.parse_args()

    comparisons = compare_cutflows(
        read_cutflow_csv(args.reference),
        read_cutflow_csv(args.observed),
        relative_tolerance=args.relative_tolerance,
        low_count_threshold=args.low_count_threshold,
        low_count_absolute_tolerance=args.low_count_absolute_tolerance,
    )
    passed = all(row.passed for row in comparisons)
    payload = {
        "schema_version": 1,
        "passed": passed,
        "reference": str(args.reference),
        "observed": str(args.observed),
        "comparisons": [comparison_as_dict(row) for row in comparisons],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"{'PASS' if passed else 'FAIL'}: {args.out}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
