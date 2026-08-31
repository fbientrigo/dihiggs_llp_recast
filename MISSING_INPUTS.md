# Missing higher-mass response inputs

No provenance-approved full LHE input was found for either requested extension
mass:

- `mH2 = 300 GeV`: missing.
- `mH2 = 350 GeV`: missing.

Inspected artifacts:

- `/home/fabian/atlas_dihiggs/dihiggs_hep_cross/results/r14_direct_g_production/proc_output/Events/`
  and its MG5 banners: the available H2 pair-production files are 10,000-event
  samples at 130, 150, 170, 200, and 250 GeV only.
- `/home/fabian/atlas_dihiggs/dihiggs_hep_cross/artifacts/h2_first_physical/madgraph/`:
  two 1,000-event, fully documented 150 GeV samples only.
- Local corresponding relabelled inputs under `data/raw/` and the existing
  response-study result inputs: they mirror the 130/150/170/200/250 GeV
  sources; none is 300 or 350 GeV.
- `results/r10_effective_ctau_g_br_scan/`: entries named `ctau_300` are a
  lifetime coordinate, not an `mH2 = 300 GeV` production sample.

The 200 and 250 GeV candidates are not substitutes: their event records and
MG5 banners establish the wrong H2 masses. No events were generated in this
mission.

Future MadGraph production must provide, for each requested mass, the same
intended `g g > H > h2 h2` topology, H2 stable in the LHE, a recorded event
count (preferably the current two-seed 20,000-event convention), MG5/UFO and
PDF/beam/run-card provenance, seeds/run IDs, source and output SHA256 values,
and an explicit check that the recast handoff and analysis semantics are
unchanged. Only then may the existing relabel/Pythia/recast configuration be
reused.
