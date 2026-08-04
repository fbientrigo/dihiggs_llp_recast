#!/usr/bin/env python3
"""Build results/toy_cutflow_ab_repaired.csv from the A/B logs of every lifetime mode.

AB_RECAST_INFRASTRUCTURE_TEST / TOY_LIFETIME_PLUMBING_TEST.
Synthetic LHE input: these columns show that the analysis wiring and the lifetime
propagation work. They are not efficiencies, acceptances or exclusions.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

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
    values: dict[str, float] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        for key, label in STAGES:
            if label.strip() not in line or line.strip().startswith("High-pT"):
                continue
            m = NUMBER.search(line)
            if m:
                values[key] = float(m.group(1))
    return values


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results", type=Path, default=Path("results"))
    ap.add_argument("--out", type=Path, default=Path("results/toy_cutflow_ab_repaired.csv"))
    args = ap.parse_args()

    # column label -> log file
    cols = {
        "A_original_baseline": args.results / "cpp_A_original.log",
        "B_modified_baseline": args.results / "cpp_B_modified.log",
        "A_original_setlifetime": args.results / "cpp_A_original_setlifetime.log",
        "B_modified_setlifetime": args.results / "cpp_B_modified_setlifetime.log",
        "A_original_staged": args.results / "cpp_A_original_staged.log",
        "B_modified_staged": args.results / "cpp_B_modified_staged.log",
    }
    data = {name: parse_log(p) for name, p in cols.items()}
    missing = [n for n, d in data.items() if not d]
    if missing:
        raise SystemExit(f"[FAIL] no cutflow parsed for: {missing}")

    order = list(cols)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["stage"] + order + ["label"])
        for key, _ in STAGES:
            w.writerow([key] + [data[n].get(key, "") for n in order]
                       + ["AB_RECAST_INFRASTRUCTURE_TEST"])
    print(f"[OK] wrote {args.out}")

    # Report the A/B relation for each lifetime mode.
    for lt in ("baseline", "setlifetime", "staged"):
        a = data[f"A_original_{lt}"]
        b = data[f"B_modified_{lt}"]
        ja, jb = a["trackless_jet_selection_pct"], b["trackless_jet_selection_pct"]
        acc_a, acc_b = a["trackless_acc_pct"], b["trackless_acc_pct"]
        rel = "looser-or-equal" if jb >= ja else "TIGHTER (unexpected)"
        print(f"  {lt:12s} jet_sel A={ja:6.2f}% B={jb:6.2f}% -> B {rel};"
              f" Trackless Acc A={acc_a:6.2f}% B={acc_b:6.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
