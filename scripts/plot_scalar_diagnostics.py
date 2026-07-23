#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    rows = [
        json.loads(line)
        for line in args.events.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "diagnostics.json").write_text(
        json.dumps(
            {
                "schema": "scalar_h2.diagnostics.v1",
                "events": rows,
                "failure_reason_counts": dict(Counter(row["failure_reason"] for row in rows)),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise SystemExit(f"matplotlib is required for plots: {exc}") from None
    specs = {
        "beta_gamma": ("beta_gamma", "h2 beta*gamma"),
        "lab_flight_length_mm": ("lab_flight_length_mm", "h2 lab flight length [mm]"),
        "proper_flight_length_mm": ("proper_flight_length_mm", "h2 proper flight length [mm]"),
        "dv_radius_mm": ("dv_radius_mm", "DV radius [mm]"),
        "dv_z_mm": ("dv_z_mm", "DV z [mm]"),
        "n_jets": ("n_jets", "number of jets"),
        "leading_jet_pt_GeV": ("leading_jet_pt_GeV", "leading jet pT [GeV]"),
        "subleading_jet_pt_GeV": ("subleading_jet_pt_GeV", "subleading jet pT [GeV]"),
        "ht_GeV": ("ht_GeV", "HT [GeV]"),
        "charged_descendants": ("charged_descendants", "charged descendants"),
        "selected_displaced_track_multiplicity": (
            "selected_displaced_track_multiplicity",
            "selected displaced-track multiplicity",
        ),
        "truth_dv_mass_GeV": ("truth_dv_mass_GeV", "truth DV mass [GeV]"),
        "reconstructed_dv_mass_GeV": ("reconstructed_dv_mass_GeV", "reconstructed DV mass [GeV]"),
    }
    for filename, (key, xlabel) in specs.items():
        plt.figure(figsize=(5, 3.2))
        plt.hist([row[key] for row in rows], bins=20)
        plt.xlabel(xlabel)
        plt.ylabel("events")
        plt.tight_layout()
        plt.savefig(args.out / f"{filename}.png", dpi=130)
        plt.close()
    failures = Counter(row["failure_reason"] for row in rows)
    plt.figure(figsize=(6, 3.2))
    plt.bar(list(failures), list(failures.values()))
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("events")
    plt.title("failure reason by selection stage")
    plt.tight_layout()
    plt.savefig(args.out / "failure_reason.png", dpi=130)
    plt.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
