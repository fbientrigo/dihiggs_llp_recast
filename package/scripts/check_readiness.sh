#!/usr/bin/env bash
set -u

ok=0
warn=0
check_cmd() {
  local cmd="$1"
  if command -v "$cmd" >/dev/null 2>&1; then
    printf '[OK]   %-12s %s\n' "$cmd" "$(command -v "$cmd")"
  else
    printf '[MISS] %-12s not found\n' "$cmd"
    warn=$((warn+1))
  fi
}

printf '%s\n' '=== Stage 0: package tools ==='
check_cmd python3
check_cmd make

printf '%s\n' '=== Stage 1: recast stack ==='
check_cmd g++
check_cmd fastjet-config
check_cmd pythia8-config

printf '%s\n' '=== Stage 2: event generation ==='
check_cmd mg5_aMC
check_cmd Mathematica

if [[ -n "${UPSTREAM_ROOT:-}" && -d "${UPSTREAM_ROOT}" ]]; then
  printf '[OK]   UPSTREAM_ROOT %s\n' "$UPSTREAM_ROOT"
else
  printf '[MISS] UPSTREAM_ROOT is unset or not a directory\n'
  warn=$((warn+1))
fi

if [[ $warn -eq 0 ]]; then
  echo '[READY] All detectable components are present.'
else
  echo "[PARTIAL] $warn component(s) missing. Stage 0 may still run."
fi
exit 0
