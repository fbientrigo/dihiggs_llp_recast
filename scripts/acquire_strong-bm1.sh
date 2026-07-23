#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    *) echo "Usage: $0 [--dry-run]" >&2; exit 2 ;;
  esac
done

if [[ "$DRY_RUN" != 1 ]]; then
  echo "BLOCKED_EXTERNAL_ARTIFACT: exact strong-bm1 SLHA and LHE inputs are unavailable" >&2
  exit 2
fi

exec python3 "$ROOT/scripts/prepare_upstream_benchmark.py" --benchmark strong-bm1 --dry-run
