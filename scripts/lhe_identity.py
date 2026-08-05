#!/usr/bin/env python3
"""Compute the canonical identity of a relabelled LHE input.

Distinguishes three separate hashes for a relabelled .lhe.gz file:

- source_lhe_sha256: sha256 of the untouched canonical (pre-relabel) LHE.
- canonical_uncompressed_sha256: sha256 of the *decompressed* relabelled
  event stream -- the physics-content identity. Two relabel runs that
  decompress to the same bytes represent the same physics regardless of
  gzip header metadata (mtime, embedded filename, compression level).
- deterministic_relabelled_gzip_sha256: sha256 of the compressed .lhe.gz
  file produced by the current deterministic writer in
  scripts/relabel_lhe_pdg.py (fixed mtime=0, empty embedded filename).
  Stable across repeated runs on the same machine/gzip implementation, but
  is not itself a physics statement -- content equivalence must be judged
  by canonical_uncompressed_sha256, not this hash.

Used both to (re)compute the identity block recorded in
results/r8_h2_model_derived_4b/input_manifest.json and by
scripts/verify_r8_artifacts.py to check a fresh relabel against that record
without treating compressed-metadata-only differences as physics drift.
"""

import argparse
import gzip
import hashlib
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from relabel_lhe_pdg import relabel  # noqa: E402


def sha256_of_file(path):
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


def compute_identity(canonical_lhe_path, from_pdg, to_pdg, expected_events, expected_relabelled):
    """Relabel canonical_lhe_path into a private temporary file and return
    its identity hashes without touching any repository path. Raises on any
    validation failure (propagated from relabel())."""
    source_lhe_sha256 = sha256_of_file(canonical_lhe_path)
    with tempfile.TemporaryDirectory(prefix="r8-lhe-identity-") as tmp_dir:
        tmp_out = os.path.join(tmp_dir, "relabelled.lhe.gz")
        n_events, n_relabelled = relabel(
            canonical_lhe_path, tmp_out, from_pdg, to_pdg, expected_events, expected_relabelled
        )
        return {
            "source_lhe_sha256": source_lhe_sha256,
            "canonical_uncompressed_sha256": sha256_of_decompressed(tmp_out),
            "deterministic_relabelled_gzip_sha256": sha256_of_file(tmp_out),
            "n_events": n_events,
            "n_relabelled": n_relabelled,
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("canonical_lhe")
    parser.add_argument("--from-pdg", type=int, required=True)
    parser.add_argument("--to-pdg", type=int, required=True)
    parser.add_argument("--expected-events", type=int, required=True)
    parser.add_argument("--expected-relabelled", type=int, required=True)
    args = parser.parse_args()

    identity = compute_identity(
        args.canonical_lhe,
        args.from_pdg,
        args.to_pdg,
        args.expected_events,
        args.expected_relabelled,
    )
    print(json.dumps(identity, indent=2))


if __name__ == "__main__":
    sys.exit(main())
