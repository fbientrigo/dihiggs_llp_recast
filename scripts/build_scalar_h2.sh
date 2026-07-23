#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${TOOLCHAIN_ENV:-${ROOT}/configs/toolchain.env}"
UPSTREAM="${ROOT}/external/recastingCodes/DisplacedVertices/ATLAS-SUSY-2018-13_GCottin/recast_code/1_analysis"
OUT="${ROOT}/build/scalar_h2_recast"
mkdir -p "${OUT}"
"${CXX:-g++}" -std=c++11 -O2 \
  -I"${PYTHIA8}/include" -I"${FASTJET3}/include" -I"${UPSTREAM}" \
  "${ROOT}/src/scalar_h2_recast.cc" "${UPSTREAM}/Simpler_ToyDetector.cc" "${UPSTREAM}/efficiency.cc" \
  -L"${PYTHIA8}/lib" -lpythia8 -L"${FASTJET3}/lib" -lfastjet -lz \
  -Wl,-rpath,"${PYTHIA8}/lib" -Wl,-rpath,"${FASTJET3}/lib" \
  -o "${OUT}/scalar_h2_recast"
sha256sum "${OUT}/scalar_h2_recast" > "${OUT}/scalar_h2_recast.sha256"
echo "${OUT}/scalar_h2_recast"
