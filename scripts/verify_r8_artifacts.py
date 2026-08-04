#!/usr/bin/env python3
"""Verify the committed R8 result artifacts (results/r8_h2_model_derived_4b/)
without rerunning MadGraph, Pythia, or the C++ recast.

This is the --verify-existing engine behind scripts/run_r8_reproduction.sh.
It checks, purely from what is already on disk plus the fast Python test
suite:

  1. every file hash recorded in artifact_manifest.json matches disk;
  2. the canonical LHE input hashes/event-counts recorded in
     input_manifest.json match the required upstream values (and, if the
     raw LHE happens to be cached locally under data/raw/, its live hash
     and event count too -- best effort, since raw LHE is intentionally not
     committed, see AGENTS.md);
  3. both runs' committed recast.log report exactly 1000 processed events;
  4. the normalization arithmetic recomputed from the committed recast.log
     files matches the numeric fields stored in normalization.json (the
     validation-status vocabulary strings are excluded from this numeric
     comparison by design -- see docs/R8_H2_MODEL_DERIVED_4B_RESULT.md
     "Validation status");
  5. the relabeller's atomic-publish contract (scripts/relabel_lhe_pdg.py)
     holds, including its negative paths, via tests/test_relabel_lhe_pdg.py.

Exits 0 only if every check passes.
"""

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
    cache_dir = os.path.join(ROOT, "data", "raw", "r8_h2_model_derived_4b")
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


def main():
    checks = [
        check_artifact_manifest(),
        check_canonical_lhe_hashes(),
        check_relabel_script_hash_matches_manifest(),
        check_run_event_counts(),
        check_normalization_arithmetic(),
        check_relabel_atomicity(),
    ]
    if all(checks):
        print("\n[PASS] all R8 --verify-existing checks passed")
        return 0
    print("\n[FAIL] one or more R8 --verify-existing checks failed", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
