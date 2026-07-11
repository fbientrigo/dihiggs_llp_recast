# Architecture

## Data flow

```text
frozen upstream source
  -> documented toolchain build
  -> upstream MG5/LHE benchmark
  -> Pythia8 shower and decay
  -> FastJet reconstruction
  -> public DV+jets recast
  -> cutflow comparison
  -> configurable scalar adaptation
  -> paper benchmark comparison
  -> local 2HDM samples
  -> statistical reinterpretation
```

## Ownership boundary

`external/recastingCodes` is an immutable input. The project may carry patches, wrappers and comparison code, but it must always preserve the ability to run the frozen upstream baseline unchanged.

## Components

- `configs/upstream.lock.json`: immutable upstream repository and commit.
- `scripts/bootstrap_upstream.sh`: deterministic materialization of that revision.
- `scripts/check_environment.py`: non-invasive toolchain inventory.
- `scripts/check_upstream_layout.py`: expected-file contract.
- `scripts/write_environment_manifest.py`: provenance snapshot.
- `scripts/run_upstream_recast.sh`: auditable wrapper for one `.cmnd` card.
- `src/dvrecast`: dependency-free configuration and manifest primitives.

## Deliberately absent

The initial scaffold does not include a custom UFO, scalar event generation, modified recast implementation, HEPData interpolation or limit-setting code. Adding any of those before upstream validation would mix infrastructure, generator and analysis failures.
