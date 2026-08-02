#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dvrecast.readiness import upstream_build_readiness  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Check upstream recast build prerequisites")
    parser.add_argument("--pythia8", required=True)
    parser.add_argument("--fastjet3", required=True)
    parser.add_argument("--cxx", default="g++")
    args = parser.parse_args()

    readiness = upstream_build_readiness(
        {"PYTHIA8": args.pythia8, "FASTJET3": args.fastjet3, "CXX": args.cxx}
    )
    if readiness.state == "READY":
        print("Upstream recast build readiness: READY")
        return 0
    print("Upstream recast build readiness: BLOCKED", file=sys.stderr)
    for blocker in readiness.blockers:
        print(f"[ERROR] Missing prerequisite: {blocker}", file=sys.stderr)
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
