#!/usr/bin/env python3
"""Write a response/derivative table and an interactive Plotly view."""

from __future__ import annotations

import argparse
import html
import json
import math
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dvrecast.s_response import differentiate_response_table  # noqa: E402

# The self-contained HTML/CSS template below intentionally contains long lines.
# ruff: noqa: E501

DEFAULT_VALUE_COLS = ("local_eff", "cumulative_eff", "acc", "acc_x_eff")


def _read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def _finite_response(series: pd.Series) -> bool:
    numeric = pd.to_numeric(series, errors="coerce")
    return bool(numeric.notna().all() and numeric.map(math.isfinite).all())


def _differentiate_available_responses(
    df: pd.DataFrame,
    value_cols: list[str],
    group_cols: list[str],
    s_col: str,
    stage_col: str | None,
    derivative_col: str = "dresponse_ds",
    derivative_scheme_col: str = "derivative_scheme",
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for value_col in value_cols:
        if stage_col is None:
            slices = [(None, df)]
        else:
            slices = df.groupby(stage_col, sort=True, dropna=False, observed=False)
        for stage_value, stage_df in slices:
            response = stage_df[value_col]
            if response.isna().all():
                # A metric can be intentionally undefined for a stage, as
                # acc_x_eff is for all non-final stages in the current table.
                continue
            if not _finite_response(response):
                raise ValueError(
                    f"response column {value_col!r} contains non-finite values "
                    f"in {stage_col}={stage_value!r}"
                )
            differentiated = differentiate_response_table(
                stage_df, value_col=value_col, group_cols=group_cols, s_col=s_col
            )
            differentiated = differentiated.rename(
                columns={
                    value_col: "response",
                    "dresponse_ds": derivative_col,
                    "derivative_scheme": derivative_scheme_col,
                }
            )
            differentiated.insert(0, "response_column", value_col)
            frames.append(differentiated)

    if not frames:
        raise ValueError("no response/stage combination has at least three finite s points")
    return pd.concat(frames, ignore_index=True)


def _write_table(df: pd.DataFrame, output: Path, parquet_output: Path | None) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix.lower() == ".parquet":
        df.to_parquet(output, index=False)
    else:
        df.to_csv(output, index=False)
    if parquet_output is not None:
        parquet_output.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(parquet_output, index=False)


def _ordered_values(series: pd.Series) -> list[object]:
    """Return distinct values in a stable, data-driven presentation order."""
    values = series.drop_duplicates().tolist()
    numeric = pd.to_numeric(pd.Series(values), errors="coerce")
    if numeric.notna().all():
        return [
            value
            for _, value in sorted(
                zip(numeric.tolist(), values, strict=True), key=lambda item: item[0]
            )
        ]
    return sorted(values, key=lambda value: str(value))


def _ordered_stage_values(df: pd.DataFrame, stage_col: str | None) -> list[object]:
    if stage_col is None:
        return [None]
    if "stage_order" in df.columns:
        stages = (
            df[[stage_col, "stage_order"]]
            .drop_duplicates(subset=[stage_col])
            .sort_values("stage_order", kind="stable")[stage_col]
            .tolist()
        )
        return stages
    return _ordered_values(df[stage_col])


def _json_safe(value: object) -> object:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def _plot(
    derivative_df: pd.DataFrame,
    output: Path,
    group_cols: list[str],
    stage_col: str | None,
    stage_values: list[object],
    coordinate_col: str,
    mass_col: str,
) -> None:
    response_columns = set(derivative_df["response_column"].dropna().tolist())
    display_columns = [
        column for column in ("local_eff", "cumulative_eff") if column in response_columns
    ]
    if not display_columns:
        raise ValueError("the interactive plot requires local_eff and/or cumulative_eff data")

    mass_values = _ordered_values(derivative_df[mass_col])
    threshold_values = _ordered_values(derivative_df[coordinate_col])
    stage_values = [
        stage
        for stage in stage_values
        if stage_col is None
        or derivative_df[derivative_df[stage_col].eq(stage)]["response_column"].isin(
            display_columns
        ).any()
    ]
    if not stage_values:
        raise ValueError("no plottable cutflow stages were found")

    figure = go.Figure()
    selections: list[dict[str, object]] = []
    axis_specs = (
        {
            "view_axis": "threshold",
            "fixed_col": mass_col,
            "fixed_values": mass_values,
            "x_col": coordinate_col,
            "x_title": "threshold scale s",
            "response_name": "ε(s)",
            "derivative_name": "dε/ds",
            "derivative_col": "dresponse_ds",
            "derivative_scheme_col": "derivative_scheme",
            "hover_x": "s",
            "hover_derivative": "d epsilon / ds",
        },
        {
            "view_axis": "mass",
            "fixed_col": coordinate_col,
            "fixed_values": threshold_values,
            "x_col": mass_col,
            "x_title": "mH₂ [GeV]",
            "response_name": "ε(mH₂)",
            "derivative_name": "dε/dmH₂",
            "derivative_col": "dresponse_dmH2",
            "derivative_scheme_col": "derivative_scheme_dmH2",
            "hover_x": "mH₂ [GeV]",
            "hover_derivative": "d epsilon / dmH₂",
        },
    )
    grouping = list(dict.fromkeys([mass_col, coordinate_col, *([] if stage_col is None else [stage_col])]))
    for spec in axis_specs:
        for fixed_index, fixed_value in enumerate(spec["fixed_values"]):
            for stage_index, stage_value in enumerate(stage_values):
                selection_mask = derivative_df[spec["fixed_col"]].eq(fixed_value)
                if stage_col is not None:
                    selection_mask &= derivative_df[stage_col].eq(stage_value)
                for response_column in display_columns:
                    subset = derivative_df[
                        selection_mask & derivative_df["response_column"].eq(response_column)
                    ].sort_values(spec["x_col"])
                    if subset.empty:
                        continue
                    metadata = {
                        name: value
                        for name, value in zip(
                            grouping,
                            [
                                fixed_value if name == spec["fixed_col"] else stage_value
                                if name == stage_col
                                else subset.iloc[0][name]
                                for name in grouping
                            ],
                            strict=True,
                        )
                    }
                    metadata_text = ", ".join(f"{name}={value}" for name, value in metadata.items())
                    customdata = [
                        [
                            row[spec["x_col"]],
                            row["response"],
                            row[spec["derivative_col"]],
                            row[spec["derivative_scheme_col"]],
                            metadata_text,
                        ]
                        for row in subset.to_dict("records")
                    ]
                    legendgroup = f"{spec['view_axis']}-{fixed_index}-{stage_index}-{response_column}"
                    top_index = len(figure.data)
                    figure.add_trace(
                        go.Scatter(
                            x=subset[spec["x_col"]],
                            y=subset["response"],
                            mode="lines+markers",
                            name=spec["response_name"],
                            legendgroup=legendgroup,
                            visible=False,
                            line=dict(color="#2563eb", width=2.5, dash="solid"),
                            marker=dict(color="#2563eb", size=7, symbol="circle"),
                            yaxis="y",
                            customdata=customdata,
                            hovertemplate=(
                                f"{spec['hover_x']}=%{{customdata[0]}}<br>epsilon=%{{customdata[1]}}<br>"
                                f"{spec['hover_derivative']}=%{{customdata[2]}}<br>"
                                "scheme=%{customdata[3]}<br>%{customdata[4]}<extra></extra>"
                            ),
                        )
                    )
                    bottom_index = len(figure.data)
                    figure.add_trace(
                        go.Scatter(
                            x=subset[spec["x_col"]],
                            y=subset[spec["derivative_col"]],
                            mode="lines+markers",
                            name=spec["derivative_name"],
                            legendgroup=legendgroup,
                            visible=False,
                            line=dict(color="#f97316", width=2.5, dash="dash"),
                            marker=dict(color="#f97316", size=7, symbol="diamond"),
                            yaxis="y2",
                            customdata=customdata,
                            hovertemplate=(
                                f"{spec['hover_x']}=%{{customdata[0]}}<br>epsilon=%{{customdata[1]}}<br>"
                                f"{spec['hover_derivative']}=%{{customdata[2]}}<br>"
                                "scheme=%{customdata[3]}<br>%{customdata[4]}<extra></extra>"
                            ),
                        )
                    )
                    selections.append(
                        {
                            "view_axis": spec["view_axis"],
                            "fixed_index": fixed_index,
                            "stage_index": stage_index,
                            "response_column": response_column,
                            "response_trace": top_index,
                            "derivative_trace": bottom_index,
                        }
                    )

    if not selections:
        raise ValueError("no plottable response groups were found")
    first_selection = next(
        selection
        for selection in selections
        if selection["view_axis"] == "threshold"
        and selection["fixed_index"] == 0
        and selection["stage_index"] == 0
        and selection["response_column"] == display_columns[0]
    )
    figure.data[first_selection["response_trace"]].visible = True
    figure.data[first_selection["derivative_trace"]].visible = True
    figure.update_layout(
        template="plotly_white",
        height=590,
        xaxis=dict(title="threshold scale s", anchor="y", showgrid=True, gridcolor="#e5e7eb"),
        yaxis=dict(title="ε(s)", anchor="x", rangemode="tozero"),
        yaxis2=dict(
            title="dε/ds",
            overlaying="y",
            side="right",
            showgrid=False,
            zeroline=True,
            zerolinecolor="#d1d5db",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#d1d5db",
            borderwidth=1,
        ),
        hoverlabel=dict(namelength=-1),
        margin=dict(l=80, r=85, t=65, b=65),
    )

    mass_labels = [str(value) for value in mass_values]
    threshold_labels = [str(value) for value in threshold_values]
    stage_options = "".join(
        f'<option value="{index}">{html.escape(str(value) if value is not None else "All data")}</option>'
        for index, value in enumerate(stage_values)
    )
    state = {
        "mass_values": [_json_safe(value) for value in mass_values],
        "mass_labels": mass_labels,
        "threshold_values": [_json_safe(value) for value in threshold_values],
        "threshold_labels": threshold_labels,
        "stages": [_json_safe(value) for value in stage_values],
        "selections": selections,
        "initial_response": display_columns[0],
    }
    state_json = json.dumps(state, ensure_ascii=False).replace("<", "\\u003c")
    plot_html = pio.to_html(
        figure,
        include_plotlyjs="inline",
        full_html=False,
        config={"responsive": True, "displaylogo": False},
        div_id="response-plot",
    )
    initial_stage = str(stage_values[0]) if stage_values[0] is not None else "All data"
    initial_mass = html.escape(mass_labels[0])
    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>H₂ Trackless response to jet-threshold scale</title>
  <style>
    :root {{ color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, -apple-system, sans-serif; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: #f8fafc; color: #172033; }}
    main {{ width: min(1540px, calc(100vw - 48px)); margin: 0 auto; padding: 34px 0 30px; }}
    header {{ margin-bottom: 22px; }}
    h1 {{ margin: 0; font-size: clamp(1.55rem, 2.2vw, 2.25rem); line-height: 1.15; letter-spacing: -0.02em; }}
    #subtitle {{ margin: 8px 0 0; color: #526174; font-size: 1rem; }}
    .controls {{ display: grid; gap: 18px; margin-bottom: 22px; padding: 18px 20px 20px; background: white; border: 1px solid #dbe3ee; border-radius: 12px; box-shadow: 0 5px 18px rgba(15, 23, 42, 0.06); }}
    .control {{ min-width: 0; }}
    .control-label {{ display: flex; align-items: baseline; justify-content: space-between; gap: 14px; margin-bottom: 9px; font-weight: 700; font-size: 0.95rem; }}
    .selected-value {{ color: #1d4ed8; font-variant-numeric: tabular-nums; white-space: nowrap; }}
    input[type="range"] {{ display: block; width: 100%; accent-color: #2563eb; cursor: pointer; }}
    datalist {{ display: flex; justify-content: space-between; width: calc(100% - 14px); margin: 2px 7px 0; color: #64748b; font-size: 0.78rem; }}
    .stage-row {{ display: flex; align-items: end; gap: 24px; flex-wrap: wrap; }}
    .stage-control {{ flex: 1 1 360px; }}
    select {{ width: 100%; max-width: 650px; padding: 9px 34px 9px 11px; border: 1px solid #b8c5d6; border-radius: 7px; background: white; color: #172033; font: inherit; }}
    .checkbox-control {{ display: flex; align-items: center; min-height: 40px; padding-bottom: 1px; }}
    .checkbox-control label {{ display: flex; align-items: center; gap: 9px; font-weight: 700; cursor: pointer; }}
    input[type="checkbox"] {{ width: 18px; height: 18px; accent-color: #2563eb; cursor: pointer; }}
    .plot-card {{ padding: 4px 6px 0; background: white; border: 1px solid #dbe3ee; border-radius: 12px; box-shadow: 0 5px 18px rgba(15, 23, 42, 0.06); overflow: hidden; }}
    @media (max-width: 700px) {{ main {{ width: min(100% - 24px, 1540px); padding-top: 22px; }} .stage-row {{ gap: 12px; }} .plot-card {{ padding: 0; }} }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>H₂ Trackless response to jet-threshold scale</h1>
      <p id="subtitle" aria-live="polite">mH₂ = {initial_mass} GeV · {html.escape(initial_stage)} · local efficiency</p>
    </header>
    <section class="controls" aria-label="Plot controls">
      <div class="control view-control">
        <div class="control-label"><label for="view-axis">View</label></div>
        <select id="view-axis" aria-label="Response view">
          <option value="threshold">Threshold scale</option>
          <option value="mass">H₂ mass</option>
        </select>
      </div>
      <div class="control">
        <div class="control-label"><label id="fixed-label" for="fixed-slider">m_H2 [GeV]</label><span id="fixed-value" class="selected-value">{initial_mass} GeV</span></div>
        <input id="fixed-slider" type="range" min="0" max="{len(mass_values) - 1}" step="1" value="0" list="fixed-ticks" aria-label="m_H2 [GeV]">
        <datalist id="fixed-ticks"></datalist>
      </div>
      <div class="stage-row">
        <div class="control stage-control">
          <div class="control-label"><label for="stage-select">Cutflow stage</label></div>
          <select id="stage-select" aria-label="Cutflow stage">{stage_options}</select>
        </div>
        <div class="control checkbox-control">
          <label for="cumulative-toggle"><input id="cumulative-toggle" type="checkbox"> Cumulative</label>
        </div>
      </div>
    </section>
    <section class="plot-card" aria-label="Interactive response plot">
      {plot_html}
    </section>
  </main>
  <script>
    const responseState = {state_json};
    const uiState = {{
      view_axis: "threshold",
      selected_fixed_value: 0,
      selected_stage: 0,
      use_cumulative: false,
    }};
    const plot = document.getElementById("response-plot");
    const viewAxis = document.getElementById("view-axis");
    const fixedSlider = document.getElementById("fixed-slider");
    const fixedLabel = document.getElementById("fixed-label");
    const fixedValue = document.getElementById("fixed-value");
    const fixedTicks = document.getElementById("fixed-ticks");
    const stageSelect = document.getElementById("stage-select");
    const cumulativeToggle = document.getElementById("cumulative-toggle");
    const subtitle = document.getElementById("subtitle");

    function axisConfig() {{
      if (uiState.view_axis === "mass") {{
        return {{
          values: responseState.threshold_values,
          labels: responseState.threshold_labels,
          fixedLabel: "threshold scale s",
          fixedSuffix: "",
          xTitle: "mH₂ [GeV]",
          responseTitle: "ε(mH₂)",
          derivativeTitle: "dε/dmH₂",
          fixedSubtitle: "s",
        }};
      }}
      return {{
        values: responseState.mass_values,
        labels: responseState.mass_labels,
        fixedLabel: "m_H2 [GeV]",
        fixedSuffix: " GeV",
        xTitle: "threshold scale s",
        responseTitle: "ε(s)",
        derivativeTitle: "dε/ds",
        fixedSubtitle: "mH₂",
      }};
    }}

    function configureFixedSlider() {{
      const config = axisConfig();
      uiState.selected_fixed_value = Math.min(uiState.selected_fixed_value, config.values.length - 1);
      fixedSlider.max = String(config.values.length - 1);
      fixedSlider.value = String(uiState.selected_fixed_value);
      fixedSlider.setAttribute("aria-label", config.fixedLabel);
      fixedLabel.textContent = config.fixedLabel;
      fixedTicks.replaceChildren(...config.labels.map((label, index) => {{
        const option = document.createElement("option");
        option.value = String(index);
        option.label = label;
        return option;
      }}));
    }}

    function updateResponsePlot() {{
      const config = axisConfig();
      uiState.selected_fixed_value = Number(fixedSlider.value);
      uiState.selected_stage = Number(stageSelect.value);
      uiState.use_cumulative = cumulativeToggle.checked;
      const responseColumn = uiState.use_cumulative ? "cumulative_eff" : "local_eff";
      const visible = Array(plot.data.length).fill(false);
      for (const selection of responseState.selections) {{
        if (selection.view_axis === uiState.view_axis && selection.fixed_index === uiState.selected_fixed_value && selection.stage_index === uiState.selected_stage && selection.response_column === responseColumn) {{
          visible[selection.response_trace] = true;
          visible[selection.derivative_trace] = true;
        }}
      }}
      Plotly.restyle(plot, {{visible: visible}});
      Plotly.relayout(plot, {{
        "xaxis.title.text": config.xTitle,
        "yaxis.title.text": config.responseTitle,
        "yaxis2.title.text": config.derivativeTitle,
      }});
      const fixed = config.labels[uiState.selected_fixed_value];
      const stage = responseState.stages[uiState.selected_stage] ?? "All data";
      const mode = uiState.use_cumulative ? "cumulative" : "local";
      fixedValue.textContent = `${{fixed}}${{config.fixedSuffix}}`;
      subtitle.textContent = `${{config.fixedSubtitle}} = ${{fixed}}${{uiState.view_axis === "mass" ? "" : " GeV"}} · ${{stage}} · ${{mode}} efficiency`;
    }}

    viewAxis.addEventListener("change", () => {{
      uiState.view_axis = viewAxis.value;
      uiState.selected_fixed_value = 0;
      configureFixedSlider();
      updateResponsePlot();
    }});
    fixedSlider.addEventListener("input", updateResponsePlot);
    stageSelect.addEventListener("change", updateResponsePlot);
    cumulativeToggle.addEventListener("change", updateResponsePlot);
    configureFixedSlider();
    updateResponsePlot();
  </script>
</body>
</html>
"""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="long-form CSV or Parquet table")
    parser.add_argument("--group-by", nargs="+", required=True, help="grouping columns")
    parser.add_argument("--s-col", default="s", help="coordinate column (default: s)")
    parser.add_argument("--stage-col", default="stage", help="stage column; use 'none' to disable")
    parser.add_argument(
        "--value-cols",
        nargs="+",
        default=None,
        help="response columns (default: available local/cumulative/acc columns)",
    )
    parser.add_argument("--output", type=Path, required=True, help="interactive HTML output")
    parser.add_argument(
        "--derivative-output",
        type=Path,
        default=None,
        help="derivative CSV/Parquet output (default: HTML path with .csv)",
    )
    parser.add_argument("--parquet-output", type=Path, default=None, help="optional Parquet copy")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = _read_table(args.input)
    stage_col = None if args.stage_col.lower() == "none" else args.stage_col
    value_cols = args.value_cols or [
        column for column in DEFAULT_VALUE_COLS if column in df.columns
    ]
    missing = [
        column for column in [*args.group_by, args.s_col, *value_cols] if column not in df.columns
    ]
    if missing:
        raise SystemExit(f"missing input column(s): {', '.join(dict.fromkeys(missing))}")
    if stage_col is not None and stage_col not in df.columns:
        raise SystemExit(f"missing input column: {stage_col}")
    group_cols = [*args.group_by]
    if stage_col is not None and stage_col not in group_cols:
        group_cols.append(stage_col)

    derivative_output = args.derivative_output or args.output.with_suffix(".csv")
    mass_col = "mH2"
    if mass_col not in df.columns:
        raise SystemExit("mass-axis view requires an input column: mH2")
    if mass_col == args.s_col:
        raise SystemExit("mH2 and the threshold coordinate must be different columns")

    threshold_derivative_df = _differentiate_available_responses(
        df,
        value_cols,
        group_cols,
        args.s_col,
        stage_col,
        derivative_col="dresponse_ds",
        derivative_scheme_col="derivative_scheme",
    )
    mass_group_cols = [args.s_col]
    if stage_col is not None:
        mass_group_cols.append(stage_col)
    mass_derivative_df = _differentiate_available_responses(
        df,
        value_cols,
        mass_group_cols,
        mass_col,
        stage_col,
        derivative_col="dresponse_dmH2",
        derivative_scheme_col="derivative_scheme_dmH2",
    )
    merge_keys = [mass_col, args.s_col, "response_column"]
    if stage_col is not None:
        merge_keys.append(stage_col)
    mass_derivative_columns = [*merge_keys, "dresponse_dmH2", "derivative_scheme_dmH2"]
    derivative_df = threshold_derivative_df.merge(
        mass_derivative_df[mass_derivative_columns],
        on=merge_keys,
        how="left",
        validate="one_to_one",
    )
    if derivative_df[["dresponse_dmH2", "derivative_scheme_dmH2"]].isna().any().any():
        raise ValueError("mass derivative data did not match every threshold response row")
    _write_table(derivative_df, derivative_output, args.parquet_output)
    _plot(
        derivative_df,
        args.output,
        args.group_by,
        stage_col,
        _ordered_stage_values(df, stage_col),
        args.s_col,
        mass_col,
    )
    print(f"wrote {args.output}")
    print(f"wrote {derivative_output}")
    if args.parquet_output is not None:
        print(f"wrote {args.parquet_output}")


if __name__ == "__main__":
    main()
