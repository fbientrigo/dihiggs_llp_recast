# Mass-ready input schema (Phase 5 receiver contract)

`h2_response_input_manifest.v1.schema.json` defines the manifest every
future H2 response sample (including masses beyond the currently validated
130/150/170 GeV grid) must supply before it is ingested into a response
campaign. This is a **receiver contract only** — it does not implement or
change any physics, and it does not run automatically in this release.

## Why `ctau_response_mm` and `ctau_physical_mm` are separate fields

- `ctau_response_mm`: the lifetime value written into the recast card
  (`Recast:llpTau0`) for a detector-response scan node. A factorized
  detector-response scan (as used for the validated 3x12
  `aeff_grid_20260811T042218Z` grid in this release) may vary this
  independently of any physical model width — see e.g. the ctau=0.3mm to
  1000mm scan nodes in `aeff_grid.csv`, none of which claim to be physical
  lifetimes for any specific coupling point.
- `ctau_physical_mm`: the lifetime implied by a physical model point's
  total decay width, `c*hbar/Gamma_total`. Used when the scientific question
  is about a physical coupling scenario rather than a pure detector-response
  scan (as in `results/mass_dependence_trackless/physical_ctau_summary.csv`
  in this repository's existing evidence base, where mH=130/150/170 each
  carry their own physical ctau distinct from the shared 4.326mm response
  benchmark).

**Never silently equate the two fields.** A sample manifest may set them to
the same numeric value when that is genuinely the physical lifetime being
probed (see `example_PHYSICAL_DECAYS_NO_HEAVY_CASCADES.json`), but the two
fields must always both be present and independently sourced.

## Model variants

`model_variant` here is a **physics generation** axis (how the sample was
produced/decayed), not to be confused with the recast **analysis-mode**
label (`model_variant` column in this release's own `samples.csv`, which is
always `ORIGINAL_PUBLISHED_TRACKLESS` for every sample in this release — the
recast selection, not the production physics).

This schema minimally supports:

- `FACTORIZED_G_ONLY` — pure detector-response scan points; `ctau_response_mm`
  set independently, no claim of a self-consistent physical model width.
  Example: `examples/example_FACTORIZED_G_ONLY.json`.
- `PHYSICAL_DECAYS_NO_HEAVY_CASCADES` — physical-model points with inclusive
  or forced branching sampled from an actual coupling/width calculation,
  excluding heavy-cascade decay channels by construction.
  Example: `examples/example_PHYSICAL_DECAYS_NO_HEAVY_CASCADES.json`.

Additional variants may be added later without breaking this schema
(`model_variant` is an open string field, not a closed enum).

## Validation

`validate_manifest.py` is a minimal, dependency-free structural validator
(required fields, sha256 pattern, positive-lifetime/N_events checks). It is
not a full JSON-Schema validator (no `jsonschema` package was available on
this node at release time) but enforces the same required-field/type
contract as the `.schema.json` file. Run:

```
python3 validate_manifest.py examples/example_FACTORIZED_G_ONLY.json examples/example_PHYSICAL_DECAYS_NO_HEAVY_CASCADES.json
```

## Scope

No new physics is implemented for either variant in this release. This is
scaffolding only, per mission Phase 5: "prepare the repository to ingest
future higher-mass samples without changing the current analysis."
