from __future__ import annotations

from pathlib import Path

import pytest

from dvrecast.cutflow import read_cutflow_csv, write_cutflow_csv
from dvrecast.llp_event import LlpNotFoundError, load_fixture, run_llp_smoke_cutflow

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "llp_scalar_smoke_event.json"


def test_scalar_smoke_fixture_is_found_and_traversed_end_to_end(tmp_path: Path) -> None:
    fixture = load_fixture(FIXTURE_PATH)

    rows, rejection_stage = run_llp_smoke_cutflow(fixture)

    stage_counts = {row.cut: row.count for row in rows}
    assert stage_counts["llp_identified"] == 1.0
    assert stage_counts["descendants_collected"] == 1.0
    assert stage_counts["displaced_vertex_read"] == 1.0
    assert stage_counts["vertex_in_fiducial_region"] == 1.0
    # This technical fixture has only one charged final descendant, below the
    # fixture's own min_charged_descendants=2, so it is rejected at the last
    # stage. This is the documented, expected outcome; do not loosen it.
    assert stage_counts["final_selection"] == 0.0
    assert rejection_stage == "final_selection"

    csv_path = tmp_path / "cutflow.csv"
    write_cutflow_csv(csv_path, rows)
    round_tripped = read_cutflow_csv(csv_path)
    assert round_tripped == rows


def test_scalar_smoke_accepts_explicit_pdg_override() -> None:
    fixture = load_fixture(FIXTURE_PATH)
    rows, _ = run_llp_smoke_cutflow(fixture, llp_pdg_id=9000006)
    assert rows[1].cut == "llp_identified"
    assert rows[1].count == 1.0


def test_llp_not_found_fails_clearly() -> None:
    fixture = load_fixture(FIXTURE_PATH)
    with pytest.raises(LlpNotFoundError, match="1000022"):
        run_llp_smoke_cutflow(fixture, llp_pdg_id=1000022)


def test_malformed_pdg_id_fails_clearly() -> None:
    fixture = load_fixture(FIXTURE_PATH)
    with pytest.raises(ValueError, match="invalid LLP PDG id"):
        run_llp_smoke_cutflow(fixture, llp_pdg_id="not-a-pdg-id")
