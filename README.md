# DiHiggs LLP DV+jets recast

Reproducible workspace for the ATLAS displaced-vertex plus jets recast used by the DiHiggs/2HDM LLP study.

## Current scientific status

The public recast baseline has been reproduced and the first physical H2 -> bb benchmark has been run through the frozen original/published Trackless analysis.

Canonical 150 GeV benchmark:

```text
m_H2 = 150 GeV
ctau = 4.326221529733112 mm
PDG = 35
H2 -> bb forced in the recast sample
Trackless raw acceptance = 40 / 2000 = 0.020000
Trackless weighted Acc x Eff = 31.46772 / 2000
Trackless_Aeff = 0.01573386
```

The authoritative recast interpretation for current Boundary/signal work is:

```text
EFFICIENCY_CLOSURE_RESOLVED_R8_AUTHORITATIVE
analysis = original/published Trackless
```

A later local campaign produced a larger response near `Aeff ~ 0.0531` using the executable's `modified` analysis mode. That mode changes the Trackless selection itself (jet thresholds / displaced-jet requirement / efficiency application) and is therefore **not the same observable**. It must be labelled `MODIFIED_ANALYSIS_TRACKLESS_RESPONSE` and must not silently replace the R8/R10 original-analysis response.

The historical weighted-Aeff uncertainty carried by the R10 table is provisional; it is not a detector systematic.

See `docs/CANONICAL_TRACKLESS_STATUS_20260807.md` and `docs/R8_PI_RESULT_BRIEF.md`.

## Scope

The repository has three scientific responsibilities:

1. **Upstream validation** — preserve the frozen public ATLAS DV+jets recast and its reproducible build.
2. **Scalar adaptation** — allow the LLP PDG/lifetime to be supplied without changing the published analysis selection.
3. **Acceptance/efficiency response** — produce cutflows and `A x epsilon` for validated event samples.

Production cross sections are **not** owned here. New physical-point production belongs to the MadGraph layer (`dihiggs_hep_cross`) and should be evaluated per physical point. This repository should not infer production normalization from a coupling scaling law.

## Frozen upstream baseline

```text
upstream revision: d4047c744062094c9f88e507bb1ccf69e9fe88d6
```

The R8 scalar patch is intentionally minimal: configurable LLP PDG and lifetime, with the analysis selection, efficiency maps, jet definitions and geometry otherwise preserved.

## Quick validation

```bash
git clone https://github.com/fbientrigo/dihiggs_llp_recast.git
cd dihiggs_llp_recast
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
make bootstrap
make check
make manifest
```

When the HEP toolchain is available:

```bash
cp configs/toolchain.env.example configs/toolchain.env
# Edit the Pythia8/FastJet installation prefixes.
make build-upstream
```

The frozen R8 artifacts can be verified without rerunning MadGraph or regenerating the physics sample using the repository's R8 verification scripts.

## Rules for new work

- Preserve the original/published Trackless analysis as the canonical ATLAS response.
- If testing `modified` mode, keep it explicitly separated and never compare its absolute Aeff as if it were the same selection.
- Keep raw Trackless acceptance separate from weighted `Acc x Eff`; canonical `Trackless_Aeff` is the weighted quantity divided by generated events.
- Do not rerun a large recast campaign merely to change a production cross section.
- Do not apply `BR_bb` inside the forced-decay recast efficiency; physical pair normalization uses `BR_bb^2` downstream exactly once.
- Preserve lifetime settings, cards, seeds, cutflow logs and artifact hashes for any new efficiency point.

## Repository layout

```text
configs/       frozen upstream and reproduction configuration
scripts/       bootstrap, build, verification and comparison utilities
src/dvrecast/  dependency-free Python support package
tests/         unit tests that run without the HEP stack
docs/          scientific status, validation and reproduction contracts
external/      locally materialized third-party code; ignored by Git
data/          local or downloaded inputs; heavy content ignored
results/       frozen compact validation / recast artifacts
cards/         versioned Pythia/recast cards
models/        model metadata and small source definitions
patches/       versioned adaptations against the frozen upstream commit
```

## References

- ATLAS DV+jets search: https://arxiv.org/abs/2301.13866
- Public recast: https://github.com/llprecasting/recastingCodes/tree/main/DisplacedVertices/ATLAS-SUSY-2018-13_GCottin
- HEPData: https://www.hepdata.net/record/ins2628398
## Convention provenance

The project-wide theory convention is owned by `dihiggs`. This repository's v3 cache is identified by `conventions/physics_conventions.lock.yaml`; new sample manifests and handoffs must preserve the incoming `physics_conventions_schema`, `physics_conventions_commit`, and `physics_conventions_sha256`. The cache does not make frozen recast results current or authoritative.
