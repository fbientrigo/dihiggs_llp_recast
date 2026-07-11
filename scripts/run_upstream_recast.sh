#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ANALYSIS_DIR="${ROOT}/external/recastingCodes/DisplacedVertices/ATLAS-SUSY-2018-13_GCottin/recast_code/1_analysis"
EXECUTABLE="${ANALYSIS_DIR}/recast_2301_13866"

usage() {
  echo "Usage: $0 --cmnd PATH [--out DIR] [--dry-run]" >&2
}

CMND=""
OUT="${ROOT}/results/upstream_validation"
DRY_RUN=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --cmnd) CMND="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    *) usage; exit 2 ;;
  esac
done

[[ -n "${CMND}" ]] || { usage; exit 2; }
[[ -f "${CMND}" ]] || { echo "[ERROR] Missing cmnd card: ${CMND}" >&2; exit 3; }
[[ -x "${EXECUTABLE}" ]] || { echo "[ERROR] Missing executable: ${EXECUTABLE}" >&2; exit 4; }

mkdir -p "${OUT}"
COMMAND=("${EXECUTABLE}" "$(realpath "${CMND}")")
printf '%q ' "${COMMAND[@]}" | tee "${OUT}/command.txt"
printf '\n' | tee -a "${OUT}/command.txt"

if [[ "${DRY_RUN}" == "1" ]]; then
  exit 0
fi

(
  cd "${ANALYSIS_DIR}"
  "${COMMAND[@]}"
) 2>&1 | tee "${OUT}/recast.log"
