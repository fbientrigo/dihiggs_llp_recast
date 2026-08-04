# Mission 01 — execute and audit the toy A/B recast bootstrap

You are operating on the supplied `package/` directory. Your goal is to determine exactly which layers run in the current environment and produce auditable outputs without presenting toy or proxy results as physical exclusions.

## Required actions

1. Read `START_HERE_AUDITED.md`, `README.md`, and `model/scalar_portal_contract.json`.
2. Run `scripts/check_readiness.sh` and save the output to `results/readiness.txt`.
3. Run `make all` and record return codes and generated-file hashes.
4. Run `scripts/audit_scan_topology.py examples/scan_points_example.csv`.
5. If `UPSTREAM_ROOT` points to a checkout of `llprecasting/recastingCodes`:
   - verify commit `d4047c744062094c9f88e507bb1ccf69e9fe88d6`;
   - run `git apply --check patches/recast_scalar_ab.patch` before applying it;
   - build the upstream executable only if Pythia8 and FastJet are available;
   - execute `scripts/run_cpp_ab.sh "$UPSTREAM_ROOT"`;
   - extract the original and modified Trackless cutflows into `results/toy_cutflow_ab.csv`.
6. If any dependency is missing, stop that layer cleanly and document the exact blocker. Do not invent outputs.
7. Write `results/execution_report.md` with these sections:
   - environment and versions;
   - completed layers;
   - blocked layers;
   - output inventory and hashes;
   - interpretation limits;
   - single next executable action.

## Non-negotiable labels

- Python efficiency arithmetic: `PAPER_TABLE_PROXY_NOT_EXCLUSION`.
- Synthetic LHE/recast: `TOY_LHE_PLUMBING_TEST`.
- Do not use `LOCAL_RECAST_RESULT` unless the C++ recast actually ran.
- Do not claim paper reproduction or a 2HDM exclusion.
