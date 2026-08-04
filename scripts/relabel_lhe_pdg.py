#!/usr/bin/env python3
"""Relabel a stable-particle PDG code in an LHEF file by pure text
substitution of the IDUP field on particle lines, preserving every other
field (momenta, status, mothers, colours, mass, lifetime, spin) byte for
byte.

This reproduces, as a committed and auditable tool, the ad hoc "text
substitution" relabel described in cards/r7_h2_pair_4b/ctau_4p326mm.cmnd:
Pythia8's ResonanceDecays machinery requires a registered ResonanceWidths
object to shower a heavy resonance's decay products into real jets, which
only exists for Pythia's own built-in slots (e.g. PDG 35, "H0"); a fully
custom PDG (here 9000006) has none.
"""

import argparse
import gzip
import sys


def _open_read(path):
    return gzip.open(path, "rt") if path.endswith(".gz") else open(path)


def _open_write(path):
    return gzip.open(path, "wt") if path.endswith(".gz") else open(path, "w")


def relabel(in_path, out_path, from_pdg, to_pdg):
    from_tok, to_tok = str(from_pdg), str(to_pdg)
    neg_from_tok, neg_to_tok = str(-from_pdg), str(-to_pdg)

    in_event = False
    n_events = 0
    n_relabelled = 0
    pre_existing_target = 0

    with _open_read(in_path) as fin, _open_write(out_path) as fout:
        for line in fin:
            stripped = line.strip()
            if stripped == "<event>":
                in_event = True
                n_events += 1
                fout.write(line)
                continue
            if stripped == "</event>":
                in_event = False
                fout.write(line)
                continue
            if in_event and stripped and not stripped.startswith("<"):
                fields = line.split()
                # Event header line has 6 fields (NUP, IDPRUP, XWGTUP, SCALUP,
                # AQEDUP, AQCDUP); particle lines have 13. Only particle lines
                # carry an IDUP to relabel.
                if len(fields) == 13:
                    if fields[0] in (from_tok, neg_from_tok):
                        new_id = to_tok if fields[0] == from_tok else neg_to_tok
                        fields[0] = new_id
                        fout.write(" " * max(1, 9 - len(new_id)) + " ".join(fields) + "\n")
                        n_relabelled += 1
                        continue
                    if fields[0] in (to_tok, neg_to_tok):
                        pre_existing_target += 1
            fout.write(line)

    if pre_existing_target:
        raise SystemExit(
            f"refusing to relabel: {pre_existing_target} particle line(s) already "
            f"carry target PDG {to_pdg} before relabelling"
        )
    if n_relabelled == 0:
        raise SystemExit(f"refusing to relabel: no particle line carried source PDG {from_pdg}")

    return n_events, n_relabelled


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_lhe")
    parser.add_argument("output_lhe")
    parser.add_argument("--from-pdg", type=int, required=True)
    parser.add_argument("--to-pdg", type=int, required=True)
    parser.add_argument(
        "--expected-events",
        type=int,
        required=True,
        help="LHE must contain exactly this many <event> blocks",
    )
    parser.add_argument(
        "--expected-relabelled",
        type=int,
        required=True,
        help="exact number of particle lines expected to carry --from-pdg",
    )
    args = parser.parse_args()

    n_events, n_relabelled = relabel(args.input_lhe, args.output_lhe, args.from_pdg, args.to_pdg)

    if n_events != args.expected_events:
        raise SystemExit(f"event count mismatch: found {n_events}, expected {args.expected_events}")
    if n_relabelled != args.expected_relabelled:
        raise SystemExit(
            f"relabel count mismatch: relabelled {n_relabelled}, "
            f"expected {args.expected_relabelled}"
        )

    print(
        f"OK: {n_events} events, {n_relabelled} particle lines relabelled "
        f"{args.from_pdg} -> {args.to_pdg}"
    )


if __name__ == "__main__":
    sys.exit(main())
