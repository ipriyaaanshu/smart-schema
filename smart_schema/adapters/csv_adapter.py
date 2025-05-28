"""
CSV file handling functionality for Smart Schema.
"""

from pathlib import Path
from typing import List, Optional

import pandas as pd


class CSVAdapter:
    """Handles operations related to CSV files."""

    def __init__(self, chunk_size: int = 1000):
        """Initialize the CSV adapter.

        Args:
            chunk_size: Number of rows to process at once when reading large files.
        """
        self.chunk_size = chunk_size

    def read_csv(self, file_path: str) -> pd.DataFrame:
        """Read a CSV file into a pandas DataFrame.

        Args:
            file_path: Path to the CSV file.

        Returns:
            A pandas DataFrame containing the CSV data.
        """
        return pd.read_csv(file_path)

    def read_csv_in_chunks(self, file_path: str) -> pd.io.parsers.TextFileReader:
        """Read a CSV file in chunks.

        Args:
            file_path: Path to the CSV file.

        Returns:
            A pandas TextFileReader object for iterating over chunks.
        """
        return pd.read_csv(file_path, chunksize=self.chunk_size)

    def write_csv(self, df: pd.DataFrame, file_path: str, index: bool = False) -> None:
        """Write a DataFrame to a CSV file.

        Args:
            df: The DataFrame to write.
            file_path: Path where the CSV file should be written.
            index: Whether to write the DataFrame's index.
        """
        df.to_csv(file_path, index=index)

    def split_by_rows(
        self,
        input_file: str,
        rows_per_file: int,
        output_prefix: Optional[str] = None,
    ) -> List[str]:
        """Split a CSV file into multiple files based on row count.

        Args:
            input_file: Path to the input CSV file.
            rows_per_file: Number of rows per output file.
            output_prefix: Prefix for output files (optional).

        Returns:
            List of paths to the created files.
        """
        input_path = Path(input_file)
        prefix = output_prefix or input_path.stem

        output_files = []
        for i, chunk in enumerate(pd.read_csv(input_file, chunksize=rows_per_file)):
            output_file = f"{prefix}_{i + 1}.csv"
            chunk.to_csv(output_file, index=False)
            output_files.append(output_file)

        return output_files

    def split_by_column(
        self, input_file: str, column: str, output_prefix: Optional[str] = None
    ) -> List[str]:
        """Split a CSV file into multiple files based on unique values in a column.

        Args:
            input_file: Path to the input CSV file.
            column: Name of the column to split on.
            output_prefix: Prefix for output files (optional).

        Returns:
            List of paths to the created files.
        """
        input_path = Path(input_file)
        prefix = output_prefix or input_path.stem

        df = pd.read_csv(input_file)
        output_files = []

        for value in df[column].unique():
            output_file = f"{prefix}_{value}.csv"
            df[df[column] == value].to_csv(output_file, index=False)
            output_files.append(output_file)

        return output_files

    def split_dataframe(self, df: pd.DataFrame, chunk_size: int) -> List[pd.DataFrame]:
        """Split a DataFrame into multiple smaller DataFrames based on the specified chunk size.

        Args:
            df: The DataFrame to split.
            chunk_size: Number of rows per chunk.

        Returns:
            List of smaller DataFrames.
        """
        chunks = []
        for i in range(0, len(df), chunk_size):
            chunks.append(df.iloc[i: i + chunk_size])
        return chunks

    def _write_chunk_to_file(self, df_chunk: pd.DataFrame, output_path: Path) -> None:
        df_chunk.to_csv(output_path, index=False)
