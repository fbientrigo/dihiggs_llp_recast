#!/usr/bin/env python3
"""Phase 6 scaffolding: one row per physical (mH, ctau) point, reshaping the
already-validated aeff_grid.csv columns into the input-parameters /
production-observables / jet-stage / DV-stage / Aeff / normalization /
validation-state layout requested for future parameter-attribution studies.

This produces a TABLE only. No SHAP/Shapley computation, no surrogate model,
no attribution claim of any kind is made or implemented here -- see
FUTURE_ATTRIBUTION_READINESS.md.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--primary-checkout", required=True, type=Path)
    ap.add_argument("--release-dir", required=True, type=Path)
    args = ap.parse_args()

    grid_dir = args.primary_checkout / "results" / "aeff_grid_20260811T042218Z"
    grid_rows = list(csv.DictReader((grid_dir / "grid_Aeff.csv").open()))
    anomalies = json.loads((grid_dir / "anomalies.json").read_text())

    anomaly_by_node = {}
    for a in anomalies:
        anomaly_by_node.setdefault(a["node_id"], []).append(a["type"])

    def node_id(mh, ctau):
        ctau_tag = str(ctau).replace(".", "p")
        return f"mH{int(float(mh))}_ctau{ctau_tag}"

    out_rows = []
    for r in grid_rows:
        mh = float(r["mH_GeV"])
        ctau = float(r["ctau_mm"])
        nid_guess = node_id(mh, ctau)
        flags = anomaly_by_node.get(nid_guess, [])
        validation_state = "PASS" if not flags else "PASS_WITH_WARNING:" + "|".join(flags)
        out_rows.append({
            # input model parameters
            "mH_GeV": mh,
            "ctau_response_mm": ctau,
            "ctau_physical_mm": "",  # NOT reconstructable from this release's grid; grid is a factorized response scan
            # production observables
            "N_generated": r["N_generated"],
            # jet-stage metrics
            "raw_jet_selection_fraction": r["raw_jet_selection_fraction"],
            # DV-stage metrics
            "raw_fiducial_fraction": r["raw_fiducial_fraction"],
            "raw_r_vertex_gt_4mm_fraction": r["raw_r_vertex_gt_4mm_fraction"],
            "raw_track_d0_gt_2mm_fraction": r["raw_track_d0_gt_2mm_fraction"],
            "raw_dv_multiplicity_fraction": r["raw_dv_multiplicity_fraction"],
            "raw_dv_mass_fraction": r["raw_dv_mass_fraction"],
            # Aeff
            "raw_selected": r["raw_selected"],
            "weighted_numerator": r["weighted_numerator"],
            "Aeff": r["Aeff"],
            "between_seed_half_spread": r["between_seed_half_spread"],
            # normalization
            "production_normalization_source": "NOT_IN_SCOPE_THIS_TABLE: production sigma/BR are model-point-specific and live in dihiggs_hep_cross / dihiggs manifests (see r8_h2_model_derived_4b/input_manifest.json for the mH150 canonical example), not reconstructable from a factorized response grid",
            # validation state
            "status": r["status"],
            "validation_state": validation_state,
            "provenance_source": "results/aeff_grid_20260811T042218Z/grid_Aeff.csv + anomalies.json",
        })

    outpath = args.release_dir / "parameter_attribution_readiness.csv"
    fieldnames = list(out_rows[0].keys())
    with outpath.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in out_rows:
            w.writerow(row)
    print(f"wrote {outpath} ({len(out_rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
