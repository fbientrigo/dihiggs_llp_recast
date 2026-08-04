# Mission 01 — execution report

**Date:** 2026-07-15
**Package:** `recast_ab_initial_artifacts_v2_audited.zip` → `llp_recast/package/`
**Operator:** Claude Code (automated run)

**Headline:** Stage 0 (pure Python) and the C++ recast build/run both completed. The A/B
code path is demonstrably live — the modified selection raises Trackless Jet Selection from
25.0% to 51.6% on an identical scalar point. **However, the toy chain produces zero displaced
vertices in every mode, so the displaced-vertex branch of the recast — the physics the analysis
actually exists to test — is NOT exercised.** No result here is an exclusion or a reproduction.

---

## 1. Environment and versions

| Component | Version / value |
|---|---|
| OS | Ubuntu 24.04.3 LTS on Linux 6.18.33.2-microsoft-standard-WSL2 (WSL2) |
| python3 | 3.12.7 (`/home/fabi/anaconda3/bin/python3`) |
| g++ | 13.3.0 (Ubuntu 13.3.0-6ubuntu2~24.04.1) |
| make | GNU Make 4.3 |
| Pythia8 | **8.308** (`$HOME/.local/pythia8308`) |
| FastJet | **3.4.0** (`$HOME/.local/fastjet-3.4.0`) |
| MadGraph5_aMC@NLO | **3.5.3** (2023-12-23) (`$HOME/.local/mg5amcnlo/3.5.3`) |
| Mathematica | **absent** |
| git | 2.43.0 |
| Upstream `recastingCodes` | `d4047c744062094c9f88e507bb1ccf69e9fe88d6` (verified, matches `configs/upstream.lock.json`) |

`scripts/check_readiness.sh` probes `PATH` only and therefore reports Pythia8/FastJet/MadGraph
as `[MISS]` on a bare login shell. They are installed under the prefixes recorded in
`configs/toolchain.env`. Both views are captured in `results/readiness.txt`. Mathematica is the
only genuinely absent component; it is needed only for a FeynRules/NLOCT UFO build
(Mission 02, Track P-full-loop).

### Provenance handling

- `external/recastingCodes` was left **read-only and byte-pristine** (verified: 0 changed files),
  per `AGENTS.md`. The patch was applied to a disposable work copy at
  `.local/upstream_ab_work` (gitignored), which is where the build happened.
- The upstream `Makefile` was **not edited**; `PYTHIA8`/`FASTJET3` were supplied as make
  overrides on the command line.
- The ZIP ships pre-populated `results/` and `events/`. Those were hashed as received, then
  removed with `make clean`, then regenerated, so every artifact below was produced on this
  machine. All four `make all` products reproduce the shipped hashes **bit-for-bit**, confirming
  the toy generator and the proxy are deterministic as claimed.

---

## 2. Completed layers

### 2.1 Stage 0 — pure Python (`make all`), `PAPER_TABLE_PROXY_NOT_EXCLUSION`

| Target | rc | Output |
|---|---:|---|
| `make validate` | 0 | config, SLHA width/lifetime identity and BR sums all OK |
| `make toy` | 0 | 500-event scalar + 500-event neutralino toy LHE, `TOY_LHE_PLUMBING_TEST` |
| `make proxy` | 0 | `results/ab_proxy.csv`, `results/ab_summary.md` |

The proxy is arithmetic over the paper's Table II efficiencies (`Nsig = L * sigma * eff`),
anchored at 3 events with L = 139 fb⁻¹. It contains no local simulation whatsoever.

### 2.2 Topology audit (rc=0)

`scripts/audit_scan_topology.py examples/scan_points_example.csv` → `results/scan_topology_audit.csv`.
All 3 example points screen `HIGH` (hadronic parent fraction 0.95–1.0, zero photon fraction),
so none of them trip the `gamma gamma` / `Z gamma` warning from `START_HERE_AUDITED.md`. This is a
screening flag over `(mass, ctau)`-adjacent BR content only; it does **not** establish topology
equivalence with the paper's scalar.

