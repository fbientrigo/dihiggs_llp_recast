#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 /path/to/recastingCodes" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UPSTREAM_ROOT="$(cd "$1" && pwd)"
ANALYSIS="$UPSTREAM_ROOT/DisplacedVertices/ATLAS-SUSY-2018-13_GCottin/recast_code/1_analysis"
EXE="$ANALYSIS/recast_2301_13866"

[[ -x "$EXE" ]] || {
  echo "Missing executable: $EXE. Apply the patch and build upstream first." >&2
  exit 3
}

cd "$ROOT"
"$EXE" cards/A_original/pythia_scalar_toy.cmnd original 9900035 \
  > results/cpp_A_original.log 2>&1
"$EXE" cards/B_modified/pythia_scalar_toy.cmnd modified 9900035 \
  > results/cpp_B_modified.log 2>&1

echo "[OK] results/cpp_A_original.log"
echo "[OK] results/cpp_B_modified.log"
