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

python3 "${ROOT}/scripts/check_build_prerequisites.py" \
  --pythia8 "${PYTHIA8}" --fastjet3 "${FASTJET3}" --cxx "${CXX}"
[[ -e "${ANALYSIS_DIR}/Makefile" ]] || {
  echo "[ERROR] Required path missing: ${ANALYSIS_DIR}/Makefile" >&2
  exit 3
}

mkdir -p "${OUT}"
BUILD_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BUILD_LOG="${OUT}/build-${BUILD_STAMP}.log"
{
  echo "created_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "analysis_dir=${ANALYSIS_DIR}"
  echo "PYTHIA8=${PYTHIA8}"
  echo "FASTJET3=${FASTJET3}"
  echo "CXX=${CXX}"
  echo "BUILD_JOBS=${BUILD_JOBS}"
  "${CXX}" --version | head -n 1
} | tee "${OUT}/build_environment.txt"

# The upstream Makefile has no clean target. Remove only its declared build products.
rm -f \
  "${ANALYSIS_DIR}/Simpler_ToyDetector.o" \
  "${ANALYSIS_DIR}/efficiency.o" \
  "${ANALYSIS_DIR}/recast_2301_13866.o" \
  "${ANALYSIS_DIR}/recast_2301_13866"
make -C "${ANALYSIS_DIR}" -j"${BUILD_JOBS}" \
  CXX="${CXX}" PYTHIA8="${PYTHIA8}" FASTJET3="${FASTJET3}" \
  2>&1 | tee "${BUILD_LOG}"
cp "${BUILD_LOG}" "${OUT}/build.log"

EXECUTABLE="${ANALYSIS_DIR}/recast_2301_13866"
[[ -x "${EXECUTABLE}" ]] || { echo "[ERROR] Build completed without executable." >&2; exit 4; }
ldd "${EXECUTABLE}" | tee "${OUT}/ldd.txt"
if grep -Fq "not found" "${OUT}/ldd.txt"; then
  echo "[ERROR] At least one runtime library dependency was not found." >&2
  exit 5
fi

set +e
"${EXECUTABLE}" >"${OUT}/smoke.stdout" 2>"${OUT}/smoke.stderr"
SMOKE_RC=$?
set -e
cat "${OUT}/smoke.stdout" "${OUT}/smoke.stderr" >"${OUT}/smoke.combined"
printf '%s\n' "${SMOKE_RC}" >"${OUT}/smoke.returncode"
if [[ ${SMOKE_RC} -eq 0 ]] || ! grep -Fq "pathToCMND" "${OUT}/smoke.combined"; then
  echo "[ERROR] No-argument invocation did not fail with a usage hint." >&2
  exit 6
fi

sha256sum "${EXECUTABLE}" | tee "${OUT}/executable.sha256"

echo "[OK] Built ${EXECUTABLE}"
