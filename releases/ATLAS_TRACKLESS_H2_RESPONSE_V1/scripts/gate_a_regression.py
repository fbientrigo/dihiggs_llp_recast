#!/usr/bin/env python3
"""Gate A: assert the release tables reproduce the frozen R8 and 3x20k
baseline values exactly. Failure is release-blocking (mission Gate A)."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

FROZEN = {
    "r8_frozen_mH150_ctau4p326_2x1000": {
        "N_generated": 2000, "final_raw_combined": 40,
        "weighted_combined": 31.46772, "Aeff_combined": 0.01573386,
        "jet_selection_combined": 48,
    },
    "anchor20k_mH150_ctau4p326_2x10000": {
        "N_generated": 20000, "final_raw_combined": 370,
        "weighted_combined": 267.5069, "Aeff_combined": 0.013375345,
        "jet_selection_combined": 460,
    },
    "endpoint20k_mH130_ctau4p326_2x10000": {
        "N_generated": 20000, "final_raw_combined": 300,
        "weighted_combined": 224.6426, "Aeff_combined": 0.01123213,
        "jet_selection_combined": 357,
    },
    "endpoint20k_mH170_ctau4p326_2x10000": {
        "N_generated": 20000, "final_raw_combined": 439,
        "weighted_combined": 318.6092, "Aeff_combined": 0.01593046,
        "jet_selection_combined": 558,
    },
}

TOL = 1e-6


def close(a: float, b: float, tol: float = TOL) -> bool:
    return abs(a - b) <= tol * max(1.0, abs(b))


def main() -> int:
    outdir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    cutflow_long = outdir / "cutflow_long.csv"
    samples_csv = outdir / "samples.csv"

    results = []
    ok = True

    with samples_csv.open() as f:
        samples = {row["sample_id"]: row for row in csv.DictReader(f)}

    for sample_id, frozen in FROZEN.items():
        row = samples.get(sample_id)
        checks = {}
        if row is None:
            ok = False
            results.append({"sample_id": sample_id, "status": "FAIL", "reason": "sample missing from samples.csv"})
            continue
        checks["N_generated"] = int(row["N_generated"]) == frozen["N_generated"]
        checks["final_raw_combined"] = int(row["final_raw_combined"]) == frozen["final_raw_combined"]
        checks["weighted_combined"] = close(float(row["weighted_combined"]), frozen["weighted_combined"])
        checks["Aeff_combined"] = close(float(row["Aeff_combined"]), frozen["Aeff_combined"])
        sample_ok = all(checks.values())
        ok = ok and sample_ok
        results.append({
            "sample_id": sample_id,
            "status": "PASS" if sample_ok else "FAIL",
            "checks": checks,
            "observed": {
                "N_generated": row["N_generated"],
                "final_raw_combined": row["final_raw_combined"],
                "weighted_combined": row["weighted_combined"],
                "Aeff_combined": row["Aeff_combined"],
            },
            "frozen": frozen,
        })

    # Cross-check Jet_Selection stage (combined, seed=="combined") from cutflow_long.csv
    with cutflow_long.open() as f:
        long_rows = list(csv.DictReader(f))
    for sample_id, frozen in FROZEN.items():
        js_rows = [
            r for r in long_rows
            if r["sample_id"] == sample_id and r["seed"] == "combined" and r["stage_id"] == "Jet_Selection"
        ]
        if not js_rows:
            ok = False
            results.append({"sample_id": sample_id, "status": "FAIL", "reason": "no combined Jet_Selection row in cutflow_long.csv"})
            continue
        observed_js = int(js_rows[0]["raw_count"])
        js_ok = observed_js == frozen["jet_selection_combined"]
        ok = ok and js_ok
        results.append({
            "sample_id": sample_id,
            "status": "PASS" if js_ok else "FAIL",
            "check": "Jet_Selection_combined_from_cutflow_long",
            "observed": observed_js,
            "frozen": frozen["jet_selection_combined"],
        })

    verdict = "PASS" if ok else "FAIL"
    report = {"schema": "llp_recast.atlas_trackless_h2_response.gate_a.v1", "verdict": verdict, "results": results}
    print(json.dumps(report, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
