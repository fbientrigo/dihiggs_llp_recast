"""Three-point derivatives for long-form response tables."""

from __future__ import annotations

from collections.abc import Sequence
from math import isfinite

import pandas as pd

__all__ = ["validate_series", "three_point_derivative", "differentiate_response_table"]


def validate_series(s: Sequence[float], y: Sequence[float]) -> tuple[list[float], list[float]]:
    """Validate and convert one response series for differentiation."""
    if len(s) != len(y):
        raise ValueError("s and response must have the same length")
    if len(s) < 3:
        raise ValueError("at least 3 distinct s points are required")

    try:
        s_values = [float(value) for value in s]
        y_values = [float(value) for value in y]
    except (TypeError, ValueError) as exc:
        raise ValueError("s and response values must be numeric") from exc

    if not all(isfinite(value) for value in s_values):
        raise ValueError("s values must be finite")
    if not all(isfinite(value) for value in y_values):
        raise ValueError("response values must be finite")
    if len(set(s_values)) != len(s_values):
        raise ValueError("duplicated s values are not allowed inside a group")
    return s_values, y_values


def _lagrange_derivative(x: Sequence[float], y: Sequence[float], target: float) -> float:
    """Evaluate the derivative of the quadratic Lagrange interpolant."""
    derivative = 0.0
    for j in range(3):
        numerator = 0.0
        denominator = 1.0
        for k in range(3):
            if k == j:
                continue
            denominator *= x[j] - x[k]
            other = 3 - j - k
            numerator += target - x[other]
        derivative += y[j] * numerator / denominator
    return derivative


def _derivative_with_schemes(
    s: Sequence[float], y: Sequence[float]
) -> tuple[list[float], list[str]]:
    s_values, y_values = validate_series(s, y)
    order = sorted(range(len(s_values)), key=s_values.__getitem__)
    x = [s_values[index] for index in order]
    values = [y_values[index] for index in order]
    sorted_derivatives: list[float] = [0.0] * len(x)
    sorted_schemes: list[str] = [""] * len(x)

    for index, target in enumerate(x):
        if index == 0:
            window = (0, 1, 2)
            scheme = "lower_3pt"
        elif index == len(x) - 1:
            window = (len(x) - 3, len(x) - 2, len(x) - 1)
            scheme = "upper_3pt"
        else:
            window = (index - 1, index, index + 1)
            scheme = "central_3pt"
        sorted_derivatives[index] = _lagrange_derivative(
            [x[item] for item in window], [values[item] for item in window], target
        )
        sorted_schemes[index] = scheme

    # Public function results follow the caller's input order, while the table
    # function sorts its rows before calling this helper.
    derivatives = [0.0] * len(order)
    schemes = [""] * len(order)
    for sorted_index, original_index in enumerate(order):
        derivatives[original_index] = sorted_derivatives[sorted_index]
        schemes[original_index] = sorted_schemes[sorted_index]
    return (
        derivatives,
        schemes,
    )


def three_point_derivative(s: Sequence[float], y: Sequence[float]) -> list[float]:
    """Return the three-point Lagrange derivative in the input row order."""
    return _derivative_with_schemes(s, y)[0]


def differentiate_response_table(
    df: pd.DataFrame,
    value_col: str,
    group_cols: Sequence[str] = (),
    s_col: str = "s",
) -> pd.DataFrame:
    """Differentiate one response column independently within each group.

    The result contains the group metadata, coordinate, original response,
    derivative, and the stencil used at each coordinate. Input response values
    are copied without smoothing or fitting.
    """
    group_cols = list(group_cols)
    if df.empty:
        raise ValueError("response table is empty")
    if len(set(group_cols)) != len(group_cols):
        raise ValueError("group columns must be unique")
    required = [s_col, value_col, *group_cols]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"missing required column(s): {', '.join(missing)}")
    if s_col in group_cols:
        raise ValueError("s column cannot also be a group column")

    grouped = (
        [((), df)]
        if not group_cols
        else df.groupby(group_cols, sort=True, dropna=False, observed=False)
    )
    result_parts: list[pd.DataFrame] = []
    output_cols = [*group_cols, s_col, value_col, "dresponse_ds", "derivative_scheme"]

    for _, group in grouped:
        s_values, y_values = validate_series(group[s_col].tolist(), group[value_col].tolist())
        order = sorted(range(len(s_values)), key=s_values.__getitem__)
        derivatives, schemes = _derivative_with_schemes(
            [s_values[index] for index in order], [y_values[index] for index in order]
        )
        part = group.iloc[order][[*group_cols, s_col, value_col]].copy()
        part["dresponse_ds"] = derivatives
        part["derivative_scheme"] = schemes
        result_parts.append(part[output_cols])

    return pd.concat(result_parts, ignore_index=True)[output_cols]
