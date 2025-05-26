"""
Data transformation utilities for smart_schema.
"""

from datetime import datetime
from typing import Any, Dict, List, Union

import pandas as pd


def flatten_json(data: Dict[str, Any], prefix: str = "", separator: str = "_") -> Dict[str, Any]:
    """
    Flatten a nested JSON/dictionary structure into a flat dictionary.

    Args:
        data: The nested dictionary to flatten
        prefix: The prefix to use for nested keys
        separator: The separator to use between nested keys

    Returns:
        A flat dictionary with concatenated keys
    """
    flattened = {}

    for key, value in data.items():
        new_key = f"{prefix}{separator}{key}" if prefix else key

        if isinstance(value, dict):
            flattened.update(flatten_json(value, new_key, separator))
        elif isinstance(value, list):
            # Handle lists by taking the first item if it's a dictionary
            if value and isinstance(value[0], dict):
                flattened.update(flatten_json(value[0], new_key, separator))
            else:
                flattened[new_key] = value
        else:
            flattened[new_key] = value

    return flattened


def json_to_dataframe(data: Dict[str, Any], separator: str = "_") -> pd.DataFrame:
    """
    Convert a nested JSON/dictionary structure to a pandas DataFrame.

    Args:
        data: The nested dictionary to convert
        separator: The separator to use between nested keys

    Returns:
        A pandas DataFrame with flattened structure
    """
    flattened = flatten_json(data, separator=separator)
    return pd.DataFrame([flattened])


def normalize_datetime(df: pd.DataFrame, datetime_columns: List[str]) -> pd.DataFrame:
    """
    Normalize datetime columns in a DataFrame to a consistent format.

    Args:
        df: The DataFrame to normalize
        datetime_columns: List of column names containing datetime values

    Returns:
        DataFrame with normalized datetime columns
    """
    df = df.copy()

    for col in datetime_columns:
        if col in df.columns:
            # Convert to datetime if not already
            df[col] = pd.to_datetime(df[col])
            # Convert to string format for model generation
            df[col] = df[col].dt.strftime("%Y-%m-%d %H:%M:%S")

    return df


def denormalize_datetime(df: pd.DataFrame, datetime_columns: List[str]) -> pd.DataFrame:
    """
    Convert string datetime columns back to datetime objects.

    Args:
        df: The DataFrame to denormalize
        datetime_columns: List of column names containing datetime strings

    Returns:
        DataFrame with datetime objects
    """
    df = df.copy()

    for col in datetime_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])

    return df
