#!/usr/bin/env bash
# Canonical post-merge reproduction command chain for the R8
# H2-model-derived 4b physical DV+jets recast
# (results/r8_h2_model_derived_4b/).
#
# This is the canonical post-merge reproduction command chain. The original
# PR #6 artifacts were independently hash- and arithmetic-verified before
# merge; this script is not claimed to be the literal shell history of that
# original cloud execution, but running it end to end (without
# --verify-existing) reproduces the same committed artifacts from the same
# canonical inputs, and running it with --verify-existing validates the
# committed artifacts in place without repeating the expensive numerical
# jobs.
#
# Usage:
#   scripts/run_r8_reproduction.sh                 full chain: fetch LHE,
#                                                    relabel, compile, run
#                                                    Pythia/recast twice,
#                                                    rebuild all derived
#                                                    artifacts, then verify
#   scripts/run_r8_reproduction.sh --verify-existing
#                                                    validate the already-
#                                                    committed artifacts
#                                                    only; does not fetch,
#                                                    compile, or run Pythia
#   scripts/run_r8_reproduction.sh --regenerate-inputs-only
#                                                    focused, toolchain-free
#                                                    mode: fetch/verify both
#                                                    canonical LHE inputs,
#                                                    deterministically
#                                                    relabel them, verify
#                                                    the result's content
#                                                    identity against the
#                                                    committed provenance,
#                                                    then compare a fresh
#                                                    artifact manifest
#                                                    against the preserved
#                                                    reference. Never
#                                                    compiles or runs the
#                                                    recast/geometry driver.
#   scripts/run_r8_reproduction.sh --check-manifest-scratch
#                                                    focused test of the
#                                                    reference-manifest
#                                                    scratch-dir mechanism
#                                                    alone: snapshot, then
#                                                    regenerate + compare
#                                                    against the already-
#                                                    committed result tree
#                                                    unchanged. Fetches
#                                                    nothing and touches no
#                                                    result file.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

RESULTS_DIR="results/r8_h2_model_derived_4b"
CARDS_DIR="cards/r8_h2_model_derived_4b"
DATA_DIR="data/raw/r8_h2_model_derived_4b"
CACHE_DIR="${DATA_DIR}"
TOOLCHAIN="${TOOLCHAIN_ENV:-${ROOT}/configs/toolchain.env}"
EXECUTABLE="results/upstream_build_patched/analysis/recast_2301_13866"
GEOMETRY_BIN="${RESULTS_DIR}/bin/r8_geometry_driver"

# Provenance recorded in results/r8_h2_model_derived_4b/input_manifest.json.
HEP_CROSS_REPO="fbientrigo/dihiggs_hep_cross"
HEP_CROSS_COMMIT="5914ac2cfa0509eb957ba3ff111238b725c20861"
RUN01_CANONICAL_PATH="artifacts/h2_first_physical/madgraph/run_01/unweighted_events.lhe.gz"
RUN02_CANONICAL_PATH="artifacts/h2_first_physical/madgraph/run_02/unweighted_events.lhe.gz"
RUN01_SHA256="1c580b7a590f9bbfbf213eeef0e54fdcc4b6c1dce3f13bc0ed5278f6f3aec202"
RUN02_SHA256="385faebf45403c224ce374488c3e51a06be56b13ec6b095f92393d0c8f4b1bfa"

MODE="full"
for arg in "$@"; do
  case "${arg}" in
    --verify-existing) MODE="verify" ;;
    --regenerate-inputs-only) MODE="regenerate-inputs" ;;
    --check-manifest-scratch) MODE="check-manifest-scratch" ;;
    -h|--help)
      sed -n '2,46p' "${BASH_SOURCE[0]}"
      exit 0
      ;;
    *)
      echo "[ERROR] unknown argument: ${arg}" >&2
      exit 2
      ;;
  esac
done

step() { printf '\n=== %s ===\n' "$1"; }

sha256_check() {
  local path="$1" expected="$2" actual
  actual="$(sha256sum "${path}" | awk '{print $1}')"
  if [[ "${actual}" != "${expected}" ]]; then
    echo "[ERROR] sha256 mismatch for ${path}: got ${actual}, expected ${expected}" >&2
    exit 3
  fi
  echo "[OK] ${path} sha256 = ${actual}"
}

count_events() {
  zcat "$1" | grep -c '</event>'
}

verify_event_count() {
  local path="$1" expected="$2" n
  n="$(count_events "${path}")"
  if [[ "${n}" != "${expected}" ]]; then
    echo "[ERROR] ${path} has ${n} events, expected ${expected}" >&2
    exit 4
  fi
  echo "[OK] ${path} has ${n} events"
}

# --------------------------------------------------------------------------
if [[ "${MODE}" == "verify" ]]; then
  step "Validate committed artifacts (--verify-existing; no Pythia/recast run)"
  exec python3 scripts/verify_r8_artifacts.py
fi

