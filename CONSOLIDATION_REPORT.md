# strong-bm1 consolidation report

## Verdict

`UPSTREAM_STRONG_BM1_VALIDATED`

The independently generated 0j/1j/2j samples, CKKW-L merge, and unmodified
upstream recast output are consolidated into machine-readable canonical data and
deterministic plots. This is `VALIDATED` only for the High-pT strong-bm1
benchmark: the source-unit mismatch is corrected in a separate interpretation
artifact, and no statistical-significance claim is made without weighted
second moments or event weights.

## Input verification

All requested source artifacts exist: README, comparison Markdown/CSV,
diagnosis, cutflow CSV/JSON, generation summary, LHE checksums, SLHA patch,
tool/environment records, commands, build log, and run log. Their SHA-256
values are recorded in `benchmarks/upstream/strong-bm1/checksums.sha256`.
The source README/diagnosis use the historical label `STRONG_BM1_REPRODUCED`;
the canonical verdict is instead tied to the checked compact artifacts and is
explicitly benchmark-specific.

The authors' reference is `external/recastingCodes/.../2_results/strong/gluino_run01.txt`.
It supplies the reference weighted denominator 9476.625, High-pT values
99.81456%, 29.71822%, and 26.60133%, and merged cross section
4.949932e-13 mb. The reproduction log supplies 9458.407 weighted events,
7884 accepted raw events, 99.87405%, 29.92715%, 26.84045%, and
4.889942e-13 mb. ATLAS full simulation is available only as the rounded values
in the source comparison table; ATLAS parametric simulation is available only
for A×efficiency (26.0%). Missing stages remain null.

## Numerical comparison

The cross-section conversion uses 1 mb = 1e12 fb:

| quantity | authors | reproduction | difference |
|---|---:|---:|---:|
| inclusive merged cross section [fb] | 0.4949932 | 0.4889942 | -0.0059990 (-1.21194%) |
| High-pT jet selection [%] | 99.81456 | 99.87405 | +0.05949 (+0.05960%) |
| High-pT final acceptance [%] | 29.71822 | 29.92715 | +0.20893 (+0.70304%) |
| High-pT A×efficiency [%] | 26.60133 | 26.84045 | +0.23912 (+0.89890%) |

Intermediate source rows are preserved in the canonical cutflow. The repeated
values are reported as cumulative stages because the archived logs report no
additional loss between those named cuts.

## Uncertainty and provenance

MadGraph integration uncertainties are retained per multiplicity and their
independent additive quadrature is 0.0008492731 fb. It is not promoted to a
merged uncertainty because merging is not an additive estimator in the archived
artifacts. Acceptance uncertainties are explicitly unavailable: a binomial
formula would be invalid for the weighted cutflow without event weights or
sum-of-squares. Implementation differences, finite-sample effects, and theory
scale/PDF uncertainties are kept as separate concepts.

The upstream clone is at the pinned commit. Its only tracked change is the
known local Makefile path adaptation; generated objects/logs/LHE files are
untracked. No physical analysis source file differs from the pinned upstream.

## Canonical derivations and scope

Imported compact source evidence remains immutable under
`original_llp_results/strong_bm1_20260724_000724` and the authors' archived
output remains immutable under `original_llp`. Derived repository artifacts are
the normalized-fb generation summary, recomputed comparison JSON, corrected
unit interpretation JSON, and deterministic PNG/PDF/SVG plots. The corrected
interpretation records $4.889942\times10^{-13}$ mb as $0.0004889942$ pb and
$0.4889942$ fb; it never reports the source's mislabeled $0.4889942$ as pb.

Closed scope: one High-pT strong-bm1 benchmark, including its 0j/1j/2j CKKW-L
technical inputs, authors-versus-ours numerical reconciliation, and the
separate supported ATLAS comparison. Open scope: other benchmarks, Trackless,
efficiency-map bin validation, ALP/H2 interpretation, exclusions, and a
rigorous weighted statistical-significance calculation.
