import pytest
from dvrecast.r12_scan import calculate_aggregated_efficiency, calculate_final_grid_row
from dvrecast.r8_cutflow import parse_recast_log

def test_trackless_aeff_uses_acc_x_eff_not_raw_acc():
    n_total = 2000
    raw_acc_total = 40
    acc_x_eff_total = 31.46772
    
    raw_acceptance = raw_acc_total / n_total
    weighted_aeff = acc_x_eff_total / n_total
    
    assert pytest.approx(raw_acceptance, rel=1e-9) == 40 / 2000  # 0.02
    assert pytest.approx(weighted_aeff, rel=1e-9) == 31.46772 / 2000  # 0.01573386
    assert pytest.approx(weighted_aeff, rel=1e-5) == 0.01573386
    assert weighted_aeff != pytest.approx(0.02, rel=0.01)

def test_parser_retains_both_acc_and_acc_x_eff():
    sample_log = """All Events:                                       1.000000e+03
Events with zero configured LLP found [%]:        0.000000e+00
High-pT Jet Selection [%]:                        2.000000e-01
High-pT Fiducial [%]:                             2.000000e-01
High-pT R_vertex > 4 mm [%]:                      2.000000e-01
High-pT Have track with |d_0| > 2 mm [%]:         2.000000e-01
High-pT Selected Decay Product >= 5 [%]:          2.000000e-01
High-pT Invariant Mass > 10 GeV [%]:              2.000000e-01
Trackless Jet Selection [%]:                      2.000000e+00
Trackless Fiducial [%]:                           2.000000e+00
Trackless R_vertex > 4 mm [%]:                    1.700000e+00
Trackless Have track with |d_0| > 2 mm [%]:       1.700000e+00
Trackless Selected Decay Product >= 5 [%]:        1.700000e+00
Trackless Invariant Mass > 10 GeV [%]:            1.700000e+00
High-pT Acc:                                      2.000000e+00
High-pT Acc x Eff:                                1.943024e+00
Trackless Acc:                                    1.700000e+01
Trackless Acc x Eff:                              1.247033e+01
High-pT Acc [%]:                                  2.000000e-01
High-pT Acc x Eff [%]:                            1.943024e-01
Trackless Acc [%]:                                1.700000e+00
Trackless Acc x Eff [%]:                          1.247033e+00
The inclusive cross section after merging is:     1.000000e-09 mb
"""
    parsed = parse_recast_log(sample_log)
    assert parsed.regions["Trackless"].acc == 17
    assert pytest.approx(parsed.regions["Trackless"].acc_x_eff, rel=1e-5) == 12.47033

def test_aggregation_uses_acc_x_eff_for_primary_aeff():
    # calculate_aggregated_efficiency
    aeff, err = calculate_aggregated_efficiency(
        acc_x_eff_1=12.47033, gen1=1000,
        acc_x_eff_2=18.99739, gen2=1000
    )
    assert pytest.approx(aeff, rel=1e-5) == (12.47033 + 18.99739) / 2000
    assert err == abs(12.47033/1000 - 18.99739/1000)
