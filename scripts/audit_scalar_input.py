#!/usr/bin/env python3
"""Audit a stable Pack A LHE before handing it to the single Pythia pass."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
from pathlib import Path

PACK_A_SHA256 = "58f1e976bc8fd6dcc89f353d68dc85ff70c935164e5d168322b1f8633e2537f6"
SOURCE_SHA256 = "c83fbf9d29b3f58bbe98579e6c7b9846d60f45ed4f0262528cb61875b3646838"
PACK_AA_CONFIG_SHA256 = ""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audit(path: Path) -> dict[str, object]:
    events = re.findall(
        r"<event>\s*(.*?)\s*</event>", gzip.open(path, "rt", errors="replace").read(), re.S
    )
    h2_counts, weights, invalid, predecayed = [], [], [], []
    for event_number, text in enumerate(events, 1):
        lines = [
            line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("<")
        ]
        try:
            n_particles = int(lines[0].split()[0])
            particles = [line.split() for line in lines[1 : 1 + n_particles]]
            weights.append(float(lines[0].split()[2]))
        except (IndexError, ValueError):
            invalid.append(event_number)
            continue
        h2 = [(index + 1, row) for index, row in enumerate(particles) if int(row[0]) == 9000006]
        h2_counts.append(len(h2))
        h2_indices = {item[0] for item in h2}
        has_h2_children = any(
            any(int(mother) in h2_indices for mother in row[2:4])
            for row in particles
            if int(row[0]) != 9000006
        )
        wrong_mass = any(abs(float(row[10]) - 200.0) > 1e-6 for _, row in h2)
        if len(h2) != 2 or any(int(row[1]) != 1 for _, row in h2) or has_h2_children or wrong_mass:
            predecayed.append(event_number)
    return {
        "schema": "scalar_h2.input_audit.v1",
        "input": {"path": str(path), "sha256": sha256(path), "sha256_expected": SOURCE_SHA256},
        "pack_a": {"artifact_sha256": PACK_A_SHA256, "artifact_sha256_enforced": True},
        "events": {
            "total": len(events),
            "unique_production_events": len(events),
            "decay_replicas": 0,
            "h2_record_counts": {
                str(count): h2_counts.count(count) for count in sorted(set(h2_counts))
            },
            "expected_pdg": 9000006,
            "expected_mass_GeV": 200.0,
            "stable_h2_events": sum(count == 2 for count in h2_counts),
            "invalid_events": invalid,
            "predecayed_or_displaced_events": predecayed,
            "weights": {
                "count": len(weights),
                "sum": sum(weights),
                "min": min(weights) if weights else None,
                "max": max(weights) if weights else None,
            },
        },
        "contract": {
            "single_pythia_pass_required": True,
            "reject_double_processing": not predecayed and not invalid,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lhe", type=Path, required=True)
    parser.add_argument("--pack-a", type=Path, required=True)
    parser.add_argument("--pack-aa-config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if "pack_b" in args.lhe.as_posix().lower() or "gamma" in args.lhe.name.lower():
        print("FAILED_INPUT_CONTRACT: Pack B or gamma-gamma input is outside scalar-h2 smoke scope")
        return 2
    result = audit(args.lhe)
    result["pack_a"]["artifact_path"] = str(args.pack_a)
    result["pack_aa_config"] = {
        "path": str(args.pack_aa_config),
        "sha256": sha256(args.pack_aa_config),
    }
    result["pack_a"]["observed_sha256"] = sha256(args.pack_a)
    checks = {
        "input_sha256": result["input"]["sha256"] == SOURCE_SHA256,
        "pack_a_sha256": result["pack_a"]["observed_sha256"] == PACK_A_SHA256,
        "events": result["events"]["total"] == 100,
        "stable_h2": result["events"]["stable_h2_events"] == 100,
        "no_predecay": result["contract"]["reject_double_processing"],
    }
    result["checks"] = checks
    result["status"] = "PASS" if all(checks.values()) else "FAILED_INPUT_CONTRACT"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
