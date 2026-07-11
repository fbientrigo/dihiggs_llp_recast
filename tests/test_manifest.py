from __future__ import annotations

from pathlib import Path

from dvrecast.config import UpstreamLock
from dvrecast.manifest import build_environment_manifest


def test_manifest_contains_expected_provenance(tmp_path: Path) -> None:
    lock = UpstreamLock(
        repository="https://github.com/example/repo.git",
        commit="a" * 40,
        analysis_path=Path("analysis/path"),
    )
    manifest = build_environment_manifest(tmp_path, lock)
    assert manifest["schema_version"] == 1
    assert manifest["upstream"]["expected_commit"] == "a" * 40
    assert manifest["upstream"]["checkout"] is None
    assert isinstance(manifest["tools"], list)
