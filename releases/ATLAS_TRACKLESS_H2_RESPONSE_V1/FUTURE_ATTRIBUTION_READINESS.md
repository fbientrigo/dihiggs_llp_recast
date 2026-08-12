# Future parameter-attribution readiness (Phase 6 — exploratory, disabled)

## What this release ships

`parameter_attribution_readiness.csv` — one row per validated (mH, ctau)
grid point (36 rows, the same discrete grid as Figure F), reshaped from
`results/aeff_grid_20260811T042218Z/grid_Aeff.csv` and `anomalies.json`
into the column groups a later parameter/mass-attribution study would
consume: input model parameters, production observables, jet-stage
metrics, DV-stage metrics, Aeff, normalization, and validation state.
The `production_normalization_source` column is explicitly marked
`NOT_IN_SCOPE_THIS_TABLE` for every row: production sigma/BR are
model-point-specific (see `r8_h2_model_derived_4b/input_manifest.json` for
the one point in this release where that chain is fully recorded) and are
not reconstructable from a factorized detector-response grid. This is a
**table only** — no model is fit to it in this release.

## What this release explicitly does NOT ship

**No SHAP/Shapley claims are made in this release.** No surrogate model is
trained, fit, or scaffolded here. If a future release adds a
surrogate-attribution module, that module must ship **disabled by default**
and documented as exploratory, exactly as this section anticipates but does
not build.

## Causal ablation vs. surrogate attribution — do not conflate these

This release already contains one legitimate causal-attribution result:
the **leave-one-branch-out exclusive loss** in `jet_branch_decomposition.csv`
and Figure C. Removing branch J1 (or J2/J3/J4) from the `ordinary_jet_OR`
combination and re-evaluating the exact same recast logic on the exact same
events is a **causal intervention within the recast** — it answers "what
would this analysis have selected if branch X were absent," exactly,
because the recast logic is deterministic and fully known. That result is
already computed, reviewed, and safe to use as-is.

A future SHAP/Shapley-style attribution over, say, physical model
parameters (mH, couplings, ctau) driving Aeff would be fundamentally
different: it would fit a **surrogate model** to the discrete grid and
attribute variance to input features *of that surrogate*, not of the
recast itself. That is a statement about the surrogate's learned response
surface, not a causal statement about the ATLAS selection. The two must
never be presented as equivalent evidence:

| | exact cut ablation (this release, Figure C) | future SHAP/Shapley (not in this release) |
|---|---|---|
| What varies | one boolean branch in the actual recast logic | input features of a fitted surrogate model |
| Evidence type | causal, exact, deterministic | surrogate/model attribution, approximate |
| Requires | nothing beyond the existing recast + diagnostic instrumentation | a trained model, a chosen feature set, a fit quality check |
| Status in this release | computed, reviewed, PASS | out of scope, not implemented, not claimed |

## Scope statement

This document and `parameter_attribution_readiness.csv` are scaffolding
for a **later** task. No attribution, importance ranking, or causal claim
about mH/ctau/coupling dependence beyond what is directly and exactly
computed in `jet_branch_decomposition.csv` (leave-one-out) and Figure E
(direct mass-dependence readout, not attribution) is made anywhere in this
release.
