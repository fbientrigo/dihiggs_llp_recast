#!/usr/bin/env python3
"""Print the explanatory provenance comment header for
results/r8_h2_model_derived_4b/run_0N/input_checksums.txt, sourced from the
committed input_manifest.json.

This exists so a full scripts/run_r8_reproduction.sh run reproduces the
same header instead of silently dropping it: run_recast() writes
input_checksums.txt from scratch via `sha256sum ... | tee`, and without
this, that comment block (explaining why the LHE line's hash differs from
PR #6's historical, non-deterministic-gzip-writer output) would vanish on
every full reproduction even though the three checksum lines below it
still match. sha256sum -c ignores '#'-prefixed lines, so this header is
always safe to prepend.
"""

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(ROOT, "results", "r8_h2_model_derived_4b")


def render(run, historical_hash):
    short = historical_hash[:8]
    return (
        "# Provenance note: the historical PR #6 run used a non-deterministic gzip\n"
        "# writer for the LHE line below; that run's actual compressed-file hash is\n"
        "# preserved in input_manifest.json as\n"
        f"# lhe_inputs.run_{run}.lhe_identity.historical_relabelled_gzip_sha256_at_pr6_run_time\n"
        f"# ({short}...) and is not expected to be independently reproducible. The\n"
        "# LHE hash recorded here reflects the current deterministic relabel writer\n"
        "# (scripts/relabel_lhe_pdg.py, gzip mtime=0, empty embedded filename) --\n"
        "# the hash a fresh reproduction of this run produces today. Decompressed\n"
        "# physics content is unchanged and byte-identical to the historical run;\n"
        "# see canonical_uncompressed_sha256 in input_manifest.json.\n"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", choices=["01", "02"])
    args = parser.parse_args()

    with open(os.path.join(RESULTS_DIR, "input_manifest.json")) as fh:
        manifest = json.load(fh)
    identity = manifest["lhe_inputs"][f"run_{args.run}"]["lhe_identity"]
    historical = identity["historical_relabelled_gzip_sha256_at_pr6_run_time"]
    sys.stdout.write(render(args.run, historical))


if __name__ == "__main__":
    sys.exit(main())
