from __future__ import annotations

import os
import re
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
        return (
            str(configured_path)
            if configured_path.is_file() and os.access(configured_path, os.X_OK)
            else None
        )
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


def madgraph_readiness(
    config: Mapping[str, str],
) -> tuple[Readiness, str | None, str | None]:
    configured = Path(config["MG5_HOME"]) / "bin/mg5_aMC" if config.get("MG5_HOME") else None
    configured = Path(os.environ["MG5_BIN"]) if os.environ.get("MG5_BIN") else configured
    path = resolve_executable("mg5_aMC", configured)
    if path is None:
        fallback = Path.home() / ".local/mg5amcnlo/3.5.3/bin/mg5_aMC"
        path = str(fallback) if fallback.is_file() and os.access(fallback, os.X_OK) else None
    usable = executable_is_usable(path, ("--help",))
    prefix = Path(path).resolve().parents[1] if path else None
    version_file = (
        prefix / "VERSION"
        if path
        else None
    )
    version = None
    if version_file and version_file.is_file():
        lines = version_file.read_text(encoding="utf-8").splitlines()
        if lines:
            _, separator, value = lines[0].partition("=")
            version = value.strip() if separator else None
    blockers = tuple(
        blocker
        for blocker, blocked in (
            ("usable mg5_aMC", not usable),
            ("resolved MadGraph version", usable and not version),
        )
        if blocked
    )
    return Readiness("READY" if not blockers else "BLOCKED", blockers), path, version


def selected_benchmark_readiness(
    repo_root: Path,
    benchmark: Mapping[str, object],
    generation_contract: Mapping[str, object],
    mg5_available: bool,
) -> Readiness:
    blockers: list[str] = []
    identifier = benchmark.get("identifier")
    if not isinstance(identifier, str) or not identifier:
        blockers.append("benchmark identifier is missing")
        identifier = "unknown"

    classification = generation_contract.get("classification")
    if classification in {"INCOMPLETE", "CONTRADICTORY"}:
        blockers.append(f"generation contract is {classification}")
    elif classification not in {"RECOVERED_EXACT", "RECONSTRUCTED"}:
        blockers.append("generation contract classification is missing or invalid")

    card_paths = benchmark.get("card_paths")
    values: list[str] = []
    if isinstance(card_paths, Mapping):
        for value in card_paths.values():
            if isinstance(value, str):
                values.append(value)
            elif isinstance(value, list):
                values.extend(item for item in value if isinstance(item, str))
        missing_cards = [value for value in values if not (repo_root / value).is_file()]
        if missing_cards:
            blockers.append("missing tracked cards: " + ", ".join(missing_cards))
        forbidden = [
            value
            for value in values
            if any(token in value for token in ("pack_a", "pack_aa", "pack_b", "LLscalar_v3_UFO"))
        ]
        if forbidden:
            blockers.append("refusing non-upstream strong-bm1 input: " + ", ".join(forbidden))
    if not values:
        blockers.append("benchmark has no tracked cards")
    parameter = (
        card_paths.get("parameter_or_slha_card") if isinstance(card_paths, Mapping) else None
    )
    if not parameter:
        blockers.append("missing benchmark parameter/SLHA card")
    else:
        parameter_path = repo_root / str(parameter)
        if not parameter_path.is_file():
            blockers.append("missing benchmark parameter/SLHA card")
        else:
            masses: dict[int, float] = {}
            for line in parameter_path.read_text(encoding="utf-8").splitlines():
                match = re.match(r"\s*100002([12])\s+([-+0-9.eE]+)", line)
                if match:
                    masses[1000020 + int(match.group(1))] = float(match.group(2))
            # Asserts the frozen strong-bm1 point identity (gluino/neutralino
            # masses), not the configurable LLP id from dvrecast.config;
            # strong-bm1 stays pinned to PDG 1000022 regardless of what LLP
            # identity a caller configures elsewhere.
            if abs(masses.get(1000021, float("nan")) - 2000.0) > 1e-6:
                blockers.append("SLHA lacks MASS 1000021 = 2000 GeV")
            if abs(masses.get(1000022, float("nan")) - 850.0) > 1e-6:
                blockers.append("SLHA lacks MASS 1000022 = 850 GeV")

    fields = generation_contract.get("fields")
    output = fields.get("output_naming") if isinstance(fields, dict) else None
    names = output.get("value") if isinstance(output, dict) else None
    lhe_names = [item for item in names if isinstance(item, str)] if isinstance(names, list) else []
    if not lhe_names:
        blockers.append("generation contract has no required LHE outputs")
    data_dir = repo_root / "data/upstream" / identifier
    missing_lhe = [name for name in lhe_names if not (data_dir / name).is_file()]
    if missing_lhe:
        blockers.append("missing LHE samples: " + ", ".join(missing_lhe))
    if not mg5_available:
        blockers.append("missing mg5_aMC")

    return Readiness("BLOCKED" if blockers else "NOT_RUN", tuple(blockers))
