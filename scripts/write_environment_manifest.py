#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dvrecast.config import load_upstream_lock  # noqa: E402
from dvrecast.manifest import build_environment_manifest  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Write an auditable environment manifest")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--lock", type=Path, default=ROOT / "configs" / "upstream.lock.json")
    args = parser.parse_args()

    lock = load_upstream_lock(args.lock)
    manifest = build_environment_manifest(args.repo_root, lock)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
