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

### R4/R5 status — configurable LLP identity wired into the real recast path

The LLP PDG id is a single configurable parameter,
`dvrecast.config.resolve_llp_pdg_id` (default `1000022`, the strong-bm1
neutralino), rendered into a Pythia cmnd setting by
`dvrecast.config.render_llp_pdg_cmnd_line`. That setting is consumed
directly by the frozen upstream C++ recast itself
(`external/recastingCodes/.../recast_2301_13866.cc`) via a small, reviewable
patch, `patches/0001-configurable-llp-pdg-ids.patch`, applied at build time
by `scripts/build_patched_upstream.sh` — the read-only submodule is never
edited in place. The patch replaces the original hardcoded
`idAbs() == 1000022 || ... == 1000023 || ... == 1000024` mother-finding check
with a lookup against a configurable `Recast:llpPdgIds` Pythia setting
(defaulting to that same triplet), and adds an "Events with zero configured
LLP found" diagnostic so a missing/misconfigured LLP is reported explicitly
rather than falling through as a silent zero.

`strong-bm1`'s own frozen PDG assertions in `src/dvrecast/readiness.py` are
untouched — they validate that specific benchmark's identity, not the
generic recast's LLP-following logic.

Real-path validation, via `scripts/run_r4_smoke.sh` (see
`results/r4_smoke/`): the default configuration was proven byte-identical
(cutflow lines only, modulo the run timestamp and the new diagnostic line)
between the patched and unpatched binaries on the same internally-generated
Pythia8 SUSY sample (`cards/r4_smoke/neutralino_regression.cmnd`); an
alternate scalar (PDG 35, a stand-in for a 2HDM H2-like LLP,
`cards/r4_smoke/scalar_regression.cmnd`) was identified, its descendants
traced, and its displaced vertex evaluated by the same real cutflow, which
reports a real (non-tuned) zero at the jet-preselection stage; and a
missing-PDG configuration (`cards/r4_smoke/missing_llp_regression.cmnd`)
reports 100% "zero configured LLP found" rather than a silent empty cutflow.

Exact reproduction of the full, frozen strong-bm1 campaign through this real
path remains blocked: its original LHE inputs are an unavailable external
artifact (`scripts/acquire_strong-bm1.sh` reports
`BLOCKED_EXTERNAL_ARTIFACT`), so the byte-identical patched-vs-unpatched
check above is the strongest regression evidence available in this
environment. Any H2 physical interpretation (correct 2HDM couplings,
branching ratios, and a validated benchmark point) remains a later
milestone.

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
