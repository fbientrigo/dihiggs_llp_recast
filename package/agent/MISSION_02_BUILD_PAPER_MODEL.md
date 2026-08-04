# Mission 02 — recover or implement the MadGraph model for the paper benchmark

You are a HEP phenomenology software agent. Build the smallest scientifically auditable event-generation path for arXiv:2606.01681 before mapping the user's general 2HDM.

## Goal

Produce physical LHE samples for `gg -> h* -> S S` and validate one benchmark cutflow against Table II. Keep paper reproduction separate from the user's 2HDM recast.

## Inputs

- The supplied `package/` directory.
- arXiv:2606.01681, especially Eq. (1), the simulation setup, Table I, and Table II.
- The public `llprecasting/recastingCodes` implementation pinned by the package.

## Execution order

1. Search the paper source, author repositories, model databases, and ancillary material for the exact FeynRules/UFO files. Record every source checked.
2. If the exact UFO is found, archive its URL, commit/version, license, and SHA256. Do not modify it before a baseline run.
3. If it is not found, implement a minimal paper-model FeynRules source containing:
   - a real scalar `S`;
   - the SM-like Higgs `h`;
   - `L_int = -(lambda/2) * v * h * S * S`;
   - the interactions required for a valid full-loop `gg -> h* -> SS` calculation;
   - parameters `mS`, `sin_theta`, and `lambda` with explicit conventions.
4. Export and validate a UFO. Check particle content, Hermiticity, widths, and the `hSS` vertex normalization.
5. Generate a 10k-event smoke sample for `mS=250 GeV`, `sin_theta=1e-7`, `lambda=1`, `sqrt(s)=13 TeV`, with a fixed seed.
6. Supply the scalar lifetime and branching ratios to Pythia using a validated SLHA card. Do not reuse the toy branching ratios as paper values.
7. Run the original and modified recasts on the same event sample.
8. Compare each cutflow stage with the corresponding Table-II benchmark. Report statistical uncertainty and relative deviation.
9. Only after the smoke sample is stable, define the one-million-event validation run.

## Required outputs

- `model_source/` or a documented exact external UFO.
- `models/<ufo_name>/` with SHA256 manifest.
- `cards/madgraph/` complete process, run, and parameter cards.
- `events/paper_S250_ctau5p1mm_smoke.lhe.gz`.
- `results/paper_S250_cutflow_comparison.csv`.
- `results/paper_model_validation.md`.

## Guardrails

- Do not substitute the user's 2HDM `sin(beta-alpha)` for the paper's `sin(theta)`.
- Do not identify the paper's `lambda` with `lambda6` or `lambda7`.
- Do not infer a production cross section from the LLP total width.
- A HEFT implementation must be labelled `HEFT_KINEMATIC_PROXY` and cannot close the paper-reproduction gate without a finite-top/full-loop comparison.
- Do not start the general 2HDM mapping until the paper benchmark is validated or the remaining discrepancy is quantified.
