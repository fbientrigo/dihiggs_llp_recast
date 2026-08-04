#!/usr/bin/env python3
"""Merge per-mode lifetime probe JSONs into results/lifetime_summary.json.

TOY_LIFETIME_PLUMBING_TEST. Evaluates the Mission 01B acceptance criteria
against measured values. Criteria are recorded as measured, including the ones
that fail; nothing is smoothed over.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def evaluate(mode: str, d: dict, cutflow: dict | None) -> list[dict]:
    """Return one record per acceptance criterion for a given mode."""
    pd_ = d["particle_data"]
    c = d["counts"]
    dist = d["distributions"]
    two_llp_expected = c["events_processed"] * 2

    def crit(n, text, ok, measured):
        return {"criterion": n, "requirement": text, "pass": bool(ok), "measured": measured}

    out = [
        crit(1, "isResonance == false after initialization",
             pd_["isResonance"] is False, f"isResonance={pd_['isResonance']}"),
        crit(2, "exactly two final LLPs before hadron-level processing",
             c["events_with_two_final_llps"] == c["events_processed"],
             f"{c['events_with_two_final_llps']}/{c['events_processed']} events"
             + ("" if mode == "staged" else " (not separable: single-call path)")),
        crit(3, "sampled tau values are nonzero",
             dist["tau_mean_mm"] > 0.0, f"mean tau={dist['tau_mean_mm']:.4f} mm"),
        crit(4, "LLPs are not process-level status -22 decays",
             c["terminal_llps_status_minus22"] == 0,
             f"terminal LLPs with status -22 in event record="
             f"{c['terminal_llps_status_minus22']}"),
        crit(5, "daughters inherit displaced production vertices",
             c["llps_with_displaced_daughters"] == c["terminal_llps"] and c["terminal_llps"] > 0,
             f"{c['llps_with_displaced_daughters']}/{c['terminal_llps']} LLPs"),
        crit(6, "7.9 mm < mean L3D < 9.8 mm (500-event toy sample)",
             7.9 < dist["L3D_mean_mm"] < 9.8, f"mean L3D={dist['L3D_mean_mm']:.4f} mm"),
        crit(7, "at least one LLP with Rxy > 4 mm",
             c["llps_Rxy_gt_4mm"] >= 1, f"{c['llps_Rxy_gt_4mm']}/{c['terminal_llps']} LLPs"),
    ]
    if cutflow:
        inv = cutflow.get("trackless_invariant_mass_gt_10gev_pct")
        acc = cutflow.get("trackless_acc_pct")
        out.append(crit(8, "at least one event survives DV geometrical acceptance",
                        inv is not None and inv > 0.0,
                        f"Trackless Invariant Mass > 10 GeV = {inv}%"))
        out.append(crit(9, "recast reports nonzero Trackless acceptance before efficiency",
                        acc is not None and acc > 0.0, f"Trackless Acc = {acc}%"))
    # Criterion 2 is only meaningful for the staged path.
    if mode != "staged":
        out[1]["pass"] = None
        out[1]["note"] = "not applicable: single-call path never exposes a pre-hadron phase"
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--in-dir", type=Path, required=True)
    ap.add_argument("--cutflow", type=Path, help="toy_cutflow_ab_repaired.csv")
    ap.add_argument("--out", type=Path, default=Path("results/lifetime_summary.json"))
    args = ap.parse_args()

    cutflows: dict[str, dict] = {}
    if args.cutflow and args.cutflow.exists():
        import csv
        with args.cutflow.open() as fh:
            for row in csv.DictReader(fh):
                stage = row["stage"]
                for col, mode in (("A_original_staged", "staged"),
                                  ("A_original_setlifetime", "setlifetime"),
                                  ("A_original_baseline", "baseline")):
                    if col in row and row[col] not in ("", None):
                        cutflows.setdefault(mode, {})[stage] = float(row[col])

    modes = {}
    for mode in ("baseline", "setlifetime", "staged"):
        p = args.in_dir / f"sum_{mode}.json"
        if not p.exists():
            continue
        d = json.loads(p.read_text())
        d["acceptance_criteria"] = evaluate(mode, d, cutflows.get(mode))
        modes[mode] = d

    verdicts = {}
    for mode, d in modes.items():
        crits = d["acceptance_criteria"]
        failed = [c["criterion"] for c in crits if c["pass"] is False]
        verdicts[mode] = {
            "failed_criteria": failed,
            "verdict": "PASS" if not failed else "FAIL",
        }

    summary = {
        "label": "TOY_LIFETIME_PLUMBING_TEST",
        "mission": "01B",
        "root_cause": (
            "LesHouches:setLifetime defaults to 1 (tau leptons only), so a QNUMBERS/SLHA "
            "LLP arriving final-state from an LHE takes its decay time from VTIMUP, which "
            "the toy generator writes as 0. The isResonance flag was never the cause: "
            "ResonanceDecays displaces daughters correctly whenever tau > 0."
        ),
        "recommended_repair": "setlifetime",
        "recommendation_reason": (
            "The staged path decays the LLP at hadron level, where PYTHIA cannot decay W/Z "
            "resonances. For this benchmark BR(WW)+BR(ZZ)=0.70, so 70% of decays leave "
            "stable W/Z bosons, yielding zero reconstructable tracks and zero DV acceptance."
        ),
        "verdicts": verdicts,
        "modes": modes,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"[OK] wrote {args.out}")
    for mode, v in verdicts.items():
        print(f"  {mode:12s} {v['verdict']:5s} failed={v['failed_criteria']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
