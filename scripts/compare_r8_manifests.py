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

Two tiers of expected difference are recognized:

- HARD_ALLOWED_TO_DIFFER: paths that legitimately embed environment-
  specific content (the working-directory path in run_0N/command.txt) and
  are never a statement about physics content. A hash difference here is
  always accepted.
- CHECKSUMS_FILES: run_0N/input_checksums.txt records three hashes --
  the patched recast executable, the .cmnd card, and the relabelled LHE
  input -- on separate lines. Only the LHE line is allowed to differ
  (scripts/relabel_lhe_pdg.py's gzip writer is deterministic given
  identical content, but a different gzip library/version could still
  produce different header bytes for the same decompressed bytes -- see
  scripts/verify_r8_artifacts.py's lhe_content_identity check, which is
  the authoritative arbiter of whether that difference is real physics
  drift). The executable and card lines must match exactly: a change
  there means a fresh reproduction used different recast-binary or card
  provenance than the committed reference, which is real drift and must
  fail closed, not be silently waved through because the file's overall
  hash changed for an unrelated (LHE-line) reason.

  Comparing at this granularity requires the *content* of the reference
  input_checksums.txt files, not just their hash -- scripts/
  run_r8_reproduction.sh preserves copies of them alongside the reference
  manifest (in the same scratch directory) specifically so this script can
  read them. If no such copy is found for a checksums file whose hash
  differs, this fails closed rather than assuming the difference is
  LHE-only.

Everything else must match exactly, or this exits nonzero.
"""

import json
import os
import sys

HARD_ALLOWED_TO_DIFFER = {
    "results/r8_h2_model_derived_4b/run_01/command.txt",
    "results/r8_h2_model_derived_4b/run_02/command.txt",
}

CHECKSUMS_FILES = {
    "results/r8_h2_model_derived_4b/run_01/input_checksums.txt": (
        "run_01_input_checksums.reference.txt"
    ),
    "results/r8_h2_model_derived_4b/run_02/input_checksums.txt": (
        "run_02_input_checksums.reference.txt"
    ),
}


def _parse_checksums(path):
    """Parse a sha256sum-format file (comment lines starting with '#'
    ignored) into {recorded_path: digest}."""
    entries = {}
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            digest, recorded_path = line.split(None, 1)
            entries[recorded_path.strip()] = digest
    return entries


def _compare_checksums_line_by_line(path, reference_copy_path, new_actual_path):
    """Only the .lhe.gz-suffixed line may differ between the preserved
    reference copy and the freshly-written file; every other line
    (executable, card) must match exactly."""
    ref_entries = _parse_checksums(reference_copy_path)
    new_entries = _parse_checksums(new_actual_path)
    ok = True
    for recorded_path in sorted(set(ref_entries) | set(new_entries)):
        ref_hash = ref_entries.get(recorded_path)
        new_hash = new_entries.get(recorded_path)
        if ref_hash is None or new_hash is None:
            print(
                f"[FAIL] {path}: {recorded_path} present in only one of the "
                "reference/new input_checksums.txt",
                file=sys.stderr,
            )
            ok = False
            continue
        if ref_hash == new_hash:
            continue
        if recorded_path.endswith(".lhe.gz"):
            print(
                f"[INFO] {path}: {recorded_path} hash changed (reference {ref_hash}, "
                f"new {new_hash}) -- gzip-metadata difference, not necessarily physics "
                "drift; run `scripts/verify_r8_artifacts.py --only lhe_content_identity` "
                "to confirm the decompressed content is unchanged (fails closed on real "
                "content drift)."
            )
            continue
        print(
            f"[FAIL] {path}: {recorded_path} hash drifted (reference {ref_hash}, "
            f"new {new_hash}) -- this is not the LHE line and must match exactly; "
            "recast-binary or card provenance changed",
            file=sys.stderr,
        )
        ok = False
    return ok


def main():
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} reference_manifest.json new_manifest.json", file=sys.stderr)
        return 2
    reference_path, new_path = sys.argv[1], sys.argv[2]
    reference_dir = os.path.dirname(os.path.abspath(reference_path))
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
        if path in HARD_ALLOWED_TO_DIFFER:
            print(f"[INFO] {path}: hash changed (allowed: environment-specific content)")
            continue
        if path in CHECKSUMS_FILES:
            reference_copy = os.path.join(reference_dir, CHECKSUMS_FILES[path])
            if not os.path.exists(reference_copy):
                print(
                    f"[FAIL] {path}: hash changed but no preserved reference copy "
                    f"({reference_copy}) was found to compare line-by-line -- cannot "
                    "confirm the difference is confined to the LHE line, failing closed",
                    file=sys.stderr,
                )
                ok = False
                continue
            line_ok = _compare_checksums_line_by_line(
                path, reference_copy, os.path.join(repo_root, path)
            )
            ok = ok and line_ok
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
