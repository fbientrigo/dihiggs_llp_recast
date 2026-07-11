#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCK="${ROOT}/configs/upstream.lock.json"
DEST="${ROOT}/external/recastingCodes"

readarray -t LOCK_VALUES < <(python3 - "${LOCK}" <<'PY'
import json
import sys
from pathlib import Path

obj = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(obj["repository"])
print(obj["commit"])
PY
)
REPOSITORY="${LOCK_VALUES[0]}"
COMMIT="${LOCK_VALUES[1]}"

mkdir -p "$(dirname "${DEST}")"

if [[ ! -d "${DEST}/.git" ]]; then
  if [[ -e "${DEST}" ]]; then
    echo "[ERROR] ${DEST} exists but is not a Git checkout." >&2
    exit 2
  fi
  git clone --filter=blob:none --no-checkout "${REPOSITORY}" "${DEST}"
fi

if [[ -n "$(git -C "${DEST}" status --porcelain)" && "${BOOTSTRAP_FORCE:-0}" != "1" ]]; then
  echo "[ERROR] Upstream checkout is dirty. Set BOOTSTRAP_FORCE=1 only after reviewing changes." >&2
  exit 3
fi

git -C "${DEST}" remote set-url origin "${REPOSITORY}"
git -C "${DEST}" fetch --depth 1 origin "${COMMIT}"
git -C "${DEST}" checkout --detach --force "${COMMIT}"

ACTUAL="$(git -C "${DEST}" rev-parse HEAD)"
if [[ "${ACTUAL}" != "${COMMIT}" ]]; then
  echo "[ERROR] Expected ${COMMIT}, got ${ACTUAL}." >&2
  exit 4
fi

printf '[OK] upstream=%s\n[OK] commit=%s\n[OK] path=%s\n' "${REPOSITORY}" "${ACTUAL}" "${DEST}"
