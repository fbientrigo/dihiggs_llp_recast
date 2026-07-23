from __future__ import annotations

import json
from pathlib import Path

import pytest

import dvrecast.readiness as readiness_module
from dvrecast.readiness import (
    core_environment_readiness,
    madgraph_readiness,
    selected_benchmark_readiness,
    upstream_build_readiness,
)


def _make_usable(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(0o755)


def _complete_prefixes(tmp_path: Path) -> dict[str, str]:
    pythia = tmp_path / "pythia"
    fastjet = tmp_path / "fastjet"
    (pythia / "include/Pythia8").mkdir(parents=True)
    (pythia / "include/Pythia8/Pythia.h").touch()
    (pythia / "lib").mkdir()
    (pythia / "lib/libpythia8.so").touch()
    (fastjet / "include/fastjet").mkdir(parents=True)
    (fastjet / "lib").mkdir()
    _make_usable(pythia / "bin/pythia8-config")
    _make_usable(fastjet / "bin/fastjet-config")
    return {"PYTHIA8": str(pythia), "FASTJET3": str(fastjet)}


def test_build_ready_with_complete_prefixes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _complete_prefixes(tmp_path)
    monkeypatch.setattr(readiness_module.shutil, "which", lambda name: f"/usr/bin/{name}")
    state = upstream_build_readiness(config)
    assert state.state == "READY"
    assert state.blockers == ()


def test_config_scripts_do_not_mask_missing_headers_and_libraries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pythia = tmp_path / "pythia"
    fastjet = tmp_path / "fastjet"
    _make_usable(pythia / "bin/pythia8-config")
    _make_usable(fastjet / "bin/fastjet-config")
    monkeypatch.setattr(readiness_module.shutil, "which", lambda name: f"/usr/bin/{name}")

    state = upstream_build_readiness(
        {"PYTHIA8": str(pythia), "FASTJET3": str(fastjet)}
    )

    assert state.state == "BLOCKED"
    assert str(pythia / "include/Pythia8/Pythia.h") in state.blockers
    assert f"{pythia}/lib/libpythia8.so or {pythia}/lib/libpythia8.a" in state.blockers
    assert str(fastjet / "include/fastjet") in state.blockers
    assert str(fastjet / "lib") in state.blockers


def test_madgraph_readiness_is_only_local_tool_capability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(readiness_module.shutil, "which", lambda name: None)
    monkeypatch.setenv("HOME", "/tmp/no-strong-bm1-mg5")
    monkeypatch.delenv("MG5_BIN", raising=False)
    state, path, version = madgraph_readiness({})
    assert state.state == "BLOCKED"
    assert state.blockers == ("usable mg5_aMC",)
    assert path is None
    assert version is None


def test_madgraph_resolver_finds_known_non_path_installation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(readiness_module.shutil, "which", lambda name: None)
    monkeypatch.delenv("MG5_BIN", raising=False)
    state, path, version = madgraph_readiness({})
    assert state.state == "READY"
    assert path == "/home/fabi/.local/mg5amcnlo/3.5.3/bin/mg5_aMC"
    assert version == "3.5.3"


def test_madgraph_readiness_records_configured_version(tmp_path: Path) -> None:
    prefix = tmp_path / "mg5"
    _make_usable(prefix / "bin/mg5_aMC")
    (prefix / "VERSION").write_text("version = 3.5.3\n", encoding="utf-8")

    state, path, version = madgraph_readiness({"MG5_HOME": str(prefix)})

    assert state.state == "READY"
    assert path == str(prefix / "bin/mg5_aMC")
    assert version == "3.5.3"


def test_madgraph_readiness_requires_resolved_version(tmp_path: Path) -> None:
    prefix = tmp_path / "mg5"
    _make_usable(prefix / "bin/mg5_aMC")

    state, _, version = madgraph_readiness({"MG5_HOME": str(prefix)})

    assert state.state == "BLOCKED"
    assert state.blockers == ("resolved MadGraph version",)
    assert version is None


def test_selected_benchmark_remains_blocked_without_inventory_inputs(tmp_path: Path) -> None:
    benchmark_path = Path("benchmarks/upstream/strong-bm1/benchmark.json")
    benchmark = json.loads(benchmark_path.read_text(encoding="utf-8"))
    contract_path = Path("benchmarks/upstream/strong-bm1/generation_contract.json")
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    state = selected_benchmark_readiness(
        tmp_path, benchmark, contract, mg5_available=False
    )
    assert state.state == "BLOCKED"
    # Author-confirmed reconstruction supersedes the old INCOMPLETE classification.
    assert "generation contract is INCOMPLETE" not in state.blockers
    assert any("strong_0_2000_850_0p01.lhe.gz" in item for item in state.blockers)
    assert "missing mg5_aMC" in state.blockers


def test_selected_benchmark_is_not_run_when_inputs_are_complete(tmp_path: Path) -> None:
    lhe_names = [f"strong_{index}_2000_850_0p01.lhe.gz" for index in range(3)]
    benchmark = {
        "identifier": "custom-benchmark",
        "card_paths": {"parameter_or_slha_card": "cards/strong-bm1.slha"},
        "missing_inputs": lhe_names,
    }
    contract = {
        "classification": "RECOVERED_EXACT",
        "fields": {"output_naming": {"value": lhe_names}},
    }
    data_dir = tmp_path / "data/upstream/custom-benchmark"
    data_dir.mkdir(parents=True)
    card = tmp_path / "cards/strong-bm1.slha"
    card.parent.mkdir()
    card.write_text("BLOCK MASS\n 1000021 2000\n 1000022 850\n", encoding="utf-8")
    for name in lhe_names:
        (data_dir / name).touch()

    state = selected_benchmark_readiness(
        tmp_path, benchmark, contract, mg5_available=True
    )

    assert state.state == "NOT_RUN"
    assert state.blockers == ()


def test_pack_paths_are_not_accepted_as_strong_inputs(tmp_path: Path) -> None:
    card = tmp_path / "pack_a.slha"
    card.write_text("1000021 2000\n1000022 850\n", encoding="utf-8")
    state = selected_benchmark_readiness(
        tmp_path,
        {"identifier": "strong-bm1", "card_paths": {"parameter_or_slha_card": "pack_a.slha"}},
        {"classification": "RECOVERED_EXACT", "fields": {"output_naming": {"value": []}}},
        mg5_available=True,
    )
    assert any("refusing non-upstream strong-bm1 input" in item for item in state.blockers)


def test_core_readiness_is_separate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(readiness_module.shutil, "which", lambda name: f"/usr/bin/{name}")
    assert core_environment_readiness().state == "READY"
