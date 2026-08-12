# Cut Dictionary — ATLAS DV+jets Trackless (published/original selection)

Canonical reference sample for entering/surviving/conditional-efficiency
numbers below: `anchor20k_mH150_ctau4p326_2x10000` (mH2 = 150 GeV,
ctau = 4.326221529733112 mm, N_generated = 20000, seeds 81001+81002
combined), the highest-statistics canonical sample in this release. The
frozen `r8_frozen_mH150_ctau4p326_2x1000` sample (N=2000) is the
authoritative regression fixture and is quoted alongside as a cross-check;
its raw counts are consistent (same conditional efficiencies within MC
statistics). All numbers below are read directly from `cutflow_long.csv`
and `jet_branch_decomposition.csv` in this release — see each entry's
"Evidence source" line for the exact row.

Global note on cut motivation: this release's evidence base is the
`recastingCodes` implementation source (`recast_2301_13866.cc`,
`Simpler_ToyDetector.cc`, `efficiency.cc`, upstream commit
`d4047c744062094c9f88e507bb1ccf69e9fe88d6`) and its accompanying README
(arXiv:2301.13866, arXiv:2404.06126), **not** the ATLAS paper text itself.
Where a cut's physics motivation is not stated in the code, comments, or
README available in this repository, this dictionary says so explicitly
rather than inferring a rationale — per the mission rule "never infer an
experimental motivation not supported by the source."

---

## J1 — fourth-leading jet pT

1. **Requirement**: pT(jet rank 4) > 137 GeV
2. **Object**: fourth-leading reconstructed jet (0-indexed rank 3), sorted descending by smeared pT
3. **Units**: GeV
4. **Cumulative?**: No — independent branch, evaluated on all generated events
5. **Motivation**: not stated in available source; presumed to reflect an ATLAS-SUSY-2018-13 Trackless signal-region jet-multiplicity/pT requirement (arXiv:2301.13866), not independently confirmed from ATLAS paper text in this repository
6. **Events entering**: 20000
7. **Events surviving (raw branch population, not cumulative)**: 260
8. **"Conditional efficiency" (raw population / N_generated, since not cumulative)**: 1.3%
9. **Major/minor loss for H2**: dominant branch — largest single-branch population and largest leave-one-out exclusive loss (126 events, 27.4% of the 460-event ordinary_jet_OR baseline) among J1–J4; a **major** contributor
10. **Evidence source**: `jet_branch_decomposition.csv` row (sample_id=anchor20k_mH150_ctau4p326_2x10000, branch=J1); source code `recast_2301_13866.cc` (`detector.jets[3].pT() > 137.`)

## J2 — fifth-leading jet pT

1. **Requirement**: pT(jet rank 5) > 101 GeV
2. **Object**: fifth-leading jet (rank 4)
3. **Units**: GeV
4. **Cumulative?**: No
5. **Motivation**: not stated in available source (see global note)
6. **Events entering**: 20000
7. **Events surviving (raw branch population)**: 217
8. **Conditional efficiency (raw/N_generated)**: 1.085%
9. **Major/minor loss for H2**: secondary contributor — leave-one-out exclusive loss 60 events (13.0% of baseline); **moderate**
10. **Evidence source**: `jet_branch_decomposition.csv` (branch=J2); `recast_2301_13866.cc` (`detector.jets[4].pT() > 101.`)

## J3 — sixth-leading jet pT

1. **Requirement**: pT(jet rank 6) > 83 GeV
2. **Object**: sixth-leading jet (rank 5)
3. **Units**: GeV
4. **Cumulative?**: No
5. **Motivation**: not stated in available source (see global note)
6. **Events entering**: 20000
7. **Events surviving (raw branch population)**: 94
8. **Conditional efficiency (raw/N_generated)**: 0.47%
9. **Major/minor loss for H2**: smallest branch — leave-one-out exclusive loss only 5 events (1.1% of baseline); **minor**, provides almost no exclusive coverage
10. **Evidence source**: `jet_branch_decomposition.csv` (branch=J3); `recast_2301_13866.cc` (`detector.jets[5].pT() > 83.`)

