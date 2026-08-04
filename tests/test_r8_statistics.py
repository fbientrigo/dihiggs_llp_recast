from __future__ import annotations

import pytest

from dvrecast.statistics import (
    clopper_pearson_interval,
    ks_critical_value,
    ks_two_sample_statistic,
)


def test_clopper_pearson_zero_successes_matches_textbook_value():
    lower, upper = clopper_pearson_interval(0, 10, confidence=0.95)
    assert lower == 0.0
    assert upper == pytest.approx(0.3085, abs=1e-4)


def test_clopper_pearson_symmetric_case_matches_textbook_value():
    lower, upper = clopper_pearson_interval(5, 10, confidence=0.95)
    assert lower == pytest.approx(0.1871, abs=1e-4)
    assert upper == pytest.approx(0.8129, abs=1e-4)


def test_clopper_pearson_all_successes():
    lower, upper = clopper_pearson_interval(10, 10, confidence=0.95)
    assert upper == 1.0
    assert lower == pytest.approx(0.6915, abs=1e-4)


@pytest.mark.parametrize("k,n", [(-1, 10), (11, 10)])
def test_clopper_pearson_rejects_invalid_k(k, n):
    with pytest.raises(ValueError):
        clopper_pearson_interval(k, n)


def test_clopper_pearson_rejects_nonpositive_n():
    with pytest.raises(ValueError):
        clopper_pearson_interval(0, 0)


def test_ks_two_sample_statistic_zero_for_identical_samples():
    sample = [0.1, 0.5, 0.9, 1.2, 3.4]
    assert ks_two_sample_statistic(sample, sample) == 0.0


def test_ks_two_sample_statistic_detects_shifted_distributions():
    a = [0.0, 1.0, 2.0, 3.0, 4.0]
    b = [10.0, 11.0, 12.0, 13.0, 14.0]
    assert ks_two_sample_statistic(a, b) == 1.0


def test_ks_two_sample_statistic_rejects_empty_sample():
    with pytest.raises(ValueError):
        ks_two_sample_statistic([], [1.0])


def test_ks_critical_value_matches_known_coefficient():
    # c(0.05) * sqrt((n+n)/(n*n)) with n=n reduces to c(0.05)*sqrt(2/n)
    n = 100
    expected = 1.35810 * (2 / n) ** 0.5
    assert ks_critical_value(n, n, alpha=0.05) == pytest.approx(expected, rel=1e-9)


def test_ks_critical_value_rejects_unsupported_alpha():
    with pytest.raises(ValueError):
        ks_critical_value(100, 100, alpha=0.5)
