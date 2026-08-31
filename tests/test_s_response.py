from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from dvrecast.s_response import differentiate_response_table, three_point_derivative


def test_quadratic_is_exact_at_both_edges() -> None:
    s = [-2.0, -1.0, 0.0, 1.0, 2.0]
    assert three_point_derivative(s, [x * x for x in s]) == pytest.approx(
        [2.0 * x for x in s]
    )


def test_linear_is_exact() -> None:
    s = [-3.0, -0.5, 2.0, 7.0]
    a, b = -2.75, 4.125
    assert three_point_derivative(s, [a * x + b for x in s]) == pytest.approx([a] * len(s))


def test_unsorted_input_preserves_public_row_order() -> None:
    s = [2.0, 0.0, 1.0]
    assert three_point_derivative(s, [4.0, 0.0, 1.0]) == pytest.approx([4.0, 0.0, 2.0])


def test_nonuniform_grid_uses_lagrange_weights() -> None:
    s = [0.0, 0.7, 2.4, 5.0, 9.0]
    y = [3.0 * x * x - 2.0 * x + 7.0 for x in s]
    assert three_point_derivative(s, y) == pytest.approx([6.0 * x - 2.0 for x in s])


def test_groups_are_differentiated_independently() -> None:
    rows = []
    for group, values in ((130, lambda x: x * x), (250, lambda x: 10.0 + 3.0 * x)):
        for s in (0.1, 0.4, 1.0, 2.0):
            rows.append({"mH2": group, "s": s, "response": values(s)})

    out = differentiate_response_table(pd.DataFrame(rows), "response", ["mH2"])
    assert out[out["mH2"] == 130]["dresponse_ds"].tolist() == pytest.approx(
        [0.2, 0.8, 2.0, 4.0]
    )
    assert out[out["mH2"] == 250]["dresponse_ds"].tolist() == pytest.approx([3.0] * 4)


def test_current_response_table_regression() -> None:
    root = Path(__file__).resolve().parents[1]
    input_path = root / (
        "results/jet_threshold_response_20260815T230503Z/response_table/response_table.csv"
    )
    df = pd.read_csv(input_path)

    for value_col in ("local_eff", "cumulative_eff", "acc"):
        out = differentiate_response_table(df, value_col, ["mH2", "stage"])
        assert len(out) == len(df)
        assert out["s"].tolist() == sorted(df["s"].unique().tolist()) * 40
        pd.testing.assert_series_equal(
            out[value_col].reset_index(drop=True),
            df.sort_values(["mH2", "stage", "s"])[value_col].reset_index(drop=True),
            check_names=False,
        )
        for key, original in df.groupby(["mH2", "stage"], sort=True):
            got = out[(out["mH2"] == key[0]) & (out["stage"] == key[1])]
            original = original.sort_values("s")
            expected = three_point_derivative(original["s"].tolist(), original[value_col].tolist())
            assert got["dresponse_ds"].tolist() == pytest.approx(expected)

    final = df[df["stage"] == "final acceptance"]
    out = differentiate_response_table(final, "acc_x_eff", ["mH2", "stage"])
    assert len(out) == 50
    pd.testing.assert_series_equal(
        out["acc_x_eff"].reset_index(drop=True),
        final.sort_values(["mH2", "stage", "s"])["acc_x_eff"].reset_index(drop=True),
        check_names=False,
    )


@pytest.mark.parametrize(
    ("s_values", "response", "message"),
    [
        ([0.1, 0.2], [1.0, 2.0], "at least 3"),
        ([0.1, 0.2, 0.2], [1.0, 2.0, 3.0], "duplicated"),
        ([0.1, float("nan"), 0.3], [1.0, 2.0, 3.0], "finite"),
    ],
)
def test_invalid_series_is_rejected(s_values, response, message) -> None:
    with pytest.raises(ValueError, match=message):
        three_point_derivative(s_values, response)
