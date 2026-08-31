"""Reusable response-table extraction and response/derivative plotting.

The event-level extractor is deliberately configured by ``ResponseSpec``.
Physics selections, thresholds, column names, and grouping metadata therefore
remain inputs to the utility rather than hidden campaign constants.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

__all__ = [
    "ResponseSpec",
    "default_h2_trackless_spec",
    "extract_response_tables",
    "write_response_tables",
    "make_response_derivative_figure",
]


@dataclass(frozen=True)
class ResponseSpec:
    """Column-level configuration for a threshold response extraction."""

    branch_columns: Mapping[str, str]
    nominal_thresholds: Mapping[str, float]
    additional_column: str
    stages: Sequence[tuple[str, str | None]]
    threshold_stage: str = "Jet Selection"
    weight_columns: Sequence[str] = ()
    valid_column: str | None = "valid_weight"

    @property
    def stage_names(self) -> tuple[str, ...]:
        return tuple(name for name, _ in self.stages)

    def validate(self) -> None:
        branches = tuple(self.branch_columns)
        if not branches:
            raise ValueError("at least one threshold branch is required")
        if set(branches) != set(self.nominal_thresholds):
            raise ValueError("branch columns and thresholds must have the same keys")
        if len(set(self.stage_names)) != len(self.stage_names):
            raise ValueError("stage names must be unique")
        if not self.stages or self.stages[0][1] is not None:
            raise ValueError("the first stage must be the all-events stage")
        if self.threshold_stage not in self.stage_names:
            raise ValueError("threshold stage must be present in stages")


def default_h2_trackless_spec() -> ResponseSpec:
    """Return the validated H2 Trackless diagnostic column configuration."""
    return ResponseSpec(
        branch_columns={
            "j1": "jet4_pt",
            "j2": "jet5_pt",
            "j3": "jet6_pt",
            "j4": "jet7_pt",
        },
        nominal_thresholds={"j1": 137.0, "j2": 101.0, "j3": 83.0, "j4": 55.0},
        additional_column="trackless_additional",
        stages=(
            ("All events", None),
            ("Jet Selection", None),
            ("Fiducial", "pass_fiducial"),
            ("R_vertex > 4 mm", "pass_rvtx4"),
            ("|d0| > 2 mm", "pass_d0"),
            ("selected decay products >= 5", "pass_ndecay5"),
            ("invariant mass > 10 GeV", "pass_mdv10"),
            ("final acceptance", "pass_vertex_acc"),
        ),
        weight_columns=("event_eff_trackless", "v_eff"),
    )


def _require_event_columns(events: pd.DataFrame, spec: ResponseSpec) -> None:
    required = set(spec.branch_columns.values()) | {spec.additional_column}
    required.update(column for _, column in spec.stages if column is not None)
    required.update(spec.weight_columns)
    if spec.valid_column is not None:
        required.add(spec.valid_column)
    missing = sorted(required - set(events.columns))
    if missing:
        raise ValueError(f"missing event column(s): {', '.join(missing)}")


def _metadata_columns(metadata: Mapping[str, object]) -> list[str]:
    return list(metadata.keys())


def _with_metadata(rows: Iterable[dict], metadata: Mapping[str, object]) -> list[dict]:
    return [{**metadata, **row} for row in rows]


def _jet_mask(events: pd.DataFrame, scale: float, spec: ResponseSpec) -> pd.Series:
    ordinary = pd.Series(False, index=events.index)
    for branch, column in spec.branch_columns.items():
        ordinary = ordinary | (events[column] > scale * spec.nominal_thresholds[branch])
    return ordinary & (events[spec.additional_column] == 1)


def _branch_masks(events: pd.DataFrame, scale: float, spec: ResponseSpec) -> pd.DataFrame:
    return pd.DataFrame(
        {
            branch: events[column] > scale * spec.nominal_thresholds[branch]
            for branch, column in spec.branch_columns.items()
        },
        index=events.index,
    )


def _cutflow_rows(
    metadata: Mapping[str, object], scale: float, events: pd.DataFrame, spec: ResponseSpec
) -> list[dict]:
    n_total = len(events)
    rows: list[dict] = []
    current = pd.Series(True, index=events.index)
    n_before = n_total
    for stage_order, (stage, stage_column) in enumerate(spec.stages):
        if stage_order == 0:
            mask = pd.Series(True, index=events.index)
        elif stage == spec.threshold_stage:
            mask = _jet_mask(events, scale, spec)
        else:
            if stage_column is None:
                raise ValueError(f"non-initial stage {stage!r} needs a boolean column")
            mask = current & (events[stage_column] == 1)

        n_after = int(mask.sum())
        final = stage_order == len(spec.stages) - 1
        if final and spec.weight_columns:
            weighted = events.loc[mask, list(spec.weight_columns)].prod(axis=1).sum()
            weighted_numerator = float(weighted)
            acc_x_eff = weighted_numerator / n_total if n_total else float("nan")
        else:
            weighted_numerator = float(n_after)
            acc_x_eff = None
        rows.append(
            {
                **metadata,
                "s": scale,
                "stage": stage,
                "stage_order": stage_order,
                "n_before": n_before,
                "n_after": n_after,
                "local_eff": n_after / n_before if n_before else float("nan"),
                "cumulative_eff": n_after / n_total if n_total else float("nan"),
                "weighted_numerator": weighted_numerator,
                "acc": n_after / n_total if n_total else float("nan"),
                "acc_x_eff": acc_x_eff,
            }
        )
        current = mask
        n_before = n_after
    return rows


def _branch_rows(
    metadata: Mapping[str, object], scale: float, events: pd.DataFrame, spec: ResponseSpec
) -> list[dict]:
    n_total = len(events)
    masks = _branch_masks(events, scale, spec)
    additional = events[spec.additional_column] == 1
    union = masks.any(axis=1) & additional
    n_union = int(union.sum())
    rows: list[dict] = []
    for branch in spec.branch_columns:
        without = masks.drop(columns=branch).any(axis=1) & additional
        n_without = int(without.sum())
        n_pass = int((masks[branch] & additional).sum())
        loss = n_union - n_without
        rows.append(
            {
                **metadata,
                "s": scale,
                "branch": branch,
                "threshold_GeV": scale * spec.nominal_thresholds[branch],
                "n_pass_branch": n_pass,
                "pass_rate_of_all": n_pass / n_total if n_total else float("nan"),
                "n_union": n_union,
                "n_without_branch": n_without,
                "exclusive_loss": loss,
                "exclusive_loss_pct_of_union": loss / n_union * 100.0 if n_union else float("nan"),
            }
        )
    return rows


def extract_response_tables(
    grouped_events: Iterable[tuple[Mapping[str, object], pd.DataFrame]],
    scales: Sequence[float],
    spec: ResponseSpec | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Evaluate a threshold response for arbitrary group metadata.

    ``grouped_events`` contains one event table per group and a metadata
    mapping such as ``{"mH2": 130, "ctau": 4.326}``. No mass list is
    embedded in this function.
    """
    spec = default_h2_trackless_spec() if spec is None else spec
    spec.validate()
    scales = [float(scale) for scale in scales]
    if not scales or not all(pd.notna(scale) for scale in scales):
        raise ValueError("scales must contain at least one finite value")

    cutflow: list[dict] = []
    branches: list[dict] = []
    metadata_keys: set[str] = set()
    groups = list(grouped_events)
    if not groups:
        raise ValueError("at least one event group is required")
    for metadata, original_events in groups:
        events = original_events.copy()
        _require_event_columns(events, spec)
        if spec.valid_column is not None:
            events = events[events[spec.valid_column] == 1].copy()
        metadata_keys.update(_metadata_columns(metadata))
        for scale in scales:
            cutflow.extend(_cutflow_rows(metadata, scale, events, spec))
            branches.extend(_branch_rows(metadata, scale, events, spec))

    cutflow_df = pd.DataFrame(cutflow)
    branch_df = pd.DataFrame(branches)
    group_columns = sorted(metadata_keys)
    if group_columns:
        # Preserve the caller's scale order (the validated study uses 1.0 to
        # 0.1), while sorting group metadata for deterministic output.
        cutflow_df = cutflow_df.sort_values(group_columns, kind="stable")
        branch_df = branch_df.sort_values(group_columns, kind="stable")
    return cutflow_df.reset_index(drop=True), branch_df.reset_index(drop=True)