## J4 — seventh-leading jet pT

1. **Requirement**: pT(jet rank 7) > 55 GeV
2. **Object**: seventh-leading jet (rank 6)
3. **Units**: GeV
4. **Cumulative?**: No
5. **Motivation**: not stated in available source (see global note)
6. **Events entering**: 20000
7. **Events surviving (raw branch population)**: 181
8. **Conditional efficiency (raw/N_generated)**: 0.905%
9. **Major/minor loss for H2**: second-largest exclusive coverage — leave-one-out exclusive loss 93 events (20.2% of baseline); a **major** contributor together with J1
10. **Evidence source**: `jet_branch_decomposition.csv` (branch=J4); `recast_2301_13866.cc` (`detector.jets[6].pT() > 55.`)

## ordinary_jet_OR — J1 OR J2 OR J3 OR J4

1. **Requirement**: at least one of J1, J2, J3, J4 passes
2. **Object**: event-level OR of the four branches above
3. **Units**: n/a (boolean combination)
4. **Cumulative?**: Yes, relative to `generated` (first real event-level filter in this cutflow)
5. **Motivation**: not stated in available source; the OR structure across jet multiplicities is presumed to broaden acceptance across differing hard-jet topologies, not independently confirmed
6. **Events entering**: 20000
7. **Events surviving**: 460
8. **Conditional efficiency**: 2.3%
9. **Major/minor loss for H2**: **the single dominant loss in the entire cutflow** — removes 97.7% of all generated events; every downstream stage operates on this residual 2.3%
10. **Evidence source**: `cutflow_long.csv` (sample_id=anchor20k_mH150_ctau4p326_2x10000, seed=combined, stage_id=ordinary_jet_OR)

## displaced_jet_addendum — leading/second matched-displaced-jet pT requirement

1. **Requirement**: (leading matched displaced jet pT > 70 GeV) OR (second-leading matched displaced jet pT > 50 GeV), applied on top of ordinary_jet_OR
2. **Object**: matched displaced jets (charged final LLP daughters matched to jets, ΔR<0.3, then |eta(jet)|<2.5 and R_vertex(matching)<3870mm)
3. **Units**: GeV (thresholds), mm (matching radius), dimensionless (ΔR, |eta|)
4. **Cumulative?**: Yes, relative to ordinary_jet_OR
5. **Motivation**: not stated in available source; presumed to require displaced-jet compatibility with the Trackless DV signature, not independently confirmed
6. **Events entering**: 460
7. **Events surviving**: 460
8. **Conditional efficiency**: 100% (0 events lost at this stage in all four canonical samples in this release — R8 N=2000 and all three N=20000 endpoint/anchor controls)
9. **Major/minor loss for H2**: **negligible** — every event in this release's ordinary_jet_OR sample already satisfies the displaced addendum; matching/displaced-pT failure was independently checked and found to be exactly zero (see `matching_categories_within_kinematic_union` in the diagnostic summaries)
10. **Evidence source**: `cutflow_long.csv` (stage_id=displaced_jet_addendum); diagnostics `anchor_20k_v2_summary.json.matching_categories_within_kinematic_union` (no_match=0, matched_outside=0, displaced_pt_fail=0)

## Jet_Selection — published Trackless Jet Selection (ordinary_jet_OR AND displaced_jet_addendum)

1. **Requirement**: ordinary_jet_OR AND displaced_jet_addendum
2. **Object**: event-level combination of the two stages above
3. **Units**: n/a
4. **Cumulative?**: Yes
5. **Motivation**: this is the literal definition of the published ATLAS Trackless Jet Selection region as implemented in `recast_2301_13866.cc`
6. **Events entering**: 20000
7. **Events surviving**: 460
8. **Conditional efficiency (relative to generated)**: 2.3%; (relative to displaced_jet_addendum): 100%
9. **Major/minor loss for H2**: identical population to ordinary_jet_OR in this release (the addendum removes nothing here) — this stage **is** the dominant bottleneck of the full analysis
10. **Evidence source**: `cutflow_long.csv` (stage_id=Jet_Selection); cross-checked against `results/trackless_jet_diag_20260812T032241Z/anchor_20k_v2/seed_*/recast.log` ("Trackless Jet Selection [%]")

