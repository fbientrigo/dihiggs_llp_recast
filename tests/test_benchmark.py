from __future__ import annotations

import json
import subprocess
from pathlib import Path

from dvrecast.benchmark import prepare_benchmark


def test_incomplete_benchmark_dry_run_is_blocked() -> None:
    payload = prepare_benchmark(Path.cwd(), "strong-bm1", dry_run=True)

    assert payload["state"] == "BLOCKED"
    assert payload["contract_classification"] == "INCOMPLETE"
    assert payload["generation_allowed"] is False
    assert payload["toolchain_status"] == "READY"
    assert payload["benchmark_input_status"] == "BLOCKED_EXTERNAL_ARTIFACT"
    assert "generation contract is INCOMPLETE" in payload["blockers"]
    assert payload["madgraph"]["version"] == "3.5.3"
    assert any("strong_0_2000_850_0p01.lhe.gz" in item for item in payload["blockers"])


def test_nonmatching_slha_is_rejected(tmp_path: Path) -> None:
    benchmark_dir = tmp_path / "benchmarks/upstream/demo"
    benchmark_dir.mkdir(parents=True)
    card = tmp_path / "cards/GG_qqn1_2800_10.slha"
    card.parent.mkdir()
    card.write_text("nonmatching\n", encoding="utf-8")
    (benchmark_dir / "benchmark.json").write_text(
        json.dumps(
            {
                "identifier": "demo",
                "card_paths": {
                    "parameter_or_slha_card": "cards/GG_qqn1_2800_10.slha",
                    "related_but_nonmatching_slha_card": "cards/GG_qqn1_2800_10.slha",
                },
            }
        ),
        encoding="utf-8",
    )
    (benchmark_dir / "generation_contract.json").write_text(
        json.dumps(
            {
                "benchmark": "demo",
                "classification": "RECONSTRUCTED",
                "fields": {"output_naming": {"value": []}},
            }
        ),
        encoding="utf-8",
    )

    payload = prepare_benchmark(tmp_path, "demo", dry_run=True)

    assert "refusing nonmatching 2800/10 SLHA for strong-bm1" in payload["blockers"]


def test_upstream_submodule_is_unchanged() -> None:
    result = subprocess.run(
        ["git", "-C", "external/recastingCodes", "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout == ""
