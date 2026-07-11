from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path


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
    observed_by_cut = {row.cut: row for row in observed}
    missing = [row.cut for row in reference if row.cut not in observed_by_cut]
    extra = [row.cut for row in observed if row.cut not in {item.cut for item in reference}]
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
