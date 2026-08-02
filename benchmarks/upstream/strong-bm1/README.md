# Canonical upstream `strong-bm1` baseline

This directory freezes the independently reproduced public ATLAS DV+jets
strong-production benchmark without adapting the recast to the local H2 model.
The pinned public code is the `external/recastingCodes` submodule at
`d4047c744062094c9f88e507bb1ccf69e9fe88d6`.

The authoritative machine-readable result is under
`results/upstream/strong-bm1/`. Run `bash benchmarks/upstream/strong-bm1/commands.sh`
to regenerate the plots and derived comparison JSON without rerunning event
generation. The source package and every compact artifact are checksummed in
`checksums.sha256`.

Verdict: `UPSTREAM_STRONG_BM1_PROVISIONAL`. The cutflow and cross-section values
are reconciled to the archived logs. Promotion remains provisional because the
source JSON has one mislabeled cross-section field and does not preserve the
weighted moments needed for a defensible acceptance uncertainty.
