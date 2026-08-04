from __future__ import annotations

import csv
import math
import re
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CutflowRow:
    cut: str
    count: float


@dataclass(frozen=True)
class CutflowComparison:
    cut: str
    reference: float
    observed: float
    absolute_difference: float
    relative_difference: float | None
    passed: bool


def read_cutflow_csv(path: str | Path) -> list[CutflowRow]:
    rows: list[CutflowRow] = []
    seen: set[str] = set()
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not {"cut", "count"}.issubset(reader.fieldnames):
            raise ValueError("cutflow CSV must contain columns: cut,count")
        for index, raw in enumerate(reader, start=2):
            cut = (raw.get("cut") or "").strip()
            if not cut:
                raise ValueError(f"empty cut name at line {index}")
            if cut in seen:
                raise ValueError(f"duplicate cut name: {cut}")
            try:
                count = float(raw.get("count", ""))
            except ValueError as exc:
                raise ValueError(f"invalid count for cut {cut}") from exc
            if count < 0:
                raise ValueError(f"negative count for cut {cut}")
            seen.add(cut)
            rows.append(CutflowRow(cut, count))
    if not rows:
        raise ValueError("cutflow CSV is empty")
    return rows


def compare_cutflows(
    reference: list[CutflowRow],
    observed: list[CutflowRow],
    *,
    relative_tolerance: float = 0.20,
    low_count_threshold: float = 10.0,
    low_count_absolute_tolerance: float = 3.0,
) -> list[CutflowComparison]:
    if relative_tolerance < 0 or low_count_absolute_tolerance < 0:
        raise ValueError("tolerances must be non-negative")

    reference_cuts = {row.cut for row in reference}
    observed_by_cut = {row.cut: row for row in observed}
    missing = [row.cut for row in reference if row.cut not in observed_by_cut]
    extra = [row.cut for row in observed if row.cut not in reference_cuts]
    if missing or extra:
        raise ValueError(f"cut names differ; missing={missing}, extra={extra}")

    comparisons: list[CutflowComparison] = []
    for ref in reference:
        obs = observed_by_cut[ref.cut]
        absolute = abs(obs.count - ref.count)
        relative = absolute / ref.count if ref.count > 0 else None
        if ref.count < low_count_threshold:
            passed = absolute <= low_count_absolute_tolerance
        else:
            passed = relative is not None and relative <= relative_tolerance
        comparisons.append(
            CutflowComparison(ref.cut, ref.count, obs.count, absolute, relative, passed)
        )
    return comparisons


def comparison_as_dict(row: CutflowComparison) -> dict[str, object]:
    return asdict(row)


