"""Tests for R12 parameterized Pythia/Recast scan module."""

from __future__ import annotations

import math
import pytest

from dvrecast.r12_scan import (
    BR_VALUES,
    CTAU_VALUES,
    G_VALUES,
    PRODUCTION_RUNS,
    calculate_aggregated_efficiency,
    calculate_final_grid_row,
    derive_pythia_seed,
    fmt_ctau_tag,
    fmt_g_dir,
    generate_pythia_card_content,
)


def test_r12_grid_dimensions():
    assert len(G_VALUES) == 6
    assert len(CTAU_VALUES) == 12
    assert len(BR_VALUES) == 5
    assert len(PRODUCTION_RUNS) == 2
    # 6 * 12 * 2 = 144 recast runs
    # 6 * 12 * 5 = 360 final phenomenological rows


def test_fmt_tags():
    assert fmt_g_dir(40.0) == "g40"
    assert fmt_g_dir(63.59142520075966) == "g63p591425"
    assert fmt_ctau_tag(4.326221529733112) == "ctau_4p326mm"
    assert fmt_ctau_tag(100.0) == "ctau_100mm"


def test_pythia_seed_uniqueness():
    seeds = set()
    for g_idx in range(len(G_VALUES)):
        for ctau_idx in range(len(CTAU_VALUES)):
            for run_idx in range(1, 3):
                s = derive_pythia_seed(g_idx, ctau_idx, run_idx)
                assert s not in seeds
                seeds.add(s)

    assert len(seeds) == 6 * 12 * 2  # 144 unique seeds


def test_generate_pythia_card_content():
    card = generate_pythia_card_content(
        g=100.0,
        ctau_mm=4.326221529733112,
        run_name="run_01",
        lhe_rel_path="data/raw/r12_scan/g100_run_01.lhe.gz",
        pythia_seed=122031,
    )
    assert "Main:numberOfEvents = 1000" in card
    assert "Random:seed = 122031" in card
    assert "35:tau0 = 4.326221529733112" in card
    assert "Recast:llpTau0 = 4.326221529733112" in card
    assert "35:onIfMatch = 5 -5" in card
    assert "Beams:LHEF = data/raw/r12_scan/g100_run_01.lhe.gz" in card


def test_calculate_aggregated_efficiency():
    aeff, err = calculate_aggregated_efficiency(15, 1000, 16, 1000)
    assert pytest.approx(aeff, rel=1e-5) == 31 / 2000
    expected_err = abs(15/1000 - 16/1000)
    assert pytest.approx(err, rel=1e-5) == expected_err


def test_calculate_final_grid_row():
    row = calculate_final_grid_row(
        point_id="row_001",
        g=63.59142520075966,
        ctau=4.326221529733112,
        br_bb=0.7567374858085787,
        sigma_prod_pb=0.000230291167568,
        sigma_prod_err_pb=0.000005,
        aeff=0.01573386,
        aeff_err=0.0005,
        n_gen_tot=2000,
        n_sel_tot=31,
        source_commit="test_sha",
    )
    assert row["g_hH2H2_GeV"] == 63.59142520075966
    assert row["ctau_mm"] == 4.326221529733112
    assert row["BR_H2_to_bb"] == 0.7567374858085787
    assert row["production_evaluation_mode"] == "madgraph_per_g"
    assert row["decay_mode"] == "forced_bb"
    assert row["BR_application"] == "analytical_BR_squared"
    assert row["visible_sigma_fb"] > 0
    assert row["N_expected_139fb"] > 0
