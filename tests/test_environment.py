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
    state, path = madgraph_readiness({})
    assert state.state == "BLOCKED"
    assert state.blockers == ("usable mg5_aMC",)
    assert path is None


def test_selected_benchmark_remains_blocked_without_inventory_inputs(tmp_path: Path) -> None:
    benchmark_path = Path("benchmarks/upstream/strong-bm1/benchmark.json")
    benchmark = json.loads(benchmark_path.read_text(encoding="utf-8"))
    state = selected_benchmark_readiness(tmp_path, benchmark, mg5_available=False)
    assert state.state == "BLOCKED"
    assert "missing exact bm1 SLHA/generation configuration" in state.blockers
    assert any("strong_0_2000_850_0p01.lhe.gz" in item for item in state.blockers)
    assert "missing mg5_aMC" in state.blockers


def test_selected_benchmark_is_not_run_when_inputs_are_complete(tmp_path: Path) -> None:
    lhe_names = [f"strong_{index}_2000_850_0p01.lhe.gz" for index in range(3)]
    data_dir = tmp_path / "data/upstream/strong-bm1"
    data_dir.mkdir(parents=True)
    for name in lhe_names:
        (data_dir / name).touch()
    benchmark = {
        "card_paths": {"parameter_or_slha_card": "cards/strong-bm1.slha"},
        "missing_inputs": lhe_names,
    }

    state = selected_benchmark_readiness(tmp_path, benchmark, mg5_available=True)

    assert state.state == "NOT_RUN"
    assert state.blockers == ()


def test_core_readiness_is_separate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(readiness_module.shutil, "which", lambda name: f"/usr/bin/{name}")
    assert core_environment_readiness().state == "READY"
