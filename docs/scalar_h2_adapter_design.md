# Scalar h2 adapter design

Status: `PROVISIONAL_SCALAR_SMOKE_EXECUTED`

The adapter is a project-owned C++ overlay, `src/scalar_h2_recast.cc`. It
consumes the stable Pack A LHE directly through `Pythia8::Pythia`, restores the
Pack AA decay table and `tau0` after `init()`, and passes the same in-memory
event to the unmodified `Simpler_ToyDetector` and `efficiency` implementation.
That gives one Pythia decay/shower/hadronization pass and no HepMC hand-off.

Changed:

- scalar-only PDG, mass, lifetime, seed, channel, BR and input/output options;
- scalar h2 ancestry/decay recognition, event diagnostics and structured output;
- project-owned build/run wrappers and audit/cutflow/plot tools;
- explicit `upstream-susy` (default) and `scalar-h2` wrapper modes.

Identical:

- upstream submodule commit `d4047c744062094c9f88e507bb1ccf69e9fe88d6`;
- FastJet jet construction, jet thresholds, track selection, fiducial region,
  DV track/mass thresholds, trigger-independent event maps and vertex map;
- upstream efficiency tables, compiled directly from the pinned submodule.

Rejected alternatives:

- Pack AA truth JSONL as recast input: it is validation evidence, not a full
  event record;
- Pack AA Pythia followed by recast Pythia: that would double shower/decay;
- editing or patching the frozen upstream submodule in place.

Not validated here: upstream benchmark gates R2/R3/R5/R6/R7, a public benchmark
comparison, model-derived normalization, exclusion, and paper-level acceptance.
