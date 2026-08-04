#!/usr/bin/env python3
"""Verify the committed R8 result artifacts (results/r8_h2_model_derived_4b/)
without rerunning MadGraph, Pythia, or the C++ recast.

This is the --verify-existing engine behind scripts/run_r8_reproduction.sh
(also used, via --only, by its --regenerate-inputs-only mode). It checks,
purely from what is already on disk plus the fast Python test suite:

  1. every file hash recorded in artifact_manifest.json matches disk;
  2. the canonical LHE input hashes/event-counts recorded in
     input_manifest.json match the required upstream values (and, if the
     raw LHE happens to be cached locally under data/raw/, its live hash
     and event count too -- best effort, since raw LHE is intentionally not
     committed, see AGENTS.md);
  3. input_manifest.json's relabel.script_sha256 matches the live
     scripts/relabel_lhe_pdg.py;
  4. both runs' committed recast.log report exactly 1000 processed events;
  5. the normalization arithmetic recomputed from the committed recast.log
     files matches the numeric fields stored in normalization.json (the
     validation-status vocabulary strings are excluded from this numeric
     comparison by design -- see docs/R8_H2_MODEL_DERIVED_4B_RESULT.md
     "Validation status");
  6. the relabeller's atomic-publish contract (scripts/relabel_lhe_pdg.py)
     holds, including its negative paths, via tests/test_relabel_lhe_pdg.py;
  7. if a cached relabelled LHE is present locally, its *decompressed*
     content hash matches the canonical_uncompressed_sha256 recorded in
     input_manifest.json's lhe_identity block -- the physics-content
     identity check. A mismatch on the compressed (gzip) hash alone, with
     matching decompressed content, is reported as informational, not a
     failure: gzip header metadata (mtime, embedded filename) is not
     physics content. An actual decompressed-content mismatch fails closed.

Exits 0 only if every requested check passes.
"""

import argparse
import gzip
import hashlib
import json
import math
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(ROOT, "results", "r8_h2_model_derived_4b")
DATA_DIR = os.path.join(ROOT, "data", "raw", "r8_h2_model_derived_4b")
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

