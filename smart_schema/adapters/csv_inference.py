"""
CSV schema inference utilities.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Type, Union

import pandas as pd
from pydantic import BaseModel, create_model

from ..core.model_utils import generate_pydantic_model, generate_schema_from_dataframe


def infer_column_types(df: pd.DataFrame) -> Dict[str, Type]:
    """
    Infer Pydantic types from pandas DataFrame columns.
    """
    type_mapping = {
        "int64": int,
        "float64": float,
        "bool": bool,
        "datetime64[ns]": pd.Timestamp,
        "object": str,
    }

    column_types = {}
    for column in df.columns:
        # Get the pandas dtype
        dtype = str(df[column].dtype)

        # Map to Pydantic type
        if dtype in type_mapping:
            column_types[column] = type_mapping[dtype]
        else:
            # Default to string for unknown types
            column_types[column] = str

    return column_types


def generate_model(
    df: pd.DataFrame,
    model_name: str = "DataModel",
    description: Optional[str] = None,
) -> Type[BaseModel]:
    """
    Generate a Pydantic model from a pandas DataFrame.
    """
    column_types = infer_column_types(df)

    # Create model fields with descriptions from DataFrame
    fields = {}
    for column, type_ in column_types.items():
        fields[column] = (type_, ...)  # ... means required field

    # Create the model
    model = create_model(
        model_name,
        **fields,
        __doc__=description
        or f"Model generated from DataFrame with columns: {', '.join(df.columns)}",
    )

    return model


def save_model_to_file(
    model: Type[BaseModel],
    output_path: Union[str, Path],
    model_name: str = "DataModel",
) -> None:
    """
    Save a Pydantic model to a Python file.
    """
    output_path = Path(output_path)

    # Generate model code
    model_code = f'''"""
Generated Pydantic model for data validation.
"""

from pydantic import BaseModel

class {model_name}(BaseModel):
'''

    # Add field definitions
    for field_name, field in model.model_fields.items():
        field_type = field.annotation.__name__
        model_code += f"    {field_name}: {field_type}\n"

    # Write to file
    output_path.write_text(model_code)
