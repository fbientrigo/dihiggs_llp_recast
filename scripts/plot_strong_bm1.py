#!/usr/bin/env python3
"""Generate the strong-bm1 validation figures from canonical JSON/CSV inputs."""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt

FIXED_DATE = datetime(2020, 1, 1, tzinfo=timezone.utc)
plt.rcParams["svg.hashsalt"] = "strong-bm1"
REQUIRED_CUTFLOW_COLUMNS = {
    "stage_id",
    "label",
    "our_weighted_events",
    "our_efficiency_pct",
    "authors_recast_efficiency_pct",
    "atlas_full_sim_pct",
    "atlas_parametric_pct",
}


def save_figure(figure: plt.Figure, path: Path) -> None:
    metadata = {
        "Creator": "plot_strong_bm1.py",
        "Title": path.stem,
    }
    if path.suffix == ".svg":
        metadata["Date"] = "2020-01-01T00:00:00"
    elif path.suffix == ".pdf":
        metadata["CreationDate"] = FIXED_DATE
    figure.savefig(path, bbox_inches="tight", metadata=metadata)


def load_rows(root: Path) -> list[dict[str, str]]:
    with (root / "cutflow.csv").open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_CUTFLOW_COLUMNS - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"cutflow.csv missing columns: {', '.join(sorted(missing))}")
        rows = list(reader)
    if not rows:
        raise ValueError("cutflow.csv has no stages")
    for row in rows:
        if (events := number(row, "our_weighted_events")) is None or events < 0:
            raise ValueError("cutflow.csv requires non-negative weighted events")
        for key in ("our_efficiency_pct", "authors_recast_efficiency_pct"):
            if (value := number(row, key)) is None:
                raise ValueError(f"cutflow.csv missing numeric {key!r}")
            if not 0 <= value <= 100:
                raise ValueError(f"cutflow.csv {key!r} must be within [0, 100]")
        for key in ("atlas_full_sim_pct", "atlas_parametric_pct"):
            if (value := number(row, key)) is not None and not 0 <= value <= 100:
                raise ValueError(f"cutflow.csv {key!r} must be within [0, 100]")
        row["our_pct"] = row["our_efficiency_pct"]
        row["authors_pct"] = row["authors_recast_efficiency_pct"]
    return rows


def number(row: dict[str, str], key: str) -> float | None:
    try:
        value = float(row[key]) if row[key] else None
    except ValueError as error:
        raise ValueError(f"invalid numeric {key!r}: {row[key]!r}") from error
    if value is not None and not math.isfinite(value):
        raise ValueError(f"non-finite numeric {key!r}")
    return value


def load_generation_summary(root: Path) -> dict[str, object]:
    data = json.loads((root / "generation_summary.json").read_text(encoding="utf-8"))
    merged = data.get("merged_cross_section")
    if not isinstance(merged, dict) or merged.get("unit") != "fb":
        raise ValueError("generation_summary.json must contain merged_cross_section in fb")
    for key in (
        "authors_recast",
        "our_reproduction",
        "absolute_difference",
        "relative_difference_pct",
    ):
        if not isinstance(merged.get(key), (int, float)) or not math.isfinite(merged[key]):
            raise ValueError(f"merged_cross_section.{key} must be numeric")
    if merged["authors_recast"] <= 0 or merged["our_reproduction"] <= 0:
        raise ValueError("merged cross sections must be positive")
    expected = (merged["our_reproduction"] / merged["authors_recast"] - 1) * 100
    if abs(merged["relative_difference_pct"] - expected) > 1e-8:
        raise ValueError("merged_cross_section relative difference is inconsistent")
    absolute = merged["our_reproduction"] - merged["authors_recast"]
    if abs(merged["absolute_difference"] - absolute) > 1e-8:
        raise ValueError("merged_cross_section absolute difference is inconsistent")
    reconciliation = data.get("unit_reconciliation")
    if not isinstance(reconciliation, dict):
        raise ValueError("generation_summary.json unit reconciliation is missing")
    source_values = reconciliation.get("source_value")
    if not isinstance(source_values, dict):
        raise ValueError("generation_summary.json source mb values are missing")
    pairs = (
        ("authors", merged["authors_recast"]),
        ("our_reproduction", merged["our_reproduction"]),
    )
    for source, fb in pairs:
        mb = source_values.get(source)
        if not isinstance(mb, (int, float)) or not math.isfinite(mb):
            raise ValueError(f"generation_summary.json source mb value for {source} is missing")
        if mb <= 0:
            raise ValueError(
                f"generation_summary.json source mb value for {source} must be positive"
            )
        if not math.isclose(mb * 1e12, fb, rel_tol=1e-10, abs_tol=1e-12):
            raise ValueError(
                f"generation_summary.json mb-to-fb conversion is inconsistent for {source}"
            )
    return data


