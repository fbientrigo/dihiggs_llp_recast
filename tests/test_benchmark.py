from __future__ import annotations

import json
import subprocess
from pathlib import Path

from dvrecast.benchmark import prepare_benchmark


def test_author_confirmed_reconstruction_supersedes_incomplete_block() -> None:
    """The prior INCOMPLETE/BLOCKED_EXTERNAL_ARTIFACT classification is superseded:
    author-confirmed reconstruction (see generation_contract.json classification_reason)
    means the contract classification is now RECONSTRUCTED and generation is permitted
    by the contract itself. The benchmark can still be BLOCKED for an unrelated reason
    (the LHE samples do not exist yet -- see the MadGraph generation blocker below),
    but it must no longer be blocked on contract classification or missing SLHA.
    """
    payload = prepare_benchmark(Path.cwd(), "strong-bm1", dry_run=True)

    assert payload["contract_classification"] == "RECONSTRUCTED"
    assert payload["toolchain_status"] == "READY"
    assert payload["madgraph"]["version"] == "3.5.3"
    assert "generation contract is INCOMPLETE" not in payload["blockers"]
    assert "missing benchmark parameter/SLHA card" not in payload["blockers"]
    assert "SLHA lacks MASS 1000021 = 2000 GeV" not in payload["blockers"]
    assert "SLHA lacks MASS 1000022 = 850 GeV" not in payload["blockers"]
    # Generation is still blocked, but only because the LHE samples do not exist yet
    # (MadGraph 1j/2j generation hit an unresolved zero-cross-section issue; see
    # docs/strong_bm1_reproduction_report.md). This is a real, evidenced blocker,
    # not the old artifact-availability block.
    assert payload["state"] == "BLOCKED"
    assert any("missing LHE samples" in item for item in payload["blockers"])
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
