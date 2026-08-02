from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
RESULTS = ROOT / "results/upstream/strong-bm1"
BENCHMARK = ROOT / "benchmarks/upstream/strong-bm1"


def test_cutflow_csv_json_consistency() -> None:
    payload = json.loads((RESULTS / "cutflow.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader((RESULTS / "cutflow.csv").open(encoding="utf-8", newline="")))
    assert [row["id"] for row in payload["stages"]] == [row["stage_id"] for row in rows]
    for stage, row in zip(payload["stages"], rows, strict=True):
        assert stage["label"] == row["label"]
        assert stage["our_weighted_events"] == float(row["our_weighted_events"])
        assert stage["our_efficiency_pct"] == float(row["our_efficiency_pct"])
        assert stage["authors_recast_efficiency_pct"] == float(row["authors_recast_efficiency_pct"])


def test_comparison_values_recompute() -> None:
    rows = list(csv.DictReader((RESULTS / "comparison.csv").open(encoding="utf-8", newline="")))
    for row in rows:
        ours = float(row["our_pct"])
        authors = float(row["authors_pct"])
        assert abs(float(row["absolute_difference_pct"]) - (ours - authors)) < 1e-8
        assert abs(float(row["relative_difference_pct"]) - ((ours / authors - 1) * 100)) < 1e-8
        assert abs(float(row["ratio_our_over_authors"]) - ours / authors) < 1e-8


def test_checksums_match_source_and_canonical_files() -> None:
    source_root = Path("/home/fabi/atlas_dihiggs/original_llp_results/strong_bm1_20260724_000724")
    for line in (BENCHMARK / "checksums.sha256").read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        expected, relative = line.split(maxsplit=1)
        path = (
            source_root / relative.removeprefix("source/")
            if relative.startswith("source/")
            else BENCHMARK / relative
        )
        assert path.is_file(), path
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == expected, path


def test_plot_smoke_regenerates_all_outputs(tmp_path: Path) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "plots"
    input_root.mkdir()
    for name in ("cutflow.csv", "cutflow.json", "generation_summary.json"):
        shutil.copy2(RESULTS / name, input_root / name)
    env = {**os.environ, "MPLBACKEND": "Agg"}
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/plot_strong_bm1.py"),
            "--input-root",
            str(input_root),
            "--output-root",
            str(output_root),
            "--write-comparison-json",
        ],
        check=True,
        env=env,
    )
    expected = {
        "strong_bm1_cutflow.png",
        "strong_bm1_cutflow.pdf",
        "strong_bm1_cutflow.svg",
        "strong_bm1_ratio.png",
        "strong_bm1_ratio.pdf",
        "strong_bm1_cross_section.png",
        "strong_bm1_cross_section.pdf",
    }
    assert {path.name for path in output_root.iterdir()} == expected
    assert (input_root / "comparison.json").is_file()