def write_comparison(root: Path, rows: list[dict[str, str]]) -> None:
    data = {
        "schema_version": 1,
        "benchmark": "strong-bm1",
        "sources": {"our_reproduction": "cutflow.json", "authors_recast": "upstream reference log"},
        "stages": [
            {
                "id": row["stage_id"],
                "absolute_difference_pct": round(
                    number(row, "our_pct") - number(row, "authors_pct"), 10
                ),
                "relative_difference_pct": round(
                    (number(row, "our_pct") / number(row, "authors_pct") - 1) * 100, 10
                ),
                "ratio_our_over_authors": round(
                    number(row, "our_pct") / number(row, "authors_pct"), 10
                ),
            }
            for row in rows
        ],
        "uncertainty_status": (
            "No pull is reported: weighted sum-of-squares and author uncertainties are unavailable."
        ),
    }
    (root / "comparison.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_corrected_unit_interpretation(root: Path, summary: dict[str, object]) -> None:
    reconciliation = summary.get("unit_reconciliation")
    merged = summary["merged_cross_section"]
    if not isinstance(reconciliation, dict) or not isinstance(merged, dict):
        raise ValueError("generation_summary.json unit reconciliation is missing")
    source_values = reconciliation.get("source_value")
    if not isinstance(source_values, dict) or not isinstance(
        source_values.get("our_reproduction"), (int, float)
    ):
        raise ValueError("generation_summary.json source mb value is missing")
    fb = merged["our_reproduction"]
    corrected = {
        "source_file": summary["source_artifact"],
        "source_file_modified": False,
        "identified_issue": "unit label mismatch",
        "merged_inclusive_cross_section_mb": source_values["our_reproduction"],
        "merged_inclusive_cross_section_pb": fb / 1000,
        "merged_inclusive_cross_section_fb": fb,
    }
    (root / "generation_summary_interpretation_corrected.json").write_text(
        json.dumps(corrected, indent=2) + "\n", encoding="utf-8"
    )


def plot_cutflow(root: Path, out: Path, rows: list[dict[str, str]]) -> None:
    labels = [row["label"] for row in rows]
    x = list(range(len(labels)))
    fig, (upper, lower) = plt.subplots(
        2, 1, figsize=(10, 8), sharex=True, gridspec_kw={"height_ratios": [3, 2]}
    )
    for key, label, style in (
        ("atlas_full_sim_pct", "ATLAS full simulation", "o--"),
        ("atlas_parametric_pct", "ATLAS parametric", "s--"),
        ("authors_pct", "Authors' recast", "D-"),
        ("our_pct", "Our reproduction", "o-"),
    ):
        values = [number(row, key) for row in rows]
        upper.plot(
            x,
            [value if value is not None else float("nan") for value in values],
            style,
            label=label,
        )
    upper.set_ylabel("Efficiency / acceptance [%]")
    upper.set_title("strong-bm1 High-pT cutflow")
    upper.grid(axis="y", alpha=0.25)
    upper.legend(ncol=2)
    ratio = [number(row, "our_pct") / number(row, "authors_pct") for row in rows]
    lower.axhline(1.0, color="black", linewidth=0.8)
    lower.plot(x, ratio, "o-", color="tab:purple", label="Our / authors")
    lower.set_ylabel("Ratio")
    lower.set_ylim(min(ratio) - 0.002, max(ratio) + 0.002)
    lower.grid(axis="y", alpha=0.25)
    lower.legend()
    lower.set_xticks(x, labels, rotation=25, ha="right")
    fig.tight_layout()
    for suffix in ("png", "pdf", "svg"):
        save_figure(fig, out / f"strong_bm1_cutflow.{suffix}")
    plt.close(fig)


def plot_ratio(root: Path, out: Path, rows: list[dict[str, str]]) -> None:
    labels = [row["label"] for row in rows]
    x = list(range(len(labels)))
    fig, axis = plt.subplots(figsize=(10, 4.5))
    absolute = [number(row, "our_pct") - number(row, "authors_pct") for row in rows]
    relative = [(number(row, "our_pct") / number(row, "authors_pct") - 1) * 100 for row in rows]
    axis.bar(
        [value - 0.18 for value in x],
        absolute,
        width=0.36,
        label="Absolute difference [percentage points]",
    )
    axis.bar([value + 0.18 for value in x], relative, width=0.36, label="Relative difference [%]")
    axis.axhline(0, color="black", linewidth=0.8)
    axis.set_xticks(x, labels, rotation=25, ha="right")
    axis.set_ylabel("Difference")
    axis.set_title("strong-bm1 reproduction versus authors' recast")
    axis.grid(axis="y", alpha=0.25)
    axis.legend()
    fig.tight_layout()
    for suffix in ("png", "pdf"):
        save_figure(fig, out / f"strong_bm1_ratio.{suffix}")
    plt.close(fig)


def plot_cross_section(root: Path, out: Path) -> None:
    data = load_generation_summary(root)
    values = data["merged_cross_section"]
    fig, axis = plt.subplots(figsize=(6, 4.5))
    axis.bar(
        ["Authors' recast", "Our reproduction"],
        [values["authors_recast"], values["our_reproduction"]],
        color=["tab:gray", "tab:blue"],
    )
    axis.set_ylabel("Inclusive merged cross section [fb]")
    axis.set_title("strong-bm1 inclusive merged cross section")
    axis.text(
        0.5,
        max(values["authors_recast"], values["our_reproduction"]) * 0.98,
        f"Δ = {values['relative_difference_pct']:.3f}%",
        ha="center",
        va="top",
    )
    axis.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    for suffix in ("png", "pdf"):
        save_figure(fig, out / f"strong_bm1_cross_section.{suffix}")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, default=Path("results/upstream/strong-bm1"))
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--write-comparison-json", action="store_true")
    args = parser.parse_args()
    root = args.input_root.resolve()
    out = (args.output_root or root).resolve()
    out.mkdir(parents=True, exist_ok=True)
    rows = load_rows(root)
    summary = load_generation_summary(root)
    if args.write_comparison_json:
        write_comparison(root, rows)
        write_corrected_unit_interpretation(root, summary)
    plot_cutflow(root, out, rows)
    plot_ratio(root, out, rows)
    plot_cross_section(root, out)


if __name__ == "__main__":
    main()
