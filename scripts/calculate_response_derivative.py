#!/usr/bin/env python3
"""Calculate d(response)/ds for a long-form response table."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dvrecast.s_response import differentiate_response_table  # noqa: E402


def _read(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--value-column", required=True)
    parser.add_argument("--group-by", default="", help="comma-separated grouping columns")
    parser.add_argument("--s-column", default="s")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    group_columns = [value for value in args.group_by.split(",") if value]
    result = differentiate_response_table(
        _read(args.input), args.value_column, group_columns, s_col=args.s_column
    )
    if args.output.suffix == ".parquet":
        result.to_parquet(args.output, index=False)
    else:
        result.to_csv(args.output, index=False)
    print(f"wrote {args.output} ({len(result)} rows)")


if __name__ == "__main__":
    main()
