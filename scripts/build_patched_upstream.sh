#!/usr/bin/env bash
# Build the R4/R5 configurable-LLP-PDG variant of the frozen upstream recast.
#
# The submodule in external/recastingCodes stays read-only and clean: this
# copies the pinned analysis source into a build sandbox, applies
# patches/0001-configurable-llp-pdg-ids.patch there, and builds in the
# sandbox. Never run `make` inside external/recastingCodes directly.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOLCHAIN="${TOOLCHAIN_ENV:-${ROOT}/configs/toolchain.env}"
SOURCE_DIR="${ROOT}/external/recastingCodes/DisplacedVertices/ATLAS-SUSY-2018-13_GCottin/recast_code/1_analysis"
PATCH="${ROOT}/patches/0001-configurable-llp-pdg-ids.patch"
SANDBOX="${ROOT}/results/upstream_build_patched/analysis"

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
[[ -e "${SOURCE_DIR}/Makefile" ]] || {
  echo "[ERROR] Required path missing: ${SOURCE_DIR}/Makefile" >&2
  exit 3
}
if [[ -n "$(git -C "${ROOT}/external/recastingCodes" status --porcelain 2>/dev/null)" ]]; then
  echo "[ERROR] Upstream submodule is dirty; bootstrap a clean checkout first." >&2
  exit 4
fi

rm -rf "${SANDBOX}"
mkdir -p "${SANDBOX}"
cp -r "${SOURCE_DIR}/." "${SANDBOX}/"
# The patch is rooted at the submodule root (a/DisplacedVertices/.../1_analysis/...);
# SANDBOX only mirrors the 1_analysis leaf, so strip the five extra components.
(cd "${SANDBOX}" && patch -p5 <"${PATCH}")

rm -f "${SANDBOX}"/*.o "${SANDBOX}/recast_2301_13866"
make -C "${SANDBOX}" CXX="${CXX}" PYTHIA8="${PYTHIA8}" FASTJET3="${FASTJET3}"

EXECUTABLE="${SANDBOX}/recast_2301_13866"
[[ -x "${EXECUTABLE}" ]] || { echo "[ERROR] Build completed without executable." >&2; exit 5; }
sha256sum "${EXECUTABLE}"
echo "[OK] Built ${EXECUTABLE}"
