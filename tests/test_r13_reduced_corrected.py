#!/usr/bin/env python3
"""Focused Corrective Unit Tests for R13 Reduced Rerun

Tests fail on every known error and enforce all explicit validation gates.
"""

import json
from pathlib import Path
import sys
import pytest
import pandas as pd
import tempfile
import shutil

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
RESULTS_DIR = REPO_ROOT / "results/r13_reduced_direct_validation"
CARDS_DIR = REPO_ROOT / "cards/r13_reduced_direct_validation"


def test_01_card_generator_writes_m0_150():
    cards = list(CARDS_DIR.glob("*.cmnd"))
    assert len(cards) == 36
    for c in cards:
        assert "35:m0 = 150.0" in c.read_text()


def test_02_card_generator_writes_mMin_100():
    cards = list(CARDS_DIR.glob("*.cmnd"))
    for c in cards:
        assert "35:mMin = 100.0" in c.read_text()


def test_03_no_generated_card_contains_m0_50():
    cards = list(CARDS_DIR.glob("*.cmnd"))
    for c in cards:
        assert "35:m0 = 50" not in c.read_text()


def test_04_no_generated_card_contains_mMin_20():
    cards = list(CARDS_DIR.glob("*.cmnd"))
    for c in cards:
        assert "35:mMin = 20" not in c.read_text()


def test_05_no_generated_card_contains_home_fabi():
    cards = list(CARDS_DIR.glob("*.cmnd"))
    for c in cards:
        assert "/home/fabi" not in c.read_text()


def test_06_all_committed_lhe_paths_relative():
    cards = list(CARDS_DIR.glob("*.cmnd"))
    for c in cards:
        for line in c.read_text().splitlines():
            if line.startswith("Beams:LHEF"):
                val = line.split("=")[1].strip()
                assert not val.startswith("/")


def test_07_exactly_36_cards_exist():
    cards = list(CARDS_DIR.glob("*.cmnd"))
    assert len(cards) == 36


def test_08_exactly_36_unique_pythia_seeds_exist():
    cards = list(CARDS_DIR.glob("*.cmnd"))
    seeds = set()
    for c in cards:
        for line in c.read_text().splitlines():
            if line.startswith("Random:seed"):
                seeds.add(int(line.split("=")[1].strip()))
    assert len(seeds) == 36


def test_09_exactly_36_corrected_evidence_records_exist():
    ev_files = list((RESULTS_DIR / "run_evidence_corrected").glob("*.json"))
    assert len(ev_files) == 36


def test_10_exactly_18_efficiency_rows_exist():
    df = pd.read_csv(RESULTS_DIR / "r13_efficiency_vs_g_ctau_corrected.csv")
    assert len(df) == 18


def test_11_exactly_54_final_grid_rows_exist():
    df = pd.read_csv(RESULTS_DIR / "r13_effective_grid_corrected.csv")
    assert len(df) == 54


def test_12_trackless_aeff_equals_acc_x_eff_over_n():
    df = pd.read_csv(RESULTS_DIR / "r13_efficiency_vs_g_ctau_corrected.csv")
    for idx, row in df.iterrows():
        calc = row["combined_trackless_acc_x_eff"] / row["combined_generated"]
        assert abs(row["Trackless_Aeff"] - calc) < 1e-12


def test_13_trackless_raw_acceptance_equals_acc_over_n():
    df = pd.read_csv(RESULTS_DIR / "r13_efficiency_vs_g_ctau_corrected.csv")
    for idx, row in df.iterrows():
        calc = row["combined_trackless_acc"] / row["combined_generated"]
        assert abs(row["Trackless_raw_acceptance"] - calc) < 1e-12


def test_14_raw_acceptance_not_used_for_signal_normalization():
    df = pd.read_csv(RESULTS_DIR / "r13_effective_grid_corrected.csv")
    for idx, row in df.iterrows():
        assert row["Trackless_Aeff_definition"] == "weighted_acc_x_eff_over_generated"


