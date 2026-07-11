#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class Tool:
    name: str
    required: bool
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Report compiler and HEP tool availability")
    parser.add_argument(
        "--strict-hep", action="store_true", help="Fail unless all optional HEP tools exist"
    )
    args = parser.parse_args()

    tools = [
        Tool("git", True),
        Tool("make", True),
        Tool("g++", True),
        Tool("python3", True),
        Tool("fastjet-config", False),
        Tool("pythia8-config", False),
        Tool("mg5_aMC", False, ("--version",)),
    ]

    missing_required: list[str] = []
    missing_hep: list[str] = []
    for tool in tools:
        path = shutil.which(tool.name)
        status = "FOUND" if path else "MISSING"
        detail = version(path, tool.version_args) if path else "-"
        print(f"{tool.name:18} {status:8} {path or '-'} | {detail}")
        if not path and tool.required:
            missing_required.append(tool.name)
        elif not path:
            missing_hep.append(tool.name)

    if missing_required:
        print(f"\nRequired tools missing: {', '.join(missing_required)}")
        return 2
    if args.strict_hep and missing_hep:
        print(f"\nHEP tools missing: {', '.join(missing_hep)}")
        return 3

    print("\nCore environment is usable." if not missing_required else "")
    if missing_hep:
        print("HEP stack is incomplete; upstream compilation remains BLOCKED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
