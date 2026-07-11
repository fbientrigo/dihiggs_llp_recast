from __future__ import annotations

import json
from pathlib import Path

import pytest

from dvrecast.config import UpstreamLock, load_upstream_lock


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
