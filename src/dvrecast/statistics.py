"""Dependency-free finite-statistics helpers: exact (Clopper-Pearson) binomial
intervals and the two-sample Kolmogorov-Smirnov D statistic.

Implemented from first principles (no scipy) to keep this package's zero
declared dependencies; the regularized incomplete beta function uses the
standard continued-fraction evaluation (Numerical Recipes ss6.4) built only
on ``math.lgamma``.
"""

from __future__ import annotations

import math


def _betacf(x: float, a: float, b: float, max_iter: int = 200, eps: float = 1e-12) -> float:
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < 1e-30:
        d = 1e-30
    d = 1.0 / d
    h = d
    for m in range(1, max_iter + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-30:
            d = 1e-30
        c = 1.0 + aa / c
        if abs(c) < 1e-30:
            c = 1e-30
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-30:
            d = 1e-30
        c = 1.0 + aa / c
        if abs(c) < 1e-30:
            c = 1e-30
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def regularized_incomplete_beta(x: float, a: float, b: float) -> float:
    """I_x(a, b), the regularized incomplete beta function, for x in [0, 1]."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    ln_beta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(ln_beta + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(x, a, b) / a
    return 1.0 - front * _betacf(1.0 - x, b, a) / b


def _invert_regularized_incomplete_beta(
    p: float, a: float, b: float, iterations: int = 100
) -> float:
    lo, hi = 0.0, 1.0
    for _ in range(iterations):
        mid = 0.5 * (lo + hi)
        if regularized_incomplete_beta(mid, a, b) < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def clopper_pearson_interval(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """Exact binomial confidence interval for k successes out of n trials."""
    if n <= 0:
        raise ValueError("n must be positive")
    if k < 0 or k > n:
        raise ValueError("k must satisfy 0 <= k <= n")
    if not (0.0 < confidence < 1.0):
        raise ValueError("confidence must be in (0, 1)")
    alpha = 1.0 - confidence
    lower = 0.0 if k == 0 else _invert_regularized_incomplete_beta(alpha / 2.0, k, n - k + 1)
    upper = 1.0 if k == n else _invert_regularized_incomplete_beta(1.0 - alpha / 2.0, k + 1, n - k)
    return lower, upper


def ks_two_sample_statistic(sample_a: list[float], sample_b: list[float]) -> float:
    """Two-sample Kolmogorov-Smirnov D statistic: max |CDF_a - CDF_b|."""
    if not sample_a or not sample_b:
        raise ValueError("both samples must be non-empty")
    a = sorted(sample_a)
    b = sorted(sample_b)
    na, nb = len(a), len(b)
    points = sorted(set(a) | set(b))
    d_max = 0.0
    ia = ib = 0
    for x in points:
        while ia < na and a[ia] <= x:
            ia += 1
        while ib < nb and b[ib] <= x:
            ib += 1
        d_max = max(d_max, abs(ia / na - ib / nb))
    return d_max


def ks_critical_value(n_a: int, n_b: int, alpha: float = 0.05) -> float:
    """Asymptotic KS critical value for the D statistic at significance alpha.

    Uses the standard c(alpha) coefficients (Kolmogorov distribution):
    c(0.10) = 1.22384, c(0.05) = 1.35810, c(0.01) = 1.62762.
    """
    coefficients = {0.10: 1.22384, 0.05: 1.35810, 0.01: 1.62762}
    if alpha not in coefficients:
        raise ValueError(f"alpha must be one of {sorted(coefficients)}")
    return coefficients[alpha] * math.sqrt((n_a + n_b) / (n_a * n_b))
