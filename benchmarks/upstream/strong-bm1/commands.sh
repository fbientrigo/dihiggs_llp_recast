#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
INPUT_ROOT="${INPUT_ROOT:-$ROOT/results/upstream/strong-bm1}"
OUTPUT_ROOT="${OUTPUT_ROOT:-$INPUT_ROOT/plots}"
PLOT_SCRIPT="${PLOT_SCRIPT:-$ROOT/scripts/plot_strong_bm1.py}"

for required in "$INPUT_ROOT/cutflow.csv" "$INPUT_ROOT/cutflow.json" "$INPUT_ROOT/generation_summary.json" "$PLOT_SCRIPT"; do
  [[ -f "$required" ]] || { echo "missing required input: $required" >&2; exit 2; }
done

mkdir -p "$OUTPUT_ROOT"
export MPLCONFIGDIR="${MPLCONFIGDIR:-${TMPDIR:-/tmp}/strong-bm1-matplotlib}"
python3 "$PLOT_SCRIPT" --input-root "$INPUT_ROOT" --output-root "$OUTPUT_ROOT" --write-comparison-json
