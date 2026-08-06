import json
import os
import glob
import pandas as pd
import hashlib
from scipy.stats import beta
from pathlib import Path
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=str, default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--hep-cross-dir", type=str)
    parser.add_argument("--results-dir", type=str)
    parser.add_argument("--r10-reference", type=str)
    args = parser.parse_args()

    worktree = args.repo_root
    results_dir = args.results_dir or os.path.join(worktree, "results/r12_madgraph_per_g_scan")
    r10_table_path = args.r10_reference or os.path.join(worktree, "data/r10_reference/efficiency_vs_ctau.csv")
    evidence_dir = os.path.join(results_dir, "run_evidence")

    # 1. Load evidences
    evidences = {}
    for path in glob.glob(os.path.join(evidence_dir, "*.json")):
        with open(path, "r") as f:
            data = json.load(f)
            key = (data["g_hH2H2_GeV"], data["ctau_mm"], data["production_run"])
            evidences[key] = data

    # 2. Build efficiency CSV
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(worktree, "src")))
    from dvrecast.r12_scan import G_VALUES, CTAU_VALUES, BR_VALUES, calculate_final_grid_row

    efficiency_rows = []
    for g in G_VALUES:
        for ctau in CTAU_VALUES:
            ev1 = evidences.get((g, ctau, "run_01"))
            ev2 = evidences.get((g, ctau, "run_02"))
            
            parsed1 = ev1 and ev1["parse_status"] == "PARSED"
            parsed2 = ev2 and ev2["parse_status"] == "PARSED"
            
            run_01_gen = ev1["n_events"] if parsed1 else 0
            run_01_acc = ev1["trackless_acc_count"] if parsed1 else 0
            run_01_acc_x_eff = ev1["trackless_acc_x_eff"] if parsed1 else 0.0
            run_01_raw = ev1["trackless_raw_acceptance"] if parsed1 else 0.0
            run_01_aeff = ev1["trackless_Aeff_weighted"] if parsed1 else 0.0
            
            run_02_gen = ev2["n_events"] if parsed2 else 0
            run_02_acc = ev2["trackless_acc_count"] if parsed2 else 0
            run_02_acc_x_eff = ev2["trackless_acc_x_eff"] if parsed2 else 0.0
            run_02_raw = ev2["trackless_raw_acceptance"] if parsed2 else 0.0
            run_02_aeff = ev2["trackless_Aeff_weighted"] if parsed2 else 0.0
            
            combined_gen = run_01_gen + run_02_gen
            combined_acc = run_01_acc + run_02_acc
            combined_acc_x_eff = run_01_acc_x_eff + run_02_acc_x_eff
            
            raw_acceptance = combined_acc / combined_gen if combined_gen > 0 else 0.0
            weighted_aeff = combined_acc_x_eff / combined_gen if combined_gen > 0 else 0.0
            
            # CI 95
            k = combined_acc
            n = combined_gen
            alpha = 0.05
            if k == 0 and n > 0:
                ci_low = 0.0
                ci_high = 1 - (alpha/2)**(1/n)
            elif n > 0:
                ci_low = beta.ppf(alpha/2, k, n-k+1)
                ci_high = beta.ppf(1-alpha/2, k+1, n-k)
            else:
                ci_low = 0.0
                ci_high = 0.0
                
            spread = abs(run_01_aeff - run_02_aeff)
            
            seed_status = "ASYMMETRIC"
            if parsed1 and parsed2:
                if run_01_acc > 0 and run_02_acc > 0:
                    seed_status = "COMPATIBLE"
                elif run_01_acc == 0 and run_02_acc == 0:
                    seed_status = "ZERO_BOTH"
                    
            status = "FAILED"
            if parsed1 and parsed2:
                status = "VALIDATED"
                
            row = {
                "g_hH2H2_GeV": g,
                "GHphiphi_GeV": -g,
                "ctau_mm": ctau,
                "run_01_generated": run_01_gen,
                "run_01_trackless_acc": run_01_acc,
                "run_01_trackless_acc_x_eff": run_01_acc_x_eff,
                "run_01_raw_acceptance": run_01_raw,
                "run_01_Trackless_Aeff": run_01_aeff,
                "run_02_generated": run_02_gen,
                "run_02_trackless_acc": run_02_acc,
                "run_02_trackless_acc_x_eff": run_02_acc_x_eff,
                "run_02_raw_acceptance": run_02_raw,
                "run_02_Trackless_Aeff": run_02_aeff,
                "combined_generated": combined_gen,
                "combined_trackless_acc": combined_acc,
                "combined_trackless_acc_x_eff": combined_acc_x_eff,
                "Trackless_raw_acceptance": raw_acceptance,
                "Trackless_Aeff": weighted_aeff,
                "Trackless_Aeff_definition": "weighted_acc_x_eff_over_generated",
                "Trackless_raw_acceptance_ci95_low": ci_low,
                "Trackless_raw_acceptance_ci95_high": ci_high,
                "between_run_Aeff_spread": spread,
                "Trackless_Aeff_uncertainty_model": "provisional_between_run_spread",
                "seed_compatibility_status": seed_status,
                "status": status
            }
            efficiency_rows.append(row)

    eff_df = pd.DataFrame(efficiency_rows)
    eff_df.to_csv(os.path.join(results_dir, "efficiency_vs_g_ctau.csv"), index=False)

    # 3. Build effective grid
    old_grid = pd.read_csv(os.path.join(results_dir, "effective_grid_madgraph_per_g.csv"))
    
    g0 = 63.59142520075966
    old_g0_row = old_grid[abs(old_grid["g_hH2H2_GeV"] - g0) < 1e-5].iloc[0]
    sigma_MG_g0 = old_g0_row["sigma_production_pb"]
    
    assert abs(sigma_MG_g0 - 2.308834866426e-4) < 1e-6
    assert sigma_MG_g0 < 1.0e-3
    
    grid_rows = []
    for g in G_VALUES:
        g_str = f"{g:.1f}" if g.is_integer() else str(g)
        old_row = old_grid[abs(old_grid["g_hH2H2_GeV"] - g) < 1e-5].iloc[0]
        sigma_pb = old_row["sigma_production_pb"]
        sigma_err = old_row["sigma_production_error_pb"]
        commit = "29ba4ec128102ee1bddfc8f18d69222324ebbcea" # Fixed commit
        
        for ctau in CTAU_VALUES:
            eff_row = eff_df[(eff_df["g_hH2H2_GeV"] == g) & (eff_df["ctau_mm"] == ctau)].iloc[0]
            grid_status = "FAILED"
            if eff_row["status"] == "VALIDATED" and sigma_pb > 0:
                if eff_row["Trackless_Aeff"] > 0 or eff_row["seed_compatibility_status"] == "ZERO_BOTH":
                    grid_status = "VALIDATED"
                    
            for br in BR_VALUES:
                point_id = f"r12_g{g_str}_ctau{ctau}_br{br}"
                
                row = calculate_final_grid_row(
                    point_id=point_id,
                    g=g,
                    ctau=ctau,
                    br_bb=br,
                    sigma_prod_pb=sigma_pb,
                    sigma_prod_err_pb=sigma_err,
                    aeff=eff_row["Trackless_Aeff"],
                    aeff_err=eff_row["between_run_Aeff_spread"],
                    n_gen_tot=eff_row["combined_generated"],
                    n_sel_tot=eff_row["combined_trackless_acc"],
                    source_commit=commit,
                    run_count=2,
                    aeff_definition="weighted_acc_x_eff_over_generated",
                    raw_acceptance=eff_row["Trackless_raw_acceptance"],
                    aeff_uncertainty_model="provisional_between_run_spread",
                    status=grid_status
                )
                grid_rows.append(row)

    grid_df = pd.DataFrame(grid_rows)
    grid_df.to_csv(os.path.join(results_dir, "effective_grid_madgraph_per_g.csv"), index=False)

    # 4. R10 Comparison
    r10_df = pd.read_csv(r10_table_path)
    r10_dict = r10_df.set_index("ctau_mm").to_dict("index")

    comparison_rows = []
    for idx, row in grid_df.iterrows():
        if row["status"] != "VALIDATED": continue
        
        ctau = row["ctau_mm"]
        r10_row = r10_dict.get(ctau)
        if not r10_row: continue
        
        g = row["g_hH2H2_GeV"]
        br = row["BR_H2_to_bb"]
        
        sigma_R10_pb = sigma_MG_g0 * (g / g0)**2
        
        r10_aeff = r10_row["Trackless_Aeff"]
        
        n_exp_r10 = sigma_R10_pb * 1000 * (br**2) * r10_aeff * 139.0
        
        above_r10 = n_exp_r10 >= 3.0
        above_r12 = row["N_expected_139fb"] >= 3.0
        
        threshold_changed = (above_r10 != above_r12)
        comp_status = "DEFINITIVE"
        if ctau == 0.3:
            comp_status = "UPPER_LIMIT_ONLY_R10"
            threshold_changed = False
            
        comparison_rows.append({
            "point_id": row["point_id"],
            "g_hH2H2_GeV": g,
            "ctau_mm": ctau,
            "BR_H2_to_bb": br,
            "N_expected_R12": row["N_expected_139fb"],
            "above_S95_R12": above_r12,
            "R10_Aeff": r10_row["Trackless_Aeff"],
            "R10_Aeff_status": r10_row["Trackless_status"],
            "R10_Aeff_95CL_limit": r10_row["Trackless_Aeff_95CL_limit"],
            "N_expected_R10_factorized": n_exp_r10,
            "above_S95_R10": above_r10,
            "comparison_status": comp_status,
            "threshold_changed": threshold_changed
        })
        
    comp_df = pd.DataFrame(comparison_rows)
    comp_df.to_csv(os.path.join(results_dir, "comparison_vs_r10_factorized.csv"), index=False)
    comp_df.to_json(os.path.join(results_dir, "comparison_vs_r10_factorized.json"), orient="records", indent=2)

    # 5. Fix absolute paths in production manifest
    manifest_path = os.path.join(results_dir, "production_input_manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        for run in manifest.get("runs", []):
            for k in ["source_path", "relabeled_path", "local_materialization_path"]:
                if k in run: del run[k]
            
            g_tag = f"g{run['g']:g}".replace(".", "p")
            if "63.59" in str(run['g']): g_tag = "g63p591425"
            if "205.09" in str(run['g']): g_tag = "g205p092725"
            run["local_materialization_path_relative"] = f"results/r12_madgraph_per_g_scan/relabeled_lhes/{g_tag}_{run['production_run']}_pdg35.lhe.gz"

        manifest["schema_version"] = 2
        manifest["source_repository"] = "fbientrigo/dihiggs_hep_cross"
        manifest["source_commit"] = "29ba4ec128102ee1bddfc8f18d69222324ebbcea"

        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

    # 6. Rebuild artifact_manifest
    def file_sha256(filepath):
        h = hashlib.sha256()
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192): h.update(chunk)
        return h.hexdigest()

    artifact_manifest = {
        "artifacts": {}
    }

    files_to_hash = [
        "efficiency_vs_g_ctau.csv", 
        "effective_grid_madgraph_per_g.csv", 
        "comparison_vs_r10_factorized.csv", 
        "comparison_vs_r10_factorized.json",
        "production_input_manifest.json",
        "result_summary.json",
        "verification_report.json"
    ]
    
    # Create result summary and verification report
    res_summary = {
        "status": "R12_POSTPROCESSING_CORRECTED_PENDING_REVALIDATION"
    }
    with open(os.path.join(results_dir, "result_summary.json"), "w") as f:
        json.dump(res_summary, f, indent=2)

    verif_report = {
        "commit": "29ba4ec128102ee1bddfc8f18d69222324ebbcea",
        "notes": "Rebuilt R12 outputs with corrected R10 logic"
    }
    with open(os.path.join(results_dir, "verification_report.json"), "w") as f:
        json.dump(verif_report, f, indent=2)

    # Remove old r10_comparison.csv if it exists
    old_comp = os.path.join(results_dir, "r10_comparison.csv")
    if os.path.exists(old_comp):
        os.remove(old_comp)

    for fname in files_to_hash:
        fpath = os.path.join(results_dir, fname)
        if os.path.exists(fpath):
            artifact_manifest["artifacts"][fname] = {
                "sha256": file_sha256(fpath)
            }

    with open(os.path.join(results_dir, "artifact_manifest.json"), "w") as f:
        json.dump(artifact_manifest, f, indent=2)
        
    print("Outputs rebuilt successfully!")

if __name__ == "__main__":
    main()
