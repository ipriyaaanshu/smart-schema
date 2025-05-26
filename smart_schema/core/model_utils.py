"""
Utilities for generating and working with Pydantic models.
"""

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union, get_args, get_origin, get_type_hints

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, create_model, validator

from ..utils.dataframe_utils import (
    align_dataframe_with_model,
    load_dataframe_with_model,
    validate_dataframe_with_model,
)


def _infer_type_from_value(value: Any) -> Type:
    """
    Infer Python type from a value.
    Handles basic types, lists, and dictionaries.
    """
    if value is None:
        return Any
    elif isinstance(value, bool):
        return bool
    elif isinstance(value, int):
        return int
    elif isinstance(value, float):
        return float
    elif isinstance(value, str):
        return str
    elif isinstance(value, list):
        if not value:
            return List[Any]
        # Get the most specific common type
        item_types = {_infer_type_from_value(item) for item in value}
        if len(item_types) == 1:
            return List[item_types.pop()]
        return List[Any]
    elif isinstance(value, dict):
        return Dict[str, Any]
    return Any


def _generate_schema_from_dict(
    data: Dict[str, Any], field_name: str = ""
) -> Dict[str, Dict[str, Any]]:
    """
    Generate a schema dictionary from a nested dictionary.
    """
    schema = {}
    for key, value in data.items():
        field_info = {
            "type": _infer_type_from_value(value),
            "is_nullable": value is None,
            "description": f"Field {key} from {field_name}" if field_name else f"Field {key}",
        }

        # Handle nested dictionaries
        if isinstance(value, dict):
            nested_schema = _generate_schema_from_dict(
                value, f"{field_name}.{key}" if field_name else key
            )
            field_info["nested_schema"] = nested_schema
            # Create a nested model type
            nested_model_name = f"{key.title()}Model"
            field_info["type"] = create_model(
                nested_model_name,
                **{
                    k: (v["type"], None if v["is_nullable"] else ...)
                    for k, v in nested_schema.items()
                },
            )

        # Handle lists of dictionaries
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            # Create a model for the list items
            item_schema = _generate_schema_from_dict(
                value[0], f"{field_name}.{key}[0]" if field_name else f"{key}[0]"
            )
            item_model_name = f"{key.title()}ItemModel"
            item_model = create_model(
                item_model_name,
                **{
                    k: (v["type"], None if v["is_nullable"] else ...)
                    for k, v in item_schema.items()
                },
            )
            field_info["type"] = List[item_model]

        schema[key] = field_info

    return schema


