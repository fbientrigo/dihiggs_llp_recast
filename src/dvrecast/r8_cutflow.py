"""Parse the stdout cutflow block printed by the frozen upstream DV+jets
recast binary (recast_2301_13866, patched per patches/0001) and turn it into
structured per-region counts.

The binary prints one ``label:   value`` line per stage (percentages, plus
absolute ``Acc``/``Acc x Eff`` lines); this module recovers absolute event
counts from the percentages (all denominators are the fixed
``n_events_processed``, verified independently against ``All Events:``) and
keeps the ``Acc x Eff`` efficiency-weighted figures separate from the
integer ``Acc`` counts that binomial statistics apply to.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_LINE_RE = re.compile(r"^(?P<label>.+?):\s+(?P<value>[+-]?\d+\.\d+e[+-]\d+)(?:\s+\w+)?\s*$")

# (output field name, exact label text as printed by the binary)
_STAGES = [
    ("jet_selection_pct", "{region} Jet Selection [%]"),
    ("fiducial_pct", "{region} Fiducial [%]"),
    ("r_vertex_gt_4mm_pct", "{region} R_vertex > 4 mm [%]"),
    ("track_d0_gt_2mm_pct", "{region} Have track with |d_0| > 2 mm [%]"),
    ("selected_decay_products_ge5_pct", "{region} Selected Decay Product >= 5 [%]"),
    ("invariant_mass_gt_10gev_pct", "{region} Invariant Mass > 10 GeV [%]"),
]
_REGIONS = ("High-pT", "Trackless")


@dataclass(frozen=True)
class RegionCutflow:
    region: str
    n_events: int
    stage_counts: dict[str, int]
    stage_pct: dict[str, float]
    acc: int
    acc_x_eff: float


@dataclass(frozen=True)
class RecastRunResult:
    n_events: int
    zero_llp_events: int
    regions: dict[str, RegionCutflow]
    inclusive_cross_section_mb: float


def _parse_lines(log_text: str) -> dict[str, float]:
    values: dict[str, float] = {}
    for line in log_text.splitlines():
        match = _LINE_RE.match(line.strip())
        if match:
            values[match.group("label")] = float(match.group("value"))
    return values


def _pct_to_count(pct: float, n_events: int) -> int:
    count = pct / 100.0 * n_events
    rounded = round(count)
    if abs(count - rounded) > 1e-6:
        raise ValueError(
            f"percentage {pct} over n_events={n_events} is not an exact count: {count}"
        )
    return rounded


def parse_recast_log(log_text: str) -> RecastRunResult:
    values = _parse_lines(log_text)

    def require(label: str) -> float:
        if label not in values:
            raise ValueError(f"missing expected cutflow line: {label!r}")
        return values[label]

    n_events = round(require("All Events"))
    if abs(require("All Events") - n_events) > 1e-6:
        raise ValueError(f"'All Events' is not an integer event count: {require('All Events')}")

    zero_llp_pct = require("Events with zero configured LLP found [%]")
    zero_llp_events = _pct_to_count(zero_llp_pct, n_events)

    regions: dict[str, RegionCutflow] = {}
    for region in _REGIONS:
        stage_pct = {name: require(label_fmt.format(region=region)) for name, label_fmt in _STAGES}
        stage_counts = {name: _pct_to_count(pct, n_events) for name, pct in stage_pct.items()}
        acc = round(require(f"{region} Acc"))
        acc_x_eff = require(f"{region} Acc x Eff")
        regions[region] = RegionCutflow(
            region=region,
            n_events=n_events,
            stage_counts=stage_counts,
            stage_pct=stage_pct,
            acc=acc,
            acc_x_eff=acc_x_eff,
        )

    cross_section = require("The inclusive cross section after merging is")

    return RecastRunResult(
        n_events=n_events,
        zero_llp_events=zero_llp_events,
        regions=regions,
        inclusive_cross_section_mb=cross_section,
    )


def combine_runs(runs: list[RecastRunResult]) -> dict[str, dict[str, float | int]]:
    """Combine independent runs by summing raw counts (Phase 5: only valid
    once the runs are shown statistically compatible)."""
    if not runs:
        raise ValueError("no runs to combine")
    n_total = sum(r.n_events for r in runs)
    combined: dict[str, dict[str, float | int]] = {}
    for region in _REGIONS:
        acc_total = sum(r.regions[region].acc for r in runs)
        acc_x_eff_total = sum(r.regions[region].acc_x_eff for r in runs)
        combined[region] = {
            "n_total": n_total,
            "acc_total": acc_total,
            "a_eff_acc": acc_total / n_total,
            "acc_x_eff_total": acc_x_eff_total,
            "a_eff_acc_x_eff": acc_x_eff_total / n_total,
        }
    return combined
