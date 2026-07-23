#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${TOOLCHAIN_ENV:-${ROOT}/configs/toolchain.env}"
LHE="${SCALAR_H2_LHE:?SCALAR_H2_LHE must point to the checksum-verified source LHE}"
OUT="${SCALAR_H2_OUT:-${ROOT}/results/scalar_h2_smoke}"
mkdir -p "${OUT}"
"${ROOT}/scripts/build_scalar_h2.sh" >/dev/null
"${ROOT}/build/scalar_h2_recast/scalar_h2_recast" \
  --lhe "${LHE}" --out "${OUT}/events.jsonl" --events "${SCALAR_H2_EVENTS:-100}" \
  --seed 900006005 --pdg 9000006 --mass 200 --ctau 1000 \
  --channel 5,-5:1 --is-resonance 0
