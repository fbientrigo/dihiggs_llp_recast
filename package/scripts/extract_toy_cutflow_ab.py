#!/usr/bin/env python3
"""Extract Trackless cutflows from the A/B recast logs into a single CSV.

TOY_LHE_PLUMBING_TEST: the inputs are synthetic LHE events, so the numbers below
describe code-path connectivity only. They are not a physics measurement and must
not be read as an efficiency, an acceptance or an exclusion.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

# Ordered Trackless cutflow stages exactly as printed by recast_2301_13866.
STAGES = [
    ("all_events", "All Events: "),
    ("trackless_jet_selection_pct", "Trackless Jet Selection [%]: "),
    ("trackless_fiducial_pct", "Trackless Fiducial [%]: "),
    ("trackless_rvertex_gt_4mm_pct", "Trackless R_vertex > 4 mm [%]: "),
    ("trackless_track_d0_gt_2mm_pct", "Trackless Have track with |d_0| > 2 mm [%]: "),
    ("trackless_selected_decay_products_ge_5_pct", "Trackless Selected Decay Product >= 5 [%]: "),
    ("trackless_invariant_mass_gt_10gev_pct", "Trackless Invariant Mass > 10 GeV [%]: "),
    ("trackless_acc_pct", "Trackless Acc [%]: "),
    ("trackless_acc_x_eff_pct", "Trackless Acc x Eff [%]: "),
]

NUMBER = re.compile(r"([-+]?\d+\.?\d*[eE][-+]?\d+|[-+]?\d+\.?\d*)\s*$")


def parse_log(path: Path) -> dict[str, float]:
    """Map stage key -> value. Labels are printed with setw(50), so match on the label text."""
    values: dict[str, float] = {}
    text = path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        for key, label in STAGES:
            if label.strip() not in line:
                continue
            # Skip the High-pT variants: their labels start with "High-pT".
            if line.strip().startswith("High-pT"):
                continue
            match = NUMBER.search(line)
            if match:
                values[key] = float(match.group(1))
    return values


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--log-a", type=Path, default=Path("results/cpp_A_original.log"))
    ap.add_argument("--log-b", type=Path, default=Path("results/cpp_B_modified.log"))
    ap.add_argument("--out", type=Path, default=Path("results/toy_cutflow_ab.csv"))
    args = ap.parse_args()

    a = parse_log(args.log_a)
    b = parse_log(args.log_b)

    missing = [k for k, _ in STAGES if k not in a or k not in b]
    if missing:
        raise SystemExit(f"[FAIL] stages absent from logs, refusing to write: {missing}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["stage", "A_original", "B_modified", "B_minus_A", "label"])
        for key, _ in STAGES:
            w.writerow([key, a[key], b[key], round(b[key] - a[key], 10), "TOY_LHE_PLUMBING_TEST"])

    print(f"[OK] wrote {args.out}")
    print("[NOTE] TOY_LHE_PLUMBING_TEST: synthetic LHE; connectivity only, not an exclusion.")
    if a["trackless_acc_x_eff_pct"] == 0.0 and b["trackless_acc_x_eff_pct"] == 0.0:
        print("[WARN] Trackless Acc x Eff is 0 in BOTH modes: no displaced vertex survived.")
        print("[WARN] The displaced-vertex branch of the recast is NOT exercised by this toy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