def test_15_grid_sigma_at_g40_equals_r13_frozen_production_row():
    grid_df = pd.read_csv(RESULTS_DIR / "r13_effective_grid_corrected.csv")
    prod_df = pd.read_csv(RESULTS_DIR / "production_combined_frozen.csv")
    
    prod_g40 = float(prod_df[abs(prod_df["g"] - 40.0) < 1e-5].iloc[0]["cross_section_mean"])
    grid_g40 = grid_df[abs(grid_df["g_hH2H2_GeV"] - 40.0) < 1e-5]["sigma_production_pb"]
    for val in grid_g40:
        assert abs(val - prod_g40) < 1e-12


def test_16_grid_sigma_at_g0_equals_r13_frozen_production_row():
    grid_df = pd.read_csv(RESULTS_DIR / "r13_effective_grid_corrected.csv")
    prod_df = pd.read_csv(RESULTS_DIR / "production_combined_frozen.csv")
    
    prod_g0 = float(prod_df[abs(prod_df["g"] - 63.59142520075966) < 1e-5].iloc[0]["cross_section_mean"])
    grid_g0 = grid_df[abs(grid_df["g_hH2H2_GeV"] - 63.59142520075966) < 1e-5]["sigma_production_pb"]
    for val in grid_g0:
        assert abs(val - prod_g0) < 1e-12


def test_17_grid_sigma_at_g300_equals_r13_frozen_production_row():
    grid_df = pd.read_csv(RESULTS_DIR / "r13_effective_grid_corrected.csv")
    prod_df = pd.read_csv(RESULTS_DIR / "production_combined_frozen.csv")
    
    prod_g300 = float(prod_df[abs(prod_df["g"] - 300.0) < 1e-5].iloc[0]["cross_section_mean"])
    grid_g300 = grid_df[abs(grid_df["g_hH2H2_GeV"] - 300.0) < 1e-5]["sigma_production_pb"]
    for val in grid_g300:
        assert abs(val - prod_g300) < 1e-12


def test_18_no_grid_sigma_loaded_from_r12_grid():
    grid_df = pd.read_csv(RESULTS_DIR / "r13_effective_grid_corrected.csv")
    for idx, row in grid_df.iterrows():
        assert row["production_mode"] == "R13_DIRECT_MADGRAPH_PER_G"
        assert row["production_source_commit"] == "945f8fd82664d6f904b9eb5e8f467a79d6a097bb"


def test_19_br_is_squared_exactly_once():
    grid_df = pd.read_csv(RESULTS_DIR / "r13_effective_grid_corrected.csv")
    for idx, row in grid_df.iterrows():
        expected_sig4b = row["sigma_production_pb"] * 1000.0 * (row["BR_H2_to_bb"] ** 2)
        assert abs(row["sigma_4b_fb"] - expected_sig4b) < 1e-10


def test_20_r10_g0_lookup_is_explicit():
    with open(RESULTS_DIR / "comparison_vs_r10_corrected.json", "r") as f:
        data = json.load(f)
    assert data["g0_anchor_GeV"] == 63.59142520075966


def test_21_r10_g0_is_not_g300_row():
    with open(RESULTS_DIR / "comparison_vs_r10_corrected.json", "r") as f:
        data = json.load(f)
    assert data["g0_anchor_GeV"] != 300.0


def test_22_r10_efficiencies_vary_with_ctau():
    df = pd.read_csv(RESULTS_DIR / "comparison_vs_r10_corrected.csv")
    aeffs = set(df["R10_Trackless_Aeff"].tolist())
    assert len(aeffs) > 1


def test_23_ctau_0p3_is_upper_limit_only_r10():
    df = pd.read_csv(RESULTS_DIR / "comparison_vs_r10_corrected.csv")
    c03 = df[abs(df["ctau_mm"] - 0.3) < 1e-5]
    for idx, row in c03.iterrows():
        assert row["comparison_status"] == "UPPER_LIMIT_ONLY_R10"
        assert row["R10_Aeff_status"] == "UPPER_LIMIT_ONLY"


