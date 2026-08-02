# strong-bm1 consolidation report

## Verdict

`UPSTREAM_STRONG_BM1_PROVISIONAL`

The independently generated 0j/1j/2j samples, CKKW-L merge, and unmodified
upstream recast output are consolidated into machine-readable canonical data and
deterministic plots. The result is not marked `VALIDATED` because the source
package labels one femtobarn-scale value as pb and archives weighted sums but
not weighted second moments or event weights.

## Input verification

All requested source artifacts exist: README, comparison Markdown/CSV,
diagnosis, cutflow CSV/JSON, generation summary, LHE checksums, SLHA patch,
tool/environment records, commands, build log, and run log. Their SHA-256
values are recorded in `benchmarks/upstream/strong-bm1/checksums.sha256`.
The source README/diagnosis use the historical label `STRONG_BM1_REPRODUCED`;
that label is not adopted here because the uncertainty and unit gates below are
not closed.

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
