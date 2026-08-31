#!/usr/bin/env python3
"""Extract a configurable threshold-response table from event CSVs.

The default columns describe the validated H2 Trackless diagnostic. Paths,
group metadata, and scales are command-line inputs; no current mass list or
result-directory path is embedded in the reusable implementation.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dvrecast.response import (  # noqa: E402
    default_h2_trackless_spec,
    extract_response_tables,
    write_response_tables,
)


def _value(text: str) -> int | float | str:
    try:
        value = float(text)
    except ValueError:
        return text
    return int(value) if value.is_integer() else value


def _grouped_events(root: Path, file_glob: str, group_pattern: str):
    pattern = re.compile(group_pattern)
    grouped: dict[tuple[tuple[str, object], ...], list[Path]] = defaultdict(list)
    for path in sorted(root.glob(file_glob)):
        match = pattern.search(str(path.relative_to(root)))
        if match is None:
            raise ValueError(f"group pattern did not match {path}")
        metadata = tuple((key, _value(value)) for key, value in sorted(match.groupdict().items()))
        grouped[metadata].append(path)
    if not grouped:
        raise ValueError(f"no event CSVs matched {root / file_glob}")
    for metadata_items, paths in sorted(grouped.items(), key=lambda item: str(item[0])):
        frames = []
        for path in paths:
            frame = pd.read_csv(path)
            frame["source_file"] = str(path)
            frames.append(frame)
        yield dict(metadata_items), pd.concat(frames, ignore_index=True)


def _scales(text: str) -> list[float]:
    values = [float(value) for value in text.split(",") if value.strip()]
    if not values or not all(pd.notna(value) for value in values):
        raise argparse.ArgumentTypeError("--scales must contain finite comma-separated values")
    return values


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events-root", type=Path, required=True)
    parser.add_argument("--file-glob", default="mH*/seed_*/events.csv")
    parser.add_argument(
        "--group-pattern",
        default=r"mH(?P<mH2>[0-9]+)",
        help="regex over paths below events-root; named groups become metadata columns",
    )
    parser.add_argument(
        "--scales",
        type=_scales,
        default=_scales("1.0,0.9,0.8,0.7,0.6,0.5,0.4,0.3,0.2,0.1"),
    )
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    cutflow, branches = extract_response_tables(
        _grouped_events(args.events_root, args.file_glob, args.group_pattern),
        args.scales,
        default_h2_trackless_spec(),
    )
    write_response_tables(cutflow, branches, args.out_dir)
    metric_columns = {
        "s",
        "stage",
        "stage_order",
        "n_before",
        "n_after",
        "local_eff",
        "cumulative_eff",
        "weighted_numerator",
        "acc",
        "acc_x_eff",
    }
    group_columns = [column for column in cutflow.columns if column not in metric_columns]
    totals: dict[str, int] = {}
    total_rows = cutflow[cutflow["stage_order"] == 0]
    if group_columns:
        total_rows = total_rows.drop_duplicates(group_columns)
    else:
        total_rows = total_rows.head(1)
    for row in total_rows.to_dict("records"):
        key = (
            row[group_columns[0]]
            if len(group_columns) == 1
            else tuple(row[column] for column in group_columns)
        )
        totals[str(key)] = int(row["n_before"])
    (args.out_dir / "n_generated.json").write_text(json.dumps(totals, indent=2) + "\n")
    print(f"wrote {args.out_dir / 'response_table.csv'} ({len(cutflow)} rows)")
    print(f"wrote {args.out_dir / 'branch_table.csv'} ({len(branches)} rows)")


if __name__ == "__main__":
    main()
