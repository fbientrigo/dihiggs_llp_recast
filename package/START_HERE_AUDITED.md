# START HERE — audited status of the A/B recast package

## Verdict

This is a **hybrid bootstrap package**, not a complete physics-generation package.

| Layer | Can run now? | What it proves | Physics status |
|---|---:|---|---|
| Paper-table proxy (`make proxy`) | Yes | Yield arithmetic and A/B presentation | `PAPER_TABLE_PROXY_NOT_EXCLUSION` |
| Synthetic LHE (`make toy`) | Yes | File/PDG/SLHA plumbing | `TOY_LHE_PLUMBING_TEST` |
| C++ recast with toy LHE | Conditional | Pythia/FastJet/recast connectivity and A/B code path | Local software test only |
| MadGraph event generation | No | Requires a real UFO and validated parameter mapping | Blocked |
| Paper reproduction | No | Requires paper-model event generation and cutflow validation | Blocked |
| 2HDM recast | No | Requires 2HDMC-to-UFO mapping and production coupling | Blocked |

## What the ZIP already contains

- Synthetic scalar and neutralino LHE samples.
- Pythia cards and minimal SLHA decay definitions.
- A patch for the public `llprecasting/recastingCodes` implementation.
- Original/modified A/B analysis modes.
- A paper-table efficiency proxy.
- A **model contract**, but not the model itself.

## What the ZIP does not contain

- A FeynRules source model.
- A UFO directory importable by MadGraph.
- A MadGraph `param_card.dat` consistent with a UFO.
- Physical MadGraph-generated LHE events.
- A validated production cross section.
- A mapping from the local 2HDMC parameter conventions to a UFO.
- The trilinear production coupling `h125-phi-phi` for each scan point.

The file `cards/madgraph/scalar_pair_proc_card.dat` contains
`import model SCALAR_UFO`; this is intentionally a placeholder and will fail until a real UFO is supplied.

## Correct execution order

### Stage 0 — pure-Python smoke test

```bash
unzip recast_ab_initial_artifacts_v2_audited.zip
cd package
make all
python3 scripts/audit_scan_topology.py examples/scan_points_example.csv
```

Expected result: validation passes, deterministic toy LHE files are generated, and proxy tables are written.

### Stage 1 — connect the toy sample to the public recast

Requirements:

- Linux environment.
- Public `llprecasting/recastingCodes` repository at the pinned commit.
- Pythia8 compiled with FastJet support.
- FastJet.
- A successful build of `recast_2301_13866`.

The same LHE and SLHA must be used in A and B. Only the analysis mode changes.

### Stage 2 — reproduce the paper model

Use the phenomenological scalar model of arXiv:2606.01681 before attempting the local 2HDM mapping. Required parameters are:

```text
mS, sin_theta, lambda_hSS, GammaS, BR(S -> XX), random_seed
```

The paper interaction contains a vertex equivalent to `h-S-S` with Feynman rule proportional to `lambda * v`. The scalar decay couplings scale with `sin_theta`, while the pair-production normalization scales with `lambda`.

Validate against at least these Table-II points:

```text
mS=100 GeV, ctau=290 mm
mS=170 GeV, ctau=55 mm
mS=250 GeV, ctau=5.1 mm
```

Start with 10k events for debugging. A statistical cutflow comparison requires substantially more events; the paper used one million events per benchmark.

### Stage 3 — map the local 2HDM

For each accepted 2HDMC point, export at least:

```text
point_id
m_h125, m_phi, m_A, m_Hpm
sin(beta-alpha), tan(beta)
lambda1..lambda7, m12_squared
Gamma_phi and all partial widths/BRs
g_h125_phi_phi with explicit normalization convention
kappa_top_h125 (or equivalent top Yukawa modifier)
PDG assignments and model/UFO version
```

The current scan CSV provides masses, total/partial widths and potential parameters, but not the production trilinear coupling. A cross section cannot be inferred from `Gamma_phi`.

## Key warning for the local scan

The paper's scalar has approximately SM-Higgs-like decay fractions at the same mass. The current nearest-neighbour proxy matches only `(mass, ctau)`. It does **not** prove topology equivalence.

Run:

```bash
python3 scripts/audit_scan_topology.py /path/to/scan.csv \
  --output results/scan_topology_audit.csv
```

Points dominated by `gamma gamma` or `Z gamma` should not inherit the paper's DV+jets efficiency without a dedicated simulation.
