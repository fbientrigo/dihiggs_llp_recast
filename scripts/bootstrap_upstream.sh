#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCK="${ROOT}/configs/upstream.lock.json"
DEST="${ROOT}/external/recastingCodes"

EXPECTED="$(python3 - "${LOCK}" <<'PY'
import json
import sys
from pathlib import Path

print(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["commit"])
PY
)"

cd "${ROOT}"
git submodule sync -- external/recastingCodes
git submodule update --init --recursive -- external/recastingCodes

if [[ -n "$(git -C "${DEST}" status --porcelain)" ]]; then
  echo "[ERROR] Upstream submodule is dirty; do not use it as a working tree." >&2
  exit 2
fi

ACTUAL="$(git -C "${DEST}" rev-parse HEAD)"
if [[ "${ACTUAL}" != "${EXPECTED}" ]]; then
  echo "[ERROR] Submodule mismatch: expected ${EXPECTED}, got ${ACTUAL}." >&2
  exit 3
fi

printf '[OK] commit=%s\n[OK] path=%s\n' "${ACTUAL}" "${DEST}"
