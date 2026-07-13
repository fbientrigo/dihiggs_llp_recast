#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dvrecast.config import load_toolchain_config  # noqa: E402
from dvrecast.readiness import (  # noqa: E402
    core_environment_readiness,
    madgraph_readiness,
    selected_benchmark_readiness,
    upstream_build_readiness,
)


@dataclass(frozen=True)
class Tool:
    name: str
    version_args: tuple[str, ...] = ("--version",)


def version(path: str, args: tuple[str, ...]) -> str:
    try:
        result = subprocess.run(
            [path, *args], capture_output=True, text=True, timeout=10, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unavailable"
    text = (result.stdout or result.stderr).strip().splitlines()
    return text[0] if text else f"exit={result.returncode}"


def _print_readiness(name: str, state: str, blockers: tuple[str, ...]) -> None:
    print(f"{name}: {state}")
    for blocker in blockers:
        print(f"  - {blocker}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Report compiler and HEP tool availability")
    parser.add_argument(
        "--strict-hep", action="store_true", help="Fail unless all HEP readiness checks pass"
    )
    parser.add_argument(
        "--toolchain", type=Path, default=ROOT / "configs" / "toolchain.env"
    )
    args = parser.parse_args()

    config = load_toolchain_config(args.toolchain) if args.toolchain.is_file() else {}
    configured_paths = {
        "fastjet-config": Path(config["FASTJET3"]) / "bin/fastjet-config"
        if config.get("FASTJET3")
        else None,
        "pythia8-config": Path(config["PYTHIA8"]) / "bin/pythia8-config"
        if config.get("PYTHIA8")
        else None,
        "mg5_aMC": Path(config["MG5_HOME"]) / "bin/mg5_aMC"
        if config.get("MG5_HOME")
        else None,
    }
    for tool in [
        Tool("git"),
        Tool("make"),
        Tool("g++"),
        Tool("python3"),
        Tool("fastjet-config"),
        Tool("pythia8-config"),
        Tool("mg5_aMC"),
    ]:
        configured = configured_paths.get(tool.name)
        path = str(configured) if configured and configured.is_file() else shutil.which(tool.name)
        status = "FOUND" if path else "MISSING"
        detail = version(path, tool.version_args) if path else "-"
        print(f"{tool.name:18} {status:8} {path or '-'} | {detail}")

    core = core_environment_readiness()
    build = upstream_build_readiness(config)
    madgraph, _ = madgraph_readiness(config)
    benchmark_path = ROOT / "benchmarks/upstream/strong-bm1/benchmark.json"
    selected = None
    if benchmark_path.is_file():
        benchmark = json.loads(benchmark_path.read_text(encoding="utf-8"))
        selected = selected_benchmark_readiness(
            ROOT, benchmark, madgraph.state == "READY"
        )

    print()
    _print_readiness("Core environment", core.state, core.blockers)
    _print_readiness("Upstream recast build readiness", build.state, build.blockers)
    _print_readiness(
        "MadGraph LHE-generation tool readiness", madgraph.state, madgraph.blockers
    )
    if selected is None:
        _print_readiness("Selected upstream benchmark readiness", "NOT_CONFIGURED", ())
    else:
        _print_readiness(
            "Selected upstream benchmark readiness", selected.state, selected.blockers
        )

    if core.state == "BLOCKED":
        return 2
    if args.strict_hep and (build.state == "BLOCKED" or madgraph.state == "BLOCKED"):
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
