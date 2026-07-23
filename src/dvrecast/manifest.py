from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

from .config import UpstreamLock
from .readiness import (
    Readiness,
    core_environment_readiness,
    madgraph_readiness,
    selected_benchmark_readiness,
    upstream_build_readiness,
)


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


def tool_snapshot(name: str, configured_path: Path | None = None) -> dict[str, Any]:
    path = (
        str(configured_path)
        if configured_path and configured_path.is_file()
        else shutil.which(name)
    )
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


def _pythia_version(prefix: Path | None) -> str | None:
    if prefix is None:
        return None
    header = prefix / "include" / "Pythia8" / "Pythia.h"
    if not header.is_file():
        return None
    for line in header.read_text(encoding="utf-8").splitlines():
        if line.startswith("#define PYTHIA_VERSION "):
            return line.split()[-1]
    return None


def pythia_source_provenance(toolchain: Mapping[str, str]) -> dict[str, Any]:
    declared_tag = toolchain.get("PYTHIA8_SOURCE_TAG")
    declared_commit = toolchain.get("PYTHIA8_SOURCE_COMMIT")
    configured_dir = toolchain.get("PYTHIA8_SOURCE_DIR")
    provenance: dict[str, Any] = {
        "declared_tag": declared_tag,
        "declared_commit": declared_commit,
        "source_checkout_path": None,
        "source_checkout_head": None,
        "source_checkout_tracked_dirty": None,
        "source_checkout_untracked_entries_present": None,
        "declared_commit_matches_head": None,
        "declared_tag_resolved_commit": None,
        "declared_tag_matches_head": None,
        "source_checkout_declaration_status": (
            "UNVERIFIED" if declared_tag or declared_commit else "NOT_DECLARED"
        ),
        "install_origin_status": "UNVERIFIED",
    }
    if not configured_dir:
        provenance["source_checkout_declaration_detail"] = (
            "No PYTHIA8_SOURCE_DIR was configured"
        )
        return provenance

    source_dir = Path(configured_dir).resolve()
    provenance["source_checkout_path"] = str(source_dir)
    inside = _capture(["git", "rev-parse", "--is-inside-work-tree"], source_dir)
    if not inside.get("ok") or inside.get("stdout") != "true":
        provenance["source_checkout_declaration_status"] = "UNVERIFIED"
        provenance["source_checkout_declaration_detail"] = (
            "Configured source directory is not a Git checkout"
        )
        return provenance

    head_result = _capture(["git", "rev-parse", "HEAD"], source_dir)
    tracked_status_result = _capture(
        ["git", "status", "--porcelain", "--untracked-files=no"], source_dir
    )
    untracked_result = _capture(
        ["git", "ls-files", "--others", "--exclude-standard"], source_dir
    )
    head = head_result.get("stdout") if head_result.get("ok") else None
    provenance["source_checkout_head"] = head
    provenance["source_checkout_tracked_dirty"] = (
        bool(tracked_status_result.get("stdout"))
        if tracked_status_result.get("ok")
        else None
    )
    provenance["source_checkout_untracked_entries_present"] = (
        bool(untracked_result.get("stdout")) if untracked_result.get("ok") else None
    )
    mismatches: list[str] = []
    if declared_commit and head:
        provenance["declared_commit_matches_head"] = declared_commit.lower() == head.lower()
        if not provenance["declared_commit_matches_head"]:
            mismatches.append("declared commit does not match checkout HEAD")
    elif declared_commit:
        mismatches.append("checkout HEAD could not be resolved")

    if declared_tag:
        tag_result = _capture(["git", "rev-parse", f"refs/tags/{declared_tag}^{{}}"], source_dir)
        tag_commit = tag_result.get("stdout") if tag_result.get("ok") else None
        provenance["declared_tag_resolved_commit"] = tag_commit
        provenance["declared_tag_matches_head"] = bool(
            tag_commit and head and tag_commit == head
        )
        if not provenance["declared_tag_matches_head"]:
            mismatches.append("declared tag does not resolve to checkout HEAD")

    if mismatches:
        provenance["source_checkout_declaration_status"] = "MISMATCH"
        provenance["source_checkout_declaration_detail"] = "; ".join(mismatches)
    elif head and (declared_tag or declared_commit):
        provenance["source_checkout_declaration_status"] = "MATCHES"
        provenance["source_checkout_declaration_detail"] = (
            "All configured declarations match checkout HEAD"
        )
    else:
        provenance["source_checkout_declaration_status"] = "NOT_DECLARED"
        provenance["source_checkout_declaration_detail"] = (
            "No source declarations were configured"
        )
    return provenance


