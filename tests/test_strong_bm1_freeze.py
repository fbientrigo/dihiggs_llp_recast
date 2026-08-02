from __future__ import annotations

import csv
import hashlib
import json
import math
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


def test_generation_summary_separates_sources_and_corrects_units() -> None:
    summary = json.loads((RESULTS / "generation_summary.json").read_text(encoding="utf-8"))
    merged = summary["merged_cross_section"]
    assert merged["unit"] == "fb"
    assert merged["authors_recast"] == 0.4949932
    assert merged["our_reproduction"] == 0.4889942
    assert abs(merged["relative_difference_pct"] + 1.2119358407) < 1e-10
    corrected = json.loads(
        (RESULTS / "generation_summary_interpretation_corrected.json").read_text(encoding="utf-8")
    )
    assert corrected["source_file_modified"] is False
    assert corrected["identified_issue"] == "unit label mismatch"
    assert corrected["merged_inclusive_cross_section_mb"] == 4.889942e-13
    assert corrected["merged_inclusive_cross_section_pb"] == 0.0004889942
    assert corrected["merged_inclusive_cross_section_fb"] == 0.4889942


def test_seed_provenance_is_consistent_across_canonical_artifacts() -> None:
    benchmark = json.loads((BENCHMARK / "benchmark.json").read_text(encoding="utf-8"))
    seeds = json.loads((BENCHMARK / "SEEDS.json").read_text(encoding="utf-8"))["seeds"]
    contract = json.loads((BENCHMARK / "generation_contract.json").read_text(encoding="utf-8"))
    contract_seeds = contract["fields"]["random_seeds"]["value"]
    summary = json.loads((RESULTS / "generation_summary.json").read_text(encoding="utf-8"))
    summary_seeds = {key: value["seed"] for key, value in summary["multiplicities"].items()}
    assert seeds == benchmark["generation"]["seeds"] == contract_seeds == summary_seeds


def test_no_forbidden_statistical_claims_in_canonical_reports() -> None:
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "CONSOLIDATION_REPORT.md", RESULTS / "VALIDATION_REPORT.md")
    ).lower()
    for claim in (
        "0.5" "2%",
        "less than 0.5 " "sigma",
        "within 1 " "sigma",
        "statistical " "proof",
    ):
        assert claim not in text


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
    corrected = json.loads(
        (input_root / "generation_summary_interpretation_corrected.json").read_text(
            encoding="utf-8"
        )
    )
    assert corrected["merged_inclusive_cross_section_pb"] == 0.0004889942


def test_plot_rejects_inconsistent_cross_section_summary(tmp_path: Path) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    for name in ("cutflow.csv", "generation_summary.json"):
        shutil.copy2(RESULTS / name, input_root / name)
    summary_path = input_root / "generation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["merged_cross_section"]["relative_difference_pct"] = 0
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/plot_strong_bm1.py"), "--input-root", str(input_root)],
        capture_output=True,
        text=True,
        env={**os.environ, "MPLBACKEND": "Agg"},
    )
    assert result.returncode != 0
    assert "relative difference is inconsistent" in result.stderr


def test_plot_rejects_nonfinite_or_unit_inconsistent_summary(tmp_path: Path) -> None:
    for value, message in ((float("nan"), "must be numeric"), (1.0, "mb-to-fb conversion")):
        input_root = tmp_path / message.replace(" ", "_")
        input_root.mkdir()
        for name in ("cutflow.csv", "generation_summary.json"):
            shutil.copy2(RESULTS / name, input_root / name)
        summary_path = input_root / "generation_summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if math.isnan(value):
            summary["merged_cross_section"]["our_reproduction"] = value
            summary["merged_cross_section"]["relative_difference_pct"] = value
        else:
            summary["unit_reconciliation"]["source_value"]["our_reproduction"] = value
        summary_path.write_text(json.dumps(summary), encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/plot_strong_bm1.py"),
                "--input-root",
                str(input_root),
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "MPLBACKEND": "Agg"},
        )
        assert result.returncode != 0
        assert message in result.stderr