### 2.3 Stage 1 — C++ recast build and A/B execution

- Commit verified as `d4047c74…`.
- `git apply --check patches/recast_scalar_ab.patch` → **rc=0** (dry run passed before applying).
- `git apply` → rc=0 against the work copy.
- Build → **rc=0**, executable `recast_2301_13866` produced (547 KB). Only `std::auto_ptr`
  deprecation warnings from FastJet headers under g++ 13 / `-std=c++11`; no errors.
- `scripts/run_cpp_ab.sh` → **rc=0**, ~8 s for both modes.

**A/B control verified:** after stripping comments, `cards/A_original/*.slha` and
`cards/B_modified/*.slha` are byte-identical. Both modes consumed the same LHE and the same
physics point, so the A/B difference is attributable to analysis strategy alone — the package's
central claim holds.

---

## 3. Blocked / not-validated layers

### 3.1 CRITICAL — the displaced-vertex branch is not exercised (`TOY_LHE_PLUMBING_TEST`)

The A/B run completed, but every cutflow stage below the jet selection is **exactly zero in both
modes** (`results/toy_cutflow_ab.csv`):

| Stage | A_original | B_modified |
|---|---:|---:|
| all_events | 500.0 | 500.0 |
| trackless_jet_selection_pct | 25.0 | **51.6** |
| trackless_fiducial_pct | 25.0 | 51.6 |
| trackless_rvertex_gt_4mm_pct | **0.0** | **0.0** |
| trackless_track_d0_gt_2mm_pct | 0.0 | 0.0 |
| trackless_selected_decay_products_ge_5_pct | 0.0 | 0.0 |
| trackless_invariant_mass_gt_10gev_pct | 0.0 | 0.0 |
| trackless_acc_pct | 0.0 | 0.0 |
| trackless_acc_x_eff_pct | **0.0** | **0.0** |

**Root cause (established, not inferred).** Using a standalone Pythia probe
(`scripts/diag/diag_llp_vertex.cc`, which does not touch upstream code):

1. The SLHA import is **correct**: PDG 9900035 is created with `m0 = 250 GeV`,
   `tau0 = 5.10 mm`, `mayDecay = 1`, and the intended BR mix (`bb`/`WW`/`ZZ`/`gg`).
2. But **every** terminal LLP has `tau = 0` and `rDec = 0` — 100/100 terminal LLPs, 0 with
   `rDec > 4 mm`. Expected for this benchmark is `mean rDec ≈ βγ·cτ ≈ 1.73 × 5.1 ≈ 8.8 mm`,
   which would comfortably clear the 4 mm cut.
3. In the **process record** the scalars already carry status `-22` ("decayed resonance") and
   their daughters are produced at `vProd = (0,0,0)`. The LLP is consumed by Pythia's
   process-level resonance-decay machinery, which never assigns a lifetime, so `tau0` is
   simply never used.
4. Pythia flags the SLHA/QNUMBERS-imported particle as `isResonance = 1`.

Consequently the toy exercises: LHE reading, PDG configuration, SLHA parsing, jet clustering,
and both analysis modes — but **not** vertex reconstruction, `d0`, track counting, vertex mass,
or the vertex/event efficiency parameterizations. The `Acc x Eff = 0` values are an artifact of
this plumbing gap, **not** a physics statement.

