# Full Production Execution Commands for 6 × 12 × 2 Campaign (144 Recast Runs, 360 Final Grid Rows)

## Overview
This document specifies the exact command invocations required for the full R13/R14 campaign across all 6 couplings, 12 ctau lifetimes, 2 production/recast seeds, and 5 BR values.

These commands support:
- `--execute`: Physically execute MadGraph LHE generation and Pythia/recast jobs.
- `--resume`: Skip completed and verified runs cleanly.
- `--max-parallel 2`: Enforce strict bounded parallelism limit.
- `--strict-no-fallback`: Strictly disallow falling back to factorized sigma, ctau-only Aeff, wrong g0 anchor, or stale comparison output.

---

## Phase A: Full MadGraph Production Campaign (6 g × 2 seeds = 12 physical runs)

```bash
python3 scripts/r12_run_madgraph_production.py \
  --execute \
  --resume \
  --max-parallel 2 \
  --strict-no-fallback \
  --g-values 40.0 63.59142520075966 100.0 150.0 205.09272542237372 300.0 \
  --seeds 211 223 \
  --events-per-run 1000 \
  --out-dir results/r14_full_madgraph_per_g_production
```

---

## Phase B: Full Pythia / Recast Campaign (6 g × 12 ctau × 2 runs = 144 recast runs)

```bash
python3 scripts/run_r12_madgraph_per_g_scan.py \
  --execute \
  --resume \
  --max-parallel 2 \
  --strict-no-fallback \
  --g-values 40.0 63.59142520075966 100.0 150.0 205.09272542237372 300.0 \
  --ctau-values 0.3 1.0 3.0 4.326221529733112 10.0 30.0 100.0 200.0 300.0 500.0 700.0 1000.0 \
  --br-values 0.1 0.25 0.5 0.7567374858085787 1.0 \
  --seeds 211 223 \
  --hep-cross-dir /home/fabi/atlas_dihiggs/_worktrees/r13-reduced-direct-production-validation \
  --out-dir results/r14_full_madgraph_per_g_scan
```

---

## Authoritative Validation & Post-Processing

```bash
python3 scripts/rebuild_r12_corrected_outputs.py \
  --repo-root . \
  --strict-no-fallback \
  --results-dir results/r14_full_madgraph_per_g_scan \
  --r10-reference data/r10_reference/efficiency_vs_ctau.csv
```
