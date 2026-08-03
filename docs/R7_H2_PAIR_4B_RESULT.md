# R7: first H2-pair to 4b DV+jets cutflow (provisional)

Status: **PROVISIONAL**. This is a first detector-sensitivity study for the
`pp -> H2 H2 -> b b~ b b~` topology through the real, R4-patched DV+jets
recast. The mass point (`m_H2 = 150 GeV`) and lifetime grid are provisional
2HDM Type-I benchmark values; the production mechanism is a Higgs-portal
simplified model standing in for the genuine 2HDM heavy-scalar coupling.
Nothing here should be read as a validated 2HDM exclusion result.

## Branch and commit

Branch `feat/r7-h2-pair-4b`, worktree
`/home/fabi/atlas_dihiggs/_worktrees/r7-h2-pair-4b`, based on `origin/main`
after PR #4 (R4 configurable-LLP-PDG) was merged
(merge commit `985b0bc`, containing R4 commit `0e0ee22a`).

## Source of the H2-pair sample

No existing `pp -> H2 H2 -> 4b` sample or process card was found anywhere in
the workspace (`ufos/`, `main_dihiggs/`, `hep_cross/`); the closest existing
asset was `ufos/runs/A_PI_NATIVE/pi_ufo_baseline_v1`, a validated MadGraph
process directory for `g g > H > h2 h2` (LLscalar_v3_UFO pack: PDG 9000006
for "h2", produced via an effective ggHphiphi Higgs-portal coupling through
a virtual PDG-25 propagator, `mphi_GeV = 200` in its existing benchmark
point). This is genuine H2-H2 **pair** production, not the single-resonance
`gg -> H2` case the task explicitly excludes as a main sample.

That compiled MadEvent process directory was copied out of the `ufos/`
working tree (never modified in place; `ufos/runs/**/build/` is itself
gitignored there) into a local scratch build area, and relaunched with
`Cards/param_card.dat`'s `9000006` mass changed from 200 to 150 GeV
(`m_H2 = 150 GeV` per the task spec) and `Cards/run_card.dat`'s `nevents`
raised from 100 to 1000. No branching ratios were computed or reinterpreted
in MadGraph; `h2` stays stable at LHE level (as the pack already designs
for), matching the required ownership split (MadGraph: production kinematics
only; Pythia: decay, lifetime, shower, hadronization).

