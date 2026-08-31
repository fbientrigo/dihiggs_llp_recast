# Existing H2 LHE inventory for 300/350 GeV search

The inventory below is the complete H2-containing LHE set found in the local
`fbientrigo/dihiggs_hep_cross` checkout. Event counts are per file. The MG5
banners record `generate g g > H > h2 h2`, 13 TeV beams, `nn23lo1`, and 10,000
requested events for the `r14_direct_g_production` files; the H2 records have
status 1 in the LHE event records. The 150 GeV artifact samples have their
additional provenance recorded in `artifacts/h2_first_physical/production_manifest.json`.

| path | mass [GeV] | events | production / provenance | SHA256 | verdict for 300/350 |
|---|---:|---:|---|---|---|
| `results/r14_direct_g_production/proc_output/Events/run_H2scan_mH130_tb300000_s101/unweighted_events.lhe.gz` | 130 | 10,000 | MG5 banner; run s101 | `5997e4f3a527703ae0be9eef5dae40086240c96f19789cd849e8f878c0e9dbd6` | wrong mass |
| `results/r14_direct_g_production/proc_output/Events/run_H2scan_mH130_tb300000_s107/unweighted_events.lhe.gz` | 130 | 10,000 | MG5 banner; run s107 | `da3a2c9614ab1c055fc78d51f3e62b064ca194c87162f73db441912f1946fd8b` | wrong mass |
| `results/r14_direct_g_production/proc_output/Events/run_H2scan_mH150_tb240000_s101/unweighted_events.lhe.gz` | 150 | 10,000 | MG5 banner; run s101 | `1b8a14b1457ef07b14671953243750a2c37fb247f9bc593854bcd07a9f0e0019` | wrong mass |
| `results/r14_direct_g_production/proc_output/Events/run_H2scan_mH150_tb240000_s107/unweighted_events.lhe.gz` | 150 | 10,000 | MG5 banner; run s107 | `1f42bae498b2e430eefac0dee168fb51c5d64bf97343d860dc5b30821dbb8d8a` | wrong mass |
| `results/r14_direct_g_production/proc_output/Events/run_H2scan_mH150_tb300000_s101/unweighted_events.lhe.gz` | 150 | 10,000 | MG5 banner; canonical production run s101 | `35f47f55289919eed0a234b6ba6f8729d6728c10cd4363cba035fbc4cfdb0144` | wrong mass |
| `results/r14_direct_g_production/proc_output/Events/run_H2scan_mH150_tb300000_s107/unweighted_events.lhe.gz` | 150 | 10,000 | MG5 banner; canonical production run s107 | `a81e6bbeb2da9965b928db5529b5909054fea04526f228ee9dde73bc273da7f3` | wrong mass |
| `results/r14_direct_g_production/proc_output/Events/run_H2scan_mH150_tb360000_s101/unweighted_events.lhe.gz` | 150 | 10,000 | MG5 banner; run s101 | `ad07451b242336b30f49bb6e0bfc41e400fc4407e1845964e65b6b9b05b1ce0d` | wrong mass |
| `results/r14_direct_g_production/proc_output/Events/run_H2scan_mH150_tb360000_s107/unweighted_events.lhe.gz` | 150 | 10,000 | MG5 banner; run s107 | `15ae69a1d8ce7a112cbed184da6c2ef9bd61ba143e153e4ca43fbd4c7f620ce8` | wrong mass |
| `results/r14_direct_g_production/proc_output/Events/run_H2scan_mH170_tb300000_s101/unweighted_events.lhe.gz` | 170 | 10,000 | MG5 banner; run s101 | `b7092f7bfb775760a30b7fce08ba1035adcdc4f7904907c656bee9a3afbf872c` | wrong mass |
| `results/r14_direct_g_production/proc_output/Events/run_H2scan_mH170_tb300000_s107/unweighted_events.lhe.gz` | 170 | 10,000 | MG5 banner; run s107 | `39027dba4e5fa2a537671596bbf784ac32aaa49dc31db1a98bb07dcb94085fa0` | wrong mass |
| `results/r14_direct_g_production/proc_output/Events/run_point_011af49c15561f96_s101/unweighted_events.lhe.gz` | 200 | 10,000 | MG5 banner; run s101 | `0090afc8b2fbb330e3705a258ad96069ffedfaf5172d11f5653ac488f803c8bf` | wrong mass |
| `results/r14_direct_g_production/proc_output/Events/run_point_011af49c15561f96_s107/unweighted_events.lhe.gz` | 200 | 10,000 | MG5 banner; run s107 | `67be362481c1f0d5810066645273a35c5ecc1ae886ad84018c6926ba6a7aee58` | wrong mass |
| `results/r14_direct_g_production/proc_output/Events/run_point_0960bd688a662562_s101/unweighted_events.lhe.gz` | 250 | 10,000 | MG5 banner; run s101 | `c6c3292715b6a961e50c47f3542ec1c3bdaf209d24b4e6141d2cb54d73761198` | wrong mass |
| `results/r14_direct_g_production/proc_output/Events/run_point_0960bd688a662562_s107/unweighted_events.lhe.gz` | 250 | 10,000 | MG5 banner; run s107 | `c1888779e677562857325a8592310aab801eed677b5ffb60e7ea91ff78f16159` | wrong mass |
| `artifacts/h2_first_physical/madgraph/run_01/unweighted_events.lhe.gz` | 150 | 1,000 | MG5 3.5.3 manifest; seed 101; stable in LHE | `1c580b7a590f9bbfbf213eeef0e54fdcc4b6c1dce3f13bc0ed5278f6f3aec202` | wrong mass and lower statistics |
| `artifacts/h2_first_physical/madgraph/run_02/unweighted_events.lhe.gz` | 150 | 1,000 | MG5 3.5.3 manifest; seed 107; stable in LHE | `385faebf45403c224ce374488c3e51a06be56b13ec6b095f92393d0c8f4b1bfa` | wrong mass and lower statistics |

