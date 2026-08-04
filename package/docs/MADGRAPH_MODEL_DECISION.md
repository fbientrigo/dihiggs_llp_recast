# MadGraph model decision: paper reproduction vs. local 2HDM

## Do not merge these two tasks

### Track P — reproduce arXiv:2606.01681

Goal: validate the event generation and recast against the paper before changing the model.

Minimal physics content:

1. SM-like Higgs `h` with its SM top coupling.
2. Real neutral scalar `S`.
3. `h-S-S` interaction from
   `L contains -(lambda/2) v h S S`, corresponding to an `hSS` vertex proportional to `lambda*v`.
4. Scalar mass `mS`.
5. Scalar total width and branching ratios supplied to Pythia through SLHA.

For normalized cutflow efficiencies, `lambda` changes the event normalization but not the decay lifetime. However, the off-shell production kinematics still require a physically valid `gg -> h* -> SS` matrix element.

Two implementations are possible:

- **P-full-loop:** custom FeynRules/NLOCT UFO and MadGraph loop-induced generation. This is closest to the paper.
- **P-HEFT-proxy:** effective `ggh` plus `hSS` model. This is acceptable only as an explicitly labelled kinematic/plumbing approximation; finite-top-mass effects are not reproduced exactly.

Do not call a HEFT sample a paper reproduction until its relevant distributions and cutflow are compared.

### Track D — local general 2HDM

Goal: generate the actual process for an accepted 2HDMC point.

A generic type-I UFO is not automatically sufficient. The local scan uses non-zero `lambda6`, so a model imposing the usual softly broken Z2 potential (`lambda6=lambda7=0`) is not equivalent.

Required validation gates:

1. The UFO supports the same scalar potential and conventions.
2. One reference point reproduces the 2HDMC scalar masses.
3. The UFO `h125-phi-phi` coupling matches the 2HDMC coupling after normalization conversion.
4. The total and partial widths used by Pythia match the scan point.
5. The gluon-fusion implementation is documented: full loop or effective coupling.
6. MadGraph cross sections are stable under integration settings and seeds.

## Minimum process cards

### Paper-model full-loop pattern

```text
import model PAPER_SCALAR_UFO
set complex_mass_scheme False
generate g g > h > s s [QCD]
output paper_scalar_pair
launch
```

Particle names and coupling-order syntax must be checked against the actual UFO.

### Local 2HDM pattern

```text
import model GENERAL_2HDM_UFO
generate g g > h1 > h2 h2 [QCD]
output local_2hdm_pair
launch
```

`h1` and `h2` are placeholders. Confirm the PDG/name convention in `particles.py` before generating.

## Parameter point contract

A usable MadGraph point consists of four linked artifacts:

```text
UFO model/version
MadGraph param_card.dat
MadGraph run_card.dat
Pythia SLHA/decay card
```

A standalone SLHA file containing only `MASS`, `DECAY`, and `QNUMBERS` is enough for Pythia plumbing, but it is not a complete MadGraph model parameter card.
