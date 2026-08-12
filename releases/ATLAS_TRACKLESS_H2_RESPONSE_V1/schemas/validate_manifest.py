#!/usr/bin/env python3
"""Minimal validator for h2_response_input_manifest.v1.schema.json instances
(no external jsonschema dependency available on this node)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REQUIRED = [
    "sample_id", "parent_model_point_id", "model_variant", "m_h_GeV", "m_H2_GeV",
    "m_A_GeV", "m_Hp_GeV", "ctau_response_mm", "ctau_physical_mm",
    "decay_sampling_mode", "forced_decay_channel", "physical_BR",
    "production_process", "sigma_fb", "lhe_sha256", "card_sha256", "ufo_sha256",
    "generator_version", "seed", "N_events",
]
SHA_RE = re.compile(r"^[0-9a-f]{64}$")


def validate(instance: dict) -> list[str]:
    errors = []
    for field in REQUIRED:
        if field not in instance:
            errors.append(f"missing required field: {field}")
    for field in ("lhe_sha256", "card_sha256", "ufo_sha256"):
        if field in instance and not SHA_RE.match(str(instance[field])):
            errors.append(f"{field} is not a 64-hex-char sha256")
    for field in ("ctau_response_mm", "ctau_physical_mm"):
        if field in instance and not (isinstance(instance[field], (int, float)) and instance[field] > 0):
            errors.append(f"{field} must be a positive number")
    if "N_events" in instance and not (isinstance(instance["N_events"], int) and instance["N_events"] >= 1):
        errors.append("N_events must be a positive integer")
    return errors


def main() -> int:
    ok = True
    for path in sys.argv[1:]:
        instance = json.loads(Path(path).read_text())
        errors = validate(instance)
        if errors:
            ok = False
            print(f"FAIL {path}")
            for e in errors:
                print(f"  - {e}")
        else:
            print(f"PASS {path}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
