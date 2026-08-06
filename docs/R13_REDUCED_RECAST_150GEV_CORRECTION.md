# R13 Corrective Reduced Recast — 150 GeV Physics Contract Verification Report

## Executive Summary

This report documents the corrective repair and reduced physical rerun for R13 Phase B of the 2Higgs / DiHiggs LLP recast project.

The previous R13 Pythia/recast attempt was **invalidated** due to five identified flaws:
1. Pythia cards used the wrong LLP mass contract (`35:m0 = 50.0`, `35:mMin = 20.0` instead of `150.0` and `100.0`).
2. Committed cards contained absolute developer paths (`/home/fabi/...`).
3. Final grid script extracted production cross sections from R12 instead of the pinned R13 Phase A direct production table.
4. Validation status was hardcoded (`REDUCED_END_TO_END_VALIDATED`) without explicit gate calculation.
5. Kinematic shape analysis misused Kolmogorov-Smirnov (KS) tests on paired random seeds as proof of statistical independence.

In this corrective campaign:
- **MadGraph reruns**: Exactly `0` (Phase A inputs preserved).
- **Physical Pythia/recast reruns**: Exactly `36`.
- **Efficiency table rows**: Exactly `18`.
- **Final phenomenological grid rows**: Exactly `54`.
- **Validation Gates**: Every explicit gate in Groups A through I passed.

Derived Campaign Verdict: **`REDUCED_END_TO_END_VALIDATED`**
Derived Authorization Verdict: **`FULL_EXECUTION_AUTHORIZED`**

---

## 1. Phase A Inputs and Mass Contract Restoration

### 1.1 Preserved Phase A Source Identity
- **Repository**: `fbientrigo/dihiggs_hep_cross`
- **Branch**: `feat/r13-reduced-direct-production-validation`
- **Commit SHA**: `945f8fd82664d6f904b9eb5e8f467a79d6a097bb`
- **Pull Request**: `https://github.com/fbientrigo/dihiggs_hep_cross/pull/16`

The six direct MadGraph LHE files were materialized and verified from commit `945f8fd82664d6f904b9eb5e8f467a79d6a097bb`:
- `g = 40.0 GeV`: `run_01` (seed 211), `run_02` (seed 223)
- `g = 63.59142520075966 GeV`: `run_01` (seed 211), `run_02` (seed 223)
- `g = 300.0 GeV`: `run_01` (seed 211), `run_02` (seed 223)

Every input LHE was confirmed to contain exactly 1,000 events with two 150.0 GeV $H_2$ particles (PDG 9000006).

### 1.2 Structured LHE Relabeling
All 6 LHE files were relabelled ($9000006 \to 35$) using structured event-line replacing. All 4-momenta, masses, weights, and headers were preserved byte-for-byte. Per-LHE verification reports confirm `unexpected_changed_lines == 0`.

### 1.3 Corrected Pythia Card Contract
All 36 Pythia configuration cards were regenerated in `cards/r13_reduced_direct_validation/` with:
```text
35:m0 = 150.0
35:mMin = 100.0
35:tauCalc = off
35:tau0 = <ctau>
35:onMode = off
35:onIfMatch = 5 -5

Recast:llpPdgIds = {35}
Recast:llpTau0 = <ctau>
LesHouches:setLifetime = 2

Beams:LHEF = results/r13_reduced_direct_validation/relabeled_lhes/<name>.lhe.gz
```
Zero committed cards contain `/home/fabi`. All 36 Pythia seeds are unique and deterministic (`230000 + g_idx * 1000 + ctau_idx * 10 + run_idx`).

---

## 2. Direct Production Normalization & Grid Construction

The final grid calculation loads direct production cross sections exclusively from the frozen Phase A table `production_combined_frozen.csv`:
- $g = 40.0\text{ GeV}$: $\sigma_{\text{direct}} \approx 9.1384 \times 10^{-5}\text{ pb}$
- $g = 63.59142520075966\text{ GeV}$: $\sigma_{\text{direct}} \approx 2.30965 \times 10^{-4}\text{ pb}$
- $g = 300.0\text{ GeV}$: $\sigma_{\text{direct}} \approx 5.14035 \times 10^{-3}\text{ pb}$

No R12 production cross sections or effective grid values were used. The branching ratio for $H_2 \to b\bar{b}$ was applied analytically as $\text{BR}^2$ exactly once.

---

## 3. R10 Comparison & $c\tau=0.3$ mm Upper-Limit Handling

For $c\tau = 0.3\text{ mm}$, the R10 reference efficiency is central value 0 with a 95% CL upper limit of $\approx 0.001497866$. The R10 comparison script correctly handles this point as:
- `R10_Aeff_status = UPPER_LIMIT_ONLY`
- `comparison_status = UPPER_LIMIT_ONLY_R10`
- `threshold_changed = false`
- `classification_stability = UPPER_LIMIT_ONLY`

No definitive threshold-change claim is made for $c\tau = 0.3\text{ mm}$.

---

## 4. Paired-Event Kinematic Shape Analysis

Because Phase A MadGraph runs re-use random seeds 211 and 223 across different $g$ values, LHE events at identical indices share the same random stream.

The shape comparison was performed as an **event-by-event paired comparison**:
- Particles ordered deterministically by descending $p_T$, then $\eta$, then $\phi$.
- Compared 4-momenta, masses, $p_T$, $\eta$, $\phi$, pair invariant mass, pair $p_T$, $\Delta\phi$, $\Delta\eta$, and $\Delta R$.
- Observed maximum relative differences are within textual LHE precision.
- Kolmogorov-Smirnov (KS) statistics are reported strictly as **secondary descriptive diagnostics** (`ks_pvalue_descriptive_only`).

**Scientific Conclusion**:
> With common random streams, the paired LHE events are identical or compatible within the stored numerical precision. This supports the interpretation that, for the fixed model, mass and topology used here, varying $g$ changes the normalization but does not induce a resolvable parton-level shape change.

---

## 5. Explicit Gate Verification & Full Campaign Authorization

All 48 explicit gates across Gate Groups A through I have passed.

```text
Gate Evaluation Summary:
- Total Gates: 48
- Passed Gates: 48
- Failed Gates: 0

Derived Campaign Status: REDUCED_END_TO_END_VALIDATED
Derived Full Execution Authorization: FULL_EXECUTION_AUTHORIZED
```

Fresh-clone verification (`scripts/verify_r13_reduced_corrected.py --verify-only --strict`) succeeds independently without needing the compiled recast binary or any HEP toolchain.

---

## 6. Limitations & Future Work

- **Statistical Limitations**: Each point comprises $2 \times 1,000 = 2,000$ generated events. Between-run spread is retained as a provisional uncertainty estimator.
- **Full Campaign**: The future $(6g \times 12c\tau \times 2)$ campaign command has been prepared in `FULL_EXECUTION_COMMANDS.md` with strict runtime guards (`--require-mass 150`, `--reject-absolute-card-paths`, `--require-direct-production-table`). The full campaign has **not** been executed during this mission.
