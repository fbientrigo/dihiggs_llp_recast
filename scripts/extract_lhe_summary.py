#!/usr/bin/env python3
"""Summarize a MadGraph LHE(.gz) file: masses, weights, cross section, events."""
import gzip
import hashlib
import json
import re
import sys
from pathlib import Path


def opener(path):
    return gzip.open(path, "rt") if str(path).endswith(".gz") else open(path)


def summarize(lhe_path: Path) -> dict:
    text = opener(lhe_path).read()
    event_blocks = re.findall(r"<event>\s*\n(.*?)\n", text)
    events = len(event_blocks)
    weights = []
    for header in event_blocks:
        parts = header.split()
        if len(parts) >= 3:
            weights.append(float(parts[2]))
    xsec_m = re.search(r"Integrated weight \(pb\)\s*:\s*([\d.eE+-]+)", text)
    if not xsec_m:
        xsec_m = re.search(r"#\s*Integrated weight \(pb\)\s*:\s*([\d.eE+-]+)", text)
    masses = {}
    for pdg in (1000021, 1000022):
        m = re.search(rf"\n\s*{pdg}\s+([\d.eE+-]+)\s*#", text)
        if m:
            masses[str(pdg)] = float(m.group(1))
    neg = sum(1 for w in weights if w < 0)
    return {
        "file": str(lhe_path),
        "sha256": hashlib.sha256(lhe_path.read_bytes()).hexdigest(),
        "file_size_bytes": lhe_path.stat().st_size,
        "n_events_unweighted": events,
        "n_weights_parsed": len(weights),
        "negative_weight_count": neg,
        "finite_weights": all(w == w and abs(w) != float("inf") for w in weights),
        "masses_GeV": masses,
        "integrated_weight_pb": float(xsec_m.group(1)) if xsec_m else None,
    }


if __name__ == "__main__":
    out = {}
    for p in sys.argv[1:]:
        out[p] = summarize(Path(p))
    print(json.dumps(out, indent=2))