REQUIRED_LHE_SHA256 = {
    "run_01": "1c580b7a590f9bbfbf213eeef0e54fdcc4b6c1dce3f13bc0ed5278f6f3aec202",
    "run_02": "385faebf45403c224ce374488c3e51a06be56b13ec6b095f92393d0c8f4b1bfa",
}
REQUIRED_EVENTS_PER_RUN = 1000


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_of_decompressed(gz_path):
    h = hashlib.sha256()
    with gzip.open(gz_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fail(msg):
    print(f"[FAIL] {msg}", file=sys.stderr)
    return False


def check_artifact_manifest():
    ok = True
    with open(os.path.join(RESULTS_DIR, "artifact_manifest.json")) as fh:
        manifest = json.load(fh)
    for rel_path, expected in manifest["files"].items():
        abs_path = os.path.join(ROOT, rel_path)
        if not os.path.exists(abs_path):
            ok = fail(f"missing committed artifact: {rel_path}") and ok
            continue
        actual = sha256_of(abs_path)
        if actual != expected:
            ok = fail(f"hash mismatch: {rel_path} (expected {expected}, got {actual})") and ok
    if ok:
        print(f"[OK] {len(manifest['files'])} artifact hashes match artifact_manifest.json")
    return ok


def check_canonical_lhe_hashes():
    ok = True
    with open(os.path.join(RESULTS_DIR, "input_manifest.json")) as fh:
        manifest = json.load(fh)
    for run, expected in REQUIRED_LHE_SHA256.items():
        entry = manifest["lhe_inputs"][run]
        if entry["canonical_sha256"] != expected:
            ok = fail(
                f"{run}: input_manifest.json records canonical_sha256="
                f"{entry['canonical_sha256']!r}, required {expected!r}"
            ) and ok
        elif entry["n_events"] != REQUIRED_EVENTS_PER_RUN:
            ok = fail(f"{run}: input_manifest.json records n_events={entry['n_events']!r}") and ok
        else:
            print(f"[OK] {run}: canonical LHE sha256/event-count recorded correctly")

    # Best-effort: verify a locally cached copy of the raw canonical LHE, if
    # one happens to be present (it is not committed; see AGENTS.md).
    cache_dir = DATA_DIR
    for run, expected in REQUIRED_LHE_SHA256.items():
        for candidate in (f"canonical_{run}.lhe.gz", f"{run}_unweighted_events.lhe.gz"):
            path = os.path.join(cache_dir, candidate)
            if not os.path.exists(path):
                continue
            actual = sha256_of(path)
            if actual != expected:
                msg = f"{run}: cached LHE {path} has sha256 {actual}, expected {expected}"
                ok = fail(msg) and ok
                continue
            with gzip.open(path, "rt") as fh:
                n_events = sum(1 for line in fh if line.strip() == "</event>")
            if n_events != REQUIRED_EVENTS_PER_RUN:
                ok = fail(f"{run}: cached LHE {path} has {n_events} events, expected 1000") and ok
            else:
                print(f"[OK] {run}: cached raw LHE hash + event count verified live ({path})")
    return ok


def check_relabel_script_hash_matches_manifest():
    """input_manifest.json's lhe_inputs.relabel.script_sha256 must track the
    live scripts/relabel_lhe_pdg.py, so provenance never silently drifts
    from the script that would actually run on a fresh reproduction."""
    with open(os.path.join(RESULTS_DIR, "input_manifest.json")) as fh:
        manifest = json.load(fh)
    recorded = manifest["lhe_inputs"]["relabel"]["script_sha256"]
    live = sha256_of(os.path.join(ROOT, "scripts", "relabel_lhe_pdg.py"))
    if recorded != live:
        return fail(
            "input_manifest.json lhe_inputs.relabel.script_sha256 "
            f"({recorded}) does not match the live scripts/relabel_lhe_pdg.py ({live}); "
            "update the manifest (see script_sha256_note) to match the current script"
        )
    print("[OK] input_manifest.json relabel.script_sha256 matches the live relabel_lhe_pdg.py")
    return True


def check_lhe_content_identity():
    """If a deterministically-relabelled LHE is cached locally
    (data/raw/r8_h2_model_derived_4b/relabelled_run_0N.lhe.gz), verify its
    *decompressed* content against input_manifest.json's
    lhe_identity.canonical_uncompressed_sha256 for that run. This is the
    physics-content identity check: it fails closed only on an actual
    decompressed-content difference. A difference in the compressed (gzip)
    hash alone -- e.g. a different gzip library/version producing different
    header bytes for identical content -- is reported as informational, not
    a failure, matching lhe_identity's documented gzip_contract.
    """
    with open(os.path.join(RESULTS_DIR, "input_manifest.json")) as fh:
        manifest = json.load(fh)

    ok = True
    checked_any = False
    for run in ("run_01", "run_02"):
        identity = manifest["lhe_inputs"][run]["lhe_identity"]
        path = os.path.join(DATA_DIR, f"relabelled_{run}.lhe.gz")
        if not os.path.exists(path):
            print(f"[INFO] {run}: no cached relabelled LHE at {path}; skipping this check")
            continue
        checked_any = True

        actual_uncompressed = sha256_of_decompressed(path)
        expected_uncompressed = identity["canonical_uncompressed_sha256"]
        if actual_uncompressed != expected_uncompressed:
            ok = fail(
                f"{run}: DECOMPRESSED content differs from the recorded canonical identity "
                f"(recorded {expected_uncompressed}, actual {actual_uncompressed}) -- this is "
                "real physics-content drift, not a gzip-metadata difference"
            ) and ok
            continue

        actual_gzip = sha256_of(path)
        expected_gzip = identity["deterministic_relabelled_gzip_sha256"]
        if actual_gzip != expected_gzip:
            print(
                f"[INFO] {run}: compressed gzip hash differs from the recorded deterministic "
                f"hash (recorded {expected_gzip}, actual {actual_gzip}) but decompressed content "
                "is identical -- gzip-metadata-only difference, not physics drift"
            )
        print(f"[OK] {run}: cached relabelled LHE decompressed content matches canonical hash")

    if not checked_any:
        print("[INFO] no cached relabelled LHE for either run; content-identity check skipped")
    return ok


def check_run_event_counts():
    ok = True
    for run in ("01", "02"):
        log_path = os.path.join(RESULTS_DIR, f"run_{run}", "recast.log")
        with open(log_path) as fh:
            text = fh.read()
        match = re.search(r"All Events:\s+([0-9.eE+]+)", text)
        if not match or int(float(match.group(1))) != REQUIRED_EVENTS_PER_RUN:
            ok = fail(f"run_{run}: recast.log does not report 1000 processed events") and ok
        else:
            print(f"[OK] run_{run}: recast.log reports 1000 processed events")
    return ok


def check_normalization_arithmetic():
    from build_r8_results import build_normalization  # noqa: E402

    from dvrecast.r8_cutflow import parse_recast_log  # noqa: E402

    run_results = []
    for run in ("01", "02"):
        with open(os.path.join(RESULTS_DIR, f"run_{run}", "recast.log")) as fh:
            run_results.append(parse_recast_log(fh.read()))
    recomputed = build_normalization(run_results)

    with open(os.path.join(RESULTS_DIR, "normalization.json")) as fh:
        stored = json.load(fh)

    ok = True
    for field in ("sigma_H2H2_pb", "BR_bb_squared", "sigma_4b_fb"):
        if recomputed[field] != stored[field]:
            msg = f"{field} changed: stored {stored[field]}, recomputed {recomputed[field]}"
            ok = fail(msg) and ok

    numeric_fields = (
        "acc_total",
        "n_total",
        "a_eff_acc",
        "a_eff_acc_x_eff",
        "visible_sigma_fb_acc_x_eff",
        "insufficient_mc_statistics",
    )
    for region in ("Trackless", "High-pT"):
        for field in numeric_fields:
            r_val = recomputed["regions"][region][field]
            s_val = stored["regions"][region][field]
            same = (
                math.isclose(r_val, s_val, rel_tol=1e-12, abs_tol=1e-15)
                if isinstance(r_val, float)
                else r_val == s_val
            )
            if not same:
                ok = fail(f"{region}.{field} changed: stored {s_val}, recomputed {r_val}") and ok

    if ok:
        print(
            "[OK] normalization arithmetic recomputed from committed recast.log matches "
            "normalization.json (Trackless A x eff and High-pT status unchanged)"
        )
    return ok


def check_relabel_atomicity():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_relabel_lhe_pdg.py", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    sys.stdout.write(result.stdout)
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        return fail("tests/test_relabel_lhe_pdg.py failed: atomic-publish contract not verified")
    print("[OK] relabel atomic-publish contract verified (including negative paths)")
    return True


CHECKS = {
    "artifact_manifest": check_artifact_manifest,
    "canonical_lhe_hashes": check_canonical_lhe_hashes,
    "relabel_script_hash": check_relabel_script_hash_matches_manifest,
    "lhe_content_identity": check_lhe_content_identity,
    "run_event_counts": check_run_event_counts,
    "normalization_arithmetic": check_normalization_arithmetic,
    "relabel_atomicity": check_relabel_atomicity,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only",
        help=f"comma-separated subset of checks to run: {','.join(CHECKS)} (default: all)",
    )
    args = parser.parse_args()

    if args.only:
        names = [n.strip() for n in args.only.split(",") if n.strip()]
        unknown = [n for n in names if n not in CHECKS]
        if unknown:
            print(f"[ERROR] unknown check name(s): {', '.join(unknown)}", file=sys.stderr)
            print(f"        available: {', '.join(CHECKS)}", file=sys.stderr)
            return 2
    else:
        names = list(CHECKS)

    results = [CHECKS[name]() for name in names]
    if all(results):
        print(f"\n[PASS] all requested R8 checks passed ({', '.join(names)})")
        return 0
    print("\n[FAIL] one or more R8 checks failed", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
