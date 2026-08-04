#!/usr/bin/env python3
"""Compare a freshly-regenerated results/r8_h2_model_derived_4b/
artifact_manifest.json against a preserved reference snapshot (normally the
manifest as committed before a full scripts/run_r8_reproduction.sh run).

Without this comparison, a full reproduction that regenerates
artifact_manifest.json from its own freshly-written outputs would "verify"
against itself: a drifted cutflow, geometry result, or acceptance number
would self-sign and pass a hash check that only ever compares files to a
manifest built from those same files. This script instead compares the new
manifest to the manifest that was committed *before* the run, so any
unexpected drift is caught.

A small set of paths are allowed to differ (they legitimately embed
environment-specific data such as the working directory); everything else
must match exactly, or this exits nonzero.
"""

import json
import sys

ALLOWED_TO_DIFFER = {
    "results/r8_h2_model_derived_4b/run_01/command.txt",
    "results/r8_h2_model_derived_4b/run_02/command.txt",
}


def main():
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} reference_manifest.json new_manifest.json", file=sys.stderr)
        return 2
    reference_path, new_path = sys.argv[1], sys.argv[2]

    with open(reference_path) as fh:
        reference = json.load(fh)["files"]
    with open(new_path) as fh:
        new = json.load(fh)["files"]

    ok = True
    for path, expected in reference.items():
        if path not in new:
            msg = f"[FAIL] {path}: present in reference manifest, missing from new run"
            print(msg, file=sys.stderr)
            ok = False
            continue
        actual = new[path]
        if actual == expected:
            continue
        if path in ALLOWED_TO_DIFFER:
            print(f"[INFO] {path}: hash changed (allowed: environment-specific content)")
            continue
        print(
            f"[FAIL] {path}: hash drifted from the committed reference "
            f"(reference {expected}, new run {actual}) -- reproduction did not "
            "reproduce the committed result",
            file=sys.stderr,
        )
        ok = False

    new_only = sorted(set(new) - set(reference))
    for path in new_only:
        print(f"[INFO] {path}: new in this run, not present in the reference manifest")

    if ok:
        print(f"[OK] {len(reference)} reference-manifest entries reproduced "
              f"(or allow-listed) in the fresh run")
        return 0
    print("[FAIL] fresh run did not reproduce the committed reference manifest", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
