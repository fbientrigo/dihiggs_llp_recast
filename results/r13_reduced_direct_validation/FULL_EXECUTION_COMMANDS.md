# Future R13 Full Campaign Execution Specification

> [!IMPORTANT]
> The full R13 campaign ($6g \times 12c\tau \times 2 = 144$ recast jobs) is authorized by the successful completion of the reduced end-to-end validation.
> **DO NOT RUN THE FULL CAMPAIGN IN THIS MISSION.**

## Command Specification

When authorized for full campaign execution, use the following exact command:

```bash
python3 scripts/r13_execute_full.py \
  --execute \
  --resume \
  --max-parallel 2 \
  --strict-no-fallback \
  --require-mass 150 \
  --reject-absolute-card-paths \
  --require-direct-production-table \
  --require-explicit-g0
```

## Runtime Pre-execution Safety Guards

The execution script implements preflight validation that halts execution if any of the following conditions are met:
1. Any generated Pythia card contains `35:m0` != `150.0` or `35:mMin` != `100.0`.
2. Any card or script contains `/home/fabi`.
3. The production table is not the pinned direct Phase A production table (`r13_production_combined.csv`).
4. Any requested $g$ point lacks a direct production cross-section row in the table.
5. The $R10$ $g_0$ reference point is ambiguous or not explicitly specified as $g_0 = 63.59142520075966\text{ GeV}$.
6. A stale or invalid result directory would be mixed with the new campaign output.
