#!/usr/bin/env bash
# Drive one MadGraph strong-bm1 multiplicity generation (pilot or production).
# Usage: run_strong_bm1_mg5.sh <mult:0|1|2> <nevents> <seed> <run_name> <workdir>
set -euo pipefail

MULT="${1:?mult 0|1|2}"
NEVENTS="${2:?nevents}"
SEED="${3:?seed}"
RUN_NAME="${4:?run_name}"
WORKDIR="${5:?workdir}"

REPO_ROOT="$(realpath "$(dirname "${BASH_SOURCE[0]}")/..")"
MG5_BIN="${MG5_BIN:-mg5_aMC}"
PROC_CARD="${REPO_ROOT}/benchmarks/upstream/strong-bm1/cards/source/pp2gogo_${MULT}_proc_card_mg5.dat"
RUN_CARD="${REPO_ROOT}/benchmarks/upstream/strong-bm1/cards/source/run_card.dat"
SLHA="${REPO_ROOT}/benchmarks/upstream/strong-bm1/cards/generated/GG_qqn1_2000_850_rpvLF_p01ns.slha"
PROC_DIR="${WORKDIR}/pp2gogo_${MULT}"

mkdir -p "${WORKDIR}"

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export MPLCONFIGDIR="${WORKDIR}/.cache/matplotlib"
mkdir -p "${MPLCONFIGDIR}"

if [[ ! -d "${PROC_DIR}" ]]; then
  SCRIPT="${WORKDIR}/mg5_output_${MULT}.cmd"
  # Reuse the pinned proc card verbatim, but redirect output into our workdir.
  sed "s#^output pp2gogo_${MULT}#output ${PROC_DIR}#" "${PROC_CARD}" > "${SCRIPT}"
  "${MG5_BIN}" "${SCRIPT}"
fi

cp "${RUN_CARD}" "${PROC_DIR}/Cards/run_card.dat"
cp "${SLHA}" "${PROC_DIR}/Cards/param_card.dat"

sed -i -E "s/^[[:space:]]*[0-9]+[[:space:]]*=[[:space:]]*nevents/  ${NEVENTS} = nevents/" "${PROC_DIR}/Cards/run_card.dat"
sed -i -E "s/^[[:space:]]*[0-9]+[[:space:]]*=[[:space:]]*iseed/  ${SEED} = iseed/" "${PROC_DIR}/Cards/run_card.dat"

LAUNCH_SCRIPT="${WORKDIR}/launch_${MULT}.cmd"
cat > "${LAUNCH_SCRIPT}" << EOF
launch ${PROC_DIR} -n ${RUN_NAME}
0
EOF

"${MG5_BIN}" "${LAUNCH_SCRIPT}"