_SUMMARY_RE = re.compile(r"^(High-pT|Trackless) (.+?)( \[%\])?:\s*(\S*)\s*$")
_LABELS = {
    "Jet Selection": "jet_selection",
    "Fiducial": "fiducial",
    "R_vertex > 4 mm": "r_vertex_gt_4_mm",
    "Have track with |d_0| > 2 mm": "track_d0_gt_2_mm",
    "Selected Decay Product >= 5": "selected_decay_products_ge_5",
    "Invariant Mass > 10 GeV": "invariant_mass_gt_10_gev",
    "Acc": "acceptance",
    "Acc x Eff": "acceptance_times_efficiency",
}


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def parse_upstream_cutflow(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    lines = source.read_text(encoding="utf-8", errors="replace").splitlines()
    all_events: float | None = None
    cross_section: float | None = None
    branches: dict[str, dict[str, dict[str, Any]]] = {
        "high_pt": {},
        "trackless": {},
    }
    warnings: list[str] = []

    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("All Events:"):
            all_events = float(stripped.split(":", 1)[1])
            continue
        if stripped.startswith("The inclusive cross section after merging is:"):
            cross_section = float(stripped.rsplit(None, 1)[0].split(":", 1)[1])
            continue
        if stripped == "Event has >= 1 DV passing [%]:":
            warnings.append(f"line {line_number}: blank `Event has >= 1 DV passing` summary")
            continue
        match = _SUMMARY_RE.match(stripped)
        if not match:
            continue
        branch_label, label, percent_marker, value = match.groups()
        key = _LABELS.get(label)
        if key is None:
            warnings.append(f"line {line_number}: unrecognized summary label `{label}`")
            continue
        if not value:
            warnings.append(f"line {line_number}: blank `{label}` value")
            continue
        branch = branches["high_pt" if branch_label == "High-pT" else "trackless"]
        metric = branch.setdefault(key, {})
        if percent_marker:
            metric["percent"] = float(value)
        else:
            metric["count"] = float(value)
            metric["count_source"] = "reported"

    if all_events is None or cross_section is None:
        raise ValueError("upstream summary is missing all-events or cross-section data")
    required = set(_LABELS.values())
    for branch_name, metrics in branches.items():
        missing = sorted(required - metrics.keys())
        if missing:
            raise ValueError(f"{branch_name} summary is missing metrics: {missing}")
        for metric in metrics.values():
            if "count" not in metric and "percent" in metric:
                metric["count"] = all_events * metric["percent"] / 100.0
                metric["count_source"] = "calculated_from_weighted_all_events"

    return {
        "schema_version": 1,
        "source": {"path": str(source), "sha256": _sha256(source)},
        "weighted_all_events": all_events,
        "branches": branches,
        "inclusive_cross_section_mb": cross_section,
        "parser_warnings": warnings,
    }


def compare_upstream_cutflows(
    reference: dict[str, Any],
    observed: dict[str, Any],
    *,
    relative_tolerance: float = 0.20,
    severe_tolerance: float = 0.50,
    low_count_threshold: float = 10.0,
) -> dict[str, Any]:
    diagnostics: list[dict[str, Any]] = []
    failed = False
    provisional = False
    try:
        if any(
            not math.isfinite(value) or value < 0
            for value in (relative_tolerance, severe_tolerance, low_count_threshold)
        ):
            raise ValueError("comparison thresholds must be finite and non-negative")
        for branch in ("high_pt", "trackless"):
            reference_metrics = reference["branches"][branch]
            observed_metrics = observed["branches"][branch]
            if set(reference_metrics) != set(observed_metrics):
                raise KeyError(f"{branch} metric names differ")
            for step, ref_metric in reference_metrics.items():
                obs_metric = observed_metrics[step]
                ref_count = float(ref_metric["count"])
                obs_count = float(obs_metric["count"])
                if not all(map(math.isfinite, (ref_count, obs_count))) or min(
                    ref_count, obs_count
                ) < 0:
                    raise ValueError(f"{branch}/{step} counts must be finite and non-negative")
                absolute = abs(obs_count - ref_count)
                relative = absolute / ref_count if ref_count else None
                low_statistics = ref_count < low_count_threshold
                combined_uncertainty = math.sqrt(max(ref_count, 0.0) + max(obs_count, 0.0))
                statistical_limit = max(3.0, 2.0 * combined_uncertainty)
                statistically_consistent = absolute <= statistical_limit
                if low_statistics:
                    passed = statistically_consistent
                    if not passed:
                        if relative is not None and relative > severe_tolerance:
                            failed = True
                        else:
                            provisional = True
                else:
                    passed = relative is not None and relative <= relative_tolerance + 1e-12
                    failed = failed or not passed
                diagnostics.append(
                    {
                        "branch": branch,
                        "step": step,
                        "reference_count": ref_count,
                        "observed_count": obs_count,
                        "absolute_difference": absolute,
                        "relative_difference": relative,
                        "low_statistics": low_statistics,
                        "reference_statistical_uncertainty": math.sqrt(max(ref_count, 0.0)),
                        "observed_statistical_uncertainty": math.sqrt(max(obs_count, 0.0)),
                        "statistically_consistent": statistically_consistent,
                        "passed": passed,
                    }
                )
        ref_xsec = float(reference["inclusive_cross_section_mb"])
        obs_xsec = float(observed["inclusive_cross_section_mb"])
        if not all(map(math.isfinite, (ref_xsec, obs_xsec))) or min(ref_xsec, obs_xsec) < 0:
            raise ValueError("cross sections must be finite and non-negative")
    except (KeyError, TypeError, ValueError) as exc:
        return {
            "schema_version": 1,
            "status": "BLOCKED",
            "blockers": [str(exc)],
            "steps": diagnostics,
        }

    xsec_relative = abs(obs_xsec - ref_xsec) / ref_xsec if ref_xsec else None
    status = "FAILED" if failed else "PROVISIONAL" if provisional else "VALIDATED"
    return {
        "schema_version": 1,
        "status": status,
        "criteria": {
            "well_populated_relative_tolerance": relative_tolerance,
            "unexplained_severe_tolerance": severe_tolerance,
            "low_count_threshold": low_count_threshold,
            "cross_section_affects_cutflow_status": False,
        },
        "steps": diagnostics,
        "cross_section": {
            "reference_mb": ref_xsec,
            "observed_mb": obs_xsec,
            "relative_difference": xsec_relative,
            "affects_status": False,
        },
        "parser_warnings": {
            "reference": reference.get("parser_warnings", []),
            "observed": observed.get("parser_warnings", []),
        },
    }
