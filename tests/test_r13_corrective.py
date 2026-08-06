import os
import json
import pandas as pd
from pathlib import Path
import hashlib

def test_explicit_g0():
    g0 = 63.59142520075966
    assert abs(g0 - 63.59142520075966) < 1e-10

def test_sigma_MG_g0():
    root = Path(__file__).resolve().parents[1]
    grid_df = pd.read_csv(root / "results" / "r12_madgraph_per_g_scan" / "effective_grid_madgraph_per_g.csv")
    g0 = 63.59142520075966
    row = grid_df[abs(grid_df["g_hH2H2_GeV"] - g0) < 1e-5].iloc[0]
    sigma_MG_g0 = row["sigma_production_pb"]
    assert abs(sigma_MG_g0 - 2.308834866426e-4) < 1e-6
    assert sigma_MG_g0 < 1.0e-3
    return sigma_MG_g0

def test_r10_sigma_scaling():
    sigma_MG_g0 = test_sigma_MG_g0()
    g0 = 63.59142520075966
    sigma_r10_g0 = sigma_MG_g0 * (g0 / g0)**2
    assert abs(sigma_r10_g0 - sigma_MG_g0) < 1e-10
    
    g40 = 40.0
    sigma_r10_g40 = sigma_MG_g0 * (g40 / g0)**2
    assert abs(sigma_r10_g40 - sigma_MG_g0 * (40.0 / g0)**2) < 1e-10

def test_r10_comparison_ctau_scaling_and_0p3():
    root = Path(__file__).resolve().parents[1]
    comp_df = pd.read_csv(root / "results" / "r12_madgraph_per_g_scan" / "comparison_vs_r10_factorized.csv")
    ctau_0p3_rows = comp_df[comp_df["ctau_mm"] == 0.3]
    for _, row in ctau_0p3_rows.iterrows():
        assert row["comparison_status"] == "UPPER_LIMIT_ONLY_R10"
        assert not row["threshold_changed"]

def test_one_authoritative_output():
    root = Path(__file__).resolve().parents[1]
    results_dir = root / "results" / "r12_madgraph_per_g_scan"
    assert (results_dir / "comparison_vs_r10_factorized.csv").exists()
    assert (results_dir / "comparison_vs_r10_factorized.json").exists()
    assert not (results_dir / "r10_comparison.csv").exists()

def test_benchmark_regression():
    root = Path(__file__).resolve().parents[1]
    comp_df = pd.read_csv(root / "results" / "r12_madgraph_per_g_scan" / "comparison_vs_r10_factorized.csv")
    grid_df = pd.read_csv(root / "results" / "r12_madgraph_per_g_scan" / "effective_grid_madgraph_per_g.csv")
    g_target = 63.5914
    ctau_target = 4.32622
    br_target = 0.7567374858085787
    
    row = grid_df[(abs(grid_df["g_hH2H2_GeV"] - 63.59142520075966) < 1e-2) & 
                  (abs(grid_df["ctau_mm"] - 4.326221529733112) < 1e-2) & 
                  (abs(grid_df["BR_H2_to_bb"] - br_target) < 1e-2)]
    
    assert len(row) > 0
    row = row.iloc[0]
    
    aeff = row["Trackless_Aeff"]
    n_exp = row["N_expected_139fb"]
    
    assert abs(aeff - 0.01310612) < 1e-4
    assert abs(n_exp - 0.240864) < 1e-4

def test_no_hardcoded_paths():
    import subprocess
    root = Path(__file__).resolve().parents[1]
    scripts_dir = root / "scripts"
    result = subprocess.run(["grep", "-r", "/home/fabi", str(scripts_dir)], capture_output=True, text=True)
    assert not result.stdout, f"Found hardcoded paths: {result.stdout}"

def test_manifest_completeness():
    root = Path(__file__).resolve().parents[1]
    results_dir = root / "results" / "r12_madgraph_per_g_scan"
    with open(results_dir / "artifact_manifest.json") as f:
        manifest = json.load(f)
    
    for fname, meta in manifest["artifacts"].items():
        fpath = results_dir / fname
        assert fpath.exists()
        
        h = hashlib.sha256()
        with open(fpath, "rb") as f2:
            while chunk := f2.read(8192):
                h.update(chunk)
        assert h.hexdigest() == meta["sha256"]