# --------------------------------------------------------------------------
# The reference manifest snapshot must live outside RESULTS_DIR: anything
# under RESULTS_DIR is recursively hashed into the fresh manifest by
# build_r8_artifact_manifest.py, so a snapshot placed inside that tree would
# itself become a tracked artifact -- and then be reported "missing" once
# cleaned up, or "unexpectedly new" if left behind. A scratch directory
# under $TMPDIR (or /tmp), removed on every exit path via `trap`, keeps the
# snapshot fully outside the walked tree and guarantees it never leaks.
SCRATCH_DIR="$(mktemp -d "${TMPDIR:-/tmp}/r8-reproduction.XXXXXX")"
REFERENCE_MANIFEST="${SCRATCH_DIR}/artifact_manifest.reference.json"
cleanup() {
  rm -rf "${SCRATCH_DIR}"
}
trap cleanup EXIT INT TERM

step "1/15 Snapshot the previously committed reference manifest (outside RESULTS_DIR)"
if [[ -f "${RESULTS_DIR}/artifact_manifest.json" ]]; then
  cp "${RESULTS_DIR}/artifact_manifest.json" "${REFERENCE_MANIFEST}"
  echo "[OK] preserved the committed manifest for post-run comparison (${REFERENCE_MANIFEST}, outside ${RESULTS_DIR})"
else
  echo "[INFO] no committed artifact_manifest.json found; nothing to compare the fresh run against"
fi
# Also preserve the two input_checksums.txt files' actual content (not just
# their hash, which the manifest above already carries): compare_r8_manifests.py
# needs the reference *content* to confirm that only the LHE line differs on a
# fresh run, rather than silently accepting a change to the recast-executable
# or card line too.
for run in 01 02; do
  src="${RESULTS_DIR}/run_${run}/input_checksums.txt"
  if [[ -f "${src}" ]]; then
    cp "${src}" "${SCRATCH_DIR}/run_${run}_input_checksums.reference.txt"
  fi
done

if [[ "${MODE}" == "check-manifest-scratch" ]]; then
  step "Regenerate the artifact manifest from the untouched committed result tree and compare"
  python3 scripts/build_r8_artifact_manifest.py
  if [[ -f "${REFERENCE_MANIFEST}" ]]; then
    python3 scripts/compare_r8_manifests.py "${REFERENCE_MANIFEST}" "${RESULTS_DIR}/artifact_manifest.json"
  fi
  echo "[OK] --check-manifest-scratch complete: reference manifest lived outside ${RESULTS_DIR} throughout."
  exit 0
fi

step "2/15 Fetch or locate both canonical LHE inputs"
mkdir -p "${CACHE_DIR}"
fetch_lhe() {
  local run="$1" canonical_path="$2" expected_sha="$3" dest="$4"
  if [[ -f "${dest}" ]]; then
    echo "[INFO] using existing ${dest}"
  else
    local url="https://raw.githubusercontent.com/${HEP_CROSS_REPO}/${HEP_CROSS_COMMIT}/${canonical_path}"
    echo "[INFO] fetching ${url}"
    curl -fsSL -o "${dest}" "${url}"
  fi
}
fetch_lhe run_01 "${RUN01_CANONICAL_PATH}" "${RUN01_SHA256}" "${CACHE_DIR}/canonical_run_01.lhe.gz"
fetch_lhe run_02 "${RUN02_CANONICAL_PATH}" "${RUN02_SHA256}" "${CACHE_DIR}/canonical_run_02.lhe.gz"

step "3/15 Verify SHA-256 of both canonical LHE inputs"
sha256_check "${CACHE_DIR}/canonical_run_01.lhe.gz" "${RUN01_SHA256}"
sha256_check "${CACHE_DIR}/canonical_run_02.lhe.gz" "${RUN02_SHA256}"

step "4/15 Verify 1000 events per canonical LHE input"
verify_event_count "${CACHE_DIR}/canonical_run_01.lhe.gz" 1000
verify_event_count "${CACHE_DIR}/canonical_run_02.lhe.gz" 1000

step "5/15 PDG relabel (9000006 -> 35), atomic publish on validation pass only"
python3 scripts/relabel_lhe_pdg.py \
  "${CACHE_DIR}/canonical_run_01.lhe.gz" "${DATA_DIR}/relabelled_run_01.lhe.gz" \
  --from-pdg 9000006 --to-pdg 35 --expected-events 1000 --expected-relabelled 2000
python3 scripts/relabel_lhe_pdg.py \
  "${CACHE_DIR}/canonical_run_02.lhe.gz" "${DATA_DIR}/relabelled_run_02.lhe.gz" \
  --from-pdg 9000006 --to-pdg 35 --expected-events 1000 --expected-relabelled 2000

