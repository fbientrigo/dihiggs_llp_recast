"""Summarize the per-LLP geometry CSV produced by src/r8_geometry_driver.cc
into the aggregate statistics needed for Phase 4/5 (median/mean Rxy and L3D,
fiducial-style fractions, jet-multiplicity and leading-jet-pT summaries) plus
the raw per-event samples used for the two-sample KS comparison between
independent runs.
"""

from __future__ import annotations

import csv
import statistics
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GeometrySample:
    n_llp: int
    n_events: int
    rxy_mm: list[float]
    l3d_mm: list[float]
    tau_mm: list[float]
    n_jets_per_event: list[int]
    leading_jet_pt_per_event: list[float]
    n_bbbar_decays: int


def load_geometry_csv(path: str | Path) -> GeometrySample:
    rxy: list[float] = []
    l3d: list[float] = []
    tau: list[float] = []
    n_bbbar = 0
    per_event_jets: dict[int, tuple[int, float]] = {}
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rxy.append(float(row["Rxy_mm"]))
            l3d.append(float(row["L3D_mm"]))
            tau.append(float(row["tau_generated_mm"]))
            d1, d2 = int(row["daughter1_id"]), int(row["daughter2_id"])
            if {d1, d2} == {5, -5}:
                n_bbbar += 1
            event = int(row["event"])
            per_event_jets[event] = (int(row["n_jets_pt20"]), float(row["leading_jet_pt_GeV"]))
    n_jets = [v[0] for v in per_event_jets.values()]
    leading_pt = [v[1] for v in per_event_jets.values()]
    return GeometrySample(
        n_llp=len(rxy),
        n_events=len(per_event_jets),
        rxy_mm=rxy,
        l3d_mm=l3d,
        tau_mm=tau,
        n_jets_per_event=n_jets,
        leading_jet_pt_per_event=leading_pt,
        n_bbbar_decays=n_bbbar,
    )


def _frac_gt(values: list[float], threshold: float) -> float:
    return sum(1 for v in values if v > threshold) / len(values)


def summarize(sample: GeometrySample) -> dict[str, float | int]:
    return {
        "n_llp": sample.n_llp,
        "n_events": sample.n_events,
        "n_bbbar_decays": sample.n_bbbar_decays,
        "mean_rxy_mm": statistics.fmean(sample.rxy_mm),
        "median_rxy_mm": statistics.median(sample.rxy_mm),
        "frac_rxy_gt_4mm": _frac_gt(sample.rxy_mm, 4.0),
        "mean_l3d_mm": statistics.fmean(sample.l3d_mm),
        "median_l3d_mm": statistics.median(sample.l3d_mm),
        "frac_l3d_gt_4mm": _frac_gt(sample.l3d_mm, 4.0),
        "mean_tau_generated_mm": statistics.fmean(sample.tau_mm),
        "mean_n_jets_pt20": statistics.fmean(sample.n_jets_per_event),
        "median_n_jets_pt20": statistics.median(sample.n_jets_per_event),
        "mean_leading_jet_pt_GeV": statistics.fmean(sample.leading_jet_pt_per_event),
        "median_leading_jet_pt_GeV": statistics.median(sample.leading_jet_pt_per_event),
    }


def combine_samples(samples: list[GeometrySample]) -> GeometrySample:
    offset = 0
    per_event_jets: dict[int, tuple[int, float]] = {}
    rxy: list[float] = []
    l3d: list[float] = []
    tau: list[float] = []
    n_bbbar = 0
    for sample in samples:
        rxy.extend(sample.rxy_mm)
        l3d.extend(sample.l3d_mm)
        tau.extend(sample.tau_mm)
        n_bbbar += sample.n_bbbar_decays
        paired = zip(sample.n_jets_per_event, sample.leading_jet_pt_per_event, strict=True)
        for i, (nj, pt) in enumerate(paired):
            per_event_jets[offset + i] = (nj, pt)
        offset += sample.n_events
    n_jets = [v[0] for v in per_event_jets.values()]
    leading_pt = [v[1] for v in per_event_jets.values()]
    return GeometrySample(
        n_llp=len(rxy),
        n_events=len(per_event_jets),
        rxy_mm=rxy,
        l3d_mm=l3d,
        tau_mm=tau,
        n_jets_per_event=n_jets,
        leading_jet_pt_per_event=leading_pt,
        n_bbbar_decays=n_bbbar,
    )
