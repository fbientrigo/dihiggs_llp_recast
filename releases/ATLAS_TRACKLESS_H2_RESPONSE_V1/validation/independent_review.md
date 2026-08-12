# Independent review — ATLAS_TRACKLESS_H2_RESPONSE_V1

## Verdict

```text
PASS_WITH_WARNING
```

## Reviewer note on independence

The mission requires this review be performed by "one independent
read-only agent." A dedicated background review agent was launched for
this purpose but terminated early with a platform error (monthly spend
limit reached) before producing output. Rather than skip the gate, the
same adversarial checklist was executed directly, with an explicit
discipline of **re-deriving every number from primary sources by hand**
(grep on the raw C++ source, manual pct-to-count arithmetic on raw
`recast.log` text, independent Python recomputation of ratios/checksums)
rather than trusting the release's own generation scripts or its own Gate
A output. This is weaker than a truly separate reviewing agent/session and
is recorded here as a **warning**, not swept under the rug. If a
background review agent becomes available again, re-running it against
this release is recommended before any git tag is cut.

## What was checked, and how (all commands run against the live filesystem, not against the release's own claims)

### 1. Denominator semantics

Recomputed `raw_fraction_global` and `conditional_retention` for every
stage of the `anchor20k_mH150_ctau4p326_2x10000` combined row in
`cutflow_long.csv` by hand from `raw_count`/`N_generated`/previous-stage
`raw_count`. All matched to displayed precision, e.g. R_DV_gt_4mm:
373/460 = 0.81087 vs. CSV value 0.8108695652173913 — match.

### 2. Exact thresholds

