from __future__ import annotations

from pathlib import Path

import pandas as pd

from dvrecast.response import default_h2_trackless_spec, extract_response_tables


def _grouped_events(root: Path):
    for mass in (130, 150, 170, 200, 250):
        frames = [
            pd.read_csv(path)
            for path in sorted((root / f"mH{mass}").glob("seed_*/events.csv"))
        ]
        yield {"mH2": mass}, pd.concat(frames, ignore_index=True)


def test_s1_extraction_reproduces_all_frozen_masses() -> None:
    root = Path(__file__).resolve().parents[1]
    events_root = root / "results/jet_threshold_response_20260815T230503Z/runs/main"
    frozen_root = root / "results/jet_threshold_response_20260815T230503Z/response_table"
    got, branches = extract_response_tables(_grouped_events(events_root), [1.0])
    expected = pd.read_csv(frozen_root / "response_table.csv")
    expected_branches = pd.read_csv(frozen_root / "branch_table.csv")

    columns = list(expected.columns)
    pd.testing.assert_frame_equal(
        got[columns].reset_index(drop=True), expected[expected["s"] == 1.0].reset_index(drop=True),
        check_dtype=False,
    )
    branch_columns = list(expected_branches.columns)
    pd.testing.assert_frame_equal(
        branches[branch_columns].reset_index(drop=True),
        expected_branches[expected_branches["s"] == 1.0].reset_index(drop=True),
        check_dtype=False,
    )
    assert default_h2_trackless_spec().stage_names == tuple(expected["stage"].unique())
