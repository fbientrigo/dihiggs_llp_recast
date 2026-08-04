# R8: first model-derived H2 -> 4b physical DV+jets recast

## Validation status

| Field | Value |
|---|---|
| `recast_validation_status` (primary; one of `NOT_RUN`/`BLOCKED`/`FAILED`/`PROVISIONAL`/`VALIDATED` per `AGENTS.md`) | **`VALIDATED`** |
| `acceptance_status` (explanatory, not a primary state) | `RECAST_ACCEPTANCE_COMPUTED` |
| `exclusion_status` (explanatory, not a primary state) | `NOT_RUN` |
| `highpt_statistics_status` (explanatory, High-pT region only) | `INSUFFICIENT_MC_STATISTICS` |

`recast_validation_status = VALIDATED` means the recast execution itself
(event counts, hashes, cutflow, geometry) passed every declared acceptance
criterion; it is not an exclusion claim and does not assert that every
region has adequate statistics. This is the real, patched upstream DV+jets
analysis (`recast_2301_13866`, frozen upstream commit
`d4047c744062094c9f88e507bb1ccf69e9fe88d6`) run twice on the canonical,
physically-normalized `H2scan_mH150_tb300000` MadGraph sample. Not an
exclusion statement: luminosity was not found in this repository or the
frozen upstream checkout and was not hardcoded from memory (Phase 7).
Machine-readable copy of this table:
`results/r8_h2_model_derived_4b/normalization.json`.

## What this result is, stage by stage

1. **Generated sample**: two independent 1000-event MadGraph 3.5.3 LHE runs
   of `g g > H > h2 h2` at 13 TeV (`fbientrigo/dihiggs_hep_cross` PR #10,
   merge commit `f601e318c57f780d21e8dbee4dcccd7ec1b7b88a`), h2 stable at LHE
   level, PDG `9000006`.
2. **Forced-decay sampling**: the LHE's stable-particle PDG is relabelled
   `9000006 -> 35` by pure text substitution (`scripts/relabel_lhe_pdg.py`;
   momenta/status/mothers/colours/mass/tau/spin verified byte-identical, only
   the IDUP field changes, 2000 changes per run). PDG 35 ("H0") is Pythia's
   own resonance slot and is the only way `ResonanceDecays` can shower a
   custom LLP's `b b~` decay products into real jets; forcing `35 -> b b~`
   with `35:onIfMatch = 5 -5` changes *only how events are sampled*, not the
   physical branching ratio.
3. **Physical BR^2 normalization**: applied once, downstream of acceptance,
   never inside the generation or the recast (see Normalization below).
4. **Acceptance**: computed by the real, unmodified analysis logic
   (`patches/0001-configurable-llp-pdg-ids.patch` only makes the LLP PDG and
   post-init lifetime configurable; it does not touch selection logic).
5. **Visible cross section / expected yield**: visible sigma is reported;
   expected event count is not, because no luminosity source was found.
6. **Exclusion status**: `NOT_RUN` — no observed limit, efficiency map, or
   statistical procedure from the ATLAS analysis was consulted.

## Canonical input

| Quantity | Value |
|---|---|
| Benchmark | `H2scan_mH150_tb300000` |
| m_H2 | 150.0 GeV |
| ctau | 4.32622152973311191 mm |
| Total width | 4.56118529862185007e-14 GeV |
| BR(H2->bb) | 0.756737485808578692 |
| BR(H2->bb)^2 | 0.5726516224278888 |
| sigma(pp->H2H2) | 0.000230291167568 pb (inverse-variance combined, runs compatible) |
| sigma_4b (physical) | 0.131876610738628 fb |

LHE inputs (both independently re-verified: `zcat \| grep -c '</event>'` =
1000 for each; sha256 matches the hep_cross production manifest):

| Run | Path | sha256 |
|---|---|---|
| run_01 | `hep_cross:artifacts/h2_first_physical/madgraph/run_01/unweighted_events.lhe.gz` | `1c580b7a590f9bbfbf213eeef0e54fdcc4b6c1dce3f13bc0ed5278f6f3aec202` |
| run_02 | `hep_cross:artifacts/h2_first_physical/madgraph/run_02/unweighted_events.lhe.gz` | `385faebf45403c224ce374488c3e51a06be56b13ec6b095f92393d0c8f4b1bfa` |

