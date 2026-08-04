# LLP vertex diagnostic

Standalone Pythia8 probe used to establish why the toy A/B chain produces no
displaced vertices. It does not touch the upstream recast.

Build:

```bash
P=$HOME/.local/pythia8308
g++ -o diag_llp_vertex diag_llp_vertex.cc -I$P/include -L$P/lib -lpythia8 -lz \
    -Wl,-rpath $P/lib -std=c++11
```

Run from the package root (card paths are relative):

```bash
./scripts/diag/diag_llp_vertex cards/A_original/pythia_scalar_toy.cmnd
```

It prints the particle-data record for PDG 9900035 (tau0, mayDecay,
isResonance) and, for each terminal LLP copy, the proper lifetime and the
transverse decay radius.

Observed on 2026-07-15 (Pythia 8.308): `tau0 = 5.1 mm` is imported correctly
from SLHA, but every terminal LLP has `tau = 0` and `rDec = 0`, i.e. the scalar
is decayed promptly at the production vertex. Expected for this benchmark is
`mean rDec ~ beta*gamma*ctau ~ 8.8 mm`. The same holds for the neutralino
control, so the gap is generic to the toy chain, not specific to the scalar PDG.
