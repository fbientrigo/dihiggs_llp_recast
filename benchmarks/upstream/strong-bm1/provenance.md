# strong-bm1 generation provenance

Contract classification: `RECONSTRUCTED`.

This document records the generation reconstruction. It does not supersede the
canonical High-pT result freeze, which is validated against archived compact
outputs without claiming recovery of the authors' private LHE files.

## Repository evidence

- Frozen upstream revision: `d4047c744062094c9f88e507bb1ccf69e9fe88d6`.
- The analysis was added wholesale by upstream commit
  `19cb99faf3c63a2d65e2cfbb3c1e4add5fa741a8`; the two later commits touching
  the analysis changed README/metadata only. No earlier bm1 card exists in any
  locally reachable ref.
- All strong process-card headers identify MadGraph5_aMC@NLO 3.5.3 and import
  `MSSM_SLHA2` before generating the 0/1/2-parton processes.
- `run_card.dat` fixes 13 TeV, `nn23lo1`/LHAPDF ID 230000, 10,000 events,
  automatic seeds, the documented cuts, and `ktdurham=500`.
- `bm1.cmnd` fixes three input names and CKKW-L kT merging at 500 GeV.
- `gluino_run01.txt` confirms Pythia 8.308, FastJet 3.4.0, author-local LHE
  paths, 2000 GeV gluinos, 850 GeV neutralinos, imported gluino/neutralino
  decay tables, and the distributed reference cutflow.
- The only supplied upstream/source strong SLHA is
  `GG_qqn1_2800_10_rpvLF_p01ns.slha`. It is evidence for conventions only and
  is not the authors' bm1 parameter card; the tracked 2000/850 GeV SLHA is the
  separately documented independent reconstruction.

## History and remote investigation

Read-only commands included `git log --all`, `git log --all --name-status`,
`git log -S`, `git rev-list --all`, `git grep`/`rg`, `git show`, `git fsck`, and
tree inspection. Searches covered bm1/run01 identifiers, masses, lifetime
labels, LHE paths, MG5/model/process strings, cards, widths, decays, branching
ratios, seeds, PDF/cuts, and matching settings. No hidden or historical exact
bm1 SLHA or assigned seed was recovered.

External indexed searches for the three exact LHE names, `2000_850_0p01`, and
`gluino_run01.txt` returned no additional source. The historical Launchpad
3.5.3 archive URL returned HTTP 404. The official Git repository exposes tag
`v3.5.3` at commit `59b4b9c1238978f39a32b8bc83244328187704b6`; that immutable
commit is used for the local installation. External sources do not override
the frozen repository evidence.

## Local MadGraph installation

- Version/tag/commit: 3.5.3 / `v3.5.3` /
  `59b4b9c1238978f39a32b8bc83244328187704b6`.
- Git tree checksum: `62101b54b91b73d5609224224c5feeec159f8820`.
- Source: <https://github.com/mg5amcnlo/mg5amcnlo.git>.
- Prefix: `$HOME/.local/mg5amcnlo/3.5.3`.
- Command: `scripts/install_madgraph_local.sh --version 3.5.3
  --git-commit 59b4b9c1238978f39a32b8bc83244328187704b6`.
- Interpreter/dependency: Python 3.12.3 and `six` 1.17.0; compilers: GCC and
  GFortran 13.3.0.
- Verification: help probe and non-generating `import model MSSM_SLHA2`
  succeeded; checkout HEAD matches and `git status --short` is empty.
- Warning: MG5 reports Python 3.12 support as experimental and says reweighting
  does not work. Its banner confirms version 3.5.3 dated 2023-12-23 but also
  labels the Git checkout an `UNKNOWN DEVELOPMENT VERSION`. A future
  production campaign should resolve these warnings and use a supported
  Python interpreter even after the physics contract is completed.

## Scientific boundary

The label `0p01` is not assigned a unit from the filename alone. A 0.01 ns
interpretation is recorded only as `INFERRED`, using the separate `p01ns`
card name together with its explicit width. The exact bm1 width and branching
ratios remain unknown, so the tracked SLHA is an independent reconstruction and
the canonical repository retains compact results rather than event samples.
