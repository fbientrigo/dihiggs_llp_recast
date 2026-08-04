#!/usr/bin/env python3
"""Small dependency-free validation of the demo package."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HBARC_GEV_MM = 1.973269804e-13


def main() -> int:
    cfg = json.loads((ROOT / "configs/ab_scenarios.json").read_text(encoding="utf-8"))
    assert cfg["luminosity_fb_inv"] == 139.0
    assert {b["mass_gev"] for b in cfg["benchmarks"]} == {100.0, 170.0, 250.0}

    for rel in (
        "cards/A_original/scalar_250_ctau5p1mm.slha",
        "cards/B_modified/scalar_250_ctau5p1mm.slha",
    ):
        text = (ROOT / rel).read_text(encoding="utf-8")
        match = re.search(r"DECAY\s+9900035\s+([0-9.Ee+-]+)", text)
        assert match, rel
        width = float(match.group(1))
        ctau = HBARC_GEV_MM / width
        assert abs(ctau - 5.1) < 1e-5, (rel, ctau)
        brs = [float(x) for x in re.findall(r"^\s+([0-9.Ee+-]+)\s+2\s+", text, flags=re.MULTILINE)]
        assert abs(sum(brs) - 1.0) < 1e-9, (rel, sum(brs))

    print("[OK] configuration, SLHA width/lifetime identity and BR sums")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
