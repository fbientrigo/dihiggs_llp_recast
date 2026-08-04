from __future__ import annotations

import copy
from pathlib import Path

import pytest

from dvrecast.cutflow import (
    CutflowRow,
    compare_cutflows,
    compare_upstream_cutflows,
    parse_upstream_cutflow,
    read_cutflow_csv,
)


def test_read_and_compare_cutflows(tmp_path: Path) -> None:
    reference_path = tmp_path / "reference.csv"
    reference_path.write_text("cut,count\nall,100\ntrigger,50\nvertices,5\n", encoding="utf-8")
    observed_path = tmp_path / "observed.csv"
    observed_path.write_text("cut,count\nall,95\ntrigger,45\nvertices,3\n", encoding="utf-8")

    result = compare_cutflows(
        read_cutflow_csv(reference_path), read_cutflow_csv(observed_path)
    )
    assert all(item.passed for item in result)


def test_cut_name_mismatch_is_rejected() -> None:
    with pytest.raises(ValueError, match="cut names differ"):
        compare_cutflows([CutflowRow("a", 10)], [CutflowRow("b", 10)])


def test_large_relative_difference_fails() -> None:
    result = compare_cutflows([CutflowRow("a", 100)], [CutflowRow("a", 50)])
    assert result[0].passed is False


def test_parse_upstream_reference_excerpt() -> None:
    payload = parse_upstream_cutflow("tests/fixtures/gluino_cutflow_excerpt.txt")

    assert payload["weighted_all_events"] == pytest.approx(9476.625)
    assert payload["branches"]["high_pt"]["acceptance"]["count"] == pytest.approx(
        2816.284
    )
    assert payload["branches"]["trackless"]["acceptance_times_efficiency"][
        "percent"
    ] == pytest.approx(0.02165427)
    assert payload["inclusive_cross_section_mb"] == pytest.approx(4.949932e-13)
    assert len(payload["source"]["sha256"]) == 64
    assert len(payload["parser_warnings"]) == 2


def _comparison_payload(count: float = 100.0) -> dict[str, object]:
    metric = {"count": count, "percent": count}
    return {
        "branches": {
            "high_pt": {"selection": dict(metric)},
            "trackless": {"selection": dict(metric)},
        },
        "inclusive_cross_section_mb": 1.0,
        "parser_warnings": [],
    }


def test_upstream_comparator_passes_twenty_percent_boundary() -> None:
    reference = _comparison_payload()
    observed = _comparison_payload(120.0)

    result = compare_upstream_cutflows(reference, observed)

    assert result["status"] == "VALIDATED"
    assert all(step["passed"] for step in result["steps"])


def test_upstream_comparator_reports_low_statistics_uncertainty() -> None:
    reference = _comparison_payload(4.0)
    observed = _comparison_payload(8.0)

    result = compare_upstream_cutflows(reference, observed)

    assert result["status"] == "VALIDATED"
    assert result["steps"][0]["low_statistics"] is True
    assert result["steps"][0]["reference_statistical_uncertainty"] == pytest.approx(2.0)


def test_upstream_comparator_fails_large_step_without_using_cross_section() -> None:
    reference = _comparison_payload()
    observed = _comparison_payload(49.0)
    observed["inclusive_cross_section_mb"] = 100.0

    result = compare_upstream_cutflows(reference, observed)

    assert result["status"] == "FAILED"
    assert result["cross_section"]["affects_status"] is False


def test_upstream_comparator_blocks_missing_steps() -> None:
    reference = _comparison_payload()
    observed = copy.deepcopy(reference)
    del observed["branches"]["trackless"]["selection"]

    assert compare_upstream_cutflows(reference, observed)["status"] == "BLOCKED"


def test_upstream_comparator_blocks_invalid_cross_section() -> None:
    observed = _comparison_payload()
    del observed["inclusive_cross_section_mb"]

    assert compare_upstream_cutflows(_comparison_payload(), observed)["status"] == "BLOCKED"