The corresponding local relabelled response inputs were also checked. Their
provenance is inherited from the source rows above; relabelling changes the
LLP PDG handoff only and does not create a new mass point.

| local path | mass [GeV] | events | inherited source/run | SHA256 | verdict for 300/350 |
|---|---:|---:|---|---|---|
| `data/raw/mass_dependence_trackless/relabelled_full_mH130_s101.lhe.gz` | 130 | 10,000 | r14 mH130 s101 | `f847b8b4af7ef0e5abae674536bf6c8f15e2699963fd3c1a1dbb8d1598bcb80e` | wrong mass |
| `data/raw/mass_dependence_trackless/relabelled_full_mH130_s107.lhe.gz` | 130 | 10,000 | r14 mH130 s107 | `64da630196ec695d4d38723eddac9f86391b590410f35ec11ef62baa814c49f2` | wrong mass |
| `results/aeff_grid_20260811T042218Z/inputs/relabelled_full_mH150_s101.lhe.gz` | 150 | 10,000 | r14 canonical mH150 s101 | `ec5b084c84ca90008bfc3efb5cd07fb189de5552ffee9ba4c75ade0d7628d457` | wrong mass |
| `results/aeff_grid_20260811T042218Z/inputs/relabelled_full_mH150_s107.lhe.gz` | 150 | 10,000 | r14 canonical mH150 s107 | `ba1981b70a7646d532edb8221f6aaa6c75abf34c85dede7345d94b89e20f5dbf` | wrong mass |
| `data/raw/mass_dependence_trackless/relabelled_full_mH170_s101.lhe.gz` | 170 | 10,000 | r14 mH170 s101 | `718cf189a4a0076e3aba1f5681b1cecd9a5712e3ec3f46a9e8dd25dd33bbaaa6` | wrong mass |
| `data/raw/mass_dependence_trackless/relabelled_full_mH170_s107.lhe.gz` | 170 | 10,000 | r14 mH170 s107 | `b97835418e559a62664348948a33503177164fb5852c60a4cff228a57473e6e2` | wrong mass |
| `data/raw/jet_threshold_response/relabelled_full_mH200_s101.lhe.gz` | 200 | 10,000 | r14 point 011af49c s101 | `d78c8ed9c615dc7d2014e0a21e4d73ae86c02e701bcf52a9581463b34f95282b` | wrong mass |
| `data/raw/jet_threshold_response/relabelled_full_mH200_s107.lhe.gz` | 200 | 10,000 | r14 point 011af49c s107 | `417936bae7e5c5eb77c654aa4aeec41eac882cfe4293628cd835d776b04be3f` | wrong mass |
| `data/raw/jet_threshold_response/relabelled_full_mH250_s101.lhe.gz` | 250 | 10,000 | r14 point 0960bd68 s101 | `c341e83135913d50527b09e8b746bf68bc4ab35cb43300f7511595cde1f9ac95` | wrong mass |
| `data/raw/jet_threshold_response/relabelled_full_mH250_s107.lhe.gz` | 250 | 10,000 | r14 point 0960bd68 s107 | `938606905934eb1dcd5d01cb6a8759e4eae22bec931c2dcbfc0fafd8e655cfdf` | wrong mass |

No row at 300 or 350 GeV exists. The local relabelled copies and the frozen
response inputs are derived artifacts, not new mass points; their SHA256
records are in `results/jet_threshold_response_20260815T230503Z/reference/input_sha256.txt`.
