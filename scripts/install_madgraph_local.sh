#!/usr/bin/env bash
set -euo pipefail

VERSION=""
EXPECTED_COMMIT=""
PREFIX=""
SOURCE_URL="https://github.com/mg5amcnlo/mg5amcnlo.git"
DRY_RUN=0

usage() {
  echo "usage: $0 --version VERSION --git-commit COMMIT [--prefix DIR] [--dry-run]"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version) VERSION="${2:?missing version}"; shift 2 ;;
    --git-commit) EXPECTED_COMMIT="${2:?missing commit}"; shift 2 ;;
    --prefix) PREFIX="${2:?missing prefix}"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
done

[[ "${VERSION}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || {
  echo "[ERROR] --version must be an explicit x.y.z release" >&2
  exit 2
}
[[ "${EXPECTED_COMMIT}" =~ ^[0-9a-fA-F]{40}$ ]] || {
  echo "[ERROR] --git-commit must be an explicit 40-character commit" >&2
  exit 2
}

EXPECTED_COMMIT="${EXPECTED_COMMIT,,}"
PREFIX="${PREFIX:-${HOME}/.local/mg5amcnlo/${VERSION}}"
REPO_ROOT="$(realpath "$(dirname "${BASH_SOURCE[0]}")/..")"
PREFIX="$(realpath -m "${PREFIX}")"
METADATA="${PREFIX}/.dvrecast-install"

[[ "${PREFIX}" != "${REPO_ROOT}" && "${PREFIX}" != "${REPO_ROOT}/"* ]] || {
  echo "[ERROR] Installation prefix must be outside the repository: ${PREFIX}" >&2
  exit 2
}

if [[ -e "${PREFIX}" ]]; then
  if [[ -x "${PREFIX}/bin/mg5_aMC" && -f "${METADATA}" ]] \
    && grep -Fxq "version=${VERSION}" "${METADATA}" \
    && grep -Fxq "git_commit=${EXPECTED_COMMIT}" "${METADATA}"; then
    echo "[OK] Matching installation already exists at ${PREFIX}"
    exit 0
  fi
  echo "[ERROR] Refusing to overwrite nonmatching installation: ${PREFIX}" >&2
  exit 3
fi

echo "version=${VERSION}"
echo "source_url=${SOURCE_URL}"
echo "git_commit=${EXPECTED_COMMIT}"
echo "prefix=${PREFIX}"
if [[ ${DRY_RUN} -eq 1 ]]; then
  echo "[DRY-RUN] Would clone, verify, and probe MadGraph."
  exit 0
fi

for command in git python3 gcc gfortran; do
  command -v "${command}" >/dev/null || {
    echo "[ERROR] Required command not found: ${command}" >&2
    exit 4
  }
done
python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 7))' || {
  echo "[ERROR] MadGraph 3.5.3 requires Python 3.7 or newer" >&2
  exit 4
}
SIX_VERSION="$(python3 -c 'import six; print(six.__version__)')" || {
  echo "[ERROR] MadGraph 3.5.3 requires the Python six module" >&2
  exit 4
}

mkdir -p "$(dirname "${PREFIX}")"
STAGE="$(mktemp -d "${PREFIX}.tmp.XXXXXX")"
cleanup() { rm -rf "${STAGE}"; }
trap cleanup EXIT

git clone --depth 1 --branch "v${VERSION}" --no-tags "${SOURCE_URL}" "${STAGE}/install"
ACTUAL_COMMIT="$(git -C "${STAGE}/install" rev-parse HEAD)"
[[ "${ACTUAL_COMMIT}" == "${EXPECTED_COMMIT}" ]] || {
  echo "[ERROR] Git commit mismatch: expected ${EXPECTED_COMMIT}, got ${ACTUAL_COMMIT}" >&2
  exit 5
}
[[ -x "${STAGE}/install/bin/mg5_aMC" ]] || {
  echo "[ERROR] Checkout does not contain executable bin/mg5_aMC" >&2
  exit 6
}
"${STAGE}/install/bin/mg5_aMC" --help >/dev/null
echo ".dvrecast-install" >>"${STAGE}/install/.git/info/exclude"
{
  echo "version=${VERSION}"
  echo "source_url=${SOURCE_URL}"
  echo "git_commit=${ACTUAL_COMMIT}"
  echo "git_tag=v${VERSION}"
  echo "git_dirty=$(test -n "$(git -C "${STAGE}/install" status --porcelain)" && echo true || echo false)"
  echo "installed_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "python=$(python3 --version 2>&1)"
  echo "six=${SIX_VERSION}"
  echo "gcc=$(gcc --version | head -n1)"
  echo "gfortran=$(gfortran --version | head -n1)"
} >"${STAGE}/install/.dvrecast-install"
mv "${STAGE}/install" "${PREFIX}"
echo "[OK] Installed MadGraph ${VERSION} at ${PREFIX}"
