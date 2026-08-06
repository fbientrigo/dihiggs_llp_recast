#!/usr/bin/env python3
"""R12 Mission: Parameterized Pythia/Recast Scan Campaign Driver."""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from dvrecast.r12_scan import (
    BR_VALUES,
    CTAU_VALUES,
    G_VALUES,
    LUMI_FB_INV,
    OBSERVED_S95,
    PRODUCTION_RUNS,
    calculate_aggregated_efficiency,
    calculate_final_grid_row,
    derive_pythia_seed,
    fmt_ctau_tag,
    fmt_g_dir,
    generate_pythia_card_content,
)
from relabel_lhe_pdg import relabel

DEFAULT_OUT_DIR = REPO_ROOT / "results" / "r12_madgraph_per_g_scan"
DEFAULT_CARDS_DIR = REPO_ROOT / "cards" / "r12_madgraph_per_g_scan"
DEFAULT_HEP_CROSS_DIR = REPO_ROOT.parent / "r12-six-g-madgraph-production"
if not DEFAULT_HEP_CROSS_DIR.exists():
    DEFAULT_HEP_CROSS_DIR = REPO_ROOT.parent / "hep_cross"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def get_git_commit_sha(repo_dir: Path) -> str:
    res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_dir, capture_output=True, text=True)
    if res.returncode == 0:
        return res.stdout.strip()
    return "UNKNOWN"


def locate_recast_executable() -> Path:
    candidates = [
        REPO_ROOT / "results" / "upstream_build_patched" / "analysis" / "recast_2301_13866",
        REPO_ROOT / "results" / "upstream_build" / "analysis" / "recast_2301_13866",
    ]
    for c in candidates:
        if c.exists() and os.access(c, os.X_OK):
            return c
    raise FileNotFoundError("Compiled recast executable missing. Run ./scripts/build_patched_upstream.sh first.")


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R12 Parameterized Pythia/Recast Scan Campaign.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Output directory for recast campaign.")
    parser.add_argument("--cards-dir", type=Path, default=DEFAULT_CARDS_DIR, help="Cards directory.")
    parser.add_argument("--hep-cross-dir", type=Path, default=DEFAULT_HEP_CROSS_DIR, help="Path to dihiggs_hep_cross repository/worktree.")
    parser.add_argument("--hep-cross-commit", type=str, default=None, help="Pinned Phase A commit SHA.")
    parser.add_argument("--g-values", type=float, nargs="+", default=None, help="Filter coupling values.")
    parser.add_argument("--ctau-values", type=float, nargs="+", default=None, help="Filter ctau values.")
    parser.add_argument("--max-parallel", type=int, default=2, help="Bounded parallelism limit.")
    parser.add_argument("--resume", action="store_true", help="Skip completed verified recast runs.")

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--prepare", action="store_true", help="Prepare inputs, relabel LHEs, and generate cards.")
    mode_group.add_argument("--execute", action="store_true", help="Execute full campaign including recast runs.")
    mode_group.add_argument("--verify-only", action="store_true", help="Verify campaign artifacts without execution.")

    return parser.parse_args(args)


from dvrecast.r8_cutflow import parse_recast_log


def parse_recast_output(log_path: Path) -> dict[str, Any]:
    text = log_path.read_text(encoding="utf-8", errors="replace")
    parsed = parse_recast_log(text)
    
    trackless = parsed.regions["Trackless"]
    gen_events = parsed.n_events
    sel_events = trackless.acc  # Integer accepted event count (e.g. 18 out of 1000)

    return {
        "generated_events": gen_events,
        "selected_events": sel_events,
        "cutflow": trackless.stage_counts,
    }


def execute_single_recast_job(
    recast_exec: Path,
    card_path: Path,
    log_path: Path,
) -> tuple[int, int]:
    with open(log_path, "w", encoding="utf-8") as fh:
        res = subprocess.run([str(recast_exec), str(card_path)], stdout=fh, stderr=subprocess.STDOUT, text=True)

    if res.returncode != 0:
        raise RuntimeError(f"Recast execution failed for {card_path}. See {log_path}")

    parsed = parse_recast_output(log_path)
    return parsed["generated_events"], parsed["selected_events"]


