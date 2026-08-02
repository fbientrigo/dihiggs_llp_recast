# strong-bm1 baseline freeze contract (partial -- BLOCKED)

> Historical pre-freeze record. It does not describe the canonical compact
> result freeze; use `benchmarks/upstream/strong-bm1/README.md` and
> `CONSOLIDATION_REPORT.md` for the current benchmark-specific verdict.

This mission did not reach a full baseline freeze. The following artifacts are the
durable, verified output of this run and are safe to rely on in a follow-up mission;
everything downstream of MadGraph 1j/2j generation is explicitly **not** produced.

## Frozen (verified, reusable)

| Artifact | Path | Verification |
|---|---|---|
| Upstream pin | `external/recastingCodes` submodule | `d4047c744062094c9f88e507bb1ccf69e9fe88d6`, confirmed clean |
| Upstream cards (byte-identical) | `benchmarks/upstream/strong-bm1/cards/source/` | SHA-256 matches upstream, see `cards/PROVENANCE.json` |
| Generated SLHA | `benchmarks/upstream/strong-bm1/cards/generated/GG_qqn1_2000_850_rpvLF_p01ns.slha` | Only 2 lines changed (mass block); BR sums = 1.0; tau=0.01 ns/ctau=2.998mm independently verified; see `cards/slha_transformation_audit.json` |
| Card/config audit | `results/strong-bm1/card_audit.{json,md}` (gitignored, regenerate via `scripts/audit_strong_bm1_cards.py`) | 15/15 checks PASS |
| Archived comparison reference | `external/recastingCodes/.../2_results/strong/gluino_run01.txt` | Confirmed to be the bm1 (2000/850 GeV) point: High-pT Acc=29.71822%, Acc x Eff=26.60133% |
| 0j pilot | `data/upstream/strong-bm1/mg5_processes/pilot/pp2gogo_0/` (gitignored) | 10 events, seed 111, masses/weights verified, sigma=0.000485 pb consistent with archived inclusive rate |
| Diagnostic ladder | `benchmarks/upstream/strong-bm1/generation_diagnostic_ladder.json` | 5 diagnostic MadGraph runs + 2 free checks, root cause isolated |

## Not frozen (blocked)

- 1j/2j LHE samples (pilot or production scale)
- 0j production-scale (10000-event) sample
- CKKW-L Pythia merging output
- Upstream recast build/execution output
- Reproduced cutflow, comparison, verdict artifacts

## Rerun commands

See `docs/strong_bm1_reproduction_report.md#what-exact-commands-rerun-the-reproduction`.

## Status

`STRONG_BM1_EXECUTION_BLOCKED` -- see `benchmarks/upstream/strong-bm1/benchmark.json`
(`status: "BLOCKED_AT_GENERATION"`) and the diagnostic ladder for the evidenced root
cause and minimum next action.
