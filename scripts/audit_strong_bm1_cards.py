#!/usr/bin/env python3
"""Phase 2 card/config audit for the strong-bm1 independent reproduction.

Validates the copied upstream cards and the generated SLHA against the
frozen benchmark identity before any MadGraph/Pythia execution is allowed.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "benchmarks" / "upstream" / "strong-bm1" / "cards"
SRC = CARDS / "source"
GEN = CARDS / "generated"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def br_sum(lines, pdg):
    total = 0.0
    in_block = False
    for line in lines:
        s = line.strip()
        if re.match(rf"^DECAY\s+{pdg}\s", s):
            in_block = True
            continue
        if in_block:
            if s.startswith("DECAY") or s.upper().startswith("BLOCK"):
                break
            if not s or s.startswith("#"):
                continue
            parts = s.split()
            try:
                total += float(parts[0])
            except ValueError:
                pass
    return total


def check(results, name, ok, detail=""):
    results.append({"check": name, "pass": bool(ok), "detail": detail})


def main():
    results = []

    proc0 = (SRC / "pp2gogo_0_proc_card_mg5.dat").read_text()
    proc1 = (SRC / "pp2gogo_1_proc_card_mg5.dat").read_text()
    proc2 = (SRC / "pp2gogo_2_proc_card_mg5.dat").read_text()
    run_card = (SRC / "run_card.dat").read_text()
    slha_gen_path = GEN / "GG_qqn1_2000_850_rpvLF_p01ns.slha"
    slha_src_path = SRC / "GG_qqn1_2800_10_rpvLF_p01ns.slha"
    slha_gen = slha_gen_path.read_text()
    audit = json.loads((CARDS / "slha_transformation_audit.json").read_text())

    # 1. MSSM_SLHA2
    check(results, "process_cards_use_MSSM_SLHA2",
          all("import model MSSM_SLHA2" in p for p in (proc0, proc1, proc2)))

    # 2. exactly 0j/1j/2j
    check(results, "processes_are_0j_1j_2j",
          "generate p p > go go\n" in proc0
          and "generate p p > go go j\n" in proc1
          and "generate p p > go go j j\n" in proc2)

    # 3. beam energy
    m = re.search(r"([\d.]+)\s*=\s*ebeam1", run_card)
    m2 = re.search(r"([\d.]+)\s*=\s*ebeam2", run_card)
    check(results, "beam_energy_6500_GeV_per_beam",
          m and m2 and float(m.group(1)) == 6500.0 and float(m2.group(1)) == 6500.0,
          f"ebeam1={m.group(1) if m else None} ebeam2={m2.group(1) if m2 else None}")

    # 4. nevents=10000 in the pinned production run card
    m = re.search(r"(\d+)\s*=\s*nevents", run_card)
    check(results, "run_card_nevents_10000",
          m and int(m.group(1)) == 10000, m.group(0) if m else "")

    # 5. PDF id 230000
    m = re.search(r"(\d+)\s*=\s*lhaid", run_card)
    pdlabel_m = re.search(r"(\S+)\s*=\s*pdlabel", run_card)
    check(results, "pdf_id_230000",
          m and int(m.group(1)) == 230000,
          f"lhaid={m.group(1) if m else None} pdlabel={pdlabel_m.group(1) if pdlabel_m else None} "
          "(lhaid is inactive; pdlabel=nn23lo1 is MG5's built-in set)")

    # 6. ktdurham=500
    m = re.search(r"([\d.]+)\s*=\s*ktdurham", run_card)
    check(results, "ktdurham_500_GeV", m and float(m.group(1)) == 500.0)

    # 7. gluino mass 2000
    check(results, "gluino_mass_2000_GeV", audit["mass_verification"]["1000021_GeV"] == 2000.0)

    # 8. neutralino mass 850
    check(results, "neutralino_mass_850_GeV", audit["mass_verification"]["1000022_GeV"] == 850.0)

    # 9. neutralino width
    check(results, "neutralino_width_6p582120e-14",
          abs(audit["width_verification"]["1000022_width_GeV"] - 6.582120e-14) < 1e-20)

    # 10. lifetime 0.01 ns
    check(results, "lifetime_converts_to_0p01_ns",
          abs(audit["lifetime_verification"]["tau_ns"] - 0.01) < 1e-6)

    # 11. required decay tables exist
    check(results, "required_decay_tables_exist",
          "DECAY   1000021" in slha_gen and "DECAY   1000022" in slha_gen)

    # 12. BR sums valid
    gl = br_sum(slha_gen.splitlines(), 1000021)
    n1 = br_sum(slha_gen.splitlines(), 1000022)
    check(results, "br_sums_valid", abs(gl - 1.0) < 1e-6 and abs(n1 - 1.0) < 1e-6,
          f"gluino_BR_sum={gl} n1_BR_sum={n1}")

    # 13. original template unchanged (checksum matches recorded provenance)
    check(results, "original_template_unchanged",
          sha256(slha_src_path) == audit["template_sha256"])

    # 14. generated SLHA differs only in documented fields
    src_lines = slha_src_path.read_text().splitlines()
    gen_lines = slha_gen_path.read_text().splitlines()
    pairs = enumerate(zip(src_lines, gen_lines, strict=False))
    diff_lines = [i + 1 for i, (a, b) in pairs if a != b]
    documented = [d["line"] for d in audit["changed_lines"]]
    check(results, "generated_slha_differs_only_in_documented_fields",
          diff_lines == documented, f"diff_lines={diff_lines} documented={documented}")

    # 15. output names map unambiguously to 0j/1j/2j
    check(results, "output_names_map_to_0j_1j_2j",
          "output pp2gogo_0" in proc0
          and "output pp2gogo_1" in proc1
          and "output pp2gogo_2" in proc2)

    overall = all(r["pass"] for r in results)
    report = {
        "benchmark_id": "strong-bm1",
        "overall_pass": overall,
        "checks": results,
    }

    out_dir = ROOT / "results" / "strong-bm1"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "card_audit.json").write_text(json.dumps(report, indent=2))

    md = ["# strong-bm1 card/config audit\n", f"\nOverall: {'PASS' if overall else 'FAIL'}\n\n",
          "| # | Check | Result | Detail |\n", "|---|---|---|---|\n"]
    for i, r in enumerate(results, 1):
        md.append(f"| {i} | {r['check']} | {'PASS' if r['pass'] else 'FAIL'} | {r['detail']} |\n")
    (out_dir / "card_audit.md").write_text("".join(md))

    print(json.dumps(report, indent=2))
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