def _file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _build_snapshot(repo_root: Path) -> dict[str, Any]:
    executable = (
        repo_root
        / "external/recastingCodes/DisplacedVertices/ATLAS-SUSY-2018-13_GCottin"
        / "recast_code/1_analysis/recast_2301_13866"
    )
    if not executable.is_file():
        return {"executable_path": str(executable), "available": False}

    runtime = _capture(["ldd", str(executable)])
    runtime_text = runtime.get("stdout", "")
    build_environment = repo_root / "results/upstream_build/build_environment.txt"
    build_timestamp = None
    if build_environment.is_file():
        for line in build_environment.read_text(encoding="utf-8").splitlines():
            if line.startswith("created_utc="):
                build_timestamp = line.removeprefix("created_utc=")
                break
    return {
        "available": True,
        "build_timestamp_utc": build_timestamp,
        "executable_path": str(executable),
        "executable_sha256": _file_sha256(executable),
        "runtime_library_resolution": {
            "command": runtime.get("command"),
            "returncode": runtime.get("returncode"),
            "resolved": runtime.get("ok", False) and "not found" not in runtime_text,
            "missing": [line.strip() for line in runtime_text.splitlines() if "not found" in line],
            "output": runtime_text,
            "stderr": runtime.get("stderr", ""),
        },
    }


def _readiness_snapshot(
    repo_root: Path,
    toolchain: Mapping[str, str],
    madgraph: Readiness,
    mg5_version: str | None,
) -> dict[str, Any]:
    core = core_environment_readiness()
    build = upstream_build_readiness(toolchain)
    benchmark_path = repo_root / "benchmarks/upstream/strong-bm1/benchmark.json"
    contract_path = repo_root / "benchmarks/upstream/strong-bm1/generation_contract.json"
    benchmark = (
        json.loads(benchmark_path.read_text(encoding="utf-8"))
        if benchmark_path.is_file()
        else {}
    )
    contract = (
        json.loads(contract_path.read_text(encoding="utf-8"))
        if contract_path.is_file()
        else {}
    )
    selected = selected_benchmark_readiness(
        repo_root, benchmark, contract, mg5_available=madgraph.state == "READY"
    )

    def record(state: str, blockers: tuple[str, ...]) -> dict[str, Any]:
        return {"state": state, "blockers": list(blockers)}

    return {
        "core_environment": record(core.state, core.blockers),
        "upstream_recast_build": record(build.state, build.blockers),
        "madgraph_lhe_generation_tool": {
            **record(madgraph.state, madgraph.blockers),
            "version": mg5_version,
        },
        "selected_upstream_benchmark": record(selected.state, selected.blockers),
    }


def build_environment_manifest(
    repo_root: Path, lock: UpstreamLock, toolchain: Mapping[str, str] | None = None
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    upstream_root = repo_root / "external" / "recastingCodes"
    toolchain = dict(toolchain or {})
    pythia_prefix = Path(toolchain["PYTHIA8"]) if toolchain.get("PYTHIA8") else None
    fastjet_prefix = Path(toolchain["FASTJET3"]) if toolchain.get("FASTJET3") else None
    madgraph_prefix = Path(toolchain["MG5_HOME"]) if toolchain.get("MG5_HOME") else None
    madgraph_state, madgraph_path, madgraph_version = madgraph_readiness(toolchain)
    configured_tools = {
        "fastjet-config": fastjet_prefix / "bin/fastjet-config" if fastjet_prefix else None,
        "pythia8-config": pythia_prefix / "bin/pythia8-config" if pythia_prefix else None,
        "mg5_aMC": (
            Path(toolchain["MG5_HOME"]) / "bin/mg5_aMC" if toolchain.get("MG5_HOME") else None
        ),
    }
    tools = ["git", "make", "g++", "python3", "fastjet-config", "pythia8-config"]
    tool_records = [tool_snapshot(name, configured_tools.get(name)) for name in tools]
    tool_records.append(
        {
            "name": "mg5_aMC",
            "available": madgraph_state.state == "READY",
            "path": madgraph_path,
            "version": madgraph_version,
        }
    )
    selected_env = {
        key: os.environ.get(key)
        for key in ("CC", "CXX", "PYTHIA8", "FASTJET3", "MG5_HOME", "OMP_NUM_THREADS")
    }
    return {
        "schema_version": 2,
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
        "tools": tool_records,
        "toolchain": {
            "fastjet": {
                "prefix": str(fastjet_prefix) if fastjet_prefix else None,
                "version": (
                    tool_snapshot(
                        "fastjet-config", configured_tools["fastjet-config"]
                    ).get("version")
                    if fastjet_prefix
                    else None
                ),
            },
            "pythia": {
                "prefix": str(pythia_prefix) if pythia_prefix else None,
                "version": _pythia_version(pythia_prefix),
                "source_provenance": pythia_source_provenance(toolchain),
            },
            "madgraph": {
                "prefix": str(madgraph_prefix) if madgraph_prefix else None,
                "path": madgraph_path,
                "version": madgraph_version,
                "state": madgraph_state.state,
            },
            "compiler": tool_snapshot(toolchain.get("CXX", "g++")),
        },
        "build": _build_snapshot(repo_root),
        "readiness": _readiness_snapshot(
            repo_root, toolchain, madgraph_state, madgraph_version
        ),
        "environment": selected_env,
    }