def write_response_tables(
    cutflow: pd.DataFrame, branches: pd.DataFrame, output_dir: str | Path
) -> None:
    """Write the standard CSV/Parquet response products."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    cutflow.to_csv(output / "response_table.csv", index=False)
    branches.to_csv(output / "branch_table.csv", index=False)
    cutflow.to_parquet(output / "response_table.parquet", index=False)
    branches.to_parquet(output / "branch_table.parquet", index=False)


def make_response_derivative_figure(
    response: pd.DataFrame,
    derivative: pd.DataFrame,
    response_column: str,
    group_columns: Sequence[str] = (),
    s_column: str = "s",
):
    """Build a self-contained Plotly response-over-derivative figure."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    group_columns = list(group_columns)
    for frame, name in ((response, "response"), (derivative, "derivative")):
        required = {s_column, *group_columns}
        required.add(response_column if name == "response" else "dresponse_ds")
        missing = sorted(required - set(frame.columns))
        if missing:
            raise ValueError(f"missing {name} plot column(s): {', '.join(missing)}")

    figure = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=(response_column, f"d{response_column}/d{s_column}"),
    )
    if group_columns:
        grouped = response.groupby(group_columns, sort=True, dropna=False, observed=False)
    else:
        grouped = [((), response)]
    for key, response_group in grouped:
        key_tuple = key if isinstance(key, tuple) else (key,)
        label = ", ".join(
            f"{column}={value}" for column, value in zip(group_columns, key_tuple, strict=True)
        )
        response_group = response_group.sort_values(s_column)
        if group_columns:
            selector = pd.Series(True, index=derivative.index)
            for column, value in zip(group_columns, key_tuple, strict=True):
                selector &= derivative[column].eq(value)
            derivative_group = derivative[selector].sort_values(s_column)
        else:
            derivative_group = derivative.sort_values(s_column)
        figure.add_trace(
            go.Scatter(
                x=response_group[s_column],
                y=response_group[response_column],
                mode="lines+markers",
                name=label or response_column,
                legendgroup=label or response_column,
            ),
            row=1,
            col=1,
        )
        figure.add_trace(
            go.Scatter(
                x=derivative_group[s_column],
                y=derivative_group["dresponse_ds"],
                mode="lines+markers",
                name=f"d/ds {label or response_column}",
                legendgroup=label or response_column,
                showlegend=False,
            ),
            row=2,
            col=1,
        )
    figure.update_xaxes(title_text=s_column, row=2, col=1)
    figure.update_yaxes(title_text=response_column, row=1, col=1)
    figure.update_yaxes(title_text=f"d{response_column}/d{s_column}", row=2, col=1)
    figure.update_layout(template="plotly_white", height=800, title="Response and derivative")
    return figure
