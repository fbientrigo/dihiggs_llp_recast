#!/usr/bin/env python3
"""Build the ATLAS_TRACKLESS_H2_RESPONSE_V1 canonical release tables.

Reads ONLY from already-existing, independently-reviewed campaign artifacts
under the primary checkout's ``results/`` tree (frozen R8, the trackless jet
diagnostic campaign, and the validated 3x12 Aeff(mH,ctau) grid). It does not
rerun Pythia/recast and does not hand-enter any physics number: every value
in cutflow_long.csv / jet_branch_decomposition.csv / samples.csv / Gate A is
parsed from source CSV/JSON/log files at run time.

Usage:
    python3 build_release_tables.py --primary-checkout /path/to/dihiggs_llp_recast --outdir /path/to/release
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

STAGE_ORDER = [
    "generated",
    "ordinary_jet_OR",
    "displaced_jet_addendum",
    "Jet_Selection",
    "DV_fiducial",
    "R_DV_gt_4mm",
    "d0_gt_2mm",
    "tracks_ge_5",
    "mDV_gt_10GeV",
    "final_raw",
    "efficiency_weighted",
]

STAGE_LABELS = {
    "generated": "Generated (N_processed)",
    "ordinary_jet_OR": "Ordinary jet OR (J1|J2|J3|J4)",
    "displaced_jet_addendum": "Ordinary OR AND displaced-jet addendum",
    "Jet_Selection": "Published Trackless Jet Selection",
    "DV_fiducial": "DV fiducial (R<300mm, |z|<300mm)",
    "R_DV_gt_4mm": "R_DV > 4 mm",
    "d0_gt_2mm": "track |d0| > 2 mm",
    "tracks_ge_5": "selected decay products >= 5",
    "mDV_gt_10GeV": "invariant mass(DV) > 10 GeV",
    "final_raw": "final raw selected (== mDV_gt_10GeV == Acc)",
    "efficiency_weighted": "Acc x Eff (efficiency-weighted)",
}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def load_r8_cutflow_module(primary_checkout: Path):
    sys.path.insert(0, str(primary_checkout / "src"))
    from dvrecast import r8_cutflow  # type: ignore

    return r8_cutflow


def read_events_csv_jet_counts(path: Path) -> dict:
    with path.open() as f:
        rows = list(csv.DictReader(f))
    n = len(rows)
    ordinary_or = sum(1 for r in rows if r["trackless_kinematic"] == "1")
    full_trackless = sum(1 for r in rows if r["trackless_selected"] == "1")
    return {"n": n, "ordinary_jet_OR": ordinary_or, "displaced_jet_addendum": full_trackless}


def build_sample_rows(
    sample_id: str,
    model_variant: str,
    mH_GeV: float,
    ctau_mm: float,
    seeds: list[str],
    events_csv_paths: dict[str, Path],
    recast_log_paths: dict[str, Path],
    provenance_source: str,
    r8_cutflow_mod,
) -> list[dict]:
    rows: list[dict] = []
    per_seed_jet = {}
    per_seed_dv = {}
    n_generated_per_seed = {}

    for seed in seeds:
        jet_counts = read_events_csv_jet_counts(events_csv_paths[seed])
        per_seed_jet[seed] = jet_counts
        n_generated_per_seed[seed] = jet_counts["n"]
        log_text = recast_log_paths[seed].read_text()
        parsed = r8_cutflow_mod.parse_recast_log(log_text)
        per_seed_dv[seed] = parsed.regions["Trackless"]
        if parsed.n_events != jet_counts["n"]:
            raise ValueError(
                f"{sample_id} seed {seed}: recast.log n_events={parsed.n_events} "
                f"!= events.csv rows={jet_counts['n']}"
            )

    def emit(seed_label: str, n_gen: int, jet: dict, dv) -> None:
        stage_raw = {
            "generated": n_gen,
            "ordinary_jet_OR": jet["ordinary_jet_OR"],
            "displaced_jet_addendum": jet["displaced_jet_addendum"],
            "Jet_Selection": dv.stage_counts["jet_selection_pct"],
            "DV_fiducial": dv.stage_counts["fiducial_pct"],
            "R_DV_gt_4mm": dv.stage_counts["r_vertex_gt_4mm_pct"],
            "d0_gt_2mm": dv.stage_counts["track_d0_gt_2mm_pct"],
            "tracks_ge_5": dv.stage_counts["selected_decay_products_ge5_pct"],
            "mDV_gt_10GeV": dv.stage_counts["invariant_mass_gt_10gev_pct"],
            "final_raw": dv.acc,
            "efficiency_weighted": None,
        }
        if stage_raw["mDV_gt_10GeV"] != stage_raw["final_raw"]:
            raise ValueError(f"{sample_id} {seed_label}: final_raw stage mismatch with mDV_gt_10GeV/Acc")
        weighted_final = dv.acc_x_eff

        prev_raw = None
        for stage_id in STAGE_ORDER:
            raw = stage_raw[stage_id]
            weighted = weighted_final if stage_id == "efficiency_weighted" else None
            if stage_id == "efficiency_weighted":
                raw = None
                denom_raw = stage_raw["final_raw"]
            row = {
                "sample_id": sample_id,
                "model_variant": model_variant,
                "mH_GeV": mH_GeV,
                "ctau_mm": ctau_mm,
                "seed": seed_label,
                "N_generated": n_gen,
                "analysis_region": "Trackless",
                "stage_index": STAGE_ORDER.index(stage_id),
                "stage_id": stage_id,
                "stage_label": STAGE_LABELS[stage_id],
                "raw_count": raw if raw is not None else "",
                "raw_fraction_global": (raw / n_gen) if raw is not None else "",
                "conditional_retention": "",
                "conditional_loss": "",
                "weighted_count_if_defined": weighted if weighted is not None else "",
                "provenance_source": provenance_source,
            }
            if raw is not None and prev_raw is not None and prev_raw > 0:
                cr = raw / prev_raw
                row["conditional_retention"] = cr
                row["conditional_loss"] = 1.0 - cr
            if raw is not None:
                prev_raw = raw
            rows.append(row)

    for seed in seeds:
        emit(seed, n_generated_per_seed[seed], per_seed_jet[seed], per_seed_dv[seed])

    n_gen_combined = sum(n_generated_per_seed[s] for s in seeds)
    jet_combined = {
        "ordinary_jet_OR": sum(per_seed_jet[s]["ordinary_jet_OR"] for s in seeds),
        "displaced_jet_addendum": sum(per_seed_jet[s]["displaced_jet_addendum"] for s in seeds),
    }

    class _Combined:
        pass

    dv_c = _Combined()
    dv_c.stage_counts = {
        key: sum(per_seed_dv[s].stage_counts[key] for s in seeds)
        for key in per_seed_dv[seeds[0]].stage_counts
    }
    dv_c.acc = sum(per_seed_dv[s].acc for s in seeds)
    dv_c.acc_x_eff = sum(per_seed_dv[s].acc_x_eff for s in seeds)

    emit("combined", n_gen_combined, jet_combined, dv_c)

    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--primary-checkout", required=True, type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    args = ap.parse_args()

    primary = args.primary_checkout.resolve()
    outdir = args.outdir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    r8_cutflow_mod = load_r8_cutflow_module(primary)

    diag = primary / "results" / "trackless_jet_diag_20260812T032241Z"
    r8dir = primary / "results" / "r8_h2_model_derived_4b"
    grid = primary / "results" / "aeff_grid_20260811T042218Z"

    samples = [
        dict(
            sample_id="r8_frozen_mH150_ctau4p326_2x1000",
            model_variant="ORIGINAL_PUBLISHED_TRACKLESS",
            mH_GeV=150.0,
            ctau_mm=4.326221529733112,
            seeds=["81001", "81002"],
            events_csv_paths={
                "81001": diag / "r8_regression_v2" / "seed_81001" / "events.csv",
                "81002": diag / "r8_regression_v2" / "seed_81002" / "events.csv",
            },
            recast_log_paths={
                "81001": r8dir / "run_01" / "recast.log",
                "81002": r8dir / "run_02" / "recast.log",
            },
            provenance_source="results/r8_h2_model_derived_4b/run_0{1,2}/recast.log + results/trackless_jet_diag_20260812T032241Z/r8_regression_v2/seed_*/events.csv",
        ),
        dict(
            sample_id="anchor20k_mH150_ctau4p326_2x10000",
            model_variant="ORIGINAL_PUBLISHED_TRACKLESS",
            mH_GeV=150.0,
            ctau_mm=4.326221529733112,
            seeds=["81001", "81002"],
            events_csv_paths={
                "81001": diag / "anchor_20k_v2" / "seed_81001" / "events.csv",
                "81002": diag / "anchor_20k_v2" / "seed_81002" / "events.csv",
            },
            recast_log_paths={
                "81001": diag / "anchor_20k_v2" / "seed_81001" / "recast.log",
                "81002": diag / "anchor_20k_v2" / "seed_81002" / "recast.log",
            },
            provenance_source="results/trackless_jet_diag_20260812T032241Z/anchor_20k_v2/seed_*/{events.csv,recast.log}",
        ),
        dict(
            sample_id="endpoint20k_mH130_ctau4p326_2x10000",
            model_variant="ORIGINAL_PUBLISHED_TRACKLESS",
            mH_GeV=130.0,
            ctau_mm=4.326221529733112,
            seeds=["81001", "81002"],
            events_csv_paths={
                "81001": diag / "endpoint_130_20k" / "seed_81001" / "events.csv",
                "81002": diag / "endpoint_130_20k" / "seed_81002" / "events.csv",
            },
            recast_log_paths={
                "81001": diag / "endpoint_130_20k" / "seed_81001" / "recast.log",
                "81002": diag / "endpoint_130_20k" / "seed_81002" / "recast.log",
            },
            provenance_source="results/trackless_jet_diag_20260812T032241Z/endpoint_130_20k/seed_*/{events.csv,recast.log}",
        ),
        dict(
            sample_id="endpoint20k_mH170_ctau4p326_2x10000",
            model_variant="ORIGINAL_PUBLISHED_TRACKLESS",
            mH_GeV=170.0,
            ctau_mm=4.326221529733112,
            seeds=["81001", "81002"],
            events_csv_paths={
                "81001": diag / "endpoint_170_20k" / "seed_81001" / "events.csv",
                "81002": diag / "endpoint_170_20k" / "seed_81002" / "events.csv",
            },
            recast_log_paths={
                "81001": diag / "endpoint_170_20k" / "seed_81001" / "recast.log",
                "81002": diag / "endpoint_170_20k" / "seed_81002" / "recast.log",
            },
            provenance_source="results/trackless_jet_diag_20260812T032241Z/endpoint_170_20k/seed_*/{events.csv,recast.log}",
        ),
    ]

    all_rows: list[dict] = []
    for s in samples:
        all_rows.extend(
            build_sample_rows(
                sample_id=s["sample_id"],
                model_variant=s["model_variant"],
                mH_GeV=s["mH_GeV"],
                ctau_mm=s["ctau_mm"],
                seeds=s["seeds"],
                events_csv_paths=s["events_csv_paths"],
                recast_log_paths=s["recast_log_paths"],
                provenance_source=s["provenance_source"],
                r8_cutflow_mod=r8_cutflow_mod,
            )
        )

    cutflow_long_path = outdir / "cutflow_long.csv"
    fieldnames = [
        "sample_id", "model_variant", "mH_GeV", "ctau_mm", "seed", "N_generated",
        "analysis_region", "stage_index", "stage_id", "stage_label",
        "raw_count", "raw_fraction_global", "conditional_retention",
        "conditional_loss", "weighted_count_if_defined", "provenance_source",
    ]
    with cutflow_long_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in all_rows:
            w.writerow(row)

    # --- jet_branch_decomposition.csv: leave-one-out + branch pattern data ---
    jbd_rows = []
    for s in samples:
        summary_path = {
            "r8_frozen_mH150_ctau4p326_2x1000": diag / "diagnostics" / "r8_regression_v2_summary.json",
            "anchor20k_mH150_ctau4p326_2x10000": diag / "diagnostics" / "anchor_20k_v2_summary.json",
            "endpoint20k_mH130_ctau4p326_2x10000": diag / "diagnostics" / "endpoint_130_20k_summary.json",
            "endpoint20k_mH170_ctau4p326_2x10000": diag / "diagnostics" / "endpoint_170_20k_summary.json",
        }[s["sample_id"]]
        summ = json.loads(summary_path.read_text())
        n_gen = sum(read_events_csv_jet_counts(p).get("n", 0) for p in s["events_csv_paths"].values())
        baseline = summ["matching_categories_within_kinematic_union"]["passes_full_trackless"]
        for branch in ("j1", "j2", "j3", "j4"):
            loo = summ["leave_one_branch_out"][branch]
            jbd_rows.append({
                "sample_id": s["sample_id"],
                "mH_GeV": s["mH_GeV"],
                "ctau_mm": s["ctau_mm"],
                "N_generated": n_gen,
                "branch": branch.upper(),
                "branch_raw_population": summ["branch_counts"][branch],
                "baseline_ordinary_jet_OR_count": baseline,
                "leave_one_out_selected_without_branch": loo["selected_without_branch"],
                "leave_one_out_exclusive_loss": loo["lost_when_branch_removed"],
                "leave_one_out_exclusive_loss_fraction_of_baseline": loo["fraction_of_baseline_lost"],
                "note": "exclusive/leave-one-out losses are NOT independent and must not be summed across branches (OR logic)",
                "provenance_source": str(summary_path.relative_to(primary)),
            })
        # branch-pattern overlap table (4-bit pattern j1j2j3j4 -> event count)
        for pattern, count in summ["branch_patterns_in_full_trackless_jet_selection"].items():
            jbd_rows.append({
                "sample_id": s["sample_id"],
                "mH_GeV": s["mH_GeV"],
                "ctau_mm": s["ctau_mm"],
                "N_generated": n_gen,
                "branch": f"PATTERN_{pattern}",
                "branch_raw_population": count,
                "baseline_ordinary_jet_OR_count": baseline,
                "leave_one_out_selected_without_branch": "",
                "leave_one_out_exclusive_loss": "",
                "leave_one_out_exclusive_loss_fraction_of_baseline": "",
                "note": "bitstring order j1j2j3j4 (1=passed); overlap population within full Trackless Jet Selection",
                "provenance_source": str(summary_path.relative_to(primary)),
            })

    jbd_path = outdir / "jet_branch_decomposition.csv"
    jbd_fields = [
        "sample_id", "mH_GeV", "ctau_mm", "N_generated", "branch",
        "branch_raw_population", "baseline_ordinary_jet_OR_count",
        "leave_one_out_selected_without_branch", "leave_one_out_exclusive_loss",
        "leave_one_out_exclusive_loss_fraction_of_baseline", "note", "provenance_source",
    ]
    with jbd_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=jbd_fields)
        w.writeheader()
        for row in jbd_rows:
            w.writerow(row)

    # --- samples.csv ---
    samples_path = outdir / "samples.csv"
    with samples_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "sample_id", "model_variant", "mH_GeV", "ctau_mm", "N_generated",
            "seeds", "analysis_region", "final_raw_combined", "weighted_combined",
            "Aeff_combined", "provenance_source",
        ])
        w.writeheader()
        for s in samples:
            rows_for_sample = [r for r in all_rows if r["sample_id"] == s["sample_id"] and r["seed"] == "combined"]
            final_raw = next(r["raw_count"] for r in rows_for_sample if r["stage_id"] == "final_raw")
            weighted = next(r["weighted_count_if_defined"] for r in rows_for_sample if r["stage_id"] == "efficiency_weighted")
            n_gen = next(r["N_generated"] for r in rows_for_sample if r["stage_id"] == "generated")
            w.writerow({
                "sample_id": s["sample_id"],
                "model_variant": s["model_variant"],
                "mH_GeV": s["mH_GeV"],
                "ctau_mm": s["ctau_mm"],
                "N_generated": n_gen,
                "seeds": "|".join(s["seeds"]),
                "analysis_region": "Trackless",
                "final_raw_combined": final_raw,
                "weighted_combined": weighted,
                "Aeff_combined": weighted / n_gen,
                "provenance_source": s["provenance_source"],
            })

    # --- copy aeff_grid.csv (Figure F source, full 3x12 grid) ---
    grid_src = grid / "grid_Aeff.csv"
    grid_dst = outdir / "aeff_grid.csv"
    grid_dst.write_text(grid_src.read_text())

    print(f"wrote {cutflow_long_path} ({len(all_rows)} rows)")
    print(f"wrote {jbd_path} ({len(jbd_rows)} rows)")
    print(f"wrote {samples_path} ({len(samples)} rows)")
    print(f"wrote {grid_dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
