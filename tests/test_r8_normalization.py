from __future__ import annotations

import pytest

from dvrecast.r8_normalization import (
    BR_BB_SQUARED,
    SIGMA_H2H2_PB,
    expected_signal_events,
    sigma_4b_fb,
    visible_sigma_fb,
)


def test_sigma_4b_fb_matches_canonical_manifest_value():
    # hep_cross artifacts/h2_first_physical/production_manifest.json:
    # sigma_physical_4b_fb = 0.131876610738628
    assert sigma_4b_fb() == pytest.approx(0.131876610738628, rel=1e-12)


def test_br_squared_applied_exactly_once():
    # Applying BR_bb_squared via sigma_4b_fb and again via visible_sigma_fb
    # would double-count; visible_sigma_fb must only scale by acceptance.
    once = sigma_4b_fb(SIGMA_H2H2_PB, BR_BB_SQUARED)
    twice = SIGMA_H2H2_PB * BR_BB_SQUARED * BR_BB_SQUARED * 1000.0
    assert once != pytest.approx(twice)
    assert visible_sigma_fb(1.0, once) == pytest.approx(once)


def test_visible_sigma_scales_linearly_with_acceptance():
    base = sigma_4b_fb()
    assert visible_sigma_fb(0.01, base) == pytest.approx(base * 0.01)
    assert visible_sigma_fb(0.0, base) == 0.0


def test_expected_signal_events_none_without_luminosity():
    assert expected_signal_events(1.0, None) is None


def test_expected_signal_events_scales_with_luminosity():
    assert expected_signal_events(2.0, 100.0) == pytest.approx(200.0)
