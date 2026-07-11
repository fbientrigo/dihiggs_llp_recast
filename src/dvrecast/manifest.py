from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from .config import UpstreamLock


def _capture(command: Sequence[str], cwd: Path | None = None) -> dict[str, Any]:
    try:
        result = subprocess.run(
            list(command), cwd=cwd, capture_output=True, text=True, timeout=15, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"command": list(command), "ok": False, "error": repr(exc)}
    return {
        "command": list(command),
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def git_snapshot(path: Path) -> dict[str, Any]:
    head = _capture(["git", "rev-parse", "HEAD"], path)
    status = _capture(["git", "status", "--porcelain"], path)
    return {
        "path": str(path.resolve()),
        "head": head.get("stdout") if head.get("ok") else None,
        "dirty": bool(status.get("stdout")) if status.get("ok") else None,
    }


def tool_snapshot(name: str) -> dict[str, Any]:
    path = shutil.which(name)
    if path is None:
        return {"name": name, "available": False}
    result = _capture([path, "--version"])
    first_line = (result.get("stdout") or result.get("stderr") or "").splitlines()
    return {
        "name": name,
        "available": True,
        "path": path,
        "version": first_line[0] if first_line else None,
    }


def build_environment_manifest(repo_root: Path, lock: UpstreamLock) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    upstream_root = repo_root / "external" / "recastingCodes"
    tools = ["git", "make", "g++", "python3", "fastjet-config", "pythia8-config", "mg5_aMC"]
    selected_env = {
        key: os.environ.get(key)
        for key in ("CC", "CXX", "PYTHIA8", "FASTJET3", "MG5_HOME", "OMP_NUM_THREADS")
    }
    return {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "host": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": sys.version.split()[0],
        },
        "repository": git_snapshot(repo_root),
        "upstream": {
            "expected_repository": lock.repository,
            "expected_commit": lock.commit,
            "analysis_path": str(lock.analysis_path),
            "checkout": git_snapshot(upstream_root) if (upstream_root / ".git").exists() else None,
        },
        "tools": [tool_snapshot(name) for name in tools],
        "environment": selected_env,
    }
