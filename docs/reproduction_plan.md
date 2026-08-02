# Reproduction plan

## M0 — Repository scaffold

Deliverables:

- frozen upstream lock;
- deterministic bootstrap;
- environment preflight;
- provenance manifest;
- tests and CI independent of the HEP stack.

Exit condition: `make static-check` passes.

## M1 — Upstream build

1. Install or locate FastJet and Pythia8.
2. Compile Pythia8 with FastJet support.
3. Build `recast_2301_13866` from the frozen upstream source.
4. Save compiler, linker and runtime-library evidence.

Exit condition: executable starts and the environment manifest records the resolved toolchain.

## M2 — Upstream physics validation

1. Select one supplied MG5/SLHA validation benchmark.
2. Generate or recover its LHE input.
3. run the supplied Pythia card through the unmodified recast;
4. parse the cutflow into a compact table;
5. compare against the upstream reference.

Exit condition: the validation contract is satisfied or the discrepancy is explicitly diagnosed. Do not proceed on an unexplained factor-of-two disagreement.

## M3 — Minimal scalar adaptation

Implement only:

- configurable LLP PDG IDs;
- explicit `original` and `modified` analysis modes;
- versioned patch or project-owned analysis layer;
- regression test proving the original upstream benchmark remains unchanged.

Exit condition: upstream regression remains valid after the adaptation.

### R4/R5 status — configurable LLP identity (compatibility layer only)

The LLP PDG id is now a single configurable parameter,
`dvrecast.config.resolve_llp_pdg_id`, defaulting to `1000022` (the strong-bm1
neutralino). strong-bm1 remains the validated baseline and is unaffected: it
does not call this resolver and keeps its own frozen PDG assertions in
`src/dvrecast/readiness.py`. `dvrecast.llp_event` adds fixture-driven,
dependency-free LLP identification, descendant traversal and displaced-vertex
reading (`scripts/run_llp_smoke.py`), exercised against a synthetic
alternate-scalar fixture (`tests/fixtures/llp_scalar_smoke_event.json`). This
is a **technical** smoke test, not a physics benchmark — it carries no
physics-derived thresholds and does not constitute the M4 paper benchmark or
any H2 physical interpretation, which remain later milestones blocked on
upstream compilation (M1/M2).

## M4 — Paper benchmark

Run one declared benchmark from arXiv:2606.01681 and reproduce the corresponding original/modified cutflow to the agreed tolerance. Cross-section normalization is tracked separately from acceptance and efficiency.

## M5 — Paper scan and exclusions

Only after M4:

- generate the declared mass/lifetime grid;
- freeze HEPData inputs;
- reproduce the selected figures or exclusion contours;
- document statistical assumptions.

## M6 — Local 2HDM reinterpretation

Connect validated DiHiggs event generation through a stable sample contract containing model point, process, cross section, lifetime, branching fractions, generator versions and checksums.
