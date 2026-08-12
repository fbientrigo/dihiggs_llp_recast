# ATLAS_TRACKLESS_H2_RESPONSE_V1

Publication-quality scientific release of the published/original ATLAS
DV+jets Trackless analysis (arXiv:2301.13866) response to the H2H2 (LLP)
signal, and a mass-ready receiver schema for future higher-mass samples.

**This release does not modify the ATLAS selection.** See
`SCIENTIFIC_RELEASE.md` for the full narrative.

## Start here

- `SCIENTIFIC_RELEASE.md` — the scientific narrative and answers to the
  mission's ten required questions.
- `CUT_DICTIONARY.md` — every cut, its exact requirement, units, entering/
  surviving counts, conditional efficiency, and evidence source.
- `cut_definitions.yaml` — machine-readable cut contract (single source of
  truth for every threshold; no threshold exists only in prose).
- `cutflow_long.csv` — canonical long-format cutflow dataset (all four
  canonical samples x all stages x per-seed and combined).
- `jet_branch_decomposition.csv` — leave-one-out exclusive losses and
  branch-overlap patterns for J1-J4.
- `samples.csv` — one row per canonical sample with final Aeff.
- `aeff_grid.csv` — the validated 3x12 Aeff(mH,ctau) grid (Figure F source).
- `parameter_attribution_readiness.csv` — Phase 6 scaffolding table (no
  attribution computed; see `FUTURE_ATTRIBUTION_READINESS.md`).
- `figures/{pdf,png}/` — Figures A-F; `figures/source/` — the exact
  generating script.
- `validation/` — Gate A regression results (`PASS`) and (after Phase 8)
  the independent adversarial review.
- `provenance/` — git state, environment, exact command chain, and
  checksums of every source artifact this release reused.
- `schemas/` — mass-ready input manifest schema for future H2 samples,
  with validated example instances.
- `release_manifest.json` — machine-readable release summary.
- `checksums.sha256` — sha256 of every file in this release package.

## Reproducing this release

```bash
bash provenance/commands.sh
```

This reads only from the primary checkout's existing, already-reviewed
`results/` campaign artifacts (paths recorded in
`provenance/input_checksums.sha256`); it does not rerun any Pythia/recast
simulation.

## Scope boundary

Out of scope for this release (see `release_manifest.json` ->
`not_in_scope` and `SCIENTIFIC_RELEASE.md`): threshold optimization, new
broad simulation, the "modified" analysis-mode branch, the High-pT
analysis region, and any SHAP/Shapley or surrogate-model attribution
claim.
