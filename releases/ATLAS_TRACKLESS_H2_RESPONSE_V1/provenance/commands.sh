#!/usr/bin/env bash
# Exact command chain used to build this release. Reads only from
# already-existing, independently-reviewed campaign artifacts under the
# primary checkout's results/ tree; reruns no Pythia/recast simulation.
set -euo pipefail

PRIMARY=/home/fabian/atlas_dihiggs/dihiggs_llp_recast
RELEASE_DIR=/home/fabian/atlas_dihiggs/dihiggs_llp_recast-release-v1/releases/ATLAS_TRACKLESS_H2_RESPONSE_V1

# Phase 2: cutflow_long.csv, jet_branch_decomposition.csv, samples.csv, aeff_grid.csv
python3 "$RELEASE_DIR/scripts/build_release_tables.py" \
  --primary-checkout "$PRIMARY" \
  --outdir "$RELEASE_DIR"

# Gate A: exact regression against frozen R8 + 3x20k baselines
python3 "$RELEASE_DIR/scripts/gate_a_regression.py" "$RELEASE_DIR" \
  | tee "$RELEASE_DIR/validation/gate_a_result.json"

# Phase 3: Figures A-F (pdf+png)
python3 "$RELEASE_DIR/figures/source/generate_figures.py" \
  --release-dir "$RELEASE_DIR" \
  --diag-dir "$PRIMARY/results/trackless_jet_diag_20260812T032241Z"

# Phase 6: parameter-attribution-readiness table (table only, no attribution computed)
python3 "$RELEASE_DIR/scripts/build_attribution_readiness_table.py" \
  --primary-checkout "$PRIMARY" \
  --release-dir "$RELEASE_DIR"

# Final: checksum every file in the release package
( cd "$RELEASE_DIR" && find . -type f ! -name checksums.sha256 -print0 \
    | sort -z | xargs -0 sha256sum > checksums.sha256 )
