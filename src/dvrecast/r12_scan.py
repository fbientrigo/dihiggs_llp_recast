"""R12 Mission: Parameterized Pythia/Recast Scan helpers and calculations."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

G_VALUES: list[float] = [
    40.0,
    63.59142520075966,
    100.0,
    150.0,
    205.09272542237372,
    300.0,
]

CTAU_VALUES: list[float] = [
    0.3,
    1.0,
    3.0,
    4.326221529733112,
    10.0,
    30.0,
    100.0,
    200.0,
    300.0,
    500.0,
    700.0,
    1000.0,
]

BR_VALUES: list[float] = [
    0.1,
    0.25,
    0.5,
    0.7567374858085787,
    1.0,
]

PRODUCTION_RUNS: list[str] = ["run_01", "run_02"]

LUMI_FB_INV = 139.0
OBSERVED_S95 = 3.0


def fmt_g_dir(g: float) -> str:
    """Format coupling directory name: 40.0 -> g40, 63.59142520075966 -> g63p591425."""
    if abs(g - 63.59142520075966) < 1e-5:
        return "g63p591425"
    if abs(g - 205.09272542237372) < 1e-5:
        return "g205p092725"
    s = f"{g:.6g}".replace(".", "p")
    return f"g{s}"


def fmt_ctau_tag(ctau: float) -> str:
    """Format ctau tag: 0.3 -> ctau_0p3mm, 4.326221529733112 -> ctau_4p326mm."""
    if abs(ctau - 4.326221529733112) < 1e-5:
        return "ctau_4p326mm"
    s = f"{ctau:.6g}".replace(".", "p")
    return f"ctau_{s}mm"


def derive_pythia_seed(g_idx: int, ctau_idx: int, run_idx: int) -> int:
    """Derive deterministic unique Pythia seed.

    g_idx: 0..5
    ctau_idx: 0..11
    run_idx: 1..2
    """
    return 120000 + g_idx * 1000 + ctau_idx * 10 + run_idx


def generate_pythia_card_content(
    g: float,
    ctau_mm: float,
    run_name: str,
    lhe_rel_path: str,
    pythia_seed: int,
) -> str:
    """Generate Pythia 8 configuration card (.cmnd) for recast."""
    lines = [
        f"! R12 recast card: g = {g} GeV, ctau = {ctau_mm} mm, run = {run_name}",
        "Main:numberOfEvents = 1000",
        "Main:timesAllowErrors = 3",
        "Init:showChangedSettings = on",
        "Init:showChangedParticleData = off",
        "Next:numberCount = 5000",
        "Next:numberShowInfo = 0",
        "Next:numberShowProcess = 0",
        "Next:numberShowEvent = 0",
        "",
        "Random:setSeed = on",
        f"Random:seed = {pythia_seed}",
        "",
        "PartonLevel:MPI = off",
        "PartonLevel:ISR = on",
        "PartonLevel:FSR = on",
        "HadronLevel:Hadronize = on",
        "Tune:pp = 21",
        "",
        "Higgs:useBSM = on",
        "35:m0 = 150.",
        "35:mMin = 100.",
        "35:tauCalc = off",
        f"35:tau0 = {ctau_mm}",
        "35:onMode = off",
        "35:onIfMatch = 5 -5",
        "",
        "Recast:llpPdgIds = {35}",
        f"Recast:llpTau0 = {ctau_mm}",
        "LesHouches:setLifetime = 2",
        "",
        "Beams:frameType = 4",
        "LHEFInputs:nSubruns = 1",
        "Main:subrun = 0",
        f"Beams:LHEF = {lhe_rel_path}",
        "",
    ]
    return "\n".join(lines)


def calculate_aggregated_efficiency(
    acc_x_eff_1: float,
    gen1: int,
    acc_x_eff_2: float,
    gen2: int,
) -> tuple[float, float]:
    """Aggregate two production runs using weighted acc_x_eff and compute provisional uncertainty.

    Aeff(g, ctau) = (acc_x_eff_1 + acc_x_eff_2) / (gen1 + gen2)
    delta_Aeff = provisional between-run spread
    """
    gen_tot = gen1 + gen2
    acc_x_eff_tot = acc_x_eff_1 + acc_x_eff_2
    if gen_tot <= 0:
        return 0.0, 0.0

    aeff = acc_x_eff_tot / gen_tot
    aeff_1 = acc_x_eff_1 / gen1 if gen1 > 0 else 0.0
    aeff_2 = acc_x_eff_2 / gen2 if gen2 > 0 else 0.0
    err = abs(aeff_1 - aeff_2)
    return aeff, err


def calculate_final_grid_row(
    point_id: str,
    g: float,
    ctau: float,
    br_bb: float,
    sigma_prod_pb: float,
    sigma_prod_err_pb: float,
    aeff: float,
    aeff_err: float,
    n_gen_tot: int,
    n_sel_tot: int,
    source_commit: str,
    run_count: int = 2,
    lumi_fb: float = LUMI_FB_INV,
    observed_s95: float = OBSERVED_S95,
    aeff_definition: str = "weighted_acc_x_eff_over_generated",
    raw_acceptance: float = 0.0,
    aeff_uncertainty_model: str = "provisional_between_run_spread",
    status: str = "VALIDATED"
) -> dict[str, Any]:
    """Calculate single phenomenological row for final 360-point grid.

    sigma_4b_fb = sigma_prod_pb * 1000 * BR_bb^2
    visible_sigma_fb = sigma_4b_fb * Trackless_Aeff
    N_expected_139fb = visible_sigma_fb * lumi_fb
    """
    br_sq = br_bb**2
    sigma_4b_fb = sigma_prod_pb * 1000.0 * br_sq
    visible_sigma_fb = sigma_4b_fb * aeff
    n_expected = visible_sigma_fb * lumi_fb

    # Propagated error on N_expected
    rel_err_prod = (sigma_prod_err_pb / sigma_prod_pb) if sigma_prod_pb > 0 else 0.0
    rel_err_aeff = (aeff_err / aeff) if aeff > 0 else 0.0
    rel_err_tot = math.sqrt(rel_err_prod**2 + rel_err_aeff**2)
    n_expected_err = n_expected * rel_err_tot

    n_over_s95 = n_expected / observed_s95 if observed_s95 > 0 else 0.0
    above_s95 = n_expected >= observed_s95

    return {
        "point_id": point_id,
        "g_hH2H2_GeV": g,
        "GHphiphi_GeV": -abs(g),
        "ctau_mm": ctau,
        "BR_H2_to_bb": br_bb,
        "sigma_production_pb": sigma_prod_pb,
        "sigma_production_error_pb": sigma_prod_err_pb,
        "production_source_commit": source_commit,
        "production_run_count": run_count,
        "Trackless_Aeff": aeff,
        "Trackless_Aeff_error": aeff_err,
        "Trackless_Aeff_definition": aeff_definition,
        "Trackless_raw_acceptance": raw_acceptance,
        "Trackless_Aeff_uncertainty_model": aeff_uncertainty_model,
        "recast_generated_events": n_gen_tot,
        "recast_selected_events": n_sel_tot,
        "sigma_4b_fb": sigma_4b_fb,
        "visible_sigma_fb": visible_sigma_fb,
        "N_expected_139fb": n_expected,
        "N_expected_error": n_expected_err,
        "observed_S95": observed_s95,
        "N_over_observed_S95": n_over_s95,
        "above_observed_S95": above_s95,
        "production_evaluation_mode": "madgraph_per_g",
        "decay_mode": "forced_bb",
        "BR_application": "analytical_BR_squared",
        "interpretation": "EFFECTIVE_PHENOMENOLOGICAL",
        "status": status,
    }