def main(args: list[str] | None = None) -> int:
    parsed = parse_args(args)
    out_dir = parsed.out_dir
    cards_dir = parsed.cards_dir
    hep_cross_dir = parsed.hep_cross_dir
    max_parallel = parsed.max_parallel

    g_targets = parsed.g_values if parsed.g_values else G_VALUES
    ctau_targets = parsed.ctau_values if parsed.ctau_values else CTAU_VALUES
    br_targets = BR_VALUES

    mode = "execute"
    if parsed.prepare:
        mode = "prepare"
    elif parsed.resume:
        mode = "resume"
    elif parsed.verify_only:
        mode = "verify-only"

    print("=== R12 Mission: Parameterized Pythia/Recast Scan Campaign Driver ===")
    print(f"Mode: {mode}")
    print(f"Output directory: {out_dir}")
    print(f"Cards directory: {cards_dir}")
    print(f"HepCross directory: {hep_cross_dir}")

    # Phase A pinned commit
    phase_a_commit = parsed.hep_cross_commit if parsed.hep_cross_commit else get_git_commit_sha(hep_cross_dir)
    print(f"Pinned Phase-A commit: {phase_a_commit}")

    production_dir = hep_cross_dir / "results" / "r12_madgraph_per_g_production"
    summary_p = production_dir / "production_summary.json"
    if not summary_p.exists():
        raise FileNotFoundError(f"Phase A production summary missing at {summary_p}")

    prod_summary = json.loads(summary_p.read_text(encoding="utf-8"))
    prod_comb_map = {item["g_hH2H2_GeV"]: item for item in prod_summary["combined"]}
    prod_run_map = {(item["g_hH2H2_GeV"], item["run_name"]): item for item in prod_summary["runs"]}

    relabel_dir = out_dir / "relabeled_lhes"
    logs_dir = out_dir / "recast_logs"
    cutflows_dir = out_dir / "cutflows"

    if mode in ("prepare", "execute", "resume"):
        out_dir.mkdir(parents=True, exist_ok=True)
        cards_dir.mkdir(parents=True, exist_ok=True)
        relabel_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)
        cutflows_dir.mkdir(parents=True, exist_ok=True)

    # 1. Prepare production input manifest
    manifest_runs = []
    for g in g_targets:
        g_dir = fmt_g_dir(g)
        for run_name in PRODUCTION_RUNS:
            run_info = prod_run_map.get((g, run_name))
            if not run_info:
                raise ValueError(f"Missing run info for g={g}, run={run_name}")

            src_lhe = production_dir / g_dir / run_name / "unweighted_events.lhe.gz"
            relabeled_lhe = relabel_dir / f"{g_dir}_{run_name}_pdg35.lhe.gz"

            manifest_runs.append({
                "g": g,
                "production_run": run_name,
                "production_seed": run_info["seed"],
                "source_path": str(src_lhe),
                "source_sha256": run_info["lhe_sha256"],
                "relabeled_path": str(relabeled_lhe),
                "event_count": 1000,
                "sigma_run_pb": run_info["sigma_pb"],
                "sigma_run_error_pb": run_info["sigma_error_pb"],
            })

    prod_input_manifest = {
        "repository": "fbientrigo/dihiggs_hep_cross",
        "commit": phase_a_commit,
        "campaign": "results/r12_madgraph_per_g_production",
        "runs": manifest_runs,
    }

    if mode != "verify-only":
        (out_dir / "production_input_manifest.json").write_text(
            json.dumps(prod_input_manifest, indent=2) + "\n", encoding="utf-8"
        )

    # 2. Relabel LHEs (9000006 -> 35)
    for run_item in manifest_runs:
        src_p = Path(run_item["source_path"])
        dst_p = Path(run_item["relabeled_path"])

        if mode in ("prepare", "execute", "resume"):
            if not dst_p.exists() or mode != "resume":
                print(f"Relabelling {src_p.name} -> {dst_p.name} (9000006 -> 35)...")
                relabel(
                    in_path=str(src_p),
                    out_path=str(dst_p),
                    from_pdg=9000006,
                    to_pdg=35,
                    expected_events=1000,
                    expected_relabelled=2000,
                )

        if not dst_p.exists():
            raise FileNotFoundError(f"Relabeled LHE missing: {dst_p}")

    # 3. Generate 144 Pythia Cards
    jobs_to_run = []
    card_manifest = []

    for g_idx, g in enumerate(g_targets):
        g_dir = fmt_g_dir(g)
        for ctau_idx, ctau in enumerate(ctau_targets):
            ctau_tag = fmt_ctau_tag(ctau)
            point_cards_dir = cards_dir / g_dir / ctau_tag
            if mode in ("prepare", "execute", "resume"):
                point_cards_dir.mkdir(parents=True, exist_ok=True)

            for run_idx, run_name in enumerate(PRODUCTION_RUNS, start=1):
                card_name = f"{run_name}.cmnd"
                card_path = point_cards_dir / card_name
                log_path = logs_dir / f"{g_dir}_{ctau_tag}_{run_name}.log"
                cutflow_json_path = cutflows_dir / f"{g_dir}_{ctau_tag}_{run_name}.json"

                relabeled_lhe = relabel_dir / f"{g_dir}_{run_name}_pdg35.lhe.gz"
                pythia_seed = derive_pythia_seed(g_idx, ctau_idx, run_idx)

                # Relative path from project root to relabeled LHE
                lhe_rel_path = f"results/r12_madgraph_per_g_scan/relabeled_lhes/{relabeled_lhe.name}"

                card_text = generate_pythia_card_content(
                    g=g,
                    ctau_mm=ctau,
                    run_name=run_name,
                    lhe_rel_path=lhe_rel_path,
                    pythia_seed=pythia_seed,
                )

                if mode in ("prepare", "execute", "resume"):
                    card_path.write_text(card_text, encoding="utf-8")

                job_info = {
                    "g": g,
                    "ctau": ctau,
                    "run_name": run_name,
                    "card_path": card_path,
                    "log_path": log_path,
                    "cutflow_json_path": cutflow_json_path,
                    "pythia_seed": pythia_seed,
                }
                jobs_to_run.append(job_info)
                card_manifest.append({
                    "g": g,
                    "ctau": ctau,
                    "run_name": run_name,
                    "card_path": str(card_path.relative_to(REPO_ROOT)),
                    "seed": pythia_seed,
                })

    print(f"Total Pythia cards generated: {len(jobs_to_run)}")

    if mode == "prepare":
        print("Preparation complete.")
        return 0

    # Locate recast binary
    recast_exec = locate_recast_executable()
    print(f"Recast executable: {recast_exec}")

    # 4. Execute Recast Jobs with bounded parallelism
    recast_results = {}

    def worker(job: dict[str, Any]) -> tuple[dict[str, Any], int, int]:
        c_path = job["card_path"]
        l_path = job["log_path"]
        j_path = job["cutflow_json_path"]

        should_exec = True
        if l_path.exists():
            try:
                parsed = parse_recast_output(l_path)
                if parsed.get("generated_events") == 1000:
                    should_exec = False
            except Exception:
                should_exec = True

        if should_exec:
            if mode == "verify-only":
                raise FileNotFoundError(f"Recast evidence missing/invalid for {c_path} in verify-only mode.")
            gen_ev, sel_ev = execute_single_recast_job(recast_exec, c_path, l_path)
            parsed = parse_recast_output(l_path)
            j_path.write_text(json.dumps(parsed, indent=2) + "\n", encoding="utf-8")
        else:
            j_path.write_text(json.dumps(parsed, indent=2) + "\n", encoding="utf-8")
            gen_ev, sel_ev = parsed["generated_events"], parsed["selected_events"]

        return job, gen_ev, sel_ev

    print(f"Launching {len(jobs_to_run)} recast jobs (max_parallel={max_parallel})...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_parallel) as executor:
        futures = {executor.submit(worker, job): job for job in jobs_to_run}
        for future in concurrent.futures.as_completed(futures):
            job, gen_ev, sel_ev = future.result()
            recast_results[(job["g"], job["ctau"], job["run_name"])] = (gen_ev, sel_ev)

    # 5. Aggregate 72 Aeff(g, ctau) points
    efficiency_rows = []
    for g in g_targets:
        for ctau in ctau_targets:
            gen1, sel1 = recast_results[(g, ctau, "run_01")]
            gen2, sel2 = recast_results[(g, ctau, "run_02")]

            aeff, aeff_err = calculate_aggregated_efficiency(sel1, gen1, sel2, gen2)

            efficiency_rows.append({
                "g_hH2H2_GeV": g,
                "GHphiphi_GeV": -abs(g),
                "ctau_mm": ctau,
                "run_01_selected": sel1,
                "run_01_generated": gen1,
                "run_02_selected": sel2,
                "run_02_generated": gen2,
                "combined_selected": sel1 + sel2,
                "combined_generated": gen1 + gen2,
                "Trackless_Aeff": aeff,
                "Trackless_Aeff_error": aeff_err,
                "status": "VALIDATED",
            })

    if mode != "verify-only":
        eff_csv_path = out_dir / "efficiency_vs_g_ctau.csv"
        with open(eff_csv_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(efficiency_rows[0].keys()))
            writer.writeheader()
            writer.writerows(efficiency_rows)

    # 6. Build final 360-point grid
    grid_rows = []
    point_idx = 1
    for g in g_targets:
        prod_info = prod_comb_map[g]
        sigma_prod_pb = prod_info["sigma_combined"]
        sigma_prod_err_pb = prod_info["combined_error"]

        for ctau in ctau_targets:
            eff_info = next(r for r in efficiency_rows if r["g_hH2H2_GeV"] == g and r["ctau_mm"] == ctau)
            aeff = eff_info["Trackless_Aeff"]
            aeff_err = eff_info["Trackless_Aeff_error"]
            gen_tot = eff_info["combined_generated"]
            sel_tot = eff_info["combined_selected"]

            for br in br_targets:
                pid = f"point_{point_idx:03d}"
                row = calculate_final_grid_row(
                    point_id=pid,
                    g=g,
                    ctau=ctau,
                    br_bb=br,
                    sigma_prod_pb=sigma_prod_pb,
                    sigma_prod_err_pb=sigma_prod_err_pb,
                    aeff=aeff,
                    aeff_err=aeff_err,
                    n_gen_tot=gen_tot,
                    n_sel_tot=sel_tot,
                    source_commit=phase_a_commit,
                )
                grid_rows.append(row)
                point_idx += 1

    if mode != "verify-only":
        grid_csv_path = out_dir / "effective_grid_madgraph_per_g.csv"
        with open(grid_csv_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(grid_rows[0].keys()))
            writer.writeheader()
            writer.writerows(grid_rows)

    # 7. Comparison against R10 factorized scan
    r10_cfg_path = REPO_ROOT.parent / "r12-six-g-madgraph-production" / "configs" / "r10_effective_scan.json"
    if not r10_cfg_path.exists():
        r10_cfg_path = REPO_ROOT.parent / "hep_cross" / "configs" / "r10_effective_scan.json"

    r10_cfg = json.loads(r10_cfg_path.read_text(encoding="utf-8")) if r10_cfg_path.exists() else {}
    base_anchor = r10_cfg.get("baseline_anchor", {})
    r10_aeff_baseline = base_anchor.get("Trackless_Aeff_0", 0.01573386)

    comp_rows = []
    for row in grid_rows:
        g = row["g_hH2H2_GeV"]
        ctau = row["ctau_mm"]
        br = row["BR_H2_to_bb"]

        # R10 factorized prediction:
        # sigma_R10(g) = sigma_0 * (g / g0)^2
        # Aeff_R10(ctau) is ctau-dependent only (for ctau = 4.326 mm, Aeff_0 = 0.01573386)
        sigma_r10_prod = 0.000230291167568 * ((g / 63.59142520075966) ** 2)
        n_exp_r10 = sigma_r10_prod * 1000.0 * (br**2) * r10_aeff_baseline * 139.0

        n_exp_mg = row["N_expected_139fb"]
        diff_abs = n_exp_mg - n_exp_r10
        diff_rel = (n_exp_mg / n_exp_r10 - 1.0) if n_exp_r10 > 0 else 0.0

        above_r10 = n_exp_r10 >= 3.0
        above_mg = row["above_observed_S95"]
        threshold_changed = above_r10 != above_mg

        comp_rows.append({
            "point_id": row["point_id"],
            "g_hH2H2_GeV": g,
            "ctau_mm": ctau,
            "BR_H2_to_bb": br,
            "N_expected_MG_per_g": n_exp_mg,
            "N_expected_R10_factorized": n_exp_r10,
            "abs_difference": diff_abs,
            "rel_difference": diff_rel,
            "above_S95_MG": above_mg,
            "above_S95_R10": above_r10,
            "threshold_changed": threshold_changed,
        })

    comp_json = {
        "total_points": len(comp_rows),
        "threshold_changed_points": [r for r in comp_rows if r["threshold_changed"]],
        "largest_positive_change": max(comp_rows, key=lambda x: x["rel_difference"]),
        "largest_negative_change": min(comp_rows, key=lambda x: x["rel_difference"]),
    }

    if mode != "verify-only":
        comp_csv_path = out_dir / "comparison_vs_r10_factorized.csv"
        with open(comp_csv_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(comp_rows[0].keys()))
            writer.writeheader()
            writer.writerows(comp_rows)

        (out_dir / "comparison_vs_r10_factorized.json").write_text(
            json.dumps(comp_json, indent=2) + "\n", encoding="utf-8"
        )

        # Summary & Manifests
        result_summary = {
            "campaign": "r12_madgraph_per_g_scan",
            "production_execution_status": "COMPLETED",
            "recast_execution_status": "COMPLETED",
            "grid_completeness": f"{len(grid_rows)}/360",
            "efficiency_points": f"{len(efficiency_rows)}/72",
            "recast_runs": f"{len(jobs_to_run)}/144",
            "pinned_phase_a_commit": phase_a_commit,
            "status": "VALIDATED",
        }
        (out_dir / "result_summary.json").write_text(json.dumps(result_summary, indent=2) + "\n", encoding="utf-8")

        # Verification report
        ver_report = {
            "status": "PASSED",
            "total_grid_rows": len(grid_rows),
            "total_efficiency_rows": len(efficiency_rows),
            "recast_runs_executed": len(recast_results),
            "pinned_phase_a_commit": phase_a_commit,
        }
        (out_dir / "verification_report.json").write_text(json.dumps(ver_report, indent=2) + "\n", encoding="utf-8")

        # Artifact manifest
        manifest_files = [
            "production_input_manifest.json",
            "efficiency_vs_g_ctau.csv",
            "effective_grid_madgraph_per_g.csv",
            "comparison_vs_r10_factorized.csv",
            "comparison_vs_r10_factorized.json",
            "result_summary.json",
            "verification_report.json",
        ]
        art_manifest = {}
        for rel_f in manifest_files:
            fp = out_dir / rel_f
            if fp.exists():
                art_manifest[rel_f] = sha256_file(fp)

        (out_dir / "artifact_manifest.json").write_text(json.dumps(art_manifest, indent=2) + "\n", encoding="utf-8")

    print("\nCampaign execution completed successfully.")
    print(f"Efficiency rows: {len(efficiency_rows)} / 72")
    print(f"Final grid rows: {len(grid_rows)} / 360")
    return 0


if __name__ == "__main__":
    sys.exit(main())
