from __future__ import annotations

import json
from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from typing import Any

from .config import load_toolchain_config
from .readiness import (
    madgraph_readiness,
    selected_benchmark_readiness,
    upstream_build_readiness,
)


def _hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _card_paths(card_paths: object) -> list[str]:
    if not isinstance(card_paths, Mapping):
        return []
    paths: list[str] = []
    for value in card_paths.values():
        if isinstance(value, str):
            paths.append(value)
        elif isinstance(value, list):
            paths.extend(item for item in value if isinstance(item, str))
    return paths


def prepare_benchmark(repo_root: Path, identifier: str, *, dry_run: bool) -> dict[str, Any]:
    root = repo_root.resolve()
    benchmark_dir = root / "benchmarks/upstream" / identifier
    benchmark = json.loads((benchmark_dir / "benchmark.json").read_text(encoding="utf-8"))
    contract = json.loads(
        (benchmark_dir / "generation_contract.json").read_text(encoding="utf-8")
    )
    if benchmark.get("identifier") != identifier or contract.get("benchmark") != identifier:
        raise ValueError("benchmark identifiers do not match the requested workspace")

    blockers: list[str] = []
    classification = contract.get("classification")
    fields = contract.get("fields")
    states = (
        {
            field.get("state")
            for field in fields.values()
            if isinstance(field, Mapping)
        }
        if isinstance(fields, Mapping)
        else set()
    )
    expected_classification = (
        "CONTRADICTORY"
        if "CONTRADICTORY" in states
        else "INCOMPLETE"
        if "UNKNOWN" in states
        else "RECONSTRUCTED"
        if states & {"INFERRED", "CALCULATED"}
        else "RECOVERED_EXACT"
    )
    if classification != expected_classification:
        blockers.append(
            f"generation contract classification should be {expected_classification}"
        )
    card_paths = benchmark.get("card_paths")
    cards: list[dict[str, Any]] = []
    for relative in _card_paths(card_paths):
        path = (root / relative).resolve()
        if root not in path.parents:
            blockers.append(f"card is outside repository: {relative}")
        elif path.is_file():
            cards.append({"path": relative, "sha256": _hash(path)})

    if isinstance(card_paths, Mapping):
        parameter = card_paths.get("parameter_or_slha_card")
        related = card_paths.get("related_but_nonmatching_slha_card")
        if parameter and (parameter == related or "2800_10" in str(parameter)):
            blockers.append("refusing nonmatching 2800/10 SLHA for strong-bm1")

    toolchain_path = root / "configs/toolchain.env"
    toolchain = load_toolchain_config(toolchain_path) if toolchain_path.is_file() else {}
    mg5, mg5_path, mg5_version = madgraph_readiness(toolchain)
    build = upstream_build_readiness(toolchain)
    blockers.extend(
        selected_benchmark_readiness(
            root, benchmark, contract, mg5_available=mg5.state == "READY"
        ).blockers
    )

    output = fields.get("output_naming") if isinstance(fields, Mapping) else None
    names = output.get("value") if isinstance(output, Mapping) else None
    required_inputs = (
        [name for name in names if isinstance(name, str)]
        if isinstance(names, list)
        else []
    )
    data_dir = root / "data/upstream" / identifier
    results_dir = root / "results/upstream_validation" / identifier
    missing_inputs = [name for name in required_inputs if not (data_dir / name).is_file()]

    if not dry_run and not blockers:
        (data_dir / "mg5_processes").mkdir(parents=True, exist_ok=True)
        results_dir.mkdir(parents=True, exist_ok=True)

    return {
        "schema_version": 1,
        "benchmark": identifier,
        "state": "BLOCKED" if blockers else "NOT_RUN",
        "dry_run": dry_run,
        "contract_classification": classification,
        "generation_allowed": not blockers,
        "toolchain_status": (
            "READY" if mg5.state == "READY" and build.state == "READY" else "BLOCKED"
        ),
        "benchmark_input_status": (
            "READY" if not any("missing LHE samples" in item for item in blockers)
            and classification in {"RECOVERED_EXACT", "RECONSTRUCTED"}
            else "BLOCKED_EXTERNAL_ARTIFACT"
        ),
        "blockers": blockers,
        "cards": cards,
        "madgraph": {"state": mg5.state, "path": mg5_path, "version": mg5_version},
        "toolchain": {
            "mg5": {"state": mg5.state, "path": mg5_path, "version": mg5_version},
            "pythia8": {"state": "READY" if not build.blockers else "BLOCKED"},
            "fastjet": {"state": "READY" if not build.blockers else "BLOCKED"},
        },
        "workspace": {"data": str(data_dir), "results": str(results_dir)},
        "missing_inputs": missing_inputs,
    }