**Not reused from R7**: `results/r7_h2_pair_4b/input/h2pair_m150_1000events.lhe.gz`
(simplified stand-in, `sigma = 0.0304 pb`) and its `param_card.dat`/`run_card.dat`.
R7's cross section never enters this result.

Full provenance, all commits, and all hashes: `results/r8_h2_model_derived_4b/input_manifest.json`.

## Pythia/recast configuration

| Setting | Value | Source |
|---|---|---|
| PDG handoff | LHE-level text relabel `9000006 -> 35`, then `Recast:llpPdgIds = {35}` | R7 mechanism (`cards/r7_h2_pair_4b/ctau_4p326mm.cmnd`), reused unchanged |
| ISR | on | reused from R7's real-recast path |
| FSR | on | reused from R7's real-recast path |
| MPI | off | reused from R7's real-recast path |
| Hadronization | on, `Tune:pp = 21` | reused from R7's real-recast path |
| Lifetime | `35:tau0`/`Recast:llpTau0` = full-precision `4.32622152973311191`, reapplied post-`init()` by the R4/R5 patch (`pythia.particleData.tauCalc(pdg,false); pythia.particleData.tau0(pdg,llpTau0);`) | R8-specific: R7's card used the truncated `4.326` |
| Random seed | independent per run: `81001` (run_01), `81002` (run_02) | R8-specific: R7's card set none at all |
| Jet definition | FastJet `kt_algorithm`, R=0.4, E_scheme, Best strategy, inclusive pT > 20 GeV | `Simpler_ToyDetector.cc::ToyDetector::jetDef` (unmodified) |

This is **not** the standalone `hep_cross` full-Pythia sample's
configuration (`ISR/FSR/MPI = off`), which validates lifetime/decay
bookkeeping only. It is the configuration validated by the real R7 DV+jets
recast path, which is the config a jet-based signal-region acceptance
requires. `PartonLevel:FSR = on` was kept on throughout; no shower setting
was disabled to obtain a passing cutflow.

Pythia 8.308, FastJet 3.4.0, frozen upstream `recastingCodes` commit
`d4047c744062094c9f88e507bb1ccf69e9fe88d6`
(`DisplacedVertices/ATLAS-SUSY-2018-13_GCottin`), patched binary sha256
`f03a5cb6d94d8f3c5513c814f26036d38eddb180b35f91449ff74f83201e1331`.

## Pre-run verification

- Event weights uniform per LHE run (single distinct `XWGTUP` value per
  file: `+2.2986000e-04`, `+2.3054000e-04`), confirming `A x eff = n/allevents`
  is a plain count ratio and `visible_sigma = sigma_4b_fb * A x eff` does not
  double-count the LHE's own cross section.
- Relabel verified: 2000 IDUP fields changed per run, 0 mismatches in any
  other particle-line field.
- Both runs verified post-hoc against the recast log: `All Events:
  1.000000e+03` in both; the printed `Acc`/`Acc [%]` ratios (e.g. Trackless
  run_02 `23` / `2.300000e+00%` = exactly 1000) independently confirm the
  denominator is exactly 1000, not a partial sample.
- `Too many errors!` absent from both logs (no premature termination
  tolerated by `Main:timesAllowErrors = 3` was actually needed to complete
  1000 events).
- run_02 printed one transient `Error in Pythia::next: hadronLevel failed;
  try again` / `Error in StringFragmentation::fragment: stuck in joining`.
  This is Pythia's own internal hadronization retry (the `"; try again"`
  wording is Pythia's, not the recast's `iAbort` path); it did not drop an
  event, per the exact-1000-denominator check above.
- `35: R7_LLP_SETTINGS`/`R8_GEOMETRY_SETTINGS` print `tau0=4.32622` /
  `tau0=4.3262215297331119` respectively (print-precision-limited to 6 and
  16 significant digits by the two drivers' own `cout` formatting); this
  confirms the full-precision canonical value was applied and is distinct
  from R7's `4.32600`, but is not a claim of exact double-precision
  verification from stdout text alone — the card text (committed,
  sha256-tracked) is the traceable input.
- PDG 35's `mWidth` (Pythia's default H0 width) is **not** the physical H2
  width (`4.56118529862185007e-14 GeV`); this does not affect the generated
  lifetime because `tauCalc = off` and tau0 is forced, but it is a real
  divergence between the simulated particle and the physical model point,
  recorded here per Phase 8.

