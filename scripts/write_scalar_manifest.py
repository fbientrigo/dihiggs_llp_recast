#!/usr/bin/env python3
from __future__ import annotations

# ruff: noqa: E501
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).parents[1]
UFO = Path("/home/fabi/atlas_dihiggs/ufos")
LHE = UFO / "pack_aa/inputs/pack_a_A_PI_NATIVE_200_source.lhe.gz"
PACK_A = UFO / "releases/pack_a/frozen/pi_ufo_baseline_v1_frozen_hotfix1.zip"
AA_CONFIG = UFO / "pack_aa/configs/ctau_1000_bb.yaml"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(path: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(path), *args], capture_output=True, text=True, check=False
    ).stdout.strip()


def version(command: list[str]) -> str:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    return (
        (result.stdout or result.stderr).strip().splitlines()[0]
        if (result.stdout or result.stderr).strip()
        else f"exit={result.returncode}"
    )


def main() -> int:
    out = ROOT / "results/scalar_h2_smoke"
    out.mkdir(parents=True, exist_ok=True)
    outputs = [
        out / "input_audit.json",
        out / "cutflow.json",
        out / "cutflow.csv",
        out / "atlas_constants_check.json",
        out / "plots/diagnostics.json",
        *sorted((out / "plots").glob("*.png")),
    ]
    manifest = {
        "schema": "scalar_h2.smoke_manifest.v1",
        "status": "PROVISIONAL_SCALAR_SMOKE_EXECUTED",
        "ufo": {
            "path": str(UFO),
            "commit": git(UFO, "rev-parse", "HEAD"),
            "dirty_state": git(UFO, "status", "--porcelain=v1"),
        },
        "pack_a": {
            "artifact_path": str(PACK_A),
            "artifact_sha256": sha256(PACK_A),
            "smoke_sigma_kept_separate": True,
        },
        "input_lhe": {
            "path": str(LHE),
            "sha256": sha256(LHE),
            "unique_production_events": 100,
            "decay_replicas": 0,
        },
        "pack_aa_config": {"path": str(AA_CONFIG), "sha256": sha256(AA_CONFIG)},
        "recast": {
            "path": str(ROOT),
            "implementation_base_commit": "747b8e3bdee31e22cb03a2efcc526cde7420f2d6",
            "upstream_commit": "d4047c744062094c9f88e507bb1ccf69e9fe88d6",
            "upstream_submodule_immutable": True,
            "adapter_overlay": "src/scalar_h2_recast.cc",
            "adapter_overlay_sha256": sha256(ROOT / "src/scalar_h2_recast.cc"),
        },
        "tools": {
            "MG5": version(["/home/fabi/.local/mg5amcnlo/3.5.3/bin/mg5_aMC", "--version"]),
            "Pythia8": version(["/home/fabi/.local/pythia8308/bin/pythia8-config", "--version"]),
            "FastJet": version(["/home/fabi/.local/fastjet-3.4.0/bin/fastjet-config", "--version"]),
            "compiler": version(["g++", "--version"]),
            "python": version(["python3", "--version"]),
        },
        "analysis": {
            "mode": "scalar-h2",
            "default_mode": "upstream-susy",
            "llp_pdg": 9000006,
            "mass_GeV": 200.0,
            "ctau_mm": 1000.0,
            "is_resonance": False,
            "decay": [5, -5],
            "branching_ratio": 1.0,
            "seed": 900006005,
            "single_pythia_decay_shower_hadronization_pass": True,
            "unique_production_events": 100,
            "decay_replicas": 0,
        },
        "commands": {
            "git status --short --branch": 0,
            "git submodule status": 0,
            "git diff --check": 0,
            "make hep-preflight": 0,
            "make build-upstream": 0,
            "initial make bootstrap network attempt": 2,
            "local pinned submodule seeding": 0,
            "scalar build": 0,
            "input audit": 0,
            "100-event scalar smoke": 0,
            "cutflow extraction": 0,
            "plot generation": 0,
            "ATLAS constants check": 0,
        },
        "output_sha256": {
            str(path.relative_to(ROOT)): sha256(path) for path in outputs if path.is_file()
        },
        "normalization_disclaimer": "PROVISIONAL_ENGINEERING_SMOKE; NOT_MODEL_DERIVED; UPSTREAM_REGRESSION_PENDING; no sigma*BR^2*Aepsilon, yield, exclusion or limit",
        "validation_limitations": [
            "upstream strong-bm1 inputs remain blocked",
            "no Pack B inputs used",
            "no upstream recast validation or ATLAS exclusion",
            "100 events only and no independent replica uncertainty",
        ],
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
