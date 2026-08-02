#!/usr/bin/env python3
"""Run a synthetic LLP fixture through the R4/R5 smoke cutflow.

Technical demonstration only: proves the configurable LLP PDG id can be
identified, its descendants collected, its recorded decay vertex read, and
the result passed through the existing dvrecast cutflow machinery. This is
not a physics-validated recast; see docs/reproduction_plan.md (M3).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dvrecast.cutflow import write_cutflow_csv  # noqa: E402
from dvrecast.llp_event import LlpNotFoundError, load_fixture, run_llp_smoke_cutflow  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture",
        type=Path,
        default=ROOT / "tests/fixtures/llp_scalar_smoke_event.json",
        help="path to a dvrecast.llp_smoke_fixture.v1 JSON event",
    )
    parser.add_argument(
        "--llp-pdg-id",
        default=None,
        help="override the fixture's llp_pdg_id (default: use the fixture value, "
        "falling back to the canonical default 1000022)",
    )
    parser.add_argument(
        "--out-csv", type=Path, default=None, help="optional cutflow.csv output path"
    )
    args = parser.parse_args(argv)

    fixture = load_fixture(args.fixture)
    try:
        rows, rejection_stage = run_llp_smoke_cutflow(fixture, llp_pdg_id=args.llp_pdg_id)
    except (LlpNotFoundError, ValueError) as exc:
        print(f"run_llp_smoke: {exc}", file=sys.stderr)
        return 2

    for row in rows:
        print(f"{row.cut},{row.count:.0f}")
    if rejection_stage is None:
        print("result: all stages passed", file=sys.stderr)
    else:
        print(f"result: rejected at stage '{rejection_stage}'", file=sys.stderr)

    if args.out_csv is not None:
        write_cutflow_csv(args.out_csv, rows)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
