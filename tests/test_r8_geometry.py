from __future__ import annotations

from pathlib import Path

import pytest

from dvrecast.r8_geometry import combine_samples, load_geometry_csv, summarize

_HEADER = (
    "event,llp_index,tau_generated_mm,Rxy_mm,L3D_mm,n_jets_pt20,leading_jet_pt_GeV,"
    "daughter1_id,daughter2_id\n"
)


def _write_csv(path: Path, rows: list[str]) -> Path:
    path.write_text(_HEADER + "\n".join(rows) + "\n", encoding="utf-8")
    return path


def test_load_geometry_csv_counts_events_and_llps(tmp_path: Path):
    csv_path = _write_csv(
        tmp_path / "geom.csv",
        [
            "1,3,1.0,2.0,3.0,5,100.0,5,-5",
            "1,4,4.0,5.0,6.0,5,100.0,5,-5",
            "2,3,0.5,4.5,5.0,2,50.0,-5,5",
            "2,4,2.0,1.0,2.0,2,50.0,-5,5",
        ],
    )
    sample = load_geometry_csv(csv_path)
    assert sample.n_llp == 4
    assert sample.n_events == 2
    assert sample.n_bbbar_decays == 4
    assert sample.n_jets_per_event == [5, 2]
    assert sample.leading_jet_pt_per_event == [100.0, 50.0]


def test_summarize_computes_fractions_and_means(tmp_path: Path):
    csv_path = _write_csv(
        tmp_path / "geom.csv",
        [
            "1,3,1.0,2.0,3.0,5,100.0,5,-5",
            "1,4,4.0,6.0,6.0,5,100.0,5,-5",
        ],
    )
    sample = load_geometry_csv(csv_path)
    summary = summarize(sample)
    assert summary["mean_rxy_mm"] == pytest.approx(4.0)
    assert summary["frac_rxy_gt_4mm"] == pytest.approx(0.5)  # only the 6.0 entry exceeds 4mm
    assert summary["n_bbbar_decays"] == 2


def test_combine_samples_concatenates_and_reindexes_events(tmp_path: Path):
    csv_a = _write_csv(tmp_path / "a.csv", ["1,3,1.0,2.0,3.0,5,100.0,5,-5"])
    csv_b = _write_csv(tmp_path / "b.csv", ["1,3,1.0,8.0,9.0,7,200.0,5,-5"])
    combined = combine_samples([load_geometry_csv(csv_a), load_geometry_csv(csv_b)])
    assert combined.n_events == 2
    assert combined.n_llp == 2
    assert sorted(combined.n_jets_per_event) == [5, 7]
    assert sorted(combined.rxy_mm) == [2.0, 8.0]
