#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${2:-upstream-susy}"
case "${MODE}" in
  upstream-susy)
    exec "${ROOT}/external/recastingCodes/DisplacedVertices/ATLAS-SUSY-2018-13_GCottin/recast_code/1_analysis/recast_2301_13866" "${1:?usage: run_recast.sh CMND [upstream-susy|scalar-h2]}"
    ;;
  scalar-h2)
    exec "${ROOT}/scripts/run_scalar_h2_smoke.sh"
    ;;
  *) echo "unknown mode: ${MODE}" >&2; exit 2 ;;
esac
