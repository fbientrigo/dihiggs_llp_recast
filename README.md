# DiHiggs LLP DV+jets recast

Reproducible workspace for validating the public ATLAS displaced-vertex plus jets recast before adapting it to long-lived scalar production in the local DiHiggs/2HDM program.

## Scope

The repository is deliberately split into three stages:

1. **Upstream validation** — compile and reproduce one public validation benchmark from `llprecasting/recastingCodes`.
2. **Paper reproduction** — reproduce a benchmark cutflow from arXiv:2606.01681 with configurable LLP identity and analysis mode.
3. **Local reinterpretation** — connect validated 2HDM event samples and derive limits only after stages 1 and 2 pass.

The current codebase implements the reproducibility and validation scaffold. It does **not** claim to reproduce physics results yet.

## Quick start in WSL/Linux

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

`make check` validates the repository and frozen upstream layout without requiring event generation. `make hep-preflight` reports which external HEP tools are available.

When Pythia8 and FastJet are available:

```bash
cp configs/toolchain.env.example configs/toolchain.env
# Edit the two installation prefixes.
make build-upstream
```

## First physics gate

Do not implement the scalar model or exclusions before all of the following are true:

- the public C++ recast compiles against a documented Pythia8/FastJet toolchain;
- one upstream validation sample produces a comparable cutflow;
- command line, tool versions, Git revisions, cards and outputs are captured in a manifest;
- discrepancies outside the agreed tolerance are explained.

See `docs/reproduction_plan.md` and `docs/validation_contract.md`.

## Repository layout

```text
configs/       frozen upstream and reproduction configuration
scripts/       bootstrap, build, preflight and comparison utilities
src/dvrecast/  dependency-free Python support package
tests/         unit tests that run without the HEP stack
docs/          architecture, milestones and validation contracts
external/      locally materialized third-party code; ignored by Git
data/          local or downloaded inputs; heavy content ignored
results/       manifests and compact validation summaries
cards/         versioned cards created by this project
models/        model metadata and small source definitions
patches/       versioned adaptations against the frozen upstream commit
```

## References

- Target study: https://arxiv.org/abs/2606.01681
- ATLAS DV+jets search: https://arxiv.org/abs/2301.13866
- Public recast: https://github.com/llprecasting/recastingCodes/tree/main/DisplacedVertices/ATLAS-SUSY-2018-13_GCottin
- HEPData: https://www.hepdata.net/record/ins2628398

## Status

**Phase 0 — repository and provenance scaffold.** The next executable milestone is compiling the frozen upstream recast in WSL and reproducing one upstream benchmark. Physics modifications remain blocked until that validation passes.
