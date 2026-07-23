# strong-bm1 independent reproduction report

**Verdict: `STRONG_BM1_EXECUTION_BLOCKED`**

## Which local repository state was selected?

`/home/fabi/atlas_dihiggs/llp_recast`, branch `feat/m2-strong-bm1-reproduction` at
commit `747b8e3` ("Correct strong-bm1 toolchain and input readiness"), was the most
advanced coherent baseline across the local checkouts (the sibling clone at
`/home/fabi/code/dihiggs_llp_recast` was on an older, still-`BLOCKED_EXTERNAL_ARTIFACT`
line at `e779001`). All dirty/untracked scalar-adaptation work in that checkout
(`benchmarks/scalar/`, `package/`, `docs/meetings/`, modified `cutflow.py`, etc.) was
left untouched. An isolated worktree was created at
`worktrees/strong_bm1_reproduction_<timestamp>` on new branch
`feat/r2-strong-bm1-independent-reproduction`, based on `747b8e3`.

## Which files came directly from the pinned upstream?

`external/recastingCodes` submodule pinned at `d4047c744062094c9f88e507bb1ccf69e9fe88d6`.
Copied byte-identical (SHA-256 verified, see `cards/PROVENANCE.json`):

- `pp2gogo_{0,1,2}_proc_card_mg5.dat`
- `run_card.dat`
- `bm1.cmnd`
- `GG_qqn1_2800_10_rpvLF_p01ns.slha` (public template, from the ALessa validation dir;
  byte-identical to the copy also present under GCottin's own `0_mg5_cards/`)

## Exactly how was the SLHA modified?

Only `BLOCK MASS` lines 69-70 changed: `1000021 2800.0 -> 2000.0` and
`1000022 10.0 -> 850.0`. See `cards/slha_transformation_audit.json` for the full
audit (checksums, exact diff, BR-sum checks, kinematic-consistency note).

## Was tau = 0.01 ns independently verified?

Yes. `tau = hbar/Gamma` with `Gamma(1000022) = 6.582120e-14 GeV` (unchanged from the
template) and `hbar = 6.582119569e-25 GeV*s` gives `tau = 0.010000 ns`,
`ctau = c*tau = 2.997924 mm`. Matches the mission's cited ~0.01 ns / ~2.998 mm exactly.

## Which seeds were used?

Pilot: 0j=111, 1j=222 (v1, 10 events) then 1j=222 (v2, 1000 events, same seed,
different nevents). Production seeds reserved (not yet used, since generation is
blocked): 0j=90210001, 1j=90210002, 2j=90210003 (`SEEDS.json`).

## Were 10000 events generated for each multiplicity?

**No.** Only a 0j pilot (10 events) was generated and validated. 1j pilot generation
(10 and then 1000 events, to rule out survey starvation) returned exactly zero cross
section in every one of 99 integration channels. 2j was not attempted (same root
cause expected, and further compute was not justified without first resolving 1j).
Full 10000-event production generation for any multiplicity was **not started**.

## What cross section was obtained for each multiplicity?

- 0j (pilot, 10 events, seed 111): 0.000485 +/- 0.0000033 pb. This matches the
  archived merged inclusive cross section (4.949932e-13 mb = 4.95e-4 pb) to within
  the expected relation that 0j dominates the merged inclusive rate.
- 1j: no valid cross section obtained (zero in all channels; see diagnostic ladder).
- 2j: not attempted.

## Did CKKW-L merging complete successfully?

Not reached -- no valid 1j/2j LHE samples exist to feed the merging step.

## How many events were accepted from each subrun?

Not reached.

## What complete cutflow was reproduced?

None. No reproduced cutflow exists to report; see "Baseline freeze" below for the
one piece of comparison data that *was* extracted for future use.

## How does each stage compare with archived recast and ATLAS?

Not reached. However, the archived reference (`gluino_run01.txt`) was located and
confirmed to be the correct bm1 (2000/850 GeV) comparison point: High-pT
Acc = 29.71822%, Acc x Eff = 26.60133%, matching the mission's cited reference
values exactly. This is recorded in `benchmark.json` for use once generation is
unblocked.

## What are the reproduced A and A x efficiency?

Not available (no reproduced cutflow).

## What verdict follows from the validation contract?

`STRONG_BM1_EXECUTION_BLOCKED`, per the mission's own criteria: a genuine blocker
prevented completion at the MadGraph generation stage, before any cutflow could be
extracted or compared.

## What warnings remain?

- The root cause of the 1j/2j zero-cross-section failure was narrowed to "decoupled
  squark scale (>=3 TeV, and specifically the mandated 4.5e5 GeV) combined with a
  real-emission/merging-relevant final state," but the precise Fortran-level
  mechanism (suspected: MLM-merging cluster-scale bookkeeping in `cluster.f`/
  `setcuts.f` mishandling a super-heavy spectator-propagator mass) was not traced
  further, per this mission's own diagnostic time-box.
- It is not yet known whether the original author's private generation used a
  different squark decoupling scale or a non-default MG5 `set` command not present
  in the public proc/run cards. Re-contacting the author was explicitly forbidden by
  this mission's instructions, so this is deferred to the user's judgment.

## Is the baseline ready to freeze?

Only the deterministic, pre-generation artifacts are frozen (see
`docs/strong_bm1_freeze_contract.md`): byte-identical upstream cards, the audited
SLHA transformation, the card/config audit (15/15 PASS), the archived comparison
reference, and the 0j pilot validation. No LHE samples, merged cutflow, or
comparison report exist to freeze.

## What exact commands rerun the reproduction?

```bash
# From the worktree root:
git submodule update --init external/recastingCodes
python3 scripts/audit_strong_bm1_cards.py

# 0j pilot (works):
bash scripts/run_strong_bm1_mg5.sh 0 10 111 pilot_0j data/upstream/strong-bm1/mg5_processes/pilot

# 1j pilot (reproduces the blocker):
bash scripts/run_strong_bm1_mg5.sh 1 1000 222 pilot_1j data/upstream/strong-bm1/mg5_processes/pilot
```

## Differential diagnosis (MadGraph section, per mission instructions)

See `benchmarks/upstream/strong-bm1/generation_diagnostic_ladder.json` for the full
five-run diagnostic ladder and two free checks (SLHA-source-identity diff,
IEEE_INVALID_FLAG correlation) that isolated the failure to the decoupled-squark /
real-emission interaction, ruling out: card mismatch, survey-statistics starvation,
the specific 4.5e5 GeV magnitude in isolation, gluino mass in isolation, and
generically-too-strict cuts.

## Minimum next action

Ask the user whether to: (a) consult MadGraph documentation/support about MLM
merging behavior with spectator sfermions far above the hard-process scale, (b)
attempt a documented, non-silent adjustment to the merging setup (e.g. an explicit
MG5 `set` command) as a new diagnostic round, or (c) accept a scope change to the
benchmark's squark-decoupling assumption -- which would itself be a physics-input
change requiring explicit sign-off, not something to apply silently.
