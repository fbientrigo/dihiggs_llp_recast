#!/usr/bin/env bash
# Run the R4/R5 real-path smoke samples through the patched recast binary
# built by build_patched_upstream.sh: a default-PDG neutralino sample (must
# reproduce the unpatched binary's cutflow exactly) and an alternate-scalar
# sample (PDG 35), both generated internally by Pythia8 so they do not
# depend on the externally-blocked strong-bm1 LHE files.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXECUTABLE="${ROOT}/results/upstream_build_patched/analysis/recast_2301_13866"
OUT="${ROOT}/results/r4_smoke"

[[ -x "${EXECUTABLE}" ]] || {
  echo "[ERROR] Missing ${EXECUTABLE}. Run scripts/build_patched_upstream.sh first." >&2
  exit 2
}

mkdir -p "${OUT}"
RENDERED="${OUT}/cmnd"
mkdir -p "${RENDERED}"

for name in neutralino_regression scalar_regression; do
  sed "s#@@REPO_ROOT@@#${ROOT}#" "${ROOT}/cards/r4_smoke/${name}.cmnd" >"${RENDERED}/${name}.cmnd"
  "${EXECUTABLE}" "${RENDERED}/${name}.cmnd" >"${OUT}/${name}.stdout" 2>"${OUT}/${name}.stderr"
  echo "[OK] ${name}: ${OUT}/${name}.stdout"
done
