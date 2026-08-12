# ATLAS_TRACKLESS_H2_RESPONSE_V1 — Scientific Release

## Scientific question

> What would the published ATLAS DV+jets Trackless analysis (arXiv:2301.13866,
> ATLAS-SUSY-2018-13) have done to the H2H2 signal?

This release answers that question exactly as implemented in the frozen,
unmodified `recastingCodes` upstream (commit `d4047c744062094c9f88e507bb1ccf69e9fe88d6`).
**No ATLAS threshold is changed anywhere in this release.** A separate
future task is required to study modified selections.

## What was and was not done

- **Reused, not rerun**: every number in this release traces back to
  already-existing, already-independently-reviewed campaign artifacts —
  the frozen R8 result (`results/r8_h2_model_derived_4b`, git-tracked),
  the trackless-jet diagnostic campaign (`results/trackless_jet_diag_20260812T032241Z`,
  independent review verdict `PASS`), and the validated 3x12
  Aeff(mH,ctau) grid (`results/aeff_grid_20260811T042218Z`, independent
  review verdict `PASS_WITH_WARNING`, warning already resolved/flagged in
  that campaign's own review). No Pythia/recast simulation was run to
  produce this release.
- **Built here**: the machine-readable cut contract (`cut_definitions.yaml`),
  the canonical long-format cutflow (`cutflow_long.csv`), the jet-branch
  decomposition table, six publication figures, the cut dictionary, the
  mass-ready input schema, and the parameter-attribution-readiness
  scaffold — all generated programmatically from the source artifacts
  above (`provenance/commands.sh` is the exact command chain).

## Distinguishing the release's conceptual layers

| Layer | This release |
|---|---|
| `published_analysis_definition` | `cut_definitions.yaml` — the literal J1-J4/displaced-addendum/DV-cutflow thresholds as implemented in `recast_2301_13866.cc`, original/published mode only |
| `signal_definition` | H2 pair production, H2->bb forced (conditional acceptance measurement; physical BR^2 applied downstream exactly once — see `results/r8_h2_model_derived_4b/normalization.json`) |
| `production_sample` | MadGraph `g g > H > h2 h2` LHE samples, per-sample provenance in `samples.csv` / `provenance/input_checksums.sha256` |
| `decay_ownership` | H2->bb forced at generation (`decay_sampling_mode=forced_bb` in the future-schema sense; see `schemas/README.md`) |
| `lifetime_definition` | `ctau_mm` = 4.326221529733112 mm for all four canonical samples in this release (a detector-response lifetime; see Phase 5 schema for the response/physical distinction going forward) |
| `raw_acceptance` | `cutflow_long.csv` stage `final_raw` / `samples.csv` `final_raw_combined` |
| `efficiency_weighting` | `cutflow_long.csv` stage `efficiency_weighted`, via the digitized ATLAS `vertexEff()` map |
| `A_times_efficiency` | `samples.csv` `Aeff_combined`; full 2D response in `aeff_grid.csv` / Figure F |

## Gate A — exact regression

**Verdict: PASS.** `validation/gate_a_result.json` (built by
`scripts/gate_a_regression.py`) confirms this release's own generated
tables reproduce, bit-for-bit within floating point tolerance, all four
frozen reference values:

| sample | N | final raw | weighted Acc x Eff | Aeff |
|---|---:|---:|---:|---:|
| R8 frozen (mH=150) | 2000 | 40 | 31.46772 | 0.01573386 |
| anchor 20k (mH=150) | 20000 | 370 | 267.5069 | 0.013375345 |
| endpoint 20k (mH=130) | 20000 | 300 | 224.6426 | 0.01123213 |
| endpoint 20k (mH=170) | 20000 | 439 | 318.6092 | 0.01593046 |

## Where H2 events are lost (Figures A-C, CUT_DICTIONARY.md)

Using the highest-statistics canonical sample (mH=150 GeV, N=20000):

```
Generated                 20000  (100%)
Jet Selection                460  (2.3%)      <-- dominant loss, 97.7% of events removed here
DV fiducial                  460  (2.3%)      <-- 0 additional loss
R_DV > 4mm                   373  (1.865%)    <-- minor loss, 18.9% conditional
|d0| > 2mm                   371  (1.855%)    <-- negligible
tracks >= 5                  371  (1.855%)    <-- negligible
mDV > 10 GeV                 370  (1.85%)     <-- negligible
Final raw (Acc)               370  (1.85%)
A x eff (weighted)          267.5  (1.34%)    <-- detector-response weighting, not a selection cut
```

**Jet Selection is the dominant bottleneck** because it is the first cut
applied and because the published Trackless jet-pT thresholds (137/101/83/55
GeV on jet ranks 4-7) are high relative to the ranked-jet-pT distribution
this signal actually populates (Figure D) — H2H2 -> 4b production simply
does not generate many events with a fourth jet above 137 GeV or a seventh
jet above 55 GeV at these masses. Every downstream DV-stage cut, by
contrast, removes a small single-digit-percent fraction of the already
Jet-Selection-surviving sample; the DV fiducial cut removes essentially
nothing at ctau=4.326mm because that lifetime places nearly all decays well
inside the 300mm fiducial box by construction.

## Exclusive jet-branch coverage (Figure C, jet_branch_decomposition.csv)

Leave-one-branch-out exclusive losses (out of the 460-event
`ordinary_jet_OR` baseline at mH=150) are **not additive** (OR logic) but
rank the branches' individual importance:

| branch | raw population | exclusive loss if removed | fraction of baseline |
|---|---:|---:|---:|
| J1 (pT(j4)>137 GeV) | 260 | 126 | 27.4% |
| J4 (pT(j7)>55 GeV) | 181 | 93 | 20.2% |
| J2 (pT(j5)>101 GeV) | 217 | 60 | 13.0% |
| J3 (pT(j6)>83 GeV) | 94 | 5 | 1.1% |

**J1 and J4 dominate exclusive coverage**; J3 provides almost no
independent coverage — most events that satisfy J3 also satisfy at least
one other branch. This pattern is consistent (same rank ordering, same
approximate magnitudes) across all three masses in this release (see
`jet_branch_decomposition.csv`).

## Mass dependence at fixed lifetime (Figure E)

At the shared ctau=4.326221529733112mm benchmark:

| mH2 [GeV] | Jet Selection | Final raw | A x eff |
|---:|---:|---:|---:|
| 130 | 357 | 300 | 224.6426 |
| 150 | 460 | 370 | 267.5069 |
| 170 | 558 | 439 | 318.6092 |

The mass dependence is monotonically increasing and is **driven by the
jet stage**: heavier H2 produces harder b-jets, populating the high-pT
tail probed by J1-J4 more efficiently (Figure D shows the ECDF shifting
right with mass). Downstream DV-stage conditional efficiencies are flat
across mass (see `cutflow_long.csv`), confirming the mass dependence
originates upstream of the DV cutflow, not from vertex reconstruction or
detector-response effects.

## Detector response vs. physical-model normalization

`Aeff` in this release (`samples.csv`, `aeff_grid.csv`, Figure F) is a
**detector-response/analysis-acceptance quantity only** — it does not
include the physical H2->bb branching ratio, production cross section, or
luminosity. The full 3x12 grid (`aeff_grid.csv`) is a **factorized
detector-response scan**: ctau is varied as a response-lifetime parameter,
independent of any specific physical coupling's predicted width (see
`schemas/README.md` for the `ctau_response_mm` vs `ctau_physical_mm`
distinction this release formalizes for future samples). Physical
normalization (sigma, BR^2) is applied downstream and is recorded, for the
one point where the full production chain is available in this release,
in `results/r8_h2_model_derived_4b/normalization.json` (visible sigma =
0.00207 fb at mH=150, BR_bb^2 = 0.5727).

