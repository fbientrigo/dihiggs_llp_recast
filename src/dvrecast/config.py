from __future__ import annotations

import json
import os
import re
import shlex
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True)
class UpstreamLock:
    repository: str
    commit: str
    analysis_path: Path
    purpose: str = ""

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> UpstreamLock:
        repository = str(raw.get("repository", "")).strip()
        commit = str(raw.get("commit", "")).strip().lower()
        analysis_path_raw = str(raw.get("analysis_path", "")).strip()
        purpose = str(raw.get("purpose", "")).strip()

        if not repository.startswith("https://github.com/") or not repository.endswith(".git"):
            raise ValueError("repository must be an HTTPS GitHub clone URL ending in .git")
        if not _COMMIT_RE.fullmatch(commit):
            raise ValueError("commit must be a full 40-character lowercase SHA")
        if not analysis_path_raw:
            raise ValueError("analysis_path must be a non-empty relative path")

        analysis_path = Path(analysis_path_raw)
        if analysis_path.is_absolute() or ".." in analysis_path.parts:
            raise ValueError("analysis_path must be a non-empty relative path")

        return cls(repository, commit, analysis_path, purpose)


def load_upstream_lock(path: str | Path) -> UpstreamLock:
    lock_path = Path(path)
    raw = json.loads(lock_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("upstream lock must contain a JSON object")
    return UpstreamLock.from_mapping(raw)


def load_toolchain_config(path: str | Path) -> dict[str, str]:
    """Load the simple KEY=VALUE assignments used by configs/toolchain.env."""
    config: dict[str, str] = {}
    for line_number, raw_line in enumerate(
        Path(path).read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"invalid toolchain assignment on line {line_number}")
        key, raw_value = line.split("=", 1)
        key = key.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            raise ValueError(f"invalid toolchain key on line {line_number}")
        values = shlex.split(raw_value, comments=True)
        if len(values) != 1:
            raise ValueError(f"toolchain value on line {line_number} must be one shell word")
        config[key] = os.path.expandvars(os.path.expanduser(values[0]))
    return config