## Run 1 (seed 81001)

| Quantity | Value |
|---|---|
| Processed events | 1000 / 1000 |
| Zero-configured-LLP events | 0 |
| H2 (PDG 35) records | 2000 (2/event) |
| H2 decays (-> b b~) | 2000 / 2000 (100%, forced) |
| b partons | 4000 (4/event) |
| Mean generated tau | 4.338 mm |
| Mean Rxy | 3.413 mm; median 1.915 mm; frac(Rxy>4mm) = 27.5% |
| Mean L3D | 9.759 mm; median 4.843 mm; frac(L3D>4mm) = 55.35% |
| Mean jet multiplicity (pT>20 GeV) | 5.363 |
| Mean leading-jet pT | 148.0 GeV |

Cutflow (`results/r8_h2_model_derived_4b/cutflow_run_01.csv`):

| Stage | High-pT | Trackless |
|---|---:|---:|
| Events processed | 1000 | 1000 |
| Zero configured LLP | 0 | 0 |
| Jet Selection | 2 | 21 |
| Fiducial | 2 | 21 |
| R_vertex > 4mm | 1 | 17 |
| \|d0\| > 2mm track | 1 | 17 |
| Selected decay products >= 5 | 1 | 17 |
| Invariant mass > 10 GeV | 1 | 17 |
| Acc (raw count) | 1 | 17 |
| Acc x Eff (event equivalent) | 1.0149 | 11.87817 |

A x eff (Acc-based): High-pT 0.10%, Trackless 1.70%. A x eff (Acc x Eff-based): High-pT 0.10149%, Trackless 1.187817%.

## Run 2 (seed 81002)

| Quantity | Value |
|---|---|
| Processed events | 1000 / 1000 |
| Zero-configured-LLP events | 0 |
| H2 (PDG 35) records | 2000 (2/event) |
| H2 decays (-> b b~) | 2000 / 2000 (100%, forced) |
| b partons | 4000 (4/event) |
| Mean generated tau | 4.249 mm |
| Mean Rxy | 3.339 mm; median 1.852 mm; frac(Rxy>4mm) = 25.4% |
| Mean L3D | 9.236 mm; median 4.714 mm; frac(L3D>4mm) = 54.4% |
| Mean jet multiplicity (pT>20 GeV) | 5.363 |
| Mean leading-jet pT | 144.9 GeV |

Cutflow (`results/r8_h2_model_derived_4b/cutflow_run_02.csv`):

| Stage | High-pT | Trackless |
|---|---:|---:|
| Events processed | 1000 | 1000 |
| Zero configured LLP | 0 | 0 |
| Jet Selection | 3 | 27 |
| Fiducial | 3 | 27 |
| R_vertex > 4mm | 3 | 23 |
| \|d0\| > 2mm track | 3 | 23 |
| Selected decay products >= 5 | 3 | 23 |
| Invariant mass > 10 GeV | 3 | 23 |
| Acc (raw count) | 3 | 23 |
| Acc x Eff (event equivalent) | 1.958419 | 19.58955 |

A x eff (Acc-based): High-pT 0.30%, Trackless 2.30%. A x eff (Acc x Eff-based): High-pT 0.195842%, Trackless 1.958955%.

## Compatibility (run 1 vs run 2)

Explicit criteria used: two-sample Kolmogorov-Smirnov D statistic against
the asymptotic alpha=0.05 critical value for pre-selection kinematic
distributions; Clopper-Pearson 95% interval overlap for selected counts.

| Distribution | D | critical (alpha=0.05) | compatible |
|---|---:|---:|:---:|
| Rxy (2000 LLPs/run) | 0.0295 | 0.0429 | yes |
| L3D (2000 LLPs/run) | 0.0165 | 0.0429 | yes |
| Leading-jet pT (1000 events/run) | 0.0360 | 0.0607 | yes |

Jet multiplicity: identical mean (5.363) in both runs.

