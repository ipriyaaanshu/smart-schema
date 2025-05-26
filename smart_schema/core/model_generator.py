"""
Model generator for smart_schema.
"""

from typing import Any, Dict, List, Optional, Type, Union

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, create_model

from ..utils.data_transformer import json_to_dataframe, normalize_datetime


def _convert_numpy_type(value: Any) -> Type:
    """
    Convert numpy types to Python types.

    Args:
        value: The value to convert

    Returns:
        The corresponding Python type
    """
    if isinstance(value, np.integer):
        return int
    elif isinstance(value, np.floating):
        return float
    elif isinstance(value, np.bool_):
        return bool
    elif isinstance(value, np.ndarray):
        if value.dtype.kind in "iuf":  # integer, unsigned integer, float
            return List[_convert_numpy_type(value[0])]
        return List[str]
    return type(value)


class ModelGenerator:
    """Generator for Pydantic models from various data sources."""

    def __init__(self, name: str):
        """
        Initialize the model generator.

        Args:
            name: The name of the model to generate
        """
        self.name = name

    def from_dataframe(
        self, df: pd.DataFrame, datetime_columns: Optional[List[str]] = None
    ) -> Type[BaseModel]:
        """
        Generate a Pydantic model from a pandas DataFrame.

        Args:
            df: The DataFrame to generate the model from
            datetime_columns: Optional list of column names containing datetime values

        Returns:
            A Pydantic model class
        """
        # Normalize datetime columns if specified
        if datetime_columns:
            df = normalize_datetime(df, datetime_columns)

        # Generate field definitions
        fields = {}
        for column in df.columns:
            # Get the first non-null value to determine type
            sample = df[column].dropna().iloc[0] if not df[column].empty else None

            if sample is None:
                # Default to string if no sample available
                fields[column] = (str, None)
            elif isinstance(sample, (np.integer, np.floating, np.bool_, np.ndarray)):
                # Convert numpy types to Python types
                python_type = _convert_numpy_type(sample)
                fields[column] = (python_type, None)
            elif isinstance(sample, (int, float)):
                fields[column] = (type(sample), None)
            elif isinstance(sample, bool):
                fields[column] = (bool, None)
            elif isinstance(sample, list):
                # For lists, use the type of the first element
                if sample and isinstance(sample[0], (int, float, np.integer, np.floating)):
                    element_type = _convert_numpy_type(sample[0])
                    fields[column] = (List[element_type], None)
                else:
                    fields[column] = (List[str], None)
            elif isinstance(sample, dict):
                fields[column] = (Dict[str, Any], None)
            else:
                fields[column] = (str, None)

        # Create model with configuration
        model_config = ConfigDict(arbitrary_types_allowed=True)
        return create_model(self.name, __config__=model_config, **fields)

    def from_json(
        self, data: Dict[str, Any], datetime_columns: Optional[List[str]] = None
    ) -> Type[BaseModel]:
        """
        Generate a Pydantic model from JSON data.

        Args:
            data: The JSON data to generate the model from
            datetime_columns: Optional list of column names containing datetime values

        Returns:
            A Pydantic model class
        """
        # Convert JSON to DataFrame
        df = json_to_dataframe(data)

        # Generate model from DataFrame
        return self.from_dataframe(df, datetime_columns)
