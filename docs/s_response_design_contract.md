# S-response derivative utility: design contract

## Input

- A long-form pandas `DataFrame` or table readable by pandas.
- One configurable coordinate column `s` (default name: `s`).
- One configurable response/value column, for example `local_eff`,
  `cumulative_eff`, `acc`, or `acc_x_eff`.
- Zero or more configurable group-by columns, such as `mH2`, `ctau`,
  `coupling`, `channel`, `benchmark`, and `stage`.
- Each group is expected to contain one response value for each distinct `s`.

## Operation

- Validate each differentiated series before calculating its derivative.
- Sort each group by increasing `s`; retain the original coordinate and response
  values in the output.
- Use the three-point Lagrange derivative on the nearest three distinct points.
- Use the lower one-sided stencil at the first point, the central stencil for
  interior points, and the upper one-sided stencil at the last point.
- Do not assume equal spacing, fit a curve, or smooth the measured response.
- For an equally spaced grid, the Lagrange weights reduce to the stated
  `[-3, 4, -1] / (2h)`, `[ -1, 0, 1 ] / (2h)`, and `[1, -4, 3] / (2h)` forms.

## Output

- The original group metadata and original `s` coordinate.
- The selected response value under its original column name.
- `dresponse_ds`, containing the derivative with respect to `s`.
- `derivative_scheme`, one of `lower_3pt`, `central_3pt`, or `upper_3pt`.
- Rows sorted by group metadata and increasing `s` for deterministic output.
- A derivative CSV or Parquet table from the CLI.
- One self-contained interactive Plotly HTML with response above derivative.

## Failure cases

- Raise a clear error when a group has fewer than three distinct `s` points.
- Raise a clear error when `s` values are duplicated inside a group.
- Raise a clear error when any differentiated `s` or response value is non-finite.
- Raise a clear error when a requested column is missing.
- Do not silently drop incomplete groups or modify response values.

## Scope

- The utility differentiates measured discrete responses only.
- Physics quantities, masses, couplings, and stage names are data, not code
  constants in the derivative module.
- Plot controls may expose whichever response columns and grouping values are
  present in the supplied table.
