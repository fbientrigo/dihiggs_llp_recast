from __future__ import annotations

import shutil
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Readiness:
    state: str
    blockers: tuple[str, ...]


def resolve_executable(name: str, configured_path: Path | None = None) -> str | None:
    if configured_path is not None:
        return str(configured_path) if configured_path.is_file() else None
    return shutil.which(name)


def executable_is_usable(path: str | None, version_args: tuple[str, ...] = ("--version",)) -> bool:
    if path is None:
        return False
    try:
        result = subprocess.run(
            [path, *version_args], capture_output=True, text=True, timeout=10, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def core_environment_readiness() -> Readiness:
    missing = tuple(
        name for name in ("git", "make", "g++", "python3") if shutil.which(name) is None
    )
    return Readiness("READY" if not missing else "BLOCKED", missing)


def upstream_build_readiness(config: Mapping[str, str]) -> Readiness:
    blockers: list[str] = []
    pythia_value = config.get("PYTHIA8")
    fastjet_value = config.get("FASTJET3")

    if not pythia_value:
        blockers.append("PYTHIA8 prefix is not configured")
    else:
        pythia = Path(pythia_value)
        header = pythia / "include/Pythia8/Pythia.h"
        shared = pythia / "lib/libpythia8.so"
        static = pythia / "lib/libpythia8.a"
        pythia_config = pythia / "bin/pythia8-config"
        if not header.is_file():
            blockers.append(str(header))
        if not shared.is_file() and not static.is_file():
            blockers.append(f"{shared} or {static}")
        if not executable_is_usable(str(pythia_config)):
            blockers.append(f"usable {pythia_config}")

    if not fastjet_value:
        blockers.append("FASTJET3 prefix is not configured")
    else:
        fastjet = Path(fastjet_value)
        include = fastjet / "include/fastjet"
        library = fastjet / "lib"
        fastjet_config = fastjet / "bin/fastjet-config"
        if not include.is_dir():
            blockers.append(str(include))
        if not library.is_dir():
            blockers.append(str(library))
        if not executable_is_usable(str(fastjet_config)):
            blockers.append(f"usable {fastjet_config}")

    compiler = config.get("CXX", "g++")
    if not executable_is_usable(resolve_executable(compiler)):
        blockers.append(f"usable {compiler}")
    if not executable_is_usable(shutil.which("make")):
        blockers.append("usable make")

    return Readiness("READY" if not blockers else "BLOCKED", tuple(blockers))


def madgraph_readiness(config: Mapping[str, str]) -> tuple[Readiness, str | None]:
    configured = (
        Path(config["MG5_HOME"]) / "bin/mg5_aMC" if config.get("MG5_HOME") else None
    )
    path = resolve_executable("mg5_aMC", configured)
    usable = executable_is_usable(path)
    blockers = () if usable else ("usable mg5_aMC",)
    return Readiness("READY" if usable else "BLOCKED", blockers), path


def selected_benchmark_readiness(
    repo_root: Path, benchmark: Mapping[str, object], mg5_available: bool
) -> Readiness:
    blockers: list[str] = []
    card_paths = benchmark.get("card_paths")
    parameter_card = (
        card_paths.get("parameter_or_slha_card") if isinstance(card_paths, dict) else None
    )
    if not parameter_card:
        blockers.append("missing exact bm1 SLHA/generation configuration")

    missing_inputs = benchmark.get("missing_inputs")
    lhe_names = (
        [item for item in missing_inputs if isinstance(item, str) and item.endswith(".lhe.gz")]
        if isinstance(missing_inputs, list)
        else []
    )
    data_dir = repo_root / "data/upstream/strong-bm1"
    missing_lhe = [name for name in lhe_names if not (data_dir / name).is_file()]
    if missing_lhe:
        blockers.append("missing LHE samples: " + ", ".join(missing_lhe))
    if not mg5_available:
        blockers.append("missing mg5_aMC")

    return Readiness("BLOCKED" if blockers else "NOT_RUN", tuple(blockers))
