# Upstream recast notes

## Frozen source

- Repository: `https://github.com/llprecasting/recastingCodes.git`
- Commit: `d4047c744062094c9f88e507bb1ccf69e9fe88d6`
- Analysis: `DisplacedVertices/ATLAS-SUSY-2018-13_GCottin`

The submodule contains code for recasting the ATLAS search in arXiv:2301.13866. Its README states that the C++ analysis is built with a Makefile, requires Pythia8 linked to FastJet, and runs as:

```bash
./recast_2301_13866 path/to/input.cmnd
```

The `.cmnd` card points Pythia8 to the LHE input.

## Relevant paths

```text
recast_code/0_mg5_cards/
recast_code/1_analysis/Makefile
recast_code/1_analysis/recast_2301_13866.cc
```

The upstream Makefile exposes `PYTHIA8` and `FASTJET3` installation prefixes. This repository passes those variables from `configs/toolchain.env` rather than editing the upstream file.

## Known adaptation boundary

The upstream implementation was validated for SUSY LLP identifiers. The scalar study requires project-owned parameterization of LLP PDG IDs and explicit original/modified analysis modes. That adaptation remains blocked until one untouched upstream benchmark passes the validation contract.
