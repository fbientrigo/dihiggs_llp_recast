"""Physical normalization arithmetic for the R8 H2->4b recast.

Canonical numbers (from hep_cross artifacts/h2_first_physical/production_manifest.json,
merge commit f601e318c57f780d21e8dbee4dcccd7ec1b7b88a):

    sigma_H2H2_pb = 0.000230291167568
    BR_bb = 0.756737485808578692
    BR_bb_squared = 0.5726516224278888  (== BR_bb ** 2, applied exactly once here)
    sigma_physical_4b_fb = 0.131876610738628

BR^2 is baked into sigma_physical_4b_fb already (forced H2->bb changes only
event sampling, per the mission brief); this module must never re-apply
BR_bb or BR_bb_squared to the recast's acceptance, only to the production
cross section, and must do so exactly once.
"""

from __future__ import annotations

SIGMA_H2H2_PB = 0.000230291167568
BR_BB = 0.756737485808578692
BR_BB_SQUARED = 0.5726516224278888


def sigma_4b_fb(
    sigma_h2h2_pb: float = SIGMA_H2H2_PB, br_bb_squared: float = BR_BB_SQUARED
) -> float:
    """sigma(pp -> H2 H2) * BR(H2->bb)^2, converted pb -> fb (applied exactly once)."""
    return sigma_h2h2_pb * br_bb_squared * 1000.0


def visible_sigma_fb(a_eff: float, sigma_4b_fb_value: float | None = None) -> float:
    if sigma_4b_fb_value is None:
        sigma_4b_fb_value = sigma_4b_fb()
    return sigma_4b_fb_value * a_eff


def expected_signal_events(
    visible_sigma_fb_value: float, luminosity_fb_inv: float | None
) -> float | None:
    if luminosity_fb_inv is None:
        return None
    return visible_sigma_fb_value * luminosity_fb_inv
