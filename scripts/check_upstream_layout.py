#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dvrecast.config import load_upstream_lock  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the frozen upstream recast layout")
    parser.add_argument("--root", type=Path, default=ROOT / "external" / "recastingCodes")
    parser.add_argument("--lock", type=Path, default=ROOT / "configs" / "upstream.lock.json")
    args = parser.parse_args()

    lock = load_upstream_lock(args.lock)
    base = args.root / lock.analysis_path
    expected = [
        base / "README.md",
        base / "recast_code" / "1_analysis" / "Makefile",
        base / "recast_code" / "1_analysis" / "recast_2301_13866.cc",
        base / "recast_code" / "0_mg5_cards",
    ]

    missing = [path for path in expected if not path.exists()]
    for path in expected:
        marker = "OK" if path.exists() else "MISSING"
        print(f"[{marker:7}] {path}")

    git_dir = args.root / ".git"
    if not git_dir.exists():
        missing.append(git_dir)
        print(f"[MISSING] {git_dir}")

    if missing:
        print("\nRun `make bootstrap` before upstream validation.")
        return 2

    print("\nFrozen upstream layout is present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
