from __future__ import annotations

import json
from pathlib import Path

import pytest

from dvrecast.config import (
    DEFAULT_LLP_PDG_ID,
    UpstreamLock,
    load_toolchain_config,
    load_upstream_lock,
    render_llp_pdg_cmnd_line,
    resolve_llp_pdg_id,
)


def test_load_upstream_lock(tmp_path: Path) -> None:
    path = tmp_path / "lock.json"
    path.write_text(
        json.dumps(
            {
                "repository": "https://github.com/example/repo.git",
                "commit": "a" * 40,
                "analysis_path": "analysis/path",
            }
        ),
        encoding="utf-8",
    )
    lock = load_upstream_lock(path)
    assert lock.commit == "a" * 40
    assert lock.analysis_path == Path("analysis/path")


def test_rejects_short_commit() -> None:
    with pytest.raises(ValueError, match="40-character"):
        UpstreamLock.from_mapping(
            {
                "repository": "https://github.com/example/repo.git",
                "commit": "abc123",
                "analysis_path": "analysis/path",
            }
        )


def test_rejects_parent_traversal() -> None:
    with pytest.raises(ValueError, match="relative path"):
        UpstreamLock.from_mapping(
            {
                "repository": "https://github.com/example/repo.git",
                "commit": "a" * 40,
                "analysis_path": "../escape",
            }
        )


def test_load_toolchain_config_expands_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    path = tmp_path / "toolchain.env"
    path.write_text(
        'PYTHIA8="$HOME/.local/pythia8308"\nPYTHIA8_SOURCE_TAG="pythia8308"\n',
        encoding="utf-8",
    )
    config = load_toolchain_config(path)
    assert config["PYTHIA8"] == str(tmp_path / ".local" / "pythia8308")
    assert config["PYTHIA8_SOURCE_TAG"] == "pythia8308"


def test_resolve_llp_pdg_id_defaults_to_neutralino() -> None:
    assert resolve_llp_pdg_id() == DEFAULT_LLP_PDG_ID == 1000022


def test_resolve_llp_pdg_id_prefers_explicit_over_config() -> None:
    assert resolve_llp_pdg_id(9000006, config={"llp_pdg_id": 1000023}) == 9000006


def test_resolve_llp_pdg_id_falls_back_to_config() -> None:
    assert resolve_llp_pdg_id(None, config={"llp_pdg_id": "9000006"}) == 9000006


def test_resolve_llp_pdg_id_rejects_malformed_value() -> None:
    with pytest.raises(ValueError, match="invalid LLP PDG id"):
        resolve_llp_pdg_id("not-a-pdg-id")
    with pytest.raises(ValueError, match="nonzero"):
        resolve_llp_pdg_id(0)


def test_render_llp_pdg_cmnd_line_omits_default() -> None:
    # The upstream cmnd cards already default Recast:llpPdgIds to the
    # original triplet in the C++ patch, so the default case must not emit a
    # line that could diverge from that baked-in baseline.
    assert render_llp_pdg_cmnd_line() is None
    assert render_llp_pdg_cmnd_line(DEFAULT_LLP_PDG_ID) is None


def test_render_llp_pdg_cmnd_line_for_alternate_pdg() -> None:
    assert render_llp_pdg_cmnd_line(35) == "Recast:llpPdgIds = {35}"
    assert render_llp_pdg_cmnd_line(config={"llp_pdg_id": 35}) == "Recast:llpPdgIds = {35}"
