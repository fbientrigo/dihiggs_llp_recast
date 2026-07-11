from __future__ import annotations

from pathlib import Path

import pytest

from dvrecast.cutflow import CutflowRow, compare_cutflows, read_cutflow_csv


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
