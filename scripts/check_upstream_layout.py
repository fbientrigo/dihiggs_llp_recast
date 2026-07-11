#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dvrecast.config import load_upstream_lock  # noqa: E402


def git_head(path: Path) -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=path, capture_output=True, text=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else None


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

    failed = False
    for path in expected:
        marker = "OK" if path.exists() else "MISSING"
        print(f"[{marker:8}] {path}")
        failed = failed or not path.exists()

    actual_commit = git_head(args.root) if (args.root / ".git").exists() else None
    commit_ok = actual_commit == lock.commit
    print(f"[{'OK' if commit_ok else 'MISMATCH':8}] upstream commit = {actual_commit or '-'}")
    print(f"[EXPECTED] upstream commit = {lock.commit}")
    failed = failed or not commit_ok

    if failed:
        print("\nRun `make bootstrap` before upstream validation.")
        return 2

    print("\nFrozen upstream layout and revision are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
