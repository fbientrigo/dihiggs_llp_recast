from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

CARDS = Path("benchmarks/upstream/strong-bm1/cards")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_template_slha_checksum_is_pinned() -> None:
    provenance = json.loads((CARDS / "PROVENANCE.json").read_text(encoding="utf-8"))
    entry = next(
        f for f in provenance["files"] if f["name"] == "GG_qqn1_2800_10_rpvLF_p01ns.slha"
    )
    actual = _sha256(CARDS / "source" / "GG_qqn1_2800_10_rpvLF_p01ns.slha")
    assert actual == entry["sha256"]
    assert entry["byte_identical_copy"] is True


def test_source_and_generated_cards_have_recorded_checksums() -> None:
    provenance = json.loads((CARDS / "PROVENANCE.json").read_text(encoding="utf-8"))
    for entry in provenance["files"]:
        path = CARDS / "source" / entry["name"]
        assert path.is_file()
        assert _sha256(path) == entry["sha256"]


def test_generated_slha_changes_only_documented_masses() -> None:
    audit = json.loads((CARDS / "slha_transformation_audit.json").read_text(encoding="utf-8"))
    src = (CARDS / "source/GG_qqn1_2800_10_rpvLF_p01ns.slha").read_text().splitlines()
    gen = (CARDS / "generated/GG_qqn1_2000_850_rpvLF_p01ns.slha").read_text().splitlines()

    diff_lines = [i + 1 for i, (a, b) in enumerate(zip(src, gen, strict=False)) if a != b]
    documented = [d["line"] for d in audit["changed_lines"]]
    assert diff_lines == documented
    assert audit["mass_verification"]["1000021_GeV"] == 2000.0
    assert audit["mass_verification"]["1000022_GeV"] == 850.0


def test_neutralino_lifetime_conversion_is_correct() -> None:
    audit = json.loads((CARDS / "slha_transformation_audit.json").read_text(encoding="utf-8"))
    lifetime = audit["lifetime_verification"]
    hbar = 6.582119569e-25
    gamma = audit["width_verification"]["1000022_width_GeV"]
    expected_tau_ns = (hbar / gamma) * 1e9
    assert abs(lifetime["tau_ns"] - expected_tau_ns) < 1e-9
    assert abs(lifetime["tau_ns"] - 0.01) < 1e-6


def test_all_branching_ratio_sums_are_valid() -> None:
    audit = json.loads((CARDS / "slha_transformation_audit.json").read_text(encoding="utf-8"))
    checks = audit["branching_ratio_sum_checks"]
    assert checks["valid"] is True
    assert abs(checks["gluino_1000021_BR_sum"] - 1.0) < 1e-6
    assert abs(checks["neutralino_1000022_BR_sum"] - 1.0) < 1e-6


def test_three_processes_are_distinct_and_correct() -> None:
    processes = {}
    for mult in (0, 1, 2):
        text = (CARDS / f"source/pp2gogo_{mult}_proc_card_mg5.dat").read_text()
        assert "import model MSSM_SLHA2" in text
        assert f"output pp2gogo_{mult}" in text
        for line in text.splitlines():
            if line.startswith("generate"):
                processes[mult] = line
    assert processes[0] == "generate p p > go go"
    assert processes[1] == "generate p p > go go j"
    assert processes[2] == "generate p p > go go j j"
    assert len(set(processes.values())) == 3


def test_all_final_seeds_are_explicit_and_nonzero() -> None:
    seeds = json.loads(
        Path("benchmarks/upstream/strong-bm1/SEEDS.json").read_text(encoding="utf-8")
    )
    values = list(seeds["seeds"].values())
    assert len(values) == 3
    assert len(set(values)) == 3
    assert all(isinstance(v, int) and v != 0 for v in values)


def test_all_three_expected_lhe_names_present_in_contract() -> None:
    contract = json.loads(
        Path("benchmarks/upstream/strong-bm1/generation_contract.json").read_text(
            encoding="utf-8"
        )
    )
    names = contract["fields"]["output_naming"]["value"]
    assert names == [
        "strong_0_2000_850_0p01.lhe.gz",
        "strong_1_2000_850_0p01.lhe.gz",
        "strong_2_2000_850_0p01.lhe.gz",
    ]


def test_bm1_cmnd_uses_all_three_multiplicities_and_ckkwl_unchanged() -> None:
    text = (CARDS / "source/bm1.cmnd").read_text()
    assert "Merging:doKTMerging       = on" in text
    assert "Merging:TMS               = 500" in text
    assert "Merging:nJetMax           = 2" in text
    assert "Merging:Process           = pp>{go,1000021}{go,1000021}" in text
    for mult, name in enumerate(
        [
            "strong_0_2000_850_0p01.lhe.gz",
            "strong_1_2000_850_0p01.lhe.gz",
            "strong_2_2000_850_0p01.lhe.gz",
        ]
    ):
        assert f"Main:subrun               = {mult}" in text
        assert name in text


def test_upstream_submodule_remains_pinned_and_clean() -> None:
    head = subprocess.run(
        ["git", "-C", "external/recastingCodes", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert head == "d4047c744062094c9f88e507bb1ccf69e9fe88d6"
    status = subprocess.run(
        ["git", "-C", "external/recastingCodes", "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert status == ""


def test_scalar_and_pack_inputs_are_rejected() -> None:
    from dvrecast.readiness import selected_benchmark_readiness

    benchmark = {
        "identifier": "strong-bm1",
        "card_paths": {
            "parameter_or_slha_card": "pack_a/some.slha",
            "bad": "pack_aa/thing",
            "worse": "pack_b/other",
        },
    }
    contract = {"classification": "RECONSTRUCTED", "fields": {"output_naming": {"value": []}}}
    state = selected_benchmark_readiness(Path("."), benchmark, contract, mg5_available=True)
    assert any("refusing non-upstream strong-bm1 input" in b for b in state.blockers)


def test_archived_output_is_never_accepted_as_reproduced_output() -> None:
    benchmark = json.loads(
        Path("benchmarks/upstream/strong-bm1/benchmark.json").read_text(encoding="utf-8")
    )
    reference = benchmark["reference_result_path"]
    assert reference.startswith("external/recastingCodes/")
    # The reference/archived path must never equal a project-owned reproduced-output path.
    assert "results/strong-bm1" not in reference
    assert "data/upstream/strong-bm1/lhe" not in reference
