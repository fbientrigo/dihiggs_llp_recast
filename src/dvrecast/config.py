from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True)
class UpstreamLock:
    repository: str
    commit: str
    analysis_path: Path
    purpose: str = ""

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "UpstreamLock":
        repository = str(raw.get("repository", "")).strip()
        commit = str(raw.get("commit", "")).strip().lower()
        analysis_path = Path(str(raw.get("analysis_path", "")).strip())
        purpose = str(raw.get("purpose", "")).strip()

        if not repository.startswith("https://github.com/") or not repository.endswith(".git"):
            raise ValueError("repository must be an HTTPS GitHub clone URL ending in .git")
        if not _COMMIT_RE.fullmatch(commit):
            raise ValueError("commit must be a full 40-character lowercase SHA")
        if not str(analysis_path) or analysis_path.is_absolute() or ".." in analysis_path.parts:
            raise ValueError("analysis_path must be a non-empty relative path")

        return cls(repository, commit, analysis_path, purpose)


def load_upstream_lock(path: str | Path) -> UpstreamLock:
    lock_path = Path(path)
    raw = json.loads(lock_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("upstream lock must contain a JSON object")
    return UpstreamLock.from_mapping(raw)
