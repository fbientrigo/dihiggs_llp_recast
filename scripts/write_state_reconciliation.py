#!/usr/bin/env python3
from __future__ import annotations

# ruff: noqa: E501
import argparse
import json
import subprocess
from pathlib import Path


def run(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
    ).stdout.strip()


def repo_state(path: Path, relation: str) -> dict[str, object]:
    return {
        "path": str(path),
        "repository": "dihiggs_ufo" if "ufos" in path.parts else "dihiggs_llp_recast",
        "branch": run(path, "branch", "--show-current"),
        "head": run(path, "rev-parse", "HEAD"),
        "upstream_tracking": run(path, "status", "--short", "--branch").splitlines()[0]
        if run(path, "status", "--short", "--branch")
        else "",
        "dirty_files": run(path, "status", "--porcelain=v1").splitlines(),
        "untracked_files": run(path, "ls-files", "--others", "--exclude-standard").splitlines(),
        "local_only_commits": run(path, "log", "--oneline", "origin/main..HEAD").splitlines(),
        "worktree_relation": relation,
        "remote_urls": run(path, "remote", "-v").splitlines(),
        "submodule_state": run(path, "submodule", "status").splitlines(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timestamp", required=True)
    args = parser.parse_args()
    root = Path(__file__).parents[1]
    report_dir = root / "reports"
    report_dir.mkdir(exist_ok=True)
    states = [
        repo_state(
            Path("/home/fabi/atlas_dihiggs/ufos"),
            "authoritative UFO checkout; read-only for mission",
        ),
        repo_state(
            Path("/home/fabi/atlas_dihiggs/llp_recast"), "original dirty recast checkout; preserved"
        ),
        repo_state(
            Path("/home/fabi/code/dihiggs_llp_recast"),
            "clean recast checkout; older coherent candidate",
        ),
        repo_state(root, "isolated mission worktree from 747b8e3"),
    ]
    payload = {
        "schema": "state_reconciliation.v1",
        "timestamp": args.timestamp,
        "public_references": {
            "dihiggs_ufo": "a5226cc5a58895c11d30b58912980583c127d245",
            "dihiggs_llp_recast": "220f719d001e19a8f870dc37352e2f9452672f1c",
            "recastingCodes": "d4047c744062094c9f88e507bb1ccf69e9fe88d6",
        },
        "selected_ufo_state": str(Path("/home/fabi/atlas_dihiggs/ufos")),
        "selected_recast_base": "747b8e3",
        "states": states,
        "initial_observation": {
            "ufos": "dirty with untracked closure/artifact files; no tracked modifications observed",
            "llp_recast": "dirty: src/dvrecast/cutflow.py and tests/test_cutflow.py modified plus 83 untracked paths",
            "preservation": "no reset, clean, checkout, stash, branch deletion or edits to existing dirty checkouts",
        },
    }
    stem = report_dir / f"state_reconciliation_{args.timestamp}"
    (stem.with_suffix(".json")).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = [
        f"# State reconciliation {args.timestamp}",
        "",
        "Public references were verified against GitHub: UFO `a5226cc`, recast `220f719`, upstream `d4047c7`.",
        "",
        "Selected UFO: `/home/fabi/atlas_dihiggs/ufos` (authoritative frozen Pack A/Pack AA artifacts). Selected recast base: committed local `747b8e3`; the dirty checkout was preserved.",
        "",
        "Initial observation: UFO had no tracked modifications but a large untracked closure/artifact inventory; recast had two tracked modifications and 83 untracked paths. No reset, clean, checkout, stash, branch deletion, or existing-checkout edits were performed.",
        "",
        "| path | branch | HEAD | dirty/untracked | local-only commits |",
        "|---|---|---|---:|---|",
    ]
    for state in states:
        lines.append(
            f"| `{state['path']}` | `{state['branch']}` | `{state['head']}` | {len(state['dirty_files'])}/{len(state['untracked_files'])} | {', '.join(state['local_only_commits']) or 'none'} |"
        )
    lines += [
        "",
        "The full machine-readable state, remote URLs, tracking state, submodule state, dirty files and untracked inventories are in the JSON report. The original recast tracked diff and untracked inventory are snapshotted alongside it.",
    ]
    (stem.with_suffix(".md")).write_text("\n".join(lines) + "\n", encoding="utf-8")
    original = Path("/home/fabi/atlas_dihiggs/llp_recast")
    diff = run(original, "diff", "HEAD")
    (stem.with_name(stem.name + "_recast_tracked.diff")).write_text(
        "\n".join(line.rstrip() for line in diff.splitlines()) + "\n", encoding="utf-8"
    )
    (stem.with_name(stem.name + "_recast_untracked.txt")).write_text(
        run(original, "ls-files", "--others", "--exclude-standard") + "\n", encoding="utf-8"
    )
    (stem.with_name(stem.name + "_ufo_untracked.txt")).write_text(
        run(Path("/home/fabi/atlas_dihiggs/ufos"), "ls-files", "--others", "--exclude-standard")
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
