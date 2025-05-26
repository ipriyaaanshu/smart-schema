"""
Utilities for working with pandas DataFrames and Pydantic models.
"""

from pathlib import Path
from typing import Any, Type, Union

import pandas as pd
from pydantic import BaseModel


def align_dataframe_with_model(df: pd.DataFrame, model: Type[BaseModel]) -> pd.DataFrame:
    """
    Align a pandas DataFrame with a Pydantic model's schema.

    This function ensures that:
    1. All model fields are present in the DataFrame
    2. Data types match the model's schema
    3. Optional fields are handled appropriately
    4. Extra columns are removed

    Args:
        df: Input pandas DataFrame
        model: Pydantic model class to align with

    Returns:
        DataFrame with aligned types and columns

    Raises:
        ValueError: If a required field is missing from the DataFrame
    """
    # Create a copy to avoid modifying the original
    aligned_df = df.copy()

    # Get model fields and their types
    model_fields = model.model_fields

    # Process each column
    for field_name, field in model_fields.items():
        if field_name not in aligned_df.columns:
            # If field is required, raise error
            if field.default is ...:
                raise ValueError(f"Required field '{field_name}' not found in DataFrame")
            # If field is optional, add it with None values
            aligned_df[field_name] = None
            continue

        # Get the field type
        field_type = field.annotation

        # Handle Optional types
        if hasattr(field_type, "__origin__") and field_type.__origin__ is Union:
            # Get the non-None types
            types = [t for t in field_type.__args__ if t is not type(None)]
            if len(types) == 1:
                field_type = types[0]
            else:
                # For Union types, we'll try to convert to the first non-None type
                field_type = types[0]

        # Convert column based on type
        if field_type == int:
            # For integer fields, convert to Int64 to handle NaN
            aligned_df[field_name] = pd.to_numeric(aligned_df[field_name], errors="coerce").astype(
                "Int64"
            )
        elif field_type == float:
            # For float fields, convert to float64
            aligned_df[field_name] = pd.to_numeric(aligned_df[field_name], errors="coerce").astype(
                "float64"
            )
        elif field_type == bool:
            # For boolean fields, convert to boolean
            aligned_df[field_name] = aligned_df[field_name].astype(bool)
        elif field_type == str:
            # For string fields, convert to string and handle NaN
            aligned_df[field_name] = aligned_df[field_name].astype(str).replace("nan", None)
        else:
            # For other types, keep as is
            pass

    # Drop any columns not in the model
    extra_columns = set(aligned_df.columns) - set(model_fields.keys())
    if extra_columns:
        aligned_df = aligned_df.drop(columns=list(extra_columns))

    return aligned_df


def load_dataframe_with_model(
    file_path: Union[str, Path], model: Type[BaseModel], **kwargs
) -> pd.DataFrame:
    """
    Load a DataFrame from a file and align it with a Pydantic model.

    This function:
    1. Loads data from CSV or Excel files
    2. Automatically aligns the data with the model
    3. Supports additional pandas read options

    Args:
        file_path: Path to the data file (CSV, Excel, etc.)
        model: Pydantic model class to align with
        **kwargs: Additional arguments to pass to pd.read_csv or pd.read_excel

    Returns:
        DataFrame with aligned types and columns

    Raises:
        ValueError: If the file type is not supported
    """
    # Determine file type and load accordingly
    file_path = Path(file_path)
    if file_path.suffix.lower() == ".csv":
        df = pd.read_csv(file_path, **kwargs)
    elif file_path.suffix.lower() in [".xlsx", ".xls"]:
        df = pd.read_excel(file_path, **kwargs)
    else:
        raise ValueError(f"Unsupported file type: {file_path.suffix}")

    # Align the DataFrame with the model
    return align_dataframe_with_model(df, model)


def validate_dataframe_with_model(
    df: pd.DataFrame, model: Type[BaseModel]
) -> tuple[list[dict], list[dict]]:
    """
    Validate a DataFrame against a Pydantic model.

    This function:
    1. Aligns the DataFrame with the model
    2. Validates each row
    3. Returns valid and invalid records

    Args:
        df: Input pandas DataFrame
        model: Pydantic model class to validate against

    Returns:
        Tuple of (valid_records, invalid_records) where each record is a dictionary
    """
    # Align the DataFrame with the model
    aligned_df = align_dataframe_with_model(df, model)

    valid_records = []
    invalid_records = []

    # Validate each row
    for idx, row in aligned_df.iterrows():
        try:
            # Convert row to dict and validate
            record = row.to_dict()
            model(**record)
            valid_records.append(record)
        except Exception as e:
            # Add error information to the record
            record = row.to_dict()
            record["_error"] = str(e)
            invalid_records.append(record)

    return valid_records, invalid_records
