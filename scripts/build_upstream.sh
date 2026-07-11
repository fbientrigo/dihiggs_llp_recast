#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOLCHAIN="${TOOLCHAIN_ENV:-${ROOT}/configs/toolchain.env}"
ANALYSIS_DIR="${ROOT}/external/recastingCodes/DisplacedVertices/ATLAS-SUSY-2018-13_GCottin/recast_code/1_analysis"
OUT="${ROOT}/results/upstream_build"

[[ -f "${TOOLCHAIN}" ]] || {
  echo "[ERROR] Missing ${TOOLCHAIN}. Copy configs/toolchain.env.example and edit it." >&2
  exit 2
}
# shellcheck disable=SC1090
source "${TOOLCHAIN}"

: "${PYTHIA8:?PYTHIA8 must be defined in the toolchain file}"
: "${FASTJET3:?FASTJET3 must be defined in the toolchain file}"
CXX="${CXX:-g++}"
BUILD_JOBS="${BUILD_JOBS:-4}"

for path in \
  "${PYTHIA8}/include/Pythia8/Pythia.h" \
  "${PYTHIA8}/lib/libpythia8.so" \
  "${FASTJET3}/include/fastjet" \
  "${FASTJET3}/lib" \
  "${ANALYSIS_DIR}/Makefile"; do
  [[ -e "${path}" ]] || { echo "[ERROR] Required path missing: ${path}" >&2; exit 3; }
done

mkdir -p "${OUT}"
{
  echo "created_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "analysis_dir=${ANALYSIS_DIR}"
  echo "PYTHIA8=${PYTHIA8}"
  echo "FASTJET3=${FASTJET3}"
  echo "CXX=${CXX}"
  echo "BUILD_JOBS=${BUILD_JOBS}"
  "${CXX}" --version | head -n 1
} | tee "${OUT}/build_environment.txt"

make -C "${ANALYSIS_DIR}" clean || true
make -C "${ANALYSIS_DIR}" -j"${BUILD_JOBS}" \
  CXX="${CXX}" PYTHIA8="${PYTHIA8}" FASTJET3="${FASTJET3}" \
  2>&1 | tee "${OUT}/build.log"

EXECUTABLE="${ANALYSIS_DIR}/recast_2301_13866"
[[ -x "${EXECUTABLE}" ]] || { echo "[ERROR] Build completed without executable." >&2; exit 4; }
ldd "${EXECUTABLE}" | tee "${OUT}/ldd.txt"
"${EXECUTABLE}" >"${OUT}/smoke.stdout" 2>"${OUT}/smoke.stderr" || true

echo "[OK] Built ${EXECUTABLE}"
