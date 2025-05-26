"""
CSV file splitting utilities.
"""

from pathlib import Path
from typing import Optional

import pandas as pd
from rich.console import Console

console = Console()


def split_by_rows(
    input_path: str,
    rows_per_file: int,
    output_prefix: Optional[str] = None,
) -> None:
    """
    Split a CSV file into multiple files, each with up to rows_per_file rows.
    """
    input_path = Path(input_path)
    df = pd.read_csv(input_path)
    total_rows = len(df)
    num_files = (total_rows + rows_per_file - 1) // rows_per_file

    if not output_prefix:
        output_prefix = input_path.with_suffix("").as_posix() + "_part"

    for i in range(num_files):
        start = i * rows_per_file
        end = min(start + rows_per_file, total_rows)
        part_df = df.iloc[start:end]
        out_path = f"{output_prefix}{i+1}.csv"
        part_df.to_csv(out_path, index=False)
        console.print(f"[green]Wrote rows {start+1}-{end} to {out_path}[/green]")


def split_by_column(
    input_path: str,
    column: str,
    output_prefix: Optional[str] = None,
) -> None:
    """
    Split a CSV file into multiple files, one for each unique value in the specified column.
    """
    input_path = Path(input_path)
    df = pd.read_csv(input_path)
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in CSV.")

    if not output_prefix:
        output_prefix = input_path.with_suffix("").as_posix() + f"_{column}_"

    for value, group in df.groupby(column):
        safe_value = str(value).replace("/", "-").replace(" ", "_")
        out_path = f"{output_prefix}{safe_value}.csv"
        group.to_csv(out_path, index=False)
        console.print(f"[green]Wrote {len(group)} rows for {column}={value} to {out_path}[/green]")