if [[ "${MODE}" == "regenerate-inputs" ]]; then
  step "Verify LHE content identity against the committed provenance (no recast run)"
  python3 scripts/verify_r8_artifacts.py --only canonical_lhe_hashes,relabel_script_hash,lhe_content_identity

  step "Regenerate artifact manifest and compare against the preserved reference"
  python3 scripts/build_r8_artifact_manifest.py
  if [[ -f "${REFERENCE_MANIFEST}" ]]; then
    python3 scripts/compare_r8_manifests.py "${REFERENCE_MANIFEST}" "${RESULTS_DIR}/artifact_manifest.json"
  fi
  echo "[OK] --regenerate-inputs-only complete: canonical LHE -> deterministic relabel -> content"
  echo "     hash -> gzip hash -> checksum-artifact consistency -> manifest comparison, all"
  echo "     without compiling or running the recast/geometry driver."
  exit 0
fi

step "6/15 Bootstrap and verify the locked upstream revision"
# build_patched_upstream.sh only checks that the submodule working tree is
# clean, not that it is checked out at configs/upstream.lock.json's pinned
# commit: a clean-but-wrong revision would otherwise build and report
# results from the wrong upstream physics code without any error. Bootstrap
# (sync + checkout the locked commit) and then verify it explicitly first.
./scripts/bootstrap_upstream.sh
python3 scripts/check_upstream_layout.py --root external/recastingCodes

step "7/15 Compile the patched upstream recast (recast_2301_13866)"
./scripts/build_patched_upstream.sh

step "8/15 Compile r8_geometry_driver"
[[ -f "${TOOLCHAIN}" ]] || {
  echo "[ERROR] Missing ${TOOLCHAIN}. Copy configs/toolchain.env.example and edit it." >&2
  exit 5
}
# shellcheck disable=SC1090
source "${TOOLCHAIN}"
: "${PYTHIA8:?PYTHIA8 must be defined in the toolchain file}"
: "${FASTJET3:?FASTJET3 must be defined in the toolchain file}"
CXX="${CXX:-g++}"
mkdir -p "${RESULTS_DIR}/bin"
"${CXX}" -std=c++17 -O2 \
  $("${PYTHIA8}/bin/pythia8-config" --cxxflags) \
  $("${FASTJET3}/bin/fastjet-config" --cxxflags) \
  src/r8_geometry_driver.cc -o "${GEOMETRY_BIN}" \
  $("${PYTHIA8}/bin/pythia8-config" --libs) \
  $("${FASTJET3}/bin/fastjet-config" --libs)
[[ -x "${GEOMETRY_BIN}" ]] || { echo "[ERROR] geometry driver build completed without executable." >&2; exit 6; }
echo "[OK] built ${GEOMETRY_BIN}"

run_recast() {
  local run="$1"
  local run_dir="${RESULTS_DIR}/run_${run}"
  local cmnd="${CARDS_DIR}/physical_run_${run}.cmnd"
  local lhe="${DATA_DIR}/relabelled_run_${run}.lhe.gz"
  mkdir -p "${run_dir}"
  {
    echo "# Canonical post-merge reproduction command chain:"
    echo "#   scripts/run_r8_reproduction.sh"
    echo "#   scripts/run_r8_reproduction.sh --verify-existing"
    echo "pwd=${ROOT}"
    printf '%q ' "${EXECUTABLE}" "${cmnd}"
    printf '\n'
  } | tee "${run_dir}/command.txt"
  {
    python3 scripts/print_checksums_header.py "${run}"
    sha256sum "${EXECUTABLE}" "${cmnd}" "${lhe}"
  } | tee "${run_dir}/input_checksums.txt"
  "${EXECUTABLE}" "${cmnd}" 2>&1 | tee "${run_dir}/recast.log"
}

run_geometry() {
  local run="$1"
  local run_dir="${RESULTS_DIR}/run_${run}"
  local cmnd="${CARDS_DIR}/physical_run_${run}.cmnd"
  "${GEOMETRY_BIN}" "${cmnd}" 1000 "${run_dir}/geometry.csv" 2>&1 | tee "${run_dir}/geometry_driver.log"
}

step "9/15 Run recast run_01"
run_recast 01

step "10/15 Run geometry run_01"
run_geometry 01

step "11/15 Run recast run_02"
run_recast 02

step "12/15 Run geometry run_02"
run_geometry 02

step "13/15 Parse cutflows, generate geometry summaries, compatibility and normalization results"
python3 scripts/build_r8_results.py

step "14/15 Generate artifact manifest and compare against the preserved reference"
python3 scripts/build_r8_artifact_manifest.py
if [[ -f "${REFERENCE_MANIFEST}" ]]; then
  python3 scripts/compare_r8_manifests.py "${REFERENCE_MANIFEST}" "${RESULTS_DIR}/artifact_manifest.json"
else
  echo "[WARN] no reference manifest was available; this run's manifest was not compared against a prior committed state."
fi
# REFERENCE_MANIFEST and SCRATCH_DIR are removed by the EXIT trap below,
# regardless of whether the remaining steps succeed.

step "15/15 Verify all hashes"
python3 scripts/verify_r8_artifacts.py

echo
echo "[OK] R8 reproduction chain complete."