def generate_schema_from_json(
    json_data: Union[str, Dict[str, Any]],
    model_name: str = "JsonModel",
    description: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Generate a Pydantic schema from JSON data.

    Args:
        json_data: JSON string or dictionary
        model_name: Base name for the model
        description: Optional description for the model

    Returns:
        Dictionary containing the schema specification
    """
    if isinstance(json_data, str):
        data = json.loads(json_data)
    else:
        data = json_data

    if not isinstance(data, dict):
        raise ValueError("JSON data must be an object/dictionary")

    return _generate_schema_from_dict(data)


def generate_schema_from_dataframe(
    df: pd.DataFrame,
    model_name: str = "DataFrameModel",
    description: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Generate a Pydantic schema from a pandas DataFrame.

    Args:
        df: Input pandas DataFrame
        model_name: Base name for the model
        description: Optional description for the model

    Returns:
        Dictionary containing the schema specification
    """
    schema = {}

    for column in df.columns:
        # Get sample of non-null values
        sample = df[column].dropna().head(1)
        if len(sample) == 0:
            # If all values are null, use string type
            field_type = str
        else:
            value = sample.iloc[0]
            field_type = _infer_type_from_value(value)

        # Check if column contains any null values
        is_nullable = df[column].isna().any()

        # Get column statistics for description
        stats = {
            "total_rows": len(df),
            "null_count": df[column].isna().sum(),
        }

        # Only count unique values if the type is hashable
        try:
            stats["unique_count"] = df[column].nunique()
        except TypeError:
            # For unhashable types like lists, estimate unique count
            stats["unique_count"] = "N/A (unhashable type)"

        schema[column] = {
            "type": field_type,
            "is_nullable": is_nullable,
            "description": (
                f"Column {column} from DataFrame\n"
                f"Total rows: {stats['total_rows']}\n"
                f"Null values: {stats['null_count']}\n"
                f"Unique values: {stats['unique_count']}"
            ),
        }

    return schema


def generate_pydantic_model(
    fields: Dict[str, Dict[str, Any]],
    model_name: str = "DataModel",
    description: Optional[str] = None,
) -> Type[BaseModel]:
    """
    Generate a Pydantic model from a field specification.

    Args:
        fields: Dictionary mapping field names to their specifications
               Each specification should have:
               - type: Python type or string representation of type
               - is_nullable: bool indicating if field is optional
               - default: Optional default value
               - description: Optional field description
        model_name: Name for the generated model class
        description: Optional description for the model

    Returns:
        Generated Pydantic model class
    """
    model_fields = {}
    for field_name, info in fields.items():
        field_type = info["type"]
        if info["is_nullable"]:
            field_type = Optional[field_type]
            default = info.get("default", None)
        else:
            default = ...

        # Add field with description if provided
        if "description" in info:
            model_fields[field_name] = (
                field_type,
                Field(default=default, description=info["description"]),
            )
        else:
            model_fields[field_name] = (field_type, default)

    # Create the base model
    model = create_model(
        model_name,
        **model_fields,
        __doc__=description or f"Model with fields: {', '.join(fields.keys())}",
    )

    # Add nan validator
    @validator("*", pre=True)
    def handle_nan(cls, v: Any) -> Any:
        if isinstance(v, float) and math.isnan(v):
            return None
        return v

    # Add the validator to the model
    setattr(model, "handle_nan", classmethod(handle_nan))

    return model


def save_model_to_file(
    model: Type[BaseModel],
    output_path: str,
    model_name: str = "DataModel",
) -> None:
    """
    Save a Pydantic model to a Python file.

    Args:
        model: Pydantic model class to save
        output_path: Path where the model file should be saved
        model_name: Name to use for the model class in the file
    """
    output_path = Path(output_path)

    # Collect all nested models and their dependencies
    nested_models = {}
    model_dependencies = {}

    def collect_nested_models(model_type: Type[BaseModel], model_name: str) -> None:
        if model_name in nested_models:
            return

        nested_models[model_name] = model_type
        model_dependencies[model_name] = set()

        for field_name, field in model_type.model_fields.items():
            field_type = field.annotation
            if hasattr(field_type, "__origin__") and field_type.__origin__ is list:
                # Handle list types
                item_type = field_type.__args__[0]
                if hasattr(item_type, "__name__") and item_type.__name__ != "Any":
                    item_name = item_type.__name__
                    if hasattr(item_type, "model_fields"):
                        model_dependencies[model_name].add(item_name)
                        collect_nested_models(item_type, item_name)
            elif hasattr(field_type, "__name__") and field_type.__name__ != "Any":
                # Handle direct model types
                type_name = field_type.__name__
                if hasattr(field_type, "model_fields"):
                    model_dependencies[model_name].add(type_name)
                    collect_nested_models(field_type, type_name)

    # Collect all nested models starting from the main model
    collect_nested_models(model, model_name)

    # Sort models by dependencies (topological sort)
    sorted_models = []
    visited = set()

    def visit(model_name: str) -> None:
        if model_name in visited:
            return
        visited.add(model_name)
        for dep in model_dependencies.get(model_name, set()):
            visit(dep)
        sorted_models.append(model_name)

    for model_name in nested_models:
        visit(model_name)

    # Generate model code
    model_code = f'''"""
Generated Pydantic model.
"""

from typing import Union, Optional, Any, List, Dict
from pydantic import BaseModel, Field, validator
import math

'''

    # Add model definitions in dependency order
    for model_name in sorted_models:
        model_type = nested_models[model_name]
        if hasattr(model_type, "model_fields"):
            model_code += f"class {model_name}(BaseModel):\n"
            for field_name, field in model_type.model_fields.items():
                field_type = field.annotation
                if hasattr(field_type, "__origin__") and field_type.__origin__ is Union:
                    # Handle Optional types
                    types = [t.__name__ for t in field_type.__args__ if t is not type(None)]
                    if len(types) == 1:
                        field_type = f"Optional[{types[0]}]"
                    else:
                        field_type = f"Union[{', '.join(types)}]"
                elif hasattr(field_type, "__origin__") and field_type.__origin__ is list:
                    # Handle list types
                    item_type = field_type.__args__[0]
                    if hasattr(item_type, "__name__"):
                        field_type = f"List[{item_type.__name__}]"
                    else:
                        field_type = "List[Any]"
                else:
                    field_type = field_type.__name__

                # Get field description if it exists
                field_info = field.json_schema_extra or {}
                description = field_info.get("description", "")

                if description:
                    model_code += (
                        f'    {field_name}: {field_type} = Field(description="""{description}""")\n'
                    )
                elif field.default is None:
                    model_code += f"    {field_name}: {field_type} = None\n"
                else:
                    model_code += f"    {field_name}: {field_type}\n"
            model_code += "\n"

    # Add nan validator
    model_code += """
    @validator('*', pre=True)
    def handle_nan(cls, v: Any) -> Any:
        if isinstance(v, float) and math.isnan(v):
            return None
        return v
"""

    output_path.write_text(model_code)


def generate_model_from_schema(
    schema: Dict[str, Dict[str, Any]],
    model_name: str = "DataModel",
    output_file: Optional[str] = None,
    description: Optional[str] = None,
) -> str:
    """
    Generate a Pydantic model from a schema and save it to a file.

    Args:
        schema: Dictionary mapping field names to their specifications
        model_name: Name for the generated model class
        output_file: Optional path where the model file should be saved
        description: Optional description for the model

    Returns:
        Path to the generated model file
    """
    model = generate_pydantic_model(schema, model_name, description)
    if not output_file:
        output_file = f"{model_name.lower()}_model.py"
    save_model_to_file(model, output_file, model_name)
    return output_file
