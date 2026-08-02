#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BENCHMARK=""
DRY_RUN=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --benchmark) BENCHMARK="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    *) echo "Usage: $0 --benchmark strong-bm1 [--dry-run]" >&2; exit 2 ;;
  esac
done
[[ "$BENCHMARK" == strong-bm1 && "$DRY_RUN" == 1 ]] || {
  echo "Only the blocked strong-bm1 dry-run is permitted" >&2; exit 2;
}
exec python3 "$ROOT/scripts/prepare_upstream_benchmark.py" --benchmark "$BENCHMARK" --dry-run
