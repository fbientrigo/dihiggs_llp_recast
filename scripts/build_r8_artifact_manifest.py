#!/usr/bin/env python3
"""Hash every R8 result/source/card artifact into artifact_manifest.json.
Run last, after all other results/r8_h2_model_derived_4b/*.{csv,json} and
docs/R8_H2_MODEL_DERIVED_4B_RESULT.md have been written, so the manifest
reflects final content.
"""

import hashlib
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(ROOT, "results", "r8_h2_model_derived_4b")

TRACKED_PATHS = [
    "cards/r8_h2_model_derived_4b/physical_run_01.cmnd",
    "cards/r8_h2_model_derived_4b/physical_run_02.cmnd",
    "scripts/relabel_lhe_pdg.py",
    "scripts/build_r8_results.py",
    "scripts/run_r8_reproduction.sh",
    "scripts/verify_r8_artifacts.py",
    "scripts/compare_r8_manifests.py",
    "scripts/lhe_identity.py",
    "src/r8_geometry_driver.cc",
    "src/dvrecast/r8_cutflow.py",
    "src/dvrecast/r8_geometry.py",
    "src/dvrecast/r8_normalization.py",
    "src/dvrecast/statistics.py",
    "docs/R8_H2_MODEL_DERIVED_4B_RESULT.md",
]


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    manifest = {"schema": "llp_recast.r8_h2_model_derived_4b.artifact_manifest.v1", "files": {}}

    for rel_path in TRACKED_PATHS:
        abs_path = os.path.join(ROOT, rel_path)
        if os.path.exists(abs_path):
            manifest["files"][rel_path] = sha256_of(abs_path)

    for dirpath, _dirnames, filenames in os.walk(RESULTS_DIR):
        for name in sorted(filenames):
            if name == "artifact_manifest.json":
                continue
            abs_path = os.path.join(dirpath, name)
            rel_path = os.path.relpath(abs_path, ROOT)
            manifest["files"][rel_path] = sha256_of(abs_path)

    manifest["files"] = dict(sorted(manifest["files"].items()))

    out_path = os.path.join(RESULTS_DIR, "artifact_manifest.json")
    with open(out_path, "w") as fh:
        json.dump(manifest, fh, indent=2)
    print(f"OK: wrote {out_path} with {len(manifest['files'])} entries")


if __name__ == "__main__":
    main()
