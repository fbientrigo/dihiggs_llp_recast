#!/usr/bin/env python3
"""Build the R8 H2-model-derived 4b recast result artifacts from the two
already-executed real recast runs (results/r8_h2_model_derived_4b/run_0{1,2}/
recast.log + geometry.csv). Pure post-processing: does not run Pythia or the
recast binary.
"""

import csv
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dvrecast.r8_cutflow import combine_runs, parse_recast_log  # noqa: E402
from dvrecast.r8_geometry import combine_samples, load_geometry_csv, summarize  # noqa: E402
from dvrecast.r8_normalization import BR_BB_SQUARED, SIGMA_H2H2_PB, sigma_4b_fb  # noqa: E402
from dvrecast.statistics import (  # noqa: E402
    clopper_pearson_interval,
    ks_critical_value,
    ks_two_sample_statistic,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(ROOT, "results", "r8_h2_model_derived_4b")
RUNS = ("01", "02")
REGIONS = ("High-pT", "Trackless")


def write_cutflow_csv(path, run_result):
    stage_names = [
        "jet_selection_pct",
        "fiducial_pct",
        "r_vertex_gt_4mm_pct",
        "track_d0_gt_2mm_pct",
        "selected_decay_products_ge5_pct",
        "invariant_mass_gt_10gev_pct",
    ]
    with open(path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["stage", "high_pt_count", "trackless_count"])
        writer.writerow(["events_processed", run_result.n_events, run_result.n_events])
        writer.writerow(
            ["zero_configured_llp_events", run_result.zero_llp_events, run_result.zero_llp_events]
        )
        for stage in stage_names:
            writer.writerow(
                [
                    stage,
                    run_result.regions["High-pT"].stage_counts[stage],
                    run_result.regions["Trackless"].stage_counts[stage],
                ]
            )
        writer.writerow(
            ["acc", run_result.regions["High-pT"].acc, run_result.regions["Trackless"].acc]
        )
        writer.writerow(
            [
                "acc_x_eff",
                run_result.regions["High-pT"].acc_x_eff,
                run_result.regions["Trackless"].acc_x_eff,
            ]
        )


def write_cutflow_combined_csv(path, run_results):
    stage_names = [
        "events_processed",
        "zero_configured_llp_events",
        "jet_selection_pct",
        "fiducial_pct",
        "r_vertex_gt_4mm_pct",
        "track_d0_gt_2mm_pct",
        "selected_decay_products_ge5_pct",
        "invariant_mass_gt_10gev_pct",
    ]
    with open(path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            ["stage", "region", "run_01_count", "run_02_count", "combined_count", "denominator"]
        )
        n_total = sum(r.n_events for r in run_results)
        writer.writerow(
            [
                "events_processed",
                "-",
                run_results[0].n_events,
                run_results[1].n_events,
                n_total,
                n_total,
            ]
        )
        writer.writerow(
            [
                "zero_configured_llp_events",
                "-",
                run_results[0].zero_llp_events,
                run_results[1].zero_llp_events,
                run_results[0].zero_llp_events + run_results[1].zero_llp_events,
                n_total,
            ]
        )
        for region in REGIONS:
            for stage in stage_names[2:]:
                c1 = run_results[0].regions[region].stage_counts[stage]
                c2 = run_results[1].regions[region].stage_counts[stage]
                writer.writerow([stage, region, c1, c2, c1 + c2, n_total])
            acc1 = run_results[0].regions[region].acc
            acc2 = run_results[1].regions[region].acc
            writer.writerow(["acc", region, acc1, acc2, acc1 + acc2, n_total])
            aeff1 = run_results[0].regions[region].acc_x_eff
            aeff2 = run_results[1].regions[region].acc_x_eff
            writer.writerow(["acc_x_eff", region, aeff1, aeff2, aeff1 + aeff2, n_total])


def write_geometry_summary_csv(path, run_geometries, combined_geometry):
    fields = [
        "run",
        "n_llp",
        "n_events",
        "n_bbbar_decays",
        "mean_rxy_mm",
        "median_rxy_mm",
        "frac_rxy_gt_4mm",
        "mean_l3d_mm",
        "median_l3d_mm",
        "frac_l3d_gt_4mm",
        "mean_tau_generated_mm",
        "mean_n_jets_pt20",
        "median_n_jets_pt20",
        "mean_leading_jet_pt_GeV",
        "median_leading_jet_pt_GeV",
    ]
    with open(path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(fields)
        for run_label, sample in zip(RUNS, run_geometries, strict=True):
            summary = summarize(sample)
            writer.writerow([f"run_{run_label}"] + [summary[f] for f in fields[1:]])
        summary = summarize(combined_geometry)
        writer.writerow(["combined"] + [summary[f] for f in fields[1:]])


def build_kinematic_comparison(run_geometries, run_results):
    n1, n2 = run_geometries[0].n_events, run_geometries[1].n_events
    comparisons = {}
    for label, a, b in (
        ("rxy_mm", run_geometries[0].rxy_mm, run_geometries[1].rxy_mm),
        ("l3d_mm", run_geometries[0].l3d_mm, run_geometries[1].l3d_mm),
        (
            "leading_jet_pt_GeV",
            run_geometries[0].leading_jet_pt_per_event,
            run_geometries[1].leading_jet_pt_per_event,
        ),
    ):
        d_stat = ks_two_sample_statistic(a, b)
        crit = ks_critical_value(len(a), len(b), alpha=0.05)
        comparisons[label] = {
            "ks_statistic": d_stat,
            "ks_critical_value_alpha_0.05": crit,
            "compatible_at_alpha_0.05": d_stat <= crit,
            "n_run_01": len(a) if label != "leading_jet_pt_GeV" else n1,
            "n_run_02": len(b) if label != "leading_jet_pt_GeV" else n2,
        }

    jet_mult_verdict = {
        "mean_n_jets_run_01": sum(run_geometries[0].n_jets_per_event) / n1,
        "mean_n_jets_run_02": sum(run_geometries[1].n_jets_per_event) / n2,
    }

    region_stats = {}
    for region in REGIONS:
        acc1 = run_results[0].regions[region].acc
        acc2 = run_results[1].regions[region].acc
        ci1 = clopper_pearson_interval(acc1, n1, confidence=0.95)
        ci2 = clopper_pearson_interval(acc2, n2, confidence=0.95)
        overlap = not (ci1[1] < ci2[0] or ci2[1] < ci1[0])
        region_stats[region] = {
            "run_01": {"acc": acc1, "n": n1, "a_eff": acc1 / n1, "ci95": list(ci1)},
            "run_02": {"acc": acc2, "n": n2, "a_eff": acc2 / n2, "ci95": list(ci2)},
            "ci95_overlap": overlap,
        }

    return {
        "distribution_ks_tests": comparisons,
        "jet_multiplicity": jet_mult_verdict,
        "selected_count_compatibility": region_stats,
    }


def build_normalization(run_results):
    combined = combine_runs(run_results)
    n_total = sum(r.n_events for r in run_results)
    sigma_4b = sigma_4b_fb()
    regions = {}
    for region in REGIONS:
        acc_total = combined[region]["acc_total"]
        a_eff_acc = combined[region]["a_eff_acc"]
        a_eff_acc_x_eff = combined[region]["a_eff_acc_x_eff"]
        ci95 = clopper_pearson_interval(acc_total, n_total, confidence=0.95)
        # Explicit criterion: fewer than MIN_SELECTED_FOR_USABLE_STATS raw
        # selected MC events gives a relative Poisson uncertainty
        # 1/sqrt(acc_total) above ~32%, too wide to usefully constrain a
        # signal region; report the minimum additional events needed to
        # reach that count at the currently observed acceptance.
        min_selected = 10
        insufficient = acc_total < min_selected
        min_additional_events = None
        if insufficient and a_eff_acc > 0:
            min_additional_events = max(0, math.ceil(min_selected / a_eff_acc) - n_total)
        regions[region] = {
            "acc_total": acc_total,
            "n_total": n_total,
            "a_eff_acc": a_eff_acc,
            "a_eff_acc_ci95": list(ci95),
            "a_eff_acc_x_eff": a_eff_acc_x_eff,
            "visible_sigma_fb_acc_x_eff": sigma_4b * a_eff_acc_x_eff,
            "insufficient_mc_statistics": insufficient,
            "insufficient_mc_statistics_criterion": (
                f"acc_total < {min_selected} selected MC events"
            ),
            "minimum_additional_events_needed": min_additional_events,
        }
    return {
        "sigma_H2H2_pb": SIGMA_H2H2_PB,
        "BR_bb_squared": BR_BB_SQUARED,
        "sigma_4b_fb": sigma_4b,
        "k_factor": None,
        "regions": regions,
        "luminosity_fb_inv": None,
        "luminosity_source": (
            "not found in this repository or the frozen upstream recastingCodes checkout "
            "(external/recastingCodes/DisplacedVertices/ATLAS-SUSY-2018-13_GCottin); "
            "not hardcoded from memory per mission Phase 7"
        ),
        "expected_signal_events": None,
        "exclusion_status": "RECAST_ACCEPTANCE_COMPUTED / EXCLUSION_NOT_EVALUATED",
        "next_step_by_region": {
            region: ("INSUFFICIENT_MC_STATISTICS" if regions[region]["insufficient_mc_statistics"]
                      else "RECAST_ACCEPTANCE_COMPUTED")
            for region in REGIONS
        },
    }


def main():
    run_results = []
    run_geometries = []
    for run in RUNS:
        run_dir = os.path.join(RESULTS_DIR, f"run_{run}")
        with open(os.path.join(run_dir, "recast.log")) as fh:
            run_result = parse_recast_log(fh.read())
        run_results.append(run_result)
        write_cutflow_csv(os.path.join(RESULTS_DIR, f"cutflow_run_{run}.csv"), run_result)
        run_geometries.append(load_geometry_csv(os.path.join(run_dir, "geometry.csv")))

    write_cutflow_combined_csv(os.path.join(RESULTS_DIR, "cutflow_combined.csv"), run_results)

    combined_geometry = combine_samples(run_geometries)
    write_geometry_summary_csv(
        os.path.join(RESULTS_DIR, "geometry_summary.csv"), run_geometries, combined_geometry
    )

    kinematic_comparison = build_kinematic_comparison(run_geometries, run_results)
    with open(os.path.join(RESULTS_DIR, "kinematic_comparison.json"), "w") as fh:
        json.dump(kinematic_comparison, fh, indent=2)

    normalization = build_normalization(run_results)
    with open(os.path.join(RESULTS_DIR, "normalization.json"), "w") as fh:
        json.dump(normalization, fh, indent=2)

    print("OK: wrote cutflow_run_01.csv, cutflow_run_02.csv, cutflow_combined.csv,")
    print("    geometry_summary.csv, kinematic_comparison.json, normalization.json")


if __name__ == "__main__":
    main()
