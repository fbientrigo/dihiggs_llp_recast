# M2 strong-bm1 generation-contract report

> Historical pre-freeze record. Its generation-input status does not supersede
> the canonical compact strong-bm1 result freeze described in
> `benchmarks/upstream/strong-bm1/README.md` and `CONSOLIDATION_REPORT.md`.

Status: `TOOLCHAIN_READY_BENCHMARK_INPUTS_BLOCKED`. Generation contract: `INCOMPLETE`.

## Recovered exactly

MadGraph5_aMC@NLO 3.5.3, the bundled `MSSM_SLHA2` model, all three process
definitions, 2000/850 GeV masses, neutralino PDG 1000022, 13 TeV beams,
NNPDF23 LO (`nn23lo1`, LHAPDF 230000), generation cuts, 10,000 events per
parton multiplicity, CKKW-L kT merging at 500 GeV, Pythia 8.308 configuration,
input naming, and the upstream `gluino_run01.txt` reference are directly
supported by frozen files or the reference event record.

## Not recovered

The exact bm1 SLHA, assigned automatic seeds, gluino width, full gluino
branching table, exact neutralino width/lifetime, and full neutralino branching
table are absent. The reference event record supports the particle identities
and examples of their decays but does not reconstruct the complete tables.

The 0.01 ns lifetime is only a low-confidence inference from two independent
pieces of evidence: the bm1 `0p01` label and the supplied, nonmatching
`p01ns` card with a corresponding width. It is not treated as an exact bm1
value and is not sufficient to create a final SLHA.

## Consequence

The verified local toolchain is ready: MG5 3.5.3 at
`/home/fabi/.local/mg5amcnlo/3.5.3/bin/mg5_aMC`, Pythia 8.308 at
`/home/fabi/.local/pythia8308`, and FastJet 3.4.0 at
`/home/fabi/.local/fastjet-3.4.0`. Generating even a smoke bm1 sample is not:
changing the unknown width or
decay assumptions directly changes DV acceptance. M2 therefore advances the
auditable architecture but stops before event generation. Gate B and all
scalar adaptation remain blocked pending the original card or an explicitly
approved reconstruction contract.

## MadGraph local

The process cards recover MG5 3.5.3 exactly. The historical Launchpad archive
was unavailable (HTTP 404), so the installer uses official Git tag `v3.5.3`,
verified at commit `59b4b9c1238978f39a32b8bc83244328187704b6`. The clean
checkout is installed at `$HOME/.local/mg5amcnlo/3.5.3` and passes its help
probe using Python 3.12.3 with `six` 1.17.0, GCC 13.3.0, and GFortran 13.3.0.
The bundled `MSSM_SLHA2` import also succeeds without defining or generating a
process. MG5 warns that Python 3.12 support is experimental and reweighting is
not functional; use a supported interpreter before any approved production
campaign. The banner also labels this official tagged Git checkout an
`UNKNOWN DEVELOPMENT VERSION`; this warning is retained rather than hidden.
