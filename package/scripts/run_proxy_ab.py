#!/usr/bin/env python3
"""Run the paper-anchored A/B sensitivity proxy."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


HBARC_GEV_MM = 1.973269804e-13


def load_scan(path: Path, max_points: int) -> list[dict]:
    points = []
    with path.open(encoding="utf-8", newline="") as handle:
        for i, row in enumerate(csv.DictReader(handle)):
            if len(points) >= max_points:
                break
            try:
                if all(k in row for k in ("positivity_ok", "unitarity_ok", "perturbativity_ok")):
                    if not all(float(row[k]) > 0.5 for k in ("positivity_ok", "unitarity_ok", "perturbativity_ok")):
                        continue
                width = float(row["total_width"])
                if width <= 0:
                    continue
                points.append(
                    {
                        "point_id": row.get("point_id") or f"scan_row_{i}",
                        "mass_gev": float(row["m_phi"]),
                        "ctau_mm": HBARC_GEV_MM / width,
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
    return points


def nearest_anchor(point: dict, anchors: list[dict]) -> dict:
    """Nearest neighbour in mass and log10(ctau); intentionally transparent."""
    import math

    m = float(point["mass_gev"])
    ct = max(float(point["ctau_mm"]), 1e-30)
    return min(
        anchors,
        key=lambda a: abs(m - float(a["mass_gev"])) / 100.0
        + abs(math.log10(ct) - math.log10(float(a["ctau_mm"]))),
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Paper Table-II A/B proxy; not an exclusion")
    ap.add_argument("--config", type=Path, default=Path("configs/ab_scenarios.json"))
    ap.add_argument("--scan-csv", type=Path)
    ap.add_argument("--max-scan-points", type=int, default=200)
    ap.add_argument("--out-csv", type=Path, default=Path("results/ab_proxy.csv"))
    ap.add_argument("--out-md", type=Path, default=Path("results/ab_summary.md"))
    args = ap.parse_args()

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    anchors = cfg["benchmarks"]
    points = load_scan(args.scan_csv, args.max_scan_points) if args.scan_csv else anchors
    lumi = float(cfg["luminosity_fb_inv"])
    n_anchor = float(cfg["exclusion_event_anchor"])

    rows = []
    summary_rows = []
    for point in points:
        anchor = nearest_anchor(point, anchors)
        source = "paper_table_II_direct" if point in anchors else f"nearest:{anchor['point_id']}"
        for mode, key in (("A_original", "eff_original"), ("B_modified", "eff_modified")):
            eff = float(anchor[key])
            sigma_for_anchor = n_anchor / (lumi * eff)
            summary_rows.append(
                {
                    "point_id": point["point_id"],
                    "mass_gev": point["mass_gev"],
                    "ctau_mm": point["ctau_mm"],
                    "analysis": mode,
                    "efficiency_proxy": eff,
                    "sigma_fb_for_3_events": sigma_for_anchor,
                    "efficiency_source": source,
                }
            )
            for sigma in cfg["cross_sections_fb"]:
                rows.append(
                    {
                        **summary_rows[-1],
                        "sigma_assumed_fb": float(sigma),
                        "expected_events": lumi * float(sigma) * eff,
                        "quality_flag": cfg["quality_flag"],
                    }
                )

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else []
    with args.out_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# A/B proxy anclado a Table II",
        "",
        "**PAPER_TABLE_PROXY_NOT_EXCLUSION.** Las eficiencias incluyen la mezcla de decaimientos del paper; no multiplicar nuevamente por BR.",
        "",
        "| Punto | m [GeV] | ctau [mm] | Análisis | eficiencia | sigma para 3 eventos [fb] | fuente |",
        "|---|---:|---:|---|---:|---:|---|",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['point_id']} | {float(row['mass_gev']):.1f} | {float(row['ctau_mm']):.3g} | "
            f"{row['analysis']} | {float(row['efficiency_proxy']):.3g} | "
            f"{float(row['sigma_fb_for_3_events']):.3g} | {row['efficiency_source']} |"
        )
    args.out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] wrote {args.out_csv}")
    print(f"[OK] wrote {args.out_md}")
    print("[NOTE] Paper-table proxy only; not an exclusion or local detector simulation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