**Scope of the defect — it is not the patch, and not the scalar.** The shipped neutralino
control (PDG 1000022, upstream's native LLP, run through the unpatched default code path)
reproduces the identical pathology: `R_vertex > 4 mm = 0%`, `Acc x Eff = 0`
(`results/cpp_control_neutralino.log`). The gap is generic to the toy chain.

**Remedies attempted and rejected** (each verified to fail, so the next operator need not repeat them):

| Attempt | Result |
|---|---|
| `9900035:isResonance = false` in the `.cmnd` | Segfault — the particle does not exist until SLHA is parsed during `init()`, so the card line cannot apply |
| `setIsResonance(false)` in code after `init()` | Flag flips to 0, decays stay prompt (`rDec = 0`) |
| Declare LLP natively via `9900035:new` + `isResonance = false`, bypassing SLHA | Decays stay prompt (`rDec = 0`) |
| `ProcessLevel:resonanceDecays = off` | LLP survives to status 62 but never decays at all |
| `ProcessLevel:resonanceDecays = off` + `setIsResonance(false)` after `init()` | Decays occur, but still `tau = 0`, `rDec = 0` |

The lifetime is never sampled on any of these paths. Resolving this needs focused work on how
Pythia 8.308 assigns proper lifetimes to a QNUMBERS-declared BSM particle arriving final-state
from an LHE; it is not a one-line card fix.

### 3.2 Blocked — MadGraph event generation

Blocker: no UFO. `cards/madgraph/scalar_pair_proc_card.dat` contains the placeholder
`import model SCALAR_UFO`, which cannot resolve. MadGraph 3.5.3 itself **is** installed and
available, so this layer is blocked on the model, not the generator. Mathematica is also absent,
which blocks the FeynRules/NLOCT route (Track P-full-loop) specifically.

### 3.3 Blocked — paper reproduction (arXiv:2606.01681)

Blocked transitively by 3.2, and independently by 3.1: a cutflow comparison against Table II is
meaningless while the DV branch yields zero. Not attempted.

### 3.4 Blocked — 2HDM reinterpretation

Blocked by 3.3 and by the missing production trilinear coupling `g_h125_phi_phi`. Per
`model/scalar_portal_contract.json`, a cross section cannot be inferred from `Gamma_phi`. Not attempted.

---

## 4. Output inventory and hashes (SHA256)

Generated on this machine:

```
639cb5b047dd9b0aeeda8547a47686257e0df724e409986a600d685bad14e70c  results/readiness.txt
e640a78ccfba73a83a22ed06b029b0310c0596127c35484637dbfa8a4541007c  results/ab_proxy.csv
8169cf53dc805b5e818c69dba6f6b7f60df9f5a9f4cd274f491f98590430e9c1  results/ab_summary.md
2cf3306bd6045e817d6aef2e04ba1a53502a818a2026c627493e6be76310dae4  results/ab_proxy_from_scan.csv
792647c1b94bf6ec4f065a83501694285983e1ce343bca31311b12aac59beeb1  results/ab_proxy_from_scan.md
c526e8ba72befe51b882d9ebb8d90a5f320edf663658d6821907d4aa3ac15067  results/scan_topology_audit.csv
921756586332c7d7a769bad4cbe5811490db2bdbb210c13c4477b09d41a36654  results/cpp_A_original.log
f547acbbdf534f1f37589dd5520b7e366071c7b8701b93c8c00045c25953cf09  results/cpp_B_modified.log
328b354aee98fadc947d1c12a139885cab2253e37c4e35875b85dc1608a17fbf  results/cpp_control_neutralino.log
28b2ea8e9137cc8d1b844dd55f171bf048de0716f0fd526106da0b2ad10deb31  results/toy_cutflow_ab.csv
76b46d6dc9cca10fe9870b4ded7a5a60bade6465a4d345ae4cadaf81731d23be  events/neutralino_pair_toy.lhe
7edca4583e71199987c8573c0478d25a2fe416cebb8a40eb92dea9086e87bdb8  events/scalar_pair_toy.lhe
```

Inputs pinned for this run:

```
6779c6aca081cb9e17e189ab90183eb186f1b6beb5547b4aefd159623b4882db  patches/recast_scalar_ab.patch
79a0867bfeb035599291cc4eaeee1cc69aa4488e1fc09c68b18a192ebdc315e3  cards/A_original/pythia_scalar_toy.cmnd
49a9d36b5da5c31d6df3a250709d8d4b4f905c0e0bfe11a856783a9c9c4be377  cards/A_original/scalar_250_ctau5p1mm.slha
62a5dedb101e7d33d1ee7d946b49dbf39deeed4b0ce860ba9699ea474394d5b9  cards/B_modified/pythia_scalar_toy.cmnd
ac58360efe5653fdb6483271bd7d284ae3707fc22fd5c9feb0d5578002bc2f31  cards/B_modified/scalar_250_ctau5p1mm.slha
6b8ffd5c071eaf49fd7912934fcf64140b9898d3c5019e418ce20fbaf5effcf1  examples/scan_points_example.csv
```

New files added by this run: `scripts/extract_toy_cutflow_ab.py`, `scripts/diag/diag_llp_vertex.cc`,
`scripts/diag/README.md`.

`events/*.lhe` and `*.log` are gitignored by the repository and must not be committed.

---

## 5. Interpretation limits

- **`PAPER_TABLE_PROXY_NOT_EXCLUSION`** — `ab_proxy*.csv/md` are arithmetic over the paper's
  published Table II efficiencies. No detector simulation, no local event generation, no
  exclusion. The "sigma for 3 events" column is an anchor, not a limit.
- **`TOY_LHE_PLUMBING_TEST`** — `toy_cutflow_ab.csv` and the `cpp_*.log` files come from
  synthetic two-body LHE with deterministic kinematics. This is not MadGraph and does not
  represent off-shell Higgs production.
- **`LOCAL_RECAST_RESULT` is deliberately NOT claimed.** The C++ recast did execute, but with
  toy input and a dead DV branch, so the label would be misleading.
- The 25.0% → 51.6% A/B jet-selection shift shows the modified selection is wired in and looser,
  in the expected direction. It is **not** a measurement of the paper's prospective gain: the
  paper's A/B difference also involves the vertex/event efficiency treatment, which is exactly
  the part that never ran here.
- The toy `Acc x Eff = 0%` must **not** be compared against the proxy's 2.9% (A) / 11% (B) for
  the S250 point. Those numbers have no common basis: one is a broken toy chain, the other is
  the paper's own table.
- The topology audit's three `HIGH` screens do not license inheriting the paper's DV+jets
  efficiency for those points.
- No statement about 2HDM parameter space is supported by anything in this run.

---

## 6. Single next executable action

**Make the toy LLP decay at a displaced vertex, and prove it with the diagnostic.**

Determine why Pythia 8.308 assigns `tau = 0` to a QNUMBERS-declared BSM particle arriving
final-state from an LHE, then re-run:

```bash
cd package
g++ -o scripts/diag/diag_llp_vertex scripts/diag/diag_llp_vertex.cc \
    -I$HOME/.local/pythia8308/include -L$HOME/.local/pythia8308/lib -lpythia8 -lz \
    -Wl,-rpath $HOME/.local/pythia8308/lib -std=c++11
./scripts/diag/diag_llp_vertex cards/A_original/pythia_scalar_toy.cmnd
```

**Acceptance criterion:** `mean rDec ≈ 8.8 mm` and a non-zero count of terminal LLPs with
`rDec > 4 mm` (expect roughly half). Only then re-run `scripts/run_cpp_ab.sh` and expect
`trackless_rvertex_gt_4mm_pct > 0`.

This gates everything else: until a displaced vertex survives, the recast's DV branch is
unverified, and neither the paper benchmark (Mission 02) nor any 2HDM reinterpretation can be
attempted. Note that Mission 02's Stage-1 premise — "connect the toy sample to the public
recast" — is **not** met by a run that returns zero vertices, even though the executable builds
and exits 0.

Deferred until the above passes: obtaining a real UFO (the only blocker for MadGraph, which is
otherwise installed and ready at 3.5.3).
