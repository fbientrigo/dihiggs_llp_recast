#!/usr/bin/env python3
"""Plot the distributed upstream strong-bm1 cutflow; this is not local reproduction."""

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent


def main() -> None:
    with (HERE / "reference_cutflow_upstream.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    labels = [row["label_es"] for row in rows]
    high_pt = [float(row["high_pt_percent"]) for row in rows]
    trackless = [float(row["trackless_percent"]) for row in rows]
    x = range(len(rows))

    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    fig.subplots_adjust(left=0.09, right=0.98, top=0.9, bottom=0.32)
    ax.plot(x, high_pt, "o-", linewidth=2.2, label="Región high-$p_T$")
    ax.plot(x, trackless, "s-", linewidth=2.2, label="Región trackless")
    ax.set_yscale("log")
    ax.set_ylim(0.01, 160)
    ax.set_ylabel("Fracción de eventos ponderados [%]")
    ax.set_xticks(list(x), labels, rotation=24, ha="right")
    ax.grid(axis="y", which="both", alpha=0.25)
    ax.legend(loc="lower left")
    ax.set_title(
        "Cutflow strong-bm1 distribuido por upstream",
        fontweight="bold",
        fontsize=13,
    )
    ax.annotate(
        "Aceptación × eficiencia (trackless)\n= 0,02165427 %  (2,05 eventos ponderados)",
        (len(rows) - 1, trackless[-1]),
        xytext=(-205, 26),
        textcoords="offset points",
        arrowprops={"arrowstyle": "->", "color": "#9c2f2f"},
        fontsize=9.5,
    )
    fig.text(
        0.5,
        0.02,
        "Referencia upstream distribuida — no reproducción local",
        ha="center",
        fontsize=10,
        color="#9c2f2f",
        fontweight="bold",
    )
    fig.savefig(HERE / "reference_cutflow_upstream.pdf")


if __name__ == "__main__":
    main()