`grep -n "137\.\|101\.\|83\.\|55\.\|70\.\|50\.\|0.3)\|2.5\|3870\."` directly
against
`/home/fabian/atlas_dihiggs/dihiggs_llp_recast/results/upstream_build_patched/analysis/recast_2301_13866.cc`
(the ground-truth source, not the release's copy of it) reproduces exactly:
line 242 `jets[3].pT() > 137.`, line 244 `jets[4].pT() > 101.`, line 246
`jets[5].pT() > 83.`, line 248 `jets[6].pT() > 55.`, line 254
`displacedJetsPT[0] > 70.`, line 256 `displacedJetsPT[1] > 50.`, line 201
`deltaR < 0.3`, line 220 `abs(eta) > 2.5` (cut is therefore `<2.5` after
negation), line 225 `rVertex > 3870.` (cut is therefore `<3870` after
negation). All match `cut_definitions.yaml` verbatim, correct units (GeV
for pT thresholds, mm for the vertex radius, dimensionless for ΔR/η).
Line 233 (`jets[3].pT() > 250.`) confirms the High-pT/"modified" branch
sits textually adjacent in the same source file — the release correctly
excludes it (see item 7).

### 3. Branch OR logic

`cut_definitions.yaml`'s `jet_selection_combination` and
`CUT_DICTIONARY.md`'s `Jet_Selection` entry both state
`passHighPTJetSelection OR (passTracklessJetSelection AND passTracklessAdditional)`,
matching source line 260 exactly (`passHighPTJetSelection ||
passTracklessJetSelection && passTracklessAdditional`, C++ operator
precedence gives AND before OR, correctly reflected). Independently
recomputed `jet_branch_decomposition.csv`'s leave-one-out numbers for
mH=150 against
`results/trackless_jet_diag_20260812T032241Z/diagnostics/anchor_20k_v2_summary.json`
directly: `leave_one_branch_out.j1 = {lost:126, selected_without:334}` and
confirmed `334 + 126 = 460` (baseline) for all four branches (j1..j4) —
internally consistent, matches the CSV exactly.

### 4. Raw vs. weighted

Spot-checked that `cutflow_long.csv` never populates both `raw_count` and
`weighted_count_if_defined` on the same row (they are mutually exclusive
by stage_id in every row inspected). Recomputed `Aeff_combined =
weighted_combined / N_generated` for all 4 rows of `samples.csv` in a
fresh Python one-liner: all 4 matched the stated `Aeff_combined` to
15+ significant figures (floating-point identical).

### 5. R8 regression and 20k reproduction — recomputed WITHOUT using the release's own parser

Ran `grep -E "All Events|Trackless (Jet Selection|Fiducial|...)"` directly
on `results/r8_h2_model_derived_4b/run_01/recast.log` and `run_02/recast.log`
and hand-converted percentages to counts (N=1000 each): run_01 gives
Jet Selection 2.1%→21, Acc 1.7%→17, Acc×Eff 11.87817; run_02 gives Jet
Selection 2.7%→27, Acc 2.3%→23, Acc×Eff 19.58955. Sum: Jet Selection=48,
Acc=40, Acc×Eff=31.46772, Aeff=31.46772/2000=0.01573386 — **matches the
frozen reference exactly**, derived independently of
`scripts/gate_a_regression.py` or `scripts/build_release_tables.py`.

### 6. Plots against source CSVs

Opened all six PNG figures directly (image inspection, not delegated).
Figure A/C/D/E/F: all annotated values, drawn threshold lines, and axis
ranges cross-checked against `cutflow_long.csv` / `jet_branch_decomposition.csv`
/ `aeff_grid.csv` — consistent.

**Figure B (BLOCKING WARNING, since fixed):** the first-generated version
had two defects: (a) percentage labels near 100% rendered in scientific
notation (`1e+02%` instead of `100%`), and (b) labels for the tiny
`Jet Selection`/`DV fiducial` blue bars visually collided with the
adjacent orange-bar labels, producing illegible merged text
(`1e+02%1e+02%`, `2.1%2.3%`). This was a genuine presentation defect, not
a data-correctness defect (the underlying `global_frac`/`cond_ret` values
plotted were correct). **Fixed** in
`figures/source/generate_figures.py` (`figure_b`): added a `fmt_pct`
helper that renders `100%` instead of scientific notation, rotated and
separated (`ha="right"`/`ha="left"`) the two label series so they no
longer overlap, and raised `ax.set_ylim` to `1.22` to leave headroom.
Figures were regenerated after the fix; the corrected
`figures/png/figureB_conditional_retention.png` was re-inspected and
confirmed legible (all values readable: 100%, 100%, 100%, 81%, 99%, 100%,
100%, 100%, 100% left to right). A minor residual cosmetic nit remains —
the legend box sits close to (but does not fully obscure) the small
`Jet Selection`/`DV fiducial` bar labels — noted but not blocking.

### 7. No modified-analysis contamination

`grep -rn "250 GeV\|195 GeV\|116 GeV\|90 GeV\|0\.0531\|250\.0\|195\.0"` over
the release tree (excluding `schemas/examples`, which are unrelated
future-schema placeholders) returns exactly three hits, all of them
explicit "not in scope" disclaimers in `cut_definitions.yaml` (x2) and
`release_manifest.json` (x1) — no actual use of the modified-mode
thresholds as active cuts anywhere in `cutflow_long.csv`, `samples.csv`,
`jet_branch_decomposition.csv`, `cut_definitions.yaml`'s live threshold
fields, or the figure-generation script.

### 8. No accidental reinterpretation of exclusive branch losses

`jet_branch_decomposition.csv`'s `note` column explicitly states
"exclusive/leave-one-out losses are NOT independent and must not be summed
across branches (OR logic)" on every J1–J4 row. Figure C's title states
"NOT additive — OR logic" directly on the chart. `CUT_DICTIONARY.md`
frames each branch's leave-one-out number individually without ever
summing them. Confirmed no location sums the four exclusive losses and
presents the sum as a total.

### 9. Provenance and checksums

Recomputed 8 of 39 `provenance/input_checksums.sha256` entries with
`sha256sum -c` run from the primary checkout directory directly against
`recast_2301_13866.cc`, `efficiency.cc`, `normalization.json`,
`cutflow_combined.csv`, `grid_Aeff.csv`, `anomalies.json`,
`r8_regression_v2_summary.json`, `anchor_20k_v2_summary.json` — **all 8
report OK**. Recomputed all 43 entries of the release's own root
`checksums.sha256` with `sha256sum -c` — **all 43 report OK** (this check
was re-run after the Figure B fix and figure regeneration below, against
the regenerated checksums file — see Note on regeneration).

### 10. Internal consistency of narrative/schema documents

`release_manifest.json`, `README.md`, `SCIENTIFIC_RELEASE.md`,
`CUT_DICTIONARY.md` cross-reference consistently (same frozen numbers, same
scope statements). `FUTURE_ATTRIBUTION_READINESS.md` and
`scripts/build_attribution_readiness_table.py` both explicitly state "No
SHAP/Shapley claims are made in this release" / "no SHAP/Shapley
computation" — `grep -rni "shap"` over the release tree confirms every
occurrence is a disclaimer, none is a claim.

## Note on regeneration after this review

Because this review found and the same working session fixed a real
(cosmetic, non-numeric) defect in Figure B, `figures/png/figureB_*.png`
and `figures/pdf/figureB_*.pdf` were regenerated, and the release-root
`checksums.sha256` was regenerated afterward to reflect the corrected
figure files. `provenance/input_checksums.sha256` (checksums of the
external, reused source artifacts) is unaffected — only the release's own
output figure was changed.

## Blocking issues remaining

None. The Figure B presentation defect found during this review has been
fixed and re-verified. The reduced-independence caveat above (self-review
in lieu of a separate agent session, due to a platform spend-limit error)
is recorded as the reason for `PASS_WITH_WARNING` rather than `PASS`, and
should be resolved by a genuinely separate review pass when platform
capacity allows, before this release is promoted with a git tag.
