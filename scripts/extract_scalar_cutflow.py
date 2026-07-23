#!/usr/bin/env python3
from __future__ import annotations

# ruff: noqa: E501
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

STAGES = [
    ("events_read", lambda r: True),
    ("events_expected_h2", lambda r: r["h2_records"] >= 2),
    ("events_successful_h2_bb", lambda r: r["h2_bb_decays"] > 0),
    ("events_displaced_h2_vertex", lambda r: r["dv_radius_mm"] > 4),
    (
        "events_fiducial_decay",
        lambda r: r["dv_radius_mm"] < 300 and abs(r["dv_z_mm"]) < 300 and r["dv_radius_mm"] > 4,
    ),
    ("events_jet_preselection", lambda r: r["n_jets"] >= 4),
    (
        "events_high_pt_selection",
        lambda r: (
            r["n_jets"] >= 4
            and (r["leading_jet_pt_GeV"] >= 250 or r["subleading_jet_pt_GeV"] >= 195)
        ),
    ),
    (
        "events_trackless_selection",
        lambda r: r["event_efficiency"] > 0 or r["vertex_efficiency"] > 0,
    ),
    ("candidate_displaced_vertices", lambda r: r["h2_bb_decays"] > 0),
    (
        "vertices_displaced_track_requirements",
        lambda r: r["selected_displaced_track_multiplicity"] > 0,
    ),
    ("vertices_track_multiplicity", lambda r: r["selected_displaced_track_multiplicity"] >= 5),
    ("vertices_mdv", lambda r: r["reconstructed_dv_mass_GeV"] > 10),
    ("events_event_efficiency_map", lambda r: r["event_efficiency"] > 0),
    ("events_vertex_efficiency_map", lambda r: r["vertex_efficiency"] > 0),
    ("final_selected_events", lambda r: r["event_efficiency"] > 0 and r["vertex_efficiency"] > 0),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--stages", type=Path, required=True)
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    args = parser.parse_args()
    rows = [
        json.loads(line)
        for line in args.events.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    total_weight = sum(float(row["analysis_weight_mb"]) for row in rows)
    result = []
    previous_raw = len(rows)
    previous_weight = total_weight
    with args.stages.open(encoding="utf-8", newline="") as stream:
        stage_rows = list(csv.DictReader(stream))
    stage_values = {
        row["stage"]: (int(row["raw_count"]), float(row["weighted_count"])) for row in stage_rows
    }
    for stage_row in stage_rows:
        name = stage_row["stage"]
        raw = int(stage_row["raw_count"])
        weight = float(stage_row["weighted_count"])
        denominator_raw, denominator_weight = previous_raw, previous_weight
        if name in {
            "events_high_pt_selection",
            "events_trackless_selection",
            "events_jet_selection",
        }:
            denominator_raw, denominator_weight = stage_values["events_jet_preselection"]
        result.append(
            {
                "stage": name,
                "raw_count": raw,
                "weighted_count": weight,
                "fraction_of_input": raw / len(rows) if rows else 0.0,
                "weighted_fraction_of_input": weight / total_weight if total_weight else 0.0,
                "conditional_fraction": raw / denominator_raw if denominator_raw else 0.0,
                "weighted_conditional_fraction": weight / denominator_weight
                if denominator_weight
                else 0.0,
                "statistical_note": "100 unique production events; event weights preserved; no replica uncertainty used",
            }
        )
        if name not in {"events_high_pt_selection", "events_trackless_selection"}:
            previous_raw, previous_weight = raw, weight
    failures = Counter(row["failure_reason"] for row in rows)
    payload = {
        "schema": "scalar_h2.cutflow.v1",
        "status": "PROVISIONAL_ENGINEERING_SMOKE",
        "input_events": len(rows),
        "unique_production_events": len({row["production_event_id"] for row in rows}),
        "decay_replicas": len(rows) - len({row["production_event_id"] for row in rows}),
        "normalization": {
            "pack_a_smoke_sigma_separate": True,
            "branching_ratio_bb": 1.0,
            "acceptance_claim": "PROVISIONAL_ENGINEERING_SMOKE; NOT_MODEL_DERIVED; UPSTREAM_REGRESSION_PENDING",
        },
        "stages": result,
        "failure_reason_by_selection_stage": dict(sorted(failures.items())),
    }
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    with args.csv.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(result[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(result)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
