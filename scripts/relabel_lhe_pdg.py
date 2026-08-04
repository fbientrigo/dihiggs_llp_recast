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

The result is only ever published at --output-lhe after every acceptance
check (event count, replacement count, no pre-existing target PDG) has
passed: relabel() writes to a temporary sibling file and atomically renames
it onto the destination only on success. On any failure, the temporary file
is removed and the destination path is left exactly as it was found (an
existing destination is never replaced by a rejected result).
"""

import argparse
import contextlib
import gzip
import io
import os
import sys


def _open_read(path):
    return gzip.open(path, "rt") if path.endswith(".gz") else open(path)


@contextlib.contextmanager
def _open_write(path, gzip_it):
    """Open path for text writing. When gzip_it, use a fixed mtime=0 and an
    empty embedded filename so two relabel runs on identical input produce a
    byte-identical (and thus identically-hashed) .gz output: gzip.open's
    default header embeds the current wall-clock time and the temporary
    sibling filename, which would otherwise make the published hash
    non-reproducible run to run.
    """
    if not gzip_it:
        with open(path, "w") as fh:
            yield fh
        return
    with open(path, "wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
            text = io.TextIOWrapper(gz, encoding="utf-8")
            yield text
            text.flush()


def relabel(in_path, out_path, from_pdg, to_pdg, expected_events=None, expected_relabelled=None):
    """Relabel from_pdg -> to_pdg in in_path, publishing to out_path only
    after all requested validation has passed.

    expected_events/expected_relabelled are optional; when given, the
    result is rejected (and out_path left untouched) unless the observed
    counts match exactly. The pre-existing-target-PDG and
    no-source-PDG-found checks always apply.
    """
    from_tok, to_tok = str(from_pdg), str(to_pdg)
    neg_from_tok, neg_to_tok = str(-from_pdg), str(-to_pdg)

    tmp_path = f"{out_path}.tmp{os.getpid()}"
    out_is_gzip = out_path.endswith(".gz")

    in_event = False
    n_events = 0
    n_events_closed = 0
    n_relabelled = 0
    pre_existing_target = 0

    try:
        with _open_read(in_path) as fin, _open_write(tmp_path, out_is_gzip) as fout:
            for line in fin:
                stripped = line.strip()
                if stripped == "<event>":
                    in_event = True
                    n_events += 1
                    fout.write(line)
                    continue
                if stripped == "</event>":
                    in_event = False
                    n_events_closed += 1
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
            fout.flush()

        if in_event or n_events_closed != n_events:
            raise ValueError(
                f"refusing to relabel: malformed/truncated LHE, {n_events} <event> tag(s) "
                f"opened but only {n_events_closed} closed"
            )
        if pre_existing_target:
            raise ValueError(
                f"refusing to relabel: {pre_existing_target} particle line(s) already "
                f"carry target PDG {to_pdg} before relabelling"
            )
        if n_relabelled == 0:
            raise ValueError(f"refusing to relabel: no particle line carried source PDG {from_pdg}")
        if expected_events is not None and n_events != expected_events:
            raise ValueError(f"event count mismatch: found {n_events}, expected {expected_events}")
        if expected_relabelled is not None and n_relabelled != expected_relabelled:
            raise ValueError(
                f"relabel count mismatch: relabelled {n_relabelled}, "
                f"expected {expected_relabelled}"
            )
    except BaseException:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

    # Only reached once every check above has passed: publish atomically.
    # os.replace is an atomic rename on POSIX (same filesystem, sibling
    # path), so a reader never observes a partially-written destination,
    # and a pre-existing destination is only ever replaced by a validated
    # result.
    os.replace(tmp_path, out_path)
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

    try:
        n_events, n_relabelled = relabel(
            args.input_lhe,
            args.output_lhe,
            args.from_pdg,
            args.to_pdg,
            args.expected_events,
            args.expected_relabelled,
        )
    except Exception as exc:
        raise SystemExit(str(exc)) from exc

    print(
        f"OK: {n_events} events, {n_relabelled} particle lines relabelled "
        f"{args.from_pdg} -> {args.to_pdg}"
    )


if __name__ == "__main__":
    sys.exit(main())