**PDG relabeling (9000006 -> 35):** Pythia8's `ResonanceDecays` machinery —
needed to shower the `b b~` decay products into real jets, rather than the
non-showered "hadron decay" treatment Pythia falls back to for particle
decays outside its resonance framework — requires a registered
`ResonanceWidths` C++ object for the decaying PDG. Pythia only auto-provides
this for its own built-in resonance slots (verified: attempting to decay the
literal PDG 9000006 via `9000006:new`/`addChannel` either crashes with
"no open decay channel" when left as a resonance, or silently produces an
unshowered, unphysical 2-hadron final state when forced non-resonance).
Registering a custom `ResonanceWidths` subclass requires bespoke C++ code,
which is out of scope for a cmnd-only patch and outside the R4 patch
boundary. R4 already established PDG 35 (Pythia's "H0" slot) as the
validated stand-in for a `bb~`-decaying 2HDM-like scalar LLP
(`cards/r4_smoke/scalar_regression.cmnd`). This study reuses that exact
mechanism: the LHE's stable final-state PDG is relabelled `9000006 -> 35` by
a pure text substitution (mass, momenta, and all kinematics are
byte-identical; only the numeric PDG label changes), so Pythia's own H0
resonance-decay and showering code applies to our genuinely
pair-produced-by-MadGraph kinematics.

Cross-section at the generated point: **0.03044 +/- 0.00009 pb** (MadGraph,
13 TeV, `g g > H > h2 h2`, `m_h2 = 150 GeV`).

## Generation and recast commands

```bash
# Production (once, in a copy of ufos/runs/A_PI_NATIVE/.../MG5_PROC with
# param_card.dat: 9000006 mass -> 150 GeV; run_card.dat: nevents -> 1000)
./bin/generate_events -f r7_h2pair_150

# PDG relabel (pure text substitution, kinematics unchanged)
zcat unweighted_events.lhe.gz | sed 's/\b9000006\b/35/g' | gzip -c \
  > h2pair_150_pdg35.lhe.gz

# Recast build (unmodified R4 patch, submodule untouched)
./scripts/bootstrap_upstream.sh
./scripts/build_patched_upstream.sh

# Recast run, once per lifetime (same LHE reused; only 35:tau0 changes)
./results/upstream_build_patched/analysis/recast_2301_13866 \
  cards/r7_h2_pair_4b/ctau_0p481mm.cmnd   # (LHE path substituted at run time)
./results/upstream_build_patched/analysis/recast_2301_13866 \
  cards/r7_h2_pair_4b/ctau_4p326mm.cmnd
./results/upstream_build_patched/analysis/recast_2301_13866 \
  cards/r7_h2_pair_4b/ctau_48p070mm.cmnd
```

Smoke command: the same binary run with `Main:numberOfEvents` reduced to 20
against the same LHE, used to validate the cmnd wiring before the full run
(see debugging notes below).

## Event count

**1000 events**, generated once and reused unchanged for all three lifetime
configurations (only `35:tau0` differs between the three cmnd cards).

## Topology checks (pre-cutflow, lifetime-independent)

Computed with a temporary debug build instrumenting the same
`ToyDetector`/FastJet jet definition the recast itself uses (anti-kt,
pT > 20 GeV); not part of the committed patch.

| Observable | Value |
|---|---|
| Events generated | 1000 |
| Fraction with 2 H2 at hard-process level | 100% |
| Fraction with both H2 -> b b~ | 100% |
| Mean jet multiplicity (pT > 20 GeV) | 5.29 |
| Fraction with >= 4 jets (pT > 20 GeV) | 89.7% |
| Fraction with zero configured LLP found (real recast diagnostic) | 0% |

The `H2 H2 -> 4b` topology **does reach jet preselection** in the loose
sense: production and decay proceed exactly as configured (100%/100%), and
the event has enough jet activity to form >=4 jets above a generic 20 GeV
threshold in 9 events out of 10.

## Three cutflows

Full per-stage counts are in `results/r7_h2_pair_4b/cutflow_ctau_*.csv`
(both signal regions). Condensed (identical across all three lifetimes,
out of 1000 generated events):

| Stage | High-pT region | Trackless region |
|---|---|---|
| Events processed | 1000 | 1000 |
| LLP found | 1000 | 1000 |
| Jet Selection (region-specific jet-pT thresholds) | 1 | 13 |
| Fiducial decay (`r<300mm, |z|<300mm`) | 1 | 13 |
| `R_vertex > 4 mm` | 0 | 0 |
| `|d0| > 2 mm` track | 0 | 0 |
| Selected decay products >= 5 | 0 | 0 |
| Invariant mass > 10 GeV | 0 | 0 |
| **Final selection (Acc x Eff)** | **0** | **0** |

## Acceptance x efficiency

| ctau (mm) | High-pT A x eff | Trackless A x eff |
|---|---|---|
| 0.481 | 0.0 | 0.0 |
| 4.326 | 0.0 | 0.0 |
| 48.070 | 0.0 | 0.0 |

All three lifetimes give **zero** final acceptance in both signal regions.
Per task instructions, cuts were not modified or loosened to force a
nonzero result.

## Dominant loss

**Jet Selection**, in both regions, and it is the *same* loss for all three
lifetimes (Jet Selection and Fiducial are lifetime-independent — they
depend only on production/shower kinematics, not on displaced-decay
length). The recast's High-pT region requires a 4th-leading jet
`pT > 250 GeV` (or looser thresholds down to 90 GeV for higher jet
multiplicities); the Trackless region requires `pT > 137 GeV` on the 4th
jet (down to 55 GeV for higher multiplicities). These thresholds were
calibrated for the strong-bm1 benchmark's ~2000 GeV gluino pair production.
Our `H2 H2` topology, at `m_H2 = 150 GeV` (300 GeV total system mass), has
plenty of jet *multiplicity* (89.7% with >=4 jets above a loose 20 GeV cut)
but not enough jet *pT* to clear these TeV-scale-calibrated thresholds: only
1/1000 (High-pT) and 13/1000 (Trackless) events survive.

Because so few events (1 or 13) survive Jet Selection, the subsequent
displaced-vertex geometric cut (`R_vertex > 4 mm`) removes all of them for
every lifetime tested, including the longest (48.070 mm, where a nonzero
survival rate would normally be expected on physical grounds). This is
consistent with a statistics-limited zero at the vertex stage riding on top
of an already-dominant, lifetime-independent Jet Selection loss — not
evidence that the displaced-vertex requirement itself is the leading
inefficiency.

## Interpretation

1. **Does the correct `H2 H2 -> 4b` topology reach jet preselection?**
   Yes, in the loose multiplicity sense (89.7% with >=4 jets at pT>20 GeV,
   with production and decay proceeding exactly as configured at 100%). It
   does not clear the recast's actual, much harder region-specific jet-pT
   thresholds except in a small handful of events (1-13 out of 1000).
2. **Does either signal region retain events?** No; both High-pT and
   Trackless give zero final selected events for all three lifetimes.
3. **How does acceptance change from 0.48 to 4.33 to 48.1 mm?** It does not
   change in this run — all three are zero, and the pre-vertex cutflow
   (Jet Selection, Fiducial) is numerically identical across all three by
   construction (same production sample, lifetime-independent cuts). The
   sample is too small after Jet Selection (1-13 events) to resolve any
   genuine ctau-dependence at the vertex-requirement stage.
4. **Which cut removes the most signal?** Jet Selection, by a wide margin
   (removes 98.7%-99.9% of events before any displaced-vertex logic is even
   evaluated).
5. **Is DV+jets worth continuing for this benchmark?** Not at this mass
   point and production mechanism as configured. The bottleneck is not the
   long-lived-particle physics (LLP-finding, decay, and displaced-vertex
   logic all work correctly and produce sensible, non-tuned zeros) but the
   jet-pT thresholds inherited from a search designed around a much heavier
   (~2 TeV gluino) production topology. A next iteration should first check
   whether a genuine 2HDM heavy-Higgs-mediated production mode (rather than
   this Higgs-portal simplified-model stand-in) gives harder jets, and/or
   evaluate the search's `mh2` mass dependence before concluding DV+jets is
   insensitive to a 150 GeV 2HDM scalar pair.

## Artifacts produced

- `results/r7_h2_pair_4b/cutflow_ctau_0p481mm.csv`
- `results/r7_h2_pair_4b/cutflow_ctau_4p326mm.csv`
- `results/r7_h2_pair_4b/cutflow_ctau_48p070mm.csv`
- `results/r7_h2_pair_4b/summary.csv`
- `results/r7_h2_pair_4b/acceptance_vs_ctau.pdf` (per-cut efficiency plot,
  since all three A x eff values are zero, per task instructions)
- `cards/r7_h2_pair_4b/ctau_0p481mm.cmnd`, `ctau_4p326mm.cmnd`,
  `ctau_48p070mm.cmnd`

## Genuine blockers

None that block this study's stated scope. Noted limitations, explicitly
out of scope to resolve here:

- No existing 2HDM UFO model (genuine `sin(beta-alpha)`/`lambda6/7`
  couplings) was found in the workspace; production used a Higgs-portal
  simplified model as a provisional stand-in, per the task's own framing of
  the central point as provisional.
- The `9000006 -> 35` PDG relabeling is a pragmatic workaround for a real
  Pythia8 API limitation (no auto-registered `ResonanceWidths` for fully
  custom PDGs); it does not affect kinematics but should be revisited if a
  future task needs the LLP to carry its own distinct PDG identity through
  the recast (e.g. multiple simultaneous BSM particles in one run).
