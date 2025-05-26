"""
Schema inference functionality for Smart Schema.
"""

from typing import Any, Dict, Optional

import numpy as np
import pandas as pd


class SchemaInferrer:
    """Handles inference of data schemas from structured data."""

    def __init__(self):
        """Initialize the schema inferrer."""
        pass

    def infer_from_dataframe(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Infer schema information from a DataFrame.

        Args:
            df: The DataFrame to infer schema from.

        Returns:
            A dictionary containing schema information for each column.
        """
        schema = {}

        for column in df.columns:
            schema[column] = self._infer_column_schema(df[column])

        return schema

    def _infer_column_schema(self, series: pd.Series) -> Dict[str, Any]:
        """Infer schema information for a single column.

        Args:
            series: The pandas Series to infer schema from.

        Returns:
            A dictionary containing schema information.
        """
        dtype = series.dtype
        schema = {
            "type": str(dtype),
            "nullable": series.isna().any(),
            "unique": series.nunique() == len(series),
            "min": None,
            "max": None,
            "mean": None,
            "std": None,
        }

        # Add numeric statistics if applicable
        if pd.api.types.is_numeric_dtype(dtype):
            schema.update(
                {
                    "min": float(series.min()),
                    "max": float(series.max()),
                    "mean": float(series.mean()),
                    "std": float(series.std()),
                }
            )

        return schema