| Region | run_01 Acc [95% CI] | run_02 Acc [95% CI] | CI overlap |
|---|---|---|:---:|
| High-pT | 1/1000 [0.003%, 0.556%] | 3/1000 [0.062%, 0.874%] | yes |
| Trackless | 17/1000 [0.99%, 2.71%] | 23/1000 [1.46%, 3.43%] | yes |

Both runs are statistically compatible on all checked distributions and
regions; counts are combined below. Full detail:
`results/r8_h2_model_derived_4b/kinematic_comparison.json`.

## Combined result (N_total = 2000)

| Region | Acc_total | A x eff (Acc-based) [95% CI] | A x eff (Acc x Eff-based) |
|---|---:|---|---:|
| High-pT | 4 | 0.20% [0.0545%, 0.5113%] | 0.14867% |
| Trackless | 40 | 2.00% [1.4326%, 2.7136%] | 1.573386% |

**High-pT: `INSUFFICIENT_MC_STATISTICS`** (explicit criterion: fewer than 10
selected MC events; 4 observed). Minimum additional events to reach 10
selected at the observed 0.2% acceptance: **3000** (i.e. 5000 total, 3000
more than the 2000 already generated).

**Trackless: `RECAST_ACCEPTANCE_COMPUTED`** (40 selected events, usable).

Full arithmetic: `results/r8_h2_model_derived_4b/cutflow_combined.csv`.

## R7 comparison

R7 central-lifetime (ctau=4.326mm, simplified stand-in LHE) reported
High-pT A x eff = 0.094352%, Trackless A x eff = 1.069558%.

| | R7 (central ctau) | R8 (combined, Acc x Eff-based) | ratio |
|---|---:|---:|---:|
| High-pT A x eff | 0.094352% | 0.14867% | 1.58x |
| Trackless A x eff | 1.069558% | 1.573386% | 1.47x |

R7's own jet-selection efficiency was 0.10% (High-pT) / 2.10% (Trackless) at
all three lifetimes it scanned; R8's per-run jet-selection is 0.2%/2.1%
(run_01) and 0.3%/2.7% (run_02) — both higher, and by a similar factor to
the acceptance ratio above. R7's DV geometry table at ctau=4.326mm
(mean R = 3.4552mm, R>4mm = 27.25%) is close to R8's combined mean Rxy
(3.376mm, R>4mm = 26.45%) — same ctau, same relabel mechanism, same shower
configuration, so the geometry step is not the source of the difference.
**The acceptance difference is attributable to production kinematics
(genuine `gg -> H -> h2h2` MadGraph sample vs R7's simplified stand-in) and
finite MC statistics (4 and 40 selected events respectively), not to
lifetime or selection-logic changes.** This is not forced to agree with R7;
R7's cross section is not, and must not be, used in this comparison or in
any R8 normalization.

## Normalization

sigma_4b_fb = sigma(pp->H2H2)_pb * BR(H2->bb)^2 * 1000 = 0.131876610738628
(BR^2 applied exactly once, downstream of acceptance; never re-applied to
the recast's own selection).

| Region | A x eff (Acc x Eff-based) | visible sigma (fb) |
|---|---:|---:|
| High-pT | 0.14867% | 0.000196 |
| Trackless | 1.573386% | 0.002075 |

K-factor: `null` (no model-specific K-factor source identified).

Luminosity: **not found** in this repository or the frozen upstream
`recastingCodes` checkout (`DisplacedVertices/ATLAS-SUSY-2018-13_GCottin`);
per mission Phase 7, not hardcoded from memory. `expected_signal_events =
null` as a direct consequence.

`results/r8_h2_model_derived_4b/normalization.json` carries this arithmetic
and the exact source string recorded for the missing luminosity.

## Exclusion status

`exclusion_status = **NOT_RUN**`. An exclusion claim requires the analysis's
observed/expected S95, efficiency maps, and statistical procedure, none of
which have been consulted here — only acceptance and visible cross section
were computed.

## Next step

- High-pT: `INSUFFICIENT_MC_STATISTICS` (need >= 3000 additional physical
  MadGraph events at the current production point to reach 10 selected
  events at the observed ~0.2% acceptance).
- Trackless: `RECAST_ACCEPTANCE_COMPUTED`.
- No large MadGraph campaign was started automatically, per Phase 5.