## Conditional-on-forced-bb quantities

Every acceptance/efficiency number in this release
(`raw_acceptance`, `efficiency_weighted`, `Aeff`) is conditional on the
generation-level forced H2->bb decay used in all four canonical samples.
The physical branching factor `BR_bb^2` must be applied exactly once,
downstream of this release's numbers — never folded into `Aeff` itself
(see `docs/CANONICAL_TRACKLESS_STATUS_20260807.md`, "operational rule").

## Frozen / validated status

- **Frozen and Gate-A-verified in this release**: R8 (mH=150, N=2000);
  anchor 20k (mH=150); endpoint 20k (mH=130, mH=170); the 3x12
  Aeff(mH,ctau) grid (with the ctau=0.3mm nodes flagged low-statistics,
  not used for strong significance claims).
- **Not validated / not in scope**: any mass beyond 130-170 GeV, any ctau
  outside the 0.3-1000mm grid, the "modified" analysis-mode branch, the
  High-pT analysis region.

## Repository readiness for higher-mass samples

The mass-ready input manifest schema (`schemas/h2_response_input_manifest.v1.schema.json`)
and its two validated example instances (`schemas/examples/`) define the
receiver contract for future H2 samples at any mass, with
`ctau_response_mm` and `ctau_physical_mm` as mandatory, never-conflated
separate fields, and explicit support for `FACTORIZED_G_ONLY` and
`PHYSICAL_DECAYS_NO_HEAVY_CASCADES` production-model variants. No new
physics or analysis behavior is implemented for either variant in this
release — this is scaffolding only. See `FUTURE_ATTRIBUTION_READINESS.md`
for the (also scaffolding-only, disabled) parameter-attribution readiness
statement.