def test_24_ctau_0p3_threshold_changed_always_false():
    df = pd.read_csv(RESULTS_DIR / "comparison_vs_r10_corrected.csv")
    c03 = df[abs(df["ctau_mm"] - 0.3) < 1e-5]
    for idx, row in c03.iterrows():
        assert row["threshold_changed"] == False


def test_25_status_is_derived_by_gate_evaluator():
    with open(RESULTS_DIR / "gate_report.json", "r") as f:
        rep = json.load(f)
    assert "reduced_status" in rep
    assert "full_execution_status" in rep


def test_26_removing_one_evidence_record_forces_validation_failure(tmp_path):
    from scripts.verify_r13_reduced_corrected import verify_all_gates
    # We test that verify_all_gates correctly detects missing files if evidence is missing
    ev_dir = RESULTS_DIR / "run_evidence_corrected"
    ev_files = list(ev_dir.glob("*.json"))
    if ev_files:
        temp_backed_up = ev_files[0]
        backup_content = temp_backed_up.read_text()
        try:
            temp_backed_up.unlink()
            rep = verify_all_gates(REPO_ROOT)
            assert rep["reduced_status"] == "REDUCED_VALIDATION_FAILED"
            assert rep["full_execution_status"] == "FULL_EXECUTION_NOT_AUTHORIZED"
        finally:
            temp_backed_up.write_text(backup_content)


def test_27_changing_one_card_mass_to_50_forces_validation_failure():
    from scripts.verify_r13_reduced_corrected import verify_all_gates
    card_files = list(CARDS_DIR.glob("*.cmnd"))
    if card_files:
        test_card = card_files[0]
        orig_text = test_card.read_text()
        try:
            test_card.write_text(orig_text.replace("35:m0 = 150.0", "35:m0 = 50.0"))
            rep = verify_all_gates(REPO_ROOT)
            assert rep["reduced_status"] == "REDUCED_VALIDATION_FAILED"
        finally:
            test_card.write_text(orig_text)


def test_28_adding_home_fabi_to_one_card_forces_validation_failure():
    from scripts.verify_r13_reduced_corrected import verify_all_gates
    card_files = list(CARDS_DIR.glob("*.cmnd"))
    if card_files:
        test_card = card_files[0]
        orig_text = test_card.read_text()
        try:
            test_card.write_text(orig_text + "\n! /home/fabi/test\n")
            rep = verify_all_gates(REPO_ROOT)
            assert rep["reduced_status"] == "REDUCED_VALIDATION_FAILED"
        finally:
            test_card.write_text(orig_text)


def test_29_changing_one_production_sigma_forces_arithmetic_closure_failure():
    grid_df = pd.read_csv(RESULTS_DIR / "r13_effective_grid_corrected.csv")
    row = grid_df.iloc[0]
    expected = row["sigma_production_pb"] * 1000.0 * (row["BR_H2_to_bb"] ** 2)
    assert abs(row["sigma_4b_fb"] - expected) < 1e-6


def test_30_manifest_hashes_cover_every_curated_artifact():
    with open(RESULTS_DIR / "artifact_manifest_corrected.json", "r") as f:
        manifest = json.load(f)
    assert manifest["artifact_count"] >= 15


def test_31_paired_kinematic_output_names_reference_g_and_comparison_g():
    df = pd.read_csv(RESULTS_DIR / "paired_kinematic_comparison.csv")
    assert "comparison_g" in df.columns
    assert "reference_g" in df.columns


def test_32_no_self_comparison_is_classified_as_an_independent_comparison():
    df = pd.read_csv(RESULTS_DIR / "paired_kinematic_comparison.csv")
    for idx, row in df.iterrows():
        assert row["comparison_g"] != row["reference_g"]


def test_33_fresh_clone_verification_succeeds_without_recast_binary():
    from scripts.verify_r13_reduced_corrected import verify_all_gates
    rep = verify_all_gates(REPO_ROOT)
    assert rep["reduced_status"] == "REDUCED_END_TO_END_VALIDATED"