## DV_fiducial — displaced-vertex fiducial volume

1. **Requirement**: transverse decay radius R_vertex < 300 mm AND |z_vertex| < 300 mm
2. **Object**: reconstructed LLP decay vertex (per mother, evaluated in the per-vertex loop)
3. **Units**: mm
4. **Cumulative?**: Yes, relative to Jet_Selection
5. **Motivation**: not stated in available source; presumed to define the ATLAS inner-detector Trackless fiducial region, not independently confirmed
6. **Events entering**: 460
7. **Events surviving**: 460
8. **Conditional efficiency**: 100%
9. **Major/minor loss for H2**: **negligible** — at ctau=4.326mm essentially all LLP decays occur well within a 300mm fiducial box, so this cut removes 0 events in every canonical sample in this release
10. **Evidence source**: `cutflow_long.csv` (stage_id=DV_fiducial); `recast_2301_13866.cc` (`rVertex < 300. && abs(zVertex) < 300.`)

## R_DV_gt_4mm — displaced-vertex minimum transverse distance

1. **Requirement**: R_vertex > 4 mm
2. **Object**: same reconstructed decay vertex as DV_fiducial
3. **Units**: mm
4. **Cumulative?**: Yes, relative to DV_fiducial
5. **Motivation**: not stated in available source; presumed to enforce the "displaced" (non-prompt) character required by the Trackless analysis, not independently confirmed
6. **Events entering**: 460
7. **Events surviving**: 373
8. **Conditional efficiency**: 81.1%
9. **Major/minor loss for H2**: **minor but the largest single DV-stage loss** — removes 18.9% of Jet-Selection survivors (87 events out of 460), the only DV-stage cut with a non-trivial conditional loss at this lifetime
10. **Evidence source**: `cutflow_long.csv` (stage_id=R_DV_gt_4mm); `recast_2301_13866.cc` (`rVertex > 4.`)

## d0_gt_2mm — track transverse impact parameter

