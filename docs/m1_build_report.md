# M1 upstream build report

Status: `VALIDATED` for Validation Contract Gate A (build) only. No physics benchmark
was run; the selected M2 benchmark remains `BLOCKED`.

## Revisions and toolchain

| Item | Recorded value |
|---|---|
| Repository commit | `220f719d001e19a8f870dc37352e2f9452672f1c` (dirty) |
| Upstream repository | `https://github.com/llprecasting/recastingCodes.git` |
| Upstream commit | `d4047c744062094c9f88e507bb1ccf69e9fe88d6` |
| Compiler | GCC/G++ 13.3.0 |
| FastJet | 3.4.0 at `$HOME/.local/fastjet-3.4.0` |
| PYTHIA | 8.308 at `$HOME/.local/pythia8308` |
| PYTHIA source checkout | `MATCHES`: tag `pythia8308` and declared commit `38ebd86865e4f25e9cf461b610f5c82d475ab77a` both resolve to checkout HEAD; tracked changes and untracked entries are recorded separately |
| PYTHIA install origin | `UNVERIFIED`: the installed 8.308 prefix is not proven to have been built from the declared source checkout |
| Successful build time | `2026-07-12T16:58:56Z` |
| Executable | `external/recastingCodes/DisplacedVertices/ATLAS-SUSY-2018-13_GCottin/recast_code/1_analysis/recast_2301_13866` |
| Executable SHA-256 | `9d19ee8dce66692dab668265bcf367c4b988620b8e720b896564a7d5c736c027` |

The machine-readable record is `results/manifests/environment.json` (generated and
untracked). It includes repository dirty state, prefixes, source-checkout declaration
status, separate tracked and untracked checkout state, an explicitly unverified install
origin, compiler, build timestamp, executable checksum, and complete `ldd`
output, plus the four readiness states and their exact blockers. If no optional source
checkout is configured, declarations remain `UNVERIFIED`; an unavailable checkout is
non-fatal, while contradictions are clearly flagged as `MISMATCH`.

## Command record

Commands were run from the repository root with the local virtual environment active.

| Command | Result |
|---|---|
| `make static-check` (first rerun) | `FAILED`: 12 tests passed; Ruff reported import/line formatting in newly edited files. |
| `make upstream-check` | passed; frozen layout and commit matched. |
| `make hep-preflight` | returned zero; core and build ready, generation blocked by missing MadGraph. |
| `make build-upstream` (first hardened-wrapper run) | `FAILED`: compilation and `ldd` passed, but the smoke check initially expected exit zero; upstream intentionally exits 1 after printing usage. |
| `make build-upstream` (corrected smoke contract) | passed. |
| `make manifest` | passed. |
| `make static-check` (after audit fixes) | passed: 19 tests and Ruff. |

The final completion sequence reran all five Make targets successfully, followed by a
successful `git diff --check`.

## Build evidence

The wrapper removes only the four products declared by the upstream Makefile before a
rebuild: three object files and `recast_2301_13866`. It does not call the nonexistent
upstream `clean` target or modify upstream sources. Timestamped logs are retained under
`results/upstream_build/`, with `build.log` holding the latest copy.

`ldd` resolved `libpythia8.so`, `libfastjet.so.0`, `libstdc++.so.6`, `libm.so.6`,
`libgcc_s.so.1`, `libc.so.6`, and `libz.so.1`; no entry contained `not found`. The
no-argument smoke test returned non-zero and its combined output contained the required
`pathToCMND` usage token. Standard output, standard error, and return code are retained.
The observed output was:

```text
./recast_2301_13866 pathToCMND
   - pathToCMND is the path to the Pythia input cmnd card
```

FastJet emits GCC deprecation warnings for its use of `std::auto_ptr`. These are
non-blocking third-party warnings and were not suppressed or patched.

## Readiness states

- Core environment: `READY` (Git, Make, G++, Python found).
- Upstream recast build readiness: `READY` (configured headers, libraries, usable
  config scripts, G++, and Make are present).
- MadGraph LHE-generation tool readiness: `BLOCKED` (`mg5_aMC` is missing).
- Selected upstream benchmark readiness: `BLOCKED` (the exact bm1 SLHA/generation
  configuration and all three LHE samples are missing; MadGraph is also absent).

The Ruff exclusion for `external/recastingCodes` is intentional: the immutable,
third-party submodule contains pre-existing lint violations and is outside project code
ownership. Project linting continues to cover the repository-owned Python files.

MadGraph absence does not block Gate A or report the upstream C++ build as blocked.

## M2 engineering debt

- Split environment, build, and benchmark artifacts.
- Consider out-of-tree upstream builds.
- Retain build artifacts or explicitly mark them as non-retained.
- Remove hardcoded benchmark knowledge from generic readiness code.
