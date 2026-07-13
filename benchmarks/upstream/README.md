# Upstream validation inventory

Inventory source: frozen `llprecasting/recastingCodes` commit
`d4047c744062094c9f88e507bb1ccf69e9fe88d6`. All paths below are under
`DisplacedVertices/ATLAS-SUSY-2018-13_GCottin/recast_code/` in that checkout.

## Supplied material

`0_mg5_cards/` contains one common `run_card.dat` requesting 10,000 unweighted events,
three SLHA cards, and 21 MG5 process cards:

- Strong production: `p p > go go` with 0, 1, and 2 additional partons
  (`pp2gogo_{0,1,2}_proc_card_mg5.dat`).
- Electroweak production: `n1 n2`, `n1 x1-`, `n1 x1+`, `n2 x1-`, `n2 x1+`, and
  `x1+ x1-`, each with 0, 1, and 2 additional partons.
- SLHA cards: `GG_qqn1_2800_10_rpvLF_p01ns.slha`,
  `C1N2N1_rpvLF_1700_32ns.slha`, and `C1N2N1_rpvHF_1500_p1ns.slha`.

`1_analysis/cmnd/` contains four directly runnable strong cards (`bm1.cmnd` through
`bm4.cmnd`) and six electroweak templates. The electroweak templates retain an
`@@tms@@` placeholder and therefore require benchmark-specific rendering. Every card
requests 10,000 events for each of three merged subruns.

`2_results/` contains four strong reference logs (`gluino_run01.txt` through
`gluino_run04.txt`) and ten electroweak run directories. Each electroweak directory has
six per-process logs plus a weighted aggregate `output.txt`; the upstream readme maps
runs 01-04 to trackless/light flavor, 05-07 to high-pT/heavy flavor, and 08-10 to
trackless/heavy flavor.

No LHE or LHE.GZ input is present anywhere in the frozen analysis tree. The logs refer
to author-local MadGraph output paths, which are not distributed.

## M2 selection

`strong-bm1` is selected because it has a direct card-to-result mapping
(`bm1.cmnd` to `gluino_run01.txt`) and only one production channel. It needs three
merged samples, compared with 18 samples for a complete electroweak point. It uses the
unchanged upstream physics implementation.

The selection is `BLOCKED`: MadGraph is not installed, all three named LHE inputs are
absent, and no supplied SLHA card matches the `bm1` masses encoded in the LHE names
(gluino 2000 GeV, neutralino 850 GeV, lifetime label 0.01). The supplied strong SLHA
instead describes 2800 GeV and 10 GeV masses, so substituting it would not reproduce
the reference point.
