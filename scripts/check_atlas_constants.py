#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

LITERALS = (
    "250.",
    "195.",
    "116.",
    "90.",
    "137.",
    "101.",
    "83.",
    "55.",
    "70.",
    "50.",
    "3870.",
    "300.",
    "4.",
    "520.",
    "10.",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    upstream = args.upstream.read_text(encoding="utf-8")
    adapter = args.adapter.read_text(encoding="utf-8")
    checks = {literal: literal in upstream and literal in adapter for literal in LITERALS}
    checks["no_modified_trackless_thresholds"] = " > 65." not in adapter and " > 45." not in adapter
    checks["efficiency_maps_reused"] = all(
        (args.upstream.parent / name).is_file() for name in ("efficiency.cc", "efficiency.h")
    )
    payload = {
        "schema": "scalar_h2.atlas_constants.v1",
        "checks": checks,
        "upstream_source_sha256": sha256(args.upstream),
        "efficiency_source_sha256": sha256(args.upstream.parent / "efficiency.cc"),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
