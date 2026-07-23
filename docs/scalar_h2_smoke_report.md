# Provisional scalar h2 smoke report

Status: `PROVISIONAL_SCALAR_SMOKE_EXECUTED`

The complete local path executed successfully:

`stable Pack A LHE -> one Pythia 8.308 pass -> FastJet/ToyDetector -> scalar DV+jets selection -> structured cutflow and plots`.

The primary run used 100 unique production events and zero decay replicas.
Pythia produced the requested h2 -> b bbar channel for all 100 events with
`PDG=9000006`, `m=200 GeV`, `ctau=1000 mm`, `BR=1`, `is_resonance=false`, and
seed `900006005`. The run reconstructed jets in the event record and charged
descendants/tracks in displaced candidates. The final selected count was zero.

The largest sequential loss was the displaced/fiducial vertex stage: 100
successful decays became 40 displaced/fiducial events; the jet preselection
then retained 38 and the unchanged high-pT/trackless jet selection retained
zero for this sample. The complete machine-readable result is in
`results/scalar_h2_smoke/cutflow.json` and the diagnostic distributions are in
`results/scalar_h2_smoke/plots/`.

All ATLAS constants and efficiency maps were checked against the pinned source.
The result is an engineering smoke only: Pack A's smoke cross section, BR,
acceptance, efficiency and weights remain separate. No `sigma*BR^2*Aepsilon`,
yield, exclusion or model-derived claim is made.

The upstream `strong-bm1` line remains `TOOLCHAIN_READY` /
`BENCHMARK_INPUTS_BLOCKED`; missing private SLHA, cards and LHE inputs are not
used or weakened here.

Exact rerun command:

```bash
cd /home/fabi/atlas_dihiggs/worktrees/recast_h2bb_smoke_20260723T000000Z
SCALAR_H2_LHE=/home/fabi/atlas_dihiggs/ufos/pack_aa/inputs/pack_a_A_PI_NATIVE_200_source.lhe.gz \
SCALAR_H2_OUT=results/scalar_h2_smoke SCALAR_H2_EVENTS=100 \
scripts/run_scalar_h2_smoke.sh
python3 scripts/extract_scalar_cutflow.py \
  --events results/scalar_h2_smoke/events.jsonl \
  --stages results/scalar_h2_smoke/events.jsonl.stages.csv \
  --json results/scalar_h2_smoke/cutflow.json \
  --csv results/scalar_h2_smoke/cutflow.csv
MPLCONFIGDIR=/tmp/mpl-scalar-h2 python3 scripts/plot_scalar_diagnostics.py \
  --events results/scalar_h2_smoke/events.jsonl \
  --out results/scalar_h2_smoke/plots
```
