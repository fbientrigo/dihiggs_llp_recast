# R7 H2-pair to 4b: corrected lifetime validation

Status: **VALIDATED for this deterministic 1000-event recast**. The sample is
a simplified scalar-pair stand-in, not a complete 2HDM prediction; its section
cross section must not be used as the physical 2HDM normalization.

## Reproducible input

The single persisted input used by all three recasts is
`results/r7_h2_pair_4b/input/h2pair_m150_1000events.lhe.gz`. It contains 1000
events from the compiled `gg -> H -> h2 h2` MadEvent process, with `m_h2 =
150 GeV`, stable h2 at LHE level, and fixed seed `24681357`. MadGraph reported
`0.0304 +/- 0.000148 pb` for this simplified sample. The generation command
and exact cards are retained beside the input in `results/r7_h2_pair_4b/input/`.

The recast handoff uses the pure `9000006 -> 35` PDG relabel already required
by the validated Pythia H0 resonance slot; momenta and production kinematics
are unchanged.

## Authoritative lifetime chain

Each card contains `Recast:llpPdgIds = {35}`, `Recast:llpTau0 = ...`,
`35:tauCalc = off`, `35:tau0 = ...`, and
`LesHouches:setLifetime = 2`. The last setting is required because the LHE
stores `VTIMUP = 0`; Pythia must generate the lifetime from its particle data
rather than preserve that input value.

Immediately after successful `pythia.init()`, the R4 patch reapplies
`tauCalc = false` and the requested `tau0` to every configured LLP and prints:

| ctau (mm) | m0 (GeV) | mWidth (GeV) | tau0 (mm) | tauCalc | mayDecay | isResonance |
|---:|---:|---:|---:|---|---|---|
| 0.481 | 150.00000 | 0.01636 | 0.48100 | 0 | 1 | 1 |
| 4.326 | 150.00000 | 0.01636 | 4.32600 | 0 | 1 | 1 |
| 48.070 | 150.00000 | 0.01636 | 48.07000 | 0 | 1 | 1 |

All three runs found configured LLP records in all 1000 events. The previous
lifetime-dependent result is replaced: it was unvalidated because the input
LHE was not retained, `tauCalc` could override card values, and the LHE
`VTIMUP` field could force zero generated lifetime.

## Generated geometry

The compact machine-readable summary is
`results/r7_h2_pair_4b/geometry_summary.csv`. It selects the two final H0
decay records per event from the Pythia history (2000 LLPs per run).

| ctau (mm) | median R (mm) | mean R (mm) | R > 4 mm | fiducial | L > 4 mm | expected L > 4 mm | R > 4 after High-pT | R > 4 after Trackless |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.481 | 0.1968 | 0.3842 | 0.20% | 100.00% | 4.90% | 4.51% | 0.00% | 2.38% |
| 4.326 | 1.7703 | 3.4552 | 27.25% | 100.00% | 51.20% | 52.93% | 100.00% | 45.24% |
| 48.070 | 19.6710 | 38.3938 | 84.65% | 92.65% | 93.15% | 93.30% | 100.00% | 90.48% |

The observed flight-length fractions agree in order of magnitude with
`exp[-4/(beta_gamma*ctau)]`; the radius distributions change monotonically
with the requested lifetime. The real recast reads the same final H0 decay
vertices, giving the corresponding nonzero and ctau-dependent vertex stages.

## Corrected cutflows

Counts are event counts except the final `Acc x Eff` entries, which are the
recast efficiency-weighted event equivalents.

| Stage | High-pT 0.481 | Trackless 0.481 | High-pT 4.326 | Trackless 4.326 | High-pT 48.070 | Trackless 48.070 |
|---|---:|---:|---:|---:|---:|---:|
| Events processed | 1000 | 1000 | 1000 | 1000 | 1000 | 1000 |
| LLP found | 1000 | 1000 | 1000 | 1000 | 1000 | 1000 |
| Jet Selection | 1 | 21 | 1 | 21 | 1 | 21 |
| Fiducial decay | 1 | 21 | 1 | 21 | 1 | 21 |
| R_vertex > 4 mm | 0 | 1 | 1 | 16 | 1 | 21 |
| |d0| > 2 mm track | 0 | 1 | 1 | 16 | 1 | 21 |
| Selected decay products >= 5 | 0 | 1 | 1 | 16 | 1 | 21 |
| Invariant mass > 10 GeV | 0 | 1 | 1 | 16 | 1 | 21 |
| Final A x Eff event equivalent | 0.00000 | 0.90064 | 0.94352 | 10.69558 | 0.92707 | 14.34416 |

The corrected A x Eff fractions are:

| ctau (mm) | High-pT | Trackless |
|---:|---:|---:|
| 0.481 | 0.000000% | 0.090064% |
| 4.326 | 0.094352% | 1.069558% |
| 48.070 | 0.092707% | 1.434416% |

Jet-selection efficiency is 0.10% in High-pT and 2.10% in Trackless at all
three lifetimes. It is the dominant loss after the correction; no analysis
cut was loosened.

The updated plot is `results/r7_h2_pair_4b/acceptance_vs_ctau.pdf`.
