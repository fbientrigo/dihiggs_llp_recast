#!/usr/bin/env python3
"""Audit whether scan points resemble the hadronic DV+jets topology.

This script does not correct efficiencies. It only produces transparent screening
features and warnings before applying the paper-table nearest-neighbour proxy.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def f(row: dict[str, str], key: str) -> float:
    try:
        return max(0.0, float(row.get(key, "0") or 0.0))
    except (TypeError, ValueError):
        return 0.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("scan_csv", type=Path)
    ap.add_argument("--output", type=Path, default=Path("results/scan_topology_audit.csv"))
    args = ap.parse_args()

    out_rows: list[dict[str, object]] = []
    with args.scan_csv.open(encoding="utf-8", newline="") as handle:
        for i, row in enumerate(csv.DictReader(handle)):
            total = f(row, "total_width")
            if total <= 0:
                continue
            widths = {k: f(row, k) for k in (
                "width_bb", "width_tautau", "width_WW", "width_ZZ",
                "width_gaga", "width_Zga", "width_gg", "width_hh",
            )}
            hadronic_parent = widths["width_bb"] + widths["width_gg"] + widths["width_WW"] + widths["width_ZZ"]
            photonic = widths["width_gaga"] + widths["width_Zga"]
            tau = widths["width_tautau"]
            hh = widths["width_hh"]
            had_frac = hadronic_parent / total
            photon_frac = photonic / total
            tau_frac = tau / total
            hh_frac = hh / total

            if photon_frac >= 0.5:
                level = "LOW"
                warning = "photon-dominated; paper DV+jets efficiency is not transferable"
            elif had_frac >= 0.8:
                level = "HIGH"
                warning = "topology screening only; still requires event simulation"
            elif had_frac >= 0.5:
                level = "MEDIUM"
                warning = "mixed topology; nearest paper efficiency is weakly justified"
            else:
                level = "LOW"
                warning = "non-hadronic or unaccounted decays dominate"

            out_rows.append({
                "row_index": i,
                "point_id": row.get("point_id") or f"scan_row_{i}",
                "m_phi": row.get("m_phi", ""),
                "total_width": total,
                "hadronic_parent_fraction": had_frac,
                "photon_fraction": photon_frac,
                "tau_fraction": tau_frac,
                "hh_fraction": hh_frac,
                "dv_jets_topology_screen": level,
                "warning": warning,
            })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(out_rows[0]) if out_rows else ["row_index", "warning"]
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(out_rows)

    counts = {level: sum(r.get("dv_jets_topology_screen") == level for r in out_rows) for level in ("HIGH", "MEDIUM", "LOW")}
    print(f"[OK] wrote {args.output} ({len(out_rows)} points)")
    print(f"[SCREEN] HIGH={counts['HIGH']} MEDIUM={counts['MEDIUM']} LOW={counts['LOW']}")
    print("[NOTE] Screening flag only; no detector efficiency or BR correction was applied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
