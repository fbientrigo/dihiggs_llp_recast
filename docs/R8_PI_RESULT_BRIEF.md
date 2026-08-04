# R8 PI-facing result brief: H2 -> 4b displaced-vertex + jets

Status: `recast_validation_status = VALIDATED`, `acceptance_status =
RECAST_ACCEPTANCE_COMPUTED`, `exclusion_status = NOT_RUN`. Full technical
result: `docs/R8_H2_MODEL_DERIVED_4B_RESULT.md`. No numerical value in this
brief was recomputed from a fresh run; all numbers are read from the
already-validated `results/r8_h2_model_derived_4b/` artifacts merged in
PR #6.

## Scientific question

If a long-lived scalar `H2` is pair-produced at the LHC and decays
`H2 -> b b~` at a macroscopic (mm-scale) distance from the interaction
point, is the resulting displaced-vertex + jets signature visible above
zero in a real ATLAS-style DV+jets recast, and at what rate, for one
specific 2HDM-derived benchmark point?

## Benchmark definition

| Quantity | Value |
|---|---|
| Benchmark ID | `H2scan_mH150_tb300000` |
| m(H2) | 150.0 GeV |
| Proper lifetime (ctau) | 4.32622152973311191 mm |
| BR(H2 -> b b~) | 0.7567374858085787 |
| BR(H2 -> b b~)^2 (both H2 forced to b b~) | 0.5726516224278888 |

## Production process

`g g -> H -> h2 h2` at sqrt(s) = 13 TeV, MadGraph 3.5.3, two independent
1000-event LHE samples (`fbientrigo/dihiggs_hep_cross` PR #10). Combined
production cross section sigma(pp -> H2 H2) = 0.000230291167568 pb.

## Lifetime and BR

The full-precision benchmark lifetime (4.32622152973311191 mm) is applied
post-`pythia.init()` in both recast runs, confirmed against each run's
`R7_LLP_SETTINGS`/`R8_GEOMETRY_SETTINGS` log lines. `BR(H2->bb)^2` is
applied exactly once, downstream of acceptance, and never re-applied to the
recast's own event selection.

## Two-run compatibility

Two independent 1000-event runs (seeds 81001, 81002) were processed through
the real recast and compared before combining. Rxy, L3D, and leading-jet-pT
distributions are statistically compatible (two-sample KS test, alpha =
0.05); selected-count 95% confidence intervals overlap in both signal
regions. The two runs were combined only because this compatibility check
passed (N_total = 2000).

## Trackless acceptance

| Quantity | Value |
|---|---|
| Selected events (combined) | 40 / 2000 |
| A x eff (Acc x Eff-based) | 0.01573386 (1.573386%) |
| Status | acceptance computed and validated |

## High-pT statistics limitation

| Quantity | Value |
|---|---|
| Selected events (combined) | 4 / 2000 |
| `highpt_statistics_status` | `INSUFFICIENT_MC_STATISTICS` |

Fewer than 10 selected MC events gives a relative Poisson uncertainty above
~32%, too wide to usefully constrain this region. At the observed ~0.2%
acceptance, roughly 3000 additional physical MadGraph events (5000 total)
would be needed to reach 10 selected events. No such campaign has been run.

## Physical visible cross section

Trackless region, BR^2-normalized: **visible_sigma_fb = 0.0020749281306360694 fb**
(`sigma_4b_fb x A x eff` = 0.131876610738628 fb x 0.01573386).

## Expected selected events at 139 fb^-1

Using the Run-2 integrated luminosity 139 fb^-1 (ATLAS, *JHEP* 06 (2023)
200, [arXiv:2301.13866](https://arxiv.org/abs/2301.13866); HEPData:
[10.17182/hepdata.137762](https://doi.org/10.17182/hepdata.137762)):

```
expected Trackless events = visible_sigma_fb * 139 fb^-1
                           = 0.0020749281306360694 fb * 139 fb^-1
                           = 0.2884 events
```

**Expected Trackless-region selected events at 139 fb^-1 ~ 0.288.**

## Interpretation

This benchmark has a nonzero validated Trackless acceptance, but its
model-derived production rate leads to substantially less than one expected
selected event in the full Run-2 dataset. The High-pT region does not yet
have enough simulated events to report a usable acceptance at all. Neither
observation supports treating this specific benchmark point as visible with
the current dataset.

## What is and is not concluded

**Is concluded:**
- The real, patched ATLAS DV+jets recast (`recast_2301_13866`) runs
  correctly on this model-derived sample: exactly 1000/1000 events per run,
  zero missing-LLP events, no premature termination, statistically
  compatible independent runs.
- The Trackless signal region has a nonzero, MC-statistics-adequate
  acceptance (1.573386%) for this benchmark.
- The physical visible cross section for this benchmark, in this region, is
  ~0.00207 fb, giving ~0.288 expected selected events at 139 fb^-1.

**Is not concluded:**
- No exclusion, discovery sensitivity, or model limit is claimed for this
  or any other benchmark point.
- The High-pT region's acceptance is not reported as usable (insufficient
  MC statistics), not as zero.
- Nothing here constrains any other point in the model's parameter space;
  this is a single benchmark.