1. **Requirement**: at least one daughter track with |transverse impact parameter| > 2 mm (impactedCount >= 1)
2. **Object**: charged, final-state decay-vertex daughter tracks
3. **Units**: mm
4. **Cumulative?**: Yes, relative to R_DV_gt_4mm
5. **Motivation**: not stated in available source; presumed to enforce "trackless"/displaced-track topology (this cut's name is the origin of the analysis-region label "Trackless"), not independently confirmed
6. **Events entering**: 373
7. **Events surviving**: 371
8. **Conditional efficiency**: 99.5%
9. **Major/minor loss for H2**: **negligible** (2 events lost)
10. **Evidence source**: `cutflow_long.csv` (stage_id=d0_gt_2mm); `recast_2301_13866.cc` (`abs(transverseImpactParameter) > 2.` -> `impactedCount`)

## tracks_ge_5 — selected decay-product multiplicity

1. **Requirement**: at least 5 selected daughter tracks (selectedCount >= 5), where a track is "selected" if its transverse decay-length proxy beta·gamma·tau > 520 mm AND pT/|charge| > 1 GeV
2. **Object**: charged, final-state decay-vertex daughter tracks passing the selection sub-cuts
3. **Units**: count (multiplicity); sub-cuts in mm (520) and GeV (1)
4. **Cumulative?**: Yes, relative to d0_gt_2mm
5. **Motivation**: not stated in available source; presumed to require sufficient track multiplicity for DV reconstruction, not independently confirmed
6. **Events entering**: 371
7. **Events surviving**: 371
8. **Conditional efficiency**: 100%
9. **Major/minor loss for H2**: **negligible** (0 events lost in this sample)
10. **Evidence source**: `cutflow_long.csv` (stage_id=tracks_ge_5); `recast_2301_13866.cc` (`selectedCount >= 5`)

## mDV_gt_10GeV — displaced-vertex invariant mass

1. **Requirement**: invariant mass of selected decay products (pion-mass hypothesis, `mCalc()`) > 10 GeV
2. **Object**: summed 4-momentum of selected daughter tracks at the decay vertex
3. **Units**: GeV
4. **Cumulative?**: Yes, relative to tracks_ge_5
5. **Motivation**: not stated in available source; presumed to reject low-mass combinatoric/background-like vertices, not independently confirmed
6. **Events entering**: 371
7. **Events surviving**: 370
8. **Conditional efficiency**: 99.7%
9. **Major/minor loss for H2**: **negligible** (1 event lost)
10. **Evidence source**: `cutflow_long.csv` (stage_id=mDV_gt_10GeV); `recast_2301_13866.cc` (`totalMomentumAssumingPion.mCalc() > 10.`)

## final_raw / Acc

1. **Requirement**: event passes all of the above (identical to mDV_gt_10GeV; this is the terminal raw-acceptance count)
2. **Object**: event
3. **Units**: count
4. **Cumulative?**: Yes (= mDV_gt_10GeV by construction)
5. **Motivation**: n/a — bookkeeping stage, not an independent cut
6. **Events entering**: 371
7. **Events surviving**: 370
8. **Conditional efficiency**: 99.7% (identical to mDV_gt_10GeV)
9. **Major/minor loss for H2**: n/a (duplicate of mDV_gt_10GeV by construction)
10. **Evidence source**: `cutflow_long.csv` (stage_id=final_raw); `results/r8_h2_model_derived_4b/cutflow_combined.csv` (`acc`)

## efficiency_weighted / Acc x Eff

1. **Requirement**: not a selection cut — per selected event, apply the digitized ATLAS vertex-reconstruction efficiency map `vertexEff(rVertex, massDV, nTrack)` to each fully-selected vertex and sum `vEff = 1 - prod(1 - vertexEff(...))` over selected events
2. **Object**: selected event's fully-reconstructed vertex population
3. **Units**: dimensionless (efficiency), summed as an event-weighted count
4. **Cumulative?**: n/a (multiplicative weight applied to the final_raw-selected sample, not an additional binary cut)
5. **Motivation**: applies the ATLAS-published DV reconstruction efficiency (see `efficiency_map_source` in `cut_definitions.yaml`) to convert raw acceptance into the physically meaningful Acc x Eff quantity used for the Trackless_Aeff response
6. **Events entering**: 370 (final_raw-selected events)
7. **Weighted sum surviving**: 267.5069
8. **"Conditional efficiency" (weighted/raw, i.e. the average per-event vertex-reconstruction efficiency)**: 72.3%
9. **Major/minor loss for H2**: **moderate** — the vertex-reconstruction efficiency reduces the raw-selected sample by ~28% on average at this mass/lifetime; this is a detector-response effect, not an analysis-selection loss
10. **Evidence source**: `cutflow_long.csv` (stage_id=efficiency_weighted, weighted_count_if_defined); `efficiency.cc` (`vertexEff`); `results/r8_h2_model_derived_4b/normalization.json` (Trackless `a_eff_acc_x_eff`)

---

## Cross-check: frozen R8 (N=2000, mH=150, same ctau)

| stage | raw | conditional efficiency |
|---|---:|---:|
| generated | 2000 | — |
| ordinary_jet_OR / Jet_Selection | 48 | 2.4% |
| DV_fiducial | 48 | 100% |
| R_DV_gt_4mm | 40 | 83.3% |
| d0_gt_2mm / tracks_ge_5 / mDV_gt_10GeV / final_raw | 40 | 100% each |
| efficiency_weighted | 31.46772 | 78.7% of final_raw |

Consistent within MC statistics with the N=20000 anchor sample above
(2.3% vs 2.4% Jet Selection, 81.1% vs 83.3% R_DV_gt_4mm conditional
efficiency). Source: `cutflow_long.csv`
(sample_id=r8_frozen_mH150_ctau4p326_2x1000, seed=combined).
