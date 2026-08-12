# Gate R1 — genuinely independent adversarial review (2026-08-12)

This supersedes the caveat recorded in `independent_review.md`, which was a
self-review performed in lieu of a separate agent session after the
originally requested external reviewer hit a platform spend limit.

**Reviewer:** a separate agent session with no authorship stake in this
release, read-only against the live filesystem (not against the release's
own claims).

**Verdict: PASS_WITH_WARNING**

## Checks and results

| # | Check | Result |
|---|---|---|
| 1 | Published ATLAS cuts match `cut_definitions.yaml`/`CUT_DICTIONARY.md` vs upstream source (`external/recastingCodes/.../recast_2301_13866.cc:242-349`) | PASS — line-for-line match; modified/High-pT thresholds (250/195/116/90 GeV) confirmed excluded from all live cut values |
| 2 | Denominator semantics | PASS — hand-verified `Aeff = weighted/N_generated` against `cutflow_long.csv` combined row (373/460 = 0.8108695652173913, exact) |
| 3 | Raw vs weighted distinctness | PASS — mutually exclusive columns per stage, no conflation |
| 4 | J1/J2/J3/J4 OR logic | PASS — verified in upstream C++ (`passHighPTJetSelection \|\| passTracklessJetSelection && passTracklessAdditional`), matches doc and `jet_branch_decomposition.csv` |
| 5 | Displaced-vertex addendum/DV stages | PASS — implementation matches documentation (fiducial, R_DV>4mm, d0, track multiplicity/sub-cuts, mDV>10 GeV) |
| 6 | R8 regression (N=2000) | PASS — re-ran `scripts/gate_a_regression.py` fresh (not traced from stored JSON); Jet Selection=48, final raw=40, weighted=31.46772, Aeff=0.01573386, exact match |
| 7 | 20k mH=130/150/170 controls | PASS — all three rows match frozen values exactly, confirmed via fresh script run |
| 8 | Plots vs source tables | PASS — Figure A and Figure D spot-checked against `cutflow_long.csv` / `cut_definitions.yaml` |
| 9 | Checksums | PASS — `sha256sum -c checksums.sha256`: all entries OK |
| 10 | Modified-analysis contamination | PASS — no branching on analysis_mode/physical-sample properties in the frozen recast path |
| 11 | Forced-bb conditional semantics | PASS — BR_bb² applied exactly once to production cross section, never to recast acceptance/Aeff |

Both the R8 and the three 20k regressions were reproduced by **re-running**
the release's own regression script, not merely by reading stored output.

## Warning (cheap, fixed same day)

`external/recastingCodes` is a pinned git submodule
(`d4047c744062094c9f88e507bb1ccf69e9fe88d6`) that was not checked out in the
review worktree, causing `tests/test_strong_bm1_cards.py::test_upstream_submodule_remains_pinned_and_clean`
to fail with a false-positive pin mismatch (the check fell through to the
parent repo's HEAD when the submodule directory was empty). This is not a
scientific defect: CI already runs with `submodules: recursive`, and the
pinned commit's actual cut source was independently confirmed to match via
the main checkout regardless. Root cause was that neither `README.md` nor
`SCIENTIFIC_RELEASE.md` told a fresh checkout/worktree operator to run
`git submodule update --init --recursive` before testing.

**Fix applied:** `README.md`'s "Quick validation" block now runs
`git submodule update --init --recursive` immediately after `cd
dihiggs_llp_recast`; the submodule was also initialized in this worktree and
the previously-failing test now passes (full suite re-run: no failures).

No other issue — numeric, scientific, or otherwise — was found.

## Disposition

Per mission gate policy: PASS_WITH_WARNING with only a cheap/documentary
fix required. The fix has been applied and verified. The release is frozen
as of this review; no further development cycle was started.
