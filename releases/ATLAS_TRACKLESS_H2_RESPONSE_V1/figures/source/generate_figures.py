#!/usr/bin/env python3
"""Generate publication figures A-F for ATLAS_TRACKLESS_H2_RESPONSE_V1.

Reads ONLY from the release's own machine-readable tables
(cutflow_long.csv, jet_branch_decomposition.csv, aeff_grid.csv) plus the
raw per-event diagnostic CSVs (for Figure D's ranked-jet-pT distributions,
which are not stage counts and so are not part of cutflow_long.csv). No
number is hand-entered.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# --- validated categorical / sequential palette (dataviz skill reference) ---
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
YELLOW = "#eda100"
MAGENTA = "#e87ba4"
VIOLET = "#4a3aa7"
RED = "#e34948"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
GRID = "#dedcd6"
SURFACE = "#fcfcfb"

MASS_COLOR = {130.0: BLUE, 150.0: ORANGE, 170.0: AQUA}
BRANCH_COLOR = {"J1": BLUE, "J2": ORANGE, "J3": AQUA, "J4": YELLOW}

plt.rcParams.update({
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "axes.edgecolor": GRID,
    "axes.labelcolor": INK,
    "text.color": INK,
    "xtick.color": INK_SECONDARY,
    "ytick.color": INK_SECONDARY,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.8,
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def read_csv(path: Path) -> list[dict]:
    with path.open() as f:
        return list(csv.DictReader(f))


def save(fig, outdir: Path, name: str) -> None:
    fig.savefig(outdir / "pdf" / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(outdir / "png" / f"{name}.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


CUM_STAGES = [
    "generated", "Jet_Selection", "DV_fiducial", "R_DV_gt_4mm",
    "d0_gt_2mm", "tracks_ge_5", "mDV_gt_10GeV", "final_raw",
]
CUM_LABELS = {
    "generated": "Generated",
    "Jet_Selection": "Jet Selection\n(published Trackless)",
    "DV_fiducial": "DV fiducial",
    "R_DV_gt_4mm": "R_DV > 4mm",
    "d0_gt_2mm": "|d0| > 2mm",
    "tracks_ge_5": "tracks >= 5",
    "mDV_gt_10GeV": "mDV > 10 GeV",
    "final_raw": "Final raw\n(Acc)",
}


def figure_a(long_rows, outdir, sample_id="anchor20k_mH150_ctau4p326_2x10000"):
    rows = {r["stage_id"]: r for r in long_rows if r["sample_id"] == sample_id and r["seed"] == "combined"}
    weighted = float(rows["efficiency_weighted"]["weighted_count_if_defined"])
    stages = CUM_STAGES + ["efficiency_weighted"]
    labels = [CUM_LABELS[s] for s in CUM_STAGES] + ["A x eff\n(weighted)"]
    counts = [int(rows[s]["raw_count"]) for s in CUM_STAGES] + [weighted]
    n_gen = int(rows["generated"]["raw_count"])
    fracs = [c / n_gen for c in counts]

    for logy, suffix in ((False, "linear"), (True, "logy")):
        fig, ax = plt.subplots(figsize=(9.5, 5.2))
        colors = [BLUE] * (len(stages) - 1) + [VIOLET]
        bars = ax.bar(labels, counts, color=colors, width=0.62)
        for bar, c, fr in zip(bars, counts, fracs):
            label = f"{c:,.0f}" if suffix == "linear" or c >= 1 else f"{c:.4g}"
            ax.annotate(f"{label}\n({fr*100:.3g}%)", (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                        textcoords="offset points", xytext=(0, 4), ha="center", va="bottom", fontsize=8, color=INK_SECONDARY)
        # highlight the dominant 20000 -> 460 loss
        ax.annotate("", xy=(1, counts[1]), xytext=(0, counts[0]),
                     arrowprops=dict(arrowstyle="-", color=RED, lw=1.4, ls="--"))
        ax.text(0.5, counts[0] * (0.55 if not logy else 0.4), "dominant loss:\nJet Selection",
                color=RED, ha="center", fontsize=9, fontweight="bold")
        if logy:
            ax.set_yscale("log")
            ax.set_ylabel("Events (log scale)")
            ax.set_ylim(top=max(counts) * 4)
        else:
            ax.set_ylabel("Events")
            ax.set_ylim(top=max(counts) * 1.18)
        ax.set_title(f"Figure A — Full cumulative cutflow, mH=150 GeV, ctau=4.326 mm, N={n_gen:,} ({suffix})")
        plt.setp(ax.get_xticklabels(), rotation=20, ha="right", fontsize=8)
        fig.tight_layout()
        save(fig, outdir, f"figureA_cumulative_cutflow_{suffix}")


def figure_b(long_rows, outdir, sample_id="anchor20k_mH150_ctau4p326_2x10000"):
    rows = {r["stage_id"]: r for r in long_rows if r["sample_id"] == sample_id and r["seed"] == "combined"}
    stages = CUM_STAGES
    labels = [CUM_LABELS[s] for s in stages]
    counts = [int(rows[s]["raw_count"]) for s in stages]
    n_gen = counts[0]
    global_frac = [c / n_gen for c in counts]
    cond_ret = [1.0] + [counts[i] / counts[i - 1] if counts[i - 1] else float("nan") for i in range(1, len(counts))]

    def fmt_pct(v: float) -> str:
        pct = v * 100
        if pct >= 99.95:
            return "100%"
        if pct >= 10:
            return f"{pct:.0f}%"
        return f"{pct:.2f}%"

    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    x = np.arange(len(stages))
    w = 0.38
    b1 = ax.bar(x - w / 2, global_frac, width=w, color=BLUE, label="global retention (N_stage / N_generated)")
    b2 = ax.bar(x + w / 2, cond_ret, width=w, color=ORANGE, label="conditional retention (N_stage / N_previous)")
    for bar in b1:
        ax.annotate(fmt_pct(bar.get_height()), (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    textcoords="offset points", xytext=(0, 3), ha="right", fontsize=7.5, color=INK_SECONDARY, rotation=90)
    for bar in b2:
        ax.annotate(fmt_pct(bar.get_height()), (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    textcoords="offset points", xytext=(0, 3), ha="left", fontsize=7.5, color=INK_SECONDARY, rotation=90)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=8)
    ax.set_ylabel("Retention fraction")
    ax.set_ylim(0, 1.22)
    ax.legend(loc="lower left", frameon=False, fontsize=8)
    ax.set_title("Figure B — Global vs. conditional retention, mH=150 GeV, ctau=4.326 mm")
    fig.tight_layout()
    save(fig, outdir, "figureB_conditional_retention")


def figure_c(long_rows, jbd_rows, outdir, sample_id="anchor20k_mH150_ctau4p326_2x10000"):
    long_by_stage = {r["stage_id"]: r for r in long_rows if r["sample_id"] == sample_id and r["seed"] == "combined"}
    jbd = [r for r in jbd_rows if r["sample_id"] == sample_id and r["branch"] in ("J1", "J2", "J3", "J4")]
    branches = ["J1", "J2", "J3", "J4"]
    raw_pop = [int(next(r for r in jbd if r["branch"] == b)["branch_raw_population"]) for b in branches]
    loo_loss = [int(next(r for r in jbd if r["branch"] == b)["leave_one_out_exclusive_loss"]) for b in branches]
    ordinary_or = int(long_by_stage["ordinary_jet_OR"]["raw_count"])
    displaced_add = int(long_by_stage["displaced_jet_addendum"]["raw_count"])
    full_js = int(long_by_stage["Jet_Selection"]["raw_count"])

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.2))

    ax = axes[0]
    bars = ax.bar(branches, raw_pop, color=[BRANCH_COLOR[b] for b in branches], width=0.6)
    for bar, v in zip(bars, raw_pop):
        ax.annotate(f"{v}", (bar.get_x() + bar.get_width() / 2, v), textcoords="offset points",
                    xytext=(0, 3), ha="center", fontsize=8)
    ax.set_ylabel("Raw branch population (events)")
    ax.set_title("Branch raw populations (not mutually exclusive)")

    ax2 = axes[1]
    bars2 = ax2.bar(branches, loo_loss, color=[BRANCH_COLOR[b] for b in branches], width=0.6)
    for bar, v in zip(bars2, loo_loss):
        ax2.annotate(f"-{v}", (bar.get_x() + bar.get_width() / 2, v), textcoords="offset points",
                    xytext=(0, 3), ha="center", fontsize=8)
    ax2.set_ylabel(f"Exclusive loss if branch removed\n(out of ordinary_jet_OR = {ordinary_or})")
    ax2.set_title("Leave-one-branch-out exclusive loss (NOT additive — OR logic)")

    fig.suptitle(
        f"Figure C — Jet-stage zoom, mH=150 GeV: ordinary_jet_OR={ordinary_or}  ->  "
        f"displaced addendum={displaced_add}  ->  full Jet Selection={full_js}",
        fontsize=11, fontweight="bold",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    save(fig, outdir, "figureC_jet_stage_zoom")


JET_COLS = {"pT(j4)": ("jet4_pt", 137.0), "pT(j5)": ("jet5_pt", 101.0), "pT(j6)": ("jet6_pt", 83.0), "pT(j7)": ("jet7_pt", 55.0)}


def figure_d(events_csv_by_mass: dict[float, list[Path]], outdir):
    fig, axes = plt.subplots(2, 2, figsize=(11, 9))
    for ax, (label, (col, thr)) in zip(axes.flat, JET_COLS.items()):
        for mH, paths in events_csv_by_mass.items():
            vals = []
            for p in paths:
                with p.open() as f:
                    for row in csv.DictReader(f):
                        v = float(row[col])
                        if v > 0:
                            vals.append(v)
            vals = np.sort(np.array(vals))
            if len(vals) == 0:
                continue
            ecdf = np.arange(1, len(vals) + 1) / len(vals)
            ax.plot(vals, ecdf, color=MASS_COLOR[mH], lw=1.6, label=f"mH={mH:.0f} GeV")
        ax.axvline(thr, color=RED, ls="--", lw=1.2)
        ax.annotate(f"{thr:.0f} GeV", (thr, 0.05), color=RED, fontsize=8, rotation=90, va="bottom", ha="right")
        ax.set_xlim(0, 300)
        ax.set_xlabel(f"{label} [GeV] (jets with pT>0 in that rank)")
        ax.set_ylabel("ECDF")
        ax.set_title(label)
        ax.legend(loc="lower right", frameon=False, fontsize=8)
    fig.suptitle("Figure D — Ranked jet pT ECDFs vs published thresholds (mH=130/150/170, ctau=4.326 mm)", fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    save(fig, outdir, "figureD_ranked_jet_pt_ecdf")


def figure_e(long_rows, outdir):
    sample_by_mass = {
        130.0: "endpoint20k_mH130_ctau4p326_2x10000",
        150.0: "anchor20k_mH150_ctau4p326_2x10000",
        170.0: "endpoint20k_mH170_ctau4p326_2x10000",
    }
    masses = sorted(sample_by_mass)
    stages = ["Jet_Selection", "final_raw", "efficiency_weighted"]
    stage_labels = ["Jet Selection", "Final raw (Acc)", "A x eff (weighted)"]

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.6))
    for ax, stage, slabel in zip(axes, stages, stage_labels):
        ys = []
        for mH in masses:
            row = next(r for r in long_rows if r["sample_id"] == sample_by_mass[mH] and r["seed"] == "combined" and r["stage_id"] == stage)
            val = row["weighted_count_if_defined"] if stage == "efficiency_weighted" else row["raw_count"]
            ys.append(float(val))
        ax.plot(masses, ys, "-o", color=VIOLET, lw=1.8, markersize=7)
        for mH, y in zip(masses, ys):
            ax.annotate(f"{y:,.4g}", (mH, y), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)
        ax.set_xlabel("mH2 [GeV]")
        ax.set_ylabel(slabel)
        ax.set_title(slabel)
        ax.set_xticks(masses)
    fig.suptitle("Figure E — Mass dependence at fixed ctau = 4.326 mm (jet-stage effect propagating downstream)", fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    save(fig, outdir, "figureE_mass_dependence")


def figure_f(grid_rows, outdir):
    masses = sorted({float(r["mH_GeV"]) for r in grid_rows})
    ctaus = sorted({float(r["ctau_mm"]) for r in grid_rows})
    matrix = np.full((len(masses), len(ctaus)), np.nan)
    for r in grid_rows:
        i = masses.index(float(r["mH_GeV"]))
        j = ctaus.index(float(r["ctau_mm"]))
        matrix[i, j] = float(r["Aeff"])

    fig, ax = plt.subplots(figsize=(11, 4.2))
    im = ax.imshow(matrix, aspect="auto", cmap="Blues", origin="lower")
    ax.set_xticks(range(len(ctaus)))
    ax.set_xticklabels([f"{c:g}" for c in ctaus], rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(masses)))
    ax.set_yticklabels([f"{m:g}" for m in masses])
    ax.set_xlabel("ctau [mm] (discrete simulated grid nodes — not interpolated)")
    ax.set_ylabel("mH2 [GeV]")
    for i in range(len(masses)):
        for j in range(len(ctaus)):
            v = matrix[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:.3g}", ha="center", va="center", fontsize=7,
                         color="white" if v > np.nanmax(matrix) * 0.55 else INK)
    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label("A x efficiency (Trackless)")
    ax.set_title("Figure F — A x efficiency(mH, ctau), validated discrete 3x12 grid (not interpolated)")
    fig.tight_layout()
    save(fig, outdir, "figureF_aeff_2d_grid")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--release-dir", required=True, type=Path)
    ap.add_argument("--diag-dir", required=True, type=Path, help="path to results/trackless_jet_diag_.../ for Figure D raw pT columns")
    args = ap.parse_args()

    outdir = args.release_dir / "figures"
    long_rows = read_csv(args.release_dir / "cutflow_long.csv")
    jbd_rows = read_csv(args.release_dir / "jet_branch_decomposition.csv")
    grid_rows = read_csv(args.release_dir / "aeff_grid.csv")

    figure_a(long_rows, outdir)
    figure_b(long_rows, outdir)
    figure_c(long_rows, jbd_rows, outdir)

    events_csv_by_mass = {
        130.0: [args.diag_dir / "endpoint_130_20k" / f"seed_{s}" / "events.csv" for s in ("81001", "81002")],
        150.0: [args.diag_dir / "anchor_20k_v2" / f"seed_{s}" / "events.csv" for s in ("81001", "81002")],
        170.0: [args.diag_dir / "endpoint_170_20k" / f"seed_{s}" / "events.csv" for s in ("81001", "81002")],
    }
    figure_d(events_csv_by_mass, outdir)
    figure_e(long_rows, outdir)
    figure_f(grid_rows, outdir)

    print("wrote figures A-F (pdf+png) to", outdir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
