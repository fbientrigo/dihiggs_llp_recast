# Canonical Trackless status — 2026-08-07

## Verdict

```text
EFFICIENCY_CLOSURE_RESOLVED_R8_AUTHORITATIVE
```

Scope of this verdict:

> canonical ATLAS DV+jets Trackless response under the frozen public/original analysis selection with the minimal scalar-PDG/lifetime adaptation.

## Canonical benchmark

```text
m_H2 = 150 GeV
ctau = 4.326221529733112 mm
g_hH2H2 = 63.59142520075966 GeV
BR(H2 -> bb) = 0.7567374858085787
PDG(H2) = 35
LesHouches:setLifetime = 2
```

The recast sample forces `H2 -> bb` in order to measure the conditional acceptance/efficiency. The physical pair branching factor is applied downstream as `BR_bb^2` exactly once.

## Canonical R8 Trackless result

Two independent 1000-event runs:

| Quantity | Combined value |
|---|---:|
| generated events | 2000 |
| raw Trackless selected events | 40 |
| raw Trackless acceptance | 0.020000 |
| weighted Trackless `Acc x Eff` numerator | 31.46772 |
| canonical `Trackless_Aeff` | **0.01573386** |

Definition:

```text
Trackless_Aeff = weighted Trackless (Acc x Eff) / N_generated
               = 31.46772 / 2000
               = 0.01573386
```

Do not substitute raw acceptance `40/2000 = 0.020000` for the weighted efficiency.

## Recast provenance

```text
frozen upstream commit:
  d4047c744062094c9f88e507bb1ccf69e9fe88d6

R8 patched recast executable SHA256:
  f03a5cb6d94d8f3c5513c814f26036d38eddb180b35f91449ff74f83201e1331

Pythia:
  8.308

FastJet:
  3.4.0
```

The R8 patch only makes LLP PDG IDs and lifetime configurable. It does not intentionally change the published analysis thresholds, efficiency maps, geometry or jet definitions.

## Why the later ~0.0531 result does not replace R8

The larger response was obtained with a different executable/analysis path using `modified` mode.

That mode is not merely "the same Trackless analysis with scalar lifetime support". Relative to the original/published Trackless implementation, it changes the analysis definition, including:

- Trackless jet thresholds;
- the additional displaced-jet requirement;
- the efficiency application convention.

Therefore

```text
~0.0531 = MODIFIED_ANALYSIS_TRACKLESS_RESPONSE
```

and must not be promoted as the canonical absolute ATLAS Trackless efficiency.

The first decisive divergence occurs at the analysis-mode selection itself, before interpreting later cutflow differences.

## Lifetime is not the discrepancy source

Both the canonical R8 setup and the corrected later setup use the intended scalar identity/lifetime configuration. R8 already had:

```text
Recast:llpPdgIds = {35}
Recast:llpTau0 = 4.326221529733112 mm
LesHouches:setLifetime = 2
```

R8 runtime diagnostics found zero events with missing configured LLPs and generated lifetime/geometry distributions consistent with the requested mm-scale lifetime.

## R8 cutflow summary

### run 01 — 1000 events

```text
Jet Selection                         21
Fiducial                              21
R > 4 mm                              17
|d0| > 2 mm                           17
selected decay products >= 5          17
mDV > 10 GeV                          17
raw Acc                               17
weighted Acc x Eff                    11.87817
```

### run 02 — 1000 events

```text
Jet Selection                         27
Fiducial                              27
R > 4 mm                              23
|d0| > 2 mm                           23
selected decay products >= 5          23
mDV > 10 GeV                          23
raw Acc                               23
weighted Acc x Eff                    19.58955
```

Combined weighted numerator: `31.46772`.

## R10 lifetime table status

The frozen R10 Trackless curve is the current response source for the original/published analysis at `m_H2 = 150 GeV`.

At the benchmark lifetime it reproduces:

```text
ctau_mm = 4.326221529733112
generated = 2000
selected_trackless_events = 40
Trackless_Aeff = 0.01573386
```

The historical R10 field called `Trackless_Aeff_stat_uncertainty` used a provisional `Aeff/sqrt(N_selected)` prescription. That is not a validated uncertainty treatment for weighted `Acc x Eff` and must not be presented as a detector systematic.

A useful descriptive between-run diagnostic at the benchmark is the half-spread of the two weighted efficiencies, about `0.00385569`, but it is likewise not a detector systematic.

## Operational rule

For current physical-point studies:

```text
production normalization   -> MadGraph / dihiggs_hep_cross
BR and lifetime            -> canonical model point / dihiggs
Trackless Aeff(ctau)        -> original/published R8/R10 response here
visible signal              -> downstream Boundary layer
```

Do not modify the recast simply because the production cross section changes. Run new recast points only when the event kinematics or acceptance question genuinely changes.

## Optional regression smoke

A one-input, one-seed `original` versus `modified` smoke remains useful as a permanent regression fixture to quantify the numerical impact of the analysis-mode switch. It is not required to decide which response is canonical; the analysis definitions are already different.
