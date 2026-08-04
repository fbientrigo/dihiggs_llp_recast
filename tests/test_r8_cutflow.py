from __future__ import annotations

import pytest

from dvrecast.r8_cutflow import combine_runs, parse_recast_log

# Trimmed, structurally faithful excerpt of what recast_2301_13866 (patched
# per patches/0001-configurable-llp-pdg-ids.patch) prints to stdout.
_SAMPLE_LOG = """
All Events:                                       1.000000e+03

Events with zero configured LLP found [%]:        0.000000e+00

High-pT Jet Selection [%]:                        2.000000e-01
Event has >= 1 DV passing [%]:
High-pT Fiducial [%]:                             2.000000e-01
High-pT R_vertex > 4 mm [%]:                      1.000000e-01
High-pT Have track with |d_0| > 2 mm [%]:         1.000000e-01
High-pT Selected Decay Product >= 5 [%]:          1.000000e-01
High-pT Invariant Mass > 10 GeV [%]:              1.000000e-01

Trackless Jet Selection [%]:                      2.100000e+00
Event has >= 1 DV passing [%]:
Trackless Fiducial [%]:                           2.100000e+00
Trackless R_vertex > 4 mm [%]:                    1.700000e+00
Trackless Have track with |d_0| > 2 mm [%]:       1.700000e+00
Trackless Selected Decay Product >= 5 [%]:        1.700000e+00
Trackless Invariant Mass > 10 GeV [%]:            1.700000e+00

High-pT Acc:                                      1.000000e+00
High-pT Acc x Eff:                                1.014900e+00
Trackless Acc:                                    1.700000e+01
Trackless Acc x Eff:                              1.187817e+01

High-pT Acc [%]:                                  1.000000e-01
High-pT Acc x Eff [%]:                            1.014900e-01
Trackless Acc [%]:                                1.700000e+00
Trackless Acc x Eff [%]:                          1.187817e+00

The inclusive cross section after merging is:     2.298600e-13 mb
"""


def test_parse_recast_log_recovers_known_run_01_counts():
    result = parse_recast_log(_SAMPLE_LOG)
    assert result.n_events == 1000
    assert result.zero_llp_events == 0
    assert result.regions["High-pT"].acc == 1
    assert result.regions["High-pT"].acc_x_eff == pytest.approx(1.0149)
    assert result.regions["Trackless"].acc == 17
    assert result.regions["Trackless"].acc_x_eff == pytest.approx(11.87817)
    assert result.regions["High-pT"].stage_counts["jet_selection_pct"] == 2
    assert result.regions["Trackless"].stage_counts["r_vertex_gt_4mm_pct"] == 17
    assert result.inclusive_cross_section_mb == pytest.approx(2.2986e-13)


def test_parse_recast_log_missing_line_raises():
    truncated = _SAMPLE_LOG.split("Trackless Jet Selection")[0]
    with pytest.raises(ValueError, match="missing expected cutflow line"):
        parse_recast_log(truncated)


def test_combine_runs_sums_raw_counts_not_percentages():
    run_02_log = _SAMPLE_LOG.replace("1.000000e+00", "3.000000e+00").replace(
        "1.700000e+01", "2.300000e+01"
    )
    run_01 = parse_recast_log(_SAMPLE_LOG)
    run_02 = parse_recast_log(run_02_log)
    combined = combine_runs([run_01, run_02])

    assert combined["High-pT"]["n_total"] == 2000
    assert combined["High-pT"]["acc_total"] == 4
    assert combined["High-pT"]["a_eff_acc"] == pytest.approx(4 / 2000)
    assert combined["Trackless"]["acc_total"] == 40
    assert combined["Trackless"]["a_eff_acc"] == pytest.approx(40 / 2000)


def test_combine_runs_rejects_empty_list():
    with pytest.raises(ValueError):
        combine_runs([])
