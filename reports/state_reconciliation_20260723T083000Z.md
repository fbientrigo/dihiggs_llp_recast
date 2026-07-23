# State reconciliation 20260723T083000Z

Public references were verified against GitHub: UFO `a5226cc`, recast `220f719`, upstream `d4047c7`.

Selected UFO: `/home/fabi/atlas_dihiggs/ufos` (authoritative frozen Pack A/Pack AA artifacts). Selected recast base: committed local `747b8e3`; the dirty checkout was preserved.

Initial observation: UFO had no tracked modifications but a large untracked closure/artifact inventory; recast had two tracked modifications and 83 untracked paths. No reset, clean, checkout, stash, branch deletion, or existing-checkout edits were performed.

| path | branch | HEAD | dirty/untracked | local-only commits |
|---|---|---|---:|---|
| `/home/fabi/atlas_dihiggs/ufos` | `chore/repository-curation-20260723T081927Z` | `383e0cffb9736d5a5e5f65b94bb3de1dad023202` | 0/0 | 383e0cf test: add lightweight repository metadata validation, 69c59c3 chore: improve ignore rules for generated files, 8248f44 chore: classify retained and external artifacts, bfca141 docs: update repository entry points and current pack status |
| `/home/fabi/atlas_dihiggs/llp_recast` | `feat/m2-strong-bm1-reproduction` | `747b8e3bdee31e22cb03a2efcc526cde7420f2d6` | 11/83 | 747b8e3 Correct strong-bm1 toolchain and input readiness, 75d7328 Validate upstream recast build and benchmark readiness |
| `/home/fabi/code/dihiggs_llp_recast` | `feat/m2-upstream-benchmark` | `e7790013dd957682fa88208e6f04d433f69f005f` | 0/0 | e779001 Add blocked upstream benchmark manifest, 361b132 Validate upstream recast build and benchmark readiness |
| `/home/fabi/atlas_dihiggs/worktrees/recast_h2bb_smoke_20260723T000000Z` | `feat/r4-h2bb-provisional-smoke` | `747b8e3bdee31e22cb03a2efcc526cde7420f2d6` | 40/0 | 747b8e3 Correct strong-bm1 toolchain and input readiness, 75d7328 Validate upstream recast build and benchmark readiness |

The full machine-readable state, remote URLs, tracking state, submodule state, dirty files and untracked inventories are in the JSON report. The original recast tracked diff and untracked inventory are snapshotted alongside it.
